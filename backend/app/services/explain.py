"""'AI bilan tushunish': streamed explanations, cached in ai_generations."""

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai import agents, prompts
from app.ai.provider import AIError, LLMProvider, ModelTier
from app.schemas.entry import WordEntry


def sse(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def explain_inputs(entry: WordEntry, lang: str, level: str, question: str | None) -> dict[str, Any]:
    compact = {
        "lemma": entry.lemma,
        "language": entry.language_code,
        "senses": [
            {
                "pos": s.pos,
                "domain": s.domain,
                "register": s.register,
                "definitions": s.definitions,
                "translations": {k: [t.text for t in v] for k, v in s.translations.items()},
                "examples": [e.text for e in s.examples[:2]],
            }
            for s in entry.senses
        ],
    }
    return {
        "word_id": entry.id,
        "version": entry.version,
        "explain_lang": prompts.LANG_NAMES.get(lang, lang),
        "level": level,
        "question": question,
        "entry": compact,
    }


def digest_for(provider: LLMProvider, inputs: dict[str, Any]) -> str:
    return agents.input_hash(prompts.EXPLAIN, provider.model_name(ModelTier.FAST), inputs)


async def cached_text(session: AsyncSession, digest: str) -> str | None:
    hit = await agents.cached_output(session, digest)
    return hit.output_text if hit else None


async def stream_explanation(
    session_factory: async_sessionmaker,
    provider: LLMProvider,
    inputs: dict[str, Any],
    digest: str,
    word_id: int,
    user_id: uuid.UUID | None,
) -> AsyncIterator[str]:
    stream = provider.stream_text(
        prompt=prompts.EXPLAIN.render(inputs), tier=ModelTier.FAST, system=prompts.EXPLAIN.system
    )
    parts: list[str] = []
    error: str | None = None
    try:
        async for chunk in stream:
            parts.append(chunk)
            yield sse({"delta": chunk})
    except AIError as exc:
        error = str(exc)[:2000]
        yield sse({"error": "ai_unavailable", "message": "AI vaqtincha javob bera olmadi"})
    async with session_factory() as session:
        await agents.log_generation(
            session,
            agent="explain",
            prompt=prompts.EXPLAIN,
            model=stream.model,
            digest=digest,
            output_text="".join(parts) if not error else None,
            tokens_in=stream.tokens_in,
            tokens_out=stream.tokens_out,
            word_id=word_id,
            user_id=user_id,
            error=error,
        )
        await session.commit()
    if not error:
        yield sse({"done": True, "cached": False})
