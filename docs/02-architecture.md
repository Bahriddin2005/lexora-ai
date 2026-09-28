# 02 — Arxitektura

## 1. MVP: monolit + worker
```
                    ┌──────────────────────────────┐
  Brauzer ─────────▶│  Next.js (frontend, SSR)      │
                    │  /api/* → rewrite → backend   │
                    └──────────────┬───────────────┘
                                   │ HTTP (same-origin cookie)
                    ┌──────────────▼───────────────┐
                    │  FastAPI (backend monolit)    │
                    │  api/v1 · services · ai       │
                    └──┬─────────┬────────┬────────┘
                       │         │        │
            ┌──────────▼──┐  ┌───▼────┐ ┌─▼─────────────┐
            │ PostgreSQL  │  │ Redis  │ │ Object storage │
            │ (+pg_trgm)  │  │ cache, │ │ (MinIO / S3 /  │
            │ asosiy DB   │  │ kvota, │ │  lokal disk)   │
            └──────▲──────┘  │ broker,│ └───────▲───────┘
                   │         │ trend  │         │
            ┌──────┴─────────┴───▲────┘         │
            │  Celery worker      │─────────────┘
            │  AI generatsiya, TTS, import      │
            └──────────┬──────────┘
                       │
                ┌──────▼───────┐
                │ Google Gemini │ (LLMProvider orqali)
                └──────────────┘
```

| Komponent | Texnologiya | Vazifa |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS | SSR sahifalar, SEO, UI |
| Backend | FastAPI, SQLAlchemy 2 (async, asyncpg), Pydantic v2 | REST API, biznes-logika |
| DB | PostgreSQL 16 + `pg_trgm`, `unaccent` | Asosiy ma’lumotlar, fuzzy qidiruv |
| Cache/broker | Redis 7 | Kesh, kvotalar, rate limit, job holati, trending, Celery broker |
| Worker | Celery | AI generatsiya, TTS, katta importlar |
| Storage | S3-compatible (MinIO dev’da) yoki lokal disk | Audio fayllar |
| AI | Google Gemini (`google-genai`) | Entry/Verification/Explain/Translate/Intent/TTS |
| Deploy | Docker Compose → keyin Kubernetes | |

## 2. Backend qatlamlari
```
app/
├── api/v1/        # HTTP qatlami: validatsiya, auth, response modeli. Biznes-logika yo‘q.
├── services/      # Biznes-logika: search, dictionary, translation, tts, quotas, trending, storage
├── ai/            # LLMProvider, GeminiProvider, FakeProvider, prompts, agents, pipeline
├── models/        # SQLAlchemy ORM
├── schemas/       # Pydantic DTO
├── core/          # config, db, redis, security, errors, deps
└── workers/       # Celery app va tasklar (servislarni chaqiradi)
```
Qoidalar: API → services → models; AI agentlar faqat `LLMProvider` orqali; servislar sinxron HTTP’ga bog‘liq emas (worker ham ishlatadi).

## 3. Asosiy oqimlar

### 3.1 Qidiruv (lug‘atda bor)
```
GET /api/v1/search?q=run
  → intent parser (regex) → {term: run}
  → normalize(term, lang) har faol til uchun
  → DB: exact → forms → reverse → (prefix) → trigram
  → search_logs INSERT, trending ZINCRBY
  → 200 {results, did_you_mean}
```

### 3.2 Qidiruv (lug‘atda yo‘q) → AI generatsiya
```
GET /api/v1/search?q=vibecoding
  → natija yo‘q, did_you_mean yo‘q, so‘z "haqiqiyga o‘xshaydi"
  → kvota tekshiruvi (ai_generate)
  → Redis lock gen:{lang}:{key} (takroriy generatsiyadan himoya)
  → job yaratiladi (Redis hash job:{id}) → Celery task (yoki inline rejim)
  → 200 {results: [], job: {id, status: queued}}
Frontend: GET /api/v1/jobs/{id} ni 1.5 s da polling
Worker: EntryAgent → VerificationAgent → DB ga yozish (status ai_generated/draft/rejected) → job: done
```

### 3.3 AI izoh
`POST /api/v1/words/{lang}/{slug}/explain` → kvota → kesh (ai_generations.input_hash) → bo‘lmasa Gemini stream → SSE `data: {"delta": "..."}` → oxirida keshga yoziladi.

### 3.4 Tarjima
`POST /api/v1/translate` → qisqa matn (≤ 3 so‘z) bo‘lsa lug‘atdan (AI’siz, bepul) → bo‘lmasa `ai_generations` keshi (`input_hash`) → kvota → Gemini (structured JSON) → natija log/keshga yoziladi.

### 3.5 TTS
`GET /api/v1/tts?text=&lang=` → storage kaliti `tts/{sha256}.wav` → bor bo‘lsa qaytariladi → yo‘q bo‘lsa Gemini TTS → PCM → WAV → storage → qaytariladi.

## 4. Job rejimi
`TASKS_MODE=celery` (prod): tasklar Celery orqali. `TASKS_MODE=inline` (dev/test): so‘rov ichida bajariladi — test deterministik bo‘ladi.

## 5. Autentifikatsiya
- Access JWT (15 daq) — cookie `lx_access` (httpOnly, SameSite=Lax) yoki `Authorization: Bearer`.
- Refresh token (30 kun) — cookie `lx_refresh` (path `/api/v1/auth`), DB’da hash holida, har refresh’da rotatsiya.
- Next.js `/api/*` ni backendga rewrite qiladi → cookie’lar same-origin.
- SSR paytida Next.js server kelgan cookie’larni backendga uzatadi (`BACKEND_URL`).

## 6. Konfiguratsiya
Barcha sozlamalar env orqali (`.env.example`): `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `GEMINI_API_KEY`,
`GEMINI_MODEL_SMART`, `GEMINI_MODEL_FAST`, `GEMINI_MODEL_TTS`, `AI_PROVIDER` (`gemini`|`fake`),
`TASKS_MODE`, `STORAGE_BACKEND` (`local`|`s3`), `S3_*`, `CORS_ORIGINS`, `AI_PUBLISH_THRESHOLD`.

## 7. Graceful degradation
- Gemini ishlamasa: qidiruv/so‘z sahifasi ishlaydi; AI tugmalari 503 `ai_unavailable` qaytaradi, UI xabar ko‘rsatadi.
- TTS ishlamasa: frontend `speechSynthesis` ga o‘tadi.
- Redis ishlamasa: `/readyz` 503; kvota tekshiruvi fail-closed (AI), qidiruv ishlaydi.

## 8. Scale yo‘li (keyingi fazalar)
| Bosqich | O‘zgarish |
|---|---|
| 100k+ so‘z, 20 til | Postgres read replica, CDN, so‘z sahifalarini ISR bilan keshlash |
| 1M+ so‘z, 100 til | OpenSearch (ko‘p tilli analyzer, fuzzy, synonym), `search` servisi indeksni yangilaydi (outbox pattern) |
| Live Words oqimi | Kafka/Redpanda: `raw_mentions` → `candidates` → `verified` topiclar; collector’lar alohida servis |
| Yuqori AI yuklama | Agentlarni alohida worker navbatlariga ajratish (`ai.entry`, `ai.verify`, `tts`), provayderlar fallback’i |
| Mobil / bot | Flutter ilova, Telegram bot, browser extension — bir xil `/api/v1` |

## 9. Kuzatuv (observability)
- Strukturali JSON log (request id).
- `/healthz` (process tirik), `/readyz` (DB + Redis).
- `ai_generations` jadvali: token/narx/latency → admin "AI usage".
- Keyin: Prometheus metrikalar, Sentry, OpenTelemetry.
