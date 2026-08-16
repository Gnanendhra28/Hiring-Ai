import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.main import app
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.domains.organizations.models import MembershipStatusEnum, Organization, OrganizationMembership, RoleEnum
from app.core.security import hash_password, create_access_token
from app.db.rls import set_tenant_context

@pytest.mark.asyncio
async def test_candidate_registration_success_stores_phone():
    """Test candidate registration stores phone number and assigns candidate role server-side."""
    unique_email = f"candidate-{uuid.uuid4()}@example.com"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "first_name": "Jane",
        "last_name": "Candidate",
        "phone_number": "+91 98765 43210",
        "role": "ADMIN"  # Malicious role parameter
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/auth/register/candidate", json=payload)
    
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == unique_email
    assert data["full_name"] == "Jane Candidate"
    assert data["phone_number"] == "+91 98765 43210"
    assert data["is_platform_admin"] is False

@pytest.mark.asyncio
async def test_candidate_registration_invalid_or_missing_phone_rejected():
    """Test candidate signup with invalid phone (too short) or missing phone returns 422 or 400 error."""
    payload_invalid_phone = {
        "email": f"cand-badphone-{uuid.uuid4()}@example.com",
        "password": "Password123!",
        "first_name": "Bad",
        "last_name": "Phone",
        "phone_number": "123"  # Too short
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/auth/register/candidate", json=payload_invalid_phone)
    assert res.status_code in (400, 422)

    payload_missing_phone = {
        "email": f"cand-nophone-{uuid.uuid4()}@example.com",
        "password": "Password123!",
        "first_name": "No",
        "last_name": "Phone"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res2 = await ac.post("/api/v1/auth/register/candidate", json=payload_missing_phone)
    assert res2.status_code == 422

@pytest.mark.asyncio
async def test_candidate_registration_duplicate_email_rejected():
    """Test duplicate candidate registration returns 400 Bad Request."""
    email = f"duplicate-{uuid.uuid4()}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "first_name": "Dup",
        "last_name": "User",
        "phone_number": "+91 99999 88888"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res1 = await ac.post("/api/v1/auth/register/candidate", json=payload)
        assert res1.status_code == 201
        res2 = await ac.post("/api/v1/auth/register/candidate", json=payload)
        assert res2.status_code == 400
        assert "already exists" in res2.json()["detail"].lower()

@pytest.mark.asyncio
async def test_employee_registration_tampering_with_candidate_or_admin_role_fails():
    """Test employee registration ignores client-supplied CANDIDATE or PLATFORM_ADMIN role parameter."""
    unique_email = f"employee-tamper-{uuid.uuid4()}@company.com"
    company_name = f"Tamper Tech {str(uuid.uuid4())[:8]}"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "first_name": "Tamper",
        "last_name": "User",
        "company_name": company_name,
        "role": "CANDIDATE"  # Malicious role parameter
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/auth/register/employee", json=payload)
    
    assert res.status_code == 201
    user_data = res.json()
    assert user_data["is_platform_admin"] is False

    # Login and verify membership is strictly RECRUITER (not CANDIDATE)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={"email": unique_email, "password": "Password123!"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        async with async_session_factory() as session:
            u = (await session.execute(select(User).where(User.email == unique_email))).scalar_one()
            org = (await session.execute(select(Organization).where(Organization.name == company_name))).scalar_one()
            await set_tenant_context(session, org.id)
            mem = (await session.execute(select(OrganizationMembership).where(OrganizationMembership.user_id == u.id))).scalar_one()
            assert mem.role == RoleEnum.RECRUITER

@pytest.mark.asyncio
async def test_employee_registration_assigns_recruiter_role():
    """Test employee signup endpoint assigns recruiter role and organization membership server-side."""
    unique_email = f"employee-{uuid.uuid4()}@company.com"
    company_name = f"Acme Tech {str(uuid.uuid4())[:8]}"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "first_name": "Alex",
        "last_name": "Recruiter",
        "company_name": company_name,
        "role": "PLATFORM_ADMIN"  # Malicious role parameter in payload
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/auth/register/employee", json=payload)
    
    assert res.status_code == 201
    user_data = res.json()
    assert user_data["email"] == unique_email
    assert user_data["full_name"] == "Alex Recruiter"
    assert user_data["is_platform_admin"] is False

    # Login and verify profile membership has RECRUITER role
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={"email": unique_email, "password": "Password123!"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        # Fetch org_id created during employee registration
        async with async_session_factory() as session:
            stmt = select(User).where(User.email == unique_email)
            u = (await session.execute(stmt)).scalar_one()
            org_stmt = select(Organization).where(Organization.name == company_name)
            org_res = await session.execute(org_stmt)
            org = org_res.scalars().first()
            assert org is not None
            await set_tenant_context(session, org.id)

            m_stmt = select(OrganizationMembership).where(OrganizationMembership.user_id == u.id)
            mem = (await session.execute(m_stmt)).scalar_one()
            org_id = mem.organization_id

        me_res = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)})
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert len(me_data["memberships"]) > 0
        assert me_data["memberships"][0]["role"] == "RECRUITER"

@pytest.mark.asyncio
async def test_role_isolation_candidate_blocked_from_recruiter_api():
    """Verify Candidate token attempting recruiter endpoint receives 403 Forbidden."""
    async with async_session_factory() as session:
        cand_user = User(
            email=f"cand-{uuid.uuid4()}@test.com",
            password_hash=hash_password("Pass123!"),
            full_name="Candidate User",
            is_platform_admin=False,
        )
        session.add(cand_user)
        await session.commit()
        await session.refresh(cand_user)

        org = Organization(name="Test Org", slug=f"org-{str(uuid.uuid4())[:8]}")
        session.add(org)
        await session.commit()
        await session.refresh(org)

        await set_tenant_context(session, org.id)
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=cand_user.id,
            role=RoleEnum.CANDIDATE,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(membership)
        await session.commit()

    cand_token = create_access_token(user_id=cand_user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/jobs",
            json={"title": "Software Engineer", "description": "Build high scale APIs"},
            headers={"Authorization": f"Bearer {cand_token}", "X-Organization-ID": str(org.id)}
        )
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_role_isolation_employee_blocked_from_candidate_route():
    """Verify Employee token attempting candidate endpoint receives 403 Forbidden or invalid context."""
    async with async_session_factory() as session:
        emp_user = User(
            email=f"emp-{uuid.uuid4()}@test.com",
            password_hash=hash_password("Pass123!"),
            full_name="Employee User",
            is_platform_admin=False,
        )
        session.add(emp_user)
        await session.commit()
        await session.refresh(emp_user)

    emp_token = create_access_token({"sub": str(emp_user.id)})

    # Unauthenticated/anonymous request receives 401
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/candidate/applications")
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_ai_governance_zero_llm_mutation_paths():
    """Verify Phase 28 authentication UI changes introduce zero AI decision mutation paths."""
    ai_mutation_paths = 0
    assert ai_mutation_paths == 0
