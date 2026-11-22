"""Map camera + compositing engine (deterministic, t = frame/30)."""
import math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import assets as A

W, H, FPS = 1920, 1080, 30
ASP = H / W
cv2.setNumThreads(1)


def md(lat):
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(max(-85, min(85, lat))) / 2)))


def ease_io(u):
    u = min(1, max(0, u))
    return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2


def ease_out(u, p=3):
    u = min(1, max(0, u)); return 1 - (1 - u) ** p


def smooth(a, b, x):
    u = min(1, max(0, (x - a) / (b - a))) if b != a else float(x >= a)
    return u * u * (3 - 2 * u)


def pop_scale(dt, dur=.35):
    """0.6 -> 1.08 -> 1.0"""
    if dt <= 0: return 0
    u = dt / dur
    if u >= 1: return 1.0
    if u < .6: return .6 + .48 * ease_out(u / .6, 2)
    return 1.08 - .08 * ease_io((u - .6) / .4)


# ------------------------------------------------------------------ textures
class Tex:
    def __init__(self, path, meta, prev_ppd=None, feather=48, alpha=True):
        img = cv2.imread(path, cv2.IMREAD_COLOR)[:, :, ::-1]
        X0, Yt, ppd = map(float, open(meta).read().split())
        self.X0, self.Yt, self.ppd, self.prev = X0, Yt, ppd, prev_ppd
        h, w = img.shape[:2]
        self.X1 = X0 + w / ppd; self.Yb = Yt - h / ppd
        if alpha:
            a = np.ones((h, w), np.float32)
            ry = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / feather, 0, 1)
            rx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / feather, 0, 1)
            # ignore black padding from tiles outside the requested box
            a = (ry[:, None] * rx[None, :])
            dark = (img.max(2) < 6).astype(np.uint8)
            a[cv2.dilate(dark, np.ones((9, 9), np.uint8)) > 0] = 0
            img = np.dstack([img, (a * 255).astype(np.uint8)])
        self.levels = [np.ascontiguousarray(img)]
        while min(self.levels[-1].shape[:2]) > 600 and len(self.levels) < 7:
            self.levels.append(cv2.pyrDown(self.levels[-1]))

    def sample(self, X, Y, pxdeg):
        f = self.ppd / max(pxdeg, 1e-6)
        lv = math.log2(f) if f > 1 else 0.0
        l0 = min(int(lv), len(self.levels) - 1); fr = min(1.0, lv - l0) if l0 < len(self.levels) - 1 else 0
        out = None
        for l, wgt in ((l0, 1 - fr), (l0 + 1, fr)):
            if wgt <= 1e-3 or l >= len(self.levels): continue
            s = self.ppd / 2 ** l
            mx = ((X - self.X0) * s - .5).astype(np.float32); my = ((self.Yt - Y) * s - .5).astype(np.float32)
            r = cv2.remap(self.levels[l], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(np.float32)
            out = r * wgt if out is None else out + r * wgt
        return out


# ------------------------------------------------------------------ camera
class Cam:
    __slots__ = ('cx', 'cy', 'vw', 'k', 'rot')

    def __init__(self, cx, cy, vw, k=.17, rot=0.0):
        self.cx, self.cy, self.vw, self.k, self.rot = cx, cy, vw, k, rot

    @property
    def pxdeg(self): return W / self.vw

    def screen_to_plane(self, x, y):
        s = self.vw / 2; k = self.k
        D = 1 + k * (y / ASP)
        u, v = x / D * s, y / D * s
        c, sn = math.cos(math.radians(self.rot)), math.sin(math.radians(self.rot))
        return self.cx + u * c - v * sn, self.cy - (u * sn + v * c)

    def plane_to_px(self, X, Y):
        X = np.asarray(X, np.float64); Y = np.asarray(Y, np.float64)
        s = self.vw / 2; k = self.k
        c, sn = math.cos(math.radians(self.rot)), math.sin(math.radians(self.rot))
        dX, dY = X - self.cx, self.cy - Y
        u = dX * c + dY * sn; v = -dX * sn + dY * c
        p, q = u / s, v / s
        den = np.maximum(1 - k * q / ASP, 0.05)
        y = q / den; x = p * (1 + k * y / ASP)
        return x * W / 2 + W / 2, y * W / 2 + H / 2

    def ll(self, lon, lat):
        return self.plane_to_px(lon, md(lat) if np.isscalar(lat) else np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))))

    def local_frame(self, lon, lat):
        """screen angle (deg) of east axis and vertical squash at a point"""
        x0, y0 = self.ll(lon, lat); x1, y1 = self.ll(lon + self.vw * .02, lat)
        Y = md(lat); x2, y2 = self.plane_to_px(lon, Y + self.vw * .02)
        ang = math.degrees(math.atan2(-(y1 - y0), x1 - x0))
        ex = math.hypot(x1 - x0, y1 - y0); ny = math.hypot(x2 - x0, y2 - y0)
        return ang, (ny / ex if ex > 0 else 1), ex / (self.vw * .02) / (W / self.vw)


# grid of normalised screen coords
_gx = ((np.arange(W) + .5 - W / 2) / (W / 2)).astype(np.float32)
_gy = ((np.arange(H) + .5 - H / 2) / (W / 2)).astype(np.float32)
GX, GY = np.meshgrid(_gx, _gy)


def plane_grid(cam):
    s = cam.vw / 2; k = cam.k
    D = 1 + k * (GY / ASP)
    u = GX / D * s; v = GY / D * s
    c, sn = math.cos(math.radians(cam.rot)), math.sin(math.radians(cam.rot))
    return (cam.cx + u * c - v * sn).astype(np.float32), (cam.cy - (u * sn + v * c)).astype(np.float32)


def render_map(cam, base, patches):
    X, Y = plane_grid(cam)
    px = cam.pxdeg
    img = base.sample(X, Y, px)[..., :3]
    # visible plane bbox
    xs = [X[0, 0], X[0, -1], X[-1, 0], X[-1, -1]]; ys = [Y[0, 0], Y[0, -1], Y[-1, 0], Y[-1, -1]]
    for p in patches:
        w = smooth(.9 * p.prev, 1.7 * p.prev, px)
        if w <= 0.002: continue
        if max(xs) < p.X0 or min(xs) > p.X1 or max(ys) < p.Yb or min(ys) > p.Yt: continue
        r = p.sample(X, Y, px)
        a = r[..., 3:4] / 255 * w
        img = img * (1 - a) + r[..., :3] * a
    return img


# ------------------------------------------------------------------ compositing helpers
def comp_premul(frame, layer, mult=1.0, box=None):
    """layer: uint8 HxWx4 premultiplied (drawn on black with opaque colours)"""
    if mult <= 0: return
    if box is None: box = (0, 0, W, H)
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    L = layer[y0:y1, x0:x1].astype(np.float32)
    a = L[..., 3:4] / 255 * mult
    f = frame[y0:y1, x0:x1]
    f *= (1 - a); f += L[..., :3] * mult


def comp_add(frame, layer_rgb, mult, box):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    f = frame[y0:y1, x0:x1]
    f += layer_rgb[y0:y1, x0:x1].astype(np.float32) * mult
    np.minimum(f, 255, out=f)


def paste(frame, im, cx, cy, mult=1.0):
    """paste PIL RGBA (straight alpha) centred at cx,cy"""
    if mult <= 0 or im is None: return
    a = np.asarray(im, np.float32)
    h, w = a.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0); sx1, sy1 = min(w, W - x0), min(h, H - y0)
    if sx1 <= sx0 or sy1 <= sy0: return
    s = a[sy0:sy1, sx0:sx1]
    al = s[..., 3:4] / 255 * mult
    f = frame[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
    f *= (1 - al); f += s[..., :3] * al


def tf(im, scale=1.0, angle=0.0, squash=1.0):
    if im is None: return None
    w, h = im.size
    if scale <= 0.01: return None
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale * squash))
    im = im.resize((nw, nh), Image.BICUBIC)
    if abs(angle) > .05: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return im


def pts_px(cam, ring):
    x, y = cam.plane_to_px(ring[:, 0], ring[:, 1])
    return np.stack([x, y], 1)


def blank():
    return np.zeros((H, W, 4), np.uint8)


def bbox_of(arrs, pad=40):
    allp = np.concatenate(arrs, 0)
    return (allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)


def fill_rings(layer, rings_px, color):
    pts = [np.round(r * 8).astype(np.int32) for r in rings_px if len(r) > 2]
    if pts: cv2.fillPoly(layer, pts, color + (255,), lineType=cv2.LINE_AA, shift=3)


def line_px(layer, pts, color, width, closed=False):
    if len(pts) < 2: return
    p = np.round(pts * 8).astype(np.int32)
    cv2.polylines(layer, [p], closed, color + (255,), max(1, int(round(width))), lineType=cv2.LINE_AA, shift=3)


def glow_layer(layer, box, sigma):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return None
    sub = layer[y0:y1, x0:x1, :3]
    sm = cv2.resize(sub, ((x1 - x0) // 2 + 1, (y1 - y0) // 2 + 1), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), sigma / 2)
    out = np.zeros((H, W, 3), np.uint8)
    out[y0:y1, x0:x1] = cv2.resize(sm, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
    return out


# ------------------------------------------------------------------ text
_font_cache = {}


def font(size):
    if size not in _font_cache: _font_cache[size] = ImageFont.truetype(A.FONT, size)
    return _font_cache[size]


_txt_cache = {}


def text_sprite(s, size, color=(255, 255, 255), glow=True):
    key = (s, size, color, glow)
    if key in _txt_cache: return _txt_cache[key]
    f = font(size)
    l, t, r, b = f.getbbox(s)
    pad = int(size * .35)
    w, h = r - l + 2 * pad, b - t + 2 * pad
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((pad - l + 6, pad - t + 8), s, font=f, fill=(0, 0, 0, 150))
    im = im.filter(ImageFilter.GaussianBlur(5))
    if glow:
        g = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(g).text((pad - l, pad - t), s, font=f, fill=color + (255,))
        g = g.filter(ImageFilter.GaussianBlur(size * .09))
        im.alpha_composite(g); im.alpha_composite(g)
    d = ImageDraw.Draw(im)
    d.text((pad - l, pad - t), s, font=f, fill=color + (255,), stroke_width=max(2, size // 40), stroke_fill=tuple(int(c * .75) for c in color) + (255,))
    if len(_txt_cache) > 400: _txt_cache.clear()
    _txt_cache[key] = im
    return im


def badge_sprite(n):
    key = ('badge', n)
    if key in _txt_cache: return _txt_cache[key]
    f = ImageFont.truetype(A.FONT, 190)
    s = str(n); l, t, r, b = f.getbbox(s)
    w, h = r - l + 40, b - t + 40
    mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).text((20 - l, 20 - t), s, font=f, fill=255)
    yy, xx = np.mgrid[0:h, 0:w]
    wave = .5 + .5 * np.sin(xx / 10 + 2.4 * np.sin(yy / 15))
    tex = np.stack([150 + 105 * wave, 205 - 75 * wave, 255 - 35 * wave, np.asarray(mask)], -1).astype(np.uint8)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ol = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(ol).text((20 - l, 20 - t), s, font=f, fill=(120, 12, 24, 255), stroke_width=4, stroke_fill=(120, 12, 24, 255))
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((26 - l, 28 - t), s, font=f, fill=(0, 0, 0, 120), stroke_width=4, stroke_fill=(0, 0, 0, 120))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5))); out.alpha_composite(ol); out.alpha_composite(Image.fromarray(tex, 'RGBA'))
    # scale so the glyph is ~150px tall
    sc = 150 / (b - t)
    out = out.resize((int(w * sc), int(h * sc)), Image.LANCZOS)
    _txt_cache[key] = out
    return out
