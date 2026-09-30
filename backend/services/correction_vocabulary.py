"""
Build a lightweight per-user custom vocabulary from their past corrections.

Fast speakers frequently mishear the same words repeatedly (esp. proper nouns
and low-frequency Yoruba terms). We mine the user's correction history for
word-level (wrong -> right) mappings and turn them into a glossary hint that is
injected into the transcription prompt, so the ASR model is nudged towards the
words the user actually uses.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.correction import Correction

logger = logging.getLogger(__name__)

MAX_GLOSSARY_TERMS = 25
MIN_RELEVANCE = 2  # a term must be corrected this many times to be worth keeping


def _normalize_word(w: str) -> str:
    # Strip punctuation, lower for matching.
    return "".join(c for c in (w or "").lower() if c.isalnum())


def _word_mapping_to_hint(pairs: list) -> str:
    """Turn (wrong, right) pairs into a compact glossary line for the prompt."""
    lines = []
    for wrong, right in pairs:
        wrong_n = _normalize_word(wrong)
        right_n = _normalize_word(right)
        if not wrong_n or not right_n or wrong_n == right_n:
            continue
        lines.append(f"{wrong.strip()} should be transcribed as {right.strip()}")
    return "; ".join(lines)


async def build_glossary_hint(user_id: int, db: AsyncSession) -> str:
    """Return a prompt hint string derived from the user's corrections.

    Returns an empty string when there is nothing worth suggesting.
    """
    try:
        result = await db.execute(
            select(Correction).where(Correction.user_id == user_id)
        )
        corrections = result.scalars().all()
    except Exception as e:
        logger.warning("Failed to load corrections for vocabulary: %s", e)
        return ""

    if not corrections:
        return ""

    # Count word replacements (wrong_word_in_asr -> corrected_word_in_raw).
    # The raw ASR text is stored in original_text; the user's fix in corrected_text.
    from collections import Counter

    wrong_to_right = {}  # wrong(normalized) -> right(normalized)
    wrong_count = Counter()

    for c in corrections:
        orig = (c.original_text or "").split()
        corr = (c.corrected_text or "").split()
        if len(orig) != len(corr) or not orig:
            # Align by word index when lengths match; otherwise skip.
            continue
        for w, r in zip(orig, corr):
            nw = _normalize_word(w)
            nr = _normalize_word(r)
            if not nw or not nr or nw == nr:
                continue
            wrong_count[nw] += 1
            wrong_to_right[nw] = r  # keep the latest corrected spelling

    # Only keep terms corrected enough to be reliable.
    kept = []
    for nw, cnt in wrong_count.items():
        if cnt >= MIN_RELEVANCE and nw in wrong_to_right:
            kept.append((nw, wrong_to_right[nw]))

    # Cap the glossary size.
    kept = kept[:MAX_GLOSSARY_TERMS]
    if not kept:
        return ""

    pairs = [(w, r) for w, r in kept]
    return _word_mapping_to_hint(pairs)
