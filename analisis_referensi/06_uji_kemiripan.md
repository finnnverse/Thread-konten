# TAHAP 6 — Uji kemiripan (demo v3)

**File:** `whatif_engine/out/demo_v3_audio.mp4` (37,1 dtk) · `perbandingan_v3.jpg` (14 momen, REF kiri / KITA kanan) · `perbandingan_v1.jpg` (versi pertama, untuk melihat perubahannya)

| Cek | Hasil |
|---|---|
| Format | 1080×1920, 60 fps, H.264 + AAC ✔ |
| Loudness | **-14,5 LUFS**, true peak -0,8 dBTP ✔ (target -14 ±0,5) |
| Kamera (analitik, dari lintasan kamera) | puncak 35 px/frame (ref 37) · percepatan maks 1,8 px/frame² di awal whip-zoom 0,4 dtk, selebihnya ≤ 1,5 ✔ |
| Kamera (diukur dari video, ORB) | 40 kandidat "loncatan", **39 di antaranya** jatuh di jendela objek hero/rudal besar. Di jendela itu detektor membaca gerak objek, bukan gerak peta. Satu kandidat nyata kecil di 27,3 dtk (perubahan arah pan). |
| Teks gemetar | caption ditempel di piksel bulat dan diam. Label yang bergerak memakai penempatan sub-piksel (warpAffine) ✔ |
| Tepi sorotan | geometri Natural Earth 10m, fillPoly sub-piksel 1/16 + anti-alias ✔ |

## Perbandingan per momen
| # | Momen | Status |
|---|---|---|
| 1 | Pembuka + caption | Caption **identik** (font, ukuran, posisi). Kapal selam tanpa ikon bendera (sengaja netral; bisa ditambah lewat PNG). |
| 2–3 | Whip zoom-out, jejak, ledakan | Sangat mirip: jejak putih, kepala rudal, ledakan pop. |
| 4 | Label neon cyan 3D | Mirip: per huruf, perspektif, glow 2 lapis. Referensi lebih "3D" (huruf melengkung di bidang peta); punyaku memakai perspektif datar. |
| 5 | Objek hero + latar blur | Mirip: roket, api, "x 24", label vertikal. Roket referensi model 3D dengan shading lebih halus. |
| 6 | Callout | Mirip. Warhead bus referensi model 3D bertekstur tembaga. |
| 7 | Ledakan menyebar | Mirip. |
| 8 | Kartu HUD | Mirip. Isi kartu referensi lebih transparan/oranye. |
| 9 | Label neon merah | Mirip (di frame contoh masih dalam animasi masuk). |
| 10 | Isian merah AS | Mirip: relief tembus, halo di batas utara. |
| 11 | Nisan + label kuning | Mirip. Tangan zombie **tidak** dibuat (opsional lewat PNG). |
| 12 | Rudal + label menempel | Mirip: label kuning di atas, merah di bawah, jatuh saat keluar. |
| 13 | Hujan garis kuning | Mirip. |
| 14 | Radar + gelembung | Konsep sama. Radar referensi foto/3D, punyaku vektor sederhana. |

## Perbedaan yang masih ada (jujur)
1. **Objek 3D vs vektor 2D.** Kapal selam, roket, warhead bus, nisan, dan radar di referensi adalah model 3D/foto. Punyaku digambar vektor dengan shading. Dari jauh mirip, dari dekat terlihat lebih "flat". *Perbaikan:* engine bisa memakai PNG apa pun (`"sprite": "png:file.png"`), misalnya render 3D bebas lisensi milikmu.
2. **Citra satelit.** Sumbernya Sentinel-2 2016 (CC BY). Garis awan orbit sudah dihapus otomatis, tapi **belang lajur orbit yang samar** masih bisa terlihat di Kanada/AS pada zoom menengah. Referensi tampak memakai citra yang lebih halus (gaya Blue Marble). NASA Blue Marble resolusi tinggi diblok jaringan di sini.
3. **Label neon 3D.** Referensi melengkungkan huruf mengikuti bidang 3D. Punyaku perspektif trapesium.
4. **Es laut Arktik** sebagian masih tampak sebagai bercak teal pucat di sekitar pulau kutub.
5. **Audio.** Musik dan SFX sintetis (bebas hak cipta), meniru pola yang terukur, bukan suaranya. Saya tidak bisa mendengar hasilnya; levelnya diverifikasi dengan meter.
6. Demo memakai **timing kata buatan** (belum ada VO). Untuk video final, caption mengikuti transkripsi VO kamu.

## Rencana perbaikan (kalau kamu mau lanjut iterasi)
- Tambah ikon bendera opsional di atas kapal selam/kendaraan (PNG bendera domain publik).
- Kurangi sisa es laut (ambang lebih ketat + mask pulau).
- Lengkungan label neon (warp silinder).
