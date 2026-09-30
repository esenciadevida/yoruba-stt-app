import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from middleware.auth import get_current_user
from models.user import User
from models.transcription import Transcription
from schemas.transcription import TranslateRequest, TranslateResponse
from services.translation_service import translate
from config import MAX_TRANSLATION_CHARS

router = APIRouter(prefix="/api/translate", tags=["Translation"])


async def run_translation_pipeline(text: str, direction: str = "auto") -> dict:
    """Run the translation pipeline (auto code-switch aware).

    Returns a dict with translated_text, detected_language, target_language,
    engine and code_switched. Shared between the /api/translate route and the
    history re-translate endpoint.
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
    text_stripped = text.strip()
    if len(text_stripped) > MAX_TRANSLATION_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long ({len(text_stripped)}/{MAX_TRANSLATION_CHARS} chars). Try shorter text.",
        )

    try:
        # Auto mode: if text contains mixed Yoruba/English, use code-switch
        # to produce unified Yoruba output
        if direction == "auto":
            from common.code_switch import contains_mixed_language
            if contains_mixed_language(text_stripped):
                from common.code_switch import process_mixed_text
                cs_result = await asyncio.to_thread(process_mixed_text, text_stripped)
                if cs_result.get("code_switched"):
                    return {
                        "translated_text": cs_result["text"],
                        "detected_language": "mixed",
                        "target_language": "yo",
                        "engine": "gpt-4o-mini",
                        "code_switched": True,
                    }
                return await asyncio.to_thread(translate, text=text_stripped, direction=direction)
            return await asyncio.to_thread(translate, text=text_stripped, direction=direction)
        return await asyncio.to_thread(translate, text=text_stripped, direction=direction)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")


def translation_quality(engine: str) -> str:
    """Determine quality level based on engine."""
    if engine == "chunked":
        return "medium"
    if "nllb" in engine:
        return "medium"
    if "opus" in engine:
        return "low"
    return "high"


async def save_translation(db, user, result: dict, source_text: str) -> Transcription:
    """Persist a translation into history. Used by /api/translate, the stream
    path and history re-translate."""
    record = Transcription(
        user_id=user.id,
        activity_type="translation",
        translation=result["translated_text"],
        source_language=result["detected_language"],
        target_language=result["target_language"],
        engine=result["engine"],
        final_text=source_text.strip() if source_text else source_text,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.post("", response_model=TranslateResponse)
async def translate_text(
    req: TranslateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await run_translation_pipeline(req.text, req.direction)
    record = await save_translation(db, user, result, req.text)
    quality = translation_quality(result["engine"])

    return TranslateResponse(
        source_text=req.text,
        translated_text=result["translated_text"],
        detected_language=result["detected_language"],
        target_language=result["target_language"],
        engine=result["engine"],
        quality=quality,
        code_switched=result.get("code_switched", False),
    )
