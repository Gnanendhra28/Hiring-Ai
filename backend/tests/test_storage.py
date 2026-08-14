import pytest
import uuid
from app.infrastructure.storage.azurite import LocalAzuriteStorageProvider
from app.infrastructure.storage.base import TenantAccessDeniedException

@pytest.mark.asyncio
async def test_storage_tenant_path_validation():
    provider = LocalAzuriteStorageProvider(base_dir="/tmp/test_storage_hiring")
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    valid_path = f"organizations/{org_a}/documents/doc_123/resume.pdf"
    content = b"Candidate Resume PDF Binary Data"

    # Upload under matching Org A
    uploaded_key = await provider.upload(org_a, valid_path, content)
    assert uploaded_key == valid_path

    # Verify exists
    exists = await provider.exists(org_a, valid_path)
    assert exists is True

    # Download content
    downloaded = await provider.download(org_a, valid_path)
    assert downloaded == content

    # Attempt download using Org B context -> MUST RAISE TenantAccessDeniedException
    with pytest.raises(TenantAccessDeniedException):
        await provider.download(org_b, valid_path)

    # Attempt upload with invalid prefix -> MUST RAISE ValueError
    invalid_category_path = f"organizations/{org_a}/forbidden_folder/file.txt"
    with pytest.raises(ValueError):
        await provider.upload(org_a, invalid_category_path, content)

    # Delete
    deleted = await provider.delete(org_a, valid_path)
    assert deleted is True
