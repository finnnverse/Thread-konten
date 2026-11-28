# MULAI DI SINI

Skill ini adalah **perkakas gaya**. Topik, naskah, dan VO selalu dari user.

## 0. Setup (sekali per sesi)
```bash
pip install numpy pillow opencv-python-headless scipy sherpa-onnx
# ffmpeg harus ada. Tile satelit diunduh otomatis ke cache/ dari tiles.maps.eox.at
# Model ASR (Hugging Face sering diblok -> pakai rilis GitHub):
mkdir -p models && curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2 | tar xj -C models/
```
Kalau `tiles.maps.eox.at` diblok, minta user mengizinkan host itu. Jangan mengganti ke layer berlisensi NC.

## 1. Tanya user (bila belum jelas)
Topik? Naskah dari user atau AI (dengan cek fakta)? VO sudah ada? Nama channel/watermark?

## 2. Naskah (Mode A)
Struktur referensi (pola, bukan kalimat aslinya):
1. **Hook** "What if [angka kecil / hal mengejutkan]?"
2. **Skala:** fakta + angka.
3. **Konflik:** "So why not…?"
4. **Twist:** "Because…"
5. **Isi bertahap:** sebut wilayah satu per satu.
6. **Momen unik.**
7. **Twist kedua.**
8. **Penutup** berupa angka/kalimat pendek, **tanpa CTA**.

Panjang 120–170 kata. Tulis tabel cek fakta + sumber. Kirim **teks polos** siap rekam, lalu **tunggu VO**.
Isu yang sedang berlangsung (perang/krisis): beri tanggal ("As of …"), netral, dan minta user cek ulang sebelum upload.

## 3. VO → waktu kata
```bash
ffmpeg -i projects/<slug>/vo.mp3 -ac 1 -ar 16000 /tmp/vo16k.wav
python3 tools/asr_words.py /tmp/vo16k.wav projects/<slug>/words_raw.json
```
**VO bisa beda dari naskah: ikuti VO.** Gabungkan token angka yang terpecah (mis. "twenty twenty six" → "2026").

## 4. Timeline
Salin `projects/template/make_project.py` ke `projects/<slug>/`. Semua waktu memakai `W("kata", n)`.
- `n` = kemunculan ke-n kata itu. **Kata yang sering muncul ("and", "about", "one") wajib diberi n yang benar.** Ini sumber bug paling sering.
- Validasi otomatis di template: elemen dengan `t1 <= t0` akan dicetak sebagai error.

Kosakata `project.json`:
- `camera`: `[{t, lon, lat, width_km, roll, tilt}]`, atau `{"follow": id, t0, t1, width_km}` untuk mengikuti objek bergerak.
- `regions`: `{"id": "RUS", "style": "opaque"|"tint", "t_in", "fade", "exclude_bbox", "min_lat"}`
- `elements` (gaya referensi): `neon`, `trail`, `bursts`, `ring`, `sticker` (submarine, tombstone, bubble, radar, png:file), `card`, `tracked` (+ label atas/bawah, `drop_t`), `rain`. Tipe `hero` ada di engine, tapi **jangan dipakai** (preferensi user).
- `jfx` (journey): `HL`, `Tint`, `NeonArc`, `NeonLine`, `BigLabel`, `LeaderLabel` (h > 0, geser pakai `dx`), `Pin`, `Walker` (kind = "ship"/"walk"/"train", `t1` agar jejak hilang), `Check`, `Cross`, `Chip`, `Snow`, `IceCube`, `FreezeSea`, `IceBridge`, `RouteGlow`, `GridFinale`. Geometri: `{"geom": "IRN"}` atau `{"geom": ["SAU", "ARE"]}`. Sorotan laut: ring poligon + `minus` daratan + `feather`.

## 5. Cek sebelum render penuh
```bash
python3 tests/check_cam.py projects/<slug>/project.json        # harus OK
python3 tests/stills.py projects/<slug>/project.json /tmp/s.jpg 1.5,5,9,...
```
Periksa: caption terbaca, label tidak terpotong/bertumpuk, elemen muncul di katanya, tidak ada artefak citra (gurun/es/awan).

## 6. Render + audio
```bash
python3 -m engine.render projects/<slug>/project.json projects/<slug>/video.mp4 --workers 4
python3 - <<'EOF'
import sys, json; sys.path.insert(0, '.')
from engine import audio as A; from engine.camera import Camera; from engine.render import expand_camera
P = 'projects/<slug>/'; spec = json.load(open(P + 'project.json'))
ev = A.events_from_project(spec, Camera(expand_camera(spec['camera'], {})))   # cek variasi: print(ev)
A.build_mix(spec['duration'], ev, P + 'vo.mp3', P + 'mix.wav', music_db=-18)
A.mux(P + 'video.mp4', P + 'mix.wav', P + 'final.mp4'); print(A.measure(P + 'final.mp4'))
EOF
```

## 7. Cek akhir (wajib)
- Contact sheet 1 fps: `ffmpeg -i final.mp4 -vf fps=1,scale=216:384 qc/f%02d.jpg` lalu periksa semuanya.
- ffprobe 1080x1920 60 fps; loudness -14 ±0,5 LUFS; durasi = VO + ±0,5 dtk.
- Kirim: video, paket upload (judul, deskripsi + sumber + atribusi, hashtag, jam tayang), dan daftar keterbatasan.
