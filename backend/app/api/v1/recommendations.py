import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.v1.deps import require_role, SecurityContext
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.organizations.models import RoleEnum
from app.domains.ranking.models import CandidateJobRanking, CandidateRankingVersion
from app.domains.recommendation.models import (
    CandidateDecisionAudit,
    CandidateRecommendation,
    CandidateRecommendationEvidence,
    CandidateRecommendationReason,
)
from app.domains.recommendation.schemas import (
    CandidateDecisionAuditResponse,
    CandidateDecisionResponse,
    CandidateRecommendationResponse,
    GenerateRecommendationRequest,
    RecommendationDetailResponse,
    RecommendationEvidenceResponse,
    RecommendationReasonResponse,
    RecruiterDecisionRequest,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/jobs", tags=["Candidate Recommendation & Decision Workflow Engine"])

@router.post("/{job_id}/recommendations/generate", response_model=List[CandidateRecommendationResponse], status_code=status.HTTP_201_CREATED)
async def generate_job_recommendations(
    job_id: uuid.UUID,
    payload: GenerateRecommendationRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Generates AI candidate recommendations for Top-K candidates.
    CRITICAL AI GOVERNANCE RULE:
    AI ASSISTS. RECRUITER DECIDES.
    Contains ZERO automated candidate hiring/rejection or application status mutations.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RecommendationService()

    # Determine candidate IDs to generate recommendations for
    candidate_ids = []
    if payload.candidate_id:
        candidate_ids = [payload.candidate_id]
    else:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, ctx.active_organization_id)

            stmt_v = select(CandidateRankingVersion).where(
                CandidateRankingVersion.job_id == job_id,
                CandidateRankingVersion.organization_id == ctx.active_organization_id,
            ).order_by(CandidateRankingVersion.ranking_version.desc())
            ranking_v = (await session.execute(stmt_v)).scalars().first()

            if not ranking_v:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Execute Phase 9C Candidate Ranking first.")

            stmt_top = select(CandidateJobRanking.candidate_id).where(
                CandidateJobRanking.ranking_version_id == ranking_v.id,
                CandidateJobRanking.organization_id == ctx.active_organization_id,
                CandidateJobRanking.is_top_k.is_(True),
            )
            candidate_ids = list((await session.execute(stmt_top)).scalars().all())

    results = []
    for cand_id in candidate_ids:
        rec = await service.generate_recommendation(
            job_id=job_id,
            candidate_id=cand_id,
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
        )
        if rec:
            results.append(CandidateRecommendationResponse.model_validate(rec))

    return results

@router.get("/{job_id}/recommendations", response_model=List[CandidateRecommendationResponse])
async def get_job_recommendations(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves all active candidate recommendations for a job."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(CandidateRecommendation).where(
            CandidateRecommendation.job_id == job_id,
            CandidateRecommendation.organization_id == ctx.active_organization_id,
        ).order_by(CandidateRecommendation.created_at.desc())

        recs = list((await session.execute(stmt)).scalars().all())
        return [CandidateRecommendationResponse.model_validate(r) for r in recs]

@router.get("/{job_id}/recommendations/{candidate_id}", response_model=RecommendationDetailResponse)
async def get_candidate_recommendation_detail(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves detailed recommendation, explainable reason codes, and evidence citations."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_rec = select(CandidateRecommendation).where(
            CandidateRecommendation.job_id == job_id,
            CandidateRecommendation.candidate_id == candidate_id,
            CandidateRecommendation.organization_id == ctx.active_organization_id,
        ).order_by(CandidateRecommendation.created_at.desc())
        rec_obj = (await session.execute(stmt_rec)).scalars().first()

        if not rec_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation record not found.")

        stmt_reasons = select(CandidateRecommendationReason).where(CandidateRecommendationReason.recommendation_id == rec_obj.id)
        reasons = list((await session.execute(stmt_reasons)).scalars().all())

        stmt_evidence = select(CandidateRecommendationEvidence).where(CandidateRecommendationEvidence.recommendation_id == rec_obj.id)
        evidence = list((await session.execute(stmt_evidence)).scalars().all())

        return RecommendationDetailResponse(
            recommendation=CandidateRecommendationResponse.model_validate(rec_obj),
            reasons=[RecommendationReasonResponse.model_validate(r) for r in reasons],
            evidence=[RecommendationEvidenceResponse.model_validate(e) for e in evidence],
        )

@router.post("/{job_id}/recommendations/{candidate_id}/regenerate", response_model=CandidateRecommendationResponse)
async def regenerate_candidate_recommendation(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Regenerates AI recommendation narrative for a candidate."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RecommendationService()
    rec_obj = await service.generate_recommendation(
        job_id=job_id,
        candidate_id=candidate_id,
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
    )

    if not rec_obj:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to regenerate candidate recommendation.")

    return CandidateRecommendationResponse.model_validate(rec_obj)

@router.post("/{job_id}/applications/{application_id}/decision", response_model=CandidateDecisionResponse)
async def record_recruiter_decision(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    payload: RecruiterDecisionRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Records an explicit human recruiter decision (ADVANCE, REJECT, HOLD, REQUEST_MORE_INFORMATION).
    CRITICAL AI GOVERNANCE RULE:
    Executed ONLY by explicit human recruiter authorization.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RecommendationService()
    dec_obj = await service.record_recruiter_decision(
        application_id=application_id,
        decision=payload.decision,
        organization_id=ctx.active_organization_id,
        user_id=ctx.user.id,
        decision_reason=payload.decision_reason,
    )

    if not dec_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found.")

    return CandidateDecisionResponse.model_validate(dec_obj)

@router.get("/{job_id}/applications/{application_id}/decision-history", response_model=List[CandidateDecisionAuditResponse])
async def get_decision_history(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves immutable audit history of recruiter decisions for an application."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(CandidateDecisionAudit).where(
            CandidateDecisionAudit.application_id == application_id,
            CandidateDecisionAudit.organization_id == ctx.active_organization_id,
        ).order_by(CandidateDecisionAudit.decided_at.asc())

        audits = list((await session.execute(stmt)).scalars().all())
        return [CandidateDecisionAuditResponse.model_validate(a) for a in audits]
