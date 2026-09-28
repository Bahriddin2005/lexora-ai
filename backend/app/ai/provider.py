"""Provider-agnostic LLM interface. Agents only talk to `LLMProvider`."""

import io
import wave
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import ai_unavailable


class ModelTier(StrEnum):
    SMART = "smart"
    FAST = "fast"
    TTS = "tts"


class AIError(Exception):
    pass


@dataclass
class LLMResult[T: BaseModel]:
    data: T
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0


class TextStream:
    """Async iterator of text chunks; token usage is filled in once the stream is exhausted."""

    def __init__(self, model: str):
        self.model = model
        self.tokens_in = 0
        self.tokens_out = 0
        self._chunks: AsyncIterator[str] | None = None

    def bind(self, chunks: AsyncIterator[str]) -> "TextStream":
        self._chunks = chunks
        return self

    def __aiter__(self) -> AsyncIterator[str]:
        assert self._chunks is not None
        return self._chunks


class LLMProvider(Protocol):
    name: str

    def model_name(self, tier: ModelTier) -> str: ...

    async def generate_json[T: BaseModel](
        self,
        *,
        prompt: str,
        schema: type[T],
        tier: ModelTier,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> LLMResult[T]: ...

    def stream_text(self, *, prompt: str, tier: ModelTier, system: str | None = None) -> TextStream: ...

    async def tts(self, *, text: str, lang: str, accent: str | None = None) -> bytes: ...


def pcm_to_wav(pcm: bytes, rate: int = 24000, channels: int = 1, width: int = 2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


_override: LLMProvider | None = None
_instance: LLMProvider | None = None


def set_provider(provider: LLMProvider | None) -> None:
    """Used by tests to inject a provider."""
    global _override
    _override = provider


def build_provider() -> LLMProvider | None:
    """A new provider instance (Celery tasks need one per event loop)."""
    if _override is not None:
        return _override
    if settings.ai_provider == "fake":
        from app.ai.fake import FakeProvider

        return FakeProvider()
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        from app.ai.gemini import GeminiProvider

        return GeminiProvider(settings.gemini_api_key)
    return None


def get_provider() -> LLMProvider | None:
    global _instance
    if _override is not None:
        return _override
    if _instance is None:
        _instance = build_provider()
    return _instance


def require_provider() -> LLMProvider:
    provider = get_provider()
    if provider is None:
        raise ai_unavailable()
    return provider
