from tests.conftest import make_user


async def search(client, q, **params):
    resp = await client.get("/api/v1/search", params={"q": q, **params})
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_exact_match_with_translation(client, seeded):
    data = await search(client, "run")
    top = data["results"][0]
    assert (top["lemma"], top["match"]) == ("run", "exact")
    assert top["primary_translation"] == {"language_code": "uz", "text": "yugurmoq"}
    assert top["short_definition"] == "oyoqda tez harakatlanmoq, yugurmoq"
    assert data["job"] is None


async def test_inflected_form(client, seeded):
    data = await search(client, "ran")
    assert data["results"][0]["lemma"] == "run"
    assert data["results"][0]["match"] == "form"


async def test_reverse_lookup(client, seeded):
    data = await search(client, "yugurmoq")
    assert data["results"][0]["lemma"] == "run"
    assert data["results"][0]["match"] == "reverse"


async def test_did_you_mean(client, seeded):
    data = await search(client, "beutiful")
    assert data["results"] == []
    assert data["did_you_mean"][0]["lemma"] == "beautiful"
    assert data["did_you_mean"][0]["score"] >= 0.5
    assert data["job"] is None  # a typo does not trigger AI generation


async def test_uzbek_apostrophe_variants(client, seeded):
    for q in ("o'g'il", "oʻgʻil", "ўғил"):
        data = await search(client, q)
        assert data["results"][0]["lemma"] == "oʻgʻil", q


async def test_turkish_and_russian(client, seeded):
    assert (await search(client, "Istanbul", **{"from": "tr"}))["results"][0]["lemma"] == "İstanbul"
    data = await search(client, "школа")
    assert data["results"][0]["language_code"] == "ru"


async def test_natural_language_queries(client, seeded):
    data = await search(client, "book so‘zining o‘zbekcha ma'nosi")
    assert data["results"][0]["lemma"] == "book"
    assert data["results"][0]["primary_translation"]["text"] == "kitob"

    data = await search(client, 'rus tilida "maktab" nima?')
    assert data["intent"]["target_lang"] == "ru"
    top = data["results"][0]
    assert top["lemma"] == "maktab"
    assert top["primary_translation"] == {"language_code": "ru", "text": "школа"}

    data = await search(client, "2026-yilda AI sohasida chiqqan yangi terminlarni ko‘rsat")
    assert data["intent"]["type"] == "list_new_terms"
    lemmas = {r["lemma"] for r in data["results"]}
    assert {"prompt", "LLM", "vibe coding", "hallucination"} <= lemmas


async def test_suggest(client, seeded):
    resp = await client.get("/api/v1/search/suggest", params={"q": "be"})
    assert [item["lemma"] for item in resp.json()][:1] == ["beautiful"]


async def test_search_logs_and_trending(client, seeded):
    for _ in range(3):
        await search(client, "apple")
    await search(client, "run")
    await search(client, "zzzqqq")
    resp = await client.get("/api/v1/trending")
    assert [w["lemma"] for w in resp.json()][:2] == ["apple", "run"]


async def test_rate_limit(client, seeded, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "search_rate_limit_per_minute", 2)
    await search(client, "run")
    await search(client, "run")
    resp = await client.get("/api/v1/search", params={"q": "run"})
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "rate_limited"


async def test_word_entry(client, seeded):
    await make_user(client)
    resp = await client.get("/api/v1/words/en/run")
    assert resp.status_code == 200
    entry = resp.json()
    assert entry["lemma"] == "run"
    assert [p["accent"] for p in entry["pronunciations"]] == ["US", "UK"]
    verb = entry["senses"][0]
    assert verb["pos"] == "verb"
    assert verb["translations"]["uz"][0] == {
        "text": "yugurmoq",
        "slug": None,
        "is_primary": True,
        "note": None,
    }
    assert {"text": "walk", "slug": None} in verb["antonyms"]
    assert "run out of" in [p["text"] for p in entry["relations"]["phrase"]]
    assert entry["sources"][0]["name"] == "Lexora demo lug‘ati"
    assert entry["is_favorite"] is False

    book = (await client.get("/api/v1/words/en/book")).json()
    assert book["senses"][0]["translations"]["uz"][0]["slug"] == "kitob"  # linked to the uz entry

    alias = await client.get("/api/v1/words/hello")
    assert alias.json()["lemma"] == "hello"

    missing = await client.get("/api/v1/words/en/beutiful")
    assert missing.status_code == 404
    assert missing.json()["error"]["details"]["suggestions"][0]["slug"] == "beautiful"
