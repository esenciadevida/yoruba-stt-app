"""
Shared OpenAI-powered Yoruba speech-to-text module.

Used by both the Streamlit app and the FastAPI backend so the local
(limited) W2V-BERT model is replaced by OpenAI's gpt-4o-transcribe
whenever an API key is configured. Falls back to whisper-1 and then to
the caller's local model.

gpt-4o-transcribe produces properly tone-marked Yoruba directly, so the
rule-based tone restorer is only needed for local-model output.
"""

import os
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Preferred transcription model, then fallback.
TRANSCRIPTION_MODELS = ["gpt-4o-transcribe", "whisper-1"]

# Concise prompt for gpt-4o-transcribe — the prompt param is a short hint,
# not full instructions. Keep it short so the model does not hallucinate or
# echo the prompt back instead of the speech.
YORUBA_PROMPT = (
    "Yoruba speech transcription. Use subdots ẹ ọ ṣ and all tone marks "
    "(á à é è í ì ó ò ú ù). Keep English words and proper nouns (names, places, "
    "brands) in English spelling."
)

# For automatic (auto) mode we deliberately send NO prompt: gpt-4o-transcribe
# auto-detects and natively produces tone-marked Yoruba or clean English; long
# instructional prompts make the model echo the prompt instead of the speech.

# Full instructions (used only if we need to pass context to a chat model)
YORUBA_INSTRUCTIONS = (
    "Transcribe this Yoruba speech into written Yoruba text with correct orthography. "
    "Critical rules:\n"
    "1. Use open-mid vowels ẹ and ọ (with subdot) — NOT plain e/o — for the vast majority "
    "of Yoruba words (e.g. ọmọ, ẹyin, ilẹ, ojú, ọ̀run, ẹ̀dá, ṣe).\n"
    "2. Use ṣ (s with underdot) — NOT plain s — for the Yoruba 'sh' sound "
    "(e.g. ṣe, ṣo, ẹṣin, àṣẹ, iṣẹ́).\n"
    "3. Mark all tone marks correctly: á à é è í ì ó ò ú ù on vowels.\n"
    "4. Examples of correct Yoruba: 'Báwo ni ọ̀ọ̄? Mo wà dáadáa. Ẹ kú iṣẹ́. "
    "Kí ni ọ̀rọ̀ rẹ? Mo fẹ́ lọ sí ọjà. Ọmọ náà jẹ́ ìrẹ̀kẹ̀jẹ́.'\n"
    "5. Write numbers as digits where spoken as numbers.\n"
    "Output ONLY the Yoruba transcription text, no commentary or translation."
)


def load_api_key() -> str:
    """Load OPENAI_API_KEY from the environment or local .env files."""
    for env_path in (
        os.path.join(ROOT, ".env"),
        os.path.join(ROOT, "backend", ".env"),
    ):
        if os.path.exists(env_path):
            load_dotenv(env_path)
    return os.getenv("OPENAI_API_KEY", "").strip()


def is_available() -> bool:
    return bool(load_api_key())


def transcribe_with_openai(
    audio_bytes: bytes,
    filename: str = "recording.wav",
    language: str = "yo",
) -> dict | None:
    """Transcribe audio bytes via OpenAI. Returns None when no key is set.

    Tries gpt-4o-transcribe (tone-marked Yoruba) then whisper-1. Raises
    RuntimeError if the API is configured but every attempt fails.
    """
    key = load_api_key()
    if not key:
        return None

    from openai import OpenAI

    client = OpenAI(api_key=key)
    upload = (filename or "recording.wav", audio_bytes)

    errors = []
    for model in TRANSCRIPTION_MODELS:
        try:
            kwargs = {
                "model": model,
                "file": upload,
                "response_format": "verbose_json" if model == "whisper-1" else "json",
            }
            if model == "gpt-4o-transcribe":
                kwargs["prompt"] = YORUBA_PROMPT
            elif language in {"yo", "yor", "yoruba"}:
                # For whisper-1, pass language hint so it knows to expect Yoruba
                kwargs["language"] = "yo"
            else:
                kwargs["language"] = language

            response = client.audio.transcriptions.create(**kwargs)
            text = (response.text or "").strip()
            if not text:
                continue
            return {"text": text, "engine": model}
        except Exception as e:
            errors.append(f"{model}: {e}")
            logger.warning("OpenAI transcription with %s failed: %s", model, e)

    raise RuntimeError(
        "OpenAI transcription failed: " + ("; ".join(errors) if errors else "unknown error")
    )
