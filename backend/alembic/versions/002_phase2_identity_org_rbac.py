"""002_phase2_identity_org_rbac

Revision ID: 002_phase2_identity_org_rbac
Revises: 001_phase1_rls_pgvector
Create Date: 2026-08-14 15:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_phase2_identity_org_rbac"
down_revision: Union[str, None] = "001_phase1_rls_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_platform_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Organizations Table
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "verification_status",
            sa.Enum("UNVERIFIED", "PENDING_REVIEW", "VERIFIED", "REJECTED", name="organizationverificationstatusenum"),
            nullable=False,
            server_default="UNVERIFIED",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Organization Memberships Table
    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column(
            "role",
            sa.Enum("PLATFORM_ADMIN", "ORGANIZATION_ADMIN", "RECRUITER", "CANDIDATE", name="roleenum"),
            nullable=False,
            server_default="RECRUITER",
        ),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "SUSPENDED", "INVITED", name="membershipstatusenum"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_organization_user_membership"),
    )

    # Enable and FORCE RLS on organization_memberships
    op.execute("ALTER TABLE organization_memberships ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE organization_memberships FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY organization_memberships_tenant_isolation ON organization_memberships
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        );
    """)

    # 4. Processed Events Table (Idempotency)
    op.create_table(
        "processed_events",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("consumer_id", sa.String(length=255), nullable=False, index=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("event_id", "consumer_id", name="uq_event_consumer"),
    )

    # 5. Audit Logs Table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("action", sa.String(length=100), nullable=False, index=True),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Enable and FORCE RLS on audit_logs (when organization_id is set)
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY audit_logs_tenant_isolation ON audit_logs
        FOR ALL
        USING (
            organization_id IS NULL OR organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id IS NULL OR organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs;")
    op.drop_table("audit_logs")
    op.drop_table("processed_events")
    op.execute("DROP POLICY IF EXISTS organization_memberships_tenant_isolation ON organization_memberships;")
    op.drop_table("organization_memberships")
    op.drop_table("organizations")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS roleenum;")
    op.execute("DROP TYPE IF EXISTS membershipstatusenum;")
    op.execute("DROP TYPE IF EXISTS organizationverificationstatusenum;")
