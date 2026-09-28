"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-28 11:32:02.032544
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.create_table(
        "languages",
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("native_name", sa.String(length=64), nullable=False),
        sa.Column("script", sa.String(length=8), nullable=False),
        sa.Column("direction", sa.String(length=3), server_default="ltr", nullable=False),
        sa.Column("flag", sa.String(length=8), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("tts_supported", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_languages")),
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=48), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("license", sa.String(length=120), nullable=True),
        sa.Column("reliability", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
        sa.UniqueConstraint("code", name=op.f("uq_sources_code")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=True),
        sa.Column("role", sa.String(length=16), server_default="user", nullable=False),
        sa.Column("plan", sa.String(length=16), server_default="free", nullable=False),
        sa.Column("ui_language", sa.String(length=8), server_default="uz", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_refresh_tokens_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_tokens_token_hash")),
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)
    op.create_table(
        "words",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("language_code", sa.String(length=8), nullable=False),
        sa.Column("lemma", sa.String(length=200), nullable=False),
        sa.Column("normalized", sa.String(length=200), nullable=False),
        sa.Column("entry_type", sa.String(length=24), nullable=False),
        sa.Column("frequency_zipf", sa.Float(), nullable=True),
        sa.Column("cefr_level", sa.String(length=2), nullable=True),
        sa.Column("etymology", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=32)), server_default="{}", nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["language_code"], ["languages.code"], name=op.f("fk_words_language_code_languages")
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name=op.f("fk_words_source_id_sources")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_words")),
        sa.UniqueConstraint("language_code", "normalized", name=op.f("uq_words_language_code")),
    )
    op.create_index(op.f("ix_words_language_code"), "words", ["language_code"], unique=False)
    op.create_index(
        "ix_words_normalized_prefix",
        "words",
        ["normalized"],
        unique=False,
        postgresql_ops={"normalized": "varchar_pattern_ops"},
    )
    op.create_index(
        "ix_words_normalized_trgm",
        "words",
        ["normalized"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"normalized": "gin_trgm_ops"},
    )
    op.create_index("ix_words_status_created", "words", ["status", "created_at"], unique=False)
    op.create_index("ix_words_tags", "words", ["tags"], unique=False, postgresql_using="gin")
    op.create_table(
        "ai_generations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("agent", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("word_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_ai_generations_user_id_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_ai_generations_word_id_words"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_generations")),
    )
    op.create_index(op.f("ix_ai_generations_agent"), "ai_generations", ["agent"], unique=False)
    op.create_index(op.f("ix_ai_generations_created_at"), "ai_generations", ["created_at"], unique=False)
    op.create_index(op.f("ix_ai_generations_input_hash"), "ai_generations", ["input_hash"], unique=False)
    op.create_table(
        "pronunciations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("word_id", sa.BigInteger(), nullable=False),
        sa.Column("ipa", sa.String(length=200), nullable=True),
        sa.Column("accent", sa.String(length=16), nullable=True),
        sa.Column("audio_key", sa.String(length=300), nullable=True),
        sa.Column("audio_source", sa.String(length=16), nullable=True),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_pronunciations_word_id_words"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pronunciations")),
    )
    op.create_index(op.f("ix_pronunciations_word_id"), "pronunciations", ["word_id"], unique=False)
    op.create_table(
        "search_logs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("query", sa.String(length=300), nullable=False),
        sa.Column("normalized", sa.String(length=300), nullable=False),
        sa.Column("language_code", sa.String(length=8), nullable=True),
        sa.Column("target_language", sa.String(length=8), nullable=True),
        sa.Column("intent", sa.String(length=24), nullable=False),
        sa.Column("found", sa.Boolean(), nullable=False),
        sa.Column("result_word_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["result_word_id"],
            ["words.id"],
            name=op.f("fk_search_logs_result_word_id_words"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_search_logs_user_id_users"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_search_logs")),
    )
    op.create_index("ix_search_logs_found_created", "search_logs", ["found", "created_at"], unique=False)
    op.create_index(op.f("ix_search_logs_normalized"), "search_logs", ["normalized"], unique=False)
    op.create_table(
        "user_favorites",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("word_id", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_favorites_user_id_users"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_user_favorites_word_id_words"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "word_id", name=op.f("pk_user_favorites")),
    )
    op.create_table(
        "word_forms",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("word_id", sa.BigInteger(), nullable=False),
        sa.Column("form", sa.String(length=200), nullable=False),
        sa.Column("normalized", sa.String(length=200), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=32)), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_word_forms_word_id_words"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_word_forms")),
    )
    op.create_index(op.f("ix_word_forms_normalized"), "word_forms", ["normalized"], unique=False)
    op.create_index(op.f("ix_word_forms_word_id"), "word_forms", ["word_id"], unique=False)
    op.create_table(
        "word_senses",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("word_id", sa.BigInteger(), nullable=False),
        sa.Column("sense_order", sa.Integer(), nullable=False),
        sa.Column("pos", sa.String(length=24), nullable=False),
        sa.Column("domain", sa.String(length=48), nullable=True),
        sa.Column("register", sa.String(length=16), nullable=False),
        sa.Column("cefr_level", sa.String(length=2), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name=op.f("fk_word_senses_source_id_sources")),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_word_senses_word_id_words"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_word_senses")),
    )
    op.create_index(op.f("ix_word_senses_word_id"), "word_senses", ["word_id"], unique=False)
    op.create_table(
        "word_sources",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("word_id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_ref", sa.String(length=500), nullable=True),
        sa.Column(
            "retrieved_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], name=op.f("fk_word_sources_source_id_sources")
        ),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_word_sources_word_id_words"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_word_sources")),
    )
    op.create_index(op.f("ix_word_sources_word_id"), "word_sources", ["word_id"], unique=False)
    op.create_table(
        "word_versions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("word_id", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("changed_by", sa.UUID(), nullable=True),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["changed_by"], ["users.id"], name=op.f("fk_word_versions_changed_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_word_versions_word_id_words"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_word_versions")),
        sa.UniqueConstraint("word_id", "version", name=op.f("uq_word_versions_word_id")),
    )
    op.create_index(op.f("ix_word_versions_word_id"), "word_versions", ["word_id"], unique=False)
    op.create_table(
        "examples",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("sense_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "translations", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column("source", sa.String(length=16), nullable=True),
        sa.ForeignKeyConstraint(
            ["sense_id"],
            ["word_senses.id"],
            name=op.f("fk_examples_sense_id_word_senses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_examples")),
    )
    op.create_index(op.f("ix_examples_sense_id"), "examples", ["sense_id"], unique=False)
    op.create_table(
        "reports",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("word_id", sa.BigInteger(), nullable=False),
        sa.Column("sense_id", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("resolved_by", sa.UUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["resolved_by"], ["users.id"], name=op.f("fk_reports_resolved_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["sense_id"],
            ["word_senses.id"],
            name=op.f("fk_reports_sense_id_word_senses"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_reports_user_id_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_reports_word_id_words"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports")),
    )
    op.create_index(op.f("ix_reports_status"), "reports", ["status"], unique=False)
    op.create_index(op.f("ix_reports_word_id"), "reports", ["word_id"], unique=False)
    op.create_table(
        "sense_definitions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("sense_id", sa.BigInteger(), nullable=False),
        sa.Column("language_code", sa.String(length=8), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["language_code"], ["languages.code"], name=op.f("fk_sense_definitions_language_code_languages")
        ),
        sa.ForeignKeyConstraint(
            ["sense_id"],
            ["word_senses.id"],
            name=op.f("fk_sense_definitions_sense_id_word_senses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], name=op.f("fk_sense_definitions_source_id_sources")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sense_definitions")),
        sa.UniqueConstraint("sense_id", "language_code", name=op.f("uq_sense_definitions_sense_id")),
    )
    op.create_table(
        "translations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("sense_id", sa.BigInteger(), nullable=False),
        sa.Column("target_language", sa.String(length=8), nullable=False),
        sa.Column("text", sa.String(length=300), nullable=False),
        sa.Column("normalized", sa.String(length=300), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["sense_id"],
            ["word_senses.id"],
            name=op.f("fk_translations_sense_id_word_senses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], name=op.f("fk_translations_source_id_sources")
        ),
        sa.ForeignKeyConstraint(
            ["target_language"], ["languages.code"], name=op.f("fk_translations_target_language_languages")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_translations")),
    )
    op.create_index(
        "ix_translations_lang_normalized", "translations", ["target_language", "normalized"], unique=False
    )
    op.create_index(op.f("ix_translations_sense_id"), "translations", ["sense_id"], unique=False)
    op.create_table(
        "word_relations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("word_id", sa.BigInteger(), nullable=False),
        sa.Column("sense_id", sa.BigInteger(), nullable=True),
        sa.Column("relation_type", sa.String(length=16), nullable=False),
        sa.Column("target_text", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(
            ["sense_id"],
            ["word_senses.id"],
            name=op.f("fk_word_relations_sense_id_word_senses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["word_id"], ["words.id"], name=op.f("fk_word_relations_word_id_words"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_word_relations")),
    )
    op.create_index(op.f("ix_word_relations_word_id"), "word_relations", ["word_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_word_relations_word_id"), table_name="word_relations")
    op.drop_table("word_relations")
    op.drop_index(op.f("ix_translations_sense_id"), table_name="translations")
    op.drop_index("ix_translations_lang_normalized", table_name="translations")
    op.drop_table("translations")
    op.drop_table("sense_definitions")
    op.drop_index(op.f("ix_reports_word_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_status"), table_name="reports")
    op.drop_table("reports")
    op.drop_index(op.f("ix_examples_sense_id"), table_name="examples")
    op.drop_table("examples")
    op.drop_index(op.f("ix_word_versions_word_id"), table_name="word_versions")
    op.drop_table("word_versions")
    op.drop_index(op.f("ix_word_sources_word_id"), table_name="word_sources")
    op.drop_table("word_sources")
    op.drop_index(op.f("ix_word_senses_word_id"), table_name="word_senses")
    op.drop_table("word_senses")
    op.drop_index(op.f("ix_word_forms_word_id"), table_name="word_forms")
    op.drop_index(op.f("ix_word_forms_normalized"), table_name="word_forms")
    op.drop_table("word_forms")
    op.drop_table("user_favorites")
    op.drop_index(op.f("ix_search_logs_normalized"), table_name="search_logs")
    op.drop_index("ix_search_logs_found_created", table_name="search_logs")
    op.drop_table("search_logs")
    op.drop_index(op.f("ix_pronunciations_word_id"), table_name="pronunciations")
    op.drop_table("pronunciations")
    op.drop_index(op.f("ix_ai_generations_input_hash"), table_name="ai_generations")
    op.drop_index(op.f("ix_ai_generations_created_at"), table_name="ai_generations")
    op.drop_index(op.f("ix_ai_generations_agent"), table_name="ai_generations")
    op.drop_table("ai_generations")
    op.drop_index("ix_words_tags", table_name="words", postgresql_using="gin")
    op.drop_index("ix_words_status_created", table_name="words")
    op.drop_index(
        "ix_words_normalized_trgm",
        table_name="words",
        postgresql_using="gin",
        postgresql_ops={"normalized": "gin_trgm_ops"},
    )
    op.drop_index(
        "ix_words_normalized_prefix", table_name="words", postgresql_ops={"normalized": "varchar_pattern_ops"}
    )
    op.drop_index(op.f("ix_words_language_code"), table_name="words")
    op.drop_table("words")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("sources")
    op.drop_table("languages")
