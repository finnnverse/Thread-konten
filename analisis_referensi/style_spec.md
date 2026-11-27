# STYLE SPEC — gaya "Peta Skenario What-If" (terukur dari referensi)

Semua angka diukur dari video referensi 720×1280 @60 fps dan dikonversi ke **target 1080×1920** (×1,5).
Kolom "cara ukur" menjelaskan asal tiap angka. Kalau tertulis **estimasi**, artinya angka itu tidak bisa diukur langsung.

---

## 1. Format output
| Item | Nilai | Cara ukur |
|---|---|---|
| Resolusi | 1080×1920 (referensi 720×1280, kemungkinan versi unduhan yang diperkecil) | ffprobe |
| FPS | **60** (referensi 60/1). Opsi 30 fps hanya kalau waktu render jadi masalah. | ffprobe |
| Loudness | **-14 LUFS** integrated, true peak ≤ -1 dBTP (referensi -14,1 / -3,0) | ffmpeg loudnorm |
| Durasi | mengikuti VO (referensi 65 dtk), tanpa intro/outro | |

## 2. Palet (hex diambil langsung dari piksel)
| Elemen | Hex inti | Rentang / glow | Cara ukur |
|---|---|---|---|
| Isian negara "pelaku" (opak) | **#0083FB** | p10 #007DE9 – p90 #0C8BFE | median piksel di dalam Rusia, t=36,0 & 17,6 |
| Pulau/es di wilayah opak | **#3FD0FF** (cyan muda) | — | visual t=17,6 (Novaya Zemlya) |
| Isian negara "target" (transparan) | tint **#C0402E** blend "color/multiply" | hasil di peta: p10 #5D2104 · p50 #8C3816 · p90 #D3765A | median piksel di dalam AS, t=64,6 |
| Laut dalam | **#013144** | p90 #154D5E | t=17,6 Pasifik |
| Laut dangkal/Arktik | **#0D495B** | p90 #206573 | t=17,6 Arktik |
| Daratan tak tersorot (hijau) | **#494F2B** | | Kanada t=64,6 |
| Latar di luar bidang peta | **#191919** | #202021 | strip atas t=17,6 |
| Caption | **#FCFFFF** | outline gelap | median piksel teks (3 frame) |
| Neon cyan (label) | inti **#06EBFF** | glow #006A94 | label OHIO t=6,2 |
| Neon cyan (label vertikal) | inti **#08F4FF** | glow #048BAD | TRIDENT-II t=8,8 |
| Neon kuning | inti **#FFDF0A** / #FFED13 | glow #B5953F | DEAD HAND t=35,5 / SARMAT t=48,4 |
| Neon merah | inti **#F5030A** | glow #B2413D | SATAN-II t=48,4 |
| Putih glow ("x 24") | **#FBFCFE** | halo putih | t=8,8 |
| Api roket | **#FEFC00** | tepi #A38015 | t=8,8 |
| Ledakan | oranye **#F08A3A** (inti terang #FFC060) | | visual t=17,6 |
| Kartu HUD | bingkai **#FF6A3A**, ikon ⚠ merah #FF2A2A | | visual t=21,9 / 23,2 |

## 3. Tipografi
| Peran | Font (OFL, Google Fonts) | Ukuran @1080p | Detail | Cara ukur |
|---|---|---|---|---|
| **Caption** | **Manrope wght 700** | **71 px** (font size); tinggi kapital ≈ **52 px**; x-height ≈ 38 px | fill #FCFFFF; **outline hitam 2–2,5 px, opasitas ±55%**; tanpa offset bayangan; tanpa kotak latar; satu baris; **huruf kecil biasa** (kapital hanya di awal kalimat/nama); tanda baca tetap ditulis | Pencocokan piksel (IoU) 11 kandidat font: Manrope 700 = 0,84–0,85, Rubik 600 = 0,74–0,80, Poppins ≤0,72. Outline: profil luminans di luar glyph (jarak 2 px = 28 vs latar 52) |
| Label neon besar | **Jost wght 600–700**, KAPITAL, **letter-spacing 0,25–0,45 em** (makin lebar saat keluar), dalam tanda kutip ‘…’ | tinggi kapital 45–60 px | inti warna + glow 2 lapis (lihat §4) | **estimasi** visual: geometris ala Futura (A runcing, O bulat). Pencocokan IoU tidak bisa karena label perspektif 3D |
| Label objek (nama/julukan) | Jost 600, KAPITAL, spacing 0,02 em | kapital ±38 px | kuning di atas objek, merah di bawah | estimasi visual t=48,4 |
| Label vertikal | **Space Mono Bold**, KAPITAL, spacing 0,3 em, diputar 90° | kapital ±42 px | cyan neon | estimasi visual (glyph slab mono) |
| Angka pengali "x 24" | **Jost Bold Italic** | tinggi angka ±90 px | putih + halo putih | estimasi visual |
| Callout "x 14 warheads" | **Jost 400** | x-height ±25 px | putih tipis + glow halus, garis penunjuk 2 px | estimasi visual |
| Watermark (baru, tidak ada di referensi) | Manrope 700 | 30 px, opasitas 55% | "WhatIf Atlas" | usulan |

## 4. Efek neon / glow (diukur)
Profil intensitas di luar huruf (piksel 720p): setengah intensitas di **±7 px**, sepersepuluh di **±21–23 px**.
→ Resep 1080p: lapisan inti + **blur Gaussian σ 5 px (opasitas 0,9)** + **blur σ 20 px (opasitas 0,5)**, mode *screen/add*.
Tepi glow tidak kotak/terpotong.

## 5. Tata letak & zona aman (1080×1920)
| Zona | Posisi | Cara ukur |
|---|---|---|
| Caption | pusat **x = 545** (0,505 lebar); bagian atas huruf y ≈ **1514**, baseline **y ≈ 1564** (81,5% tinggi); lebar maks ±880 px | bbox piksel putih tiap frame, 60 fps (x tengah 362–365 dari 720 di hampir semua potongan) |
| Label & objek overlay | pita **y 380–1250** (20–65%), tidak pernah masuk zona caption | posisi elemen di keyframe |
| Objek hero | pusat x ≈ 0,40 lebar, y ≈ 0,50 | t=8,8 |
| Zona UI platform (jangan diisi teks penting) | kanan **x > 930** (tombol like/comment), bawah **y > 1640** (judul/akun), atas **y < 150** | konvensi Shorts/TikTok |
| Watermark | tengah atas **y ≈ 230**, di bawah ikon UI atas | usulan |
| Vinyet | sudut ±12% lebih gelap (**estimasi**; rata-rata seluruh video sudut/tengah = 0,79, tapi sebagian karena konten) | luminans rata-rata 130 frame |

## 6. Peta
- **Citra**: satelit warna natural **dengan batimetri** (laut bertekstur relief). Padanan bebas lisensi: NASA Blue Marble "topo + bathy" (domain publik). Laut di-grade ke teal (#013144–#0D495B).
- **Proyeksi**: tampak **Mercator** (Rusia memanjang ke utara); dipasang sebagai **bidang 3D** dengan kemiringan kecil dan roll kamera ±3–15°/dtk. Tepi bidang dengan latar #191919 sesekali terlihat saat zoom-out.
- **Isian opak**: poligon negara dikecilkan ±2–3 px ke dalam, jadi sisa garis pantai asli (cokelat/gelap) tetap terlihat tipis. Isinya #0083FB dengan tekstur noise halus ±5% kecerahan. Danau tetap berlubang.
- **Isian transparan**: tint merah gaya "color/multiply" (relief tetap terlihat), tepi feather ±4 px, plus **halo terang ±45 px di luar batas** (terlihat di Kanada t=64,6).
- Geometri batas: Natural Earth admin-0 (10m untuk close-up, 50m untuk zoom-out).

## 7. Animasi (durasi diukur dari jumlah piksel warna per frame @60 fps)
| Jenis | Masuk | Tahan | Keluar | Easing | Data ukur |
|---|---|---|---|---|---|
| Caption | **cut 0 frame** | sampai potongan berikut | cut | — | piksel putih berubah dalam 1 frame |
| Label neon besar | **0,45 dtk**, muncul per huruf kiri→kanan (stagger ±0,03 dtk/huruf) dengan kilatan awal (puncak ±2× lalu turun) | 0,5–0,9 dtk, spacing melebar pelan | **0,5–0,7 dtk**, huruf melebar + memudar jadi titik | masuk ease-out; keluar ease-in | cyan 6,03→6,50 / 7,00→7,50; merah 25,2→25,5 / 26,2→26,9; kuning 35,0→35,4 / 35,9→36,6 |
| Isian negara transparan | **0,7 dtk** fade | permanen | — | ease-out | 29,25→29,95 |
| Ledakan | pop **0,15 dtk** skala 0→1,15→1,0; muncul berurutan tiap ±0,2 dtk | tetap & berdenyut | fade 0,3 dtk | ease-out-back | jumlah piksel oranye bertambah bertahap 17,1–17,7 |
| Objek hero (latar blur) | latar blur **0,2 dtk** (7,25→7,45); objek pop **0,12 dtk** | selama kalimat | **rack-focus**: objek blur 0,15 dtk → keduanya blur 0,5 dtk → peta tajam 0,15 dtk | ease-in-out | ketajaman Laplacian: 76→9 dan 207→11→75 |
| Label menempel objek, keluar | **jatuh** ±165 px dalam 0,6 dtk + fade | | | ease-in (gravitasi) | pusat-y kuning: 191→246 (@360p) dalam 50,0→50,6 |
| Kartu HUD | glitch: double-exposure + blur 0,5 dtk → tajam | berkedip ±0,5 dtk | scale-down 0,2 dtk | | 21,5–22,7 |
| Stiker (nisan, radar, bubble) | pop 0,15–0,2 dtk + overshoot; bubble goyang ±4° | | scale-down 0,3–0,8 dtk | ease-out-back | visual |
| Jejak rudal | garis melengkung tumbuh mengikuti kepala, 1,0–1,5 dtk per lintasan | ekor memudar | | ease-in-out | visual |

## 8. Kamera (diukur per frame: ORB + affine parsial)
- **Tanpa cut sama sekali.** Pindah lokasi selalu pakai whip-zoom atau whip-pan.
- **Profil kecepatan selalu berbentuk lonceng** (sinus ease-in-out), tanpa lonjakan. Contoh terukur:
  - Whip zoom-out 0,0→1,15 dtk: puncak −4,9%/frame di 0,5 dtk, total ×0,19.
  - Whip zoom-in 4,0→4,8 dtk: puncak +4,2%/frame.
  - Whip-pan 58,3→59,9 dtk: puncak **25 px/frame @720p (≈37 px/frame @1080p)**, durasi 1,6 dtk.
  - Pan mengikuti rudal 28,0→30,0 dtk: puncak 8,4 px/frame @720p.
- **Durasi gerak besar: 0,8–1,6 dtk**, dimulai 0–0,3 dtk sebelum kata kuncinya.
- **Drift** saat "diam": zoom ±5–30%/dtk + roll ±2–10°/dtk. Kamera hanya benar-benar diam saat objek hero tampil dengan latar blur.
- **Tracking**: saat objek bernama terbang, objek tetap di layar dan peta yang bergeser (−170..−220 px/dtk @720p).
- Batas aman implementasi: perubahan kecepatan per frame ≤ 15% dari puncak, supaya tidak ada loncatan.

## 9. Ritme
- Narasi **3,16 kata/dtk** (190 wpm).
- Caption: **2–4 kata, ganti tiap 0,4–1,3 dtk** (median ±0,7 dtk), sinkron ke awal kata pertama potongan (selisih 0–0,1 dtk).
- Perubahan visual besar (label/objek/gerak kamera): **tiap 1–2,5 dtk**, tepat di kata kunci (angka, nama, kata kerja aksi).
- Setiap **angka** yang diucapkan selalu punya visual (x 24, x 14, jumlah ledakan, dll).

## 10. Audio
**Keterbatasan:** saya tidak bisa mendengar audio. Analisis di bawah berasal dari spektrogram + deteksi onset, termasuk trik pemisahan **kanal side (L−R)**: VO direkam mono di tengah, jadi kanal side hampir murni musik/SFX. Lihat `spektrogram_mix.png` dan `spektrogram_musik_sfx.png`.

| Lapisan | Temuan | Cara ukur |
|---|---|---|
| VO | pria, nada dasar ±100–130 Hz, padat (hampir tanpa jeda >0,15 dtk) | spektrogram mix |
| Musik | **pad/drone sinematik gelap + sub-bass**, akor bertahan dan berganti tiap ±1,3 dtk (periodisitas 46 BPM, kemungkinan setengah tempo **±92 BPM**). Tidak ada drum yang jelas. | spektrogram side + autokorelasi onset |
| Level musik | kanal side **-14 dB di bawah mix**; energi <85 Hz −10 dB dari pita vokal → musik ±**-16 s/d -20 dB di bawah VO** | volumedetect mid/side |
| SFX whoosh (noise lebar 500 Hz–10 kHz, 0,5–1,5 dtk) | 1,2–2,4 (peluncuran) · 3,4–4,0 (whip zoom-in) · 14,6–15,6 (peluncuran) · 26,4–28 (peluncuran/pan) · 30,8–31,6 (whip) · 37,0–38,3 · 51,2–51,6 (zoom-out) · 59,0–60,5 (whip) | blok noise lebar di spektrogram side |
| SFX nada/alarm | ±1,3 kHz, 0,6 dtk di **22,0–22,6** (kartu peringatan) · sapuan nada ±3 kHz turun di 0,4–2,3 (ping/sonar saat cincin target) | garis horizontal tipis di spektrogram side |
| SFX dentum | sub-bass kuat 0–2,3 dtk (pembuka) · "drop" (energi bawah hilang sesaat) di 22,7 · 27,1 · 51,9 | pita <80 Hz |
| Ledakan | tidak ada transien keras yang menonjol. Ledakan kemungkinan tidak ber-SFX, atau SFX-nya sangat pelan. | tidak ada puncak sub-bass konsisten di 2,9/17,3/33,3/53 |

**Resep mix untuk video baru:** VO -14 LUFS dominan · musik drone sintetis ±92 BPM di -18 dB relatif VO, ducking 4–6 dB saat VO bicara · whoosh di tiap whip/peluncuran (-12 dB) · alarm di kartu peringatan · sub-boom di detik 0. Semua dibuat sintetis (bebas hak cipta).

## 11. Yang TIDAK ditiru
Naskah kata per kata, potret tokoh nyata, musik/SFX asli, dan suara VO. Referensi tidak memiliki watermark, logo, atau ikon sosmed.

## 12. Keyframe referensi
18 frame resolusi penuh ada di `keyframes/` (kf01–kf18), ringkasannya di `keyframes_overview.jpg`.
