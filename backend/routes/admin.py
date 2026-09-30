import asyncio
import os
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case, text
from datetime import datetime, timedelta, timezone
from database import get_db
from models.user import User
from models.transcription import Transcription
from models.audit_log import AuditLog
from middleware.admin import get_admin_user
from services.auth_service import hash_password
from schemas.admin import (
    AdminUserItem, AdminUserList, AdminUserDetail, AdminStats,
    AdminCreateUser, AdminUpdateUser,
    AdminActivityItem, AdminActivityList, AdminSystemHealth,
    AuditLogItem, AuditLogList,
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

_start_time = time.time()


async def log_audit(db: AsyncSession, admin: User, action: str, target_type: str = None, target_id: int = None, detail: str = None, ip: str = None):
    entry = AuditLog(
        admin_id=admin.id, admin_username=admin.username,
        action=action, target_type=target_type, target_id=target_id,
        detail=detail, ip_address=ip,
    )
    db.add(entry)


@router.get("/audit", response_model=AuditLogList)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    count_result = await db.execute(select(func.count()).select_from(AuditLog))
    total = count_result.scalar()
    result = await db.execute(
        select(AuditLog).order_by(desc(AuditLog.created_at)).offset(offset).limit(per_page)
    )
    items = result.scalars().all()

    log_items = [
        AuditLogItem(
            id=item.id,
            admin_id=item.admin_id or 0,
            admin_username=item.admin_username,
            action=item.action,
            target_type=item.target_type,
            target_id=item.target_id,
            detail=item.detail,
            ip_address=item.ip_address,
            created_at=item.created_at,
        )
        for item in items
    ]
    return AuditLogList(items=log_items, total=total, page=page, per_page=per_page)


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    user_row = (await db.execute(
        select(
            func.count(User.id).label("total_users"),
            func.count(case((User.created_at >= week_ago, 1))).label("recent_signups"),
        )
    )).one()

    trans_row = (await db.execute(
        select(
            func.count(case((Transcription.activity_type == "transcription", 1))).label("t_count"),
            func.count(case((Transcription.activity_type == "translation", 1))).label("tr_count"),
            func.count(func.distinct(case(
                (Transcription.created_at >= week_ago, Transcription.user_id),
            ))).label("active_users_7d"),
            func.coalesce(func.sum(case(
                (Transcription.activity_type == "transcription",
                 func.length(Transcription.final_text) - func.length(func.replace(Transcription.final_text, " ", "")) + 1),
            )), 0).label("words_t"),
            func.coalesce(func.sum(case(
                (Transcription.activity_type == "translation",
                 func.length(Transcription.translation) - func.length(func.replace(Transcription.translation, " ", "")) + 1),
            )), 0).label("words_tr"),
        )
    )).one()

    week_start = today - timedelta(days=6)
    daily_rows = (await db.execute(
        select(
            func.date(Transcription.created_at).label("day"),
            func.count().label("count"),
        ).where(
            Transcription.created_at >= week_start
        ).group_by(func.date(Transcription.created_at))
    )).all()

    daily_map = {str(row.day): row.count for row in daily_rows}
    daily_activity = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = str(day.date())
        daily_activity.append({"date": day.strftime("%b %d"), "count": daily_map.get(day_str, 0)})

    return AdminStats(
        total_users=user_row.total_users,
        total_transcriptions=trans_row.t_count,
        total_translations=trans_row.tr_count,
        active_users_7d=trans_row.active_users_7d,
        recent_signups=user_row.recent_signups,
        total_words_transcribed=trans_row.words_t,
        total_words_translated=trans_row.words_tr,
        daily_activity=daily_activity,
    )


@router.post("/users", response_model=AdminUserItem, status_code=201)
async def create_user(
    body: AdminCreateUser,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    if body.email:
        existing_email = await db.execute(select(User).where(User.email == body.email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=await hash_password(body.password),
        is_admin=body.is_admin,
    )
    db.add(user)
    await log_audit(db, admin, "create_user", "user", None, f"Created user '{body.username}'")
    await db.commit()
    await db.refresh(user)

    return AdminUserItem(
        id=user.id, username=user.username, email=user.email,
        is_admin=user.is_admin, created_at=user.created_at,
    )


@router.get("/users", response_model=AdminUserList)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    role: str = Query(None),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    t_counts = (
        select(Transcription.user_id, func.count().label("transcription_count"))
        .where(Transcription.activity_type == "transcription")
        .group_by(Transcription.user_id)
    ).subquery()

    tr_counts = (
        select(Transcription.user_id, func.count().label("translation_count"))
        .where(Transcription.activity_type == "translation")
        .group_by(Transcription.user_id)
    ).subquery()

    last_active = (
        select(Transcription.user_id, func.max(Transcription.created_at).label("last_active"))
        .group_by(Transcription.user_id)
    ).subquery()

    base = (
        select(
            User.id.label("id"),
            User.username.label("username"),
            User.email.label("email"),
            User.is_admin.label("is_admin"),
            User.created_at.label("created_at"),
            func.coalesce(t_counts.c.transcription_count, 0).label("transcription_count"),
            func.coalesce(tr_counts.c.translation_count, 0).label("translation_count"),
            last_active.c.last_active.label("last_active"),
        )
        .outerjoin(t_counts, User.id == t_counts.c.user_id)
        .outerjoin(tr_counts, User.id == tr_counts.c.user_id)
        .outerjoin(last_active, User.id == last_active.c.user_id)
    )

    if search:
        base = base.where(User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
    if role == "admin":
        base = base.where(User.is_admin == True)
    elif role == "user":
        base = base.where(User.is_admin == False)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar()

    result = await db.execute(
        base.order_by(desc(User.created_at)).offset(offset).limit(per_page)
    )
    rows = result.all()

    items = [
        AdminUserItem(
            id=row.id, username=row.username, email=row.email,
            is_admin=row.is_admin, created_at=row.created_at,
            transcription_count=row.transcription_count,
            translation_count=row.translation_count,
            last_active=row.last_active,
        )
        for row in rows
    ]

    return AdminUserList(items=items, total=total, page=page, per_page=per_page)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    user_q = await db.execute(select(User).where(User.id == user_id))
    user = user_q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stats_row = (await db.execute(
        select(
            func.count(case((Transcription.activity_type == "transcription", 1))).label("t_count"),
            func.count(case((Transcription.activity_type == "translation", 1))).label("tr_count"),
            func.coalesce(func.sum(case(
                (Transcription.activity_type == "transcription",
                 func.length(Transcription.final_text) - func.length(func.replace(Transcription.final_text, " ", "")) + 1),
            )), 0).label("words_t"),
            func.coalesce(func.sum(case(
                (Transcription.activity_type == "translation",
                 func.length(Transcription.translation) - func.length(func.replace(Transcription.translation, " ", "")) + 1),
            )), 0).label("words_tr"),
            func.max(Transcription.created_at).label("last_active"),
        ).where(Transcription.user_id == user.id)
    )).one()

    recent_q = await db.execute(
        select(Transcription).where(Transcription.user_id == user.id).order_by(desc(Transcription.created_at)).limit(10)
    )
    recent = recent_q.scalars().all()
    recent_items = [
        AdminActivityItem(
            id=item.id, user=user.username, user_id=user.id,
            activity_type=item.activity_type,
            summary=f"{(item.final_text or '')[:60]} → {(item.translation or '')[:60]}" if item.activity_type == "translation" else (item.final_text or "")[:100],
            engine=item.engine, created_at=item.created_at,
        )
        for item in recent
    ]

    return AdminUserDetail(
        id=user.id, username=user.username, email=user.email,
        is_admin=user.is_admin, created_at=user.created_at,
        transcription_count=stats_row.t_count,
        translation_count=stats_row.tr_count,
        total_words_transcribed=stats_row.words_t,
        total_words_translated=stats_row.words_tr,
        last_active=stats_row.last_active,
        recent_activity=recent_items,
    )


@router.put("/users/{user_id}", response_model=AdminUserItem)
async def update_user(
    user_id: int,
    body: AdminUpdateUser,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.username is not None and body.username != user.username:
        existing = await db.execute(select(User).where(User.username == body.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = body.username

    if body.email is not None:
        if body.email != user.email:
            existing = await db.execute(select(User).where(User.email == body.email))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already in use")
        user.email = body.email

    if body.password:
        user.password_hash = await hash_password(body.password)

    if body.is_admin is not None:
        if user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot change your own admin status")
        user.is_admin = body.is_admin

    await log_audit(db, admin, "update_user", "user", user_id, f"Updated user '{user.username}'")
    await db.commit()
    await db.refresh(user)

    counts_row = (await db.execute(
        select(
            func.count(case((Transcription.activity_type == "transcription", 1))).label("t_count"),
            func.count(case((Transcription.activity_type == "translation", 1))).label("tr_count"),
        ).where(Transcription.user_id == user.id)
    )).one()

    return AdminUserItem(
        id=user.id, username=user.username, email=user.email,
        is_admin=user.is_admin, created_at=user.created_at,
        transcription_count=counts_row.t_count,
        translation_count=counts_row.tr_count,
    )


@router.put("/users/{user_id}/role")
async def toggle_admin_role(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own admin status")

    user.is_admin = not user.is_admin
    action = "promote_admin" if user.is_admin else "demote_admin"
    await log_audit(db, admin, action, "user", user_id, f"{'Promoted' if user.is_admin else 'Demoted'} user '{user.username}'")
    await db.commit()
    return {"is_admin": user.is_admin, "username": user.username}


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    await log_audit(db, admin, "delete_user", "user", user_id, f"Deleted user '{user.username}'")
    await db.delete(user)
    await db.commit()


@router.get("/activity", response_model=AdminActivityList)
async def get_activity(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    activity_type: str = Query(None),
    user_id: int = Query(None),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    base = (
        select(Transcription, User.username.label("username"))
        .join(User, Transcription.user_id == User.id)
    )
    if activity_type:
        base = base.where(Transcription.activity_type == activity_type)
    if user_id:
        base = base.where(Transcription.user_id == user_id)

    count_result = await db.execute(
        select(func.count()).select_from(
            select(Transcription).where(
                *([Transcription.activity_type == activity_type] if activity_type else []),
                *([Transcription.user_id == user_id] if user_id else []),
            ).subquery()
        )
    )
    total = count_result.scalar()

    result = await db.execute(
        base.order_by(desc(Transcription.created_at)).offset(offset).limit(per_page)
    )
    rows = result.all()

    activity_items = [
        AdminActivityItem(
            id=row.Transcription.id, user=row.username, user_id=row.Transcription.user_id,
            activity_type=row.Transcription.activity_type,
            summary=f"{(row.Transcription.final_text or '')[:60]} → {(row.Transcription.translation or '')[:60]}" if row.Transcription.activity_type == "translation" else (row.Transcription.final_text or "")[:100],
            engine=row.Transcription.engine, created_at=row.Transcription.created_at,
        )
        for row in rows
    ]

    return AdminActivityList(items=activity_items, total=total, page=page, per_page=per_page)


@router.get("/health", response_model=AdminSystemHealth)
async def get_system_health(
    admin: User = Depends(get_admin_user),
):
    db_ok = True
    try:
        from database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    asr_loaded = os.path.isdir(os.path.join(_base, "yoruba_model"))

    def _walk_storage():
        total = 0.0
        for path in ["yoruba_model", "models", "uploads"]:
            full = os.path.join(_base, path)
            if os.path.exists(full):
                for dirpath, _, filenames in os.walk(full):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.isfile(fp):
                            total += os.path.getsize(fp) / (1024 * 1024)
        return total

    storage_mb = await asyncio.to_thread(_walk_storage)

    engine_name = (
        "NLLB-200 + GPT-4o-mini"
        if os.environ.get("OPENAI_API_KEY")
        else "NLLB-200 (offline)"
    )

    return AdminSystemHealth(
        status="healthy" if db_ok else "degraded",
        db_connected=db_ok,
        asr_model_loaded=asr_loaded,
        translation_engine=engine_name,
        total_storage_mb=round(storage_mb, 1),
        uptime_seconds=round(time.time() - _start_time, 0),
    )
