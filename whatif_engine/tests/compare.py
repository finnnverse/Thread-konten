"""Side-by-side comparison: reference vs ours at matched moments. usage: compare.py ours.mp4 ref.mp4 out.jpg"""
import sys, subprocess, os
from PIL import Image, ImageDraw, ImageFont
ours, ref, out = sys.argv[1:4]
PAIRS = [  # (label, ref_t, ours_t)
 ("1 Pembuka: kapal selam + caption", 0.25, 0.25), ("2 Whip zoom-out + jejak", 2.0, 2.0), ("3 Ledakan di ujung jejak", 3.6, 3.3),
 ("4 Label neon cyan 3D", 6.3, 6.2), ("5 Objek hero + latar blur", 8.8, 8.8), ("6 Callout x14 / x10", 12.7, 12.6),
 ("7 Ledakan menyebar (zoom-out)", 19.5, 18.6), ("8 Kartu HUD peringatan", 23.2, 20.0), ("9 Label neon merah", 25.6, 20.45),
 ("10 Isian merah AS", 29.8, 23.1), ("11 Nisan + label kuning", 35.5, 26.0), ("12 Rudal + label menempel", 48.4, 29.9),
 ("13 Hujan garis kuning", 52.3, 32.5), ("14 Radar + gelembung (finale)", 56.0, 35.8)]
font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "..", "fonts", "Manrope[wght].ttf"), 22)
W, H = 300, 533; cols = 7
rows = (len(PAIRS) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (2 * W + 12), rows * (H + 40)), (18, 18, 18)); d = ImageDraw.Draw(sheet)
tmp = out + ".tmp.png"
for i, (lab, rt, ot) in enumerate(PAIRS):
    cx, cy = (i % cols) * (2 * W + 12), (i // cols) * (H + 40)
    for j, (v, t) in enumerate(((ref, rt), (ours, ot))):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", v, "-frames:v", "1", tmp], check=True)
        sheet.paste(Image.open(tmp).convert("RGB").resize((W, H)), (cx + j * W, cy + 34))
        d.text((cx + j * W + 6, cy + 40), ("REF " if j == 0 else "KITA ") + f"{t}s", fill=(255, 220, 0), font=font)
    d.text((cx + 4, cy + 4), lab, fill=(255, 255, 255), font=font)
os.remove(tmp); sheet.save(out, quality=88); print(out)
