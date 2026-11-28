---
name: whatif-map-shorts
description: "Buat video peta vertikal 1080x1920 60fps gaya 'What-If peta satelit' (Shorts/TikTok/Reels) untuk topik APA PUN dari user: geopolitik, jalur dagang, sejarah, bencana, militer. Peta satelit ber-grade teal, sorotan negara dari geometri asli, kamera whip-zoom mulus, caption 2-4 kata Manrope, label neon 3D, animasi journey (BigLabel, LeaderLabel, busur neon, kapal/pejalan, Chip, finale kartu), SFX bervariasi + musik sintetis, -14 LUFS. Topik, naskah, dan VO SELALU dari user."
---

# WhatIf Map Shorts — skill gaya video peta

> **BACA DULU (untuk AI yang memakai skill ini)**
> 1. Skill ini **tidak berisi topik**. Topik/naskah/VO selalu dari user di percakapan.
> 2. Jangan membuat ulang video referensi atau contoh proyek (contoh ada di zip terpisah).
> 3. Mulai dari **`MULAI_DI_SINI.md`**.
> 4. Aturan gaya terukur ada di `reference/style_spec.md`; keyframe referensi di `reference/keyframes/`.

## Isi
| Path | Isi |
|---|---|
| `engine/` | renderer Python (numpy, PIL, OpenCV, scipy, ffmpeg) |
| `engine/render.py` | timeline `project.json` → MP4 (render paralel per segmen) |
| `engine/tiles.py`, `destreak.py` | citra Sentinel-2 cloudless 2016 (EOX, CC BY 4.0) + penghapus garis awan orbit + es laut |
| `engine/maprender.py` | peta dasar (mip mulus, tanpa aliasing), grade warna, sorotan negara opak/transparan |
| `engine/camera.py` | kamera PCHIP + penghalus Gaussian waktu, `check_camera()` (tanpa loncatan) |
| `engine/text.py` | caption Manrope 700 (terukur), pemecah caption 2-4 kata |
| `engine/fx.py`, `sprites.py` | label neon 3D, jejak/rudal, ledakan, kartu HUD, stiker vektor |
| `engine/journey_fx.py` | animasi journey (map-journey-style) lewat kunci `"jfx"` |
| `engine/audio.py` | musik drone sintetis + 20 SFX + perencana SFX anti-repetisi + mix -14 LUFS |
| `tools/asr_words.py` | transkripsi VO → waktu tiap kata (Parakeet ONNX) |
| `tests/stills.py`, `sheet.py`, `camcheck.py`, `check_cam.py`, `compare.py` | QC |
| `projects/template/make_project.py` | kerangka proyek baru |
| `fonts/`, `assets/fonts/` | Manrope, Jost, Space Mono, Lilita One, Montserrat (semua OFL, lisensi disertakan) |
| `data/` | Natural Earth admin-0 10m/50m/110m (domain publik) |
| `reference/` | style_spec.md (angka terukur), keyframes, breakdown |

## Aturan gaya (ringkas — detail & cara ukur di `reference/style_spec.md`)
- **Format:** 1080x1920, 60 fps, H.264 + AAC, **-14 LUFS**, TP ≤ -1 dBTP. Tanpa intro/outro, tanpa CTA, selesai di angka/kalimat penutup.
- **Caption:** Manrope 700 ukuran 71 px, #FCFFFF, outline gelap 2 px 55%, **bayangan halus** (supaya terbaca di gurun/salju), pusat x 0,505·W, baseline 0,815·H. Isinya 2-4 kata dan **ganti keras** tepat di kata pertama.
- **Peta:** satelit dengan grade laut teal #013144–#0D495B dan darat zaitun. Sorotan memakai **geometri asli Natural Earth**: pelaku = opak #0083FB, target = tint merah dengan relief tembus.
- **Kamera:** tanpa cut. Pindah lokasi = whip-zoom/whip-pan berbentuk lonceng 0,8–1,6 dtk. Selalu drift pelan + roll ±2–10°/dtk. Jalankan `check_camera`: maks ±37 px/frame, percepatan ≤1,5 px/f².
- **Ritme:** 1 perubahan visual tiap 1–2,5 dtk, **tepat di kata kuncinya** (angka, nama, kata kerja). Setiap angka yang diucapkan harus punya visual.
- **Label:** neon 3D (Jost, kapital, tracking lebar, glow 2 lapis σ5/σ20) untuk nama besar; BigLabel journey untuk angka; LeaderLabel untuk nama kecil; Chip untuk fakta pendek.
- **Preferensi user (wajib):**
  - **Jangan pakai adegan "objek besar + latar blur"** (roket/warhead di tengah layar). Angka ditampilkan **di atas peta**.
  - **Whoosh hanya di momen besar** (≥5 dtk jarak, maks 6/menit). SFX lain dibuat bervariasi: satu jenis SFX maks 2× per 8 dtk.
  - Kirim contoh/klip uji sebelum render panjang.
- **Aman platform:** bahasa netral, tanpa tokoh nyata (potret), tanpa korban/kekerasan grafis. Kata sensitif boleh disensor ala referensi ("W#R").

## Atribusi wajib (deskripsi video)
`Map data: Natural Earth. Satellite imagery: Sentinel-2 cloudless - https://s2maps.eu by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2016), CC BY 4.0.`
**Jangan** memakai layer s2cloudless 2018+ (lisensi NC) untuk channel yang dimonetisasi.

## Batasan (sampaikan jujur ke user)
- Objek (kapal selam, roket, nisan, radar) adalah vektor 2D, bukan model 3D.
- Belang lajur orbit Sentinel yang samar kadang masih terlihat di zoom menengah.
- Audio sintetis; AI tidak bisa mendengar hasilnya, hanya mengukur level.
- Render ±16 dtk per 1 dtk video di 4 core (60 fps).
