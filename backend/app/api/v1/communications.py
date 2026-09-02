import uuid
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.v1.deps import get_current_user, require_role, SecurityContext
from app.api.v1.schemas import CommunicationDraftRequest, CommunicationResponse
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application
from app.domains.audit.models import AuditLog
from app.domains.communications.models import Communication, CommunicationStatusEnum
from app.domains.identity.models import User
from app.domains.jobs.models import Job
from app.domains.organizations.models import RoleEnum
from app.infrastructure.email.base import MailpitEmailAdapter
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus

router = APIRouter(prefix="", tags=["Communications"])
event_bus = InMemoryEventBus()
email_adapter = MailpitEmailAdapter()

@router.post("/communications/draft", response_model=CommunicationResponse, status_code=status.HTTP_201_CREATED)
async def draft_communication(
    payload: CommunicationDraftRequest,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Drafts a candidate email for consequential hiring workflow stages.
    Performs mandatory validation and sets status to PENDING_APPROVAL.
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

        # 3. Validation Rules
        validation_results = {
            "candidate_valid": True,
            "job_valid": True,
            "recipient_valid": "@" in payload.recipient_email,
            "subject_valid": len(payload.subject) > 3,
            "body_valid": len(payload.body) > 10,
        }

        if not all(validation_results.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email Validation Failed: {validation_results}",
            )

        comm = Communication(
            organization_id=ctx.active_organization_id,
            job_id=job.id,
            application_id=app_rec.id,
            candidate_id=app_rec.candidate_id,
            workflow_stage=payload.workflow_stage,
            recipient_email=payload.recipient_email,
            subject=payload.subject,
            body=payload.body,
            status=CommunicationStatusEnum.PENDING_APPROVAL,
            provider="MAILPIT",
            validation_json=validation_results,
        )
        session.add(comm)

        audit = AuditLog(
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            action="communication.created",
            resource_type="communication",
            resource_id=str(comm.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        stmt_created = select(Communication).where(Communication.id == comm.id)
        return (await session.execute(stmt_created)).scalar_one()

@router.post("/communications/{communication_id}/approve", response_model=CommunicationResponse)
async def approve_communication(
    communication_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    HUMAN APPROVAL ENDPOINT:
    Recruiter reviews and explicitly approves email draft.
    Transition to APPROVED allows execution via /send.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(Communication).where(Communication.id == communication_id, Communication.organization_id == ctx.active_organization_id)
        comm = (await session.execute(stmt)).scalar_one_or_none()

        if not comm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Communication draft not found.")

        if comm.status == CommunicationStatusEnum.CANCELLED or comm.status == CommunicationStatusEnum.DELETED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot approve cancelled or deleted communication.")

        now_utc = datetime.now(UTC)
        comm.status = CommunicationStatusEnum.APPROVED
        comm.approved_by_user_id = ctx.user.id
        comm.approved_at = now_utc

        audit = AuditLog(
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            action="communication.approved",
            resource_type="communication",
            resource_id=str(comm.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        return (await session.execute(stmt)).scalar_one()

@router.post("/communications/{communication_id}/send", response_model=CommunicationResponse)
async def send_communication(
    communication_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Executes email delivery for an APPROVED communication draft.
    CRITICAL SECURITY GUARD: Unapproved communications (status != APPROVED) MUST be rejected with HTTP 403 Forbidden!
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(Communication).where(Communication.id == communication_id, Communication.organization_id == ctx.active_organization_id)
        comm = (await session.execute(stmt)).scalar_one_or_none()

        if not comm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Communication record not found.")

        # CRITICAL HUMAN APPROVAL GUARD
        if comm.status != CommunicationStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Human Approval Required: Email must be explicitly reviewed and approved by a recruiter before sending. Current status: '{comm.status.value}'.",
            )

        # Execute Send via EmailProvider Adapter
        await email_adapter.send_email(
            recipient_email=comm.recipient_email,
            subject=comm.subject,
            body=comm.body,
        )

        now_utc = datetime.now(UTC)
        comm.status = CommunicationStatusEnum.SENT
        comm.sent_at = now_utc

        audit = AuditLog(
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            action="communication.sent",
            resource_type="communication",
            resource_id=str(comm.id),
        )
        session.add(audit)
        await session.commit()

        # Publish Event
        event_envelope = EventEnvelope(
            event_type="communication.sent",
            aggregate_id=comm.id,
            organization_id=ctx.active_organization_id,
            correlation_id=str(uuid.uuid4()),
            payload={
                "communication_id": str(comm.id),
                "recipient_email": comm.recipient_email,
                "workflow_stage": comm.workflow_stage.value,
            },
        )
        await event_bus.publish(event_envelope)

        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        return (await session.execute(stmt)).scalar_one()

@router.post("/communications/{communication_id}/cancel", response_model=CommunicationResponse)
async def cancel_communication(
    communication_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Cancels/Deletes a pending communication draft before sending, recording an append-only audit event."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(Communication).where(Communication.id == communication_id, Communication.organization_id == ctx.active_organization_id)
        comm = (await session.execute(stmt)).scalar_one_or_none()

        if not comm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Communication draft not found.")

        if comm.status == CommunicationStatusEnum.SENT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel an email that has already been sent.")

        comm.status = CommunicationStatusEnum.CANCELLED

        audit = AuditLog(
            organization_id=ctx.active_organization_id,
            user_id=ctx.user.id,
            action="communication.cancelled",
            resource_type="communication",
            resource_id=str(comm.id),
        )
        session.add(audit)
        await session.commit()

        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)
        return (await session.execute(stmt)).scalar_one()

@router.get("/jobs/{job_id}/communications", response_model=list[CommunicationResponse])
async def list_job_communications(
    job_id: uuid.UUID,
    status_filter: CommunicationStatusEnum | None = Query(None, alias="status"),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """Lists email communications for a job requisition in active tenant context."""
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, ctx.active_organization_id)

        stmt = select(Communication).where(Communication.job_id == job_id, Communication.organization_id == ctx.active_organization_id)
        if status_filter:
            stmt = stmt.where(Communication.status == status_filter)

        results = list((await session.execute(stmt)).scalars().all())
        return results

@router.get("/candidate/communications", response_model=list[CommunicationResponse])
async def list_my_candidate_communications(user: User = Depends(get_current_user)):
    """Candidate endpoint: Lists sent communications for the authenticated candidate."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, user_id=user.id)

        stmt = select(Communication).where(
            Communication.candidate_id == user.id,
            Communication.status == CommunicationStatusEnum.SENT,
        ).order_by(Communication.sent_at.desc())
        comms = list((await session.execute(stmt)).scalars().all())
        return comms
