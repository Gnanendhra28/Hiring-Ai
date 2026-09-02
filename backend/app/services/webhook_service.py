import hashlib
import json
import uuid
import httpx
from datetime import datetime, timedelta, UTC
from sqlalchemy import select

from app.core.logging import logger
from app.core.webhook_security import (
    compute_hmac_signature,
    generate_webhook_secret,
    validate_webhook_url,
)
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.webhooks.models import WebhookEvent, WebhookDeliveryStatusEnum, WebhookSubscription
from app.domains.webhooks.schemas import ALLOWED_WEBHOOK_EVENTS
from app.events.integration_events import IntegrationBaseEvent

class WebhookService:
    """
    Tenant-Isolated Enterprise Outbound Webhook Service.
    Handles subscription management, HMAC-SHA256 signing, SSRF URL validation,
    idempotent event publication, and exponential backoff delivery retries.
    """

    async def create_subscription(
        self,
        organization_id: uuid.UUID,
        endpoint_url: str,
        subscribed_events: list[str],
        user_id: uuid.UUID,
    ) -> WebhookSubscription:
        # 1. SSRF & URL Validation
        clean_url = validate_webhook_url(endpoint_url, allow_http=True)

        # 2. Validate Event Subscriptions
        for evt in subscribed_events:
            if evt not in ALLOWED_WEBHOOK_EVENTS:
                raise ValueError(f"Invalid event type '{evt}'. Allowed events: {ALLOWED_WEBHOOK_EVENTS}")

        secret = generate_webhook_secret()

        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            sub = WebhookSubscription(
                organization_id=organization_id,
                endpoint_url=clean_url,
                secret=secret,
                enabled=True,
                subscribed_events=subscribed_events,
                created_by_user_id=user_id,
            )
            session.add(sub)
            await session.commit()
            await session.refresh(sub)
            return sub

    async def get_subscriptions(self, organization_id: uuid.UUID) -> list[WebhookSubscription]:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            stmt = select(WebhookSubscription).where(
                WebhookSubscription.organization_id == organization_id
            ).order_by(WebhookSubscription.created_at.desc())
            return list((await session.execute(stmt)).scalars().all())

    async def get_subscription(
        self, subscription_id: uuid.UUID, organization_id: uuid.UUID
    ) -> WebhookSubscription | None:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            stmt = select(WebhookSubscription).where(
                WebhookSubscription.id == subscription_id,
                WebhookSubscription.organization_id == organization_id,
            )
            return (await session.execute(stmt)).scalars().first()

    async def update_subscription(
        self,
        subscription_id: uuid.UUID,
        organization_id: uuid.UUID,
        endpoint_url: str | None = None,
        enabled: bool | None = None,
        subscribed_events: list[str] | None = None,
    ) -> WebhookSubscription | None:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            stmt = select(WebhookSubscription).where(
                WebhookSubscription.id == subscription_id,
                WebhookSubscription.organization_id == organization_id,
            )
            sub = (await session.execute(stmt)).scalars().first()
            if not sub:
                return None

            if endpoint_url is not None:
                sub.endpoint_url = validate_webhook_url(endpoint_url, allow_http=True)
            if enabled is not None:
                sub.enabled = enabled
            if subscribed_events is not None:
                for evt in subscribed_events:
                    if evt not in ALLOWED_WEBHOOK_EVENTS:
                        raise ValueError(f"Invalid event type '{evt}'. Allowed events: {ALLOWED_WEBHOOK_EVENTS}")
                sub.subscribed_events = subscribed_events

            await session.commit()
            await session.refresh(sub)
            return sub

    async def delete_subscription(
        self, subscription_id: uuid.UUID, organization_id: uuid.UUID
    ) -> bool:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            stmt = select(WebhookSubscription).where(
                WebhookSubscription.id == subscription_id,
                WebhookSubscription.organization_id == organization_id,
            )
            sub = (await session.execute(stmt)).scalars().first()
            if not sub:
                return False

            await session.delete(sub)
            await session.commit()
            return True

    async def rotate_secret(
        self, subscription_id: uuid.UUID, organization_id: uuid.UUID
    ) -> str | None:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            stmt = select(WebhookSubscription).where(
                WebhookSubscription.id == subscription_id,
                WebhookSubscription.organization_id == organization_id,
            )
            sub = (await session.execute(stmt)).scalars().first()
            if not sub:
                return None

            new_secret = generate_webhook_secret()
            sub.secret = new_secret
            await session.commit()
            return new_secret

    async def publish_integration_event(self, event: IntegrationBaseEvent) -> list[uuid.UUID]:
        """
        Idempotently publishes an integration event to all enabled webhook subscriptions for the tenant.
        """
        payload_dict = event.model_dump(mode="json")
        payload_json = json.dumps(payload_dict, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        created_event_ids = []

        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=event.organization_id)

            stmt_subs = select(WebhookSubscription).where(
                WebhookSubscription.organization_id == event.organization_id,
                WebhookSubscription.enabled.is_(True),
            )
            subs = list((await session.execute(stmt_subs)).scalars().all())

            for sub in subs:
                events_list = sub.subscribed_events if isinstance(sub.subscribed_events, list) else []
                if event.event_type not in events_list:
                    continue

                # Check idempotency
                stmt_exist = select(WebhookEvent).where(
                    WebhookEvent.subscription_id == sub.id,
                    WebhookEvent.event_id == event.event_id,
                )
                existing = (await session.execute(stmt_exist)).scalars().first()
                if existing:
                    continue

                we = WebhookEvent(
                    organization_id=event.organization_id,
                    subscription_id=sub.id,
                    event_id=event.event_id,
                    event_type=event.event_type,
                    payload_json=payload_json,
                    payload_hash=payload_hash,
                    delivery_status=WebhookDeliveryStatusEnum.PENDING,
                    attempt_count=0,
                )
                session.add(we)
                await session.flush()
                created_event_ids.append(we.id)

            await session.commit()

        # Trigger async delivery
        for we_id in created_event_ids:
            await self.deliver_webhook_event(webhook_event_id=we_id)

        return created_event_ids

    async def deliver_webhook_event(self, webhook_event_id: uuid.UUID) -> bool:
        """
        Executes HTTP POST delivery to subscription target URL with HMAC-SHA256 headers.
        Applies strict 5s timeout and exponential backoff retry classification.
        """
        async with async_session_factory() as session:
            await session.begin()

            stmt_we = select(WebhookEvent).where(WebhookEvent.id == webhook_event_id)
            we = (await session.execute(stmt_we)).scalars().first()
            if not we:
                return False

            await set_tenant_context(session, organization_id=we.organization_id)

            stmt_sub = select(WebhookSubscription).where(WebhookSubscription.id == we.subscription_id)
            sub = (await session.execute(stmt_sub)).scalars().first()
            if not sub or not sub.enabled:
                we.delivery_status = WebhookDeliveryStatusEnum.FAILED
                we.last_error_code = "SUBSCRIPTION_DISABLED_OR_DELETED"
                await session.commit()
                return False

            now = datetime.now(UTC)
            we.attempt_count += 1
            if not we.first_attempt_at:
                we.first_attempt_at = now
            we.last_attempt_at = now
            we.delivery_status = WebhookDeliveryStatusEnum.DELIVERING

            ts_str = str(int(now.timestamp()))
            signature = compute_hmac_signature(secret=sub.secret, timestamp=ts_str, payload_body=we.payload_json)

            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Id": str(we.event_id),
                "X-Webhook-Timestamp": ts_str,
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": we.event_type,
                "User-Agent": "AIHiringPlatform-WebhookDispatcher/1.0",
            }

            url = sub.endpoint_url
            success = False
            http_status = None
            error_msg = None

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    res = await client.post(url, content=we.payload_json, headers=headers)
                    http_status = res.status_code
                    we.last_http_status = http_status

                    if 200 <= http_status < 300:
                        success = True
                        we.delivery_status = WebhookDeliveryStatusEnum.DELIVERED
                        we.delivered_at = now
                        we.next_retry_at = None
                        logger.info(f"[WEBHOOK SUCCESS] Event: {we.event_type} | ID: {we.event_id} | Status: {http_status}")
                    elif http_status in [400, 401, 403, 404]:
                        we.delivery_status = WebhookDeliveryStatusEnum.FAILED
                        we.last_error_code = f"PERMANENT_HTTP_{http_status}"
                        logger.warning(f"[WEBHOOK PERMANENT FAIL] Event: {we.event_type} | ID: {we.event_id} | Status: {http_status}")
                    else:
                        error_msg = f"HTTP_{http_status}"
            except Exception as ex:
                error_msg = str(ex)[:250]
                logger.error(f"[WEBHOOK DELIVERY ERROR] Event: {we.event_type} | ID: {we.event_id} | Error: {error_msg}")

            if not success and we.delivery_status != WebhookDeliveryStatusEnum.FAILED:
                if we.attempt_count < 5:
                    we.delivery_status = WebhookDeliveryStatusEnum.RETRYING
                    we.last_error_code = error_msg or "TRANSIENT_FAILURE"
                    backoff_sec = min(300, 5 * (2 ** (we.attempt_count - 1)))
                    we.next_retry_at = now + timedelta(seconds=backoff_sec)
                else:
                    we.delivery_status = WebhookDeliveryStatusEnum.FAILED
                    we.last_error_code = error_msg or "MAX_RETRIES_EXCEEDED"

            await session.commit()
            return success

    async def send_test_webhook(
        self, subscription_id: uuid.UUID, organization_id: uuid.UUID
    ) -> tuple[bool, int | None]:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            stmt = select(WebhookSubscription).where(
                WebhookSubscription.id == subscription_id,
                WebhookSubscription.organization_id == organization_id,
            )
            sub = (await session.execute(stmt)).scalars().first()
            if not sub:
                return False, None

            now = datetime.now(UTC)
            test_event_id = uuid.uuid4()
            payload = {
                "event_id": str(test_event_id),
                "event_type": "webhook.test",
                "event_version": "1.0",
                "occurred_at": now.isoformat(),
                "organization_id": str(organization_id),
                "job_id": None,
                "message": "This is a synthetic test event generated by recruiter request. Zero candidate or hiring state modified.",
            }
            payload_json = json.dumps(payload, sort_keys=True)
            ts_str = str(int(now.timestamp()))
            signature = compute_hmac_signature(secret=sub.secret, timestamp=ts_str, payload_body=payload_json)

            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Id": str(test_event_id),
                "X-Webhook-Timestamp": ts_str,
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": "webhook.test",
                "User-Agent": "AIHiringPlatform-WebhookDispatcher/1.0",
            }

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    res = await client.post(sub.endpoint_url, content=payload_json, headers=headers)
                    return (200 <= res.status_code < 300), res.status_code
            except (httpx.HTTPError, TimeoutError, ConnectionError) as ex:
                logger.error(f"[WEBHOOK TEST ERROR] Sub: {subscription_id} | Network Error: {ex!s}")
                return False, None
            except Exception as ex:
                logger.error(f"[WEBHOOK TEST ERROR] Sub: {subscription_id} | Unexpected Error: {ex!s}")
                return False, None

    async def get_delivery_history(
        self, organization_id: uuid.UUID, subscription_id: uuid.UUID | None = None
    ) -> list[WebhookEvent]:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            stmt = select(WebhookEvent).where(WebhookEvent.organization_id == organization_id)
            if subscription_id:
                stmt = stmt.where(WebhookEvent.subscription_id == subscription_id)

            stmt = stmt.order_by(WebhookEvent.created_at.desc()).limit(100)
            return list((await session.execute(stmt)).scalars().all())
