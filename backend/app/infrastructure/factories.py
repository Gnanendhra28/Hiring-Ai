from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.ai_gateway.base import AIGatewayProvider, TestAIGatewayAdapter
from app.infrastructure.ai_gateway.gemini_adapter import GeminiAIGatewayAdapter
from app.infrastructure.ai_gateway.openai_adapter import OpenAIAIGatewayAdapter
from app.infrastructure.embeddings.base import EmbeddingProvider, TestEmbeddingAdapter
from app.infrastructure.embeddings.gemini_adapter import GeminiEmbeddingAdapter
from app.infrastructure.embeddings.openai_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.ocr.base import OCRProvider, TestOCRAdapter

class AIGatewayFactory:
    """Factory for selecting and instantiating the appropriate AI Gateway Provider (Gemini, OpenAI, Test)."""

    @staticmethod
    def get_provider() -> AIGatewayProvider:
        env = settings.APP_ENV.lower().strip()
        provider_name = (getattr(settings, "LLM_PROVIDER", None) or settings.AI_PROVIDER).lower().strip()

        if env in ("staging", "production"):
            if provider_name == "gemini":
                logger.info(f"Instantiating REAL GeminiAIGatewayAdapter for {env.upper()} environment.")
                return GeminiAIGatewayAdapter()
            elif provider_name == "openai":
                logger.info(f"Instantiating REAL OpenAIAIGatewayAdapter for {env.upper()} environment.")
                return OpenAIAIGatewayAdapter()
            else:
                raise ValueError(f"CRITICAL CONFIGURATION ERROR: Unsupported AI Provider '{provider_name}' in {env.upper()} environment.")

        if env in ("testing", "test"):
            logger.info("Instantiating TestAIGatewayAdapter for TESTING environment.")
            return TestAIGatewayAdapter()

        # Development environment override
        gemini_key = getattr(settings, "GEMINI_API_KEY", None) or settings.AI_API_KEY
        if provider_name == "gemini" and gemini_key and gemini_key not in ("placeholder_gemini_api_key", "placeholder_ai_api_key", "secret", "change_me") and not gemini_key.startswith("AQ."):
            logger.info("Instantiating REAL GeminiAIGatewayAdapter for development environment.")
            return GeminiAIGatewayAdapter()

        if provider_name == "openai" and settings.AI_API_KEY and settings.AI_API_KEY not in ("placeholder_ai_api_key", "secret", "change_me"):
            logger.info("Instantiating REAL OpenAIAIGatewayAdapter for development environment.")
            return OpenAIAIGatewayAdapter()

        logger.info(f"Instantiating TestAIGatewayAdapter for {env.upper()} environment.")
        return TestAIGatewayAdapter()

class EmbeddingProviderFactory:
    """Factory for selecting and instantiating the appropriate Embedding Provider (Gemini, OpenAI, Test)."""

    @staticmethod
    def get_provider() -> EmbeddingProvider:
        env = settings.APP_ENV.lower().strip()
        provider_name = getattr(settings, "EMBEDDING_PROVIDER", "gemini").lower().strip()

        if env in ("staging", "production"):
            if provider_name == "gemini":
                logger.info(f"Instantiating REAL GeminiEmbeddingAdapter for {env.upper()} environment.")
                return GeminiEmbeddingAdapter()
            elif provider_name == "openai":
                logger.info(f"Instantiating REAL OpenAIEmbeddingAdapter for {env.upper()} environment.")
                return OpenAIEmbeddingAdapter()
            else:
                raise ValueError(f"CRITICAL CONFIGURATION ERROR: Unsupported Embedding Provider '{provider_name}' in {env.upper()} environment.")

        if env in ("testing", "test"):
            logger.info("Instantiating TestEmbeddingAdapter for TESTING environment.")
            return TestEmbeddingAdapter()

        gemini_key = getattr(settings, "GEMINI_API_KEY", None) or settings.AI_API_KEY
        if provider_name == "gemini" and gemini_key and gemini_key not in ("placeholder_gemini_api_key", "placeholder_ai_api_key", "secret", "change_me") and not gemini_key.startswith("AQ."):
            logger.info("Instantiating REAL GeminiEmbeddingAdapter for development environment.")
            return GeminiEmbeddingAdapter()

        if provider_name == "openai" and settings.AI_API_KEY and settings.AI_API_KEY not in ("placeholder_ai_api_key", "secret", "change_me"):
            logger.info("Instantiating REAL OpenAIEmbeddingAdapter for development environment.")
            return OpenAIEmbeddingAdapter()

        logger.info(f"Instantiating TestEmbeddingAdapter for {env.upper()} environment.")
        return TestEmbeddingAdapter()

class OCRProviderFactory:
    """Factory for selecting and instantiating the appropriate OCR Provider."""

    @staticmethod
    def get_provider() -> OCRProvider:
        logger.info(f"Instantiating OCRProvider for {settings.APP_ENV.upper()} environment.")
        return TestOCRAdapter()
