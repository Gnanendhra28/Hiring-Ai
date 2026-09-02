import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger

async def set_tenant_context(
    session: AsyncSession,
    organization_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    is_platform_admin: bool = False,
) -> None:
    """
    Sets transaction-scoped session variables for PostgreSQL Row Level Security (RLS).
    Executes set_config for app.current_organization_id, app.current_user_id, and app.current_is_platform_admin.
    """
    if organization_id:
        org_str = str(organization_id)
        await session.execute(
            text("SELECT set_config('app.current_organization_id', :org_id, true)"),
            {"org_id": org_str},
        )
        logger.debug(f"Established transaction RLS tenant context for organization_id={org_str}")

    if user_id:
        user_str = str(user_id)
        await session.execute(
            text("SELECT set_config('app.current_user_id', :user_id, true)"),
            {"user_id": user_str},
        )
        logger.debug(f"Established transaction RLS user context for user_id={user_str}")

    if is_platform_admin:
        await session.execute(
            text("SELECT set_config('app.current_is_platform_admin', 'true', true)")
        )
        logger.debug("Established transaction RLS platform admin context")
