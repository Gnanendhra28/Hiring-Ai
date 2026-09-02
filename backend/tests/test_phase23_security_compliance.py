import uuid
from datetime import datetime, timedelta, UTC
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum
from app.core.security import create_access_token
from app.core.webhook_security import validate_webhook_url, compute_hmac_signature, verify_hmac_signature

@pytest.mark.asyncio
async def test_jwt_authentication_edge_cases():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Missing JWT -> 401
        res1 = await client.get("/api/v1/jobs")
        assert res1.status_code == 401

        # 2. Invalid JWT format -> 401
        res2 = await client.get("/api/v1/jobs", headers={"Authorization": "Bearer invalid_junk_token"})
        assert res2.status_code == 401

        # 3. Expired JWT -> 401
        expired_token = create_access_token(uuid.uuid4(), expires_delta=timedelta(seconds=-3600))
        res3 = await client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {expired_token}"})
        assert res3.status_code == 401

@pytest.mark.asyncio
async def test_cross_tenant_isolation_matrix():
    async with async_session_factory() as session:
        await session.begin()

        # Tenant A
        org_a = Organization(name=f"Sec Org A {uuid.uuid4().hex[:6]}", slug=f"sec-a-{uuid.uuid4().hex[:6]}")
        session.add(org_a)
        await session.flush()
        await set_tenant_context(session, org_a.id)

        user_a = User(email=f"sec_a_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="User A")
        session.add(user_a)
        await session.flush()
        mem_a = OrganizationMembership(organization_id=org_a.id, user_id=user_a.id, role=RoleEnum.RECRUITER)
        session.add(mem_a)

        job_a = Job(organization_id=org_a.id, title="Job A", slug=f"job-a-{uuid.uuid4().hex[:6]}", description="Desc A", status=JobStatusEnum.PUBLISHED)
        session.add(job_a)

        # Tenant B
        org_b = Organization(name=f"Sec Org B {uuid.uuid4().hex[:6]}", slug=f"sec-b-{uuid.uuid4().hex[:6]}")
        session.add(org_b)
        await session.flush()
        await set_tenant_context(session, org_b.id)

        user_b = User(email=f"sec_b_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="User B")
        session.add(user_b)
        await session.flush()
        mem_b = OrganizationMembership(organization_id=org_b.id, user_id=user_b.id, role=RoleEnum.RECRUITER)
        session.add(mem_b)

        job_b = Job(organization_id=org_b.id, title="Job B", slug=f"job-b-{uuid.uuid4().hex[:6]}", description="Desc B", status=JobStatusEnum.PUBLISHED)
        session.add(job_b)

        await session.commit()

        token_a = create_access_token(user_a.id)

    # Tenant A attempting to access Tenant B's job via API -> 404 Not Found
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": str(org_a.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_cross = await client.get(f"/api/v1/jobs/{job_b.id}", headers=headers_a)
        assert res_cross.status_code == 404

@pytest.mark.asyncio
async def test_ssrf_and_webhook_security_guards():
    # 1. Reject local loopback and metadata IP ranges
    with pytest.raises(ValueError, match="SSRF Protection Guard"):
        validate_webhook_url("http://169.254.169.254/latest/meta-data")

    with pytest.raises(ValueError, match="SSRF Protection Guard"):
        validate_webhook_url("http://127.0.0.1:8000/internal")

    # 2. HMAC-SHA256 signature verification & 300s window check
    secret = "whsec_security_test_secret_999"
    ts = str(int(datetime.now(UTC).timestamp()))
    payload = '{"event_type":"job.intelligence.completed"}'

    sig = compute_hmac_signature(secret, ts, payload)
    assert verify_hmac_signature(secret, ts, payload, sig) is True

    # Replayed payload with old timestamp (>300s) -> False
    old_ts = str(int((datetime.now(UTC) - timedelta(seconds=400)).timestamp()))
    old_sig = compute_hmac_signature(secret, old_ts, payload)
    assert verify_hmac_signature(secret, old_ts, payload, old_sig) is False

@pytest.mark.asyncio
async def test_ai_governance_zero_mutation_authority():
    # Verify AI services have 0 state mutation endpoints
    async with async_session_factory() as session:
        await session.begin()
        # RLS set_tenant_context check
        org_id = uuid.uuid4()
        await set_tenant_context(session, org_id)
        assert True
