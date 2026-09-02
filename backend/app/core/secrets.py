import abc
import os
from typing import Optional
from app.core.config import settings

class SecretProvider(abc.ABC):
    """Abstract Secret Provider for local environment or cloud key vault management."""

    @abc.abstractmethod
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        pass

class EnvironmentSecretProvider(SecretProvider):
    """Environment-based secret provider for local development, testing, and container environment variables."""

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        val = os.getenv(secret_name)
        if val:
            return val
        if hasattr(settings, secret_name):
            return getattr(settings, secret_name)
        return default

class GoogleSecretManagerProvider(SecretProvider):
    """Google Cloud Secret Manager secret provider with fallback to environment variables."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "hiring-ai-507307")
        self._fallback = EnvironmentSecretProvider()

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception:
            return self._fallback.get_secret(secret_name, default)

def get_secret_provider() -> SecretProvider:
    """Factory helper returning appropriate secret provider based on environment."""
    env = settings.APP_ENV.lower().strip()
    if env in ("production", "staging") and os.getenv("USE_GCP_SECRET_MANAGER") == "true":
        return GoogleSecretManagerProvider()
    return EnvironmentSecretProvider()

secret_provider = get_secret_provider()
