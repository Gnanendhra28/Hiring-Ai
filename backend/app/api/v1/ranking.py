import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func

from app.api.v1.deps import require_role, SecurityContext
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.organizations.models import RoleEnum
from app.domains.ranking.models import CandidateJobRanking, CandidateRankingVersion
from app.domains.ranking.schemas import (
    CandidateJobRankingResponse,
    CandidateRankingVersionResponse,
    GenerateRankingRequest,
    RankingListPaginatedResponse,
    TopKRankingResponse,
)
from app.services.ranking_service import RankingService

router = APIRouter(prefix="/jobs", tags=["Candidate Deterministic Ranking Engine"])

@router.post("/{job_id}/ranking/generate", response_model=CandidateRankingVersionResponse, status_code=status.HTTP_201_CREATED)
async def generate_candidate_ranking(
    job_id: uuid.UUID,
    payload: GenerateRankingRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Generates a deterministic candidate ranking snapshot.
    CRITICAL AI GOVERNANCE RULE:
    Zero LLM calls. Consumes authoritative Phase 9B candidate scores only.
    Contains ZERO automated application status mutation logic.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RankingService()
    ranking_v = await service.generate_ranking_snapshot(
        job_id=job_id,
        organization_id=ctx.active_organization_id,
        top_k=payload.top_k,
        user_id=ctx.user.id,
    )

    if not ranking_v:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate candidate ranking snapshot. Verify Job Intelligence is active and not STALE, and candidate scores exist.",
        )

    return CandidateRankingVersionResponse.model_validate(ranking_v)

@router.get("/{job_id}/ranking", response_model=RankingListPaginatedResponse)
async def get_candidate_rankings(
    job_id: uuid.UUID,
    version_number: Optional[int] = Query(None, description="Ranking snapshot version number. Defaults to latest version."),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves paginated candidate rankings for a job (sorted by rank_position ASC)."""
    async with async_session_factory() as session:
        await session.begin()

        target_org_id = ctx.active_organization_id
        if not target_org_id:
            from app.domains.organizations.models import OrganizationMembership
            stmt_mem = select(OrganizationMembership.organization_id).where(OrganizationMembership.user_id == ctx.user.id)
            target_org_id = (await session.execute(stmt_mem)).scalars().first()

        await set_tenant_context(session, target_org_id, user_id=ctx.user.id, is_platform_admin=True)

        from app.domains.jobs.models import Job
        stmt_job = select(Job).where(Job.id == job_id)
        job_rec = (await session.execute(stmt_job)).scalar_one_or_none()
        if not job_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job requisition not found.")

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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job requisition not found.")

        # 1. Fetch Target Ranking Version
        stmt_v = select(CandidateRankingVersion).where(
            CandidateRankingVersion.job_id == job_id,
        )
        if version_number is not None:
            stmt_v = stmt_v.where(CandidateRankingVersion.ranking_version == version_number)
        else:
            stmt_v = stmt_v.order_by(CandidateRankingVersion.ranking_version.desc())

        ranking_v = (await session.execute(stmt_v)).scalars().first()

        if not ranking_v:
            return RankingListPaginatedResponse(
                ranking_version=None,
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )

        # 2. Query Paginated Candidate Job Rankings
        stmt_count = select(func.count(CandidateJobRanking.id)).where(
            CandidateJobRanking.ranking_version_id == ranking_v.id,
        )
        if target_org_id:
            stmt_count = stmt_count.where(CandidateJobRanking.organization_id == target_org_id)
        total = (await session.execute(stmt_count)).scalar() or 0

        offset = (page - 1) * page_size
        stmt_items = select(CandidateJobRanking).where(
            CandidateJobRanking.ranking_version_id == ranking_v.id,
        )
        if target_org_id:
            stmt_items = stmt_items.where(CandidateJobRanking.organization_id == target_org_id)
        stmt_items = stmt_items.order_by(CandidateJobRanking.rank_position.asc()).offset(offset).limit(page_size)

        items = list((await session.execute(stmt_items)).scalars().all())
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return RankingListPaginatedResponse(
            ranking_version=CandidateRankingVersionResponse.model_validate(ranking_v),
            items=[CandidateJobRankingResponse.model_validate(it) for it in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

@router.get("/{job_id}/ranking/versions", response_model=List[CandidateRankingVersionResponse])
async def get_ranking_versions(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves all historical ranking snapshot versions for a job."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(CandidateRankingVersion).where(
            CandidateRankingVersion.job_id == job_id,
            CandidateRankingVersion.organization_id == ctx.active_organization_id,
        ).order_by(CandidateRankingVersion.ranking_version.desc())

        versions = list((await session.execute(stmt)).scalars().all())
        return [CandidateRankingVersionResponse.model_validate(v) for v in versions]

@router.get("/{job_id}/ranking/top-k", response_model=TopKRankingResponse)
async def get_top_k_rankings(
    job_id: uuid.UUID,
    limit: Optional[int] = Query(None, ge=1, le=500, description="Override Top-K limit filter for display"),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves Top-K eligible candidate rankings for a job."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_v = select(CandidateRankingVersion).where(
            CandidateRankingVersion.job_id == job_id,
            CandidateRankingVersion.organization_id == ctx.active_organization_id,
        ).order_by(CandidateRankingVersion.ranking_version.desc())

        ranking_v = (await session.execute(stmt_v)).scalars().first()

        if not ranking_v:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ranking snapshot version found for job.")

        target_limit = limit if limit is not None else ranking_v.top_k

        stmt_top_k = select(CandidateJobRanking).where(
            CandidateJobRanking.ranking_version_id == ranking_v.id,
            CandidateJobRanking.organization_id == ctx.active_organization_id,
            CandidateJobRanking.is_top_k.is_(True),
        ).order_by(CandidateJobRanking.rank_position.asc()).limit(target_limit)

        top_k_items = list((await session.execute(stmt_top_k)).scalars().all())

        return TopKRankingResponse(
            ranking_version=CandidateRankingVersionResponse.model_validate(ranking_v),
            top_k_candidates=[CandidateJobRankingResponse.model_validate(it) for it in top_k_items],
        )

@router.get("/{job_id}/ranking/candidates/{candidate_id}", response_model=CandidateJobRankingResponse)
async def get_candidate_rank_detail(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Retrieves specific candidate rank position in latest ranking snapshot."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt_v = select(CandidateRankingVersion).where(
            CandidateRankingVersion.job_id == job_id,
            CandidateRankingVersion.organization_id == ctx.active_organization_id,
        ).order_by(CandidateRankingVersion.ranking_version.desc())

        ranking_v = (await session.execute(stmt_v)).scalars().first()

        if not ranking_v:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ranking snapshot version found for job.")

        stmt_item = select(CandidateJobRanking).where(
            CandidateJobRanking.ranking_version_id == ranking_v.id,
            CandidateJobRanking.candidate_id == candidate_id,
            CandidateJobRanking.organization_id == ctx.active_organization_id,
        )
        item = (await session.execute(stmt_item)).scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found in current ranking snapshot.")

        return CandidateJobRankingResponse.model_validate(item)
