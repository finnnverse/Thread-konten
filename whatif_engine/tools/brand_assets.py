"""Channel art in the video style: satellite globe avatar, YouTube banner, Facebook cover.
usage: python3 tools/brand_assets.py "WhatIf Atlas" "Maps that answer the question: what if?" outdir"""
import sys, os, math, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw, ImageFilter
from engine.tiles import TileSource
from engine.destreak import CleanTiles
from engine.geo import Countries
from engine.maprender import MapRenderer, LutGrade
from engine.camera import Camera
from engine.fx import static_glow_text, glow_rgba
from engine.text import font, blit_sub
from engine import journey_fx as J

NAME, TAG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(OUT, exist_ok=True)
raw = TileSource(os.path.join(ROOT, "cache/s2_2016"))
tiles = CleanTiles(raw, os.path.join(ROOT, "cache/s2_clean"), land=Countries(os.path.join(ROOT, "data"), "50m"))
grade = LutGrade()

# ---------- equirectangular texture from z4 mercator tiles ----------
z = 4; n = 1 << z
tiles.prefetch([(z, x, y) for x in range(n) for y in range(n)])
merc = tiles.mosaic(z, 0, 0, n - 1, n - 1)                       # 4096x4096 mercator
merc = (grade(merc) * 255).astype(np.uint8)
EW, EH = 4096, 2048
lon = np.linspace(-180, 180, EW, endpoint=False) + 180 / EW
lat = np.linspace(85, -85, EH)
my = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * merc.shape[0]
mx = (lon + 180) / 360 * merc.shape[1]
MX, MY = np.meshgrid(mx.astype(np.float32), my.astype(np.float32))
equi = cv2.remap(merc, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def globe(size, lon0=50, lat0=22, tilt_light=True):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    x = (xx - size / 2 + 0.5) / (size / 2); y = -(yy - size / 2 + 0.5) / (size / 2)
    r2 = x * x + y * y; inside = r2 <= 1.0
    zc = np.sqrt(np.clip(1 - r2, 0, 1))
    la0, lo0 = math.radians(lat0), math.radians(lon0)
    latp = np.arcsin(np.clip(zc * math.sin(la0) + y * math.cos(la0), -1, 1))
    lonp = lo0 + np.arctan2(x, zc * math.cos(la0) - y * math.sin(la0))
    u = ((np.degrees(lonp) + 180) % 360) / 360 * EW; v = (85 - np.degrees(latp)) / 170 * EH
    img = cv2.remap(equi, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32) / 255
    shade = (0.55 + 0.45 * np.clip(zc * 0.8 + (x * -0.35 + y * 0.35), 0, 1))[..., None]
    rim = np.clip((r2 - 0.82) / 0.18, 0, 1)[..., None] * np.array([0.25, 0.75, 1.0]) * 0.55
    img = np.clip(img * shade + rim, 0, 1)
    a = np.clip((1.0 - np.sqrt(r2)) * size / 2.5, 0, 1)
    return np.concatenate([img, a[..., None]], 2).astype(np.float32)


def bg(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / W, (yy - H / 2) / H)
    c0, c1 = np.array([0.05, 0.25, 0.32]), np.array([0.01, 0.07, 0.10])
    return (c0 * (1 - np.clip(r * 1.6, 0, 1))[..., None] + c1 * np.clip(r * 1.6, 0, 1)[..., None]).astype(np.float32)


def save(arr, name, size=None, q=95):
    im = Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8))
    if size: im = im.resize(size, Image.LANCZOS)
    p = os.path.join(OUT, name); im.save(p, quality=q) if name.endswith(".jpg") else im.save(p); print(p, im.size)


# ---------- 1) avatar 800x800 (works for YT 98px circle and FB 176px circle) ----------
S = 800; av = bg(S, S)
g = globe(640, 52, 24)
blit_sub(av, g, S / 2, S / 2)
q = static_glow_text("?", 300, "#FFDF0A", family="jost", weight=800, glow="#FFB000")
blit_sub(av, q, S / 2 + 6, S / 2 - 20)
ring = np.zeros((S, S), np.float32); cv2.circle(ring, (S // 2, S // 2), 330, 1.0, 6, cv2.LINE_AA)
from engine.text import blit
blit(av, glow_rgba(ring, "#06EBFF", s1=6, s2=22), 0, 0)
save(av, "profil_800x800.png")
save(av, "profil_preview_98px.png", (98, 98))

# ---------- 2) map backdrop (wide satellite world, graded) ----------
def map_backdrop(W, H, lon_c=55, lat_c=28, width_km=19000):
    cam = Camera([dict(t=0, lon=lon_c, lat=lat_c, width_km=width_km, roll=0, tilt=0)], W, H)
    mr = MapRenderer(tiles, W, H, max_zoom=6); M, s = cam.matrix(0)
    tiles.prefetch(mr.tiles_for(M, s))
    img = mr.base(M, s)
    pil = Image.fromarray((img * 255).astype(np.uint8)).convert("RGBA")
    P = lambda lo, la: tuple(float(v[0]) for v in cam.geo_to_screen(0, lo, la))
    fx = [J.NeonArc((56.4, 26.5), (121.5, 31.2), 0, dur=0.01, bulge=0.22, w=7),
          J.NeonArc((56.4, 26.5), (-74, 40.7), 0, dur=0.01, bulge=-0.15, w=7, col="#ffd84a"),
          J.NeonArc((32.5, 30.0), (4.5, 51.9), 0, dur=0.01, bulge=0.2, w=6, col="#9eeb25")]
    pil = J.draw_all(pil, fx, 5.0, P)
    return np.asarray(pil.convert("RGB")).astype(np.float32) / 255


def title_block(img, cx, cy, scale):
    t1 = static_glow_text(NAME.upper(), int(150 * scale), "#FFFFFF", family="jost", weight=800, tracking=0.06, glow="#06EBFF", s1=6 * scale, s2=26 * scale)
    blit_sub(img, t1, cx, cy - 40 * scale)
    t2 = static_glow_text(TAG, int(54 * scale), "#7FF3FF", family="jost", weight=500, tracking=0.02, s1=3, s2=10, a2=0.35)
    blit_sub(img, t2, cx, cy + 95 * scale)


# YouTube banner 2560x1440, everything important inside central 1235x338 (strictest safe area)
W, H = 2560, 1440
yb = map_backdrop(W, H)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
band = np.exp(-((yy - H / 2) / 260) ** 2)[..., None]                  # darken centre band for text contrast
yb = yb * (1 - 0.55 * band)
title_block(yb, W / 2, H / 2, 0.86)
save(yb, "youtube_banner_2560x1440.jpg")
guide = (np.clip(yb, 0, 1) * 255).astype(np.uint8).copy()
cv2.rectangle(guide, (W // 2 - 1235 // 2, H // 2 - 338 // 2), (W // 2 + 1235 // 2, H // 2 + 338 // 2), (255, 60, 60), 4)
cv2.rectangle(guide, (W // 2 - 1546 // 2, H // 2 - 423 // 2), (W // 2 + 1546 // 2, H // 2 + 423 // 2), (255, 200, 0), 3)
Image.fromarray(guide).resize((1280, 720)).save(os.path.join(OUT, "cek_zona_aman_banner.jpg"), quality=88)

# Facebook cover: 851x315 display, export 2x = 1702x630; keep bottom-left (profile overlap) clear
W, H = 1702, 630
fb = map_backdrop(W, H, lon_c=60, lat_c=30, width_km=17000)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
band = np.exp(-((yy - H * 0.45) / 170) ** 2)[..., None]
fb = fb * (1 - 0.55 * band)
title_block(fb, W * 0.56, H * 0.45, 0.8)
save(fb, "facebook_cover_1702x630.jpg")
