"""Phase 9B Candidate Scoring tables and RLS policies

Revision ID: 011_phase9b_candidate_scoring
Revises: 010_phase9a_candidate_matching
Create Date: 2026-08-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '011_phase9b_candidate_scoring'
down_revision: Union[str, None] = '010_phase9a_candidate_matching'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums if they do not exist
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE eligibilitystatusenum AS ENUM ('PASS', 'FAIL', 'PENDING', 'UNKNOWN');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    op.execute("""
    DO $$ BEGIN
        CREATE TYPE factortypeenum AS ENUM ('REQUIRED_SKILLS', 'SEMANTIC_MATCH', 'EXPERIENCE', 'EDUCATION', 'PREFERRED_SKILLS', 'OTHER_REQUIREMENTS');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    op.execute("""
    DO $$ BEGIN
        CREATE TYPE confidencetierenum AS ENUM ('HIGH', 'MEDIUM', 'LOW');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    op.execute("""
    DO $$ BEGIN
        CREATE TYPE scoringprocessingstatusenum AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    # 2. Table: scoring_configurations
    op.create_table(
        'scoring_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('required_skills_weight', sa.Float(), nullable=False, server_default='0.30'),
        sa.Column('semantic_match_weight', sa.Float(), nullable=False, server_default='0.20'),
        sa.Column('experience_weight', sa.Float(), nullable=False, server_default='0.20'),
        sa.Column('education_weight', sa.Float(), nullable=False, server_default='0.10'),
        sa.Column('preferred_skills_weight', sa.Float(), nullable=False, server_default='0.10'),
        sa.Column('other_requirements_weight', sa.Float(), nullable=False, server_default='0.10'),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_scoring_configurations_org_id', 'scoring_configurations', ['organization_id'])

    # 3. Table: candidate_job_scores
    op.create_table(
        'candidate_job_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_intelligence_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_intelligence_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=True),
        sa.Column('scoring_configuration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scoring_configurations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scoring_configuration_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('eligibility_status', postgresql.ENUM('PASS', 'FAIL', 'PENDING', 'UNKNOWN', name='eligibilitystatusenum', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score_confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('confidence_tier', postgresql.ENUM('HIGH', 'MEDIUM', 'LOW', name='confidencetierenum', create_type=False), nullable=False, server_default='HIGH'),
        sa.Column('status', postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='scoringprocessingstatusenum', create_type=False), nullable=False, server_default='COMPLETED'),
        sa.Column('safe_error_message', sa.Text(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_candidate_job_scores_org_id', 'candidate_job_scores', ['organization_id'])
    op.create_index('idx_candidate_job_scores_job_id', 'candidate_job_scores', ['job_id'])
    op.create_index('idx_candidate_job_scores_candidate_id', 'candidate_job_scores', ['candidate_id'])
    op.create_index(
        'uq_candidate_job_score_version',
        'candidate_job_scores',
        ['job_id', 'candidate_id', 'job_intelligence_version_id', 'candidate_document_id', 'scoring_configuration_version'],
        unique=True,
    )

    # 4. Table: candidate_factor_scores
    op.create_table(
        'candidate_factor_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_job_score_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_job_scores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('factor_type', postgresql.ENUM('REQUIRED_SKILLS', 'SEMANTIC_MATCH', 'EXPERIENCE', 'EDUCATION', 'PREFERRED_SKILLS', 'OTHER_REQUIREMENTS', name='factortypeenum', create_type=False), nullable=False),
        sa.Column('raw_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('normalized_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('configured_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('normalized_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('weighted_contribution', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('applicable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_candidate_factor_scores_score_id', 'candidate_factor_scores', ['candidate_job_score_id'])

    # 5. Table: candidate_hard_requirement_results
    op.create_table(
        'candidate_hard_requirement_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_job_score_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_job_scores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='MATCHED'),
        sa.Column('candidate_value', sa.String(500), nullable=True),
        sa.Column('required_value', sa.String(500), nullable=True),
        sa.Column('operator', sa.String(50), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('evidence_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_candidate_hard_req_score_id', 'candidate_hard_requirement_results', ['candidate_job_score_id'])

    # 6. Table: scoring_processing_audits
    op.create_table(
        'scoring_processing_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_job_score_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_job_scores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('processing_duration_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='COMPLETED'),
        sa.Column('error_message_safe', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_scoring_audits_score_id', 'scoring_processing_audits', ['candidate_job_score_id'])

    # 7. Enable and FORCE RLS on all 5 tables
    tables = [
        'scoring_configurations',
        'candidate_job_scores',
        'candidate_factor_scores',
        'candidate_hard_requirement_results',
        'scoring_processing_audits',
    ]

    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
        CREATE POLICY {table}_tenant_isolation_policy ON {table}
        AS PERMISSIVE FOR ALL
        TO PUBLIC
        USING (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
        WITH CHECK (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
        """)


def downgrade() -> None:
    tables = [
        'scoring_processing_audits',
        'candidate_hard_requirement_results',
        'candidate_factor_scores',
        'candidate_job_scores',
        'scoring_configurations',
    ]

    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")
        op.drop_table(table)

    op.execute("DROP TYPE IF EXISTS scoringprocessingstatusenum;")
    op.execute("DROP TYPE IF EXISTS confidencetierenum;")
    op.execute("DROP TYPE IF EXISTS factortypeenum;")
    op.execute("DROP TYPE IF EXISTS eligibilitystatusenum;")
