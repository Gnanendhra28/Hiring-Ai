from abc import ABC, abstractmethod
from typing import Any, Dict
from app.core.logging import logger

class EmailProvider(ABC):
    """Abstract Base Class for Email Providers (Mailpit for dev, SMTP/Azure Communications for prod)."""

    @abstractmethod
    async def send_email(self, recipient_email: str, subject: str, body: str) -> Dict[str, Any]:
        pass

class MailpitEmailAdapter(EmailProvider):
    """Local Development & Testing Email Adapter."""

    async def send_email(self, recipient_email: str, subject: str, body: str) -> Dict[str, Any]:
        logger.info(f"[MAILPIT DEV] Sent email to={recipient_email}, subject='{subject}'")
        return {
            "status": "SENT",
            "recipient": recipient_email,
            "provider": "MAILPIT",
        }
