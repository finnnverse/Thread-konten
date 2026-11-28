"""Typography: caption (Manrope 700, measured), neon labels (Jost), helpers."""
import os, math
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
FONTS = {
    "manrope": "Manrope[wght].ttf",
    "jost": "Jost[wght].ttf",
    "jost_italic": "Jost-Italic[wght].ttf",
    "mono": "SpaceMono-Bold.ttf",
}


@lru_cache(64)
def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONT_DIR, FONTS[name]), size=size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def hexa(h, a=255):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


# ----------------------------------------------------------------------------- RGBA layer helpers
def blit(img, rgba, x, y, alpha=1.0, add=False):
    """Composite float RGBA sprite (H,W,4, premultiplied=False, 0..1) onto float RGB img at
    integer-aligned position (use blit_sub for sub-pixel)."""
    h, w = rgba.shape[:2]; H, W = img.shape[:2]
    x0, y0 = int(x), int(y)
    sx0, sy0 = max(0, -x0), max(0, -y0); dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W, x0 + w), min(H, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return img
    s = rgba[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    a = s[..., 3:4] * alpha
    reg = img[dy0:dy1, dx0:dx1]
    if add:
        reg += s[..., :3] * a; np.clip(reg, 0, 1, out=reg)
    else:
        reg *= (1 - a); reg += s[..., :3] * a
    return img


def blit_sub(img, rgba, cx, cy, alpha=1.0, scale=1.0, angle=0.0, add=False):
    """Sub-pixel placement (centre cx,cy) with optional scale/rotation: no jitter for moving text."""
    if alpha <= 0.002 or scale <= 0.002:
        return img
    h, w = rgba.shape[:2]
    pad = int(math.ceil(max(w, h) * scale * 0.75)) + 4
    ix, iy = int(math.floor(cx)), int(math.floor(cy))
    fx, fy = cx - ix, cy - iy
    R = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    R[0, 2] += pad - w / 2 + fx; R[1, 2] += pad - h / 2 + fy
    pm = rgba.copy(); pm[..., :3] *= pm[..., 3:4]                       # premultiply for correct filtering
    out = cv2.warpAffine(pm, R, (2 * pad, 2 * pad), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = out[..., 3:4]
    rgb = np.where(a > 1e-4, out[..., :3] / np.maximum(a, 1e-4), 0)
    return blit(img, np.concatenate([rgb, a], 2), ix - pad, iy - pad, alpha, add)


def pil_to_rgba(im):
    return np.asarray(im.convert("RGBA")).astype(np.float32) / 255.0


# ----------------------------------------------------------------------------- caption
class CaptionStyle:
    """Measured: Manrope wght 700, 47.5 px @720p -> 71 px @1080p; fill #FCFFFF; dark outline ~2.25 px
    @55% opacity, no drop-shadow offset, no box; centre x 0.505*W, baseline 0.815*H; hard cuts."""
    size = 71; weight = 700; fill = "#FCFFFF"; stroke = 2; stroke_alpha = 0.55
    cx = 0.505; baseline = 0.815; max_w = 0.84


@lru_cache(256)
def caption_sprite(text, W=1080, style=CaptionStyle):
    sz = style.size
    f = font("manrope", sz, style.weight)
    while f.getlength(text) > style.max_w * W and sz > 40:
        sz -= 2; f = font("manrope", sz, style.weight)
    asc, desc = f.getmetrics()
    tw = int(f.getlength(text)) + 20; th = asc + desc + 20
    stroke = Image.new("L", (tw, th)); ImageDraw.Draw(stroke).text((10, 10), text, font=f, fill=255, stroke_width=style.stroke, stroke_fill=255)
    body = Image.new("L", (tw, th)); ImageDraw.Draw(body).text((10, 10), text, font=f, fill=255)
    s = np.asarray(stroke, np.float32) / 255; b = np.asarray(body, np.float32) / 255
    a = np.maximum(b, s * style.stroke_alpha)
    col = np.array(hexa(style.fill)[:3], np.float32) / 255
    rgb = np.where(b[..., None] > 0, col, 0) * b[..., None] / np.maximum(a[..., None], 1e-4)
    return np.concatenate([rgb, a[..., None]], 2).astype(np.float32), 10 + asc  # sprite, baseline offset in sprite


def draw_caption(img, text, style=CaptionStyle):
    if not text:
        return img
    H, W = img.shape[:2]
    spr, base = caption_sprite(text, W, style)
    x = style.cx * W - spr.shape[1] / 2
    y = style.baseline * H - base
    return blit(img, spr, round(x), round(y))


def chunk_words(words, max_words=3, max_chars=22, min_dur=0.35, gap_break=0.30):
    """words: [[start,end,text],...] -> caption chunks [(t0,t1,text)] in the reference rhythm:
    2-4 words, break at punctuation / pauses, cut exactly at the first word's start."""
    chunks, cur = [], []
    def flush():
        if cur:
            chunks.append([cur[0][0], cur[-1][1], " ".join(w[2] for w in cur)])
    for i, w in enumerate(words):
        if cur:
            text = " ".join(x[2] for x in cur + [w])
            gap = w[0] - cur[-1][1]
            if len(cur) >= max_words or len(text) > max_chars or gap > gap_break or cur[-1][2][-1:] in ".,?!;:":
                flush(); cur = []
        cur.append(w)
    flush()
    for i in range(len(chunks) - 1):              # each chunk stays until the next one starts
        chunks[i][1] = chunks[i + 1][0]
    # merge too-short chunks into previous
    out = []
    for c in chunks:
        if out and c[1] - c[0] < min_dur and len(out[-1][2]) + len(c[2]) < max_chars + 6:
            out[-1][1] = c[1]; out[-1][2] += " " + c[2]
        else:
            out.append(c)
    return [tuple(c) for c in out]
