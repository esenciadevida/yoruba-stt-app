"""
Shared NLLB-200 (distilled-600M) English <-> Yoruba translation module.

NLLB (Meta's No Language Left Behind) is a 200-language translation model.
The distilled 600M variant runs on CPU in ~5-10s per sentence and produces
excellent idiomatic Yoruba with full tone marks (better than GPT for
English -> Yoruba). Yoruba -> English quality is weaker, so callers should
prefer GPT for that direction and use NLLB as an offline fallback.
"""

import os
import re
import logging
import threading

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Checkpoints stored locally so the app works fully offline once downloaded.
MODEL_PATH = os.path.join(ROOT, "models", "nllb-200-distilled-600M")

# NLLB FloRes-200 language codes.
LANG_CODES = {
    "en": "eng_Latn",
    "yo": "yor_Latn",
}

_LOAD_LOCK = threading.Lock()
_CACHE = {"tokenizer": None, "model": None}


def is_available() -> bool:
    """True when the local NLLB checkpoint exists on disk."""
    return os.path.isdir(MODEL_PATH) and os.path.exists(
        os.path.join(MODEL_PATH, "config.json")
    )


def load_nllb() -> tuple | None:
    """Load (tokenizer, model) once, cached for the process lifetime."""
    if _CACHE["model"] is not None:
        return _CACHE["tokenizer"], _CACHE["model"]
    if not is_available():
        logger.warning("NLLB model not found at %s", MODEL_PATH)
        return None

    with _LOAD_LOCK:
        if _CACHE["model"] is not None:
            return _CACHE["tokenizer"], _CACHE["model"]
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            logger.info("Loading NLLB-200-distilled-600M from %s", MODEL_PATH)
            tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
            # The checkpoint ships a max_length of 200 in its generation
            # config, which clashes with our max_new_tokens and triggers a
            # noisy warning on every call. Clear it so only max_new_tokens
            # governs output length.
            model.generation_config.max_length = None
            _CACHE["tokenizer"] = tokenizer
            _CACHE["model"] = model
            return tokenizer, model
        except Exception as e:
            logger.error("Failed to load NLLB model: %s", e)
            return None


def _looks_like_echo(source: str, output: str) -> bool:
    """Heuristic: NLLB yo->en sometimes echoes the input instead of translating."""
    s = re.sub(r"[^\w\s]", "", source).lower().split()
    o = re.sub(r"[^\w\s]", "", output).lower().split()
    if not s:
        return False
    overlap = sum(1 for w in o if w in s)
    return len(o) > 0 and overlap / len(s) >= 0.5


def translate_with_nllb(
    text: str,
    direction: str = "auto",
    detected: str | None = None,
) -> dict | None:
    """Translate text with NLLB-200. Returns the same dict shape as GPT."""
    if not text or not text.strip():
        return None

    if direction == "en2yo":
        source, target = "en", "yo"
    elif direction == "yo2en":
        source, target = "yo", "en"
    else:
        from common.language_detect import detect_language

        detected = detect_language(text) if detected is None else detected
        source = "yo" if detected == "yo" else "en"
        target = "en" if source == "yo" else "yo"

    loaded = load_nllb()
    if loaded is None:
        return None
    tokenizer, model = loaded

    try:
        import torch

        inputs = tokenizer(
            text.strip(),
            return_tensors="pt",
            truncation=True,
            max_length=256,
        ).input_ids
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_new_tokens=200,
                num_beams=4,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(
                    LANG_CODES[target]
                ),
            )
        translated = tokenizer.batch_decode(
            outputs, skip_special_tokens=True
        )[0].strip()
    except Exception as e:
        logger.error("NLLB translation failed: %s", e)
        return None

    if not translated:
        return None

    if source == "yo" and _looks_like_echo(text, translated):
        logger.warning("NLLB yo->en echoed input; treating as failure")
        return None

    return {
        "translated_text": translated,
        "detected_language": source,
        "target_language": target,
        "engine": "nllb-200-distilled-600m",
    }
