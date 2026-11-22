"""Egypt explainer scene: geography data, camera shots and timeline (all times = video seconds)."""
import json, math, os, re, random
import numpy as np, shapefile
from shapely.geometry import Polygon, MultiPolygon, box as sbox
from shapely.ops import unary_union
import assets as A
from engine import *
import elements as E
from elements import *

NE = os.environ['NE_DIR']; TIMING = os.environ['TIMING']
VO_OFF = .5
DUR = int(os.environ.get('DUR', '182'))

# ------------------------------------------------------------------ word timing
_tm = json.load(open(TIMING))
VO_LEN = _tm['dur']


def T(sec, word, occ=1, end=False):
    n = 0
    for w in _tm['words']:
        if w['sec'] != sec: continue
        if re.sub(r'[^\w-]', '', w['w']) == word:
            n += 1
            if n == occ: return (w['t1'] if end else w['t0']) + VO_OFF
    raise KeyError((sec, word, occ))


def SEC(sec):
    return min(w['t0'] for w in _tm['words'] if w['sec'] == sec) + VO_OFF


S0 = VO_OFF; S1, S2, S3, S4, S5, S6, S7, SP = [SEC(s) for s in ['BAB 1', 'BAB 2', 'BAB 3', 'BAB 4', 'BAB 5', 'BAB 6', 'BAB 7', 'PENUTUP']]
VO_END = VO_OFF + VO_LEN
END0 = round(max(VO_END, T('PENUTUP', 'berikutnya', 2, end=True)) + .25, 2)


# ------------------------------------------------------------------ geography
def to_plane(coords):
    a = np.asarray(coords, np.float64)
    return np.stack([a[:, 0], np.degrees(np.log(np.tan(np.pi / 4 + np.radians(np.clip(a[:, 1], -85, 85)) / 2)))], 1)


def shp_geoms(path, key, vals):
    sf = shapefile.Reader(path); f = [x[0] for x in sf.fields[1:]]
    out = {}
    for r, s in zip(sf.records(), sf.shapes()):
        d = dict(zip(f, r))
        if d.get(key) in vals:
            parts = list(s.parts) + [len(s.points)]
            rings = [s.points[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
            out[d[key]] = rings
    return out


C = shp_geoms(NE + '/ne_10m_admin_0_countries.shp', 'ADM0_A3', {'EGY', 'SDN', 'FRA', 'LBY', 'ISR', 'PSE', 'JOR', 'SAU'})
DSP = shp_geoms(NE + '/ne_10m_admin_0_disputed_areas.shp', 'NAME', {'Bir Tawil', 'Halayib Triangle'})


def shp_poly(rings):
    polys = [Polygon(r) for r in rings if len(r) > 3]
    return unary_union([p.buffer(0) for p in polys])


def rings_of(g, minarea=0.0005):
    out = []
    geoms = g.geoms if hasattr(g, 'geoms') else [g]
    for p in geoms:
        if p.is_empty or p.area < minarea: continue
        out.append(to_plane(np.asarray(p.exterior.coords)))
    return out


EGY_G = shp_poly(C['EGY']); SDN_G = shp_poly(C['SDN'])
BRT_G = shp_poly(DSP['Bir Tawil']); HAL_G = shp_poly(DSP['Halayib Triangle'])
EGY = rings_of(EGY_G); SDN = rings_of(SDN_G.difference(HAL_G))
BRT = rings_of(BRT_G); HAL = rings_of(HAL_G.intersection(EGY_G.union(SDN_G)))
SINAI_G = EGY_G.intersection(Polygon([(32.3, 31.5), (32.3, 30.0), (32.55, 29.93), (32.7, 29.5), (33.1, 28.9), (33.6, 28.2), (34.15, 27.55), (35.5, 27.55), (35.5, 31.5)]))
SINAI = rings_of(SINAI_G); MAIN = rings_of(EGY_G.difference(SINAI_G))
DELTA = rings_of(EGY_G.intersection(Polygon([(31.2, 30.08), (29.85, 31.15), (30.6, 31.6), (31.9, 31.6), (32.3, 31.25)])))
WEST = rings_of(EGY_G.intersection(Polygon([(24.6, 21.8), (24.6, 31.7), (29.7, 31.0), (30.6, 29.5), (30.9, 27.5), (31.8, 25.5), (32.4, 23.9), (31.5, 21.8)])))
# France (mainland), moved onto the map west of Egypt with equal-area correction
fr = max(C['FRA'], key=lambda r: len(r) if (min(p[1] for p in r) > 41 and min(p[0] for p in r) > -6) else 0)
fr = np.asarray(fr)
fc = fr.mean(0)
def move_equal_area(ring, c_from, c_to):
    kx = math.cos(math.radians(c_from[1])) / math.cos(math.radians(c_to[1]))
    out = np.stack([c_to[0] + (ring[:, 0] - c_from[0]) * kx, c_to[1] + (ring[:, 1] - c_from[1])], 1)
    return to_plane(out)
FRA_MOVED = [move_equal_area(fr, fc, (19.0, 26.6))]

# Nile (chain NE river parts within Egypt, south->north)
def nile_line():
    sf = shapefile.Reader(NE + '/ne_10m_rivers_lake_centerlines.shp'); f = [x[0] for x in sf.fields[1:]]
    parts = []
    for r, s in zip(sf.records(), sf.shapes()):
        d = dict(zip(f, r))
        if d['name'] == 'Nile':
            pp = list(s.parts) + [len(s.points)]
            for i in range(len(pp) - 1): parts.append(np.asarray(s.points[pp[i]:pp[i + 1]]))
    # start from part containing the southern-most point above 21.5
    parts = [p for p in parts if p[:, 1].max() > 21.4]
    cur = min(parts, key=lambda p: p[:, 1].min())
    if cur[0, 1] > cur[-1, 1]: cur = cur[::-1]
    chain = [cur]; rest = [p for p in parts if p is not cur]
    while rest:
        end = chain[-1][-1]
        best = min(rest, key=lambda p: min(np.hypot(*(p[0] - end)), np.hypot(*(p[-1] - end))))
        d0, d1 = np.hypot(*(best[0] - end)), np.hypot(*(best[-1] - end))
        if min(d0, d1) > .3: break
        chain.append(best if d0 <= d1 else best[::-1]); rest = [p for p in rest if p is not best]
    line = np.vstack(chain)
    line = line[line[:, 1] > 21.9]
    return line
NILE = nile_line()
DAMIETTA = [(31.23, 30.12), (31.18, 30.47), (31.25, 30.71), (31.38, 31.04), (31.6, 31.25), (31.81, 31.42), (31.84, 31.52)]
ROSETTA = [(31.13, 30.19), (30.98, 30.45), (30.87, 30.65), (30.82, 30.82), (30.65, 31.13), (30.42, 31.40), (30.36, 31.47)]
NILE_FULL = to_plane(np.vstack([NILE, np.asarray(DAMIETTA)]))
CANAL = [(32.30, 31.26), (32.32, 30.85), (32.29, 30.58), (32.33, 30.40), (32.43, 30.26), (32.50, 30.15), (32.56, 29.95)]
GULF = [(32.56, 29.95), (32.65, 29.6), (32.95, 29.1), (33.35, 28.55), (33.8, 27.95), (34.15, 27.6)]
ROUTE_LONG = [(3.0, 51.5), (-3.0, 49.8), (-9.5, 44.5), (-11.0, 38.0), (-16.5, 28.5), (-19.0, 15.0), (-12.0, 4.0), (0.0, -1.5), (8.0, -6.0),
              (11.5, -17.0), (15.5, -30.0), (18.4, -35.6), (26.0, -35.5), (36.0, -29.0), (43.0, -20.0), (49.5, -10.0), (55.5, 2.0), (63.0, 13.0), (72.5, 18.5)]
ROUTE_SUEZ = [(3.0, 51.5), (-3.0, 49.8), (-9.5, 44.5), (-10.5, 37.5), (-5.8, 35.95), (5.0, 37.6), (12.0, 37.6), (20.0, 34.5), (28.0, 32.2), (32.3, 31.35)] + CANAL + \
             [(33.3, 28.4), (35.5, 25.5), (38.5, 20.0), (41.5, 15.0), (43.4, 12.6), (48.0, 12.8), (55.0, 15.0), (63.0, 17.5), (72.5, 18.5)]
L1899 = [(24.98, 22.0), (36.88, 22.0)]
def l1902():
    b = np.asarray(BRT_G.exterior.coords); h = np.asarray(HAL_G.exterior.coords if HAL_G.geom_type == 'Polygon' else max(HAL_G.geoms, key=lambda g: g.area).exterior.coords)
    south = sorted([tuple(p) for p in b if p[1] < 21.99], key=lambda p: p[0])
    bw, be = b[:, 0].min(), b[:, 0].max(); hw = h[np.argmin(h[:, 0])]; hn = h[np.argmax(h[:, 1])]
    return [(24.98, 22.0), (bw, 22.0)] + south + [(be, 22.0), (hw[0], 22.0), (hn[0], hn[1]), (hn[0] + .25, hn[1] - .15)]
L1902 = l1902()
LAKE_NASSER = None
sf = shapefile.Reader(NE + '/ne_10m_lakes.shp'); f = [x[0] for x in sf.fields[1:]]
for r, s in zip(sf.records(), sf.shapes()):
    if dict(zip(f, r))['name'] == 'Lake Nasser':
        LAKE_NASSER = rings_of(shp_poly([s.points[s.parts[i]:(list(s.parts) + [len(s.points)])[i + 1]] for i in range(len(s.parts))]), 0.0)


def P(lon, lat): return to_plane([(lon, lat)])[0]


def PL(pts): return to_plane(pts)


# ------------------------------------------------------------------ camera shots
# (t_start, lon, lat, vw, tilt, rot, dur, mid_vw)
SHOTS = []
def shot(t, lon, lat, vw, tilt=.17, rot=0.0, dur=None, mid=None, snd=True):
    SHOTS.append([t, lon, lat, vw, tilt, rot, dur, mid, snd])

I = 'INTRO'
shot(0.0, 26, 34, 80, .14, -4)
shot(0.55, 30.6, 26.8, 17, .18, 3, dur=2.3)
shot(T(I, 'perbatasannya') - .3, 32.0, 23.6, 13, .17, -2, dur=1.2)
shot(T(I, 'Kamu') - .1, 30.4, 27.2, 18, .18, 2, dur=1.1)
shot(T(I, 'sampai') - .1, 27, 30, 55, .15, -3, dur=1.4)
# BAB 1
B = 'BAB 1'
shot(S1 - .2, 27.0, 27.0, 26, .18, 3, dur=1.6)
shot(T(B, 'Sisanya') - .2, 30.6, 26.6, 15, .19, -3, dur=1.2)
shot(T(B, 'Dari') - .1, 30.0, 27.0, 40, .13, 0, dur=1.5)
shot(T(B, 'Garis') - .1, 31.3, 26.6, 15, .19, 4, dur=1.4)
shot(T(B, 'Satu') - .3, 30.80, 28.10, 1.6, .2, -6, dur=2.0)
shot(T(B, 'Lebih') - .4, 30.8, 27.0, 16, .18, 2, dur=1.7)
# BAB 2
B = 'BAB 2'
shot(S2 - .2, 31.0, 30.75, 4.6, .19, -4, dur=2.2, mid=28)
shot(T(B, 'Di', 2) - .1, 31.24, 30.06, 0.5, .2, 5, dur=1.9)
shot(T(B, 'pinggirnya') - .1, 31.15, 29.98, 0.27, .21, -2, dur=1.0)
shot(T(B, 'Tapi') - .2, 31.0, 31.05, 3.3, .19, 3, dur=1.9)
# BAB 3
B = 'BAB 3'
shot(S3 - .2, 32.42, 30.6, 3.0, .19, -3, dur=2.0, mid=22)
shot(T(B, 'Tanpa') - .1, 28.0, 8.0, 150, .12, 0, dur=2.7)
shot(T(B, 'Tahun') - .2, 32.57, 30.03, 0.45, .2, 4, dur=2.7)
# BAB 4
B = 'BAB 4'
shot(S4 - .2, 33.3, 29.4, 6.0, .18, -3, dur=1.7, mid=18)
shot(T(B, 'Artinya') - .1, 35.0, 27.0, 50, .15, 2, dur=1.6)
shot(T(B, 'Di', 2) - .1, 33.95, 28.52, 1.4, .2, -4, dur=2.0)
shot(T(B, 'pantainya') - .2, 34.25, 27.85, 1.5, .2, 3, dur=1.0)
# BAB 5
B = 'BAB 5'
shot(S5 - .2, 32.88, 23.98, 0.40, .2, 3, dur=2.3, mid=16)
shot(T(B, 'Di', 2) - .1, 32.25, 22.95, 4.2, .18, -3, dur=1.6)
shot(T(B, 'Tapi') - .1, 31.626, 22.337, 0.2, .2, 4, dur=1.9)
# BAB 6
B = 'BAB 6'
shot(S6 - .2, 31.2, 22.4, 13, .17, -2, dur=2.0, mid=30)
shot(T(B, 'Mesir') - .1, 35.3, 22.45, 4.2, .19, 3, dur=1.2)
shot(T(B, 'Akibatnya') - .1, 33.6, 21.95, 4.0, .19, -3, dur=1.2)
shot(T(B, 'karena') - .1, 34.0, 22.2, 9, .18, 2, dur=1.0)
shot(T(B, 'Ini') - .1, 26, 21, 60, .15, -2, dur=1.8)
# BAB 7
B = 'BAB 7'
shot(S7 - .2, 27.5, 27.8, 11, .18, 3, dur=1.8, mid=30)
shot(T(B, 'ada') - .1, 27.3, 29.55, 3.5, .19, -3, dur=1.0)
shot(T(B, 'Ada') - .25, 27.95, 27.35, 1.8, .2, 3, dur=1.1)
shot(T(B, 'Oasis') - .2, 25.52, 29.2, 3.5, .19, -3, dur=1.2)
shot(T(B, 'Sementara') - .1, 31.72, 30.02, 1.2, .2, 4, dur=2.0)
shot(T(B, 'Negara') - .1, 30.6, 27.0, 17, .18, -2, dur=1.8)
shot(SP - .5, 28, 30, 55, .15, 3, dur=3.0)

DIAG = (T('BAB 7', 'sekitar'), T('BAB 7', 'Ada') - .35)  # hard-cut diagram window


def _state(s):
    return np.array([s[1], md(s[2]), math.log(s[3]), s[4], s[5]], np.float64)


def cam_at(t):
    """naik-geser-turun flights between shots, slow drift + orbit while holding"""
    i = 0
    while i + 1 < len(SHOTS) and SHOTS[i + 1][0] <= t: i += 1
    # state at the start of shot i flight = drifted end state of previous shot
    def held(j, tt):
        s = _state(SHOTS[j]).copy()
        arr = SHOTS[j][0] + (flight_dur(j) if j > 0 else 0)
        h = max(0, tt - arr)
        nxt = SHOTS[j + 1][0] if j + 1 < len(SHOTS) else 1e9
        hold_len = max(.01, nxt - arr)
        s[2] += math.log(.96) * h / 5
        if hold_len > 4:
            dirn = 1 if j % 2 == 0 else -1
            s[4] += dirn * 8 * smooth(0, 1, h / max(hold_len, 6))
        return s
    if i == 0: s = held(0, t); return Cam(s[0], s[1], math.exp(s[2]), s[3], s[4])
    a = held(i - 1, SHOTS[i][0]); b = _state(SHOTS[i])
    d = flight_dur(i); u = (t - SHOTS[i][0]) / d
    if u >= 1:
        s = held(i, t); return Cam(s[0], s[1], math.exp(s[2]), s[3], s[4])
    e = ease_io(u)
    pos = a[:2] + (b[:2] - a[:2]) * e
    lv = a[2] + (b[2] - a[2]) * e
    dist = math.hypot(*(b[:2] - a[:2]))
    mid = SHOTS[i][7]
    top = max(a[2], b[2])
    tgt = math.log(mid) if mid else math.log(max(math.exp(top), dist * 1.5))
    bump = max(0, tgt - top)
    lv += bump * math.sin(math.pi * ease_io(u) ** .9)
    k = a[3] + (b[3] - a[3]) * e; r = a[4] + (b[4] - a[4]) * e
    return Cam(pos[0], pos[1], math.exp(lv), k, r)


def flight_dur(i):
    s = SHOTS[i]
    if s[6]: return s[6]
    return 1.5


def flight_windows():
    return [(s[0], s[0] + flight_dur(i), s[8]) for i, s in enumerate(SHOTS) if i > 0]


for (a, b, snd) in flight_windows():
    if snd: E.sfx(a + (b - a) / 2 - 4 / 30 - .35, 'whoosh', 2)  # whoosh onset ~4 frames before peak speed (sound crest at +0.35s)

# ------------------------------------------------------------------ elements
EL = []
def add(e): EL.append(e); return e

LIME = (150, 255, 60); RED = (170, 25, 35); PURPLE = (150, 60, 215); ORANGE = (255, 150, 40); CYAN = (90, 230, 255); YEL = (255, 225, 60)

# --- INTRO
I = 'INTRO'
add(Region(EGY, .9, S1 + 1.5, LIME, snd=True))
add(Sprite(A.emoji('smile'), 30.0, 27.5, T(I, 'Negara'), T(I, 'tipis', end=True), off=(-330, -80), float_amp=6, kind='emoji', glow=True))
add(Counter(30.0, 26.5, T(I, 'satu'), T(I, 'tipis') - .1, 1_000_000, spin=1.2, dy=60, size=150))
add(Path(PL(NILE), T(I, 'pita'), S1 + 1, .8, color=LIME, width=5, snd=False))
add(Region(SINAI, T(I, 'Afrika'), T(I, 'pun', end=True), ORANGE, alpha=.85, snd=True))
add(Pin(33.6, 21.9, T(I, 'tanah'), T(I, 'Kamu')))
add(Region(BRT, T(I, 'tanah'), T(I, 'Kamu'), (200, 200, 200), alpha=.9, pulse=True, lw=2, snd=False))
add(Sprite(A.emoji('think'), 30.6, 27.2, T(I, 'Kamu'), T(I, 'petanya', end=True) - .1, off=(0, -60), float_amp=6, kind='emoji', glow=True))

# --- BAB 1
B = 'BAB 1'
add(Badge(1, S1, S2 - .01))
add(Region(FRA_MOVED, T(B, 'dua') - .15, T(B, 'sekitar') + 1.6, (0, 0, 0), alpha=.92, flag=flag_fill('FRA'), snd=True))
add(Region(EGY, T(B, 'Tapi'), T(B, 'Dari'), RED, alpha=.8, zoomfade=None))
add(Path(PL(NILE), T(B, 'Tapi'), T(B, 'Dari') + .3, .9, color=LIME, width=7, snd=False))
add(Counter(31.6, 27.6, T(B, 'sembilan'), T(B, 'lima', 2) - .2, 95, spin=1.2, suffix='%', start=10, dy=-30))
add(Counter(31.6, 27.6, T(B, 'lima', 2), T(B, 'Sisanya') + .2, 5, spin=.6, suffix='%', start=1, dy=-30, ticks=False))
add(Region(WEST, T(B, 'Sisanya'), T(B, 'Dari') + .2, (230, 170, 70), alpha=.75, pulse=True, zoomfade=None, snd=True))
add(Path(PL(NILE), T(B, 'garis'), T(B, 'Garis') + .2, .9, color=LIME, width=9, snd=False))
add(Path(NILE_FULL, T(B, 'Sungai') - .3, T(B, 'Satu') + .2, 2.3, color=CYAN, width=6, arrow=True))
add(IconRow(30.8, 28.1, [('palm', T(B, 'ladang')), ('desert', T(B, 'berdiri'))], T(B, 'Lebih') - .2, off=(0, -170)))
add(Counter(30.8, 27.2, T(B, 'seratus'), S2 - .3, 100_000_000, spin=1.4, color=YEL, size=150, riser=True))
add(IconRow(30.8, 27.2, [('people', T(B, 'bergantung'))], S2 - .3, off=(0, 120)))

# --- BAB 2
B = 'BAB 2'
add(Badge(2, S2, S3 - .01))
add(Region(EGY, S2 + .2, S3 + 1, LIME, zoomfade=(4, 9)))
add(Path(PL(DAMIETTA), T(B, 'Nil'), S3, 1.4, color=CYAN, width=5, snd=False, minvw=2.0))
add(Path(PL(ROSETTA), T(B, 'Nil') + .3, S3, 1.4, color=CYAN, width=5, snd=False, minvw=2.0))
add(Region(DELTA, T(B, 'Delta'), T(B, 'Di', 2) + .5, LIME, alpha=.6, zoomfade=(1.5, 3), snd=True, glow=(255, 255, 160)))
add(Pin(31.235, 30.044, T(B, 'Kairo'), T(B, 'Tapi')))
add(Counter(31.235, 30.044, T(B, 'dua') - .1, T(B, 'Tapi') - .15, 20_000_000, spin=.9, dy=-90, size=140))
add(Pin(31.134, 29.979, T(B, 'Piramida'), T(B, 'Tapi') + .4))
add(Sprite(A.place_card(A.card('pyramids', 1), -5), 31.134, 29.979, T(B, 'Giza'), T(B, 'naik') , off=(260, -170), from_pin=True))
add(IconRow(31.134, 29.979, [('pyramid', T(B, 'Piramida'))], T(B, 'Tapi') + .3, off=(-180, -60)))
add(Region(DELTA, T(B, 'rendah') - .3, S3, (60, 140, 230), alpha=.0, zoomfade=None, colorto=RED, tcolor=T(B, 'tanah', 2)))
add(Region(DELTA, T(B, 'tanah', 2), S3 + .3, RED, alpha=.55, zoomfade=None, snd=False, fin=1.0))
add(Arrows([(30.3, 31.75), (30.9, 31.85), (31.5, 31.8), (32.0, 31.7)], T(B, 'Laut'), S3, -90))
add(Path(PL([(29.95, 31.17), (30.35, 31.45), (30.85, 31.55), (31.35, 31.6), (31.85, 31.5), (32.3, 31.26)]), T(B, 'pantai'), S3 + .2, .9, color=(255, 70, 70), width=6, snd=False))
E.sfx(T(B, 'menggerogoti'), 'impact', 3)

# --- BAB 3
B = 'BAB 3'
add(Badge(3, S3, S4 - .01))
add(Region(EGY, S3 + .2, S4 + .5, LIME, zoomfade=(4, 9)))
add(Path(PL(CANAL), T(B, 'Terusan'), T(B, 'Tanpa') + 2.5, 1.2, color=CYAN, width=7))
add(Counter(32.42, 30.6, T(B, 'seratus'), T(B, 'Laut') - .1, 193, spin=1.2, start=20, dy=-30))
add(Pin(32.30, 31.26, T(B, 'Laut'), T(B, 'Tanpa') + .3))
add(Pin(32.56, 29.95, T(B, 'Laut', 2), T(B, 'Tanpa') + .3))
add(Path(PL(ROUTE_LONG), T(B, 'kapal') - .2, T(B, 'Tahun') + .3, 2.8, color=(255, 80, 80), width=5, arrow=True))
add(Path(PL(ROUTE_SUEZ), T(B, 'Sekitar'), T(B, 'Tahun') + .3, 1.6, color=CYAN, width=6, arrow=True, snd=False))
add(Counter(32.3, 31.0, T(B, 'dua'), T(B, 'Tahun') + .2, 12, spin=1.2, start=1, suffix='%', dy=-60, size=180))
add(Pin(32.578, 30.017, T(B, 'satu', 2) - .2, S4))
add(Sprite(A.place_card(A.card('ship', 2), 6), 32.578, 30.017, T(B, 'kapal', 2), S4 - .1, off=(300, -150), from_pin=True))
add(IconRow(32.578, 30.017, [('ship', T(B, 'raksasa'))], S4 - .1, off=(-200, -40)))
add(Counter(32.578, 30.017, T(B, 'enam'), S4 - .1, 6, spin=.7, start=1, dy=150, size=170, ticks=False))

# --- BAB 4
B = 'BAB 4'
add(Badge(4, S4, S5 - .01))
add(Region(MAIN, S4 + .2, S5 + .5, LIME, zoomfade=(3, 6)))
add(Region(SINAI, T(B, 'Semenanjung'), T(B, 'Di', 2) + 1.0, (120, 255, 200), alpha=.8, colorto=ORANGE, tcolor=T(B, 'Asia') - .1, zoomfade=(3, 6), snd=True, glow=(255, 220, 120)))
add(Path(PL(CANAL + GULF[1:]), T(B, 'Terusan'), T(B, 'Di', 2) + .5, 1.4, color=(255, 255, 255), width=5))
add(Arrows([(31.2, 29.0)], T(B, 'Afrika'), T(B, 'Asia') + 1.5, 180, color=LIME, size=40, snd=False))
add(Arrows([(34.6, 29.8)], T(B, 'Asia'), T(B, 'Asia', 2) + .8, 0, color=ORANGE, size=40))
add(Region(SINAI, T(B, 'Artinya'), T(B, 'Di', 2), ORANGE, alpha=.9, zoomfade=None, pulse=True, lw=2))
add(Region(MAIN, T(B, 'Artinya'), T(B, 'Di', 2), LIME, alpha=.9, zoomfade=None, lw=2, snd=True))
add(Pin(33.955, 28.51, T(B, 'Gunung'), S5))
add(IconRow(33.955, 28.51, [('mountain', T(B, 'Katarina'))], T(B, 'pantainya'), off=(0, -150)))
add(Pin(34.25, 27.73, T(B, 'terumbu') - .3, S5))
add(IconRow(34.25, 27.73, [('fish', T(B, 'terumbu'))], S5 - .1, off=(-180, -80)))
add(Sprite(A.place_card(A.card('reef', 3), -6), 34.25, 27.73, T(B, 'karang'), S5 - .05, off=(240, -170), from_pin=True))

# --- BAB 5
B = 'BAB 5'
add(Badge(5, S5, S6 - .01))
add(Region(EGY, S5 + .2, S6 + .5, LIME, zoomfade=(4, 9)))
add(Pin(32.878, 23.97, T(B, 'Bendungan'), T(B, 'Di', 2) + .3))
add(IconRow(32.878, 23.97, [('dam', T(B, 'Aswan')), ('wave', T(B, 'banjir'))], T(B, 'Di', 2), off=(0, -170)))
add(Counter(32.878, 23.97, T(B, 'seribu'), T(B, 'mengakhiri') + .4, 1970, spin=1.3, start=1900, fmt='{:d}', dy=130, size=160))
add(Region(LAKE_NASSER, T(B, 'Danau') - .3, T(B, 'Tapi') + .5, CYAN, alpha=.85, zoomfade=None, wipe=(T(B, 'Danau') - .3, T(B, 'Danau') + 1.6), snd=True, glow=(200, 255, 255)))
E.sfx(T(B, 'terbesar'), 'impact', 3)
add(Pin(31.6255, 22.3369, T(B, 'Abu'), S6))
add(Sprite(A.place_card(A.card('temple', 4), -4), 31.6255, 22.3369, T(B, 'Simbel'), T(B, 'disusun') + .3, off=(-330, -160), from_pin=True))
add(Sprite(A.place_card(A.card('temple_blocks', 5), 5), 31.6255, 22.3369, T(B, 'dipotong'), S6 - .1, off=(330, -150), from_pin=True))
add(Arrows([(31.6255, 22.3369)], T(B, 'disusun'), T(B, 'puzzle') + .2, 90, color=(255, 255, 255), size=46))
add(IconRow(31.6255, 22.3369, [('puzzle', T(B, 'puzzle'))], S6 - .1, off=(0, 170)))

# --- BAB 6
B = 'BAB 6'
add(Badge(6, S6, S7 - .01))
add(Region(EGY, S6 + .2, S7 + .5, LIME, zoomfade=(2, 4)))
add(Region(SDN, T(B, 'Sudan'), S7 + .5, PURPLE, alpha=.8, zoomfade=(2, 4), snd=True, glow=(230, 160, 255)))
add(Path(PL(L1899), T(B, 'dari'), T(B, 'Akibatnya') + .2, 1.6, color=(255, 255, 255), width=6))
add(Counter(27.5, 22.0, T(B, 'seribu'), T(B, 'dan') - .05, 1899, spin=1.2, start=1800, fmt='{:d}', dy=-70, size=140, ticks=True))
add(Path(PL(L1902), T(B, 'dan'), T(B, 'Akibatnya') + .2, 1.2, color=YEL, width=6, dash=False, snd=False))
add(Counter(27.5, 22.0, T(B, 'seribu', 2), T(B, 'Mesir') + .3, 1902, spin=.9, start=1899, fmt='{:d}', dy=80, size=140, color=YEL, ticks=False))
add(Region(HAL, T(B, 'Segitiga'), S7, (0, 0, 0), alpha=.9, zoomfade=None, flag=flag_fill('EGY', split='SDN'), snd=True))
add(Region(BRT, T(B, 'Bir'), S7 + .5, (205, 205, 205), alpha=.85, zoomfade=None, pulse=True, snd=False))
add(Pin(33.6, 21.85, T(B, 'Bir'), S7))
add(Arc((31.0, 24.5), (35.4, 22.7), T(B, 'mengklaimnya'), T(B, 'Ini') + .5, .8, h=-.3, color=(80, 230, 110), width=6))
add(Arc((31.5, 19.0), (35.6, 22.2), T(B, 'berarti'), T(B, 'Ini') + .5, .8, h=.3, color=(255, 110, 190), width=6))

# --- BAB 7
B = 'BAB 7'
add(Badge(7, S7, END0))
add(Region(EGY, S7 + .2, END0, LIME, zoomfade=(3, 7)))
add(Region(WEST, T(B, 'Gurun'), T(B, 'Depresi') + .4, (240, 180, 70), alpha=.7, zoomfade=None, snd=True, glow=(255, 230, 150)))
add(Pin(27.3, 29.55, T(B, 'Depresi'), DIAG[1] + 1))
add(Pin(27.95, 27.35, T(B, 'Putih'), T(B, 'Oasis')))
add(IconRow(27.95, 27.35, [('rock', T(B, 'jamur'))], T(B, 'Oasis') - .1, off=(-190, -60)))
add(Sprite(A.place_card(A.card('whitedesert', 6), 4), 27.95, 27.35, T(B, 'batu'), T(B, 'Oasis') - .05, off=(270, -160), from_pin=True))
add(Pin(25.52, 29.2, T(B, 'Siwa'), T(B, 'Sementara') + .3))
add(IconRow(25.52, 29.2, [('palm', T(B, 'hijau'))], T(B, 'Sementara'), off=(-190, -60)))
add(Sprite(A.place_card(A.card('oasis', 7), -6), 25.52, 29.2, T(B, 'Siwa') + .3, T(B, 'Sementara') + .1, off=(270, -160), from_pin=True))
add(Pin(31.235, 30.044, T(B, 'kota') - .3, T(B, 'Negara') + .5))
add(Pin(31.72, 30.02, T(B, 'ibu'), T(B, 'Negara') + .8))
add(IconRow(31.72, 30.02, [('building', T(B, 'baru'))], T(B, 'Negara') + .3, off=(0, 150)))
add(Sprite(A.place_card(A.card('capital', 8), 5), 31.72, 30.02, T(B, 'dari'), T(B, 'Negara') + .2, off=(300, -170), from_pin=True))
add(Path(NILE_FULL, T(B, 'sungai') - .3, END0, 1.4, color=CYAN, width=6, snd=False))
E.sfx(T(B, 'sendiri', end=True) - .05, 'ding', 3)

# --- PENUTUP
add(Subscribe(SP, T('PENUTUP', 'komentar', end=True) + .4, T('PENUTUP', 'kasih')))

# ------------------------------------------------------------------ diagram (Qattara cross-section) & end screen
DIAG_COUNTER = Counter(0, 0, DIAG[0] + .9, DIAG[1], -133, spin=1.2, start=-13, screen=(1180, 760), size=170, color=(255, 225, 60), riser=True)
_diag_cache = {}


def diagram(t):
    t0, t1 = DIAG
    u = t - t0
    if 'bg' not in _diag_cache:
        bg = np.zeros((H, W, 3), np.float32); bg[:] = (10, 28, 58)
        for x in range(0, W, 60): bg[:, x:x + 1] = (30, 60, 100)
        for y in range(0, H, 60): bg[y:y + 1, :] = (30, 60, 100)
        _diag_cache['bg'] = bg
        xs = np.arange(W)
        prof = np.interp(xs, [0, 330, 380, 620, 800, 960, 1120, 1300, 1500, 1920], [700, 700, 560, 545, 650, 800, 690, 520, 470, 430])
        _diag_cache['prof'] = prof
    fr = _diag_cache['bg'].copy()
    prof = _diag_cache['prof']; SEA = 620
    wipe = min(1, u / .6)
    L = blank()
    sea = np.array([[0, SEA], [380, SEA], [380, H], [0, H]], np.float64)
    fill_rings(L, [sea], (30, 120, 200))
    xs = np.arange(0, W, 8)
    poly = np.vstack([[[x, prof[min(x, W - 1)]] for x in xs], [[W, H], [0, H]]]).astype(np.float64)
    fill_rings(L, [poly], (110, 70, 40))
    L[:, int(W * wipe):] = 0
    comp_premul(fr, L, 1, (0, 0, W, H))
    if u > .5:
        a = min(1, (u - .5) / .3)
        D = blank()
        xx = np.arange(0, W, 40)
        for x in xx: line_px(D, np.array([[x, SEA], [x + 22, SEA]], float), (120, 220, 255), 3)
        comp_premul(fr, D, a, (0, 0, W, H))
    if u > .8:
        g = min(1, (u - .8) / .7)
        D = blank(); bx = 960; by = prof[bx]
        line_px(D, np.array([[bx - 140, SEA], [bx + 140, SEA]], float), YEL, 6)
        line_px(D, np.array([[bx, SEA], [bx, SEA + (by - SEA) * g]], float), YEL, 6)
        line_px(D, np.array([[bx - 40, SEA + (by - SEA) * g], [bx + 40, SEA + (by - SEA) * g]], float), YEL, 6)
        comp_premul(fr, D, 1, (0, 0, W, H))
    return fr


_sun = {}


def endscreen(t):
    if 'th' not in _sun:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        _sun['th'] = np.arctan2(yy - H / 2, xx - W / 2); _sun['r'] = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / (W / 2)
    th = _sun['th'] + (t - END0) * .18
    st = (np.floor(th / (2 * np.pi / 24)) % 2)[..., None]
    c1 = np.array([40, 120, 235], np.float32); c2 = np.array([70, 160, 250], np.float32)
    fr = c1 * (1 - st) + c2 * st
    fr *= (1.15 - .35 * np.clip(_sun['r'], 0, 1.4)[..., None])
    return np.clip(fr, 0, 255)
