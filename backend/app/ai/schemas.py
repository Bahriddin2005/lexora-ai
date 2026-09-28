"""Structured outputs of AI agents. Lists of {lang, text} are used instead of dicts (Gemini schema limits)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import EntryType, Register
from app.schemas.entry import ExampleIn, FormIn, PronunciationIn, SenseIn, TranslationIn, WordEntryIn

_CEFR = {"A1", "A2", "B1", "B2", "C1", "C2"}
_REGISTERS = {r.value for r in Register}
_ENTRY_TYPES = {e.value for e in EntryType}


class LangText(BaseModel):
    lang: str
    text: str


class GenTranslation(BaseModel):
    lang: str
    text: str
    is_primary: bool = False
    note: str | None = None


class GenExample(BaseModel):
    text: str
    translations: list[LangText] = Field(default_factory=list)


class GenSense(BaseModel):
    pos: str
    domain: str | None = None
    register: str = "neutral"
    cefr_level: str | None = None
    definitions: list[LangText] = Field(default_factory=list)
    translations: list[GenTranslation] = Field(default_factory=list)
    examples: list[GenExample] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    antonyms: list[str] = Field(default_factory=list)


class GeneratedEntry(BaseModel):
    is_valid_word: bool
    language: str
    lemma: str
    entry_type: str = "word"
    ipa: str | None = None
    cefr_level: str | None = None
    tags: list[str] = Field(default_factory=list)
    forms: list[str] = Field(default_factory=list)
    etymology_en: str | None = None
    etymology_uz: str | None = None
    senses: list[GenSense] = Field(default_factory=list)
    phrases: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    def to_entry_in(self, allowed_langs: set[str]) -> WordEntryIn:
        def cefr(value: str | None) -> str | None:
            value = (value or "").strip().upper()[:2]
            return value if value in _CEFR else None

        senses = []
        for s in self.senses[:8]:
            translations: dict[str, list[TranslationIn]] = {}
            for t in s.translations:
                if t.lang in allowed_langs and t.lang != self.language and t.text.strip():
                    translations.setdefault(t.lang, []).append(
                        TranslationIn(text=t.text.strip()[:300], is_primary=t.is_primary, note=t.note)
                    )
            for items in translations.values():
                if not any(t.is_primary for t in items):
                    items[0].is_primary = True
            senses.append(
                SenseIn(
                    pos=(s.pos or "noun").strip().lower()[:24],
                    domain=(s.domain or None) and s.domain.strip().lower()[:48],
                    register=s.register if s.register in _REGISTERS else "neutral",
                    cefr_level=cefr(s.cefr_level),
                    definitions={
                        d.lang: d.text.strip() for d in s.definitions if d.lang in allowed_langs and d.text
                    },
                    translations=translations,
                    examples=[
                        ExampleIn(
                            text=e.text,
                            translations={t.lang: t.text for t in e.translations if t.lang in allowed_langs},
                        )
                        for e in s.examples[:4]
                        if e.text.strip()
                    ],
                    synonyms=[x for x in s.synonyms if x.strip()][:10],
                    antonyms=[x for x in s.antonyms if x.strip()][:10],
                )
            )
        etymology = {k: v for k, v in (("en", self.etymology_en), ("uz", self.etymology_uz)) if v}
        return WordEntryIn(
            lemma=self.lemma.strip()[:200],
            entry_type=self.entry_type if self.entry_type in _ENTRY_TYPES else "word",
            cefr_level=cefr(self.cefr_level),
            tags=[t.strip().lower()[:32] for t in self.tags if t.strip()][:10],
            etymology=etymology or None,
            pronunciations=[PronunciationIn(ipa=self.ipa)] if self.ipa else [],
            forms=[FormIn(form=f) for f in self.forms if f.strip()][:20],
            senses=senses,
            relations={"phrase": [p for p in self.phrases if p.strip()][:10]} if self.phrases else {},
        )


class Verification(BaseModel):
    verdict: Literal["accept", "review", "reject"]
    confidence: float = Field(ge=0, le=1)
    issues: list[str] = Field(default_factory=list)


class IntentResult(BaseModel):
    type: Literal["lookup", "translate", "list_new_terms"] = "lookup"
    term: str | None = None
    source_lang: str | None = None
    target_lang: str | None = None
    domain: str | None = None
    year: int | None = None


class TranslationResult(BaseModel):
    translation: str
    detected_source: str
    alternatives: list[str] = Field(default_factory=list)
    notes: str | None = None
