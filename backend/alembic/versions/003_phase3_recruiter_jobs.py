"""003_phase3_recruiter_jobs

Revision ID: 003_phase3_recruiter_jobs
Revises: 002_phase2_identity_org_rbac
Create Date: 2026-08-14 15:20:00.000000

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_phase3_recruiter_jobs"
down_revision: str | None = "002_phase2_identity_org_rbac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. Recruiter Profiles Table
    op.create_table(
        "recruiter_profiles",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Jobs Table (Tenant RLS Scoped)
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("department", sa.String(length=255), nullable=True, index=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column(
            "employment_type",
            postgresql.ENUM("FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP", name="employmenttypeenum"),
            nullable=False,
            server_default="FULL_TIME",
        ),
        sa.Column(
            "status",
            postgresql.ENUM("DRAFT", "PUBLISHED", "PAUSED", "CLOSED", name="jobstatusenum"),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("created_by_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Enable & FORCE RLS on jobs
    op.execute("ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE jobs FORCE ROW LEVEL SECURITY;")
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

    # 3. Organization Invites Table (Tenant RLS Scoped)
    op.create_table(
        "organization_invites",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email", sa.String(length=255), nullable=False, index=True),
        sa.Column(
            "role",
            postgresql.ENUM("PLATFORM_ADMIN", "ORGANIZATION_ADMIN", "RECRUITER", "CANDIDATE", name="roleenum", create_type=False),
            nullable=False,
            server_default="RECRUITER",
        ),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("invited_by_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Enable & FORCE RLS on organization_invites
    op.execute("ALTER TABLE organization_invites ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE organization_invites FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY organization_invites_tenant_isolation ON organization_invites
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS organization_invites_tenant_isolation ON organization_invites;")
    op.drop_table("organization_invites")
    op.execute("DROP POLICY IF EXISTS jobs_tenant_isolation ON jobs;")
    op.drop_table("jobs")
    op.drop_table("recruiter_profiles")
    op.execute("DROP TYPE IF EXISTS employmenttypeenum;")
    op.execute("DROP TYPE IF EXISTS jobstatusenum;")
