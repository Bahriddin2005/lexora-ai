import os
import tempfile

os.environ["ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret-key-that-is-long-enough-1234"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://lexora:lexora@localhost:5432/lexora_test"
)
os.environ["DB_NULL_POOL"] = "true"
os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")
os.environ["AI_PROVIDER"] = "fake"
os.environ["TASKS_MODE"] = "inline"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["STORAGE_LOCAL_DIR"] = tempfile.mkdtemp(prefix="lexora-test-storage-")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select, text  # noqa: E402

from app import models  # noqa: E402,F401
from app.ai import provider as provider_module  # noqa: E402
from app.ai.fake import FakeProvider  # noqa: E402
from app.core.db import Base, SessionLocal, engine  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.seed.demo import seed_demo  # noqa: E402
from app.seed.languages import seed_languages  # noqa: E402
from app.services import languages as languages_service  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
async def _schema():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_languages(session)
    yield


@pytest.fixture(autouse=True)
async def _clean():
    tables = [t.name for t in Base.metadata.sorted_tables if t.name != "languages"]
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))
    await get_redis().flushdb()
    languages_service.invalidate()
    fake = FakeProvider()
    provider_module.set_provider(fake)
    yield
    provider_module.set_provider(None)


@pytest.fixture
def fake() -> FakeProvider:
    provider = provider_module.get_provider()
    assert isinstance(provider, FakeProvider)
    return provider


@pytest.fixture
async def db():
    async with SessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def seeded():
    async with SessionLocal() as session:
        await seed_demo(session)


async def make_user(
    client: AsyncClient, email: str = "user@example.com", role: str = "user", plan: str = "free"
):
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": "secret123"})
    assert resp.status_code == 201, resp.text
    if role != "user" or plan != "free":
        async with SessionLocal() as session:
            user = await session.scalar(select(User).where(User.email == email))
            user.role = role
            user.plan = plan
            await session.commit()
    return resp.json()


@pytest.fixture
async def user_client(client):
    await make_user(client)
    return client


@pytest.fixture
async def editor_client(client):
    await make_user(client, "editor@example.com", role="editor")
    return client


@pytest.fixture
async def admin_client(client):
    await make_user(client, "admin@example.com", role="admin")
    return client
