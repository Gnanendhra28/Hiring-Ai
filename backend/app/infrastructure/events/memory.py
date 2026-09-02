from app.infrastructure.events.base import EventBus, EventHandler
from app.infrastructure.events.envelope import EventEnvelope
from app.core.logging import logger

class InMemoryEventBus(EventBus):
    """
    In-memory EventBus for local development and automated test suites.
    CRITICAL SECURITY GUARD: Must NEVER be instantiated in staging or production.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = {}
        self.published_events: list[EventEnvelope] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler to event '{event_type}' (InMemory)")

    async def publish(self, event: EventEnvelope) -> None:
        self.published_events.append(event)
        logger.info(f"Published event '{event.event_type}' [id={event.event_id}, org={event.organization_id}] (InMemory)")

        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in InMemory event handler for {event.event_type}: {e!s}")

    async def publish_batch(self, events: list[EventEnvelope]) -> None:
        for event in events:
            await self.publish(event)
