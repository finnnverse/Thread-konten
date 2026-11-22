"""v2 textures, closer to the reference look: real satellite land (EOX Sentinel-2 cloudless 2016, CC BY 4.0)
at every zoom + Natural Earth ocean-bottom relief for the sea, graded vivid (rich greens, golden desert, luminous teal sea)."""
import math, os, sys, urllib.request, concurrent.futures as cf
import numpy as np, cv2, shapefile
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
NE, OUT, CACHE = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
URL = 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg'


def mdeg(lat): return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def tile(z, x, y):
    p = f'{CACHE}/{z}_{x}_{y}.jpg'
    for _ in range(5):
        if os.path.exists(p) and os.path.getsize(p) > 0: break
        try:
            req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={'User-Agent': 'map-render/1.0'})
            open(p, 'wb').write(urllib.request.urlopen(req, timeout=40).read())
        except Exception as e: print('retry', z, x, y, e, flush=True)
    return np.asarray(Image.open(p).convert('RGB'))


def mosaic(z, lon0, lon1, lat0, lat1):
    n = 2 ** z
    tx0, tx1 = int((lon0 + 180) / 360 * n), int((lon1 + 180) / 360 * n)
    ty = lambda lat: int((1 - math.radians(mdeg(lat)) / math.pi) / 2 * n)
    ty0, ty1 = max(0, ty(lat1)), min(n - 1, ty(lat0))
    jobs = [(x, y) for y in range(ty0, ty1 + 1) for x in range(tx0, tx1 + 1)]
    with cf.ThreadPoolExecutor(8) as ex: tiles = list(ex.map(lambda q: tile(z, *q), jobs))
    img = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 3), np.uint8)
    for (x, y), t in zip(jobs, tiles): img[(y - ty0) * 256:(y - ty0 + 1) * 256, (x - tx0) * 256:(x - tx0 + 1) * 256] = t
    ppd = 256 * n / 360; X0 = tx0 * 360 / n - 180; Yt = math.degrees(math.pi * (1 - 2 * ty0 / n))
    return img, X0, Yt, ppd


# ---- land mask from Natural Earth 10m land (rasterised in the texture's mercator grid)
_land = None
def land_mask(h, w, X0, Yt, ppd):
    global _land
    if _land is None:
        sf = shapefile.Reader(NE + '/ne_10m_land.shp'); _land = []
        for s in sf.shapes():
            pp = list(s.parts) + [len(s.points)]
            for i in range(len(pp) - 1): _land.append(np.asarray(s.points[pp[i]:pp[i + 1]]))
    m = np.zeros((h, w), np.uint8)
    X1 = X0 + w / ppd; Yb = Yt - h / ppd
    for r in _land:
        if r[:, 0].max() < X0 or r[:, 0].min() > X1: continue
        Y = np.degrees(np.log(np.tan(np.pi / 4 + np.radians(np.clip(r[:, 1], -85, 85)) / 2)))
        if Y.max() < Yb or Y.min() > Yt: continue
        px = np.stack([(r[:, 0] - X0) * ppd, (Yt - Y) * ppd], 1)
        cv2.fillPoly(m, [np.round(px * 8).astype(np.int32)], 255, cv2.LINE_AA, 3)
    return m


_lakes = None
def lake_mask(h, w, X0, Yt, ppd):
    global _lakes
    if _lakes is None:
        sf = shapefile.Reader(NE + '/ne_10m_lakes.shp'); _lakes = []
        for s_ in sf.shapes():
            pp = list(s_.parts) + [len(s_.points)]
            for i in range(len(pp) - 1): _lakes.append(np.asarray(s_.points[pp[i]:pp[i + 1]]))
    m = np.zeros((h, w), np.uint8); X1 = X0 + w / ppd; Yb = Yt - h / ppd
    for r in _lakes:
        if r[:, 0].max() < X0 or r[:, 0].min() > X1: continue
        Y = np.degrees(np.log(np.tan(np.pi / 4 + np.radians(np.clip(r[:, 1], -85, 85)) / 2)))
        if Y.max() < Yb or Y.min() > Yt: continue
        px = np.stack([(r[:, 0] - X0) * ppd, (Yt - Y) * ppd], 1)
        cv2.fillPoly(m, [np.round(px * 8).astype(np.int32)], 255, cv2.LINE_AA, 3)
    k = max(3, int(ppd * .03) | 1)
    m = cv2.dilate(m, np.ones((k, k), np.uint8))
    return cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), max(1, k / 3))


# ---- ocean-bottom relief, resampled to the same grid
OB = None
def ocean(h, w, X0, Yt, ppd):
    global OB
    if OB is None: OB = np.asarray(Image.open(NE + '/OB_50M/OB_50M.tif').convert('L')).astype(np.float32)
    oh, ow = OB.shape
    xs = (X0 + (np.arange(w) + .5) / ppd + 180) / 360 * ow - .5
    Ys = Yt - (np.arange(h) + .5) / ppd
    lats = np.degrees(2 * np.arctan(np.exp(np.radians(Ys))) - np.pi / 2)
    ys = (90 - lats) / 180 * oh - .5
    return cv2.remap(OB, np.tile(xs.astype(np.float32), (h, 1)), np.repeat(ys.astype(np.float32)[:, None], w, 1), cv2.INTER_LINEAR)


def grade(img, X0, Yt, ppd, coast_px):
    h, w = img.shape[:2]
    a = img.astype(np.float32) / 255
    # --- land: vivid natural colour
    lum = a @ np.array([.3, .59, .11], np.float32)
    sat = 1.30
    land = lum[..., None] + (a - lum[..., None]) * sat
    land = np.clip((land - .5) * 1.10 + .5, 0, 1)
    # tone: bright deserts -> warm golden tan (not neon), vegetation -> rich green
    hi = np.clip((lum - .55) / .3, 0, 1)[..., None]
    land = land * (1 - .22 * hi) + np.array([.80, .62, .36]) * .22 * hi
    veg = np.clip((a[..., 1] - a[..., 0]) * 8 + .1, 0, 1)[..., None]
    land = land * (1 - .3 * veg) + land * np.array([.85, 1.10, .75]) * .3 * veg
    land = np.clip(land * np.array([1.0, .97, .88]), 0, 1)
    # --- sea: luminous teal with relief + brighter shelves near the coast
    m = land_mask(h, w, X0, Yt, ppd).astype(np.float32) / 255
    ob = ocean(h, w, X0, Yt, ppd) / 255
    relief = (ob - cv2.GaussianBlur(ob, (0, 0), max(2, ppd * .3))) * 3.0
    dist = cv2.distanceTransform((m < .5).astype(np.uint8), cv2.DIST_L2, 5) / max(coast_px, 1)
    shelf = np.exp(-dist * 1.2)
    deep = np.array([.05, .36, .48]); light = np.array([.16, .70, .74])
    sea = deep + (light - deep) * (shelf[..., None] * .85) + relief[..., None] * .5
    sea += (ob[..., None] - .6) * .35
    # keep satellite detail in shallow coastal water (lagoons, river mouths)
    sea = np.clip(sea, 0, 1)
    mm = cv2.GaussianBlur(m, (0, 0), 1.0)[..., None]
    out = land * mm + sea * (1 - mm)
    # inland water (Nile, lakes): satellite dark water on land -> teal
    wat = (np.clip((.30 - lum) / .10, 0, 1) * np.clip((a[..., 2] - a[..., 1] + .005) / .02, 0, 1) * np.clip((a[..., 2] - a[..., 0]) / .03, 0, 1))[..., None] * mm
    # lakes (Lake Nasser etc.): inside the Natural Earth lake outline, dark pixels are water
    lk = lake_mask(h, w, X0, Yt, ppd)
    lw = (lk * np.clip((.45 - lum) / .12, 0, 1))[..., None]
    wat = np.maximum(wat, lw)
    out = out * (1 - wat) + (light * .85) * wat
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def build(name, z, lon0, lon1, lat0, lat1, coast_deg):
    if os.path.exists(f'{OUT}/{name}.png'): return
    img, X0, Yt, ppd = mosaic(z, lon0, lon1, lat0, lat1)
    g = grade(img, X0, Yt, ppd, coast_deg * ppd)
    Image.fromarray(g).save(f'{OUT}/{name}.png'); open(f'{OUT}/{name}.txt', 'w').write(f'{X0} {Yt} {ppd}\n')
    print(name, g.shape, flush=True)


if __name__ == '__main__':
    build('base', 6, -60, 125, -50, 70, 1.2)
    build('p1_egypt_z8', 8, 23.5, 38.0, 20.5, 32.8, .3)
    build('p2_delta_z10', 10, 29.0, 35.2, 27.3, 31.9, .08)
    build('p2_aswan_z10', 10, 30.8, 33.6, 21.4, 24.4, .08)
    build('p3_cairo_z13', 13, 30.95, 31.50, 29.85, 30.20, .02)
    build('p3_suez_z12', 12, 32.05, 32.70, 29.85, 31.35, .03)
    build('p3_aswan_z12', 12, 32.70, 33.05, 23.80, 24.20, .03)
    build('p3_abusimbel_z13', 13, 31.52, 31.75, 22.26, 22.42, .02)
