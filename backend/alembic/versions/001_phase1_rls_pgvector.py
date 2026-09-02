"""001_phase1_rls_pgvector

Revision ID: 001_phase1_rls_pgvector
Revises: 
Create Date: 2026-08-14 15:00:00.000000

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "001_phase1_rls_pgvector"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create rls_test_records table
    op.create_table(
        "rls_test_records",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Enable & FORCE Row Level Security (RLS) on rls_test_records
    # Note: FORCE ROW LEVEL SECURITY ensures RLS is enforced even for superusers & table owners.
    op.execute("ALTER TABLE rls_test_records ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE rls_test_records FORCE ROW LEVEL SECURITY;")

    # 4. Create RLS Policy for tenant isolation
    op.execute("""
        CREATE POLICY rls_test_records_tenant_isolation ON rls_test_records
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        );
    """)

    # 5. Create HNSW Vector Index
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_rls_test_records_embedding
        ON rls_test_records USING hnsw (embedding vector_cosine_ops);
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_rls_test_records_embedding;")
    op.execute("DROP POLICY IF EXISTS rls_test_records_tenant_isolation ON rls_test_records;")
    op.execute("ALTER TABLE rls_test_records NO FORCE ROW LEVEL SECURITY;")
    op.drop_table("rls_test_records")
