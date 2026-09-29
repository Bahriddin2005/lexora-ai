from tests.conftest import make_user


async def test_favorites(client, seeded):
    run = (await client.get("/api/v1/words/en/run")).json()
    assert (await client.post("/api/v1/me/favorites", json={"word_id": run["id"]})).status_code == 401

    await make_user(client)
    assert (await client.post("/api/v1/me/favorites", json={"word_id": run["id"]})).status_code == 201
    assert (
        await client.post("/api/v1/me/favorites", json={"word_id": run["id"]})
    ).status_code == 201  # idempotent
    assert (await client.get("/api/v1/words/en/run")).json()["is_favorite"] is True

    favorites = (await client.get("/api/v1/me/favorites")).json()
    assert [f["lemma"] for f in favorites] == ["run"]
    assert favorites[0]["saved_at"]

    assert (await client.delete(f"/api/v1/me/favorites/{run['id']}")).status_code == 204
    assert (await client.get("/api/v1/me/favorites")).json() == []
    assert (await client.post("/api/v1/me/favorites", json={"word_id": 999999})).status_code == 404


async def test_reports(client, seeded):
    run = (await client.get("/api/v1/words/en/run")).json()
    resp = await client.post(
        "/api/v1/reports",
        json={
            "word_id": run["id"],
            "sense_id": run["senses"][0]["id"],
            "reason": "wrong_translation",
            "comment": "x",
        },
    )
    assert resp.status_code == 201
    bad = await client.post(
        "/api/v1/reports", json={"word_id": run["id"], "sense_id": 999999, "reason": "other"}
    )
    assert bad.status_code == 400
    invalid = await client.post("/api/v1/reports", json={"word_id": run["id"], "reason": "nope"})
    assert invalid.status_code == 422


async def test_discover_lists(client, seeded):
    dictionary = (await client.get("/api/v1/dictionary", params={"size": 100})).json()
    assert dictionary["total"] == len(dictionary["items"])
    assert dictionary["total"] >= 40
    assert dictionary["items"] == sorted(
        dictionary["items"], key=lambda word: (word["slug"], word["language_code"], word["id"])
    )

    english_b = (await client.get("/api/v1/dictionary", params={"lang": "en", "letter": "b"})).json()
    assert english_b["items"] and all(
        word["language_code"] == "en" and word["lemma"].lower().startswith("b")
        for word in english_b["items"]
    )

    search_result = (await client.get("/api/v1/dictionary", params={"q": "olma"})).json()
    assert any(word["lemma"] == "apple" for word in search_result["items"])

    ai_terms = {w["lemma"] for w in (await client.get("/api/v1/ai-terms")).json()}
    assert {"prompt", "LLM", "vibe coding", "hallucination"} <= ai_terms
    assert "run" not in ai_terms
    new = (await client.get("/api/v1/new-words", params={"lang": "tr", "limit": 2})).json()
    assert len(new) == 2 and all(w["language_code"] == "tr" for w in new)
    sitemap = (await client.get("/api/v1/sitemap-words")).json()
    assert {"language_code": "uz", "slug": "o'g'il"} in [
        {"language_code": s["language_code"], "slug": s["slug"]} for s in sitemap
    ]


async def test_quota_endpoint(client):
    data = (await client.get("/api/v1/me/quota")).json()
    assert data["plan"] == "anon"
    assert data["usage"]["ai_explain"] == {"used": 0, "limit": 5}
