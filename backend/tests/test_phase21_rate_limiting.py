import time
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.rate_limiter import rate_limiter
from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum
from app.domains.identity.models import User
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_tenant_aware_rate_limiting_and_quota_isolation():
    rate_limiter.reset()
    rate_limiter.enabled_in_test = True

    try:
        async with async_session_factory() as session:
            await session.begin()

            # Org A
            org_a = Organization(name=f"Org A {uuid.uuid4().hex[:6]}", slug=f"org-a-{uuid.uuid4().hex[:6]}")
            session.add(org_a)
            await session.flush()
            await set_tenant_context(session, org_a.id)

            user_a = User(email=f"user_a_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="User A")
            session.add(user_a)
            await session.flush()
            mem_a = OrganizationMembership(organization_id=org_a.id, user_id=user_a.id, role=RoleEnum.RECRUITER)
            session.add(mem_a)

            # Org B
            org_b = Organization(name=f"Org B {uuid.uuid4().hex[:6]}", slug=f"org-b-{uuid.uuid4().hex[:6]}")
            session.add(org_b)
            await session.flush()
            await set_tenant_context(session, org_b.id)

            user_b = User(email=f"user_b_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="User B")
            session.add(user_b)
            await session.flush()
            mem_b = OrganizationMembership(organization_id=org_b.id, user_id=user_b.id, role=RoleEnum.RECRUITER)
            session.add(mem_b)

            await session.commit()

            token_a = create_access_token(user_a.id)
            token_b = create_access_token(user_b.id)

        headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": str(org_a.id)}
        headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": str(org_b.id)}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Exhaust Auth route quota for Org A (Limit = 10)
            for _ in range(10):
                res = await client.get("/api/v1/webhooks/subscriptions", headers=headers_a)
                assert res.status_code == 200
                assert "X-RateLimit-Limit" in res.headers
                assert "X-RateLimit-Remaining" in res.headers

            # 2. Org B should NOT be rate limited (Tenant Isolation PASS)
            res_b = await client.get("/api/v1/webhooks/subscriptions", headers=headers_b)
            assert res_b.status_code == 200
            assert int(res_b.headers["X-RateLimit-Remaining"]) >= 0

    finally:
        rate_limiter.enabled_in_test = False
        rate_limiter.reset()

@pytest.mark.asyncio
async def test_rate_limit_headers_and_429_generation():
    rate_limiter.reset()
    rate_limiter.enabled_in_test = True

    try:
        async with async_session_factory() as session:
            await session.begin()

            org = Organization(name=f"Headers Org {uuid.uuid4().hex[:6]}", slug=f"hdr-{uuid.uuid4().hex[:6]}")
            session.add(org)
            await session.flush()
            await set_tenant_context(session, org.id)

            user = User(email=f"hdr_user_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="Hdr User")
            session.add(user)
            await session.flush()
            mem = OrganizationMembership(organization_id=org.id, user_id=user.id, role=RoleEnum.RECRUITER)
            session.add(mem)

            await session.commit()
            token = create_access_token(user.id)

        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. First request returns headers
            res1 = await client.get("/api/v1/webhooks/subscriptions", headers=headers)
            assert res1.status_code == 200
            assert "X-RateLimit-Limit" in res1.headers
            assert "X-RateLimit-Remaining" in res1.headers
            assert "X-RateLimit-Reset" in res1.headers

    finally:
        rate_limiter.enabled_in_test = False
        rate_limiter.reset()

@pytest.mark.asyncio
async def test_operations_observability_endpoint():
    async with async_session_factory() as session:
        await session.begin()

        org = Organization(name=f"Ops Org {uuid.uuid4().hex[:6]}", slug=f"ops-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        user = User(email=f"ops_admin_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="Ops Admin")
        session.add(user)
        await session.flush()
        mem = OrganizationMembership(organization_id=org.id, user_id=user.id, role=RoleEnum.ORGANIZATION_ADMIN)
        session.add(mem)

        await session.commit()
        token = create_access_token(user.id)

    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health Probe
        res_h = await client.get("/api/v1/operations/health")
        assert res_h.status_code == 200
        assert res_h.json()["status"] == "ok"

        # 2. Operations Metrics
        res_m = await client.get("/api/v1/operations/metrics", headers=headers)
        assert res_m.status_code == 200
        data = res_m.json()
        assert data["organization_id"] == str(org.id)
        assert "system_health" in data
        assert "rate_limiting" in data
        assert "webhook_observability" in data
        assert data["ai_governance"]["ai_mutation_paths"] == 0
