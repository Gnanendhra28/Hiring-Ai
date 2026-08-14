"""008_phase7_hnsw_vector_index

Revision ID: 008_phase7_hnsw_vector_index
Revises: 007_phase7_document_intelligence
Create Date: 2026-08-14 16:18:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = "008_phase7_hnsw_vector_index"
down_revision: Union[str, None] = "007_phase7_document_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Enums for Evidence Verification & Skill Duration
    op.execute("CREATE TYPE evidenceverificationstatusenum AS ENUM ('VERIFIED', 'PARTIALLY_VERIFIED', 'UNVERIFIED');")
    op.execute("CREATE TYPE skilldurationstatusenum AS ENUM ('DETERMINISTIC_CALCULATED', 'UNKNOWN');")

    # 2. Add columns to candidate tables
    op.execute("ALTER TABLE candidate_skills ADD COLUMN skill_duration_status skilldurationstatusenum NOT NULL DEFAULT 'UNKNOWN';")
    op.execute("ALTER TABLE candidate_skills ADD COLUMN evidence_verification_status evidenceverificationstatusenum NOT NULL DEFAULT 'UNVERIFIED';")
    op.execute("ALTER TABLE candidate_experiences ADD COLUMN evidence_verification_status evidenceverificationstatusenum NOT NULL DEFAULT 'UNVERIFIED';")
    op.execute("ALTER TABLE candidate_educations ADD COLUMN evidence_verification_status evidenceverificationstatusenum NOT NULL DEFAULT 'UNVERIFIED';")
    op.execute("ALTER TABLE candidate_extracted_facts ADD COLUMN evidence_verification_status evidenceverificationstatusenum NOT NULL DEFAULT 'UNVERIFIED';")

    # 3. Create HNSW Index on pgvector candidate embeddings
    op.execute("CREATE INDEX idx_candidate_embeddings_hnsw ON candidate_embeddings USING hnsw (embedding vector_cosine_ops);")

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_candidate_embeddings_hnsw;")
    op.execute("ALTER TABLE candidate_extracted_facts DROP COLUMN IF EXISTS evidence_verification_status;")
    op.execute("ALTER TABLE candidate_educations DROP COLUMN IF EXISTS evidence_verification_status;")
    op.execute("ALTER TABLE candidate_experiences DROP COLUMN IF EXISTS evidence_verification_status;")
    op.execute("ALTER TABLE candidate_skills DROP COLUMN IF EXISTS evidence_verification_status;")
    op.execute("ALTER TABLE candidate_skills DROP COLUMN IF EXISTS skill_duration_status;")
    op.execute("DROP TYPE IF EXISTS skilldurationstatusenum;")
    op.execute("DROP TYPE IF EXISTS evidenceverificationstatusenum;")
