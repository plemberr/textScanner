import re
import spacy
import os
import sys

# nlp = spacy.load("ru_core_news_sm")


def resource_path(rel):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.abspath(rel)

MODEL_PATH = resource_path("spacy_models/ru_core_news_sm")
nlp = spacy.load(MODEL_PATH)

def extract_fields(text):
    """
        Основная функция nlp-анализа текста.
        Принимает строку, возвращает словарь.
    """

    lines = [line.strip() for line in text.splitlines()]

    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()

    # Результат работы функции
    result = { "sender": None, "recipient": None, "document_date": None,
        "document_number": None, "subject": None, "content_summary": None
    }

    # Регулярные выражение даты и номера
    date_patterns = [
        r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",  # 28.01.2025 или 28/01/2025
        r"\b\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4}\b",
        # 7 февраля 2025
        r"\b\d{4}-\d{2}-\d{2}\b"
    ]
    date_re = re.compile("|".join(f"({p})" for p in date_patterns), re.IGNORECASE)
    num_re = re.compile(r"(?:Документ\s*№[:\s]*|№[:\s]*|Номер[:\s]*)\s*([\w\/\-]+(?:[:\s]*\d{1,2}[\/\-]?\d{1,4})?)", re.IGNORECASE)

    #
    for idx, ln in enumerate(lines):
        if re.match(r"^(Отправитель|От кого)\b", ln, re.IGNORECASE):
            sender_block = collect_block_from(lines, idx)
            sender_block = [s for s in sender_block if s]
            if sender_block:
                result["sender"] = " ".join(spacy_persons(nlp(" ".join(sender_block)))).strip()

        elif re.match(r"^(Получатель|Кому)\b", ln, re.IGNORECASE):
            recipient_block = collect_block_from(lines, idx)
            recipient_block = [s for s in recipient_block if s]
            if recipient_block:
                result["recipient"] = " ".join(spacy_persons(nlp(" ". join(recipient_block).strip()))).strip()

        elif re.match(r"^(Тема|Subject)[:\s]", ln, re.IGNORECASE):
            if ":" in ln:
                result["subject"] = ln.split(":", 1)[1].strip()
            else:
                # если тема на следующей строке
                if idx + 1 < len(lines) and lines[idx + 1].strip():
                    result["subject"] = lines[idx + 1].strip()

        elif result["sender"] is None:
            sender_block = collect_block_from(lines, idx-1)
            sender_block = [s for s in sender_block if s]
            if sender_block:
                result["sender"] = " ".join(spacy_persons(nlp(" ".join(sender_block)))).strip()


    num_match = num_re.search(text)
    if num_match:
        result["document_number"] = num_match.group(1).strip()

        # Поиск даты — отдаем первое правдоподобное совпадение
    date_match = date_re.search(text)
    if date_match:
        for g in date_match.groups():
            if g:
                result["document_date"] = g.strip().strip(" .гГ")
                break

    # Нормализуем пробелы
    for k in ["sender", "recipient", "document_date", "document_number", "subject"]:
        if result.get(k):
            result[k] = " ".join(result[k].split())

    return result

def collect_block_from(lines, i):
    """
        Объединение строк в смысловые блоки.
    """
    block = []
    if ":" in lines[i]:
        after = lines[i].split(":", 1)[1].strip()
        if after:
            block.append(after)
    j = i + 1
    while j < len(lines):
        ln = lines[j].strip()
        if ln == "":
            break
        if re.match(r"^(От|Отправитель|От кого|Получатель|Кому|Документ|Дата|Тема|Текст|С уважением)\b", ln, re.IGNORECASE):
            break
        block.append(ln)
        j += 1

    return block

def spacy_persons(doc):
    """
        Поиск конкретных ФИО / Организаций в блоке.
    """
    persons = [ent.text for ent in doc.ents if ent.label_ in ("PER", "ORG")]

    return persons