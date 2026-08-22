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
        from app.core.config import settings
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        has_smtp = (
            settings.SMTP_HOST
            and settings.SMTP_HOST not in ("localhost", "127.0.0.1")
            and settings.SMTP_USER
        )

        if has_smtp:
            try:
                msg = MIMEMultipart()
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = recipient_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                port = settings.SMTP_PORT or 587
                clean_password = (settings.SMTP_PASSWORD or "").replace(" ", "").strip()

                with smtplib.SMTP(settings.SMTP_HOST, port, timeout=10) as server:
                    if settings.SMTP_USER and clean_password:
                        server.starttls()
                        server.login(settings.SMTP_USER, clean_password)
                    server.send_message(msg)

                logger.info(f"[SMTP EMAIL] Successfully delivered real email to={recipient_email}")
                return {"status": "SENT", "recipient": recipient_email, "provider": "SMTP"}
            except Exception as e:
                logger.error(f"[SMTP EMAIL ERROR] Failed sending real email via {settings.SMTP_HOST}: {e}")
                if settings.APP_ENV == "development":
                    logger.info(f"[DEV FALLBACK] Falling back to Dev Email Simulator for local testing:\nSubject: {subject}\nBody:\n{body}")
                    return {"status": "SIMULATED", "recipient": recipient_email, "provider": "DEV_SIMULATOR", "error": str(e)}
                return {"status": "FAILED", "error": str(e), "recipient": recipient_email}
        else:
            logger.info(f"[DEV EMAIL SIMULATOR] Email to={recipient_email}:\nSubject: {subject}\nBody:\n{body}")
            return {"status": "SIMULATED", "recipient": recipient_email, "provider": "DEV_SIMULATOR"}
