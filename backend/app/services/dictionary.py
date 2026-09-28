"""Reading, writing and serializing dictionary entries."""

import uuid
from collections import defaultdict
from collections.abc import Iterable, Sequence
from urllib.parse import quote

from sqlalchemy import delete, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Example,
    Pronunciation,
    SenseDefinition,
    Source,
    Translation,
    Word,
    WordForm,
    WordRelation,
    WordSense,
    WordSource,
    WordVersion,
)
from app.models.enums import VISIBLE_STATUSES, RelationType
from app.schemas.entry import (
    ExampleIn,
    ExampleOut,
    FormIn,
    FormOut,
    LinkOut,
    PrimaryTranslation,
    PronunciationIn,
    PronunciationOut,
    SenseIn,
    SenseOut,
    SourceOut,
    TranslationIn,
    TranslationOut,
    WordEntry,
    WordEntryIn,
    WordSummary,
)
from app.services.normalization import normalize

ENTRY_OPTIONS = (
    selectinload(Word.senses).selectinload(WordSense.definitions),
    selectinload(Word.senses).selectinload(WordSense.translations),
    selectinload(Word.senses).selectinload(WordSense.examples),
    selectinload(Word.forms),
    selectinload(Word.pronunciations),
    selectinload(Word.relations),
    selectinload(Word.source_links),
)
SUMMARY_OPTIONS = (
    selectinload(Word.senses).selectinload(WordSense.definitions),
    selectinload(Word.senses).selectinload(WordSense.translations),
)

KNOWN_SOURCES: dict[str, dict[str, object]] = {
    "wiktionary": {"name": "Wiktionary", "type": "dataset", "url": "https://www.wiktionary.org",
                   "license": "CC BY-SA 4.0", "reliability": 0.9},
    "gemini": {"name": "Google Gemini (AI)", "type": "ai", "reliability": 0.6},
    "editor": {"name": "Lexora muharrirlari", "type": "editor", "reliability": 1.0},
    "demo-seed": {"name": "Lexora demo lug‘ati", "type": "editor", "license": "CC BY-SA 4.0", "reliability": 0.9},
}  # fmt: skip


async def get_source(session: AsyncSession, code: str) -> Source:
    source = await session.scalar(select(Source).where(Source.code == code))
    if source is None:
        meta = KNOWN_SOURCES.get(code, {"name": code, "type": "web", "reliability": 0.5})
        source = Source(code=code, **meta)
        session.add(source)
        await session.flush()
    return source


# ---------- lookups ----------


async def load_word(session: AsyncSession, word_id: int) -> Word | None:
    stmt = (
        select(Word)
        .options(*ENTRY_OPTIONS)
        .where(Word.id == word_id)
        .execution_options(populate_existing=True)
    )
    return await session.scalar(stmt)


async def find_word(session: AsyncSession, lang: str, slug: str, visible_only: bool = True) -> Word | None:
    stmt = (
        select(Word)
        .options(*ENTRY_OPTIONS)
        .where(Word.language_code == lang, Word.normalized == normalize(slug, lang))
    )
    if visible_only:
        stmt = stmt.where(Word.status.in_(VISIBLE_STATUSES))
    return await session.scalar(stmt)


async def existing_keys(session: AsyncSession, pairs: Iterable[tuple[str, str]]) -> set[tuple[str, str]]:
    """Which (language_code, normalized) pairs exist as visible entries."""
    wanted = {p for p in pairs if p[1]}
    if not wanted:
        return set()
    stmt = select(Word.language_code, Word.normalized).where(
        tuple_(Word.language_code, Word.normalized).in_(list(wanted)), Word.status.in_(VISIBLE_STATUSES)
    )
    return {(lang, key) for lang, key in (await session.execute(stmt)).all()}


# ---------- serialization ----------


def audio_url(text: str, lang: str, accent: str | None = None) -> str:
    url = f"/api/v1/tts?text={quote(text)}&lang={lang}"
    return f"{url}&accent={quote(accent)}" if accent else url


def _link(text: str, lang: str, known: set[tuple[str, str]]) -> LinkOut:
    key = normalize(text, lang)
    return LinkOut(text=text, slug=key if (lang, key) in known else None)


async def build_entry(session: AsyncSession, word: Word, is_favorite: bool = False) -> WordEntry:
    lang = word.language_code
    pairs: set[tuple[str, str]] = {(lang, normalize(r.target_text, lang)) for r in word.relations}
    for sense in word.senses:
        pairs |= {(t.target_language, t.normalized) for t in sense.translations}
    known = await existing_keys(session, pairs)

    by_sense: dict[int | None, list[WordRelation]] = defaultdict(list)
    for rel in word.relations:
        by_sense[rel.sense_id].append(rel)

    senses = []
    for sense in word.senses:
        translations: dict[str, list[TranslationOut]] = defaultdict(list)
        for t in sense.translations:
            translations[t.target_language].append(
                TranslationOut(
                    text=t.text,
                    is_primary=t.is_primary,
                    note=t.note,
                    slug=t.normalized if (t.target_language, t.normalized) in known else None,
                )
            )
        rels = by_sense.get(sense.id, [])
        senses.append(
            SenseOut(
                id=sense.id,
                pos=sense.pos,
                domain=sense.domain,
                register=sense.register,
                cefr_level=sense.cefr_level,
                definitions={d.language_code: d.text for d in sense.definitions},
                translations=dict(translations),
                examples=[ExampleOut(text=e.text, translations=e.translations or {}) for e in sense.examples],
                synonyms=[_link(r.target_text, lang, known) for r in rels if r.relation_type == "synonym"],
                antonyms=[_link(r.target_text, lang, known) for r in rels if r.relation_type == "antonym"],
            )
        )

    relations: dict[str, list[LinkOut]] = {t.value: [] for t in RelationType}
    seen: set[tuple[str, str]] = set()
    for rel in word.relations:
        if (rel.relation_type, rel.target_text) in seen:
            continue
        seen.add((rel.relation_type, rel.target_text))
        relations[rel.relation_type].append(_link(rel.target_text, lang, known))

    sources = []
    if word.source:
        sources.append(SourceOut(name=word.source.name, url=word.source.url, license=word.source.license))
    for link in word.source_links:
        if word.source and link.source_id == word.source.id and not link.external_ref:
            continue
        sources.append(
            SourceOut(
                name=link.source.name, url=link.external_ref or link.source.url, license=link.source.license
            )
        )
    # Keep one line per source name, preferring the one with a specific URL.
    unique: dict[str, SourceOut] = {}
    for s in sources:
        if s.name not in unique or (s.url and s.url != unique[s.name].url):
            unique[s.name] = s

    return WordEntry(
        id=word.id,
        language_code=lang,
        lemma=word.lemma,
        slug=word.normalized,
        entry_type=word.entry_type,
        status=word.status,
        confidence=word.confidence,
        cefr_level=word.cefr_level,
        frequency_zipf=word.frequency_zipf,
        tags=list(word.tags or []),
        etymology=word.etymology,
        audio_url=audio_url(word.lemma, lang),
        pronunciations=[
            PronunciationOut(ipa=p.ipa, accent=p.accent, audio_url=audio_url(word.lemma, lang, p.accent))
            for p in word.pronunciations
        ],
        forms=[FormOut(form=f.form, tags=list(f.tags or [])) for f in word.forms],
        senses=senses,
        relations=relations,
        sources=list(unique.values()),
        is_favorite=is_favorite,
        version=word.version,
        updated_at=word.updated_at,
    )


def default_target(word_lang: str, requested: str | None) -> str:
    if requested and requested != word_lang:
        return requested
    return "uz" if word_lang != "uz" else "en"


def summarize(
    word: Word, target_lang: str | None = None, explain_lang: str | None = None, match: str | None = None
) -> WordSummary:
    target = default_target(word.language_code, target_lang)
    order = [explain_lang or "uz", "uz", "en", word.language_code]
    short_definition = None
    for lang in order:
        short_definition = next(
            (d.text for s in word.senses for d in s.definitions if d.language_code == lang), None
        )
        if short_definition:
            break
    primary = None
    for sense in word.senses:
        candidates = [t for t in sense.translations if t.target_language == target]
        if candidates:
            best = next((t for t in candidates if t.is_primary), candidates[0])
            primary = PrimaryTranslation(language_code=target, text=best.text)
            break
    pos: list[str] = []
    for s in word.senses:
        if s.pos not in pos:
            pos.append(s.pos)
    return WordSummary(
        id=word.id,
        language_code=word.language_code,
        lemma=word.lemma,
        slug=word.normalized,
        entry_type=word.entry_type,
        status=word.status,
        confidence=word.confidence,
        pos=pos,
        cefr_level=word.cefr_level,
        short_definition=short_definition,
        primary_translation=primary,
        match=match,
    )


async def summaries(
    session: AsyncSession,
    ids: Sequence[int],
    target_lang: str | None = None,
    explain_lang: str | None = None,
    matches: dict[int, str] | None = None,
    visible_only: bool = True,
) -> list[WordSummary]:
    if not ids:
        return []
    stmt = select(Word).options(*SUMMARY_OPTIONS).where(Word.id.in_(list(ids)))
    if visible_only:
        stmt = stmt.where(Word.status.in_(VISIBLE_STATUSES))
    words = {w.id: w for w in (await session.scalars(stmt)).all()}
    matches = matches or {}
    return [summarize(words[i], target_lang, explain_lang, matches.get(i)) for i in ids if i in words]


def to_entry_in(word: Word) -> WordEntryIn:
    by_sense: dict[int | None, list[WordRelation]] = defaultdict(list)
    for rel in word.relations:
        by_sense[rel.sense_id].append(rel)
    senses = []
    for sense in word.senses:
        translations: dict[str, list[TranslationIn]] = defaultdict(list)
        for t in sense.translations:
            translations[t.target_language].append(
                TranslationIn(text=t.text, is_primary=t.is_primary, note=t.note)
            )
        rels = by_sense.get(sense.id, [])
        senses.append(
            SenseIn(
                pos=sense.pos,
                domain=sense.domain,
                register=sense.register,
                cefr_level=sense.cefr_level,
                definitions={d.language_code: d.text for d in sense.definitions},
                translations=dict(translations),
                examples=[ExampleIn(text=e.text, translations=e.translations or {}) for e in sense.examples],
                synonyms=[r.target_text for r in rels if r.relation_type == "synonym"],
                antonyms=[r.target_text for r in rels if r.relation_type == "antonym"],
            )
        )
    relations: dict[RelationType, list[str]] = defaultdict(list)
    for rel in by_sense.get(None, []):
        relations[RelationType(rel.relation_type)].append(rel.target_text)
    return WordEntryIn(
        lemma=word.lemma,
        entry_type=word.entry_type,
        cefr_level=word.cefr_level,
        frequency_zipf=word.frequency_zipf,
        tags=list(word.tags or []),
        etymology=word.etymology,
        pronunciations=[PronunciationIn(ipa=p.ipa, accent=p.accent) for p in word.pronunciations],
        forms=[FormIn(form=f.form, tags=list(f.tags or [])) for f in word.forms],
        senses=senses,
        relations=dict(relations),
    )


# ---------- writing ----------


async def apply_entry(
    session: AsyncSession,
    word: Word,
    entry: WordEntryIn,
    *,
    source_id: int | None = None,
    confidence: float | None = None,
    example_source: str | None = None,
) -> Word:
    """Replace the whole content of `word` with `entry`. Returns the reloaded word."""
    lang = word.language_code
    word.lemma = entry.lemma
    word.normalized = normalize(entry.lemma, lang)
    word.entry_type = entry.entry_type
    word.cefr_level = entry.cefr_level
    word.frequency_zipf = entry.frequency_zipf
    word.tags = sorted({t.strip().lower() for t in entry.tags if t.strip()})
    word.etymology = {k: v for k, v in (entry.etymology or {}).items() if v} or None
    if source_id is not None:
        word.source_id = source_id
    if confidence is not None:
        word.confidence = confidence

    if word.id is None:
        session.add(word)
        await session.flush()
    else:
        for model in (WordRelation, WordSense, WordForm, Pronunciation):
            await session.execute(delete(model).where(model.word_id == word.id))

    objects: list[object] = []
    for order, s in enumerate(entry.senses):
        sense = WordSense(
            word_id=word.id,
            sense_order=order,
            pos=s.pos.strip().lower(),
            domain=s.domain,
            register=s.register,
            cefr_level=s.cefr_level,
            status=word.status,
            confidence=word.confidence,
            source_id=word.source_id,
        )
        sense.definitions = [
            SenseDefinition(language_code=code, text=text.strip())
            for code, text in s.definitions.items()
            if text.strip()
        ]
        sense.translations = [
            Translation(
                target_language=code,
                text=t.text.strip(),
                normalized=normalize(t.text, code),
                is_primary=t.is_primary,
                note=t.note,
                confidence=word.confidence,
                source_id=word.source_id,
            )
            for code, items in s.translations.items()
            for t in items
            if t.text.strip()
        ]
        sense.examples = [
            Example(text=e.text.strip(), translations=e.translations, source=example_source)
            for e in s.examples
        ]
        objects.append(sense)
        for rel_type, targets in ((RelationType.SYNONYM, s.synonyms), (RelationType.ANTONYM, s.antonyms)):
            objects.extend(
                WordRelation(
                    word_id=word.id, sense=sense, relation_type=rel_type.value, target_text=t.strip()
                )
                for t in dict.fromkeys(targets)
                if t.strip()
            )
    for rel_type, targets in entry.relations.items():
        objects.extend(
            WordRelation(word_id=word.id, relation_type=RelationType(rel_type).value, target_text=t.strip())
            for t in dict.fromkeys(targets)
            if t.strip()
        )
    seen_forms: set[str] = set()
    for f in entry.forms:
        key = normalize(f.form, lang)
        if key and key != word.normalized and key not in seen_forms:
            seen_forms.add(key)
            objects.append(WordForm(word_id=word.id, form=f.form.strip(), normalized=key, tags=f.tags))
    objects.extend(
        Pronunciation(word_id=word.id, ipa=p.ipa, accent=p.accent)
        for p in entry.pronunciations
        if p.ipa or p.accent
    )
    session.add_all(objects)
    await session.flush()
    reloaded = await load_word(session, word.id)
    assert reloaded is not None
    return reloaded


async def add_source_link(
    session: AsyncSession, word: Word, source: Source, external_ref: str | None = None
) -> None:
    exists = await session.scalar(
        select(WordSource.id).where(WordSource.word_id == word.id, WordSource.source_id == source.id)
    )
    if not exists:
        session.add(WordSource(word_id=word.id, source_id=source.id, external_ref=external_ref))


def snapshot(word: Word) -> dict[str, object]:
    data = to_entry_in(word).model_dump(mode="json")
    data.update({"status": word.status, "confidence": word.confidence, "language_code": word.language_code})
    return data


async def save_version(
    session: AsyncSession, word: Word, reason: str, user_id: uuid.UUID | None = None
) -> WordVersion:
    version = WordVersion(
        word_id=word.id,
        version=word.version,
        snapshot=snapshot(word),
        changed_by=user_id,
        reason=reason[:200],
    )
    session.add(version)
    await session.flush()
    return version


async def create_entry(
    session: AsyncSession,
    lang: str,
    entry: WordEntryIn,
    *,
    status: str,
    source_code: str,
    confidence: float | None = None,
    reason: str = "create",
    user_id: uuid.UUID | None = None,
    external_ref: str | None = None,
    example_source: str | None = None,
) -> Word:
    source = await get_source(session, source_code)
    word = Word(language_code=lang, lemma=entry.lemma, normalized=normalize(entry.lemma, lang), status=status)
    word = await apply_entry(
        session, word, entry, source_id=source.id, confidence=confidence, example_source=example_source
    )
    await add_source_link(session, word, source, external_ref)
    await save_version(session, word, reason, user_id)
    return word


async def update_entry(
    session: AsyncSession,
    word: Word,
    entry: WordEntryIn,
    *,
    reason: str,
    user_id: uuid.UUID | None = None,
    status: str | None = None,
    source_code: str | None = None,
    confidence: float | None = None,
) -> Word:
    word.version += 1
    if status:
        word.status = status
    source_id = None
    if source_code:
        source = await get_source(session, source_code)
        source_id = source.id
        await add_source_link(session, word, source)
    word = await apply_entry(session, word, entry, source_id=source_id, confidence=confidence)
    await save_version(session, word, reason, user_id)
    return word


async def set_status(
    session: AsyncSession, word: Word, status: str, *, reason: str, user_id: uuid.UUID | None = None
) -> Word:
    word.status = status
    word.version += 1
    for sense in word.senses:
        sense.status = status
    await session.flush()
    await save_version(session, word, reason, user_id)
    return word
