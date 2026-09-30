from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from database import get_db
from models.user import User
from models.transcription import Transcription
from middleware.auth import get_current_user
from schemas.auth import UserResponse
from schemas.profile import ProfileUpdateRequest, PasswordChangeRequest, UserStats
from services.auth_service import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Profile"])


@router.get("/stats", response_model=UserStats)
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        select(
            func.count(case((Transcription.activity_type == "transcription", 1))).label("t_count"),
            func.count(case((Transcription.activity_type == "translation", 1))).label("tr_count"),
            func.coalesce(func.sum(func.char_length(Transcription.final_text)), 0).label("words"),
        ).where(Transcription.user_id == user.id)
    )).one()

    return UserStats(
        total_transcriptions=row.t_count or 0,
        total_translations=row.tr_count or 0,
        total_words_translated=row.words or 0,
        account_created=user.created_at,
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.username and req.username != user.username:
        existing = await db.execute(select(User).where(User.username == req.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = req.username

    if req.email is not None:
        if req.email != user.email:
            if req.email:
                existing = await db.execute(select(User).where(User.email == req.email))
                if existing.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="Email already registered")
        user.email = req.email or None

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/password")
async def change_password(
    req: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await verify_password(req.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.password_hash = await hash_password(req.new_password)
    await db.commit()
    return {"message": "Password updated successfully"}
