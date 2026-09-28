from pathlib import Path

from app.seed.demo import load_demo_entries
from app.seed.kaikki import import_entries, read_jsonl

FIXTURE = Path(__file__).parent / "fixtures" / "kaikki_sample.jsonl"


async def test_kaikki_import(client, db):
    stats = await import_entries(db, read_jsonl(FIXTURE), {"en", "ru"})
    assert stats["created"] == 2  # cat (en) and кошка (ru); "cats" is only an inflection
    assert stats["skipped_empty"] == 1

    cat = (await client.get("/api/v1/words/en/cat")).json()
    assert [s["pos"] for s in cat["senses"]] == ["noun", "noun", "verb"]
    assert cat["senses"][0]["translations"]["uz"][0]["text"] == "mushuk"
    assert [t["text"] for t in cat["senses"][0]["translations"]["ru"]] == ["кошка", "кот"]
    assert "de" not in cat["senses"][0]["translations"]
    assert cat["senses"][1]["register"] == "slang"
    assert {p["accent"] for p in cat["pronunciations"]} == {"UK", "US"}
    assert cat["forms"] == [{"form": "cats", "tags": ["plural"]}]
    assert cat["relations"]["derived"][0]["text"] == "catfish"
    assert cat["sources"][0]["url"] == "https://en.wiktionary.org/wiki/cat"

    koshka = (await client.get("/api/v1/words/ru/кошка")).json()
    assert koshka["senses"][0]["translations"]["en"][0]["text"] == "cat"
    assert koshka["senses"][0]["examples"][0]["translations"] == {"en": "The cat is sleeping."}

    again = await import_entries(db, read_jsonl(FIXTURE), {"en", "ru"})
    assert again["created"] == 0 and again["skipped_existing"] == 2


def test_demo_seed_is_valid():
    entries = load_demo_entries()
    assert len(entries) >= 40
    assert {e.language_code for e in entries} == {"en", "uz", "ru", "tr"}
    for entry in entries:
        assert entry.senses, entry.lemma
        for sense in entry.senses:
            assert sense.definitions, entry.lemma
