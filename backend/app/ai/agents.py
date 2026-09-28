"""AI agents: each has a versioned prompt, a typed output, caching and logging to `ai_generations`."""

import hashlib
import json
import logging
import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import prompts
from app.ai.provider import AIError, LLMProvider, ModelTier
from app.ai.schemas import GeneratedEntry, IntentResult, TranslationResult, Verification
from app.core.config import AI_PRICING
from app.models import AIGeneration

logger = logging.getLogger("lexora.ai")


def input_hash(prompt: prompts.Prompt, model: str, inputs: dict[str, Any]) -> str:
    raw = f"{prompt.id}|{model}|{json.dumps(inputs, sort_keys=True, ensure_ascii=False)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> Decimal:
    price_in, price_out = AI_PRICING.get(model, (0.5, 2.0))
    return Decimal(str(round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 6)))


async def log_generation(
    session: AsyncSession,
    *,
    agent: str,
    prompt: prompts.Prompt,
    model: str,
    digest: str,
    output: dict[str, Any] | None = None,
    output_text: str | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
    latency_ms: int = 0,
    word_id: int | None = None,
    user_id: uuid.UUID | None = None,
    error: str | None = None,
) -> None:
    session.add(
        AIGeneration(
            agent=agent,
            model=model,
            prompt_version=prompt.id,
            input_hash=digest,
            output=output,
            output_text=output_text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_usd=estimate_cost(model, tokens_in, tokens_out),
            word_id=word_id,
            user_id=user_id,
            ok=error is None,
            error=error,
        )
    )
    await session.flush()


async def cached_output(session: AsyncSession, digest: str) -> AIGeneration | None:
    return await session.scalar(
        select(AIGeneration)
        .where(AIGeneration.input_hash == digest, AIGeneration.ok.is_(True))
        .order_by(AIGeneration.id.desc())
        .limit(1)
    )


async def call_json[T: BaseModel](
    session: AsyncSession,
    provider: LLMProvider,
    *,
    prompt: prompts.Prompt,
    inputs: dict[str, Any],
    schema: type[T],
    tier: ModelTier,
    use_cache: bool = True,
    word_id: int | None = None,
    user_id: uuid.UUID | None = None,
    retries: int = 1,
) -> T:
    model = provider.model_name(tier)
    digest = input_hash(prompt, model, inputs)
    if use_cache:
        hit = await cached_output(session, digest)
        if hit and hit.output is not None:
            return schema.model_validate(hit.output)
    last_error: Exception | None = None
    for _ in range(retries + 1):
        try:
            result = await provider.generate_json(
                prompt=prompt.render(inputs), schema=schema, tier=tier, system=prompt.system
            )
        except AIError as exc:
            last_error = exc
            logger.warning("AI call %s failed: %s", prompt.id, exc)
            continue
        await log_generation(
            session,
            agent=prompt.name,
            prompt=prompt,
            model=result.model,
            digest=digest,
            output=result.data.model_dump(mode="json"),
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            latency_ms=result.latency_ms,
            word_id=word_id,
            user_id=user_id,
        )
        return result.data
    await log_generation(
        session, agent=prompt.name, prompt=prompt, model=model, digest=digest, error=str(last_error)[:2000]
    )
    raise AIError(str(last_error))


async def generate_entry(
    session: AsyncSession,
    provider: LLMProvider,
    *,
    term: str,
    lang_hint: str | None,
    languages: list[str],
    domain_hint: str | None = None,
    use_cache: bool = True,
    user_id: uuid.UUID | None = None,
) -> GeneratedEntry:
    inputs = {
        "term": term,
        "lang_hint": lang_hint,
        "languages": languages,
        "target_langs": languages,
        "definition_langs": ["en", "uz"],
        "domain_hint": domain_hint,
    }
    return await call_json(
        session, provider, prompt=prompts.ENTRY, inputs=inputs, schema=GeneratedEntry, tier=ModelTier.SMART,
        use_cache=use_cache, user_id=user_id,
    )  # fmt: skip


async def verify_entry(session: AsyncSession, provider: LLMProvider, entry: GeneratedEntry) -> Verification:
    inputs = {"entry": entry.model_dump(mode="json")}
    return await call_json(
        session, provider, prompt=prompts.VERIFY, inputs=inputs, schema=Verification, tier=ModelTier.FAST
    )


async def parse_intent(session: AsyncSession, provider: LLMProvider, query: str) -> IntentResult:
    return await call_json(
        session,
        provider,
        prompt=prompts.INTENT,
        inputs={"query": query},
        schema=IntentResult,
        tier=ModelTier.FAST,
    )


async def translate(
    session: AsyncSession,
    provider: LLMProvider,
    *,
    text: str,
    source: str,
    target: str,
    context: str | None,
    user_id: uuid.UUID | None = None,
) -> TranslationResult:
    inputs = {"text": text, "source": source, "target": target, "context": context}
    return await call_json(
        session, provider, prompt=prompts.TRANSLATE, inputs=inputs, schema=TranslationResult,
        tier=ModelTier.FAST, user_id=user_id,
    )  # fmt: skip
