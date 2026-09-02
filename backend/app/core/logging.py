import logging
import json
import sys
import re
from datetime import datetime, timezone
from typing import Any, Dict
from app.core.config import settings

SENSITIVE_PATTERNS = [
    re.compile(r'(password|token|secret|api_key|authorization|cookie|gemini_api_key|database_url|db_password)["\']?\s*[:=]\s*["\']?([^"\'\s&]+)', re.IGNORECASE),
    re.compile(r'(bearer\s+)[a-zA-Z0-9\-\._~\+\/]+=*', re.IGNORECASE),
    re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE),  # Emails
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # SSNs
    re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),  # Phone numbers
    re.compile(r'postgres(ql)?(\+asyncpg)?:\/\/[^:]+:([^@]+)@', re.IGNORECASE),  # DB passwords in URIs
    re.compile(r'(resume_text|extracted_text|raw_text)["\']?\s*[:=]\s*["\']?([^"\'\s&]+)', re.IGNORECASE),
]

class JSONFormatter(logging.Formatter):
    def sanitize(self, text: str) -> str:
        if not text:
            return text
        sanitized = text
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r'[REDACTED]', sanitized)
        return sanitized


    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self.sanitize(record.getMessage()),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }

        # Structured context attributes
        context_fields = [
            "trace_id",
            "span_id",
            "correlation_id",
            "request_id",
            "organization_id",
            "user_id",
            "event_id",
            "job_id",
            "application_id",
        ]
        for field in context_fields:
            if hasattr(record, field):
                log_object[field] = getattr(record, field)

        if record.exc_info:
            log_object["exception"] = self.sanitize(self.formatException(record.exc_info))

        return json.dumps(log_object)

def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())
    root_logger.handlers = [handler]

    # Suppress verbose third-party logs
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("ai_hiring_platform")
