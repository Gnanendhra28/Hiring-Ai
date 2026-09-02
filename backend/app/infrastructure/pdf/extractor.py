import fitz  # PyMuPDF
from typing import Any
from app.core.config import settings
from app.core.logging import logger

class TextQualityEvaluator:
    """Evaluates text quality extracted from native PDF to determine if OCR fallback is required."""

    @staticmethod
    def evaluate(extracted_text: str, total_pages: int) -> tuple[float, bool]:
        if not extracted_text or len(extracted_text.strip()) == 0:
            return 0.0, True  # Needs OCR

        words = extracted_text.split()
        word_count = len(words)
        char_count = len(extracted_text)

        if word_count < settings.TEXT_QUALITY_MIN_WORDS:
            logger.info(f"Text quality low: word_count={word_count} < min_words={settings.TEXT_QUALITY_MIN_WORDS}")
            return 0.2, True  # Needs OCR

        # Evaluate garbled characters (non-ASCII or unprintable control ratio)
        printable_count = sum(1 for c in extracted_text if c.isprintable() or c in ("\n", "\r", "\t"))
        garbled_ratio = (char_count - printable_count) / max(char_count, 1)

        if garbled_ratio > settings.TEXT_QUALITY_GARBLED_RATIO_MAX:
            logger.info(f"Text quality low: garbled_ratio={garbled_ratio:.2f} > max={settings.TEXT_QUALITY_GARBLED_RATIO_MAX}")
            return max(0.0, 1.0 - garbled_ratio), True

        # Calculate quality score (0.0 to 1.0)
        quality_score = min(1.0, (word_count / (total_pages * 100)))
        needs_ocr = quality_score < 0.3
        return round(quality_score, 2), needs_ocr

class PDFExtractor:
    """Extracts text from PDF documents using PyMuPDF (fitz)."""

    @staticmethod
    def extract_text(file_bytes: bytes) -> dict[str, Any]:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages = doc.page_count
            pages_data: list[dict[str, Any]] = []
            full_text_parts = []

            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                full_text_parts.append(text)
                pages_data.append({
                    "page_number": page_num + 1,
                    "text": text,
                })

            full_text = "\n".join(full_text_parts)
            quality_score, needs_ocr = TextQualityEvaluator.evaluate(full_text, total_pages)

            return {
                "success": True,
                "total_pages": total_pages,
                "full_text": full_text,
                "pages": pages_data,
                "text_quality_score": quality_score,
                "needs_ocr": needs_ocr,
                "error": None,
            }
        except Exception as e:
            logger.error(f"PyMuPDF text extraction failed: {e!s}")
            return {
                "success": False,
                "total_pages": 0,
                "full_text": "",
                "pages": [],
                "text_quality_score": 0.0,
                "needs_ocr": True,
                "error": str(e),
            }
