import sys
import os
import re
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from common.translation import translate_with_gpt, GPT_SYSTEM_PROMPT
from common.nllb import translate_with_nllb
from common.opus_mt import translate_yo_en
from common.language_detect import detect_language
from common.nllb_quality import assess_en_to_yo
from common.tone_restore import restore_tones
from common.translation_cache import translation_cache

logger = logging.getLogger(__name__)

# Maximum characters before chunking is triggered
MAX_CHUNK_CHARS = 400
# Sentence boundary regex for splitting long texts
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?;])\s+')

# en->yo: when the English source contains technical / abstract terms, NLLB
# tends to "Yorubize" the English words into pseudo-Yoruba (e.g. 'tẹ́st' for
# 'test', 'òf' for 'of'). Route those to GPT+RAG first for real, natural
# Yoruba and keep NLLB for short, simple, everyday sentences.
_NLLB_UNSAFE_TERMS = [
    "transcrib", "translat", "test", "voice", "audio", "speech",
    "tool", "machine", "device", "app", "software", "application",
    "record", "capture", "convert", "human", "person", "his voice",
    "her voice", "surface", "recogn",
]

# en->yo: raised only for longer sources where GPT context is affordable and
# NLLB quality degrades the most.
_NLLB_MAX_SIMPLE_CHARS = 80


def _nllb_safe_for_en2yo(text: str) -> bool:
    """True when NLLB is a good first-choice for this English text.

    NLLB handles short, simple, everyday sentences well (greetings, common
    statements). Longer or technical text goes to GPT+RAG first.
    """
    t = text.strip().lower()
    if not t:
        return False
    if len(t) > _NLLB_MAX_SIMPLE_CHARS:
        return False
    low = t
    if any(term in low for term in _NLLB_UNSAFE_TERMS):
        return False
    return True


def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into sentence-level chunks for translation.

    ASR output often has NO punctuation (Yoruba STT usually emits no periods),
    so sentence-splitting alone can leave one giant un-chunkable blob. To keep
    every chunk a reasonable size (avoiding GPT output truncation), we also
    break long runs at word boundaries.
    """
    if len(text) <= max_chars:
        return [text]

    _WORD = re.compile(r'\S+')
    chunks = []
    # First, group by real sentence boundaries (clauses can also be split on commas).
    _CLAUSE = re.compile(r'(?<=[.!?;,]).\s*')
    sentences = _CLAUSE.split(text)
    current = ""

    for sent in sentences:
        # A single sentence longer than max_chars: hard-split it at word
        # boundaries so no chunk is ever oversized.
        if len(sent) > max_chars:
            words = _WORD.findall(sent)
            buf = ""
            for w in words:
                if buf and len(buf) + 1 + len(w) > max_chars:
                    chunks.append(buf.strip())
                    buf = w
                else:
                    buf = (buf + " " + w).strip() if buf else w
            current = buf  # leftover words join the next sentence chunk
            continue

        if len(current) + len(sent) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = sent
        else:
            current = (current + " " + sent).strip() if current else sent

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text]


def translate(text: str, direction: str = "auto") -> dict | None:
    """Translate Yoruba <-> English using the best available engine.

    Strategy:
      * English -> Yoruba: NLLB-200 first (offline, idiomatic); escalates
        to GPT+RAG if quality is low. GPT as plain fallback.
        Tone restoration applied as safety net for NLLB output.
      * Yoruba -> English: GPT-4o-mini first (reliable); opus-mt offline
        fallback; NLLB as last resort.
      * Long texts are chunked into sentence-level segments.
      * Results are cached for 1 hour to avoid re-translating.
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    if direction == "en2yo":
        detected = "en"
    elif direction == "yo2en":
        detected = "yo"
    else:
        detected = detect_language(text)
        direction = "en2yo" if detected == "en" else "yo2en"

    # Check cache first
    cached = translation_cache.get(text, direction)
    if cached is not None:
        logger.info("Translation cache hit for %d chars", len(text))
        return cached

    # --- Chunk long texts ---
    chunks = _chunk_text(text)
    if len(chunks) > 1:
        results = []
        for chunk in chunks:
            result = _translate_single(chunk, direction, detected)
            if result:
                results.append(result["translated_text"])
            else:
                results.append(chunk)  # fallback: keep original
        combined = " ".join(results)
        final = {
            "translated_text": combined,
            "detected_language": detected,
            "target_language": "en" if detected == "yo" else "yo",
            "engine": "chunked",
        }
        translation_cache.put(text, direction, final)
        return final

    result = _translate_single(text, direction, detected)
    if result is not None:
        translation_cache.put(text, direction, result)
    return result


def _translate_single(text: str, direction: str, detected: str) -> dict | None:
    """Translate a single chunk (no chunking)."""
    if direction == "en2yo":
        # When the source contains proper nouns / brand / place names, prefer
        # GPT+RAG: it preserves them verbatim in English. NLLB tends to
        # transliterate them into garbled tone-marked "Yoruba".
        from common.proper_nouns import contains_proper_nouns
        proper_noun_text = contains_proper_nouns(text)
        nllb_first = _nllb_safe_for_en2yo(text) and not proper_noun_text

        # Try the cheap/fast offline path first when the source is simple.
        nllb_good = None
        if nllb_first:
            nllb_good, nllb_result = _translate_en2yo_nllb(text, detected)
            if nllb_good:
                return nllb_result

        # GPT+RAG for complex/technical/proper-noun text, or when NLLB output
        # was unusable. 
        if not nllb_first:
            gpt_result = translate_with_gpt(text, direction=direction, detected=detected)
            if gpt_result is not None:
                gpt_result["translated_text"] = restore_tones(gpt_result["translated_text"])
                return gpt_result
            # GPT unavailable -> fall back to any NLLB output we have.
            if nllb_result is not None:
                nllb_result["translated_text"] = restore_tones(nllb_result["translated_text"])
                return nllb_result
            return None

        # NLLB was tried but scored low -> escalate to GPT+RAG.
        gpt_result = translate_with_gpt(text, direction=direction, detected=detected)
        if gpt_result is not None:
            gpt_result["translated_text"] = restore_tones(gpt_result["translated_text"])
            return gpt_result
        logger.warning("GPT unavailable; returning best-effort NLLB output for en->yo")
        if nllb_result is not None:
            nllb_result["translated_text"] = restore_tones(nllb_result["translated_text"])
            return nllb_result
        return None

    result = translate_with_gpt(text, direction=direction, detected=detected)
    if result is not None:
        return result

    logger.warning("GPT unavailable for yo->en, trying opus-mt offline fallback")
    opus_result = translate_yo_en(text)
    if opus_result is not None:
        return opus_result

    logger.warning("opus-mt unavailable, falling back to NLLB for yo->en")
    return translate_with_nllb(text, direction=direction, detected=detected)


def _translate_en2yo_nllb(text: str, detected: str) -> tuple[bool, dict | None]:
    """Run the NLLB en->yo path with the quality gate.

    Returns (good, result). When NLLB responds, result is the (tone-restored)
    translation and ``good`` says whether the quality gate accepted it. When
    ``good`` is False, callers may escalate to GPT+RAG but keep ``result`` as a
    best-effort fallback. ``good``/result are None when NLLB is unavailable.
    """
    nllb_result = translate_with_nllb(text, direction="en2yo", detected=detected)
    if nllb_result is None:
        return None, None
    if nllb_result.get("translated_text"):
        nllb_result["translated_text"] = restore_tones(nllb_result["translated_text"])
    good, reason = assess_en_to_yo(text, nllb_result["translated_text"])
    if not good:
        logger.info("NLLB en->yo scored low quality (%s)", reason)
    return good, nllb_result
