from sqlalchemy import func, select

from app.ai.schemas import Verification
from app.models import AIGeneration, Word, WordVersion
from tests.conftest import make_user


async def search(client, q, **params):
    resp = await client.get("/api/v1/search", params={"q": q, **params})
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_unknown_word_is_generated(client, seeded, db):
    data = await search(client, "vibecheck", **{"from": "en"})
    assert data["results"] == []
    job = data["job"]
    assert job["status"] == "queued"

    done = (await client.get(f"/api/v1/jobs/{job['id']}")).json()
    assert done["status"] == "done"
    assert done["word"] == {"language_code": "en", "slug": "vibecheck"}

    entry = (await client.get("/api/v1/words/en/vibecheck")).json()
    assert entry["status"] == "ai_generated"
    assert entry["confidence"] == 0.85
    assert entry["senses"][0]["translations"]["uz"][0]["text"] == "vibecheck-uz"
    assert entry["sources"][0]["name"] == "Google Gemini (AI)"

    versions = await db.scalar(select(func.count()).select_from(WordVersion))
    assert versions >= 1
    agents = set((await db.scalars(select(AIGeneration.agent))).all())
    assert {"entry", "verify"} <= agents

    again = await search(client, "vibecheck")
    assert again["results"][0]["lemma"] == "vibecheck"
    assert again["job"] is None


async def test_low_confidence_goes_to_draft(client, seeded, fake, db):
    fake.verdicts["doubtful"] = Verification(verdict="review", confidence=0.4, issues=["unsure"])
    job = (await search(client, "doubtful", **{"from": "en"}))["job"]
    result = (await client.get(f"/api/v1/jobs/{job['id']}")).json()
    assert result["status"] == "draft"
    assert result["word"] is None
    assert (await db.scalar(select(Word.status).where(Word.normalized == "doubtful"))) == "draft"
    assert (await client.get("/api/v1/words/en/doubtful")).status_code == 404

    # The next search does not call the AI again: the draft already exists.
    calls_before = len(fake.calls)
    job2 = (await search(client, "doubtful", **{"from": "en"}))["job"]
    assert (await client.get(f"/api/v1/jobs/{job2['id']}")).json()["status"] == "draft"
    assert len(fake.calls) == calls_before


async def test_rejected_and_not_a_word(client, seeded, fake):
    fake.verdicts["wrongword"] = Verification(verdict="reject", confidence=0.1)
    job = (await search(client, "wrongword", **{"from": "en"}))["job"]
    assert (await client.get(f"/api/v1/jobs/{job['id']}")).json()["status"] == "rejected"

    fake.invalid_terms.add("qwrtz")
    job = (await search(client, "qwrtz", **{"from": "en"}))["job"]
    result = (await client.get(f"/api/v1/jobs/{job['id']}")).json()
    assert result["status"] == "not_a_word"
    assert result["suggestions"] == ["test"]


async def test_ai_failure_marks_job_failed(client, seeded, fake):
    fake.fail = True
    job = (await search(client, "brokenai", **{"from": "en"}))["job"]
    assert (await client.get(f"/api/v1/jobs/{job['id']}")).json()["status"] == "failed"


async def test_generation_quota_for_anonymous(client, seeded):
    statuses = []
    for term in ("alpha", "bravo", "charlie", "delta"):
        data = await search(client, f"{term}zz", **{"from": "en"})
        statuses.append(data["job"]["status"] if data["job"] else data["notice"])
    assert statuses == ["queued", "queued", "queued", "quota_exceeded"]


async def test_non_words_do_not_trigger_ai(client, seeded):
    data = await search(client, "12345")
    assert data["job"] is None


async def test_explain_stream_and_cache(client, seeded, fake):
    resp = await client.post("/api/v1/words/en/run/explain", json={"lang": "uz", "level": "simple"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    assert '"delta": "run"' in body
    assert '"done": true, "cached": false' in body

    stream_calls = [c for c in fake.calls if c[0] == "stream"]
    assert stream_calls[0][1]["explain_lang"] == "Uzbek (Latin script)"

    cached = await client.post("/api/v1/words/en/run/explain", json={"lang": "uz", "level": "simple"})
    assert '"cached": true' in cached.text
    assert "**run** — sodda izoh." in cached.text
    assert len([c for c in fake.calls if c[0] == "stream"]) == 1


async def test_explain_quota(client, seeded):
    for level in ("simple", "detailed"):
        for i in range(3):
            resp = await client.post(
                "/api/v1/words/en/run/explain", json={"lang": "uz", "level": level, "question": f"q{i}?"}
            )
            if resp.status_code == 429:
                assert resp.json()["error"]["code"] == "quota_exceeded"
                return
    raise AssertionError("anonymous explain quota (5/day) was not enforced")


async def test_translate_dictionary_then_ai(client, seeded, fake):
    resp = await client.post("/api/v1/translate", json={"text": "run", "source": "auto", "target": "uz"})
    data = resp.json()
    assert data["translation"] == "yugurmoq"
    assert data["dictionary"]["slug"] == "run"
    assert "chopmoq" in data["alternatives"]

    sentence = {"text": "Knowledge is power, they say.", "source": "en", "target": "uz"}
    first = (await client.post("/api/v1/translate", json=sentence)).json()
    assert first["translation"] == "[uz] Knowledge is power, they say."
    assert first["cached"] is False
    second = (await client.post("/api/v1/translate", json=sentence)).json()
    assert second["cached"] is True

    too_long = await client.post("/api/v1/translate", json={"text": "a" * 1200, "target": "uz"})
    assert too_long.json()["error"]["code"] == "text_too_long"
    same = await client.post("/api/v1/translate", json={"text": "salom", "source": "uz", "target": "uz"})
    assert same.status_code == 400


async def test_tts_is_cached(client, seeded, fake):
    resp = await client.get("/api/v1/tts", params={"text": "run", "lang": "en", "accent": "US"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/wav"
    assert resp.content[:4] == b"RIFF"
    await client.get("/api/v1/tts", params={"text": "run", "lang": "en", "accent": "US"})
    assert len([c for c in fake.calls if c[0] == "tts"]) == 1


async def test_ai_unavailable(client, seeded, monkeypatch):
    from app.ai import provider as provider_module

    provider_module.set_provider(None)
    monkeypatch.setattr(provider_module, "_instance", None)
    monkeypatch.setattr(provider_module, "build_provider", lambda: None)
    data = await search(client, "newthing", **{"from": "en"})
    assert data["ai_available"] is False
    assert data["notice"] == "ai_unavailable"
    resp = await client.post("/api/v1/words/en/run/explain", json={})
    assert resp.status_code == 503
    await make_user(client)
