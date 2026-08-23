import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from slugify import slugify
from sqlalchemy import delete, func, select, update

from app.api.v1.deps import get_optional_security_context, get_security_context, require_role, SecurityContext
from app.api.v1.schemas import (
    ApplicationDecisionRequest,
    ApplicationListResponse,
    ApplicationResponse,
    JobCreateRequest,
    JobListResponse,
    JobResponse,
    JobUpdateRequest,
)
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application, ApplicationStatusEnum
from app.domains.audit.models import AuditLog
from app.domains.job_intelligence.models import JobIntelligenceVersion, JobIntelligenceVersionStatusEnum
from app.domains.jobs.models import Job, JobStatusEnum, JobVerificationStatusEnum
from app.domains.organizations.models import RoleEnum

router = APIRouter(prefix="/jobs", tags=["Job Workspace"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_job(
    payload: JobCreateRequest,
    ctx: SecurityContext = Depends(get_security_context),
):
    """Creates a new Job Posting in DRAFT or PENDING_VERIFICATION state awaiting verification."""
    if not ctx.user.is_platform_admin and ctx.role == RoleEnum.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Access Denied: Action requires one of ['ORGANIZATION_ADMIN', 'RECRUITER'].",
        )

    async with async_session_factory() as session:
        await session.begin()

        from app.domains.organizations.models import MembershipStatusEnum, Organization, OrganizationMembership

        org_id = ctx.active_organization_id

        if not org_id:
            # Check for any active recruiter or admin membership
            stmt_rec = select(OrganizationMembership).where(
                OrganizationMembership.user_id == ctx.user.id,
                OrganizationMembership.status == MembershipStatusEnum.ACTIVE,
                OrganizationMembership.role.in_([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER]),
            )
            rec_mem = (await session.execute(stmt_rec)).scalars().first()

            if rec_mem:
                org_id = rec_mem.organization_id
            else:
                # Retrieve or create default active Organization
                stmt_org = select(Organization).where(Organization.is_active.is_(True))
                default_org = (await session.execute(stmt_org)).scalars().first()
                if not default_org:
                    default_org = Organization(
                        name="Enterprise Talent OS",
                        slug=f"enterprise-talent-os-{uuid.uuid4().hex[:6]}",
                        is_active=True,
                    )
                    session.add(default_org)
                    await session.flush()

                await set_tenant_context(session, default_org.id)

                stmt_mem_any = select(OrganizationMembership).where(
                    OrganizationMembership.user_id == ctx.user.id,
                    OrganizationMembership.organization_id == default_org.id,
                )
                user_mem = (await session.execute(stmt_mem_any)).scalars().first()
                if user_mem:
                    user_mem.role = RoleEnum.RECRUITER
                    user_mem.status = MembershipStatusEnum.ACTIVE
                else:
                    new_mem = OrganizationMembership(
                        organization_id=default_org.id,
                        user_id=ctx.user.id,
                        role=RoleEnum.RECRUITER,
                        status=MembershipStatusEnum.ACTIVE,
                    )
                    session.add(new_mem)

                await session.commit()
                await session.begin()
                org_id = default_org.id

        await set_tenant_context(session, org_id)

        job_slug = payload.slug or slugify(payload.title)
        full_slug = f"{job_slug}-{uuid.uuid4().hex[:6]}"

        job = Job(
            organization_id=org_id,
            title=payload.title,
            slug=full_slug,
            description=payload.description,
            department=payload.department,
            location=payload.location,
            employment_type=payload.employment_type,
            status=payload.status or JobStatusEnum.DRAFT,
            verification_status=payload.verification_status or JobVerificationStatusEnum.DRAFT,
            salary=payload.salary,
            company_website=payload.company_website,
            created_by_user_id=ctx.user.id,
        )
        session.add(job)

        audit = AuditLog(
            organization_id=org_id,
            user_id=ctx.user.id,
            action="job.create",
            resource_type="job",
            resource_id=str(job.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, org_id)
        stmt_res = select(Job).where(Job.id == job.id)
        created_job = (await session.execute(stmt_res)).scalar_one()

        return created_job

@router.put("/applications/{application_id}/status", response_model=ApplicationResponse)
@router.put("/{job_id}/applications/{application_id}/status", response_model=ApplicationResponse)
@router.patch("/applications/{application_id}/status", response_model=ApplicationResponse)
@router.patch("/{job_id}/applications/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    payload: Dict[str, Any],
    job_id: Optional[uuid.UUID] = None,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Recruiter Application Status Update Endpoint:
    Updates application status through lifecycle states (SUBMITTED, REVIEWED, SHORTLISTED, INTERVIEW, SELECTED, REJECTED).
    """
    new_status_str = payload.get("status")
    if not new_status_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Field 'status' is required.")

    try:
        new_status = ApplicationStatusEnum(new_status_str.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status_str}'."
        )

    async with async_session_factory() as session:
        await session.begin()
        target_org_id = ctx.active_organization_id
        await set_tenant_context(session, organization_id=target_org_id, user_id=ctx.user.id, is_platform_admin=True)

        stmt = select(Application).where(Application.id == application_id)
        app = (await session.execute(stmt)).scalar_one_or_none()

        if not app:
            # Re-try setting tenant context if active_organization_id was not set
            stmt_all = select(Application).where(Application.id == application_id)
            res_all = await session.execute(stmt_all)
            app = res_all.scalar_one_or_none()

        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found.")

        await set_tenant_context(session, organization_id=app.organization_id, user_id=ctx.user.id, is_platform_admin=True)

        # Verify job ownership
        stmt_job = select(Job).where(Job.id == app.job_id)
        job = (await session.execute(stmt_job)).scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated job posting not found.")

        if not ctx.user.is_platform_admin and job.created_by_user_id != ctx.user.id:
            if ctx.active_organization_id and job.organization_id != ctx.active_organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to update application status.")

        app.status = new_status
        app.decided_by_user_id = ctx.user.id
        app.decided_at = datetime.now(timezone.utc)

        audit = AuditLog(
            organization_id=app.organization_id,
            user_id=ctx.user.id,
            action=f"application.status.{new_status.value.lower()}",
            resource_type="application",
            resource_id=str(app.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, organization_id=app.organization_id, user_id=ctx.user.id, is_platform_admin=True)
        stmt_res = select(Application).where(Application.id == app.id)
        updated_app = (await session.execute(stmt_res)).scalar_one()

        return ApplicationResponse.model_validate(updated_app)

@router.put("/{job_id}", response_model=JobResponse)
@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: uuid.UUID,
    payload: JobUpdateRequest,
    ctx: SecurityContext = Depends(get_security_context),
):
    """Updates job posting content, status, and transitions active job intelligence to STALE."""
    if not ctx.user.is_platform_admin and ctx.role == RoleEnum.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Access Denied: Action requires one of ['ORGANIZATION_ADMIN', 'RECRUITER'].",
        )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)

        stmt = select(Job).where(Job.id == job_id)
        job = (await session.execute(stmt)).scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        if job.organization_id:
            await set_tenant_context(session, organization_id=job.organization_id, is_platform_admin=True)

        # Check ownership / org permission
        if not ctx.user.is_platform_admin and job.created_by_user_id != ctx.user.id:
            if ctx.active_organization_id and job.organization_id != ctx.active_organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this job posting.")

        if payload.title is not None:
            job.title = payload.title
        if payload.description is not None:
            job.description = payload.description
        if payload.department is not None:
            job.department = payload.department
        if payload.location is not None:
            job.location = payload.location
        if payload.employment_type is not None:
            job.employment_type = payload.employment_type
        if payload.salary is not None:
            job.salary = payload.salary
        if payload.company_website is not None:
            job.company_website = payload.company_website
        if payload.verification_status is not None:
            if ctx.user.is_platform_admin or payload.verification_status in [JobVerificationStatusEnum.DRAFT, JobVerificationStatusEnum.PENDING_VERIFICATION]:
                job.verification_status = payload.verification_status
        if payload.status is not None:
            if payload.status == JobStatusEnum.PUBLISHED and job.verification_status != JobVerificationStatusEnum.APPROVED and not ctx.user.is_platform_admin:
                job.status = JobStatusEnum.DRAFT
            else:
                job.status = payload.status

        # Mark active intelligence STALE if content updated
        await session.execute(
            update(JobIntelligenceVersion)
            .where(JobIntelligenceVersion.job_id == job_id, JobIntelligenceVersion.is_active.is_(True))
            .values(status=JobIntelligenceVersionStatusEnum.STALE)
        )

        audit = AuditLog(
            organization_id=job.organization_id,
            user_id=ctx.user.id,
            action="job.update",
            resource_type="job",
            resource_id=str(job.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)
        return (await session.execute(stmt)).scalar_one()

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(get_security_context),
):
    """Deletes a job posting and associated audit record within tenant context."""
    if not ctx.user.is_platform_admin and ctx.role == RoleEnum.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Access Denied: Action requires one of ['ORGANIZATION_ADMIN', 'RECRUITER'].",
        )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)

        stmt = select(Job).where(Job.id == job_id)
        job = (await session.execute(stmt)).scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        # Check ownership / org permission
        if not ctx.user.is_platform_admin and job.created_by_user_id != ctx.user.id:
            if ctx.active_organization_id and job.organization_id != ctx.active_organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this job posting.")

        await session.execute(delete(JobIntelligenceVersion).where(JobIntelligenceVersion.job_id == job_id))
        await session.execute(delete(Application).where(Application.job_id == job_id))
        await session.execute(delete(Job).where(Job.id == job_id))

        audit = AuditLog(
            organization_id=job.organization_id,
            user_id=ctx.user.id,
            action="job.delete",
            resource_type="job",
            resource_id=str(job_id),
        )
        session.add(audit)
        await session.commit()

@router.post("/{job_id}/submit-verification", response_model=JobResponse)
async def submit_job_for_verification(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(get_security_context),
):
    """Submits a DRAFT or REJECTED job posting to Platform Admins for verification."""
    if not ctx.user.is_platform_admin and ctx.role == RoleEnum.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Access Denied: Action requires one of ['ORGANIZATION_ADMIN', 'RECRUITER'].",
        )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)

        stmt = select(Job).where(Job.id == job_id)
        job = (await session.execute(stmt)).scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        job.verification_status = JobVerificationStatusEnum.PENDING_VERIFICATION
        job.rejection_reason = None

        audit = AuditLog(
            organization_id=job.organization_id,
            user_id=ctx.user.id,
            action="job.submit_verification",
            resource_type="job",
            resource_id=str(job.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)
        stmt_res = select(Job).where(Job.id == job.id)
        updated_job = (await session.execute(stmt_res)).scalar_one()

        return JobResponse.model_validate(updated_job)

@router.post("/{job_id}/publish", response_model=JobResponse)
async def publish_job(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(get_security_context),
):
    """
    Publishes an APPROVED job posting.
    CRITICAL SECURITY GUARD: Rejects direct transition to PUBLISHED if verification_status != APPROVED.
    """
    if not ctx.user.is_platform_admin and ctx.role == RoleEnum.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Access Denied: Action requires one of ['ORGANIZATION_ADMIN', 'RECRUITER'].",
        )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)

        stmt = select(Job).where(Job.id == job_id)
        job = (await session.execute(stmt)).scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        # CRITICAL VERIFICATION CHECK
        if job.verification_status != JobVerificationStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Job Verification Required: Posting must be verified and approved by a Platform Admin before publication. Current verification status: '{job.verification_status.value}'.",
            )

        job.status = JobStatusEnum.PUBLISHED

        audit = AuditLog(
            organization_id=job.organization_id,
            user_id=ctx.user.id,
            action="job.publish",
            resource_type="job",
            resource_id=str(job.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)
        stmt_res = select(Job).where(Job.id == job.id)
        updated_job = (await session.execute(stmt_res)).scalar_one()

        return JobResponse.model_validate(updated_job)

@router.get("", response_model=JobListResponse)
@router.get("/", response_model=JobListResponse, include_in_schema=False)
async def list_jobs(
    status_filter: Optional[JobStatusEnum] = Query(None, alias="status"),
    department_filter: Optional[str] = Query(None, alias="department"),
    public_only: bool = Query(False, alias="public_only"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: SecurityContext = Depends(get_security_context),
):
    """Lists jobs in active organization tenant context or public candidate listings."""
    async with async_session_factory() as session:
        await session.begin()

        from app.domains.organizations.models import MembershipStatusEnum, OrganizationMembership

        target_org_id = ctx.active_organization_id
        if not target_org_id and ctx.user:
            stmt_mem = select(OrganizationMembership).where(
                OrganizationMembership.user_id == ctx.user.id,
                OrganizationMembership.status == MembershipStatusEnum.ACTIVE,
            )
            mem = (await session.execute(stmt_mem)).scalars().first()
            if mem:
                target_org_id = mem.organization_id

        if public_only:
            # Public Candidate Directory: return all published & admin-approved jobs across all employers
            await set_tenant_context(session, is_platform_admin=True)
            stmt = select(Job).where(
                Job.verification_status == JobVerificationStatusEnum.APPROVED,
                Job.status == JobStatusEnum.PUBLISHED,
                Job.created_by_user_id.isnot(None),
            )
        elif ctx.user:
            # Authenticated Recruiter / Admin Workspace: return owned / tenant requisitions across all lifecycle states
            await set_tenant_context(session, is_platform_admin=True)
            if ctx.user.is_platform_admin:
                stmt = select(Job)
            elif target_org_id:
                stmt = select(Job).where(
                    (Job.organization_id == target_org_id) | (Job.created_by_user_id == ctx.user.id)
                )
            else:
                stmt = select(Job).where(Job.created_by_user_id == ctx.user.id)
        else:
            # Unauthenticated public candidate fallback
            await set_tenant_context(session, is_platform_admin=True)
            stmt = select(Job).where(
                Job.verification_status == JobVerificationStatusEnum.APPROVED,
                Job.status == JobStatusEnum.PUBLISHED,
                Job.created_by_user_id.isnot(None),
            )

        if status_filter:
            stmt = stmt.where(Job.status == status_filter)
        if department_filter:
            stmt = stmt.where(Job.department.ilike(f"%{department_filter}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Job.created_at.desc()).offset(offset).limit(page_size)
        jobs = list((await session.execute(stmt)).scalars().all())

        return JobListResponse(
            items=[JobResponse.model_validate(j) for j in jobs],
            total=total,
            page=page,
            page_size=page_size,
        )



@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    ctx: SecurityContext = Depends(get_optional_security_context),
):
    """Fetches single job details by UUID or slug for recruiters or public candidates."""
    async with async_session_factory() as session:
        await session.begin()
        if ctx.active_organization_id and not (ctx.user and ctx.user.is_platform_admin):
            await set_tenant_context(session, ctx.active_organization_id)
            stmt = select(Job).where(Job.organization_id == ctx.active_organization_id)
        else:
            await set_tenant_context(session, is_platform_admin=True)
            stmt = select(Job)

        try:
            val_uuid = uuid.UUID(job_id)
            stmt = stmt.where(Job.id == val_uuid)
        except ValueError:
            stmt = stmt.where(
                Job.slug == job_id,
                (Job.status == JobStatusEnum.PUBLISHED) | (Job.verification_status == JobVerificationStatusEnum.APPROVED)
            )

        job = (await session.execute(stmt)).scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        return job

@router.get("/{job_id}/applications", response_model=ApplicationListResponse)
async def list_job_applications(
    job_id: uuid.UUID,
    status_filter: Optional[ApplicationStatusEnum] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Lists applications submitted to a specific job requisition in active tenant context.
    Uses server-side database pagination to efficiently handle 10K+ to 300K+ application volumes.
    """
    async with async_session_factory() as session:
        await session.begin()
        org_id = ctx.active_organization_id
        await set_tenant_context(session, organization_id=org_id, user_id=ctx.user.id, is_platform_admin=True)

        # Verify job belongs to user or active organization
        stmt_job = select(Job).where(Job.id == job_id)
        job = (await session.execute(stmt_job)).scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        if not ctx.user.is_platform_admin and job.created_by_user_id != ctx.user.id:
            if ctx.active_organization_id and job.organization_id and job.organization_id != ctx.active_organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view applications for this job.")

        job_org = job.organization_id or org_id
        await set_tenant_context(session, organization_id=job_org, user_id=ctx.user.id, is_platform_admin=True)

        # Application Query
        stmt = select(Application).where(Application.job_id == job_id)
        if status_filter:
            stmt = stmt.where(Application.status == status_filter)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Application.submitted_at.desc()).offset(offset).limit(page_size)
        apps = list((await session.execute(stmt)).scalars().all())

        candidate_ids = [a.candidate_id for a in apps]
        user_map = {}
        profile_map = {}
        if candidate_ids:
            from app.domains.identity.models import User
            from app.domains.candidates.models import CandidateProfile

            stmt_users = select(User).where(User.id.in_(candidate_ids))
            users = (await session.execute(stmt_users)).scalars().all()
            user_map = {u.id: u for u in users}

            stmt_profiles = select(CandidateProfile).where(CandidateProfile.user_id.in_(candidate_ids))
            profiles = (await session.execute(stmt_profiles)).scalars().all()
            profile_map = {p.user_id: p for p in profiles}

        res_items = []
        for a in apps:
            app_resp = ApplicationResponse.model_validate(a)
            u = user_map.get(a.candidate_id)
            p = profile_map.get(a.candidate_id)
            if u:
                app_resp.candidate_name = u.full_name or u.email
                app_resp.candidate_email = u.email
            if p:
                app_resp.headline = p.headline
                app_resp.skills = p.skills
            res_items.append(app_resp)

        return ApplicationListResponse(
            items=res_items,
            total=total,
            page=page,
            page_size=page_size,
        )

@router.post("/applications/{application_id}/decision", response_model=ApplicationResponse)
async def record_human_application_decision(
    application_id: uuid.UUID,
    payload: ApplicationDecisionRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Human Recruiter Decision Endpoint:
    Records recruiter decision (SHORTLIST or REJECT).
    Silently changing candidate state without human decision is strictly prohibited.
    """
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)

        stmt = select(Application).where(Application.id == application_id)
        app = (await session.execute(stmt)).scalar_one_or_none()

        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found.")

        new_status = ApplicationStatusEnum.SHORTLISTED if payload.action.upper() == "SHORTLIST" else ApplicationStatusEnum.REJECTED
        app.status = new_status
        app.decided_by_user_id = ctx.user.id
        app.decided_at = datetime.now(timezone.utc)
        app.decision_reason = payload.reason

        audit_action = "application.shortlisted" if new_status == ApplicationStatusEnum.SHORTLISTED else "application.rejected"
        audit = AuditLog(
            organization_id=app.organization_id,
            user_id=ctx.user.id,
            action=audit_action,
            resource_type="application",
            resource_id=str(app.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)
        stmt_res = select(Application).where(Application.id == app.id)
        return ApplicationResponse.model_validate((await session.execute(stmt_res)).scalar_one())
