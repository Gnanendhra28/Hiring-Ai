"""005_phase5_job_verification_pipeline

Revision ID: 005_phase5_job_verification_pipeline
Revises: 004_phase4_candidate_apps
Create Date: 2026-08-14 15:30:00.000000

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_phase5_job_verification"
down_revision: str | None = "004_phase4_candidate_apps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. Job Verification Enum & Columns
    job_verification_enum = postgresql.ENUM(
        "DRAFT", "PENDING_VERIFICATION", "APPROVED", "REJECTED", name="jobverificationstatusenum"
    )
    job_verification_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "jobs",
        sa.Column(
            "verification_status",
            job_verification_enum,
            nullable=False,
            server_default="DRAFT",
        ),
    )
    op.create_index("ix_jobs_verification_status", "jobs", ["verification_status"])
    op.add_column("jobs", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("verified_by_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("jobs", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))

    # Update jobs RLS policy to enforce BOTH APPROVED and PUBLISHED for public access, and grant Platform Admin access
    op.execute("DROP POLICY IF EXISTS jobs_tenant_isolation ON jobs;")
    op.execute("""
        CREATE POLICY jobs_tenant_isolation ON jobs
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR (verification_status = 'APPROVED' AND status = 'PUBLISHED')
            OR (current_setting('app.current_is_platform_admin', true) = 'true')
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR (current_setting('app.current_is_platform_admin', true) = 'true')
        );
    """)

    # Update audit_logs RLS policy to grant Platform Admin access and support NULL organization_id for user registration/login
    op.execute("DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs;")
    op.execute("""
        CREATE POLICY audit_logs_tenant_isolation ON audit_logs
        FOR ALL
        USING (
            organization_id IS NULL
            OR organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR (current_setting('app.current_is_platform_admin', true) = 'true')
        )
        WITH CHECK (
            organization_id IS NULL
            OR organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR (current_setting('app.current_is_platform_admin', true) = 'true')
        );
    """)

    # 2. Application Decision Tracking Columns
    op.add_column("applications", sa.Column("decided_by_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("applications", sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("applications", sa.Column("decision_reason", sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column("applications", "decision_reason")
    op.drop_column("applications", "decided_at")
    op.drop_column("applications", "decided_by_user_id")

    op.execute("DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs;")
    op.execute("""
        CREATE POLICY audit_logs_tenant_isolation ON audit_logs
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        );
    """)

    op.execute("DROP POLICY IF EXISTS jobs_tenant_isolation ON jobs;")
    op.execute("""
        CREATE POLICY jobs_tenant_isolation ON jobs
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR status = 'PUBLISHED'
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        );
    """)
    op.drop_column("jobs", "verified_at")
    op.drop_column("jobs", "verified_by_user_id")
    op.drop_column("jobs", "rejection_reason")
    op.drop_index("ix_jobs_verification_status", table_name="jobs")
    op.drop_column("jobs", "verification_status")
    op.execute("DROP TYPE IF EXISTS jobverificationstatusenum;")
