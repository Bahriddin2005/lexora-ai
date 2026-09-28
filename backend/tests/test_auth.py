from tests.conftest import make_user


async def test_register_login_me_logout(client):
    data = await make_user(client, "Ali@Example.com")
    assert data["user"]["email"] == "ali@example.com"
    assert data["user"]["role"] == "user"
    assert client.cookies.get("lx_access")

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "ali@example.com"

    assert (await client.post("/api/v1/auth/logout")).status_code == 204
    client.cookies.clear()
    assert (await client.get("/api/v1/auth/me")).status_code == 401

    bad = await client.post("/api/v1/auth/login", json={"email": "ali@example.com", "password": "wrong-pass"})
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "invalid_credentials"

    ok = await client.post("/api/v1/auth/login", json={"email": "ali@example.com", "password": "secret123"})
    assert ok.status_code == 200
    token = ok.json()["access_token"]
    client.cookies.clear()
    bearer = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert bearer.status_code == 200


async def test_duplicate_email_and_validation(client):
    await make_user(client, "dup@example.com")
    resp = await client.post(
        "/api/v1/auth/register", json={"email": "dup@example.com", "password": "secret123"}
    )
    assert resp.status_code == 409
    short = await client.post("/api/v1/auth/register", json={"email": "x@example.com", "password": "123"})
    assert short.status_code == 422
    assert short.json()["error"]["code"] == "validation_error"


async def test_refresh_rotates_token(client):
    await make_user(client, "r@example.com")
    old_refresh = client.cookies.get("lx_refresh")
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 200
    new_refresh = client.cookies.get("lx_refresh")
    assert new_refresh and new_refresh != old_refresh

    client.cookies.set("lx_refresh", old_refresh)
    reused = await client.post("/api/v1/auth/refresh")
    assert reused.status_code == 401


async def test_update_profile(user_client):
    resp = await user_client.patch("/api/v1/auth/me", json={"display_name": "Malika", "ui_language": "ru"})
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Malika"
    assert resp.json()["ui_language"] == "ru"


async def test_languages_and_health(client):
    langs = (await client.get("/api/v1/languages")).json()
    assert [lang["code"] for lang in langs] == ["uz", "en", "ru", "tr"]
    assert (await client.get("/healthz")).json() == {"status": "ok"}
