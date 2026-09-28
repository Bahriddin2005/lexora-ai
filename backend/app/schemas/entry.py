from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import EntryType, Register, RelationType

CEFR = Literal["A1", "A2", "B1", "B2", "C1", "C2"]


# ---------- input (admin editor, AI, seeds, importers) ----------


class TranslationIn(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    is_primary: bool = False
    note: str | None = Field(default=None, max_length=300)


class ExampleIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    translations: dict[str, str] = Field(default_factory=dict)


class SenseIn(BaseModel):
    pos: str = Field(min_length=1, max_length=24)
    domain: str | None = Field(default=None, max_length=48)
    register: Register = Register.NEUTRAL
    cefr_level: CEFR | None = None
    definitions: dict[str, str] = Field(default_factory=dict)
    translations: dict[str, list[TranslationIn]] = Field(default_factory=dict)
    examples: list[ExampleIn] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    antonyms: list[str] = Field(default_factory=list)


class PronunciationIn(BaseModel):
    ipa: str | None = Field(default=None, max_length=200)
    accent: str | None = Field(default=None, max_length=16)


class FormIn(BaseModel):
    form: str = Field(min_length=1, max_length=200)
    tags: list[str] = Field(default_factory=list)


class WordEntryIn(BaseModel):
    lemma: str = Field(min_length=1, max_length=200)
    entry_type: EntryType = EntryType.WORD
    cefr_level: CEFR | None = None
    frequency_zipf: float | None = None
    tags: list[str] = Field(default_factory=list)
    etymology: dict[str, str] | None = None
    pronunciations: list[PronunciationIn] = Field(default_factory=list)
    forms: list[FormIn] = Field(default_factory=list)
    senses: list[SenseIn] = Field(default_factory=list)
    relations: dict[RelationType, list[str]] = Field(default_factory=dict)


class SeedEntry(WordEntryIn):
    language_code: str


# ---------- output ----------


class LinkOut(BaseModel):
    text: str
    slug: str | None = None


class TranslationOut(LinkOut):
    is_primary: bool = False
    note: str | None = None


class ExampleOut(BaseModel):
    text: str
    translations: dict[str, str] = Field(default_factory=dict)


class SenseOut(BaseModel):
    id: int
    pos: str
    domain: str | None
    register: str
    cefr_level: str | None
    definitions: dict[str, str]
    translations: dict[str, list[TranslationOut]]
    examples: list[ExampleOut]
    synonyms: list[LinkOut]
    antonyms: list[LinkOut]


class PronunciationOut(BaseModel):
    ipa: str | None
    accent: str | None
    audio_url: str | None


class FormOut(BaseModel):
    form: str
    tags: list[str]


class SourceOut(BaseModel):
    name: str
    url: str | None
    license: str | None


class WordEntry(BaseModel):
    id: int
    language_code: str
    lemma: str
    slug: str
    entry_type: str
    status: str
    confidence: float | None
    cefr_level: str | None
    frequency_zipf: float | None
    tags: list[str]
    etymology: dict[str, str] | None
    audio_url: str | None
    pronunciations: list[PronunciationOut]
    forms: list[FormOut]
    senses: list[SenseOut]
    relations: dict[str, list[LinkOut]]
    sources: list[SourceOut]
    is_favorite: bool = False
    version: int
    updated_at: datetime


class PrimaryTranslation(BaseModel):
    language_code: str
    text: str


class WordSummary(BaseModel):
    id: int
    language_code: str
    lemma: str
    slug: str
    entry_type: str
    status: str
    confidence: float | None = None
    pos: list[str]
    cefr_level: str | None
    short_definition: str | None
    primary_translation: PrimaryTranslation | None
    match: str | None = None
    score: float | None = None
    saved_at: datetime | None = None
