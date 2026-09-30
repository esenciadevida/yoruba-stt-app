import os
import tempfile
import logging
import time
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

_GTTS_SUPPORTED = {
    "af", "am", "ar", "bg", "bn", "bs", "ca", "cs", "cy", "da", "de", "el",
    "en", "eo", "es", "et", "eu", "fi", "fr", "fr-ca", "fr-fr", "gl", "gu",
    "he", "hi", "hr", "hu", "hy", "id", "is", "it", "ja", "jv", "ka", "kk",
    "km", "kn", "ko", "ku", "ky", "la", "lo", "lt", "lv", "mg", "mk", "ml",
    "mn", "mr", "ms", "mt", "my", "ne", "nl", "no", "pa", "pl", "pt", "pt-br",
    "ro", "ru", "si", "sk", "sl", "sq", "sr", "su", "sv", "sw", "ta", "te",
    "th", "tl", "tr", "uk", "ur", "uz", "vi", "zh-cn", "zh-tw", "zu",
}

_EDGE_TTS_MAP = {
    "en": "en-US-JennyNeural",
    "yo": "en-US-GuyNeural",
}


def text_to_speech(text: str, lang: str = "yo") -> dict:
    if not text or not text.strip():
        return None
    text = text.strip()

    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        result = _openai_synthesize(text, lang)
        if result:
            return result
        logger.warning("OpenAI TTS failed, trying fallback engines")

    if lang in _EDGE_TTS_MAP:
        result = _edge_tts_synthesize(text, lang)
        if result:
            return result

    if lang in _GTTS_SUPPORTED:
        result = _gtts_synthesize(text, lang)
        if result:
            return result

    logger.error("No TTS engine available for language '%s'", lang)
    return None


def _openai_synthesize(text: str, lang: str = "yo") -> dict:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        voice = "alloy" if lang != "en" else "nova"
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )

        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        with open(tmp.name, "wb") as f:
            f.write(response.content)

        word_count = len(text.split())
        duration_est = word_count / 2.5
        return {
            "audio_path": tmp.name,
            "engine": "openai-tts",
            "duration_estimate": round(duration_est, 2),
            "format": "mp3",
        }
    except Exception as e:
        logger.error("OpenAI TTS failed: %s: %s", type(e).__name__, e, exc_info=True)
        return None


def _edge_tts_synthesize(text: str, lang: str = "yo") -> dict:
    try:
        import edge_tts
        import asyncio

        voice = _EDGE_TTS_MAP.get(lang, "en-US-JennyNeural")
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()

        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(tmp.name)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(lambda: asyncio.run(_generate())).result()
            else:
                loop.run_until_complete(_generate())
        except RuntimeError:
            asyncio.run(_generate())

        if os.path.getsize(tmp.name) == 0:
            os.remove(tmp.name)
            return None

        word_count = len(text.split())
        duration_est = word_count / 2.5
        return {
            "audio_path": tmp.name,
            "engine": "edge-tts",
            "duration_estimate": round(duration_est, 2),
            "format": "mp3",
        }
    except Exception as e:
        logger.error("Edge TTS synthesis failed: %s", e)
        return None


def _gtts_synthesize(text: str, lang: str = "yo") -> dict:
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        tts.save(tmp.name)
        word_count = len(text.split())
        duration_est = word_count / 2.5
        return {
            "audio_path": tmp.name,
            "engine": "gtts",
            "duration_estimate": round(duration_est, 2),
            "format": "mp3",
        }
    except Exception as e:
        logger.error("gTTS synthesis failed: %s", e)
        return None


def cleanup_file(path: str):
    try:
        time.sleep(30)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
