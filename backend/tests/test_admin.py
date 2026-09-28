from sqlalchemy import select

from app.models import User
from tests.conftest import make_user


async def test_permissions(client, seeded):
    assert (await client.get("/api/v1/admin/stats")).status_code == 401
    await make_user(client)
    assert (await client.get("/api/v1/admin/stats")).status_code == 403


async def test_editor_workflow(editor_client, seeded, fake):
    client = editor_client
    # A user searches for a missing word; AI makes a draft.
    from app.ai.schemas import Verification

    fake.verdicts["gaslight"] = Verification(verdict="review", confidence=0.5, issues=["check uz"])
    fake.invalid_terms.add("nonexistentterm")
    await client.get("/api/v1/search", params={"q": "gaslight", "from": "en"})
    await client.get("/api/v1/search", params={"q": "nonexistentterm"})

    queue = (await client.get("/api/v1/admin/moderation")).json()
    row = next(r for r in queue["items"] if r["lemma"] == "gaslight")
    assert row["status"] == "draft"
    assert row["demand"] >= 1

    detail = (await client.get(f"/api/v1/admin/words/{row['id']}")).json()
    assert detail["versions"][0]["reason"] == "ai:generate"
    form = detail["form"]
    form["senses"][0]["definitions"]["uz"] = "aldab, odamni oʻziga ishonmaydigan qilmoq"
    form["senses"][0]["pos"] = "verb"
    updated = (
        await client.put(f"/api/v1/admin/words/{row['id']}", json={"entry": form, "reason": "fixed uz"})
    ).json()
    assert updated["entry"]["senses"][0]["definitions"]["uz"].startswith("aldab")
    assert updated["entry"]["version"] == 2
    assert updated["versions"][0]["changed_by"] == "editor@example.com"

    published = (await client.post(f"/api/v1/admin/words/{row['id']}/publish")).json()
    assert published["entry"]["status"] == "published"
    assert (await client.get("/api/v1/words/en/gaslight")).status_code == 200

    old = (await client.get(f"/api/v1/admin/words/{row['id']}/versions/1")).json()
    assert old["status"] == "draft"

    missing = (await client.get("/api/v1/admin/missing-words")).json()
    assert "nonexistentterm" in [m["normalized"] for m in missing]
    assert "gaslight" not in [m["normalized"] for m in missing]

    stats = (await client.get("/api/v1/admin/stats")).json()
    assert stats["words"]["by_status"]["published"] >= 40
    assert stats["ai_calls_7d"] >= 2

    usage = (await client.get("/api/v1/admin/ai-usage")).json()
    assert {a["agent"] for a in usage["by_agent"]} >= {"entry", "verify"}

    # Editors cannot manage users or languages.
    assert (await client.get("/api/v1/admin/users")).status_code == 403


async def test_create_generate_regenerate_delete(admin_client, seeded):
    client = admin_client
    created = await client.post("/api/v1/admin/words", json={"language_code": "uz", "lemma": "kitobxon"})
    assert created.status_code == 201
    word_id = created.json()["entry"]["id"]
    assert created.json()["entry"]["status"] == "draft"
    assert (
        await client.post("/api/v1/admin/words", json={"language_code": "uz", "lemma": "kitobxon"})
    ).status_code == 409

    job = (await client.post("/api/v1/admin/words/generate", json={"term": "moonshot", "lang": "en"})).json()
    assert (await client.get(f"/api/v1/jobs/{job['id']}")).json()["status"] == "done"

    regen = (await client.post(f"/api/v1/admin/words/{word_id}/regenerate")).json()
    assert (await client.get(f"/api/v1/jobs/{regen['id']}")).json()["status"] == "done"
    detail = (await client.get(f"/api/v1/admin/words/{word_id}")).json()
    assert detail["entry"]["senses"]
    assert detail["versions"][0]["reason"] == "ai:regenerate"

    listing = (await client.get("/api/v1/admin/words", params={"lang": "uz", "q": "kitob"})).json()
    assert {r["lemma"] for r in listing["items"]} == {"kitob", "kitobxon"}

    assert (await client.delete(f"/api/v1/admin/words/{word_id}")).status_code == 204
    assert (await client.get(f"/api/v1/admin/words/{word_id}")).status_code == 404


async def test_reports_users_languages(admin_client, seeded, db):
    client = admin_client
    run = (await client.get("/api/v1/words/en/run")).json()
    await client.post("/api/v1/reports", json={"word_id": run["id"], "reason": "other", "comment": "typo"})
    reports = (await client.get("/api/v1/admin/reports")).json()
    assert reports["total"] == 1
    rid = reports["items"][0]["id"]
    assert (await client.patch(f"/api/v1/admin/reports/{rid}", json={"status": "resolved"})).json()[
        "status"
    ] == "resolved"
    assert (await client.get("/api/v1/admin/reports")).json()["total"] == 0

    users = (await client.get("/api/v1/admin/users")).json()
    me = users["items"][0]
    assert me["email"] == "admin@example.com"
    assert (
        await client.patch(f"/api/v1/admin/users/{me['id']}", json={"is_active": False})
    ).status_code == 400

    other = User(email="u2@example.com", password_hash="x")
    db.add(other)
    await db.commit()
    patched = await client.patch(f"/api/v1/admin/users/{other.id}", json={"plan": "pro", "role": "editor"})
    assert patched.json()["plan"] == "pro"
    assert (
        await db.scalar(
            select(User.role).where(User.email == "u2@example.com").execution_options(populate_existing=True)
        )
    ) == "editor"

    new_lang = {"code": "kk", "name": "Kazakh", "native_name": "Қазақша", "script": "Cyrl", "flag": "🇰🇿"}
    assert (await client.post("/api/v1/admin/languages", json=new_lang)).status_code == 201
    codes = [lang["code"] for lang in (await client.get("/api/v1/languages")).json()]
    assert "kk" in codes
    await client.patch("/api/v1/admin/languages/kk", json={"is_active": False})
    assert "kk" not in [lang["code"] for lang in (await client.get("/api/v1/languages")).json()]
