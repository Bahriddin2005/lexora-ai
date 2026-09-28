import hashlib

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import agents, prompts
from app.ai.provider import LLMProvider, ModelTier
from app.core.config import settings
from app.services import quotas
from app.services.storage import get_storage

MAX_TTS_CHARS = 200
_TTS_PROMPT = prompts.Prompt(name="tts", version=1, system="", task="")


def audio_digest(text: str, lang: str, accent: str | None, model: str) -> str:
    raw = f"{model}|{settings.gemini_tts_voice}|{lang}|{accent or ''}|{text}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_audio(
    session: AsyncSession,
    redis: Redis,
    provider: LLMProvider,
    *,
    text: str,
    lang: str,
    accent: str | None,
    subject: quotas.Subject,
) -> bytes:
    model = provider.model_name(ModelTier.TTS)
    digest = audio_digest(text, lang, accent, model)
    key = f"tts/{digest}.wav"
    storage = get_storage()
    cached = await storage.get(key)
    if cached is not None:
        return cached
    await quotas.consume(redis, subject, "tts")
    try:
        audio = await provider.tts(text=text, lang=lang, accent=accent)
    except Exception:
        await quotas.refund(redis, subject, "tts")
        raise
    await storage.put(key, audio, "audio/wav")
    await agents.log_generation(
        session, agent="tts", prompt=_TTS_PROMPT, model=model, digest=digest, tokens_in=len(text) // 4 + 1
    )
    await session.commit()
    return audio
