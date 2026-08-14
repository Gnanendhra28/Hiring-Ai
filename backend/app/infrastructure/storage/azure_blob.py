import uuid
from typing import Any, Dict, Optional
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from app.infrastructure.storage.base import StorageProvider
from app.core.config import settings
from app.core.logging import logger

class AzureBlobStorageProvider(StorageProvider):
    """
    Real Azure Blob Storage SDK adapter for staging and production environments.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        container_name: Optional[str] = None,
    ) -> None:
        conn_str = connection_string or settings.AZURE_STORAGE_CONNECTION_STRING
        if not conn_str:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is required for AzureBlobStorageProvider")
            
        self.container_name = container_name or settings.AZURE_STORAGE_CONTAINER_DOCUMENTS
        self.client = BlobServiceClient.from_connection_string(conn_str)

    async def _get_container_client(self):
        return self.client.get_container_client(self.container_name)

    async def upload(
        self,
        organization_id: uuid.UUID,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        validated_path = self.validate_tenant_path(organization_id, path)
        container = await self._get_container_client()
        blob_client = container.get_blob_client(validated_path)

        await blob_client.upload_blob(
            content,
            overwrite=True,
            content_type=content_type,
            metadata=metadata or {},
        )
        logger.info(f"Uploaded blob to Azure Blob Storage: {validated_path}")
        return validated_path

    async def download(self, organization_id: uuid.UUID, path: str) -> bytes:
        validated_path = self.validate_tenant_path(organization_id, path)
        container = await self._get_container_client()
        blob_client = container.get_blob_client(validated_path)

        try:
            stream = await blob_client.download_blob()
            return await stream.readall()
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Blob not found in Azure Storage: {validated_path}")

    async def delete(self, organization_id: uuid.UUID, path: str) -> bool:
        validated_path = self.validate_tenant_path(organization_id, path)
        container = await self._get_container_client()
        blob_client = container.get_blob_client(validated_path)

        try:
            await blob_client.delete_blob()
            return True
        except ResourceNotFoundError:
            return False

    async def exists(self, organization_id: uuid.UUID, path: str) -> bool:
        validated_path = self.validate_tenant_path(organization_id, path)
        container = await self._get_container_client()
        blob_client = container.get_blob_client(validated_path)
        return await blob_client.exists()

    async def get_metadata(self, organization_id: uuid.UUID, path: str) -> Dict[str, Any]:
        validated_path = self.validate_tenant_path(organization_id, path)
        container = await self._get_container_client()
        blob_client = container.get_blob_client(validated_path)

        try:
            properties = await blob_client.get_blob_properties()
            return {
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "metadata": properties.metadata,
                "last_modified": properties.last_modified,
            }
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Blob not found in Azure Storage: {validated_path}")

    async def close(self):
        await self.client.close()
