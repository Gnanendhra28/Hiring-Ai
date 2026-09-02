import uuid
from typing import Generic, TypeVar
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    """Generic async repository providing standard data access operations."""

    def __init__(self, model_cls: type[T], session: AsyncSession) -> None:
        self.model_cls = model_cls
        self.session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> T | None:
        result = await self.session.execute(
            select(self.model_cls).where(self.model_cls.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> list[T]:
        result = await self.session.execute(
            select(self.model_cls).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(self.model_cls).where(self.model_cls.id == entity_id)
        )
        return result.rowcount > 0
