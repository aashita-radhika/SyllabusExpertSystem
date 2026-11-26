"""Curated and content-driven syllabus generation."""
import re
from collections import Counter

STOP = set("a an the and or but if then than of to in on for by with from at as is are was were be been being it its this that these those their they them we you your our can could may might will would should do does did have has had not no into about over under between through after before such also more most other some any each both how what when where why which who whose use used using based called known including example examples".split())

CURATED = {
"computer networks": [
("Network Foundations", ["Network models and architectures", "OSI reference model", "TCP/IP protocol suite", "Network topologies", "Transmission media"]),
("Data Link and Physical Layers", ["Signals and encoding", "Framing and error detection", "Media access control", "Ethernet and switching", "Wireless LAN fundamentals"]),
("Network and Internetwork Layer", ["IPv4 and IPv6 addressing", "Subnetting and CIDR", "Routing algorithms", "IP forwarding", "Address resolution"]),
("Transport Layer", ["Process-to-process delivery", "UDP and TCP", "Flow and congestion control", "Reliable data transfer", "Ports and sockets"]),
("Application and Network Security", ["DNS and name resolution", "HTTP and web services", "Email protocols", "Network security principles", "Firewalls and secure communication"])],
"operating systems": [
("OS Foundations", ["Operating system services", "Kernel architectures", "System calls", "Processes and process states", "Threads and multithreading"]),
("Process Management", ["CPU scheduling", "Inter-process communication", "Process synchronization", "Critical sections and semaphores", "Deadlocks and recovery"]),
("Memory Management", ["Address translation", "Contiguous allocation", "Paging and page tables", "Virtual memory", "Page replacement algorithms"]),
("Storage and File Systems", ["File concepts and operations", "Directory structures", "File allocation methods", "Disk scheduling", "I/O systems"]),
("Protection and Modern Systems", ["Protection domains", "Access control", "Security threats", "Virtualization", "Distributed and embedded systems"])],
"dbms": [
("Database Concepts and Architecture", ["Database system fundamentals", "Three-schema architecture", "Data models", "Database users and administrators", "Relational model"]),
("Relational Design and SQL", ["Relations and keys", "Relational algebra", "SQL queries and joins", "Constraints and views", "Database design principles"]),
("Dependencies and Normalization", ["Functional dependencies", "First normal form", "Second and third normal forms", "BCNF", "Decomposition and lossless joins"]),
("Transactions and Concurrency", ["ACID properties", "Transaction states", "Serializability", "Lock-based protocols", "Recovery and logging"]),
("Storage, Indexing and Applications", ["File organization", "B-tree indexes", "Hash indexing", "Query processing", "Database security and backup"])],
}


def tokens(text):
    return [w for w in re.findall(r"[a-z][a-z0-9-]{2,}", text.lower()) if w not in STOP]


def relevance(topic, corpus):
    words = tokens(topic)
    text = corpus.lower()
    hits = sum(len(re.findall(r"\b" + re.escape(word) + r"\b", text)) for word in words)
    return min(100, round(100 * hits / max(1, len(words) * 5)))


def generate_syllabus(subject, documents, corpus):
    key = re.sub(r"[^a-z0-9 ]", "", subject.lower()).strip()
    selected = next((value for name, value in CURATED.items() if name == key or name in key or key in name), None)
    if selected:
        units = [{"title": title, "topics": [{"name": topic, "relevance": relevance(topic, corpus)} for topic in topics]} for title, topics in selected]
        return units, "Curated subject framework enriched with estimated keyword relevance from the supplied source text."
    headings = []
    for doc in documents:
        # Heading-like phrases are preserved in extracted text; title is also a useful seed.
        headings.append(doc.get("title", ""))
        headings.extend(line for line in doc["text"].splitlines() if 2 <= len(line.split()) <= 10)
    counts = Counter(tokens(corpus))
    bigrams = Counter()
    for line in headings:
        phrase = " ".join(tokens(line)[:4]).strip()
        if len(phrase.split()) >= 2:
            bigrams[phrase.title()] += 5
    phrases = [phrase for phrase, _ in bigrams.most_common(30)]
    for word, count in counts.most_common(50):
        if count >= 2 and word not in {p.lower() for p in phrases}:
            phrases.append(word.title())
    if not phrases:
        phrases = [subject.strip().title()]
    phrases = phrases[:25]
    units = []
    for i in range(0, len(phrases), 5):
        topics = phrases[i:i + 5]
        if topics:
            units.append({"title": f"{subject.title()} — Key Concepts {len(units) + 1}", "topics": [{"name": topic, "relevance": relevance(topic, corpus)} for topic in topics]})
        if len(units) == 5:
            break
    return units, "Content-driven topic grouping using extracted headings and frequent terms; relevance is estimated by keyword frequency, not academic importance."


def word_count(text):
    return len(re.findall(r"\b\w+\b", text))
