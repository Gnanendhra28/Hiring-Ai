import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import require_role, SecurityContext
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.matching.models import (
    CandidateJobMatch,
    CandidateRequirementMatch,
    CandidateSemanticMatch,
)
from app.domains.matching.schemas import (
    CandidateJobMatchResponse,
    FeatureMatchDetailResponse,
    RequirementMatchResponse,
    SemanticMatchResponse,
)
from app.domains.organizations.models import RoleEnum
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/jobs", tags=["Candidate Feature Matching"])

class ProcessMatchingRequest(BaseModel):
    candidate_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None

@router.post("/{job_id}/matching/process", response_model=CandidateJobMatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_candidate_matching(
    job_id: uuid.UUID,
    payload: ProcessMatchingRequest,
    background_tasks: BackgroundTasks,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Triggers asynchronous candidate feature retrieval & requirement matching engine.
    Matches Candidate AI Intelligence (Phase 7) against Versioned Job Intelligence (Phase 8).
    CRITICAL AI GOVERNANCE RULE: Contains ZERO overall match score or candidate ranking.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = MatchingService()
    
    # Process matching asynchronously via FastAPI BackgroundTasks
    background_tasks.add_task(
        service.process_candidate_matching,
        job_id=job_id,
        candidate_id=payload.candidate_id,
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
        application_id=payload.application_id,
    )

    # Return initial or existing match status record synchronously
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(CandidateJobMatch).where(
            CandidateJobMatch.job_id == job_id,
            CandidateJobMatch.candidate_id == payload.candidate_id,
            CandidateJobMatch.organization_id == ctx.active_organization_id,
        )
        match_rec = (await session.execute(stmt)).scalars().first()

        if not match_rec:
            # Execute synchronously for immediate initial creation in tests
            await service.process_candidate_matching(
                job_id=job_id,
                candidate_id=payload.candidate_id,
                organization_id=ctx.active_organization_id,
                user_id=ctx.user.id,
                application_id=payload.application_id,
            )
            match_rec = (await session.execute(stmt)).scalars().first()

        return match_rec

@router.get("/{job_id}/matching/status", response_model=List[CandidateJobMatchResponse])
async def get_job_matching_statuses(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves list of candidate matching records for a job requisition."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(CandidateJobMatch).where(
            CandidateJobMatch.job_id == job_id,
            CandidateJobMatch.organization_id == ctx.active_organization_id,
        )
        matches = list((await session.execute(stmt)).scalars().all())
        return [CandidateJobMatchResponse.model_validate(m) for m in matches]

@router.get("/{job_id}/matching/features/{candidate_id}", response_model=FeatureMatchDetailResponse)
async def get_candidate_feature_matches(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves full feature-level match details between candidate and job requisition."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_m = select(CandidateJobMatch).where(
            CandidateJobMatch.job_id == job_id,
            CandidateJobMatch.candidate_id == candidate_id,
            CandidateJobMatch.organization_id == ctx.active_organization_id,
        )
        match_rec = (await session.execute(stmt_m)).scalar_one_or_none()

        if not match_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matching record not found.")

        stmt_reqs = select(CandidateRequirementMatch).where(CandidateRequirementMatch.match_id == match_rec.id)
        req_matches = list((await session.execute(stmt_reqs)).scalars().all())

        stmt_sems = select(CandidateSemanticMatch).where(CandidateSemanticMatch.match_id == match_rec.id)
        sem_matches = list((await session.execute(stmt_sems)).scalars().all())

        return FeatureMatchDetailResponse(
            match=CandidateJobMatchResponse.model_validate(match_rec),
            requirement_matches=[RequirementMatchResponse.model_validate(r) for r in req_matches],
            semantic_matches=[SemanticMatchResponse.model_validate(s) for s in sem_matches],
        )

@router.get("/{job_id}/matching/requirements/{candidate_id}", response_model=List[RequirementMatchResponse])
async def get_candidate_requirement_matches(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves requirement match items for a specific candidate."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_m = select(CandidateJobMatch).where(
            CandidateJobMatch.job_id == job_id,
            CandidateJobMatch.candidate_id == candidate_id,
            CandidateJobMatch.organization_id == ctx.active_organization_id,
        )
        match_rec = (await session.execute(stmt_m)).scalar_one_or_none()

        if not match_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matching record not found.")

        stmt_reqs = select(CandidateRequirementMatch).where(CandidateRequirementMatch.match_id == match_rec.id)
        req_matches = list((await session.execute(stmt_reqs)).scalars().all())
        return [RequirementMatchResponse.model_validate(r) for r in req_matches]

@router.get("/{job_id}/matching/semantic/{candidate_id}", response_model=List[SemanticMatchResponse])
async def get_candidate_semantic_matches(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves context-aware semantic similarity scores for a specific candidate."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_m = select(CandidateJobMatch).where(
            CandidateJobMatch.job_id == job_id,
            CandidateJobMatch.candidate_id == candidate_id,
            CandidateJobMatch.organization_id == ctx.active_organization_id,
        )
        match_rec = (await session.execute(stmt_m)).scalar_one_or_none()

        if not match_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matching record not found.")

        stmt_sems = select(CandidateSemanticMatch).where(CandidateSemanticMatch.match_id == match_rec.id)
        sem_matches = list((await session.execute(stmt_sems)).scalars().all())
        return [SemanticMatchResponse.model_validate(s) for s in sem_matches]

@router.post("/{job_id}/matching/retry", response_model=CandidateJobMatchResponse)
async def retry_candidate_matching(
    job_id: uuid.UUID,
    payload: ProcessMatchingRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retries candidate feature matching pipeline after a failure."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = MatchingService()
    success = await service.process_candidate_matching(
        job_id=job_id,
        candidate_id=payload.candidate_id,
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
        application_id=payload.application_id,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Candidate matching retry failed.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_m = select(CandidateJobMatch).where(
            CandidateJobMatch.job_id == job_id,
            CandidateJobMatch.candidate_id == payload.candidate_id,
            CandidateJobMatch.organization_id == ctx.active_organization_id,
        )
        return (await session.execute(stmt_m)).scalar_one()
