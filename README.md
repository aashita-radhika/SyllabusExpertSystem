# Syllabus Studio

A Flask web application that turns publicly accessible educational webpages into a structured syllabus, estimated topic relevance scores, and exactly ten extractive practice questions with answers. The application uses Requests and BeautifulSoup for page extraction and ReportLab for PDF exports.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The server honors the `PORT` environment variable and binds to `0.0.0.0`.

## Features

- Curated five-unit frameworks for Computer Networks, Operating Systems, and DBMS, enriched with keyword-frequency estimates from extracted content.
- Content-driven syllabus grouping for other subjects.
- Exactly ten questions, with answers selected from relevant extracted sentences; insufficient evidence is identified honestly.
- Source-by-source processing status and concise errors.
- Individual and global answer reveal controls, saved light/dark theme, responsive layout, and three PDF exports.

## Public web access and safety

Only public HTTP(S) pages are fetched. The extractor rejects local/private IP destinations, validates redirects, limits response size, applies request timeouts, and does not bypass authentication, paywalls, or access restrictions. Websites that render content only in JavaScript may not provide extractable text. Topic relevance is a simple estimated keyword frequency, not verified academic importance or an AI assessment.
