import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import require_role, SecurityContext
from app.domains.organizations.models import RoleEnum
from app.domains.webhooks.schemas import (
    SecretRotationResponse,
    WebhookEventResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionCreateResponse,
    WebhookSubscriptionResponse,
    WebhookSubscriptionUpdate,
    WebhookTestResponse,
)
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Enterprise Outbound Webhook Management"])

@router.post(
    "/subscriptions",
    response_model=WebhookSubscriptionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook_subscription(
    payload: WebhookSubscriptionCreate,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Creates tenant-isolated webhook subscription.
    Exposes HMAC signing secret EXACTLY ONCE upon creation response.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = WebhookService()
    try:
        sub = await service.create_subscription(
            organization_id=ctx.active_organization_id,
            endpoint_url=payload.endpoint_url,
            subscribed_events=payload.subscribed_events,
            user_id=ctx.user.id,
        )
        return WebhookSubscriptionCreateResponse.model_validate(sub)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.get("/subscriptions", response_model=list[WebhookSubscriptionResponse])
async def list_webhook_subscriptions(
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Lists all webhook subscriptions for active tenant.
    EXCLUDES webhook secret for security.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = WebhookService()
    subs = await service.get_subscriptions(organization_id=ctx.active_organization_id)
    return [WebhookSubscriptionResponse.model_validate(s) for s in subs]

@router.get("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook_subscription(
    subscription_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Retrieves single webhook subscription metadata (EXCLUDES secret).
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = WebhookService()
    sub = await service.get_subscription(
        subscription_id=subscription_id, organization_id=ctx.active_organization_id
    )
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook subscription not found.")

    return WebhookSubscriptionResponse.model_validate(sub)

@router.patch("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook_subscription(
    subscription_id: uuid.UUID,
    payload: WebhookSubscriptionUpdate,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Updates webhook subscription destination URL, enabled status, or event subscriptions.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = WebhookService()
    try:
        sub = await service.update_subscription(
            subscription_id=subscription_id,
            organization_id=ctx.active_organization_id,
            endpoint_url=payload.endpoint_url,
            enabled=payload.enabled,
            subscribed_events=payload.subscribed_events,
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook subscription not found.")
        return WebhookSubscriptionResponse.model_validate(sub)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_subscription(
    subscription_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Deletes webhook subscription and associated delivery history.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = WebhookService()
    success = await service.delete_subscription(
        subscription_id=subscription_id, organization_id=ctx.active_organization_id
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook subscription not found.")

    return None

@router.post("/subscriptions/{subscription_id}/rotate-secret", response_model=SecretRotationResponse)
async def rotate_webhook_secret(
    subscription_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Rotates cryptographic signing secret.
    Returns new secret EXACTLY ONCE upon response.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = WebhookService()
    new_secret = await service.rotate_secret(
        subscription_id=subscription_id, organization_id=ctx.active_organization_id
    )
    if not new_secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook subscription not found.")

    return SecretRotationResponse(subscription_id=subscription_id, new_secret=new_secret)

@router.post("/subscriptions/{subscription_id}/test", response_model=WebhookTestResponse)
async def send_test_webhook(
    subscription_id: uuid.UUID,
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Dispatches synthetic 'webhook.test' event to verify endpoint connectivity and HMAC signature.
    Zero candidate, application, or hiring state modified.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = WebhookService()
    delivered, status_code = await service.send_test_webhook(
        subscription_id=subscription_id, organization_id=ctx.active_organization_id
    )

    return WebhookTestResponse(
        subscription_id=subscription_id,
        event_type="webhook.test",
        delivery_status="DELIVERED" if delivered else "FAILED",
        http_status=status_code,
        delivered=delivered,
    )

@router.get("/events", response_model=list[WebhookEventResponse])
async def get_webhook_delivery_history(
    subscription_id: uuid.UUID | None = Query(None, description="Optional subscription filter"),
    ctx: SecurityContext = Depends(require_role([RoleEnum.ORGANIZATION_ADMIN, RoleEnum.RECRUITER])),
):
    """
    Returns audit history log of outbound webhook event deliveries for tenant.
    """
    if not ctx.active_organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Organization-ID required.")

    service = WebhookService()
    events = await service.get_delivery_history(
        organization_id=ctx.active_organization_id, subscription_id=subscription_id
    )
    return [WebhookEventResponse.model_validate(e) for e in events]
