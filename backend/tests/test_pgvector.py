import pytest
import uuid
from sqlalchemy import select
from app.db.uow import AsyncUnitOfWork
from app.db.models.rls_test import RLSTestRecord

@pytest.mark.asyncio
async def test_pgvector_extension_and_similarity_search():
    """
    PROVES POSTGRESQL PGVECTOR EXTENSION OPERABILITY:
    Inserts 1536-dimension embeddings into RLSTestRecord and executes
    vector cosine similarity search (<=> operator) against PostgreSQL.
    """
    org_id = uuid.uuid4()
    record_1_id = uuid.uuid4()
    record_2_id = uuid.uuid4()

    # Generate orthogonal 1536-dim vector embeddings
    embedding_vector_1 = [1.0] + [0.0] * 1535
    embedding_vector_2 = [0.0] + [1.0] * 1535

    async with AsyncUnitOfWork(organization_id=org_id) as uow:
        rec1 = RLSTestRecord(
            id=record_1_id,
            organization_id=org_id,
            title="Vector Target Profile A",
            embedding=embedding_vector_1
        )
        rec2 = RLSTestRecord(
            id=record_2_id,
            organization_id=org_id,
            title="Vector Target Profile B",
            embedding=embedding_vector_2
        )
        uow.session.add_all([rec1, rec2])

    # Query vector cosine similarity using pgvector operator <=>
    async with AsyncUnitOfWork(organization_id=org_id) as uow:
        # Search query vector aligned with vector 1
        query_vector = [0.95] + [0.05] + [0.0] * 1534
        stmt = (
            select(RLSTestRecord)
            .where(RLSTestRecord.id.in_([record_1_id, record_2_id]))
            .order_by(RLSTestRecord.embedding.cosine_distance(query_vector))
            .limit(1)
        )
        result = await uow.session.execute(stmt)
        nearest = result.scalar_one_or_none()

        assert nearest is not None
        assert nearest.id == record_1_id
        assert nearest.title == "Vector Target Profile A"
