from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

KNOWN_INSECURE_SECRETS = {
    "dev_secret_key_change_in_production_min_32_bytes_long",
    "dev_encryption_key_32_bytes_long!!",
    "placeholder_ai_api_key",
    "placeholder_client_id",
    "placeholder_client_secret",
    "placeholder_ms_client_id",
    "placeholder_ms_client_secret",
    "placeholder_google_client_id",
    "placeholder_google_client_secret",
    "secret",
    "password",
    "change_me",
}

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Environment
    APP_ENV: str = "development"  # development, staging, production
    APP_NAME: str = "AI Hiring SaaS Platform"
    APP_VERSION: str = "1.0.0"
    API_BASE_URL: str = "http://localhost:8000/api/v1"
    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"

    # Database (Azure PostgreSQL + pgvector)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hiring_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # Azure Services
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_RESOURCE_GROUP: Optional[str] = None
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = "UseDevelopmentStorage=true"
    AZURE_STORAGE_ACCOUNT: Optional[str] = "staihiringdev"
    AZURE_STORAGE_CONTAINER_DOCUMENTS: str = "documents"
    AZURE_SERVICE_BUS_CONNECTION_STRING: Optional[str] = None
    AZURE_SERVICE_BUS_TOPIC_APPLICATION_EVENTS: str = "application-events"

    # Security
    SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_bytes_long"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = "dev_encryption_key_32_bytes_long!!"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # OIDC / OAuth2
    OIDC_CLIENT_ID: Optional[str] = None
    OIDC_CLIENT_SECRET: Optional[str] = None
    OIDC_ISSUER: Optional[str] = None

    # AI Gateway & Cost Safeguards
    AI_PROVIDER: str = "openai"
    LLM_PROVIDER: str = "gemini"
    AI_API_KEY: Optional[str] = "placeholder_ai_api_key"
    GEMINI_API_KEY: Optional[str] = "placeholder_gemini_api_key"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    AI_FAST_MODEL: str = "gpt-4o-mini"
    AI_STRONG_MODEL: str = "gpt-4o"
    AI_ESCALATION_CONFIDENCE_THRESHOLD: float = 0.75
    AI_MAX_INPUT_TOKENS: int = 4000
    AI_MAX_OUTPUT_TOKENS: int = 2000
    AI_REQUEST_TIMEOUT_SECONDS: float = 30.0
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536


    # Document Intelligence & Processing
    MAX_RESUME_SIZE_BYTES: int = 1024 * 1024  # 1 MB Limit
    TEXT_QUALITY_MIN_WORDS: int = 20
    TEXT_QUALITY_GARBLED_RATIO_MAX: float = 0.25



    # Email
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""
    EMAIL_FROM: str = "AI Hiring Platform <noreply@hiringplatform.com>"

    # Readiness Policy Configuration
    READINESS_CHECK_DB: bool = True
    READINESS_CHECK_REDIS: bool = True

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        env = self.APP_ENV.lower().strip()
        if env in ("production", "staging"):
            # Strict Secret Validation for Staging & Production
            insecure_found = []
            if self.SECRET_KEY in KNOWN_INSECURE_SECRETS or len(self.SECRET_KEY) < 32:
                insecure_found.append("SECRET_KEY is insecure or under 32 bytes")
            if self.ENCRYPTION_KEY in KNOWN_INSECURE_SECRETS or len(self.ENCRYPTION_KEY) < 32:
                insecure_found.append("ENCRYPTION_KEY is insecure or under 32 bytes")
            if self.AI_API_KEY in KNOWN_INSECURE_SECRETS:
                insecure_found.append("AI_API_KEY is using a placeholder key")
            if "postgres:postgres@localhost" in self.DATABASE_URL:
                insecure_found.append("DATABASE_URL is using default local credentials")

            if insecure_found:
                error_msg = (
                    f"CRITICAL SECURITY CONFIGURATION ERROR in {env.upper()} environment:\n"
                    + "\n".join(f"  - {err}" for err in insecure_found)
                    + "\nSecrets must be provided via Azure Key Vault or secure runtime environment variables."
                )
                raise ValueError(error_msg)
        return self

settings = Settings()
