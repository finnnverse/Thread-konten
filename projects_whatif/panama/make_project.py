"""Panama Canal — 'What if the world's most important shortcut ran out of water?'"""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
raw = json.load(open(os.path.join(D, "words_raw.json")))

words = []
for s, e, w in raw:
    w = {"Gaton": "Gatun"}.get(w, w)
    if w == "billion.":                       # VO says "6.6 billion dollars" (ASR wrote "$6.6 billion")
        words.append([s, round(s + (e - s) * 0.55, 2), "billion"]); words.append([round(s + (e - s) * 0.55, 2), e, "dollars."]); continue
    if w == "$6.6":
        w = "6.6"
    words.append([s, e, w])
json.dump(words, open(os.path.join(D, "words.json"), "w"))


def W(word, n=1, off=0.0):
    k = 0
    for s, e, w in words:
        if w.lower().strip(",.?!:;") == word.lower():
            k += 1
            if k == n:
                return round(s + off, 2)
    raise KeyError(f"{word} #{n}")


DUR = round(words[-1][1] + 0.9, 2)
CANAL = [[-79.92, 9.39], [-79.915, 9.30], [-79.92, 9.265], [-79.88, 9.22], [-79.82, 9.17], [-79.76, 9.12], [-79.70, 9.10],
         [-79.66, 9.06], [-79.63, 9.03], [-79.60, 9.01], [-79.58, 8.97], [-79.55, 8.88]]
CANAL_REV = CANAL[::-1]
LAND = {"geom": ["PAN", "COL", "CRI", "NIC", "ECU", "PER", "MEX", "SLV", "HND", "GTM", "USA", "CHL"]}


def ship(route, t0, dur, col="#ffffff", icon=44, dashed=True, t1=None):
    return {"fx": "Walker", "args": [route], "t0": t0, "dur": dur, "kind": "ship", "icon": icon, "w": 3, "dashed": dashed,
            "col": col, "t1": t1 if t1 else round(t0 + dur + 1.0, 2)}


spec = {
  "fps": 60, "size": [1080, 1920], "duration": DUR, "words": "words.json", "max_zoom": 8,
  "watermark": {"text": "WhatIf Atlas", "y": 230, "size": 30, "opacity": 0.55},
  "camera": [
    {"t": 0.0, "lon": -80.0, "lat": 14.0, "width_km": 8000, "roll": -5, "tilt": 11},
    {"t": W("water", 1), "lon": -79.75, "lat": 9.15, "width_km": 500, "roll": -2, "tilt": 9},
    {"t": W("panama", 1), "lon": -79.75, "lat": 9.14, "width_km": 320, "roll": -6, "tilt": 8},
    {"t": W("about", 1), "lon": -79.74, "lat": 9.12, "width_km": 320, "roll": -8, "tilt": 8},
    {"t": W("save"), "lon": -79.75, "lat": 9.1, "width_km": 320, "roll": -4, "tilt": 9},
    {"t": W("around", 1, 0.2), "lon": -78.0, "lat": -6.0, "width_km": 13500, "roll": 0, "tilt": 12},
    {"t": W("and", 2), "lon": -79.8, "lat": 9.1, "width_km": 1000, "roll": -2, "tilt": 10},
    {"t": W("ever", off=0.1), "lon": -75.0, "lat": 12.0, "width_km": 2500, "roll": 1, "tilt": 10},
    {"t": W("strait", off=0.5), "lon": -25.0, "lat": 38.0, "width_km": 19000, "roll": 0, "tilt": 11},
    {"t": W("asia", off=0.3), "lon": -150.0, "lat": 33.0, "width_km": 21000, "roll": 1, "tilt": 11},
    {"t": W("gas", off=0.4), "lon": -155.0, "lat": 33.0, "width_km": 21000, "roll": 2, "tilt": 11},
    {"t": W("tankers", off=0.0), "lon": -95.0, "lat": 16.0, "width_km": 8000, "roll": -2, "tilt": 11},
    {"t": W("panama", 2, 0.2), "lon": -80.5, "lat": 10.5, "width_km": 1800, "roll": -4, "tilt": 10},
    {"t": W("canal's"), "lon": -79.75, "lat": 9.1, "width_km": 320, "roll": -6, "tilt": 9},
    {"t": W("record"), "lon": -79.75, "lat": 9.12, "width_km": 320, "roll": -7, "tilt": 9},
    {"t": W("problem"), "lon": -79.8, "lat": 9.15, "width_km": 320, "roll": -4, "tilt": 8},
    {"t": W("rain", 1), "lon": -79.85, "lat": 9.18, "width_km": 320, "roll": -2, "tilt": 8},
    {"t": W("gatun"), "lon": -79.86, "lat": 9.17, "width_km": 320, "roll": 2, "tilt": 8},
    {"t": W("half"), "lon": -79.72, "lat": 9.12, "width_km": 320, "roll": 3, "tilt": 9},
    {"t": W("now", off=0.1), "lon": -81.5, "lat": 8.5, "width_km": 2600, "roll": 1, "tilt": 10},
    {"t": W("niño", off=0.5), "lon": -97.0, "lat": 3.0, "width_km": 11000, "roll": 0, "tilt": 12},
    {"t": W("back", off=0.2), "lon": -99.0, "lat": 4.0, "width_km": 11500, "roll": 0, "tilt": 12},
    {"t": W("already"), "lon": -85.0, "lat": 8.0, "width_km": 3500, "roll": -2, "tilt": 11},
    {"t": W("ships", 2), "lon": -79.8, "lat": 9.12, "width_km": 320, "roll": -3, "tilt": 10},
    {"t": W("dry"), "lon": -79.8, "lat": 9.15, "width_km": 320, "roll": -5, "tilt": 9},
    {"t": W("choose"), "lon": -79.8, "lat": 9.12, "width_km": 320, "roll": -2, "tilt": 9},
    {"t": DUR, "lon": -79.8, "lat": 9.1, "width_km": 700, "roll": 2, "tilt": 10}
  ],
  "regions": [],
  "elements": [
    {"type": "neon", "text": "PANAMA\nCANAL", "t_in": W("panama", 1) - 0.1, "t_out": W("about", 1) - 0.1, "pos": [560, 650],
     "color": "#06EBFF", "size": 90, "angle": -10, "persp": 0.2},
    {"type": "neon", "text": "EL NIÑO", "t_in": W("el") - 0.05, "t_out": W("canal", 3) - 0.1, "pos": [540, 560],
     "color": "#FF8A1E", "glow": "#B2413D", "size": 96, "weight": 800, "tracking": 0.12},
    {"type": "card", "t_in": W("cut") - 0.1, "t_out": W("dry") - 0.2, "pos": [540, 640], "size": 340, "blink": True, "label": "SLOTS CUT"}
  ],
  "jfx": [
    # hook: lake lights up on "water?"
    {"fx": "HL", "args": [{"lake": "Lago Gatun"}], "t0": W("water", 1) - 0.1, "t1": W("and", 2) - 0.2, "col": "#1f8fe0", "alpha": 0.75, "tex": "ocean_hl"},
    # the canal itself: a permanent cyan line so it reads at every zoom
    {"fx": "Walker", "args": [CANAL], "t0": W("panama", 1) - 0.3, "dur": 1.0, "icon": 0, "w": 7, "col": "#7ff3ff", "t1": W("strait", off=-0.3)},
    {"fx": "Walker", "args": [CANAL], "t0": W("panama", 2) - 0.5, "dur": 0.01, "icon": 0, "w": 7, "col": "#7ff3ff", "t1": W("niño") - 0.3},
    {"fx": "Walker", "args": [CANAL], "t0": W("ships", 2) - 0.5, "dur": 0.01, "icon": 0, "w": 7, "col": "#7ff3ff"},
    ship(CANAL, W("panama", 1) - 0.2, 5.5, icon=46),
    {"fx": "BigLabel", "args": ["80 KM", -79.05, 9.75], "t0": W("80"), "t1": W("save") - 0.1, "angle": -10, "size": 150},
    {"fx": "LeaderLabel", "args": ["LOCKS", -79.92, 9.27], "t0": W("locks"), "t1": W("save"), "h": 200, "dx": -150, "size": 40},
    {"fx": "LeaderLabel", "args": ["GATUN LAKE", -79.85, 9.2], "t0": W("lakes"), "t1": W("save"), "h": 300, "dx": 120, "size": 40},
    # the long way around vs the shortcut
    {"fx": "Walker", "args": [[[-74.0, 40.4], [-66, 18], [-40, -5], [-37, -14], [-48, -28], [-58, -40], [-65, -52], [-67.3, -56.2],
                               [-75, -50], [-74, -35], [-77, -15], [-90, 0], [-108, 18], [-122.5, 37.8]]],
     "t0": W("sailing") - 0.1, "dur": 1.6, "icon": 0, "w": 6, "col": "#ff5a5a", "dashed": True, "t1": W("and", 2) + 0.3},
    {"fx": "Walker", "args": [[[-74.0, 40.4], [-76, 25], [-79.92, 9.39], [-79.55, 8.88], [-92, 12], [-110, 22], [-122.5, 37.8]]],
     "t0": W("all") - 0.1, "dur": 0.9, "icon": 0, "w": 7, "col": "#9eeb25", "t1": W("and", 2) + 0.3},
    {"fx": "LeaderLabel", "args": ["CAPE HORN", -67.3, -56.2], "t0": W("america"), "t1": W("and", 2) + 0.3, "h": 140, "size": 34},
    # best year ever
    {"fx": "BigLabel", "args": ["BEST YEAR EVER", -76.0, 11.5], "t0": W("best"), "t1": W("when") - 0.1, "angle": -8, "size": 120, "col": "#ffd84a"},
    # Hormuz choked -> US energy to Asia
    {"fx": "Cross", "args": [56.4, 26.5], "t0": W("choked"), "t1": W("asia", off=0.6), "size": 110},
    {"fx": "LeaderLabel", "args": ["HORMUZ", 56.4, 26.5], "t0": W("hormuz"), "t1": W("asia", off=0.6), "h": 170, "size": 34},
    ship([[-94.5, 28.8], [-89, 25], [-85.5, 21.8], [-81, 14], [-79.92, 9.39], [-79.55, 8.88], [-88, 9], [-110, 15], [-145, 24],
          [-175, 31], [-200, 34], [-220.2, 35.4]], W("started"), 3.6, col="#ffd84a", icon=50),
    ship([[-94.0, 29.2], [-88, 24.5], [-85, 21.5], [-80.5, 14], [-79.92, 9.39], [-79.55, 8.88], [-90, 8], [-120, 12], [-150, 20],
          [-180, 25], [-238.5, 31.2]], W("buying"), 3.8, col="#ffd84a", icon=50),
    {"fx": "Chip", "args": ["US OIL & GAS → ASIA"], "t0": W("american"), "t1": W("gas", off=0.5), "lonlat": [-150, 30], "dy": -120, "size": 42},
    # squeezed through Panama + record revenue
    ship(CANAL, W("squeezed") - 0.3, 3.2, col="#ffd84a", icon=50),
    ship(CANAL_REV, W("squeezed"), 3.2, col="#ffd84a", icon=50),
    {"fx": "BigLabel", "args": ["$6.6 BILLION", -79.75, 9.45], "t0": W("record") + 0.2, "t1": W("but") - 0.1, "angle": -8, "size": 130, "col": "#ffd84a"},
    {"fx": "Chip", "args": ["RECORD REVENUE · FISCAL 2026"], "t0": W("billion") , "t1": W("but") - 0.1, "lonlat": [-79.7, 8.8], "dy": 60, "size": 36},
    # runs on rain, not fuel
    {"fx": "BigLabel", "args": ["FUEL", -79.75, 9.3], "t0": W("fuel") - 0.1, "t1": W("it", 2) + 0.4, "angle": -8, "size": 130},
    {"fx": "Cross", "args": [-79.35, 9.33], "t0": W("fuel") + 0.15, "t1": W("it", 2) + 0.4, "size": 110},
    {"fx": "BigLabel", "args": ["RAIN", -79.8, 9.32], "t0": W("rain", 1) - 0.05, "t1": W("every") - 0.1, "angle": -8, "size": 150, "col": "#7ff3ff"},
    {"fx": "Snow", "args": [W("rain", 1) - 0.1, W("every") + 0.3], "n": 90},
    # 50 million gallons from Gatun Lake
    {"fx": "HL", "args": [{"lake": "Lago Gatun"}], "t0": W("gatun") - 0.2, "t1": W("now") + 0.6, "col": "#1f8fe0", "alpha": 0.8, "tex": "ocean_hl"},
    ship(CANAL, W("every") - 0.1, 4.0, icon=48),
    {"fx": "BigLabel", "args": ["50M GALLONS", -79.55, 9.8], "t0": W("50"), "t1": W("and", 5) - 0.1, "angle": -8, "size": 120, "col": "#7ff3ff"},
    {"fx": "Chip", "args": ["PER SHIP"], "t0": W("gallons"), "t1": W("and", 5) - 0.1, "lonlat": [-79.55, 9.8], "dy": 110, "size": 40},
    # drinking water for half of Panama
    {"fx": "Pin", "args": [-79.52, 8.98], "t0": W("drinking") - 0.1, "t1": W("now")},
    {"fx": "LeaderLabel", "args": ["PANAMA CITY", -79.52, 8.98], "t0": W("drinking"), "t1": W("now"), "h": 150, "dx": 190, "size": 40},
    {"fx": "Pin", "args": [-79.9, 9.36], "t0": W("water", 3) - 0.1, "t1": W("now")},
    {"fx": "LeaderLabel", "args": ["COLÓN", -79.9, 9.36], "t0": W("water", 3), "t1": W("now"), "h": 230, "dx": -170, "size": 40},
    {"fx": "BigLabel", "args": ["HALF OF PANAMA", -79.6, 8.45], "t0": W("half"), "t1": W("now") - 0.1, "angle": -8, "size": 110, "col": "#ffffff"},
    # El Nino: warm band in the eastern Pacific (water only)
    {"fx": "HL", "args": [[[[-175, -7], [-81, -7], [-79, 4], [-90, 8], [-175, 8], [-175, -7]]]], "t0": W("niño") - 0.2,
     "t1": W("canal", 3) - 0.1, "tex": "fire", "alpha": 0.55, "minus": LAND, "feather": 40},
    {"fx": "Chip", "args": ["36 → 32 SHIPS A DAY (SEPT 2026)"], "t0": W("ships", 2), "t1": W("dry") - 0.2, "lonlat": [-79.75, 8.85], "dy": 140, "size": 38},
    {"fx": "HL", "args": [{"lake": "Lago Gatun"}], "t0": W("dry") - 0.1, "t1": W("so") + 0.5, "tex": "fire", "alpha": 0.55},
    {"fx": "BigLabel", "args": ["1 MONTH EARLY", -79.7, 9.6], "t0": W("month") - 0.1, "t1": W("so") - 0.1, "angle": -8, "size": 100, "col": "#ffb04a"},
    {"fx": "Chip", "args": ["DRY SEASON"], "t0": W("dry"), "t1": W("so") - 0.1, "lonlat": [-79.75, 8.85], "dy": 150, "size": 44},
    # the choice
    {"fx": "Chip", "args": ["WATER FOR SHIPS"], "t0": W("ships", 3) - 0.1, "t1": W("and", 7) + 0.3, "xy": [540, 640], "size": 54},
    {"fx": "Chip", "args": ["WATER FOR PEOPLE"], "t0": W("people", 1) - 0.1, "t1": W("and", 7) + 0.3, "xy": [540, 860], "size": 54},
    {"fx": "GridFinale", "args": [W("by") - 0.1], "text": "PEOPLE FIRST", "t_text": W("people", 2) - 0.05, "bg": "blur"}
  ]
}
bad = [(it.get("fx"), it.get("t0"), it.get("t1")) for it in spec["jfx"] if it.get("t1") is not None and it.get("t0") is not None and it["t1"] <= it["t0"]]
bad += [(e["type"], e.get("t_in"), e.get("t_out")) for e in spec["elements"] if e.get("t_out") is not None and e["t_out"] <= e["t_in"]]
if bad:
    raise SystemExit(f"ERROR t1<=t0: {bad}")
json.dump(spec, open(os.path.join(D, "project.json"), "w"), indent=1, ensure_ascii=False)
print("duration", DUR, "words", len(words))
