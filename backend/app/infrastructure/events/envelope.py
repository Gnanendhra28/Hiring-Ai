import uuid
from datetime import datetime, UTC
from typing import Any
from pydantic import BaseModel, Field

class EventEnvelope(BaseModel):
    """
    Standardized immutable event payload structure across the system.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str = Field(..., description="Dot-notation event name, e.g. application.created")
    event_version: str = Field(default="1.0.0")
    aggregate_id: uuid.UUID = Field(..., description="ID of entity producing event")
    organization_id: uuid.UUID = Field(..., description="Tenant ID of organization context")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str = Field(..., description="Distributed tracing correlation ID")
    session_id: str | None = Field(default=None, description="Optional Service Bus session key for aggregate ordering")
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "EventEnvelope":
        return cls.model_validate_json(json_str)
