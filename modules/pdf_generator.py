"""ReportLab PDF rendering for syllabus, Q&A, and complete packs."""
from html import escape
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, PageBreak

PURPLE = colors.HexColor("#6558d3")


def _safe(value):
    # Paragraph uses XML markup; escape page-derived/user-provided text.
    return xml_escape(str(value or "")).replace("\n", "<br/>")


def build_pdf(kind, data):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm, title=f"Syllabus Studio — {data.get('subject', 'Study Pack')}")
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("StudioTitle", parent=base["Title"], textColor=PURPLE, fontName="Helvetica-Bold", fontSize=22, leading=27, alignment=TA_LEFT, spaceAfter=8),
        "subtitle": ParagraphStyle("StudioSub", parent=base["Normal"], textColor=colors.HexColor("#536078"), fontSize=11, leading=16, spaceAfter=16),
        "h": ParagraphStyle("StudioH", parent=base["Heading2"], textColor=PURPLE, fontSize=14, leading=18, spaceBefore=12, spaceAfter=7, keepWithNext=True),
        "body": ParagraphStyle("StudioBody", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, spaceAfter=5, wordWrap="CJK"),
        "small": ParagraphStyle("StudioSmall", parent=base["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#536078"), spaceAfter=5, wordWrap="CJK"),
    }
    story = [Paragraph("Syllabus Studio", styles["title"]), Paragraph(_safe(data.get("subject", "Study Pack")), styles["subtitle"])]
    if kind in ("syllabus", "complete"):
        story.append(Paragraph("Generated syllabus", styles["h"]))
        for number, unit in enumerate(data.get("syllabus", []), 1):
            group = [Paragraph(f"Unit {number}: {_safe(unit.get('title'))}", styles["h"])]
            for topic in unit.get("topics", []):
                name = topic.get("name", "") if isinstance(topic, dict) else topic
                group.append(Paragraph("• " + _safe(name), styles["body"]))
            story.append(KeepTogether(group))
        if kind == "syllabus":
            story.append(Spacer(1, 8))
    if kind in ("qa", "complete"):
        if kind == "complete":
            story.append(PageBreak())
        story.append(Paragraph("Questions and answers", styles["h"]))
        for i, item in enumerate(data.get("questions", []), 1):
            story.append(KeepTogether([Paragraph(f"{i}. {_safe(item.get('question'))}", styles["h"]), Paragraph("<b>Answer:</b> " + _safe(item.get("answer")), styles["body"]), Spacer(1, 5)]))
    if kind == "complete":
        story.append(Paragraph("Source verification", styles["h"]))
        for source in data.get("sources", []):
            status = "Processed" if source.get("ok") else "Not processed"
            story.append(Paragraph(f"{_safe(status)} — {_safe(source.get('url'))}", styles["small"]))
            if source.get("message"):
                story.append(Paragraph(_safe(source.get("message")), styles["small"]))
        story.append(Paragraph("Syllabus generation method", styles["h"]))
        story.append(Paragraph(_safe(data.get("method", "")), styles["body"]))
    doc.build(story)
    return output.getvalue()
