"""
Offline MarianMT (Helsinki-NLP/opus-mt-yo-en) Yoruba -> English translation.

Used as a fast offline fallback when GPT is unavailable for yo->en.
NLLB is stronger for en->yo, but this model is faster for yo->en.
"""

import os
import logging
import threading

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, "models", "opus-mt-yo-en")

_LOAD_LOCK = threading.Lock()
_CACHE = {"tokenizer": None, "model": None}


def is_available() -> bool:
    return os.path.isdir(MODEL_PATH) and os.path.exists(
        os.path.join(MODEL_PATH, "config.json")
    )


def _load():
    if _CACHE["model"] is not None:
        return _CACHE["tokenizer"], _CACHE["model"]
    if not is_available():
        return None

    with _LOAD_LOCK:
        if _CACHE["model"] is not None:
            return _CACHE["tokenizer"], _CACHE["model"]
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            logger.info("Loading opus-mt-yo-en from %s", MODEL_PATH)
            tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
            _CACHE["tokenizer"] = tokenizer
            _CACHE["model"] = model
            return tokenizer, model
        except Exception as e:
            logger.error("Failed to load opus-mt-yo-en: %s", e)
            return None


def translate_yo_en(text: str) -> dict | None:
    """Translate Yoruba text to English using the local MarianMT model."""
    if not text or not text.strip():
        return None

    loaded = _load()
    if loaded is None:
        return None
    tokenizer, model = loaded

    try:
        import torch
        inputs = tokenizer(text.strip(), return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            output = model.generate(**inputs, max_new_tokens=512, num_beams=4)
        translated = tokenizer.decode(output[0], skip_special_tokens=True).strip()

        if not translated:
            return None

        return {
            "translated_text": translated,
            "detected_language": "yo",
            "target_language": "en",
            "engine": "opus-mt-yo-en",
        }
    except Exception as e:
        logger.error("opus-mt-yo-en translation failed: %s", e)
        return None
