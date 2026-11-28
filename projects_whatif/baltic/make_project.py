"""Baltic cables — 'What if Russia cut every cable under the Baltic Sea?'"""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
raw = json.load(open(os.path.join(D, "words_raw.json")))

words = []
for s, e, w in raw:
    if w == "100":
        w = "hundred"
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


DUR = round(words[-1][1] + 1.0, 2)
DATA, POWER, GAS = "#7ff3ff", "#ffd84a", "#ff8a3d"
CABLES = {   # approximate public routes (lon, lat)
    "C-Lion1":        (DATA,  [[24.93, 60.15], [23.5, 59.85], [21.5, 59.5], [20.3, 58.6], [19.7, 57.3], [18.5, 56.0], [16.0, 55.3], [13.5, 54.75], [12.1, 54.18]]),
    "BCS":            (DATA,  [[18.75, 57.45], [21.06, 56.03]]),
    "Elisa":          (DATA,  [[24.95, 60.15], [24.75, 59.45]]),
    "Estlink1":       (POWER, [[24.55, 60.13], [24.6, 59.42]]),
    "Estlink2":       (POWER, [[25.65, 60.3], [27.0, 59.43]]),
    "NordBalt":       (POWER, [[16.45, 56.7], [18.5, 56.2], [21.1, 55.7]]),
    "BalticCable":    (POWER, [[13.15, 55.37], [12.0, 54.7], [10.85, 54.0]]),
    "SwePol":         (POWER, [[14.85, 56.15], [16.0, 55.4], [17.0, 54.6]]),
    "Balticconnector": (GAS,  [[24.0, 60.04], [24.05, 59.35]]),
    "NordStream":     (GAS,   [[28.05, 60.55], [26.5, 60.15], [24.5, 59.85], [22.0, 59.45], [20.0, 58.3], [19.6, 57.0], [17.5, 55.9], [15.5, 55.3], [14.4, 54.7], [13.65, 54.15]]),
    "BalticPipe":     (GAS,   [[12.2, 55.25], [13.6, 54.75], [15.07, 54.1]]),
}
BALTIC_SEA = [[[10, 53.8], [14, 53.6], [21, 54.2], [22, 57], [24.2, 57], [24.5, 59.2], [30.5, 59.8], [30.5, 60.8], [26, 60.8], [22, 60.6],
               [21.5, 63], [25.5, 65.9], [22, 66], [17, 63], [19, 60], [18.5, 59], [16.5, 56.2], [12.5, 56.0], [10, 55.5], [10, 53.8]]]
LAND = {"geom": ["FIN", "SWE", "EST", "LVA", "LTU", "RUS", "POL", "DEU", "DNK", "NOR", "BLR"]}


def cable(name, t0, t1=None, dur=0.6, w=6):
    col, route = CABLES[name]
    return {"fx": "Walker", "args": [route], "t0": round(t0, 2), "dur": dur, "icon": 0, "w": w, "col": col, "t1": t1}


def ship(route, t0, dur, col="#ffffff", icon=44, t1=None, dashed=True, w=3):
    return {"fx": "Walker", "args": [route], "t0": round(t0, 2), "dur": dur, "kind": "ship", "icon": icon, "w": w, "dashed": dashed,
            "col": col, "t1": t1 if t1 else round(t0 + dur + 1.0, 2)}


cam = [
    (0.0, 15.0, 57.0, 4200, -4, 11),
    (W("baltic", 1), 20.0, 58.0, 1900, -2, 10),
    (W("shallow"), 19.5, 58.0, 1700, -4, 10),
    (W("across"), 19.0, 57.5, 1800, -2, 10),
    (W("finland", 1), 20.0, 58.5, 2000, 0, 10),
    (W("breaking"), 19.5, 58.0, 1750, 2, 10),
    (W("in", 1), 22.5, 59.2, 900, 0, 10),
    (W("ship's"), 24.3, 59.75, 400, -4, 9),
    (W("estonia", 1), 24.4, 59.75, 380, -6, 9),
    (W("christmas"), 25.4, 59.88, 470, -3, 9),
    (W("hundred"), 25.7, 59.9, 440, -2, 9),
    (W("estonia", 2), 25.9, 59.85, 450, 0, 9),
    (W("new"), 25.0, 59.85, 370, -3, 9),
    (W("broken"), 24.85, 59.82, 340, -5, 9),
    (W("prove"), 21.0, 58.3, 1700, -2, 10),
    (W("in", 2, 0.3), 24.0, 57.3, 1300, -2, 10),
    (W("russia's", 2), 28.0, 57.0, 2300, 0, 11),
    (W("europe's"), 21.0, 55.5, 2600, 1, 11),
    (W("part", 2), 20.0, 57.2, 1700, -2, 10),
    (W("nato"), 21.0, 58.0, 1600, -1, 10),
    (W("marines"), 23.5, 59.6, 950, -3, 9),
    (W("but"), 19.5, 57.5, 1900, -1, 10),
    (DUR, 19.5, 57.5, 2150, 1, 11),
]

jfx = []
# --- hook: all cables flash in, then the sea lights up ---
order = ["NordStream", "C-Lion1", "Estlink2", "NordBalt", "Balticconnector", "BCS", "SwePol", "Estlink1", "BalticCable", "BalticPipe", "Elisa"]
for i, n in enumerate(order):
    jfx.append(cable(n, W("cable", 1) + 0.06 * i, W("shallow"), dur=0.4))
jfx.append({"fx": "Cross", "args": [21.0, 58.6], "t0": W("cut", 1), "t1": W("shallow"), "size": 90})
# --- shallow sea ---
jfx.append({"fx": "HL", "args": [BALTIC_SEA], "t0": W("shallow") - 0.1, "t1": W("across") + 0.3, "tex": "ocean_hl", "alpha": 0.6, "minus": LAND, "feather": 30})
jfx.append({"fx": "BigLabel", "args": ["55 M", 19.2, 58.6], "t0": W("fifty"), "t1": W("across") - 0.1, "angle": -8, "size": 170, "col": DATA})
jfx.append({"fx": "Chip", "args": ["AVERAGE DEPTH"], "t0": W("meters"), "t1": W("across") - 0.1, "lonlat": [19.2, 58.6], "dy": 120, "size": 42})
# --- dozens of cables & pipelines (they stay until the close-ups) ---
for i, n in enumerate(order):
    jfx.append(cable(n, W("cables", 1) + 0.13 * i, W("in", 1) + 0.3, dur=0.7))
jfx.append({"fx": "Chip", "args": ["POWER"], "t0": W("power", 1) - 0.05, "t1": W("finland", 1) - 0.1, "xy": [300, 560], "col": POWER, "size": 46})
jfx.append({"fx": "Chip", "args": ["GAS"], "t0": W("gas", 1) - 0.05, "t1": W("finland", 1) - 0.1, "xy": [540, 560], "col": GAS, "size": 46})
jfx.append({"fx": "Chip", "args": ["INTERNET"], "t0": W("internet") - 0.05, "t1": W("finland", 1) - 0.1, "xy": [780, 560], "col": DATA, "size": 46})
for code, word in [("FIN", ("finland", 1)), ("SWE", ("sweden", 1)), ("DEU", ("germany", 1))]:
    jfx.append({"fx": "HL", "args": [{"geom": code}], "t0": W(*word) - 0.05, "t1": W("breaking") + 0.2, "col": "gold", "alpha": 0.55})
jfx.append({"fx": "HL", "args": [{"geom": ["EST", "LVA", "LTU"]}], "t0": W("baltic", 3) - 0.05, "t1": W("breaking") + 0.2, "col": "gold", "alpha": 0.55})
# --- they keep breaking ---
for i, (lo, la) in enumerate([(25.9, 59.95), (19.7, 57.4), (24.0, 59.7)]):
    jfx.append({"fx": "Cross", "args": [lo, la], "t0": W("keep") + 0.22 * i, "t1": W("in", 1) + 0.2, "size": 80, "sfx": i == 0})
# --- 2023: Balticconnector ---
jfx.append({"fx": "BigLabel", "args": ["2023", 24.0, 60.35], "t0": W("2023") - 0.05, "t1": W("on", 1) - 0.1, "angle": -8, "size": 140})
jfx.append(cable("Balticconnector", W("2023") - 0.2, W("on", 1), dur=0.6, w=8))
jfx.append(cable("Estlink1", W("2023") - 0.2, W("on", 1), dur=0.01, w=5))
jfx.append(ship([[25.6, 59.82], [24.9, 59.8], [24.03, 59.72], [23.3, 59.68]], W("ship's") - 0.4, 2.4, icon=46))
jfx.append({"fx": "Cross", "args": [24.03, 59.72], "t0": W("ripped"), "t1": W("on", 1) - 0.1, "size": 100})
jfx.append({"fx": "LeaderLabel", "args": ["GAS PIPELINE", 24.03, 59.5], "t0": W("pipeline") - 0.1, "t1": W("on", 1) - 0.1, "h": 220, "dx": -150, "size": 38})
jfx.append({"fx": "LeaderLabel", "args": ["FINLAND", 24.4, 60.25], "t0": W("finland", 2), "t1": W("on", 1) - 0.1, "h": 120, "dx": 120, "size": 36})
jfx.append({"fx": "LeaderLabel", "args": ["ESTONIA", 24.6, 59.3], "t0": W("estonia", 1) - 0.1, "t1": W("on", 1) - 0.1, "h": 120, "dx": 160, "size": 36})
# --- Christmas 2024: Eagle S, ~100 km drag, Estlink 2 cut ---
jfx.append({"fx": "BigLabel", "args": ["DEC 25, 2024", 25.6, 60.45], "t0": W("christmas"), "t1": W("the", 4) + 0.4, "angle": -8, "size": 110})
jfx.append(cable("Estlink2", W("christmas") - 0.3, W("on", 2), dur=0.6, w=8))
jfx.append(ship([[27.6, 59.98], [26.6, 59.95], [25.6, 59.87], [24.6, 59.8]], W("tanker") - 0.2, 6.0, col="#ff5a5a", icon=50, t1=W("on", 2) - 0.2, dashed=False, w=6))
jfx.append({"fx": "Chip", "args": ["EAGLE S"], "t0": W("eagle") - 0.05, "t1": W("dragged") + 0.3, "lonlat": [26.8, 59.97], "dy": -110, "size": 42})
jfx.append({"fx": "Chip", "args": ["RUSSIA'S SHADOW FLEET"], "t0": W("shadow") - 0.1, "t1": W("for", 1), "xy": [540, 560], "col": "#ff5a5a", "fg": "#ffffff", "size": 42})
jfx.append({"fx": "BigLabel", "args": ["~100 KM", 25.3, 60.55], "t0": W("hundred"), "t1": W("on", 2) - 0.1, "angle": -8, "size": 140, "col": "#ff5a5a"})
jfx.append({"fx": "Chip", "args": ["ANCHOR DRAG MARKS"], "t0": W("kilometers"), "t1": W("on", 2) - 0.1, "lonlat": [25.3, 60.55], "dy": -110, "size": 38})
jfx.append({"fx": "Cross", "args": [26.24, 59.9], "t0": W("cut", 2), "t1": W("on", 2) - 0.1, "size": 100})
# --- New Year's Eve 2025: another ship seized ---
jfx.append({"fx": "BigLabel", "args": ["DEC 31, 2025", 25.1, 59.35], "t0": W("new") - 0.05, "t1": W("finland", 3) + 0.6, "angle": -8, "size": 100})
jfx.append(cable("Elisa", W("new") - 0.3, W("every", 2), dur=0.6, w=8))
jfx.append(ship([[26.0, 59.93], [25.4, 59.9], [24.86, 59.82]], W("year's"), 3.2, col="#ff5a5a", icon=48, t1=W("every", 2), dashed=False, w=6))
jfx.append({"fx": "Pin", "args": [24.94, 60.17], "t0": W("seized") - 0.1, "t1": W("every", 2)})
jfx.append({"fx": "Chip", "args": ["SEIZED"], "t0": W("seized"), "t1": W("every", 2) - 0.1, "lonlat": [24.94, 60.17], "dy": -110, "col": "#ff5a5a", "fg": "#ffffff", "size": 44})
jfx.append({"fx": "Cross", "args": [24.86, 59.82], "t0": W("broken"), "t1": W("every", 2), "size": 100})
jfx.append({"fx": "LeaderLabel", "args": ["DATA CABLE", 24.8, 59.6], "t0": W("cable", 3) - 0.1, "t1": W("every", 2) - 0.1, "h": 180, "dx": 140, "size": 36})
# --- accident? ---
jfx.append({"fx": "BigLabel", "args": ["ACCIDENT?", 21.0, 58.6], "t0": W("accident") - 0.05, "t1": W("in", 2) + 0.1, "angle": -8, "size": 140, "col": POWER})
# --- 2025: unplugged from Russia's grid, joined Europe's ---
RED = "#d83a3a"
for code, n in [("EST", 3), ("LVA", 1), ("LTU", 1)]:
    word = ("estonia", 3) if code == "EST" else (("latvia", 1) if code == "LVA" else ("lithuania", 1))
    jfx.append({"fx": "HL", "args": [{"geom": code}], "t0": W(*word) - 0.05, "t1": W("joined") + 0.1, "col": RED, "alpha": 0.6})
jfx.append({"fx": "Tint", "args": [{"geom": ["RUS", "BLR"]}], "t0": W("russia's", 2) - 0.1, "t1": W("part", 2), "col": RED, "alpha": 0.4})
jfx.append({"fx": "BigLabel", "args": ["UNPLUGGED", 25.0, 58.3], "t0": W("unplugged"), "t1": W("joined") - 0.05, "angle": -8, "size": 120})
jfx.append({"fx": "HL", "args": [{"geom": ["EST", "LVA", "LTU"]}], "t0": W("joined"), "t1": W("so") + 0.3, "col": "#1f8fe0", "alpha": 0.7})
jfx.append({"fx": "Tint", "args": [{"geom": ["POL", "DEU", "FIN", "SWE", "DNK"]}], "t0": W("europe's") - 0.05, "t1": W("part", 2) + 0.3, "col": "#1f8fe0", "alpha": 0.35})
jfx.append({"fx": "Chip", "args": ["EUROPE'S GRID · FEB 2025"], "t0": W("europe's"), "t1": W("part", 2) - 0.1, "xy": [540, 560], "col": "#1f8fe0", "fg": "#ffffff", "size": 42})
# --- part of that link runs under this sea ---
for n in ["Estlink1", "Estlink2", "NordBalt"]:
    jfx.append(cable(n, W("link") - 0.1, W("but"), dur=0.6, w=8))
jfx.append({"fx": "LeaderLabel", "args": ["ESTLINK", 25.8, 59.9], "t0": W("runs"), "t1": W("so") - 0.1, "h": 160, "dx": 120, "size": 36})
jfx.append({"fx": "LeaderLabel", "args": ["NORDBALT", 18.5, 56.2], "t0": W("under", 2), "t1": W("so") - 0.1, "h": 160, "dx": -120, "size": 36})
# --- NATO patrols, US Marines with drones ---
for i, route in enumerate([[[14.5, 55.0], [16.5, 55.7], [18.5, 56.6]], [[20.0, 59.2], [21.5, 59.55], [23.0, 59.8]], [[19.0, 57.8], [19.8, 56.8], [20.3, 55.9]]]):
    jfx.append(ship(route, W("patrols") - 0.2 + 0.3 * i, 3.0, col="#9eeb25", icon=44, t1=W("but") + 0.2))
jfx.append({"fx": "Chip", "args": ["NATO · BALTIC SENTRY"], "t0": W("nato") - 0.05, "t1": W("us") - 0.1, "xy": [540, 560], "col": "#9eeb25", "size": 42})
jfx.append({"fx": "Pin", "args": [24.94, 60.17], "t0": W("us") - 0.1, "t1": W("but")})
jfx.append({"fx": "LeaderLabel", "args": ["US MARINES", 24.94, 60.17], "t0": W("marines") - 0.1, "t1": W("but") - 0.05, "h": 180, "dx": -140, "size": 40})
jfx.append({"fx": "Chip", "args": ["+ DRONES"], "t0": W("drones") - 0.05, "t1": W("but") - 0.05, "lonlat": [24.94, 60.17], "dy": 90, "size": 40})
# --- can't guard every meter: all cables back, one anchor finale ---
for i, n in enumerate(order):
    jfx.append(cable(n, W("guard") - 0.1 + 0.07 * i, None, dur=0.5))
jfx.append({"fx": "GridFinale", "args": [W("one", 1) - 0.05], "text": "ONE ANCHOR", "t_text": W("anchor", 3) - 0.05, "bg": "blur"})

spec = {
    "fps": 60, "size": [1080, 1920], "duration": DUR, "words": "words.json", "max_zoom": 8,
    "watermark": {"text": "WhatIf Atlas", "y": 230, "size": 30, "opacity": 0.55},
    "camera": [{"t": t, "lon": lo, "lat": la, "width_km": w, "roll": r, "tilt": ti} for t, lo, la, w, r, ti in cam],
    "regions": [],
    "elements": [
        {"type": "neon", "text": "BALTIC\nSEA", "t_in": W("baltic", 1) - 0.05, "t_out": W("shallow") - 0.1, "pos": [540, 700],
         "color": "#06EBFF", "size": 92, "angle": -8, "persp": 0.2},
    ],
    "jfx": jfx,
}
bad = [(it.get("fx"), it.get("t0"), it.get("t1")) for it in spec["jfx"] if it.get("t1") is not None and it.get("t0") is not None and it["t1"] <= it["t0"]]
bad += [(e["type"], e.get("t_in"), e.get("t_out")) for e in spec["elements"] if e.get("t_out") is not None and e["t_out"] <= e["t_in"]]
if bad:
    raise SystemExit(f"ERROR t1<=t0: {bad}")
json.dump(spec, open(os.path.join(D, "project.json"), "w"), indent=1, ensure_ascii=False)
print("duration", DUR, "words", len(words))
