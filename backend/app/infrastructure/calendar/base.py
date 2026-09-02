from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from app.core.logging import logger

class CalendarProvider(ABC):
    """Abstract Base Class for Calendar Providers (Microsoft Graph / Google Calendar)."""

    @abstractmethod
    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        attendees: list[str],
        timezone: str = "UTC",
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def cancel_event(self, event_id: str) -> bool:
        pass

class TestCalendarAdapter(CalendarProvider):
    """Controlled Test Calendar Adapter for Local Development and Integration Tests."""

    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        attendees: list[str],
        timezone: str = "UTC",
    ) -> dict[str, Any]:
        logger.info(f"Created test calendar event: '{summary}' from {start_time.isoformat()} to {end_time.isoformat()} [{timezone}]")
        return {
            "event_id": f"cal-evt-{start_time.strftime('%Y%m%d%H%M%S')}",
            "summary": summary,
            "status": "CONFIRMED",
            "provider": "TEST",
        }

    async def cancel_event(self, event_id: str) -> bool:
        logger.info(f"Cancelled test calendar event: {event_id}")
        return True
