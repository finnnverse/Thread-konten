---
name: "satmap-story-shorts"
description: "Buat Shorts/TikTok/Reels vertikal gaya 'cerita peta satelit + kartun': peta citra satelit yang terus bergerak, maskot hewan/benda kartun flat di atas peta, adegan kartun sela, caption 1-2 baris di ATAS layar dengan kata kunci berwarna, ±130 detik, ditutup polling 'Ngaku deh... kamu pilih mana?'. Dari topik/riset sampai naskah, lalu dari VO user sampai MP4. Bahasa Indonesia."
---

# Satmap Story Shorts

Gaya ini dipelajari dari 2 video referensi (topik: badak jawa di Ujung Kulon, dan kenapa Kalimantan tidak punya harimau). **Referensi hanya untuk gaya**: jangan memakai nama channel, watermark, karakter, teks kartu, atau naskah mereka. Semua karakter, warna merek, dan kalimat dibuat sendiri (lihat bagian "Pembeda dari referensi").

Hubungan dengan skill lain: ini saudara dari `map-route-shorts` (@mapnesiaa). Bedanya: basemap **satelit** (bukan peta vektor Natural Earth), caption di **atas** (bukan satu kata di bawah), ada **adegan kartun penuh layar**, dan durasi **±2 menit** gaya bercerita (bukan 45-60 dtk). Bila engine `maproute-engine.zip` tersedia, pakai ulang kameranya, align VO, mixer audio, dan kartunya; tambahkan modul di bagian "Engine".

---

## 1. Anatomi video referensi (hasil bedah)

| Aspek | Temuan |
|---|---|
| Format | 1080x1920 (referensi diunduh 480x854), 30 fps, ±135 dtk |
| Panjang VO | ±290-310 kata, ±45 kalimat; 1 kalimat 1,5-4 dtk; jeda antar-kalimat ±0,3 dtk |
| Suara | VO pria santai (gaya TTS natural, bahasa gaul ringan: "nggak", "gede", "nyebut", "ngaku deh"), musik latar pelan terus-menerus tanpa jeda, SFX kecil (whoosh, pop) |
| Kamera | **Hampir tanpa hard-cut** (deteksi scene hanya 1 cut keras per video). Kamera meluncur/zoom terus di atas peta satelit; adegan kartun masuk lewat transisi geser/fade |
| Proporsi adegan | ±70% peta satelit, ±30% adegan kartun penuh layar |
| Ganti visual | tiap 2-3 dtk (setiap frasa caption) |

### 1a. Caption (ciri paling khas)
- Posisi **atas**, baris pertama di y ≈ 8-9% tinggi layar (≈160 px dari 1920), rata tengah.
- Font sans **tebal membulat** (Montserrat ExtraBold / Fredoka Bold / Poppins ExtraBold), KAPITAL, putih + bayangan lembut gelap (tanpa kotak).
- Pola 2 baris: baris 1 putih kecil (konteks), baris 2 **kata kunci berwarna** sedikit lebih besar. Kadang baris 2 sangat besar sebagai "punch" (1 kata/angka).
  - Contoh pola: `TERSISA CUMA DI` / `UJUNG KULON` (kuning), `NGGAK SAMPAI` / `100 EKOR` (merah besar), `AIR LAUT TURUN` / `120 METER` (biru).
- Kode warna kata kunci (konsisten, makna emosional):
  - **Kuning**: nama tempat, istilah, info netral penting (UJUNG KULON, REFUGIUM, JAUH LEBIH ANEH)
  - **Merah/coral**: angka bahaya, kematian, kehilangan, tuduhan (100 EKOR, MATI, PIDANA, KARENA KITA)
  - **Hijau**: selamat, hutan, hal positif (BADAKNYA SELAMAT, HUTANNYA BAGUS)
  - **Biru muda**: air/laut/es/alam (DIKEPUNG LAUT, LAUT NAIK LAGI, KARENA ALAM)
- Caption **bukan transkrip penuh**: ringkasan 2-6 kata dari kalimat VO, muncul kata per kata (pop/fade ±0,1 dtk per kata), baris 2 muncul tepat saat kata kuncinya diucapkan.
- Jeda dramatis: caption "KATANYA..." / "TERNYATA..." / "NGAKU DEH..." pakai elipsis.

### 1b. Layer peta satelit
- Citra satelit warna natural (laut biru tua bergradasi, daratan hijau-cokelat), sedikit vignette gelap di tepi, warna agak redup supaya caption terbaca.
- **Sorotan wilayah**: pulau/area diberi fill kuning-zaitun semi transparan (±55%) + glow tepi; warna lain untuk kontras (oranye-cokelat untuk wilayah kedua, merah-bata untuk wilayah "rusak").
- **Label peta**: teks kapital kecil putih/kuning + panah lengkung tipis tangan ("KALIMANTAN ↘", "BANTEN ↓").
- **Maskot di peta**: ikon kepala/badan hewan flat (abu-abu badak, oranye harimau) diletakkan di lokasi, pop-in + memantul kecil.
- Grafis di peta (semua flat, garis putih/kuning, ujung membulat):
  - garis putus-putus rute + ikon bergerak; **jejak kaki** berjalan untuk migrasi hewan
  - lingkaran riak konsentris (tsunami, gempa, sonar) dan lingkaran sorot kuning
  - pin bernomor 1-2-3 dengan panah (mis. "dikepung laut di 3 sisi")
  - tanda tanya dalam lingkaran putus-putus, tanda X merah, ikon gelombang
  - **pengukur vertikal** (bar air 0 m sampai -120 m) + pembanding gedung "40 LANTAI"
  - **jam berputar mundur** / ikon ⏪ untuk "kita mundur dulu" (+ efek garis scan/VHS)
  - animasi muka laut turun/naik (daratan Sunda muncul/tenggelam)
  - deret ikon menyebar ke banyak lokasi lalu hilang satu per satu ("satu per satu")
  - pola kotak sawah/kota menutupi pulau (hutan dibuka)

### 1c. Adegan kartun penuh layar (sela)
Gaya flat vector, garis luar tipis, gradasi lembut, latar sederhana:
- **Langit + awan + rumput** (siang): perubahan habitat (gedung tumbuh), rumah kedua, truk pindahan, hewan diangkat helikopter.
- **Malam + bulan + siluet pohon**: bahaya/pemburu (senter, siluet orang).
- **Sabana oranye senja + akasia**: luar negeri (Afrika), dengan siluet kawanan lalu berubah jadi garis putus-putus (mati).
- **Gua cokelat + grid ekskavasi**: penemuan fosil (tulang, gigi, harimau "hantu" biru bercahaya).
- **Hutan hujan gelap + hujan**: lingkungan sulit.
- **Infografis hitungan**: grid ikon hewan (100 ikon, 10 berwarna merah putus-putus = "1/10"), ikon "dulu ada 10, sekarang mati semua".
- **Metafora benda**: kulkas berlogo pulau yang ternyata kosong ("pulau raksasa, kulkas kosong"), paspor dicoret, kulit+taring dicoret ("bukan oleh-oleh, itu pidana"), gedung sekolah berisi titik-titik (pembanding jumlah).
- **Karakter manusia** (kepala bulat putih, wajah simpel): penjelajah bertopi safari (manusia/penonton), profesor rambut putih + kacamata (peneliti). Dipakai untuk "manusia susah masuk", "peneliti nemu", dan di penutup.

### 1d. Penutup (CTA polling) ±8-10 dtk
1. Latar hutan/langit + maskot atau karakter.
2. Caption `NGAKU DEH...` lalu baris kuning `KAMU PILIH MANA?` / `DULU KAMU KIRA?`.
3. Kartu opsi bergambar (thumbnail persegi membulat + nomor bulat berwarna + label 2 baris) muncul **satu per satu** sinkron dengan VO; opsi 1 diberi centang biru.
4. Diakhiri `JAWAB DI KOMENTAR` besar kuning + balon chat "Aku: •••".

---

## 2. Formula naskah (dua referensi memakai pola yang sama)

| Detik | Blok | Fungsi | Pola kalimat |
|---|---|---|---|
| 0-5 | **Hook paradoks** | kontras ukuran/jumlah | "Kenapa [A] yang segede ini nggak punya [X]? Padahal [B] yang sekecil itu pernah punya." / "Semua [X] yang tersisa di dunia sekarang tinggal di satu [tempat kecil] ini." |
| 5-12 | Angka + status quo | fakta keras | "Jumlahnya nggak sampai [angka]." / "[C] punya, [D] dulu punya. [A]? Satu ekor pun nggak ada." |
| 12-20 | **Anggapan umum + "tapi"** | open loop | "Banyak yang bilang [anggapan]. Tapi ceritanya jauh lebih aneh." / "Katanya [alasan]. Tapi kalau memang [alasan], kenapa justru [paradoks]?" |
| 20-35 | **"Kita mundur dulu"** | rewind waktu | "Oke, kita mundur dulu." / "Kita mundur [N] ribu tahun." |
| 35-60 | Mekanisme 1 | sebab-akibat + istilah | angka konkret + **analogi sehari-hari** ("setinggi gedung 40 lantai", "tanpa paspor") + istilah ilmiah 1 kata + artinya ("Ahli nyebutnya refugium. Tempat pelarian terakhir.") |
| 60-70 | **Twist 2** | pertanyaan baru | "Jadi kenapa nggak ada? Ternyata ada." / "Terus, tsunaminya gimana?" |
| 70-95 | Mekanisme 2 | bukti + analogi | "Ibaratnya, pulaunya raksasa, tapi kulkasnya hampir kosong." |
| 95-115 | **Belokan emosi** | manusia sebagai sebab | "Tapi bagian paling sedih / paling bahaya justru..." + angka korban + pembanding ("lebih sedikit dari murid satu sekolah", "sepersepuluh dari semuanya") |
| 115-125 | **Punchline paralel** | moral | "[A] kehilangan [X] karena alam. [B] kehilangan [X] karena kita." / "Yang bikin [X] terpojok bukan [anggapan]. Itu manusia." |
| 125-135 | **CTA polling** | komentar | "Ngaku deh, kalau kamu yang memutuskan: [opsi 1], [opsi 2], atau [opsi 3]? Tulis di komentar." / "Ngaku deh, dari dulu kamu kira [anggapan] juga? Tulis di komentar." |

Aturan menulis:
- Kalimat pendek 4-12 kata, bahasa ngobrol ("nggak", "gede", "nyambung", "nemu"), sapaan "kamu", subjek "kita" untuk manusia.
- Setiap 10-15 dtk harus ada **pertanyaan kecil** atau kata belok ("Tapi", "Justru", "Ternyata", "Nah", "Terus").
- Minimal 3 angka konkret dan 3 analogi sehari-hari per video.
- Satu istilah ilmiah/unik yang jadi "kata oleh-oleh" (refugium, Sundaland, zaman es).
- Akhiri dengan nilai/aksi yang aman (konservasi, hukum), tanpa menggurui panjang.
- Panjang 260-320 kata (±120-140 dtk). Bila user minta versi pendek: 150-180 kata, buang Mekanisme 2.
- **Cek fakta setiap angka** (WebSearch lalu baca sumbernya; utamakan Wikipedia, IUCN, KLHK/BKSDA, jurnal, media besar). Catat sumber untuk deskripsi. Contoh jebakan di referensi: VO bilang laut turun "120 meter" tapi caption "108 METER" (tidak konsisten): angka di caption dan VO wajib sama.

Topik yang cocok: misteri sebaran hewan/tumbuhan, "kenapa X hanya ada di Y", pulau/selat/gunung yang membentuk sejarah, bencana + dampak, zaman es/Sundaland, batas alam (Garis Wallace), spesies terakhir, kota/pulau yang hilang. Satu kawasan peta per video (kamera tidak terbang lintas benua, sama seperti aturan `map-route-shorts`).

---

## 3. Alur kerja

### Mode A: naskah
1. User memberi topik atau naskah referensi. Bila referensi: pertahankan alur, **tulis ulang semua kalimat**.
2. Riset + cek fakta, tulis naskah sesuai formula di atas.
3. Kirim ke user: teks polos siap rekam (code block), daftar fakta + sumber, dan **rencana visual singkat** per kalimat (peta/kartun + caption + warna kata kunci) supaya user bisa mengoreksi sebelum VO.
4. User merekam VO sendiri (TTS/generator suara milik user) lalu mengirim file.

### Mode B: VO jadi video
1. `vo.wav`: `ffmpeg -i in -ac 1 -ar 48000 -c:a pcm_s16le vo.wav`.
2. Transkrip + timestamp per kata (faster-whisper). Bila HuggingFace diblokir: model whisper-small CTranslate2 tersedia lewat npm `@skillninja/shortmovie-telop-model-p0..p3` (`npm pack`, gabung `model.bin.part0..3`, cek sha256 dengan `model.sha256`). Baca audio sebagai WAV 16 kHz + numpy (versi PyAV di container bisa error bila diberi path mp4).
3. Tulis `storyboard.json` (lihat format di bawah): satu entri per frasa caption, berisi waktu dari kata pertama, adegan, kamera, dan elemen grafis.
4. Render still di detik-detik kunci → contact sheet → periksa → perbaiki.
5. Render penuh, mix (VO 0 dB, musik -22 s.d. -26 dB dengan ducking, SFX -18 s.d. -24 dB), normalisasi -14 LUFS.
6. Verifikasi: contact sheet 12-16 frame, `ffprobe` 1080x1920 30 fps, caption tidak terpotong, angka caption = angka VO, CTA utuh di akhir.
7. Kirim MP4 (SendUserFile, `render`) + paket upload (judul, deskripsi + sumber, hashtag).

### Format `storyboard.json`
```json
{
  "brand": {"accent": "#FFD23F", "danger": "#FF5A4E", "good": "#5BD66B", "water": "#7FD3FF",
            "font": "Montserrat-ExtraBold", "watermark": null},
  "beats": [
    {"t": 0.0, "cap": ["KALIMANTAN SEGEDE INI"], "scene": "map",
     "cam": {"lon": 114.0, "lat": 0.5, "span": 14}, "fx": [{"fill": "borneo", "col": "accent"}, {"label": "KALIMANTAN", "lon": 114, "lat": 1.5}]},
    {"t": 3.2, "cap": ["PADAHAL BALI", "SEKECIL INI|accent"], "scene": "map",
     "cam": {"lon": 115.1, "lat": -8.4, "span": 2.2}, "fx": [{"label": "BALI", "lon": 115.1, "lat": -8.2}]},
    {"t": 19.6, "cap": ["MUNDUR KE", "20.000 TAHUN LALU|accent"], "scene": "map",
     "cam": {"lon": 108, "lat": 0, "span": 22}, "fx": [{"rewind_clock": true}]},
    {"t": 79.5, "cap": ["PULAUNYA RAKSASA...", "KULKASNYA KOSONG|accent"], "scene": "cartoon:fridge"}
  ]
}
```
Caption: `"TEKS|warna"`; baris tanpa warna = putih; `"TEKS|danger|big"` = punch besar.

---

## 4. Engine (yang perlu dibangun / ditambahkan)

Bila `maproute-engine.zip` ada, pakai ulang: kamera `V(lon,lat,span)` + easing, `admin1()`/poligon Natural Earth untuk fill & outline, `align`, mixer + `auto_sfx`, `movers` (rute + ikon bergerak). Tambahkan modul:

1. **`map/satbase.py`**: basemap citra satelit equirectangular, dipotong + diskalakan per frame sesuai kamera, color grade (saturasi -10%, kontras +5%, vignette 25%), dan vektor fill/label digambar di atasnya.
   - Sumber citra: NASA Blue Marble Next Generation (domain publik). Untuk zoom pulau (span 2-4°) butuh resolusi tinggi (tile 21600x10800 per dunia atau 86400 per tile 500 m/px → ±125 m/px). Dari container ini `*.nasa.gov`, EOX, dan ArcGIS **diblokir**; `raw.githubusercontent.com` dan npm bisa, tapi tekstur di sana umumnya hanya 4K (terlalu buram untuk zoom pulau). Jadi: **minta user melampirkan** potongan Blue Marble/Sentinel-2 cloudless kawasan Indonesia (mis. bbox 90-145 BT, 12 LU-14 LS) sekali, simpan di `vendor/sat/`, pakai untuk semua video.
   - Efek muka laut turun/naik: pakai data batimetri (mis. GEBCO yang dilampirkan user, atau kontur -120 m Natural Earth `ne_10m_bathymetry_*`) sebagai masker, warnai area dangkal jadi daratan hijau-kecokelatan.
2. **`scenes/`**: adegan kartun flat digambar prosedural (PIL/cairo/SVG → PNG per frame): `sky`, `night_forest`, `savanna`, `cave`, `rainforest_rain`, `grid_count`, `fridge`, `truck`, `house`, `school`. Setiap adegan menerima maskot + teks.
3. **`chars/`**: maskot dan karakter **milik sendiri** sebagai SVG berlapis (badan, kepala, mata, mulut) supaya bisa kedip, menoleh, memantul. Buat set ekspresi: normal, kaget, sedih, senang.
4. **`captions_top.py`**: caption 1-2 baris atas, pop per kata, warna kata kunci, mode `big`, bayangan lembut.
5. **`fx.py`**: riak konsentris, lingkaran sorot, pin bernomor + panah, jejak kaki, tanda tanya putus-putus, X merah, gauge air, jam mundur + garis VHS, grid ikon, transisi geser/wipe antar adegan (tanpa hard-cut).
6. **`outro_poll.py`**: kartu opsi 1-3 bergambar + centang + balon "Aku: •••".

Render target ±2-4 fps di container; video 135 dtk ±20-35 menit. Render per beat ke `seg/NNN.mp4` agar bisa dilanjutkan setelah container restart.

---

## 5. Pembeda dari referensi (WAJIB, supaya tidak sama persis)

Struktur dan tata bahasa visual boleh mirip (itu genre). Yang **harus** milik sendiri:
- **Nama channel & watermark**: pakai merek user (bukan nama channel referensi). Posisi watermark beda (mis. pojok kiri bawah di atas safe-area, bukan atas tengah).
- **Maskot & karakter**: desain sendiri (proporsi, warna, ekspresi, aksesori khas). Jangan meniru penjelajah bertopi safari / profesor rambut putih referensi; buat tokoh pemandu sendiri.
- **Palet aksen**: tetapkan 4 warna merek sendiri (kuning/merah/hijau/biru bisa diganti nada lain, mis. kuning-lemon → oranye-mangga, biru muda → toska).
- **Font**: pilih font lain dari referensi (mis. Fredoka/Baloo/Lilita One untuk punch, Inter ExtraBold untuk baris 1).
- **Caption**: boleh tetap di atas, tapi beri ciri: mis. label kecil "BAB 1/2/3", garis bawah stabilo pada kata kunci, atau kotak tipis.
- **Penutup**: frasa CTA sendiri (mis. "Jujur deh..." / "Tim mana kamu?"), desain kartu opsi sendiri.
- **Naskah & topik**: tidak memakai topik/kalimat referensi (badak jawa Ujung Kulon, harimau Kalimantan) kecuali sudut pandang dan kalimat ditulis ulang total serta fakta dicek ulang.
- **Musik/SFX**: musik bebas royalti / sintetis sendiri; jangan pakai audio dari video referensi.

Daftar perubahan yang dipilih user disimpan di `brand` storyboard dan di catatan "Keputusan user" di bawah agar konsisten antar-video.

### Keputusan user
- (kosong: isi saat user menentukan nama merek, maskot, palet, font, posisi watermark, frasa CTA)

---

## 6. Paket upload
- **YouTube Shorts** judul ≤70 karakter, pola pertanyaan paradoks ("Kenapa Kalimantan yang Segede Ini Nggak Punya Harimau?") + `#shorts`; deskripsi 2-3 kalimat fakta, pertanyaan + "Tulis di komentar 👇", baris `Sumber: ...`, 5-7 hashtag.
- **Instagram/Facebook Reels**: 1-2 kalimat + pertanyaan + hashtag + `#reels`.
- Catatan durasi: Shorts maks 3 menit; ±135 dtk aman. TikTok dan Reels juga mendukung.

## 7. Keamanan konten
Jangan memakai nama/logo/watermark/karakter kreator lain, jangan menyalin teks kartu persis, jangan memasukkan audio referensi. Topik satwa dilindungi: sebut sanksi hukum secara umum dan akurat (UU No. 32/2024 tentang Konservasi SDA Hayati dan Ekosistemnya), tanpa menyebut cara berburu/menjual. Bencana: angka korban dari sumber resmi, tanpa sensasi.
