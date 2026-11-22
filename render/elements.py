"""Animated scene elements. Each element: t0, t1, draw(frame, cam, t). SFX registered on construction."""
import math, random
import numpy as np, cv2
from PIL import Image, ImageDraw
import assets as A
from engine import *

SFX = []  # (time, kind, priority)


def sfx(t, kind, pr=1):
    SFX.append((round(t, 3), kind, pr))


def fade(t, t0, t1, fin=.35, fout=.35):
    if t < t0 or t > t1: return 0.0
    return min(1, (t - t0) / fin if fin > 0 else 1, (t1 - t) / fout if fout > 0 else 1)


class El:
    t0 = 0; t1 = 0; geo = True
    def active(self, t): return self.t0 <= t <= self.t1


def tint(fr, L, col, fa, box):
    """colour the area but keep the terrain texture visible (like a translucent highlighter)"""
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    m = L[y0:y1, x0:x1, 3:4].astype(np.float32) / 255 * fa
    f = fr[y0:y1, x0:x1]
    lum = (f @ np.array([.3, .59, .11], np.float32))[..., None] / 255
    c = np.array(col, np.float32) * (0.62 + 0.75 * (lum - .45))
    f *= (1 - m); f += np.clip(c, 0, 255) * m


class Region(El):
    """polygon fill + glowing outline. rings: list of (N,2) plane coords"""
    def __init__(self, rings, t0, t1, color=(150, 255, 60), alpha=.85, outline=(255, 255, 255), glow=(120, 240, 255),
                 lw=3, zoomfade=(1.2, 4.0), fin=.4, fout=.4, colorto=None, tcolor=None, pulse=False, wipe=None, snd=False, flag=None):
        self.rings, self.t0, self.t1 = rings, t0, t1
        self.color, self.alpha, self.outline, self.glowc, self.lw = color, alpha, outline, glow, lw
        self.zoomfade, self.fin, self.fout, self.colorto, self.tcolor, self.pulse, self.wipe = zoomfade, fin, fout, colorto, tcolor, pulse, wipe
        self.flag = flag
        if snd: sfx(t0, 'pop', 1)

    def draw(self, fr, cam, t):
        a = fade(t, self.t0, self.t1, self.fin, self.fout)
        if a <= 0: return
        rp = [pts_px(cam, r) for r in self.rings]
        box = bbox_of(rp, 30)
        if box[2] < 0 or box[3] < 0 or box[0] > W or box[1] > H: return
        col = self.color
        if self.colorto is not None and t > self.tcolor:
            u = smooth(self.tcolor, self.tcolor + .8, t)
            col = tuple(int(c0 * (1 - u) + c1 * u) for c0, c1 in zip(self.color, self.colorto))
        zf = 1.0 if self.zoomfade is None else smooth(self.zoomfade[0], self.zoomfade[1], cam.vw)
        fa = self.alpha * zf * a
        if self.pulse: fa *= .75 + .25 * math.sin(t * 5)
        L = blank()
        if self.flag is not None:
            self.draw_flag(fr, rp, box, fa)
        elif fa > 0.01:
            fill_rings(L, rp, col)
            if self.wipe is not None:  # reveal north->south  (wipe=(tw0,tw1))
                u = smooth(self.wipe[0], self.wipe[1], t)
                ys = np.concatenate(rp)[:, 1]; cut = ys.min() + (ys.max() - ys.min() + 4) * u
                L[int(max(0, min(H, cut))):] = 0
            tint(fr, L, col, fa, box)
        # outline: bright on arrival, then 40%
        oi = (1.0 if t - self.t0 < 1.0 else .4 + .6 * math.exp(-(t - self.t0 - 1.0) * 2.5)) * a * smooth(.5, 1.3, cam.vw)
        if self.lw > 0 and oi > .01:
            O = blank()
            for r in rp: line_px(O, r, self.glowc, self.lw * 3.2, closed=True)
            g = glow_layer(O, box, 7)
            if g is not None: comp_add(fr, g, .9 * oi, box)
            O2 = blank()
            for r in rp: line_px(O2, r, self.outline, self.lw, closed=True)
            comp_premul(fr, O2, min(1, oi + .2), box)

    def draw_flag(self, fr, rp, box, fa):
        x0, y0, x1, y1 = [int(v) for v in box]
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
        if x1 - x0 < 4 or y1 - y0 < 4: return
        M = np.zeros((H, W), np.uint8)
        cv2.fillPoly(M, [np.round(r * 8).astype(np.int32) for r in rp], 255, lineType=cv2.LINE_AA, shift=3)
        fl = self.flag(x1 - x0, y1 - y0)  # RGB uint8 array
        m = M[y0:y1, x0:x1, None].astype(np.float32) / 255 * min(1, fa / .85)
        f = fr[y0:y1, x0:x1]
        f *= (1 - m); f += fl.astype(np.float32) * m


class Path(El):
    """progressive glowing line over plane-coord polyline"""
    def __init__(self, pts, t0, t1, tdraw, color=(90, 230, 255), width=4, arrow=False, glow=True, dash=False, snd='whoosh', fout=.4, minvw=0.8):
        self.p = np.asarray(pts, np.float64); self.t0, self.t1, self.tdraw = t0, t1, tdraw
        self.color, self.width, self.arrow, self.glow, self.dash, self.fout, self.minvw = color, width, arrow, glow, dash, fout, minvw
        seg = np.hypot(*np.diff(self.p, axis=0).T); self.cum = np.concatenate([[0], np.cumsum(seg)]); self.L = self.cum[-1]
        if snd: sfx(t0, snd, 2)

    def partial(self, u):
        d = self.L * u
        i = np.searchsorted(self.cum, d)
        pts = self.p[:max(1, i)]
        if 0 < i < len(self.p):
            s = (d - self.cum[i - 1]) / max(1e-9, self.cum[i] - self.cum[i - 1])
            pts = np.vstack([pts, self.p[i - 1] + (self.p[i] - self.p[i - 1]) * s])
        return pts

    def draw(self, fr, cam, t):
        a = fade(t, self.t0, self.t1, .01, self.fout) * smooth(self.minvw * .6, self.minvw, cam.vw)
        if a <= 0: return
        u = ease_io((t - self.t0) / self.tdraw) if self.tdraw > 0 else 1
        pts = self.partial(u)
        if len(pts) < 2: return
        px = pts_px(cam, pts)
        box = bbox_of([px], 40)
        L = blank()
        if self.dash:
            cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(px, axis=0).T))])
            dl = 22; on = (cum // dl) % 2 == 0
            for i in range(len(px) - 1):
                if on[i]: line_px(L, px[i:i + 2], self.color, self.width)
        else:
            line_px(L, px, self.color, self.width)
        if self.arrow and u > .02:
            tip = px[-1]; back = px[max(0, len(px) - 4)]
            v = tip - back; n = np.hypot(*v)
            if n > 1e-3:
                v /= n; nrm = np.array([-v[1], v[0]]); s = 10 + self.width * 2.5
                tri = np.array([tip + v * s * .6, tip - v * s + nrm * s * .75, tip - v * s - nrm * s * .75])
                fill_rings(L, [tri], self.color)
        if self.glow:
            g = glow_layer(L, box, 9)
            if g is not None: comp_add(fr, g, .9 * a, box)
        comp_premul(fr, L, a, box)


class Arc(Path):
    """curved arc between two lon/lat points (bezier in plane coords)"""
    def __init__(self, a, b, t0, t1, tdraw, h=.25, **kw):
        P0 = np.array([a[0], md(a[1])]); P1 = np.array([b[0], md(b[1])])
        d = P1 - P0; n = np.array([-d[1], d[0]])
        C = (P0 + P1) / 2 + n * h
        s = np.linspace(0, 1, 80)[:, None]
        pts = (1 - s) ** 2 * P0 + 2 * (1 - s) * s * C + s ** 2 * P1
        super().__init__(pts, t0, t1, tdraw, arrow=True, **kw)


class Pin(El):
    def __init__(self, lon, lat, t0, t1, snd=True):
        self.lon, self.lat, self.t0, self.t1 = lon, lat, t0, t1
        if snd: sfx(t0, 'pop', 1)

    def xy(self, cam): return cam.ll(self.lon, self.lat)

    def draw(self, fr, cam, t):
        a = fade(t, self.t0, self.t1, .01, .3)
        if a <= 0: return
        x, y = self.xy(cam)
        if not (-50 < x < W + 50 and -50 < y < H + 50): return
        s = pop_scale(t - self.t0, .35)
        L = blank()
        ph = ((t - self.t0) % 1.4) / 1.4
        r = 14 + 34 * ph
        cv2.circle(L, (int(x * 8), int(y * 8)), int(r * 8), (255, 60, 60, 255), 3, cv2.LINE_AA, 3)
        comp_premul(fr, L, a * (1 - ph) * .9, (x - 60, y - 60, x + 60, y + 60))
        L = blank()
        cv2.circle(L, (int(x * 8), int(y * 8)), int(15 * s * 8), (255, 255, 255, 255), -1, cv2.LINE_AA, 3)
        cv2.circle(L, (int(x * 8), int(y * 8)), int(11 * s * 8), (225, 30, 40, 255), -1, cv2.LINE_AA, 3)
        comp_premul(fr, L, a, (x - 30, y - 30, x + 30, y + 30))


def clampxy(x, y, w, h, m=30):
    return min(max(x, w / 2 + m), W - w / 2 - m), min(max(y, h / 2 + m + 10), H - h / 2 - m)


class Counter(El):
    def __init__(self, lon, lat, t0, t1, value, spin=1.3, start=None, fmt='{:,}', suffix='', prefix='', size=170,
                 color=(255, 255, 255), dy=-40, screen=None, riser=False, impact=True, ticks=True):
        self.lon, self.lat, self.t0, self.t1, self.v, self.spin = lon, lat, t0, t1, value, spin
        self.start = value * .1 if start is None else start
        self.fmt, self.suffix, self.prefix, self.size, self.color, self.dy, self.screen = fmt, suffix, prefix, size, color, dy, screen
        if riser: sfx(t0 - 1.2, 'riser', 2)
        if ticks: sfx(t0 + .05, 'tick', 0)
        if impact: sfx(t0 + spin, 'impact', 3)

    def text(self, t):
        u = ease_out((t - self.t0) / self.spin, 3)
        v = self.v if u >= 1 else self.start + (self.v - self.start) * u
        s = self.fmt.format(int(round(v))).replace(',', '.')
        return self.prefix + s + self.suffix

    def draw(self, fr, cam, t):
        a = fade(t, self.t0, self.t1, .15, .25)
        if a <= 0: return
        if self.screen is not None:
            x, y = self.screen; ang, sq = 0, 1
        else:
            x, y = cam.ll(self.lon, self.lat); y += self.dy
            ang, sq, _ = cam.local_frame(self.lon, self.lat)
            sq = max(.75, min(1, sq))
        dt = t - self.t0 - self.spin
        sc = 1.0
        if 0 <= dt < .25: sc = 1 + .14 * math.sin(dt / .25 * math.pi)
        if t - self.t0 < .2: sc *= .7 + .3 * (t - self.t0) / .2
        im = tf(text_sprite(self.text(t), self.size, self.color), sc, ang * .9, sq)
        x, y = clampxy(x, y, im.size[0] * .8, im.size[1] * .8)
        paste(fr, im, x, y, a)


class Sprite(El):
    """generic geo-anchored sprite with pop-in, float, optional travel from pin (cards)"""
    def __init__(self, im, lon, lat, t0, t1, off=(0, -160), from_pin=False, float_amp=0, snd='pop', tilt_follow=False, glow=False, kind='icon'):
        self.im, self.lon, self.lat, self.t0, self.t1 = im, lon, lat, t0, t1
        self.off, self.from_pin, self.fa, self.tilt_follow, self.kind = off, from_pin, float_amp, tilt_follow, kind
        if glow:
            g = Image.new('RGBA', (im.size[0] + 80, im.size[1] + 80), (0, 0, 0, 0))
            al = im.split()[3].point(lambda v: 255 if v > 20 else 0)
            wh = Image.new('RGBA', im.size, (255, 255, 255, 255)); wh.putalpha(al)
            g.alpha_composite(wh, (40, 40)); from PIL import ImageFilter
            g = g.filter(ImageFilter.GaussianBlur(16)); g2 = Image.new('RGBA', g.size); g2.alpha_composite(g); g2.alpha_composite(g)
            g2.alpha_composite(im, (40, 40)); self.im = g2
        if snd: sfx(t0, snd, 1)

    def draw(self, fr, cam, t):
        if not self.active(t): return
        dt, rt = t - self.t0, self.t1 - t
        x, y = cam.ll(self.lon, self.lat)
        tx, ty = x + self.off[0], y + self.off[1]
        w, h = self.im.size
        tx, ty = clampxy(tx, ty, w * .9, h * .9, 20)
        if self.from_pin:
            u = ease_out(dt / .4, 3); sc = .12 + .88 * u
            cx, cy = x + (tx - x) * u, y + (ty - y) * u
        else:
            sc = pop_scale(dt, .4); cx, cy = tx, ty
            if self.kind == 'emoji' and dt < .45:  # bigger overshoot for emoji
                u = dt / .45; sc = 1.18 * math.sin(u * math.pi / 2) if u < .7 else 1.18 - .18 * (u - .7) / .3
        if rt < .25: sc *= max(0.05, rt / .25)
        cy += self.fa * math.sin(t * 2.4)
        im = tf(self.im, sc)
        paste(fr, im, cx, cy, 1.0)


class IconRow(El):
    def __init__(self, lon, lat, items, t1, off=(0, -150), gap=128):
        """items: list of (name, t)"""
        self.lon, self.lat, self.items, self.t1, self.off, self.gap = lon, lat, items, t1, off, gap
        self.t0 = min(t for _, t in items); self.ims = [A.icon(n) for n, _ in items]
        for _, tt in items: sfx(tt, 'pop', 1)

    def draw(self, fr, cam, t):
        if not self.active(t): return
        x, y = cam.ll(self.lon, self.lat)
        n = len(self.items)
        bx, by = x + self.off[0], y + self.off[1]
        tot = (n - 1) * self.gap
        bx, by = clampxy(bx, by, tot + 140, 140, 20)
        rt = self.t1 - t
        for i, ((name, ti), im) in enumerate(zip(self.items, self.ims)):
            if t < ti: continue
            sc = pop_scale(t - ti, .35)
            if rt < .25: sc *= max(.05, rt / .25)
            paste(fr, tf(im, sc), bx - tot / 2 + i * self.gap, by, 1)


class Badge(El):
    geo = False
    def __init__(self, n, t0, t1):
        self.n, self.t0, self.t1 = n, t0, t1; sfx(t0, 'pop', 2)

    def draw(self, fr, cam, t):
        if not self.active(t): return
        im = badge_sprite(self.n); sc = pop_scale(t - self.t0, .35)
        im2 = tf(im, sc)
        paste(fr, im2, 24 + im.size[0] / 2 - 14, 24 + im.size[1] / 2 - 22, 1)


class Arrows(El):
    """small white arrows at lon/lat points pointing along a direction (deg, screen), bobbing"""
    def __init__(self, pts, t0, t1, ang, color=(255, 255, 255), size=34, snd=True):
        self.pts, self.t0, self.t1, self.ang, self.color, self.size = pts, t0, t1, ang, color, size
        if snd: sfx(t0, 'pop', 1)

    def draw(self, fr, cam, t):
        a = fade(t, self.t0, self.t1, .3, .3)
        if a <= 0: return
        L = blank(); allp = []
        for i, (lon, lat) in enumerate(self.pts):
            if t < self.t0 + i * .15: continue
            x, y = cam.ll(lon, lat)
            r = math.radians(self.ang); v = np.array([math.cos(r), -math.sin(r)]); n = np.array([-v[1], v[0]])
            bob = 8 * math.sin((t - self.t0) * 5 + i)
            c = np.array([x, y]) + v * bob; s = self.size
            arr = np.array([c + v * s, c + n * s * .7, c + n * s * .28, c + n * s * .28 - v * s * .9, c - n * s * .28 - v * s * .9, c - n * s * .28, c - n * s * .7])
            fill_rings(L, [arr], self.color); allp.append(arr)
        if allp:
            box = bbox_of(allp, 30); comp_premul(fr, L, a, box)


class Subscribe(El):
    geo = False
    def __init__(self, t0, t1, tclick):
        self.t0, self.t1, self.tc = t0, t1, tclick
        self.b0, self.b1, self.cur = A.subscribe(0), A.subscribe(1), A.cursor()
        sfx(t0, 'pop', 2); sfx(tclick, 'click', 2)

    def draw(self, fr, cam, t):
        if not self.active(t): return
        dt, rt = t - self.t0, self.t1 - t
        y = H - 130 + 200 * (1 - ease_out(dt / .45, 3)) + (200 * (1 - rt / .35) if rt < .35 else 0)
        sc = 1.0
        if 0 <= t - self.tc < .2: sc = 1 - .08 * math.sin((t - self.tc) / .2 * math.pi)
        im = self.b1 if t >= self.tc else self.b0
        paste(fr, tf(im, sc), W / 2, y, 1)
        if self.tc - .9 < t < self.tc + 1.2:
            u = ease_io((t - (self.tc - .9)) / .8)
            cx = W / 2 + 330 - 160 * u; cy = y + 120 - 95 * u
            paste(fr, self.cur, cx + 20, cy + 30, 1)


def flag_fill(code, split=None):
    """returns callable (w,h)->RGB array. split: (code2, angle) two flags split diagonally"""
    def f(w, h):
        a = np.asarray(A.flag(code, max(8, w), max(8, h)).convert('RGB'))
        if split:
            b = np.asarray(A.flag(split, max(8, w), max(8, h)).convert('RGB'))
            yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
            m = (xx / a.shape[1] - .08 * (yy / a.shape[0] - .5)) > .5
            a = np.where(m[..., None], b, a)
        return a[:h, :w]
    return f
