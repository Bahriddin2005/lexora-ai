# 00 — Lexora AI: umumiy ko‘rinish

> **Lexora AI = Dictionary + Translator + AI + Learning + Live Language Database**
>
> Oddiy tarjimon emas — AI asosidagi global, tirik lug‘at ekotizimi. Til o‘zgargani sari lug‘at ham yangilanib boradi.

## Vizyon
Foydalanuvchi istalgan so‘zni kiritadi (`run`) va tizim faqat "yugurmoq" demaydi. U quyidagilarni beradi:
ma’nolar (sense), talaffuz (IPA + audio), so‘z turkumi, CEFR darajasi, chastota, sinonim/antonimlar,
kontekstga qarab tarjimalar, misollar, slang va zamonaviy ma’nolar, iboralar, etimologiya va AI izoh.

## 7 ta asosiy modul
| # | Modul | Vazifasi | MVP’da |
|---|---|---|---|
| 1 | 🌍 Global Dictionary | Qo‘llab-quvvatlanadigan tillardagi so‘zlar bazasi | ✅ (uz, en, ru, tr) |
| 2 | 🤖 AI Dictionary | So‘z ma’nosini kontekst asosida tushuntirish, yangi so‘zni AI bilan yaratish | ✅ |
| 3 | ⚡ Live Words | Yangi termin, slang va iboralarni aniqlash | ⏳ Faza 4 (11–14 hafta) |
| 4 | 🔄 Translator | So‘z, gap va matn tarjimasi | ✅ |
| 5 | 🎙️ Voice | Ovozli qidiruv (STT) va talaffuz (TTS) | ✅ qisman (brauzer STT + Gemini TTS) |
| 6 | 📚 Learning | Flashcard, test, spaced repetition | ⏳ Faza 5 (15–18 hafta), MVP’da ❤️ saqlash |
| 7 | 🔌 API | Boshqa sayt, bot va agentlarga ulash | ✅ REST `/api/v1` (API kalitlar — Scale fazasi) |

## MVP chegarasi (3–6 hafta)
Kiradi: login/ro‘yxatdan o‘tish, tillar, lug‘at qidiruvi (typo correction, tabiiy til so‘rovlari),
so‘z sahifasi, tarjima, talaffuz, misollar, AI izoh ("AI bilan tushunish"), AI orqali yangi so‘z yaratish
(verification + moderatsiya bilan), favorites (❤️), xato haqida xabar (🚩), trending, admin panel.

Kirmaydi (keyingi fazalar): Live Words collector, learning (SRS), to‘lov tizimi, API kalitlar, mobil ilova,
Telegram bot, browser extension, OpenSearch, Kafka.

## Asosiy tamoyillar
1. **Tarjima so‘zga emas, ma’noga (sense) bog‘lanadi.** `run` → "yugurmoq" (harakat), "boshqarmoq" (biznes), "ishga tushirmoq" (dastur).
2. **AI topgan narsa avtomatik "to‘g‘ri" emas.** Har yozuvda `source` + `confidence` + `status` bor; moderatsiya oqimi majburiy.
3. **Sodda boshlash.** Monolit FastAPI + Celery worker. Kafka/mikroservis — faqat kerak bo‘lganda.
4. **Tillar konfiguratsiya orqali qo‘shiladi.** Yangi til = `languages` jadvaliga yozuv + normalizatsiya qoidasi.
5. **Provayderga bog‘lanmaslik.** AI `LLMProvider` interfeysi orqali; default — Google Gemini.

## Kengayish yo‘li
`4 til → 20 til → 100+ til → Live Global Dictionary`

## Glossariy
| Atama | Ma’nosi |
|---|---|
| **Word / Entry** | Lug‘atdagi bosh so‘z (lemma) — bitta til + normalizatsiyalangan shakl |
| **Lemma** | So‘zning lug‘at shakli (`ran` → `run`) |
| **Sense** | So‘zning bitta ma’nosi; o‘z POS, domen, tarjimalari va misollariga ega |
| **POS** | Part of speech — so‘z turkumi (noun, verb, adj…) |
| **CEFR** | A1–C2 til darajasi |
| **Zipf** | So‘z chastotasi shkalasi (1–7), `wordfreq` kutubxonasidan |
| **Normalized key** | Qidiruv uchun kanonik shakl (kichik harf, apostroflar birxillashtirilgan, transliteratsiya) |
| **Confidence** | AI yoki manba ishonchliligi 0–1 |
| **Status** | `draft` / `ai_generated` / `published` / `rejected` |
| **Agent** | Bitta vazifaga ixtisoslashgan AI komponent (Meaning, Translation, Verification…) |

## Hujjatlar xaritasi
- [01-PRD.md](01-PRD.md) — mahsulot talablari
- [02-architecture.md](02-architecture.md) — arxitektura
- [03-database-schema.md](03-database-schema.md) — ma’lumotlar bazasi
- [04-api-spec.md](04-api-spec.md) — API
- [05-ai-agents.md](05-ai-agents.md) — AI agentlar
- [06-search.md](06-search.md) — qidiruv
- [07-pages-and-ux.md](07-pages-and-ux.md) — sahifalar va UX
- [08-admin-panel.md](08-admin-panel.md) — admin panel
- [09-ui-design-system.md](09-ui-design-system.md) — dizayn tizimi
- [10-learning-srs.md](10-learning-srs.md) — learning moduli
- [11-live-words.md](11-live-words.md) — Live Words pipeline
- [12-roadmap.md](12-roadmap.md) — yo‘l xaritasi
- [13-agent-tasks.md](13-agent-tasks.md) — AI coding agent uchun tasklar
