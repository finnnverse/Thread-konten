---
name: kampung-3d-short
description: Buat video Shorts/TikTok/Reels vertikal (maks 60 detik) gaya "cerita haru warga kampung" dengan karakter 3D tetap seri Warga Kampung (Mbah Sarni, Pak Sobri, Bu Lastri, Bayu, Laras, Mas Gilang, Kakek Wiryo, kucing Si Belang) di set kampung Indonesia 3D, caption satu kata, crossfade, musik lembut, memakai VO milik user. Render three.js di dalam Remotion, bisa jalan di server tanpa GPU. Pakai saat user minta video "warga kampung", "kayak referensi kampung", "cerita haru kampung", atau menyebut salah satu tokoh di atas.
---

# Warga Kampung 3D short (three.js + Remotion)

Format: video vertikal 1080x1920 (render preview 540x960), 30 fps, **maksimal 60 detik**. Cerita human interest yang hangat atau haru di sebuah kampung Indonesia, diceritakan oleh satu narator (VO user), dan ditutup dengan twist atau pesan.

## Aturan tetap
- **Tokoh selalu dari roster** (`templates/remotion/roster.ts`): jangan mengubah warna, baju, atau proporsi tokoh lama. Tokoh baru = entri baru di `ROSTER` (tunjukkan character sheet ke user dulu lewat composition `CastSheet`).
  - Mbah Sarni (nenek penjual jamu), Pak Sobri (ketua RT), Bu Lastri (pemilik warung), Bayu (anak SD), Laras (remaja SMA), Mas Gilang (montir), Kakek Wiryo (veteran), Si Belang (kucing, muncul di setiap video).
  - Lihat `references/karakter/*.jpg` untuk tampilannya.
- **Gaya visual "soft-blocky"**: kepala kotak membulat, wajah dilukis (decal) yang ganti ekspresi, outline cokelat tipis, cahaya siang hangat, bayangan lembut, warna kalem.
- Video gaya ini diinspirasi dari referensi user (cerita kampung 3D dengan caption satu kata). Ambil **gayanya** saja: jangan salin cerita, nama warung, atau tokoh video lain.
- Caption: satu kata per kemunculan, huruf kecil, Nunito 900 putih dengan stroke cokelat gelap, posisi 63% dari atas, pop kecil saat muncul. Tanda baca dibuang.
- Bahasa VO dan caption: Indonesia (kecuali user minta Inggris).

## Alur kerja
1. **Ide**: tawarkan 5 ide cerita (judul hook + inti cerita + twist + tokoh yang dipakai). Cerita yang bagus untuk format ini: satu kampung kompak menolong seseorang diam-diam, salah paham yang ternyata baik, kebiasaan kecil yang ternyata punya alasan menyentuh, anak kecil dan orang tua, kejujuran kecil.
2. **Script**: maksimal ~145 kata (VO 55–60 detik). Struktur:
   - Hook (0–3 dtk): kalimat penasaran ("Setiap pagi, warung ini selalu ...").
   - Setup (3–15 dtk): siapa, di mana, kebiasaan apa.
   - Konflik/misteri (15–40 dtk).
   - Twist/pengungkapan (40–52 dtk).
   - Penutup hangat (52–60 dtk), satu kalimat yang bisa di-quote.
   Tulis juga daftar shot kasar per kalimat. Simpan di `shorts/<slug>/SCRIPT.md`.
3. **VO dari user**: user merekam/generate VO sendiri lalu upload. Resample ke 48 kHz mono, tulis transcript (angka ditulis sebagai kata), jalankan `templates/tools/align.py` untuk `words.json` (s/e per kata). Cek jeda di audio cocok dengan titik/koma.
4. **Story file** (`src/videos/kampung/<slug>.ts`, contoh `templates/remotion/demo.ts`):
   - `shots`: potong tiap 2–4 detik, ikuti kalimat VO. Crossfade default 0.33 dtk (`fade`).
   - `tracks`: per tokoh `path` (jalan otomatis + menghadap arah jalan), `face`, `lookAt`, `expr`, `pose`, `talk` (interval mulut bergerak), `hidden`.
   - `words`: dari `words.json`.
   - `extra`: properti khusus cerita (mis. surat, kaleng uang, buku utang) dibuat dengan helper `part/rbox/clay` dari `cast3d.ts`.
5. **Cek still** dulu (`stills.mjs`, scale 0.5) untuk tiap shot: framing, tokoh tidak tertutup properti, caption terbaca.
6. **Render** dalam potongan ≤ 900 frame (batas 2 jam per perintah background):
   `npx remotion render src/index.ts <Comp> out/x/partA.mp4 --frames=0-899 --scale=0.5 --concurrency=4 --gl=swangle --browser-executable=/opt/pw-browsers/chromium --timeout=600000 --codec h264 --crf 18`
   lalu concat (`ffmpeg -f concat -c copy`).
7. **Audio**: musik lembut (pluck gitar/kalimba + pad + musicbox dari `templates/audio/instruments.py`, 80–95 bpm, kunci mayor; berganti minor lembut di bagian haru, kembali mayor di twist). Duck musik -9 dB di bawah VO. SFX kecil: ayam, langkah, pintu, kaleng/koin, angin. Normalisasi mix ke **-11 LUFS**, peak -1 dB (referensi sangat keras, -8.5 LUFS; -11 aman untuk platform). Contoh mixer: `templates/audio/example_mix_banjir_bir.py`.
8. Mux: `ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart final.mp4`. QA: cek beberapa frame, durasi ≤ 60 dtk, kirim ke user, commit ke `shorts/<slug>/`.

## Kamera (layar vertikal!)
Lebar yang terlihat hanya ~0.56 x tinggi. Jadi kamera harus lebih jauh dari perkiraan:
- Close-up wajah: jarak ~2.8–3.2 m, fov 36–40, mata kamera ~0.2 m di atas mata tokoh.
- Medium (setengah badan sampai full): jarak 4–5.5 m, fov 38–40.
- Wide gang: jarak 8–11 m, tinggi 2–3 m, fov 40.
- Over-the-shoulder: tokoh depan harus di **tepi** frame (~10° dari sumbu ke tokoh yang dilihat), bukan di tengah.
- Insert properti (buku, uang, surat): jarak 0.8–1.2 m, fov 30–34.
- Setiap shot punya 2 key kamera (dorong pelan 5–10%); `shake` hanya untuk momen kaget.
- Jangan letakkan kamera di dalam/terhalang properti (toples di meja warung sering menghalangi, cek still).

## Peta set (meter, `set.ts`)
- Gang Mawar membentang di sumbu z (x -2.2..2.2, z -40..12). Gerbang "GANG MAWAR RT 03/RW 05" di z=10.
- Warung Bu Lastri: sisi kiri (x<0) di z≈1.5. Konter biru menghadap gang di x≈-2.0; Bu Lastri berdiri di belakang konter (`spots.warung_dalam` = [-2.55, 1.5], yaw +π/2). Pembeli di x≈-0.7..-1.2.
- Teras Mbah Sarni (amben bambu + botol jamu): sisi kanan di z≈0.3, tokoh berdiri di [3.3, 0.8].
- Ruang tamu (sofa, meja teh, kalender, foto): `ROOM_X`=60, dinding belakang z=-3; kamera dari +z.
- Ayam (3 ekor, mematuk), pohon pisang, pohon mangga, tiang listrik + kabel, awan bergerak.
- Yaw 0 = menghadap +z (ke arah gerbang). Kamera menghadap -z melihat ke dalam gang.

## Render & performa (server tanpa GPU)
- Chromium SwiftShader: `--gl=swangle`. Default: tanpa MSAA (`aa:false`), shadow PCF 2048. Kurang lebih 3 dtk per frame pada 540x960, jadi 60 detik video ≈ 90–100 menit.
- Mesh statis set otomatis digabung (`freezeStatic`). Objek yang bergerak harus diberi `userData.dynamic = true`.
- inputProps untuk eksperimen: `{"aa":true}` (lebih halus, 1.6x lebih lambat), `{"shadow":"basic","smap":1024}` (cepat, bayangan bergerigi), `{"dpr":...}`.

## File
- `templates/remotion/`: `cast3d.ts` (karakter + kucing), `roster.ts` (pemeran tetap), `set.ts` (kampung), `engine.ts` (track/kamera/caption), `Kampung.tsx` (renderer `makeShort(story)`), `CastSheet.tsx` (character sheet), `demo.ts` (contoh cerita 8 detik).
- Butuh paket: remotion 4.0.300, @remotion/three, three 0.169, @react-three/fiber 8.17, react 18.3.1, `@fontsource/nunito@5.0.18`.
- Daftarkan di `src/Root.tsx`: `const X = makeShort(STORY); <Composition id="X" component={X} durationInFrames={STORY.total} fps={30} width={1080} height={1920} />`.
