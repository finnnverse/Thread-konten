"""Render single frames at given times -> contact sheet. usage: stills.py project.json out.jpg t1,t2,..."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.render import Engine
from PIL import Image, ImageDraw
from concurrent.futures import ProcessPoolExecutor
spec_path, out, ts = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(",")]
def one(t):
    eng = Engine(json.load(open(spec_path)), os.path.dirname(os.path.abspath(spec_path)))
    eng.prefetch(t, t + 0.02)
    return (np.clip(eng.frame(t), 0, 1) * 255).astype(np.uint8)
_e = Engine(json.load(open(spec_path)), os.path.dirname(os.path.abspath(spec_path)))
for _t in ts: _e.prefetch(_t, _t + 0.02)
with ProcessPoolExecutor(4) as ex:
    frames = list(ex.map(one, ts))
W, H = 300, 533; cols = min(8, len(ts)); rows = (len(ts) + cols - 1) // cols
sheet = Image.new("RGB", (cols * W, rows * H)); d = ImageDraw.Draw(sheet)
for i, (t, f) in enumerate(zip(ts, frames)):
    x, y = (i % cols) * W, (i // cols) * H
    sheet.paste(Image.fromarray(f).resize((W, H)), (x, y)); d.rectangle([x, y, x + 60, y + 16], fill="black"); d.text((x + 3, y + 2), f"{t:.1f}s", fill="yellow")
sheet.save(out, quality=88); print(out)
