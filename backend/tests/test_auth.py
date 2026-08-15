import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine



@pytest.mark.asyncio
async def test_user_registration_and_login():
    try:
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
            headers={"Authorization": "Bearer invalid_tampered_token_string"}
        )
        assert resp2.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_flow_and_type_enforcement():
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            email = f"test_refresh_{uuid.uuid4().hex[:8]}@example.com"
            
            # 1. Register & Login
            reg_res = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "SecurePassword123!", "full_name": "Refresh User"}
            )
            assert reg_res.status_code == 201
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "SecurePassword123!"}
            )
            assert login_resp.status_code == 200
            tokens = login_resp.json()
            access_token = tokens["access_token"]
            refresh_token = tokens["refresh_token"]

            # 2. Reject Refresh Token passed as Bearer Access Token to /me
            me_with_refresh = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {refresh_token}"}
            )
            assert me_with_refresh.status_code == 401
            assert "Access token required" in me_with_refresh.json()["detail"]

            # 3. Reject Access Token passed as payload to /auth/refresh
            refresh_with_access = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": access_token}
            )
            assert refresh_with_access.status_code == 401
            assert "Refresh token required" in refresh_with_access.json()["detail"]

            # 4. Successfully Exchange Refresh Token for New Token Pair
            refresh_resp = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            assert refresh_resp.status_code == 200
            new_tokens = refresh_resp.json()
            assert "access_token" in new_tokens
            assert "refresh_token" in new_tokens
            assert new_tokens["token_type"] == "bearer"
            new_access = new_tokens["access_token"]

            # 5. Access /me with new access token
            me_resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {new_access}"}
            )
            assert me_resp.status_code == 200
            assert me_resp.json()["user"]["email"] == email

            # 6. Reject Invalid Refresh Token
            bad_refresh_resp = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid_refresh_token_string"}
            )
            assert bad_refresh_resp.status_code == 401
    finally:
        await engine.dispose()





