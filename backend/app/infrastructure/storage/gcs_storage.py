"""
Google Cloud Storage / Firebase Storage Resume Provider.
Manages immutable candidate resume file artifacts under:
resumes/{candidateId}/{resumeId}/{sanitized_filename}

Integrates with Google Cloud Storage SDK / Firebase Admin Storage with
automatic local volume fallback for resilient local development and offline testing.
"""

import os
import re
from datetime import timedelta
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger


class GCSResumeStorageProvider:
    """
    Production GCS / Firebase Storage Provider with short-lived signed URLs
    and local filesystem fallback.
    """

    def __init__(
        self,
        bucket_name: str | None = None,
        storage_root: str | None = None,
    ) -> None:
        self.bucket_name = (
            bucket_name
            or getattr(settings, "FIREBASE_STORAGE_BUCKET", None)
            or getattr(settings, "GCS_BUCKET_NAME", None)
            or os.getenv("FIREBASE_STORAGE_BUCKET")
            or os.getenv("GCS_BUCKET_NAME")
            or "hiring-ai-4ae76.appspot.com"
        )
        self.storage_root = Path(storage_root or getattr(settings, "UPLOAD_DIR", "storage") or "storage")
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self._gcs_client = None

    def _get_gcs_client(self):
        if self._gcs_client is None:
            try:
                from google.cloud import storage
                self._gcs_client = storage.Client()
                logger.info(f"[GCS Storage] Initialized GCS client for bucket: {self.bucket_name}")
            except Exception as ex:
                logger.debug(f"[GCS Storage] Google Cloud Storage SDK not configured; using local filesystem: {ex}")
                self._gcs_client = False
        return self._gcs_client if self._gcs_client is not False else None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizes user-provided filename to prevent directory traversal and unsafe characters."""
        base = os.path.basename(filename)
        # Keep alphanumeric, dashes, underscores, and single dot for extension
        clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
        return clean or "resume.pdf"

    def build_storage_path(self, candidate_id: str, resume_id: str, filename: str) -> str:
        """Constructs canonical storage path: resumes/{candidateId}/{resumeId}/{filename}"""
        clean_file = self.sanitize_filename(filename)
        return f"resumes/{candidate_id!s}/{resume_id!s}/{clean_file}"

    def upload_file(
        self,
        candidate_id: str,
        resume_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> str:
        """
        Uploads resume artifact to GCS bucket and mirrors to local storage.
        Returns canonical storage_path.
        """
        storage_path = self.build_storage_path(candidate_id, resume_id, filename)

        # 1. Write to local storage mirror
        local_full_path = self.storage_root / storage_path
        local_full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_full_path, "wb") as f:
            f.write(content)

        # 2. Upload to GCS if client available
        client = self._get_gcs_client()
        if client:
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(storage_path)
                blob.upload_from_string(content, content_type=content_type)
                logger.info(f"[GCS Storage] Uploaded {len(content)} bytes to gs://{self.bucket_name}/{storage_path}")
            except Exception as ex:
                logger.warning(f"[GCS Storage] Upload to gs://{self.bucket_name}/{storage_path} failed, local mirror preserved: {ex}")

        return storage_path

    def download_file(self, storage_path: str) -> bytes:
        """
        Downloads resume content by canonical storage path.
        Checks local mirror first for high speed, then fetches from GCS.
        """
        clean_path = storage_path.lstrip("/")
        local_full_path = self.storage_root / clean_path

        if local_full_path.exists():
            with open(local_full_path, "rb") as f:
                return f.read()

        client = self._get_gcs_client()
        if client:
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(clean_path)
                data = blob.download_as_bytes()
                # Cache locally
                local_full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_full_path, "wb") as f:
                    f.write(data)
                return data
            except Exception as ex:
                logger.error(f"[GCS Storage] Failed downloading gs://{self.bucket_name}/{clean_path}: {ex}")

        raise FileNotFoundError(f"Resume artifact '{clean_path}' not found on storage.")

    def generate_signed_url(self, storage_path: str, expiration_minutes: int = 15) -> str | None:
        """
        Generates a v4 signed URL for secure, temporary browser access (15 min default).
        Returns None if GCS signing credentials are not available in current environment.
        """
        clean_path = storage_path.lstrip("/")
        client = self._get_gcs_client()
        if client:
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(clean_path)
                url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(minutes=expiration_minutes),
                    method="GET",
                )
                return url
            except Exception as ex:
                logger.debug(f"[GCS Storage] Signed URL generation unavailable: {ex}")
                return None
        return None

    def delete_file(self, storage_path: str) -> bool:
        """Deletes resume artifact from both local storage and GCS."""
        clean_path = storage_path.lstrip("/")
        local_full_path = self.storage_root / clean_path
        deleted = False

        if local_full_path.exists():
            local_full_path.unlink(missing_ok=True)
            deleted = True

        client = self._get_gcs_client()
        if client:
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(clean_path)
                if blob.exists():
                    blob.delete()
                    deleted = True
            except Exception as ex:
                logger.warning(f"[GCS Storage] Delete failed on gs://{self.bucket_name}/{clean_path}: {ex}")

        return deleted

    def exists(self, storage_path: str) -> bool:
        clean_path = storage_path.lstrip("/")
        local_full_path = self.storage_root / clean_path
        if local_full_path.exists():
            return True

        client = self._get_gcs_client()
        if client:
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(clean_path)
                return blob.exists()
            except Exception:
                return False
        return False
