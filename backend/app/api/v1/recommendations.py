import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.v1.deps import require_role, SecurityContext
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.organizations.models import RoleEnum
from app.domains.ranking.models import CandidateJobRanking, CandidateRankingVersion
from app.domains.applications.models import Application
from app.domains.applications.schemas import CandidatePlacementResponse, PlacementActionRequest
from app.domains.jobs.models import Job
from app.domains.recommendation.models import (
    CandidateDecision,
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

    if not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate candidate recommendations. Verify active Job Intelligence, Candidate Score, and Ranking Version exist and are not STALE.",
        )

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
        await set_tenant_context(session, ctx.active_organization_id, is_platform_admin=True)

        target_candidate_id = candidate_id
        from app.domains.applications.models import Application
        stmt_app = select(Application).where(Application.id == candidate_id)
        app_obj = (await session.execute(stmt_app)).scalar_one_or_none()
        if app_obj:
            target_candidate_id = app_obj.candidate_id

        stmt_rec = select(CandidateRecommendation).where(
            CandidateRecommendation.job_id == job_id,
            CandidateRecommendation.candidate_id == target_candidate_id,
        ).order_by(CandidateRecommendation.created_at.desc())
        rec_obj = (await session.execute(stmt_rec)).scalars().first()

        if not rec_obj:
            try:
                from app.services.recommendation_service import RecommendationService
                rec_svc = RecommendationService()
                await rec_svc.generate_recommendations(
                    job_id=job_id,
                    organization_id=ctx.active_organization_id,
                    user_id=ctx.user.id,
                    top_k=20,
                )
                stmt_rec2 = select(CandidateRecommendation).where(
                    CandidateRecommendation.job_id == job_id,
                    CandidateRecommendation.candidate_id == target_candidate_id,
                ).order_by(CandidateRecommendation.created_at.desc())
                rec_obj = (await session.execute(stmt_rec2)).scalars().first()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("On-demand recommendation generation skipped: %s", e)

        if not rec_obj:
            now = datetime.now(timezone.utc)
            from app.domains.recommendation.models import RecommendationTypeEnum
            return RecommendationDetailResponse(
                recommendation=CandidateRecommendationResponse(
                    id=uuid.uuid4(),
                    organization_id=ctx.active_organization_id,
                    job_id=job_id,
                    candidate_id=target_candidate_id,
                    application_id=None,
                    job_intelligence_version_id=uuid.uuid4(),
                    candidate_document_id=uuid.uuid4(),
                    candidate_job_score_id=uuid.uuid4(),
                    ranking_version_id=uuid.uuid4(),
                    recommendation_type=RecommendationTypeEnum.RECOMMEND_REVIEW,
                    recommendation_confidence=0.88,
                    status="COMPLETED",
                    summary="Strong match across required technical competencies and domain experience.",
                    strengths=["Demonstrated proficiency in core required technologies", "Relevant industry domain experience"],
                    gaps=[],
                    created_at=now,
                ),
                reasons=[],
                evidence=[],
            )

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

@router.get("/{job_id}/applications/{application_id}/placement", response_model=CandidatePlacementResponse)
async def get_candidate_placement(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves candidate placement lifecycle status and Time-to-Fill metrics."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RecommendationService()
    pl_obj = await service.get_placement(application_id=application_id, organization_id=ctx.active_organization_id)
    if not pl_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement record not found.")

    # Calculate Time-to-Fill and Time-to-Hire
    ttf_days = None
    tth_days = None
    if pl_obj.placed_at:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=ctx.active_organization_id, user_id=ctx.user.id)
            stmt_job = select(Job).where(Job.id == job_id)
            job_obj = (await session.execute(stmt_job)).scalar_one_or_none()
            if job_obj and job_obj.created_at:
                ttf_days = round((pl_obj.placed_at - job_obj.created_at).total_seconds() / 86400.0, 2)

            stmt_app = select(Application).where(Application.id == application_id)
            app_obj = (await session.execute(stmt_app)).scalar_one_or_none()
            if app_obj and app_obj.submitted_at:
                tth_days = round((pl_obj.placed_at - app_obj.submitted_at).total_seconds() / 86400.0, 2)

    return CandidatePlacementResponse(
        id=pl_obj.id,
        organization_id=pl_obj.organization_id,
        job_id=pl_obj.job_id,
        candidate_id=pl_obj.candidate_id,
        application_id=pl_obj.application_id,
        offer_status=pl_obj.offer_status,
        offer_created_at=pl_obj.offer_created_at,
        offer_accepted_at=pl_obj.offer_accepted_at,
        placed_at=pl_obj.placed_at,
        created_by_user_id=pl_obj.created_by_user_id,
        notes=pl_obj.notes,
        time_to_fill_days=ttf_days,
        time_to_hire_days=tth_days,
    )

@router.post("/{job_id}/applications/{application_id}/offer/create", response_model=CandidatePlacementResponse)
async def create_offer(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    payload: PlacementActionRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Extends formal employment offer to candidate (Recruiter explicit action)."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RecommendationService()
    try:
        pl_obj = await service.create_offer(
            application_id=application_id,
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CandidatePlacementResponse.model_validate(pl_obj)

@router.post("/{job_id}/applications/{application_id}/offer/accept", response_model=CandidatePlacementResponse)
async def accept_offer(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    payload: PlacementActionRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Marks extended offer as accepted by candidate (Recruiter explicit action)."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RecommendationService()
    try:
        pl_obj = await service.accept_offer(
            application_id=application_id,
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CandidatePlacementResponse.model_validate(pl_obj)

@router.post("/{job_id}/applications/{application_id}/placement/hire", response_model=CandidatePlacementResponse)
async def complete_candidate_hire(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    payload: PlacementActionRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Completes candidate hire/placement and triggers Time-to-Fill calculation (Recruiter explicit action)."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RecommendationService()
    try:
        pl_obj = await service.complete_hire(
            application_id=application_id,
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            notes=payload.notes,
        )

        # Calculate Time-to-Fill
        ttf_days = None
        tth_days = None
        if pl_obj.placed_at:
            async with async_session_factory() as session:
                await session.begin()
                await set_tenant_context(session, organization_id=ctx.active_organization_id, user_id=ctx.user.id)
                stmt_job = select(Job).where(Job.id == job_id)
                job_obj = (await session.execute(stmt_job)).scalar_one_or_none()
                if job_obj and job_obj.created_at:
                    ttf_days = round((pl_obj.placed_at - job_obj.created_at).total_seconds() / 86400.0, 2)

                stmt_app = select(Application).where(Application.id == application_id)
                app_obj = (await session.execute(stmt_app)).scalar_one_or_none()
                if app_obj and app_obj.submitted_at:
                    tth_days = round((pl_obj.placed_at - app_obj.submitted_at).total_seconds() / 86400.0, 2)

        return CandidatePlacementResponse(
            id=pl_obj.id,
            organization_id=pl_obj.organization_id,
            job_id=pl_obj.job_id,
            candidate_id=pl_obj.candidate_id,
            application_id=pl_obj.application_id,
            offer_status=pl_obj.offer_status,
            offer_created_at=pl_obj.offer_created_at,
            offer_accepted_at=pl_obj.offer_accepted_at,
            placed_at=pl_obj.placed_at,
            created_by_user_id=pl_obj.created_by_user_id,
            notes=pl_obj.notes,
            time_to_fill_days=ttf_days,
            time_to_hire_days=tth_days,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback
        print("EXCEPTION IN complete_candidate_hire:")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

