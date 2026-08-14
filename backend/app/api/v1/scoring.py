import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import require_role, SecurityContext
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.organizations.models import RoleEnum
from app.domains.scoring.models import (
    CandidateFactorScore,
    CandidateHardRequirementResult,
    CandidateJobScore,
)
from app.domains.scoring.schemas import (
    CandidateFactorScoreResponse,
    CandidateJobScoreResponse,
    HardRequirementResultResponse,
    ScoreBreakdownDetailResponse,
    ScoringConfigurationResponse,
)
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/jobs", tags=["Candidate Deterministic Scoring Engine"])

class ProcessScoringRequest(BaseModel):
    candidate_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None

@router.post("/{job_id}/scoring/process", response_model=CandidateJobScoreResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_candidate_scoring(
    job_id: uuid.UUID,
    payload: ProcessScoringRequest,
    background_tasks: BackgroundTasks,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Triggers deterministic candidate scoring calculation.
    CRITICAL AI GOVERNANCE RULE:
    Contains ZERO LLM-generated overall scores, candidate rankings, Top-K calculations, or automatic status mutations.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = ScoringService()

    # Process scoring asynchronously via background tasks
    background_tasks.add_task(
        service.process_candidate_scoring,
        job_id=job_id,
        candidate_id=payload.candidate_id,
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
        application_id=payload.application_id,
    )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(CandidateJobScore).where(
            CandidateJobScore.job_id == job_id,
            CandidateJobScore.candidate_id == payload.candidate_id,
            CandidateJobScore.organization_id == ctx.active_organization_id,
        ).order_by(CandidateJobScore.created_at.desc())
        score_rec = (await session.execute(stmt)).scalars().first()

        if not score_rec:
            # Synchronous initial execution for immediate response in tests
            await service.process_candidate_scoring(
                job_id=job_id,
                candidate_id=payload.candidate_id,
                organization_id=ctx.active_organization_id,
                user_id=ctx.user.id,
                application_id=payload.application_id,
            )
            score_rec = (await session.execute(stmt)).scalars().first()

        return score_rec

@router.get("/{job_id}/scoring/{candidate_id}", response_model=CandidateJobScoreResponse)
async def get_candidate_score(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves master candidate score summary."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(CandidateJobScore).where(
            CandidateJobScore.job_id == job_id,
            CandidateJobScore.candidate_id == candidate_id,
            CandidateJobScore.organization_id == ctx.active_organization_id,
        ).order_by(CandidateJobScore.created_at.desc())
        score_rec = (await session.execute(stmt)).scalars().first()

        if not score_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate score record not found.")

        return CandidateJobScoreResponse.model_validate(score_rec)

@router.get("/{job_id}/scoring/{candidate_id}/breakdown", response_model=ScoreBreakdownDetailResponse)
async def get_candidate_score_breakdown(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves full explainable score breakdown, factor scores, and hard requirement results."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_s = select(CandidateJobScore).where(
            CandidateJobScore.job_id == job_id,
            CandidateJobScore.candidate_id == candidate_id,
            CandidateJobScore.organization_id == ctx.active_organization_id,
        ).order_by(CandidateJobScore.created_at.desc())
        score_rec = (await session.execute(stmt_s)).scalars().first()

        if not score_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate score record not found.")

        stmt_factors = select(CandidateFactorScore).where(CandidateFactorScore.candidate_job_score_id == score_rec.id)
        factors = list((await session.execute(stmt_factors)).scalars().all())

        stmt_hards = select(CandidateHardRequirementResult).where(CandidateHardRequirementResult.candidate_job_score_id == score_rec.id)
        hards = list((await session.execute(stmt_hards)).scalars().all())

        return ScoreBreakdownDetailResponse(
            score=CandidateJobScoreResponse.model_validate(score_rec),
            factor_scores=[CandidateFactorScoreResponse.model_validate(f) for f in factors],
            hard_requirement_results=[HardRequirementResultResponse.model_validate(h) for h in hards],
        )

@router.get("/{job_id}/scoring/configuration", response_model=ScoringConfigurationResponse)
async def get_active_scoring_configuration(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves active scoring configuration for the organization."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = ScoringService()
    config = await service.get_or_create_active_configuration(
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
    )
    return ScoringConfigurationResponse.model_validate(config)

@router.post("/{job_id}/scoring/recalculate", response_model=CandidateJobScoreResponse)
async def recalculate_candidate_score(
    job_id: uuid.UUID,
    payload: ProcessScoringRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Recalculates candidate score after configuration or feature match updates."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = ScoringService()
    success = await service.process_candidate_scoring(
        job_id=job_id,
        candidate_id=payload.candidate_id,
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
        application_id=payload.application_id,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Candidate scoring calculation failed.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_s = select(CandidateJobScore).where(
            CandidateJobScore.job_id == job_id,
            CandidateJobScore.candidate_id == payload.candidate_id,
            CandidateJobScore.organization_id == ctx.active_organization_id,
        ).order_by(CandidateJobScore.created_at.desc())
        return (await session.execute(stmt_s)).scalars().first()
