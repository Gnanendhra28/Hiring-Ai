import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.infrastructure.ai_gateway.gemini_adapter import GeminiAIGatewayAdapter

@pytest.mark.asyncio
async def test_gemini_retry_success_first_attempt():
    adapter = GeminiAIGatewayAdapter(api_key="test_key")

    mock_resp = httpx.Response(
        200,
        json={
            "candidates": [{"content": {"parts": [{"text": "Success Narrative"}]}}],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
        },
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await adapter.chat_completion([{"role": "user", "content": "Hello"}])

        assert res["content"] == "Success Narrative"
        assert mock_post.call_count == 1

@pytest.mark.asyncio
async def test_gemini_retry_on_transient_429_then_succeed():
    adapter = GeminiAIGatewayAdapter(api_key="test_key")

    mock_429 = httpx.Response(429, text="Rate limit exceeded")
    mock_200 = httpx.Response(
        200,
        json={
            "candidates": [{"content": {"parts": [{"text": "Retried Narrative"}]}}],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
        },
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [mock_429, mock_200]
        res = await adapter.chat_completion([{"role": "user", "content": "Hello"}])

        assert res["content"] == "Retried Narrative"
        assert mock_post.call_count == 2

@pytest.mark.asyncio
async def test_gemini_retry_fail_fast_on_permanent_400():
    adapter = GeminiAIGatewayAdapter(api_key="test_key")

    mock_400 = httpx.Response(400, text="Bad Request")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_400
        with pytest.raises(RuntimeError, match="status 400"):
            await adapter.chat_completion([{"role": "user", "content": "Hello"}])

        # Permanent 400 client error MUST NOT be retried!
        assert mock_post.call_count == 1
