"""Procedural sprites (drawn with PIL at 3x supersampling, returned as float RGBA 0..1).
All generic / topic-neutral. Any PNG can also be used through `load_png`."""
import math, os
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from .text import font, hexa

SS = 3  # supersampling


def _fin(im, size=None):
    w, h = im.size
    im = im.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS) if size is None else im.resize(size, Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255.0
    return a


def load_png(path, height=None):
    im = Image.open(path).convert("RGBA")
    if height:
        im = im.resize((max(1, int(im.width * height / im.height)), int(height)), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def add_shadow(rgba, dx=6, dy=10, blur=8, alpha=0.45):
    h, w = rgba.shape[:2]; p = int(blur * 2 + max(abs(dx), abs(dy)))
    out = np.zeros((h + 2 * p, w + 2 * p, 4), np.float32)
    sh = np.zeros((h + 2 * p, w + 2 * p), np.float32); sh[p + dy:p + dy + h, p + dx:p + dx + w] = rgba[..., 3]
    sh = cv2.GaussianBlur(sh, (0, 0), blur) * alpha
    out[..., 3] = sh
    a = rgba[..., 3:4]; reg = out[p:p + h, p:p + w]
    reg[..., :3] = rgba[..., :3] * a + reg[..., :3] * (1 - a) * 0
    reg[..., 3:4] = a + reg[..., 3:4] * (1 - a)
    rgbm = np.where(reg[..., 3:4] > 1e-4, rgba[..., :3] * a / np.maximum(reg[..., 3:4], 1e-4), 0)
    reg[..., :3] = rgbm
    return out


# ----------------------------------------------------------------------------- explosion
@lru_cache(64)
def explosion(size=110, seed=0):
    """stylised spiky burst: measured orange #F08A3A with light core."""
    rng = np.random.default_rng(seed); S = size * SS; im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    c = S / 2
    def star(r0, r1, n, col, jitter):
        pts = []
        for i in range(n * 2):
            a = i * math.pi / n + rng.uniform(-jitter, jitter)
            r = (r1 if i % 2 == 0 else r0) * rng.uniform(0.82, 1.08)
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.polygon(pts, fill=col)
    star(S * 0.30, S * 0.48, 11, hexa("#C4501E"), 0.12)
    star(S * 0.27, S * 0.43, 11, hexa("#F08A3A"), 0.12)
    for k in range(7):                                  # puffs
        a = rng.uniform(0, 2 * math.pi); r = S * rng.uniform(0.05, 0.2); rr = S * rng.uniform(0.09, 0.16)
        d.ellipse([c + r * math.cos(a) - rr, c + r * math.sin(a) - rr, c + r * math.cos(a) + rr, c + r * math.sin(a) + rr], fill=hexa("#FFB060"))
    d.ellipse([c - S * 0.12, c - S * 0.12, c + S * 0.12, c + S * 0.12], fill=hexa("#FFE6A0"))
    im = im.filter(ImageFilter.GaussianBlur(SS * 0.6))
    return add_shadow(_fin(im), 3, 5, 4, 0.35)


# ----------------------------------------------------------------------------- rockets
@lru_cache(16)
def rocket(length=520, vertical=True, body="#F4F4F2", dark="#151515", emblem=True):
    """Generic ballistic rocket (white/black), nose up when vertical."""
    L = length * SS; W = int(L * 0.19); im = Image.new("RGBA", (W + 4 * SS, L)); d = ImageDraw.Draw(im)
    x0, x1 = 2 * SS, 2 * SS + W; nose = int(W * 1.15)
    d.pieslice([x0, 0, x1, nose * 2], 180, 360, fill=hexa(body)); d.rectangle([x0, nose, x1, L], fill=hexa(body))
    d.pieslice([x0 + W * 0.3, 0, x1 - W * 0.3, W * 0.5], 180, 360, fill=hexa("#2A2A2A"))
    d.rectangle([x0, int(L * 0.27), x1, int(L * 0.31)], fill=hexa(dark))
    d.rectangle([x0, int(L * 0.47), x1, L], fill=hexa(dark))
    if emblem:                                         # generic hazard trefoil
        cx, cy, r = (x0 + x1) / 2, L * 0.56, W * 0.3
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hexa("#F28C1E"))
        for k in range(3):
            a0 = -90 + k * 120 - 30
            d.pieslice([cx - r * 0.85, cy - r * 0.85, cx + r * 0.85, cy + r * 0.85], a0, a0 + 60, fill=hexa("#111111"))
        d.ellipse([cx - r * 0.18, cy - r * 0.18, cx + r * 0.18, cy + r * 0.18], fill=hexa("#111111"))
    arr = np.asarray(im).astype(np.float32)               # cylinder shading
    xs = np.linspace(-1, 1, arr.shape[1]); shade = (0.78 + 0.30 * np.cos(np.clip(xs - 0.25, -1.5, 1.5) * 1.2))[None, :, None]
    arr[..., :3] = np.clip(arr[..., :3] * shade, 0, 255)
    im = Image.fromarray(arr.astype(np.uint8))
    if not vertical:
        im = im.rotate(-90, expand=True)
    return _fin(im)


@lru_cache(8)
def flame(width=110, length=330):
    """Measured: core #FEFC00, edge #A38015, soft glow."""
    S = SS; W, L = width * S, length * S; im = Image.new("RGBA", (W * 2, L)); d = ImageDraw.Draw(im)
    for i, (col, sc) in enumerate([("#FFB000", 1.0), ("#FFE600", 0.78), ("#FFFBD0", 0.38)]):
        w = W * sc; pts = [(W - w / 2, 0), (W + w / 2, 0), (W + w * 0.12, L * (0.98 - 0.25 * i)), (W - w * 0.12, L * (0.98 - 0.25 * i))]
        d.polygon(pts, fill=hexa(col))
    im = im.filter(ImageFilter.GaussianBlur(S * 3))
    return _fin(im)


@lru_cache(8)
def warhead_bus(height=420, n=7):
    """Generic multi-cone payload stage (MIRV-like): drum + cones."""
    S = SS; H = height * S; W = int(H * 0.62); im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
    top = int(H * 0.38)
    d.rounded_rectangle([0, top, W, H], radius=W // 10, fill=hexa("#F2F2F0"))
    d.rectangle([0, int(H * 0.62), W, H - W // 12], fill=hexa("#141414")); d.rounded_rectangle([0, int(H * 0.62), W, H], radius=W // 10, fill=hexa("#141414"))
    d.rectangle([W * 0.45, H * 0.92, W * 0.58, H * 0.96], fill=hexa("#DDDDDD"))
    d.ellipse([W * 0.47, H * 0.48, W * 0.53, H * 0.52], fill=hexa("#151515"))
    d.rounded_rectangle([W * 0.3, top - H * 0.30, W * 0.7, top + 4], radius=W // 12, fill=hexa("#B7743A"))  # central canister
    for k in range(n):
        cx = W * (0.08 + 0.84 * k / (n - 1)); h = H * (0.30 - 0.06 * abs(k - (n - 1) / 2) / ((n - 1) / 2))
        d.polygon([(cx - W * 0.06, top + 6), (cx + W * 0.06, top + 6), (cx, top - h)], fill=hexa("#202020"))
    arr = np.asarray(im).astype(np.float32); xs = np.linspace(-1, 1, arr.shape[1])
    arr[..., :3] *= (0.75 + 0.32 * np.cos(np.clip(xs - 0.3, -1.5, 1.5) * 1.1))[None, :, None]
    return add_shadow(_fin(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))), 8, 14, 10, 0.45)


# ----------------------------------------------------------------------------- vessels / vehicles
@lru_cache(16)
def submarine(length=300, color="#8C949A"):
    """Top-down generic submarine: hull capsule + sail + fins, soft shadow."""
    S = SS; L = length * S; W = int(L * 0.13); im = Image.new("RGBA", (L, W * 3)); d = ImageDraw.Draw(im)
    y0 = W; d.rounded_rectangle([0, y0, L, y0 + W], radius=W // 2, fill=hexa(color))
    d.rounded_rectangle([L * 0.28, y0 + W * 0.25, L * 0.4, y0 + W * 0.75], radius=W // 5, fill=hexa("#5D646A"))
    d.polygon([(L * 0.02, y0 - W * 0.35), (L * 0.09, y0 + W * 0.5), (L * 0.02, y0 + W * 1.35)], fill=hexa("#6F777D"))
    for k in range(8):
        x = L * (0.45 + k * 0.045); d.ellipse([x, y0 + W * 0.42, x + W * 0.16, y0 + W * 0.58], fill=hexa("#6A7278"))
    arr = np.asarray(im).astype(np.float32); ys = np.linspace(-1, 1, arr.shape[0])
    arr[..., :3] *= (0.8 + 0.3 * np.cos(np.clip(ys + 0.2, -1.5, 1.5) * 2.5))[:, None, None]
    return add_shadow(_fin(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))), 4, 6, 5, 0.5)


@lru_cache(8)
def tombstone(height=230, text="R.I.P."):
    S = SS; H = height * S; W = int(H * 0.72); im = Image.new("RGBA", (int(W * 1.6), int(H * 1.12))); d = ImageDraw.Draw(im)
    ox = int(W * 0.3)
    d.rounded_rectangle([ox, 0, ox + W, H * 0.92], radius=int(W * 0.48), fill=hexa("#9EA2A4"))
    d.rectangle([ox, H * 0.45, ox + W, H * 0.92], fill=hexa("#9EA2A4"))
    f = font("jost", int(H * 0.13), 500); tw = f.getlength(text)
    d.text((ox + W / 2 - tw / 2, H * 0.30), text, font=f, fill=hexa("#4A4E50"))
    d.ellipse([0, H * 0.82, W * 1.6, H * 1.1], fill=hexa("#3B2A20"))          # dirt mound
    rng = np.random.default_rng(height)
    for k in range(180):
        x, y = rng.uniform(W * 0.15, W * 1.45), rng.uniform(H * 0.86, H * 1.04)
        d.ellipse([x, y, x + 6 * S, y + 4 * S], fill=hexa(["#2B1D16", "#4A3427", "#5A4030"][k % 3]))
    for k in range(5):                                                       # flowers
        x = ox + W * (0.15 + k * 0.17); y = H * (0.84 + 0.03 * (k % 2))
        d.line([x, y, x, y + H * 0.06], fill=hexa("#3E7D2A"), width=2 * S)
        d.ellipse([x - 6 * S, y - 6 * S, x + 6 * S, y + 6 * S], fill=hexa("#FFFFFF")); d.ellipse([x - 2 * S, y - 2 * S, x + 2 * S, y + 2 * S], fill=hexa("#F2C230"))
    arr = np.asarray(im).astype(np.float32); xs = np.linspace(-1, 1, arr.shape[1])
    arr[..., :3] *= (0.85 + 0.2 * np.cos(np.clip(xs - 0.2, -1.5, 1.5)))[None, :, None]
    return add_shadow(_fin(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))), 6, 8, 6, 0.4)


@lru_cache(16)
def speech_bubble(text="Everything is fine here!", width=230):
    S = SS; W = width * S; f = font("jost", int(W * 0.095), 600)
    words = text.split(); lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) > W * 0.62 and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    H = int(W * 0.68); im = Image.new("RGBA", (W, int(H * 1.25))); d = ImageDraw.Draw(im)
    d.polygon([(W * 0.18, H * 0.7), (W * 0.06, H * 1.2), (W * 0.36, H * 0.82)], fill=hexa("#000000"))
    d.ellipse([0, 0, W, H], fill=hexa("#000000")); d.ellipse([4 * S, 4 * S, W - 4 * S, H - 4 * S], fill=hexa("#FFFFFF"))
    d.polygon([(W * 0.2, H * 0.7), (W * 0.09, H * 1.12), (W * 0.34, H * 0.8)], fill=hexa("#FFFFFF"))
    lh = f.getmetrics()[0] + f.getmetrics()[1]; y = H / 2 - lh * len(lines) / 2
    for ln in lines:
        d.text((W / 2 - f.getlength(ln) / 2, y), ln, font=f, fill=hexa("#111111")); y += lh
    return add_shadow(_fin(im), 3, 5, 4, 0.35)


@lru_cache(8)
def radar_unit(height=260):
    """generic air-defence radar on a truck (front-ish view)."""
    S = SS; H = height * S; W = int(H * 0.9); im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
    d.rectangle([W * 0.46, H * 0.35, W * 0.54, H * 0.78], fill=hexa("#5B5F58"))
    d.ellipse([W * 0.22, 0, W * 0.78, H * 0.48], fill=hexa("#C9CCC6")); d.ellipse([W * 0.3, H * 0.06, W * 0.7, H * 0.42], fill=hexa("#AEB2AB"))
    for k in range(5):
        y = H * (0.08 + k * 0.07); d.line([W * 0.3, y, W * 0.7, y], fill=hexa("#90948D"), width=2 * S)
    d.rounded_rectangle([W * 0.15, H * 0.72, W * 0.85, H * 0.9], radius=8 * S, fill=hexa("#4B5040"))
    for x in (0.25, 0.5, 0.75):
        d.ellipse([W * x - H * 0.06, H * 0.84, W * x + H * 0.06, H * 0.98], fill=hexa("#1C1C1C"))
    return add_shadow(_fin(im), 8, 10, 8, 0.45)


@lru_cache(8)
def target_ring(size=90, color="#FFD400"):
    S = SS; R = size * S; im = Image.new("RGBA", (R, R)); d = ImageDraw.Draw(im)
    d.ellipse([R * 0.1, R * 0.1, R * 0.9, R * 0.9], outline=hexa(color), width=int(R * 0.07))
    d.ellipse([R * 0.4, R * 0.4, R * 0.6, R * 0.6], fill=hexa(color))
    return _fin(im)


@lru_cache(8)
def hud_card(width=300, frame="#FF6A3A", icon="#FF2A2A", label="WARNING"):
    """sci-fi warning card: frame + hatched header + triangle '!' + label."""
    S = SS; W = width * S; H = int(W * 1.32); im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
    lw = int(W * 0.025)
    d.rounded_rectangle([lw, lw, W - lw, H - lw], radius=int(W * 0.08), fill=hexa("#2A1410", 150), outline=hexa(frame), width=lw)
    d.rounded_rectangle([W * 0.1, H * 0.06, W * 0.9, H * 0.19], radius=int(W * 0.03), outline=hexa(frame), width=lw // 2)
    for k in range(12):
        x = W * (0.13 + k * 0.065); d.line([x, H * 0.17, x + W * 0.05, H * 0.08], fill=hexa(frame), width=lw // 2)
    cx, cy, r = W / 2, H * 0.52, W * 0.28
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=hexa(icon), width=lw)
    tr = r * 0.62; d.polygon([(cx, cy - tr), (cx + tr * 0.95, cy + tr * 0.7), (cx - tr * 0.95, cy + tr * 0.7)], fill=hexa(icon))
    f = font("jost", int(r * 0.7), 800); d.text((cx - f.getlength("!") / 2, cy - tr * 0.55), "!", font=f, fill=hexa("#FFFFFF"))
    f2 = font("jost", int(W * 0.08), 700); d.text((cx - f2.getlength(label) / 2, H * 0.8), label, font=f2, fill=hexa(frame))
    d.line([W * 0.3, H * 0.92, W * 0.7, H * 0.92], fill=hexa(frame), width=lw // 2)
    base = _fin(im)
    glow = cv2.GaussianBlur(base[..., 3], (0, 0), 6)
    out = base.copy(); col = np.array(hexa(frame)[:3], np.float32) / 255
    a = np.maximum(base[..., 3], glow * 0.6)
    out[..., :3] = np.where(base[..., 3:4] > 0.01, base[..., :3], col) ; out[..., 3] = a
    return out
