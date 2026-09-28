# 01 — PRD (Product Requirements Document)

## 1. Muammo
- O‘zbek tilida zamonaviy, kontekstli, ko‘p tilli lug‘at yo‘q: mavjud tarjimonlar so‘zga bitta tarjima beradi, ma’no farqlarini, misollarni, slangni ko‘rsatmaydi.
- Yangi so‘zlar (AI terminlari, slang) lug‘atlarga yillar o‘tib kiradi.
- Til o‘rganuvchi so‘zni topgach, uni yodlash uchun boshqa ilovaga o‘tishi kerak.

## 2. Maqsad
Uzbek ⇄ English ⇄ Russian ⇄ Turkish uchun eng yaxshi kontekstli lug‘at + tarjimon + AI izohni yaratish,
keyin arxitekturani o‘zgartirmasdan 100+ tilga kengaytirish.

## 3. Personalar
| Persona | Tavsif | Asosiy ehtiyoj |
|---|---|---|
| **Talaba Malika (19)** | IELTS ga tayyorlanadi | So‘z ma’nosi, misollar, CEFR, talaffuz, saqlab yodlash |
| **Dasturchi Jasur (27)** | Inglizcha texnik hujjat o‘qiydi | Kontekstli tarjima ("python dasturlashda"), yangi AI terminlari |
| **Tarjimon Dilnoza (34)** | Rus/turk/ingliz matnlar bilan ishlaydi | Aniq sinonimlar, iboralar, matn tarjimasi |
| **Maktab o‘quvchisi Bekzod (14)** | Ingliz tili darsida | Sodda o‘zbekcha izoh, ovozli qidiruv |
| **Muharrir (editor)** | Lug‘at sifatini nazorat qiladi | Moderatsiya navbati, tahrir, versiyalar |
| **Dasturchi-integrator** | Bot/sayt quradi | Barqaror REST API |

## 4. User stories (MVP)
### Qidiruv va lug‘at
- US-1: Men `run` ni kiritsam, so‘z sahifasida uning barcha ma’nolari, o‘zbekcha tarjimalari, talaffuzi va misollarini ko‘raman.
- US-2: Men `beutiful` deb xato yozsam, "**beautiful** nazarda tutdingizmi?" taklifini ko‘raman.
- US-3: Men `yugurmoq` (o‘zbekcha) yozsam, `run` (inglizcha) va boshqa tillardagi mosliklarni ko‘raman (reverse lookup).
- US-4: Men "rus tilida "maktab" nima?", "cringe nima degani?", "python so‘zi dasturlashda nimani anglatadi?" kabi tabiiy savollar bera olaman.
- US-5: Lug‘atda yo‘q so‘z bo‘lsa, AI uni tayyorlaydi; natija "AI tomonidan yaratilgan" belgisi va ishonchlilik darajasi bilan ko‘rsatiladi.
- US-6: Qidiruv maydonida yozayotganimda avtomatik takliflar chiqadi.
- US-7: Mikrofon tugmasini bosib, ovoz bilan qidira olaman (brauzer qo‘llasa).
- US-8: `ran`, `running` kabi shakllar `run` ga olib boradi.

### So‘z sahifasi
- US-9: 🔊 tugmasi orqali so‘z talaffuzini eshitaman.
- US-10: "🤖 AI bilan tushunish" tugmasi so‘zni o‘zbek tilida sodda yoki batafsil tushuntiradi (stream).
- US-11: Sinonim/antonimni bossam, o‘sha so‘z sahifasiga o‘taman.
- US-12: Xato ko‘rsam, 🚩 orqali muharrirga xabar beraman.
- US-13: ❤️ bosib so‘zni shaxsiy lug‘atimga saqlayman (login talab qilinadi).

### Tarjima
- US-14: Men matn (≤ 1000 belgi free, ≤ 5000 pro) kiritib, tilni avtomatik aniqlash bilan tarjima olaman; muqobil variantlar va izohlar ko‘rsatiladi.
- US-15: Bitta so‘z tarjima qilinsa, lug‘at sahifasiga havola beriladi.

### Kashf qilish
- US-16: Bosh sahifada 🔥 Trending, 🤖 AI terms, 🌍 New words bo‘limlarini ko‘raman.

### Hisob
- US-17: Email + parol bilan ro‘yxatdan o‘taman, kiraman, chiqaman; profil tilini tanlayman.

### Admin
- US-18: Muharrir sifatida AI yaratgan yozuvlarni navbatda ko‘rib, tahrirlab, tasdiqlayman yoki rad etaman.
- US-19: Foydalanuvchilar qidirib topa olmagan so‘zlar ro‘yxatini ko‘rib, ularni AI bilan yarata olaman.
- US-20: Har bir tahrir versiyalanadi, avvalgi holatni ko‘ra olaman.
- US-21: Admin foydalanuvchi rolini/tarifini, tillarni boshqaradi, AI xarajatlarini kuzatadi.

## 5. Funksional talablar
| ID | Talab | Prioritet |
|---|---|---|
| F-1 | Tillar `languages` jadvalida; faol tillar API orqali qaytadi | P0 |
| F-2 | So‘z qidiruvi: exact → shakllar → reverse → prefix → trigram → AI | P0 |
| F-3 | Tabiiy til so‘rovlarini tahlil qilish (regex + LLM fallback) | P0 |
| F-4 | So‘z yozuvi: senses, definitions (ko‘p tilli), translations, examples, pronunciations, relations, etymology, CEFR, chastota | P0 |
| F-5 | AI generatsiya: EntryAgent + VerificationAgent, confidence, status | P0 |
| F-6 | AI izoh (SSE stream), keshlanadi | P0 |
| F-7 | Tarjima (lug‘at birinchi, keyin LLM), kesh | P0 |
| F-8 | TTS audio (kesh bilan), brauzer fallback | P1 |
| F-9 | Auth: JWT (httpOnly cookie) + rollar | P0 |
| F-10 | Favorites, reports | P0 |
| F-11 | Trending (real-time Redis), New words, AI terms | P1 |
| F-12 | Admin: dashboard, words, editor, moderatsiya, reports, missing words, users, languages, AI usage | P0 |
| F-13 | Kvotalar va rate limit (anonim/free/pro) | P1 |
| F-14 | SEO: SSR so‘z sahifalari, metadata, JSON-LD, sitemap | P1 |
| F-15 | UI tillari: uz (default), en, ru; dark mode | P1 |

## 6. Nofunksional talablar
- **Tezlik:** lug‘atdagi so‘z qidiruvi p95 < 150 ms (backend), so‘z sahifasi TTFB < 500 ms.
- **AI generatsiya:** p95 < 20 s; foydalanuvchi kutish holatini ko‘radi.
- **Ishonchlilik:** AI provayder ishlamasa lug‘at qidiruvi ishlashda davom etadi (graceful degradation).
- **Xavfsizlik:** argon2 parollar, httpOnly + SameSite cookie, rate limit, rollar bo‘yicha ruxsat, input validatsiya.
- **Litsenziya:** Wiktionary (CC BY-SA 4.0) ma’lumotlari uchun atributsiya `/about` sahifasida.
- **Kengayuvchanlik:** yangi til qo‘shish kod o‘zgarishini talab qilmasligi kerak (normalizatsiya qoidasi bundan mustasno).
- **Kuzatuv:** har AI chaqiruv `ai_generations` ga token/narx/latency bilan yoziladi.
- **A11y:** klaviatura navigatsiyasi, kontrast WCAG AA.

## 7. Tariflar (monetizatsiya)
| | Free (anonim) | Free (login) | Pro | Developer API |
|---|---|---|---|---|
| Lug‘at qidiruvi | ✅ | ✅ | ✅ | ✅ |
| AI izoh / kun | 5 | 20 | 500 | tarif bo‘yicha |
| AI yangi so‘z / kun | 3 | 10 | 100 | — |
| Tarjima belgi / kun | 2 000 | 10 000 | 200 000 | tarif bo‘yicha |
| Matn uzunligi (bir so‘rov) | 1 000 | 1 000 | 5 000 | 5 000 |
| TTS / kun | 30 | 100 | 2 000 | tarif bo‘yicha |
| Reklama | bor | bor | yo‘q | — |
| Voice (server STT), rasm orqali tarjima, cheksiz learning | — | — | ✅ (keyingi fazalar) | — |

MVP’da to‘lov integratsiyasi yo‘q — admin foydalanuvchi tarifini qo‘lda o‘zgartiradi. Keyin: Payme/Click (UZ), Stripe (xalqaro).
Limitlar `backend/app/core/config.py` dagi `QUOTAS` orqali sozlanadi.

## 8. KPI
- DAU / WAU, qidiruvlar soni, "topilmadi" ulushi (< 5% maqsad).
- So‘z sahifasidan ❤️ konversiyasi.
- AI yozuvlar tasdiqlanish ulushi, o‘rtacha confidence.
- 1000 qidiruvga AI xarajati ($).
- Organik (SEO) trafik ulushi.

## 9. Chegaralar va xavflar
| Xavf | Yumshatish |
|---|---|
| AI gallyutsinatsiyasi | VerificationAgent, confidence threshold, moderatsiya, 🚩 reports |
| AI xarajati o‘sishi | Kesh (DB + Redis), kvotalar, arzon model (flash) arzon vazifalarga |
| O‘zbek tili ma’lumotlari kam | AI backfill + muharrirlar + foydalanuvchi reportlari |
| Litsenziya | Faqat ochiq litsenziyali datasetlar, atributsiya |
| Spam/suiiste’mol | Rate limit, kvota, "haqiqiy so‘z" tekshiruvi |
