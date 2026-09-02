"""Phase 14 Schema Synchronization: phone, resume_id, candidate & application profile extensions

Revision ID: 014_phase14_schema_sync
Revises: 013_phase9d_recommendation
Create Date: 2026-09-02

"""
from collections.abc import Sequence

from alembic import op

revision: str = '014_phase14_schema_sync'
down_revision: str | None = '013_phase9d_recommendation'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. users table
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);")

    # 2. jobs table
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary VARCHAR(100);")
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_website VARCHAR(500);")

    # 3. candidate_profiles table
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS phone VARCHAR(50);")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS headline VARCHAR(255);")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS summary TEXT;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS photo_url TEXT;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS degree VARCHAR(255);")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS college VARCHAR(255);")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS skills JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS experience JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS education JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS career_preferences JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS languages JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS internships JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS projects JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS accomplishments JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS employment JSON;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS website_url VARCHAR(500);")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500);")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS resume_url VARCHAR(1024);")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS raw_resume_text TEXT;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS resume_filename VARCHAR(255);")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS resume_filesize INTEGER;")
    op.execute("ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS resume_updated_at VARCHAR(100);")

    # 4. applications table
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS resume_id VARCHAR(255);")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS resume_file_path VARCHAR(500);")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS answers_json JSON;")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS decided_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL;")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS decided_at TIMESTAMPTZ;")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS decision_reason TEXT;")

    # 5. recruiter_profiles table
    op.execute("ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);")
    op.execute("ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);")
    op.execute("ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS website_url VARCHAR(500);")
    op.execute("ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS registration_id VARCHAR(255);")
    op.execute("ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500);")
    op.execute("ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) NOT NULL DEFAULT 'UNVERIFIED';")
    op.execute("ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS submitted_at VARCHAR(100);")

def downgrade() -> None:
    pass
