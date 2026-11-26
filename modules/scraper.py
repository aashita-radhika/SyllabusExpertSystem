"""Conservative public-web HTML extraction with basic SSRF protections."""
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

MAX_BYTES = 2_000_000
TIMEOUT = (5, 12)
BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".test")


def _validate_public_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(BLOCKED_SUFFIXES):
            raise ValueError
        try:
            addresses = [ipaddress.ip_address(host)]
        except ValueError:
            addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)]
        if not addresses or any(not address.is_global for address in addresses):
            raise ValueError
        return parsed
    except (ValueError, socket.gaierror, OSError):
        raise ValueError("This URL is invalid or does not point to a publicly accessible host.")


def scrape_url(url):
    current = url
    session = requests.Session()
    session.trust_env = False  # Do not inherit proxy settings from the host environment.
    headers = {"User-Agent": "SyllabusStudio/1.0 (educational content extractor; respects site access controls)", "Accept": "text/html,application/xhtml+xml"}
    response = None
    try:
        for _ in range(4):
            _validate_public_url(current)
            try:
                response = session.get(current, headers=headers, timeout=TIMEOUT, allow_redirects=False, stream=True)
            except requests.Timeout:
                raise ValueError("The page took too long to respond (request timed out).")
            except requests.RequestException:
                raise ValueError("The website could not be reached. It may be unavailable or blocking automated requests.")
            if response.is_redirect or response.is_permanent_redirect:
                target = response.headers.get("Location")
                response.close()
                if not target:
                    raise ValueError("The website returned an invalid redirect.")
                current = urljoin(current, target)
                continue
            break
        else:
            raise ValueError("The page redirected too many times.")

        if response.status_code in (401, 403, 429):
            raise ValueError("The website denied automated access. Use a publicly accessible page; sign-in and access restrictions are not bypassed.")
        if response.status_code >= 400:
            raise ValueError(f"The website returned HTTP {response.status_code}.")
        content_type = response.headers.get("Content-Type", "").lower()
        if content_type and not any(kind in content_type for kind in ("text/html", "application/xhtml+xml")):
            raise ValueError("The URL did not return an HTML page.")
        chunks, size = [], 0
        for chunk in response.iter_content(32_768):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("The page is too large to process (2 MB maximum).")
            chunks.append(chunk)
        raw = b"".join(chunks)
        if not raw.strip():
            raise ValueError("The page did not contain readable content.")
        soup = BeautifulSoup(raw, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else urlparse(current).netloc
        for element in soup.select("script, style, noscript, nav, footer, header, aside, form, iframe, svg, [role='navigation'], [aria-hidden='true']"):
            element.decompose()
        pieces = []
        for node in soup.select("h1, h2, h3, h4, p, li"):
            text = " ".join(node.get_text(" ", strip=True).split())
            if len(text) >= 30 and text not in pieces:
                pieces.append(text)
        if not pieces:
            raise ValueError("No useful text was found. The page may require JavaScript or contain no readable article content.")
        return {"url": url, "title": title[:200], "text": "\n".join(pieces)[:100_000], "sentences": _sentences(pieces)}
    finally:
        if response is not None:
            response.close()
        session.close()


def _sentences(pieces):
    import re
    result = []
    for piece in pieces:
        result.extend(part.strip() for part in re.split(r"(?<=[.!?])\s+", piece) if len(part.strip()) >= 35)
    return result
