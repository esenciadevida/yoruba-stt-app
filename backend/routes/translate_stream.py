import asyncio
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from database import get_db
from middleware.auth import get_current_user
from models.user import User
from models.transcription import Transcription
from schemas.transcription import TranslateRequest
from services.translation_service import GPT_SYSTEM_PROMPT, detect_language, translate
from common.nllb import translate_with_nllb
from common.nllb_quality import assess_en_to_yo
from common.translation import _with_few_shot
from config import OPENAI_API_KEY, MAX_TRANSLATION_CHARS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/translate", tags=["Translation"])


def _error_sse(msg: str) -> StreamingResponse:
    """Return a single-event SSE error response."""
    return StreamingResponse(
        iter([f"data: {json.dumps({'error': msg})}\n\n"]),
        media_type="text/event-stream",
    )


@router.post("/stream")
async def translate_stream(
    req: TranslateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream translation token-by-token using Server-Sent Events.

    Pipeline mirrors the non-streaming path:
      en2yo: NLLB first -> quality check -> GPT+RAG streaming if low quality
      yo2en: GPT+RAG streaming -> opus-mt fallback
    """
    if not req.text or not req.text.strip():
        return _error_sse("Empty text")

    text = req.text.strip()
    if len(text) > MAX_TRANSLATION_CHARS:
        return _error_sse(
            f"Text too long ({len(text)}/{MAX_TRANSLATION_CHARS} chars). Try shorter text."
        )

    direction = req.direction if hasattr(req, 'direction') else "auto"

    # Auto mode: check for mixed Yoruba/English and handle via code-switch
    if direction == "auto":
        from common.code_switch import contains_mixed_language
        if contains_mixed_language(text):
            return StreamingResponse(
                _code_switch_stream(text, user, db),
                media_type="text/event-stream",
            )

    if direction == "en2yo":
        detected = "en"
    elif direction == "yo2en":
        detected = "yo"
    else:
        detected = await asyncio.to_thread(detect_language, text)
        direction = "en2yo" if detected == "en" else "yo2en"

    # --- en2yo: try NLLB first, escalate to GPT+RAG streaming if low quality ---
    if direction == "en2yo":
        # Prefer GPT+RAG streaming when proper nouns are present: it preserves
        # them verbatim in English instead of transliterating like NLLB.
        from common.proper_nouns import contains_proper_nouns
        if contains_proper_nouns(text):
            logger.info("Proper nouns detected; using GPT+RAG streaming for en->yo")
            return StreamingResponse(
                _gpt_stream(text, detected, direction, user, db),
                media_type="text/event-stream",
            )

        nllb_result = await asyncio.to_thread(
            translate_with_nllb, text, direction=direction, detected=detected
        )
        if nllb_result is not None:
            good, reason = await asyncio.to_thread(
                assess_en_to_yo, text, nllb_result["translated_text"]
            )
            if good:
                full_text = nllb_result["translated_text"]
                return StreamingResponse(
                    _sse_generator(full_text, detected, "yo", "nllb-200", "medium", text, user, db),
                    media_type="text/event-stream",
                )
            logger.info("NLLB en->yo low quality (%s), streaming GPT+RAG", reason)

    # --- GPT streaming path (with RAG few-shot) ---
    return StreamingResponse(
        _gpt_stream(text, detected, direction, user, db),
        media_type="text/event-stream",
    )


async def _sse_generator(
    full_text: str, detected: str, target: str, engine: str, quality: str,
    source: str, user, db, code_switched: bool = False,
):
    """Yield a single done-event (for NLLB / local fallback results)."""
    yield f"data: {json.dumps({'token': '', 'done': True, 'full_text': full_text, 'detected_language': detected, 'target_language': target, 'engine': engine, 'quality': quality, 'code_switched': code_switched})}\n\n"
    await _save_translation(db, user, source, full_text, detected, target, engine)


async def _gpt_stream(text: str, detected: str, direction: str, user, db):
    """Stream GPT-4o-mini translation token-by-token with RAG few-shot."""
    if not OPENAI_API_KEY:
        result = await asyncio.to_thread(translate, text, direction)
        if not result:
            yield f"data: {json.dumps({'error': 'Translation service unavailable'})}\n\n"
            return
        full_text = result["translated_text"]
        yield f"data: {json.dumps({'token': '', 'done': True, 'full_text': full_text, 'detected_language': result['detected_language'], 'target_language': result['target_language'], 'engine': result['engine'], 'quality': 'fallback'})}\n\n"
        return

    target_lang_code = "en" if detected == "yo" else "yo"
    target_lang_name = "English" if detected == "yo" else "Yoruba"
    source_lang_name = "Yoruba" if detected == "yo" else "English"

    user_msg = f"Translate the following {source_lang_name} text to {target_lang_name}:\n\n{text}"
    user_msg = _with_few_shot(text, detected, user_msg)

    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": GPT_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=1024,
            stream=True,
        )

        full_text = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_text += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

        yield f"data: {json.dumps({'token': '', 'done': True, 'full_text': full_text, 'detected_language': detected, 'target_language': target_lang_code, 'engine': 'gpt-4o-mini', 'quality': 'high'})}\n\n"
        await _save_translation(db, user, text, full_text, detected, target_lang_code, "gpt-4o-mini")

    except Exception as e:
        logger.warning("Streaming translation failed: %s", e)
        yield f"data: {json.dumps({'error': 'Translation failed. Please try again.'})}\n\n"


async def _save_translation(db, user, source, translated, src_lang, tgt_lang, engine):
    """Save translation to history."""
    try:
        record = Transcription(
            user_id=user.id,
            activity_type="translation",
            translation=translated,
            source_language=src_lang,
            target_language=tgt_lang,
            engine=engine,
            final_text=source,
        )
        db.add(record)
        await db.commit()
    except Exception as e:
        logger.warning("Failed to save translation: %s", e)


CODE_SWITCH_SYSTEM_PROMPT = """You are an expert Yoruba language processor. Your job is to handle code-switched text — text that mixes English and Yoruba — and produce a unified, well-formatted Yoruba output.

RULES:
1. Identify which words/phrases are English and which are Yoruba.
2. Keep Yoruba portions EXACTLY as they are (preserve tone marks and spelling).
3. For English portions, apply these rules IN ORDER:

   a) LOANWORDS — keep as-is: In Nigerian Yoruba, many English words are used
      naturally as loanwords. When the speaker clearly uses an English noun or
      phrase as a natural part of their Yoruba sentence, KEEP IT AS-IS.
      Common loanwords to preserve: "wrist watch", "phone", "laptop", "car",
      "bread", "butter", "sugar", "money", "job", "office", "meeting", "boss",
      "salary", "problem", "thing", "place", "time", "day", "night", "ring",
      "chain", "bag", "shoe", "cap", "TV", "radio", "video", "camera", etc.

   b) ENGLISH SENTENCES/PHRASES — translate to Yoruba: When the speaker uses
      a full English phrase or sentence (not a single loanword), translate it
      to Yoruba. E.g. "I want to buy" → "mo fẹ́ ra".

   c) PROPER NOUNS: Personal names, brands, company names, clinic names, places
      → keep them VERBATIM in correct English spelling. NEVER transliterate them
      into Yoruba phonetics and NEVER add Yoruba tone marks or subdot letters
      to an English proper noun (incorrect: "baóklínitnííbi", "èlẹ́gọ́stìtibẹlawa";
      correct: "BioClinix", "Lagos State").

4. Make the output flow naturally as a single Yoruba sentence.
5. Use proper Yoruba orthography: subdot letters (ẹ, ọ, ṣ) and all tone marks.
6. Return ONLY the unified Yoruba text. No explanations, no quotes."""


async def _code_switch_stream(text: str, user, db):
    """Stream code-switch resolution token-by-token using GPT-4o-mini."""
    if not OPENAI_API_KEY:
        from common.code_switch import process_mixed_text
        cs_result = await asyncio.to_thread(process_mixed_text, text)
        full_text = cs_result["text"] if cs_result.get("code_switched") else text
        yield f"data: {json.dumps({'token': '', 'done': True, 'full_text': full_text, 'detected_language': 'mixed', 'target_language': 'yo', 'engine': 'gpt-4o-mini', 'quality': 'fallback', 'code_switched': cs_result.get('code_switched', False)})}\n\n"
        await _save_translation(db, user, text, full_text, "mixed", "yo", "gpt-4o-mini")
        return

    user_msg = f"Convert this mixed Yoruba/English text into unified, properly formatted Yoruba:\n\n{text}"

    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CODE_SWITCH_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=1024,
            stream=True,
        )

        full_text = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_text += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

        yield f"data: {json.dumps({'token': '', 'done': True, 'full_text': full_text, 'detected_language': 'mixed', 'target_language': 'yo', 'engine': 'gpt-4o-mini', 'quality': 'high', 'code_switched': True})}\n\n"
        await _save_translation(db, user, text, full_text, "mixed", "yo", "gpt-4o-mini")

    except Exception as e:
        logger.warning("Code-switch streaming failed: %s", e)
        yield f"data: {json.dumps({'error': 'Code-switch translation failed. Please try again.'})}\n\n"
