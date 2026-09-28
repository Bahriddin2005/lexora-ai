# 13 — AI coding agent uchun tasklar

Har task: **maqsad → fayllar → done mezoni**. Bitta task = bitta PR. Avval `CLAUDE.md` va tegishli `docs/` bo‘limini o‘qing.
Umumiy done mezoni: `make lint test` yashil, yangi logika uchun test bor, API o‘zgarsa `04-api-spec.md` yangilangan.

## Faza 2 — MVP (bajarilgan, namuna sifatida)
| # | Task | Asosiy fayllar |
|---|---|---|
| 2.1 | Backend skeleti, config, DB, Alembic, healthz | `backend/app/main.py`, `app/core/*`, `alembic/` |
| 2.2 | Auth (JWT cookie, refresh rotatsiya, rollar) | `app/api/v1/auth.py`, `app/core/security.py` |
| 2.3 | Normalizatsiya + testlar | `app/services/normalization.py`, `tests/test_normalization.py` |
| 2.4 | So‘z modeli, entry serializatsiya, `GET /words/...` | `app/models/dictionary.py`, `app/services/dictionary.py` |
| 2.5 | Qidiruv, suggest, did-you-mean, intent parser | `app/services/search.py`, `app/services/intent.py` |
| 2.6 | AI provayder, Entry/Verify agentlar, jobs | `app/ai/*`, `app/services/generation.py` |
| 2.7 | Explain SSE, tarjima, TTS, kvotalar | `app/api/v1/words.py`, `translate.py`, `tts.py`, `app/services/quotas.py` |
| 2.8 | Favorites, reports, trending, new, ai-terms | `app/api/v1/me.py`, `discover.py` |
| 2.9 | Admin API | `app/api/v1/admin/*` |
| 2.10 | Frontend: sahifalar, i18n, SEO | `frontend/src/app/*` |
| 2.11 | Admin UI | `frontend/src/app/admin/*` |

## Faza 3 — AI (7–10 hafta)
**3.1 Uz izohlari backfill.** Maqsad: `sense_definitions` da `uz` yo‘q bo‘lgan top-N (zipf bo‘yicha) sense’lar uchun batch generatsiya.
Fayllar: `app/workers/tasks.py` (`backfill_definitions`), `app/ai/prompts/definitions.py`, `scripts/backfill.py`.
Done: 100 ta sense’lik dry-run, `ai_generations` da xarajat, natijalar `ai_generated` statusda, test FakeProvider bilan.

**3.2 Kontekstli tarjima.** `POST /translate/in-context {sentence, word_index}` → so‘zning aynan shu gapdagi ma’nosi (sense_id bilan moslash).
Done: 10 ta golden test (masalan "bank" daryo qirg‘og‘i vs moliya).

**3.3 AI chat.** So‘z sahifasida ko‘p turli suhbat (`/words/{lang}/{slug}/chat`, SSE, tarix 10 ta xabar). Kvota: explain bilan umumiy.

**3.4 Misollar backfill.** Misolsiz sense’lar uchun 2 ta misol + uz/ru tarjimasi. Done: ExampleAgent, sifat tekshiruvi (so‘z misolda borligini tekshirish).

**3.5 Typo correction v2.** Klaviatura masofasi (QWERTY/ЙЦУКЕН), fonetik (Double Metaphone en), kirill↔lotin xato klaviatura ("ghbdtn" → "привет").
Done: `tests/test_typos.py` da 50 ta holat, ≥ 90% top-1.

**3.6 Sinonim/antonim boyitish.** WordNet (en) importi + AI tasdiqlash.

## Faza 4 — Live Dictionary (11–14 hafta)
**4.1** `live_candidates`, `live_mentions` jadvallari + Alembic migratsiya.
**4.2** Collector: `search_logs` (found=false) agregatori — har 10 daqiqa, Celery beat.
**4.3** Collector: Wikipedia EventStreams (recentchange) consumer — yangi sahifa sarlavhalaridan nomzodlar.
**4.4** Collector: RSS (sozlanadigan ro‘yxat), HN API.
**4.5** Skorlash (11-live-words.md formula), `score ≥ T` → generatsiya pipeline (mavjud `generation.py` qayta ishlatiladi).
**4.6** Gemini Google Search grounding bilan tekshiruv (manba URL’lari `word_sources` ga).
**4.7** `/live` sahifa + `GET /live?since=` API.
Done (faza): e2e — soxta RSS’dagi yangi termin 2 manbada → 10 daqiqada `ai_generated` + `new` tegi bilan chiqadi.

## Faza 5 — Learning (15–18 hafta)
**5.1** `learning_items`, `review_logs` + `py-fsrs` integratsiyasi; ❤️ → learning item avtomatik.
**5.2** `/learn/queue`, `/learn/review` API + testlar (FSRS jadvali deterministik).
**5.3** Flashcard UI (klaviatura: 1–4 baholash, Space — ag‘darish).
**5.4** Test (4 variant) generatori — chalg‘ituvchilar tanlash.
**5.5** Cloze (gap) mashqi, Listening (TTS), Speaking (STT — Gemini audio).
**5.6** Progress sahifasi, streak.

## Faza 6 — Scale
**6.1** Developer API: `api_keys` (hash + prefix), `X-API-Key` middleware, tarif limitlari, `/developers` sahifa.
**6.2** To‘lovlar: Payme/Click webhook’lari, `subscriptions`, plan avtomatik yangilanishi.
**6.3** Telegram bot (aiogram): inline qidiruv `@lexora_bot run`, kunlik so‘z.
**6.4** Browser extension: so‘zni belgilash → popup (API).
**6.5** Flutter ilova: qidiruv, so‘z sahifasi, favorites, learning (offline kesh).
**6.6** OpenSearch: indeks sxemasi, outbox + indexer worker, `SearchBackend` interfeysi orqali almashtirish.
**6.7** Yangi 16 til (12-roadmap.md) — har biri alohida task: normalizatsiya + import + backfill.

## Agentga ko‘rsatma shabloni
```
Kontekst: Lexora AI, docs/<bo‘lim>.md.
Task: <raqam va nom>.
Cheklovlar: CLAUDE.md konvensiyalari; mavjud servislarni qayta ishlating (<fayllar>); yangi dependency — asoslang.
Done: <mezonlar>; make lint test yashil; docs yangilangan.
```
