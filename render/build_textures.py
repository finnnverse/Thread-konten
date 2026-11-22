"""Build Mercator textures: Natural Earth base (graded, 'Opsi 2') + EOX Sentinel-2 patches colour-matched to it."""
import math, os, sys, urllib.request, concurrent.futures as cf
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
NE = sys.argv[1]; OUT = sys.argv[2]; CACHE = sys.argv[3]
os.makedirs(OUT, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
def mdeg(lat): return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
def ilat(y): return math.degrees(2 * math.atan(math.exp(math.radians(y))) - math.pi / 2)

def grade_ne(a):
    a = a.astype(np.float32); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sea = np.clip((b - r - 25) / 40, 0, 1)[..., None]
    lum = (0.3 * r + 0.59 * g + 0.11 * b)[..., None] / 255
    deep = np.clip(1 - (b[..., None] - 140) / 110, 0, 1)
    seac = np.array([18, 95, 118]) * (0.75 + 0.5 * lum) * (1 - 0.45 * deep)
    land = np.stack([r * 0.60, g * 0.60, b * 0.22], -1)
    land = (land - 95.0) * 1.25 + 95.0
    land = land * 0.85 + np.array([8, 6, 0])
    return np.clip(land * (1 - sea) + seac * sea, 0, 255).astype(np.uint8)

# ---- base texture
LON0, LON1, LAT0, LAT1, PPD = -60.0, 125.0, -50.0, 70.0, 60
if not os.path.exists(OUT + '/base.png'):
    R = Image.open(NE + '/NE1_HR_LC_SR_W_DR.tif').convert('RGB')
    x0, x1 = int((LON0 + 180) * 60), int((LON1 + 180) * 60)
    y0, y1 = int((90 - LAT1) * 60), int((90 - LAT0) * 60)
    eq = np.asarray(R.crop((x0, y0, x1, y1))); del R
    Yt, Yb = mdeg(LAT1), mdeg(LAT0)
    H = int((Yt - Yb) * PPD); W = eq.shape[1]
    ys = Yt - (np.arange(H) + 0.5) / PPD
    lats = np.degrees(2 * np.arctan(np.exp(np.radians(ys))) - np.pi / 2)
    rows = ((LAT1 - lats) * 60 - 0.5).astype(np.float32)
    mx = np.tile(np.arange(W, dtype=np.float32), (H, 1)); my = np.repeat(rows[:, None], W, 1)
    merc = cv2.remap(eq, mx, my, cv2.INTER_LINEAR)
    base = grade_ne(merc)
    Image.fromarray(base).save(OUT + '/base.png')
    open(OUT + '/base.txt', 'w').write(f'{LON0} {Yt} {PPD}\n')
    print('base', base.shape, flush=True)
base = np.asarray(Image.open(OUT + '/base.png'))
bX0, bYt, bP = map(float, open(OUT + '/base.txt').read().split())

URL = 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg'
def tile(z, x, y):
    p = f'{CACHE}/{z}_{x}_{y}.jpg'
    for _ in range(4):
        if os.path.exists(p) and os.path.getsize(p) > 0: break
        try:
            req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={'User-Agent': 'map-render/1.0'})
            open(p, 'wb').write(urllib.request.urlopen(req, timeout=40).read())
        except Exception as e:
            print('retry', z, x, y, e, flush=True)
    return np.asarray(Image.open(p).convert('RGB'))

def patch(name, z, lon0, lon1, lat0, lat1):
    if os.path.exists(f'{OUT}/{name}.png'): return
    n = 2 ** z
    tx0, tx1 = int((lon0 + 180) / 360 * n), int((lon1 + 180) / 360 * n)
    def ty(lat): return int((1 - math.radians(mdeg(lat)) / math.pi) / 2 * n)
    ty0, ty1 = ty(lat1), ty(lat0)
    jobs = [(x, y) for y in range(ty0, ty1 + 1) for x in range(tx0, tx1 + 1)]
    with cf.ThreadPoolExecutor(8) as ex: tiles = list(ex.map(lambda q: tile(z, *q), jobs))
    Wt, Ht = (tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256
    img = np.zeros((Ht, Wt, 3), np.uint8)
    for (x, y), t in zip(jobs, tiles): img[(y - ty0) * 256:(y - ty0 + 1) * 256, (x - tx0) * 256:(x - tx0 + 1) * 256] = t
    ppd = 256 * n / 360
    X0 = tx0 * 360 / n - 180
    Yt = math.degrees(math.pi * (1 - 2 * ty0 / n))
    # colour-match to base (Reinhard in Lab), using base resampled to same area
    h, w = img.shape[:2]
    mx = ((X0 + (np.arange(w) + 0.5) / ppd) - bX0) * bP
    my = (bYt - (Yt - (np.arange(h) + 0.5) / ppd)) * bP
    ref = cv2.remap(base, np.tile(mx.astype(np.float32), (h, 1)), np.repeat(my.astype(np.float32)[:, None], w, 1), cv2.INTER_LINEAR)
    src_rgb = img.astype(np.float32)
    a = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32); b = cv2.cvtColor(ref, cv2.COLOR_RGB2LAB).astype(np.float32)
    # match the smooth (low-frequency) colour and keep satellite detail
    k = max(3, int(ppd * 0.25) | 1)
    lowa = cv2.GaussianBlur(a, (0, 0), k / 3); lowb = cv2.GaussianBlur(b, (0, 0), k / 3)
    out = a.copy()
    sa = a.reshape(-1, 3).std(0) + 1e-3; sb = b.reshape(-1, 3).std(0) + 1e-3
    out = lowb + (a - lowa) * np.array([1.15, 1.0, 1.0])  # base colour + satellite detail
    out = np.clip(out, 0, 255).astype(np.uint8)
    img = cv2.cvtColor(out, cv2.COLOR_LAB2RGB).astype(np.float32)
    o = cv2.cvtColor(cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_LAB2RGB), cv2.COLOR_RGB2LAB).astype(np.float32)  # noop guard
    L8 = a[..., 0]; R0, G0, B0 = [src_rgb[..., i] for i in range(3)]
    wat = np.clip((105 - L8) / 20, 0, 1) * np.clip((B0 - R0 + 2) / 8, 0, 1) * np.clip((B0 - .75 * G0) / 6, 0, 1)
    wat = cv2.GaussianBlur(wat.astype(np.float32), (0, 0), 1.2)[..., None]
    teal = np.array([20, 92, 115], np.float32) * (0.75 + L8[..., None] / 160)
    img = np.clip(img * (1 - wat) + teal * wat, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(f'{OUT}/{name}.png')
    open(f'{OUT}/{name}.txt', 'w').write(f'{X0} {Yt} {ppd}\n')
    print(name, img.shape, len(jobs), 'tiles', flush=True)

patch('p1_egypt_z8', 8, 23.5, 38.0, 20.5, 32.8)
patch('p2_delta_z10', 10, 29.0, 35.2, 27.3, 31.9)
patch('p2_aswan_z10', 10, 30.8, 33.6, 21.4, 24.4)
patch('p3_cairo_z13', 13, 30.95, 31.50, 29.85, 30.20)
patch('p3_suez_z12', 12, 32.05, 32.70, 29.85, 31.35)
patch('p3_aswan_z12', 12, 32.70, 33.05, 23.80, 24.20)
patch('p3_abusimbel_z13', 13, 31.52, 31.75, 22.26, 22.42)
