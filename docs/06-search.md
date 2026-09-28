# 06 — Qidiruv

Qidiruv — mahsulotning eng kuchli funksiyasi. MVP’da PostgreSQL (`pg_trgm`) ustida; 1M+ so‘zda OpenSearch’ga ko‘chiriladi
(interfeys `services/search.py` o‘zgarmaydi).

## 1. Normalizatsiya (`services/normalization.py`)
`normalize(text, lang) -> str` — DB’dagi `normalized` ustuni va qidiruv kaliti uchun **bir xil** funksiya.

| Qadam | Barcha tillar | uz | ru | tr | en |
|---|---|---|---|---|---|
| Unicode | NFKC, bo‘shliqlarni siqish, trim | | | | |
| Apostroflar | `ʻ ʼ ’ ‘ \` ´ ′` → `'` | ✅ | | | ✅ |
| Kirill → lotin | | `ўғил` → `o'g'il` | | | |
| Kichik harf | `casefold` | ✅ | ✅ | `İ→i`, `I→ı` keyin `ı→i` | ✅ |
| Maxsus | | | `ё→е` | | diakritika olib tashlanadi (`café→cafe`) |

Misollar: `oʻgʻil`, `o‘g‘il`, `o'g'il`, `ўғил` → `o'g'il`; `İstanbul` → `istanbul`; `Ёлка` → `елка`.

Yozuv (script) aniqlash: `detect_script(text)` → `Latn` / `Cyrl` / `Arab`; kirillda `ў ғ қ ҳ` bo‘lsa → `uz`, aks holda `ru` ehtimoli yuqori.

## 2. Tabiiy til so‘rovlari (intent parser)
`services/intent.py` — avval regex shablonlar (tez, bepul), keyin kerak bo‘lsa LLM.

| So‘rov | Intent |
|---|---|
| `book` | `lookup {term: book}` |
| `book so‘zining o‘zbekcha ma'nosi` | `lookup {term: book, target_lang: uz}` |
| `rus tilida "maktab" nima?` | `translate {term: maktab, target_lang: ru}` |
| `python so‘zi dasturlashda nimani anglatadi?` | `lookup {term: python, domain: computing, target_lang: uz}` |
| `cringe nima degani?` | `lookup {term: cringe, target_lang: uz}` |
| `2026-yilda AI sohasida chiqqan yangi terminlarni ko‘rsat` | `list_new_terms {domain: ai, year: 2026}` |
| `what does serendipity mean` | `lookup {term: serendipity, target_lang: en}` |
| `что значит кринж` | `lookup {term: кринж, target_lang: ru}` |
| `школа по-английски` | `translate {term: школа, target_lang: en}` |

Til nomlari lug‘ati: `o‘zbekcha/o‘zbek tilida/uzbek/по-узбекски → uz`, `inglizcha/ingliz tilida/english/по-английски → en`,
`ruscha/rus tilida/russian/по-русски → ru`, `turkcha/turk tilida/turkish/по-турецки → tr`.
Domen lug‘ati: `dasturlashda/programming/в программировании → computing`, `AI sohasida/sun’iy intellekt/ai → ai`,
`tibbiyotda/medicine → medicine`, `iqtisodda/economics → economics`, `sportda/sports → sports`, `huquqda/law → law`.

Regex mos kelmasa va so‘rov ≥ 3 so‘zdan iborat bo‘lsa → `IntentAgent` (LLM, JSON, `ai_generations` keshi). LLM yo‘q bo‘lsa → butun so‘rov `lookup`.

## 3. Qidiruv tartibi (`services/search.py`)
Nomzod tillar: `from` berilgan bo‘lsa — faqat u; aks holda barcha faol tillar (script bo‘yicha filtrlangan).
Har til uchun `key = normalize(term, lang)`.

| # | Bosqich | SQL g‘oyasi | `match` |
|---|---|---|---|
| 1 | Exact | `words.normalized = key AND language_code = lang` | `exact` |
| 2 | Shakllar | `word_forms.normalized = key` → `words` | `form` |
| 3 | Reverse | `translations.normalized = key AND target_language = lang` → sense → word | `reverse` |
| 4 | Prefix (natija < 5 bo‘lsa) | `normalized LIKE key || '%'` (`varchar_pattern_ops`), chastota bo‘yicha | `prefix` |
| 5 | Did you mean (natija 0 bo‘lsa) | `similarity(normalized, key) > 0.3 ORDER BY similarity DESC, frequency DESC LIMIT 5` | — |
| 6 | AI | Natija yo‘q, did-you-mean < 0.5, validity gate o‘tdi → job | — |

Saralash: `exact > form > reverse > prefix`, keyin `frequency_zipf DESC`, keyin `from/to` juftligidagi til.
Faqat `published` + `ai_generated`.

`beutiful` → trigram o‘xshashligi `beautiful` bilan ≈ 0.58 → "**beautiful** nazarda tutdingizmi?"

## 4. Autocomplete (`/search/suggest`)
Prefix (1-bosqich kalit bilan) + chastota; 2+ belgidan boshlab; Redis kesh 1 soat (`sug:{lang}:{key}`); frontendda 150 ms debounce.

## 5. Loglar va trending
- Har qidiruv → `search_logs` (topildimi, natija so‘zi, intent).
- Topilgan exact/form natija → Redis `ZINCRBY trend:{lang}:{YYYYMMDDHH} 1 {word_id}` (TTL 48 soat).
- `/trending` = so‘nggi 24 soatlik bucket’lar yig‘indisi (`ZUNIONSTORE`, 60 s kesh) — real vaqtda yangilanadi.
- `found=false` loglar → admin "Topilmagan so‘zlar" ro‘yxati (talab bo‘yicha saralangan).

## 6. `list_new_terms` intent
`words WHERE (tags @> {domain} OR sense.domain = domain) AND extract(year from first_seen_at) = year ORDER BY first_seen_at DESC`.
MVP’da mavjud ma’lumot bo‘yicha ishlaydi; Faza 4’da Live Words to‘ldiradi.

## 7. OpenSearch’ga ko‘chish (Scale)
- Indeks: `words_{lang}` — til analyzer’lari (uz uchun custom: apostrof normalizatsiya + transliteratsiya char_filter).
- Maydonlar: lemma, forms, translations.*, definitions.*, tags, frequency (function_score).
- Fuzzy (`fuzziness: AUTO`), `search_as_you_type` autocomplete, sinonimlar.
- DB → indeks: transactional outbox + worker.
