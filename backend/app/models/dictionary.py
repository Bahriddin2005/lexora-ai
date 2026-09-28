import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import ContentStatus, EntryType, Register


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(16))
    url: Mapped[str | None] = mapped_column(String(500))
    license: Mapped[str | None] = mapped_column(String(120))
    reliability: Mapped[float] = mapped_column(Float, default=0.5)


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    language_code: Mapped[str] = mapped_column(ForeignKey("languages.code"), index=True)
    lemma: Mapped[str] = mapped_column(String(200))
    normalized: Mapped[str] = mapped_column(String(200))
    entry_type: Mapped[str] = mapped_column(String(24), default=EntryType.WORD.value)
    frequency_zipf: Mapped[float | None] = mapped_column(Float)
    cefr_level: Mapped[str | None] = mapped_column(String(2))
    etymology: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list, server_default="{}")
    status: Mapped[str] = mapped_column(String(16), default=ContentStatus.DRAFT.value)
    confidence: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source: Mapped[Source | None] = relationship(lazy="joined")
    senses: Mapped[list["WordSense"]] = relationship(
        back_populates="word", passive_deletes=True, order_by="WordSense.sense_order"
    )
    forms: Mapped[list["WordForm"]] = relationship(passive_deletes=True, order_by="WordForm.id")
    pronunciations: Mapped[list["Pronunciation"]] = relationship(
        passive_deletes=True, order_by="Pronunciation.id"
    )
    relations: Mapped[list["WordRelation"]] = relationship(passive_deletes=True, order_by="WordRelation.id")
    source_links: Mapped[list["WordSource"]] = relationship(passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("language_code", "normalized"),
        Index(
            "ix_words_normalized_trgm",
            "normalized",
            postgresql_using="gin",
            postgresql_ops={"normalized": "gin_trgm_ops"},
        ),
        Index(
            "ix_words_normalized_prefix", "normalized", postgresql_ops={"normalized": "varchar_pattern_ops"}
        ),
        Index("ix_words_tags", "tags", postgresql_using="gin"),
        Index("ix_words_status_created", "status", "created_at"),
    )


class WordForm(Base):
    __tablename__ = "word_forms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    form: Mapped[str] = mapped_column(String(200))
    normalized: Mapped[str] = mapped_column(String(200), index=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list, server_default="{}")


class Pronunciation(Base):
    __tablename__ = "pronunciations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    ipa: Mapped[str | None] = mapped_column(String(200))
    accent: Mapped[str | None] = mapped_column(String(16))
    audio_key: Mapped[str | None] = mapped_column(String(300))
    audio_source: Mapped[str | None] = mapped_column(String(16))


class WordSense(Base):
    __tablename__ = "word_senses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    sense_order: Mapped[int] = mapped_column(Integer, default=0)
    pos: Mapped[str] = mapped_column(String(24))
    domain: Mapped[str | None] = mapped_column(String(48))
    register: Mapped[str] = mapped_column(String(16), default=Register.NEUTRAL.value)
    cefr_level: Mapped[str | None] = mapped_column(String(2))
    status: Mapped[str] = mapped_column(String(16), default=ContentStatus.DRAFT.value)
    confidence: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))

    word: Mapped[Word] = relationship(back_populates="senses")
    definitions: Mapped[list["SenseDefinition"]] = relationship(passive_deletes=True)
    translations: Mapped[list["Translation"]] = relationship(
        passive_deletes=True, order_by="(Translation.is_primary.desc(), Translation.id)"
    )
    examples: Mapped[list["Example"]] = relationship(passive_deletes=True, order_by="Example.id")


class SenseDefinition(Base):
    __tablename__ = "sense_definitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sense_id: Mapped[int] = mapped_column(ForeignKey("word_senses.id", ondelete="CASCADE"))
    language_code: Mapped[str] = mapped_column(ForeignKey("languages.code"))
    text: Mapped[str] = mapped_column(Text)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))

    __table_args__ = (UniqueConstraint("sense_id", "language_code"),)


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sense_id: Mapped[int] = mapped_column(ForeignKey("word_senses.id", ondelete="CASCADE"), index=True)
    target_language: Mapped[str] = mapped_column(ForeignKey("languages.code"))
    text: Mapped[str] = mapped_column(String(300))
    normalized: Mapped[str] = mapped_column(String(300))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(String(300))
    confidence: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))

    __table_args__ = (Index("ix_translations_lang_normalized", "target_language", "normalized"),)


class Example(Base):
    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sense_id: Mapped[int] = mapped_column(ForeignKey("word_senses.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    translations: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict, server_default="{}")
    source: Mapped[str | None] = mapped_column(String(16))


class WordRelation(Base):
    __tablename__ = "word_relations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    sense_id: Mapped[int | None] = mapped_column(ForeignKey("word_senses.id", ondelete="CASCADE"))
    relation_type: Mapped[str] = mapped_column(String(16))
    target_text: Mapped[str] = mapped_column(String(200))

    sense: Mapped[WordSense | None] = relationship()


class WordSource(Base):
    __tablename__ = "word_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    external_ref: Mapped[str | None] = mapped_column(String(500))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Source] = relationship(lazy="joined")


class WordVersion(Base):
    __tablename__ = "word_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reason: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("word_id", "version"),)
