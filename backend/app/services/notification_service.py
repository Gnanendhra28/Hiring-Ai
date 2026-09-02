import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class NotificationTypeEnum:
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    INTERVIEW_REMINDER = "INTERVIEW_REMINDER"
    CANDIDATE_APPLIED = "CANDIDATE_APPLIED"
    CANDIDATE_SHORTLISTED = "CANDIDATE_SHORTLISTED"
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
    SCORECARD_READY = "SCORECARD_READY"
    OFFER_READY = "OFFER_READY"
    OFFER_APPROVED = "OFFER_APPROVED"
    OFFER_ACCEPTED = "OFFER_ACCEPTED"


class OperationalNotificationService:
    """
    Operational Notification & Collaboration Communications Service.
    Handles in-app notifications, candidate-safe transactional emails,
    recruiter collaboration alerts, and idempotent event delivery.
    """

    def __init__(self):
        self._delivered_event_ids = set()

    async def send_operational_notification(
        self,
        event_name: str,
        organization_id: uuid.UUID,
        payload: Dict[str, Any],
        recipient_email: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> bool:
        """
        Dispatches read-only operational notification safely with idempotency.
        """
        if idempotency_key:
            if idempotency_key in self._delivered_event_ids:
                logger.info(f"[IDEMPOTENT EVENT] Event {event_name} with key {idempotency_key} already processed. Skipping.")
                return True
            self._delivered_event_ids.add(idempotency_key)

        logger.info(
            f"[OPERATIONAL NOTIFICATION] Event: {event_name} | Org: {organization_id} | Recipient: {recipient_email or 'SYSTEM_ADMIN'} | Payload: {payload}"
        )
        return True

    async def dispatch_candidate_email(
        self,
        recipient_email: str,
        template_name: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Dispatches candidate-safe email notification.
        CRITICAL PRIVACY CONTROL:
        Strips internal recruiter scores, internal notes, AI reasoning, and private rubrics.
        """
        # Strict privacy filtering
        safe_context = {
            "candidate_name": context.get("candidate_name", "Candidate"),
            "job_title": context.get("job_title", "Position"),
            "company_name": context.get("company_name", "Hiring Team"),
            "interview_url": context.get("interview_url"),
            "scheduled_time_utc": context.get("scheduled_time_utc"),
        }

        logger.info(f"[CANDIDATE EMAIL SENT] Template: {template_name} | To: {recipient_email} | Context: {safe_context}")
        return {
            "status": "SENT",
            "recipient": recipient_email,
            "template": template_name,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

    async def dispatch_recruiter_alert(
        self,
        organization_id: uuid.UUID,
        recruiter_email: str,
        alert_title: str,
        message: str,
        resource_id: str,
    ) -> Dict[str, Any]:
        """
        Dispatches in-app and email alert to authorized recruiter.
        """
        logger.info(
            f"[RECRUITER ALERT] Org: {organization_id} | To: {recruiter_email} | Title: {alert_title} | Res: {resource_id}"
        )
        return {
            "status": "DELIVERED",
            "organization_id": str(organization_id),
            "recipient": recruiter_email,
            "title": alert_title,
            "message": message,
            "resource_id": resource_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
