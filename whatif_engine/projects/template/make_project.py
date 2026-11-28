"""TEMPLATE — salin ke projects/<slug>/ lalu isi BAGIAN TOPIK. Jalankan: python3 make_project.py
Butuh: words_raw.json (tools/asr_words.py) dan vo.mp3 di folder yang sama."""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
raw = json.load(open(os.path.join(D, "words_raw.json")))

# ---- words: ikuti VO. Gabungkan token yang terpecah di sini bila perlu (angka/tahun) ----
words = [list(w) for w in raw]
json.dump(words, open(os.path.join(D, "words.json"), "w"))


def W(word, n=1, off=0.0):
    """waktu mulai kemunculan ke-n `word` di VO (+off). Kata umum ('and','about','one') -> isi n yang benar!"""
    k = 0
    for s, e, w in words:
        if w.lower().strip(",.?!:;") == word.lower():
            k += 1
            if k == n:
                return round(s + off, 2)
    raise KeyError(f"{word} #{n}")


DUR = round(words[-1][1] + 0.9, 2)

# =========================== BAGIAN TOPIK ===========================
spec = {
  "fps": 60, "size": [1080, 1920], "duration": DUR, "words": "words.json",
  "watermark": {"text": "", "y": 230, "size": 30, "opacity": 0.55},     # isi nama channel dari user
  "camera": [
    {"t": 0.0, "lon": 0, "lat": 20, "width_km": 9000, "roll": -4, "tilt": 11},
    {"t": DUR, "lon": 0, "lat": 20, "width_km": 6000, "roll": 2, "tilt": 10},
  ],
  "regions": [],      # {"id": "RUS", "style": "opaque"} / {"id": "USA", "style": "tint", "t_in": W("america")}
  "elements": [],     # neon / trail / bursts / sticker / card / tracked / rain
  "jfx": [],          # HL / BigLabel / LeaderLabel / NeonArc / Walker / Chip / Cross / GridFinale ...
}
# ====================================================================

# validasi: elemen yang hilang sebelum muncul
bad = [(it.get("fx"), it.get("t0"), it.get("t1")) for it in spec["jfx"] if it.get("t1") is not None and it.get("t0") is not None and it["t1"] <= it["t0"]]
bad += [(e["type"], e.get("t_in"), e.get("t_out")) for e in spec["elements"] if e.get("t_out") is not None and e.get("t_in") is not None and e["t_out"] <= e["t_in"]]
if bad:
    raise SystemExit(f"ERROR t1<=t0: {bad}")
json.dump(spec, open(os.path.join(D, "project.json"), "w"), indent=1)
print("duration", DUR, "words", len(words))
