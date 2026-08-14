import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.uow import AsyncUnitOfWork
from app.infrastructure.events.idempotency import EventIdempotencyTracker

@pytest.mark.asyncio
async def test_multi_organization_membership_and_header_tampering_protection():
    """
    PROVES SECURITY RULE:
    A user CANNOT gain access to another organization merely by modifying X-Organization-ID.
    Backend authorization MUST verify active membership and return HTTP 403 Forbidden.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register User 1 (Owner of Org A)
        email1 = f"owner1_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": email1, "password": "Password123!", "full_name": "Owner 1"})
        login1 = await client.post("/api/v1/auth/login", json={"email": email1, "password": "Password123!"})
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # User 1 creates Org A
        org_a_resp = await client.post("/api/v1/organizations", json={"name": "Org A", "slug": f"org-a-{uuid.uuid4().hex[:6]}"}, headers=headers1)
        org_a_id = org_a_resp.json()["id"]

        # Register User 2 (Owner of Org B)
        email2 = f"owner2_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": email2, "password": "Password123!", "full_name": "Owner 2"})
        login2 = await client.post("/api/v1/auth/login", json={"email": email2, "password": "Password123!"})
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 2 creates Org B
        org_b_resp = await client.post("/api/v1/organizations", json={"name": "Org B", "slug": f"org-b-{uuid.uuid4().hex[:6]}"}, headers=headers2)
        org_b_id = org_b_resp.json()["id"]

        # Verify User 1 can access Org A
        me_org_a = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token1}", "X-Organization-ID": org_a_id})
        assert me_org_a.status_code == 200

        # CRITICAL TEST: User 1 passes User 2's Org B ID in X-Organization-ID header
        # MUST BE BLOCKED BY AUTHORIZATION MIDDLEWARE WITH HTTP 403 FORBIDDEN
        tampered_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token1}", "X-Organization-ID": org_b_id})
        assert tampered_resp.status_code == 403
        assert "Access Denied" in tampered_resp.json()["detail"]

@pytest.mark.asyncio
async def test_event_idempotency_tracker():
    org_id = uuid.uuid4()
    event_id = uuid.uuid4()
    consumer_id = "resume_processor_worker_1"

    async with AsyncUnitOfWork(organization_id=org_id) as uow:
        # Check initial state
        is_processed = await EventIdempotencyTracker.is_processed(uow.session, event_id, consumer_id)
        assert is_processed is False

        # Mark processed
        await EventIdempotencyTracker.mark_processed(uow.session, event_id, consumer_id)

    # Check updated state
    async with AsyncUnitOfWork(organization_id=org_id) as uow:
        is_processed_after = await EventIdempotencyTracker.is_processed(uow.session, event_id, consumer_id)
        assert is_processed_after is True
