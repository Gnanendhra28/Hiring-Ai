"""
Candidate Ingestion Pipeline - PDF Text Extractor
Uses PyMuPDF (fitz) to extract clean, structured text and metadata from PDF resumes.
"""

from typing import Any, Dict
import pymupdf  # PyMuPDF


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts readable text from PDF bytes using PyMuPDF.
    Cleans up duplicate whitespace and standardizes newlines.
    """
    if not pdf_bytes:
        return ""

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text")
        if text and text.strip():
            pages_text.append(text.strip())

    doc.close()
    return "\n\n".join(pages_text)


def extract_pdf_metadata(pdf_bytes: bytes) -> Dict[str, Any]:
    """Extracts PDF metadata such as page count, creation date, and title."""
    if not pdf_bytes:
        return {"page_count": 0, "metadata": {}}

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    meta = doc.metadata or {}
    page_count = len(doc)
    doc.close()

    return {
        "page_count": page_count,
        "format": meta.get("format", "PDF"),
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
    }
