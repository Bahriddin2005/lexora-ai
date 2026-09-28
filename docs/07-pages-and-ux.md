# 07 — Sahifalar va UX

Belgi: ✅ MVP · ⏳ keyingi faza.

## Sahifalar xaritasi
| Yo‘l | Sahifa | Kirish | Faza |
|---|---|---|---|
| `/` | Bosh sahifa | hamma | ✅ |
| `/search?q=&from=&to=` | Qidiruv natijalari | hamma | ✅ |
| `/w/[lang]/[slug]` | So‘z sahifasi | hamma | ✅ |
| `/translate` | Tarjimon | hamma | ✅ |
| `/trending` | 🔥 Trending so‘zlar | hamma | ✅ |
| `/new` | 🌍 Yangi so‘zlar | hamma | ✅ |
| `/ai-terms` | 🤖 AI terminlari | hamma | ✅ |
| `/login`, `/register` | Kirish / ro‘yxatdan o‘tish | mehmon | ✅ |
| `/profile` | Profil, UI tili, tarif, kvota | user | ✅ |
| `/favorites` | ❤️ Mening lug‘atim | user | ✅ |
| `/about` | Loyiha haqida, manbalar va litsenziyalar | hamma | ✅ |
| `/admin/*` | Admin panel (08-admin-panel.md) | editor/admin | ✅ |
| `/learn`, `/learn/flashcards`, `/learn/quiz`, `/learn/progress` | Learning | user | ⏳ 5 |
| `/live` | ⚡ Live Words oqimi | hamma | ⏳ 4 |
| `/pricing`, `/developers`, `/developers/keys` | Tariflar, API hujjatlari, kalitlar | hamma/user | ⏳ Scale |

## Global layout
```
┌───────────────────────────────────────────────────────────────────┐
│ LEXORA AI   [🔍 kichik qidiruv]   Tarjima  Trending  AI terms  ☾  UZ▾  Kirish │
├───────────────────────────────────────────────────────────────────┤
│                              kontent                               │
├───────────────────────────────────────────────────────────────────┤
│ Haqida · Manbalar (Wiktionary CC BY-SA) · API · © Lexora AI         │
└───────────────────────────────────────────────────────────────────┘
```
Bosh sahifada header qidiruvi yashiriladi. `/` tugmasi — qidiruvga fokus; `Esc` — tozalash.

## Bosh sahifa `/`
```
                         LEXORA AI
                 Dunyo tillari bitta joyda.

        ┌─────────────────────────────────────────┐
        │ 🔍 So‘z yoki ibora kiriting          🎙️ │
        └─────────────────────────────────────────┘
            [autocomplete: run — yugurmoq · runner — yuguruvchi]

               Uzbek 🇺🇿   ⇄   English 🇬🇧

   🔥 Trending          🤖 AI terms          🌍 New words
   • cringe             • LLM                • vibe coding
   • deadline           • prompt             • rizz
```
- 🎙️ — brauzer Web Speech API (`SpeechRecognition`), til = tanlangan manba til; qo‘llanmasa yashiriladi.
- Til juftligi `from/to` sifatida qidiruvga uzatiladi va `localStorage` da eslab qolinadi.

## Qidiruv natijalari `/search`
- Bitta `exact` natija bo‘lsa → darhol `/w/{lang}/{slug}` ga redirect.
- Bir nechta natija: kartalar (lemma, til bayrog‘i, POS, qisqa izoh, asosiy tarjima, `match` belgisi).
- 0 natija + `did_you_mean` → "**beautiful** nazarda tutdingizmi?" havolalar + "AI bilan baribir izlash" tugmasi.
- `job` bo‘lsa → "🤖 AI bu so‘zni tayyorlamoqda…" (skeleton + progress), 1.5 s polling, tayyor bo‘lgach redirect.
  `draft` → "Ma’lumot muharrirlarga tekshiruvga yuborildi". `not_a_word` → takliflar.
- `list_new_terms` → sarlavha "2026 · AI sohasidagi yangi terminlar" + ro‘yxat.

## So‘z sahifasi `/w/[lang]/[slug]`
```
 🇬🇧 English · verb, noun · A1 · ●●●●○ chastota        [❤️] [🚩] [↗ ulashish]
 ┌──────────────────────────────────────────────────────────┐
 │  run                                                     │
 │  /rʌn/ 🔊 US   /rʌn/ 🔊 UK                               │
 │  🇺🇿 yugurmoq · 🇷🇺 бежать · 🇹🇷 koşmak                    │
 └──────────────────────────────────────────────────────────┘
 [🤖 AI tomonidan yaratilgan · ishonch 78%]  (faqat ai_generated)

 VERB
 1. oyoqda tez harakatlanmoq   (to move swiftly on foot)
    🇺🇿 yugurmoq, chopmoq  🇷🇺 бежать  🇹🇷 koşmak
    › She runs every morning. — U har tong yuguradi.
    Sinonim: sprint, dash · Antonim: walk
 2. [business] boshqarmoq  (to manage)
    ...
 NOUN
 1. yugurish ...

 Iboralar: run out of · run into · in the long run
 Shakllar: ran · running · runs
 ▸ Etimologiya
 ┌ 🤖 AI bilan tushunish ────────────────────────────────┐
 │ [Sodda] [Batafsil]  [Savol bering…            ] [→]    │
 │ (stream matn)                                          │
 └────────────────────────────────────────────────────────┘
 Manbalar: Wiktionary (CC BY-SA 4.0)
```
- Izohlar tartibi: foydalanuvchi UI tili (`uz`) birinchi, so‘ng so‘zning o‘z tilidagi izoh.
- Sinonim/antonim/tarjima chiplari — lug‘atdagi sahifaga havola.
- 🔊: `/api/v1/tts` audio; xato bo‘lsa `speechSynthesis`.
- 🚩: modal — sabab (noto‘g‘ri tarjima / izoh / talaffuz / haqoratli / boshqa) + izoh.
- ❤️: login bo‘lmasa `/login?next=…`.
- SEO: SSR, `<title>run — ma’nosi, tarjimasi, talaffuzi | Lexora AI</title>`, description, canonical, OpenGraph, JSON-LD `DefinedTerm`.
- `draft/rejected` — 404 (admin uchun admin muharriri).

## Tarjimon `/translate`
Ikki panel: chapda manba (til tanlash + auto), o‘ngda natija; ⇄ almashtirish; belgi hisoblagich (limit bilan);
muqobillar va izohlar; natijada 🔊 va 📋 nusxalash; bitta so‘z bo‘lsa "Lug‘atda ochish →".

## Auth sahifalari
Minimal forma, xatolar inline (o‘zbekcha), muvaffaqiyatdan so‘ng `next` ga qaytish.

## Holatlar
- Yuklanish: skeleton. Xato: do‘stona xabar + qayta urinish. AI mavjud emas: "AI vaqtincha ishlamayapti".
- Kvota tugadi: "Bugungi limit tugadi — ertaga qayta urinib ko‘ring yoki Pro’ga o‘ting".

## UI tillari
`uz` (default), `en`, `ru` — yengil o‘z i18n qatlami (`frontend/src/i18n`, `next-intl` hali Next.js 16 ni rasman qo‘llamaydi), cookie `NEXT_LOCALE`; lug‘at kontenti tili UI tilidan mustaqil. Admin panel faqat o‘zbek tilida.

## Mobil
Mobile-first: qidiruv to‘liq kenglikda, header menyusi burger, so‘z sahifasida sticky "🔊 ❤️" panel.
