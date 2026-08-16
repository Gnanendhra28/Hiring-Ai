import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, HttpUrl, Field

ALLOWED_WEBHOOK_EVENTS = [
    "job.intelligence.completed",
    "offer.created",
    "offer.accepted",
    "candidate.hired",
]

class WebhookSubscriptionCreate(BaseModel):
    endpoint_url: str = Field(..., description="Target HTTPS destination URL for webhook POST requests")
    subscribed_events: List[str] = Field(
        ...,
        description="List of event types to subscribe to (e.g. ['offer.accepted', 'candidate.hired'])",
    )

class WebhookSubscriptionUpdate(BaseModel):
    endpoint_url: Optional[str] = None
    enabled: Optional[bool] = None
    subscribed_events: Optional[List[str]] = None

class WebhookSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    endpoint_url: str
    enabled: bool
    subscribed_events: List[str]
    created_at: datetime
    updated_at: datetime

class WebhookSubscriptionCreateResponse(WebhookSubscriptionResponse):
    secret: str = Field(..., description="Cryptographic signing secret. Exposed ONLY ONCE upon creation.")

class SecretRotationResponse(BaseModel):
    subscription_id: uuid.UUID
    new_secret: str = Field(..., description="New cryptographic signing secret. Exposed ONLY ONCE upon rotation.")

class WebhookEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    subscription_id: uuid.UUID
    event_id: uuid.UUID
    event_type: str
    delivery_status: str
    attempt_count: int
    first_attempt_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    last_http_status: Optional[int] = None
    last_error_code: Optional[str] = None
    created_at: datetime

class WebhookTestResponse(BaseModel):
    subscription_id: uuid.UUID
    event_type: str = "webhook.test"
    delivery_status: str
    http_status: Optional[int] = None
    delivered: bool
