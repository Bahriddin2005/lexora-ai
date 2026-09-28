"""Natural-language query parsing: rules first, LLM fallback only when rules are not enough."""

import re
from typing import Literal

from pydantic import BaseModel

from app.services.normalization import clean

IntentType = Literal["lookup", "translate", "list_new_terms"]


class Intent(BaseModel):
    type: IntentType = "lookup"
    term: str | None = None
    source_lang: str | None = None
    target_lang: str | None = None
    domain: str | None = None
    year: int | None = None


# Phrases are matched on the lowercased query with unified apostrophes.
LANGUAGE_WORDS: dict[str, str] = {
    "o'zbekcha": "uz", "o'zbek tilida": "uz", "o'zbek tiliga": "uz", "o'zbek tilidagi": "uz", "o'zbekchada": "uz",
    "uzbek": "uz", "по-узбекски": "uz", "на узбекском": "uz", "на узбекский": "uz",
    "inglizcha": "en", "ingliz tilida": "en", "ingliz tiliga": "en", "ingliz tilidagi": "en", "inglizchada": "en",
    "english": "en", "по-английски": "en", "на английском": "en", "на английский": "en",
    "ruscha": "ru", "rus tilida": "ru", "rus tiliga": "ru", "rus tilidagi": "ru", "ruschada": "ru",
    "russian": "ru", "по-русски": "ru", "на русском": "ru", "на русский": "ru",
    "turkcha": "tr", "turk tilida": "tr", "turk tiliga": "tr", "turk tilidagi": "tr", "turkchada": "tr",
    "turkish": "tr", "по-турецки": "tr", "на турецком": "tr", "на турецкий": "tr",
}  # fmt: skip

DOMAIN_WORDS: dict[str, str] = {
    "dasturlashda": "computing", "dasturlash": "computing", "programming": "computing", "in programming": "computing",
    "в программировании": "computing", "it sohasida": "computing",
    "ai sohasida": "ai", "sun'iy intellekt sohasida": "ai", "sun'iy intellektda": "ai", "ai terms": "ai",
    "ai terminlar": "ai", "ai terminlarni": "ai", "в сфере ии": "ai",
    "tibbiyotda": "medicine", "medicine": "medicine", "в медицине": "medicine",
    "iqtisodda": "economics", "iqtisodiyotda": "economics", "economics": "economics", "в экономике": "economics",
    "sportda": "sports", "sports": "sports", "в спорте": "sports",
    "huquqda": "law", "law": "law", "в праве": "law",
}  # fmt: skip

# Words that signal a natural-language question (and are removed when extracting the term).
CUES: dict[str, str] = {
    # uz
    "so'zining": "uz", "so'zi": "uz", "so'zini": "uz", "ma'nosi": "uz", "ma'nosini": "uz", "nima": "uz",
    "degani": "uz", "nimani": "uz", "anglatadi": "uz", "tarjimasi": "uz", "tarjima": "uz", "qanday": "uz",
    "bo'ladi": "uz", "deyiladi": "uz", "izohi": "uz",
    # en
    "what": "en", "does": "en", "mean": "en", "means": "en", "meaning": "en", "translate": "en",
    "translation": "en", "define": "en", "definition": "en",
    # ru
    "что": "ru", "значит": "ru", "означает": "ru", "перевод": "ru", "переведи": "ru", "как": "ru",
}  # fmt: skip
WEAK_FILLERS = {
    "of", "is", "the", "a", "in", "into", "to", "word", "how", "do", "you", "say", "please",
    "это", "слово", "слова", "будет", "по", "ga", "da",
}  # fmt: skip

_NEW_TERMS = re.compile(
    r"(yangi|chiqqan|paydo bo'lgan).*(termin|atama|so'zlar)|new (ai )?(terms|words)|новые (термины|слова)"
)
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_QUOTED = re.compile(r"[\"“”«»„](.+?)[\"“”«»„]")
_TRAILING = re.compile(r"[?!.]+$")


def _find_phrases(q: str, table: dict[str, str]) -> list[tuple[str, str]]:
    found = []
    for phrase in sorted(table, key=len, reverse=True):
        if re.search(rf"(?<![\w']){re.escape(phrase)}(?![\w'])", q):
            found.append((phrase, table[phrase]))
            q = q.replace(phrase, " ")
    return found


def parse_intent_rules(query: str) -> tuple[Intent, bool]:
    """Returns (intent, is_natural_language)."""
    q = _TRAILING.sub("", clean(query).lower()).strip()
    langs = _find_phrases(q, LANGUAGE_WORDS)
    domains = _find_phrases(q, DOMAIN_WORDS)
    domain = domains[0][1] if domains else None

    if _NEW_TERMS.search(q):
        year_match = _YEAR.search(q)
        return Intent(
            type="list_new_terms", domain=domain, year=int(year_match.group()) if year_match else None
        ), True

    tokens = q.split()
    cue_langs = [CUES[t] for t in tokens if t in CUES]
    is_nl = len(tokens) > 1 and bool(cue_langs or langs or domains)
    if not is_nl:
        return Intent(term=clean(query)), False

    quoted = _QUOTED.search(clean(query))
    if quoted:
        term = quoted.group(1).strip()
    else:
        rest = q
        for phrase, _ in langs + domains:
            rest = re.sub(rf"(?<![\w']){re.escape(phrase)}(?![\w'])", " ", rest)
        kept = [t for t in rest.split() if t not in CUES and t not in WEAK_FILLERS and not _YEAR.fullmatch(t)]
        term = " ".join(kept).strip("'\" ") or clean(query)

    target = langs[0][1] if langs else (cue_langs[0] if cue_langs else None)
    translate_markers = ("tilida", "tiliga", "по-", "на ", "translate", "перевод", "переведи")
    kind: IntentType = "translate" if langs and any(m in q for m in translate_markers) else "lookup"
    return Intent(type=kind, term=term, target_lang=target, domain=domain), True


def needs_llm(intent: Intent, is_nl: bool) -> bool:
    if intent.type != "lookup" and intent.type != "translate":
        return False
    words = len((intent.term or "").split())
    return (is_nl and words >= 3) or (not is_nl and words >= 5)
