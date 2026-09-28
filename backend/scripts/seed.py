"""Seed languages and the demo dictionary: `uv run python -m scripts.seed [--no-demo]`."""

import argparse
import asyncio

from app.core.db import SessionLocal
from app.seed.demo import seed_demo
from app.seed.languages import seed_languages


async def main(demo: bool) -> None:
    async with SessionLocal() as session:
        await seed_languages(session)
        print("languages: ok")
        if demo:
            print(f"demo words created: {await seed_demo(session)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-demo", action="store_true")
    asyncio.run(main(demo=not parser.parse_args().no_demo))
