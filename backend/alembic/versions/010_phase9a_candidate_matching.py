"""010_phase9a_candidate_matching

Revision ID: 010_phase9a_candidate_matching
Revises: 009_phase8_job_intelligence
Create Date: 2026-08-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_phase9a_candidate_matching'
down_revision = '009_phase8_job_intelligence'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create Enums explicitly via Raw SQL with IF NOT EXISTS guard
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'match_status_enum') THEN
                CREATE TYPE match_status_enum AS ENUM (
                    'MATCHED', 'PARTIALLY_MATCHED', 'NOT_MATCHED', 'UNKNOWN', 'NOT_APPLICABLE', 'PROTECTED_EXCLUDED'
                );
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'match_processing_status_enum') THEN
                CREATE TYPE match_processing_status_enum AS ENUM (
                    'PENDING', 'PROCESSING', 'RETRIEVING', 'HARD_RULE_EVALUATION', 'SEMANTIC_MATCHING', 'FEATURE_MATCHING', 'EVIDENCE_MAPPING', 'COMPLETED', 'FAILED', 'RETRY_REQUIRED', 'STALE'
                );
            END IF;
        END
        $$;
    """)

    match_status_enum = postgresql.ENUM(
        'MATCHED', 'PARTIALLY_MATCHED', 'NOT_MATCHED', 'UNKNOWN', 'NOT_APPLICABLE', 'PROTECTED_EXCLUDED',
        name='match_status_enum',
        create_type=False,
    )

    match_proc_status_enum = postgresql.ENUM(
        'PENDING', 'PROCESSING', 'RETRIEVING', 'HARD_RULE_EVALUATION', 'SEMANTIC_MATCHING', 'FEATURE_MATCHING', 'EVIDENCE_MAPPING', 'COMPLETED', 'FAILED', 'RETRY_REQUIRED', 'STALE',
        name='match_processing_status_enum',
        create_type=False,
    )

    # 2. Table: candidate_job_matches
    op.create_table(
        'candidate_job_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_intelligence_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_intelligence_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=True),
        sa.Column('matching_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', match_proc_status_enum, nullable=False, server_default='PENDING'),
        sa.Column('total_requirements_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('matched_requirements_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('hard_requirements_failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ai_provider', sa.String(length=50), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('overall_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('safe_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_cand_job_matches_org', 'candidate_job_matches', ['organization_id'])
    op.create_index('idx_cand_job_matches_job', 'candidate_job_matches', ['job_id'])
    op.create_index('idx_cand_job_matches_cand', 'candidate_job_matches', ['candidate_id'])
    op.create_index(
        'uq_candidate_job_match_version',
        'candidate_job_matches',
        ['job_id', 'candidate_id', 'job_intelligence_version_id', 'candidate_document_id'],
        unique=True,
    )

    # 3. Table: candidate_requirement_matches
    op.create_table(
        'candidate_requirement_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_job_matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_type', sa.String(length=50), nullable=False),
        sa.Column('raw_required_value', sa.Text(), nullable=False),
        sa.Column('canonical_required_value', sa.String(length=255), nullable=False),
        sa.Column('requirement_level', sa.String(length=50), nullable=False),
        sa.Column('hard_constraint', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('match_status', match_status_enum, nullable=False, server_default='UNKNOWN'),
        sa.Column('candidate_value', sa.Text(), nullable=True),
        sa.Column('normalized_candidate_value', sa.String(length=255), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('evidence_text', sa.Text(), nullable=True),
        sa.Column('evidence_verification_status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_cand_req_matches_org', 'candidate_requirement_matches', ['organization_id'])
    op.create_index('idx_cand_req_matches_match', 'candidate_requirement_matches', ['match_id'])
    op.create_index('idx_cand_req_matches_req', 'candidate_requirement_matches', ['job_requirement_id'])

    # 4. Table: candidate_semantic_matches
    op.create_table(
        'candidate_semantic_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_job_matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query_context', sa.String(length=50), nullable=False),
        sa.Column('candidate_context', sa.String(length=50), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('dimension', sa.Integer(), nullable=False, server_default='1536'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_cand_sem_matches_org', 'candidate_semantic_matches', ['organization_id'])
    op.create_index('idx_cand_sem_matches_match', 'candidate_semantic_matches', ['match_id'])

    # 5. Table: match_evidences
    op.create_table(
        'match_evidences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_requirement_matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quote_text', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_match_evidences_org', 'match_evidences', ['organization_id'])
    op.create_index('idx_match_evidences_req_match', 'match_evidences', ['requirement_match_id'])

    # 6. Table: match_processing_audits
    op.create_table(
        'match_processing_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_job_matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('processing_stage', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_match_proc_audits_org', 'match_processing_audits', ['organization_id'])
    op.create_index('idx_match_proc_audits_match', 'match_processing_audits', ['match_id'])

    # 7. Enable & Force Row Level Security on all 5 tables
    tables = [
        'candidate_job_matches',
        'candidate_requirement_matches',
        'candidate_semantic_matches',
        'match_evidences',
        'match_processing_audits',
    ]

    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            USING (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
        """)

def downgrade() -> None:
    tables = [
        'match_processing_audits',
        'match_evidences',
        'candidate_semantic_matches',
        'candidate_requirement_matches',
        'candidate_job_matches',
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)

    op.execute("DROP TYPE IF EXISTS match_processing_status_enum;")
    op.execute("DROP TYPE IF EXISTS match_status_enum;")
