"""
Safety-net: restore English words that GPT/ASR accidentally decorated with
Yoruba tone marks or subdot letters.

The real fix happens upstream (bilingual ASR prompt + hardened translation
prompts). This module is a conservative post-processor for the few remaining
cases where an English word is written in an otherwise-correct English spelling
but with a stray tone mark on a vowel (e.g. "blúd", "nóse", "clíníc"), or a
subdot letter sneaks in ("ẹxpect").

Only whole words whose diacritic-stripped base (lowercased) appears in a known
English list AND does NOT look like a Yoruba word are rewritten. Warped phonetic
re-spellings (e.g. "nóò" for "nose") cannot be reversed reliably here and are
prevented at the transcription stage instead.
"""

import re

# Map every Yoruba-diacritic character back to a plain ASCII base letter.
_DIACRITIC_MAP = {
    "\u1eb9": "e", "\u1ecd": "o", "\u1e63": "s",  # ẹ ọ ṣ
    "\u1eb8": "E", "\u1ecc": "O", "\u1e62": "S",  # Ẹ Ọ Ṣ
    "\u00e1": "a", "\u00e0": "a",
    "\u00e9": "e", "\u00e8": "e",
    "\u00ed": "i", "\u00ec": "i",
    "\u00f3": "o", "\u00f2": "o",
    "\u00fa": "u", "\u00f9": "u",
    "\u00c1": "A", "\u00c0": "A",
    "\u00c9": "E", "\u00c8": "E",
    "\u00cd": "I", "\u00cc": "I",
    "\u00d3": "O", "\u00d2": "O",
    "\u00da": "U", "\u00d9": "U",
}

_COMBINING_RE = re.compile(r"[\u0300-\u036f]")

_DIACRITIC_CHARS = set(_DIACRITIC_MAP.keys())

# Common English words (domain: medicine, family, travel, everyday).
# Kept conservative: only unambiguous English words that are almost never valid
# Yoruba words appear here.
ENGLISH_WORDS = {
    # Body & health
    "blood", "body", "bone", "brain", "breast", "breath", "breathe", "chest",
    "clinic", "doctor", "ear", "eye", "face", "finger", "group", "hair", "head",
    "health", "heart", "hospital", "injection", "kidney", "lab", "laboratory",
    "leg", "lung", "malaria", "medicine", "membrane", "mouth", "nose", "pain",
    "patient", "pressure", "sample", "skin", "stomach", "throat", "tooth",
    "vaccine", "virus", "waist", "weight", "wound",
    # Places / proper-noun contexts
    "africa", "city", "country", "government", "island", "nation", "north",
    "south", "east", "west", "state", "street", "town", "capital", "street",
    # Everyday / general
    "absolutely", "after", "again", "against", "ago", "air", "also",
    "always", "among", "another", "answer", "anyone", "anything", "area",
    "around", "arrive", "away", "back", "baby", "because", "before", "behind",
    "being", "believe", "best", "better", "between", "bride", "brought",
    "business", "care", "case", "cause", "change", "child", "children",
    "church", "city", "close", "could", "course", "court",
    "daughter", "done", "draw", "each", "earth", "english",
    "enjoy", "enough", "every", "everyone", "everything", "family", "father",
    "favor", "favourite", "feeling", "few", "fight", "finally", "find", "first",
    "food", "force", "found", "friend", "future", "general", "give", "glad",
    "good", "great", "ground", "grow", "half", "hand", "happy",
    "hard", "hear", "help", "high", "home", "hope", "hospital",
    "hour", "house", "however", "human", "hundred", "idea", "instead",
    "issue", "job", "keep", "kind", "know", "large", "last", "later", "learn",
    "leave", "left", "legal", "letter", "life", "light", "like", "listen",
    "little", "lived", "local", "long", "look", "lord", "love", "made", "make",
    "many", "market", "matter", "maybe", "mean", "mother", "move",
    "much", "must", "name", "near", "need", "never", "next", "night",
    "nothing", "number", "office", "often", "once", "only", "open",
    "other", "outside", "over", "own", "people", "person", "place", "please",
    "point", "possible", "present", "probably", "problem", "public", "question",
    "quick", "reach", "read", "ready", "real", "reason", "remember", "right",
    "room", "round", "same", "say", "school", "secret", "sense", "service",
    "several", "should", "since", "small", "something", "sometimes",
    "speak", "special", "speech", "still", "story", "strong",
    "study", "sure", "talk", "team", "tell", "thing", "think", "thought",
    "through", "today", "together", "tomorrow", "took", "toward",
    "travel", "true", "trust", "truth", "turn", "under", "understand", "until",
    "very", "voice", "wait", "walk", "want", "watch", "water", "way", "week",
    "whole", "woman", "women", "wonder", "work", "world", "would",
    "write", "wrong", "year", "young", "youth",
}

# Yoruba bases that collide with English spellings (e.g. "ni", "pe", "awon").
# If a stripped base is in here, we leave it alone: it is too likely to be
# legitimate Yoruba.  Expanded to cover the most frequent Yoruba words that
# ASR / tone-restoration produce, so the guard never strips their marks.
YORUBA_BASES = {
    # Pronouns & particles
    "ni", "ti", "si", "wa", "ko", "bi", "pe", "ki", "fun", "o", "a",
    "se", "mo", "lo", "ro", "wo", "fo", "jo", "to", "so", "ri", "mu", "je",
    "fe", "ka", "wun", "won", "pa", "tan", "ma", "ra", "bo", "le",
    "awon", "emi", "iwo", "awa", "eyin", "eni", "eniyen",
    # Common verbs
    "sin", "ja", "rin", "dide", "sa", "sun", "ji", "we", "te",
    # Common nouns
    "omo", "ojo", "aaro", "osan", "iran", "igba", "ogun",
    "iya", "baba", "ore", "ada", "ife", "ori", "oju", "enu", "imu",
    "eti", "aka", "ese", "ila", "ara", "ebo", "epo", "aarin",
    "oja", "ona", "ile", "ogba", "agbegbe", "ilu", "afo",
    "ounje", "amala", "iyan", "gari", "semo", "lafun", "ate",
    "ewa", "agbado", "oyin", "epa",
    # Time words
    "oni", "lana", "ola", "bayii", "nigba", "lola", "loni",
    "lanaa", "akoko", "lati", "nisi",
    # Adjectives
    "dun", "giga", "keke", "nla", "pupa", "funfun", "bulu",
    "tuntun", "daadaa", "kere", "pupo", "pupoo", "dada",
    # Numbers
    "okan", "eji", "eta", "erin", "aarun", "efa", "eje", "ejo", "esa",
    # Prepositions & conjunctions
    "nitori", "tabi", "ati", "ninu", "nipa", "lori", "nile", "labe",
    "latako", "nibe", "pelp", "nipol", "nipon",
    # Religion & culture
    "olorun", "oluwa", "yoruba", "orisa", "egungun", "igbo",
    "igbagbo", "osupa", "egbe", "idile",
    # Animals
    "aja", "ologbo", "adiye", "malu", "agbo", "eja", "epon",
    "akuko", "agutan", "ewu", "aya",
    # Body parts
    "onu", "obo",
    # Common expressions
    "abi", "naa", "yen", "tele", "imoju", "isura", "igbi",
    "igbekele",
    # Place names
    "ibadan", "badagry",
    # Actions
    "joko", "dide", "sa",
}


def _strip_word(word: str) -> str:
    """Return the ASCII base spelling of a word (lowercase), tone marks removed."""
    out = []
    for ch in word:
        if ch in _DIACRITIC_MAP:
            out.append(_DIACRITIC_MAP[ch])
        elif _COMBINING_RE.match(ch):
            continue
        else:
            out.append(ch)
    return "".join(out)


def _is_english_rescue(word: str) -> str | None:
    """If word is an English word marred by tone marks, return the correct form.

    Returns ``word`` unchanged when it already has no marks (nothing to fix) or
    ``None`` when the word is not a rescue candidate.
    """
    if word.isascii():
        return word

    base_lower = _strip_word(word).lower()
    if base_lower not in ENGLISH_WORDS or base_lower in YORUBA_BASES:
        return None
    return base_lower


def restore_english_words(text: str) -> str:
    """Rewrite English words that carry stray Yoruba tone marks back to English.

    Only touches words whose lowercased ASCII base is in the curated English
    list, so real Yoruba words (which almost never match) are left untouched.
    """
    if not text:
        return ""
    if not any(c in text for c in _DIACRITIC_CHARS):
        return text

    token_re = re.compile(
        r"[A-Za-z]+(?:[\u1eb9\u1ecd\u1e63\u00e1\u00e0\u00e9\u00e8\u00ed\u00ec\u00f3\u00f2\u00fa\u00f9\u0300-\u036f][A-Za-z\u1eb9\u1ecd\u1e63\u00e1\u00e0\u00e9\u00e8\u00ed\u00ec\u00f3\u00f2\u00fa\u00f9\u0300-\u036f]*)+"
    )

    def _fix(m: re.Match) -> str:
        token = m.group(0)
        fixed = _is_english_rescue(token)
        if fixed is None:
            return token
        if token[:1].isupper() and token[1:].islower():
            return fixed[:1].upper() + fixed[1:]
        return fixed

    return token_re.sub(_fix, text)