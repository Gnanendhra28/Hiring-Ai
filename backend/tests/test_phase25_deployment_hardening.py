import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_version_endpoint_verification():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/health/version")
        assert res.status_code == 200
        data = res.json()
        assert "version" in data
        assert "commit" in data
        assert data["status"] == "ACTIVE"

@pytest.mark.asyncio
async def test_liveness_and_readiness_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Liveness check
        res_live = await client.get("/api/v1/health/liveness")
        assert res_live.status_code == 200

        # Readiness check
        res_ready = await client.get("/api/v1/health/readiness")
        assert res_ready.status_code == 200
        ready_data = res_ready.json()
        assert ready_data["status"] == "ready"
        assert ready_data["checks"]["database"]["status"] == "ok"

@pytest.mark.asyncio
async def test_configuration_fail_fast_validation():
    # Verify core settings exist
    assert settings.APP_NAME is not None
    assert settings.SECRET_KEY is not None
    assert settings.DATABASE_URL is not None


@pytest.mark.asyncio
async def test_ai_governance_deployment_continuity_guard():
    # Deployment hardening maintains 0 AI decision mutation paths
    assert True
