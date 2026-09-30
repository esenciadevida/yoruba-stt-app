import sys
import os
import logging

# Add parent directory to path for shared module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from common.translation import translate_with_gpt, load_api_key, GPT_MODEL
from common.nllb import translate_with_nllb, is_available as nllb_available
from common.language_detect import detect_language
from common.nllb_quality import assess_en_to_yo

logger = logging.getLogger(__name__)


@st.cache_resource
def load_translation_model():
    """Return a translation backend handle: (tokenizer, model, device).

    No heavy local weights are loaded eagerly. ``device`` is a string tag
    used to select the translation engine:
      * "nllb"   -> NLLB-200-distilled-600M is available offline
      * "gpt"    -> OpenAI GPT translation (API key configured)
      * "offline"-> no local model and no API key
    """
    if nllb_available():
        return None, None, "nllb"
    if load_api_key():
        return None, None, "gpt"
    return None, None, "offline"


def _build_result(best, detected, direction, config=GPT_MODEL):
    return {
        "best_translation": best,
        "variants": [
            {
                "text": best,
                "quality_score": 1.0,
                "config": config,
            }
        ],
        "detected_language": detected,
        "direction": direction,
        "chunks_used": 1,
    }


def translate_text(
    text,
    direction="auto",
    num_variants=1,
    tokenizer=None,
    model=None,
    device="auto",
):
    """Translate Yoruba <-> English with the best available engine.

    Strategy (shared with the backend):
      * English -> Yoruba: NLLB-200 first (excellent, offline); its output is
        scored and escalates to GPT+RAG when it looks non-idiomatic. GPT is
        the plain fallback when NLLB is unavailable.
      * Yoruba -> English: GPT first (reliable), NLLB offline fallback.
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    if direction == "auto":
        detected = detect_language(text)
        direction = "en2yo" if detected == "en" else "yo2en"
    elif direction == "en2yo":
        detected = "en"
    else:
        detected = "yo"

    if direction == "en2yo":
        result = translate_with_nllb(text, direction=direction, detected=detected)
        if result is not None:
            good, reason = assess_en_to_yo(text, result["translated_text"])
            if good:
                pass
            else:
                logger.info("NLLB en->yo scored low quality (%s); trying GPT+RAG", reason)
                fixed = translate_with_gpt(text, direction=direction, detected=detected)
                if fixed is not None:
                    result = fixed
        elif load_api_key():
            result = translate_with_gpt(text, direction=direction, detected=detected)
    else:
        result = translate_with_gpt(text, direction=direction, detected=detected)
        if result is None:
            result = translate_with_nllb(text, direction=direction, detected=detected)

    if result is None:
        return None

    return _build_result(
        best=result["translated_text"],
        detected=result["detected_language"],
        direction=direction,
        config=result["engine"],
    )
