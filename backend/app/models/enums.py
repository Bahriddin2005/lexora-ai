from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"


class UserPlan(StrEnum):
    FREE = "free"
    PRO = "pro"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    AI_GENERATED = "ai_generated"
    PUBLISHED = "published"
    REJECTED = "rejected"


VISIBLE_STATUSES = (ContentStatus.PUBLISHED.value, ContentStatus.AI_GENERATED.value)


class EntryType(StrEnum):
    WORD = "word"
    PHRASE = "phrase"
    IDIOM = "idiom"
    PHRASAL_VERB = "phrasal_verb"
    ABBREVIATION = "abbreviation"
    PROPER_NOUN = "proper_noun"


class Register(StrEnum):
    NEUTRAL = "neutral"
    FORMAL = "formal"
    INFORMAL = "informal"
    SLANG = "slang"
    VULGAR = "vulgar"
    ARCHAIC = "archaic"


class RelationType(StrEnum):
    SYNONYM = "synonym"
    ANTONYM = "antonym"
    RELATED = "related"
    DERIVED = "derived"
    PHRASE = "phrase"


class SourceType(StrEnum):
    DATASET = "dataset"
    AI = "ai"
    EDITOR = "editor"
    USER = "user"
    WEB = "web"


class ReportReason(StrEnum):
    WRONG_TRANSLATION = "wrong_translation"
    WRONG_DEFINITION = "wrong_definition"
    WRONG_PRONUNCIATION = "wrong_pronunciation"
    OFFENSIVE = "offensive"
    DUPLICATE = "duplicate"
    OTHER = "other"


class ReportStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    REJECTED = "rejected"
