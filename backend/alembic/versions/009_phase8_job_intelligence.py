"""009_phase8_job_intelligence

Revision ID: 009_phase8_job_intelligence
Revises: 008_phase7_hnsw_vector_index
Create Date: 2026-08-14 16:22:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "009_phase8_job_intelligence"
down_revision: Union[str, None] = "008_phase7_hnsw_vector_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create Enums
    op.execute("CREATE TYPE requirementtypeenum AS ENUM ('SKILL', 'EXPERIENCE', 'EDUCATION', 'CERTIFICATION', 'LOCATION', 'WORK_MODE', 'RESPONSIBILITY', 'TECHNOLOGY', 'LANGUAGE', 'OTHER');")
    op.execute("CREATE TYPE requirementlevelenum AS ENUM ('REQUIRED', 'PREFERRED', 'INFORMATIONAL');")
    op.execute("CREATE TYPE requirementpriorityenum AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW');")
    op.execute("CREATE TYPE workmodeenum AS ENUM ('REMOTE', 'HYBRID', 'ONSITE', 'FLEXIBLE', 'UNSPECIFIED');")
    op.execute("CREATE TYPE jobintelligenceversionstatusenum AS ENUM ('PENDING', 'PROCESSING', 'EXTRACTING', 'VALIDATING', 'NORMALIZING', 'EVIDENCE_VALIDATION', 'EMBEDDING', 'COMPLETED', 'FAILED', 'RETRY_REQUIRED', 'STALE');")

    # 2. Table: job_intelligence_versions
    op.create_table(
        "job_intelligence_versions",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("organization_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_job_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false", index=True),
        sa.Column("status", postgresql.ENUM("PENDING", "PROCESSING", "EXTRACTING", "VALIDATING", "NORMALIZING", "EVIDENCE_VALIDATION", "EMBEDDING", "COMPLETED", "FAILED", "RETRY_REQUIRED", "STALE", name="jobintelligenceversionstatusenum", create_type=False), nullable=False, server_default="PENDING", index=True),
        sa.Column("ai_provider", sa.String(length=50), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
        sa.Column("overall_confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("safe_error_message", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 3. Table: job_requirements
    op.create_table(
        "job_requirements",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("organization_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("intelligence_version_id", sa.UUID(), sa.ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("requirement_type", postgresql.ENUM("SKILL", "EXPERIENCE", "EDUCATION", "CERTIFICATION", "LOCATION", "WORK_MODE", "RESPONSIBILITY", "TECHNOLOGY", "LANGUAGE", "OTHER", name="requirementtypeenum", create_type=False), nullable=False, index=True),
        sa.Column("raw_value", sa.String(length=500), nullable=False),
        sa.Column("canonical_value", sa.String(length=500), nullable=False, index=True),
        sa.Column("requirement_level", postgresql.ENUM("REQUIRED", "PREFERRED", "INFORMATIONAL", name="requirementlevelenum", create_type=False), nullable=False, server_default="REQUIRED"),
        sa.Column("hard_constraint", sa.Boolean(), nullable=False, server_default="true", index=True),
        sa.Column("operator", sa.String(length=50), nullable=True),
        sa.Column("minimum_value", sa.Float(), nullable=True),
        sa.Column("maximum_value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("priority", postgresql.ENUM("CRITICAL", "HIGH", "MEDIUM", "LOW", name="requirementpriorityenum", create_type=False), nullable=False, server_default="MEDIUM"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("evidence_verification_status", postgresql.ENUM("VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", name="evidenceverificationstatusenum", create_type=False), nullable=False, server_default="UNVERIFIED"),
        sa.Column("is_protected_feature", sa.Boolean(), nullable=False, server_default="false", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 4. Table: job_responsibilities
    op.create_table(
        "job_responsibilities",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("organization_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("intelligence_version_id", sa.UUID(), sa.ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("responsibility_text", sa.Text(), nullable=False),
        sa.Column("associated_skills", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 5. Table: job_intents
    op.create_table(
        "job_intents",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("organization_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("intelligence_version_id", sa.UUID(), sa.ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("raw_intent", sa.Text(), nullable=False),
        sa.Column("canonical_intent", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 6. Table: job_embeddings
    op.execute("CREATE TABLE job_embeddings (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE, job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE, intelligence_version_id UUID NOT NULL REFERENCES job_intelligence_versions(id) ON DELETE CASCADE, context_type VARCHAR(100) NOT NULL, embedding vector(1536) NOT NULL, provider VARCHAR(50) NOT NULL DEFAULT 'openai', model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small', dimension INTEGER NOT NULL DEFAULT 1536, metadata_json JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT now());")

    op.execute("CREATE INDEX idx_job_embeddings_org ON job_embeddings(organization_id);")
    op.execute("CREATE INDEX idx_job_embeddings_job ON job_embeddings(job_id);")
    op.execute("CREATE INDEX idx_job_embeddings_ver ON job_embeddings(intelligence_version_id);")
    op.execute("CREATE INDEX idx_job_embeddings_ctx ON job_embeddings(context_type);")

    # 7. Create HNSW Vector Index on job_embeddings
    op.execute("CREATE INDEX idx_job_embeddings_hnsw ON job_embeddings USING hnsw (embedding vector_cosine_ops);")

    # 8. PostgreSQL RLS Policies
    for tbl in ["job_intelligence_versions", "job_requirements", "job_responsibilities", "job_intents", "job_embeddings"]:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {tbl} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {tbl}_tenant_isolation ON {tbl} FOR ALL
            USING (
                organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            );
        """)

def downgrade() -> None:
    for tbl in ["job_embeddings", "job_intents", "job_responsibilities", "job_requirements", "job_intelligence_versions"]:
        op.execute(f"DROP POLICY IF EXISTS {tbl}_tenant_isolation ON {tbl};")
        op.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE;")

    op.execute("DROP TYPE IF EXISTS jobintelligenceversionstatusenum;")
    op.execute("DROP TYPE IF EXISTS workmodeenum;")
    op.execute("DROP TYPE IF EXISTS requirementpriorityenum;")
    op.execute("DROP TYPE IF EXISTS requirementlevelenum;")
    op.execute("DROP TYPE IF EXISTS requirementtypeenum;")
