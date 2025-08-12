from __future__ import annotations
import io
import re
from typing import Dict, Tuple

from docx import Document
from PyPDF2 import PdfReader


EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}")


def _read_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")


def _read_pdf(file: io.BytesIO) -> str:
    reader = PdfReader(file)
    text_parts = []
    for page in reader.pages:
        try:
            text_parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(text_parts)


def _read_docx(file: io.BytesIO) -> str:
    doc = Document(file)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_and_fields(uploaded_file) -> Tuple[str, Dict[str, str]]:
    """
    Accepts a Streamlit UploadedFile or any file-like object with .read() and .name.
    Returns (text, fields_dict).
    """
    name = getattr(uploaded_file, "name", "resume.txt").lower()
    data = uploaded_file.read()

    text = ""
    if name.endswith(".pdf"):
        text = _read_pdf(io.BytesIO(data))
    elif name.endswith(".docx"):
        text = _read_docx(io.BytesIO(data))
    else:
        text = _read_txt(data)

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    first_line = lines[0] if lines else ""
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)

    fields = {
        "name": first_line if 1 <= len(first_line.split()) <= 5 else "",
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else "",
    }

    return text, fields
