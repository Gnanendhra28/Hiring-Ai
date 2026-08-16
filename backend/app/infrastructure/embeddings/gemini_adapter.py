import asyncio
from typing import List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.embeddings.base import EmbeddingProvider

class GeminiEmbeddingAdapter(EmbeddingProvider):
    """
    Production Google Gemini Embedding Provider generating 1536-dimensional unit-normalized float vectors
    compatible with the pgvector database schema.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None) or settings.AI_API_KEY
        self.model = model or getattr(settings, "EMBEDDING_MODEL", "gemini-embedding-001")

        env = settings.APP_ENV.lower().strip()
        if env in ("staging", "production"):
            if not self.api_key or self.api_key in (
                "placeholder_gemini_api_key",
                "placeholder_ai_api_key",
                "secret",
                "change_me",
            ):
                raise ValueError(
                    f"CRITICAL CONFIGURATION ERROR: GEMINI_API_KEY is missing or invalid for Gemini Embedding Provider in {env.upper()} environment."
                )

        if settings.EMBEDDING_DIMENSION != 1536:
            raise ValueError(
                f"CRITICAL EMBEDDING DIMENSION MISMATCH: Configured dimension ({settings.EMBEDDING_DIMENSION}) "
                f"does not match standard database schema dimension (1536)."
            )

    async def generate_embedding(self, text: str) -> List[float]:
        logger.info(f"[Gemini Embedding] Generating vector embedding for text segment ({len(text)} chars) using model={self.model}")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        payload = {
            "model": f"models/{self.model}",
            "content": {
                "parts": [{"text": text[:8000]}]
            },
            "outputDimensionality": 1536,
        }

        TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
        max_attempts = 3
        attempt = 0
        backoff_base = 0.1

        while attempt < max_attempts:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
                    resp = await client.post(url, json=payload, headers=headers)

                    if resp.status_code == 200:
                        data = resp.json()
                        embedding_data = data.get("embedding", {})
                        vec = embedding_data.get("values", [])

                        if not vec or len(vec) != settings.EMBEDDING_DIMENSION:
                            raise RuntimeError(
                                f"Gemini Embedding API returned unexpected dimension {len(vec)} (expected {settings.EMBEDDING_DIMENSION})."
                            )

                        # Normalize vector to unit length
                        norm = sum(x * x for x in vec) ** 0.5
                        if norm > 0:
                            vec = [x / norm for x in vec]

                        return vec

                    if resp.status_code in TRANSIENT_STATUS_CODES:
                        if attempt < max_attempts:
                            delay = backoff_base * (2 ** (attempt - 1))
                            logger.warning(
                                f"[Gemini Embedding] Transient error {resp.status_code} (Attempt {attempt}/{max_attempts}). "
                                f"Retrying in {delay:.2f}s..."
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error(f"[Gemini Embedding] Max retries exhausted ({max_attempts}) for status {resp.status_code}.")
                            raise RuntimeError(f"Gemini Embedding API call failed with status {resp.status_code}: {resp.text}")

                    # Permanent client error -> fail fast
                    logger.error(f"[Gemini Embedding] Permanent error status {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"Gemini Embedding API call failed with status {resp.status_code}: {resp.text}")

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                if attempt < max_attempts:
                    delay = backoff_base * (2 ** (attempt - 1))
                    logger.warning(
                        f"[Gemini Embedding] Network error (Attempt {attempt}/{max_attempts}): {net_err}. Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"[Gemini Embedding] Max retries exhausted for network error: {net_err}")
                    raise RuntimeError(f"Gemini Embedding network error after {max_attempts} attempts: {str(net_err)}")

        raise RuntimeError("Gemini Embedding API call failed: Max attempts reached.")
