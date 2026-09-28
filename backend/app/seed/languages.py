from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Language

LANGUAGES = [
    {
        "code": "uz",
        "name": "Uzbek",
        "native_name": "O‘zbekcha",
        "script": "Latn",
        "flag": "🇺🇿",
        "sort_order": 1,
    },
    {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "script": "Latn",
        "flag": "🇬🇧",
        "sort_order": 2,
    },
    {
        "code": "ru",
        "name": "Russian",
        "native_name": "Русский",
        "script": "Cyrl",
        "flag": "🇷🇺",
        "sort_order": 3,
    },
    {
        "code": "tr",
        "name": "Turkish",
        "native_name": "Türkçe",
        "script": "Latn",
        "flag": "🇹🇷",
        "sort_order": 4,
    },
]


async def seed_languages(session: AsyncSession) -> None:
    for lang in LANGUAGES:
        stmt = insert(Language).values(direction="ltr", is_active=True, tts_supported=True, **lang)
        await session.execute(stmt.on_conflict_do_nothing(index_elements=["code"]))
    await session.commit()
