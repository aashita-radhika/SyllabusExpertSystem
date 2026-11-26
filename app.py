from flask import Flask, jsonify, render_template, request, send_file
from io import BytesIO
import os

from modules.pdf_generator import build_pdf
from modules.question_generator import generate_questions
from modules.scraper import scrape_url
from modules.syllabus_generator import generate_syllabus, word_count

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    subject = str(data.get("subject", "")).strip()
    urls = data.get("urls", [])
    if not subject or len(subject) > 120:
        return jsonify(error="Enter a subject between 1 and 120 characters."), 400
    if not isinstance(urls, list) or not urls or len(urls) > 10:
        return jsonify(error="Enter between 1 and 10 educational URLs."), 400
    urls = [str(url).strip() for url in urls if str(url).strip()]
    if not urls:
        return jsonify(error="Enter at least one URL."), 400

    sources, documents = [], []
    for url in urls:
        try:
            document = scrape_url(url)
            documents.append(document)
            sources.append({"url": url, "ok": True, "title": document["title"], "message": "Content extracted successfully."})
        except Exception as exc:
            # Errors are deliberately concise and do not expose server internals.
            sources.append({"url": url, "ok": False, "message": str(exc) or "The page could not be processed."})

    if not documents:
        return jsonify(success=False, error="None of the supplied pages could be processed. Check the URLs and try publicly accessible educational pages.", sources=sources), 200

    corpus = "\n".join(doc["text"] for doc in documents)
    syllabus, method = generate_syllabus(subject, documents, corpus)
    questions = generate_questions(syllabus, documents)
    result = {
        "success": True,
        "subject": subject,
        "syllabus": syllabus,
        "questions": questions,
        "sources": sources,
        "method": method,
        "stats": {"units": len(syllabus), "questions": 10, "sources": sum(1 for s in sources if s["ok"]), "words": word_count(corpus)},
    }
    return jsonify(result)


@app.post("/api/export/<kind>")
def export(kind):
    if kind not in {"syllabus", "qa", "complete"}:
        return jsonify(error="Unknown export type."), 404
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("syllabus"), list) or not isinstance(data.get("questions"), list) or len(data["questions"]) != 10:
        return jsonify(error="Generate a complete study pack before exporting."), 400
    try:
        pdf = build_pdf(kind, data)
    except Exception:
        app.logger.exception("PDF export failed")
        return jsonify(error="The PDF could not be created. Please try again."), 500
    safe_subject = "".join(ch if ch.isalnum() or ch in "-_ " else "" for ch in str(data.get("subject", "study-pack"))).strip().replace(" ", "-")[:50] or "study-pack"
    return send_file(BytesIO(pdf), mimetype="application/pdf", as_attachment=True, download_name=f"{safe_subject}-{kind}.pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
