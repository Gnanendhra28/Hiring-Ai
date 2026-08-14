"""Phase 9D Candidate Recommendation and Decision Workflow tables and RLS policies

Revision ID: 013_phase9d_recommendation
Revises: 012_phase9c_candidate_ranking
Create Date: 2026-08-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '013_phase9d_recommendation'
down_revision: Union[str, None] = '012_phase9c_candidate_ranking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums if they do not exist
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE recommendationtypeenum AS ENUM (
            'STRONGLY_RECOMMEND_REVIEW',
            'RECOMMEND_REVIEW',
            'NEUTRAL_REVIEW',
            'REQUIRES_REVIEW',
            'NOT_RECOMMENDED_FOR_REVIEW',
            'RECOMMENDATION_FAILED'
        );
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    op.execute("""
    DO $$ BEGIN
        CREATE TYPE reviewstateenum AS ENUM (
            'PENDING_REVIEW',
            'UNDER_REVIEW',
            'REVIEWED',
            'DECISION_REQUIRED',
            'DECIDED'
        );
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    op.execute("""
    DO $$ BEGIN
        CREATE TYPE recruiterdecisionenum AS ENUM (
            'ADVANCE',
            'REJECT',
            'HOLD',
            'REQUEST_MORE_INFORMATION',
            'NO_DECISION'
        );
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    op.execute("""
    DO $$ BEGIN
        CREATE TYPE reasoncodeenum AS ENUM (
            'ALL_CRITICAL_REQUIREMENTS_MET',
            'STRONG_REQUIRED_SKILL_ALIGNMENT',
            'STRONG_RELEVANT_EXPERIENCE',
            'HIGH_SCORE_CONFIDENCE',
            'TOP_K_CANDIDATE',
            'HARD_REQUIREMENT_FAILED',
            'LOW_SCORE_CONFIDENCE',
            'UNKNOWN_REQUIRED_INFORMATION',
            'MISSING_REQUIRED_SKILL',
            'PREFERRED_SKILL_GAP',
            'SEMANTIC_ALIGNMENT',
            'INSUFFICIENT_EVIDENCE'
        );
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    # 2. Table: candidate_recommendations
    op.create_table(
        'candidate_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=True),
        sa.Column('job_intelligence_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_intelligence_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_job_score_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_job_scores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ranking_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_ranking_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_type', postgresql.ENUM('STRONGLY_RECOMMEND_REVIEW', 'RECOMMEND_REVIEW', 'NEUTRAL_REVIEW', 'REQUIRES_REVIEW', 'NOT_RECOMMENDED_FOR_REVIEW', 'RECOMMENDATION_FAILED', name='recommendationtypeenum', create_type=False), nullable=False, server_default='RECOMMEND_REVIEW'),
        sa.Column('recommendation_confidence', sa.Float(), nullable=False, server_default='0.90'),
        sa.Column('status', sa.String(50), nullable=False, server_default='COMPLETED'),
        sa.Column('summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('strengths', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('gaps', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_candidate_recommendations_org_id', 'candidate_recommendations', ['organization_id'])
    op.create_index('idx_candidate_recommendations_job_id', 'candidate_recommendations', ['job_id'])
    op.create_index('idx_candidate_recommendations_cand_id', 'candidate_recommendations', ['candidate_id'])
    op.create_index(
        'uq_candidate_recommendation_version_tuple',
        'candidate_recommendations',
        ['job_id', 'candidate_id', 'job_intelligence_version_id', 'candidate_document_id', 'candidate_job_score_id', 'ranking_version_id'],
        unique=True,
    )

    # 3. Table: candidate_recommendation_reasons
    op.create_table(
        'candidate_recommendation_reasons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_recommendations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason_code', postgresql.ENUM('ALL_CRITICAL_REQUIREMENTS_MET', 'STRONG_REQUIRED_SKILL_ALIGNMENT', 'STRONG_RELEVANT_EXPERIENCE', 'HIGH_SCORE_CONFIDENCE', 'TOP_K_CANDIDATE', 'HARD_REQUIREMENT_FAILED', 'LOW_SCORE_CONFIDENCE', 'UNKNOWN_REQUIRED_INFORMATION', 'MISSING_REQUIRED_SKILL', 'PREFERRED_SKILL_GAP', 'SEMANTIC_ALIGNMENT', 'INSUFFICIENT_EVIDENCE', name='reasoncodeenum', create_type=False), nullable=False),
        sa.Column('reason_type', sa.String(50), nullable=False, server_default='POSITIVE'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_rec_reasons_rec_id', 'candidate_recommendation_reasons', ['recommendation_id'])

    # 4. Table: candidate_recommendation_evidence
    op.create_table(
        'candidate_recommendation_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_recommendations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False, server_default='CANDIDATE_DOCUMENT'),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('evidence_text', sa.Text(), nullable=False),
        sa.Column('verification_status', sa.String(50), nullable=False, server_default='VERIFIED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_rec_evidence_rec_id', 'candidate_recommendation_evidence', ['recommendation_id'])

    # 5. Table: candidate_decisions
    op.create_table(
        'candidate_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_recommendations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('review_state', postgresql.ENUM('PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED', 'DECISION_REQUIRED', 'DECIDED', name='reviewstateenum', create_type=False), nullable=False, server_default='PENDING_REVIEW'),
        sa.Column('decision', postgresql.ENUM('ADVANCE', 'REJECT', 'HOLD', 'REQUEST_MORE_INFORMATION', 'NO_DECISION', name='recruiterdecisionenum', create_type=False), nullable=False, server_default='NO_DECISION'),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('decided_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_candidate_decisions_org_id', 'candidate_decisions', ['organization_id'])
    op.create_index('idx_candidate_decisions_app_id', 'candidate_decisions', ['application_id'])
    op.create_index(
        'uq_candidate_decision_application',
        'candidate_decisions',
        ['application_id'],
        unique=True,
    )

    # 6. Table: candidate_decision_audits
    op.create_table(
        'candidate_decision_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_recommendations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision', postgresql.ENUM('ADVANCE', 'REJECT', 'HOLD', 'REQUEST_MORE_INFORMATION', 'NO_DECISION', name='recruiterdecisionenum', create_type=False), nullable=False),
        sa.Column('previous_state', sa.String(50), nullable=False),
        sa.Column('new_state', sa.String(50), nullable=False),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('decided_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('correlation_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_decision_audits_app_id', 'candidate_decision_audits', ['application_id'])

    # 7. Table: recommendation_processing_audits
    op.create_table(
        'recommendation_processing_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_recommendations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False, server_default='gemini'),
        sa.Column('model', sa.String(100), nullable=False, server_default='gemini-1.5-flash'),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('processing_duration_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='COMPLETED'),
        sa.Column('error_message_safe', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_rec_processing_audits_rec_id', 'recommendation_processing_audits', ['recommendation_id'])

    # 8. Enable and FORCE RLS on all 6 tables
    tables = [
        'candidate_recommendations',
        'candidate_recommendation_reasons',
        'candidate_recommendation_evidence',
        'candidate_decisions',
        'candidate_decision_audits',
        'recommendation_processing_audits',
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
        'recommendation_processing_audits',
        'candidate_decision_audits',
        'candidate_decisions',
        'candidate_recommendation_evidence',
        'candidate_recommendation_reasons',
        'candidate_recommendations',
    ]

    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")
        op.drop_table(table)

    op.execute("DROP TYPE IF EXISTS reasoncodeenum;")
    op.execute("DROP TYPE IF EXISTS recruiterdecisionenum;")
    op.execute("DROP TYPE IF EXISTS reviewstateenum;")
    op.execute("DROP TYPE IF EXISTS recommendationtypeenum;")
