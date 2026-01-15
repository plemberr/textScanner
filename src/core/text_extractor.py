import os
import logging
from pathlib import Path
import sys
from pdf2image import convert_from_path
import pytesseract
import fitz
import pdfplumber
from docx import Document
from PIL import Image
import re

# Указать путь к tesseract.exe
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def resource_path(relative_path: str) -> str:
    """
    Возвращает корректный путь:
    - при обычном запуске → из папки проекта
    - при запуске exe (PyInstaller) → из _MEIPASS
    """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


pytesseract.pytesseract.tesseract_cmd = resource_path(
    os.path.join("tesseract", "tesseract.exe")
)


def normalize_text(text):
    if text is None:
        return ""
    return re.sub(r'\n{2,}', '\n', text)


# OCR для изображений
def ocr_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang='rus')
        return text
    except Exception as e:
        logging.error(f"OCR failed for {image_path}: {e}")
        return None

# OCR для PDF без текста
def ocr_pdf(pdf_path):
    try:
        images = convert_from_path(pdf_path)
        full_text = ""
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang='rus')
            full_text += text + "\n"
        return full_text
    except Exception as e:
        logging.error(f"OCR PDF failed for {pdf_path}: {e}")
        return None

# Прямое извлечение текста из PDF
def extract_text_pdf(pdf_path):
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                page_text = page.get_text()
                if page_text.strip():
                    text += page_text + "\n"
        if not text.strip():
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        return text if text.strip() else None
    except Exception as e:
        logging.error(f"PDF extraction failed for {pdf_path}: {e}")
        return None

# Извлечение текста из DOCX
def extract_text_docx(docx_path):
    try:
        doc = Document(docx_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text if text.strip() else None
    except Exception as e:
        logging.error(f"DOCX extraction failed for {docx_path}: {e}")
        return None

# Основная функция
def extract_text(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        logging.error(f"File not found: {file_path}")
        return None

    ext = file_path.suffix.lower()
    if ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        return normalize_text(ocr_image(file_path))
    elif ext == '.pdf':
        text = extract_text_pdf(file_path)
        if text:
            return normalize_text(text)
        else:
            return normalize_text(ocr_pdf(file_path))
    elif ext == '.docx':
        return normalize_text(extract_text_docx(file_path))
    else:
        logging.error(f"Unsupported file type: {file_path}")
        return None

# # Настройка логирования
# logging.basicConfig(
#     filename='logs/text_extractor.log',
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )