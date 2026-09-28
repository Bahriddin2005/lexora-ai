"""Import Wiktionary data from kaikki.org (Wiktextract JSONL, CC BY-SA 4.0).

Each JSONL line is one (word, part of speech) entry. Lines are grouped per (language, word) into a single
Lexora entry; translations are attached to the sense whose gloss best matches the translation's sense label.
"""

import json
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Word
from app.models.enums import ContentStatus
from app.schemas.entry import ExampleIn, FormIn, PronunciationIn, SenseIn, TranslationIn, WordEntryIn
from app.services import dictionary
from app.services.normalization import normalize

POS_MAP = {
    "noun": "noun", "verb": "verb", "adj": "adj", "adv": "adv", "name": "proper_noun", "pron": "pron",
    "prep": "prep", "conj": "conj", "intj": "interj", "num": "num", "phrase": "phrase", "prep_phrase": "phrase",
    "abbrev": "noun", "det": "det", "particle": "particle", "suffix": "suffix", "prefix": "prefix",
}  # fmt: skip
REGISTER_TAGS = {"slang": "slang", "informal": "informal", "colloquial": "informal", "formal": "formal",
                 "vulgar": "vulgar", "archaic": "archaic", "obsolete": "archaic"}  # fmt: skip
TOPIC_DOMAINS = {"computing": "computing", "programming": "computing", "medicine": "medicine", "sports": "sports",
                 "law": "law", "economics": "economics", "finance": "economics", "business": "business",
                 "artificial-intelligence": "ai", "machine-learning": "ai"}  # fmt: skip
FORM_SKIP_TAGS = {
    "table-tags",
    "inflection-template",
    "class",
    "romanization",
    "canonical",
    "multiword-construction",
}
_WORD_RE = re.compile(r"[\w']+")


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def group_entries(
    lines: Iterable[dict[str, Any]], langs: set[str]
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for raw in lines:
        lang = raw.get("lang_code")
        if lang in langs and raw.get("word"):
            groups.setdefault((lang, raw["word"]), []).append(raw)
    return groups


def _is_form_of(sense: dict[str, Any]) -> bool:
    tags = set(sense.get("tags", []))
    return bool(sense.get("form_of") or sense.get("alt_of")) or "form-of" in tags or "alt-of" in tags


def _gloss(sense: dict[str, Any]) -> str | None:
    glosses = sense.get("glosses") or sense.get("raw_glosses") or []
    return glosses[-1].strip() if glosses else None


def _overlap(a: str, b: str) -> int:
    return len(set(_WORD_RE.findall(a.lower())) & set(_WORD_RE.findall(b.lower())))


def _accent(tags: list[str]) -> str | None:
    tagset = set(tags)
    if tagset & {"US", "General-American"}:
        return "US"
    if tagset & {"UK", "Received-Pronunciation"}:
        return "UK"
    return None


def to_entry(
    word: str, raws: list[dict[str, Any]], lang: str, allowed: set[str], max_senses: int = 8
) -> WordEntryIn | None:
    senses: list[SenseIn] = []
    glosses: list[tuple[int, str, str]] = []  # (sense index, pos, gloss) for translation matching
    relations: dict[str, list[str]] = {"derived": [], "related": [], "synonym": [], "antonym": []}
    forms: list[FormIn] = []
    pronunciations: list[PronunciationIn] = []
    etymology = None

    for raw in raws:
        pos = POS_MAP.get(raw.get("pos", ""), raw.get("pos", "noun"))[:24]
        pos_start = len(senses)
        for s in raw.get("senses", []):
            if len(senses) >= max_senses:
                break
            gloss = _gloss(s)
            if not gloss or _is_form_of(s):
                continue
            tags = s.get("tags", [])
            register = next((REGISTER_TAGS[t] for t in tags if t in REGISTER_TAGS), "neutral")
            domain = next((TOPIC_DOMAINS[t] for t in s.get("topics", []) if t in TOPIC_DOMAINS), None)
            examples = []
            for ex in s.get("examples", [])[:2]:
                text = (ex.get("text") or "").strip()
                if text and len(text) < 400:
                    translated = ex.get("english") or ex.get("translation")
                    examples.append(
                        ExampleIn(text=text, translations={"en": translated} if translated else {})
                    )
            translations: dict[str, list[TranslationIn]] = {}
            if lang != "en" and "en" in allowed and len(gloss.split()) <= 4:
                translations["en"] = [TranslationIn(text=gloss.rstrip("."), is_primary=True)]
            senses.append(
                SenseIn(
                    pos=pos,
                    domain=domain,
                    register=register,
                    definitions={"en": gloss},
                    translations=translations,
                    examples=examples,
                    synonyms=[x["word"] for x in s.get("synonyms", []) if x.get("word")][:8],
                    antonyms=[x["word"] for x in s.get("antonyms", []) if x.get("word")][:8],
                )
            )
            glosses.append((len(senses) - 1, pos, gloss))

        for t in raw.get("translations", []):
            code = t.get("code") or t.get("lang_code")
            text = (t.get("word") or "").strip()
            if code not in allowed or code == lang or not text:
                continue
            candidates = [g for g in glosses if g[0] >= pos_start]
            if not candidates:
                continue
            label = t.get("sense") or ""
            index = (
                max(candidates, key=lambda g: (_overlap(label, g[2]), -g[0]))[0]
                if label
                else candidates[0][0]
            )
            items = senses[index].translations.setdefault(code, [])
            if text not in [i.text for i in items] and len(items) < 5:
                items.append(TranslationIn(text=text[:300], is_primary=not items))

        for key in ("derived", "related", "synonyms", "antonyms"):
            target = key.rstrip("s") if key in ("synonyms", "antonyms") else key
            relations[target].extend(x["word"] for x in raw.get(key, []) if x.get("word"))
        for f in raw.get("forms", []):
            tags = set(f.get("tags", []))
            text = (f.get("form") or "").strip()
            if text and text != word and not tags & FORM_SKIP_TAGS and len(forms) < 12:
                forms.append(FormIn(form=text[:200], tags=sorted(tags)[:4]))
        for snd in raw.get("sounds", []):
            if snd.get("ipa") and len(pronunciations) < 3:
                accent = _accent(snd.get("tags", []))
                if accent not in [p.accent for p in pronunciations]:
                    pronunciations.append(PronunciationIn(ipa=snd["ipa"][:200], accent=accent))
        if not etymology and raw.get("etymology_text"):
            etymology = {"en": raw["etymology_text"].strip()[:1500]}

    if not senses:
        return None
    return WordEntryIn(
        lemma=word[:200],
        entry_type="proper_noun"
        if all(s.pos == "proper_noun" for s in senses)
        else ("phrase" if " " in word else "word"),
        etymology=etymology,
        pronunciations=pronunciations,
        forms=forms,
        senses=senses,
        relations={k: list(dict.fromkeys(v))[:10] for k, v in relations.items() if v},
    )


def zipf(word: str, lang: str) -> float | None:
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return None
    try:
        value = zipf_frequency(word, lang)
    except LookupError:
        return None
    return round(value, 2) if value > 0 else None


async def import_entries(
    session: AsyncSession,
    lines: Iterable[dict[str, Any]],
    langs: set[str],
    *,
    limit: int | None = None,
    min_zipf: float | None = None,
    allowed_targets: set[str] | None = None,
) -> dict[str, int]:
    stats = {"created": 0, "skipped_existing": 0, "skipped_empty": 0, "skipped_rare": 0}
    groups = group_entries(lines, langs)
    ranked = sorted(groups.items(), key=lambda kv: -(zipf(kv[0][1], kv[0][0]) or 0))
    targets = allowed_targets or {"uz", "en", "ru", "tr"}
    for (lang, word), raws in ranked:
        if limit is not None and stats["created"] >= limit:
            break
        freq = zipf(word, lang)
        if min_zipf is not None and freq is not None and freq < min_zipf:
            stats["skipped_rare"] += 1
            continue
        if await session.scalar(
            select(Word.id).where(Word.language_code == lang, Word.normalized == normalize(word, lang))
        ):
            stats["skipped_existing"] += 1
            continue
        entry = to_entry(word, raws, lang, targets)
        if entry is None:
            stats["skipped_empty"] += 1
            continue
        entry.frequency_zipf = freq
        await dictionary.create_entry(
            session, lang, entry, status=ContentStatus.PUBLISHED, source_code="wiktionary", confidence=0.9,
            reason="import:kaikki", external_ref=f"https://en.wiktionary.org/wiki/{quote(word)}",
            example_source="dataset",
        )  # fmt: skip
        stats["created"] += 1
        if stats["created"] % 200 == 0:
            await session.commit()
    await session.commit()
    return stats
