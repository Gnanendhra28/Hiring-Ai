import uuid
from typing import TypeVar
from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.db.rls import set_tenant_context

T = TypeVar("T")

class AsyncUnitOfWork:
    """
    Unit of Work pattern wrapping a database transaction.
    Manages transaction lifecycle and applies transaction-scoped RLS tenant context.
    """

    def __init__(self, organization_id: uuid.UUID | None = None) -> None:
        self.organization_id = organization_id
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "AsyncUnitOfWork":
        self.session = async_session_factory()
        await self.session.begin()

        if self.organization_id is not None:
            await set_tenant_context(self.session, self.organization_id)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.session:
            try:
                if exc_type is not None:
                    await self.rollback()
                else:
                    await self.commit()
            except Exception:
                await self.rollback()
                raise
            finally:
                await self.session.close()
                self.session = None

    async def commit(self) -> None:
        if self.session and self.session.is_active:
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session and self.session.is_active:
            await self.session.rollback()
