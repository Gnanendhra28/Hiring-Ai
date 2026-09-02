import uuid
from abc import ABC, abstractmethod
from typing import Any

class TenantAccessDeniedException(Exception):
    """Raised when an object storage path does not match the active organization_id context."""
    pass

class StorageProvider(ABC):
    """Abstract Object Storage Provider interface enforcing structured tenant path validation."""

    VALID_PREFIXES = ("jobs/", "candidates/", "applications/", "documents/")

    def validate_tenant_path(self, organization_id: uuid.UUID, path: str) -> str:
        """
        Ensures that storage paths strictly follow:
        organizations/{organization_id}/{category}/{entity_id}/{filename}
        """
        org_str = str(organization_id).lower()
        clean_path = path.lstrip("/")

        expected_prefix = f"organizations/{org_str}/"
        if not clean_path.startswith(expected_prefix):
            raise TenantAccessDeniedException(
                f"Security Violation: Storage path '{path}' does not match active tenant '{org_str}'"
            )

        relative_part = clean_path[len(expected_prefix):]
        if not any(relative_part.startswith(prefix) for prefix in self.VALID_PREFIXES):
            raise ValueError(
                f"Invalid storage path category in '{path}'. Must start with one of {self.VALID_PREFIXES}"
            )

        return clean_path

    @abstractmethod
    async def upload(
        self,
        organization_id: uuid.UUID,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Uploads content to storage and returns object key."""
        pass

    @abstractmethod
    async def download(self, organization_id: uuid.UUID, path: str) -> bytes:
        """Downloads object bytes from storage."""
        pass

    @abstractmethod
    async def delete(self, organization_id: uuid.UUID, path: str) -> bool:
        """Deletes object from storage."""
        pass

    @abstractmethod
    async def exists(self, organization_id: uuid.UUID, path: str) -> bool:
        """Checks if object exists in storage."""
        pass

    @abstractmethod
    async def get_metadata(self, organization_id: uuid.UUID, path: str) -> dict[str, Any]:
        """Fetches object metadata."""
        pass
