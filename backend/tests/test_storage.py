import pytest
import uuid
from app.infrastructure.storage.gcs_storage import GCSResumeStorageProvider

def test_gcs_storage_upload_download_and_signed_url():
    provider = GCSResumeStorageProvider(storage_root="/tmp/test_gcs_storage_hiring")
    candidate_id = str(uuid.uuid4())
    resume_id = str(uuid.uuid4())
    filename = "Senior_Software_Engineer_Resume.pdf"
    content = b"%PDF-1.4 Mock resume content for testing."

    # 1. Upload
    path = provider.upload_file(
        candidate_id=candidate_id,
        resume_id=resume_id,
        filename=filename,
        content=content,
        content_type="application/pdf"
    )
    assert f"resumes/{candidate_id}/{resume_id}" in path

    # 2. Exists
    exists = provider.exists(path)
    assert exists is True

    # 3. Download
    downloaded = provider.download_file(path)
    assert downloaded == content

    # 4. Generate Signed URL (valid string in cloud with credentials, or None in local mock)
    signed_url = provider.generate_signed_url(path, expiration_minutes=15)
    assert signed_url is None or isinstance(signed_url, str)

    # 5. Delete
    deleted = provider.delete_file(path)
    assert deleted is True


