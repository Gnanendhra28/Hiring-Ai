import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.api.v1.deps import get_current_user
from app.api.v1.schemas import (
    ApplicationResponse,
    ApplicationSubmitRequest,
    CandidateProfileRequest,
    CandidateProfileResponse,
)
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application, ApplicationStatusEnum
from app.domains.audit.models import AuditLog
from app.domains.candidates.models import CandidateProfile
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum, JobVerificationStatusEnum
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus

router = APIRouter(prefix="/candidate", tags=["Candidate Platform"])
event_bus = InMemoryEventBus()

@router.get("/profile", response_model=CandidateProfileResponse)
async def get_my_candidate_profile(user: User = Depends(get_current_user)):
    """Fetches candidate profile metadata for current authenticated user."""
    async with async_session_factory() as session:
        stmt = select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = CandidateProfile(user_id=user.id)
            session.add(profile)
            await session.commit()
            await session.refresh(profile)

        resp = CandidateProfileResponse.model_validate(profile)
        resp.full_name = user.full_name
        return resp

@router.put("/profile", response_model=CandidateProfileResponse)
async def update_my_candidate_profile(
    payload: CandidateProfileRequest,
    user: User = Depends(get_current_user),
):
    """Creates or updates candidate profile metadata."""
    async with async_session_factory() as session:
        if payload.full_name is not None:
            stmt_u = select(User).where(User.id == user.id)
            u_obj = (await session.execute(stmt_u)).scalar_one_or_none()
            if u_obj:
                u_obj.full_name = payload.full_name

        stmt = select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = CandidateProfile(
                user_id=user.id,
                location=payload.location,
                headline=payload.headline,
                summary=payload.summary,
                phone=payload.phone,
                photo_url=payload.photo_url,
                degree=payload.degree,
                college=payload.college,
                skills=payload.skills,
                experience=payload.experience,
                education=payload.education,
                career_preferences=payload.career_preferences,
                languages=payload.languages,
                internships=payload.internships,
                projects=payload.projects,
                accomplishments=payload.accomplishments,
                employment=payload.employment,
                website_url=payload.website_url,
                linkedin_url=payload.linkedin_url,
                resume_url=payload.resume_url,
                resume_filename=payload.resume_filename,
                resume_filesize=payload.resume_filesize,
                resume_updated_at=payload.resume_updated_at,
            )
            session.add(profile)
        else:
            if payload.location is not None:
                profile.location = payload.location
            if payload.headline is not None:
                profile.headline = payload.headline
            if payload.summary is not None:
                profile.summary = payload.summary
            if payload.phone is not None:
                profile.phone = payload.phone
            if payload.photo_url is not None:
                profile.photo_url = payload.photo_url
            if payload.degree is not None:
                profile.degree = payload.degree
            if payload.college is not None:
                profile.college = payload.college
            if payload.skills is not None:
                profile.skills = payload.skills
                flag_modified(profile, "skills")
            if payload.experience is not None:
                profile.experience = payload.experience
                flag_modified(profile, "experience")
            if payload.education is not None:
                profile.education = payload.education
                flag_modified(profile, "education")
            if payload.career_preferences is not None:
                profile.career_preferences = payload.career_preferences
                flag_modified(profile, "career_preferences")
            if payload.languages is not None:
                profile.languages = payload.languages
                flag_modified(profile, "languages")
            if payload.internships is not None:
                profile.internships = payload.internships
                flag_modified(profile, "internships")
            if payload.projects is not None:
                profile.projects = payload.projects
                flag_modified(profile, "projects")
            if payload.accomplishments is not None:
                profile.accomplishments = payload.accomplishments
                flag_modified(profile, "accomplishments")
            if payload.employment is not None:
                profile.employment = payload.employment
                flag_modified(profile, "employment")
            if payload.website_url is not None:
                profile.website_url = payload.website_url
            if payload.linkedin_url is not None:
                profile.linkedin_url = payload.linkedin_url
            if payload.resume_url is not None:
                profile.resume_url = payload.resume_url
            if payload.resume_filename is not None:
                profile.resume_filename = payload.resume_filename
            if payload.resume_filesize is not None:
                profile.resume_filesize = payload.resume_filesize
            if payload.resume_updated_at is not None:
                profile.resume_updated_at = payload.resume_updated_at

        await session.commit()
        await session.refresh(profile)

        resp = CandidateProfileResponse.model_validate(profile)
        resp.full_name = payload.full_name or user.full_name
        return resp

@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def submit_application(
    payload: ApplicationSubmitRequest,
    user: User = Depends(get_current_user),
):
    """
    Submits a job application for a published job.
    Enforces duplicate application prevention at the API & database level.
    Fires asynchronous application.submitted event via EventBus.
    """
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)

        # 1. Fetch Job Requisition & verify status is PUBLISHED
        stmt_job = select(Job).where(Job.id == payload.job_id)
        job_result = await session.execute(stmt_job)
        job = job_result.scalar_one_or_none()

        if not job or job.status != JobStatusEnum.PUBLISHED or job.verification_status != JobVerificationStatusEnum.APPROVED or job.created_by_user_id is None:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job posting '{payload.job_id}' is not open for public applications.",
            )

        from app.domains.jobs.closing_date import parse_job_closing_date
        closing_date_str, is_closed = parse_job_closing_date(job.description)
        if is_closed:
            job.status = JobStatusEnum.CLOSED
            await session.commit()
            date_info = f" passed on {closing_date_str}" if closing_date_str else ""
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Applications Closed: The application deadline for this position{date_info}. No further candidate applications will be accepted.",
            )

        # 2. Check for duplicate application (candidate_id, job_id)
        stmt_existing = select(Application).where(
            Application.candidate_id == user.id,
            Application.job_id == payload.job_id,
        )
        existing = (await session.execute(stmt_existing)).scalar_one_or_none()
        if existing:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate Application: You have already submitted an application for this job position.",
            )

        # 3. Set transaction RLS context for target organization & candidate
        await set_tenant_context(session, organization_id=job.organization_id, user_id=user.id)

        # 4. Create Application record
        application = Application(
            candidate_id=user.id,
            job_id=job.id,
            organization_id=job.organization_id,
            status=ApplicationStatusEnum.SUBMITTED,
            resume_file_path=payload.resume_file_path,
            answers_json=payload.answers_json,
        )
        session.add(application)
        await session.flush()

        audit = AuditLog(
            organization_id=job.organization_id,
            user_id=user.id,
            action="application.submit",
            resource_type="application",
            resource_id=str(application.id),
        )
        session.add(audit)
        await session.commit()

        # 5. Publish application.submitted Event
        event_envelope = EventEnvelope(
            event_type="application.submitted",
            aggregate_id=application.id,
            organization_id=job.organization_id,
            correlation_id=str(uuid.uuid4()),
            payload={
                "candidate_id": str(user.id),
                "job_id": str(job.id),
                "organization_id": str(job.organization_id),
                "submitted_at": application.submitted_at.isoformat(),
            },
        )
        await event_bus.publish(event_envelope)

        # Re-query created application
        await session.begin()
        await set_tenant_context(session, organization_id=job.organization_id, user_id=user.id)
        stmt_created = select(Application).where(Application.id == application.id)
        created_app = (await session.execute(stmt_created)).scalar_one()

        return created_app

@router.get("/applications", response_model=List[ApplicationResponse])
async def list_my_applications(user: User = Depends(get_current_user)):
    """Lists applications submitted by the current authenticated candidate (Candidate Ownership Isolation)."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)
        stmt = select(Application).where(Application.candidate_id == user.id).order_by(Application.submitted_at.desc())
        result = await session.execute(stmt)
        apps = list(result.scalars().all())

        return [ApplicationResponse.model_validate(a) for a in apps]

@router.patch("/applications/{app_id}/close", response_model=ApplicationResponse)
async def close_candidate_application(
    app_id: uuid.UUID,
    user: User = Depends(get_current_user),
):
    """Allows candidate to withdraw / close an active job application."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)

        stmt = select(Application).where(
            Application.id == app_id,
            Application.candidate_id == user.id,
        )
        app = (await session.execute(stmt)).scalar_one_or_none()

        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        app.status = ApplicationStatusEnum.WITHDRAWN
        await session.commit()

        await session.begin()
        await set_tenant_context(session, user_id=user.id)
        return (await session.execute(stmt)).scalar_one()
