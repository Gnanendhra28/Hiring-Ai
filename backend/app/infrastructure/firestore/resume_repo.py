"""
Firestore Repository for Candidate Resumes and Job Applications.
Manages persistent documents under:
- resumes/{resumeId}
- applications/{applicationId}
- users/{userId}

Provides high-speed persistence with Google Cloud Firestore AsyncClient
and automatic local JSON store fallback for local development and test isolation.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.logging import logger


class FirestoreResumeRepository:
    """
    Production Firestore Repository for Resumes and Job Applications.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        storage_dir: Optional[str] = None,
    ) -> None:
        self.project_id = (
            project_id
            or os.getenv("FIRESTORE_PROJECT_ID")
            or os.getenv("FIREBASE_PROJECT_ID")
            or "hiring-ai-4ae76"
        )
        self.storage_dir = Path(storage_dir or "backend/storage/firestore_db")
        self.resumes_dir = self.storage_dir / "resumes"
        self.applications_dir = self.storage_dir / "applications"
        self.resumes_dir.mkdir(parents=True, exist_ok=True)
        self.applications_dir.mkdir(parents=True, exist_ok=True)
        self._firestore_client = None

    async def _get_client(self):
        if self._firestore_client is None:
            try:
                from google.cloud import firestore
                self._firestore_client = firestore.AsyncClient(project=self.project_id)
                logger.info(f"[Firestore Repo] Connected to Cloud Firestore project: {self.project_id}")
            except Exception as ex:
                logger.debug(f"[Firestore Repo] Cloud Firestore client offline; using local document store: {ex}")
                self._firestore_client = False
        return self._firestore_client if self._firestore_client is not False else None

    # =========================================================================
    # RESUMES COLLECTION: resumes/{resumeId}
    # =========================================================================

    async def save_resume(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves or updates a resume metadata document.
        Schema: {resumeId, candidateId, fileName, contentType, storagePath, fileSize, uploadedAt, status, version}
        """
        resume_id = str(resume_data["resumeId"])
        doc_data = dict(resume_data)
        doc_data["resumeId"] = resume_id
        doc_data["candidateId"] = str(doc_data["candidateId"])
        if "uploadedAt" not in doc_data or not doc_data["uploadedAt"]:
            doc_data["uploadedAt"] = datetime.now(timezone.utc).isoformat()
        if "status" not in doc_data:
            doc_data["status"] = "active"

        # Calculate version if not present
        if "version" not in doc_data or not doc_data["version"]:
            existing = await self.list_resumes_by_candidate(doc_data["candidateId"])
            doc_data["version"] = len(existing) + 1

        # 1. Save to local fallback store
        local_file = self.resumes_dir / f"{resume_id}.json"
        with open(local_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, indent=2, default=str)

        # 2. Save to Cloud Firestore if connected (with fast timeout)
        client = await self._get_client()
        if client:
            try:
                import asyncio
                doc_ref = client.collection("resumes").document(resume_id)
                await asyncio.wait_for(doc_ref.set(doc_data), timeout=1.5)
            except Exception as ex:
                logger.debug(f"[Firestore Repo] Cloud Firestore save_resume fallback to local: {ex}")

        return doc_data

    async def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a resume document by resumeId."""
        resume_id = str(resume_id)
        
        # 1. Try Cloud Firestore
        client = await self._get_client()
        if client:
            try:
                import asyncio
                doc_ref = client.collection("resumes").document(resume_id)
                doc = await asyncio.wait_for(doc_ref.get(), timeout=1.5)
                if doc.exists:
                    return doc.to_dict()
            except Exception as ex:
                logger.debug(f"[Firestore Repo] Cloud get_resume fallback: {ex}")

        # 2. Local fallback
        local_file = self.resumes_dir / f"{resume_id}.json"
        if local_file.exists():
            try:
                with open(local_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return None

    async def list_resumes_by_candidate(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Lists all active resume documents for a candidate, ordered by version descending."""
        cand_str = str(candidate_id)
        resumes: List[Dict[str, Any]] = []

        # 1. Try Cloud Firestore
        client = await self._get_client()
        if client:
            try:
                query = client.collection("resumes").where("candidateId", "==", cand_str)
                async for doc in query.stream():
                    data = doc.to_dict()
                    if data.get("status") != "deleted":
                        resumes.append(data)
                if resumes:
                    resumes.sort(key=lambda r: r.get("version", 1), reverse=True)
                    return resumes
            except Exception as ex:
                logger.debug(f"[Firestore Repo] Cloud list_resumes attempt failed: {ex}")

        # 2. Local fallback
        for fpath in self.resumes_dir.glob("*.json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if str(data.get("candidateId")) == cand_str and data.get("status") != "deleted":
                        resumes.append(data)
            except Exception:
                continue

        resumes.sort(key=lambda r: r.get("version", 1), reverse=True)
        return resumes

    async def delete_resume(self, resume_id: str) -> bool:
        """Marks resume status as deleted."""
        resume_id = str(resume_id)
        data = await self.get_resume(resume_id)
        if not data:
            return False

        data["status"] = "deleted"
        data["deletedAt"] = datetime.now(timezone.utc).isoformat()
        await self.save_resume(data)
        return True

    # =========================================================================
    # APPLICATIONS COLLECTION: applications/{applicationId}
    # =========================================================================

    async def save_application(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves or updates a job application document.
        Schema: {applicationId, jobId, candidateId, resumeId, status, appliedAt, updatedAt}
        """
        app_id = str(app_data["applicationId"])
        doc_data = dict(app_data)
        doc_data["applicationId"] = app_id
        doc_data["jobId"] = str(doc_data["jobId"])
        doc_data["candidateId"] = str(doc_data["candidateId"])
        if "resumeId" in doc_data and doc_data["resumeId"]:
            doc_data["resumeId"] = str(doc_data["resumeId"])
        if "appliedAt" not in doc_data or not doc_data["appliedAt"]:
            doc_data["appliedAt"] = datetime.now(timezone.utc).isoformat()
        doc_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

        # 1. Local fallback
        local_file = self.applications_dir / f"{app_id}.json"
        with open(local_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, indent=2, default=str)

        # 2. Cloud Firestore
        client = await self._get_client()
        if client:
            try:
                import asyncio
                doc_ref = client.collection("applications").document(app_id)
                await asyncio.wait_for(doc_ref.set(doc_data), timeout=1.5)
            except Exception as ex:
                logger.debug(f"[Firestore Repo] Cloud Firestore save_application fallback: {ex}")

        return doc_data

    async def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Fetches application document by applicationId."""
        app_id = str(application_id)

        # 1. Cloud Firestore
        client = await self._get_client()
        if client:
            try:
                doc_ref = client.collection("applications").document(app_id)
                doc = await doc_ref.get()
                if doc.exists:
                    return doc.to_dict()
            except Exception as ex:
                logger.debug(f"[Firestore Repo] Cloud get_application failed: {ex}")

        # 2. Local fallback
        local_file = self.applications_dir / f"{app_id}.json"
        if local_file.exists():
            try:
                with open(local_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return None

    async def list_applications_by_job(self, job_id: str) -> List[Dict[str, Any]]:
        """Lists all applications for a given job."""
        j_str = str(job_id)
        apps: List[Dict[str, Any]] = []

        # 1. Cloud Firestore
        client = await self._get_client()
        if client:
            try:
                query = client.collection("applications").where("jobId", "==", j_str)
                async for doc in query.stream():
                    apps.append(doc.to_dict())
                if apps:
                    return apps
            except Exception as ex:
                logger.debug(f"[Firestore Repo] Cloud list_applications_by_job failed: {ex}")

        # 2. Local fallback
        for fpath in self.applications_dir.glob("*.json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if str(data.get("jobId")) == j_str:
                        apps.append(data)
            except Exception:
                continue

        return apps
