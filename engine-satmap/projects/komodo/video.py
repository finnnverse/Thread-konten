import os, sys, math, json, functools, numpy as np, cairocffi as cairo
HERE = os.path.dirname(os.path.abspath(__file__))
_r = HERE
while not os.path.isdir(os.path.join(_r, 'engine')): _r = os.path.dirname(_r)
sys.path.insert(0, os.path.join(_r, 'engine'))
from core import *

TAIL = 64.8
ISL = json.load(open(os.path.join(S, 'assets', 'islands.json')))
KOM, RIN, FLO, BALI, JAVA, AUS = ISL['komodo'], ISL['rinca'], ISL['flores'], ISL['bali'], ISL['java'], ISL['australia']
KR = KOM + RIN
KOMODO_PT = (119.47, -8.57)

CAM = CamPath((119.6, -8.6, 5.5), [
    (0.0, 2.9, 119.58, -8.64, 1.7),
    (3.18, 4.3, 117.6, -8.45, 6.6),
    (5.56, 6.4, 119.6, -8.62, 2.6),
    (10.3, 12.4, 132, -16, 42),
    (18.4, 18.9, 142, -18, 30),
    (22.6, 25.0, 123, -10, 14),
    (25.32, 26.3, 120.9, -8.65, 4.6),
    (27.54, 28.6, 117.2, -8.3, 10),
    (31.76, 32.6, 120.2, -8.65, 4.0),
    (34.3, 35.2, 136, -19, 40),
    (36.4, 37.6, 119.58, -8.64, 1.9),
    (41.2, 42.0, 120.5, -8.6, 3.8),
    (50.0, 50.3, 120.2, -9.0, 12),
    (52.8, 55.2, 119.58, -8.64, 2.2),
    (56.28, 57.4, 119.58, -8.64, 2.7),
])
CAM.punches = [9.44, 18.38, 35.94, 45.1, 57.58]
CAM.shakes = [45.1, 57.58]

CAPS = caption_list([
    (0.0, 'KADAL TERBESAR DI DUNIA', 'CUMA DI SINI', 1.22),
    (3.18, 'PADAHAL BALI', 'LEBIH SUBUR|good', 4.56),
    (5.56, 'BANYAK YANG NGIRA', 'ASLI SINI?', 7.38),
    (8.24, 'TAPI CERITANYA', 'KEBALIK!|danger|big', 9.44),
    (9.98, 'MUNDUR HAMPIR', '4 JUTA TAHUN', 11.28),
    (13.02, 'PENELITI NEMU', 'FOSIL RAKSASA', 14.18),
    (15.44, 'DIBANDINGIN SAMA', 'KOMODO SEKARANG|good', 17.08),
    (18.02, 'TERNYATA...', 'SAMA!|good|big', 18.38),
    (18.7, 'JADI KOMODO ITU', 'PENDATANG|accent|big', 20.12),
    (20.7, 'KOMODO JAGO', 'BERENANG|water|big', 21.64),
    (22.08, 'DIDUGA LOMPAT', 'PULAU KE PULAU', 23.74),
    (25.32, 'SAMPAI FLORES', '±900 RIBU TAHUN LALU', 26.02),
    (27.54, 'KENAPA BERHENTI', 'DI SINI?', 28.64),
    (28.94, 'DUGAANNYA: DI BARAT', 'ADA HARIMAU|danger', 31.2),
    (31.76, 'DI FLORES', 'KADAL JADI RAJA', 33.1),
    (34.56, 'YANG DI AUSTRALIA', 'HILANG|danger|big', 35.94),
    (36.4, 'PULAU KECIL INI', 'BENTENG TERAKHIR|accent|big', 37.92),
    (39.88, 'TAPI SEKARANG', 'TERANCAM|danger|big', 40.98),
    (41.4, 'HUTAN DIBUKA', 'LAUT TERUS NAIK|water', 43.12),
    (44.02, 'STATUSNYA SEKARANG', 'TERANCAM PUNAH|danger', 45.1),
    (45.8, 'HABITATNYA MENYUSUT', 'MIN. 30%|danger|big', 47.74),
    (48.78, 'DALAM', '45 TAHUN|accent|big', 49.2),
    (50.78, 'DULU LAUT SURUT', 'MENGANTAR|water', 51.84),
    (52.8, 'SEKARANG LAUT NAIK', 'MENENGGELAMKAN|danger', 54.82),
    (56.28, 'DAN KALI INI', 'GARA-GARA KITA|danger|big', 57.58),
    (58.98, 'JUJUR DEH...', 'KOMODO ASLI MANA?', 60.68),
    (62.12, 'TULIS DI', 'KOMENTAR|accent|big', 62.44),
], TAIL)

def sea_level(t):
    if 42.9 <= t < 44.4: return 12 * ease((t - 43.0) / 1.0)
    if 50.4 <= t < 52.8: return -120 * ease((t - 50.9) / 1.5)
    if 52.8 <= t < 58.9:
        if t < 53.9: return -120 * (1 - ease((t - 52.8) / 1.1))
        return 14 * ease((t - 54.0) / 1.4)
    return 0.0

JOURNEY = [(150.3, -23.0), (145.5, -18.5), (141.5, -15.5), (136.5, -12.6), (131.5, -11.8), (127.4, -10.4),
           (124.3, -9.7), (122.4, -8.8), (120.4, -8.68), (119.5, -8.6)]

def komodo_on_map(ctx, cam, t, lon, lat, width, t_pop, name='komodo', flip=False, rot=0.0, alpha=1.0):
    if t < t_pop: return None
    x, y = cam.pt(lon, lat); s = pop(t, t_pop, 0.32)
    bob = 3 * math.sin(t * 5.0)
    # sticker shadow
    ctx.save(); ctx.translate(x, y + 4); ctx.scale(1, 0.25)
    ctx.arc(0, 0, width * 0.5 * s, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgba(0, 0, 0, 0.28 * alpha); ctx.fill()
    draw_sprite(ctx, name + '_st', x, y + bob, width * 1.45 * s, anchor=(0.5, 0.86), flipx=flip, rot=rot, alpha=alpha)
    return x, y

def suitcase(ctx, x, y, s, a):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -40, -60, 80, 60, 10); ctx.set_source_rgba(0.55, 0.33, 0.18, a); ctx.fill_preserve()
    ctx.set_source_rgba(0.17, 0.1, 0.05, a); ctx.set_line_width(5); ctx.stroke()
    ctx.new_path(); ctx.arc(0, -60, 16, math.pi, 2 * math.pi); ctx.stroke()
    ctx.move_to(-40, -32); ctx.line_to(40, -32); ctx.set_source_rgba(1, 0.75, 0.2, a); ctx.set_line_width(6); ctx.stroke()
    ctx.restore()

@functools.lru_cache(None)
def clearing_cells():
    rng = np.random.default_rng(3); cells = []
    for lon in np.arange(119.8, 122.6, 0.055):
        for lat in np.arange(-9.0, -8.2, 0.055):
            cells.append((lon + rng.random() * 0.01, lat + rng.random() * 0.01, rng.random()))
    return cells

def overlays(ctx, t, cam):
    # B1-B4 komodo on its island
    if t < 10.2:
        a = fade(t, 1.0) if t < 9.9 else clamp((10.2 - t) / 0.3)
        fill_island(ctx, cam, KR, 'accent', 0.5 * fade(t, 1.3, 3.3, 0.4) + 0.0)
        if 1.9 < t < 3.4:
            x, y = cam.pt(119.45, -8.52); arrow_label(ctx, 'P. KOMODO', x - 230, y - 330, x - 30, y - 120, 'white', 40, fade(t, 1.9, 3.3))
            x, y = cam.pt(119.70, -8.70); arrow_label(ctx, 'RINCA', x + 170, y + 300, x + 20, y + 60, 'white', 40, fade(t, 2.2, 3.3))
        rot = math.pi * ease((t - 9.44) / 0.35) if t > 9.44 else 0
        w = 190 if t < 3.2 else 150
        komodo_on_map(ctx, cam, t, *KOMODO_PT, w, 0.9, rot=rot, alpha=a)
        if 3.4 < t < 5.7:
            a2 = fade(t, 3.74, 5.6)
            fill_island(ctx, cam, BALI, 'good', 0.6 * a2)
            x, y = cam.pt(115.15, -8.15); arrow_label(ctx, 'BALI', x + 10, y - 260, x, y - 30, 'white', 44, a2)
        if 6.9 < t < 8.3:
            x, y = cam.pt(*KOMODO_PT); qmark(ctx, x + 150, y - 190, 62 * pop(t, 7.0), t, fade(t, 7.0, 8.25))
    # rewind clock
    if 9.98 <= t < 12.8:
        a = fade(t, 10.0, 12.7, 0.25); cx, cy = W / 2, 1060
        ring(ctx, cx, cy, 120, 'white', 0.9 * a, 10)
        ctx.new_path(); ctx.arc(cx, cy, 120, 0, 2 * math.pi); ctx.set_source_rgba(0.05, 0.1, 0.2, 0.45 * a); ctx.fill()
        for i in range(12):
            an = i * math.pi / 6; ctx.move_to(cx + 96 * math.cos(an), cy + 96 * math.sin(an)); ctx.line_to(cx + 108 * math.cos(an), cy + 108 * math.sin(an))
        ctx.set_source_rgba(1, 1, 1, a); ctx.set_line_width(5); ctx.stroke()
        for L, sp, wdt in [(70, -9.0, 9), (95, -30.0, 6)]:
            an = sp * (t - 10) - math.pi / 2
            ctx.move_to(cx, cy); ctx.line_to(cx + L * math.cos(an), cy + L * math.sin(an))
            ctx.set_source_rgba(*hexc('accent', a)); ctx.set_line_width(wdt); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        for k in range(2):
            x0 = 60 + k * 54
            ctx.move_to(x0 + 50, 560); ctx.line_to(x0, 590); ctx.line_to(x0 + 50, 620); ctx.close_path()
            ctx.set_source_rgba(1, 1, 1, a * (0.6 + 0.4 * (int(t * 4) % 2))); ctx.fill()
    if 12.3 < t < 13.4:
        a = fade(t, 12.48)
        fill_island(ctx, cam, AUS, 'accent', 0.35 * a)
        x, y = cam.pt(150.5, -23.3); pulse(ctx, x, y, t, 12.7, 'accent')
    # B7 pendatang
    if 18.6 < t < 20.9:
        fill_island(ctx, cam, AUS, 'accent', 0.25 * fade(t, 18.7, 20.8))
        r = komodo_on_map(ctx, cam, t, 147.5, -21.5, 230, 18.95)
        if r and t > 20.12:
            suitcase(ctx, r[0] + 150, r[1] + 5, pop(t, 20.12), 1.0)
        x, y = cam.pt(146, -24.5)
        arrow_label(ctx, 'QUEENSLAND', x - 120, y + 260, x, y + 30, 'white', 40, fade(t, 19.2, 20.8))
    # B9 journey
    if 22.0 < t < 28.0:
        pts = smooth([cam.pt(*p) for p in JOURNEY], 10)
        frac = ease_io((t - 22.4) / 2.6)
        a = fade(t, 22.1, 27.9, 0.4)
        ctx.set_dash([18, 14]); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        head, ang = polyline_partial(ctx, pts, frac)
        ctx.set_source_rgba(0, 0, 0, 0.35 * a); ctx.set_line_width(10); ctx.stroke_preserve()
        ctx.set_source_rgba(*hexc('accent', a)); ctx.set_line_width(6); ctx.stroke(); ctx.set_dash([])
        if t < 25.6:
            for sx, sy in [cam.pt(129.5, -11.2), cam.pt(125.7, -10.1), cam.pt(123.3, -9.25)]:
                d = math.hypot(head[0] - sx, head[1] - sy)
                if d < 90: ring(ctx, sx, sy, 20 + (90 - d) * 0.6, 'water', 0.8 * (d / 90), 4)
            draw_sprite(ctx, 'komodo_st', head[0], head[1] + 2 * math.sin(t * 9), 220, anchor=(0.5, 0.86), flipx=True)
    if 25.0 < t < 27.6:
        a = fade(t, 25.6, 27.5)
        fill_island(ctx, cam, FLO + KR, 'accent', 0.5 * a)
    if 25.5 < t < 31.9:
        komodo_on_map(ctx, cam, t, *KOMODO_PT, 140, 25.5, flip=True, alpha=fade(t, 25.5, 31.8))
    # B11-12 west
    if 27.6 < t < 32.0:
        a = fade(t, 27.7, 31.9)
        p0 = cam.pt(119.2, -8.5); p1 = cam.pt(116.6, -8.3)
        ctx.set_dash([16, 12]); ctx.move_to(*p0)
        u = ease((t - 27.9) / 0.7); ctx.line_to(p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
        ctx.set_source_rgba(1, 1, 1, a); ctx.set_line_width(6); ctx.stroke(); ctx.set_dash([])
        if t > 28.6: x, y = cam.pt(116.0, -8.45); qmark(ctx, x, y - 120, 60 * pop(t, 28.6), t, a * fade(t, 28.6, 30.4))
        if t > 30.4:
            fill_island(ctx, cam, JAVA + BALI, 'danger', 0.38 * fade(t, 30.5, 31.9))
            for i, (lo, la) in enumerate([(111.6, -7.45), (113.7, -7.95), (115.15, -8.35)]):
                x, y = cam.pt(lo, la); s = pop(t, 31.2 + 0.14 * i)
                draw_sprite(ctx, 'tiger_st', x, y - 50, 160 * s, alpha=a)
    # B13 raja
    if 31.7 < t < 34.7:
        a = fade(t, 31.8, 34.6)
        fill_island(ctx, cam, FLO + KR, 'accent', 0.35 * fade(t, 32.26, 34.6))
        r = komodo_on_map(ctx, cam, t, 120.25, -8.62, 250, 31.9, alpha=a)
        if r and t > 33.55:
            u = clamp((t - 33.55) / 0.35); yb = -220 * (1 - back(u))
            draw_sprite(ctx, 'crown_st', r[0] + 0.30 * 360, r[1] - 0.33 * 360 + yb, 120, rot=0.25, alpha=a)
    # B14 hilang
    if 34.4 < t < 36.7:
        a = fade(t, 34.5, 36.6)
        for i, (lo, la) in enumerate([(146, -20.5), (149.5, -24.5), (143.5, -24.5)]):
            nm = 'komodo' if t < 35.94 else 'fossil'
            al = a if t < 35.94 else a * (1 - 0.6 * clamp((t - 35.94) / 0.3))
            komodo_on_map(ctx, cam, t, lo, la, 140, 34.6 + 0.12 * i, alpha=al, name=nm)
        if t > 35.94:
            x, y = cam.pt(146.5, -23); red_x(ctx, x, y - 40, 70, a, (t - 35.94) / 0.3)
    # B15-16 benteng
    if 36.4 < t < 44.2:
        a = fade(t, 36.5, 44.0)
        komodo_on_map(ctx, cam, t, *KOMODO_PT, 170 if t < 41 else 130, 36.6, alpha=a)
        if t > 37.92 and t < 41.6:
            x, y = cam.pt(119.58, -8.64); r = cam.px_per_deg() * 0.3 * (0.6 + 0.4 * ease_out((t - 37.92) / 0.4))
            col = 'accent' if t < 40.98 else 'danger'
            ring(ctx, x, y, r, col, 0.9 * fade(t, 37.92, 41.5), 10)
            ring(ctx, x, y, r + 14, col, 0.35 * fade(t, 37.92, 41.5), 18)
            fill_island(ctx, cam, KR, col, 0.35 * fade(t, 37.92, 41.5))
            if t > 40.98: pulse(ctx, x, y, t, 40.98, 'danger', r, r + 120, 0.9)
        if 40.98 < t < 41.6:
            ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(0.7, 0.05, 0.1, 0.12 * (1 + math.sin(t * 12)) * fade(t, 40.98, 41.5)); ctx.fill()
    # B17 clearing
    if 42.2 < t < 44.3:
        a = fade(t, 42.3, 44.2)
        ctx.save()
        for r in FLO: poly_path(ctx, cam, r)
        ctx.clip()
        c0 = (120.9, -8.6); prog = (t - 42.34) * 0.9
        k = cam.px_per_deg() * 0.05
        for lon, lat, rr in clearing_cells():
            d = math.hypot(lon - c0[0], lat - c0[1]) * 1.3 + rr * 0.15
            if d < prog:
                x, y = cam.pt(lon, lat); s = clamp((prog - d) / 0.15)
                ctx.rectangle(x - k * s / 2, y - k * s / 2, k * s * 0.92, k * s * 0.92)
                ctx.set_source_rgba(0.78, 0.6, 0.36, 0.75 * a); ctx.fill_preserve()
                ctx.set_source_rgba(0.45, 0.32, 0.16, 0.6 * a); ctx.set_line_width(1.5); ctx.stroke()
        ctx.restore()
    # B18 stamp
    if 44.0 < t < 46.1:
        a = fade(t, 44.05, 46.0)
        ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(0.02, 0.04, 0.08, 0.4 * a); ctx.fill()
        if t > 45.1:
            u = clamp((t - 45.1) / 0.18); s = 1.8 - 0.8 * ease_out(u)
            ctx.save(); ctx.translate(W / 2, 1080); ctx.rotate(-0.12); ctx.scale(s, s)
            rrect(ctx, -380, -120, 760, 240, 26); ctx.set_source_rgba(*hexc('danger', a * u)); ctx.set_line_width(14); ctx.stroke()
            rrect(ctx, -362, -102, 724, 204, 18); ctx.set_source_rgba(*hexc('danger', 0.18 * a * u)); ctx.fill()
            ctx.restore()
            draw_text(ctx, 'TERANCAM PUNAH', W / 2, 1060, 96, 'danger', 'punch', scale=s, alpha=a * u, rot=-0.12, stroke=4)
            draw_text(ctx, 'IUCN · 2021', W / 2 + 14, 1160, 40, 'white', 'body', scale=s, alpha=a * u, rot=-0.12, stroke=3)
    # B20 laut surut
    if 50.3 < t < 52.9:
        a = fade(t, 50.4, 52.8)
        if t > 51.6:
            seg = smooth([cam.pt(*p) for p in JOURNEY[5:]], 10)
            ctx.set_dash([18, 14]); head, _ = polyline_partial(ctx, seg, ease_io((t - 51.7) / 1.0))
            ctx.set_source_rgba(*hexc('accent', a)); ctx.set_line_width(6); ctx.stroke(); ctx.set_dash([])
            draw_sprite(ctx, 'komodo_st', head[0], head[1], 200, anchor=(0.5, 0.86), flipx=True, alpha=a)
        draw_text(ctx, f'{sea_level(t):+.0f} M', 900, 1500, 60, 'water', 'punch', alpha=a * fade(t, 50.8), stroke=4)
    # B21 laut naik
    if 52.8 < t < 58.4:
        a = fade(t, 52.9, 58.3)
        nm = 'komodo' if t < 54.82 else 'komodo_sad'
        komodo_on_map(ctx, cam, t, *KOMODO_PT, 170, 53.3, name=nm, alpha=a)
        if t > 54.0:
            x, y = cam.pt(119.58, -8.64)
            for i in range(3):
                u = ((t - 54.0) / 1.6 + i / 3) % 1
                ring(ctx, x, y, cam.px_per_deg() * (0.55 - 0.3 * u), 'water', 0.7 * u * a, 5)
        if t < 55.4: draw_text(ctx, f'{sea_level(t):+.0f} M', 900, 1500, 60, 'water', 'punch', alpha=a * fade(t, 52.8, 55.4), stroke=4)
    if 56.2 < t < 58.9:
        a = fade(t, 56.3, 58.8)
        ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(0.45, 0.03, 0.08, 0.28 * a); ctx.fill()
        if t > 57.5:
            s = pop(t, 57.58)
            for i in range(3):
                u = ((t - 57.58) * 0.8 + i / 3) % 1
                ctx.new_path(); ctx.arc(470 + 40 * i, 1180 - 260 * u, 30 + 40 * u, 0, 2 * math.pi)
                ctx.set_source_rgba(0.6, 0.6, 0.65, 0.6 * (1 - u) * a); ctx.fill()
            draw_sprite(ctx, 'factory', W / 2, 1520, 420 * s, alpha=a, anchor=(0.5, 1.0))

# ---------------- scenes ----------------
def grad(ctx, y0, y1, c0, c1):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgb(0, *[c / 255 for c in c0]); g.add_color_stop_rgb(1, *[c / 255 for c in c1])
    ctx.set_source(g); ctx.rectangle(0, y0, W, y1 - y0); ctx.fill()

def wavy_band(ctx, y, amp, wl, col, ph=0.0, bottom=H):
    ctx.new_path(); ctx.move_to(0, bottom)
    for x in range(0, W + 21, 20): ctx.line_to(x, y + amp * math.sin(x / wl + ph))
    ctx.line_to(W, bottom); ctx.close_path(); ctx.set_source_rgba(*col); ctx.fill()

def scene_dig(ctx, t):
    grad(ctx, 0, 780, (255, 214, 153), (246, 152, 98))
    ctx.new_path(); ctx.arc(820, 600, 95, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.95, 0.8, 0.85); ctx.fill()
    ctx.move_to(0, 780); ctx.line_to(0, 700); ctx.line_to(140, 690); ctx.line_to(170, 640); ctx.line_to(330, 640); ctx.line_to(360, 700)
    ctx.line_to(700, 710); ctx.line_to(730, 670); ctx.line_to(900, 668); ctx.line_to(940, 720); ctx.line_to(W, 720); ctx.line_to(W, 780); ctx.close_path()
    ctx.set_source_rgb(0.72, 0.36, 0.24); ctx.fill()
    for i, c in enumerate([(190, 92, 58), (166, 74, 48), (140, 58, 40), (112, 46, 34)]):
        wavy_band(ctx, 770 + i * 290, 10, 90 + i * 20, (c[0] / 255, c[1] / 255, c[2] / 255, 1), i)
    rrect(ctx, 90, 1070, 900, 440, 30); ctx.set_source_rgba(0.3, 0.12, 0.08, 0.55); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35); ctx.set_line_width(3)
    for x in range(90, 991, 150): ctx.move_to(x, 1070); ctx.line_to(x, 1510)
    for y in range(1070, 1511, 110): ctx.move_to(90, y); ctx.line_to(990, y)
    ctx.stroke()
    draw_sprite(ctx, 'fossil', W / 2, 1290, 700, rot=-0.03)
    rx = 900 + 300 * (1 - ease_out((t - 13.0) / 0.5))
    draw_sprite(ctx, 'researcher', rx, 1800 + 6 * math.sin(t * 6), 230, anchor=(0.5, 1.0), rot=0.04 * math.sin(t * 3))
    rrect(ctx, W / 2 - 250, 470, 500, 70, 35); ctx.set_source_rgba(0.06, 0.1, 0.16, 0.75); ctx.fill()
    draw_text(ctx, 'QUEENSLAND, AUSTRALIA', W / 2, 505, 38, 'white', 'body', stroke=0, shadow=False)
    if t > 15.44:
        x = W / 2 + 700 * (1 - ease_out((t - 15.44) / 0.6))
        draw_sprite(ctx, 'komodo', x, 900 + 5 * math.sin(t * 5), 700)
        if t > 16.7:
            a = fade(t, 16.7)
            ctx.set_dash([12, 10]); ctx.set_source_rgba(1, 1, 1, 0.85 * a); ctx.set_line_width(4)
            for xx in (300, 560, 830): ctx.move_to(xx, 960); ctx.line_to(xx, 1230)
            ctx.stroke(); ctx.set_dash([])
        if t > 18.38:
            s = pop(t, 18.38); ctx.new_path(); ctx.arc(W / 2, 1100, 72 * s, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexc('good')); ctx.fill_preserve(); ctx.set_source_rgba(1, 1, 1, 1); ctx.set_line_width(7); ctx.stroke()
            ctx.move_to(W / 2 - 32 * s, 1100); ctx.line_to(W / 2 - 8 * s, 1126 * 1 + 0 * s); ctx.line_to(W / 2 + 36 * s, 1072)
            ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()

def scene_swim(ctx, t):
    grad(ctx, 0, 1000, (140, 214, 236), (226, 248, 255))
    ctx.new_path(); ctx.arc(840, 560, 80, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.86, 0.35, 1); ctx.fill()
    ctx.new_path(); ctx.move_to(40, 1000); ctx.curve_to(120, 900, 260, 900, 330, 1000); ctx.close_path(); ctx.set_source_rgb(0.3, 0.55, 0.3); ctx.fill()
    grad(ctx, 990, H, (40, 175, 190), (10, 76, 118))
    x = 330 + 110 * (t - 20.7); y = 1080 + 10 * math.sin(t * 4)
    draw_sprite(ctx, 'komodo', x, y, 600, rot=0.04 * math.sin(t * 3))
    wavy_band(ctx, 1110, 14, 60, (0.16, 0.66, 0.74, 0.88), t * 3)
    ctx.set_source_rgba(1, 1, 1, 0.6); ctx.set_line_width(5); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(7):
        yy = 1220 + i * 95; xx = (i * 173 + t * 120) % (W + 200) - 100
        ctx.move_to(xx, yy); ctx.curve_to(xx + 30, yy - 14, xx + 60, yy - 14, xx + 90, yy); ctx.stroke()
    for i in range(5):
        u = ((t * 2) + i / 5) % 1
        ctx.new_path(); ctx.arc(x - 300 - 30 * i, 1100 - 60 * math.sin(math.pi * u), 8, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.8 * (1 - u)); ctx.fill()

HAB_CAM = Cam(119.47, -8.575, 0.36)
def scene_habitat(ctx, t):
    grad(ctx, 0, H, (16, 62, 74), (6, 28, 38))
    cam = HAB_CAM; cam.oy = -30
    pts = [cam.pt(*p) for p in KOM[0]]
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    def path(k):
        ctx.new_path()
        for i, (x, y) in enumerate(pts): (ctx.move_to if i == 0 else ctx.line_to)(cx + (x - cx) * k, cy + (y - cy) * k)
        ctx.close_path()
    path(1.0); ctx.set_source_rgba(*hexc('danger', 0.45 * fade(t, 47.3))); ctx.fill()
    k = 1 - (1 - math.sqrt(0.7)) * ease_io((t - 47.3) / 1.0)
    path(k); ctx.set_source_rgba(0.45, 0.6, 0.3, 1); ctx.fill_preserve()
    ctx.set_source_rgba(1, 0.97, 0.88, 1); ctx.set_line_width(4); ctx.stroke()
    path(1.0); ctx.set_dash([14, 10]); ctx.set_source_rgba(1, 1, 1, 0.8); ctx.set_line_width(4); ctx.stroke(); ctx.set_dash([])
    draw_sprite(ctx, 'komodo_sad_st' if t > 47.5 else 'komodo_st', cx, cy + 60, 320, anchor=(0.5, 0.86))
    draw_text(ctx, 'P. KOMODO', cx, cy - 330, 40, 'white', 'body', stroke=3, alpha=fade(t, 46.0))
    if t > 47.74:
        n = int(round(30 * ease_out((t - 47.74) / 0.6)))
        draw_text(ctx, f'-{n}%', W / 2, 1600, 150, 'danger', 'punch', scale=0.7 + 0.3 * pop(t, 47.74), stroke=6)
    if t > 49.2:
        s = 1.5 * pop(t, 49.2); hx, hy = W / 2, 1790
        ctx.save(); ctx.translate(hx, hy); ctx.scale(s, s)
        ctx.move_to(-34, -50); ctx.line_to(34, -50); ctx.line_to(0, 0); ctx.line_to(34, 50); ctx.line_to(-34, 50); ctx.line_to(0, 0); ctx.close_path()
        ctx.set_source_rgba(1, 0.9, 0.6, 1); ctx.fill_preserve(); ctx.set_source_rgba(0.05, 0.1, 0.15, 1); ctx.set_line_width(5); ctx.stroke()
        ctx.restore()

THUMBS = {}
def thumb(key, lon, lat, span):
    if key not in THUMBS:
        im = map_image(Cam(lon, lat, span)).crop((0, 360, 1080, 1260)).resize((360, 300))
        THUMBS[key] = rgb_surface(im)
    return THUMBS[key]

def card(ctx, x, y, s, a, surf, num, numcol, label):
    if s <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -195, -6, 390, 450, 34); ctx.set_source_rgba(0, 0, 0, 0.3 * a); ctx.fill()
    rrect(ctx, -195, -20, 390, 450, 34); ctx.set_source_rgba(1, 1, 1, a); ctx.fill()
    ctx.save(); rrect(ctx, -180, -5, 360, 300, 24); ctx.clip(); ctx.set_source_surface(surf, -180, -5); ctx.paint_with_alpha(a); ctx.restore()
    ctx.new_path(); ctx.arc(-172, -14, 40, 0, 2 * math.pi); ctx.set_source_rgba(*hexc(numcol, a)); ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, a); ctx.set_line_width(6); ctx.stroke()
    ctx.restore()
    draw_text(ctx, str(num), x - 172 * s, y - 14 * s, int(54 * s) or 1, 'white', 'punch', stroke=0, shadow=False, alpha=a)
    draw_text(ctx, label, x, y + 360 * s, int(52 * s) or 1, (11, 27, 43), 'punch', stroke=0, shadow=False, alpha=a)

def scene_cta(ctx, t):
    grad(ctx, 0, H, (22, 70, 92), (98, 160, 112))
    for i, (yy, c) in enumerate([(1500, (0.2, 0.42, 0.3)), (1620, (0.14, 0.33, 0.22)), (1760, (0.1, 0.24, 0.16))]):
        wavy_band(ctx, yy, 40, 160 + 40 * i, c + (1,), i * 1.7)
    card(ctx, 285, 700, 1.15 * pop(t, 60.9), 1.0, thumb('flo', 120.6, -8.6, 3.0), 1, 'accent', 'FLORES')
    card(ctx, 795, 700, 1.15 * pop(t, 61.35), 1.0, thumb('aus', 134, -25, 40), 2, 'water', 'AUSTRALIA')
    if t > 61.2: draw_text(ctx, 'ATAU', W / 2, 900, 44, 'white', 'body', stroke=3, alpha=fade(t, 61.2))
    draw_sprite(ctx, 'komodo_st', 300, 1800 + 5 * math.sin(t * 4), 560, anchor=(0.5, 0.86))
    if t > 59.6:
        s = pop(t, 59.6); ctx.new_path(); ctx.arc(560, 1380, 58 * s, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.95); ctx.fill()
        ctx.arc(510, 1455, 14 * s, 0, 2 * math.pi); ctx.fill(); ctx.arc(485, 1490, 8 * s, 0, 2 * math.pi); ctx.fill()
        draw_text(ctx, '?', 560, 1384, int(80 * s) or 1, (11, 27, 43), 'punch', stroke=0, shadow=False)
    if t > 62.12:
        s = pop(t, 62.12); x, y = 800, 1600
        ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
        rrect(ctx, -190, -70, 380, 140, 40); ctx.set_source_rgba(1, 1, 1, 1); ctx.fill()
        ctx.move_to(120, 60); ctx.line_to(170, 110); ctx.line_to(80, 66); ctx.close_path(); ctx.fill()
        ctx.restore()
        draw_text(ctx, 'Aku:', x - 95 * s, y, int(46 * s) or 1, (11, 27, 43), 'body', stroke=0, shadow=False)
        for i in range(3):
            b = 0.5 + 0.5 * math.sin(t * 8 - i * 0.9)
            ctx.new_path(); ctx.arc(x + (10 + 46 * i) * s, y - 6 * b * s, 13 * s, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexc('accent')); ctx.fill()

SCENES = [(13.02, 18.72, scene_dig), (20.7, 22.1, scene_swim), (45.8, 50.4, scene_habitat), (58.7, TAIL + 1, scene_cta)]

def scene_offset(t, t0, t1):
    if t < t0 or t >= t1: return None
    if t < t0 + 0.3: return H * (1 - ease_io((t - t0) / 0.3))
    if t > t1 - 0.3: return -H * ease_io((t - (t1 - 0.3)) / 0.3)
    return 0.0

def rewind_fx(arr, t):
    if not (9.98 <= t < 12.7): return arr
    a = fade(t, 10.0, 12.6, 0.3)
    out = arr.copy()
    sh = int(10 * a)
    out[..., 2] = np.roll(arr[..., 2], sh, axis=1); out[..., 0] = np.roll(arr[..., 0], -sh, axis=1)
    out[::4] = (out[::4] * (1 - 0.35 * a)).astype(np.uint8)
    rng = np.random.default_rng(int(t * 30))
    for _ in range(3):
        y = rng.integers(0, H - 40); hgt = rng.integers(8, 40)
        out[y:y + hgt] = np.roll(out[y:y + hgt], int(rng.integers(-40, 40) * a), axis=1)
    g = (out[..., :3].astype(np.float32) * (1 - 0.25 * a) + 40 * a)
    out[..., :3] = np.clip(g, 0, 255).astype(np.uint8)
    return out

def frame(t):
    cam = CAM.at(t)
    covered = any((o := scene_offset(t, a, b)) is not None and abs(o) < 1 for a, b, _ in SCENES)
    if covered: base = Image.new('RGB', (W, H))
    else: base = map_image(cam, sea_level(t))
    surf = rgb_surface(base); ctx = cairo.Context(surf)
    if not covered:
        overlays(ctx, t, cam)
        vignette(ctx, 0.5)
    for a, b, fn in SCENES:
        o = scene_offset(t, a, b)
        if o is None: continue
        ctx.save(); ctx.translate(0, o); ctx.rectangle(0, 0, W, H); ctx.clip(); fn(ctx, t)
        g = cairo.LinearGradient(0, 0, 0, 560); g.add_color_stop_rgba(0, 0.01, 0.04, 0.09, 0.35); g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g); ctx.rectangle(0, 0, W, 560); ctx.fill(); ctx.restore()
    for c in CAPS: draw_caption(ctx, t, c)
    surf.flush()
    arr = np.frombuffer(surf.get_data(), np.uint8).reshape(H, W, 4)
    return rewind_fx(arr, t)

# ---------------- sfx cue list ----------------
SFX = [(0.9, 'pop'), (1.22, 'pluck'), (3.18, 'whoosh'), (3.74, 'pop'), (4.56, 'pluck'), (5.56, 'whoosh'), (7.0, 'pop'),
       (8.24, 'tick'), (9.44, 'bonk'), (9.98, 'rewind'), (11.28, 'pluck'), (12.48, 'whoosh'), (13.02, 'whoosh'),
       (14.18, 'pluck'), (15.44, 'whoosh'), (16.7, 'tick'), (18.38, 'ding'), (18.72, 'whoosh'), (18.95, 'pop'),
       (20.12, 'pop'), (20.7, 'splash'), (22.1, 'whoosh'), (23.0, 'splash'), (24.1, 'splash'), (25.32, 'whoosh'),
       (26.02, 'pluck'), (27.54, 'whoosh'), (28.6, 'pop'), (31.2, 'pop'), (31.34, 'pop'), (31.48, 'pop'),
       (31.76, 'whoosh'), (33.72, 'ding'), (34.3, 'whoosh'), (34.6, 'pop'), (35.94, 'bonk'), (36.4, 'whoosh'),
       (37.92, 'pluck'), (40.98, 'thud'), (41.2, 'whoosh'), (42.34, 'tick'), (43.12, 'splash'), (45.1, 'stamp'),
       (45.8, 'whoosh'), (47.74, 'tick'), (49.2, 'pluck'), (50.4, 'whoosh'), (50.9, 'sweep_down'), (52.9, 'sweep_up'),
       (54.82, 'sad'), (56.28, 'whoosh'), (57.58, 'thud'), (58.7, 'whoosh'), (59.6, 'pop'), (60.9, 'pop'), (61.35, 'pop'),
       (62.12, 'bubble')]
