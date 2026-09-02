"""
Candidate Resume Management API.
Supports multi-version PDF/DOCX resume uploads, secure storage in GCS/Firebase Storage,
and metadata indexing in Firestore and PostgreSQL.
"""

import uuid
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.candidates.models import CandidateProfile
from app.domains.identity.models import User
from app.api.v1.deps import get_current_user
from app.infrastructure.firestore.resume_repo import FirestoreResumeRepository
from app.infrastructure.storage.gcs_storage import GCSResumeStorageProvider

router = APIRouter()

MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

# Magic header byte signatures
PDF_MAGIC = b"%PDF-"
DOCX_MAGIC = b"PK\x03\x04"


class ResumeMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    resume_id: str
    candidate_id: str
    file_name: str
    content_type: str
    storage_path: str
    file_size: int
    uploaded_at: str
    status: str
    version: int
    download_url: str | None = None


class ResumeAccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    resume_id: str
    application_id: str
    file_name: str
    content_type: str
    file_size: int
    access_url: str
    expires_in_seconds: int = 900
    access_type: str = "DIRECT_STREAM"


def validate_file_content(content: bytes, filename: str, content_type: str) -> str:
    """
    Validates file MIME type, size, and magic byte headers.
    Returns normalized content type.
    """
    if len(content) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Resume file size ({len(content) / 1024 / 1024:.1f} MB) exceeds maximum allowed limit (10 MB).",
        )

    # Magic byte header inspection
    is_pdf = content.startswith(PDF_MAGIC) or filename.lower().endswith(".pdf")
    is_docx = content.startswith(DOCX_MAGIC) or filename.lower().endswith(".docx")

    if is_pdf:
        return "application/pdf"
    elif is_docx:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format. Only verified PDF (.pdf) and Word (.docx) documents are permitted.",
        )


@router.post("/upload", response_model=ResumeMetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    Candidate Resume Upload Endpoint:
    - Validates file type (PDF/DOCX magic bytes) and size (<10MB).
    - Assigns immutable unique resumeId.
    - Stores file in Firebase Storage / GCS.
    - Records metadata in Firestore and PostgreSQL.
    """
    raw_content = await file.read()
    if not raw_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    sanitized_filename = GCSResumeStorageProvider.sanitize_filename(file.filename or "resume.pdf")
    content_type = validate_file_content(raw_content, sanitized_filename, file.content_type or "")

    resume_id = str(uuid.uuid4())
    candidate_id = str(user.id)
    now_iso = datetime.now(UTC).isoformat()

    # 1. Upload to Storage (GCS / Firebase Storage + local mirror)
    storage_provider = GCSResumeStorageProvider()
    storage_path = storage_provider.upload_file(
        candidate_id=candidate_id,
        resume_id=resume_id,
        filename=sanitized_filename,
        content=raw_content,
        content_type=content_type,
    )

    # 2. Save metadata in Firestore
    firestore_repo = FirestoreResumeRepository()
    existing_resumes = await firestore_repo.list_resumes_by_candidate(candidate_id)
    version = len(existing_resumes) + 1

    resume_doc = {
        "resumeId": resume_id,
        "candidateId": candidate_id,
        "fileName": sanitized_filename,
        "contentType": content_type,
        "storagePath": storage_path,
        "fileSize": len(raw_content),
        "uploadedAt": now_iso,
        "status": "active",
        "version": version,
    }
    saved_doc = await firestore_repo.save_resume(resume_doc)

    # 3. Synchronize to PostgreSQL CandidateProfile
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id, is_platform_admin=True)
        stmt = select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        profile = (await session.execute(stmt)).scalar_one_or_none()

        rel_resume_url = f"/api/v1/resumes/{resume_id}/file"
        if not profile:
            profile = CandidateProfile(
                user_id=user.id,
                resume_url=rel_resume_url,
                resume_filename=sanitized_filename,
                resume_filesize=len(raw_content),
                resume_updated_at=now_iso,
            )
            session.add(profile)
        else:
            profile.resume_url = rel_resume_url
            profile.resume_filename = sanitized_filename
            profile.resume_filesize = len(raw_content)
            profile.resume_updated_at = now_iso

        await session.commit()

    logger.info(
        f"[Resume Upload] Candidate {user.email} uploaded {sanitized_filename} (v{version}, {len(raw_content)} bytes) -> resumeId={resume_id}"
    )

    return ResumeMetadataResponse(
        resume_id=resume_id,
        candidate_id=candidate_id,
        file_name=sanitized_filename,
        content_type=content_type,
        storage_path=storage_path,
        file_size=len(raw_content),
        uploaded_at=now_iso,
        status="active",
        version=version,
        download_url=f"/api/v1/resumes/{resume_id}/file",
    )


@router.get("", response_model=list[ResumeMetadataResponse])
@router.get("/list", response_model=list[ResumeMetadataResponse])
async def list_candidate_resumes(
    user: User = Depends(get_current_user),
):
    """
    Candidate Endpoint: Lists all uploaded resume versions for current authenticated candidate.
    """
    candidate_id = str(user.id)
    firestore_repo = FirestoreResumeRepository()
    resumes = await firestore_repo.list_resumes_by_candidate(candidate_id)

    results = []
    for r in resumes:
        r_id = r.get("resumeId")
        results.append(
            ResumeMetadataResponse(
                resume_id=r_id,
                candidate_id=candidate_id,
                file_name=r.get("fileName", "resume.pdf"),
                content_type=r.get("contentType", "application/pdf"),
                storage_path=r.get("storagePath", ""),
                file_size=r.get("fileSize", 0),
                uploaded_at=r.get("uploadedAt", ""),
                status=r.get("status", "active"),
                version=r.get("version", 1),
                download_url=f"/api/v1/resumes/{r_id}/file",
            )
        )
    return results


@router.get("/{resume_id}", response_model=ResumeMetadataResponse)
async def get_resume_metadata(
    resume_id: str,
    user: User = Depends(get_current_user),
):
    """
    Candidate/Admin Endpoint: Fetches metadata for a specific resume.
    Enforces candidate ownership.
    """
    firestore_repo = FirestoreResumeRepository()
    resume = await firestore_repo.get_resume(resume_id)
    if not resume or resume.get("status") == "deleted":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume record not found.")

    # Authorization check: Candidate owns resume or is platform admin
    if str(resume.get("candidateId")) != str(user.id) and not user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You do not have permission to access this resume.",
        )

    return ResumeMetadataResponse(
        resume_id=resume_id,
        candidate_id=str(resume["candidateId"]),
        file_name=resume.get("fileName", "resume.pdf"),
        content_type=resume.get("contentType", "application/pdf"),
        storage_path=resume.get("storagePath", ""),
        file_size=resume.get("fileSize", 0),
        uploaded_at=resume.get("uploadedAt", ""),
        status=resume.get("status", "active"),
        version=resume.get("version", 1),
        download_url=f"/api/v1/resumes/{resume_id}/file",
    )


@router.get("/{resume_id}/file")
@router.get("/{resume_id}/download")
async def download_resume_file(
    resume_id: str,
    user: User = Depends(get_current_user),
):
    """
    Candidate Endpoint: Streams or downloads the candidate's own resume file.
    """
    firestore_repo = FirestoreResumeRepository()
    resume = await firestore_repo.get_resume(resume_id)
    if not resume or resume.get("status") == "deleted":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume document not found.")

    # Security check
    if str(resume.get("candidateId")) != str(user.id) and not user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You cannot download resumes belonging to another candidate.",
        )

    storage_path = resume.get("storagePath")
    storage_provider = GCSResumeStorageProvider()

    try:
        content = storage_provider.download_file(storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file artifact unavailable in storage.",
        )

    filename = resume.get("fileName", "resume.pdf")
    content_type = resume.get("contentType", "application/pdf")

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.delete("/{resume_id}", status_code=status.HTTP_200_OK)
async def delete_resume(
    resume_id: str,
    user: User = Depends(get_current_user),
):
    """
    Candidate Endpoint: Deletes/archives a resume version.
    """
    firestore_repo = FirestoreResumeRepository()
    resume = await firestore_repo.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    if str(resume.get("candidateId")) != str(user.id) and not user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

    await firestore_repo.delete_resume(resume_id)
    return {"message": "Resume deleted successfully.", "resume_id": resume_id}
