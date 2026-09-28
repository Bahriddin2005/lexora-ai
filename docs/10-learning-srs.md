# 10 — Learning moduli (Faza 5: 15–18 hafta)

Maqsad: lug‘atni **til o‘rganish servisiga** aylantirish. Foydalanuvchi ❤️ bosib saqlagan so‘zlar — o‘quv materiali.

## Zanjir
```
❤️ saqlash → Flashcard → Test (ko‘p tanlov) → Gap tuzish → Listening → Speaking → Takrorlash (SRS)
```
| Mashq | Tavsif | Manba |
|---|---|---|
| Flashcard | Old: so‘z + IPA + 🔊; orqa: tarjima + misol. Baholash: Again / Hard / Good / Easy | `word_senses`, `examples` |
| Test | 4 variantli: so‘z → tarjima, tarjima → so‘z; chalg‘ituvchilar — o‘sha POS/CEFR’dagi so‘zlar | DB |
| Gap tuzish | Misoldagi so‘z yashiriladi (cloze); yoki berilgan so‘z bilan gap tuzish → AI baholaydi | `examples`, ExplainAgent |
| Listening | TTS audio → yozib olish (dictation) | TTS |
| Speaking | Foydalanuvchi talaffuz qiladi → STT → solishtirish, ball | Whisper/Gemini audio |

## Spaced repetition: FSRS
- Algoritm: **FSRS** (Free Spaced Repetition Scheduler; `py-fsrs` kutubxonasi) — SM-2 dan aniqroq.
- `learning_items`: `state, due, stability, difficulty, reps, lapses, last_review`.
- `review_logs`: har javob (rating 1–4, mashq turi, vaqt) — FSRS parametrlarini shaxsiylashtirish uchun.
- Kunlik navbat: `due <= now()` bo‘lganlar + yangi so‘zlar limiti (default 10/kun).

## AI yordamchi
- Foydalanuvchi darajasi (CEFR) bo‘yicha misollar generatsiyasi.
- Xatolar tahlili: "siz *affect* va *effect* ni ko‘p adashtirasiz" + mini-dars.
- Shaxsiy lug‘atdan kunlik "5 daqiqalik dars".

## API (reja)
| Metod | Yo‘l |
|---|---|
| GET | `/learn/queue?limit=20` |
| POST | `/learn/review` `{item_id, rating, review_type, duration_ms}` |
| GET | `/learn/stats` (streak, o‘rganilgan so‘zlar, aniqlik) |
| POST | `/learn/quiz` → savollar to‘plami |

## Gamifikatsiya
Streak 🔥, kunlik maqsad, darajalar, haftalik reyting (ixtiyoriy).

## Tarif
Free: kuniga 20 ta takrorlash, flashcard + test. Pro: cheksiz, listening/speaking, AI baholash.
