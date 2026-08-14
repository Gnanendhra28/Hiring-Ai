import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_user_registration_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        # 1. Register User
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "SecurePassword123!",
                "full_name": "Test User"
            }
        )
        assert reg_resp.status_code == 201
        data = reg_resp.json()
        assert data["email"] == email
        assert "id" in data

        # 2. Login User
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "SecurePassword123!"
            }
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # 3. Access Profile with Access Token
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_resp.status_code == 200
        profile = me_resp.json()
        assert profile["user"]["email"] == email

@pytest.mark.asyncio
async def test_unauthenticated_and_invalid_tokens():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Unauthenticated request
        resp1 = await client.get("/api/v1/auth/me")
        assert resp1.status_code == 401

        # Invalid token signature
        resp2 = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_tampered_token_string"}
        )
        assert resp2.status_code == 401
