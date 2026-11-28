"""
journey_fx.py — preset gaya "JOURNEY" (peta perjalanan lintas benua) untuk maproute-engine.

Semua efek digambar di atas frame PIL RGBA yang SUDAH berisi peta dasar
(citra satelit + fills engine), dan SEBELUM caption/kartu/watermark engine.

Kontrak integrasi (lihat addon/INTEGRASI.md):
    import journey_fx as J
    img = J.draw_all(img, spec.get('jfx', []), t_local, P)     # tiap frame
    img = J.post_all(img, spec.get('jfx', []), t_local)         # efek layar penuh (finale)

    P(lon, lat) -> (x, y) piksel pada frame yang sedang dirender (proyeksi + kamera engine).
    t_local     -> detik sejak shot dimulai (sama dengan t0 di spec engine).

Semua ukuran ditulis dalam piksel ruang 1080x1920 lalu diskalakan otomatis ke
ukuran frame yang sebenarnya (engine merender 810x1440 -> s = 0.75).

Hanya butuh: numpy, PIL. Tidak butuh shapely/scipy.
"""
from __future__ import annotations

import math
import os
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, '..', 'assets'))
FONT_PATH = os.path.join(ASSETS, 'fonts', 'LilitaOne-Regular.ttf')      # label besar (bulat)
FONT_SANS = os.path.join(ASSETS, 'fonts', 'Montserrat-VF.ttf')          # caption & label kecil (geometris)

# ----------------------------------------------------------------------------
# Palet (diambil dari frame referensi, 1080x1920)
# ----------------------------------------------------------------------------
PAL = {
    'ocean':        '#0a3a4c',
    'arc':          '#35b8ff',   # garis lengkung biru neon (hook)
    'route':        '#ffffff',   # jejak jalan kaki
    'route_glow':   '#2f9bff',   # rute penuh saat zoom-out akhir
    'neon_green':   '#9eeb25',   # garis penghubung benua
    'check':        '#18ff00',   # ceklis
    'leader':       '#2cc7d9',   # label kecil cyan + garis
    'pin':          '#e3202c',
    'gold':         '#e1a838',   # negara jalur (kuning mustard)
    'gold_hl':      '#f2a516',   # negara asal (oranye-kuning)
    'egypt':        '#f05a5a',   # negara penting (merah salmon)
    'red':          '#c8102e',   # negara besar (Kanada/Turki/negara bagian)
    'blue':         '#3b4fc4',   # negara tujuan (AS)
    'lightblue':    '#5fb8e6',   # Alaska / Palestina
    'green':        '#66ca38',
    'yellow':       '#d8c52a',
    'orange':       '#f08a2c',
    'magenta':      '#c22fd6',
    'teal_tint':    '#3fa7bd',   # tint wilayah raksasa (Rusia)
    'ice':          '#cfe8f7',
    'frozen':       '#2382ca',
    'grid_bg':      '#2a347a',
    'grid_line':    '#4b5aa8',
    'km':           '#7ff3ff',
}


def hexrgb(c, a=255):
    if isinstance(c, tuple):
        return c if len(c) == 4 else (*c, a)
    c = PAL.get(c, c).lstrip('#')
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)


# ----------------------------------------------------------------------------
# Easing & util
# ----------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out_cubic(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x); return x * x * (3 - 2 * x)


def ease_out_back(x, k=1.7):
    x = clamp(x); x -= 1; return 1 + x * x * ((k + 1) * x + k)


def life(t, t0, t1=None, fin=0.3, fout=0.35):
    """Alpha 0..1 untuk elemen yang muncul di t0 dan hilang di t1."""
    if t < t0:
        return 0.0
    a = ease_out_cubic((t - t0) / max(fin, 1e-3))
    if t1 is not None:
        a *= 1 - ease_in_out((t - t1) / max(fout, 1e-3)) if t >= t1 else 1
    return clamp(a)


def S(img):
    """Skala dari ruang 1080x1920 ke frame sebenarnya."""
    return img.size[1] / 1920.0


@lru_cache(maxsize=32)
def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, int(size))
    except OSError:
        return ImageFont.load_default()


@lru_cache(maxsize=64)
def font_sans(size, weight=800):
    """Montserrat variable: 600 = SemiBold (label kecil), 800 = ExtraBold (caption)."""
    try:
        f = ImageFont.truetype(FONT_SANS, int(size))
        f.set_variation_by_axes([weight])
        return f
    except (OSError, AttributeError):
        return font(size)


def paste_sub(img, tile, x, y):
    """Tempel tile dengan pusat di (x, y) memakai posisi SUBPIKSEL (tidak gemetar saat kamera bergerak)."""
    X, Y = x - tile.size[0] / 2, y - tile.size[1] / 2
    ix, iy = math.floor(X), math.floor(Y); fx, fy = X - ix, Y - iy
    if fx > 1e-3 or fy > 1e-3:
        tile = tile.transform((tile.size[0] + 1, tile.size[1] + 1), Image.AFFINE, (1, 0, -fx, 0, 1, -fy), Image.BILINEAR)
    W, H = img.size
    if ix >= W or iy >= H or ix + tile.size[0] <= 0 or iy + tile.size[1] <= 0:
        return img
    cx0, cy0 = max(0, -ix), max(0, -iy)
    cx1, cy1 = min(tile.size[0], W - ix), min(tile.size[1], H - iy)
    img.alpha_composite(tile.crop((cx0, cy0, cx1, cy1)), (ix + cx0, iy + cy0))
    return img


def text_tile(text, f, fill, stroke, stroke_fill, glow=None, glow_r=0, pad=None):
    bb = f.getbbox(text, stroke_width=stroke)
    pad = pad if pad is not None else int(glow_r * 2.5) + 4
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((pad - bb[0], pad - bb[1]), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if glow and glow_r:
        g = Image.new('RGBA', tile.size, glow); g.putalpha(tile.split()[3].filter(ImageFilter.GaussianBlur(glow_r)))
        tile = Image.alpha_composite(g, tile)
    return tile


def proj_poly(P, ring):
    return [P(lon, lat) for lon, lat in ring]


def rings_of(geom):
    """Terima: ring [(lon,lat)...], list ring, atau list polygon (list of rings).
    Kembalikan list ring luar (lubang diabaikan; cukup untuk highlight)."""
    if not geom:
        return []
    if isinstance(geom[0][0], (int, float)):
        return [geom]
    if isinstance(geom[0][0][0], (int, float)):
        return list(geom)
    out = []
    for g in geom:
        out += rings_of(g)
    return out


def poly_mask(size, P, geom, ss=2):
    """Mask poligon dengan supersampling ss x ss (tepi halus, tidak bergerigi)."""
    W, H = size
    m = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(m)
    for r in rings_of(geom):
        pts = [(x * ss, y * ss) for x, y in proj_poly(P, r)]
        if len(pts) >= 3:
            d.polygon(pts, fill=255)
    return m.reduce(ss) if ss > 1 else m


def glow_layer(layer, radius, strength=1.0):
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        a = np.asarray(g).astype(np.float32)
        a[..., 3] = np.clip(a[..., 3] * strength, 0, 255)
        g = Image.fromarray(a.astype(np.uint8), 'RGBA')
    return g


def over(img, layer):
    return Image.alpha_composite(img, layer)


def with_alpha(layer, a):
    if a >= 0.999:
        return layer
    arr = np.asarray(layer).copy()
    arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


# ----------------------------------------------------------------------------
# Tekstur prosedural (di-cache per ukuran)
# ----------------------------------------------------------------------------
def _value_noise(w, h, cell, seed):
    rng = np.random.default_rng(seed)
    gw, gh = w // cell + 2, h // cell + 2
    g = rng.random((gh, gw)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8), 'L').resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32)[:h, :w] / 255.0


def fbm(w, h, seed=1, base=160, octaves=4):
    acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0.0; cell = base
    for o in range(octaves):
        acc += amp * _value_noise(w, h, max(cell, 2), seed + o * 17)
        tot += amp; amp *= 0.5; cell //= 2
    return acc / tot


def _ramp(n, stops):
    """n: array 0..1 ; stops: [(pos, '#hex'), ...] -> RGB uint8."""
    xs = np.array([s[0] for s in stops], np.float32)
    cols = np.array([hexrgb(s[1])[:3] for s in stops], np.float32)
    out = np.stack([np.interp(n, xs, cols[:, i]) for i in range(3)], -1)
    return out.astype(np.uint8)


@lru_cache(maxsize=16)
def texture(kind, w, h, seed=7):
    n = fbm(w, h, seed, base=max(w, h) // 6)
    if kind == 'fire':        # Afrika: kuning panas -> merah
        y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        v = np.clip(0.55 * n + 0.6 * y - 0.05, 0, 1)
        rgb = _ramp(v, [(0, '#fff2b0'), (0.25, '#ffc046'), (0.5, '#ff6a00'), (0.75, '#f01400'), (1, '#b00000')])
    elif kind == 'violet':    # Amerika: ungu neon -> nila gelap
        y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        v = np.clip(0.5 * n + 0.5 * y, 0, 1)
        rgb = _ramp(v, [(0, '#b066ff'), (0.3, '#5a1fd6'), (0.6, '#2a0f9a'), (1, '#120650')])
    elif kind == 'ocean_hl':  # Samudra disorot: biru terang
        rgb = _ramp(n, [(0, '#0b4f9a'), (0.5, '#1f8fe0'), (1, '#55c8ff')])
    elif kind == 'ice':       # Siberia: es retak
        cr = np.abs(fbm(w, h, seed + 5, base=max(w, h) // 14) - 0.5) < 0.025
        v = np.clip(0.85 + 0.15 * n - cr * 0.25, 0, 1)
        rgb = _ramp(v, [(0, '#8fbfdc'), (0.7, '#cfe8f7'), (1, '#f4fbff')])
    elif kind == '_noise':
        g = (fbm(w, h, seed + 9, base=max(w, h) // 9, octaves=5) * 255).astype(np.uint8)
        return Image.fromarray(np.stack([g, g, g, np.full_like(g, 255)], -1), 'RGBA')
    elif kind == 'frozen':    # laut membeku: lempeng es + retakan
        v = np.clip(n * 1.1 - 0.05, 0, 1)
        rgb = _ramp(v, [(0, '#1a73bd'), (0.5, '#2f8fd6'), (1, '#6cc4f5')])
        im = Image.fromarray(rgb, 'RGB').convert('RGBA'); d = ImageDraw.Draw(im, 'RGBA')
        r = random.Random(seed)
        for _ in range(int(w * h / 22000)):         # lempeng bersudut
            cx, cy, R0 = r.random() * w, r.random() * h, (0.02 + r.random() * 0.06) * w
            pts = [(cx + math.cos(a0) * R0 * (0.6 + 0.4 * r.random()), cy + math.sin(a0) * R0 * (0.6 + 0.4 * r.random()))
                   for a0 in sorted(r.random() * 6.283 for _ in range(5))]
            sh = r.choice([(255, 255, 255, 16), (150, 215, 255, 20), (40, 120, 200, 14)])
            d.polygon(pts, fill=sh)
        for _ in range(int(w * h / 9000)):          # retakan
            x, y = r.random() * w, r.random() * h; ang = r.random() * 6.283; pts = [(x, y)]
            for _k in range(r.randint(3, 7)):
                ang += (r.random() - 0.5) * 1.2; L = (0.01 + r.random() * 0.03) * w
                x += math.cos(ang) * L; y += math.sin(ang) * L; pts.append((x, y))
            d.line(pts, fill=(225, 245, 255, 70), width=max(1, w // 900))
        return im
    else:
        rgb = np.full((h, w, 3), 255, np.uint8)
    a = np.full((h, w, 1), 255, np.uint8)
    return Image.fromarray(np.concatenate([rgb, a], -1), 'RGBA')


# ----------------------------------------------------------------------------
# Basis efek
# ----------------------------------------------------------------------------
class FX:
    post = False   # True = efek layar penuh, dipanggil lewat post_all()

    def draw(self, img, t, P):
        return img


# ---------- 1. Sorotan wilayah (solid / bertekstur), menumpuk -----------------
class HL(FX):
    """Highlight wilayah. geom = hasil G.select(...) / ring lon-lat.
    tex: None | 'fire' | 'violet' | 'ice' | 'ocean_hl' | 'frozen'
         ('fire'/'violet'/'ice' mengikuti relief citra satelit di bawahnya, seperti peta panas)
    clip: geom pembatas (hanya bagian geom yang ada di dalam clip yang menyala),
          mis. Rusia di-clip wilayah timur Ural = Siberia dengan garis pantai asli.
    minus: geom yang dikecualikan, mis. daratan supaya sorotan laut mengikuti pantai.
    feather: px (ruang 1080) pelembut tepi luar.
    t1=None -> tetap menyala (gaya referensi: jejak negara menumpuk)."""

    def __init__(self, geom, t0, col='gold', alpha=0.72, tex=None, t1=None,
                 fin=0.35, edge=True, glow=True, punch=True, clip=None, minus=None, feather=0):
        self.geom, self.t0, self.t1 = geom, t0, t1
        self.col, self.alpha, self.tex = col, alpha, tex
        self.fin, self.edge, self.glow, self.punch = fin, edge, glow, punch
        self.clip, self.minus, self.feather = clip, minus, feather

    def mask(self, img, P):
        m = poly_mask(img.size, P, self.geom)
        if self.clip:
            m = ImageChops.multiply(m, poly_mask(img.size, P, self.clip))
        if self.feather:                       # lembutkan tepi luar saja
            m = m.filter(ImageFilter.GaussianBlur(self.feather * S(img)))
        if self.minus:                         # potongan pantai tetap tajam
            m = ImageChops.subtract(m, poly_mask(img.size, P, self.minus))
        return m

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, self.fin)
        if a <= 0:
            return img
        m = self.mask(img, P)
        bb = m.getbbox()
        if not bb:
            return img
        if self.tex:
            base = Image.new('RGBA', img.size, (0, 0, 0, 0))
            base.paste(tex_relief(self.tex, img, bb), bb[:2])
        else:
            base = Image.new('RGBA', img.size, hexrgb(self.col))
        # "flash" saat muncul: alpha sedikit naik lalu turun ke nilai normal
        k = 1.0
        if self.punch:
            k += 0.25 * max(0.0, 1 - (t - self.t0) / 0.5)
        al = m.point(lambda v: int(v * clamp(self.alpha * k) * a))
        lay = base.copy(); lay.putalpha(al)
        if self.glow:
            gl = Image.new('RGBA', img.size, hexrgb(self.col if not self.tex else '#ffffff'))
            gl.putalpha(m.filter(ImageFilter.GaussianBlur(10 * S(img))).point(lambda v: int(v * 0.35 * a)))
            img = over(img, gl)
        img = over(img, lay)
        if self.edge:
            e = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(3)))
            e = e.filter(ImageFilter.GaussianBlur(0.6))
            el = Image.new('RGBA', img.size, (255, 255, 255, 0)); el.putalpha(e.point(lambda v: int(min(255, v * 1.4) * 0.55 * a)))
            img = over(img, el)
        return img


RAMPS = {
    'fire':   [(0, '#fff6c0'), (0.22, '#ffd34d'), (0.42, '#ff9416'), (0.6, '#ff4a00'), (0.8, '#d80600'), (1, '#760000')],
    'violet': [(0, '#0e0545'), (0.3, '#22109a'), (0.55, '#4b22d6'), (0.78, '#9150ff'), (1, '#e6d2ff')],
    'ice':    [(0, '#86b9d8'), (0.55, '#cbe6f6'), (0.85, '#eef8ff'), (1, '#ffffff')],
}


def tex_relief(kind, img, bb):
    """Tekstur untuk area bb, memakai luminans citra di bawahnya + noise (detail seperti peta panas)."""
    x0, y0, x1, y1 = bb
    W, H = img.size
    if kind not in RAMPS:
        return texture(kind, W, H).crop(bb)
    lum = np.asarray(img.crop(bb).convert('L'), np.float32)
    lo, hi = np.percentile(lum, 4), np.percentile(lum, 96)
    ln = np.clip((lum - lo) / max(hi - lo, 1), 0, 1)
    n = np.asarray(texture('_noise', W, H).crop(bb).convert('L'), np.float32) / 255
    if kind == 'fire':
        v = np.clip(0.95 * (1 - ln) + 0.45 * (n - 0.5), 0, 1)
    elif kind == 'violet':
        v = np.clip(0.9 * ln + 0.4 * (n - 0.5) + 0.05, 0, 1)
    else:  # ice
        cr = (np.abs(n - 0.5) < 0.018).astype(np.float32)
        v = np.clip(0.55 + 0.35 * ln + 0.2 * (n - 0.5) - 0.35 * cr, 0, 1)
    rgb = _ramp(v, RAMPS[kind])
    a = np.full(v.shape + (1,), 255, np.uint8)
    return Image.fromarray(np.concatenate([rgb, a], -1), 'RGBA')


# ---------- 2. Garis lengkung neon (hook: A -> B) -----------------------------
class NeonArc(FX):
    def __init__(self, a, b, t0, dur=1.2, col='arc', bulge=0.22, w=5, t1=None, side=1):
        self.a, self.b, self.t0, self.dur, self.col = a, b, t0, dur, col
        self.bulge, self.w, self.t1, self.side = bulge, w, t1, side

    def pts(self, P, n=80):
        (x0, y0), (x1, y1) = P(*self.a), P(*self.b)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        cx, cy = mx - dy * self.bulge * self.side, my + dx * self.bulge * self.side
        return [((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1,
                 (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1) for u in np.linspace(0, 1, n)]

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.05)
        if a <= 0:
            return img
        p = ease_in_out((t - self.t0) / self.dur)
        pts = self.pts(P); k = max(2, int(len(pts) * p))
        s = S(img)
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.line(pts[:k], fill=hexrgb(self.col), width=max(1, int(self.w * s)), joint='curve')
        img = over(img, with_alpha(glow_layer(lay, 8 * s, 2.0), a))
        lay2 = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay2).line(pts[:k], fill=(230, 248, 255, 255), width=max(1, int(self.w * 0.45 * s)))
        img = over(img, with_alpha(over(lay, lay2), a))
        return img


# ---------- 3. Garis lurus neon (penghubung benua) ----------------------------
class NeonLine(NeonArc):
    def __init__(self, a, b, t0, dur=0.6, col='neon_green', w=6, t1=None):
        super().__init__(a, b, t0, dur, col, 0.0, w, t1)


# ---------- 4. Label besar putih bercahaya, miring ----------------------------
class BigLabel(FX):
    """Teks besar putih + outline tipis + glow putih, pop-in dengan overshoot.
    Dipakai untuk benua / negara besar ("Afrika", "Amerika", "Russia",
    "Amerika Serikat"). col='leader' -> teks cyan (contoh 'Siberia')."""

    def __init__(self, text, lon, lat, t0, t1=None, angle=-12, size=92, col='#ffffff',
                 outline='#7a8a99', glow='#ffffff', dx=0, dy=0, xy=None):
        """xy=(x, y) piksel ruang 1080x1920 -> label menempel di layar (tidak ikut peta)."""
        self.xy = xy
        self.text, self.lon, self.lat, self.t0, self.t1 = text, lon, lat, t0, t1
        self.angle, self.size, self.col, self.outline, self.glow = angle, size, col, outline, glow
        self.dx, self.dy = dx, dy

    def _tile(self, s):
        key = round(s, 4)
        if getattr(self, '_tk', None) != key:
            f = font(self.size * s)
            t = text_tile(self.text, f, hexrgb(self.col), max(1, int(3 * s)), hexrgb(self.outline),
                          hexrgb(self.glow), 9 * s)
            self._tc = t.rotate(-self.angle, resample=Image.BICUBIC, expand=True); self._tk = key
        return self._tc

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.12)
        if a <= 0:
            return img
        s = S(img)
        sc = 0.4 + 0.6 * ease_out_back((t - self.t0) / 0.35)
        tile = self._tile(s)
        if abs(sc - 1) > 1e-3:
            tile = tile.resize((max(1, int(tile.size[0] * sc)), max(1, int(tile.size[1] * sc))), Image.BICUBIC)
        x, y = (self.xy[0] * s, self.xy[1] * s) if self.xy else P(self.lon, self.lat)
        x += self.dx * s; y += self.dy * s
        return paste_sub(img, with_alpha(tile, a), x, y)


# ---------- 5. Label kecil cyan + garis penunjuk + titik ----------------------
class LeaderLabel(FX):
    """Label negara/kota gaya referensi: teks kecil cyan di atas, garis vertikal
    tipis turun ke titik di lokasi. Garis tumbuh dari bawah ke atas."""

    def __init__(self, text, lon, lat, t0, t1=None, h=120, size=24, col='leader', dx=0):
        self.text, self.lon, self.lat, self.t0, self.t1 = text, lon, lat, t0, t1
        self.h, self.size, self.col, self.dx = h, size, col, dx

    def _tile(self, s):
        key = round(s, 4)
        if getattr(self, '_tk', None) != key:
            f = font_sans(self.size * s, 600)
            self._tc = text_tile(self.text, f, hexrgb(self.col), max(1, int(1 * s)), (8, 40, 56, 160),
                                 hexrgb(self.col, 200), 5 * s); self._tk = key
        return self._tc

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.25)
        if a <= 0:
            return img
        s = S(img)
        x, y = P(self.lon, self.lat)
        g = ease_out_cubic((t - self.t0) / 0.35)
        top = y - self.h * s * g
        # garis + titik: digambar di tile kecil supaya murah & halus
        x0, x1 = min(x, x + self.dx * s * g) - 12 * s, max(x, x + self.dx * s * g) + 12 * s
        y0, y1 = top - 4 * s, y + 12 * s
        if x1 < 0 or x0 > img.size[0] or y1 < 0 or y0 > img.size[1]:
            return img
        ss = 3
        tw_, th_ = int((x1 - x0) * ss) + 2, int((y1 - y0) * ss) + 2
        lay = Image.new('RGBA', (tw_, th_), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        c = hexrgb(self.col)
        P0 = ((x - x0) * ss, (y - y0) * ss); P1 = ((x + self.dx * s * g - x0) * ss, (top - y0) * ss)
        d.line([P0, P1], fill=c, width=max(1, int(2 * s * ss)))
        r = 5 * s * ss
        d.ellipse([P0[0] - r, P0[1] - r, P0[0] + r, P0[1] + r], fill=c)
        lay = lay.resize((max(1, tw_ // ss), max(1, th_ // ss)), Image.LANCZOS)
        gl = glow_layer(lay, 3 * s, 1.3)
        img = paste_sub(img, with_alpha(gl, a * 0.7), (x0 + x1) / 2, (y0 + y1) / 2)
        img = paste_sub(img, with_alpha(lay, a), (x0 + x1) / 2, (y0 + y1) / 2)
        if g > 0.55:
            tile = self._tile(s)
            ta = a * clamp((g - 0.55) / 0.3)
            img = paste_sub(img, with_alpha(tile, ta), x + self.dx * s * g, top - tile.size[1] / 2 + 6 * s)
        return img


# ---------- 6. Pin merah (titik awal / tujuan) --------------------------------
class Pin(FX):
    def __init__(self, lon, lat, t0, t1=None, size=70, col='pin'):
        self.lon, self.lat, self.t0, self.t1, self.size, self.col = lon, lat, t0, t1, size, col

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.1)
        if a <= 0:
            return img
        s = S(img); R = self.size * s / 2
        drop = (1 - ease_out_back((t - self.t0) / 0.45, 2.4)) * 160 * s
        x, y = P(self.lon, self.lat); y -= drop
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        # bayangan
        d.ellipse([x - R * 0.5, y + drop - R * 0.15, x + R * 0.5, y + drop + R * 0.15], fill=(0, 0, 0, 90))
        cy = y - R * 1.45
        d.polygon([(x - R * 0.72, cy + R * 0.55), (x + R * 0.72, cy + R * 0.55), (x, y)], fill=hexrgb(self.col))
        d.ellipse([x - R, cy - R, x + R, cy + R], fill=hexrgb(self.col), outline=(255, 255, 255, 255), width=max(1, int(3 * s)))
        d.ellipse([x - R * 0.48, cy - R * 0.48, x + R * 0.48, cy + R * 0.48], fill=(250, 250, 250, 255))
        d.ellipse([x - R * 0.3, cy - R * 0.4, x - R * 0.05, cy - R * 0.15], fill=(255, 255, 255, 255))
        return over(img, with_alpha(lay, a))


# ---------- 7. Pejalan kaki (ikon jejak kaki + jejak putih) --------------------
@lru_cache(maxsize=16)
def _train_icon(px):
    """Lingkaran putih + kereta tampak depan (gelap). Supersampling 4x."""
    S4 = px * 4; im = Image.new('RGBA', (S4, S4), (0, 0, 0, 0)); d = ImageDraw.Draw(im); u = S4 / 20
    d.ellipse([2, 2, S4 - 3, S4 - 3], fill=(255, 255, 255, 255), outline=(30, 30, 30, 255), width=max(2, S4 // 16))
    ink = (24, 34, 48, 255)
    d.rounded_rectangle([6 * u, 4.2 * u, 14 * u, 14.2 * u], radius=2.2 * u, fill=ink)           # badan
    d.rounded_rectangle([7.2 * u, 5.4 * u, 12.8 * u, 9.0 * u], radius=0.9 * u, fill=(150, 210, 240, 255))  # kaca
    for cx in (7.9, 12.1):
        d.ellipse([(cx - 0.75) * u, 11.0 * u, (cx + 0.75) * u, 12.5 * u], fill=(255, 220, 90, 255))   # lampu
    d.line([(7.0 * u, 14.2 * u), (5.6 * u, 16.4 * u)], fill=ink, width=int(1.1 * u))
    d.line([(13.0 * u, 14.2 * u), (14.4 * u, 16.4 * u)], fill=ink, width=int(1.1 * u))
    return im.resize((px, px), Image.LANCZOS)


@lru_cache(maxsize=16)
def _ship_icon(px):
    """Lingkaran putih + kapal feri tampak samping."""
    S4 = px * 4; im = Image.new('RGBA', (S4, S4), (0, 0, 0, 0)); d = ImageDraw.Draw(im); u = S4 / 20
    d.ellipse([2, 2, S4 - 3, S4 - 3], fill=(255, 255, 255, 255), outline=(30, 30, 30, 255), width=max(2, S4 // 16))
    ink = (24, 34, 48, 255)
    d.polygon([(3.6 * u, 11.2 * u), (16.4 * u, 11.2 * u), (14.4 * u, 14.4 * u), (5.6 * u, 14.4 * u)], fill=ink)  # lambung
    d.rounded_rectangle([6.2 * u, 7.4 * u, 13.6 * u, 11.2 * u], radius=0.6 * u, fill=(40, 120, 200, 255))      # kabin
    for k in range(3):
        d.rectangle([(7.0 + k * 2.2) * u, 8.4 * u, (8.2 + k * 2.2) * u, 9.6 * u], fill=(220, 240, 255, 255))
    d.rectangle([9.2 * u, 5.0 * u, 10.6 * u, 7.4 * u], fill=ink)
    return im.resize((px, px), Image.LANCZOS)


def _footprint_icon(px):
    """Lingkaran putih + dua telapak kaki hitam. Dibuat sekali per ukuran."""
    im = Image.new('RGBA', (px, px), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([1, 1, px - 2, px - 2], fill=(255, 255, 255, 255), outline=(30, 30, 30, 255), width=max(1, px // 14))
    u = px / 10
    for (fx, fy, rot) in [(3.6, 5.6, -18), (6.3, 4.0, 18)]:
        sole = Image.new('RGBA', (px, px), (0, 0, 0, 0)); sd = ImageDraw.Draw(sole)
        sd.ellipse([fx * u - 0.9 * u, fy * u - 1.5 * u, fx * u + 0.9 * u, fy * u + 1.2 * u], fill=(20, 20, 20, 255))
        sd.ellipse([fx * u - 0.7 * u, fy * u + 1.35 * u, fx * u + 0.7 * u, fy * u + 2.3 * u], fill=(20, 20, 20, 255))
        im = Image.alpha_composite(im, sole.rotate(rot, center=(fx * u, fy * u), resample=Image.BICUBIC))
    return im


class Walker(FX):
    """Ikon jejak kaki berjalan di sepanjang rute (list (lon,lat)), meninggalkan
    garis putih. Rute panjang: pecah per shot, pakai `done` = rute leg sebelumnya
    (digambar penuh sejak awal shot)."""

    def __init__(self, route, t0, dur=None, done=None, col='route', w=4, icon=46, ease=False, t1=None, times=None,
                 kind='walk', dashed=False):
        """times: opsional, daftar detik (panjang = len(route)) kapan ikon tiba di tiap titik.
        Dengan times, SATU Walker bisa menempuh seluruh rute multi-shot/multi-leg, termasuk
        berhenti (dua titik berurutan dengan jeda waktu besar = jalan pelan, titik sama = diam)."""
        self.route, self.t0, self.done = route, t0, done or []
        self.times = list(times) if times else None
        if self.times:
            self.t0 = self.times[0]; dur = self.times[-1] - self.times[0]
        self.dur = dur or 1.0
        self.col, self.w, self.icon, self.ease, self.t1 = col, w, icon, ease, t1
        self.kind, self.dashed = kind, dashed

    def pos(self, t):
        """Posisi (lon, lat) ikon pada waktu t — dipakai juga untuk kamera 'ikuti pejalan'."""
        if self.times:
            ts, r = self.times, self.route
            if t <= ts[0]:
                return r[0]
            for i in range(1, len(ts)):
                if t <= ts[i]:
                    u = (t - ts[i - 1]) / max(ts[i] - ts[i - 1], 1e-6)
                    return (r[i - 1][0] + u * (r[i][0] - r[i - 1][0]), r[i - 1][1] + u * (r[i][1] - r[i - 1][1]))
            return r[-1]
        return None

    @staticmethod
    def _cum(pts):
        L = [0.0]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
        return L

    def head(self, P, t):
        if self.times:
            ts = self.times; out = [P(*self.route[0])]
            for i in range(1, len(ts)):
                if t >= ts[i]:
                    out.append(P(*self.route[i]))
                else:
                    out.append(P(*self.pos(t))); break
            return out
        pts = proj_poly(P, self.route)
        p = clamp((t - self.t0) / self.dur)
        if self.ease:
            p = ease_in_out(p)
        L = self._cum(pts); target = p * L[-1]
        out = [pts[0]]
        for i in range(1, len(pts)):
            if L[i] <= target:
                out.append(pts[i])
            else:
                seg = L[i] - L[i - 1] or 1
                u = (target - L[i - 1]) / seg
                out.append((pts[i - 1][0] + u * (pts[i][0] - pts[i - 1][0]), pts[i - 1][1] + u * (pts[i][1] - pts[i - 1][1])))
                break
        return out

    def draw(self, img, t, P):
        if t < self.t0 - 0.0001 and not self.done:
            return img
        a = life(t, self.t0 - 0.2, self.t1, 0.2)
        s = S(img)
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        wpx = max(1, int(self.w * s))
        if self.done:
            d.line(proj_poly(P, self.done), fill=hexrgb(self.col), width=wpx, joint='curve')
        trail = self.head(P, max(t, self.t0))
        if len(trail) >= 2:
            if self.dashed:
                dash, gap = 16 * s, 11 * s; acc = 0.0; on = True
                for (x0, y0), (x1, y1) in zip(trail, trail[1:]):
                    L = math.hypot(x1 - x0, y1 - y0); pos = 0.0
                    while pos < L:
                        step = min((dash if on else gap) - acc, L - pos)
                        if on:
                            u0, u1 = pos / L, (pos + step) / L
                            d.line([(x0 + (x1 - x0) * u0, y0 + (y1 - y0) * u0), (x0 + (x1 - x0) * u1, y0 + (y1 - y0) * u1)],
                                   fill=hexrgb(self.col), width=wpx)
                        pos += step; acc += step
                        if acc >= (dash if on else gap) - 1e-6:
                            acc = 0.0; on = not on
            else:
                d.line(trail, fill=hexrgb(self.col), width=wpx, joint='curve')
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
        sh.paste((0, 0, 0, 110), mask=lay.split()[3].filter(ImageFilter.GaussianBlur(2 * s)))
        img = over(img, sh); img = over(img, lay)
        if self.icon <= 0:
            return img
        px_ = max(8, int(self.icon * s))
        ic = {'train': _train_icon, 'ship': _ship_icon}.get(self.kind, _footprint_icon)(px_)
        sh2 = Image.new('RGBA', (ic.size[0] + 16, ic.size[1] + 16), (0, 0, 0, 0)); sh2.paste((0, 0, 0, 120), (8, 11), ic)
        sh2 = sh2.filter(ImageFilter.GaussianBlur(4 * s))
        x, y = trail[-1]
        al = max(a, 0.0) if self.t1 else 1.0
        img = paste_sub(img, with_alpha(sh2, al), x, y)
        return paste_sub(img, with_alpha(ic, al), x, y)


# ---------- 8. Ceklis hijau neon (momen "BISA!") ------------------------------
class Check(FX):
    def __init__(self, x, y, t0, t1=None, size=200, col='check', geo=False):
        """x,y = piksel ruang 1080x1920 (geo=False) atau lon,lat (geo=True)."""
        self.x, self.y, self.t0, self.t1, self.size, self.col, self.geo = x, y, t0, t1, size, col, geo

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.05)
        if a <= 0:
            return img
        s = S(img)
        x, y = (P(self.x, self.y) if self.geo else (self.x * s, self.y * s))
        R = self.size * s / 2
        pc = ease_out_cubic((t - self.t0) / 0.6)
        pk = ease_out_cubic((t - self.t0 - 0.45) / 0.35)
        pop = 1 + 0.12 * math.sin(clamp((t - self.t0 - 0.8) / 0.25) * math.pi)
        R *= pop
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        W = max(2, int(R * 0.16)); c = hexrgb(self.col)
        if pc > 0:
            d.arc([x - R, y - R, x + R, y + R], start=-90, end=-90 + 360 * pc, fill=c, width=W)
        if pk > 0:
            p1, p2, p3 = (x - R * 0.45, y + R * 0.02), (x - R * 0.1, y + R * 0.33), (x + R * 0.5, y - R * 0.3)
            if pk < 0.4:
                u = pk / 0.4; d.line([p1, (p1[0] + (p2[0] - p1[0]) * u, p1[1] + (p2[1] - p1[1]) * u)], fill=c, width=W)
            else:
                u = (pk - 0.4) / 0.6
                d.line([p1, p2, (p2[0] + (p3[0] - p2[0]) * u, p2[1] + (p3[1] - p2[1]) * u)], fill=c, width=W, joint='curve')
        img = over(img, with_alpha(glow_layer(lay, 10 * s, 1.8), a))
        return over(img, with_alpha(lay, a))


# ---------- 9. Salju -----------------------------------------------------------
class Snow(FX):
    def __init__(self, t0, t1=None, n=70, seed=3):
        self.t0, self.t1, self.n = t0, t1, n
        r = random.Random(seed)
        self.p = [(r.random(), r.random(), 0.4 + r.random() * 0.8, 3 + r.random() * 7, r.random() * 6.28) for _ in range(n)]

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.6)
        if a <= 0:
            return img
        W, H = img.size; s = S(img)
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for (x0, y0, v, r, ph) in self.p:
            y = ((y0 + (t - self.t0) * v * 0.12) % 1.0) * H
            x = (x0 * W + math.sin(t * 1.3 + ph) * 18 * s) % W
            rr = r * s
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255, 200))
        return over(img, with_alpha(lay.filter(ImageFilter.GaussianBlur(1.6 * s)), a))


# ---------- 10. Karakter kubus es menggigil -----------------------------------
class IceCube(FX):
    def __init__(self, lon, lat, t0, t1=None, size=80, seed=0):
        self.lon, self.lat, self.t0, self.t1, self.size, self.seed = lon, lat, t0, t1, size, seed

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.2)
        if a <= 0:
            return img
        s = S(img); R = self.size * s * (0.5 + 0.5 * ease_out_back((t - self.t0) / 0.4))
        x, y = P(self.lon, self.lat)
        x += math.sin(t * 55 + self.seed) * 2.5 * s   # menggigil
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        o = R * 0.22
        ink = (70, 90, 110, 255)
        # kubus 3/4: sisi atas & kanan
        d.polygon([(x - R / 2, y - R / 2), (x - R / 2 + o, y - R / 2 - o), (x + R / 2 + o, y - R / 2 - o), (x + R / 2, y - R / 2)], fill=(235, 248, 255, 235), outline=ink)
        d.polygon([(x + R / 2, y - R / 2), (x + R / 2 + o, y - R / 2 - o), (x + R / 2 + o, y + R / 2 - o), (x + R / 2, y + R / 2)], fill=(190, 222, 240, 235), outline=ink)
        d.rounded_rectangle([x - R / 2, y - R / 2, x + R / 2, y + R / 2], radius=R * 0.08, fill=(215, 238, 252, 240), outline=ink, width=max(1, int(2 * s)))
        # wajah
        er = R * 0.09
        for ex in (-0.18, 0.18):
            d.ellipse([x + ex * R - er, y - R * 0.12 - er, x + ex * R + er, y - R * 0.12 + er], fill=(255, 255, 255, 255), outline=ink)
            d.ellipse([x + ex * R - er * 0.45, y - R * 0.1 - er * 0.45, x + ex * R + er * 0.45, y - R * 0.1 + er * 0.45], fill=ink)
        # mulut bergemetar (gigi)
        mx0, mx1, my = x - R * 0.22, x + R * 0.22, y + R * 0.17
        zig = [(mx0 + (mx1 - mx0) * i / 6, my + (R * 0.04 if i % 2 else -R * 0.04)) for i in range(7)]
        d.line(zig, fill=ink, width=max(1, int(2 * s)))
        # garis getar
        for k in (-1, 1):
            xx = x + k * (R * 0.75)
            d.arc([xx - R * 0.12, y - R * 0.2, xx + R * 0.12, y + R * 0.2], 100 if k > 0 else -80, 260 if k > 0 else 80, fill=(255, 255, 255, 220), width=max(1, int(2 * s)))
        return over(img, with_alpha(lay, a))


# ---------- 11. Laut membeku ---------------------------------------------------
class FreezeSea(FX):
    """Area laut (geom lon-lat, mis. kotak Selat Bering) berubah jadi es biru
    yang menyebar dari `origin` (lon,lat). `land` = geom daratan yang dikecualikan
    (mis. G.select('RUS') + G.select('USA')) supaya daratan tetap terlihat."""

    def __init__(self, area, t0, dur=1.6, origin=None, land=None, t1=None, alpha=0.85, shards=True, feather=60):
        self.area, self.t0, self.dur, self.origin, self.feather = area, t0, dur, origin, feather
        self.land, self.t1, self.alpha, self.shards = land, t1, alpha, shards

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.05)
        if a <= 0:
            return img
        W, H = img.size
        m = poly_mask(img.size, P, self.area)
        if self.feather:
            m = m.filter(ImageFilter.GaussianBlur(self.feather * S(img)))
        if self.land:
            m = ImageChops.subtract(m, poly_mask(img.size, P, self.land))
        p = ease_in_out((t - self.t0) / self.dur)
        ox, oy = P(*self.origin) if self.origin else (W / 2, H / 2)
        rad = Image.new('L', img.size, 0)
        Rr = p * math.hypot(W, H)
        ImageDraw.Draw(rad).ellipse([ox - Rr, oy - Rr, ox + Rr, oy + Rr], fill=255)
        rad = rad.filter(ImageFilter.GaussianBlur(40 * S(img)))
        m = ImageChops.multiply(m, rad)
        tex = texture('frozen', W, H).copy()
        tex.putalpha(m.point(lambda v: int(v * self.alpha * a)))
        img = over(img, tex)
        if self.shards and 0 < p < 1:
            r = random.Random(11); lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            for _ in range(14):
                ang = r.random() * 6.28; dist = Rr * (0.7 + 0.3 * r.random()); sz = (30 + r.random() * 60) * S(img)
                cx, cy = ox + math.cos(ang) * dist, oy + math.sin(ang) * dist
                d.polygon([(cx, cy - sz), (cx + sz * 0.4, cy), (cx, cy + sz * 0.7), (cx - sz * 0.5, cy)], fill=(40, 100, 170, 120))
            sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); sh.paste(lay, mask=m)
            img = over(img, with_alpha(sh, 1 - p))
        return img


# ---------- 12. Jembatan es / kayu --------------------------------------------
class IceBridge(FX):
    """Jembatan es: balok es bertekstur (biru-putih) dengan tepi terang, muncul berurutan
    dari a ke b dan sedikit 'mengendap' (pop) saat terbentuk. a, b = (lon, lat)."""

    def __init__(self, a, b, t0, dur=0.8, t1=None, width=44, overhang=0.12):
        self.a, self.b, self.t0, self.dur, self.t1 = a, b, t0, dur, t1
        self.width, self.overhang = width, overhang

    def draw(self, img, t, P):
        al = life(t, self.t0, self.t1, 0.05)
        if al <= 0:
            return img
        s = S(img)
        (x0, y0), (x1, y1) = P(*self.a), P(*self.b)
        L = math.hypot(x1 - x0, y1 - y0) or 1
        ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux
        o = self.overhang * L
        x0, y0, L = x0 - ux * o, y0 - uy * o, L + 2 * o
        hw = self.width * s / 2
        n = max(5, int(L / (16 * s)))
        p = clamp((t - self.t0) / self.dur)
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        r = random.Random(5)
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            appear = clamp((p * (n + 2) - i) / 2.0)
            if appear <= 0:
                break
            pop = 1 + 0.25 * math.sin(appear * math.pi) * (1 - appear)
            jit = (r.random() - 0.5) * 0.25 * hw
            w0 = hw * pop * (0.85 + 0.3 * r.random())
            ax, ay = x0 + ux * L * u0, y0 + uy * L * u0 + jit
            bx, by = x0 + ux * L * u1, y0 + uy * L * u1 + jit
            quad = [(ax - nx * w0, ay - ny * w0), (bx - nx * w0, by - ny * w0), (bx + nx * w0, by + ny * w0), (ax + nx * w0, ay + ny * w0)]
            shade = 215 + int(30 * r.random())
            d.polygon(quad, fill=(int(shade * 0.78), int(shade * 0.92), 255, int(240 * appear)),
                      outline=(250, 254, 255, int(255 * appear)))
            d.line([quad[0], quad[1]], fill=(255, 255, 255, int(255 * appear)), width=max(1, int(3 * s)))
            d.line([((ax + bx) / 2 - nx * w0 * 0.5, (ay + by) / 2 - ny * w0 * 0.5),
                    ((ax + bx) / 2 + nx * w0 * 0.3, (ay + by) / 2 + ny * w0 * 0.3)], fill=(150, 200, 235, int(200 * appear)), width=max(1, int(2 * s)))
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); sh.paste((0, 30, 60, 150), mask=lay.split()[3].filter(ImageFilter.GaussianBlur(6 * s)))
        img = over(img, with_alpha(sh, al))
        gl = Image.new('RGBA', img.size, (190, 240, 255, 0)); gl.putalpha(lay.split()[3].filter(ImageFilter.GaussianBlur(10 * s)).point(lambda v: int(v * 0.5)))
        img = over(img, with_alpha(gl, al))
        return over(img, with_alpha(lay, al))


# ---------- 13. Badge sosmed (diisi manual oleh user) --------------------------
class SocialBadge(FX):
    """Ikon sosmed + handle yang mengambang di laut (referensi: IG/YT/TikTok + @nama).
    Ikon diambil dari assets/social/*.png (user mengisi sendiri, urut nama file).
    handle diisi user. Bila folder kosong -> badge TIDAK digambar.
    keys = [(t, x, y, scale, angle), ...] keyframe posisi (ruang 1080x1920)."""

    def __init__(self, keys, t0, t1=None, handle=None, icon_px=70):
        self.keys, self.t0, self.t1, self.handle, self.icon_px = keys, t0, t1, handle, icon_px
        d = os.path.join(ASSETS, 'social')
        self.icons = [Image.open(os.path.join(d, f)).convert('RGBA') for f in sorted(os.listdir(d))
                      if f.lower().endswith('.png')] if os.path.isdir(d) else []

    def _kf(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1:]
        for k0, k1 in zip(ks, ks[1:]):
            if t <= k1[0]:
                u = ease_in_out((t - k0[0]) / (k1[0] - k0[0]))
                return tuple(a + (b - a) * u for a, b in zip(k0[1:], k1[1:]))
        return ks[-1][1:]

    def draw(self, img, t, P):
        if not self.icons and not self.handle:
            return img
        a = life(t, self.t0, self.t1, 0.25)
        if a <= 0:
            return img
        s = S(img); x, y, sc, ang = self._kf(t)
        ip = int(self.icon_px * sc * s); gap = int(ip * 0.18)
        n = len(self.icons)
        tw = max(1, n * ip + (n - 1) * gap)
        tile = Image.new('RGBA', (tw + 40, ip + int(ip * 0.8) + 40), (0, 0, 0, 0))
        for i, ic in enumerate(self.icons):
            r = ic.resize((ip, ip), Image.LANCZOS); tile.paste(r, (20 + i * (ip + gap), 20), r)
        if self.handle:
            f = font(ip * 0.55); d = ImageDraw.Draw(tile)
            ww = f.getlength(self.handle)
            d.text(((tile.size[0] - ww) / 2, 20 + ip + ip * 0.08), self.handle, font=f, fill=(255, 255, 255, 255),
                   stroke_width=max(1, int(2 * s)), stroke_fill=(20, 30, 40, 255))
        tile = tile.rotate(-ang, resample=Image.BICUBIC, expand=True)
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        lay.paste(tile, (int(x * s - tile.size[0] / 2), int(y * s - tile.size[1] / 2)), tile)
        return over(img, with_alpha(lay, a))


# ---------- 14. Rute penuh menyala (zoom-out akhir) ---------------------------
class RouteGlow(FX):
    """Rute menyala. dur=None -> langsung penuh (fade-in); dur=detik -> garis tumbuh dari awal ke akhir."""
    def __init__(self, route, t0, col='route_glow', w=5, t1=None, dur=None):
        self.route, self.t0, self.col, self.w, self.t1, self.dur = route, t0, col, w, t1, dur

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.5 if not self.dur else 0.05)
        if a <= 0:
            return img
        s = S(img)
        pts = proj_poly(P, self.route)
        if self.dur:
            p = ease_in_out((t - self.t0) / self.dur)
            L = [0.0]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
            tgt = p * L[-1]; out = [pts[0]]
            for i in range(1, len(pts)):
                if L[i] <= tgt:
                    out.append(pts[i])
                else:
                    u = (tgt - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
                    out.append((pts[i - 1][0] + u * (pts[i][0] - pts[i - 1][0]), pts[i - 1][1] + u * (pts[i][1] - pts[i - 1][1]))); break
            pts = out
        if len(pts) < 2:
            return img
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).line(pts, fill=hexrgb(self.col), width=max(1, int(self.w * s)), joint='curve')
        img = over(img, with_alpha(glow_layer(lay, 7 * s, 2.2), a))
        return over(img, with_alpha(lay, a))


# ---------- 15. Finale: peta jadi kartu + angka neon --------------------------
class GridFinale(FX):
    """Efek layar penuh (post), pasang di shot terakhir.
    Mulai t0, frame peta mengecil (dur) menjadi KARTU bersudut membulat dengan bayangan
    dan garis cahaya cyan. Di belakangnya ada latar `bg`:
      'blur' (default): versi peta yang diperbesar, di-blur & digelapkan (bersih, tanpa kotak)
      'grid'          : latar grid navy (persis referensi)
    Teks neon besar pop di t_text, di tengah kartu. Piksel transparan di frame
    (di luar peta) tidak ikut kartu: kartu = bbox area peta."""
    post = True

    def __init__(self, t0, text='22.500 KM', t_text=None, dur=0.7, scale_to=0.86, bg='blur',
                 radius=38, cell=120, size=120, sub=None, t1=None, t_sub=None):
        self.t0, self.text, self.dur, self.scale_to, self.bg = t0, text, dur, scale_to, bg
        self.t_text = t0 + 0.4 if t_text is None else t_text
        self.radius, self.cell, self.size, self.sub = radius, cell, size, sub
        self.t1, self.t_sub = t1, t_sub

    def _bg(self, img, src):
        s = S(img); W, H = img.size
        if self.bg == 'grid':
            bg = Image.new('RGBA', img.size, hexrgb('grid_bg')); d = ImageDraw.Draw(bg); c = self.cell * s
            for i in range(int(W / c) + 2):
                d.line([(i * c, 0), (i * c, H)], fill=hexrgb('grid_line'), width=max(1, int(3 * s)))
            for j in range(int(H / c) + 2):
                d.line([(0, j * c), (W, j * c)], fill=hexrgb('grid_line'), width=max(1, int(3 * s)))
            return bg
        sw, sh = src.size; k = max(W / sw, H / sh) * 1.15
        big = src.convert('RGB').resize((int(sw * k), int(sh * k)), Image.BILINEAR)
        big = big.crop(((big.width - W) // 2, (big.height - H) // 2, (big.width - W) // 2 + W, (big.height - H) // 2 + H))
        small = big.resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
        a = np.asarray(small, np.float32) * 0.42 + np.array([4, 14, 24], np.float32)
        # vinyet
        yy, xx = np.mgrid[0:H, 0:W]
        v = 1 - 0.45 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
        a = np.clip(a * v[..., None], 0, 255).astype(np.uint8)
        return Image.fromarray(a, 'RGB').convert('RGBA')

    def draw(self, img, t, P=None):
        if t < self.t0:
            return img
        t1 = getattr(self, 't1', None)
        if t1 is not None and t >= t1 + 0.6:
            return img
        s = S(img); W, H = img.size
        p = ease_in_out((t - self.t0) / self.dur)
        if t1 is not None and t > t1:
            p = min(p, 1 - ease_in_out((t - t1) / 0.6))
        bb = img.split()[3].point(lambda v: 255 if v > 200 else 0).getbbox() or (0, 0, W, H)
        src = img.crop(bb)
        out = self._bg(img, src)
        out = Image.blend(img.convert('RGBA'), out, p) if p < 1 else out
        # kartu
        k = 1 - (1 - self.scale_to) * p
        cw = int(src.width * k * min(1.0, W / src.width)); chh = int(src.height * k * min(1.0, W / src.width))
        card = src.resize((max(1, cw), max(1, chh)), Image.LANCZOS).convert('RGBA')
        rad = int(self.radius * s * p)
        mk = Image.new('L', card.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=rad, fill=255)
        cx, cy = (W - card.width) // 2, int((bb[1] + bb[3]) / 2 - card.height / 2 + (H / 2 - (bb[1] + bb[3]) / 2) * p)
        # bayangan + cahaya tepi
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); shm = Image.new('L', img.size, 0)
        ImageDraw.Draw(shm).rounded_rectangle([cx, cy + 14 * s, cx + card.width, cy + card.height + 14 * s], radius=rad, fill=int(170 * p))
        sh.putalpha(shm.filter(ImageFilter.GaussianBlur(22 * s))); out = over(out, sh)
        cardl = Image.new('RGBA', img.size, (0, 0, 0, 0)); cardl.paste(card, (cx, cy), mk); out = over(out, cardl)
        if p > 0:
            gl = Image.new('RGBA', img.size, (0, 0, 0, 0))
            ImageDraw.Draw(gl).rounded_rectangle([cx, cy, cx + card.width, cy + card.height], radius=rad,
                                                 outline=(127, 243, 255, int(230 * p)), width=max(1, int(4 * s)))
            out = over(out, glow_layer(gl, 9 * s, 2.0)); out = over(out, gl)
        fade = 1.0 if t1 is None or t <= t1 else max(0.0, 1 - (t - t1) / 0.35)
        if t >= self.t_text and fade > 0:
            u = (t - self.t_text)
            sc = 0.5 + 0.5 * ease_out_back(u / 0.35)
            f = font(self.size * s * min(sc, 1.0) if sc < 0.98 else self.size * s)
            bbt = f.getbbox(self.text); tw, th = bbt[2] - bbt[0], bbt[3] - bbt[1]
            lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            tx = (W - tw) / 2 - bbt[0] - (1 - ease_out_cubic(u / 0.3)) * W * 0.25
            ty = cy + card.height / 2 - th / 2 - bbt[1]
            dl.text((tx, ty), self.text, font=f, fill=hexrgb('#eaffff'), stroke_width=max(1, int(4 * s)), stroke_fill=hexrgb('#1ab8d6'))
            subs = self.sub if isinstance(self.sub, (list, tuple)) else ([(self.sub, self.t_text + 0.25)] if self.sub else [])
            f2 = font_sans(self.size * 0.36 * s, 800); yy = ty + th + 34 * s
            for txt, ts_ in subs:
                if t >= ts_:
                    k2 = clamp((t - ts_) / 0.3); w2 = f2.getlength(txt)
                    dl.text(((W - w2) / 2, yy + (1 - k2) * 20 * s), txt, font=f2, fill=(235, 250, 255, int(255 * k2)),
                            stroke_width=max(1, int(3 * s)), stroke_fill=(10, 60, 80, int(255 * k2)))
                yy += self.size * 0.48 * s
            lay = with_alpha(lay, fade)
            out = over(out, glow_layer(Image.composite(Image.new('RGBA', img.size, hexrgb('km')), Image.new('RGBA', img.size, (0, 0, 0, 0)), lay.split()[3]), 22 * s, 2.5))
            out = over(out, lay)
        return out


Finale = GridFinale   # nama alias


# ---------- 16. Tint wilayah raksasa (mis. seluruh Rusia jadi teal) -----------
class Tint(HL):
    def __init__(self, geom, t0, col='teal_tint', alpha=0.45, t1=None):
        super().__init__(geom, t0, col, alpha, None, t1, 0.5, edge=False, glow=False, punch=False)


# ---------- 17. Chip: label kotak di layar / di peta -------------------------
class Chip(FX):
    """Kotak label membulat (mis. 'DIBUKA 2021', '± 1 JAM'). Posisi: xy=(x,y) layar 1080x1920
    atau lonlat=(lon,lat) + dy (piksel) di atas titik itu. Pop dengan overshoot."""

    def __init__(self, text, t0, t1=None, xy=None, lonlat=None, dy=-70, col='#ffffff', fg='#0b2433', size=40, emoji=None):
        self.text, self.t0, self.t1, self.xy, self.lonlat, self.dy = text, t0, t1, xy, lonlat, dy
        self.col, self.fg, self.size, self.emoji = col, fg, size, emoji

    def _tile(self, s):
        if getattr(self, '_tk', None) == round(s, 4):
            return self._tc
        f = font_sans(self.size * s, 800); tw = f.getlength(self.text)
        ew = 0; em = None
        if self.emoji:
            try:
                ef = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
                em = Image.new('RGBA', (136, 136), (0, 0, 0, 0)); ImageDraw.Draw(em).text((4, 4), self.emoji, font=ef, embedded_color=True)
                ew = int(self.size * 1.25 * s); em = em.resize((ew, ew), Image.LANCZOS)
            except OSError:
                em = None; ew = 0
        padx, pady = 26 * s, 16 * s; h = int(self.size * s * 1.25 + 2 * pady); w = int(tw + 2 * padx + (ew + 12 * s if em else 0))
        tile = Image.new('RGBA', (w + 30, h + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(tile)
        sh = Image.new('RGBA', tile.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([15, 21, 15 + w, 21 + h], radius=h // 2, fill=(0, 0, 0, 120))
        tile.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6 * s)))
        d.rounded_rectangle([15, 15, 15 + w, 15 + h], radius=h // 2, fill=hexrgb(self.col))
        x0 = 15 + padx
        if em:
            tile.alpha_composite(em, (int(x0), int(15 + (h - ew) / 2))); x0 += ew + 12 * s
        bb = f.getbbox(self.text)
        d.text((x0, 15 + (h - (bb[3] - bb[1])) / 2 - bb[1]), self.text, font=f, fill=hexrgb(self.fg))
        self._tc, self._tk = tile, round(s, 4)
        return tile

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.1)
        if a <= 0:
            return img
        s = S(img); tile = self._tile(s)
        sc = 0.5 + 0.5 * ease_out_back((t - self.t0) / 0.35)
        if abs(sc - 1) > 1e-3:
            tile = tile.resize((max(1, int(tile.size[0] * sc)), max(1, int(tile.size[1] * sc))), Image.BICUBIC)
        if self.xy:
            x, y = self.xy[0] * s, self.xy[1] * s
        else:
            x, y = P(*self.lonlat); y += self.dy * s
        return paste_sub(img, with_alpha(tile, a), x, y)


# ---------- 18. Tanda silang merah (perbatasan ditutup) -----------------------
class Cross(FX):
    def __init__(self, lon, lat, t0, t1=None, size=70):
        self.lon, self.lat, self.t0, self.t1, self.size = lon, lat, t0, t1, size

    def draw(self, img, t, P):
        a = life(t, self.t0, self.t1, 0.05)
        if a <= 0:
            return img
        s = S(img); R_ = self.size * s / 2 * (0.3 + 0.7 * ease_out_back((t - self.t0) / 0.3, 2.2))
        n = int(R_ * 2 + 24); c = n / 2
        tile = Image.new('RGBA', (n * 3, n * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(tile); k = 3
        d.ellipse([(c - R_) * k, (c - R_) * k, (c + R_) * k, (c + R_) * k], fill=(214, 32, 44, 255), outline=(255, 255, 255, 255), width=int(4 * s * k))
        q = R_ * 0.42
        for (ax, ay, bx, by) in [(-q, -q, q, q), (-q, q, q, -q)]:
            d.line([((c + ax) * k, (c + ay) * k), ((c + bx) * k, (c + by) * k)], fill=(255, 255, 255, 255), width=int(R_ * 0.22 * k))
        tile = tile.resize((n, n), Image.LANCZOS)
        g = Image.new('RGBA', tile.size, (255, 60, 60, 0)); g.putalpha(tile.split()[3].filter(ImageFilter.GaussianBlur(8 * s)).point(lambda v: int(v * 0.6)))
        x, y = P(self.lon, self.lat)
        img = paste_sub(img, with_alpha(g, a), x, y)
        return paste_sub(img, with_alpha(tile, a), x, y)


# ----------------------------------------------------------------------------
# Entry point untuk engine
# ----------------------------------------------------------------------------
def draw_all(img, fx_list, t, P):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    for fx in fx_list or []:
        if not fx.post:
            img = fx.draw(img, t, P)
    return img


def post_all(img, fx_list, t):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    for fx in fx_list or []:
        if fx.post:
            img = fx.draw(img, t, None)
    return img


__all__ = ['PAL', 'HL', 'Tint', 'NeonArc', 'NeonLine', 'BigLabel', 'LeaderLabel', 'Pin', 'Walker', 'Check',
           'Snow', 'IceCube', 'FreezeSea', 'IceBridge', 'SocialBadge', 'RouteGlow', 'GridFinale', 'Finale',
           'draw_all', 'post_all', 'font', 'font_sans', 'Chip', 'Cross', 'paste_sub', 'text_tile']
