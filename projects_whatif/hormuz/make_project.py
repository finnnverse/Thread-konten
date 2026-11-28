"""Hormuz — 'Why the world can't go around Hormuz'. Builds words.json (from VO transcript) + project.json.
Every visual change is keyed to the word it illustrates (W('word') = start time of that word in the VO)."""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
raw = json.load(open(os.path.join(D, "words_raw.json")))

# --- words: follow the VO; merge "november twenty twenty six," -> "November 2026,"
words = []; i = 0
while i < len(raw):
    s, e, w = raw[i]
    if w.lower() == "november" and i + 3 < len(raw) and raw[i + 1][2].lower() == "twenty":
        words.append([s, e, "November"]); words.append([raw[i + 1][0], raw[i + 3][1], "2026,"]); i += 4; continue
    if w == "This" and words and words[-1][2].endswith(","):
        w = "this"
    words.append([s, e, w]); i += 1
json.dump(words, open(os.path.join(D, "words.json"), "w"))


def W(word, n=1, off=0.0):
    k = 0
    for s, e, w in words:
        if w.lower().strip(",.?!:") == word.lower():
            k += 1
            if k == n:
                return round(s + off, 2)
    raise KeyError(word)


DUR = round(words[-1][1] + 0.9, 2)
STRAIT = [56.38, 26.55]
GULF_RING = [[47.6, 30.3], [49.0, 30.6], [50.8, 30.2], [52.5, 28.2], [54.8, 27.2], [56.2, 27.4], [56.95, 26.9],
             [56.9, 26.0], [56.3, 25.9], [55.6, 25.2], [54.0, 24.0], [51.6, 23.9], [50.4, 24.6], [49.6, 26.4],
             [48.2, 28.6], [47.6, 30.3]]
LAND = {"geom": ["IRN", "SAU", "ARE", "OMN", "QAT", "BHR", "KWT", "IRQ"]}
ASIA_ROUTE = [[56.6, 26.3], [58.5, 24.2], [63, 20], [72, 12], [80, 5.8], [92, 5.6], [97, 5.0], [100.5, 2.8], [103.8, 1.25]]


def ship(route, t0, dur, dashed=True, col="#ffffff", icon=44, t1=None):
    d = {"fx": "Walker", "args": [route], "t0": t0, "dur": dur, "kind": "ship", "icon": icon, "w": 3, "dashed": dashed, "col": col}
    d["t1"] = t1 if t1 else round(t0 + dur + 1.2, 2)        # ship trails clear away after arriving
    return d


spec = {
  "fps": 60, "size": [1080, 1920], "duration": DUR, "words": "words.json",
  "audio": {"vo": "vo.mp3"},
  "watermark": {"text": "WhatIf Atlas", "y": 230, "size": 30, "opacity": 0.55},
  "camera": [
    {"t": 0.0, "lon": 55.0, "lat": 24.5, "width_km": 7000, "roll": -6, "tilt": 11},
    {"t": W("only", 1), "lon": 56.2, "lat": 26.3, "width_km": 900, "roll": -3, "tilt": 9},
    {"t": W("Hormuz"), "lon": 56.3, "lat": 26.6, "width_km": 700, "roll": -2, "tilt": 9},
    {"t": W("every"), "lon": 56.1, "lat": 26.4, "width_km": 1100, "roll": 2, "tilt": 9},
    {"t": W("that's", 2), "lon": 56.0, "lat": 26.3, "width_km": 1300, "roll": 3, "tilt": 10},
    {"t": W("one-fifth", off=0.5), "lon": 58, "lat": 24, "width_km": 9500, "roll": -2, "tilt": 12},
    {"t": W("and", 1, -0.1), "lon": 58, "lat": 24.5, "width_km": 8500, "roll": -1, "tilt": 12},
    {"t": W("shipping", off=-0.2), "lon": 56.45, "lat": 26.4, "width_km": 300, "roll": -8, "tilt": 8},
    {"t": W("wide", 2, 0.6), "lon": 56.5, "lat": 26.35, "width_km": 270, "roll": -10, "tilt": 8},
    {"t": W("around", 1), "lon": 52.0, "lat": 26.8, "width_km": 2200, "roll": 0, "tilt": 10},
    {"t": W("for"), "lon": 49.6, "lat": 27.6, "width_km": 1700, "roll": 2, "tilt": 10},
    {"t": W("bahrain"), "lon": 50.8, "lat": 27.2, "width_km": 1800, "roll": 3, "tilt": 10},
    {"t": W("sea", 1, 0.2), "lon": 54.5, "lat": 25.8, "width_km": 2600, "roll": 0, "tilt": 10},
    {"t": W("arabia", off=0.3), "lon": 48.5, "lat": 24.8, "width_km": 3000, "roll": -2, "tilt": 11},
    {"t": W("day", 2, 0.3), "lon": 47.5, "lat": 24.8, "width_km": 3200, "roll": -3, "tilt": 11},
    {"t": W("iran", off=0.2), "lon": 54.0, "lat": 27.6, "width_km": 2300, "roll": 2, "tilt": 10},
    {"t": W("used", off=0.4), "lon": 54.6, "lat": 27.2, "width_km": 2100, "roll": 3, "tilt": 10},
    {"t": W("going", off=0.0), "lon": -12.0, "lat": 36.0, "width_km": 17500, "roll": -1, "tilt": 11},
    {"t": W("america", off=0.7), "lon": -14.0, "lat": 36.0, "width_km": 17800, "roll": -2, "tilt": 11},
    {"t": W("goes", off=-0.2), "lon": 98.0, "lat": 22.0, "width_km": 11500, "roll": 2, "tilt": 12},
    {"t": W("korea", off=0.4), "lon": 102.0, "lat": 24.0, "width_km": 11000, "roll": 3, "tilt": 12},
    {"t": W("lng", off=-0.6), "lon": 53.5, "lat": 25.8, "width_km": 1600, "roll": -2, "tilt": 10},
    {"t": W("door", off=0.3), "lon": 54.8, "lat": 26.0, "width_km": 1500, "roll": -3, "tilt": 10},
    {"t": W("traffic"), "lon": 56.35, "lat": 26.5, "width_km": 520, "roll": -6, "tilt": 9},
    {"t": W("watching"), "lon": 56.3, "lat": 26.5, "width_km": 650, "roll": -4, "tilt": 9},
    {"t": DUR, "lon": 56.0, "lat": 26.0, "width_km": 2600, "roll": 0, "tilt": 11}
  ],
  "regions": [],
  "elements": [
    {"type": "card", "t_in": W("as"), "t_out": W("dropped") - 0.2, "pos": [540, 760], "size": 380, "blink": True, "label": "NOV 2026"},
    {"type": "neon", "text": "STRAIT OF\nHORMUZ", "t_in": W("strait") - 0.1, "t_out": W("every") - 0.2, "pos": [560, 700],
     "color": "#06EBFF", "size": 84, "angle": -10, "persp": 0.2},
    {"type": "neon", "text": "TRAFFIC DOWN", "t_in": W("dropped") - 0.1, "t_out": W("whole") - 0.4, "pos": [540, 1100],
     "color": "#F5030A", "glow": "#B2413D", "size": 70, "weight": 800, "tracking": 0.1}
  ],
  "jfx": [
    # hook: ships moving through the strait + the 54 km gap
    ship([[54.2, 26.2], [55.6, 26.5], [56.25, 26.62], [56.6, 26.4], [57.2, 25.6], [58.2, 24.8]], 0.2, 5.8),
    ship([[58.6, 24.6], [57.3, 25.4], [56.65, 26.25], [56.15, 26.45], [55.0, 26.3], [53.5, 26.2]], 0.6, 6.0),
    {"fx": "NeonLine", "args": [[56.33, 26.37], [56.45, 26.86]], "t0": W("54") - 0.05, "dur": 0.5, "t1": W("every") - 0.2, "col": "#7ff3ff", "w": 7},
    {"fx": "BigLabel", "args": ["54 KM", 55.6, 26.95], "t0": W("54"), "t1": W("strait") - 0.1, "angle": -10, "size": 150, "col": "#ffffff"},
    {"fx": "HL", "args": [{"geom": "__GULF__"}], "t0": W("hormuz") - 0.2, "t1": W("built", 1), "col": "#1f8fe0", "alpha": 0.62,
     "tex": "ocean_hl", "minus": LAND, "feather": 70},
    # 20 million barrels
    ship([[51.9, 25.9], [54.0, 26.2], [55.9, 26.5], [56.6, 26.25], [57.6, 25.2], [59.0, 23.8]], W("every") - 0.2, 4.5),
    ship([[50.6, 27.0], [53.0, 26.7], [55.8, 26.6], [56.55, 26.3], [57.4, 25.3]], W("day") + 0.3, 4.0),
    {"fx": "BigLabel", "args": ["20M", 54.9, 27.3], "t0": W("20"), "t1": W("that's", 2) - 0.1, "angle": -10, "size": 170, "col": "#ffd84a"},
    {"fx": "LeaderLabel", "args": ["BARRELS EVERY DAY", 56.3, 26.0], "t0": W("barrels"), "t1": W("that's", 2) - 0.1, "h": 260, "size": 36},
    # one fifth of world oil
    {"fx": "BigLabel", "args": ["1 / 5", 60.5, 30.5], "t0": W("one-fifth"), "t1": W("and", 1) - 0.1, "angle": -10, "size": 170, "col": "#ffffff"},
    {"fx": "Chip", "args": ["OF ALL OIL THE WORLD USES"], "t0": W("oil", 3), "t1": W("and", 1), "lonlat": STRAIT, "dy": 120, "size": 40},
    # two lanes, two miles each
    {"fx": "Walker", "args": [[[55.95, 26.66], [56.32, 26.70], [56.62, 26.52], [56.88, 26.20]]], "t0": W("each") - 0.1, "dur": 1.1,
     "icon": 0, "w": 9, "col": "#35b8ff", "t1": W("so") - 0.1},
    {"fx": "Walker", "args": [[[55.95, 26.52], [56.30, 26.56], [56.55, 26.40], [56.78, 26.12]]], "t0": W("each") + 0.2, "dur": 1.1,
     "icon": 0, "w": 9, "col": "#9eeb25", "t1": W("so") - 0.1},
    {"fx": "LeaderLabel", "args": ["2 MILES", 56.45, 26.68], "t0": W("two", 1), "t1": W("so") - 0.1, "h": 170, "size": 40},
    {"fx": "LeaderLabel", "args": ["2 MILES", 56.62, 26.38], "t0": W("miles") , "t1": W("so") - 0.1, "h": 90, "dx": 170, "size": 40},
    # no way around
    {"fx": "NeonArc", "args": [[50.5, 27.0], [39.5, 21.5]], "t0": W("around", 1) - 0.2, "dur": 0.9, "t1": W("for") - 0.1, "bulge": 0.25, "col": "#ffffff"},
    {"fx": "Cross", "args": [45.6, 25.9], "t0": W("no"), "t1": W("for"), "size": 110},
    # the four countries (each lights up on its word and stays)
    {"fx": "HL", "args": [{"geom": "KWT"}], "t0": W("kuwait"), "col": "gold_hl", "t1": W("saudi") - 0.2},
    {"fx": "LeaderLabel", "args": ["KUWAIT", 47.6, 29.3], "t0": W("kuwait"), "t1": W("saudi") - 0.2, "h": 150, "size": 34},
    {"fx": "HL", "args": [{"geom": "QAT"}], "t0": W("qatar"), "col": "egypt", "t1": W("saudi") - 0.2},
    {"fx": "LeaderLabel", "args": ["QATAR", 51.2, 25.3], "t0": W("qatar"), "t1": W("saudi") - 0.2, "h": 110, "dx": 150, "size": 34},
    {"fx": "HL", "args": [{"geom": "IRQ"}], "t0": W("iraq"), "col": "orange", "t1": W("saudi") - 0.2},
    {"fx": "BigLabel", "args": ["IRAQ", 46.3, 31.2], "t0": W("iraq"), "t1": W("saudi") - 0.2, "angle": -10, "size": 90},
    {"fx": "HL", "args": [{"geom": "BHR"}], "t0": W("bahrain"), "col": "magenta", "t1": W("saudi") - 0.2},
    {"fx": "LeaderLabel", "args": ["BAHRAIN", 50.55, 26.05], "t0": W("bahrain"), "t1": W("saudi") - 0.2, "h": 200, "dx": -60, "size": 34},
    ship([[48.6, 29.3], [50.6, 27.6], [53.5, 26.5], [55.9, 26.55], [56.6, 26.3], [57.4, 25.3], [59.5, 23.0], [61.5, 21.0]],
         W("this", 1) - 0.1, 2.6, col="#7ff3ff", icon=52),
    {"fx": "LeaderLabel", "args": ["OPEN SEA", 60.5, 21.6], "t0": W("open"), "t1": W("saudi") - 0.1, "h": 150, "size": 38},
    # bypass pipelines
    {"fx": "HL", "args": [{"geom": "SAU"}], "t0": W("saudi"), "col": "gold", "alpha": 0.55, "t1": W("even") - 0.1},
    {"fx": "HL", "args": [{"geom": "ARE"}], "t0": W("uae"), "col": "green", "alpha": 0.6, "t1": W("even") - 0.1},
    {"fx": "Walker", "args": [[[49.7, 25.9], [46.5, 24.9], [43.5, 24.4], [40.5, 24.2], [38.1, 24.1]]], "t0": W("pipelines") - 0.1, "dur": 1.2,
     "icon": 0, "w": 8, "col": "#ffd84a", "t1": W("even") - 0.1},
    {"fx": "Walker", "args": [[[53.7, 23.8], [55.2, 24.4], [56.33, 25.12]]], "t0": W("pipelines") + 0.2, "dur": 0.8,
     "icon": 0, "w": 8, "col": "#9eeb25", "t1": W("even") - 0.1},
    {"fx": "LeaderLabel", "args": ["PIPELINE TO THE RED SEA", 42.5, 24.35], "t0": W("skip"), "t1": W("even") - 0.1, "h": 190, "size": 32},
    {"fx": "LeaderLabel", "args": ["TO FUJAIRAH", 56.3, 25.1], "t0": W("skip") + 0.3, "t1": W("even") - 0.1, "h": 160, "size": 32},
    {"fx": "Chip", "args": ["BYPASS: ONLY A FEW MILLION BARRELS/DAY"], "t0": W("few"), "t1": W("even") - 0.1, "lonlat": [47.0, 27.5], "dy": -40, "size": 36},
    # Iran's pipeline
    {"fx": "Tint", "args": [{"geom": "IRN"}], "t0": W("iran"), "t1": W("twist") , "alpha": 0.4},
    {"fx": "Walker", "args": [[[50.6, 29.4], [52.5, 28.3], [54.6, 27.4], [56.3, 26.9], [57.77, 25.64]]], "t0": W("built", 2) - 0.1, "dur": 1.0,
     "icon": 0, "w": 8, "col": "#ffffff", "t1": W("twist")},
    {"fx": "LeaderLabel", "args": ["IRAN'S BYPASS", 53.5, 27.9], "t0": W("one", 1), "t1": W("twist"), "h": 190, "size": 34},
    {"fx": "Cross", "args": [57.77, 25.64], "t0": W("barely"), "t1": W("twist"), "size": 100},
    # twist: not America -> Asia
    {"fx": "NeonArc", "args": [[56.4, 26.5], [-75.0, 38.0]], "t0": W("most", 2) - 0.1, "dur": 1.2, "t1": W("about", 2) - 0.1, "bulge": 0.18, "col": "#ffffff", "w": 7},
    {"fx": "Cross", "args": [-72.0, 39.5], "t0": W("america"), "t1": W("about", 2) - 0.1, "size": 120},
    {"fx": "BigLabel", "args": ["USA", -76.0, 50.0], "t0": W("america"), "t1": W("about", 2) - 0.1, "angle": -10, "size": 120},
    {"fx": "BigLabel", "args": ["84%", 72.0, 6.0], "t0": W("84%"), "t1": W("nearly") - 0.2, "angle": -10, "size": 190, "col": "#ffd84a"},
    ship(ASIA_ROUTE + [[107, 8], [112, 14], [117, 21], [122.0, 29.8]], W("goes") - 0.1, 3.2),
    ship([[56.6, 26.3], [60, 24], [65, 23], [69.6, 22.6]], W("asia") - 0.1, 1.6),
    ship(ASIA_ROUTE + [[108, 6], [116, 14], [124, 24], [130, 30], [139.9, 35.4]], W("goes") + 0.3, 3.6),
    ship(ASIA_ROUTE + [[107, 9], [115, 17], [122, 26], [126, 32], [129.4, 35.4]], W("goes") + 0.6, 3.4),
    {"fx": "HL", "args": [{"geom": "CHN"}], "t0": W("china"), "col": "red", "alpha": 0.6, "t1": W("nearly") - 0.2},
    {"fx": "HL", "args": [{"geom": "IND"}], "t0": W("india"), "col": "orange", "alpha": 0.65, "t1": W("nearly") - 0.2},
    {"fx": "HL", "args": [{"geom": "JPN"}], "t0": W("japan"), "col": "yellow", "t1": W("nearly") - 0.2},
    {"fx": "HL", "args": [{"geom": "KOR"}], "t0": W("south"), "col": "magenta", "t1": W("nearly") - 0.2},
    {"fx": "LeaderLabel", "args": ["JAPAN", 139.0, 36.5], "t0": W("japan"), "t1": W("nearly") - 0.2, "h": 140, "size": 32},
    {"fx": "LeaderLabel", "args": ["SOUTH KOREA", 127.8, 36.5], "t0": W("south"), "t1": W("nearly") - 0.2, "h": 220, "dx": -120, "size": 32},
    # LNG
    {"fx": "HL", "args": [{"geom": "QAT"}], "t0": W("lng") - 0.3, "col": "lightblue", "t1": W("as")},
    ship([[51.65, 25.95], [53.5, 26.3], [55.8, 26.55], [56.55, 26.3], [57.5, 25.2], [59.0, 23.9]], W("lng") - 0.2, 2.6, col="#7ff3ff", icon=50),
    {"fx": "Chip", "args": ["~19% OF WORLD LNG"], "t0": W("fifth", 1) - 0.1, "t1": W("as"), "lonlat": [53.0, 24.3], "dy": 120, "size": 42},
    {"fx": "BigLabel", "args": ["LNG", 51.6, 27.9], "t0": W("lng"), "t1": W("as"), "angle": -10, "size": 120, "col": "#7ff3ff"},
    # finale
    {"fx": "GridFinale", "args": [W("whole") - 0.1], "text": "54 KM", "t_text": W("narrow") - 0.1, "bg": "blur"}
  ]
}
# substitute the Gulf ring (water polygon, land subtracted by journey HL 'minus')
for it in spec["jfx"]:
    if it.get("args") and isinstance(it["args"][0], dict) and it["args"][0].get("geom") == "__GULF__":
        it["args"][0] = [GULF_RING]
json.dump(spec, open(os.path.join(D, "project.json"), "w"), indent=1)
print("duration", DUR, "words", len(words))
