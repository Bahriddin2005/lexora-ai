# 05 — AI agentlar arxitekturasi

Bitta ulkan AI o‘rniga **bir nechta ixtisoslashgan agent**. Har agent: aniq kirish/chiqish (Pydantic schema),
versiyalangan prompt, log (`ai_generations`), kesh.

## 1. Provayder qatlami
```python
class LLMProvider(Protocol):
    name: str
    async def generate_json(self, *, prompt: str, schema: type[BaseModel], model: ModelTier,
                            system: str | None = None, temperature: float = 0.2) -> LLMResult[BaseModel]: ...
    def stream_text(self, *, prompt: str, model: ModelTier, system: str | None = None) -> AsyncIterator[str]: ...
    async def tts(self, *, text: str, lang: str, voice: str | None = None) -> bytes: ...  # WAV
```
- `GeminiProvider` — `google-genai` SDK: `client.aio.models.generate_content(..., config=GenerateContentConfig(response_mime_type="application/json", response_schema=Schema))`, stream uchun `generate_content_stream`, TTS uchun `response_modalities=["AUDIO"]` (PCM 24 kHz → WAV).
- `FakeProvider` — testlar va API kalitsiz dev uchun deterministik javoblar.
- Model darajalari (`ModelTier`): `smart` (EntryAgent), `fast` (Verification, Intent, Translate, Explain), `tts`.
  Env: `GEMINI_MODEL_SMART`, `GEMINI_MODEL_FAST`, `GEMINI_MODEL_TTS`.
- Keyin: `OpenAIProvider`, `LocalProvider` (Ollama), provayderlar orasida fallback.

## 2. To‘liq agentlar zanjiri (maqsad arxitektura)
```
Internet / APIs / Open datasets
              ↓
      Collector Agent ──────────── yangi termin/ibora nomzodlari (Faza 4)
              ↓
      Language Agent ───────────── qaysi til? (script + model)
              ↓
      Meaning Agent ────────────── ma’nolar, POS, domen, register, CEFR
              ↓
      Translation Agent ────────── har sense uchun uz/ru/tr/en ekvivalentlar
              ↓
      Example Agent ────────────── tabiiy misollar + tarjimalari
              ↓
      Verification Agent ───────── mustaqil tekshiruv, confidence, muammolar
              ↓
      Publishing Agent ─────────── duplicate check, status qoidasi, DB, indeks, versiya
```

## 3. MVP’dagi amalga oshirish
Kechikish va narxni kamaytirish uchun Meaning + Translation + Example + Language **bitta strukturali chaqiruvda** (`EntryAgent`) birlashtiriladi.
Verification alohida (mustaqil nazorat bo‘lishi uchun). Publishing — deterministik kod (LLM emas).

```
search miss ─▶ validity gate ─▶ lock ─▶ EntryAgent (smart) ─▶ VerificationAgent (fast) ─▶ Publisher (kod)
```

### 3.1 Validity gate (kod)
- 1–4 token, 2–60 belgi, harf/apostrof/defis/probel; raqam yoki URL emas.
- Trigram "did you mean" o‘xshashligi ≥ 0.5 bo‘lsa — avtomatik generatsiya qilinmaydi (typo), `force_ai=true` kerak.
- Kvota: `ai_generate`.

### 3.2 EntryAgent — `entry@1`
Kirish: `term`, `lang_hint`, `target_langs=[uz, en, ru, tr]`, `domain_hint`.
Chiqish (`GeneratedEntry`):
```json
{
  "is_valid_word": true,
  "language": "en",
  "lemma": "vibe coding",
  "entry_type": "phrase",
  "ipa": "/vaɪb ˈkoʊdɪŋ/",
  "cefr_level": null,
  "tags": ["ai", "new", "slang"],
  "forms": [],
  "etymology_en": "Coined in 2025…",
  "etymology_uz": "2025-yilda paydo bo‘lgan…",
  "senses": [{
    "pos": "noun", "domain": "ai", "register": "informal", "cefr_level": null,
    "definitions": [{"lang": "en", "text": "…"}, {"lang": "uz", "text": "…"}],
    "translations": [{"lang": "uz", "text": "…", "is_primary": true, "note": null}, {"lang": "ru", "text": "…"}],
    "examples": [{"text": "…", "translations": [{"lang": "uz", "text": "…"}]}],
    "synonyms": [], "antonyms": []
  }],
  "phrases": [],
  "suggestions": []
}
```
Prompt qoidalari: faqat ishonchli ma’lumot; noma’lum bo‘lsa maydonni bo‘sh qoldirish; `is_valid_word=false` bo‘lsa `suggestions` berish;
o‘zbek tili — lotin yozuvi, `oʻ gʻ` uchun `ʻ` (U+02BB); har sense uchun kamida 1 ta misol; 1–6 sense.

### 3.3 VerificationAgent — `verify@1`
Kirish: `GeneratedEntry` JSON. Vazifa: "Siz tajribali leksikograf-muharrirsiz. Faktik xatolarni, noto‘g‘ri tarjimalarni, uydirma ma’nolarni toping."
Chiqish:
```json
{"verdict": "accept" | "review" | "reject", "confidence": 0.0-1.0, "issues": ["…"], "corrected_primary_uz": null}
```

### 3.4 Publisher (kod)
| Shart | Natija |
|---|---|
| `is_valid_word = false` | DB’ga yozilmaydi, job `not_a_word` + `suggestions` |
| `verdict = reject` yoki `confidence < 0.3` | `rejected` (admin ko‘radi) |
| `confidence < AI_PUBLISH_THRESHOLD` (default 0.6) yoki `verdict = review` | `draft` → moderatsiya navbati |
| aks holda | `ai_generated` → foydalanuvchiga "AI" belgisi bilan ko‘rinadi |
Duplicate check: `UNIQUE(language_code, normalized)` + `word_forms` bo‘yicha tekshiruv; mavjud bo‘lsa yangilanmaydi (regenerate’dan tashqari).
Manba: `sources.code = gemini`; `word_versions` ga v1 snapshot.

### 3.5 Boshqa agentlar
| Agent | Prompt | Model | Chiqish | Kesh |
|---|---|---|---|---|
| IntentAgent | `intent@1` | fast | `{type, term, source_lang, target_lang, domain, year}` | `ai_generations` (input_hash) |
| TranslateAgent | `translate@1` | fast | `{translation, detected_source, alternatives[], notes}` | `ai_generations` (input_hash) |
| ExplainAgent | `explain@1` | fast (stream) | Markdown matn | `ai_generations` (input_hash) |
| TTS | — | tts | WAV | Storage |

## 4. Ishonchlilik (trust) modeli
- Har yozuv: `source_id` + `confidence` + `status`.
- Manba ishonchliligi (`sources.reliability`): Wiktionary 0.9, editor 1.0, Gemini 0.6, user 0.3.
- UI: `ai_generated` → "🤖 AI tomonidan yaratilgan · ishonch 78%" + "xato haqida xabar" tugmasi.
- Foydalanuvchi reportlari moderatsiya navbatida yozuvni yuqoriga ko‘taradi.

## 5. Xarajat nazorati
- Kesh: bir xil kirish → bir xil javob (sha256 `input_hash`).
- Kvotalar (01-PRD.md §7), Redis lock bilan dublikat generatsiyaning oldini olish.
- Arzon vazifalar `fast` modelda; faqat EntryAgent `smart` modelda.
- Har chaqiruv `ai_generations` ga: tokenlar, `cost_usd` (narxlar config’da), latency.
- Admin "AI usage" sahifasi: kun/agent bo‘yicha xarajat.

## 6. Promptlar
`backend/app/ai/prompts/*.py` — har prompt `NAME@VERSION`. Prompt o‘zgarsa versiya oshiriladi → kesh avtomatik yangilanadi
(input_hash’ga prompt versiyasi kiradi).

## 7. Xatolar
- Provayder xatosi/timeout (30 s) → 1 marta retry (exponential backoff) → job `failed`, `ai_generations.ok=false`.
- Schema’ga mos kelmagan JSON → Pydantic validatsiya xatosi → retry → `failed`.
- `AI_PROVIDER` sozlanmagan yoki kalit yo‘q → `ai_available=false`, AI endpointlar 503.

## 8. Faza 4: Live Words agentlari
[11-live-words.md](11-live-words.md) ga qarang: Collector (RSS, Reddit/HN API, Wikipedia yangi sahifalari, Google Trends,
Gemini Google Search grounding), nomzodlarni skorlash, keyin yuqoridagi pipeline.
