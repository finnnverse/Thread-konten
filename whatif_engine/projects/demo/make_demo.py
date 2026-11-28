"""Builds demo project.json: every element type, scene order mirrors the reference for side-by-side tests."""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
text = ("What if two subs fired at once? The subs on patrol here are deep patrol boats, and each carries up to 24 missiles. "
        "Each missile can split into 10 warheads. That means hundreds of strikes in minutes. But the other side would see it coming. "
        "Their warning systems light up and they hit back right away. Even a perfect first strike would not stop it, "
        "because of the last resort system. Then comes the heavy missile, flying over the pole. "
        "It splits apart over the target, and no defense can catch it. All of that in under 30 minutes.")
words = text.split(); rate = 3.0; t = 0.15; W = []
for w in words:
    d = 0.17 + 0.034 * len(w.strip(",.?"))
    W.append([round(t, 2), round(t + d, 2), w]); t += d + (0.3 if w[-1] in ".?" else 0.03)
json.dump(W, open(os.path.join(D, "words.json"), "w"))
dur = round(W[-1][1] + 0.6, 2)
SUB = [158.5, 47.5]; RU = [95, 60]; US = [-98, 39]
spec = {
  "fps": 60, "size": [1080, 1920], "duration": dur, "words": "words.json",
  "watermark": {"text": "WhatIf Atlas", "y": 230, "size": 30, "opacity": 0.55},
  "regions": [
    {"id": "RUS", "style": "opaque", "color": "#0083FB", "island_color": "#3FD0FF"},
    {"id": "USA", "style": "tint", "t_in": 22.2, "fade": 0.7, "exclude_bbox": [-180, 15, -129, 75], "min_lat": 22}
  ],
  "camera": [
    {"t": 0.0, "lon": 159.6, "lat": 47.1, "width_km": 1150, "roll": -10, "tilt": 8},
    {"t": 0.3, "lon": 157.5, "lat": 47.6, "width_km": 1650, "roll": -9, "tilt": 8},
    {"t": 1.25, "lon": 112, "lat": 50, "width_km": 9500, "roll": 2, "tilt": 12},
    {"t": 3.3, "lon": 104, "lat": 50, "width_km": 10500, "roll": -2, "tilt": 12},
    {"t": 4.1, "lon": 150, "lat": 49, "width_km": 3200, "roll": -6, "tilt": 9},
    {"t": 4.7, "lon": 157, "lat": 47.5, "width_km": 1700, "roll": -8, "tilt": 8},
    {"t": 7.4, "lon": 157.5, "lat": 47.2, "width_km": 1550, "roll": -11, "tilt": 8},
    {"t": 13.8, "lon": 157.6, "lat": 47.1, "width_km": 1500, "roll": -12, "tilt": 8},
    {"t": 14.6, "lon": 156, "lat": 48, "width_km": 1800, "roll": -10, "tilt": 9},
    {"t": 16.3, "lon": 100, "lat": 47, "width_km": 11500, "roll": 2, "tilt": 13},
    {"t": 18.0, "lon": 96, "lat": 52, "width_km": 9000, "roll": -1, "tilt": 12},
    {"t": 20.3, "lon": 92, "lat": 58, "width_km": 6500, "roll": -4, "tilt": 11},
    {"t": 22.7, "lon": -108, "lat": 45, "width_km": 8200, "roll": 3, "tilt": 11},
    {"t": 24.6, "lon": 95, "lat": 58, "width_km": 5600, "roll": -3, "tilt": 10},
    {"t": 27.3, "lon": 92, "lat": 58, "width_km": 6200, "roll": 2, "tilt": 10},
    {"t": 28.0, "lon": 165, "lat": 66, "width_km": 2600, "roll": 6, "tilt": 8},
    {"follow": "heavy", "t0": 28.6, "t1": 31.4, "step": 0.7, "width_km": 2600, "roll": 9, "tilt": 8, "lead": [6, -3]},
    {"t": 32.4, "lon": -98, "lat": 45, "width_km": 6200, "roll": -2, "tilt": 10},
    {"t": dur, "lon": -92, "lat": 42, "width_km": 3600, "roll": -6, "tilt": 8}
  ],
  "elements": [
    {"type": "sticker", "sprite": "submarine", "at": [158.2, 47.0], "t_in": -1, "t_out": 15.2, "size": 340, "angle": -28, "map_scale": 0.75},
    {"type": "sticker", "sprite": "submarine", "at": [159.0, 47.9], "t_in": -1, "t_out": 15.2, "size": 340, "angle": -28, "map_scale": 0.75},
    {"type": "ring", "at": SUB, "t0": 0.4, "t1": 1.3, "size": 90},
    {"type": "trail", "from": SUB, "to": [95, 60], "t0": 1.25, "dur": 1.5, "count": 6, "spread": 7, "to_spread": 1.6, "bulge": 0.16,
     "stagger": 0.07, "impact": True, "impact_out": 4.4, "head_size": 60, "width": 4},
    {"type": "neon", "text": "DEEP PATROL\nSUBMARINES", "t_in": 5.45, "t_out": 6.9, "pos": [560, 760], "color": "#06EBFF",
     "size": 84, "angle": -14, "persp": 0.22},
    {"type": "hero", "sprite": "rocket", "size": 800, "t_in": 7.55, "t_out": 10.45, "rise": 260, "flame": True,
     "mult": "x 24", "mult_t": 7.95, "vlabel": "MISSILE-X", "vlabel_t": 8.4, "vlabel_size": 76, "mult_size": 120, "mult_dx": 330, "pos": [430, 900]},
    {"type": "hero", "sprite": "warhead_bus", "size": 760, "t_in": 10.55, "t_out": 13.55, "pos": [430, 900], "rise": 0,
     "callout": {"text": "x 10 warheads", "t": 11.9, "size": 60}},
    {"type": "trail", "from": SUB, "to": [100, 58], "t0": 14.6, "dur": 1.8, "count": 7, "spread": 6, "to_spread": 2.2, "bulge": 0.2,
     "stagger": 0.09, "width": 5, "head_size": 70, "color": "#E8FBFF"},
    {"type": "bursts", "region": "RUS", "n": 14, "t0": 16.5, "interval": 0.17, "t1": 19.4, "size": 140, "seed": 4, "lat_range": [48, 66]},
    {"type": "card", "t_in": 19.5, "t_out": 20.05, "pos": [560, 560], "size": 330, "blink": True, "label": "WARNING"},
    {"type": "neon", "text": "TOTAL W#R", "t_in": 20.15, "t_out": 20.95, "pos": [560, 640], "color": "#F5030A", "glow": "#B2413D",
     "size": 74, "weight": 800, "tracking": 0.08},
    {"type": "trail", "from": [60, 57], "to": [-100, 42], "t0": 20.9, "dur": 2.0, "count": 5, "spread": 5, "bulge": -0.12,
     "stagger": 0.1, "head_size": 64, "width": 4, "impact": True, "impact_out": 23.8, "impact_size": 110},
    {"type": "sticker", "sprite": "tombstone", "at": [80, 58], "t_in": 24.7, "t_out": 27.4, "size": 300, "follow_roll": False},
    {"type": "sticker", "sprite": "tombstone", "at": [95, 60], "t_in": 24.85, "t_out": 27.4, "size": 300, "follow_roll": False},
    {"type": "sticker", "sprite": "tombstone", "at": [110, 58], "t_in": 25.0, "t_out": 27.4, "size": 300, "follow_roll": False},
    {"type": "neon", "text": "THE LAST RESORT SYSTEM", "t_in": 25.6, "t_out": 26.9, "pos": [540, 640], "color": "#FFDF0A",
     "size": 70, "wave": 0.06, "tracking": 0.22},
    {"type": "tracked", "id": "heavy", "from": [165, 66], "to": [-88, 46], "t0": 28.3, "dur": 4.4, "ease": "linear", "size": 430,
     "top": {"text": "RS-X HEAVY", "t": 28.8, "size": 62, "gap": 80}, "bottom": {"text": "TITAN", "t": 29.6, "size": 58, "gap": 70}, "drop_t": 31.2},
    {"type": "rain", "t0": 32.0, "t1": 33.5, "box_geo": [[-122, 49], [-75, 30]], "n": 30, "angle": -30},
    {"type": "bursts", "region": "USA", "exclude_bbox": [-180, 15, -129, 75], "n": 14, "t0": 32.9, "interval": 0.08, "t1": 36.5, "size": 95, "seed": 7, "lat_range": [27, 48]},
    {"type": "sticker", "sprite": "radar", "at": [-100, 39], "t_in": 34.1, "t_out": dur + 1, "size": 300, "follow_roll": False},
    {"type": "sticker", "sprite": "bubble", "text": "Everything is fine here!", "at": [-84, 42], "t_in": 34.5, "t_out": dur + 1,
     "size": 300, "wobble": 4, "follow_roll": False}
  ]
}
json.dump(spec, open(os.path.join(D, "project.json"), "w"), indent=1)
print("duration", dur, "words", len(W))
