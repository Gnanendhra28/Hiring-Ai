from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.db.base import Base, TimestampMixin, TenantMixin, UUIDMixin

class RLSTestRecord(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Minimal record model used strictly for Phase 1 RLS policy & pgvector integration testing.
    """
    __tablename__ = "rls_test_records"
    __table_args__ = {"extend_existing": True}

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
