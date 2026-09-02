import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine, async_session_factory
from app.domains.identity.models import User
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_user_profile_and_logout():
    try:
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        async with async_session_factory() as session:
            user = User(email=email, password_hash="FIREBASE_AUTH", full_name="Test Firebase User", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        token = create_access_token({"sub": str(user.id)})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Access Profile with Token
            me_resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert me_resp.status_code == 200
            profile = me_resp.json()
            assert profile["user"]["email"] == email

            # 2. Logout
            logout_resp = await client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert logout_resp.status_code == 200
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_unauthenticated_and_invalid_tokens():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Unauthenticated request
        resp1 = await client.get("/api/v1/auth/me")
        assert resp1.status_code == 401

        # Invalid token signature
        resp2 = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.payload"}
        )
        assert resp2.status_code == 401
