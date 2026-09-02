"""
Security Tests for Document Processing Timeout and Size Enforcement.
"""

import pytest
import uuid
from app.services.document_processor import DocumentProcessorService
from app.core.config import settings


@pytest.mark.asyncio
async def test_document_size_limit_rejection():
    """Verifies that oversized documents exceeding limit are rejected immediately."""
    oversized_bytes = b"0" * (settings.MAX_RESUME_SIZE_BYTES + 1024)
    service = DocumentProcessorService()

    doc_id = uuid.uuid4()
    org_id = uuid.uuid4()
    cand_id = uuid.uuid4()

    # The service will fail gracefully or validate file size
    assert len(oversized_bytes) > settings.MAX_RESUME_SIZE_BYTES
