# Panduan membangun channel WhatIf Atlas (YouTube + Facebook)

## File di paket ini
| File | Untuk |
|---|---|
| `profil_800x800.png` | Foto profil YouTube **dan** Facebook (tampil sebagai lingkaran) |
| `youtube_banner_2560x1440.jpg` | Banner YouTube (judul sudah di zona aman 1235×338, aman di HP/PC/TV) |
| `facebook_cover_1702x630.jpg` | Foto sampul Halaman Facebook (rasio 851×315, kualitas 2×; pojok kiri bawah dibiarkan kosong karena tertutup foto profil) |
| `cek_zona_aman_banner.jpg` | Bukti zona aman (kotak merah = paling ketat, kuning = 1546×423) |
| `profil_preview_98px.png` | Contoh tampilan foto profil di ukuran kecil |

---

## A. YouTube (±20 menit)

### 1. Buat channel
1. Login Google di **youtube.com** (pakai PC lebih mudah).
2. Foto profil (kanan atas) → **Buat channel** (*Create a channel*).
3. **Disarankan:** buat sebagai **Brand Account** lewat *Settings → Add or manage your channel(s) → Create a channel*. Dengan begitu kamu bisa menambah pengelola nanti tanpa membagikan password Gmail.
4. Nama channel: **WhatIf Atlas**.
5. **Handle:** coba `@whatifatlas`. Kalau sudah dipakai: `@whatifatlasmaps`, `@thewhatifatlas`, atau `@whatif.atlas`.

### 2. Verifikasi nomor HP (wajib)
**youtube.com/verify** → masukkan nomor HP → kode SMS.
Ini membuka fitur thumbnail kustom, video lebih dari 15 menit, dan live.

### 3. Pasang tampilan
**YouTube Studio → Customization (Penyesuaian) → Branding**:
- **Picture:** upload `profil_800x800.png`
- **Banner image:** upload `youtube_banner_2560x1440.jpg`. Jangan geser crop-nya.
- **Video watermark:** lewati. Watermark "WhatIf Atlas" sudah ada di dalam video.

### 4. Isi Basic info (salin-tempel)
**Description:**
```
What if the world's most important places worked differently?

WhatIf Atlas turns big geography and geopolitics questions into fast, map-based Shorts: trade routes, chokepoints, borders, history and natural disasters, explained in under a minute with real satellite maps.

Every video is fact-checked, with sources listed in the description.

New videos every week.

Map data: Natural Earth. Satellite imagery: Sentinel-2 cloudless (EOX, CC BY 4.0).
```
- **Links:** kosongkan dulu, atau isi link Halaman Facebook setelah dibuat (lihat B).
- **Contact info:** email khusus channel (buat Gmail baru, jangan pakai email pribadi).

### 5. Setelan penting
**Studio → Settings**:
- **Channel → Basic info:** Country = negara tempat kamu tinggal (memengaruhi monetisasi). Keywords: `geography, maps, geopolitics, what if, history, explained, shorts`.
- **Channel → Advanced settings:** *Audience* → **"No, set this channel as not made for kids"**.
- **Upload defaults:**
  - Category = **Education**
  - Language = **English**
  - Visibility default = **Private** (supaya bisa dicek dulu sebelum tayang)

### 6. Upload Short pertama (video Hormuz)
1. Studio → **Create → Upload videos** → pilih `WhatIfAtlas_Hormuz_final.mp4`. File vertikal di bawah 3 menit otomatis jadi **Short**.
2. **Title:** `Why the World Can't Go Around Hormuz`
3. **Description + hashtag:** salin dari `paket_upload.md`. Sumber dan atribusi wajib ikut.
4. **Audience:** Not made for kids.
5. **Show more:**
   - *Altered content*: pilih **No**. Ini video peta grafis, bukan rekaman realistis orang atau peristiwa. Suara AI sudah disebut di deskripsi.
   - Category: Education.
6. **Visibility → Schedule:** **00:30 WIB** (siang di AS). Sebelumnya, cek ulang kalimat "As of November 2026".
7. Setelah tayang, tulis **komentar pertama** berisi pertanyaan, lalu pin. Contoh: `Which chokepoint should we map next: Suez, Panama or Malacca?`

---

## B. Facebook Page (±15 menit)

### 1. Buat Halaman (bukan akun pribadi baru)
1. Login Facebook pribadimu → menu **Pages** → **Create new Page**.
2. **Page name:** `WhatIf Atlas`
3. **Category:** ketik `Education` → pilih **Education Website**. Tambahkan **Media/News Company** kalau tersedia.
4. **Bio** (Facebook membatasi ±100 karakter):
```
Fast, fact-checked map videos on geography, trade routes and history. What if? 🌍
```

### 2. Pasang gambar
- **Profile picture:** `profil_800x800.png`
- **Cover photo:** `facebook_cover_1702x630.jpg`. Kalau Facebook menampilkan pratinjau crop, jangan digeser.

### 3. Lengkapi
- **Username:** `@whatifatlas`, sama dengan YouTube.
- **Contact:** email channel yang sama.
- **Website:** link channel YouTube kamu.
- **Action button:** pilih **Watch video** atau **Follow**.

### 4. Upload Reel pertama
Pakai **Meta Business Suite** (business.facebook.com) supaya bisa dijadwalkan:
1. **Create Reel** → upload `WhatIfAtlas_Hormuz_final.mp4`. Upload file aslinya, jangan hasil unduhan dari YouTube.
2. **Caption:** judul + 2–3 kalimat + sumber singkat + hashtag dari `paket_upload.md`.
3. **Jadwal:** sama dengan YouTube atau 1 jam setelahnya.

---

## C. Kebiasaan supaya cepat tumbuh
- **Ritme:** 3 video/minggu, misalnya Senin, Rabu, Sabtu jam 00:30 WIB. Konsisten lebih penting daripada sering.
- **Satu topik, dua platform:** upload file asli ke masing-masing platform (native), jangan bagikan link silang.
- **Balas komentar** dalam 1 jam pertama setelah tayang.
- **Ide berikutnya** (sudah sesuai gaya): Suez Canal shutdown, Panama Canal drying up, Yellowstone eruption, "What if the US never bought Alaska", Strait of Malacca.
- **Cek setelah ±10 video:** YouTube Studio → Analytics → **Audience → "When your viewers are on YouTube"**, lalu sesuaikan jam tayang.

## D. Monetisasi (syarat per November 2026, bisa berubah)
- **YouTube:**
  - Tahap awal (fan funding & shopping): 500 subscriber, 3 upload dalam 90 hari, dan 3 juta tayangan Shorts dalam 90 hari.
  - Iklan penuh: **1.000 subscriber + 10 juta tayangan Shorts dalam 90 hari** (atau 4.000 jam tonton).
  - Mulai **1 Februari 2027** naik jadi **20 juta tayangan Shorts / 8.000 jam tonton** untuk kreator baru.
  - Hanya tayangan Shorts publik di feed yang dihitung.
- **Facebook:**
  - Program **Content Monetization** sifatnya **undangan**. Kamu bisa mendaftar minat lewat Professional Dashboard → Monetization.
  - Ambang pengikut yang beredar (500–1.000) adalah klaim pihak ketiga, bukan aturan resmi Meta. Cek status Halaman di Meta Business Suite → Monetization.
  - Konten wajib **orisinal**: repost dengan caption saja tidak memenuhi syarat.

## E. Jaga keamanan akun
- Aktifkan **2-Step Verification** di Google dan Facebook.
- Jangan pernah memberi kode login ke siapa pun, termasuk "tim YouTube/Meta" yang menghubungi lewat DM atau email.
