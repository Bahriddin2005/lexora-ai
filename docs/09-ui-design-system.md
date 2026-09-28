# 09 — UI dizayn tizimi

Tamoyil: **Google darajasida soddalik** — bitta qidiruv maydoni, keraksiz bezak yo‘q, kontent — asosiy qahramon.

## Brend
- Nom: **Lexora AI** · Shior: "Dunyo tillari bitta joyda."
- Logo: so‘z belgisi `LEXORA` (semibold, harflar oralig‘i keng) + `AI` aksent rangda.

## Ranglar (CSS o‘zgaruvchilar, Tailwind orqali)
| Token | Light | Dark | Qo‘llanilishi |
|---|---|---|---|
| `--bg` | `#ffffff` | `#0b0f17` | Fon |
| `--surface` | `#f6f7fb` | `#121826` | Kartalar |
| `--border` | `#e4e7ef` | `#232b3b` | Chiziqlar |
| `--text` | `#0f172a` | `#e6e9f0` | Asosiy matn |
| `--muted` | `#5b6477` | `#98a2b3` | Ikkinchi darajali matn |
| `--brand` | `#4f46e5` | `#818cf8` | Tugmalar, havolalar |
| `--accent` | `#0ea5e9` | `#38bdf8` | AI elementlari |
| `--success` | `#16a34a` | `#4ade80` | Tasdiqlangan |
| `--warning` | `#d97706` | `#fbbf24` | AI / draft belgilari |
| `--danger` | `#dc2626` | `#f87171` | Xato, rad etish |
Kontrast — WCAG AA (matn ≥ 4.5:1).

## Tipografiya
- Shrift: **Inter** (lotin, kirill) + **Noto Sans** fallback (arab, boshqa yozuvlar); IPA uchun `Noto Sans` / `Charis SIL`.
- Shkala: headword 48/56 px (mobil 36), h2 24, h3 18, body 16, small 14, caption 12.
- Headword — semibold, `letter-spacing: -0.02em`.

## Komponentlar
| Komponent | Tavsif |
|---|---|
| `SearchBox` | Katta (56 px) yumaloq maydon, 🔍, 🎙️, autocomplete dropdown, klaviatura navigatsiyasi (↑↓ Enter Esc) |
| `LanguagePair` | Ikki select + ⇄ tugma |
| `WordHeader` | Headword, IPA + 🔊, POS chiplari, CEFR/chastota badge, asosiy tarjimalar |
| `SenseItem` | Raqam, domen tegi, izoh, tarjima chiplari, misollar, sinonim/antonim |
| `Chip` | Havola-chip (sinonim, tarjima) |
| `Badge` | CEFR, status (AI/draft), domen |
| `AIPanel` | Rejim tugmalari, savol maydoni, stream matn, "AI xato qilishi mumkin" izohi |
| `FavoriteButton`, `ReportDialog`, `SpeakButton` | |
| `WordCard` | Ro‘yxatlar (trending, new, qidiruv) uchun |
| `Skeleton`, `EmptyState`, `ErrorState` | Holatlar |
| Admin: `DataTable`, `StatusSelect`, `JsonDiff` (versiyalar) | |

## Layout va oraliqlar
- Maksimal kenglik: kontent 768 px (so‘z sahifasi), 1200 px (admin).
- Oraliq shkalasi 4 px (Tailwind default). Burchaklar: 12 px kartalar, 999 px qidiruv.
- Soyalar minimal; ajratish — `border` bilan.

## Dark mode
`prefers-color-scheme` + qo‘lda almashtirish (☾), `localStorage` da saqlanadi; `class="dark"` strategiyasi.

## RTL tayyorgarlik
Arab/fors/urdu qo‘shilganda: `dir` atributi so‘z tili bo‘yicha (`languages.direction`); CSS’da logical xususiyatlar (`ms-*`, `me-*`, `ps-*`).

## Accessibility
- Barcha tugmalarda `aria-label` (🔊 "Talaffuzni eshitish").
- Fokus halqasi ko‘rinadi; modal fokusni ushlaydi.
- `lang` atributi har bir kontent bo‘lagida (`<span lang="ru">бежать</span>`) — ekran o‘quvchilar to‘g‘ri talaffuz qiladi.

## Ikonkalar
`lucide-react`; emoji faqat bo‘lim sarlavhalarida (🔥 🤖 🌍).
