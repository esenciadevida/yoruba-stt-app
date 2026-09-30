"""
Code-switching detection and resolution for Yoruba-English mixed text.

When a speaker mixes English words into Yoruba speech (extremely common in
Nigeria), this module detects the mixed language and uses GPT to translate
the English portions into proper Yoruba, producing a unified Yoruba output.
"""

import os
import re
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Yoruba character sets ──
YORUBA_DIACRITICS = set("\u1eb9\u1ecd\u1e63\u00e1\u00e0\u00e9\u00e8\u00ed\u00ec\u00f3\u00f2\u00fa\u00f9")
YORUBA_SUBDOTS = set("\u1eb9\u1ecd\u1e63")  # ẹ ọ ṣ

# ── Common English words that appear in Nigerian Yoruba speech ──
# These are NOT exhaustive but cover the most frequent code-switch triggers
COMMON_ENGLISH_WORDS = {
    # Pronouns
    "i", "we", "you", "he", "she", "it", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "our", "their", "mine", "yours", "ours",
    # Articles & determiners
    "the", "a", "an", "this", "that", "these", "those", "some", "all",
    "every", "each", "any", "no",
    # Prepositions
    "to", "in", "on", "at", "for", "with", "from", "by", "of", "about",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "under", "over", "up", "down",
    # Common verbs
    "go", "come", "see", "get", "give", "take", "make", "do", "have",
    "be", "is", "am", "are", "was", "were", "been", "being",
    "can", "will", "would", "could", "should", "may", "might",
    "want", "need", "like", "love", "know", "think", "say", "tell",
    "ask", "help", "try", "start", "stop", "buy", "sell", "eat", "drink",
    "sleep", "walk", "run", "talk", "speak", "read", "write", "work",
    "play", "send", "receive", "call", "phone", "open", "close",
    "learn", "teach", "study", "finish", "begin", "keep", "let",
    # Common nouns
    "time", "day", "week", "month", "year", "morning", "afternoon",
    "evening", "night", "today", "tomorrow", "yesterday",
    "money", "car", "house", "school", "work", "food", "water",
    "man", "woman", "child", "children", "people", "person", "friend",
    "family", "mother", "father", "brother", "sister", "son", "daughter",
    "name", "place", "thing", "problem", "question", "answer",
    "good", "bad", "big", "small", "new", "old", "first", "last",
    "much", "many", "more", "most", "little", "few",
    # Adjectives
    "happy", "sad", "fine", "well", "ready", "sure", "sure",
    # Adverbs
    "very", "also", "too", "here", "there", "now", "then",
    "always", "never", "sometimes", "often", "still", "already",
    "just", "only", "really", "quickly", "slowly",
    # Conjunctions
    "and", "but", "or", "because", "so", "if", "when", "while",
    # Question words
    "what", "who", "where", "when", "why", "how", "which",
    # Common Nigerian English
    "please", "sorry", "thank", "thanks", "ok", "okay", "yes", "no",
    "problem", "abeg", "oga", "madam",
    # Numbers
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "hundred", "thousand", "million",
    # Misc
    "thing", "things", "everything", "something", "nothing", "anything",
    "way", "time", "place", "number", "part", "side",
}

# ── Yoruba words (high-confidence, unambiguous) ──
YORUBA_WORDS = {
    "lati", "nitori", "nigbati", "ninu", "tabi", "awon", "aaro", "osan",
    "nkan", "lori", "nipa", "bawo", "kini", "nibo", "bayii", "beenii",
    "pele", "jowo", "olorun", "oluwa", "yoruba", "omo", "ile", "ojo",
    "ori", "enu", "imu", "eti", "oju", "aka", "ese", "ara", "epo",
    "ounje", "amala", "iyan", "gari", "agbado", "oyin", "epa",
    "iya", "baba", "ore", "adura", "ebo", "ife", "ominira", "alafia",
    "igbo", "orisa", "egungun", "sango", "ogun", "ese", "egun",
    "okan", "eji", "eta", "erin", "aarun", "efa", "eje", "ejo", "esa",
    "dun", "giga", "nla", "pupa", "funfun", "tuntun", "daadaa", "pupo",
    "mo", "lo", "ri", "ra", "mu", "je", "fe", "gbo", "so", "sun",
    "ji", "we", "fo", "se", "te", "ka", "tun", "da", "fa", "wo",
    "ni", "ti", "naa", "ko", "wa", "si", "bi", "se", "pe", "ati",
    "ki", "fun", "a", "o", "e", "won", "emii", "emi", "iwọ", "awa",
    "eyin", "eni", "nlo", "nje", "nbo", "ngbo", "nse", "nwa", "nri",
    "jeun", "oja", "lola", "ona", "sugbon", "oba", "bayi", "eko",
    "isu", "ata", "oko", "eti", "enu", "imu", "eku", "orin", "ise",
    "sise", "iwosan", "iranlowo", "olori", "won", "abi", "naa",
    "yen", "tele", "imoju", "isura", "igbi", "igbekele", "onu", "obo",
    "awon", "igbese", "iyaloja", "ireke", "idaduro", "adugbo", "igboro",
    "won", "nwori", "jeun", "gbogbo", "eleti", "badagry", "lagos", "eko",
    # Common Yoruba words without diacritics that appear in code-switched text
    "omo", "ode", "aro", "osan", "ori", "enu", "oju", "aka", "ese",
    "omo", "ojo", "ile", "oro", "awon", "ti", "ni", "si", "lati",
    "nitori", "tabi", "sugbon", "tori", "nigba", "nigbati", "ninu",
    "bayii", "beenii", "bawo", "kini", "nibo", "pele", "jowo",
    "olorun", "oluwa", "ise", "ifa", "oni", "ama", "ise", "ori",
}


def _clean_word(word: str) -> str:
    """Strip punctuation from a word for matching."""
    return re.sub(r"[^\w]", "", word.lower())


def _has_yoruba_diacritics(word: str) -> bool:
    """True when the word contains Yoruba-specific characters."""
    return any(c in YORUBA_DIACRITICS for c in word)


# Plain-ASCII words that exist in the Yoruba lexicon but are ALSO common
# English words ("a", "won", "o"...) or English-language mentions of the
# Yoruba language/people ("Yoruba"). On their own they must NOT count as
# Yoruba evidence, or a pure-English sentence like "I want to buy a phone"
# or "...translate it into Yoruba" would be misclassified as code-switched.
_AMBIGUOUS_ASCII_YORUBA = {
    "a", "o", "e", "won", "yoruba",
}


def _is_english_word(word: str) -> bool:
    """Check if a word is plausibly English.

    Strategy:
    1. Exact match in COMMON_ENGLISH_WORDS → definitely English
    2. Pure ASCII letters (no diacritics), not in YORUBA_WORDS, length >= 3
       → plausibly English (covers "bread", "computer", "gadgets", "island", etc.)
    3. Otherwise → not English
    """
    w = _clean_word(word)
    if not w:
        return False
    if w in COMMON_ENGLISH_WORDS:
        return True
    # Heuristic: pure ASCII alpha word, at least 3 chars, not a known Yoruba word
    if len(w) >= 3 and w.isascii() and w.isalpha() and w not in YORUBA_WORDS:
        return True
    return False


def _is_yoruba_word(word: str) -> bool:
    """Check if a word is plausibly Yoruba."""
    w = _clean_word(word)
    if not w:
        return False
    # Has Yoruba-specific characters -> definitely Yoruba
    if _has_yoruba_diacritics(w):
        return True
    # Plain ASCII "a"/"o"/"e"/"won"/"Yoruba" overlap with English and are
    # NOT reliable evidence on their own.
    if w in _AMBIGUOUS_ASCII_YORUBA:
        return False
    if w in YORUBA_WORDS:
        return True
    return False


def contains_mixed_language(text: str) -> bool:
    """Quick check if text contains both Yoruba and English words.

    Conservative: returns True only when there is *real* evidence of BOTH
    languages, to avoid flagging pure-English sentences that merely mention
    the Yoruba language, or single overlapping letters ("a", "o", "e").
    """
    if not text or not text.strip():
        return False

    words = text.split()
    if len(words) < 2:
        return False

    yoruba_count = 0
    english_count = 0
    yoruba_diacritic = False

    for word in words:
        if _is_yoruba_word(word):
            yoruba_count += 1
            if _has_yoruba_diacritics(word):
                yoruba_diacritic = True
        elif _is_english_word(word):
            english_count += 1

    if yoruba_count < 1 or english_count < 1:
        return False

    # A single bare "Yoruba" mention with all-English words is NOT a mix.
    # Require either a diacritic-bearing Yoruba word, or at least two
    # unambiguous Yoruba lexicon words, plus real English evidence.
    total_tagged = yoruba_count + english_count
    if total_tagged < 3:
        return False
    if yoruba_diacritic:
        return True
    return yoruba_count >= 2


def process_mixed_text(raw_text: str, api_key: str | None = None) -> dict:
    """Translate English portions of mixed Yoruba/English text to Yoruba.

    Uses GPT-4o-mini in a single call to:
    1. Identify which parts are English and which are Yoruba
    2. Translate only the English parts to Yoruba
    3. Preserve the Yoruba parts unchanged
    4. Produce a unified, well-formatted Yoruba output with proper tone marks

    Returns:
        {
            "text": "unified Yoruba text",
            "code_switched": True,
            "source_text": "original mixed text"
        }
    """
    from common.translation import load_api_key, GPT_MODEL

    key = api_key if api_key is not None else load_api_key()
    if not key:
        logger.warning("No OpenAI API key available for code-switching")
        return {
            "text": raw_text,
            "code_switched": False,
            "source_text": raw_text,
        }

    if not contains_mixed_language(raw_text):
        return {
            "text": raw_text,
            "code_switched": False,
            "source_text": raw_text,
        }

    # Check cache for previously resolved code-switch results
    from common.translation_cache import translation_cache
    cached = translation_cache.get(raw_text, "code-switch")
    if cached is not None:
        logger.info("Code-switch cache hit for: %s", raw_text[:40])
        return {
            "text": cached["text"],
            "code_switched": True,
            "source_text": raw_text,
        }

    system_prompt = """You are an expert Yoruba language processor. Your job is to handle code-switched text — text that mixes English and Yoruba — and produce a unified, well-formatted Yoruba output.

RULES:
1. Identify which words/phrases are English and which are Yoruba.
2. Keep Yoruba portions EXACTLY as they are (preserve tone marks and spelling).
3. For English portions, apply these rules IN ORDER:

   a) LOANWORDS — keep as-is: In Nigerian Yoruba, many English words are used
      naturally as loanwords. When the speaker clearly uses an English noun or
      phrase as a natural part of their Yoruba sentence, KEEP IT AS-IS.
      Common loanwords to preserve (do NOT translate these):
      - Objects: "wrist watch", "ring", "chain", "bag", "shoe", "cap", "cloth"
      - Tech: "phone", "laptop", "computer", "TV", "radio", "video", "camera"
      - Food: "bread", "butter", "sugar", "tea", "coffee", "noodles"
      - Vehicles: "car", "truck", "bus", "bike", "motorcycle"
      - Money: "money", "dollar", "pound", "naira"
      - Work: "job", "office", "meeting", "boss", "salary"
      - General: "problem", "thing", "place", "time", "day", "night"

   b) ENGLISH SENTENCES/PHRASES — translate to Yoruba: When the speaker uses
      a full English phrase or sentence (not a single loanword), translate it
      to Yoruba. Examples:
      - "I want to buy" → "mo fẹ́ ra"
      - "she is going to the market" → "ó ń lọ sí ọjà"
      - "the meeting is tomorrow" → "ipade náà ni ọ̀la"
      - "I need help" → "mo ní ìrànwọ́"

   c) PROPER NOUNS: Personal names (Pascal, Samuel), brands (Google, iPhone),
      company or clinic names (BioClinix), places (Lagos, Plateau, Ebonyi) →
      keep them VERBATIM in correct English spelling. NEVER transliterate them
      into Yoruba phonetics and NEVER add tone marks or subdot letters to an
      English proper noun (incorrect: "baóklínitnííbi" or "èlẹ́gọ́stìtibẹlawa";
      correct: "BioClinix", "Lagos State").

4. Make the output flow naturally as a single Yoruba sentence. Adjust word order
   and connectors if needed for natural Yoruba grammar.
5. Use proper Yoruba orthography: subdot letters (ẹ, ọ, ṣ) and all tone marks.
6. Return ONLY the unified Yoruba text. No explanations, no prefixes, no quotes.

EXAMPLES:
Input: "Mo wo wrist watch olowo nla"
Output: "Mo wọ́ wrist watch olówó nla"

Input: "Mo fe ki O n I want to buy some amala and efo riro"
Output: "Mo fẹ́ kí ó ní mo fẹ́ ra àmàlà àti ẹ̀fọ̀ rírọ̀"

Input: "Mo n work for the school ni ibadan"
Output: "Mo ń iṣẹ́ fún ilé-ìwé ní Ìbàdàn"

Input: "She is a very nice woman, o dara pupo"
Output: "Ó jẹ́ obìnrin tó dára jùlọ, ó dára púpọ̀"

Input: "I want to go to Lagos Island to buy bread and computer gadgets"
Output: "Mo fẹ́ lọ sí Ẹ̀kó láti ra bread àti computer gadgets"

Input: "My friend dey work for Google ni Lagos and e buy new iPhone yesterday"
Output: "Ọ̀rẹ́ mi ń iṣẹ́ fún Google ní Ẹ̀kó, ó sì ra iPhone tuntun lánà"

Input: "Pascal and Samuel dey live for Plateau state"
Output: "Pascal àti Samuel ń gbé ní ìpínlẹ̀ Plateau"

Input: "A ti wa ni ile ise BioClinix ni Lagos State"
Output: "A ti wà ní ilé iṣẹ́ BioClinix ní Lagos State"

Input: "The test started from the nose, then the blood group"
Output: "Àyẹ̀wù bẹ̀rẹ̀ láti ara imú, lẹ́yìn náà blood group"
"""

    user_msg = f"Convert this mixed Yoruba/English text into unified, properly formatted Yoruba:\n\n{raw_text.strip()}"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        result_text = response.choices[0].message.content.strip()

        # Strip wrapping quotes if GPT added them
        if len(result_text) > 2:
            if (result_text.startswith('"') and result_text.endswith('"')) or \
               (result_text.startswith("'") and result_text.endswith("'")):
                result_text = result_text[1:-1].strip()

        if not result_text:
            logger.warning("GPT returned empty code-switch result")
            return {
                "text": raw_text,
                "code_switched": False,
                "source_text": raw_text,
            }

        logger.info("Code-switch resolved: '%s' -> '%s'", raw_text[:60], result_text[:60])
        # Cache the result to avoid redundant GPT calls for identical input
        translation_cache.put(raw_text, "code-switch", {"text": result_text})
        return {
            "text": result_text,
            "code_switched": True,
            "source_text": raw_text,
        }

    except Exception as e:
        logger.warning("Code-switch GPT call failed: %s", e)
        return {
            "text": raw_text,
            "code_switched": False,
            "source_text": raw_text,
        }


