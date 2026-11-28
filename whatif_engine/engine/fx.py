"""Effects: neon text (measured 2-layer glow), 3D-perspective labels with per-letter reveal,
arcs/trails, streak rain, easing curves."""
import math
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image, ImageDraw
from .text import font, hexa, blit, blit_sub

# ----------------------------------------------------------------------------- easing
def clamp01(x): return max(0.0, min(1.0, x))
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp01(x); return x ** 3
def ease_io(x): x = clamp01(x); return 0.5 - 0.5 * math.cos(math.pi * x)
def ease_out_back(x, s=1.9):
    x = clamp01(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2


def pop_scale(t, t0, dur=0.15, out_t=None, out_dur=0.25):
    """measured pop: 0->1.15->1 in ~0.15 s (ease-out-back); optional scale-down exit."""
    if t < t0:
        return 0.0
    s = ease_out_back((t - t0) / dur)
    if out_t is not None and t > out_t:
        s *= 1 - ease_in((t - out_t) / out_dur)
    return max(0.0, s)


# ----------------------------------------------------------------------------- glow
def glow_rgba(alpha, core_hex, glow_hex=None, s1=5.0, a1=0.9, s2=20.0, a2=0.5, core_white=0.0):
    """Measured neon: half-intensity at +-7px, tenth at +-22px (720p) -> sigma 5 & 20 @1080p.
    Returns RGBA (straight alpha) with core colour on glyphs and coloured halo around."""
    core = np.array(hexa(core_hex)[:3], np.float32) / 255
    gl = np.array(hexa(glow_hex or core_hex)[:3], np.float32) / 255
    g1 = cv2.GaussianBlur(alpha, (0, 0), s1, borderType=cv2.BORDER_CONSTANT) * a1
    sm = cv2.resize(alpha, (max(1, alpha.shape[1] // 4), max(1, alpha.shape[0] // 4)), interpolation=cv2.INTER_AREA)
    g2 = cv2.resize(cv2.GaussianBlur(sm, (0, 0), s2 / 4, borderType=cv2.BORDER_CONSTANT), (alpha.shape[1], alpha.shape[0])) * a2
    halo = np.clip(g1 + g2, 0, 1)
    a = np.clip(alpha + halo * (1 - alpha), 0, 1)
    c = core * (1 - core_white) + core_white
    rgb = (c[None, None] * alpha[..., None] + gl[None, None] * (halo * (1 - alpha))[..., None]) / np.maximum(a[..., None], 1e-4)
    return np.concatenate([rgb, a[..., None]], 2).astype(np.float32)


# ----------------------------------------------------------------------------- neon label
class NeonLabel:
    """3D neon label (reference: 'OHIO CLASS SUBMARINES', 'THE DEAD HAND SYSTEM', 'WORLD W#R 3.0').
    in: per-letter reveal left->right over `in_dur` (0.45 s) with an entry flash;
    hold: tracking slowly widens; out: letters spread wider + fade (0.5-0.7 s)."""

    def __init__(self, text, t_in, t_out, pos, color="#06EBFF", glow=None, size=64, weight=650,
                 tracking=0.32, quotes=True, angle=0.0, persp=0.0, in_dur=0.45, out_dur=0.6,
                 family="jost", anchor="screen", flash=True, wave=0.0):
        self.text = (f"‘{text}’" if quotes else text)
        self.t_in, self.t_out, self.pos = t_in, t_out, pos
        self.color, self.glow, self.size, self.weight = color, glow, size, weight
        self.tracking, self.angle, self.persp = tracking, angle, persp
        self.in_dur, self.out_dur, self.family, self.anchor, self.flash, self.wave = in_dur, out_dur, family, anchor, flash, wave

    def _layout(self, track):
        f = font(self.family, self.size * 2, self.weight)
        lines = self.text.split("\n"); out = []
        for ln in lines:
            xs, x = [], 0.0
            for ch in ln:
                xs.append(x); x += f.getlength(ch) + track * self.size * 2
            out.append((ln, xs, x - track * self.size * 2))
        return f, out

    def render(self, t):
        if t < self.t_in or t > self.t_out + self.out_dur:
            return None
        u_in = (t - self.t_in) / self.in_dur
        u_out = clamp01((t - self.t_out) / self.out_dur)
        hold = clamp01((t - self.t_in - self.in_dur) / max(0.01, self.t_out - self.t_in - self.in_dur))
        track = self.tracking + 0.04 * hold + 0.35 * ease_in(u_out)
        f, lines = self._layout(track)
        asc, desc = f.getmetrics(); pad = 80; lh = int((asc + desc) * 0.92)
        total = max(l[2] for l in lines)
        W, H = int(total + 2 * pad) // 2 * 2, int(lh * len(lines) + desc + 2 * pad) // 2 * 2
        chars = [(li, i, ch) for li, (ln, xs, w) in enumerate(lines) for i, ch in enumerate(ln)]
        n = len(chars)
        im = Image.new("L", (W, H)); d = ImageDraw.Draw(im)
        for k, (li, i, ch) in enumerate(chars):
            ai = clamp01((u_in * (n + 3) - k) / 3.0)
            ao = 1 - clamp01((ease_in(u_out) * (n + 4) - (n - 1 - k) * 0.6) / 3.0) if u_out > 0 else 1
            al = ai * ao
            if al <= 0.01 or ch == " ":
                continue
            ln, xs, w = lines[li]
            dy = math.sin(k * 0.55 + t * 3) * self.wave * self.size
            d.text((pad + (total - w) / 2 + xs[i], pad + li * lh + dy), ch, font=f, fill=int(255 * al))
        a = cv2.resize(np.asarray(im, np.float32) / 255, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        flash = 1.0
        if self.flash and 0 <= u_in <= 1.2:
            flash = 1 + 0.9 * math.exp(-((u_in - 0.35) / 0.25) ** 2)      # measured overshoot (~2x pixels)
        rgba = glow_rgba(a, self.color, self.glow, a1=0.9 * flash, a2=0.5 * flash, core_white=0.15)
        if self.persp:
            h, w = rgba.shape[:2]; k = self.persp
            src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
            dst = np.float32([[0, h * k * 0.5], [w, 0], [w, h], [0, h - h * k * 0.5]])
            P = cv2.getPerspectiveTransform(src, dst)
            pm = rgba.copy(); pm[..., :3] *= pm[..., 3:4]
            pm = cv2.warpPerspective(pm, P, (w, h), flags=cv2.INTER_LINEAR)
            rgba = np.concatenate([np.where(pm[..., 3:4] > 1e-4, pm[..., :3] / np.maximum(pm[..., 3:4], 1e-4), 0), pm[..., 3:4]], 2)
        return rgba

    def draw(self, img, t, cam=None):
        spr = self.render(t)
        if spr is None:
            return img
        if self.anchor == "geo" and cam is not None:
            x, y = cam.geo_to_screen(t, self.pos[0], self.pos[1]); x, y = float(x[0]), float(y[0])
            ang = self.angle - cam.state(t)["roll"]
        else:
            x, y = self.pos; ang = self.angle
        return blit_sub(img, spr, x, y, angle=ang, add=False)


@lru_cache(64)
def static_glow_text(text, size, color, family="jost", weight=700, italic=False, tracking=0.0, glow=None, core_white=0.0, s1=5, s2=20, a2=0.5):
    fam = "jost_italic" if italic else family
    f = font(fam, size * 2, weight); asc, desc = f.getmetrics(); pad = 70
    xs, x = [], 0.0
    for ch in text:
        xs.append(x); x += f.getlength(ch) + tracking * size * 2
    im = Image.new("L", (int(x + 2 * pad), asc + desc + 2 * pad)); d = ImageDraw.Draw(im)
    for i, ch in enumerate(text):
        d.text((pad + xs[i], pad), ch, font=f, fill=255)
    a = cv2.resize(np.asarray(im, np.float32) / 255, (im.width // 2, im.height // 2), interpolation=cv2.INTER_AREA)
    return glow_rgba(a, color, glow, s1=s1, s2=s2, a2=a2, core_white=core_white)


# ----------------------------------------------------------------------------- arcs / trails
def bezier(p0, p1, bulge, n=64):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0; nrm = np.array([-d[1], d[0]])
    c = (p0 + p1) / 2 + nrm * bulge
    u = np.linspace(0, 1, n)[:, None]
    return (1 - u) ** 2 * p0 + 2 * (1 - u) * u * c + u ** 2 * p1


def draw_trail(layer_rgb, layer_a, pts, width=4.0, color=(1, 1, 1), tail_fade=True):
    """Anti-aliased tapered polyline into a float RGB+alpha layer (screen space)."""
    n = len(pts)
    if n < 2:
        return
    for i in range(n - 1):
        u = i / (n - 1)
        a = (u ** 1.3) if tail_fade else 1.0
        w = max(1.0, width * (0.35 + 0.65 * u))
        p, q = pts[i], pts[i + 1]
        if not (np.isfinite(p).all() and np.isfinite(q).all()):
            continue
        tmp_pts = np.round(np.array([p, q]) * 16).astype(np.int32)
        cv2.line(layer_a, tuple(tmp_pts[0]), tuple(tmp_pts[1]), float(a), int(round(w)), cv2.LINE_AA, 4)
        for c in range(3):
            cv2.line(layer_rgb[c], tuple(tmp_pts[0]), tuple(tmp_pts[1]), float(a * color[c]), int(round(w)), cv2.LINE_AA, 4)


class GlowLayer:
    """Screen-space additive layer for trails/streaks; one quarter-res bloom pass per frame."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.rgb = [np.zeros((H, W), np.float32) for _ in range(3)]; self.a = np.zeros((H, W), np.float32)
        self.dirty = False

    def clear(self):
        for c in self.rgb: c.fill(0)
        self.a.fill(0); self.dirty = False

    def composite(self, img, bloom=0.8, sigma=10):
        if not self.dirty:
            return img
        a = np.clip(self.a, 0, 1)
        rgb = np.stack(self.rgb, 2) / np.maximum(self.a[..., None], 1e-4)
        rgb = np.clip(rgb, 0, 1)
        img = img * (1 - a[..., None]) + rgb * a[..., None]
        sm = cv2.resize(np.stack(self.rgb, 2), (self.W // 4, self.H // 4), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), sigma / 4)
        img = img + cv2.resize(sm, (self.W, self.H)) * bloom
        return np.clip(img, 0, 1)


def streak_rain(layer, t, t0, t1, box, n=26, color=(1.0, 0.77, 0.0), angle=-35, length=120, seed=1):
    """MIRV-like rain of yellow lines falling diagonally inside screen box (x0,y0,x1,y1)."""
    if not (t0 <= t <= t1):
        return
    rng = np.random.default_rng(seed); x0, y0, x1, y1 = box
    a = math.radians(angle); dx, dy = math.sin(a), math.cos(a)
    fade = min(1.0, (t - t0) / 0.2, (t1 - t) / 0.3)
    for k in range(n):
        st = t0 + rng.uniform(0, (t1 - t0) * 0.6); life = rng.uniform(0.35, 0.6)
        u = (t - st) / life
        if not (0 <= u <= 1):
            continue
        sx, sy = rng.uniform(x0, x1), rng.uniform(y0, y0 + (y1 - y0) * 0.5)
        hx, hy = sx + dx * u * (y1 - y0) * 0.6, sy + dy * u * (y1 - y0) * 0.6
        pts = np.array([[hx - dx * length * k_, hy - dy * length * k_] for k_ in np.linspace(1, 0, 8)])
        draw_trail(layer.rgb, layer.a, pts, width=5, color=color)
        layer.dirty = True
    for c in layer.rgb: c *= 1.0
    layer.a *= fade


def glitch(rgba, amount, seed=0):
    """double-exposure + horizontal slice offsets + blur (HUD card entrance)."""
    if amount <= 0.01:
        return rgba
    rng = np.random.default_rng(seed); out = rgba.copy(); h = rgba.shape[0]
    for k in range(6):
        y0 = int(rng.uniform(0, h * 0.9)); y1 = min(h, y0 + int(rng.uniform(6, h * 0.12)))
        out[y0:y1] = np.roll(rgba[y0:y1], int(rng.uniform(-30, 30) * amount), axis=1)
    ghost = np.roll(rgba, int(26 * amount), axis=1) * 0.5
    out = np.maximum(out, ghost)
    k = int(1 + 10 * amount) | 1
    return cv2.GaussianBlur(out, (k, k), 0)
