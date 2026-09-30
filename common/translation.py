"""
Shared GPT-powered English <-> Yoruba translation module.

Used by both the Streamlit app and the FastAPI backend so the local
(legacy, low-quality) T5 translation model is replaced by OpenAI's
gpt-4o-mini whenever an API key is configured.
"""

import os
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Model used for translation
GPT_MODEL = "gpt-4o-mini"


def load_api_key() -> str:
    """Load OPENAI_API_KEY from the environment or local .env files."""
    for env_path in (
        os.path.join(ROOT, ".env"),
        os.path.join(ROOT, "backend", ".env"),
    ):
        if os.path.exists(env_path):
            load_dotenv(env_path)
    return os.getenv("OPENAI_API_KEY", "").strip()


GPT_SYSTEM_PROMPT = """You are an expert Yoruba-English translator (Èdè Yorùbá), fluent in both languages and their cultures.

Rules:
1. Determine the source language. English is written in plain ASCII. Yoruba may or may not include tone marks (ẹ, ọ, ṣ, á, à, é, è, í, ì, ó, ò, ú, ù).
2. If the input is English, translate it to Yoruba. If it is Yoruba, translate it to English.
3. Yoruba output MUST always use proper tone marks (ẹ, ọ, ṣ, á, à, é, è, í, ì, ó, ò, ú, ù) and correct spelling (e.g. 'àwọn', 'fẹ́', 'ọ̀rọ̀').
4. NEVER transliterate English words into Yoruba phonetics. WRONG: 'tẹ́st' for 'test', 'ojẹ́' for 'of', 'búfẹ́' for 'wants', 'àlílò' for 'use'. Instead use a REAL Yoruba word or a natural description. WRONG: 'ọ̀hún ẹ̀nọ́ kalẹ̀' for 'captures human voice'. Use real Yoruba: e.g. 'tó gba ohùn ènìyàn'.
5. Produce natural, idiomatic, fluent Yoruba — the way a native speaker talks. Re-express the idea in natural Yoruba sentence structure even if the word order changes. Never settle for a word-by-word, stilted translation.
6. For technical or abstract words that lack a written loanword, prefer an established Yoruba term or a natural descriptive phrase, e.g. 'transcription' -> 'àkọsílẹ̀ ọ̀rọ̀', 'translate' -> 'tumọ̀', 'test' -> 'ìgbìyànjú' or 'àgbéyẹ̀wò' when speaking of trials.
7. Common loanwords that Nigerians actually say in everyday Yoruba can stay in English: phone, computer, bread, butter, car, bus, money, job, office, meeting, problem, place, time, day, night, thing, pain, hospital, clinic, video, camera, TV, radio, laptop. But prefer the Yoruba word when it is the common everyday term, e.g. 'train' -> 'ọkọ̀ ojú irin', 'street' -> 'òpópónà' or 'ọ̀nà', 'government' -> 'ìjọba'.
8. PRESERVE proper nouns EXACTLY in their original English spelling: personal names, brand names, company/clinic names, place names (Lagos, Plateau, London, Badagry, Ghana, BioClinix, Google). NEVER add tone marks or subdot letters to these.
9. When Yoruba input is missing tone marks or is slightly garbled, interpret the intended meaning, normalize it correctly, then translate it faithfully.
10. For greetings use the standard Yoruba forms (ẹ káàárọ̀, ẹ káàsán, ẹ káalẹ́, ẹ kú iṣẹ́, etc.). For idioms and proverbs, give the culturally equivalent expression.
11. Keep numbers as digits.
12. Return ONLY the translated text. No explanations, no quotes, no prefixes, no extra formatting.

EXAMPLES OF GOOD ENGLISH -> YORUBA:
- "The government lighted the streets." -> "Ìjọba tàn iná sí àwọn òpópónà."
- "I want to buy bread and a phone." -> "Mo fẹ́ ra búrẹ́dì àti fóònù."
- "Test of a person who wants to use a tool that captures human voice." -> "Àgbéyẹ̀wò ẹnìkan tó fẹ́ lo ohun èlò tó ń gba ohùn ènìyàn." 
- "I was amazed by the wedding decorations." -> "Àwọn ohun ọ̀ṣọ́ ìgbéyàwó yẹn yà mí lẹ́nu." """


def _detect_source(text: str, direction: str, detected: str | None) -> tuple[str, str]:
    """Return (detected_source, target_lang_code)."""
    if direction == "en2yo":
        return "en", "yo"
    if direction == "yo2en":
        return "yo", "en"

    if detected is None:
        from common.language_detect import detect_language
        detected = detect_language(text)

    source = "yo" if detected == "yo" else "en"
    target = "en" if source == "yo" else "yo"
    return source, target


def _with_few_shot(text: str, source: str, user_msg: str) -> str:
    """Retrieve similar parallel pairs and prepend them as few-shot examples."""
    try:
        from common.translation_rag import get_few_shot_examples
    except Exception:
        return user_msg

    direction_key = "en2yo" if source == "en" else ("yo2en" if source == "yo" else None)
    if direction_key is None:
        return user_msg

    try:
        examples = get_few_shot_examples(text, direction_key, k=3)
    except Exception as e:
        logger.warning("Few-shot retrieval failed: %s", e)
        return user_msg

    if not examples:
        return user_msg

    src_name = "English" if direction_key == "en2yo" else "Yoruba"
    tgt_name = "Yoruba" if direction_key == "en2yo" else "English"
    lines = [f"Here are reference translations of similar {src_name} sentences to guide you:"]
    for src, tgt in examples:
        lines.append(f"--- {src_name}: {src}")
        lines.append(f"--- {tgt_name}: {tgt}")
    lines.append("--- End of references. Now translate the text below, matching the reference style:")
    return "\n".join(lines) + "\n\n" + user_msg


def translate_with_gpt(
    text: str,
    direction: str = "auto",
    detected: str | None = None,
    api_key: str | None = None,
) -> dict | None:
    """Translate text using OpenAI gpt-4o-mini. Returns None on any failure."""
    from openai import OpenAI

    key = api_key if api_key is not None else load_api_key()
    if not key:
        return None

    source, target = _detect_source(text, direction, detected)
    source_name = "Yoruba" if source == "yo" else "English"
    target_name = "English" if source == "yo" else "Yoruba"

    user_msg = f"Translate the following {source_name} text to {target_name}:\n\n{text.strip()}"
    user_msg = _with_few_shot(text, source, user_msg)

    try:
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": GPT_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        translated = response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("GPT translation failed: %s", e)
        return None

    if not translated:
        return None

    return {
        "translated_text": translated,
        "detected_language": source,
        "target_language": target,
        "engine": GPT_MODEL,
    }
