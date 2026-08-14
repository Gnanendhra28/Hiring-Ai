import uuid
from datetime import timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.v1.deps import get_current_user, require_role, SecurityContext
from app.api.v1.schemas import InterviewResponse, InterviewScheduleRequest
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application
from app.domains.audit.models import AuditLog
from app.domains.identity.models import User
from app.domains.interviews.models import Interview, InterviewStatusEnum
from app.domains.jobs.models import Job
from app.domains.organizations.models import RoleEnum
from app.infrastructure.calendar.base import TestCalendarAdapter
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus
from app.infrastructure.video.base import TestVideoMeetingAdapter

router = APIRouter(prefix="", tags=["Interviews"])
event_bus = InMemoryEventBus()
video_adapter = TestVideoMeetingAdapter()
calendar_adapter = TestCalendarAdapter()

@router.post("/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def schedule_interview(
    payload: InterviewScheduleRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Schedules an interview session with a candidate.
    Generates video meeting room link via VideoMeetingProvider adapter and creates calendar event.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        # 1. Fetch Job
        stmt_job = select(Job).where(Job.id == payload.job_id, Job.organization_id == ctx.active_organization_id)
        job = (await session.execute(stmt_job)).scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        # 2. Fetch Application
        stmt_app = select(Application).where(Application.id == payload.application_id, Application.organization_id == ctx.active_organization_id)
        app_rec = (await session.execute(stmt_app)).scalar_one_or_none()
        if not app_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate application not found.")

        start_utc = payload.scheduled_start_at.astimezone(timezone.utc)
        end_utc = start_utc + timedelta(minutes=payload.duration_minutes)

        # 3. Create Video Meeting Link via Provider Adapter
        meeting_data = await video_adapter.create_meeting(
            topic=f"Interview: {job.title} - Candidate {app_rec.candidate_id}",
            duration_minutes=payload.duration_minutes,
        )
        meeting_url = meeting_data["meeting_url"]

        # 4. Create Calendar Event via Provider Adapter
        await calendar_adapter.create_event(
            summary=f"Interview - {job.title}",
            start_time=start_utc,
            end_time=end_utc,
            attendees=[str(payload.interviewer_user_id), str(app_rec.candidate_id)],
            timezone=payload.timezone,
        )

        # 5. Store Interview record
        interview = Interview(
            organization_id=ctx.active_organization_id,
            job_id=job.id,
            application_id=app_rec.id,
            interviewer_user_id=payload.interviewer_user_id,
            candidate_id=app_rec.candidate_id,
            interview_type=payload.interview_type,
            scheduled_start_at=start_utc,
            scheduled_end_at=end_utc,
            timezone=payload.timezone,
            status=InterviewStatusEnum.SCHEDULED,
            meeting_provider=payload.meeting_provider,
            meeting_url=meeting_url,
            notes=payload.notes,
        )
        session.add(interview)

        audit = AuditLog(
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            action="interview.scheduled",
            resource_type="interview",
            resource_id=str(interview.id),
        )
        session.add(audit)
        await session.commit()

        # Publish Event
        event_envelope = EventEnvelope(
            event_type="interview.scheduled",
            aggregate_id=interview.id,
            organization_id=ctx.active_organization_id,
            correlation_id=str(uuid.uuid4()),
            payload={
                "interview_id": str(interview.id),
                "candidate_id": str(app_rec.candidate_id),
                "meeting_url": meeting_url,
            },
        )
        await event_bus.publish(event_envelope)

        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        stmt_created = select(Interview).where(Interview.id == interview.id)
        return (await session.execute(stmt_created)).scalar_one()

@router.get("/jobs/{job_id}/interviews", response_model=List[InterviewResponse])
async def list_job_interviews(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Lists all scheduled interviews for a job in active tenant context."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(Interview).where(Interview.job_id == job_id, Interview.organization_id == ctx.active_organization_id)
        interviews = list((await session.execute(stmt)).scalars().all())
        return interviews

@router.get("/candidate/interviews", response_model=List[InterviewResponse])
async def list_my_candidate_interviews(user: User = Depends(get_current_user)):
    """Candidate endpoint: Lists scheduled interviews for the authenticated candidate."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)

        stmt = select(Interview).where(Interview.candidate_id == user.id).order_by(Interview.scheduled_start_at.asc())
        interviews = list((await session.execute(stmt)).scalars().all())
        return interviews
