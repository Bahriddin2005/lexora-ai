"""Deterministic provider for tests and for running without an API key (AI_PROVIDER=fake)."""

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from app.ai.prompts import parse_input
from app.ai.provider import AIError, LLMResult, ModelTier, TextStream, pcm_to_wav
from app.ai.schemas import (
    GeneratedEntry,
    GenExample,
    GenSense,
    GenTranslation,
    IntentResult,
    LangText,
    TranslationResult,
    Verification,
)


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.entries: dict[str, GeneratedEntry] = {}
        self.invalid_terms: set[str] = set()
        self.verdicts: dict[str, Verification] = {}
        self.intents: dict[str, IntentResult] = {}
        self.fail = False

    def model_name(self, tier: ModelTier) -> str:
        return "fake"

    def _check(self) -> None:
        if self.fail:
            raise AIError("fake provider failure")

    async def generate_json[T: BaseModel](
        self,
        *,
        prompt: str,
        schema: type[T],
        tier: ModelTier,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> LLMResult[T]:
        self._check()
        inputs = parse_input(prompt)
        self.calls.append((schema.__name__, inputs))
        data: BaseModel
        if schema is GeneratedEntry:
            data = self._entry(inputs)
        elif schema is Verification:
            data = self.verdicts.get(
                inputs["entry"]["lemma"], Verification(verdict="accept", confidence=0.85)
            )
        elif schema is IntentResult:
            data = self.intents.get(inputs["query"], IntentResult(type="lookup", term=inputs["query"]))
        elif schema is TranslationResult:
            source = inputs["source"] if inputs["source"] != "auto" else "en"
            data = TranslationResult(
                translation=f"[{inputs['target']}] {inputs['text']}", detected_source=source
            )
        else:
            raise AIError(f"fake provider: unsupported schema {schema.__name__}")
        return LLMResult(data=data, model="fake", tokens_in=len(prompt) // 4, tokens_out=50, latency_ms=1)  # type: ignore[arg-type]

    def _entry(self, inputs: dict[str, Any]) -> GeneratedEntry:
        term = inputs["term"]
        if term in self.entries:
            return self.entries[term]
        if term in self.invalid_terms:
            return GeneratedEntry(is_valid_word=False, language="en", lemma=term, suggestions=["test"])
        lang = inputs.get("lang_hint") or "en"
        others = [code for code in inputs["target_langs"] if code != lang]
        return GeneratedEntry(
            is_valid_word=True,
            language=lang,
            lemma=term,
            ipa=f"/{term}/",
            tags=["new"],
            senses=[
                GenSense(
                    pos="noun",
                    domain=inputs.get("domain_hint"),
                    definitions=[
                        LangText(lang="en", text=f"meaning of {term}"),
                        LangText(lang="uz", text=f"{term} ma’nosi"),
                    ],
                    translations=[
                        GenTranslation(lang=code, text=f"{term}-{code}", is_primary=True) for code in others
                    ],
                    examples=[
                        GenExample(
                            text=f"This is {term}.", translations=[LangText(lang="uz", text=f"Bu {term}.")]
                        )
                    ],
                    synonyms=[f"{term}-syn"],
                )
            ],
        )

    def stream_text(self, *, prompt: str, tier: ModelTier, system: str | None = None) -> TextStream:
        inputs = parse_input(prompt)
        self.calls.append(("stream", inputs))
        stream = TextStream("fake")

        async def chunks() -> AsyncIterator[str]:
            self._check()
            for part in ("**", inputs["entry"]["lemma"], "** — ", "sodda ", "izoh."):
                yield part
            stream.tokens_in, stream.tokens_out = len(prompt) // 4, 10

        return stream.bind(chunks())

    async def tts(self, *, text: str, lang: str, accent: str | None = None) -> bytes:
        self._check()
        self.calls.append(("tts", {"text": text, "lang": lang, "accent": accent}))
        return pcm_to_wav(b"\x00\x00" * 2400)
