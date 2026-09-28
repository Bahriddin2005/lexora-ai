# 12 — Yo‘l xaritasi

Strategiya: birinchi versiyada "barcha tillar + butun internet + har soniya" ni birdan qurishga urinmaslik.
Avval **Uzbek 🇺🇿 ⇄ English 🇬🇧 ⇄ Russian 🇷🇺 ⇄ Turkish 🇹🇷** bilan kuchli MVP.

| Bosqich | Haftalar | Natija | Holat |
|---|---|---|---|
| **1. Foundation** | 1–2 | Nom, branding, UX/UI, DB arxitekturasi, API spetsifikatsiyasi (shu `docs/`) | ✅ |
| **2. MVP** | 3–6 | Login, tillar, qidiruv, tarjima, talaffuz, misollar, AI izoh, AI generatsiya, favorites, reports, trending, admin panel | ✅ (shu repo) |
| **3. AI** | 7–10 | Kontekstli tarjima (gap ichida so‘z), sinonim/antonim boyitish, AI chat ("so‘z bilan suhbat"), avtomatik misollar backfill, uz izohlari backfill, typo correction’ni yaxshilash (klaviatura-masofa, fonetik) | ⏳ |
| **4. Live Dictionary** | 11–14 | Collector → Verification → Moderation → Publishing pipeline, `/live` sahifa | ⏳ |
| **5. Learning** | 15–18 | Flashcards, testlar, progress, FSRS spaced repetition | ⏳ |
| **6. Scale** | 19+ | Flutter mobil ilova, Telegram bot, browser extension, public Developer API (kalitlar, tariflar), to‘lovlar (Payme/Click/Stripe), OpenSearch, CDN | ⏳ |

## Tillar kengayishi
`4 til → 20 til → 100+ til → Live Global Dictionary`
- 20 til: kk, ky, tg, tk, az, de, fr, es, it, ar, fa, zh, ja, ko, hi, ur (normalizatsiya qoidalari + Wiktionary import + AI backfill).
- Har yangi til uchun checklist: `languages` yozuvi → normalizatsiya qoidasi + testlar → import → AI backfill (top-5k) → UI tarjimasi (ixtiyoriy) → TTS tekshiruvi.

## MVP’dan keyingi darhol vazifalar
1. To‘liq Wiktionary importi (en top-20k, ru/tr top-10k, uz hammasi) — `scripts/import_kaikki.py`.
2. Uz izohlari AI backfill (top-5k inglizcha so‘z) — batch, moderatsiya bilan.
3. Parolni tiklash (SMTP), Google/Telegram login.
4. Prometheus/Sentry monitoring.
5. Yuklama testi (k6): 200 RPS qidiruv.

## Muvaffaqiyat mezonlari (MVP)
- 20 000+ so‘z, 4 til, "topilmadi" < 10%.
- p95 qidiruv < 150 ms.
- 100 ta beta foydalanuvchi, 30% haftalik qaytish.
