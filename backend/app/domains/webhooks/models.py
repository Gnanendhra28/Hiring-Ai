import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin, TenantMixin

class WebhookDeliveryStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"

class WebhookSubscription(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Tenant-scoped webhook subscription configuration.
    Stores destination endpoint URL and signing secret.
    """
    __tablename__ = "webhook_subscriptions"
    __table_args__ = {"extend_existing": True}

    endpoint_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    subscribed_events: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    events: Mapped[List["WebhookEvent"]] = relationship(
        "WebhookEvent", back_populates="subscription", cascade="all, delete-orphan"
    )

class WebhookEvent(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Immutable outbound webhook event delivery log record.
    Supports idempotency, exponential backoff retries, and delivery audit.
    """
    __tablename__ = "webhook_events"
    __table_args__ = {"extend_existing": True}

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    delivery_status: Mapped[WebhookDeliveryStatusEnum] = mapped_column(
        SQLEnum(WebhookDeliveryStatusEnum, name="webhookdeliverystatusenum"),
        default=WebhookDeliveryStatusEnum.PENDING,
        nullable=False,
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    last_http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_error_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationship
    subscription: Mapped["WebhookSubscription"] = relationship("WebhookSubscription", back_populates="events")
