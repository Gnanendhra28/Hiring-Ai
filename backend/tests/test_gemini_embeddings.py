import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.config import settings
from app.infrastructure.embeddings.gemini_adapter import GeminiEmbeddingAdapter
from app.infrastructure.embeddings.openai_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.embeddings.base import TestEmbeddingAdapter
from app.infrastructure.factories import EmbeddingProviderFactory

@pytest.mark.asyncio
async def test_gemini_embedding_adapter_success():
    adapter = GeminiEmbeddingAdapter(api_key="test_real_gemini_key_123", model="gemini-embedding-001")

    fake_vector = [0.1] * 1536
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "embedding": {
            "values": fake_vector
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        vec = await adapter.generate_embedding("Senior Python Developer Requirement")

        assert len(vec) == 1536
        # Unit norm check
        norm = sum(x * x for x in vec) ** 0.5
        assert pytest.approx(norm, 1e-5) == 1.0

        # Verify request parameters
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["x-goog-api-key"] == "test_real_gemini_key_123"
        assert kwargs["json"]["outputDimensionality"] == 1536

@pytest.mark.asyncio
async def test_gemini_embedding_adapter_dimension_mismatch():
    adapter = GeminiEmbeddingAdapter(api_key="test_real_gemini_key_123")

    fake_vector = [0.1] * 768  # Wrong dimension (768 instead of 1536)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "embedding": {
            "values": fake_vector
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(RuntimeError, match="unexpected dimension"):
            await adapter.generate_embedding("Test text")

def test_embedding_factory_selection():
    with patch.object(settings, "APP_ENV", "production"), \
         patch.object(settings, "EMBEDDING_PROVIDER", "gemini"), \
         patch.object(settings, "GEMINI_API_KEY", "real_gemini_key_prod_123"):
        provider = EmbeddingProviderFactory.get_provider()
        assert isinstance(provider, GeminiEmbeddingAdapter)

    with patch.object(settings, "APP_ENV", "production"), \
         patch.object(settings, "EMBEDDING_PROVIDER", "openai"), \
         patch.object(settings, "AI_API_KEY", "real_openai_key_prod_123"):
        provider = EmbeddingProviderFactory.get_provider()
        assert isinstance(provider, OpenAIEmbeddingAdapter)

    with patch.object(settings, "APP_ENV", "development"), \
         patch.object(settings, "EMBEDDING_PROVIDER", "gemini"), \
         patch.object(settings, "GEMINI_API_KEY", "placeholder_gemini_api_key"):
        provider = EmbeddingProviderFactory.get_provider()
        assert isinstance(provider, TestEmbeddingAdapter)

def test_gemini_embedding_missing_credential_in_production():
    with patch.object(settings, "APP_ENV", "production"), \
         patch.object(settings, "GEMINI_API_KEY", "placeholder_gemini_api_key"), \
         patch.object(settings, "AI_API_KEY", "placeholder_ai_api_key"):
        with pytest.raises(ValueError, match="GEMINI_API_KEY is missing or invalid"):
            GeminiEmbeddingAdapter()
