import random
from abc import ABC, abstractmethod
from typing import List
from app.core.config import settings
from app.core.logging import logger

class EmbeddingProvider(ABC):
    """Abstract Base Class for Embedding Providers (OpenAI text-embedding-3, Azure OpenAI, SentenceTransformers)."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        pass

class TestEmbeddingAdapter(EmbeddingProvider):
    """Controlled Embedding Adapter generating versioned 1536-dim vector embeddings for pgvector."""

    async def generate_embedding(self, text: str) -> List[float]:
        logger.info(f"Generating test 1536-dim embedding for text segment ({len(text)} chars)")
        # Produce a deterministic 1536-dimensional normalized float vector
        random.seed(hash(text) % 2**32)
        vec = [random.uniform(-0.1, 0.1) for _ in range(settings.EMBEDDING_DIMENSION)]

        # Normalize vector to unit length
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]

        return vec
