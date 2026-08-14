"""004_phase4_candidate_apps

Revision ID: 004_phase4_candidate_apps
Revises: 003_phase3_recruiter_jobs
Create Date: 2026-08-14 15:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_phase4_candidate_apps"
down_revision: Union[str, None] = "003_phase3_recruiter_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Candidate Profiles Table
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("experience", sa.JSON(), nullable=True),
        sa.Column("education", sa.JSON(), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Applications Table (Tenant RLS Scoped + Candidate Ownership)
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column(
            "status",
            sa.Enum(
                "SUBMITTED",
                "PROCESSING",
                "RECRUITER_REVIEW",
                "SHORTLISTED",
                "REJECTED",
                "WITHDRAWN",
                "ASSESSMENT",
                "INTERVIEW",
                "OFFER",
                "HIRED",
                name="applicationstatusenum",
            ),
            nullable=False,
            server_default="SUBMITTED",
        ),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="DIRECT"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resume_file_path", sa.String(length=500), nullable=True),
        sa.Column("answers_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job_application"),
    )

    # Enable and FORCE RLS on applications
    op.execute("ALTER TABLE applications ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE applications FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY applications_tenant_isolation ON applications
        FOR ALL
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
    op.execute("DROP POLICY IF EXISTS applications_tenant_isolation ON applications;")
    op.drop_table("applications")
    op.drop_table("candidate_profiles")
    op.execute("DROP TYPE IF EXISTS applicationstatusenum;")
