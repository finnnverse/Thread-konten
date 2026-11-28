# TAHAP 1 — Data teknis video referensi

| Item | Nilai | Cara ukur |
|---|---|---|
| Resolusi | 720×1280 (9:16) | ffprobe |
| FPS | 60/1 konstan (3914 frame) | ffprobe r_frame_rate/avg_frame_rate |
| Durasi | 65,29 dtk | ffprobe format.duration |
| Codec video | H.264, ±2,71 Mbps | ffprobe |
| Audio | AAC, 44.100 Hz, stereo, 128 kbps | ffprobe |
| Loudness | **-14,1 LUFS** integrated, true peak -3,0 dBTP, LRA 2,5 LU | ffmpeg loudnorm (print summary) |
| Hening | tidak ada bagian < -35 dB ≥0,25 dtk → ada musik dasar terus-menerus di bawah VO | ffmpeg silencedetect |
| Scene cut keras | **0** (skor scene ffmpeg tidak pernah > 0,08) | `select=gt(scene,0.08)` |
| Transisi | Semua kontinu: (a) whip-zoom kamera 4%/frame, (b) blur depth-of-field ke objek 3D (7,4–7,9 dtk masuk; 13,7–14,1 dtk keluar) | ORB + estimateAffinePartial2D per frame (lihat Tahap 4) |

Frame: 130 frame @2 fps (contact sheet) + 24 frame resolusi penuh di momen penting.

# TAHAP 2 — Naskah & struktur

**Transkripsi:** Whisper via HuggingFace/OpenAI diblok proxy. Pengganti: model ONNX dari rilis GitHub sherpa-onnx — Whisper small.en (teks) + **NVIDIA Parakeet TDT 0.6B int8** (teks + timestamp per kata). Dicek silang dengan caption di layar (60 fps) → cocok; satu koreksi: "Sarma" = "SARMAT".
Tabel 206 kata lengkap + potongan caption: `02_waktu_kata.md`.

(Naskah asli referensi sengaja TIDAK disertakan di skill: yang ditiru hanya pola strukturnya, bukan kata-katanya.)

Statistik: 206 kata / 65,3 dtk = **3,16 kata/dtk (190 wpm)**, cepat & rata. Jeda antar kalimat 0,3–0,8 dtk.

## Struktur & pola kalimat (template netral topik)
| Bagian | Detik | Fungsi | Pola kalimat |
|---|---|---|---|
| HOOK | 0–3,4 | Pertanyaan "bagaimana jika" + angka kecil + aksi besar | "Apa yang terjadi kalau [JUMLAH KECIL] [PELAKU] melakukan [AKSI BESAR] ke [TARGET]?" |
| ISI 1 — skala | 3,5–15,2 | Fakta bertingkat, angka dikalikan | "Well, [PELAKU] yang ada di dekat [TARGET] adalah [NAMA SPESIFIK], dan tiap [X] membawa sampai [ANGKA] [Y]. Dan tiap [Y] bisa [ANGKA] [Z], masing-masing cukup untuk [DAMPAK VISUAL]." |
| PAYOFF matematis | 15,2–21,4 | Hasil kali → angka mengejutkan + waktu singkat | "Artinya, [JUMLAH KECIL] [X] bisa [HASIL TOTAL] dalam [WAKTU], sebelum [TARGET] sempat [REAKSI]." |
| KONFLIK/TWIST | 21,5–30,4 | "Tapi…" — pihak lain bereaksi | "Tapi [TARGET] tidak akan menunggu. Begitu [SENSOR] mendeteksi [PEMICU], mereka akan anggap [INTERPRETASI] dan [BALASAN] seketika." |
| ESKALASI | 30,4–34,9 | Bahkan skenario terbaik gagal | "Bahkan kalau [PELAKU] berhasil [SKENARIO TERBAIK], itu tidak akan menghentikan [AKIBAT]." |
| MOMEN UNIK | 35–43,9 | Fakta "seram/aneh" bernama | "[TARGET] punya [NAMA SISTEM UNIK], [DEFINISI 3 KATA]. Kalau [KONDISI], ia [AKSI] otomatis. Tanpa [X]. Dan di situlah semuanya jadi [EMOSI]." |
| ISI 2 — senjata balik | 44–58,4 | Perkenalan objek + julukan + superlatif + angka | "[TARGET] punya sesuatu bernama [NAMA], dijuluki [JULUKAN], salah satu [SUPERLATIF]. Ia bisa [ANGKA], masing-masing [SIFAT]. Begitu [SIFAT] sampai tidak ada [PENANGKAL] yang bisa menghentikannya." |
| FINALE | 58,4–65,3 | Daftar target cepat + batas waktu | "[TARGET] bisa [AKSI] [JUMLAH], mengenai [A], [B], [C], dan [D] dalam waktu kurang dari [WAKTU]." |
| CTA | — | **Tidak ada CTA** — video berakhir tepat di angka penutup (loop-friendly) | — |
