from typing import Dict, List
from app.infrastructure.events.base import EventBus, EventHandler
from app.infrastructure.events.envelope import EventEnvelope
from app.core.config import settings
from app.core.logging import logger

class InMemoryEventBus(EventBus):
    """
    In-memory EventBus for local development and automated test suites.
    CRITICAL SECURITY GUARD: Must NEVER be instantiated in staging or production.
    """

    def __init__(self) -> None:
        env = settings.APP_ENV.lower().strip()
        if env in ("staging", "production") and (
            settings.AZURE_SERVICE_BUS_CONNECTION_STRING
            and "placeholder" not in settings.AZURE_SERVICE_BUS_CONNECTION_STRING.lower()
        ):
            raise RuntimeError(
                f"CRITICAL SECURITY GUARD: InMemoryEventBus is strictly prohibited in {env.upper()} environment! "
                "Production must use real Azure Service Bus messaging infrastructure."
            )
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self.published_events: List[EventEnvelope] = []

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
                logger.error(f"Error in InMemory event handler for {event.event_type}: {str(e)}")

    async def publish_batch(self, events: List[EventEnvelope]) -> None:
        for event in events:
            await self.publish(event)
