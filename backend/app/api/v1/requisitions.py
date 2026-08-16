import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.v1.deps import require_role, SecurityContext
from app.domains.organizations.models import RoleEnum
from app.domains.requisitions.schemas import RequisitionReportResponse, TenantRequisitionReportResponse
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
async def export_requisition_report_csv(
    job_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Exports clean, tenant-scoped CSV requisition report.
    Excludes raw resume text, PII, passwords, and API tokens.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = RequisitionReportingService()
    csv_data = await service.export_requisition_report_csv(job_id=job_id, organization_id=ctx.active_organization_id)
    if not csv_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisition not found or access denied.")

    filename = f"requisition_report_{job_id}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)
