"""Import a kaikki.org Wiktextract JSONL dump.

Download e.g. https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl (large!), then:
    uv sync --extra import   # installs wordfreq for frequency ranking
    uv run python -m scripts.import_kaikki path/to/file.jsonl --lang en --limit 20000 --min-zipf 3
"""

import argparse
import asyncio
from pathlib import Path

from app.core.db import SessionLocal
from app.seed.kaikki import import_entries, read_jsonl
from app.seed.languages import seed_languages


async def main(args: argparse.Namespace) -> None:
    async with SessionLocal() as session:
        await seed_languages(session)
        stats = await import_entries(
            session, read_jsonl(Path(args.path)), set(args.lang), limit=args.limit, min_zipf=args.min_zipf
        )
    print(stats)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--lang", action="append", default=None, help="language code(s) to import, e.g. en")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-zipf", type=float, default=None)
    ns = parser.parse_args()
    ns.lang = ns.lang or ["en"]
    asyncio.run(main(ns))
