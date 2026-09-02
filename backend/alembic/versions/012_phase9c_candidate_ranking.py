"""Phase 9C Candidate Ranking tables and RLS policies

Revision ID: 012_phase9c_candidate_ranking
Revises: 011_phase9b_candidate_scoring
Create Date: 2026-08-14

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '012_phase9c_candidate_ranking'
down_revision: str | None = '011_phase9b_candidate_scoring'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create Enum if it does not exist
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE rankingversionstatusenum AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'STALE');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    # 2. Table: candidate_ranking_versions
    op.create_table(
        'candidate_ranking_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_intelligence_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_intelligence_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scoring_configuration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scoring_configurations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ranking_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('top_k', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('status', postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'STALE', name='rankingversionstatusenum', create_type=False), nullable=False, server_default='COMPLETED'),
        sa.Column('candidate_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('eligible_candidate_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ineligible_candidate_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unknown_candidate_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_candidate_ranking_versions_org_id', 'candidate_ranking_versions', ['organization_id'])
    op.create_index('idx_candidate_ranking_versions_job_id', 'candidate_ranking_versions', ['job_id'])
    op.create_index(
        'uq_candidate_ranking_version_num',
        'candidate_ranking_versions',
        ['job_id', 'ranking_version'],
        unique=True,
    )

    # 3. Table: candidate_job_rankings
    op.create_table(
        'candidate_job_rankings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ranking_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_ranking_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=True),
        sa.Column('candidate_job_score_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_job_scores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_intelligence_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_intelligence_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rank_position', sa.Integer(), nullable=False),
        sa.Column('is_top_k', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('eligibility_status', postgresql.ENUM('PASS', 'FAIL', 'PENDING', 'UNKNOWN', name='eligibilitystatusenum', create_type=False), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score_confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_candidate_job_rankings_org_id', 'candidate_job_rankings', ['organization_id'])
    op.create_index('idx_candidate_job_rankings_ver_id', 'candidate_job_rankings', ['ranking_version_id'])
    op.create_index('idx_candidate_job_rankings_job_id', 'candidate_job_rankings', ['job_id'])
    op.create_index('idx_candidate_job_rankings_candidate_id', 'candidate_job_rankings', ['candidate_id'])
    op.create_index('idx_candidate_job_rankings_rank_pos', 'candidate_job_rankings', ['rank_position'])
    op.create_index('idx_candidate_job_rankings_is_top_k', 'candidate_job_rankings', ['is_top_k'])
    op.create_index(
        'uq_candidate_job_ranking_version_candidate',
        'candidate_job_rankings',
        ['ranking_version_id', 'candidate_id'],
        unique=True,
    )

    # 4. Table: ranking_processing_audits
    op.create_table(
        'ranking_processing_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ranking_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_ranking_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('processing_duration_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='COMPLETED'),
        sa.Column('error_message_safe', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_ranking_audits_ver_id', 'ranking_processing_audits', ['ranking_version_id'])

    # 5. Enable and FORCE RLS on all 3 tables
    tables = [
        'candidate_ranking_versions',
        'candidate_job_rankings',
        'ranking_processing_audits',
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
        'ranking_processing_audits',
        'candidate_job_rankings',
        'candidate_ranking_versions',
    ]

    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")
        op.drop_table(table)

    op.execute("DROP TYPE IF EXISTS rankingversionstatusenum;")
