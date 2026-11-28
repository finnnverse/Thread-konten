"""Timeline renderer: project JSON -> MP4 (1080x1920, 60 fps by default), rendered in parallel
segments and concatenated losslessly (same encoder settings, -c copy).

Usage:  python -m engine.render project.json out.mp4 [--workers 4] [--from 0 --to 10] [--fps 60]
"""
import os, sys, json, math, time, argparse, subprocess, tempfile
import numpy as np
import cv2

from .tiles import TileSource, ATTRIBUTION
from .destreak import CleanTiles
from .geo import Countries, merc, unmerc
from .camera import Camera
from .maprender import MapRenderer, ring_mask, apply_opaque_fill, apply_tint_fill, hex2rgb
from .text import draw_caption, chunk_words, blit, blit_sub, font, hexa, pil_to_rgba
from . import sprites as SP
from .fx import (NeonLabel, static_glow_text, bezier, draw_trail, GlowLayer, streak_rain, glitch,
                 pop_scale, ease_io, ease_in, ease_out, clamp01)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ============================================================================ helpers
def expand_camera(spec, tracked):
    keys = []
    for k in spec:
        if "follow" in k:
            tr = tracked[k["follow"]]
            for t in np.arange(k["t0"], k["t1"] + 1e-6, k.get("step", 0.5)):
                lon, lat = tr.geo_at(t)
                dlon, dlat = k.get("lead", [0, 0])
                keys.append(dict(t=float(t), lon=lon + dlon, lat=lat + dlat, width_km=k["width_km"], roll=k.get("roll", 0), tilt=k.get("tilt", 10)))
        else:
            keys.append(k)
    return keys


def random_points_in(rings, n, seed, lat_range=None):
    rng = np.random.default_rng(seed); out = []
    ext = [r for r in rings if not r["hole"] and r["mainland"]]
    paths = [np.stack([r["lon"], r["lat"]], 1).astype(np.float32) for r in ext]
    lon0 = min(r["lon"].min() for r in ext); lon1 = max(r["lon"].max() for r in ext)
    la0 = min(r["lat"].min() for r in ext); la1 = max(r["lat"].max() for r in ext)
    if lat_range:
        la0, la1 = max(la0, lat_range[0]), min(la1, lat_range[1])
    tries = 0
    while len(out) < n and tries < 20000:
        tries += 1
        p = (rng.uniform(lon0, lon1), rng.uniform(la0, la1))
        if any(cv2.pointPolygonTest(pa, (float(p[0]), float(p[1])), False) > 0 for pa in paths):
            if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 3.0 for q in out):
                out.append(p)
    return out


class Path2:
    """Moving object along a screen-space Bezier between two geo points (in Mercator)."""

    def __init__(self, a, b, t0, dur, bulge=0.15, ease="io"):
        self.a, self.b, self.t0, self.dur, self.bulge, self.ease = a, b, t0, dur, bulge, ease
        ax, ay = merc(a[0], a[1]); bx_lon = b[0] + 360 * round((a[0] - b[0]) / 360); bx, by = merc(bx_lon, b[1])
        self.pts = bezier((float(ax), float(ay)), (float(bx), float(by)), bulge, 96)

    def u(self, t):
        x = clamp01((t - self.t0) / self.dur)
        return ease_io(x) if self.ease == "io" else (x if self.ease == "linear" else ease_in(x) * 0.3 + x * 0.7)

    def merc_at(self, u):
        i = u * (len(self.pts) - 1); k = min(int(i), len(self.pts) - 2); f = i - k
        return self.pts[k] * (1 - f) + self.pts[k + 1] * f

    def geo_at(self, t):
        m = self.merc_at(self.u(t)); lon, lat = unmerc(m[0], m[1]); return float(lon), float(lat)

    def screen_poly(self, cam, M, u0, u1, clon):
        n = max(2, int(48 * (u1 - u0)) + 2)
        us = np.linspace(u0, u1, n)
        P = np.array([self.merc_at(u) for u in us])
        # keep x near camera longitude
        cx = (clon + 180) / 360
        P[:, 0] += np.round(cx - P[:, 0])
        sx, sy = cam.project(M, P[:, 0], P[:, 1])
        return np.stack([sx, sy], 1)


# ============================================================================ engine
class Engine:
    def __init__(self, spec, base_dir):
        self.spec, self.base_dir = spec, base_dir
        self.W, self.H = spec.get("size", [1080, 1920]); self.fps = spec.get("fps", 60)
        cache = os.path.join(ROOT, "cache")
        raw = TileSource(os.path.join(cache, "s2_2016"))
        self.tiles = CleanTiles(raw, os.path.join(cache, "s2_clean"), land=Countries(os.path.join(ROOT, "data"), "50m"))
        self.mr = MapRenderer(self.tiles, self.W, self.H)
        self.C = Countries(os.path.join(ROOT, "data"), "10m")
        # moving objects (tracked) first: camera may follow them
        self.tracked = {}
        for e in spec.get("elements", []):
            if e["type"] == "tracked":
                self.tracked[e["id"]] = Path2(e["from"], e["to"], e["t0"], e["dur"], e.get("bulge", 0.08), e.get("ease", "linear"))
        self.cam = Camera(expand_camera(spec["camera"], self.tracked), self.W, self.H)
        # regions
        self.regions = []
        for r in spec.get("regions", []):
            rings = self.C.rings(r["id"], tuple(r["exclude_bbox"]) if r.get("exclude_bbox") else None)
            if r.get("min_lat") is not None:
                rings = [x for x in rings if x["lat"].mean() >= r["min_lat"]]
            self.regions.append((r, rings))
        # captions
        self.captions = []
        if spec.get("words"):
            words = json.load(open(os.path.join(base_dir, spec["words"]))) if isinstance(spec["words"], str) else spec["words"]
            self.captions = chunk_words(words, **spec.get("caption_rules", {}))
            if self.captions:
                self.captions[-1] = (self.captions[-1][0], spec.get("duration", self.captions[-1][1] + 0.5), self.captions[-1][2])
        elif spec.get("captions"):
            self.captions = [tuple(c) for c in spec["captions"]]
        # element prep
        self.neons = []; self.elements = spec.get("elements", [])
        for e in self.elements:
            if e["type"] == "neon":
                self.neons.append((e, NeonLabel(e["text"], e["t_in"], e["t_out"], tuple(e.get("at", e.get("pos", [540, 700]))),
                                                color=e.get("color", "#06EBFF"), glow=e.get("glow"), size=e.get("size", 60),
                                                weight=e.get("weight", 650), tracking=e.get("tracking", 0.30), quotes=e.get("quotes", True),
                                                angle=e.get("angle", 0), persp=e.get("persp", 0), wave=e.get("wave", 0),
                                                anchor="geo" if "at" in e else "screen", in_dur=e.get("in_dur", 0.45), out_dur=e.get("out_dur", 0.6))))
            if e["type"] == "bursts" and "points" not in e:
                rings = self.C.rings(e["region"], tuple(e["exclude_bbox"]) if e.get("exclude_bbox") else None)
                e["points"] = random_points_in(rings, e["n"], e.get("seed", 1), e.get("lat_range"))
        self.glow = GlowLayer(self.W, self.H)

    # ---------------------------------------------------------------- tiles
    def prefetch(self, t0, t1):
        keys = set()
        for t in np.arange(t0, t1, 1 / 15):
            M, s = self.cam.matrix(t); keys.update(self.mr.tiles_for(M, s))
        return len(keys), self.tiles.prefetch(sorted(keys))

    # ---------------------------------------------------------------- helpers
    def g2s(self, t, lon, lat):
        x, y = self.cam.geo_to_screen(t, lon, lat); return float(np.atleast_1d(x)[0]), float(np.atleast_1d(y)[0])

    def hero_weight(self, t):
        w = 0.0
        for e in self.elements:
            if e["type"] == "hero":
                a = clamp01((t - e["t_in"] + 0.05) / 0.2); b = 1 - clamp01((t - e["t_out"] - 0.25) / 0.18)
                w = max(w, min(a, b))
        return w

    # ---------------------------------------------------------------- frame
    def frame(self, t):
        W, H = self.W, self.H
        M, scale = self.cam.matrix(t)
        img = self.mr.base(M, scale)
        st = self.cam.state(t); clon = unmerc(st["mx"], st["my"])[0]
        noise = None
        for r, rings in self.regions:
            t_in, t_out = r.get("t_in", -1), r.get("t_out", 1e9)
            amt = ease_out((t - t_in) / r.get("fade", 0.7)) if t_in >= 0 else 1.0
            if t > t_out:
                amt *= 1 - ease_io((t - t_out) / r.get("fade_out", 0.5))
            if amt <= 0:
                continue
            if r.get("style", "opaque") == "opaque":
                if noise is None:
                    noise = self.mr.noise(M)
                nlat = r.get("island_north_of", 66)
                main = ring_mask(self.cam, t, rings, W, H, select=lambda x: x["hole"] or x["mainland"] or x["lat"].mean() < nlat, M=M)
                img = apply_opaque_fill(img, main, noise, r.get("color", "#0083FB"), amount=amt)
                isl = ring_mask(self.cam, t, rings, W, H, select=lambda x: (not x["hole"]) and (not x["mainland"]) and x["lat"].mean() >= nlat, M=M)
                img = apply_opaque_fill(img, isl, noise, r.get("island_color", "#3FD0FF"), inset_px=0, amount=amt)
            else:
                img = apply_tint_fill(img, ring_mask(self.cam, t, rings, W, H, M=M), r.get("color", "#C0402E"), amount=amt)

        # ---- depth-of-field background for hero scenes (measured 0.2 s blur-in)
        hw = self.hero_weight(t)
        if hw > 0:
            sm = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
            sm = cv2.GaussianBlur(sm, (0, 0), 0.5 + 5.5 * hw)
            bl = cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR)
            img = img * (1 - hw) + bl * hw * (1 - 0.22 * hw) + 0.0

        self.glow.clear()
        late = []                                         # drawn after trails
        for e in self.elements:
            ty = e["type"]
            if ty == "ring" and e["t0"] <= t <= e["t1"]:
                x, y = self.g2s(t, *e["at"]); ph = ((t - e["t0"]) * 2.2) % 1.0
                spr = SP.target_ring(e.get("size", 90), e.get("color", "#FFD400"))
                blit_sub(img, spr, x, y, alpha=1 - 0.6 * ph, scale=0.7 + 0.6 * ph)
            elif ty == "sticker":
                self._sticker(img, e, t)
            elif ty == "bursts":
                for i, p in enumerate(e["points"]):
                    t0 = e["t0"] + i * e.get("interval", 0.2)
                    s = pop_scale(t, t0, 0.15, e.get("t1"), 0.3)
                    if s <= 0:
                        continue
                    x, y = self.g2s(t, *p); pul = 1 + 0.05 * math.sin((t - t0) * 9 + i)
                    blit_sub(img, SP.explosion(e.get("size", 100), i % 6), x, y, scale=s * pul, angle=(i * 37) % 360)
            elif ty == "trail":
                self._trails(img, e, t, M, clon)
            elif ty == "tracked":
                late.append(e)
            elif ty == "rain":
                b = e.get("box");
                if "box_geo" in e:
                    (x0, y0), (x1, y1) = self.g2s(t, *e["box_geo"][0]), self.g2s(t, *e["box_geo"][1]); b = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
                streak_rain(self.glow, t, e["t0"], e["t1"], b, n=e.get("n", 26), angle=e.get("angle", -35), seed=e.get("seed", 1))
        img = self.glow.composite(img, bloom=0.55)
        for e in late:
            self._tracked(img, e, t, M, clon)
        for e, L in self.neons:
            L.draw(img, t, self.cam)
        for e in self.elements:
            if e["type"] == "hero":
                self._hero(img, e, t)
            elif e["type"] == "card":
                self._card(img, e, t)
        img *= self.mr.vignette
        for c0, c1, tx in self.captions:
            if c0 <= t < c1:
                img = draw_caption(img, tx); break
        wm = self.spec.get("watermark")
        if wm:
            spr = _wm_sprite(wm["text"], wm.get("size", 30))
            blit(img, spr, round(W / 2 - spr.shape[1] / 2), round(wm.get("y", 230) - spr.shape[0] / 2), alpha=wm.get("opacity", 0.55))
        return img

    # ---------------------------------------------------------------- element painters
    def _sprite(self, e):
        s = e["sprite"]; size = e.get("size", 200)
        if s.startswith("png:"):
            return SP.load_png(os.path.join(self.base_dir, s[4:]), size)
        return {"submarine": lambda: SP.submarine(size), "tombstone": lambda: SP.tombstone(size, e.get("text", "R.I.P.")),
                "bubble": lambda: SP.speech_bubble(e.get("text", "Everything is fine here!"), size),
                "radar": lambda: SP.radar_unit(size), "explosion": lambda: SP.explosion(size, e.get("seed", 0)),
                "rocket": lambda: SP.rocket(size), "rocket_h": lambda: SP.rocket(size, vertical=False),
                "warhead_bus": lambda: SP.warhead_bus(size), "card": lambda: SP.hud_card(size)}[s]()

    def _sticker(self, img, e, t):
        t_in, t_out = e["t_in"], e.get("t_out", 1e9)
        if t < t_in or t > t_out + 0.4:
            return
        s = pop_scale(t, t_in, e.get("pop", 0.18), t_out, e.get("out_dur", 0.3))
        if s <= 0:
            return
        if "at" in e:
            x, y = self.g2s(t, *e["at"]); roll = self.cam.state(t)["roll"]
        else:
            x, y = e["pos"]; roll = 0
        if e.get("map_scale"):
            s *= (self.cam.px_per_km(t) / e["map_scale"])
        ang = e.get("angle", 0) - (roll if e.get("follow_roll", True) else 0)
        if e.get("wobble"):
            ang += e["wobble"] * math.sin((t - t_in) * 7)
        dy = 0
        if e.get("rise"):
            dy = (1 - ease_out((t - t_in) / 0.45)) * e.get("rise", 120); s = max(s, 0.001) if t >= t_in else 0
        blit_sub(img, self._sprite(e), x + e.get("dx", 0), y + e.get("dy", 0) + dy, scale=s, angle=ang)

    def _trails(self, img, e, t, M, clon):
        n = e.get("count", 1); spread = e.get("spread", 1.5)
        for i in range(n):
            t0 = e["t0"] + i * e.get("stagger", 0.08)
            if t < t0:
                continue
            a = (e["from"][0] + (i - (n - 1) / 2) * spread * 0.35, e["from"][1] + (i - (n - 1) / 2) * spread * 0.1)
            b = (e["to"][0] + (i - (n - 1) / 2) * spread * e.get("to_spread", 1.0), e["to"][1] + ((i * 7) % 5 - 2) * spread * 0.5 * e.get("to_spread", 1.0))
            key = ("_p", i); P = e.get(key)
            if P is None:
                P = Path2(a, b, t0, e.get("dur", 1.3), e.get("bulge", 0.18) * (1 + 0.15 * ((i % 3) - 1))); e[key] = P
            u = P.u(t)
            fade_tail = clamp01((t - (t0 + P.dur)) / e.get("tail_fade", 0.8))
            u_tail = max(0.0, u - e.get("trail_len", 0.55)) + fade_tail * (u - max(0.0, u - e.get("trail_len", 0.55)))
            if u - u_tail > 0.002:
                pts = P.screen_poly(self.cam, M, u_tail, u, clon)
                col = hex2rgb(e.get("color", "#FFFFFF"))
                draw_trail(self.glow.rgb, self.glow.a, pts, width=e.get("width", 4.0), color=tuple(col)); self.glow.dirty = True
            if u < 1.0 and e.get("head", "rocket") and t <= t0 + P.dur:
                pts = P.screen_poly(self.cam, M, max(0, u - 0.01), u, clon)
                ang = -math.degrees(math.atan2(pts[-1][1] - pts[0][1], pts[-1][0] - pts[0][0]))
                blit_sub(img, SP.rocket(e.get("head_size", 60), vertical=False), pts[-1][0], pts[-1][1], angle=ang)
            if e.get("impact") and t >= t0 + P.dur:
                ti = t0 + P.dur; s = pop_scale(t, ti, 0.15, e.get("impact_out"), 0.3)
                if s > 0:
                    x, y = self.g2s(t, *P.geo_at(ti + 1e-3))
                    blit_sub(img, SP.explosion(e.get("impact_size", 90), i % 6), x, y, scale=s)

    def _tracked(self, img, e, t, M, clon):
        P = self.tracked[e["id"]]
        if t < e["t0"] - 0.01 or t > e["t0"] + e["dur"] + e.get("linger", 0):
            return
        u = P.u(t)
        pts = P.screen_poly(self.cam, M, max(0, u - e.get("trail_len", 0.25)), u, clon)
        draw_trail(self.glow.rgb, self.glow.a, pts, width=e.get("width", 10), color=(1, 1, 1))
        img[:] = self.glow.composite(img, bloom=0.5); self.glow.clear()
        p2 = P.screen_poly(self.cam, M, max(0, u - 0.004), u + 1e-4, clon)
        ang = -math.degrees(math.atan2(p2[-1][1] - p2[0][1], p2[-1][0] - p2[0][0]))
        x, y = pts[-1]
        blit_sub(img, SP.rocket(e.get("size", 200), vertical=False), x, y, angle=ang)
        for key, off in (("top", -1), ("bottom", 1)):
            lab = e.get(key)
            if not lab:
                continue
            tt = lab.get("t", e["t0"]);
            if t < tt:
                continue
            s = pop_scale(t, tt, 0.18)
            drop = e.get("drop_t"); dy = 0; al = 1.0
            if drop and t > drop:                                     # measured: falls ~165 px in 0.6 s, ease-in
                u_ = clamp01((t - drop) / 0.6); dy = 165 * u_ ** 2; al = 1 - u_ ** 1.5
            spr = static_glow_text(lab["text"], lab.get("size", 40), lab.get("color", "#FFED13" if off < 0 else "#F5030A"),
                                   weight=lab.get("weight", 650), italic=lab.get("italic", off > 0))
            nx, ny = math.sin(math.radians(ang)) * off * -1, math.cos(math.radians(ang)) * off * -1
            gap = lab.get("gap", 52)
            blit_sub(img, spr, x - math.cos(math.radians(ang)) * e.get("size", 200) * 0.15 + nx * -gap,
                     y + ny * -gap + dy, scale=s, angle=ang * 0.6, alpha=al)

    def _hero(self, img, e, t):
        if t < e["t_in"] or t > e["t_out"] + 0.45:
            return
        W, H = self.W, self.H
        cx, cy = e.get("pos", [W * 0.40, H * 0.47])
        a_in = ease_out((t - e["t_in"]) / 0.15)
        exit_u = clamp01((t - e["t_out"]) / 0.18)                    # rack focus: subject blurs out first
        spr = self._sprite(e)
        rise = (1 - ease_out((t - e["t_in"]) / 0.35)) * e.get("rise", 0)
        sc = e.get("scale", 1.0) * (0.6 + 0.4 * a_in) if e.get("pop", True) else e.get("scale", 1.0)
        if e.get("flame"):
            fl = SP.flame(int(spr.shape[1] * 0.95), int(spr.shape[0] * 0.62))
            flick = 1 + 0.05 * math.sin(t * 40) + 0.03 * math.sin(t * 23)
            fy = cy + rise + spr.shape[0] * sc * 0.5 + fl.shape[0] * sc * flick * 0.45
            blit_sub(img, fl, cx, fy, scale=sc * flick, alpha=a_in * (1 - exit_u), add=False)
        s2 = spr
        if exit_u > 0:
            k = int(2 + 30 * exit_u) | 1; s2 = cv2.GaussianBlur(spr, (k, k), 0)
        blit_sub(img, s2, cx, cy + rise, scale=sc, alpha=a_in * (1 - exit_u * 0.85))
        if e.get("mult"):
            tm = e.get("mult_t", e["t_in"] + 0.05); s = pop_scale(t, tm, 0.15)
            if s > 0:
                spr_m = static_glow_text(e["mult"], e.get("mult_size", 90), "#FBFCFE", italic=True, weight=700)
                blit_sub(img, spr_m, cx + e.get("mult_dx", 250), cy + e.get("mult_dy", -40), scale=s, alpha=1 - exit_u)
        if e.get("vlabel"):
            tl = e.get("vlabel_t", e["t_in"] + 0.4)
            if t >= tl:
                L = e.setdefault("_vl", NeonLabel(e["vlabel"], tl, e["t_out"], (0, 0), color="#08F4FF", size=e.get("vlabel_size", 46),
                                                  family="mono", weight=None, tracking=0.12, quotes=False, out_dur=0.25))
                spr_v = L.render(t)
                if spr_v is not None:
                    blit_sub(img, spr_v, cx - spr.shape[1] * sc * 0.5 - 45, cy + rise + 40, angle=90, alpha=1 - exit_u)
        if e.get("callout"):
            c = e["callout"]; tc = c.get("t", e["t_in"] + 0.8)
            if t >= tc:
                u = ease_out((t - tc) / 0.35)
                x0, y0 = cx + spr.shape[1] * sc * 0.18, cy - spr.shape[0] * sc * 0.25
                x1, y1 = x0 + 130, y0 - 200
                xe, ye = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                cv2.line(img, (int(x0 * 16), int(y0 * 16)), (int(xe * 16), int(ye * 16)), (1, 1, 1), 3, cv2.LINE_AA, 4)
                L = c.setdefault("_L", NeonLabel(c["text"], tc + 0.15, e["t_out"], (0, 0), color="#FFFFFF", glow="#9FD8FF", size=c.get("size", 44),
                                                 weight=420, tracking=0.02, quotes=False, in_dur=0.4, out_dur=0.2))
                spr_c = L.render(t)
                if spr_c is not None:
                    blit_sub(img, spr_c, x1 + spr_c.shape[1] * 0.3, y1 - 30, alpha=1 - exit_u)

    def _card(self, img, e, t):
        if t < e["t_in"] or t > e["t_out"] + 0.25:
            return
        spr = SP.hud_card(e.get("size", 300), label=e.get("label", "WARNING"))
        g = 1 - clamp01((t - e["t_in"]) / 0.5)                         # glitch entrance (measured ~0.5 s)
        s = pop_scale(t, e["t_in"], 0.2, e["t_out"], 0.2)
        al = 1.0
        if e.get("blink"):
            ph = ((t - e["t_in"] - 0.5) / e.get("blink_period", 0.5)) % 1.0
            al = 1.0 if ph < 0.6 or t < e["t_in"] + 0.5 else 0.45
        x, y = e.get("pos", [540, 650])
        blit_sub(img, glitch(spr, g, int(t * 30)) if g > 0 else spr, x, y, scale=s, alpha=al)


_WM = {}
def _wm_sprite(text, size):
    k = (text, size)
    if k not in _WM:
        from PIL import Image, ImageDraw
        f = font("manrope", size * 2, 700); w = int(f.getlength(text)) + 20; asc, desc = f.getmetrics()
        im = Image.new("L", (w, asc + desc + 20)); ImageDraw.Draw(im).text((10, 10), text, font=f, fill=255)
        a = cv2.resize(np.asarray(im, np.float32) / 255, (w // 2, (asc + desc + 20) // 2), interpolation=cv2.INTER_AREA)
        _WM[k] = np.concatenate([np.ones(a.shape + (3,), np.float32), a[..., None]], 2)
    return _WM[k]


# ============================================================================ driver
def _worker(args):
    spec_path, f0, f1, out = args
    spec = json.load(open(spec_path)); eng = Engine(spec, os.path.dirname(os.path.abspath(spec_path)))
    fps = eng.fps
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{eng.W}x{eng.H}", "-r", str(fps), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-g", str(fps), out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        img = eng.frame(f / fps)
        p.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    return out


def render(spec_path, out, workers=4, t_from=0.0, t_to=None, fps=None):
    import multiprocessing as mp
    spec = json.load(open(spec_path))
    if fps:
        spec["fps"] = fps; tmp = spec_path + ".tmp.json"; json.dump(spec, open(tmp, "w")); spec_path = tmp
    fps = spec.get("fps", 60); dur = t_to or spec["duration"]
    eng = Engine(spec, os.path.dirname(os.path.abspath(spec_path)))
    t0 = time.time(); n, new = eng.prefetch(t_from, dur); print(f"tiles {n} (downloaded {new}) {time.time()-t0:.0f}s", flush=True)
    F0, F1 = int(round(t_from * fps)), int(round(dur * fps))
    bounds = np.linspace(F0, F1, workers * 2 + 1).astype(int)
    tmpd = tempfile.mkdtemp(prefix="seg_", dir=os.path.dirname(os.path.abspath(out)))
    jobs = [(spec_path, int(a), int(b), os.path.join(tmpd, f"{i:03d}.mp4")) for i, (a, b) in enumerate(zip(bounds, bounds[1:])) if b > a]
    t0 = time.time()
    with mp.get_context("fork").Pool(workers) as pool:
        segs = pool.map(_worker, jobs, chunksize=1)
    lst = os.path.join(tmpd, "list.txt"); open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    for s in segs: os.remove(s)
    os.remove(lst); os.rmdir(tmpd)
    print(f"rendered {F1-F0} frames in {time.time()-t0:.0f}s -> {out}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("out")
    ap.add_argument("--workers", type=int, default=4); ap.add_argument("--from", dest="t_from", type=float, default=0)
    ap.add_argument("--to", type=float, default=None); ap.add_argument("--fps", type=int, default=None)
    a = ap.parse_args(); render(a.project, a.out, a.workers, a.t_from, a.to, a.fps)
