# TAHAP 3 — Breakdown detik per detik

Sumber angka kamera: ORB feature matching + `estimateAffinePartial2D` per frame (60 fps) → zoom/rotasi/geser per detik (px dalam skala 720p). Lon/lat & lebar pandang = **perkiraan visual** dengan mencocokkan garis pantai di frame (±5°), bukan hasil ukur eksak.
Bukti: `contact_00-20s.jpg … contact_60-65s.jpg` (tiap 0,5 dtk, ada timestamp), `elemen_visual.jpg`.

| Detik | Kata | Kamera (pusat lon/lat · lebar pandang) | Elemen muncul/hilang | Animasi | Warna | Efek khusus |
|---|---|---|---|---|---|---|
| 0,00–0,33 | (kata VO dihapus) | 158°E 45°N · ±1.500 km, roll −0,3°/frame | 2 kapal selam 3D abu-abu + ikon bendera kecil di atasnya | sudah ada di frame 1 (tanpa intro) | laut #013144–#0d495b | dimulai di tengah gerakan |
| 0,33–1,07 | (kata VO dihapus) | **whip zoom-out** ×0,95/frame (≈ ×0,17/dtk) + geser → 105°E 50°N · ±9.000 km | cincin target kuning berdenyut di posisi kapal selam (0,5–1,0) | ring scale-pulse | kuning #ffd400 | Rusia sudah terisi biru opak |
| 1,07–2,53 | (kata VO dihapus) | drift zoom-out ×0,91/dtk, geser +60 px/dtk | 5–6 rudal + jejak putih melengkung dari Pasifik ke barat | jejak "tumbuh" mengikuti kepala rudal, ±1,2 dtk per lintasan | putih glow | rudal = sprite hitam-putih kecil di ujung jejak |
| 2,53–3,43 | (kata VO dihapus) | zoom-out ×0,67/dtk, rotasi −10°/dtk | ledakan oranye pop di ujung lintasan | pop scale 0→1 ±0,15 dtk | oranye #f08a3a | tepi peta (latar #191919) terlihat di pojok atas → peta = bidang 3D miring |
| 3,43–4,50 | (kata VO dihapus) | **whip zoom-in** ×1,04/frame (4,23–4,50) kembali ke 160°E 52°N · ±2.500 km | ledakan memudar | fade 0,3 dtk | | |
| 4,50–5,37 | (kata VO dihapus) | hampir diam, zoom ×1,34/dtk pelan | 2 kapal selam 3D di Laut Okhotsk/Pasifik | — | | |
| 5,37–7,40 | (kata VO dihapus) | diam, rotasi pelan | **Label neon 3D cyan** "'OHIO CLASS SUBMARINES'" miring perspektif, dengan tanda kutip | masuk per huruf (5,9–6,3), keluar huruf berjarak lebar lalu buyar (7,0–7,4) | cyan #31e3ff glow | letter-spacing melebar saat keluar |
| 7,40–7,95 | (kata VO dihapus) | latar **blur DOF** + gelap (7,4–7,9) | "x" kecil putih di tengah | fade-in | | blur ±20 px |
| 7,95–10,50 | (kata VO dihapus) | latar blur diam | **Objek hero**: rudal vertikal hitam-putih + simbol radiasi + api kuning; "x 24" putih italic glow; teks vertikal neon "TRIDENT-II" | rudal naik dari bawah (7,95–8,3), "x 24" pop, label vertikal ketik huruf (8,4–8,9) | api #ffe600, cyan #29d8ff | glow putih pada "x 24" |
| 10,50–11,87 | (kata VO dihapus) | blur | rudal mengecil & berubah jadi **warhead bus** (MIRV) | scale-down + morph (10,3–10,8), bus scale-up 11,0–11,6 | putih/hitam/tembaga | |
| 11,87–13,73 | (kata VO dihapus) | blur | **callout**: garis penunjuk putih tipis + "x 14 warheads" | teks ketik mengikuti kurva (12,0–12,5) lalu lurus | putih | font tipis rounded |
| 13,73–14,43 | (kata VO dihapus) | **rack-focus**: objek blur, peta kembali tajam (13,7–14,1) | objek hilang | blur out ±0,4 dtk | | |
| 14,43–15,87 | (kata VO dihapus) | dekat kapal selam, 158°E 48°N · ±1.200 km | rudal besar meluncur dari kapal selam, jejak cyan-putih tebal | luncur cepat | jejak cyan #5fe8ff | |
| 15,87–17,30 | (kata VO dihapus) | **whip zoom-out** ×0,26/dtk mengikuti rudal → 95°E 45°N · ±12.000 km | 6+ lintasan ke barat | | | |
| 17,30–19,33 | (kata VO dihapus) | 90°E 35°N · ±14.000 km, lalu zoom-in ×1,25/dtk | ledakan pop berurutan (±1 tiap 0,2 dtk, total ±14) | pop | oranye | tepi peta + Antartika terlihat (bidang 3D miring) |
| 19,33–21,47 | (kata VO dihapus) | zoom-in pelan, rotasi −2..−4°/dtk | ledakan bertahan & menumpuk | | | |
| 21,47–22,73 | (kata VO dihapus) | zoom ×2/dtk + geser ke utara | ledakan jadi bayangan biru transparan; **kartu peringatan HUD** | masuk glitch: double-exposure + blur (21,5) → tajam (22,0) → hilang (22,6) | bingkai oranye-merah #ff6a3a, ikon ⚠ merah | glitch/ghosting |
| 22,73–25,63 | (kata VO dihapus) | geser ke utara 54°E… → 95°E 60°N · ±5.000 km | kartu muncul lagi kecil, **berkedip** merah/biru tiap ±0,5 dtk | pop + blink | | |
| 25,63–26,97 | (kata VO dihapus) | zoom-out pelan ×0,79/dtk | **label neon merah** "'WORLD W#R 3.0'" (sensor huruf 'a' → '#') | geser masuk dari kanan + ketik (25,2–25,6), buyar jadi titik (26,4–26,9) | merah #ff2030 glow | sensor kata sensitif |
| 26,97–30,37 | (kata VO dihapus) | **pan cepat ke timur** −366 px/dtk mengikuti rudal → Bering → Amerika Utara | rudal dari Rusia ke timur; **AS terisi merah** (29,5) | fill fade-in ±0,5 dtk | merah #c0402e transparan (multiply) | tepi utara isian AS gradasi lembut |
| 30,37–31,57 | (kata VO dihapus) | **whip-pan balik ke barat** +309 px/dtk + zoom-in ×1,3 | kapal selam Pasifik meluncurkan banyak rudal (jejak putih tebal) | | | |
| 31,57–32,83 | (kata VO dihapus) | pan +224 px/dtk ke Rusia tengah | **stiker potret 2 tokoh** (kartun cut-out) | pop | | (tidak akan ditiru: figur nyata) |
| 32,83–34,97 | (kata VO dihapus) | zoom-in ×1,9/dtk lalu pelan | potret → **3 batu nisan R.I.P.** (tanah + bunga), ledakan di sekitar | swap pop (32,7), ledakan pop berurutan | abu-abu, oranye | |
| 34,97–36,63 | (kata VO dihapus) | zoom-out ×0,7/dtk | **tangan zombie** muncul dari makam tengah; **label neon kuning** "'THE DEAD HAND SYSTEM'" | tangan naik dari bawah (35,0–35,4); label ketik bergelombang, keluar huruf melebar/buyar (36,2–36,6) | kuning #ffd21a glow | |
| 36,63–38,00 | (kata VO dihapus) | zoom-out ×0,8/dtk | nisan mengecil & hilang | scale-down 37,0–37,8 | | |
| 38,00–41,63 | (kata VO dihapus) | **pan ke timur** −390 px/dtk mengikuti rudal → Amerika Utara | rudal dari Rusia, AS merah, ikon pesawat kecil hitam di Kanada | | | |
| 41,63–43,00 | (kata VO dihapus) | **whip-pan balik ke barat** +575 px/dtk | ledakan kecil di AS (41,5–42,2) | pop | | |
| 43,00–45,10 | (kata VO dihapus) | zoom-in ×2,3/dtk ke Chukotka 175°E 65°N · ±2.000 km | **rudal horizontal** + label kuning "RS-28 SARMAT" menempel di atasnya | label pop + glow | kuning #ffe14a | kamera mulai **mengikuti** rudal |
| 45,10–50,70 | (kata VO dihapus) | tracking: rudal tetap di layar, peta geser −174..−220 px/dtk, rotasi +8..+11°/dtk | label merah "SATAN-II" muncul di bawah rudal (47,9) | pop | merah #ff2a2a | jejak asap putih di belakang rudal |
| 50,70–51,33 | (kata VO dihapus) | | label kuning & merah **jatuh** ke bawah dan pudar (50,2–50,7) | drop + fade | | |
| 51,33–53,50 | (kata VO dihapus) | **whip zoom-out** ×0,27/dtk ke Amerika Utara 100°W 45°N · ±6.000 km | **garis-garis kuning** (MIRV) menghujani AS; ledakan bintang oranye pop di ±15 titik (53,0–53,5) | streak bergerak diagonal | kuning #ffc400 | |
| 53,50–54,73 | (kata VO dihapus) | zoom-in pelan ×1,2/dtk | ledakan bertahan | | | |
| 54,73–58,43 | (kata VO dihapus) | hampir diam, zoom ×1,05–1,2/dtk | **stiker radar/peluncur** di AS + **gelembung bicara komik** "Everything is fine here!" | radar pop 55,0; bubble pop + goyang 55,4 | bubble putih, outline hitam | humor ironi |
| 58,43–60,00 | (kata VO dihapus) | **whip-pan ke barat** +758 px/dtk (lonjakan terbesar, 25 px/frame) ke Rusia | rudal diluncurkan dari Rusia (59,3) | | | |
| 60,00–62,70 | (kata VO dihapus) | pan ke timur −508 px/dtk mengikuti rudal → AS | ledakan di AS (62,0–62,4) | | | |
| 62,70–65,29 | (kata VO dihapus) | zoom-in ×1,2–1,4/dtk ke 90°W 45°N · ±3.000 km | satu rudal besar mendekat ke AS bagian timur laut | | | **berakhir di tengah gerakan** (tanpa outro/CTA) → loop |

## Ritme visual (diukur)
- Caption ganti **setiap 0,4–1,3 dtk** (median ±0,7 dtk), 2–4 kata per potongan, ganti **keras (cut, tanpa animasi)** — dicek frame-per-frame: piksel putih berubah dalam 1 frame.
- Kamera **tidak pernah diam** kecuali saat objek hero (8,3–13,7 dtk). Tidak ada cut; semua perpindahan lokasi = whip-zoom atau whip-pan.
- Elemen besar (label neon/objek hero/kartu) muncul **tepat di kata kuncinya** (selisih 0–0,3 dtk sebelum kata).

# Daftar SEMUA jenis elemen visual
1. **Peta satelit** natural-color dengan relief + batimetri laut, dipasang sebagai **bidang 3D** (tepi peta dan latar gelap #191919 kadang terlihat).
2. **Isian negara opak** biru azure (Rusia) — menutup daratan sepenuhnya, tekstur relief samar.
3. **Isian negara transparan** merah (AS) — multiply, relief tetap terlihat, tepi utara gradasi lembut.
4. Pulau/es kutub di wilayah tersorot berwarna **cyan terang** (Novaya Zemlya dll).
5. **Kapal selam 3D** abu-abu + **ikon bendera** kecil di atasnya.
6. **Cincin target** kuning berdenyut.
7. **Rudal kecil + jejak melengkung** putih glow (banyak, paralel).
8. **Rudal besar** meluncur dari kapal selam dengan jejak cyan tebal.
9. **Ledakan** sprite oranye bergerigi (pop).
10. **Label neon 3D** perspektif (cyan / kuning / merah), huruf kapital, letter-spacing lebar, dalam tanda kutip, masuk per huruf, keluar buyar.
11. **Objek hero** di tengah layar (rudal vertikal + api), dengan **latar blur DOF** + gelap.
12. Teks pengali **"x 24"** putih italic glow.
13. **Label vertikal** neon di samping objek.
14. **Morph/transformasi objek** (rudal → warhead bus).
15. **Callout** garis penunjuk + teks tipis yang mengetik mengikuti kurva.
16. **Rack-focus** (blur keluar-masuk) sebagai transisi.
17. **Kartu HUD peringatan** (bingkai sci-fi + ikon ⚠) dengan **glitch/double-exposure** & **berkedip**.
18. **Sensor kata** dengan '#' (W#r).
19. **Stiker potret cut-out** (tokoh) → diganti **batu nisan R.I.P.** (swap).
20. **Stiker tangan zombie** naik dari tanah.
21. **Label menempel objek bergerak** (nama rudal di atas, julukan merah di bawah) + **jatuh** saat selesai.
22. **Hujan garis kuning** (MIRV) diagonal.
23. **Ledakan bintang kecil** tersebar di wilayah.
24. **Stiker radar/peluncur** + **gelembung bicara komik**.
25. **Ikon pesawat** hitam kecil di peta.
26. **Kamera**: whip-zoom, whip-pan, tracking objek, roll/rotasi kontinu ±3–15°/dtk, zoom drift.
27. **Caption** satu baris putih, outline tipis gelap.
28. **Watermark/akun/logo**: tidak terlihat di video (tidak ada yang perlu dihindari).
29. Audio: musik dasar terus-menerus + VO; SFX dianalisis di Tahap 4.

## Catatan untuk replika (jujur sejak awal)
- Objek 3D (kapal selam, rudal, warhead bus, nisan, tangan, radar) dibuat referensi dengan render 3D/stiker. Di Python/PIL saya akan buat versi **2D vektor bergaya** (shading gradien, bayangan) — mirip, tapi tidak 100% identik dengan 3D.
- Potret tokoh nyata **tidak ditiru** (ganti ikon generik/siluet).
- Musik/SFX asli tidak dipakai; diganti sintetis.
