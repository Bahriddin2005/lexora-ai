# 04 — API spetsifikatsiyasi (`/api/v1`)

Interaktiv OpenAPI: backend ishga tushgach `http://localhost:8000/docs`.

## Umumiy qoidalar
- Format: JSON (UTF-8). Vaqt: ISO 8601 UTC.
- Auth: cookie `lx_access` (brauzer) yoki `Authorization: Bearer <access_token>` (API mijozlar).
- `slug` — so‘zning normalizatsiyalangan shakli, URL-encode qilingan (`o'g'il` → `o'g'il`, `break a leg` → `break%20a%20leg`).
- Ommaviy endpointlar faqat `published` va `ai_generated` yozuvlarni qaytaradi.

### Xato formati
```json
{ "error": { "code": "quota_exceeded", "message": "Kunlik AI izoh limiti tugadi", "details": {"kind": "ai_explain", "limit": 20, "reset_in": 3600} } }
```
| HTTP | code |
|---|---|
| 400 | `bad_request` |
| 401 | `unauthorized` |
| 403 | `forbidden` |
| 404 | `not_found` |
| 409 | `conflict` |
| 422 | `validation_error` |
| 429 | `quota_exceeded`, `rate_limited` |
| 503 | `ai_unavailable` |

## Auth
| Metod | Yo‘l | Tana | Javob |
|---|---|---|---|
| POST | `/auth/register` | `{email, password (≥8), display_name?}` | 201 `User` + cookie’lar |
| POST | `/auth/login` | `{email, password}` | 200 `{user, access_token}` + cookie’lar |
| POST | `/auth/refresh` | — (cookie `lx_refresh`) | 200 `{user, access_token}`, refresh rotatsiya |
| POST | `/auth/logout` | — | 204, cookie’lar o‘chiriladi |
| GET | `/auth/me` | — | `User` |
| PATCH | `/auth/me` | `{display_name?, ui_language?}` | `User` |

`User = {id, email, display_name, role, plan, ui_language, created_at}`

## Tillar
`GET /languages` → `[{code, name, native_name, script, direction, flag}]`

## Qidiruv
### `GET /search?q=&from=&to=&force_ai=false`
```json
{
  "query": "beutiful",
  "intent": {"type": "lookup", "term": "beutiful", "source_lang": null, "target_lang": "uz", "domain": null, "year": null},
  "results": [],
  "did_you_mean": [{"language_code": "en", "lemma": "beautiful", "slug": "beautiful", "score": 0.58}],
  "job": null,
  "ai_available": true
}
```
`results[]` = `WordSummary`:
```json
{"id": 1, "language_code": "en", "lemma": "run", "slug": "run", "entry_type": "word", "status": "published",
 "pos": ["verb", "noun"], "cefr_level": "A1", "short_definition": "to move swiftly on foot",
 "primary_translation": {"language_code": "uz", "text": "yugurmoq"}, "match": "exact"}
```
`match`: `exact` | `form` | `reverse` | `prefix` | `list`.
Topilmasa va so‘z haqiqiyga o‘xshasa: `"job": {"id": "…", "status": "queued"}`.
`intent.type = list_new_terms` bo‘lsa `results` — domen/yil bo‘yicha yangi so‘zlar.

### `GET /search/suggest?q=&lang=` → `[{language_code, lemma, slug, primary_translation}]` (≤ 8)
### `GET /jobs/{id}`
```json
{"id": "…", "status": "done", "word": {"language_code": "en", "slug": "vibecoding"}, "message": null, "suggestions": []}
```
`status`: `queued` | `running` | `done` | `draft` (moderatsiyaga yuborildi) | `not_a_word` | `failed`.

## So‘zlar
### `GET /words/{lang}/{slug}?explain_lang=uz` → `WordEntry`
```json
{
  "id": 1, "language_code": "en", "lemma": "run", "slug": "run", "entry_type": "word",
  "status": "published", "confidence": 1.0, "cefr_level": "A1", "frequency_zipf": 6.1,
  "tags": [], "etymology": {"en": "From Old English rinnan…"},
  "pronunciations": [{"ipa": "/rʌn/", "accent": "US", "audio_url": "/api/v1/tts?text=run&lang=en"}],
  "forms": [{"form": "ran", "tags": ["past"]}],
  "senses": [{
    "id": 10, "pos": "verb", "domain": null, "register": "neutral", "cefr_level": "A1",
    "definitions": {"en": "to move swiftly on foot", "uz": "oyoqda tez harakatlanmoq"},
    "translations": {"uz": [{"text": "yugurmoq", "is_primary": true, "note": null, "slug": "yugurmoq"}],
                     "ru": [{"text": "бежать", "is_primary": true}], "tr": [{"text": "koşmak", "is_primary": true}]},
    "examples": [{"text": "She runs every morning.", "translations": {"uz": "U har tong yuguradi."}}],
    "synonyms": ["sprint"], "antonyms": ["walk"]
  }],
  "relations": {"synonym": [{"text": "sprint", "slug": "sprint"}], "antonym": [], "related": [], "derived": [], "phrase": [{"text": "run out of"}]},
  "sources": [{"name": "Wiktionary", "url": "https://en.wiktionary.org/wiki/run", "license": "CC BY-SA 4.0"}],
  "is_favorite": false,
  "updated_at": "2026-09-28T10:00:00Z"
}
```
### `GET /words/{term}?lang=en` — qisqa alias (developer API): `GET /api/v1/words/hello`
### `POST /words/{lang}/{slug}/explain` → `text/event-stream`
Tana: `{"lang": "uz", "level": "simple" | "detailed", "question": "…?"}`
```
data: {"delta": "“Run” so‘zi asosan "}
data: {"delta": "“yugurmoq” ma’nosini beradi…"}
data: {"done": true, "cached": false}
```

## Tarjima va ovoz
### `POST /translate`
```json
// so‘rov
{"text": "Knowledge is power", "source": "auto", "target": "uz", "context": null}
// javob
{"translation": "Bilim — kuch", "detected_source": "en", "alternatives": ["Bilim kuchdir"],
 "notes": "Frensis Bekonga nisbat beriladigan ibora", "dictionary": null, "cached": false}
```
### `GET /tts?text=run&lang=en&voice=default` → `audio/wav` (keshlanadi; ≤ 200 belgi)

## Kashf qilish
| Yo‘l | Javob |
|---|---|
| `GET /trending?lang=&limit=20` | `[WordSummary + score]` (so‘nggi 24 soat, real-time) |
| `GET /new-words?lang=&limit=20&page=1` | `[WordSummary]` eng yangi qo‘shilganlar |
| `GET /ai-terms?limit=20` | `[WordSummary]` `ai` tegi yoki `domain=ai` |
| `GET /sitemap-words?page=1&size=5000` | `[{language_code, slug, updated_at}]` |

## Foydalanuvchi
| Metod | Yo‘l | Izoh |
|---|---|---|
| GET | `/me/favorites?page=` | `[WordSummary + saved_at]` |
| POST | `/me/favorites` | `{word_id}` → 201 |
| DELETE | `/me/favorites/{word_id}` | 204 |
| GET | `/me/quota` | `{plan, usage: {ai_explain: {used, limit}, …}}` |
| POST | `/reports` | `{word_id, sense_id?, reason, comment?}` → 201 (anonim ham mumkin) |

## Admin (`editor` yoki `admin`)
| Metod | Yo‘l | Rol | Izoh |
|---|---|---|---|
| GET | `/admin/stats` | editor | So‘zlar statuslar bo‘yicha, foydalanuvchilar, 24 soat qidiruvlar, top topilmaganlar, AI xarajati |
| GET | `/admin/words?status=&lang=&q=&page=&size=` | editor | Ro‘yxat |
| POST | `/admin/words` | editor | `{language_code, lemma, entry_type?}` qo‘lda yaratish (draft) |
| POST | `/admin/words/generate` | editor | `{term, lang?}` → job |
| GET | `/admin/words/{id}` | editor | `WordEntry` (har qanday status) + `versions[]` |
| PUT | `/admin/words/{id}` | editor | `{entry: WordEntryIn, reason}` — to‘liq almashtirish, versiya +1 |
| POST | `/admin/words/{id}/publish` | editor | → `published` |
| POST | `/admin/words/{id}/reject` | editor | → `rejected` |
| POST | `/admin/words/{id}/regenerate` | editor | AI qayta yaratadi (versiya saqlanadi) |
| DELETE | `/admin/words/{id}` | admin | |
| GET | `/admin/words/{id}/versions/{version}` | editor | Snapshot |
| GET | `/admin/moderation?page=` | editor | `draft` + `ai_generated`, talab (qidiruvlar) va confidence bo‘yicha saralangan |
| GET | `/admin/reports?status=open` | editor | |
| PATCH | `/admin/reports/{id}` | editor | `{status}` |
| GET | `/admin/missing-words?days=30&lang=` | editor | `[{normalized, query, language_code, count, last_searched_at}]` |
| GET | `/admin/users?q=&page=` | admin | |
| PATCH | `/admin/users/{id}` | admin | `{role?, plan?, is_active?}` |
| GET/POST | `/admin/languages` | admin | |
| PATCH | `/admin/languages/{code}` | admin | `{is_active?, sort_order?, tts_supported?, …}` |
| GET | `/admin/ai-usage?days=30` | editor | `{totals, by_agent[], by_day[]}` |

`WordEntryIn` — `WordEntry` bilan bir xil tuzilma (id’larsiz): `lemma, entry_type, cefr_level, tags, etymology, pronunciations[], forms[], senses[] {pos, domain, register, cefr_level, definitions{}, translations{lang: [{text, is_primary, note}]}, examples[], synonyms[], antonyms[]}, relations{}`.

## Xizmat
`GET /healthz` → `{"status": "ok"}` · `GET /readyz` → DB + Redis tekshiruvi.

## Kvota va rate limit
- Qidiruv: IP bo‘yicha 60 so‘rov/daqiqa → `429 rate_limited`.
- AI izoh, AI generatsiya, tarjima belgilari, TTS: kunlik kvota (01-PRD.md §7) → `429 quota_exceeded`.
- Javob sarlavhalari: `X-Quota-Remaining` (AI endpointlarda).

## Developer API (Scale fazasi)
`X-API-Key` sarlavhasi, `api_keys` jadvali, tarif bo‘yicha limit. Endpointlar o‘sha `/api/v1`:
`GET /api/v1/words/hello`, `POST /api/v1/translate`, `GET /api/v1/languages`, `GET /api/v1/trending`.
