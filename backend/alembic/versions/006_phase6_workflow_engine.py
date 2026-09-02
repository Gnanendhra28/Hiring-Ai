"""006_phase6_workflow_engine

Revision ID: 006_phase6_workflow_engine
Revises: 005_phase5_job_verification
Create Date: 2026-08-14 15:35:00.000000

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_phase6_workflow_engine"
down_revision: str | None = "005_phase5_job_verification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. Assessments Table
    op.create_table(
        "assessments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("passing_score", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE assessments FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY assessments_tenant_isolation ON assessments FOR ALL
        USING (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
        WITH CHECK (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
    """)

    # 2. Assessment Assignments Table
    assignment_status_enum = postgresql.ENUM(
        "DRAFT", "READY", "SENT", "STARTED", "COMPLETED", "EXPIRED", "CANCELLED", name="assessmentassignmentstatusenum", create_type=False
    )
    op.execute("CREATE TYPE assessmentassignmentstatusenum AS ENUM ('DRAFT', 'READY', 'SENT', 'STARTED', 'COMPLETED', 'EXPIRED', 'CANCELLED');")

    op.create_table(
        "assessment_assignments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("assessment_id", sa.UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("application_id", sa.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", assignment_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE assessment_assignments ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE assessment_assignments FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY assessment_assignments_tenant_isolation ON assessment_assignments FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

    # 3. Assessment Results Table
    op.create_table(
        "assessment_results",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("assignment_id", sa.UUID(as_uuid=True), sa.ForeignKey("assessment_assignments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE assessment_results ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE assessment_results FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY assessment_results_tenant_isolation ON assessment_results FOR ALL
        USING (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
        WITH CHECK (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
    """)

    # 4. Interviews Table
    interview_type_enum = postgresql.ENUM("TECHNICAL", "BEHAVIORAL", "HR", "SYSTEM_DESIGN", name="interviewtypeenum", create_type=False)
    interview_status_enum = postgresql.ENUM("SCHEDULED", "RESCHEDULED", "COMPLETED", "CANCELLED", name="interviewstatusenum", create_type=False)
    meeting_provider_enum = postgresql.ENUM("TEAMS", "ZOOM", "MEET", "TEST", name="meetingproviderenum", create_type=False)

    op.execute("CREATE TYPE interviewtypeenum AS ENUM ('TECHNICAL', 'BEHAVIORAL', 'HR', 'SYSTEM_DESIGN');")
    op.execute("CREATE TYPE interviewstatusenum AS ENUM ('SCHEDULED', 'RESCHEDULED', 'COMPLETED', 'CANCELLED');")
    op.execute("CREATE TYPE meetingproviderenum AS ENUM ('TEAMS', 'ZOOM', 'MEET', 'TEST');")

    op.create_table(
        "interviews",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("application_id", sa.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("interviewer_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("interview_type", interview_type_enum, nullable=False, server_default="TECHNICAL"),
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False, server_default="UTC"),
        sa.Column("status", interview_status_enum, nullable=False, server_default="SCHEDULED"),
        sa.Column("meeting_provider", meeting_provider_enum, nullable=False, server_default="TEST"),
        sa.Column("meeting_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE interviews FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY interviews_tenant_isolation ON interviews FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        );
    """)

    # 5. Communications Table
    workflow_stage_enum = postgresql.ENUM("SHORTLIST", "ASSESSMENT_INVITATION", "INTERVIEW_INVITATION", "REJECTION", "OFFER", name="workflowstageenum", create_type=False)
    comm_status_enum = postgresql.ENUM("DRAFT", "PENDING_APPROVAL", "APPROVED", "SENDING", "SENT", "FAILED", "CANCELLED", "DELETED", name="communicationstatusenum", create_type=False)

    op.execute("CREATE TYPE workflowstageenum AS ENUM ('SHORTLIST', 'ASSESSMENT_INVITATION', 'INTERVIEW_INVITATION', 'REJECTION', 'OFFER');")
    op.execute("CREATE TYPE communicationstatusenum AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'SENDING', 'SENT', 'FAILED', 'CANCELLED', 'DELETED');")

    op.create_table(
        "communications",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("application_id", sa.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("workflow_stage", workflow_stage_enum, nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", comm_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="MAILPIT"),
        sa.Column("validation_json", sa.JSON(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE communications ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE communications FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY communications_tenant_isolation ON communications FOR ALL
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
    op.execute("DROP POLICY IF EXISTS communications_tenant_isolation ON communications;")
    op.drop_table("communications")
    op.execute("DROP TYPE IF EXISTS communicationstatusenum;")
    op.execute("DROP TYPE IF EXISTS workflowstageenum;")

    op.execute("DROP POLICY IF EXISTS interviews_tenant_isolation ON interviews;")
    op.drop_table("interviews")
    op.execute("DROP TYPE IF EXISTS meetingproviderenum;")
    op.execute("DROP TYPE IF EXISTS interviewstatusenum;")
    op.execute("DROP TYPE IF EXISTS interviewtypeenum;")

    op.execute("DROP POLICY IF EXISTS assessment_results_tenant_isolation ON assessment_results;")
    op.drop_table("assessment_results")

    op.execute("DROP POLICY IF EXISTS assessment_assignments_tenant_isolation ON assessment_assignments;")
    op.drop_table("assessment_assignments")
    op.execute("DROP TYPE IF EXISTS assessmentassignmentstatusenum;")

    op.execute("DROP POLICY IF EXISTS assessments_tenant_isolation ON assessments;")
    op.drop_table("assessments")
