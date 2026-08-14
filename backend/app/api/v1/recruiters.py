from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.v1.deps import get_current_user
from app.api.v1.schemas import RecruiterProfileRequest, RecruiterProfileResponse
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.domains.recruiters.models import RecruiterProfile

router = APIRouter(prefix="/recruiters", tags=["Recruiter Profiles"])

@router.get("/me", response_model=RecruiterProfileResponse)
async def get_my_recruiter_profile(user: User = Depends(get_current_user)):
    """Fetches recruiter profile metadata for current authenticated user."""
    async with async_session_factory() as session:
        stmt = select(RecruiterProfile).where(RecruiterProfile.user_id == user.id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            # Auto-create empty profile
            profile = RecruiterProfile(user_id=user.id)
            session.add(profile)
            await session.commit()
            await session.refresh(profile)

        return profile

@router.put("/me", response_model=RecruiterProfileResponse)
async def update_my_recruiter_profile(
    payload: RecruiterProfileRequest,
    user: User = Depends(get_current_user),
):
    """Creates or updates recruiter profile metadata."""
    async with async_session_factory() as session:
        stmt = select(RecruiterProfile).where(RecruiterProfile.user_id == user.id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = RecruiterProfile(
                user_id=user.id,
                job_title=payload.job_title,
                department=payload.department,
                phone_number=payload.phone_number,
            )
            session.add(profile)
        else:
            if payload.job_title is not None:
                profile.job_title = payload.job_title
            if payload.department is not None:
                profile.department = payload.department
            if payload.phone_number is not None:
                profile.phone_number = payload.phone_number

        await session.commit()
        await session.refresh(profile)

        return profile
