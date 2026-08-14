import os
import uuid
from typing import Any, Dict, Optional
from app.infrastructure.storage.base import StorageProvider
from app.core.logging import logger

class LocalAzuriteStorageProvider(StorageProvider):
    """
    Local filesystem & Azurite emulator storage provider for development and testing.
    """

    def __init__(self, base_dir: str = "/tmp/hiring_platform_storage") -> None:
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_full_path(self, validated_path: str) -> str:
        return os.path.join(self.base_dir, validated_path)

    async def upload(
        self,
        organization_id: uuid.UUID,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        validated_path = self.validate_tenant_path(organization_id, path)
        full_path = self._get_full_path(validated_path)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(content)

        logger.debug(f"Uploaded {len(content)} bytes to local/azurite storage at {validated_path}")
        return validated_path

    async def download(self, organization_id: uuid.UUID, path: str) -> bytes:
        validated_path = self.validate_tenant_path(organization_id, path)
        full_path = self._get_full_path(validated_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Object not found: {validated_path}")

        with open(full_path, "rb") as f:
            return f.read()

    async def delete(self, organization_id: uuid.UUID, path: str) -> bool:
        validated_path = self.validate_tenant_path(organization_id, path)
        full_path = self._get_full_path(validated_path)

        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    async def exists(self, organization_id: uuid.UUID, path: str) -> bool:
        validated_path = self.validate_tenant_path(organization_id, path)
        full_path = self._get_full_path(validated_path)
        return os.path.exists(full_path)

    async def get_metadata(self, organization_id: uuid.UUID, path: str) -> Dict[str, Any]:
        validated_path = self.validate_tenant_path(organization_id, path)
        full_path = self._get_full_path(validated_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Object not found: {validated_path}")

        stat = os.stat(full_path)
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "path": validated_path,
        }
