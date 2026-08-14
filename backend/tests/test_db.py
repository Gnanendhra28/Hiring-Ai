import pytest
import uuid
from app.db.session import check_database_health
from app.db.uow import AsyncUnitOfWork
from app.db.models.rls_test import RLSTestRecord
from app.db.repositories.base import BaseRepository

@pytest.mark.asyncio
async def test_database_health():
    is_healthy = await check_database_health()
    assert is_healthy is True

@pytest.mark.asyncio
async def test_unit_of_work_transaction_commit():
    org_id = uuid.uuid4()
    record_id = uuid.uuid4()

    async with AsyncUnitOfWork(organization_id=org_id) as uow:
        repo = BaseRepository(RLSTestRecord, uow.session)
        record = RLSTestRecord(
            id=record_id,
            organization_id=org_id,
            title="Unit of Work Commit Test"
        )
        await repo.add(record)
        # Auto-committed at __aexit__

    # Verify persistence
    async with AsyncUnitOfWork(organization_id=org_id) as uow:
        repo = BaseRepository(RLSTestRecord, uow.session)
        fetched = await repo.get_by_id(record_id)
        assert fetched is not None
        assert fetched.title == "Unit of Work Commit Test"
        assert fetched.organization_id == org_id

@pytest.mark.asyncio
async def test_unit_of_work_transaction_rollback():
    org_id = uuid.uuid4()
    record_id = uuid.uuid4()

    try:
        async with AsyncUnitOfWork(organization_id=org_id) as uow:
            repo = BaseRepository(RLSTestRecord, uow.session)
            record = RLSTestRecord(
                id=record_id,
                organization_id=org_id,
                title="Rollback Test"
            )
            await repo.add(record)
            raise RuntimeError("Force Rollback")
    except RuntimeError:
        pass

    # Verify record was rolled back
    async with AsyncUnitOfWork(organization_id=org_id) as uow:
        repo = BaseRepository(RLSTestRecord, uow.session)
        fetched = await repo.get_by_id(record_id)
        assert fetched is None
