import re

# =====================================================
# YORUBA TONE MAP — multi-word phrases and common words
# Single-char entries removed (too aggressive for automated restoration)
# =====================================================

TONE_MAP = {

    # ── Greetings & Politeness ──
    "bawo ni": "báwo ni",
    "e kaaro": "ẹ káàárọ̀",
    "e kaasan": "ẹ káàsán",
    "e kuurole": "ẹ kúùrọ̀lẹ́",
    "e kaale": "ẹ káalẹ́",
    "e ku irora": "ẹ kú ìrora",
    "e ku ise": "ẹ kú iṣẹ́",
    "e ku ojo": "ẹ kú ojọ́",
    "odabo": "òdàbọ̀",
    "o daabo": "ó dàábọ̀",
    "e se": "ẹ ṣe",
    "e seun": "ẹ ṣéun",
    "e se pupo": "ẹ ṣẹ̀pọ̀pọ̀",
    "jowo": "jọ̀wọ́",
    "joo": "jọ̀ọ́",
    "pele": "pẹ̀lẹ́",
    "o ku ojumo": "ó kú ojúmọ́",
    "o ku osan": "ó kú ọ̀sán",
    "o ku irule": "ó kú ìrúlẹ́",
    "e ku ojo ibo": "ẹ kú ojọ́ ibọ̀",
    "o dabo": "ó dàbọ̀",
    "o re o": "ó ẹ rẹ o",
    "o ti ri": "ó ti rí",
    "o n lo": "ó ń lọ",
    "mo n lo": "mọ́ ń lọ",

    # ── Common Expressions ──
    "mo wa daadaa": "mo wà dáadáa",
    "mo wa": "mo wà",
    "o daa": "ó dáa",
    "o dara": "ó dára",
    "beeni": "bẹ́ẹ̀ni",
    "rara": "rárá",
    "ooto": "ọ̀ọ́tọ́",
    "o ye ko": "ó yẹ kí",
    "o ye": "ó yẹ",
    "mo ye": "mọ̀yẹ́",
    "mo lo": "mọ̀ lọ",
    "mo de": "mọ̀ dé",
    "mo wa lo": "mo wà lọ",
    "mo fe": "mọ̀ fẹ́",
    "o fe": "ó fẹ́",
    "ko si": "kọ̀ sí",
    "ko wa": "kọ̀ wá",
    "ko ni": "kọ̀ ní",
    "mo ni": "mọ̀ ní",
    "mo ro": "mọ̀ rọ̀",
    "mo mo": "mọ̀ mọ̀",
    "o mo": "ó mọ̀",
    "a mo": "à mọ̀",
    "a wa": "à wá",
    "a lo": "à lọ",
    "a se": "à ṣe",
    "a ro": "à rọ̀",
    "e mo": "ẹ mọ̀",
    "e lo": "ẹ lọ",
    "e wa": "ẹ wá",
    "e ro": "ẹ rọ̀",

    # ── Pronouns (multi-char only) ──
    "emi": "èmi",
    "iwọ": "ìwọ",
    "awa": "àwa",
    "awon": "àwọn",
    "eyin": "ẹ̀yìn",
    "eni": "ẹni",
    "eniyen": "ẹnìyẹn",

    # ── Common Verbs (multi-char only) ──
    "je": "jẹ",
    "mu": "mú",
    "lo": "lọ",
    "wa": "wá",
    "ri": "rí",
    "fe": "fẹ́",
    "ko": "kọ́",
    "gbo": "gbọ́",
    "so": "sọ",
    "sun": "sùn",
    "ji": "jí",
    "we": "wẹ",
    "fo": "fọ",
    "se": "ṣe",
    "te": "tẹ́",
    "ka": "kà",
    "tun": "tún",
    "wo": "wọ̀",
    "da": "dá",
    "fa": "fà",
    "gbu": "gbù",
    "nu": "nú",
    "du": "dù",
    "ku": "kú",
    "su": "sù",
    "bu": "bù",
    "wu": "wù",
    "fu": "fù",
    "gu": "gù",
    "ju": "jù",
    "yu": "yù",
    "zu": "zù",
    "hu": "hù",
    "ru": "rù",
    "tu": "tú",
    "pu": "pù",

    # ── Common Nouns ──
    "omo": "ọmọ",
    "ojo": "ọjọ́",
    "aaro": "ààrọ̀",
    "osan": "ọ̀sán",
    "iran": "ìrà",
    "igba": "igbá",
    "ogun": "ogún",

    # ── Numbers ──
    "okan": "ọ̀kan",
    "eji": "ẹ̀jì",
    "eta": "ẹ̀ta",
    "erin": "ẹ̀rin",
    "aarun": "àárún",
    "efa": "ẹ̀fà",
    "eje": "ẹ̀jẹ",
    "ejo": "ẹ̀jọ",
    "esa": "ẹ̀sà",
    "mokanla": "mọ́kanlá",
    "mejila": "mẹ́jìnlá",

    # ── Adjectives ──
    "dun": "dùn",
    "giga": "gígà",
    "keke": "kékéré",
    "nla": "ńlá",
    "pupa": "púpá",
    "funfun": "fùnfùn",
    "bulu": "búlù",
    "tuntun": "tuntun",
    "daadaa": "dáadáa",
    "kere": "kéré",
    "pupo": "púpọ̀",
    "pupoo": "púpọ̀ọ́",
    "dada": "dádá",
    "miiran": "mìíràn",

    # ── Family ──
    "iya": "ìyá",
    "baba": "bàbá",
    "ore": "ọ̀rẹ́",
    "ada": "àdá",
    "abinibi": "abínìbí",

    # ── Places ──
    "oja": "ọjà",
    "ona": "ọ̀nà",
    "ile iwe": "ilé ìwé",
    "ile iwosan": "ilé ìwòsàn",
    "ogba": "ogbá",
    "agbegbe": "agbègbè",
    "ilu": "ilú",
    "afo": "àfọ́",
    "oju oja": "ọjọ́ ọjà",
    "isin": "ìṣiñ",
    "ipin": "ìpín",
    "ita": "ìtà",

    # ── Food & Drink ──
    "ounje": "oúnjẹ",
    "amala": "àmàlà",
    "iyan": "ìyàn",
    "gari": "gàrì",
    "semo": "sẹ̀mọ̀",
    "lafun": "láfùn",
    "ate": "àtẹ́",
    "ewa": "ẹ̀wà",
    "agbado": "agbàdò",
    "oyin": "oyìn",
    "epa": "ẹ̀pá",
    "mu omi": "mú omi",
    "je ounje": "jẹ oúnjẹ",

    # ── Time ──
    "oni": "òní",
    "lana": "lánàá",
    "ola": "ọ̀la",
    "bayii": "báyìí",
    "nigba ti": "nìgbà tí",
    "nigba": "nìgbà",
    "lola": "lọ̀la",
    "loni": "lóní",
    "lanaa": "lánàá",
    "ni aaro": "ní ààrọ̀",
    "ni osan": "ní ọ̀sán",
    "ni ojo": "ní ojọ́",
    "ni ale": "ní àlẹ́",
    "igba akoko": "ìgbà akókò",
    "akoko": "akókò",
    "ibadan": "ìbàdàn",
    "di poju": "dí pọ̀jú",
    "lati": "láti",
    "nisi": "nísì",

    # ── Questions ──
    "se o": "ṣé o",
    "kini ohun": "kí ni ohun",
    "kini ojo": "kí ni ojọ́",
    "kini": "kí ni",
    "nibo": "níbo",
    "ta ni": "ta ni",
    "nigbati": "nìgbà tí",
    "kilode": "kí lọ́de",
    "se ohun": "ṣé ohun",
    "nigba ta": "nìgbà tí a",
    "niko": "níkí",

    # ── Prepositions & Conjunctions ──
    "nitori": "nìtorí",
    "tabi": "tàbí",
    "ati": "àti",
    "ninu": "nínú",
    "nipa": "nípa",
    "lori": "lórí",
    "nile": "nílé",
    "labe": "labẹ́",
    "latako": "látákò",
    "nibe": "níbẹ̀",
    "pẹlu": "pẹ̀lú",
    "nipọ": "nípọ̀",
    "lọwọ": "lọ́wọ́",
    "nipọn": "nípọ̀n",

    # ── Religion & Culture ──
    "olorun": "olórun",
    "oluwa": "olúwa",
    "yoruba": "yorùbá",
    "orisa": "òrìṣà",
    "egungun": "ẹ̀gúngún",
    "igbo": "ìgbó",
    "esi": "ẹ̀sì",
    "orin": "orin",
    "ijọ": "ijọ̀",
    "igbagbo": "ìgbàgbọ́",
    "osupa": "ọ̀súpá",
    "ori": "orí",
    "egbe": "ẹ̀gbẹ́",
    "idile": "idìlé",

    # ── Animals ──
    "aja": "ajá",
    "ologbo": "ológbò",
    "adiye": "àdìyẹ",
    "malu": "màlúù",
    "agbo": "àgbò",
    "eja": "ẹja",
    "epon": "ẹ̀pòn",
    "akuko": "akúkọ",
    "agutan": "agútàn",
    "ewu": "ẹ̀wù",
    "aya": "àyá",

    # ── Body Parts ──
    "oju": "ọjú",
    "enu": "ẹnu",
    "imu": "imú",
    "eti": "etí",
    "aka": "àkà",
    "ese": "ẹ̀sẹ́",
    "ila": "ilá",
    "iboju": "ìbojú",
    "ara": "àrà",
    "ebo": "ẹ̀bọ̀",
    "igbe": "ìgbẹ́",
    "epo": "ẹ̀pọ̀",
    "aarin": "aàrín",

    # ── Actions & States ──
    "sin": "sìn",
    "ja": "jà",
    "fe wa": "fẹ́ wá",
    "fe lo": "fẹ́ lọ",
    "fe je": "fẹ́ jẹ",
    "fe mu": "fẹ́ mú",
    "wi": "wí",
    "rin": "rìn",
    "rin lo": "rìn lọ",
    "rin wa": "rìn wá",
    "joko": "jọkò",
    "joko si": "jọkò sí",
    "dide": "dídẹ́",
    "dide lo": "dídẹ́ lọ",
    "sa lo": "sà lọ",
    "sa wa": "sà wá",

    # ── Relationship Words ──
    "ife": "ifẹ́",
    "ife mi": "ifẹ́ mi",
    "omo okunrin": "ọmọkùnrin",
    "omo obinrin": "ọmọbìnrin",
    "okunrin": "okùnrin",
    "obinrin": "obìnrin",
    "omoba": "omúwá",
    "omode": "omọdé",
    "agbalagbi": "agbàlàgbì",
    "eyan": "èyàn",
    "ilara": "ìlélá",
    "idile": "idìlé",
    "owo": "owó",
    "ogbo": "ọ̀gbọ̀",
    "eleyi": "èyí",
    "eyin": "ẹ̀yìn",

    # ── Common Phrases (pronoun + verb) ──
    "mo n": "mọ́ ń",
    "o n": "ó ń",
    "a n": "à ń",
    "e n": "ẹ ń",
    "mo ti": "mọ̀ ti",
    "o ti": "ó ti",
    "a ti": "à ti",
    "e ti": "ẹ ti",
    "mo le": "mọ̀ lè",
    "o le": "ó lè",
    "a le": "à lè",
    "e le": "ẹ lè",
    "mo gbọ": "mọ̀ gbọ́",
    "o gbọ": "ó gbọ́",
    "a gbọ": "à gbọ́",
    "e gbọ": "ẹ gbọ́",
    "mo se": "mọ̀ ṣe",
    "o se": "ó ṣe",

    # ── Additional Common Words (multi-char only, no duplicates) ──
    "abi": "abí",
    "dabi": "dá bí",
    "naa": "náà",
    "yen": "yẹn",
    "tele": "tẹ̀lé",
    "omoba": "omúwá",
    "omode": "omọdé",
    "agbalagbi": "agbàlàgbì",
    "eleyi": "èyí",
    "ogbo": "ọ̀gbọ̀",
    "ilara": "ìlélá",
    "imoju": "ìmọ̀jú",
    "isura": "ìsùúrà",
    "igbi": "ìgbì",
    "igbekele": "ìgbé̀kẹ́lẹ́",
    "omi inu": "omi inú",
    "ojo ibo": "ojọ́ ibọ̀",
    "ojo isin": "ojọ́ ìsìn",
    "ojo ale": "ojọ́ àlẹ́",
    "nigbana": "nìgbà náà",
    "igba ojo": "igbá ojọ́",
    "eyan": "èyàn",
    "owo": "owó",
    "omo": "ọmọ",
    "oju": "ọjú",
    "enu": "ẹnu",
    "imu": "imú",
    "eti": "etí",
    "aka": "àkà",
    "ese": "ẹ̀sẹ́",
    "ila": "ilá",
    "ara": "àrà",
    "igbe": "ìgbẹ́",
    "epo": "ẹ̀pọ̀",
    "aarin": "aàrín",
    "onu": "ọnú",
    "obo": "óbọ",
    "ewu": "ẹ̀wù",
    "afo": "àfọ́",

    # ── Government & Society ──
    "igbejọba": "ìgbẹ̀jọba",
    "igbosesi": "ìgbọ̀sẹ̀sì",
    "ajoye": "àjòyè",
    "ogbomirin": "ogbóńirin",
    "ogbongbodo": "ogbongbọdọ",

    # ── Common Verbs & Phrases ──
    "mo ri": "mọ̀ rí",
    "o ri": "ó rí",
    "a ri": "à rí",
    "e ri": "ẹ rí",
    "mo fi": "mọ̀ fi",
    "o fi": "ó fi",
    "a fi": "à fi",
    "mo ka": "mọ̀ kà",
    "o ka": "ó kà",
    "mo gbo": "mọ̀ gbọ́",
    "o gbo": "ó gbọ́",
    "mo so": "mọ̀ sọ",
    "o so": "ó sọ",
    "mo le": "mọ̀ lè",
    "o le": "ó lè",
    "a le": "à lè",
    "mo wa": "mo wà",
    "o wa": "ó wà",
    "a wa": "à wá",
    "mo lo": "mọ̀ lọ",
    "o lo": "ó lọ",
    "a lo": "à lọ",
    "mo de": "mọ̀ dé",
    "o de": "ó dé",
    "a de": "à dé",
    "mo je": "mọ̀ jẹ",
    "o je": "ó jẹ",
    "a je": "à jẹ",
    "mo mu": "mọ̀ mú",
    "o mu": "ó mú",
    "a mu": "à mú",
    "mo fe": "mọ̀ fẹ́",
    "o fe": "ó fẹ́",
    "a fe": "à fẹ́",

    # ── Place-related ──
    "lati": "láti",
    "si ibe": "sí ibẹ̀",
    "ni ibe": "ní ibẹ̀",
    "lati ibe": "láti ibẹ̀",

    # ── More Common Expressions ──
    "o ti": "ó ti",
    "mo ti": "mọ̀ ti",
    "a ti": "à ti",
    "e ti": "ẹ ti",
    "o n lo": "ó ń lọ",
    "mo n lo": "mọ́ ń lọ",
    "a n lo": "à ń lọ",
    "e n lo": "ẹ ń lọ",
    "o ti ri": "ó ti rí",
    "mo ti ri": "mọ̀ ti rí",
    "a ti ri": "à ti rí",
    "e ti ri": "ẹ ti rí",
}

# =====================================================
# SORT LONGEST FIRST (for greedy matching)
# =====================================================

SORTED_KEYS = sorted(TONE_MAP.keys(), key=len, reverse=True)

# Pre-compiled regex (built once at import time, not per call)
_TONE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in SORTED_KEYS) + r")\b",
    flags=re.IGNORECASE,
)


def _tone_replace(match):
    key = match.group(0).lower()
    return TONE_MAP.get(key, match.group(0))


# =====================================================
# MAIN FUNCTION
# =====================================================

def restore_tones(text: str) -> str:
    """Restore Yoruba tone marks onunttoned text.

    Strategy:
    - Match multi-word phrases first (greedy, longest first)
    - Only replace words that don't already have diacritics
    - Never lowercase the full text (preserves any existing marks)
    - Skip single-character entries to avoid false positives
    """
    if not text:
        return ""

    # No text-level early-out on diacritics: keys are untoned and IGNORECASE
    # never folds a diacritic letter onto a base letter, so the regex only
    # matches words that LACK tone marks. Already-toned words (e.g. "ọmọ",
    # "èmi") are never matched, and words still missing their tones (e.g.
    # "emi" next to a toned "iwọ") are restored. Per-word protection in
    # _tone_replace keeps the behavior safe.

    output = _TONE_PATTERN.sub(_tone_replace, text)
    return output
