import uuid
from datetime import datetime, UTC
from sqlalchemy import DateTime, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin
from app.core.logging import logger

class ProcessedEvent(Base, UUIDMixin):
    """
    Tracks processed event IDs per consumer to guarantee event consumer idempotency.
    """
    __tablename__ = "processed_events"
    __table_args__ = (
        UniqueConstraint("event_id", "consumer_id", name="uq_event_consumer"),
        {"extend_existing": True},
    )

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    consumer_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

class EventIdempotencyTracker:
    """Helper for checking and recording event processing idempotency."""

    @staticmethod
    async def is_processed(session: AsyncSession, event_id: uuid.UUID, consumer_id: str) -> bool:
        stmt = select(ProcessedEvent).where(
            ProcessedEvent.event_id == event_id,
            ProcessedEvent.consumer_id == consumer_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def mark_processed(session: AsyncSession, event_id: uuid.UUID, consumer_id: str) -> None:
        processed = ProcessedEvent(event_id=event_id, consumer_id=consumer_id)
        session.add(processed)
        await session.flush()
        logger.debug(f"Marked event {event_id} as processed by consumer {consumer_id}")
