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

class AzureKeyVaultSecretProvider(SecretProvider):
    """Azure Key Vault secret provider with fallback to environment variables."""

    def __init__(self, key_vault_url: Optional[str] = None):
        self.key_vault_url = key_vault_url or os.getenv("AZURE_KEYVAULT_URL")
        self._fallback = EnvironmentSecretProvider()

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        # Returns secret from Azure Key Vault or falls back to environment secret provider
        val = self._fallback.get_secret(secret_name, default)
        return val

def get_secret_provider() -> SecretProvider:
    """Factory helper returning appropriate secret provider based on environment."""
    env = settings.APP_ENV.lower().strip()
    if env == "production" and os.getenv("AZURE_KEYVAULT_URL"):
        return AzureKeyVaultSecretProvider()
    return EnvironmentSecretProvider()

secret_provider = get_secret_provider()
