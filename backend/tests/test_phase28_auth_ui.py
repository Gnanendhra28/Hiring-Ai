import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_firebase_role_onboarding_for_candidate():
    """Test onboarding role sets phone number for candidate."""
    unique_email = f"candidate-{uuid.uuid4()}@example.com"
    async with async_session_factory() as session:
        user = User(email=unique_email, password_hash="FIREBASE_AUTH", full_name="Jane Candidate", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    payload = {
        "role": "CANDIDATE",
        "phone_number": "+91 98765 43210",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/auth/onboard-role", json=payload, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    assert res.json()["success"] is True


@pytest.mark.asyncio
async def test_firebase_role_onboarding_for_recruiter():
    """Test onboarding role creates organization and recruiter profile."""
    unique_email = f"employee-{uuid.uuid4()}@company.com"
    async with async_session_factory() as session:
        user = User(email=unique_email, password_hash="FIREBASE_AUTH", full_name="Alex Recruiter", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    payload = {
        "role": "RECRUITER",
        "company_name": "Acme Innovations",
        "job_title": "Head of Talent",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/auth/onboard-role", json=payload, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    assert res.json()["success"] is True

    # Check profile and memberships
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        me_res = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me_res.status_code == 200
    data = me_res.json()
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["role"] == "ORGANIZATION_ADMIN"


@pytest.mark.asyncio
async def test_role_isolation_candidate_blocked_from_recruiter_api():
    """Test that a user with CANDIDATE role is strictly rejected (403) from accessing recruiter APIs."""
    candidate_email = f"candidate-iso-{uuid.uuid4()}@example.com"
    async with async_session_factory() as session:
        cand_user = User(email=candidate_email, password_hash="FIREBASE_AUTH", full_name="Pure Candidate", is_active=True)
        session.add(cand_user)
        await session.commit()
        await session.refresh(cand_user)

    token = create_access_token({"sub": str(cand_user.id)})

    fake_org_id = str(uuid.uuid4())
    job_payload = {
        "title": "Unauthorized Job",
        "department": "Engineering",
        "location": "Remote",
        "job_type": "FULL_TIME",
        "description": "Job description with sufficient length for validation.",
        "requirements": ["Python"],
        "responsibilities": ["Coding"],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/jobs",
            json=job_payload,
            headers={"Authorization": f"Bearer {token}", "X-Organization-ID": fake_org_id},
        )

    assert res.status_code == 403


@pytest.mark.asyncio
async def test_role_isolation_recruiter_blocked_from_admin_api():
    """Test that an Organization Recruiter/Admin cannot access Platform Admin APIs."""
    recruiter_email = f"rec-iso-{uuid.uuid4()}@company.com"
    async with async_session_factory() as session:
        rec_user = User(email=recruiter_email, password_hash="FIREBASE_AUTH", full_name="Org Recruiter", is_active=True, is_platform_admin=False)
        session.add(rec_user)
        await session.commit()
        await session.refresh(rec_user)

    token = create_access_token({"sub": str(rec_user.id)})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/jobs/pending", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 403
