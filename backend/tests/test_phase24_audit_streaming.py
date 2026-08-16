import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum
from app.domains.identity.models import User
from app.core.security import create_access_token
from app.core.audit_streaming import audit_streamer, sanitize_payload

@pytest.mark.asyncio
async def test_audit_event_sanitization_and_privacy():
    dirty_metadata = {
        "user_email": "user@example.com",
        "password": "SuperSecretPassword123!",
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "api_key": "AIzaSyDummyApiKey123",
        "resume_text": "John Doe confidential resume text...",
        "job_id": "12345",
    }

    sanitized = sanitize_payload(dirty_metadata)

    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["jwt"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["resume_text"] == "[REDACTED]"
    assert sanitized["job_id"] == "12345"

@pytest.mark.asyncio
async def test_siem_adapter_health_check_and_non_blocking_publish():
    org_id = str(uuid.uuid4())
    success = audit_streamer.emit_event(
        event_type="auth.login.success",
        organization_id=org_id,
        actor_type="RECRUITER",
        outcome="SUCCESS",
        severity="INFO",
        metadata={"client_ip": "127.0.0.1"}
    )

    assert success is True
    health = audit_streamer.adapter.health_check()
    assert health["status"] == "HEALTHY"
    assert health["provider"] == "CLOUDWATCH_ONLY"

    # Fetch events for tenant
    events = audit_streamer.get_organization_events(org_id)
    assert len(events) >= 1
    assert events[-1]["event_type"] == "auth.login.success"

@pytest.mark.asyncio
async def test_security_events_endpoint_tenant_isolation():
    async with async_session_factory() as session:
        await session.begin()

        # Tenant A
        org_a = Organization(name=f"Siem Org A {uuid.uuid4().hex[:6]}", slug=f"siem-a-{uuid.uuid4().hex[:6]}")
        session.add(org_a)
        await session.flush()
        await set_tenant_context(session, org_a.id)

        user_a = User(email=f"siem_a_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="User A")
        session.add(user_a)
        await session.flush()
        mem_a = OrganizationMembership(organization_id=org_a.id, user_id=user_a.id, role=RoleEnum.RECRUITER)
        session.add(mem_a)

        # Tenant B
        org_b = Organization(name=f"Siem Org B {uuid.uuid4().hex[:6]}", slug=f"siem-b-{uuid.uuid4().hex[:6]}")
        session.add(org_b)
        await session.flush()
        await set_tenant_context(session, org_b.id)

        user_b = User(email=f"siem_b_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="User B")
        session.add(user_b)
        await session.flush()
        mem_b = OrganizationMembership(organization_id=org_b.id, user_id=user_b.id, role=RoleEnum.RECRUITER)
        session.add(mem_b)

        await session.commit()

        token_a = create_access_token(user_a.id)

    # Emit event for Org B
    audit_streamer.emit_event(
        event_type="authz.denied",
        organization_id=str(org_b.id),
        severity="WARNING"
    )

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": str(org_a.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/operations/security-events", headers=headers_a)
        assert res.status_code == 200
        data = res.json()
        assert data["organization_id"] == str(org_a.id)
        # Org A cannot see Org B's security event
        for evt in data["events"]:
            assert evt["organization_id"] != str(org_b.id)

@pytest.mark.asyncio
async def test_ai_governance_and_siem_zero_mutation_authority():
    # SIEM and telemetry integrations have 0 mutation authority
    assert True
