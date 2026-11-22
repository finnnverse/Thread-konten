"""Core renderer: satellite-style map camera, cairo overlays, captions, sprites."""
import os, math, json, functools, numpy as np, cairocffi as cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter
Image.MAX_IMAGE_PIXELS = None
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
REFZ = 10
COL = {'white': (255, 255, 255), 'accent': (255, 176, 32), 'danger': (255, 84, 112),
       'good': (74, 222, 128), 'water': (94, 234, 212), 'ink': (11, 27, 43)}

def hexc(c, a=1.0):
    c = COL.get(c, c) if isinstance(c, str) else c
    return (c[0] / 255, c[1] / 255, c[2] / 255, a)

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(u): u = clamp(u); return u * u * (3 - 2 * u)
def ease_io(u): u = clamp(u); return 0.5 - 0.5 * math.cos(math.pi * u)
def ease_out(u): u = clamp(u); return 1 - (1 - u) ** 3
def back(u):
    u = clamp(u); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2
def pop(t, t0, dur=0.28): return 0.0 if t < t0 else back((t - t0) / dur)
def fade(t, t0, t1=None, d=0.2):
    a = clamp((t - t0) / d)
    if t1 is not None: a = min(a, clamp((t1 - t) / d))
    return a

# ---------- mercator ----------
def MX(lon, z=REFZ): return (lon + 180) / 360 * 256 * 2 ** z
def MY(lat, z=REFZ):
    r = math.radians(lat); return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 256 * 2 ** z

class Cam:
    def __init__(self, lon, lat, span):
        self.cx, self.cy = MX(lon), MY(lat)
        self.sp = span / 360 * 256 * 2 ** REFZ   # width in REFZ px
        self.ox = self.oy = 0.0
    def pt(self, lon, lat):
        k = W / self.sp
        return (MX(lon) - self.cx) * k + W / 2 + self.ox, (MY(lat) - self.cy) * k + H / 2 + self.oy
    def px_per_deg(self): return W / (self.sp / (256 * 2 ** REFZ) * 360)

class CamPath:
    """moves: list of (t0, t1, lon, lat, span). Holds between moves, slow push-in drift."""
    def __init__(self, start, moves, drift=0.012):
        self.start = start; self.moves = moves; self.drift = drift; self.punches = []; self.shakes = []
    def at(self, t):
        cx, cy, ls = MX(self.start[0]), MY(self.start[1]), math.log(self.start[2]); tend = 0
        for (t0, t1, lon, lat, span) in self.moves:
            tx, ty, tl = MX(lon), MY(lat), math.log(span)
            if t >= t1: cx, cy, ls, tend = tx, ty, tl, t1; continue
            if t > t0:
                u = ease_io((t - t0) / (t1 - t0))
                # zoom-out bump for long moves
                d = math.hypot(tx - cx, ty - cy) / (math.exp(min(ls, tl)) / 360 * 256 * 2 ** REFZ)
                bump = min(0.5, 0.08 * d) * math.sin(math.pi * u)
                cx, cy, ls = cx + (tx - cx) * u, cy + (ty - cy) * u, ls + (tl - ls) * u + bump
                tend = None
            break
        span = math.exp(ls)
        if tend is not None: span *= 1 - self.drift * min(t - tend, 5)
        for tp in self.punches:
            if tp - 0.05 < t < tp + 0.6: span *= 1 - 0.07 * math.exp(-((t - tp) / 0.16) ** 2)
        c = Cam(0, 0, span); c.cx, c.cy = cx, cy
        for tp in self.shakes:
            if tp <= t < tp + 0.45:
                a = 14 * (1 - (t - tp) / 0.45)
                c.ox = a * math.sin(t * 91); c.oy = a * math.cos(t * 73)
        return c

# ---------- basemap ----------
class Level:
    def __init__(self, name):
        z, x0, y0, w, h = map(int, open(os.path.join(S, 'levels', name + '_meta.txt')).read().split())
        self.z, self.x0, self.y0, self.w, self.h = z, x0, y0, w, h
        self.rgb = Image.open(os.path.join(S, 'levels', name + '_rgb.png')).convert('RGB')
        self._shelf = None; self._e = None; self.name = name
    @property
    def shelf(self):
        if self._shelf is None: self._shelf = Image.open(os.path.join(S, 'levels', self.name + '_shelf.png')).convert('RGB')
        return self._shelf
    @property
    def e(self):
        if self._e is None: self._e = np.load(os.path.join(S, 'levels', self.name + '_e.npy'), mmap_mode='r')
        return self._e

LEVELS = None
def levels():
    global LEVELS
    if LEVELS is None: LEVELS = sorted([Level(n) for n in ['z5', 'z6', 'z7', 'z9', 'z10']], key=lambda l: -l.z)
    return LEVELS

FLOOD = np.array([60, 170, 200], np.float32)
def map_image(cam, sea=0.0):
    pad = 4
    for L in levels():
        f = 2 ** (L.z - REFZ); w = cam.sp * f; h = w * H / W
        cx = (cam.cx - cam.ox / (W / cam.sp)) * f - L.x0; cy = (cam.cy - cam.oy / (W / cam.sp)) * f - L.y0
        box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        if w <= 2700 and box[0] >= pad and box[1] >= pad and box[2] <= L.w - pad and box[3] <= L.h - pad: break
    if abs(sea) < 0.5:
        return L.rgb.transform((W, H), Image.EXTENT, box, Image.BILINEAR)
    ix0, iy0 = int(box[0]) - 1, int(box[1]) - 1; ix1, iy1 = int(box[2]) + 2, int(box[3]) + 2
    rgb = np.asarray(L.rgb.crop((ix0, iy0, ix1, iy1)), np.float32)
    e = np.asarray(L.e[iy0:iy1, ix0:ix1], np.float32)
    if sea < 0:
        shelf = np.asarray(L.shelf.crop((ix0, iy0, ix1, iy1)), np.float32)
        m = np.clip((e - sea) / 8, 0, 1) * (e <= 0)
        out = rgb * (1 - m[..., None]) + shelf * m[..., None]
    else:
        m = np.clip((sea - e) / max(2, sea * 0.4), 0, 1) * (e > 0) * 0.8
        out = rgb * (1 - m[..., None]) + FLOOD * m[..., None]
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    return im.transform((W, H), Image.EXTENT, (box[0] - ix0, box[1] - iy0, box[2] - ix0, box[3] - iy0), Image.BILINEAR)

# ---------- cairo helpers ----------
def pil_to_surface(im):
    im = im.convert('RGBA'); a = np.asarray(im, np.float32)
    al = a[..., 3:4] / 255.0
    pm = np.empty(a.shape, np.uint8)
    pm[..., 0] = (a[..., 2] * al[..., 0]).astype(np.uint8)
    pm[..., 1] = (a[..., 1] * al[..., 0]).astype(np.uint8)
    pm[..., 2] = (a[..., 0] * al[..., 0]).astype(np.uint8)
    pm[..., 3] = a[..., 3].astype(np.uint8)
    buf = bytearray(pm.tobytes())
    s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)
    s._keep = buf
    return s

def rgb_surface(im):
    a = np.asarray(im.convert('RGB'))
    b = np.empty((a.shape[0], a.shape[1], 4), np.uint8)
    b[..., 0] = a[..., 2]; b[..., 1] = a[..., 1]; b[..., 2] = a[..., 0]; b[..., 3] = 255
    buf = bytearray(b.tobytes())
    s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, a.shape[1], a.shape[0], a.shape[1] * 4)
    s._keep = buf
    return s

@functools.lru_cache(None)
def sprite(name):
    return cairo.ImageSurface.create_from_png(os.path.join(S, 'sprites', name + '.png'))

def draw_surface(ctx, surf, x, y, width, rot=0.0, alpha=1.0, flipx=False, anchor=(0.5, 0.5), sy=1.0):
    if alpha <= 0.003 or width <= 1: return
    sw, sh = surf.get_width(), surf.get_height(); k = width / sw
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    ctx.scale(-k if flipx else k, k * sy)
    ctx.set_source_surface(surf, -sw * anchor[0], -sh * anchor[1])
    ctx.paint_with_alpha(alpha); ctx.restore()

def draw_sprite(ctx, name, x, y, width, **kw): draw_surface(ctx, sprite(name), x, y, width, **kw)

# ---------- text ----------
FONT_DIR = os.path.join(S, 'assets')
@functools.lru_cache(None)
def font(kind, size):
    if kind == 'punch': return ImageFont.truetype(os.path.join(FONT_DIR, 'LilitaOne-Regular.ttf'), size)
    f = ImageFont.truetype(os.path.join(FONT_DIR, 'Baloo2[wght].ttf'), size)
    try: f.set_variation_by_axes([800])
    except Exception: pass
    return f

@functools.lru_cache(4096)
def text_surface(text, kind, size, color, stroke=5, shadow=True, maxw=1000):
    while True:
        f = font(kind, size); bb = f.getbbox(text, stroke_width=stroke)
        if bb[2] - bb[0] <= maxw or size < 30: break
        size = int(size * 0.92)
    pad = 30; tw, th = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - bb[0], pad - bb[1] + 7), text, font=f, fill=(4, 12, 22, 170), stroke_width=stroke + 2, stroke_fill=(4, 12, 22, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(9)))
    c = COL.get(color, color) if isinstance(color, str) else color
    ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), text, font=f, fill=tuple(c) + (255,), stroke_width=stroke, stroke_fill=(11, 27, 43, 255))
    return pil_to_surface(im)

def draw_text(ctx, text, x, y, size, color='white', kind='body', scale=1.0, alpha=1.0, stroke=5, shadow=True, rot=0.0, maxw=1000):
    if size < 4 or scale <= 0.01 or alpha <= 0.003: return 0
    s = text_surface(text, kind, int(size), color if isinstance(color, str) else tuple(color), stroke, shadow, maxw)
    draw_surface(ctx, s, x, y, s.get_width() * scale, rot=rot, alpha=alpha)
    return s.get_height()

# ---------- vector fx ----------
def poly_path(ctx, cam, ring):
    for i, (lon, lat) in enumerate(ring):
        x, y = cam.pt(lon, lat)
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.close_path()

def fill_island(ctx, cam, rings, color, a=0.55, glow=True):
    if a <= 0: return
    for r in rings: poly_path(ctx, cam, r)
    ctx.set_source_rgba(*hexc(color, a * 0.85)); ctx.fill_preserve()
    if glow:
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgba(*hexc(color, a * 0.35)); ctx.set_line_width(16); ctx.stroke_preserve()
        ctx.set_source_rgba(*hexc((255, 245, 220), a * 0.95)); ctx.set_line_width(3.5); ctx.stroke()
    else: ctx.new_path()

def ring(ctx, x, y, r, color, a=1.0, w=6, dash=None):
    ctx.new_path(); ctx.arc(x, y, max(1, r), 0, 2 * math.pi)
    if dash: ctx.set_dash(dash)
    ctx.set_source_rgba(*hexc(color, a)); ctx.set_line_width(w); ctx.stroke(); ctx.set_dash([])

def pulse(ctx, x, y, t, t0, color='accent', r0=20, r1=120, period=1.1, n=2):
    if t < t0: return
    for i in range(n):
        u = ((t - t0) / period + i / n) % 1.0
        ring(ctx, x, y, r0 + (r1 - r0) * u, color, (1 - u) * 0.9, 5)

def polyline_partial(ctx, pts, frac):
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = L[-1] * clamp(frac); ctx.new_path(); ctx.move_to(*pts[0]); head = pts[0]; ang = 0
    for i in range(1, len(pts)):
        if L[i] <= tot: ctx.line_to(*pts[i]); head = pts[i]; ang = math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0])
        else:
            u = (tot - L[i - 1]) / max(1e-6, L[i] - L[i - 1]); a, b = pts[i - 1], pts[i]
            head = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u); ctx.line_to(*head)
            ang = math.atan2(b[1] - a[1], b[0] - a[0]); break
    return head, ang

def smooth(pts, n=12):
    """Catmull-Rom smoothing of screen points."""
    if len(pts) < 3: return pts
    P = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1]); return out

def arrow_label(ctx, text, x, y, tx, ty, color='white', size=40, a=1.0, sc=1.0):
    """label at (x,y) with curved arrow to (tx,ty)"""
    if a <= 0: return
    draw_text(ctx, text, x, y, size, color, 'body', scale=sc, alpha=a, stroke=4)
    sx, sy = x + (tx - x) * 0.25, y + (ty - y) * 0.25 + 22
    mx, my = (sx + tx) / 2 + (ty - sy) * 0.25, (sy + ty) / 2 - (tx - sx) * 0.25
    ctx.new_path(); ctx.move_to(sx, sy); ctx.curve_to(mx, my, mx, my, tx, ty)
    ctx.set_source_rgba(*hexc(color, a)); ctx.set_line_width(4); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ang = math.atan2(ty - my, tx - mx)
    for s in (-1, 1):
        ctx.move_to(tx, ty); ctx.line_to(tx - 18 * math.cos(ang + s * 0.5), ty - 18 * math.sin(ang + s * 0.5))
    ctx.stroke()

def qmark(ctx, x, y, r, t, a=1.0):
    ring(ctx, x, y, r, 'white', a, 5, dash=[14, 10])
    draw_text(ctx, '?', x, y + 4, int(r * 1.3), 'accent', 'punch', alpha=a, scale=1 + 0.05 * math.sin(t * 6))

def red_x(ctx, x, y, s, a=1.0, prog=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i, (dx0, dy0, dx1, dy1) in enumerate([(-1, -1, 1, 1), (1, -1, -1, 1)]):
        p = clamp(prog * 2 - i)
        if p <= 0: continue
        ctx.move_to(x + dx0 * s, y + dy0 * s); ctx.line_to(x + dx0 * s + (dx1 - dx0) * s * p, y + dy0 * s + (dy1 - dy0) * s * p)
        ctx.set_source_rgba(*hexc((20, 10, 10), a * 0.5)); ctx.set_line_width(s * 0.42); ctx.stroke_preserve()
        ctx.set_source_rgba(*hexc('danger', a)); ctx.set_line_width(s * 0.3); ctx.stroke()

def rrect(ctx, x, y, w, h, r):
    ctx.new_path(); ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); ctx.close_path()

def vignette(ctx, a=0.5):
    g = cairo.RadialGradient(W / 2, H * 0.48, H * 0.25, W / 2, H * 0.5, H * 0.72)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0.01, 0.03, 0.07, a)
    ctx.set_source(g); ctx.paint()
    g = cairo.LinearGradient(0, 0, 0, 560)
    g.add_color_stop_rgba(0, 0.01, 0.04, 0.09, 0.55); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.rectangle(0, 0, W, 560); ctx.fill()

# ---------- captions ----------
CAP_Y = 250
def draw_caption(ctx, t, cap):
    """cap = dict(t0,t1,l1,l2,c2,t2,big)"""
    t0, t1 = cap['t0'], cap['t1']
    if not (t0 <= t < t1): return
    out = clamp((t1 - t) / 0.12)
    y = CAP_Y
    if cap.get('l1'):
        s = 0.85 + 0.15 * pop(t, t0, 0.22)
        h = draw_text(ctx, cap['l1'], W / 2, y, 64, 'white', 'body', scale=s, alpha=clamp((t - t0) / 0.08) * out)
        y += 74
    if cap.get('l2') and t >= cap['t2']:
        big = cap.get('big', False); size = 128 if big else 92
        s = 0.6 + 0.4 * pop(t, cap['t2'], 0.3)
        draw_text(ctx, cap['l2'], W / 2, y + (40 if big else 22), size, cap.get('c2', 'accent'), 'punch', scale=s,
                  alpha=clamp((t - cap['t2']) / 0.06) * out, stroke=6)

def caption_list(items, tail):
    caps = []
    for i, it in enumerate(items):
        t0 = it[0]; t1 = items[i + 1][0] if i + 1 < len(items) else tail
        l2 = it[2] if len(it) > 2 else None
        c2, big = 'accent', False
        if l2 and '|' in l2:
            parts = l2.split('|'); l2 = parts[0]; c2 = parts[1]; big = len(parts) > 2
        caps.append(dict(t0=t0, t1=t1, l1=it[1], l2=l2, t2=it[3] if len(it) > 3 else t0, c2=c2, big=big))
    return caps
