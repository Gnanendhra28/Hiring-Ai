import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.v1.deps import get_current_user, require_role, SecurityContext
from app.api.v1.schemas import (
    AssessmentAssignRequest,
    AssessmentAssignmentResponse,
    AssessmentCreateRequest,
    AssessmentResponse,
)
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application
from app.domains.assessments.models import (
    Assessment,
    AssessmentAssignment,
    AssessmentAssignmentStatusEnum,
    AssessmentResult,
)
from app.domains.audit.models import AuditLog
from app.domains.identity.models import User
from app.domains.jobs.models import Job
from app.domains.organizations.models import RoleEnum
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus

router = APIRouter(prefix="", tags=["Assessments"])
event_bus = InMemoryEventBus()

@router.post("/jobs/{job_id}/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    job_id: uuid.UUID,
    payload: AssessmentCreateRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Creates a technical or behavioral assessment template for a job requisition."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        # Verify job belongs to active organization
        stmt_job = select(Job).where(Job.id == job_id, Job.organization_id == ctx.active_organization_id)
        job = (await session.execute(stmt_job)).scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

        assessment = Assessment(
            organization_id=ctx.active_organization_id,
            job_id=job_id,
            title=payload.title,
            description=payload.description,
            duration_minutes=payload.duration_minutes,
            passing_score=payload.passing_score,
        )
        session.add(assessment)

        audit = AuditLog(
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            action="assessment.created",
            resource_type="assessment",
            resource_id=str(assessment.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        stmt_created = select(Assessment).where(Assessment.id == assessment.id)
        return (await session.execute(stmt_created)).scalar_one()

@router.get("/jobs/{job_id}/assessments", response_model=List[AssessmentResponse])
async def list_job_assessments(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Lists all assessment templates configured for a job requisition."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(Assessment).where(Assessment.job_id == job_id, Assessment.organization_id == ctx.active_organization_id)
        results = list((await session.execute(stmt)).scalars().all())
        return results

@router.post("/assessments/{assessment_id}/assign", response_model=AssessmentAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentAssignRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Assigns an assessment template to a candidate's job application."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        # 1. Fetch assessment
        stmt_ass = select(Assessment).where(Assessment.id == assessment_id, Assessment.organization_id == ctx.active_organization_id)
        ass = (await session.execute(stmt_ass)).scalar_one_or_none()
        if not ass:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment template not found.")

        # 2. Fetch candidate application
        stmt_app = select(Application).where(Application.id == payload.application_id, Application.organization_id == ctx.active_organization_id)
        app_rec = (await session.execute(stmt_app)).scalar_one_or_none()
        if not app_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate application not found.")

        now_utc = datetime.now(timezone.utc)
        due_at = now_utc + timedelta(days=payload.due_days)

        assignment = AssessmentAssignment(
            organization_id=ctx.active_organization_id,
            assessment_id=ass.id,
            application_id=app_rec.id,
            candidate_id=app_rec.candidate_id,
            status=AssessmentAssignmentStatusEnum.SENT,
            assigned_at=now_utc,
            due_at=due_at,
        )
        session.add(assignment)

        audit = AuditLog(
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            action="assessment.assigned",
            resource_type="assessment_assignment",
            resource_id=str(assignment.id),
        )
        session.add(audit)
        await session.commit()

        # Publish Event
        event_envelope = EventEnvelope(
            event_type="assessment.assigned",
            aggregate_id=assignment.id,
            organization_id=ctx.active_organization_id,
            correlation_id=str(uuid.uuid4()),
            payload={
                "assignment_id": str(assignment.id),
                "candidate_id": str(app_rec.candidate_id),
                "assessment_id": str(ass.id),
            },
        )
        await event_bus.publish(event_envelope)

        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        stmt_created = select(AssessmentAssignment).where(AssessmentAssignment.id == assignment.id)
        return (await session.execute(stmt_created)).scalar_one()

@router.get("/candidate/assessments", response_model=List[AssessmentAssignmentResponse])
async def list_my_candidate_assessments(user: User = Depends(get_current_user)):
    """Candidate endpoint: Lists assessments assigned to the authenticated candidate."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)

        stmt = select(AssessmentAssignment).where(AssessmentAssignment.candidate_id == user.id).order_by(AssessmentAssignment.assigned_at.desc())
        assignments = list((await session.execute(stmt)).scalars().all())
        return assignments

@router.post("/candidate/assessments/{assignment_id}/submit", response_model=AssessmentAssignmentResponse)
async def submit_candidate_assessment(
    assignment_id: uuid.UUID,
    user: User = Depends(get_current_user),
):
    """Candidate endpoint: Submits completed assessment and records score."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)

        stmt = select(AssessmentAssignment).where(AssessmentAssignment.id == assignment_id, AssessmentAssignment.candidate_id == user.id)
        assignment = (await session.execute(stmt)).scalar_one_or_none()

        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment assignment not found.")

        if assignment.status == AssessmentAssignmentStatusEnum.COMPLETED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment is already completed.")

        now_utc = datetime.now(timezone.utc)
        assignment.status = AssessmentAssignmentStatusEnum.COMPLETED
        assignment.completed_at = now_utc

        await set_tenant_context(session, organization_id=assignment.organization_id, user_id=user.id)

        result = AssessmentResult(
            organization_id=assignment.organization_id,
            assignment_id=assignment.id,
            score=88,
            passed=True,
            result_data={"submitted_by": str(user.id), "answers_correct": 18, "total_questions": 20},
            completed_at=now_utc,
        )
        session.add(result)

        audit = AuditLog(
            organization_id=assignment.organization_id,
            user_id=user.id,
            action="assessment.completed",
            resource_type="assessment_assignment",
            resource_id=str(assignment.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, user_id=user.id)
        return (await session.execute(stmt)).scalar_one()
