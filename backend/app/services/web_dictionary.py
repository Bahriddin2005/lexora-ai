"""Best-effort internet dictionary suggestions from Wiktionary's MediaWiki API."""

import asyncio
from dataclasses import dataclass

import httpx

SUPPORTED_WIKIS = ("uz", "en", "ru", "tr")


@dataclass(frozen=True)
class WebWord:
    language_code: str
    title: str
    description: str | None
    url: str


async def _search_wiki(client: httpx.AsyncClient, language_code: str, query: str) -> list[WebWord]:
    response = await client.get(
        f"https://{language_code}.wiktionary.org/w/api.php",
        params={
            "action": "opensearch",
            "search": query,
            "limit": 6,
            "namespace": 0,
            "format": "json",
        },
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 4:
        return []
    titles, descriptions, urls = payload[1], payload[2], payload[3]
    if not all(isinstance(items, list) for items in (titles, descriptions, urls)):
        return []
    return [
        WebWord(
            language_code=language_code,
            title=str(title)[:200],
            description=(str(description)[:500] or None),
            url=str(url),
        )
        for title, description, url in zip(titles, descriptions, urls, strict=False)
        if title and str(url).startswith("https://")
    ]


async def search(query: str, preferred_language: str | None = None, limit: int = 12) -> list[WebWord]:
    languages = list(SUPPORTED_WIKIS)
    if preferred_language in languages:
        languages.remove(preferred_language)
        languages.insert(0, preferred_language)
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(4.0),
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "LexoraAI/0.1 (https://github.com/Bahriddin2005/lexora-ai; "
                    "contact: Bahriddin2005@users.noreply.github.com)"
                )
            },
        ) as client:
            batches = await asyncio.gather(
                *(_search_wiki(client, language, query) for language in languages),
                return_exceptions=True,
            )
    except httpx.HTTPError:
        return []

    found: list[WebWord] = []
    seen: set[tuple[str, str]] = set()
    for batch in batches:
        if isinstance(batch, BaseException):
            continue
        for item in batch:
            key = (item.language_code, item.title.casefold())
            if key not in seen:
                seen.add(key)
                found.append(item)
                if len(found) >= limit:
                    return found
    return found
