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

class SMTPEmailAdapter(EmailProvider):
    """SMTP Email Provider for sending emails to Gmail and external domains."""

    async def send_email(self, recipient_email: str, subject: str, body: str) -> Dict[str, Any]:
        try:
            from app.core.config import settings
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            if settings.SMTP_HOST and settings.SMTP_HOST not in ("localhost", "127.0.0.1") and settings.SMTP_USER:
                msg = MIMEMultipart()
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = recipient_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.starttls()
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

                logger.info(f"[SMTP EMAIL] Sent email to={recipient_email}, subject='{subject}'")
                return {"status": "SENT", "recipient": recipient_email, "provider": "SMTP"}
            else:
                logger.info(f"[EMAIL SERVICE] Simulated email dispatch to={recipient_email}:\nSubject: {subject}\nBody:\n{body}")
                return {"status": "SENT", "recipient": recipient_email, "provider": "DEV_SIMULATOR"}
        except Exception as e:
            logger.error(f"[EMAIL SERVICE ERROR] Failed sending email to={recipient_email}: {e}")
            return {"status": "FAILED", "error": str(e), "recipient": recipient_email}
