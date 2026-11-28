"""Nauru — 'What if a country got rich by selling its own ground?' (script + VO by the channel owner)"""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
raw = json.load(open(os.path.join(D, "words_raw.json")))

# ASR -> caption text that matches the written script
words, i = [], 0
while i < len(raw):
    s, e, w = raw[i]
    nxt = [r[2] for r in raw[i + 1:i + 4]]
    if w == "nineteen" and nxt[:2] == ["sixty", "eight,"]:
        words.append([s, raw[i + 2][1], "1968,"]); i += 3; continue
    if w == "nineteen" and nxt[:1] == ["seventies,"]:
        words.append([s, raw[i + 1][1], "1970s,"]); i += 2; continue
    if w == "fifty" and nxt[:1] == ["thousand"]:
        words.append([s, raw[i + 1][1], "50,000"]); i += 2; continue
    if w == "Mind" and nxt[:2] == ["Out", "Center."]:
        words.append([s, raw[i + 1][1], "mined-out"]); words.append([raw[i + 2][0], raw[i + 2][1], "center."]); i += 3; continue
    if w == "The" and words and words[-1][2] == "2000,":
        w = "the"
    if w == "80%":
        w = "80 percent"
    words.append([s, e, w]); i += 1
json.dump(words, open(os.path.join(D, "words.json"), "w"))


def W(word, n=1, off=0.0):
    k = 0
    for s, e, w in words:
        if w.lower().strip(",.?!:;") == word.lower():
            k += 1
            if k == n:
                return round(s + off, 2)
    raise KeyError(f"{word} #{n}")


DUR = round(words[-1][1] + 1.0, 2)
C = (166.932, -0.523)                                     # island centre
COAST = json.load(open(os.path.join(D, "nauru_coast.json")))
INNER = [[round(C[0] + (x - C[0]) * 0.8, 5), round(C[1] + (y - C[1]) * 0.8, 5)] for x, y in COAST]
GOLD, GREEN, GREY, RED = "#ffd84a", "#59d85a", "#c9c2b5", "#ff5a5a"


def ship(route, t0, dur, col="#ffffff", icon=44, t1=None):
    return {"fx": "Walker", "args": [route], "t0": round(t0, 2), "dur": dur, "kind": "ship", "icon": icon, "w": 3, "dashed": True,
            "col": col, "t1": t1 if t1 else round(t0 + dur + 1.0, 2)}


ISL = 13
cam = [
    (0.0, C[0], C[1], 22, -4, 9),
    (W("ground"), C[0], C[1], ISL, -2, 8),
    (W("nauru", 1), C[0], C[1] + 0.003, 12, -5, 8),
    (W("nation"), C[0], C[1], 30, -3, 9),
    (W("kilometers", off=0.2), C[0], C[1], 110, -1, 10),
    (W("pacific", off=1.0), 168.0, -4.0, 4200, 0, 11),
    (W("capital"), 167.5, -3.5, 4000, 2, 11),
    (W("in", 2), C[0], C[1], 400, 1, 10),
    (W("prospectors"), C[0], C[1], 40, 0, 9),
    (W("purest"), C[0], C[1], ISL, -3, 8),
    (W("years"), C[0], C[1] + 0.002, 12, -5, 8),
    (W("phosphate", 2), C[0], C[1], 200, -3, 9),
    (W("means"), C[0], C[1], 1500, -1, 10),
    (W("fertilizer", off=0.3), 162.0, -10.0, 9000, 0, 11),
    (W("wanted"), 160.0, -5.0, 14000, 1, 11),
    (W("after", off=0.2), C[0], C[1], 3000, 0, 11),
    (W("independence", off=0.3), C[0], C[1], 120, -1, 9),
    (W("1968"), C[0], C[1], ISL, -3, 8),
    (W("exploded"), C[0], C[1], 14, -5, 8),
    (W("income"), C[0], C[1], ISL, -3, 8),
    (W("year", 1), C[0], C[1], 18, -2, 8),
    (W("second"), C[0], C[1], 120, -1, 9),
    (W("only"), C[0], C[1], 2200, 0, 10),
    (W("arabia", off=0.3), 100.0, 16.0, 21000, 0, 12),
    (W("but", 1), 102.0, 14.0, 20500, 1, 12),
    (W("phosphate", 3), C[0], C[1], 4000, 0, 11),
    (W("digging"), C[0], C[1], 250, -2, 9),
    (W("island", 3), C[0], C[1], ISL, -3, 8),
    (W("mined", 1), C[0], C[1], 12, -5, 8),
    (W("spikes"), C[0], C[1], 12.5, -2, 8),
    (W("dollars", 2), C[0], C[1], 14, 0, 8),
    (W("then"), C[0], C[1], 200, 0, 9),
    (W("on", 2, -0.1), C[0], C[1], 2500, 0, 11),
    (W("deals", off=0.4), 90.0, 22.0, 22000, 0, 12),
    (W("london", off=-0.1), 10.0, 48.0, 6000, -1, 11),
    (W("musical", off=0.2), -0.12, 51.5, 1400, -3, 10),
    (W("vinci"), -0.12, 51.5, 1300, -5, 10),
    (W("2000", off=0.4), 80.0, 20.0, 24000, 0, 12),
    (W("phosphate", 4), C[0], C[1], 3000, 0, 11),
    (W("was", 3), C[0], C[1], 200, -1, 9),
    (W("fund", 2), C[0], C[1], 30, -2, 9),
    (W("today"), C[0], C[1], ISL, -3, 8),
    (W("center"), C[0], C[1], 11.5, -5, 8),
    (DUR, C[0], C[1], 14, -2, 8),
]

jfx = [
    # hook: the island lights up gold, then the ground is 'sold'
    {"fx": "HL", "args": [[COAST]], "t0": W("rich") - 0.1, "t1": W("this") + 0.3, "col": "gold", "alpha": 0.55},
    {"fx": "BigLabel", "args": ["$", C[0] + 0.02, C[1] + 0.02], "t0": W("selling"), "t1": W("this") - 0.05, "angle": -8, "size": 220, "col": GOLD},
    # smallest island nation, 21 km², 12,000 people, no capital
    {"fx": "BigLabel", "args": ["21 KM²", C[0], C[1] + 0.06], "t0": W("21") - 0.05, "t1": W("pacific") + 0.2, "angle": -8, "size": 150},
    {"fx": "Pin", "args": [C[0], C[1]], "t0": W("pacific") - 0.1, "t1": W("in", 2)},
    {"fx": "LeaderLabel", "args": ["NAURU", C[0], C[1]], "t0": W("pacific"), "t1": W("in", 2), "h": 190, "dx": 120, "size": 46},
    {"fx": "LeaderLabel", "args": ["AUSTRALIA", 146.0, -24.0], "t0": W("people") - 0.2, "t1": W("in", 2), "h": 120, "size": 34},
    {"fx": "Chip", "args": ["≈ 12,000 PEOPLE"], "t0": W("12,000") - 0.05, "t1": W("in", 2), "xy": [540, 560], "size": 46},
    {"fx": "Chip", "args": ["NO OFFICIAL CAPITAL"], "t0": W("official") - 0.05, "t1": W("in", 2), "xy": [540, 660], "col": RED, "fg": "#ffffff", "size": 42},
    # 1900: phosphate under the island
    {"fx": "BigLabel", "args": ["1900", C[0], C[1] + 0.05], "t0": W("1900") - 0.05, "t1": W("purest") - 0.1, "angle": -8, "size": 160},
    {"fx": "HL", "args": [[INNER]], "t0": W("purest") - 0.1, "t1": W("phosphate", 2), "col": GOLD, "alpha": 0.6, "tex": "fire"},
    {"fx": "BigLabel", "args": ["PHOSPHATE", C[0], C[1] + 0.045], "t0": W("phosphate", 1) - 0.05, "t1": W("phosphate", 2) - 0.1, "angle": -8, "size": 120, "col": GOLD},
    {"fx": "Chip", "args": ["BIRD DROPPINGS"], "t0": W("bird") - 0.05, "t1": W("phosphate", 2) - 0.1, "lonlat": [C[0], C[1] - 0.04], "dy": 0, "size": 44},
    {"fx": "Chip", "args": ["MILLIONS OF YEARS"], "t0": W("millions") - 0.05, "t1": W("phosphate", 2) - 0.1, "lonlat": [C[0], C[1] - 0.04], "dy": 80, "size": 40},
    # fertilizer -> the whole world wanted it
    {"fx": "BigLabel", "args": ["FERTILIZER", 160.0, -2.0], "t0": W("fertilizer") - 0.05, "t1": W("after") - 0.1, "angle": -8, "size": 120, "col": GREEN},
    ship([[C[0], C[1]], [160, -8], [156, -20], [153.5, -27.5], [151.5, -33.8]], W("whole"), 2.4, col=GOLD, icon=46, t1=W("after")),
    ship([[C[0], C[1]], [170, -15], [174, -30], [174.8, -36.8]], W("world") - 0.1, 2.4, col=GOLD, icon=46, t1=W("after")),
    ship([[C[0], C[1]], [158, 10], [148, 25], [140, 34.5]], W("wanted") - 0.2, 2.2, col=GOLD, icon=46, t1=W("after")),
    # 1968 independence, Nauru takes the mines, prices explode
    {"fx": "BigLabel", "args": ["1968", C[0], C[1] + 0.05], "t0": W("1968") - 0.05, "t1": W("took") + 0.3, "angle": -8, "size": 160},
    {"fx": "Chip", "args": ["INDEPENDENCE"], "t0": W("independence"), "t1": W("took") + 0.3, "lonlat": [C[0], C[1] + 0.05], "dy": 110, "size": 42},
    {"fx": "HL", "args": [[INNER]], "t0": W("mines") - 0.1, "t1": W("by", 2), "col": GOLD, "alpha": 0.55},
    {"fx": "Check", "args": [C[0], C[1]], "t0": W("mines"), "t1": W("prices") - 0.1, "geo": True, "size": 160},
    {"fx": "BigLabel", "args": ["PRICES BOOM", C[0], C[1] - 0.045], "t0": W("prices") - 0.05, "t1": W("by", 2) - 0.1, "angle": -8, "size": 120, "col": GOLD},
    # $50,000 per person, second only to Saudi Arabia
    {"fx": "BigLabel", "args": ["$50,000", C[0], C[1] + 0.045], "t0": W("50,000") - 0.05, "t1": W("second") + 0.2, "angle": -8, "size": 150, "col": GOLD},
    {"fx": "Chip", "args": ["PER PERSON · PER YEAR"], "t0": W("dollars", 1), "t1": W("second") + 0.2, "lonlat": [C[0], C[1] + 0.045], "dy": 115, "size": 40},
    {"fx": "Chip", "args": ["MID-1970s"], "t0": W("1970s") - 0.05, "t1": W("50,000"), "xy": [540, 560], "size": 44},
    {"fx": "HL", "args": [{"geom": "SAU"}], "t0": W("saudi") - 0.1, "t1": W("but", 1) + 0.6, "col": "gold", "alpha": 0.9},
    {"fx": "Chip", "args": ["#1 SAUDI ARABIA"], "t0": W("saudi"), "t1": W("but", 1) + 0.5, "xy": [540, 560], "size": 44},
    {"fx": "Pin", "args": [C[0], C[1]], "t0": W("second") - 0.1, "t1": W("but", 1) + 0.6},
    {"fx": "Chip", "args": ["#2 NAURU"], "t0": W("second"), "t1": W("but", 1) + 0.5, "xy": [540, 650], "size": 44, "col": GOLD},
    # digging up the island: 80 percent strip mined
    {"fx": "HL", "args": [[INNER]], "t0": W("digging") - 0.1, "t1": W("money"), "col": GREY, "alpha": 0.7},
    {"fx": "BigLabel", "args": ["80%", C[0], C[1] + 0.045], "t0": W("80 percent") - 0.05, "t1": W("leaving"), "angle": -8, "size": 180, "col": "#ffffff"},
    {"fx": "Chip", "args": ["STRIP MINED"], "t0": W("strip") - 0.05, "t1": W("leaving"), "lonlat": [C[0], C[1] + 0.045], "dy": 130, "size": 44, "col": RED, "fg": "#ffffff"},
    {"fx": "BigLabel", "args": ["MOONSCAPE", C[0], C[1] + 0.045], "t0": W("moonscape") - 0.05, "t1": W("money") - 0.05, "angle": -8, "size": 130, "col": GREY},
    {"fx": "LeaderLabel", "args": ["LIMESTONE SPIKES", C[0] + 0.005, C[1] - 0.005], "t0": W("limestone"), "t1": W("money") - 0.05, "h": 260, "dx": 60, "size": 40},
    # trust fund -> burned on bad deals -> London musical
    {"fx": "BigLabel", "args": ["$1 BILLION+", C[0], C[1] + 0.045], "t0": W("billion") - 0.1, "t1": W("burned") + 0.3, "angle": -8, "size": 140, "col": GOLD},
    {"fx": "Chip", "args": ["TRUST FUND"], "t0": W("trust") - 0.05, "t1": W("burned") + 0.3, "lonlat": [C[0], C[1] + 0.045], "dy": 120, "size": 44},
    {"fx": "Pin", "args": [-0.12, 51.5], "t0": W("london") - 0.1, "t1": W("by", 3)},
    {"fx": "LeaderLabel", "args": ["LONDON", -0.12, 51.5], "t0": W("london"), "t1": W("by", 3), "h": 170, "dx": 130, "size": 44},
    {"fx": "BigLabel", "args": ["LEONARDO", -1.5, 55.0], "t0": W("leonardo") - 0.05, "t1": W("by", 3), "angle": -8, "size": 130, "col": GOLD},
    {"fx": "Chip", "args": ["FAILED MUSICAL"], "t0": W("failed") - 0.05, "t1": W("by", 3), "lonlat": [-0.12, 51.5], "dy": 120, "size": 42, "col": RED, "fg": "#ffffff"},
    # 2000: phosphate gone, fund empty
    {"fx": "Chip", "args": ["BY 2000"], "t0": W("2000") - 0.05, "t1": W("gone") + 0.3, "xy": [540, 560], "size": 48},
    {"fx": "Cross", "args": [C[0], C[1]], "t0": W("gone"), "t1": W("today") - 0.1, "size": 150},
    {"fx": "BigLabel", "args": ["FUND: $0", C[0], C[1] + 0.05], "t0": W("empty") - 0.05, "t1": W("today") - 0.05, "angle": -8, "size": 130, "col": RED},
    # today: the thin green ring around the mined-out centre
    {"fx": "HL", "args": [[COAST]], "t0": W("ring") - 0.15, "t1": W("was", 5) + 0.2, "col": GREEN, "alpha": 0.7, "minus": [INNER]},
    {"fx": "HL", "args": [[INNER]], "t0": W("center") - 0.15, "t1": W("was", 5) + 0.2, "col": GREY, "alpha": 0.6},
    {"fx": "LeaderLabel", "args": ["WHERE PEOPLE LIVE", C[0] - 0.024, C[1] - 0.01], "t0": W("lives"), "t1": W("was", 5), "h": 320, "dx": -40, "size": 38},
    {"fx": "LeaderLabel", "args": ["MINED-OUT", C[0] + 0.004, C[1] + 0.004], "t0": W("mined-out"), "t1": W("was", 5), "h": 230, "dx": 80, "size": 40},
    {"fx": "GridFinale", "args": [W("was", 5) - 0.05], "text": "WORTH IT?", "t_text": W("worth", 2) - 0.05, "bg": "blur"},
]

spec = {
    "fps": 60, "size": [1080, 1920], "duration": DUR, "words": "words.json", "max_zoom": 14, "hi_ocean": True,
    "watermark": {"text": "WhatIf Atlas", "y": 230, "size": 30, "opacity": 0.55},
    "camera": [{"t": t, "lon": lo, "lat": la, "width_km": w, "roll": r, "tilt": ti} for t, lo, la, w, r, ti in cam],
    "regions": [],
    "elements": [
        {"type": "neon", "text": "NAURU", "t_in": W("nauru", 1) - 0.05, "t_out": W("just") - 0.1, "pos": [540, 640],
         "color": "#06EBFF", "size": 110, "angle": -8, "persp": 0.2},
    ],
    "jfx": jfx,
}
bad = [(it.get("fx"), it.get("t0"), it.get("t1")) for it in spec["jfx"] if it.get("t1") is not None and it.get("t0") is not None and it["t1"] <= it["t0"]]
bad += [(e["type"], e.get("t_in"), e.get("t_out")) for e in spec["elements"] if e.get("t_out") is not None and e["t_out"] <= e["t_in"]]
if bad:
    raise SystemExit(f"ERROR t1<=t0: {bad}")
json.dump(spec, open(os.path.join(D, "project.json"), "w"), indent=1, ensure_ascii=False)
print("duration", DUR, "words", len(words))
