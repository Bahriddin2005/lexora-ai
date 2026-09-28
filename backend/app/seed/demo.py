import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Word
from app.models.enums import ContentStatus
from app.schemas.entry import SeedEntry, WordEntryIn
from app.services import dictionary
from app.services.normalization import normalize

DEMO_FILE = Path(__file__).with_name("demo_words.json")


def load_demo_entries() -> list[SeedEntry]:
    return [SeedEntry.model_validate(item) for item in json.loads(DEMO_FILE.read_text(encoding="utf-8"))]


async def seed_demo(session: AsyncSession) -> int:
    """Insert the hand-curated demo dictionary. Existing entries are left untouched."""
    created = 0
    for entry in load_demo_entries():
        lang = entry.language_code
        exists = await session.scalar(
            select(Word.id).where(Word.language_code == lang, Word.normalized == normalize(entry.lemma, lang))
        )
        if exists:
            continue
        await dictionary.create_entry(
            session,
            lang,
            WordEntryIn.model_validate(entry.model_dump(exclude={"language_code"})),
            status=ContentStatus.PUBLISHED,
            source_code="demo-seed",
            confidence=1.0,
            reason="seed:demo",
            example_source="editor",
        )
        created += 1
    await session.commit()
    return created
