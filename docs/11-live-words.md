# 11 — Live Words: "tirik" lug‘at (Faza 4: 11–14 hafta)

"Har soniyada yangilanadi" — server har soniyada butun internetni tekshiradi degani **emas**.
Bu **event-driven pipeline**: yangi ma’lumot kelishi bilan qayta ishlanadi.

## Pipeline
```
Internet / APIs / Open datasets
              ↓
      Live Word Collector  (rejali + stream manbalar)
              ↓
      Nomzodlarni ajratish (n-gram, noma’lum token, chastota tezligi)
              ↓
      Yangi termin topildimi?  ── yo‘q ──▶ mention_count++
              ↓ ha
          AI Agent (Language → Meaning → Translation → Example)
              ↓
      Duplicate check (normalized, forms, sinonimlar)
              ↓
      Ishonchlilik tekshiruvi (Verification + manbalar soni + tezlik)
              ↓
      Moderation / validation (editor navbati; yuqori skor → avto ai_generated)
              ↓
          Database → Search indeks → Foydalanuvchi (⚡ Live sahifa, trending)
```

## Manbalar (bosqichma-bosqich)
| Manba | Usul | Tillar |
|---|---|---|
| Foydalanuvchi qidiruvlari (`search_logs.found=false`) | Ichki, real-time | barcha — **eng qimmatli signal** |
| Wikipedia / Wiktionary yangi sahifalari | RecentChanges stream (EventStreams) | en, ru, tr, uz |
| Texnologiya yangiliklari (RSS), arXiv | Rejali (har 15 daqiqa) | en |
| Hacker News, Reddit API | Rejali | en |
| O‘zbek yangiliklar saytlari (RSS) | Rejali | uz, ru |
| Google Trends | Rejali | barcha |
| Gemini + Google Search grounding | Nomzodni tekshirish (izohlash va manba URL’lari) | barcha |

## Nomzod skori
```
score = w1·log(mention_count) + w2·velocity(24h/7d) + w3·source_diversity + w4·search_demand − w5·spam_signals
```
`score ≥ T_auto` va Verification `accept` → `ai_generated` (tag `new`); aks holda moderatsiya navbati.

## Ma’lumotlar
`live_candidates (term, language_code, normalized, first_seen_at, mention_count, velocity, sources jsonb, score, status)`,
`live_mentions (candidate_id, source_url, snippet, seen_at)`.

## Texnologiya
- Boshlanishida: Celery beat + workerlar (`collector.*` navbatlari), Redis streams.
- Hajm oshganda: Kafka/Redpanda topiclar `raw_mentions → candidates → enriched → verified`, collector’lar alohida servis.

## Himoyalar
- Spam/reklama nomlari filtri, haqoratli so‘zlar ro‘yxati.
- Brend nomlari — `proper_noun` sifatida, alohida belgilanadi.
- Har termin uchun kamida 2 mustaqil manba (yoki yuqori qidiruv talabi) talab qilinadi.
- Hech narsa manba + confidence’siz nashr qilinmaydi.

## UI
`/live` — ⚡ oqim: "Bugun paydo bo‘lgan 12 ta yangi termin", har termin: qachon birinchi ko‘rilgan, manbalar, grafik (mention’lar).
