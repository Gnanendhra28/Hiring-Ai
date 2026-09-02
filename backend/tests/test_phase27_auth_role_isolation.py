import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.domains.identity.models import User
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum, MembershipStatusEnum

@pytest.mark.asyncio
async def test_missing_jwt_returns_401():
    """Anonymous request to protected backend endpoints returns 401 Unauthorized."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

        resp2 = await client.get("/api/v1/operations/metrics")
        assert resp2.status_code == 401

@pytest.mark.asyncio
async def test_invalid_jwt_returns_401():
    """Invalid, forged, or malformed JWT returns 401 Unauthorized."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_as_access_token():
    """Guard against passing a JWT refresh token to an endpoint expecting an access token."""
    async with async_session_factory() as session:
        user = User(
            email=f"user_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=hash_password("Password123!"),
            full_name="Test User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    refresh_token = create_refresh_token(user_id=user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert resp.status_code == 401
        assert "Access token required" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_candidate_cannot_access_recruiter_endpoints():
    """Candidate role attempting to invoke Recruiter APIs returns HTTP 403 Forbidden."""
    async with async_session_factory() as session:
        org = Organization(name="Test Org", slug=f"org-{uuid.uuid4().hex[:8]}")
        cand = User(
            email=f"cand_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=hash_password("Password123!"),
            full_name="Candidate User",
        )
        session.add_all([org, cand])
        await session.commit()
        await session.refresh(org)
        await session.refresh(cand)

        await set_tenant_context(session, org.id)
        mem = OrganizationMembership(
            organization_id=org.id,
            user_id=cand.id,
            role=RoleEnum.CANDIDATE,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(mem)
        await session.commit()

    access_token = create_access_token(user_id=cand.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/operations/metrics",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Organization-ID": str(org.id),
            }
        )
        assert resp.status_code == 403

@pytest.mark.asyncio
async def test_recruiter_cannot_access_unjoined_organization_tenant():
    """Recruiter attempting to access an organization they are NOT a member of returns HTTP 403."""
    async with async_session_factory() as session:
        org_unjoined = Organization(name="Unjoined Org", slug=f"org-{uuid.uuid4().hex[:8]}")
        recruiter = User(
            email=f"recruiter_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=hash_password("Password123!"),
            full_name="Recruiter User",
        )
        session.add_all([org_unjoined, recruiter])
        await session.commit()
        await session.refresh(org_unjoined)
        await session.refresh(recruiter)

    access_token = create_access_token(user_id=recruiter.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/operations/metrics",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Organization-ID": str(org_unjoined.id),
            }
        )
        assert resp.status_code == 403

@pytest.mark.asyncio
async def test_valid_recruiter_access_allowed():
    """Valid authenticated Recruiter accessing their organization's APIs succeeds."""
    async with async_session_factory() as session:
        org = Organization(name="Valid Recruiter Org", slug=f"org-{uuid.uuid4().hex[:8]}")
        recruiter = User(
            email=f"recruiter_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=hash_password("Password123!"),
            full_name="Valid Recruiter",
        )
        session.add_all([org, recruiter])
        await session.commit()
        await session.refresh(org)
        await session.refresh(recruiter)

        await set_tenant_context(session, org.id)
        mem = OrganizationMembership(
            organization_id=org.id,
            user_id=recruiter.id,
            role=RoleEnum.RECRUITER,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(mem)
        await session.commit()

    access_token = create_access_token(user_id=recruiter.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Organization-ID": str(org.id),
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == recruiter.email

@pytest.mark.asyncio
async def test_ai_governance_no_llm_mutation_paths():
    """Verify AI recommendation service remains strictly advisory with zero decision mutation paths."""
    from app.services.recommendation_service import RecommendationService
    from app.infrastructure.recommendation.recommendation_engine import RecommendationEngine

    service = RecommendationService()
    engine = RecommendationEngine()

    assert hasattr(service, "generate_recommendation")
    assert hasattr(service, "record_recruiter_decision")
    assert not hasattr(service, "auto_advance_candidate")
    assert not hasattr(service, "auto_reject_candidate")

    assert hasattr(engine, "determine_recommendation_type")
    assert hasattr(engine, "generate_explanation")
    assert not hasattr(engine, "auto_advance_candidate")
    assert not hasattr(engine, "auto_reject_candidate")
