"""Dictionary search on PostgreSQL: exact → forms → reverse (translations) → prefix → trigram suggestions."""

import re
from dataclasses import dataclass

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SearchLog, Translation, Word, WordForm, WordSense
from app.models.enums import VISIBLE_STATUSES
from app.services.languages import LanguageInfo, candidates_for_script
from app.services.normalization import detect_script, normalize, tokens

MATCH_RANK = {"exact": 0, "form": 1, "reverse": 2, "prefix": 3}
MAX_RESULTS = 20
_WORDLIKE = re.compile(r"^[^\W\d_]+(?:['\- ][^\W\d_]+)*'?$")


@dataclass
class Suggestion:
    language_code: str
    lemma: str
    slug: str
    score: float


def candidate_languages(term: str, active: list[LanguageInfo], source: str | None) -> list[str]:
    codes = [lang.code for lang in active]
    if source and source in codes:
        return [source]
    langs = candidates_for_script(active, detect_script(term))
    return langs or codes


def keys_for(term: str, langs: list[str]) -> dict[str, str]:
    keys = {lang: normalize(term, lang) for lang in langs}
    return {lang: key for lang, key in keys.items() if key}


def looks_like_word(term: str) -> bool:
    """Gate for AI generation: 1-4 tokens of letters (apostrophes/hyphens allowed), 2-60 chars."""
    t = normalize(term)
    return 2 <= len(t) <= 60 and len(tokens(t)) <= 4 and bool(_WORDLIKE.match(t))


def _like_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def lookup(session: AsyncSession, term: str, langs: list[str]) -> list[tuple[int, str]]:
    keys = keys_for(term, langs)
    if not keys:
        return []
    visible = Word.status.in_(VISIBLE_STATUSES)
    found: dict[int, tuple[int, float, int]] = {}  # id -> (rank, -freq, lang order)
    order = {lang: i for i, lang in enumerate(langs)}

    def add(rows, match: str) -> None:
        for word_id, freq, lang in rows:
            rank = (MATCH_RANK[match], -(freq or 0.0), order.get(lang, 99))
            if word_id not in found or rank < found[word_id]:
                found[word_id] = rank

    cols = (Word.id, Word.frequency_zipf, Word.language_code)
    exact = or_(*[and_(Word.language_code == lang, Word.normalized == key) for lang, key in keys.items()])
    add((await session.execute(select(*cols).where(exact, visible))).all(), "exact")

    forms = or_(*[and_(Word.language_code == lang, WordForm.normalized == key) for lang, key in keys.items()])
    stmt = select(*cols).join(WordForm, WordForm.word_id == Word.id).where(forms, visible).distinct()
    add((await session.execute(stmt)).all(), "form")

    reverse = or_(
        *[
            and_(Translation.target_language == lang, Translation.normalized == key)
            for lang, key in keys.items()
        ]
    )
    stmt = (
        select(*cols)
        .join(WordSense, WordSense.word_id == Word.id)
        .join(Translation, Translation.sense_id == WordSense.id)
        .where(reverse, visible)
        .distinct()
    )
    add((await session.execute(stmt)).all(), "reverse")

    if len(found) < 5:
        prefix = or_(
            *[
                and_(Word.language_code == lang, Word.normalized.like(_like_escape(key) + "%"))
                for lang, key in keys.items()
                if len(key) >= 2
            ]
        )
        stmt = (
            select(*cols)
            .where(prefix, visible, Word.id.not_in(list(found) or [0]))
            .order_by(Word.frequency_zipf.desc().nulls_last(), func.length(Word.normalized))
            .limit(8)
        )
        add((await session.execute(stmt)).all(), "prefix")

    ranked = sorted(found.items(), key=lambda item: item[1])[:MAX_RESULTS]
    rank_to_match = {v: k for k, v in MATCH_RANK.items()}
    return [(word_id, rank_to_match[rank[0]]) for word_id, rank in ranked]


async def did_you_mean(
    session: AsyncSession, term: str, langs: list[str], limit: int = 5
) -> list[Suggestion]:
    by_key: dict[str, list[str]] = {}
    for lang, key in keys_for(term, langs).items():
        by_key.setdefault(key, []).append(lang)
    suggestions: dict[tuple[str, str], Suggestion] = {}
    for key, key_langs in by_key.items():
        similarity = func.similarity(Word.normalized, key)
        stmt = (
            select(Word.language_code, Word.lemma, Word.normalized, similarity.label("score"))
            .where(
                Word.language_code.in_(key_langs),
                Word.status.in_(VISIBLE_STATUSES),
                Word.normalized.op("%")(key),
                Word.normalized != key,
            )
            .order_by(similarity.desc(), Word.frequency_zipf.desc().nulls_last())
            .limit(limit)
        )
        for lang, lemma, normalized, score in (await session.execute(stmt)).all():
            suggestions[(lang, normalized)] = Suggestion(lang, lemma, normalized, round(float(score), 3))
    return sorted(suggestions.values(), key=lambda s: -s.score)[:limit]


async def prefix_suggest(session: AsyncSession, q: str, langs: list[str], limit: int = 8) -> list[int]:
    keys = {lang: key for lang, key in keys_for(q, langs).items() if key}
    if not keys:
        return []
    prefix = or_(
        *[
            and_(Word.language_code == lang, Word.normalized.like(_like_escape(key) + "%"))
            for lang, key in keys.items()
        ]
    )
    stmt = (
        select(Word.id)
        .where(prefix, Word.status.in_(VISIBLE_STATUSES))
        .order_by(func.length(Word.normalized), Word.frequency_zipf.desc().nulls_last())
        .limit(limit)
    )
    return list((await session.scalars(stmt)).all())


async def list_new_terms(
    session: AsyncSession, domain: str | None, year: int | None, lang: str | None = None, limit: int = 30
) -> list[int]:
    stmt = select(Word.id).where(Word.status.in_(VISIBLE_STATUSES))
    if domain:
        has_domain = (
            select(WordSense.id).where(WordSense.word_id == Word.id, WordSense.domain == domain).exists()
        )
        stmt = stmt.where(or_(Word.tags.contains([domain]), has_domain))
    if year:
        stmt = stmt.where(func.extract("year", Word.first_seen_at) == year)
    if lang:
        stmt = stmt.where(Word.language_code == lang)
    stmt = stmt.order_by(Word.first_seen_at.desc(), Word.id.desc()).limit(limit)
    return list((await session.scalars(stmt)).all())


async def log_search(
    session: AsyncSession,
    *,
    query: str,
    normalized: str,
    language_code: str | None,
    target_language: str | None,
    intent: str,
    found: bool,
    result_word_id: int | None,
    user_id=None,
) -> None:
    session.add(
        SearchLog(
            user_id=user_id,
            query=query[:300],
            normalized=normalized[:300],
            language_code=language_code,
            target_language=target_language,
            intent=intent,
            found=found,
            result_word_id=result_word_id,
        )
    )
