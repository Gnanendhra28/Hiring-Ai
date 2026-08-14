from abc import ABC, abstractmethod
from typing import Awaitable, Callable, List
from app.infrastructure.events.envelope import EventEnvelope

EventHandler = Callable[[EventEnvelope], Awaitable[None]]

class EventBus(ABC):
    """Abstract Event Bus interface for publishing and subscribing domain events."""

    @abstractmethod
    async def publish(self, event: EventEnvelope) -> None:
        """Publishes a single event envelope."""
        pass

    @abstractmethod
    async def publish_batch(self, events: List[EventEnvelope]) -> None:
        """Publishes a batch of event envelopes."""
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribes an async handler function to a specific event type."""
        pass
