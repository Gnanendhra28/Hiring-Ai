import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.rate_limiter import rate_limiter

@pytest.mark.asyncio
async def test_rate_limiter_protection_and_bypass():
    rate_limiter.reset()
    rate_limiter.enabled_in_test = True
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Health probes bypass rate limiter completely
            for _ in range(20):
                res = await client.get("/live")
                assert res.status_code == 200

            # 2. Login endpoint allows up to 5 requests, 6th returns 429
            for i in range(5):
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": f"rate_limit_{i}@example.com", "password": "WrongPassword123!"}
                )
                # Should receive 401 Unauthorized (not 429) for the first 5 requests
                assert resp.status_code == 401

            # 6th request triggers rate limit HTTP 429
            over_limit_resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "rate_limit_6@example.com", "password": "WrongPassword123!"}
            )
            assert over_limit_resp.status_code == 429
            assert "Rate limit exceeded" in over_limit_resp.json()["detail"]
            assert "Retry-After" in over_limit_resp.headers
    finally:
        rate_limiter.enabled_in_test = False
        rate_limiter.reset()

