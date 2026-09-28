# 08 — Admin panel

Admin panel frontendning `/admin` bo‘limi (bir xil auth, bir xil dizayn). Backend: `/api/v1/admin/*`.

## Rollar va ruxsatlar
| Amal | user | editor | admin |
|---|---|---|---|
| Lug‘atdan foydalanish, ❤️, 🚩 | ✅ | ✅ | ✅ |
| Dashboard, so‘zlar ro‘yxati, muharrir, moderatsiya, reportlar, topilmaganlar, AI usage | | ✅ | ✅ |
| So‘zni o‘chirish | | | ✅ |
| Foydalanuvchilar (rol, tarif, bloklash) | | | ✅ |
| Tillarni boshqarish | | | ✅ |

Birinchi admin: `python -m scripts.create_admin email parol` (yoki `make admin`).

## Sahifalar
### `/admin` — Dashboard
Kartalar: jami so‘zlar (status bo‘yicha), tillar bo‘yicha, foydalanuvchilar, 24 soatdagi qidiruvlar, "topilmadi" ulushi,
7 kunlik AI xarajati ($), ochiq reportlar. Jadval: top-10 topilmagan so‘zlar (tez "AI bilan yaratish" tugmasi bilan).

### `/admin/words` — So‘zlar
Filtrlar: status, til, qidiruv. Ustunlar: lemma, til, POS, status, confidence, versiya, yangilangan. Paginatsiya.
"Yangi so‘z" (qo‘lda) va "AI bilan yaratish" tugmalari.

### `/admin/words/[id]` — Muharrir
- Chapda forma: lemma, entry_type, CEFR, teglar, etimologiya (uz/en), talaffuzlar (IPA, aksent), shakllar.
- Senses: qo‘shish/o‘chirish/tartiblash; har sense — POS, domen, register, CEFR, izohlar (til bo‘yicha), tarjimalar (til bo‘yicha, asosiy belgisi),
  misollar (+ tarjimalar), sinonim/antonim.
- O‘ngda: status, confidence, manbalar, **versiyalar tarixi** (snapshot’ni ko‘rish), ochiq reportlar.
- Tugmalar: 💾 Saqlash (sabab kiritiladi → versiya +1), ✅ Nashr qilish, ⛔ Rad etish, 🔁 AI bilan qayta yaratish, 🗑 O‘chirish (admin).

### `/admin/moderation` — Moderatsiya navbati
`draft` va `ai_generated` yozuvlar. Saralash: talab (so‘nggi 30 kun qidiruvlar soni) ↓, confidence ↑, reportlar ↓.
Har qatorda: lemma, til, confidence, Verification issues, tezkor ✅/⛔ va "Tahrirlash".

### `/admin/reports` — Reportlar
Filtr: `open` / `resolved` / `rejected`. Qator: so‘z (havola), sabab, izoh, kim, qachon; "Hal qilindi" / "Rad etildi".

### `/admin/missing` — Topilmagan so‘zlar
`search_logs.found=false` guruhlangan: normalized, namunaviy so‘rov, til, soni, oxirgi qidiruv. "AI bilan yaratish" → job.

### `/admin/users` — Foydalanuvchilar (admin)
Qidiruv (email), rol, tarif, faol/bloklangan — inline o‘zgartirish.

### `/admin/languages` — Tillar (admin)
Ro‘yxat, faol/nofaol, tartib, TTS qo‘llab-quvvatlashi; yangi til qo‘shish (code, name, native_name, script, direction, flag).

### `/admin/ai-usage` — AI xarajatlari
Davr (7/30 kun): jami chaqiruvlar, tokenlar, $; agent bo‘yicha jadval; kunlik grafik; xatolar ulushi.

## Moderatsiya oqimi
```
Foydalanuvchi qidiradi → topilmadi → AI (Entry → Verify)
   ├─ ai_generated → saytda "AI" belgisi bilan ko‘rinadi → moderatsiya navbatida
   └─ draft → faqat navbatda
Muharrir: tekshiradi → tahrirlaydi (versiya) → ✅ published / ⛔ rejected
Foydalanuvchi 🚩 → report → muharrir hal qiladi (kerak bo‘lsa so‘zni tahrirlaydi)
```

## Audit
Har tahrir `word_versions` (kim, qachon, sabab, to‘liq snapshot). Status o‘zgarishlari ham versiya sifatida yoziladi.
