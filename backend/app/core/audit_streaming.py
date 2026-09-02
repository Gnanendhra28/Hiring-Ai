import json
import logging
import uuid
from datetime import datetime, UTC
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger("ai_hiring_platform.audit_streamer")

SENSITIVE_KEYS = {
    "password", "jwt", "token", "access_token", "refresh_token",
    "secret", "api_key", "gemini_api_key", "webhook_secret",
    "authorization", "bearer", "resume_text", "document_text",
    "email", "phone", "address"
}

class SecurityEventSchema(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_version: str = "1.0"
    occurred_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    organization_id: str | None = None
    actor_type: str = "SYSTEM"
    actor_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    outcome: str = "SUCCESS"  # SUCCESS, FAILURE, DENIED
    severity: str = "INFO"    # INFO, WARNING, HIGH, CRITICAL
    correlation_id: str | None = None
    request_id: str | None = None
    source: str = "api"
    metadata: dict[str, Any] = Field(default_factory=dict)

def sanitize_payload(data: Any) -> Any:
    """Recursively strip sensitive credentials, tokens, and PII from metadata payloads."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if k.lower() in SENSITIVE_KEYS:
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_payload(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    return data

class SIEMAdapter:
    def publish(self, event: dict[str, Any]) -> bool:
        raise NotImplementedError

    def health_check(self) -> dict[str, Any]:
        raise NotImplementedError

class CloudWatchSIEMAdapter(SIEMAdapter):
    def publish(self, event: dict[str, Any]) -> bool:
        try:
            # Emit structured JSON audit log to CloudWatch stream via root logger
            sanitized_event = sanitize_payload(event)
            logger.info(json.dumps(sanitized_event))
            return True
        except Exception as e:
            # Non-blocking fail-safe: never crash application due to logging errors
            logger.error(f"Audit streaming error: {e}")
            return False

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "HEALTHY",
            "provider": "CLOUDWATCH_ONLY",
            "external_siem": "NOT_CONFIGURED"
        }

class AuditStreamerService:
    def __init__(self):
        self.adapter: SIEMAdapter = CloudWatchSIEMAdapter()
        # In-memory circular buffer for operations dashboard monitoring (max 100 events)
        self._event_buffer: list[dict[str, Any]] = []

    def emit_event(
        self,
        event_type: str,
        organization_id: str | None = None,
        actor_type: str = "SYSTEM",
        actor_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        outcome: str = "SUCCESS",
        severity: str = "INFO",
        correlation_id: str | None = None,
        request_id: str | None = None,
        source: str = "api",
        metadata: dict[str, Any] | None = None
    ) -> bool:
        try:
            sanitized_meta = sanitize_payload(metadata or {})
            event_obj = SecurityEventSchema(
                event_type=event_type,
                organization_id=str(organization_id) if organization_id else None,
                actor_type=actor_type,
                actor_id=str(actor_id) if actor_id else None,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                outcome=outcome,
                severity=severity,
                correlation_id=correlation_id,
                request_id=request_id,
                source=source,
                metadata=sanitized_meta
            )
            event_dict = event_obj.model_dump()

            # Store in buffer
            self._event_buffer.append(event_dict)
            if len(self._event_buffer) > 200:
                self._event_buffer.pop(0)

            # Publish to CloudWatch / SIEM
            return self.adapter.publish(event_dict)
        except Exception as ex:
            # Non-blocking fail-safe
            logger.error(f"Failed to emit audit event: {ex}")
            return False

    def get_organization_events(self, organization_id: str, limit: int = 50) -> list[dict[str, Any]]:
        str_org_id = str(organization_id)
        filtered = [e for e in self._event_buffer if e.get("organization_id") == str_org_id]
        return filtered[-limit:]

audit_streamer = AuditStreamerService()
