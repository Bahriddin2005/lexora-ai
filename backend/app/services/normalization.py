"""Canonical search keys. The same function builds `words.normalized` and the query key."""

import re
import unicodedata

_APOSTROPHES = re.compile(r"[ʻʼ’‘`´′ʹ']")
_SPACES = re.compile(r"\s+")
_EDGE_PUNCT = '"“”„«»‹›()[]{}.,!?;:…'

_UZ_CYR_MARKERS = set("ўғқҳЎҒҚҲ")
_UZ_CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "'",
    "ь": "", "ы": "i", "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}  # fmt: skip
_CYR_VOWELS = set("аеёиоуўэюя")

# Languages that accept input in more than their primary script.
ALT_SCRIPTS: dict[str, set[str]] = {"uz": {"Cyrl"}}


def detect_script(text: str) -> str:
    counts = {"Latn": 0, "Cyrl": 0, "Arab": 0}
    for ch in text:
        if not ch.isalpha():
            continue
        name = unicodedata.name(ch, "")
        if name.startswith("CYRILLIC"):
            counts["Cyrl"] += 1
        elif name.startswith("ARABIC"):
            counts["Arab"] += 1
        elif name.startswith("LATIN"):
            counts["Latn"] += 1
    best = max(counts, key=lambda k: counts[k])
    return best if counts[best] else "Latn"


def has_uz_cyrillic(text: str) -> bool:
    return any(ch in _UZ_CYR_MARKERS for ch in text)


def transliterate_uz_cyrillic(text: str) -> str:
    out: list[str] = []
    lower = text.lower()
    for i, ch in enumerate(lower):
        if ch == "е":
            prev = lower[i - 1] if i else ""
            at_start = not prev or not prev.isalpha()
            out.append("ye" if at_start or prev in _CYR_VOWELS or prev in "ъь" else "e")
        else:
            out.append(_UZ_CYR_TO_LAT.get(ch, ch))
    return "".join(out)


def _strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return unicodedata.normalize("NFC", "".join(c for c in decomposed if not unicodedata.combining(c)))


def clean(text: str) -> str:
    """Language-independent cleanup: NFKC, unified apostrophes, collapsed spaces, trimmed punctuation."""
    s = unicodedata.normalize("NFKC", text)
    s = _APOSTROPHES.sub("'", s)
    s = _SPACES.sub(" ", s).strip()
    return s.strip(_EDGE_PUNCT).strip()


def normalize(text: str, lang: str | None = None) -> str:
    s = clean(text)
    if lang == "tr":
        s = s.replace("İ", "i").replace("I", "ı").lower().replace("ı", "i")
    else:
        s = s.lower()
    if lang == "uz":
        if detect_script(s) == "Cyrl":
            s = transliterate_uz_cyrillic(s)
    elif lang == "ru":
        s = s.replace("ё", "е")
    elif lang not in ("tr",) and detect_script(s) == "Latn":
        s = _strip_diacritics(s)
    return s


def tokens(text: str) -> list[str]:
    return [t for t in clean(text).split(" ") if t]
