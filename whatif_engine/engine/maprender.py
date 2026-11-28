"""Base map + region highlights, rendered straight at output resolution.

Anti-aliasing / no shimmer: tiles are fetched one level ABOVE the needed density and reduced with
INTER_AREA to ~1.25 texture px per screen px, then warped with bilinear filtering -> zoom is
continuous, no mip popping, no aliasing.
Highlights use the real Natural Earth polygons, projected per frame with sub-pixel precision
(cv2.fillPoly shift=4 + LINE_AA).
"""
import math
import cv2
import numpy as np
from .geo import merc, unmerc

SUB = 4                       # fillPoly sub-pixel bits (1/16 px)


def hex2rgb(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


# ----------------------------------------------------------------------------- base map
class MapRenderer:
    def __init__(self, tiles, W=1080, H=1920, density=1.25, max_zoom=11, grade=None):
        self.tiles, self.W, self.H, self.density, self.max_zoom = tiles, W, H, density, max_zoom
        self.grade = grade or LutGrade()
        self._noise = _make_noise(1024, seed=3)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = ((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2
        self.vignette = (1.0 - 0.12 * np.clip(r2, 0, 1.6))[..., None].astype(np.float32)

    def view_bbox(self, M, margin=60):
        Minv = np.linalg.inv(M)
        xs = np.array([-margin, self.W / 2, self.W + margin, -margin, self.W + margin, -margin, self.W / 2, self.W + margin])
        ys = np.array([-margin, -margin, -margin, self.H / 2, self.H / 2, self.H + margin, self.H + margin, self.H + margin])
        p = Minv @ np.vstack([xs, ys, np.ones_like(xs)])
        mx, my = p[0] / p[2], p[1] / p[2]
        return mx.min(), my.min(), mx.max(), my.max()

    def plan(self, M, scale):
        """tiles needed for this view -> (z, tx0, ty0, tx1, ty1)"""
        zf = math.log2(max(scale * self.density, 1) / 256.0)
        z = int(min(self.max_zoom, max(1, math.ceil(zf))))
        N = 256 * (1 << z)
        x0, y0, x1, y1 = self.view_bbox(M)
        y0, y1 = max(y0, -0.02), min(y1, 1.02)
        return z, int(math.floor(x0 * N / 256)), int(math.floor(y0 * N / 256)), int(math.floor(x1 * N / 256)), int(math.floor(y1 * N / 256))

    def tiles_for(self, M, scale):
        z, tx0, ty0, tx1, ty1 = self.plan(M, scale)
        return [(z, x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]

    def base(self, M, scale):
        z, tx0, ty0, tx1, ty1 = self.plan(M, scale)
        N = 256.0 * (1 << z)
        mos = self.tiles.mosaic(z, tx0, ty0, tx1, ty1)
        r = min(1.0, scale * self.density / N)
        if r < 0.999:
            mos = cv2.resize(mos, (max(1, int(round(mos.shape[1] * r))), max(1, int(round(mos.shape[0] * r)))), interpolation=cv2.INTER_AREA)
            rx = mos.shape[1] / ((tx1 - tx0 + 1) * 256.0); ry = mos.shape[0] / ((ty1 - ty0 + 1) * 256.0)
        else:
            rx = ry = 1.0
        A = np.array([[1 / (rx * N), 0, tx0 * 256 / N], [0, 1 / (ry * N), ty0 * 256 / N], [0, 0, 1.0]])
        img = cv2.warpPerspective(mos, M @ A, (self.W, self.H), flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=(25, 25, 25))
        off = (img[..., 0] == 25) & (img[..., 1] == 25) & (img[..., 2] == 25)
        out = self.grade(img)
        if off.any():
            out[off] = 25 / 255.0
        return out

    def noise(self, M, freq=6.0):
        """world-anchored soft noise (0..1) for fill texture"""
        S = np.array([[1 / (1024 * freq), 0, 0], [0, 1 / (1024 * freq), 0], [0, 0, 1.0]])
        return cv2.warpPerspective(self._noise, M @ S, (self.W, self.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


class LutGrade:
    """Histogram-matched grade (fitted on reference frames): separate LUTs for ocean and land,
    blended by a soft 'water' classifier on the source colours. Operates on uint8 input."""

    def __init__(self, path=None, strength=1.0):
        import os
        path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "grade_luts.npz")
        d = np.load(path)
        self.lo = np.clip(d["ocean"], 0, 255).astype(np.uint8).T.reshape(256, 1, 3)
        self.ll = np.clip(d["land"], 0, 255).astype(np.uint8).T.reshape(256, 1, 3)
        self.strength = strength

    def __call__(self, u8):
        o = cv2.LUT(u8, self.lo).astype(np.float32); l = cv2.LUT(u8, self.ll).astype(np.float32)
        f = u8.astype(np.float32)
        R, G, B = f[..., 0], f[..., 1], f[..., 2]
        w = np.clip((B - R - 4) / 12.0, 0, 1) * np.clip((150 - f.max(2)) / 40.0, 0, 1)
        out = (o * w[..., None] + l * (1 - w[..., None]))
        if self.strength != 1.0:
            out = f + (out - f) * self.strength
        return out * (1 / 255.0)


class Grade:
    """Colour grade sat imagery toward the reference look (teal ocean, muted land).
    out = clip((M @ rgb + off) ** gamma). Fitted in stage 6 against reference pixels."""

    def __init__(self, M=None, off=None, gamma=1.0, sat=1.0):
        self.M = np.asarray(M if M is not None else np.eye(3), np.float32)
        self.off = np.asarray(off if off is not None else [0, 0, 0], np.float32)
        self.gamma, self.sat = gamma, sat

    def __call__(self, img):
        img = img.astype(np.float32) / 255.0
        out = img @ self.M.T + self.off
        if self.sat != 1.0:
            l = out.mean(2, keepdims=True); out = l + (out - l) * self.sat
        np.clip(out, 0, 1, out=out)
        if self.gamma != 1.0:
            out **= self.gamma
        return out


def _make_noise(n, seed=0):
    rng = np.random.default_rng(seed); acc = np.zeros((n, n), np.float32); amp = 1.0
    for k in (8, 16, 32, 64):
        g = rng.random((k, k)).astype(np.float32)
        g = np.tile(g, (3, 3)); g = cv2.resize(g, (n * 3, n * 3), interpolation=cv2.INTER_CUBIC)[n:2 * n, n:2 * n]
        acc += amp * g; amp *= 0.55
    acc -= acc.min(); acc /= acc.max(); return acc


# ----------------------------------------------------------------------------- polygons
def ring_mask(cam, t, rings, W, H, select=None, M=None):
    """Rasterize Natural Earth rings (exteriors minus holes) to a float32 AA mask 0..1."""
    if M is None:
        M, _ = cam.matrix(t)
    s = cam.state(t); clon = unmerc(s["mx"], s["my"])[0]
    m = np.zeros((H, W), np.uint8)
    for draw_holes in (False, True):
        polys = []
        for r in rings:
            if r["hole"] != draw_holes or (select and not select(r)):
                continue
            lon = r["lon"] + 360.0 * np.round((clon - r["lon"].mean()) / 360.0)
            x, y = merc(lon, r["lat"])
            sx, sy = cam.project(M, x, y)
            if sx.max() < -50 or sx.min() > W + 50 or sy.max() < -50 or sy.min() > H + 50:
                continue
            pts = np.stack([np.clip(sx, -4000, W + 4000), np.clip(sy, -4000, H + 4000)], 1)
            polys.append(np.round(pts * (1 << SUB)).astype(np.int32))
        if polys:
            cv2.fillPoly(m, polys, 0 if draw_holes else 255, lineType=cv2.LINE_AA, shift=SUB)
    return m.astype(np.float32) / 255.0


def apply_opaque_fill(img, mask, noise, color="#0083FB", inset_px=2.5, amount=1.0, texture=0.10):
    """Opaque 'actor' fill (measured #0083FB, p10..p90 ~ #007DE9..#0C8BFE) inset from the coast."""
    if amount <= 0 or mask.max() == 0:
        return img
    if inset_px > 0:
        k = int(math.ceil(inset_px)) * 2 + 1
        mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    c = hex2rgb(color)
    tex = (1.0 + texture * (noise - 0.5) * 2.0)[..., None]
    fill = np.clip(c[None, None] * tex, 0, 1)
    a = (mask * amount)[..., None]
    return img * (1 - a) + fill * a


def apply_tint_fill(img, mask, tint="#C0402E", amount=1.0, feather=2.0, halo_px=45, halo_gain=0.18):
    """Translucent 'target' fill: keeps terrain relief (luminance * colour), soft edge + outer halo."""
    if amount <= 0 or mask.max() == 0:
        return img
    if feather > 0:
        mask = cv2.GaussianBlur(mask, (0, 0), feather)
    lum = img @ np.array([0.30, 0.59, 0.11], np.float32)
    # measured: unfilled land L~75 -> fill p50 #8C3816 => per-channel gain (1.87,0.75,0.29)
    gain = hex2rgb(tint) / max(hex2rgb(tint).max(), 1e-6) * np.array([1.87, 1.87, 1.87], np.float32)
    # calibrated on graded land (median L~0.38) -> reference fill p50 #8C3816
    gain = np.array([1.45, 0.58, 0.24], np.float32) if tint.upper() == "#C0402E" else gain
    tinted = np.clip(lum[..., None] * gain[None, None], 0, 1)
    a = (mask * amount)[..., None]
    out = img * (1 - a) + tinted * a
    if halo_px > 0:
        sm = cv2.resize(mask, (mask.shape[1] // 4, mask.shape[0] // 4), interpolation=cv2.INTER_AREA)
        sm = cv2.resize(cv2.GaussianBlur(sm, (0, 0), halo_px / 8.0), (mask.shape[1], mask.shape[0]), interpolation=cv2.INTER_LINEAR)
        halo = np.clip(sm - mask, 0, 1)
        out = out + (halo * halo_gain * amount)[..., None] * (1 - out)
    return out
