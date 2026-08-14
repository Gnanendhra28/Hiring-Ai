from typing import Dict, List, Optional
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from app.infrastructure.events.base import EventBus, EventHandler
from app.infrastructure.events.envelope import EventEnvelope
from app.core.config import settings
from app.core.logging import logger

class AzureServiceBusEventBus(EventBus):
    """
    Real Azure Service Bus EventBus adapter for staging and production environments.
    Fail fast at startup if configuration or connection string is invalid.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        topic_name: Optional[str] = None,
    ) -> None:
        conn_str = connection_string or settings.AZURE_SERVICE_BUS_CONNECTION_STRING
        env = settings.APP_ENV.lower().strip()

        if not conn_str or "placeholder" in conn_str:
            if env in ("staging", "production"):
                raise ValueError(
                    f"CRITICAL SERVICE BUS CONFIGURATION ERROR in {env.upper()}: "
                    "AZURE_SERVICE_BUS_CONNECTION_STRING is missing or using placeholder values."
                )
            else:
                logger.warning("Azure Service Bus connection string is not configured. Local fallback required.")

        self.conn_str = conn_str
        self.topic_name = topic_name or settings.AZURE_SERVICE_BUS_TOPIC_APPLICATION_EVENTS
        self.client: Optional[ServiceBusClient] = (
            ServiceBusClient.from_connection_string(conn_str) if conn_str and "placeholder" not in conn_str else None
        )
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler to topic '{self.topic_name}' filter '{event_type}'")

    async def publish(self, event: EventEnvelope) -> None:
        if not self.client:
            raise RuntimeError("Azure Service Bus client is not initialized.")

        async with self.client.get_topic_sender(self.topic_name) as sender:
            msg = ServiceBusMessage(
                body=event.to_json(),
                content_type="application/json",
                correlation_id=event.correlation_id,
                message_id=str(event.event_id),
                session_id=event.session_id if event.session_id else None,
                application_properties={
                    "event_type": event.event_type,
                    "event_version": event.event_version,
                    "organization_id": str(event.organization_id),
                    "aggregate_id": str(event.aggregate_id),
                },
            )
            await sender.send_messages(msg)
            logger.info(f"Published event '{event.event_type}' to Azure Service Bus topic '{self.topic_name}' [session_id={event.session_id}]")

    async def publish_batch(self, events: List[EventEnvelope]) -> None:
        if not self.client or not events:
            return

        async with self.client.get_topic_sender(self.topic_name) as sender:
            batch = await sender.create_message_batch()
            for event in events:
                msg = ServiceBusMessage(
                    body=event.to_json(),
                    content_type="application/json",
                    correlation_id=event.correlation_id,
                    message_id=str(event.event_id),
                    session_id=event.session_id if event.session_id else None,
                    application_properties={
                        "event_type": event.event_type,
                        "organization_id": str(event.organization_id),
                    },
                )
                try:
                    batch.add_message(msg)
                except ValueError:
                    # Batch full, send current batch and create new one
                    await sender.send_messages(batch)
                    batch = await sender.create_message_batch()
                    batch.add_message(msg)

            if len(batch) > 0:
                await sender.send_messages(batch)

    async def close(self):
        if self.client:
            await self.client.close()
