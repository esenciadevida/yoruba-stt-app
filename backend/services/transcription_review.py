"""
Second-pass AI verification of ASR output (Yoruba).

The audio model (gpt-4o-transcribe / whisper / local) can get the words mostly
right but leave tone marks off, use plain e/o/s instead of ẹ/ọ/ṣ, or emit ASR
artifacts (stutter, merged/split words, hallucinated filler). This module runs
the raw text through a fast language model to return clean, properly-spelled,
tone-marked Yoruba -- WITHOUT changing the meaning or wording.

The result is used as `final_text`. The original raw ASR output is preserved so
the UI can show a diff and the user can still edit/correct.
"""

import logging
import re

from openai import OpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

REVIEW_MODEL = "gpt-4o-mini"

REVIEW_SYSTEM = (
    "You are an expert Yoruba orthography corrector. You receive a raw speech-to-text "
    "transcription in Yoruba that may contain errors. Your ONLY task is to fix the "
    "spelling and orthography of the Yoruba text. Strict rules:\n"
    "1. Fix subdot letters: use ẹ ọ ṣ (with underdot) instead of plain e/o/s where "
    "the correct Yoruba word requires them (e.g. ọmọ, ẹyin, iṣẹ́, àṣẹ, ẹ̀dá).\n"
    "2. Correct tone marks: á à é è í ì ó ò ú ù on the correct vowels. Every Yoruba "
    "word that carries a tone must have it added. For example: 'awon' -> 'àwọn', "
    "'nigba' -> 'nìgbà', 'modede' -> 'mò dédé', 'wolonjo' -> 'wọ́lọ́ǹjọ́'.\n"
    "3. Fix spacing: split words wrongly merged together and join words wrongly split, "
    "only where it is clearly correct Yoruba.\n"
    "4. Remove ASR artifacts: repeated/stuttered words that are clearly accidental "
    "duplicates, and nonsense filler tokens that are not real Yoruba words.\n"
    "5. Do NOT translate, do NOT summarize, do NOT rephrase, do NOT add commentary. "
    "Keep every real word the speaker said, in the same order.\n"
    "6. If you are not certain a correction is correct, leave the word unchanged.\n"
    "7. Do NOT add tone marks or subdot letters to English words, loanwords, or proper "
    "nouns / place names (Badagry, Lagos, Google, clinic, bread, streetlights, etc.). "
    "Keep them in plain English spelling.\n"
    "8. Output ONLY the corrected Yoruba text. No explanation, no quotes, no prefix."
)


def _looks_yoruba(text: str) -> bool:
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return False
    # A usable heuristic: most Yoruba words contain subdot letters / tone marks,
    # or contain the digit-8 n-subscript markers; but plain Yoruba also exists.
    # We accept any non-empty mostly-alphabetic text for review to be safe.
    return True


def review_transcription(raw_text: str, language: str = "yo"):
    """Return (corrected_text, was_reviewed).

    `was_reviewed` is True when the language model produced a distinct corrected
    version (so callers can skip the rule-based tone restorer). On any failure or
    no-op it returns the original text with was_reviewed False.
    """
    text = (raw_text or "").strip()
    if not text:
        return "", False
    if language and language.strip().lower() not in {"yo", "yor", "yoruba"}:
        return text, False

    if not OPENAI_API_KEY:
        return text, False

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=REVIEW_MODEL,
            temperature=0.0,
            messages=[
                {"role": "system", "content": REVIEW_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        "Correct the orthography and tone marks of this Yoruba "
                        "transcription. Output only the corrected Yoruba text:\n\n"
                        f"{text}"
                    ),
                },
            ],
        )
        corrected = (response.choices[0].message.content or "").strip()
        corrected = re.sub(r'^["\'`\s]+|["\'`\s]+$', "", corrected)
        if not corrected or corrected == text:
            return text, False
        return corrected, True
    except Exception as e:
        logger.warning("Transcription review failed, keeping original: %s", e)
        return text, False
