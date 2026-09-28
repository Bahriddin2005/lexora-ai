# 03 — Ma’lumotlar bazasi (PostgreSQL 16)

Asosiy g‘oya: **bitta so‘z = bitta tarjima** modeli global lug‘at uchun yetarli emas.
Tarjimalar, izohlar va misollar **ma’noga (`word_senses`)** bog‘lanadi.

```
languages ─┐
           ├──< words ──< word_senses ──< sense_definitions (izoh, har tilda)
sources ───┘     │  │            ├──< translations ──> words (target_word_id, ixtiyoriy)
                 │  │            ├──< examples (translations JSONB)
                 │  │            └──< word_relations (sense darajasida)
                 │  ├──< word_forms (ran → run)
                 │  ├──< pronunciations (IPA, audio)
                 │  ├──< word_relations (synonym/antonym/related/derived/phrase)
                 │  ├──< word_sources ──> sources
                 │  └──< word_versions (snapshot JSONB)
users ──< user_favorites >── words
users ──< reports >── words
users ──< refresh_tokens
search_logs, ai_generations (log/kesh)
```

## Foydalanuvchi ro‘yxatidagi jadvallar → bizning sxema
| G‘oyadagi jadval | Sxemada |
|---|---|
| users, languages, words, word_senses, translations, examples, pronunciations, sources, word_sources, word_versions, reports | Xuddi shu nom bilan |
| synonyms, antonyms | `word_relations.relation_type = synonym/antonym` |
| phrases | `words.entry_type = phrase/idiom/phrasal_verb` + `word_relations.relation_type = phrase` |
| slang | `word_senses.register = slang` + `words.tags` |
| etymologies | `words.etymology` (JSONB, tillar bo‘yicha) |
| ai_analysis | `ai_generations` |
| user_dictionary | `user_favorites` |
| learning_progress | `learning_items` + `review_logs` (Faza 5) |

## Enumlar
| Enum | Qiymatlar |
|---|---|
| `user_role` | `user`, `editor`, `admin` |
| `user_plan` | `free`, `pro` |
| `content_status` | `draft`, `ai_generated`, `published`, `rejected` |
| `entry_type` | `word`, `phrase`, `idiom`, `phrasal_verb`, `abbreviation`, `proper_noun` |
| `register` | `neutral`, `formal`, `informal`, `slang`, `vulgar`, `archaic` |
| `relation_type` | `synonym`, `antonym`, `related`, `derived`, `phrase` |
| `source_type` | `dataset`, `ai`, `editor`, `user`, `web` |
| `report_reason` | `wrong_translation`, `wrong_definition`, `wrong_pronunciation`, `offensive`, `duplicate`, `other` |
| `report_status` | `open`, `resolved`, `rejected` |

## MVP jadvallari

### `languages`
| Ustun | Tur | Izoh |
|---|---|---|
| code | varchar(8) PK | ISO 639-1: `uz`, `en`, `ru`, `tr` |
| name | varchar(64) | "Uzbek" |
| native_name | varchar(64) | "O‘zbekcha" |
| script | varchar(8) | `Latn`, `Cyrl`, `Arab` |
| direction | varchar(3) | `ltr` / `rtl` |
| flag | varchar(8) | 🇺🇿 |
| is_active | bool | Qidiruvda ishtirok etadimi |
| tts_supported | bool | |
| sort_order | int | |

### `users`
| Ustun | Tur | Izoh |
|---|---|---|
| id | uuid PK | |
| email | varchar(255) UNIQUE | kichik harfda saqlanadi |
| password_hash | varchar(255) | argon2 |
| display_name | varchar(80) | |
| role | user_role | default `user` |
| plan | user_plan | default `free` |
| ui_language | varchar(8) | default `uz` |
| is_active | bool | |
| created_at, updated_at, last_login_at | timestamptz | |

### `refresh_tokens`
`id uuid PK, user_id → users (cascade), token_hash varchar(64) UNIQUE, expires_at, revoked_at, user_agent, created_at`

### `sources`
`id serial PK, code varchar(48) UNIQUE (wiktionary, gemini, editor, demo-seed, user), name, type source_type, url, license, reliability float (0–1)`

### `words`
| Ustun | Tur | Izoh |
|---|---|---|
| id | bigserial PK | |
| language_code | → languages | |
| lemma | varchar(200) | Ko‘rsatiladigan shakl (`Apple`, `o‘g‘il`) |
| normalized | varchar(200) | Qidiruv kaliti (06-search.md) |
| entry_type | entry_type | |
| frequency_zipf | float null | 1–7 |
| cefr_level | varchar(2) null | A1…C2 |
| etymology | jsonb null | `{"en": "...", "uz": "..."}` |
| tags | varchar[] | `ai`, `slang`, `new`, `tech`… (GIN indeks) |
| status | content_status | |
| confidence | float null | 0–1 |
| source_id | → sources | Asosiy manba |
| version | int | Har tahrirda +1 |
| first_seen_at | timestamptz | Live Words uchun |
| created_at, updated_at | timestamptz | |

Cheklov/indekslar: `UNIQUE(language_code, normalized)`; `GIN (normalized gin_trgm_ops)`; `btree (normalized varchar_pattern_ops)` — prefix; `(status, created_at)`; `GIN(tags)`.

### `word_forms`
`id, word_id → words (cascade), form varchar(200), normalized varchar(200), tags varchar[]` — indeks `normalized`. Misol: `ran`, `running`, `runs` → `run`.

### `pronunciations`
`id, word_id → words (cascade), ipa varchar(200), accent varchar(16) (US/UK/general), audio_key varchar(300) null, audio_source varchar(16) (tts/human)`

### `word_senses`
| Ustun | Tur | Izoh |
|---|---|---|
| id | bigserial PK | |
| word_id | → words (cascade) | |
| sense_order | int | Tartib |
| pos | varchar(24) | noun, verb, adj, adv, pron, prep, conj, interj, num, phrase, proper_noun |
| domain | varchar(48) null | computing, ai, medicine, sports, business, law… |
| register | register | |
| cefr_level | varchar(2) null | |
| status | content_status | |
| confidence | float null | |
| source_id | → sources null | |

### `sense_definitions`
`id, sense_id → word_senses (cascade), language_code → languages, text text, source_id null` — `UNIQUE(sense_id, language_code)`.
Misol: `run` (verb, 1-ma’no) → `en`: "to move swiftly on foot", `uz`: "oyoqda tez harakatlanmoq".

### `translations`
| Ustun | Tur | Izoh |
|---|---|---|
| id | bigserial PK | |
| sense_id | → word_senses (cascade) | |
| target_language | → languages | |
| text | varchar(300) | "yugurmoq" |
| normalized | varchar(300) | Reverse lookup uchun (indeks `(target_language, normalized)`) |
| target_word_id | → words null | Maqsad tildagi yozuvga havola |
| is_primary | bool | Asosiy tarjima |
| note | varchar(300) null | "sport kontekstida" |
| confidence | float null | |
| source_id | → sources null | |

### `examples`
`id, sense_id → word_senses (cascade), text text (so‘z tilida), translations jsonb ({"uz": "...", "ru": "..."}), source varchar(16) (dataset/ai/editor)`

### `word_relations`
`id, word_id → words (cascade), sense_id → word_senses null (cascade), relation_type relation_type, target_text varchar(200), target_word_id → words null`

### `word_sources`
`id, word_id → words (cascade), source_id → sources, external_ref varchar(500) (URL/ID), retrieved_at timestamptz`

### `word_versions`
`id, word_id → words (cascade), version int, snapshot jsonb (to‘liq yozuv), changed_by → users null, reason varchar(200), created_at` — `UNIQUE(word_id, version)`.

### `ai_generations`
| Ustun | Tur | Izoh |
|---|---|---|
| id | bigserial PK | |
| agent | varchar(32) | entry, verify, explain, translate, intent, tts |
| model | varchar(64) | |
| prompt_version | varchar(16) | `entry@1` |
| input_hash | varchar(64) | sha256 — kesh kaliti (indeks) |
| output | jsonb null | Strukturali natija |
| output_text | text null | Matnli natija (explain) |
| tokens_in, tokens_out, latency_ms | int | |
| cost_usd | numeric(10,6) | Taxminiy |
| word_id | → words null | |
| user_id | → users null | |
| ok | bool | |
| error | text null | |
| created_at | timestamptz | |

### `user_favorites`
`user_id → users (cascade), word_id → words (cascade), note varchar(300) null, created_at` — PK `(user_id, word_id)`.

### `reports`
`id, user_id → users null, word_id → words (cascade), sense_id null, reason report_reason, comment text, status report_status, resolved_by → users null, resolved_at, created_at`

### `search_logs`
`id bigserial, user_id null, query varchar(300), normalized varchar(300), language_code varchar(8) null, target_language varchar(8) null, intent varchar(24), found bool, result_word_id → words null, created_at` — indekslar `(found, created_at)`, `(normalized)`.

## Kontent status lifecycle
```
            import (dataset)                     editor tasdiqlaydi
  ┌──────────────────────────────▶ published ◀──────────────────────┐
  │                                                                 │
AI EntryAgent ─▶ VerificationAgent ─┬─ confidence ≥ threshold ─▶ ai_generated
                                    ├─ threshold > c ≥ 0.3     ─▶ draft (faqat admin ko‘radi)
                                    └─ verdict=reject / c < 0.3 ─▶ rejected
editor rad etadi ─▶ rejected
```
Ommaviy API faqat `published` va `ai_generated` ni ko‘rsatadi (`ai_generated` "AI" belgisi bilan).

## Versiyalash
Admin har `PUT /admin/words/{id}` da: joriy yozuvning to‘liq snapshot’i `word_versions` ga yoziladi → `words.version += 1`.
AI regeneratsiya ham shunday. Bu audit va "orqaga qaytarish" imkonini beradi.

## Keyingi fazalar jadvallari (hozircha yaratilmaydi)
| Jadval | Ustunlar | Faza |
|---|---|---|
| `learning_items` | user_id, word_id, sense_id, state (new/learning/review/relearning), due, stability, difficulty, reps, lapses, last_review | 5 |
| `review_logs` | item_id, rating (1–4), review_type (flashcard/quiz/gap/listening/speaking), reviewed_at, elapsed_days | 5 |
| `word_lists` | user_id, name, is_public | 5 |
| `live_candidates` | term, language_code, normalized, first_seen_at, mention_count, velocity, sources jsonb, score, status | 4 |
| `live_mentions` | candidate_id, source_url, snippet, seen_at | 4 |
| `api_keys` | user_id, name, prefix, key_hash, scopes, rate_limit, created_at, revoked_at | Scale |
| `api_usage` | api_key_id, day, requests | Scale |
| `subscriptions`, `payments` | user_id, provider (payme/click/stripe), plan, status, period | Scale |

## Migratsiyalar
Alembic (`backend/alembic`). Birinchi migratsiya `pg_trgm` va `unaccent` extension’larini yoqadi.
Yangi til qo‘shish migratsiya emas — `languages` jadvaliga yozuv (admin panel yoki `scripts/seed_languages.py`).
