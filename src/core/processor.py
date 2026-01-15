from src.core.text_extractor import extract_text
from src.core.nlp_extractor import extract_fields
from src.core.classifier import classify_document


def process_document(file_path: str) -> dict:
    text = extract_text(file_path)

    if not text:
        return {"error": "Не удалось извлечь текст из документа"}

    fields = extract_fields(text)
    classification = classify_document(text)

    return {
        "document_type": classification.get("label"),
        "sender": fields.get("sender"),
        "recipient": fields.get("recipient"),
        "document_date": fields.get("document_date"),
        "document_number": fields.get("document_number"),
        "subject": fields.get("subject"),
    }