"""
Heuristic detection of proper nouns / brand names inside English text.

Used to route English->Yoruba translation to GPT (which preserves proper nouns
verbatim) instead of NLLB (which may transliterate or "Yorubize" them, e.g.
"BioClinix" -> "baóklínitnííbi", "Lagos" -> "èlẹ́gọ́stìtibẹlawa").
"""

import re

# Common place names / brand tokens (canonical spellings we expect to keep).
KNOWN_PROPER_NOUNS = {
    "lagos", "abuja", "ibadan", "ilorin", "kano", "portharcourt", "benin",
    "ogun", "oyo", "osun", "ondo", "ekiti", "kwara", "niger", "kaduna",
    "sokoto", "borno", "yobe", "gombe", "adamawa", "taraba", "plateau",
    "nasarawa", "benue", "kogi", "enugu", "anambra", "imo", "enugu",
    "akwaibom", "crossriver", "bayelsa", "rivers", "delta", "edo", "abia",
    "ebonyi", "bioclinix", "google", "facebook", "mtn", "glo", "airtel",
    "nigeria", "accra", "london", "america", "unitedstates", "china",
    "iphone", "whatsapp", "instagram", "youtube", "twitter",
}


def contains_proper_nouns(text: str | None) -> bool:
    """True when text likely contains a proper noun / brand / place name."""
    if not text:
        return False

    words = text.split()
    if not words:
        return False

    for i, w in enumerate(words):
        clean = re.sub(r"[^A-Za-z0-9]", "", w)
        if not clean:
            continue

        # 1) Known proper-noun tokens (case-insensitive).
        if clean.lower() in KNOWN_PROPER_NOUNS:
            return True

        # 2) CamelCase / PascalCase (e.g. BioClinix, iPhone, WordPress).
        if clean[0].isupper() and any(c.isupper() for c in clean[1:]):
            return True

        # 3) Title-cased word not at the start of a sentence (e.g. "in Lagos
        #    State", "at BioClinix").  A lowercase word must precede it.
        if clean[0].isupper() and i > 0:
            prev = re.sub(r"[^A-Za-z0-9]", "", words[i - 1])
            if prev and prev[0].islower():
                return True

    return False