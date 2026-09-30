"""
Shared Yoruba language detection module.

Used by both Streamlit and FastAPI backends to avoid code duplication.
"""

# Yoruba-specific characters (with diacritics)
YORUBA_CHARS = set("\u1eb9\u1ecd\u1e63\u00e1\u00e0\u00e9\u00e8\u00ed\u00ec\u00f3\u00f2\u00fa\u00f9")

# High-frequency Yoruba words that rarely appear in English
YORUBA_WORDS = {
    "ni", "ti", "naa", "ko", "wa", "si", "lati", "bi", "se",
    "ninu", "ki", "fun", "tabi", "awon", "nitori", "pe", "ati",
    "nigbati", "omo", "ile", "ojo", "aaro", "osan", "iru",
    "nkan", "nbe", "la", "lori", "nile", "nisin",
    # Additional common Yoruba words
    "mo", "lo", "ri", "ra", "mu", "je", "fe", "gbo", "so",
    "sun", "ji", "we", "fo", "se", "le", "te", "ka", "tun",
    "da", "fa", "wo", "pe", "bi", "ki",
    "nipa", "p\u1eb9lu", "l\u1e63w\u1ecd", "lab\u1eb9", "l\u00e1t\u00e1k\u00f2",
    "nibo", "kini", "bayii", "beenii", "bawo",
    # Contractions & common words as produced by ASR (often without tone marks)
    "nlo", "nje", "nbo", "ngbo", "nse", "nwa", "nri",
    "jeun", "oja", "lola", "ona", "sugbon", "oba", "bayi",
    "eko", "isu", "ata", "oko", "eti", "enu", "imu", "eku", "orin",
    "ise", "sise", "iwosan", "ounje", "agbado", "epa", "oyin",
    "iranlowo", "olori", "adura", "oja", "lola", "ona", "won", "e",
    # Pronouns and particles (common in Yoruba, ambiguous in English)
    "o", "n", "a",
}

# Words that exist in BOTH English and Yoruba (low confidence)
AMBIGUOUS_WORDS = {"ko", "wa", "si", "bi", "ni", "la", "se", "pe", "fun", "ki", "o", "a", "mi", "lo", "ri", "mu", "je", "fe", "fo", "wo", "da", "fa", "n", "won", "e"}

# Yoruba subject pronouns (very common at the start of short utterances)
YORUBA_PRONOUNS = {
    "mo", "o", "a", "e", "won", "emi", "iwo", "awa", "eyin", "eni",
    "wọn", "ẹ", "à", "ó", "mọ",
}

# Common short Yoruba expressions (used for short-utterance detection)
YORUBA_COMMON_SHORT = {
    "seun", "kaaro", "kaasan", "kaale", "kuurole", "odabo", "dabo",
    "beeni", "rara", "daadaa", "pupo", "dada", "pele", "jowo",
}

# Longer Yoruba-only words (high confidence when found).
# NOTE: 'yoruba' / 'èdè Yorùbá' is intentionally NOT here. An English sentence
# can mention "Yoruba" (the language) and would be falsely detected as Yoruba;
# genuine Yoruba writes it with diacritics ("Yorùbá"), which Tier 1 catches.
YORUBA_HIGH_CONFIDENCE = {
    "lati", "nitori", "nigbati", "ninu", "tabi", "awon",
    "aaro", "osan", "nkan", "lori", "nipa", "p\u1eb9lu",
    "ohun", "ogun", "igbo", "orisa", "olufun", "olowa",
    "bawo", "kini", "nibo", "bayii", "beenii", "pele",
    "jowo", "olorun", "oluwa",
    "nigbati", "nitori", "lati", "ninu",
    "oju", "ori", "omo", "ile", "ojo",
    "aaro", "osan", "oru", "abiku", "orogbo",
    "efun", "osun", "sango", "shango", "ogun",
    "esa", "egun", "ebo", "adura", "ife",
    "ife", "ile", "oko", "igbo", "odo",
    "ominira", "alafia", "ayọ", "ibusun",
}


def detect_language(text: str) -> str:
    """
    Detect whether text is Yoruba or English.

    Uses a three-tier approach:
    1. Character-based detection (diacritics = definitely Yoruba)
    2. High-confidence word matching (unambiguous Yoruba words)
    3. Frequency-based scoring with ambiguous word penalty

    Returns "yo" for Yoruba, "en" for English.
    """
    if not text or not text.strip():
        return "en"

    text_lower = text.lower().strip()
    words = text_lower.split()
    word_set = set(words)

    # Tier 1: If any Yoruba-specific characters are present, it's Yoruba
    if any(c in YORUBA_CHARS for c in text_lower):
        return "yo"

    # Tier 2: Check for high-confidence Yoruba-only words
    high_conf_matches = word_set & YORUBA_HIGH_CONFIDENCE
    if high_conf_matches:
        return "yo"

    # Tier 2.5: Short Yoruba expressions (pronoun-initial or common phrases)
    if len(words) < 4:
        # Common short expressions like "e seun", "pele", "jowo"
        if any(w in YORUBA_COMMON_SHORT for w in words):
            return "yo"
        # Pronoun-initial Yoruba pattern, e.g. "mo wa", "a lo", "ó ti rí"
        if words[0] in YORUBA_PRONOUNS:
            rest = words[1:]
            if len(rest) >= 1:
                yorubaish = [w for w in rest if w in YORUBA_WORDS or w in YORUBA_HIGH_CONFIDENCE]
                if len(yorubaish) >= len(rest) * 0.5:
                    return "yo"

    # Tier 3: Frequency-based scoring
    yoruba_count = 0
    ambiguous_count = 0

    for w in words:
        # YORUBA_COMMON_SHORT words are high-confidence, unambiguous Yoruba,
        # but they are intentionally kept out of YORUBA_WORDS (they are
        # handled by Tier 2.5 for short utterances). Count them here so longer
        # phrases like "e seun pupo fun iranlowo re" are still detected.
        if w in YORUBA_WORDS or w in YORUBA_COMMON_SHORT:
            if w in AMBIGUOUS_WORDS:
                ambiguous_count += 1
            else:
                yoruba_count += 1

    # Need enough words to make a decision
    if len(words) < 3:
        return "en"

    # Score: high-confidence matches weigh more, ambiguous much less
    score = (yoruba_count * 1.5 + ambiguous_count * 0.1) / len(words)

    # Require strong evidence — a single word that overlaps with Yoruba
    # (e.g. "we", "or", "a") must not flip an English sentence to Yoruba.
    if yoruba_count >= 2 and score > 0.35:
        return "yo"
    if yoruba_count >= 1 and score > 0.55:
        return "yo"

    return "en"
