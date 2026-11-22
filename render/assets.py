"""Code-drawn assets: flags, icons, illustration cards, emoji, subscribe button, sunburst, diagram.
Everything is drawn with PIL at 2x and downsampled (no downloaded imagery)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = '/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf'
FONT_B = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'


def ss(w, h, k=2):
    im = Image.new('RGBA', (w * k, h * k), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im), k


def down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


# ---------------------------------------------------------------- flags
def flag(code, w=600, h=400):
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    if code == 'EGY':
        d.rectangle([0, 0, w, h / 3], fill=(206, 17, 38)); d.rectangle([0, h / 3, w, 2 * h / 3], fill=(255, 255, 255))
        d.rectangle([0, 2 * h / 3, w, h], fill=(0, 0, 0))
        cx, cy, s = w / 2, h / 2, h / 7  # simplified golden eagle
        gold = (192, 147, 0)
        d.polygon([(cx - 2.2 * s, cy - .2 * s), (cx - .4 * s, cy - .9 * s), (cx, cy - .2 * s), (cx + .4 * s, cy - .9 * s), (cx + 2.2 * s, cy - .2 * s), (cx + .6 * s, cy + .9 * s), (cx - .6 * s, cy + .9 * s)], fill=gold)
        d.ellipse([cx - .35 * s, cy - 1.45 * s, cx + .35 * s, cy - .75 * s], fill=gold)
    elif code == 'SDN':
        d.rectangle([0, 0, w, h / 3], fill=(210, 16, 52)); d.rectangle([0, h / 3, w, 2 * h / 3], fill=(255, 255, 255))
        d.rectangle([0, 2 * h / 3, w, h], fill=(0, 0, 0)); d.polygon([(0, 0), (w * .38, h / 2), (0, h)], fill=(0, 114, 41))
    elif code == 'FRA':
        for i, c in enumerate([(0, 35, 149), (255, 255, 255), (237, 41, 57)]):
            d.rectangle([i * w / 3, 0, (i + 1) * w / 3, h], fill=c)
    return im


# ---------------------------------------------------------------- icons (white circle, 110 px)
def _icon_canvas():
    return ss(110, 110, 4)


def icon(name, size=110):
    im, d, k = _icon_canvas(); S = 110 * k; c = S / 2
    d.ellipse([4 * k, 4 * k, S - 4 * k, S - 4 * k], fill=(255, 255, 255, 255), outline=(225, 230, 235, 255), width=3 * k)
    u = S / 110
    def P(pts): return [(c + x * u, c + y * u) for x, y in pts]
    if name == 'pyramid':
        d.polygon(P([(-34, 24), (0, -30), (34, 24)]), fill=(226, 176, 84)); d.polygon(P([(0, -30), (34, 24), (8, 24)]), fill=(186, 132, 52))
        d.line(P([(-36, 26), (36, 26)]), fill=(200, 160, 90), width=4 * k)
    elif name == 'ship':
        d.polygon(P([(-38, 6), (38, 6), (28, 22), (-30, 22)]), fill=(40, 70, 140))
        cols = [(230, 80, 60), (60, 160, 90), (240, 190, 50), (70, 140, 220)]
        for i in range(5):
            d.rectangle(P([(-30 + i * 12, -8), (-20 + i * 12, 5)]), fill=cols[i % 4])
        d.rectangle(P([(24, -18), (32, 5)]), fill=(240, 240, 245), outline=(90, 90, 100))
        d.line(P([(-44, 28), (44, 28)]), fill=(60, 150, 220), width=4 * k)
    elif name == 'drop':
        d.polygon(P([(0, -34), (-22, 4), (22, 4)]), fill=(40, 150, 230)); d.ellipse(P([(-22, -16), (22, 28)]), fill=(40, 150, 230))
        d.ellipse(P([(-12, 2), (-4, 14)]), fill=(180, 225, 255))
    elif name == 'people':
        for dx, col in ((-20, (240, 120, 60)), (20, (60, 130, 220)), (0, (250, 190, 40))):
            d.ellipse(P([(dx - 9, -26), (dx + 9, -8)]), fill=col); d.pieslice(P([(dx - 17, -4), (dx + 17, 34)]), 180, 360, fill=col)
    elif name == 'mountain':
        d.polygon(P([(-40, 26), (-8, -28), (24, 26)]), fill=(150, 100, 70)); d.polygon(P([(0, 26), (22, -8), (42, 26)]), fill=(120, 80, 60))
        d.polygon(P([(-8, -28), (-17, -13), (-10, -16), (-4, -10), (1, -15)]), fill=(255, 255, 255))
    elif name == 'fish':
        d.ellipse(P([(-30, -14), (16, 14)]), fill=(250, 150, 40)); d.polygon(P([(12, 0), (34, -16), (34, 16)]), fill=(250, 120, 30))
        d.ellipse(P([(-22, -6), (-14, 2)]), fill=(30, 30, 30))
        for x in (-6, 4): d.line(P([(x, -12), (x, 12)]), fill=(255, 255, 255), width=3 * k)
        d.polygon(P([(-36, 30), (-30, 18), (-24, 30)]), fill=(230, 80, 120)); d.polygon(P([(-26, 30), (-18, 14), (-12, 30)]), fill=(240, 110, 150))
    elif name == 'dam':
        d.rectangle(P([(-40, -6), (40, 28)]), fill=(70, 150, 220))
        d.polygon(P([(-40, -18), (40, -18), (34, 28), (-34, 28)]), fill=(170, 170, 175))
        for x in (-20, 0, 20): d.rectangle(P([(x - 5, 0), (x + 5, 28)]), fill=(90, 170, 240))
        d.rectangle(P([(-42, -24), (42, -16)]), fill=(120, 120, 128))
    elif name == 'wave':
        for j, yy in enumerate((-12, 4, 20)):
            pts = [(x, yy + 7 * math.sin(x / 9)) for x in range(-38, 39, 2)]
            d.line(P(pts), fill=(40, 140, 230), width=7 * k, joint='curve')
    elif name == 'temple':
        d.rectangle(P([(-40, -24), (40, 28)]), fill=(214, 160, 96))
        for x in (-28, -10, 10, 28):
            d.ellipse(P([(x - 6, -20), (x + 6, -8)]), fill=(160, 110, 60)); d.rectangle(P([(x - 8, -8), (x + 8, 24)]), fill=(180, 125, 70))
        d.rectangle(P([(-4, 6), (4, 28)]), fill=(70, 40, 20))
    elif name == 'puzzle':
        d.rectangle(P([(-28, -28), (2, 2)]), fill=(240, 90, 80)); d.rectangle(P([(4, -28), (32, 2)]), fill=(60, 150, 230))
        d.rectangle(P([(-28, 4), (2, 32)]), fill=(250, 190, 40)); d.rectangle(P([(4, 4), (32, 32)]), fill=(80, 190, 110))
        d.ellipse(P([(-4, -18), (10, -4)]), fill=(240, 90, 80)); d.ellipse(P([(-20, -4), (-6, 10)]), fill=(250, 190, 40))
    elif name == 'palm':
        d.ellipse(P([(-36, 18), (36, 34)]), fill=(70, 160, 220))
        d.line(P([(0, 26), (-4, 0), (-2, -20)]), fill=(140, 90, 40), width=7 * k, joint='curve')
        for a in (-150, -110, -70, -30, 10):
            r = math.radians(a)
            d.line(P([(-2, -20), (-2 + 30 * math.cos(r), -20 + 22 * math.sin(r) + 12)]), fill=(50, 160, 60), width=8 * k)
    elif name == 'rock':
        d.polygon(P([(-40, 30), (40, 30), (40, 22), (-40, 22)]), fill=(235, 215, 170))
        d.polygon(P([(-8, 22), (8, 22), (5, -2), (-5, -2)]), fill=(230, 230, 225))
        d.ellipse(P([(-30, -26), (30, 2)]), fill=(248, 248, 244), outline=(200, 200, 195), width=2 * k)
    elif name == 'building':
        d.rectangle(P([(-34, 0), (-16, 30)]), fill=(120, 160, 200)); d.rectangle(P([(16, -6), (34, 30)]), fill=(100, 140, 190))
        d.polygon(P([(-10, 30), (10, 30), (6, -30), (0, -40), (-6, -30)]), fill=(70, 110, 170))
        for y in range(-20, 28, 8): d.line(P([(-5, y), (5, y)]), fill=(200, 230, 255), width=2 * k)
    elif name == 'desert':
        d.ellipse(P([(14, -30), (34, -10)]), fill=(250, 190, 40))
        d.pieslice(P([(-50, -4), (20, 50)]), 180, 360, fill=(230, 180, 90)); d.pieslice(P([(-10, 4), (54, 56)]), 180, 360, fill=(210, 155, 70))
    elif name == 'arrow_up':
        d.polygon(P([(0, -34), (-24, -6), (-9, -6), (-9, 30), (9, 30), (9, -6), (24, -6)]), fill=(40, 170, 90))
    im = down(im, size, size)
    sh = Image.new('RGBA', (size + 24, size + 24), (0, 0, 0, 0))
    a = Image.new('L', (size, size), 0); ImageDraw.Draw(a).ellipse([4, 4, size - 4, size - 4], fill=120)
    sh.paste((0, 0, 0, 255), (16, 18), a); sh = sh.filter(ImageFilter.GaussianBlur(5))
    sh.alpha_composite(im, (12, 12))
    return sh


# ---------------------------------------------------------------- illustration cards
def _sky(d, w, h, top, bot):
    for y in range(h):
        f = y / h; d.line([(0, y), (w, y)], fill=tuple(int(top[i] * (1 - f) + bot[i] * f) for i in range(3)))


def card(name, seed=0):
    w, h, k = 420, 290, 2
    im = Image.new('RGB', (w * k, h * k)); d = ImageDraw.Draw(im); W, H = w * k, h * k
    rnd = random.Random(seed)
    if name == 'pyramids':
        _sky(d, W, H, (250, 170, 90), (255, 225, 170)); d.ellipse([W * .70, H * .12, W * .82, H * .29], fill=(255, 240, 200))
        d.rectangle([0, H * .68, W, H], fill=(222, 170, 95))
        for cx, s, sh in ((W * .32, .52, 1), (W * .62, .40, 1), (W * .82, .22, 1)):
            base = H * .74; top = base - W * s * .55
            d.polygon([(cx - W * s / 2, base), (cx, top), (cx + W * s / 2, base)], fill=(228, 175, 92))
            d.polygon([(cx, top), (cx + W * s / 2, base), (cx + W * s * .12, base)], fill=(178, 122, 58))
        for i in range(6):
            x0 = rnd.uniform(-W * .2, W * .8); d.arc([x0, H * .8, x0 + rnd.uniform(W * .3, W * .7), H * 1.3], 180, 360, fill=(200, 145, 70), width=3 * k)
    elif name == 'ship':
        d.rectangle([0, 0, W, H], fill=(226, 190, 120))
        d.polygon([(W * .10, 0), (W * .48, 0), (W * .90, H), (W * .52, H)], fill=(40, 120, 170))
        d.polygon([(W * .14, 0), (W * .44, 0), (W * .86, H), (W * .56, H)], fill=(55, 140, 190))
        cx, cy, L, B, a = W * .5, H * .5, W * .78, H * .12, math.radians(-14)
        def R(x, y): return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
        d.polygon([R(-L / 2, -B / 2), R(L / 2 - B, -B / 2), R(L / 2, 0), R(L / 2 - B, B / 2), R(-L / 2, B / 2)], fill=(40, 60, 120))
        cols = [(220, 70, 50), (60, 150, 90), (240, 180, 40), (70, 130, 210), (230, 230, 230)]
        for i in range(16):
            x = -L / 2 + L * .14 + i * L * .045
            for j in range(2):
                d.polygon([R(x, -B / 2 + j * B / 2 + 2), R(x + L * .04, -B / 2 + j * B / 2 + 2), R(x + L * .04, j * B / 2 - 2), R(x, j * B / 2 - 2)], fill=cols[(i * 3 + j) % 5])
        d.polygon([R(-L / 2 + 6, -B / 2), R(-L / 2 + L * .1, -B / 2), R(-L / 2 + L * .1, B / 2), R(-L / 2 + 6, B / 2)], fill=(245, 245, 245))
    elif name in ('temple', 'temple_blocks'):
        _sky(d, W, H, (110, 175, 235), (200, 230, 250)); d.rectangle([0, H * .82, W, H], fill=(225, 185, 120))
        fac = Image.new('RGBA', (W, H), (0, 0, 0, 0)); f = ImageDraw.Draw(fac)
        f.polygon([(W * .06, H * .86), (W * .12, H * .10), (W * .88, H * .10), (W * .94, H * .86)], fill=(205, 150, 90))
        for i in range(4):
            x = W * (.2 + i * .2)
            f.ellipse([x - W * .055, H * .2, x + W * .055, H * .38], fill=(175, 118, 64))
            f.polygon([(x - W * .07, H * .2), (x + W * .07, H * .2), (x + W * .05, H * .3), (x - W * .05, H * .3)], fill=(190, 135, 75))
            f.rectangle([x - W * .075, H * .38, x + W * .075, H * .70], fill=(185, 128, 70))
            f.rectangle([x - W * .085, H * .70, x + W * .085, H * .86], fill=(170, 115, 62))
        f.rectangle([W * .47, H * .55, W * .53, H * .86], fill=(60, 35, 20))
        if name == 'temple_blocks':
            out = Image.new('RGBA', (W, H), (0, 0, 0, 0)); n, m = 7, 5
            for i in range(n):
                for j in range(m):
                    bx, by = W * i / n, H * j / m
                    blk = fac.crop((int(bx), int(by), int(bx + W / n), int(by + H / m)))
                    out.alpha_composite(blk, (int(bx + rnd.uniform(-10, 10) * k + (i - n / 2) * 4 * k), int(by + rnd.uniform(-8, 8) * k + (j - m / 2) * 5 * k - 18 * k)))
            fac = out
        im = im.convert('RGBA'); im.alpha_composite(fac); im = im.convert('RGB'); d = ImageDraw.Draw(im)
    elif name == 'reef':
        _sky(d, W, H, (30, 150, 200), (10, 70, 130))
        for i in range(9):
            x = rnd.uniform(0, W); hh = rnd.uniform(.15, .35) * H; col = rnd.choice([(240, 100, 120), (250, 160, 60), (200, 80, 190), (250, 200, 80)])
            for b in range(5):
                a = math.radians(rnd.uniform(-60, 60) - 90)
                d.line([(x, H), (x + math.cos(a) * hh, H + math.sin(a) * hh)], fill=col, width=int(rnd.uniform(8, 14) * k))
        for i in range(7):
            x, y = rnd.uniform(.1, .9) * W, rnd.uniform(.15, .6) * H; s = rnd.uniform(14, 24) * k
            col = rnd.choice([(255, 150, 30), (255, 220, 60), (90, 200, 250)])
            d.ellipse([x - s, y - s * .5, x + s, y + s * .5], fill=col); d.polygon([(x + s * .8, y), (x + s * 1.6, y - s * .6), (x + s * 1.6, y + s * .6)], fill=col)
        for i in range(25):
            x, y = rnd.uniform(0, W), rnd.uniform(0, H * .7); r = rnd.uniform(2, 5) * k
            d.ellipse([x - r, y - r, x + r, y + r], outline=(200, 240, 255), width=k)
    elif name == 'whitedesert':
        _sky(d, W, H, (90, 160, 230), (190, 220, 245)); d.rectangle([0, H * .62, W, H], fill=(238, 222, 190))
        for cx, s in ((W * .25, 1.0), (W * .6, .75), (W * .85, .5)):
            base = H * .78 + (1 - s) * H * .05
            d.polygon([(cx - 18 * k * s, base), (cx + 18 * k * s, base), (cx + 12 * k * s, base - 70 * k * s), (cx - 12 * k * s, base - 70 * k * s)], fill=(225, 222, 210))
            d.ellipse([cx - 75 * k * s, base - 120 * k * s, cx + 75 * k * s, base - 55 * k * s], fill=(250, 250, 246))
            d.ellipse([cx - 60 * k * s, base - 85 * k * s, cx + 70 * k * s, base - 58 * k * s], fill=(222, 220, 212))
    elif name == 'oasis':
        _sky(d, W, H, (100, 170, 235), (230, 225, 200)); d.rectangle([0, H * .6, W, H], fill=(225, 180, 105))
        d.ellipse([W * .22, H * .70, W * .80, H * .92], fill=(50, 150, 190))
        for cx, s in ((W * .2, 1), (W * .34, .8), (W * .7, 1.1), (W * .85, .8), (W * .5, .7)):
            base = H * .74; top = base - 110 * k * s
            d.line([(cx, base), (cx - 6 * k, (base + top) / 2), (cx, top)], fill=(120, 80, 40), width=int(9 * k * s), joint='curve')
            for a in range(-170, 10, 30):
                r = math.radians(a)
                d.line([(cx, top), (cx + 60 * k * s * math.cos(r), top + 30 * k * s * math.sin(r) + 22 * k * s)], fill=(40, 140, 60), width=int(10 * k * s))
    elif name == 'capital':
        _sky(d, W, H, (240, 160, 100), (255, 220, 170)); d.rectangle([0, H * .78, W, H], fill=(225, 180, 105))
        for i in range(12):
            x = W * (.05 + i * .08); hh = H * rnd.uniform(.18, .42)
            d.rectangle([x, H * .78 - hh, x + W * .055, H * .78], fill=(110, 130, 160))
            for y in range(int(H * .78 - hh + 8 * k), int(H * .78), 12 * k):
                d.line([(x + 6 * k, y), (x + W * .055 - 6 * k, y)], fill=(250, 220, 150), width=2 * k)
        cx = W * .62
        d.polygon([(cx - 30 * k, H * .78), (cx + 30 * k, H * .78), (cx + 12 * k, H * .1), (cx, H * .02), (cx - 12 * k, H * .1)], fill=(70, 90, 130))
    im = im.resize((w, h), Image.LANCZOS)
    B = 6
    fr = Image.new('RGBA', (w + 2 * B, h + 2 * B), (255, 255, 255, 255)); fr.paste(im, (B, B))
    return fr


def place_card(fr, angle):
    w, h = fr.size; pad = 40
    can = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', can.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([pad + 12, pad + 16, pad + w + 12, pad + h + 16], fill=(0, 0, 0, 140))
    can.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9))); can.alpha_composite(fr, (pad, pad))
    return can.rotate(angle, resample=Image.BICUBIC, expand=True)


# ---------------------------------------------------------------- emoji (3D-ish, code drawn)
def emoji(kind, size=345):
    k = 2; S = size * k
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    y, x = np.mgrid[0:S, 0:S].astype(np.float32) / S
    r = np.sqrt((x - .5) ** 2 + (y - .5) ** 2)
    m = np.clip((0.46 - r) * S / 2, 0, 1)
    hl = np.sqrt((x - .38) ** 2 + (y - .32) ** 2)
    base = np.stack([255 - 20 * hl, 215 - 90 * hl, 50 + 0 * hl], -1)
    shade = np.clip(1.08 - 0.42 * np.clip(r / .46, 0, 1) ** 4, 0, 1)[..., None]
    rgb = np.clip(base * shade + 60 * np.exp(-(hl / .12) ** 2)[..., None], 0, 255)
    im = Image.fromarray(np.dstack([rgb, m * 255]).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im); u = S / 100
    brown = (90, 50, 20)
    if kind == 'smile':
        for ex in (35, 65):
            d.ellipse([ex * u - 5 * u, 30 * u, ex * u + 5 * u, 46 * u], fill=brown)
            d.ellipse([ex * u - 2 * u, 32 * u, ex * u + 1 * u, 37 * u], fill=(255, 255, 255))
        d.chord([24 * u, 40 * u, 76 * u, 82 * u], 0, 180, fill=brown)
        d.chord([30 * u, 62 * u, 70 * u, 82 * u], 200, 340, fill=(230, 80, 80))
        d.rectangle([28 * u, 60 * u, 72 * u, 64 * u], fill=(255, 255, 255))
    else:  # thinking
        d.arc([26 * u, 18 * u, 44 * u, 30 * u], 200, 340, fill=brown, width=int(3 * u))
        d.arc([56 * u, 20 * u, 74 * u, 30 * u], 200, 340, fill=brown, width=int(3 * u))
        for ex in (36, 64):
            d.ellipse([ex * u - 5 * u, 32 * u, ex * u + 5 * u, 46 * u], fill=brown)
            d.ellipse([ex * u - 1 * u, 33 * u, ex * u + 3 * u, 38 * u], fill=(255, 255, 255))
        d.line([34 * u, 66 * u, 54 * u, 63 * u], fill=brown, width=int(4 * u))
        hand = (250, 180, 40)
        d.rounded_rectangle([60 * u, 60 * u, 68 * u, 82 * u], radius=4 * u, fill=hand, outline=(200, 130, 20), width=int(1.5 * u))
        d.ellipse([52 * u, 76 * u, 84 * u, 98 * u], fill=hand, outline=(200, 130, 20), width=int(1.5 * u))
    return im.resize((size, size), Image.LANCZOS)


# ---------------------------------------------------------------- subscribe button
def subscribe(state):
    w, h = 560, 130
    im, d, k = ss(w, h, 2)
    col = (220, 30, 30) if state < 1 else (110, 110, 115)
    d.rounded_rectangle([6 * k, 10 * k, (w - 6) * k, (h - 10) * k], radius=55 * k, fill=col)
    d.pieslice([50 * k, 34 * k, 104 * k, 96 * k], 180, 360, fill=(255, 255, 255))
    d.polygon([(50 * k, 65 * k), (104 * k, 65 * k), (110 * k, 84 * k), (44 * k, 84 * k)], fill=(255, 255, 255))
    d.ellipse([70 * k, 84 * k, 84 * k, 98 * k], fill=(255, 255, 255))
    f = ImageFont.truetype(FONT_B, 54 * k)
    d.text((140 * k, 65 * k), 'SUBSCRIBE' if state < 1 else 'SUBSCRIBED', font=f, fill=(255, 255, 255), anchor='lm')
    return down(im, w, h)


def cursor():
    im, d, k = ss(70, 90, 3)
    pts = [(10, 6), (10, 66), (25, 52), (36, 78), (46, 74), (35, 48), (56, 48)]
    d.polygon([(x * k, y * k) for x, y in pts], fill=(255, 255, 255), outline=(20, 20, 20), width=3 * k)
    return down(im, 70, 90)
