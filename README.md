# Lexora AI

> **Dunyo tillari bitta joyda.** Oddiy tarjimon emas — AI asosidagi global, tirik lug‘at ekotizimi:
> Dictionary + Translator + AI + Learning + Live Language Database.

`run` deb yozsangiz, Lexora faqat "yugurmoq" demaydi: ma’nolar (sense) bo‘yicha tarjimalar, talaffuz (IPA + audio),
so‘z turkumi, CEFR, chastota, misollar, sinonim/antonimlar, iboralar, etimologiya va "🤖 AI bilan tushunish" beradi.
Lug‘atda yo‘q so‘zni AI tayyorlaydi, boshqa model tekshiradi, ishonchlilik darajasi va moderatsiya bilan chiqaradi.

MVP tillari: 🇺🇿 o‘zbek ⇄ 🇬🇧 ingliz ⇄ 🇷🇺 rus ⇄ 🇹🇷 turk (yangi til — `languages` jadvaliga yozuv).

## Imkoniyatlar (MVP)
- 🔍 **Qidiruv**: exact → shakllar (`ran` → `run`) → teskari (`yugurmoq` → `run`) → prefix → "**beautiful** nazarda tutdingizmi?"; autocomplete; ovozli qidiruv (brauzer).
- 💬 **Tabiiy til so‘rovlari**: `rus tilida "maktab" nima?`, `cringe nima degani?`, `python so‘zi dasturlashda nimani anglatadi?`, `2026-yilda AI sohasida chiqqan yangi terminlarni ko‘rsat`.
- 🤖 **AI**: yangi so‘z generatsiyasi (EntryAgent → VerificationAgent → confidence bo‘yicha nashr/qoralama), stream qilinadigan AI izoh, kontekstli tarjima, TTS — Google Gemini, `LLMProvider` interfeysi orqali.
- 🔄 **Tarjimon**: qisqa matn — lug‘atdan (bepul), qolgani — AI (keshlanadi).
- ❤️ Mening lug‘atim, 🚩 xato haqida xabar, 🔥 real-vaqt trending, 🌍 yangi so‘zlar, AI terminlar.
- 🛠 **Admin panel**: moderatsiya navbati, to‘liq muharrir (versiyalar bilan), reportlar, topilmagan so‘zlar, foydalanuvchilar, tillar, AI xarajatlari.
- 🔐 JWT (httpOnly cookie) + refresh rotatsiya, rollar (user/editor/admin), kunlik kvotalar va rate limit.
- 🌐 UI: o‘zbek (default), ingliz, rus; dark mode; SEO (SSR, JSON-LD, sitemap).

## Texnologiyalar
| Qism | Stack |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2, Celery |
| DB / cache | PostgreSQL 16 (`pg_trgm`), Redis 7 |
| AI | Google Gemini (`google-genai`): `gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-3.8-flash-lite-tts` |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4 |
| Storage | S3-compatible (MinIO) yoki lokal disk (audio) |
| Test | pytest, Vitest, Playwright |

## Tez start (Docker)
```bash
cp .env.example .env            # GEMINI_API_KEY ni kiriting (yoki AI_PROVIDER=fake)
make up                          # docker compose up --build + demo lug‘at
docker compose exec backend python -m scripts.create_admin you@example.com secret123
```
- Sayt: http://localhost:3000 · API: http://localhost:8000/docs · MinIO: http://localhost:9001

## Lokal ishlab chiqish
Talablar: Python 3.12 + [uv](https://docs.astral.sh/uv/), Node 22, PostgreSQL 16, Redis 7 (`make dev-db` ularni Docker’da ko‘taradi).
```bash
# backend
cp .env.example backend/.env    # kerak bo‘lsa DATABASE_URL/REDIS_URL ni o‘zgartiring
cd backend
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed                   # 4 til + 42 ta demo so‘z
uv run python -m scripts.create_admin admin@lexora.uz admin12345
uv run uvicorn app.main:app --reload --port 8000

# frontend (boshqa terminalda)
cd frontend
npm install
BACKEND_URL=http://localhost:8000 npm run dev    # http://localhost:3000
```

### Gemini API kaliti
1. https://aistudio.google.com/apikey dan kalit oling.
2. `.env` / `backend/.env` ga `GEMINI_API_KEY=...` yozing (`AI_PROVIDER=gemini`).
3. Kalitsiz ishlatish uchun `AI_PROVIDER=fake` — deterministik soxta javoblar (demo va testlar uchun), `AI_PROVIDER=none` — AI o‘chiq (lug‘at ishlaydi).

Model nomlari `GEMINI_MODEL_SMART/FAST/TTS` orqali o‘zgartiriladi. Narxlar (xarajat hisobi uchun) — `backend/app/core/config.py::AI_PRICING`.

### Wiktionary importi
```bash
cd backend && uv sync --extra import
# https://kaikki.org dan JSONL yuklab oling (masalan English dictionary)
uv run python -m scripts.import_kaikki kaikki.org-dictionary-English.jsonl --lang en --limit 20000 --min-zipf 3
```
Ma’lumotlar CC BY-SA 4.0 — atributsiya `/about` sahifasida va har bir yozuvning "Manbalar" qismida.

## Testlar
```bash
make backend-lint backend-test   # ruff + 60+ pytest (Postgres va Redis kerak; AI — FakeProvider)
make frontend-check              # eslint + tsc + vitest
```
**E2E (Playwright)** ishlab turgan stack ustida: backend `AI_PROVIDER=fake` bilan, seed va admin (`admin@lexora.uz` / `admin12345`
yoki `E2E_ADMIN_EMAIL`/`E2E_ADMIN_PASSWORD`), frontend `:3000` da (`E2E_BASE_URL` bilan o‘zgartiriladi):
```bash
cd frontend && npx playwright install chromium && npx playwright test
```
CI (`.github/workflows/ci.yml`): backend (ruff, pytest, `alembic check`), frontend (lint, typecheck, vitest, build) va e2e.

## Tuzilma
```
backend/   FastAPI: app/api/v1 (HTTP) → app/services (logika) → app/models; app/ai (Gemini, agentlar, promptlar)
frontend/  Next.js: src/app (sahifalar, admin), src/components, src/lib (API client), src/i18n
docs/      Texnik hujjatlar: PRD, arxitektura, DB, API, AI agentlar, qidiruv, UX, admin, dizayn, roadmap
```
AI coding agentlar uchun: [`CLAUDE.md`](CLAUDE.md) va [`docs/13-agent-tasks.md`](docs/13-agent-tasks.md).

## Hujjatlar
[Umumiy ko‘rinish](docs/00-overview.md) · [PRD](docs/01-PRD.md) · [Arxitektura](docs/02-architecture.md) ·
[DB sxema](docs/03-database-schema.md) · [API](docs/04-api-spec.md) · [AI agentlar](docs/05-ai-agents.md) ·
[Qidiruv](docs/06-search.md) · [Sahifalar](docs/07-pages-and-ux.md) · [Admin](docs/08-admin-panel.md) ·
[Dizayn](docs/09-ui-design-system.md) · [Learning](docs/10-learning-srs.md) · [Live Words](docs/11-live-words.md) ·
[Roadmap](docs/12-roadmap.md)
