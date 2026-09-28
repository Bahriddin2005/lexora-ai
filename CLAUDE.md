# Lexora AI — AI coding agentlar uchun qo'llanma

Loyiha haqida: `docs/00-overview.md`. Har task oldidan tegishli `docs/` bo'limini o'qing; tasklar ro'yxati — `docs/13-agent-tasks.md`.

## Tuzilma
- `backend/` — FastAPI monolit (Python 3.12, uv). Qatlamlar: `api/v1` (HTTP) → `services` (biznes-logika) → `models` (SQLAlchemy). AI faqat `app/ai` dagi `LLMProvider` orqali.
- `frontend/` — Next.js App Router + TypeScript + Tailwind. `/api/*` backendga rewrite qilinadi.
- `docs/` — texnik hujjatlar (o'zbek tilida). API yoki sxema o'zgarsa, hujjatni ham yangilang.

## Buyruqlar
- `make dev-db` — Postgres + Redis (docker compose).
- `make backend-test` / `make backend-lint` — `cd backend && uv run pytest` / `uv run ruff check . && uv run ruff format --check .`
- `make migrate` — `cd backend && uv run alembic upgrade head`
- `make seed` — tillar + demo lug'at.
- `make frontend-check` — `cd frontend && npm run lint && npm run typecheck && npm run test`
- `make e2e` — Playwright (backend va frontend ishlab turgan bo'lishi kerak).

## Konvensiyalar
- Normalizatsiya faqat `app/services/normalization.py::normalize` orqali — DB kaliti va qidiruv kaliti bir xil bo'lishi shart.
- Yangi AI chaqiruv: `app/ai/agents/` da agent, `app/ai/prompts/` da versiyalangan prompt (`name@N`), Pydantic chiqish sxemasi, `ai_generations` ga log. Testlarda `FakeProvider`.
- Ommaviy API faqat `published` + `ai_generated` ni qaytaradi (`VISIBLE_STATUSES`).
- Xatolar `app/core/errors.py::AppError` orqali (`{"error": {"code", "message", "details"}}`).
- Admin o'zgarishlari `word_versions` ga snapshot yozadi (`services/dictionary.py::save_version`).
- Frontend matnlari `frontend/messages/{uz,en,ru}.json` da (uz — asosiy).
- Kodni atrofdagi kod uslubida yozing; izohlar qisqa.
