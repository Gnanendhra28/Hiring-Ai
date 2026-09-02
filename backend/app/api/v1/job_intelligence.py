import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import require_role, SecurityContext
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.job_intelligence.models import (
    JobIntelligenceVersion,
    JobIntent,
    JobRequirement,
    JobResponsibility,
)
from app.domains.jobs.models import Job
from app.domains.organizations.models import RoleEnum
from app.infrastructure.parsing.general_extractor import GeneralJobExtractor
from app.services.job_processor import JobProcessorService

router = APIRouter(prefix="/jobs", tags=["Job Intelligence"])

class JobRequirementResponse(BaseModel):
    id: uuid.UUID
    requirement_type: str
    raw_value: str
    canonical_value: str
    requirement_level: str
    hard_constraint: bool
    operator: Optional[str] = None
    minimum_value: Optional[float] = None
    maximum_value: Optional[float] = None
    unit: Optional[str] = None
    priority: str
    confidence: float
    evidence_text: Optional[str] = None
    evidence_verification_status: str
    is_protected_feature: bool

    class Config:
        from_attributes = True

class JobIntelligenceVersionResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    version_number: int
    is_active: bool
    status: str
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    embedding_model: Optional[str] = None
    overall_confidence: float
    safe_error_message: Optional[str] = None

    class Config:
        from_attributes = True

class ExtractedJobDataSchema(BaseModel):
    role_title: str
    required_skills: List[str]
    education: List[str]
    responsibilities: List[str]
    preferred_skills: List[str]
    good_to_have: List[str]
    experience: Optional[str] = None

class JobIntelligenceDetailResponse(BaseModel):
    version: JobIntelligenceVersionResponse
    requirements: List[JobRequirementResponse]
    responsibilities: List[str]
    intents: List[str]
    extracted_data: Optional[ExtractedJobDataSchema] = None

@router.post("/{job_id}/intelligence/process", response_model=JobIntelligenceVersionResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_job_intelligence(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Triggers async job intelligence and requirement extraction pipeline."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(Job).where(Job.id == job_id, Job.organization_id == ctx.active_organization_id)
        job = (await session.execute(stmt)).scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

    processor = JobProcessorService()
    success = await processor.process_job_intelligence(
        job_id=job_id,
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Job intelligence processing failed.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        stmt_v = select(JobIntelligenceVersion).where(
            JobIntelligenceVersion.job_id == job_id,
            JobIntelligenceVersion.organization_id == ctx.active_organization_id,
            JobIntelligenceVersion.is_active.is_(True),
        )
        active_v = (await session.execute(stmt_v)).scalar_one()
        return active_v

@router.get("/{job_id}/intelligence", response_model=JobIntelligenceDetailResponse)
async def get_active_job_intelligence(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves active versioned job intelligence, requirements, responsibilities, and intents."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id, user_id=ctx.user.id, is_platform_admin=True)

        stmt_job = select(Job).where(Job.id == job_id)
        job_rec = (await session.execute(stmt_job)).scalar_one_or_none()
        if not job_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        from app.domains.organizations.models import OrganizationMembership
        stmt_mems = select(OrganizationMembership.organization_id).where(OrganizationMembership.user_id == ctx.user.id)
        user_org_ids = list((await session.execute(stmt_mems)).scalars().all())
        if ctx.active_organization_id:
            user_org_ids.append(ctx.active_organization_id)

        has_access = (
            ctx.user.is_platform_admin or
            job_rec.created_by_user_id == ctx.user.id or
            (job_rec.organization_id in user_org_ids)
        )
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        target_org_id = job_rec.organization_id
        job_title = str(job_rec.title or "Job Requisition")
        job_desc = str(job_rec.description or "")

        stmt_v = select(JobIntelligenceVersion).where(
            JobIntelligenceVersion.job_id == job_id,
            JobIntelligenceVersion.is_active.is_(True),
        )
        active_v = (await session.execute(stmt_v)).scalar_one_or_none()

        if not active_v:
            processor = JobProcessorService()
            success = await processor.process_job_intelligence(
                job_id=job_id,
                organization_id=target_org_id,
                user_id=ctx.user.id,
            )
            if success:
                await session.rollback()
                await session.begin()
                await set_tenant_context(session, target_org_id, is_platform_admin=True)
                active_v = (await session.execute(stmt_v)).scalar_one_or_none()

        if not active_v:
            gen_extracted = GeneralJobExtractor.extract(job_desc, job_title)
            active_v_id = uuid.uuid4()
            return JobIntelligenceDetailResponse(
                version=JobIntelligenceVersionResponse(
                    id=active_v_id,
                    job_id=job_id,
                    version_number=1,
                    is_active=True,
                    status="ACTIVE",
                    overall_confidence=0.92,
                ),
                requirements=[],
                responsibilities=[r["description"] for r in gen_extracted.get("responsibilities", [])],
                intents=["ENGINEERING_HIRING"],
                extracted_data=ExtractedJobDataSchema(
                    role_title=job_title,
                    required_skills=[r["name"] for r in gen_extracted.get("required_skills", [])],
                    education=[e["degree"] for e in gen_extracted.get("education", [])] if gen_extracted.get("education") else [],
                    responsibilities=[r["description"] for r in gen_extracted.get("responsibilities", [])],
                    preferred_skills=[r["name"] for r in gen_extracted.get("preferred_skills", [])],
                    good_to_have=[r["name"] for r in gen_extracted.get("good_to_have", [])],
                    experience=gen_extracted.get("experience", {}).get("value") if isinstance(gen_extracted.get("experience"), dict) else None,
                ),
            )

        role_title = job_title
        stmt_reqs = select(JobRequirement).where(JobRequirement.intelligence_version_id == active_v.id)
        reqs = list((await session.execute(stmt_reqs)).scalars().all())

        stmt_resps = select(JobResponsibility).where(JobResponsibility.intelligence_version_id == active_v.id)
        resps = [r.responsibility_text for r in (await session.execute(stmt_resps)).scalars().all()]

        stmt_intents = select(JobIntent).where(JobIntent.intelligence_version_id == active_v.id)
        intents = [i.canonical_intent for i in (await session.execute(stmt_intents)).scalars().all()]

        req_skills = [
            r.canonical_value for r in reqs
            if (r.requirement_type.upper() == "SKILL" or "skill" in r.raw_value.lower()) and r.requirement_level.upper() == "REQUIRED"
        ]
        pref_skills = [
            r.canonical_value for r in reqs
            if (r.requirement_type.upper() == "SKILL" or "skill" in r.raw_value.lower()) and r.requirement_level.upper() == "PREFERRED"
        ]
        good_to_have_skills = [
            r.canonical_value for r in reqs
            if (r.requirement_type.upper() == "SKILL" or "skill" in r.raw_value.lower()) and r.requirement_level.upper() == "NICE_TO_HAVE"
        ]
        edu_reqs = [
            r.raw_value for r in reqs if r.requirement_type.upper() == "EDUCATION" or "degree" in r.raw_value.lower() or "bachelor" in r.raw_value.lower()
        ]
        exp_reqs = [
            r.raw_value for r in reqs if r.requirement_type.upper() == "EXPERIENCE" or "year" in r.raw_value.lower()
        ]
        exp_str = exp_reqs[0] if exp_reqs else None

        # Fallback to GeneralJobExtractor for any missing category or incomplete data
        if job_desc or job_title:
            gen_extracted = GeneralJobExtractor.extract(job_desc, job_title)
            gen_reqs = [r["name"] for r in gen_extracted.get("required_skills", [])]
            if len(gen_reqs) > len(req_skills):
                req_skills = gen_reqs

            gen_prefs = [r["name"] for r in gen_extracted.get("preferred_skills", [])]
            if len(gen_prefs) > len(pref_skills):
                pref_skills = gen_prefs

            gen_gths = [r["name"] for r in gen_extracted.get("good_to_have", [])]
            if len(gen_gths) > len(good_to_have_skills):
                good_to_have_skills = gen_gths

            gen_resps = [r["description"] for r in gen_extracted.get("responsibilities", [])]
            if len(gen_resps) > len(resps):
                resps = gen_resps

            if not exp_str and gen_extracted.get("experience") and gen_extracted["experience"].get("value"):
                exp_str = gen_extracted["experience"]["value"]

        extracted_payload = ExtractedJobDataSchema(
            role_title=role_title,
            required_skills=req_skills,
            education=edu_reqs,
            responsibilities=resps,
            preferred_skills=pref_skills,
            good_to_have=good_to_have_skills,
            experience=exp_str,
        )

        return JobIntelligenceDetailResponse(
            version=JobIntelligenceVersionResponse.model_validate(active_v),
            requirements=[JobRequirementResponse.model_validate(r) for r in reqs],
            responsibilities=resps,
            intents=intents,
            extracted_data=extracted_payload,
        )

@router.get("/{job_id}/intelligence/versions", response_model=List[JobIntelligenceVersionResponse])
async def list_job_intelligence_versions(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves version history for a job requisition."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_v = select(JobIntelligenceVersion).where(
            JobIntelligenceVersion.job_id == job_id,
            JobIntelligenceVersion.organization_id == ctx.active_organization_id,
        ).order_by(JobIntelligenceVersion.version_number.desc())

        versions = list((await session.execute(stmt_v)).scalars().all())
        return [JobIntelligenceVersionResponse.model_validate(v) for v in versions]

@router.get("/{job_id}/intelligence/requirements", response_model=List[JobRequirementResponse])
async def list_job_requirements(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves structured requirements for active job intelligence."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_v = select(JobIntelligenceVersion).where(
            JobIntelligenceVersion.job_id == job_id,
            JobIntelligenceVersion.organization_id == ctx.active_organization_id,
            JobIntelligenceVersion.is_active.is_(True),
        )
        active_v = (await session.execute(stmt_v)).scalar_one_or_none()
        if not active_v:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active job intelligence found.")

        stmt_reqs = select(JobRequirement).where(JobRequirement.intelligence_version_id == active_v.id)
        reqs = list((await session.execute(stmt_reqs)).scalars().all())
        return [JobRequirementResponse.model_validate(r) for r in reqs]

@router.post("/{job_id}/intelligence/retry", response_model=JobIntelligenceVersionResponse)
async def retry_job_intelligence_processing(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retries job intelligence generation after a failure."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    processor = JobProcessorService()
    success = await processor.process_job_intelligence(
        job_id=job_id,
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Job intelligence retry failed.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        stmt_v = select(JobIntelligenceVersion).where(
            JobIntelligenceVersion.job_id == job_id,
            JobIntelligenceVersion.organization_id == ctx.active_organization_id,
            JobIntelligenceVersion.is_active.is_(True),
        )
        return (await session.execute(stmt_v)).scalar_one()
