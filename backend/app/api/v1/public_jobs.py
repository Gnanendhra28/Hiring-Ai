from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.v1.schemas import PublicJobListResponse, PublicJobResponse
from app.db.session import async_session_factory
from app.domains.jobs.models import Job, JobStatusEnum
from app.domains.organizations.models import Organization

router = APIRouter(prefix="/jobs/public", tags=["Public Job Directory"])

@router.get("", response_model=PublicJobListResponse)
@router.get("/", response_model=PublicJobListResponse, include_in_schema=False)
async def list_public_jobs(
    department_filter: str | None = Query(None, alias="department"),
    location_filter: str | None = Query(None, alias="location"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Public Endpoint: Lists open job requisitions (status == 'PUBLISHED' ONLY).
    Strictly filters out draft, paused, or closed jobs and internal recruiter notes.
    """
    async with async_session_factory() as session:
        from app.domains.jobs.models import JobVerificationStatusEnum

        stmt = (
            select(Job)
            .options(selectinload(Job.organization_id))
            .join(Organization, Job.organization_id == Organization.id)
            .where(
                Job.created_by_user_id.isnot(None),
                Job.status == JobStatusEnum.PUBLISHED,
                Job.verification_status == JobVerificationStatusEnum.APPROVED,
                Organization.is_active.is_(True),
            )
        )

        if department_filter:
            stmt = stmt.where(Job.department.ilike(f"%{department_filter}%"))
        if location_filter:
            stmt = stmt.where(Job.location.ilike(f"%{location_filter}%"))
        if search:
            stmt = stmt.where(Job.title.ilike(f"%{search}%") | Job.description.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            select(Job, Organization.name.label("org_name"))
            .join(Organization, Job.organization_id == Organization.id)
            .where(
                Job.created_by_user_id.isnot(None),
                Job.status == JobStatusEnum.PUBLISHED,
                Job.verification_status == JobVerificationStatusEnum.APPROVED,
                Organization.is_active.is_(True),
            )
            .order_by(Job.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        rows = result.all()

        public_items = [
            PublicJobResponse(
                id=job.id,
                title=job.title,
                slug=job.slug,
                organization_name=org_name,
                department=job.department,
                location=job.location,
                employment_type=job.employment_type,
                description=job.description,
                created_at=job.created_at,
            )
            for job, org_name in rows
        ]

        return PublicJobListResponse(
            items=public_items,
            total=total,
            page=page,
            page_size=page_size,
        )

@router.get("/{slug}", response_model=PublicJobResponse)
async def get_public_job_by_slug(slug: str):
    """
    Public Endpoint: Fetches detailed public job posting by slug.
    Returns 404 if job is not published.
    """
    async with async_session_factory() as session:
        stmt = (
            select(Job, Organization.name.label("org_name"))
            .join(Organization, Job.organization_id == Organization.id)
            .where(Job.slug == slug, Job.status == JobStatusEnum.PUBLISHED, Organization.is_active.is_(True))
        )
        result = await session.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Public job posting with slug '{slug}' not found or no longer active.",
            )

        job, org_name = row
        return PublicJobResponse(
            id=job.id,
            title=job.title,
            slug=job.slug,
            organization_name=org_name,
            department=job.department,
            location=job.location,
            employment_type=job.employment_type,
            description=job.description,
            created_at=job.created_at,
        )
