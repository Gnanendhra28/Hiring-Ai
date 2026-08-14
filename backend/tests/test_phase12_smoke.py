import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_smoke_01_liveness_probe():
    """Smoke test: GET /live endpoint returns 200 alive."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/live")
        assert res.status_code == 200
        assert res.json()["status"] == "alive"

@pytest.mark.asyncio
async def test_smoke_02_readiness_probe():
    """Smoke test: GET /ready endpoint returns 200 ready."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/ready")
        assert res.status_code == 200
        assert res.json()["status"] == "ready"

@pytest.mark.asyncio
async def test_smoke_03_metrics_endpoint():
    """Smoke test: GET /metrics endpoint returns Prometheus text format."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/metrics")
        assert res.status_code == 200
        assert "text/plain" in res.headers["content-type"]

@pytest.mark.asyncio
async def test_smoke_04_unauthenticated_jobs_list_protected():
    """Smoke test: GET /api/v1/jobs endpoint requires authorization and returns 401 Unauthorized."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/jobs")
        assert res.status_code == 401
        assert "detail" in res.json()

