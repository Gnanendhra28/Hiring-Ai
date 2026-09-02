import httpx
from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.embeddings.base import EmbeddingProvider

class OpenAIEmbeddingAdapter(EmbeddingProvider):
    """Production OpenAI Embedding Provider generating versioned float vectors."""

    def __init__(self):
        env = settings.APP_ENV.lower().strip()
        if env in ("staging", "production"):
            if not settings.AI_API_KEY or settings.AI_API_KEY in ("placeholder_ai_api_key", "secret", "change_me"):
                raise ValueError(
                    f"CRITICAL CONFIGURATION ERROR: AI_API_KEY is missing or invalid for OpenAI Embedding Provider in {env.upper()} environment."
                )

        if settings.EMBEDDING_DIMENSION != 1536:
            raise ValueError(
                f"CRITICAL EMBEDDING DIMENSION MISMATCH: Configured dimension ({settings.EMBEDDING_DIMENSION}) "
                f"does not match OpenAI text-embedding-3-small database schema dimension (1536)."
            )

    async def generate_embedding(self, text: str) -> list[float]:
        logger.info(f"[OpenAI Embedding] Generating vector embedding for text segment ({len(text)} chars)")
        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "input": text[:8000],
            "model": settings.EMBEDDING_MODEL,
        }

        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post("https://api.openai.com/v1/embeddings", json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI Embedding API call failed with status {resp.status_code}: {resp.text}")

            data = resp.json()
            vec = data["data"][0]["embedding"]

            # Normalize vector to unit length
            norm = sum(x * x for x in vec) ** 0.5
            if norm > 0:
                vec = [x / norm for x in vec]

            return vec
