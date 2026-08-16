import logging
import uuid
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OperationalNotificationService:
    """
    Operational Notification Service.
    Handles read-only event notifications (candidate hired, offer accepted, report export completed).
    Uses a mocked logger provider during local development/testing to prevent sending unsolicited emails.
    """

    async def send_operational_notification(
        self,
        event_name: str,
        organization_id: uuid.UUID,
        payload: Dict[str, Any],
        recipient_email: Optional[str] = None,
    ) -> bool:
        """
        Dispatches read-only operational notification safely.
        """
        logger.info(
            f"[OPERATIONAL NOTIFICATION] Event: {event_name} | Org: {organization_id} | Recipient: {recipient_email or 'SYSTEM_ADMIN'} | Payload: {payload}"
        )
        return True
