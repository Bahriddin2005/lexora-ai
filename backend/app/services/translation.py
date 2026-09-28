"""Translation: dictionary first (free, exact), LLM otherwise (cached in ai_generations)."""

import uuid

from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import agents, prompts
from app.ai.provider import LLMProvider, ModelTier
from app.ai.schemas import TranslationResult
from app.core.config import TRANSLATE_MAX_CHARS
from app.core.errors import AppError, ai_unavailable, bad_request
from app.services import dictionary, quotas, search
from app.services.languages import active_languages
from app.services.normalization import tokens


class DictionaryRef(BaseModel):
    language_code: str
    slug: str
    lemma: str


class TranslateOut(BaseModel):
    translation: str
    detected_source: str | None
    alternatives: list[str] = Field(default_factory=list)
    notes: str | None = None
    dictionary: DictionaryRef | None = None
    cached: bool = False


async def from_dictionary(session: AsyncSession, text: str, source: str, target: str) -> TranslateOut | None:
    active = await active_languages(session)
    langs = search.candidate_languages(text, active, None if source == "auto" else source)
    langs = [lang for lang in langs if lang != target]
    hits = [h for h in await search.lookup(session, text, langs) if h[1] in ("exact", "form")]
    if not hits:
        return None
    word = await dictionary.load_word(session, hits[0][0])
    if word is None:
        return None
    options = [t for sense in word.senses for t in sense.translations if t.target_language == target]
    if not options:
        return None
    primary = next((t for t in options if t.is_primary), options[0])
    alternatives = list(dict.fromkeys(t.text for t in options if t.text != primary.text))[:3]
    return TranslateOut(
        translation=primary.text,
        detected_source=word.language_code,
        alternatives=alternatives,
        dictionary=DictionaryRef(language_code=word.language_code, slug=word.normalized, lemma=word.lemma),
    )


async def translate(
    session: AsyncSession,
    redis: Redis,
    provider: LLMProvider | None,
    *,
    text: str,
    source: str,
    target: str,
    context: str | None,
    subject: quotas.Subject,
    user_id: uuid.UUID | None,
) -> TranslateOut:
    text = text.strip()
    if not text:
        raise bad_request("Matn bo‘sh")
    max_chars = TRANSLATE_MAX_CHARS.get(subject.plan, 1000) if not subject.unlimited else 20_000
    if len(text) > max_chars:
        raise AppError(
            400, "text_too_long", f"Matn juda uzun (maksimal {max_chars} belgi)", {"max": max_chars}
        )
    if source == target:
        raise bad_request("Manba va maqsad tillari bir xil")

    if len(tokens(text)) <= 3 and not context:
        found = await from_dictionary(session, text, source, target)
        if found:
            return found

    if provider is None:
        raise ai_unavailable()
    inputs = {"text": text, "source": source, "target": target, "context": context}
    digest = agents.input_hash(prompts.TRANSLATE, provider.model_name(ModelTier.FAST), inputs)
    hit = await agents.cached_output(session, digest)
    if hit and hit.output:
        return TranslateOut(**TranslationResult.model_validate(hit.output).model_dump(), cached=True)

    await quotas.consume(redis, subject, "translate_chars", len(text))
    result = await agents.translate(
        session, provider, text=text, source=source, target=target, context=context, user_id=user_id
    )
    await session.commit()
    return TranslateOut(**result.model_dump())
