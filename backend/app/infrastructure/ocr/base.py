from abc import ABC, abstractmethod
from typing import Any
from app.core.logging import logger

class OCRProvider(ABC):
    """Abstract Base Class for OCR Providers (PaddleOCR, Tesseract, Azure Read API)."""

    @abstractmethod
    async def extract_text_from_pdf(self, file_bytes: bytes) -> dict[str, Any]:
        pass

class TestOCRAdapter(OCRProvider):
    """Controlled OCR Adapter for Scanned Document Fallback in Development/Testing."""

    async def extract_text_from_pdf(self, file_bytes: bytes) -> dict[str, Any]:
        logger.info(f"Executed Test OCR fallback on PDF ({len(file_bytes)} bytes)")
        ocr_text = (
            "SENIOR SOFTWARE ENGINEER - RESUME\n"
            "Skills: Python, FastAPI, PostgreSQL, RAG, Docker, Kubernetes\n"
            "Experience:\n"
            "Acme Corp - Senior Architect (2021-01 - Present)\n"
            "Beta Systems - Staff Engineer (2018-06 - 2020-12)\n"
            "Education:\n"
            "BS Computer Science - Tech University (2014 - 2018)"
        )
        return {
            "success": True,
            "provider": "TEST_OCR",
            "extracted_text": ocr_text,
            "confidence": 0.95,
            "pages": [{"page_number": 1, "text": ocr_text}],
        }
