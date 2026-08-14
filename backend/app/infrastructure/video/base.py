import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict
from app.core.logging import logger

class VideoMeetingProvider(ABC):
    """Abstract Base Class for Video Meeting Providers (Microsoft Teams, Zoom, Google Meet)."""

    @abstractmethod
    async def create_meeting(self, topic: str, duration_minutes: int) -> Dict[str, Any]:
        pass

class TestVideoMeetingAdapter(VideoMeetingProvider):
    """Development / Testing Video Meeting Provider Adapter."""

    async def create_meeting(self, topic: str, duration_minutes: int) -> Dict[str, Any]:
        meeting_id = uuid.uuid4().hex[:10]
        meeting_url = f"https://meet.internal/test-room/{meeting_id}"
        logger.info(f"Generated test video meeting: '{topic}' ({duration_minutes}m) -> {meeting_url}")
        return {
            "meeting_id": meeting_id,
            "meeting_url": meeting_url,
            "provider": "TEST",
        }
