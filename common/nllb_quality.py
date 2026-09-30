"""
Heuristic quality scoring for NLLB English -> Yoruba output.

NLLB en->yo is usually excellent, but on some inputs it emits non-idiomatic
or orthographically corrupt Yoruba (e.g. "Àárọ̀, báwo..." for a good-morning
greeting, or plain ASCII "E kaaro" with no tone marks). Callers use this
module to decide whether the NLLB result is good enough to return directly,
or whether to escalate to GPT+RAG few-shot for a corrected translation.

Note: NLLB legitimately renders tone-marked vowels as base letter + combining
mark (e.g. "fẹ́" for "fẹ́"), so combining marks are NOT treated as corruption.
All checks are free (pure string logic) so good NLLB output costs nothing.
"""

import re

from common.nllb import _looks_like_echo

# Precomposed Yoruba tone letters plus any combining mark (NLLB renders
# tone-marked vowels as base + combining, e.g. "ẹ́" for "ẹ́").
TONE_OR_COMBINING = r"[ẹọṣáàéèíìóòúù]|[\u0300-\u036f]"

# (English trigger pattern, required Yoruba pattern). If a trigger matches the
# source, the output must contain its required form.
GREETING_RULES = [
    (r"good\s+morning", r"káàárọ|kaaro"),
    (r"good\s+afternoon", r"káàsán|kaasan"),
    (r"good\s+evening", r"káalẹ|kaale"),
    (r"good\s+night", r"dàárọ|daaro|dáa"),
    (r"good\s+day", r"kàá|kú\s+ọjọ|kaasan|kaaro"),
    (r"\bhello\b|\bhi\b|how\s+(are|do\s+you)|how're|hows", r"báwo|bawo|è\s+ká|kú|kàá|kaaro|kaasan|àlàáfíà|alafia"),
    (r"\bwelcome\b", r"kàbọ|kabo"),
    (r"\bgoodbye\b|\bbye\b|see\s+you", r"dàbọ|dabo|máa rí|ma a rí|má a rí"),
    (r"\bthank", r"seun|ṣeun|dúpẹ|dupe|dúpé|dupé"),
    (r"\bplease\b", r"jọ̀wọ́|jowo|jọwọ|dákun|dakun"),
]

_REPEAT_WORD = re.compile(r"\b(\w{3,})\b(\s+\1\b){2,}")

# Yoruba diacritic letters -> plain ASCII base (for detecting transliteration).
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

# base vowel + combining dot below -> precomposed Yoruba ẹ/ọ/ṣ (with tone kept).
_COMBINING_DOT_MAP = {
    "e": "ẹ", "é": "ẹ́", "è": "ẹ̀", "ē": "ẹ̄",
    "E": "Ẹ", "É": "Ẹ́", "È": "Ẹ̀",
    "o": "ọ", "ó": "ọ́", "ò": "ọ̀", "ō": "ọ̄",
    "O": "Ọ", "Ó": "Ọ́", "Ò": "Ọ̀",
    "s": "ṣ", "S": "Ṣ",
}


def normalize_combining(text: str) -> str:
    """Rewrite NLLB's base+combining-dot spelling (ẹ́, ọ̀, ṣe̩...) to the
    standard precomposed ẹ/ọ/ṣ used everywhere else in the app, so heuristic
    pattern matching sees the canonical orthography."""
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\u0323" and out and out[-1] in _COMBINING_DOT_MAP:
            out[-1] = _COMBINING_DOT_MAP[out[-1]]
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def has_combining_dot_corruption(text: str) -> bool:
    """Diagnostic only: dots/rings on letters that never carry them.

    This is intentionally NOT part of ``assess_en_to_yo`` because NLLB
    legitimately writes ẹ/ọ/ṣ as base+combining (ẹ́, ọ̀, ṣẹ́). It can still be
    useful for auditing corpus or model output offline.
    """
    return bool(re.search(r"[A-Za-z]\u0323|[A-Za-z]\u0325", text))


def _greeting_mismatch(source: str, output: str) -> bool:
    src = source.lower()
    norm = normalize_combining(output).lower()
    for trigger, required in GREETING_RULES:
        if re.search(trigger, src):
            if not re.search(required, norm):
                return True
    return False


def _no_tone_marks(output: str) -> bool:
    return len(output) >= 8 and not re.search(TONE_OR_COMBINING, output)


# English words that NLLB frequently transliterates ("Yorubizes") into
# pseudo-Yoruba like "tẹ́st" (test), "ojẹ́" (of), "wí" (with). When the source
# is English and several of these ASCII bases appear in the output, the output
# is very likely corrupted transliteration rather than real Yoruba. Kept
# conservative: real loanwords (phone, computer, bread...) are NOT listed, and
# common Yoruba words (won, mo, ti, ni, si, awa...) are excluded too.
_ENGLISH_TRANSLITERATION_BASES = {
    "test", "tests", "of", "the", "and", "with", "from", "for", "that",
    "this", "these", "those", "there", "their", "they", "which", "what",
    "when", "where", "who", "whose", "why", "how", "will", "would", "could",
    "should", "can", "can't", "cannot", "won't", "you", "your", "yours",
    "we", "our", "ours", "them", "their", "want", "wants", "wanted",
    "wanting", "use", "uses", "used", "using", "transcrib", "translat",
    "machine", "device", "tool", "app", "application", "program", "software",
    "speech", "voice", "audio", "record", "recording", "recorded", "human",
    "person", "people", "man", "woman", "women", "write", "written", "read",
    "language", "english", "capture", "captures", "convert", "convert",
}

# Yoruba bases that can coincide with the English list above; must be
# excluded or the check would falsely flag real Yoruba words.
_YORUBA_COLLIDES = {
    "won", "mo", "ni", "ti", "si", "wa", "ko", "pe", "fun", "kan", "la",
    "ta", "ra", "le", "bi", "o", "a", "e", "so", "lo", "ro", "wo", "fo",
    "jo", "to", "je", "mu", "ri", "ohun", "si",
}


# Exact pseudo-Yoruba artifacts NLLB repeatedly emits for common English words
# on technical/abstract input. These keep the English consonant/syllable shape
# but with Yoruba vowels/tones, so they look like real Yoruba but are not.
_NLLB_ARTIFACT_TOKENS = {
    "tẹstv", "tẹst", "test", "ojẹ", "oje", "ðẹ", "wánti", "wanti", "want",
    "búfẹ", "bufe", "mẹjìn", "mejin", "mashín", "mashin", "àlílò", "alilo",
    "kaptur", "kápchạ", "kapture", "kàpture", "konvẹt",
    "kónvẹti", "sọftwẹ", "softwe", "apọ", "àpọ", "rekọd", "rekod",
    "rekọdi", "wòis", "wois", "vòis", "vois", "trànskrạib", "transkraib",
}


def _is_english_transliteration_base(base: str) -> bool:
    """True when an ASCII-decorated token is (or prefixes) a known English
    transliteration artifact. NLLB writes pseudo-Yoruba like 'tẹ́st' (test),
    'ojẹ́' (of), 'wánti' (want to), 'mẹ́jìn' (machine). We match both exact
    artifact tokens and tokens that *start* with an English stem of length
    >= 3."""
    if not base:
        return False
    if base in _NLLB_ARTIFACT_TOKENS:
        return True
    for art in _ENGLISH_TRANSLITERATION_BASES:
        if len(art) < 3:
            continue
        if base == art or (len(base) >= len(art) and base[: len(art)] == art):
            return True
    return False


def _contains_english_transliteration(output: str) -> bool:
    """Detect pseudo-Yoruba made by transliterating English words.

    NLLB (and weak seq2seq models) sometimes "Yorubize" English when it hits
    a technical/abstract sentence. Typical artifacts: 'tẹ́st', 'ojẹ́',
    'wántípé' (want to), 'òf' (of). These all carry tone marks, so the normal
    tone-mark check does not catch them. We strip the diacritics from each
    token and look for several English stems.
    """
    if not output:
        return False
    tokens = re.findall(
        r"[A-Za-z\u1eb9\u1ecd\u1e63\u00e1\u00e0\u00e9\u00e8\u00ed\u00ec\u00f3\u00f2\u00fa\u00f9\u0300-\u036f]+",
        output,
    )
    if len(tokens) < 3:
        return False
    hits = 0
    for tok in tokens:
        base = "".join(
            _DIACRITIC_MAP.get(c, c)
            for c in tok
            if not re.match(r"[\u0300-\u036f]", c)
        ).lower()
        if base in _YORUBA_COLLIDES:
            continue
        if _is_english_transliteration_base(base):
            hits += 1
    # Two or more English transliteration artifacts => very likely corrupted.
    return hits >= 2


def assess_en_to_yo(source: str, output: str) -> tuple[bool, str | None]:
    """Return (good, reason). ``good`` is False when GPT should re-translate."""
    if not output.strip():
        return False, "empty output"
    if _looks_like_echo(source, output):
        return False, "output echoes input"
    if _greeting_mismatch(source, output):
        return False, "non-standard greeting form"
    if _no_tone_marks(output):
        return False, "missing tone marks"
    if _REPEAT_WORD.search(output):
        return False, "repeated/garbled tokens"
    if _contains_english_transliteration(output):
        return False, "english words transliterated to pseudo-Yoruba"
    return True, None
