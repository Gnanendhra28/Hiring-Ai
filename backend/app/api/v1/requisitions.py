import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.v1.deps import require_role, SecurityContext
from app.domains.organizations.models import RoleEnum
from app.domains.requisitions.schemas import (
    AIGovernanceAnalyticsResponse,
    AITelemetryResponse,
    AuditAnalyticsResponse,
    OrganizationDashboardResponse,
    RequisitionReportResponse,
    TenantRequisitionReportResponse,
)
from app.services.requisition_reporting_service import RequisitionReportingService

router = APIRouter(prefix="/requisitions", tags=["Enterprise Requisition Reporting & Analytics"])

@router.get("/report", response_model=TenantRequisitionReportResponse)
async def get_tenant_aggregated_report(
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Returns aggregated tenant-level requisition metrics across all jobs.
    Requires RECRUITER or ORGANIZATION_ADMIN role.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    return await service.get_tenant_aggregated_report(organization_id=ctx.active_organization_id)

@router.get("/dashboard", response_model=OrganizationDashboardResponse)
async def get_organization_dashboard(
    start_date: datetime | None = Query(None, description="Optional start timestamp filter"),
    end_date: datetime | None = Query(None, description="Optional end timestamp filter"),
    status_filter: str | None = Query(None, alias="status", description="Optional requisition status filter"),
    department: str | None = Query(None, description="Optional department filter"),
    employment_type: str | None = Query(None, description="Optional employment type filter"),
    location: str | None = Query(None, description="Optional location filter"),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Returns enterprise organization-level reporting dashboard, aggregate metrics, and requisition performance table.
    Enforces tenant context and RLS isolation.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    return await service.get_organization_dashboard(
        organization_id=ctx.active_organization_id,
        start_date=start_date,
        end_date=end_date,
        status=status_filter,
        department=department,
        employment_type=employment_type,
        location=location,
    )

@router.get("/audit-analytics", response_model=AuditAnalyticsResponse)
async def get_audit_analytics(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Returns read-only recruiter decision audit analytics and lifecycle event counts.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    return await service.get_tenant_audit_analytics(
        organization_id=ctx.active_organization_id,
        start_date=start_date,
        end_date=end_date,
    )

@router.get("/ai-governance-analytics", response_model=AIGovernanceAnalyticsResponse)
async def get_ai_governance_analytics(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Returns organization AI advisory activity metrics vs recruiter decisions.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    return await service.get_tenant_ai_governance_analytics(
        organization_id=ctx.active_organization_id,
        start_date=start_date,
        end_date=end_date,
    )

@router.get("/ai-telemetry", response_model=AITelemetryResponse)
async def get_ai_telemetry(
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Returns tenant operational AI invocation stats and latency telemetry.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    return await service.get_tenant_ai_telemetry(organization_id=ctx.active_organization_id)

@router.get("/report/export")
async def export_organization_report_csv(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    department: str | None = Query(None),
    employment_type: str | None = Query(None),
    location: str | None = Query(None),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Exports organization-level CSV report across all tenant requisitions.
    Excludes raw resume text, PII, passwords, and API tokens.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    csv_data = await service.export_organization_report_csv(
        organization_id=ctx.active_organization_id,
        start_date=start_date,
        end_date=end_date,
        status=status_filter,
        department=department,
        employment_type=employment_type,
        location=location,
    )

    filename = f"organization_requisition_report_{ctx.active_organization_id}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=csv_data, media_type="text/csv", headers=headers)

@router.get("/{job_id}/report", response_model=RequisitionReportResponse)
async def get_requisition_report(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Returns deterministic requisition report and candidate funnel analytics for a job.
    Enforces tenant isolation (cross-tenant request returns 404).
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    report = await service.get_requisition_report(job_id=job_id, organization_id=ctx.active_organization_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisition not found or access denied.")

    return report

@router.get("/{job_id}/report/export")
async def export_single_requisition_report_csv(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Exports clean, tenant-scoped CSV requisition report for a single job.
    Excludes raw resume text, PII, passwords, and API tokens.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    csv_data = await service.export_requisition_report_csv(job_id=job_id, organization_id=ctx.active_organization_id)
    if not csv_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisition not found or access denied.")

    filename = f"requisition_report_{job_id}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=csv_data, media_type="text/csv", headers=headers)
