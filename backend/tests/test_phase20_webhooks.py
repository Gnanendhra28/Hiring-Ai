import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import async_session_factory, engine
from sqlalchemy import text
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum
from app.domains.identity.models import User
from app.domains.webhooks.models import WebhookSubscription, WebhookEvent, WebhookDeliveryStatusEnum
from app.domains.webhooks.schemas import ALLOWED_WEBHOOK_EVENTS
from app.core.security import create_access_token
from app.core.webhook_security import (
    compute_hmac_signature,
    generate_webhook_secret,
    validate_webhook_url,
    verify_hmac_signature,
)
from app.events.integration_events import CandidateHiredEvent, OfferAcceptedEvent, OfferCreatedEvent, JobIntelligenceCompletedEvent
from app.services.webhook_service import WebhookService

async def ensure_webhook_tables():
    async with engine.begin() as conn:
        await conn.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'webhookdeliverystatusenum') THEN CREATE TYPE webhookdeliverystatusenum AS ENUM ('PENDING', 'DELIVERING', 'DELIVERED', 'RETRYING', 'FAILED'); END IF; END $$;"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_subscriptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                endpoint_url VARCHAR(2048) NOT NULL,
                secret VARCHAR(255) NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                subscribed_events JSONB NOT NULL DEFAULT '[]',
                created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                subscription_id UUID NOT NULL REFERENCES webhook_subscriptions(id) ON DELETE CASCADE,
                event_id UUID NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash VARCHAR(64) NOT NULL,
                delivery_status webhookdeliverystatusenum NOT NULL DEFAULT 'PENDING',
                attempt_count INT NOT NULL DEFAULT 0,
                first_attempt_at TIMESTAMPTZ,
                last_attempt_at TIMESTAMPTZ,
                next_retry_at TIMESTAMPTZ,
                delivered_at TIMESTAMPTZ,
                last_http_status INT,
                last_error_code VARCHAR(255),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

@pytest.mark.asyncio
async def test_webhook_security_and_ssrf_protection():
    # 1. Valid URLs
    assert validate_webhook_url("https://api.partner.com/webhooks", allow_http=False) == "https://api.partner.com/webhooks"
    assert validate_webhook_url("http://localhost:8000/test", allow_http=True) == "http://localhost:8000/test"

    # 2. SSRF Protection: Private & Metadata IP Rejection
    with pytest.raises(ValueError, match="SSRF Protection Guard"):
        validate_webhook_url("http://169.254.169.254/latest/meta-data")

    with pytest.raises(ValueError, match="SSRF Protection Guard"):
        validate_webhook_url("http://10.0.0.1/webhook")

    with pytest.raises(ValueError, match="SSRF Protection Guard"):
        validate_webhook_url("http://192.168.1.1/webhook")

    # 3. Invalid Protocol Rejection
    with pytest.raises(ValueError, match="Invalid URL protocol"):
        validate_webhook_url("file:///etc/passwd")

    with pytest.raises(ValueError, match="Invalid URL protocol"):
        validate_webhook_url("ftp://server/webhook")

@pytest.mark.asyncio
async def test_hmac_sha256_signing_and_replay_protection():
    secret = "whsec_test_secret_123456789"
    ts = str(int(datetime.now(timezone.utc).timestamp()))
    payload = '{"event":"candidate.hired","job_id":"123"}'

    sig = compute_hmac_signature(secret=secret, timestamp=ts, payload_body=payload)
    assert sig.startswith("sha256=")

    # Verification PASS
    assert verify_hmac_signature(secret=secret, timestamp=ts, payload_body=payload, signature_header=sig) is True

    # Modified Payload -> Verification FAIL
    assert verify_hmac_signature(secret=secret, timestamp=ts, payload_body='{"event":"candidate.hired","job_id":"999"}', signature_header=sig) is False

    # Modified Secret -> Verification FAIL
    assert verify_hmac_signature(secret="whsec_wrong_secret", timestamp=ts, payload_body=payload, signature_header=sig) is False

    # Expired Timestamp (> 300s) -> Verification FAIL
    old_ts = str(int((datetime.now(timezone.utc) - timedelta(seconds=400)).timestamp()))
    old_sig = compute_hmac_signature(secret=secret, timestamp=old_ts, payload_body=payload)
    assert verify_hmac_signature(secret=secret, timestamp=old_ts, payload_body=payload, signature_header=old_sig) is False

@pytest.mark.asyncio
async def test_webhook_subscription_crud_and_secret_non_disclosure():
    await ensure_webhook_tables()

    async with async_session_factory() as session:
        await session.begin()

        slug = f"org-wh-{uuid.uuid4().hex[:6]}"
        org = Organization(name=f"Webhook Org {uuid.uuid4().hex[:6]}", slug=slug)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        user = User(email=f"wh_admin_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="Webhook Admin")
        session.add(user)
        await session.flush()

        mem = OrganizationMembership(organization_id=org.id, user_id=user.id, role=RoleEnum.ORGANIZATION_ADMIN)
        session.add(mem)
        await session.commit()

        token = create_access_token(user.id)

    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Webhook Subscription (Secret exposed ONCE)
        res_create = await client.post(
            "/api/v1/webhooks/subscriptions",
            json={
                "endpoint_url": "https://example.com/webhook",
                "subscribed_events": ["offer.accepted", "candidate.hired"],
            },
            headers=headers,
        )
        assert res_create.status_code == 201
        data_create = res_create.json()
        sub_id = data_create["id"]
        assert "secret" in data_create
        assert data_create["secret"].startswith("whsec_")

        # 2. List Webhook Subscriptions (Secret EXCLUDED)
        res_list = await client.get("/api/v1/webhooks/subscriptions", headers=headers)
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert len(data_list) == 1
        assert "secret" not in data_list[0]

        # 3. Get Single Webhook Subscription (Secret EXCLUDED)
        res_get = await client.get(f"/api/v1/webhooks/subscriptions/{sub_id}", headers=headers)
        assert res_get.status_code == 200
        assert "secret" not in res_get.json()

        # 4. Rotate Secret (New Secret exposed ONCE)
        res_rot = await client.post(f"/api/v1/webhooks/subscriptions/{sub_id}/rotate-secret", headers=headers)
        assert res_rot.status_code == 200
        assert "new_secret" in res_rot.json()

        # 5. Delete Webhook Subscription
        res_del = await client.delete(f"/api/v1/webhooks/subscriptions/{sub_id}", headers=headers)
        assert res_del.status_code == 204

@pytest.mark.asyncio
async def test_webhook_event_publication_idempotency_and_governance():
    await ensure_webhook_tables()

    service = WebhookService()

    async with async_session_factory() as session:
        await session.begin()

        slug = f"org-evt-{uuid.uuid4().hex[:6]}"
        org = Organization(name=f"Event Org {uuid.uuid4().hex[:6]}", slug=slug)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        user = User(email=f"evt_rec_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="Recruiter")
        session.add(user)
        await session.flush()

        mem = OrganizationMembership(organization_id=org.id, user_id=user.id, role=RoleEnum.RECRUITER)
        session.add(mem)
        await session.commit()

    # Create active subscription
    sub = await service.create_subscription(
        organization_id=org.id,
        endpoint_url="http://testserver/webhook-mock",
        subscribed_events=["candidate.hired"],
        user_id=user.id,
    )

    evt = CandidateHiredEvent(
        event_id=uuid.uuid4(),
        organization_id=org.id,
        job_id=uuid.uuid4(),
        application_id=uuid.uuid4(),
        candidate_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        time_to_fill_days=5.0,
    )

    # 1. Publish Event
    created_ids1 = await service.publish_integration_event(evt)
    assert len(created_ids1) == 1

    # 2. Idempotency: Duplicate publication emits 0 new delivery records
    created_ids2 = await service.publish_integration_event(evt)
    assert len(created_ids2) == 0

    # 3. Payload Contract & Privacy Verification
    history = await service.get_delivery_history(organization_id=org.id, subscription_id=sub.id)
    assert len(history) == 1
    we = history[0]
    payload = we.payload_json
    assert "password" not in payload
    assert "jwt" not in payload
    assert "raw_resume_text" not in payload
    assert str(evt.job_id) in payload
