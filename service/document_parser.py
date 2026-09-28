import os
from PyPDF2 import PdfReader


def extract_text_from_text(file_path: str) -> dict:
    """Extracts text from a plain text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return {"text": text.strip(), "page_count": 1}


def extract_text_from_pdf(file_path: str) -> dict:
    """Extracts text from a PDF file."""
    reader = PdfReader(file_path)
    extracted_pages = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_pages.append(page_text)

    full_text = "\n".join(extracted_pages)
    return {"text": full_text.strip(), "page_count": len(reader.pages)}


def extract_text(file_path: str) -> dict:
    """Extracts text based on file extension."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        return extract_text_from_text(file_path)
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(
            f"Unsupported file format: '{ext}'. Only .pdf and .txt are allowed."
        )
