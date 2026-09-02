"""
Security Tests for Global Exception Handling and Log Redaction.
Verifies that synthetic secret values, database passwords, tokens,
and candidate PII are never leaked in client responses or logs.
"""

import pytest
import json
import logging
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.logging import JSONFormatter


def test_json_formatter_redaction_synthetic_secrets():
    """Verifies that JSONFormatter redacts synthetic secret patterns and passwords."""
    formatter = JSONFormatter()

    synthetic_message = (
        "Database connection error: postgresql+asyncpg://app_user:FAKE_DB_PASSWORD_456@34.93.18.139/hiring_db. "
        "Authorization header: Bearer FAKE_FIREBASE_TOKEN_789. "
        "Gemini key: AIzaSy_FAKE_GEMINI_SECRET_1234567890. "
        "Candidate phone: +1 (555) 234-5678. "
        "SSN: 000-12-3456."
    )

    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test_file.py",
        lineno=42,
        msg=synthetic_message,
        args=(),
        exc_info=None,
    )

    formatted_json_str = formatter.format(record)
    parsed = json.loads(formatted_json_str)
    msg = parsed["message"]

    assert "FAKE_DB_PASSWORD_456" not in msg
    assert "FAKE_FIREBASE_TOKEN_789" not in msg
    assert "000-12-3456" not in msg
    assert "+1 (555) 234-5678" not in msg
    assert "[REDACTED]" in msg


@pytest.mark.asyncio
async def test_global_exception_handler_client_response_safety():
    """Verifies that unhandled internal exceptions return clean JSON with request_id and no stack traces."""
    # Add a dynamic test route to trigger unhandled exception
    @app.get("/api/v1/test-synthetic-unhandled-error")
    async def synthetic_error_route():
        raise RuntimeError("Simulated internal exception with FAKE_GEMINI_SECRET_9999")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/test-synthetic-unhandled-error")
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == "INTERNAL_ERROR"
        assert "message" in data
        assert "request_id" in data
        assert "FAKE_GEMINI_SECRET_9999" not in str(data)
        assert "traceback" not in str(data).lower()
