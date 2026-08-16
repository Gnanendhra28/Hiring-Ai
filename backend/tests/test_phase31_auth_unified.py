import pytest
import uuid
from fastapi import status
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_unified_login_role_resolution_candidate():
    """Verifies candidate email/password login succeeds on POST /api/v1/auth/login."""
    email = f"phase31_candidate_{uuid.uuid4()}@example.com"
    async with async_session_factory() as session:
        user = User(
            email=email,
            password_hash=hash_password("Password123!"),
            full_name="Phase31 Candidate",
            is_platform_admin=False,
        )
        session.add(user)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_resp.status_code == status.HTTP_200_OK
        profile = me_resp.json()
        assert profile["user"]["email"] == email
        assert profile["user"]["is_platform_admin"] is False
        assert len(profile["memberships"]) == 0

@pytest.mark.asyncio
async def test_unified_login_role_resolution_admin():
    """Verifies admin email/password login succeeds through unified POST /api/v1/auth/login."""
    email = f"phase31_admin_{uuid.uuid4()}@example.com"
    async with async_session_factory() as session:
        user = User(
            email=email,
            password_hash=hash_password("AdminPass123!"),
            full_name="Phase31 Admin",
            is_platform_admin=True,
        )
        session.add(user)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "AdminPass123!"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_resp.status_code == status.HTTP_200_OK
        profile = me_resp.json()
        assert profile["user"]["is_platform_admin"] is True

@pytest.mark.asyncio
async def test_google_auth_url_endpoint():
    """Verifies GET /api/v1/auth/google/url returns configuration state."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/google/url")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "configured" in data
        assert "url" in data

@pytest.mark.asyncio
async def test_google_oauth_unconfigured_error():
    """Verifies POST /api/v1/auth/google/callback fails gracefully when Google credentials are unset."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/google/callback",
            json={"code": "fake_auth_code"},
        )
        assert resp.status_code in (status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_401_UNAUTHORIZED)
