import asyncio
import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.user import User
from models.transcription import Transcription
from middleware.auth import get_current_user
from services.stt_service import transcribe
from services.tone_service import restore_tones
from schemas.transcription import TranscribeResponse, AudioQuality, WordConfidence, PolishRequest, PolishResponse
from config import ALLOWED_AUDIO_TYPES, MAX_UPLOAD_SIZE_MB, UPLOAD_DIR

router = APIRouter(prefix="/api/transcribe", tags=["Transcription"])


async def _polish_text(text: str, language: str = "yo") -> dict:
    """Apply the offline polish passes to an already-transcribed draft.

    This is the second step of the two-step workflow: the user reviews the
    raw ASR draft, then clicks "Políṣ / Fix tone marks" and this runs
    code-switch resolution + tone restoration + english-guard on the
    *confirmed* text (which may have been edited by the user).

    Returns {"text": polished, "code_switched": bool, "language": str}.
    """
    import re
    from common.code_switch import contains_mixed_language, process_mixed_text
    from common.english_guard import restore_english_words

    final_text = (text or "").strip()
    code_switched = False
    final_lang = language or "yo"

    if final_text:
        # Resolve mixed Yoruba/English into one clean output.
        if contains_mixed_language(final_text):
            cs_result = await asyncio.to_thread(process_mixed_text, final_text)
            if cs_result.get("code_switched"):
                final_text = cs_result["text"]
                code_switched = True
                final_lang = "yo"

        # Rule-based tone restoration (safe: only touches words lacking
        # diacritics). Apply first so review gets better input.
        if final_lang in ("yo", "yor", "yoruba"):
            final_text = await asyncio.to_thread(restore_tones, final_text)

        # Two-pass AI review for Yoruba orthography/tone correctness, but
        # only when there's an NVIDIA API key configured.
        if final_lang in ("yo", "yor", "yoruba"):
            from services.transcription_review import review_transcription
            reviewed, was_reviewed = await asyncio.to_thread(
                review_transcription, final_text, final_lang
            )
            if was_reviewed:
                final_text = reviewed

        # Safety net: restore English words that gained Yoruba marks.
        final_text = await asyncio.to_thread(restore_english_words, final_text)

    return {
        "text": final_text,
        "code_switched": code_switched,
        "language": final_lang,
    }


async def _run_pipeline(
    user: User,
    db: AsyncSession,
    filepath: str,
    content_type: str,
    language: str,
    preferred_engine: str = "auto",
    draft_only: bool = False,
) -> dict:
    """Run the ASR cascade + polish (code-switch, review, tone) for one audio file.

    Returns a dict with raw_text, final_text, engine, detected_language,
    code_switched, confidence, word_confidences and quality_data.

    When ``draft_only`` is True, the pipeline stops at the raw ASR output:
    no code-switch resolution, no review, no tone restoration. This lets the
    UI show the user exactly what the speech engine heard *before* making
    any "improvement" passes, so transcription vs. translation errors can
    be seen separately.
    """
    # Build a per-user glossary from their correction history so the ASR
    # prompt is nudged towards words the user frequently corrects.
    from services.correction_vocabulary import build_glossary_hint
    custom_vocab = await build_glossary_hint(user.id, db)

    stt_result = await asyncio.to_thread(
        transcribe,
        filepath,
        content_type=content_type,
        language=language,
        custom_vocabulary=custom_vocab,
        retry_if_low=True,
        preferred_engine=preferred_engine,
    )
    raw_text = stt_result["text"]
    engine = stt_result.get("engine", "")

    # Resolve language: use detected_language from stt if auto
    detected_lang = stt_result.get("detected_language", language)
    if language in ("auto", ""):
        final_lang = detected_lang
    else:
        final_lang = language

    confidence = stt_result["confidence"]
    word_confidences = stt_result.get("word_confidences", [])
    quality_data = stt_result.get("quality", {})

    # Draft-only mode: report the raw ASR output verbatim so the user can
    # review where the speech engine's mistakes happened. No polishing.
    if draft_only:
        return {
            "raw_text": raw_text,
            "final_text": raw_text,
            "engine": engine,
            "detected_language": detected_lang,
            "code_switched": False,
            "confidence": confidence,
            "word_confidences": word_confidences,
            "quality_data": quality_data,
        }

    # Code-switch detection: if the transcription contains mixed
    # Yoruba and English, translate the English parts to Yoruba
    # to produce a unified Yoruba output.
    #
    # Skip if confidence is low (< 0.7): garbled ASR output would
    # produce bad code-switch results. Better to show raw text than
    # to translate garbage.
    code_switched = False
    final_text = raw_text
    if (raw_text or "").strip() and (confidence or 0) >= 0.7:
        from common.code_switch import contains_mixed_language, process_mixed_text
        if contains_mixed_language(raw_text):
            cs_result = await asyncio.to_thread(process_mixed_text, raw_text)
            if cs_result.get("code_switched"):
                final_text = cs_result["text"]
                code_switched = True
                detected_lang = "yo"
                final_lang = "yo"
                # Safety net: apply rule-based tone restoration to catch
                # any words GPT may have missed. Only touches words
                # without existing diacritics, so it's always safe.
                final_text = await asyncio.to_thread(restore_tones, final_text)

    # Two-pass AI verification for Yoruba: after the ASR engine returns, run
    # the raw text through a language model that fixes orthography, tone
    # marks and subdot letters (ẹ ọ ṣ) without changing meaning.
    #
    # Runs for ALL engines — including gpt-4o-transcribe, which produces
    # tone-marked output but still makes tone-mark errors that the review
    # pass corrects safely (rule: "if uncertain, leave unchanged").
    if (not code_switched
            and final_lang in ("yo", "yor", "yoruba")
            and (raw_text or "").strip()):
        from services.transcription_review import review_transcription
        reviewed, was_reviewed = await asyncio.to_thread(
            review_transcription, raw_text, final_lang
        )
        if was_reviewed:
            final_text = reviewed
        else:
            # Review returned no changes or is unavailable: fall back to
            # rule-based tone restoration for text lacking diacritics.
            if (confidence or 0) >= 0.6:
                _YORUBA_DIACRITICS = set(
                    "\u1eb9\u1ecd\u1e63\u00e1\u00e0\u00e9\u00e8"
                    "\u00ed\u00ec\u00f3\u00f2\u00fa\u00f9"
                )
                has_marks = any(c in _YORUBA_DIACRITICS for c in final_text)
                if not has_marks:
                    final_text = await asyncio.to_thread(restore_tones, final_text)
    elif (raw_text or "").strip() and (confidence or 0) >= 0.6:
        # Non-Yoruba final_lang: still apply rule-based tone restoration
        # for plain (un-toned) Yoruba text as a safety net.
        final_text = await asyncio.to_thread(restore_tones, final_text)

    # Safety net: restore English words that accidentally received Yoruba
    # tone marks / subdot letters from the ASR or the code-switch pass.
    from common.english_guard import restore_english_words
    final_text = await asyncio.to_thread(restore_english_words, final_text)

    return {
        "raw_text": raw_text,
        "final_text": final_text,
        "engine": engine,
        "detected_language": final_lang,
        "code_switched": code_switched,
        "confidence": confidence,
        "word_confidences": word_confidences,
        "quality_data": quality_data,
    }


@router.post("", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("auto"),
    draft_only: bool = Form(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_type = (audio.content_type or "").lower().strip()
    base_type = raw_type.split(";")[0].strip()

    # Validate against the whitelist to reject arbitrary uploads (e.g. a
    # malicious non-audio file that spoofs a broad content type).
    if base_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported audio type: {audio.content_type or 'unknown'}")

    content = await audio.read()
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_UPLOAD_SIZE_MB}MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    original_filename = audio.filename or "recording.webm"
    ext = os.path.splitext(original_filename)[1] or ".webm"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    try:
        pipeline = await _run_pipeline(user, db, filepath, audio.content_type, language, draft_only=draft_only)
    except Exception as e:
        # Pipeline failed: clean up the stored audio so we don't leak orphan files.
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    # Draft-only runs are intermediate (the user may edit the draft before
    # finalizing), so don't persist them to history yet. The audio is still
    # removed so we don't leak orphan files.
    if draft_only:
        if os.path.exists(filepath):
            os.remove(filepath)
        return TranscribeResponse(
            raw_text=pipeline["raw_text"],
            final_text=pipeline["raw_text"],
            confidence=pipeline["confidence"],
            word_confidences=[WordConfidence(**w) for w in pipeline["word_confidences"]],
            quality=AudioQuality(**pipeline["quality_data"]) if pipeline["quality_data"] else None,
            detected_language=pipeline["detected_language"],
            engine=pipeline["engine"],
            code_switched=False,
        )

    # Persist the audio so users can replay or re-transcribe later. The file
    # stays on disk (UPLOAD_DIR) and is removed only when the history entry is
    # deleted.
    record = Transcription(
        user_id=user.id,
        activity_type="transcription",
        raw_text=pipeline["raw_text"],
        final_text=pipeline["final_text"],
        audio_filename=filename,
        original_filename=original_filename,
        engine=pipeline["engine"],
        source_language=pipeline["detected_language"],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    quality = AudioQuality(**pipeline["quality_data"]) if pipeline["quality_data"] else None
    words = [WordConfidence(**w) for w in pipeline["word_confidences"]]

    return TranscribeResponse(
        raw_text=pipeline["raw_text"],
        final_text=pipeline["final_text"],
        confidence=pipeline["confidence"],
        word_confidences=words,
        quality=quality,
        id=record.id,
        created_at=record.created_at,
        detected_language=pipeline["detected_language"],
        engine=pipeline["engine"],
        code_switched=pipeline["code_switched"],
    )


@router.post("/polish", response_model=PolishResponse)
async def polish_draft(request: PolishRequest, user: User = Depends(get_current_user)):
    """Second step of the two-step workflow.

    Takes user-confirmed (possibly edited) draft text and applies the
    code-switch + tone restoration + orthographic review passes, so errors
    still visible in a protected draft get cleaned into final Yoruba.
    """
    try:
        result = await _polish_text(request.text, request.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Polish failed: {e}")
    return PolishResponse(text=result["text"])