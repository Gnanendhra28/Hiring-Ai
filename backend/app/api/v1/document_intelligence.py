import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.api.v1.deps import get_current_user, require_role, SecurityContext
from app.core.config import settings
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application
from app.domains.document_intelligence.models import (
    CandidateDocument,
    CandidateEducation,
    CandidateExperience,
    CandidateExtractedFact,
    CandidateSkill,
    DocumentProcessingStatusEnum,
)
from app.domains.identity.models import User
from app.domains.organizations.models import RoleEnum
from app.services.document_processor import DocumentProcessorService

router = APIRouter(prefix="", tags=["Document Intelligence"])
processor_service = DocumentProcessorService()

# --- Pydantic Response Schemas ---
class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    file_name: str
    file_size_bytes: int
    processing_status: DocumentProcessingStatusEnum
    safe_error_message: str | None

class CandidateSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    raw_skill_name: str
    canonical_skill_name: str
    years_experience: float | None
    confidence: float
    evidence_text: str | None
    page_number: int | None

class CandidateExperienceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    job_title: str
    raw_start_date: str | None
    raw_end_date: str | None
    duration_months: int
    is_current: bool
    confidence: float
    evidence_text: str | None
    page_number: int | None

class CandidateEducationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution: str
    degree: str | None
    field_of_study: str | None
    confidence: float
    evidence_text: str | None
    page_number: int | None

class CandidateExtractedFactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fact_type: str
    raw_value: str
    canonical_value: str
    evidence_text: str | None
    page_number: int | None
    confidence: float

class DocumentIntelligenceEvidenceResponse(BaseModel):
    document_id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID
    processing_status: DocumentProcessingStatusEnum
    ocr_used: bool
    text_quality_score: float | None
    skills: list[CandidateSkillResponse]
    experiences: list[CandidateExperienceResponse]
    educations: list[CandidateEducationResponse]
    facts: list[CandidateExtractedFactResponse]

@router.post("/applications/{application_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_candidate_resume(
    application_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    Candidate endpoint: Uploads PDF resume document.
    Validates file size limit, MIME type, and PDF magic header. Triggers async document processing.
    """
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # 1. File Size Validation
    if file_size > settings.MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size ({file_size} bytes) exceeds configured maximum limit of {settings.MAX_RESUME_SIZE_BYTES} bytes (1 MB).",
        )

    # 2. MIME & Magic Header Validation (Must be PDF)
    if not file.filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents (.pdf) are supported.",
        )

    if not file_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed document: File content header is not a valid PDF file.",
        )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)

        # 3. Verify application ownership
        stmt_app = select(Application).where(Application.id == application_id, Application.candidate_id == user.id)
        app_rec = (await session.execute(stmt_app)).scalar_one_or_none()
        if not app_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found or access denied.")

        doc = CandidateDocument(
            organization_id=app_rec.organization_id,
            application_id=app_rec.id,
            candidate_id=user.id,
            file_name=file.filename or "resume.pdf",
            file_path=f"resumes/{app_rec.organization_id}/{user.id}/{file.filename}",
            file_size_bytes=file_size,
            mime_type="application/pdf",
            processing_status=DocumentProcessingStatusEnum.UPLOADED,
        )
        session.add(doc)
        await session.commit()
        doc_id = doc.id
        org_id = app_rec.organization_id

    # 4. Trigger Asynchronous Processing with RLS Tenant & Candidate parameters
    await processor_service.process_document(
        document_id=doc_id,
        organization_id=org_id,
        candidate_id=user.id,
        file_bytes=file_bytes,
    )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)
        stmt_created = select(CandidateDocument).where(CandidateDocument.id == doc_id)
        return (await session.execute(stmt_created)).scalar_one()

@router.get("/documents/{document_id}", response_model=DocumentUploadResponse)
async def get_document_status(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
):
    """Retrieves current processing status of a candidate document."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)

        stmt = select(CandidateDocument).where(CandidateDocument.id == document_id)
        doc = (await session.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate document not found.")

        return doc

@router.get("/applications/{application_id}/intelligence", response_model=DocumentIntelligenceEvidenceResponse)
async def get_application_document_intelligence(
    application_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Recruiter endpoint: Retrieves extracted structured candidate facts, skills, evidence quotes, and page numbers.
    Zero candidate overall matching score is included in Phase 7!
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        # 1. Verify application belongs to organization
        stmt_app = select(Application).where(Application.id == application_id, Application.organization_id == ctx.active_organization_id)
        app_rec = (await session.execute(stmt_app)).scalar_one_or_none()
        if not app_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found in active organization.")

        # 2. Fetch Document
        stmt_doc = select(CandidateDocument).where(CandidateDocument.application_id == application_id).order_by(CandidateDocument.created_at.desc())
        doc = (await session.execute(stmt_doc)).scalars().first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resume document found for this application.")

        # 3. Fetch Extracted Skills, Experiences, Educations, Facts
        stmt_skills = select(CandidateSkill).where(CandidateSkill.document_id == doc.id)
        skills = list((await session.execute(stmt_skills)).scalars().all())

        stmt_exp = select(CandidateExperience).where(CandidateExperience.document_id == doc.id)
        experiences = list((await session.execute(stmt_exp)).scalars().all())

        stmt_edu = select(CandidateEducation).where(CandidateEducation.document_id == doc.id)
        educations = list((await session.execute(stmt_edu)).scalars().all())

        stmt_facts = select(CandidateExtractedFact).where(CandidateExtractedFact.document_id == doc.id)
        facts = list((await session.execute(stmt_facts)).scalars().all())

        return DocumentIntelligenceEvidenceResponse(
            document_id=doc.id,
            candidate_id=doc.candidate_id,
            application_id=doc.application_id,
            processing_status=doc.processing_status,
            ocr_used=doc.ocr_used,
            text_quality_score=doc.text_quality_score,
            skills=skills,
            experiences=experiences,
            educations=educations,
            facts=facts,
        )
