from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.api.v1.deps import get_security_context, SecurityContext
from app.api.v1.schemas import DashboardMetricsResponse, JobResponse
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application
from app.domains.jobs.models import Job, JobStatusEnum

router = APIRouter(prefix="/dashboard", tags=["Recruiter Dashboard"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(ctx: SecurityContext = Depends(get_security_context)):
    """
    Returns real database metrics for recruiter dashboard.
    Counts real database records within active tenant RLS context.
    """
    if not ctx.active_organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-Organization-ID is required to retrieve workspace metrics.",
        )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        # 1. Real Active Jobs Count (PUBLISHED)
        stmt_active = select(func.count(Job.id)).where(
            Job.organization_id == ctx.active_organization_id,
            Job.status == JobStatusEnum.PUBLISHED,
        )
        active_jobs_count = (await session.execute(stmt_active)).scalar() or 0

        # 2. Real Draft Jobs Count
        stmt_draft = select(func.count(Job.id)).where(
            Job.organization_id == ctx.active_organization_id,
            Job.status == JobStatusEnum.DRAFT,
        )
        draft_jobs_count = (await session.execute(stmt_draft)).scalar() or 0

        # 3. Real Closed Jobs Count
        stmt_closed = select(func.count(Job.id)).where(
            Job.organization_id == ctx.active_organization_id,
            Job.status == JobStatusEnum.CLOSED,
        )
        closed_jobs_count = (await session.execute(stmt_closed)).scalar() or 0

        # 4. Real Total Applications Count
        stmt_apps = select(func.count(Application.id)).where(
            Application.organization_id == ctx.active_organization_id
        )
        total_applications_count = (await session.execute(stmt_apps)).scalar() or 0

        # 5. Recent 5 Jobs
        stmt_recent = (
            select(Job)
            .where(Job.organization_id == ctx.active_organization_id)
            .order_by(Job.created_at.desc())
            .limit(5)
        )
        recent_jobs = list((await session.execute(stmt_recent)).scalars().all())

        return DashboardMetricsResponse(
            organization_id=ctx.active_organization_id,
            active_jobs_count=active_jobs_count,
            draft_jobs_count=draft_jobs_count,
            closed_jobs_count=closed_jobs_count,
            total_applications_count=total_applications_count,
            recent_jobs=[JobResponse.model_validate(j) for j in recent_jobs],
        )
