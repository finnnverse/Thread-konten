"""Remove Sentinel-2 cloudless-2016 orbit streaks (thin bright haze bands along the satellite track).

Detector: a streak is (1) thin and brighter than its surroundings ACROSS the track and
(2) long and straight ALONG the track. Track angle from the meridian for a sun-synchronous
orbit (inclination 98.6 deg) at latitude phi: alpha = asin(cos(98.6)/cos(phi)) -- Mercator is
conformal so the angle holds on the map. Snow ridges / coasts are not long-straight along
alpha, so they survive.
"""
import math, os
import numpy as np
import cv2
from PIL import Image
from .geo import unmerc

INCL = math.radians(98.6)


def track_angle(lat):
    v = abs(math.cos(INCL)) / max(0.2, math.cos(math.radians(lat)))
    return math.degrees(math.asin(min(1.0, v)))   # degrees clockwise from north ("/" streaks)


def line_kernel(length, angle_deg):
    """binary line SE; angle measured clockwise from image 'up'."""
    L = int(length) | 1; k = np.zeros((L, L), np.uint8); c = L // 2
    a = math.radians(angle_deg)
    dx, dy = math.sin(a) * c, -math.cos(a) * c
    cv2.line(k, (int(round(c - dx)), int(round(c - dy))), (int(round(c + dx)), int(round(c + dy))), 1, 1)
    return k


def _line_mean(length, angle_deg):
    k = line_kernel(length, angle_deg).astype(np.float32); return k / k.sum()


def destreak(rgb_u8, lat, px_per_km, strength=1.0, debug=False):
    img = rgb_u8.astype(np.float32) / 255.0
    L = img @ np.array([0.30, 0.59, 0.11], np.float32)
    w = max(7, int(round(10.0 * px_per_km)) | 1)          # streaks are <= ~8 km wide
    ln = max(41, int(round(120.0 * px_per_km)) | 1)        # consistent along ~120 km (dashed ok)
    mx, mn = img.max(2), img.min(2); sat = (mx - mn) / np.maximum(mx, 1e-3)
    grey = np.clip((0.50 - sat) / 0.25, 0, 1)
    a0 = track_angle(lat)
    # 1) find the track angle on a 1/4-res copy (cheap)
    q = 4; Ls = cv2.resize(L, (L.shape[1] // q, L.shape[0] // q), interpolation=cv2.INTER_AREA)
    gs = cv2.resize(grey, (L.shape[1] // q, L.shape[0] // q), interpolation=cv2.INTER_AREA)
    ws, lns = max(3, (w // q) | 1), max(15, (ln // q) | 1); best = None
    for ang in np.arange(a0 - 4, a0 + 12.1, 1.5):
        th_s = np.clip(Ls - cv2.morphologyEx(Ls, cv2.MORPH_OPEN, line_kernel(ws, ang + 90)), 0, 1) * gs
        an = cv2.filter2D(th_s, -1, _line_mean(lns, ang)) - cv2.filter2D(th_s, -1, _line_mean(lns, ang + 90))
        sc = np.percentile(an, 99.9)
        if best is None or sc > best[0]:
            best = (sc, ang)
    ang = best[1]
    # 2) full-res detection at that angle only
    perp = line_kernel(w, ang + 90)
    th = np.clip(L - cv2.morphologyEx(L, cv2.MORPH_OPEN, perp), 0, 1) * grey
    anis = cv2.filter2D(th, -1, _line_mean(ln, ang), borderType=cv2.BORDER_REFLECT) - \
           cv2.filter2D(th, -1, _line_mean(ln, ang + 90), borderType=cv2.BORDER_REFLECT)
    # thin, bright, grey pixel lying on a line that is clearly brighter along-track than across
    m = np.clip((anis - 0.025) / 0.03, 0, 1) * np.clip((th - 0.05) / 0.06, 0, 1)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    m = cv2.GaussianBlur(m, (0, 0), 1.5) * strength
    bgc = np.stack([cv2.morphologyEx(img[..., i], cv2.MORPH_OPEN, perp) for i in range(3)], 2)
    bgc = cv2.GaussianBlur(bgc, (0, 0), 1.0)
    out = img * (1 - m[..., None]) + bgc * m[..., None]
    out = deband(out, ang, px_per_km)
    out = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    return (out, m, ang) if debug else out


def deband(img, ang, px_per_km, length_km=500, max_gain=0.12):
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    gain = _deband_gain(small, ang, px_per_km / 4, length_km, max_gain)
    gain = cv2.resize(gain, (w, h), interpolation=cv2.INTER_LINEAR)
    return img * gain[..., None]


def _deband_gain(img, ang, px_per_km, length_km, max_gain):
    """Remove brightness steps between orbit swaths: along-track mean minus isotropic mean of
    log-luminance estimates a per-swath gain; applied only on land-like pixels, clamped."""
    L = np.log(np.clip(img @ np.array([0.30, 0.59, 0.11], np.float32), 0.02, 1))
    water = (img[..., 2] > img[..., 0] + 0.03) & (img.max(2) < 0.5)
    wland = cv2.GaussianBlur((~water).astype(np.float32), (0, 0), 3)
    ln = max(31, int(round(length_km * px_per_km)) | 1)
    k = _line_mean(ln, ang)
    num_a = cv2.filter2D(L * wland, -1, k, borderType=cv2.BORDER_REFLECT)
    den_a = cv2.filter2D(wland, -1, k, borderType=cv2.BORDER_REFLECT)
    sig = ln / 2.6
    num_i = cv2.GaussianBlur(L * wland, (0, 0), sig); den_i = cv2.GaussianBlur(wland, (0, 0), sig)
    band = num_a / np.maximum(den_a, 1e-3) - num_i / np.maximum(den_i, 1e-3)
    band = np.clip(band, -max_gain, max_gain) * np.clip(den_a / 0.6, 0, 1)
    band = cv2.GaussianBlur(band, (0, 0), max(1.0, 1.5 * px_per_km))
    bright = np.clip((img.mean(2) - 0.38) / 0.15, 0, 1)                   # deserts/snow: no haze bands -> leave alone
    wl = wland * (1 - bright)
    return (np.exp(-band) * wl + (1 - wl)).astype(np.float32)


class CleanTiles:
    """Wraps a TileSource: tiles at zoom <= max_clean_z are destreaked in 4x4-tile blocks
    (with 1-tile margin to avoid seams) and cached as PNG."""

    def __init__(self, src, cache_dir, max_clean_z=8, block=4, land=None):
        """land: optional engine.geo.Countries (50m) -> sea ice outside land is recoloured to open ocean."""
        self.land = land; self._land_rings = None
        self.src, self.cache_dir, self.maxz, self.block = src, cache_dir, max_clean_z, block
        self.max_zoom = src.max_zoom; self.offmap = src.offmap; self.mem = {}

    def _p(self, z, x, y):
        return os.path.join(self.cache_dir, str(z), str(x), f"{y}.png")

    def _build_block(self, z, bx, by):
        n = 1 << z; B = self.block
        x0, y0 = bx * B - 1, by * B - 1
        mos = np.concatenate([np.concatenate([self.src.get(z, x, y) for x in range(x0, x0 + B + 2)], 1)
                              for y in range(y0, y0 + B + 2)], 0)
        lat = float(unmerc(0, (by * B + B / 2) / n)[1])
        px_per_km = 256 * n / (40075.016686 * max(0.05, math.cos(math.radians(lat))))
        clean = destreak(mos, lat, px_per_km)
        if self.land is not None:
            clean = self._remove_sea_ice(clean, z, x0, y0)
        for j in range(B):
            for i in range(B):
                x, y = bx * B + i, by * B + j
                if 0 <= y < n:
                    p = self._p(z, x % n, y); os.makedirs(os.path.dirname(p), exist_ok=True)
                    tmp = f"{p}.{os.getpid()}.tmp.png"
                    Image.fromarray(clean[(j + 1) * 256:(j + 2) * 256, (i + 1) * 256:(i + 2) * 256]).save(tmp, compress_level=1)
                    os.replace(tmp, p)                                   # atomic: readers never see half files

    def _remove_sea_ice(self, img, z, x0, y0):
        from .geo import merc
        if self._land_rings is None:
            rr = []
            for f in self.land.features:
                g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
                rr += [np.asarray(p[0], float) for p in polys]
            self._land_rings = rr
        N = 256 * (1 << z); H, W = img.shape[:2]
        m = np.zeros((H, W), np.uint8); polys = []
        for r in self._land_rings:
            for sh in (-360, 0, 360):
                x, y = merc(r[:, 0] + sh, r[:, 1])
                px, py = x * N - x0 * 256, y * N - y0 * 256
                if px.max() < -5 or px.min() > W + 5 or py.max() < -5 or py.min() > H + 5:
                    continue
                polys.append(np.round(np.stack([px, py], 1) * 16).astype(np.int32))
        if polys:
            cv2.fillPoly(m, polys, 255, lineType=cv2.LINE_AA, shift=4)
        land = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))).astype(np.float32) / 255
        f = img.astype(np.float32)
        bright = np.clip((f.mean(2) - 45) / 35.0, 0, 1) * np.clip((f.max(2) - f.min(2) - 0) / 1.0, 1, 1)
        ice = cv2.GaussianBlur(bright * (1 - land), (0, 0), 2.0)
        ocean = np.array([20, 37, 61], np.float32)                     # S2 open-ocean median
        rng = np.random.default_rng(z * 1000003 + x0 * 7 + y0)
        tex = ocean[None, None] * (1 + 0.04 * cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 6)[..., None] * 8)
        out = f * (1 - ice[..., None]) + tex * ice[..., None]
        return np.clip(out, 0, 255).astype(np.uint8)

    def get(self, z, x, y):
        n = 1 << z
        if z > self.maxz or y < 0 or y >= n:
            return self.src.get(z, x, y)
        x %= n; k = (z, x, y)
        if k in self.mem:
            return self.mem[k]
        p = self._p(z, x, y)
        if not os.path.exists(p):
            self._build_block(z, x // self.block, y // self.block)
        try:
            a = np.asarray(Image.open(p).convert("RGB"))
        except Exception:                                                # corrupt/partial -> rebuild once
            self._build_block(z, x // self.block, y // self.block)
            a = np.asarray(Image.open(p).convert("RGB"))
        if len(self.mem) > 6000:
            self.mem.clear()
        self.mem[k] = a
        return a

    def prefetch(self, keys, workers=16):
        B = self.block; n_new = self.src.prefetch(
            [(z, x + dx, y + dy) for z, x, y in keys for dx in range(-B - 1, B + 2, B) for dy in range(-B - 1, B + 2, B)
             if 0 <= y + dy < (1 << z)] + list(keys), workers)
        blocks = {(z, (x % (1 << z)) // B, y // B) for z, x, y in keys if z <= self.maxz and 0 <= y < (1 << z)}
        todo = [b for b in blocks if not os.path.exists(self._p(b[0], (b[1] * B) % (1 << b[0]), min(b[2] * B, (1 << b[0]) - 1)))]
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(lambda b: self._build_block(*b), todo))
        return n_new

    def mosaic(self, z, tx0, ty0, tx1, ty1):
        w, h = tx1 - tx0 + 1, ty1 - ty0 + 1
        out = np.empty((h * 256, w * 256, 3), np.uint8)
        for j, ty in enumerate(range(ty0, ty1 + 1)):
            for i, tx in enumerate(range(tx0, tx1 + 1)):
                out[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = self.get(z, tx, ty)
        return out
