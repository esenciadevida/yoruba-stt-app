import os

from fastapi import APIRouter, Depends, HTTPException, Query, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from database import get_db
from models.user import User
from models.transcription import Transcription
from middleware.auth import get_current_user
from schemas.transcription import HistoryResponse, HistoryItem, HistoryUpdate, TranscribeResponse, AudioQuality, WordConfidence, TranslateResponse, RetranslateRequest
from config import UPLOAD_DIR

router = APIRouter(prefix="/api/history", tags=["History"])

_EXT_MEDIA_TYPES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".mp4": "audio/mp4",
    ".flac": "audio/flac",
}


def _to_item(rec: Transcription) -> HistoryItem:
    has_audio = False
    if rec.audio_filename:
        has_audio = os.path.exists(os.path.join(UPLOAD_DIR, rec.audio_filename)) and \
            os.path.isfile(os.path.join(UPLOAD_DIR, rec.audio_filename))
    return HistoryItem(
        id=rec.id,
        activity_type=rec.activity_type,
        raw_text=rec.raw_text,
        final_text=rec.final_text,
        translation=rec.translation,
        source_language=rec.source_language,
        target_language=rec.target_language,
        engine=rec.engine,
        audio_filename=rec.audio_filename,
        original_filename=rec.original_filename,
        title=rec.title,
        pinned=bool(rec.pinned),
        has_audio=has_audio,
        created_at=rec.created_at,
    )


@router.get("", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    activity_type: str = Query(None, pattern="^(transcription|translation)$"),
    search: str = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    base_query = select(Transcription).where(Transcription.user_id == user.id)
    if activity_type:
        base_query = base_query.where(Transcription.activity_type == activity_type)
    if search:
        pattern = f"%{search}%"
        base_query = base_query.where(
            or_(
                Transcription.final_text.ilike(pattern),
                Transcription.raw_text.ilike(pattern),
                Transcription.translation.ilike(pattern),
                Transcription.title.ilike(pattern),
            )
        )

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(desc(Transcription.pinned), desc(Transcription.created_at))
        .offset(offset)
        .limit(per_page)
    )
    items = result.scalars().all()

    return HistoryResponse(
        items=[_to_item(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.patch("/{entry_id}", response_model=HistoryItem)
async def update_history_entry(
    entry_id: int,
    update: HistoryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transcription).where(
            Transcription.id == entry_id,
            Transcription.user_id == user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if update.title is not None:
        entry.title = update.title.strip() or None
    if update.pinned is not None:
        entry.pinned = update.pinned

    await db.commit()
    await db.refresh(entry)
    return _to_item(entry)


@router.delete("/{entry_id}", status_code=204)
async def delete_history_entry(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transcription).where(
            Transcription.id == entry_id,
            Transcription.user_id == user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Remove persistently stored audio so we don't leak files on disk.
    stored = entry.audio_filename
    await db.delete(entry)
    await db.commit()
    if stored:
        path = os.path.join(UPLOAD_DIR, stored)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


@router.get("/{entry_id}/audio")
async def get_history_audio(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transcription).where(
            Transcription.id == entry_id,
            Transcription.user_id == user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if not entry.audio_filename:
        raise HTTPException(status_code=404, detail="No audio stored for this entry")

    path = os.path.join(UPLOAD_DIR, entry.audio_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    ext = os.path.splitext(entry.audio_filename)[1].lower()
    media_type = _EXT_MEDIA_TYPES.get(ext, "application/octet-stream")
    return FileResponse(
        path,
        media_type=media_type,
        filename=entry.original_filename or f"recording{ext}",
    )


@router.post("/{entry_id}/retranscribe", response_model=TranscribeResponse)
async def retranscribe_history_entry(
    entry_id: int,
    language: str = Form("auto"),
    preferred_engine: str = Form("auto"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run the transcription pipeline on stored audio, updating the same entry."""
    result = await db.execute(
        select(Transcription).where(
            Transcription.id == entry_id,
            Transcription.user_id == user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if not entry.audio_filename:
        raise HTTPException(
            status_code=400,
            detail="This entry has no stored audio to re-transcribe (older recordings were not retained).",
        )

    path = os.path.join(UPLOAD_DIR, entry.audio_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    from routes.transcribe import _run_pipeline
    try:
        pipeline = await _run_pipeline(user, db, path, "audio", language, preferred_engine=preferred_engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-transcription failed: {e}")

    entry.raw_text = pipeline["raw_text"]
    entry.final_text = pipeline["final_text"]
    entry.engine = pipeline["engine"]
    entry.source_language = pipeline["detected_language"]
    await db.commit()
    await db.refresh(entry)

    quality = AudioQuality(**pipeline["quality_data"]) if pipeline["quality_data"] else None
    words = [WordConfidence(**w) for w in pipeline["word_confidences"]]

    return TranscribeResponse(
        raw_text=pipeline["raw_text"],
        final_text=pipeline["final_text"],
        confidence=pipeline["confidence"],
        word_confidences=words,
        quality=quality,
        id=entry.id,
        created_at=entry.created_at,
        detected_language=pipeline["detected_language"],
        code_switched=pipeline["code_switched"],
    )


@router.post("/{entry_id}/retranslate", response_model=TranslateResponse)
async def retranslate_history_entry(
    entry_id: int,
    req: RetranslateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run the translation pipeline on a stored entry's text, recording the
    result as a new translation history entry."""
    result = await db.execute(
        select(Transcription).where(
            Transcription.id == entry_id,
            Transcription.user_id == user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    source_text = entry.final_text or entry.raw_text or ""
    if not source_text.strip():
        raise HTTPException(
            status_code=400,
            detail="This entry has no text to re-translate.",
        )

    from routes.translate import run_translation_pipeline, save_translation, translation_quality

    pipeline = await run_translation_pipeline(source_text, req.direction)
    record = await save_translation(db, user, pipeline, source_text)

    return TranslateResponse(
        source_text=source_text,
        translated_text=pipeline["translated_text"],
        detected_language=pipeline["detected_language"],
        target_language=pipeline["target_language"],
        engine=pipeline["engine"],
        quality=translation_quality(pipeline["engine"]),
        code_switched=pipeline.get("code_switched", False),
    )