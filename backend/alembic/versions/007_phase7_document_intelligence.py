"""007_phase7_document_intelligence

Revision ID: 007_phase7_document_intelligence
Revises: 006_phase6_workflow_engine
Create Date: 2026-08-14 16:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "007_phase7_document_intelligence"
down_revision: Union[str, None] = "006_phase6_workflow_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Candidate Documents Table
    doc_status_enum = postgresql.ENUM(
        "UPLOADED", "VALIDATING", "VALIDATED", "EXTRACTING_TEXT", "OCR_PROCESSING",
        "TEXT_EXTRACTED", "STRUCTURED_EXTRACTION", "EVIDENCE_VALIDATION",
        "EMBEDDING_GENERATION", "COMPLETED", "FAILED", "RETRY_REQUIRED",
        name="documentprocessingstatusenum", create_type=False
    )
    op.execute("""
        CREATE TYPE documentprocessingstatusenum AS ENUM (
            'UPLOADED', 'VALIDATING', 'VALIDATED', 'EXTRACTING_TEXT', 'OCR_PROCESSING',
            'TEXT_EXTRACTED', 'STRUCTURED_EXTRACTION', 'EVIDENCE_VALIDATION',
            'EMBEDDING_GENERATION', 'COMPLETED', 'FAILED', 'RETRY_REQUIRED'
        );
    """)

    op.create_table(
        "candidate_documents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("application_id", sa.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False, server_default="application/pdf"),
        sa.Column("processing_status", doc_status_enum, nullable=False, server_default="UPLOADED"),
        sa.Column("text_quality_score", sa.Float(), nullable=True),
        sa.Column("ocr_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ocr_provider", sa.String(length=50), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("safe_error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE candidate_documents ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE candidate_documents FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY candidate_documents_tenant_isolation ON candidate_documents FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

    # 2. Candidate Skills Table
    op.create_table(
        "candidate_skills",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", sa.UUID(as_uuid=True), sa.ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("raw_skill_name", sa.String(length=255), nullable=False),
        sa.Column("canonical_skill_name", sa.String(length=255), nullable=False, index=True),
        sa.Column("years_experience", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE candidate_skills ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE candidate_skills FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY candidate_skills_tenant_isolation ON candidate_skills FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

    # 3. Candidate Experiences Table
    op.create_table(
        "candidate_experiences",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", sa.UUID(as_uuid=True), sa.ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("raw_start_date", sa.String(length=50), nullable=True),
        sa.Column("raw_end_date", sa.String(length=50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("duration_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE candidate_experiences ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE candidate_experiences FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY candidate_experiences_tenant_isolation ON candidate_experiences FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

    # 4. Candidate Educations Table
    op.create_table(
        "candidate_educations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", sa.UUID(as_uuid=True), sa.ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("institution", sa.String(length=255), nullable=False),
        sa.Column("degree", sa.String(length=255), nullable=True),
        sa.Column("field_of_study", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE candidate_educations ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE candidate_educations FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY candidate_educations_tenant_isolation ON candidate_educations FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

    # 5. Candidate Extracted Facts Table
    op.create_table(
        "candidate_extracted_facts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", sa.UUID(as_uuid=True), sa.ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("fact_type", sa.String(length=100), nullable=False, index=True),
        sa.Column("raw_value", sa.String(length=500), nullable=False),
        sa.Column("canonical_value", sa.String(length=500), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("extraction_method", sa.String(length=50), nullable=False, server_default="LLM"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE candidate_extracted_facts ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE candidate_extracted_facts FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY candidate_extracted_facts_tenant_isolation ON candidate_extracted_facts FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

    # 6. Candidate Embeddings Table (pgvector)
    op.create_table(
        "candidate_embeddings",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", sa.UUID(as_uuid=True), sa.ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("context_type", sa.String(length=100), nullable=False, index=True),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="openai"),
        sa.Column("model_name", sa.String(length=100), nullable=False, server_default="text-embedding-3-small"),
        sa.Column("dimension", sa.Integer(), nullable=False, server_default="1536"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE candidate_embeddings ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE candidate_embeddings FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY candidate_embeddings_tenant_isolation ON candidate_embeddings FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

    # 7. AI Processing Audits Table
    op.create_table(
        "ai_processing_audits",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", sa.UUID(as_uuid=True), sa.ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("processing_stage", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("escalation_triggered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE ai_processing_audits ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE ai_processing_audits FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY ai_processing_audits_tenant_isolation ON ai_processing_audits FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS ai_processing_audits_tenant_isolation ON ai_processing_audits;")
    op.drop_table("ai_processing_audits")

    op.execute("DROP POLICY IF EXISTS candidate_embeddings_tenant_isolation ON candidate_embeddings;")
    op.drop_table("candidate_embeddings")

    op.execute("DROP POLICY IF EXISTS candidate_extracted_facts_tenant_isolation ON candidate_extracted_facts;")
    op.drop_table("candidate_extracted_facts")

    op.execute("DROP POLICY IF EXISTS candidate_educations_tenant_isolation ON candidate_educations;")
    op.drop_table("candidate_educations")

    op.execute("DROP POLICY IF EXISTS candidate_experiences_tenant_isolation ON candidate_experiences;")
    op.drop_table("candidate_experiences")

    op.execute("DROP POLICY IF EXISTS candidate_skills_tenant_isolation ON candidate_skills;")
    op.drop_table("candidate_skills")

    op.execute("DROP POLICY IF EXISTS candidate_documents_tenant_isolation ON candidate_documents;")
    op.drop_table("candidate_documents")

    op.execute("DROP TYPE IF EXISTS documentprocessingstatusenum;")
