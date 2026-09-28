import asyncio
import re
import time
from collections.abc import AsyncIterator

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.ai.provider import AIError, LLMResult, ModelTier, TextStream, pcm_to_wav
from app.core.config import settings

_ACCENT_HINTS = {"US": "in a General American accent", "UK": "in a British (RP) accent"}


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def model_name(self, tier: ModelTier) -> str:
        return {
            ModelTier.SMART: settings.gemini_model_smart,
            ModelTier.FAST: settings.gemini_model_fast,
            ModelTier.TTS: settings.gemini_model_tts,
        }[tier]

    async def generate_json[T: BaseModel](
        self,
        *,
        prompt: str,
        schema: type[T],
        tier: ModelTier,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> LLMResult[T]:
        model = self.model_name(tier)
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema,
        )
        started = time.perf_counter()
        try:
            resp = await asyncio.wait_for(
                self.client.aio.models.generate_content(model=model, contents=prompt, config=config),
                timeout=settings.ai_timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - provider errors are normalized to AIError
            raise AIError(f"gemini: {exc}") from exc
        latency = int((time.perf_counter() - started) * 1000)
        parsed = resp.parsed
        try:
            data = parsed if isinstance(parsed, schema) else schema.model_validate_json(resp.text or "")
        except ValidationError as exc:
            raise AIError(f"gemini: invalid JSON for {schema.__name__}: {exc}") from exc
        usage = resp.usage_metadata
        return LLMResult(
            data=data,
            model=model,
            tokens_in=(usage.prompt_token_count or 0) if usage else 0,
            tokens_out=(usage.candidates_token_count or 0) if usage else 0,
            latency_ms=latency,
        )

    def stream_text(self, *, prompt: str, tier: ModelTier, system: str | None = None) -> TextStream:
        model = self.model_name(tier)
        config = types.GenerateContentConfig(system_instruction=system, temperature=0.4)
        stream = TextStream(model)

        async def chunks() -> AsyncIterator[str]:
            try:
                async for chunk in await self.client.aio.models.generate_content_stream(
                    model=model, contents=prompt, config=config
                ):
                    if chunk.usage_metadata:
                        stream.tokens_in = chunk.usage_metadata.prompt_token_count or stream.tokens_in
                        stream.tokens_out = chunk.usage_metadata.candidates_token_count or stream.tokens_out
                    if chunk.text:
                        yield chunk.text
            except Exception as exc:  # noqa: BLE001
                raise AIError(f"gemini stream: {exc}") from exc

        return stream.bind(chunks())

    async def tts(self, *, text: str, lang: str, accent: str | None = None) -> bytes:
        hint = _ACCENT_HINTS.get((accent or "").upper(), "")
        prompt = f"Say clearly and naturally{(' ' + hint) if hint else ''}: {text}"
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=settings.gemini_tts_voice)
                )
            ),
        )
        try:
            resp = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name(ModelTier.TTS), contents=prompt, config=config
                ),
                timeout=settings.ai_timeout_seconds,
            )
            blob = resp.candidates[0].content.parts[0].inline_data
        except Exception as exc:  # noqa: BLE001
            raise AIError(f"gemini tts: {exc}") from exc
        if blob is None or not blob.data:
            raise AIError("gemini tts: empty audio")
        rate_match = re.search(r"rate=(\d+)", blob.mime_type or "")
        return pcm_to_wav(blob.data, rate=int(rate_match.group(1)) if rate_match else 24000)
