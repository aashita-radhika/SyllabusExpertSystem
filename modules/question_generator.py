"""Transparent extractive question and answer generation."""
import re
from modules.syllabus_generator import tokens

FALLBACK = "The supplied resources did not contain enough information to generate a reliable answer for this question. Please refer to your textbook or additional learning resources."
PROMPTS = [
    "Define {topic} in the context of {subject}.",
    "Why is {topic} important in {subject}?",
    "Describe the main components or steps involved in {topic}.",
    "Explain how {topic} works.",
    "What are the advantages and limitations of {topic}?",
    "How does {topic} differ from related concepts in {subject}?",
    "Give a practical example that illustrates {topic}.",
    "What problems can arise with {topic}, and how might they be addressed?",
    "What role does {topic} play in the broader study of {subject}?",
    "Summarize the key ideas a learner should understand about {topic}.",
]


def generate_questions(syllabus, documents):
    topics = [topic["name"] for unit in syllabus for topic in unit["topics"]]
    if not topics:
        topics = ["the subject"]
    sentences = []
    for document in documents:
        sentences.extend(document.get("sentences", []))
    subject = "the subject"
    questions = []
    for index in range(10):
        topic = topics[index % len(topics)]
        query = set(tokens(topic))
        ranked = sorted(enumerate(sentences), key=lambda pair: (len(query.intersection(tokens(pair[1]))), -pair[0]), reverse=True)
        chosen, seen = [], set()
        for _, sentence in ranked:
            cleaned = re.sub(r"\s+", " ", sentence).strip()
            normalized = cleaned.lower()
            if query.intersection(tokens(cleaned)) and normalized not in seen:
                chosen.append(cleaned)
                seen.add(normalized)
            if len(chosen) == 2:
                break
        questions.append({"question": PROMPTS[index].format(topic=topic, subject=subject), "topic": topic, "answer": " ".join(chosen) if chosen else FALLBACK})
    return questions
