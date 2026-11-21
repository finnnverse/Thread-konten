# assets.py — lift rig, city, site props, people for Bongkarinsemua (Blender, Z up, camera looks toward +Y)
import math, random
from lib import *

FH = 3.4                     # floor height
FLOORS = 8
H = FH * FLOORS              # shaft height (27.2)
CAR = dict(x=-0.45, w=1.7, d=1.6, h=2.35)
CW = dict(x=1.15, w=0.5, d=0.9, h=2.3)
SHEAVE = dict(x=0.35, z=H + 1.15, r=0.8)
GOV = dict(x=-1.6, y=-0.45, z=H + 0.75, r=0.32)
FONT = '/home/claude/explainer3d/vendor/fonts/Poppins-ExtraBold.ttf'

YEL, BLUE, ORANGE = 0xe9b21c, 0x2459b8, 0xe2681e

# ---------------------------------------------------------------- generic props
def helix(r, h, turns, wire, mat, loc=(0, 0, 0), parent=None, phase=0.0, n=None):
    n = n or int(turns * 24)
    pts = [(r * math.cos(phase + 2 * math.pi * turns * i / n), r * math.sin(phase + 2 * math.pi * turns * i / n), h * i / n) for i in range(n + 1)]
    o = tube(pts, wire, mat, parent); o.location = loc; o.data.splines[0].type = 'POLY'
    return o

def person(loc=(0, 0, 0), rot=0, shirt=0x9cc3e6, pants=0x8a7458, helmet=True, scale=1.0, parent=None, arm_up=0.0):
    g = empty(loc, parent, (0, 0, rot)); g.scale = (scale,) * 3
    skin = m_plain(0xc89068, 0.55); cloth = m_plain(shirt, 0.85); pc = m_plain(pants, 0.9); shoe = m_plain(0x2a2a2c, 0.6)
    for sx in (-0.11, 0.11):
        cyl(0.085, 0.82, pc, (sx, 0, 0.49), parent=g, seg=16, r2=0.075)
        box((0.13, 0.26, 0.09), shoe, (sx, -0.04, 0.05), parent=g, bevel=0.03)
    box((0.42, 0.24, 0.62), cloth, (0, 0, 1.2), parent=g, bevel=0.08)
    box((0.40, 0.22, 0.12), pc, (0, 0, 0.92), parent=g, bevel=0.04)
    arms = []
    for i, sx in enumerate((-0.27, 0.27)):
        a = empty((sx, 0, 1.46), g, (0, 0, 0))
        cyl(0.065, 0.32, cloth, (0, 0, -0.14), parent=a, seg=14)
        cyl(0.05, 0.36, skin, (0, 0, -0.45), parent=a, seg=14)
        sphere(0.055, skin, (0, 0, -0.64), parent=a, seg=12)
        arms.append(a)
    if arm_up: arms[1].rotation_euler = (0, R(-150 * arm_up), 0)
    cyl(0.06, 0.12, skin, (0, 0, 1.55), parent=g, seg=12)
    sphere(0.14, skin, (0, 0, 1.72), parent=g, scale=(0.95, 1.0, 1.12))
    sphere(0.145, m_plain(0x2a1d15, 0.8), (0, 0.02, 1.76), parent=g, scale=(1.0, 1.0, 0.95))
    if helmet:
        hm = m_plain(0xf2f2ee, 0.3, coat=0.5)
        sphere(0.165, hm, (0, 0, 1.79), parent=g, scale=(1.0, 1.08, 0.82))
        cyl(0.2, 0.02, hm, (0, -0.02, 1.76), parent=g, seg=24)
    return g, arms

def car_vehicle(loc=(0, 0, 0), rot=0, color=0xf0f0ee, parent=None):
    g = empty(loc, parent, (0, 0, rot))
    paint = m_plain(color, 0.25, coat=1.0); glass = m_plain(0x1a2430, 0.08, 0.2); tire = m_plain(0x1b1b1d, 0.8)
    box((4.2, 1.75, 0.7), paint, (0, 0, 0.62), parent=g, bevel=0.18)
    box((2.3, 1.6, 0.6), glass, (-0.2, 0, 1.18), parent=g, bevel=0.2)
    for x in (-1.35, 1.35):
        for y in (-0.82, 0.82): cyl(0.33, 0.24, tire, (x, y, 0.33), (90, 0, 0), parent=g, seg=20)
    return g

def ground_dirt(size=400):
    p = plane((size, size), m_dirt(), (0, 0, 0))
    return p

def road(y=-30, length=400, width=9):
    plane((length, width), m_asphalt(), (0, y, 0.01))
    for i in range(-40, 40):
        plane((2.2, 0.15), m_plain(0xe8e6de, 0.6), (i * 5, y, 0.02))
    for s in (-1, 1): box((length, 0.3, 0.18), m_concrete(0xb0aca4), (0, y + s * (width / 2 + 0.15), 0.09))

def ruko(x, y, w=5.0, floors=3, wall=0xd8c8aa, rot=0, parent=None):
    """Indonesian shophouse: plaster facade, windows, orange tile roof, shutter at ground"""
    g = empty((x, y, 0), parent, (0, 0, rot)); fh = 3.3; h = floors * fh
    box((w, 8, h), m_facade(wall, 0x3d4d5c, cols=3, rows=floors, w=w, h=h, frame=0.24), (0, 4, h / 2), parent=g, bevel=0.03)
    box((w * 0.86, 0.15, 2.6), m_corrugated(0x8a9096), (0, -0.05, 1.3), parent=g)
    box((w + 0.1, 0.9, 0.18), m_concrete(0xe6e0d4), (0, -0.4, fh), parent=g)
    roof = cyl(w * 0.8, 1.8, m_plain(0xc8622e, 0.7), (0, 4, h + 0.9), (0, 0, 45), parent=g, seg=4, r2=0.05)
    roof.scale = (1.0, 1.55, 1.0)
    sign = random.choice([0x2f8f4e, 0xc22a2a, 0x2a5ab8, 0xe0b020])
    box((w * 0.9, 0.1, 0.55), m_plain(sign, 0.5), (0, -0.1, fh - 0.45), parent=g)
    return g

def tower(x, y, w=14, d=14, floors=20, wall=0xc8ccd2, glass=0x6d8aa3, lit=0.0, parent=None, cols=None):
    h = floors * 3.6
    g = empty((x, y, 0), parent)
    box((w, d, h), m_facade(wall, glass, cols=cols or int(w / 2.2), rows=floors, w=w, h=h, frame=0.16, lit=lit), (0, 0, h / 2), parent=g)
    box((w + 0.5, d + 0.5, 0.8), m_concrete(0x9a958c), (0, 0, h + 0.4), parent=g)
    return g

def city_backdrop(y0=40, spread=120, seed=4, towers=True, lit=0.0):
    random.seed(seed)
    x = -spread / 2
    while x < spread / 2:
        w = random.uniform(4.5, 6.5); ruko(x + w / 2, y0, w, random.choice([2, 3, 3, 4]), random.choice([0xd8c8aa, 0xcfd2cc, 0xe2d6bc, 0xc9b79a, 0xd6cfc4]))
        x += w + 0.05
    if towers:
        for i in range(9):
            tx = -spread / 2 + 8 + i * spread / 9 + random.uniform(-4, 4)
            tower(tx, y0 + 28 + random.uniform(0, 30), random.uniform(12, 20), 14, random.randint(12, 34),
                  random.choice([0xc8ccd2, 0xb8c0c8, 0xd8d4cc, 0x8e9aa6]), random.choice([0x5d7c96, 0x6d8aa3, 0x4a6680, 0x7896ad]), lit)
    for i in range(10):
        car_vehicle((random.uniform(-spread / 2, spread / 2), y0 - 7.5 + random.choice([-1.2, 1.2]), 0), random.choice([0, 180]),
                    random.choice([0xf0f0ee, 0xf0f0ee, 0x2a3a6a, 0xb8bcc0, 0x202022]))
    road(y0 - 7.5, spread + 60, 8)

def site_fence(y=22, length=120, x0=0):
    box((length, 0.08, 2.4), m_corrugated(0xa8aeb4, stripe=(1.5, 1.95, 0x2f9a52)), (x0, y, 1.2))
    for i in range(int(length / 3)):
        cyl(0.05, 2.6, m_steel(0x8a8e94), (x0 - length / 2 + i * 3, y - 0.08, 1.3), seg=8)

def site_props(seed=2):
    random.seed(seed)
    # concrete pipes / piles stack, barrels, cones, container
    for i in range(3):
        cyl(0.35, 8, m_concrete(0xc8c0b0), (-10 + i * 0.75, 12, 0.35), (0, 90, 0), seg=24)
    cyl(0.35, 8, m_concrete(0xc8c0b0), (-9.62, 12, 0.98), (0, 90, 0), seg=24)
    for i in range(4): cyl(0.3, 0.9, m_paint(0x2a5ab8, 0.3), (8 + i * 0.7, 14, 0.45), seg=20)
    box((6, 2.4, 2.6), m_paint(0xa03a28, 0.4), (12, 16, 1.3), bevel=0.03)
    for p in [(-4, 6), (5, 5), (-6, 9)]:
        cyl(0.18, 0.7, m_plain(ORANGE, 0.5), (p[0], p[1], 0.35), r2=0.02, seg=16)
        box((0.4, 0.4, 0.04), m_plain(0x222222, 0.7), (p[0], p[1], 0.02))

# ---------------------------------------------------------------- lift rig (cut-away building)
class Rig:
    pass

def lift_rig(car_z=0.0, open_doors=False, people=0, machine=True, slabs=True, cables=5, governor=True, pit_buffers=True, light_on=True):
    r = Rig()
    conc = m_concrete(0xa9a398); cut = m_concrete(0xc4beb2, scale=2, stains=False); dark = m_concrete(0x8f8a80)
    W, Dp = 3.9, 2.9    # shaft inner width / depth (y from -1.45 .. +1.45)
    # back + side walls (front open toward camera at -Y)
    box((W + 0.5, 0.25, H + 3), conc, (0.2, Dp / 2 + 0.125, (H + 3) / 2 - 1.5))
    for sx in (-W / 2 - 0.125 + 0.2, W / 2 + 0.125 + 0.2):
        box((0.25, Dp + 0.25, H + 3), conc, (sx, 0.0, (H + 3) / 2 - 1.5))
    # pit
    box((W + 0.5, Dp + 0.5, 0.6), dark, (0.2, 0, -1.8))
    # floor slabs + rooms either side (cut faces toward camera)
    if slabs:
        tile = m_plain(0xd8d2c6, 0.35)
        for f in range(FLOORS + 1):
            z = f * FH
            for sx, w in ((-W / 2 - 0.25 + 0.2 - 3.5, 7.0), (W / 2 + 0.25 + 0.2 + 3.5, 7.0)):
                box((w, 7, 0.32), cut, (sx, 2.0, z - 0.16))
                if f < FLOORS:
                    box((w, 7, 0.02), tile, (sx, 2.0, z + 0.01))
                    box((w, 0.2, FH - 0.32), m_plain(0xe8e2d6, 0.9), (sx, 5.4, z + FH / 2))   # back wall of room
            # landing door frame on the back wall of shaft at each floor
            if f < FLOORS:
                box((1.3, 0.06, 2.2), m_steel(0xb0b4b8), (CAR['x'], Dp / 2 - 0.02, z + 1.1))
    # guide rails (T rails, oiled steel)
    rail = m_steel(0x6f747a, 0.25, brushed=False)
    for x in (CAR['x'] - CAR['w'] / 2 - 0.12, CAR['x'] + CAR['w'] / 2 + 0.12):
        box((0.06, 0.14, H + 1.6), rail, (x, 0.0, (H + 1.6) / 2 - 1.5))
        box((0.16, 0.03, H + 1.6), rail, (x, 0.07, (H + 1.6) / 2 - 1.5))
    for x in (CW['x'] - 0.33, CW['x'] + 0.33):
        box((0.05, 0.1, H + 1.6), rail, (x, 0.35, (H + 1.6) / 2 - 1.5))
    # machine room floor + machine
    r.sheave = r.motor = None
    if machine:
        box((W + 0.5, Dp + 0.5, 0.35), conc, (0.2, 0, H + 0.175))
        mz = H + 0.35
        base = m_paint(0x3a3e44, 0.2)
        box((2.6, 1.4, 0.3), base, (SHEAVE['x'] - 0.4, 0.2, mz + 0.15), bevel=0.02)
        r.sheave = empty((SHEAVE['x'], 0.0, SHEAVE['z']), rot=(90, 0, 0))
        st = m_steel(0x9aa0a6, 0.3)
        cyl(SHEAVE['r'], 0.6, st, (0, 0, 0), parent=r.sheave, seg=48)
        for k in range(6): torus(SHEAVE['r'] - 0.02, 0.025, m_steel(0x5e6268, 0.4), (0, 0, -0.25 + k * 0.1), parent=r.sheave)
        cyl(0.3, 0.7, m_paint(0x3a3e44, 0.2), (0, 0, 0), parent=r.sheave, seg=24)
        cyl(0.12, 1.4, st, (0, 0, 0.3), parent=r.sheave, seg=20)
        r.motor = empty((SHEAVE['x'], 0.95, SHEAVE['z']), rot=(90, 0, 0))
        cyl(0.62, 1.1, m_paint(BLUE, 0.25, 0.35), (0, 0, -0.1), parent=r.motor, seg=40, bevel=0.03)
        cyl(0.66, 0.12, m_paint(0x2a2e34, 0.2), (0, 0, 0.45), parent=r.motor, seg=40)
        for k in range(10): box((0.04, 1.24, 0.9), m_paint(BLUE, 0.25), (0, 0, -0.1), (0, 0, k * 18), parent=r.motor)
        # brake
        box((0.5, 0.4, 0.7), m_paint(0xb8302a, 0.3), (SHEAVE['x'] - 1.0, 0.0, mz + 0.65), bevel=0.03)
        # control cabinet
        box((0.9, 0.5, 1.8), m_paint(0xb9bcc0, 0.15), (-1.2, 1.1, mz + 0.9), bevel=0.02)
        box((0.25, 0.02, 0.12), m_emit(0x33ff66, 4), (-1.2, 0.84, mz + 1.5))
        # deflector + skylight
        area_light((0.2, -1.0, mz + 3.2), (0, 0, 0), 3, 250)
    # car
    r.car = empty((CAR['x'], 0.0, car_z))
    cw_, cd, ch = CAR['w'], CAR['d'], CAR['h']
    ss = m_steel(0xc8ccd0, 0.28); ss2 = m_steel(0xa8acb0, 0.4)
    box((cw_, cd, 0.14), m_plain(0x3a3a3c, 0.6), (0, 0, 0.07), parent=r.car)
    box((cw_ - 0.04, cd - 0.04, 0.02), m_plain(0x7a6a5a, 0.5), (0, 0, 0.15), parent=r.car)        # floor finish
    box((cw_, 0.05, ch), ss, (0, cd / 2 - 0.025, ch / 2 + 0.14), parent=r.car)
    for sx in (-1, 1):
        box((0.05, cd, ch), ss, (sx * (cw_ / 2 - 0.025), 0, ch / 2 + 0.14), parent=r.car)
        cyl(0.02, cd * 0.8, ss2, (sx * (cw_ / 2 - 0.08), 0, 1.05), (90, 0, 0), parent=r.car, seg=10)  # handrail
    box((cw_, cd, 0.08), ss2, (0, 0, ch + 0.18), parent=r.car)
    box((cw_ * 0.6, cd * 0.55, 0.02), m_emit(0xfff1d6, 6 if light_on else 0.2), (0, 0, ch + 0.13), parent=r.car)
    if light_on: point_light((0, 0, ch - 0.1), 60, (1, 0.93, 0.8), 0.4, parent=r.car)
    r.doors = []
    for sx in (-1, 1):
        dpan = box((cw_ / 2 - 0.02, 0.04, ch - 0.05), m_steel(0xd0d4d8, 0.25), (sx * cw_ / 4, -cd / 2 - 0.02, ch / 2 + 0.14), parent=r.car)
        dpan.hide_render = open_doors; r.doors.append(dpan)
    # sling / frame (painted)
    fr = m_paint(0x3c4046, 0.35, 0.4)
    for sx in (-1, 1):
        box((0.1, 0.16, ch + 0.7), fr, (sx * (cw_ / 2 + 0.06), 0, (ch + 0.7) / 2 - 0.1), parent=r.car)
    box((cw_ + 0.3, 0.2, 0.18), fr, (0, 0, ch + 0.55), parent=r.car)                 # crosshead
    box((cw_ + 0.3, 0.2, 0.16), fr, (0, 0, -0.1), parent=r.car)                      # plank
    box((0.5, 0.3, 0.25), m_paint(0x55595e, 0.3), (0, 0, ch + 0.76), parent=r.car)   # hitch
    r.gear = []
    for sx in (-1, 1):
        g = box((0.16, 0.24, 0.32), m_paint(ORANGE, 0.25), (sx * (cw_ / 2 + 0.12), 0.0, -0.05), parent=r.car, bevel=0.02)
        r.gear.append(g)
    for i in range(people):
        col = [0x2f6fd6, 0xd9262c, 0x2fa45a, 0x8a4fd6, 0xe8a23a, 0x24a3b5][i % 6]
        person((-0.45 + (i % 3) * 0.45, 0.35 - (i // 3) * 0.45, 0.15), 180 + random.uniform(-15, 15), shirt=col, helmet=False, scale=0.92, parent=r.car)
    # counterweight
    r.cw = empty((CW['x'], 0.35, 0))
    cwm = m_paint(0x3a3c40, 0.5, 0.5); cwy = m_paint(YEL, 0.5)
    for i in range(9):
        box((CW['w'] - 0.06, CW['d'] - 0.2, CW['h'] / 9 - 0.02), cwm if i % 3 else cwy, (0, 0, (i + 0.5) * CW['h'] / 9), parent=r.cw, bevel=0.01)
    for sx in (-1, 1): box((0.06, 0.12, CW['h'] + 0.3), fr, (sx * CW['w'] / 2, 0, CW['h'] / 2 + 0.05), parent=r.cw)
    box((CW['w'] + 0.1, 0.2, 0.14), fr, (0, 0, CW['h'] + 0.22), parent=r.cw)
    # ropes (cylinders scaled per frame)
    rope = m_steel(0x4a4e54, 0.35, brushed=False)
    r.ropes_car, r.ropes_cw = [], []
    ys = [(-0.2 + 0.4 * i / max(1, cables - 1)) for i in range(cables)]
    for y in ys:
        a = cyl(0.016, 1.0, rope, (0, y, 0), seg=8); r.ropes_car.append(a)
        b = cyl(0.016, 1.0, rope, (0, y + 0.0, 0), seg=8); r.ropes_cw.append(b)
    # governor
    r.gov = None
    if governor and machine:
        r.gov = empty((GOV['x'], GOV['y'], GOV['z']), rot=(0, 90, 0))
        gm = m_paint(0xc9a227, 0.3)
        cyl(GOV['r'], 0.08, m_steel(0x9aa0a6), (0, 0, 0), parent=r.gov, seg=40)
        torus(GOV['r'], 0.025, m_steel(0x5e6268), (0, 0, 0), parent=r.gov)
        for k in range(2):
            fw = box((0.18, 0.06, 0.06), gm, (0, 0, 0.06), (0, 0, k * 180), parent=r.gov); fw.location = (math.cos(k * math.pi) * 0.12, math.sin(k * math.pi) * 0.12, 0.07)
        for k in range(4): box((GOV['r'] * 1.8, 0.03, 0.03), m_steel(0x7a7e84), (0, 0, 0.0), (0, 0, k * 45), parent=r.gov)
        box((0.2, 0.4, 0.35), gm, (GOV['x'] - 0.2, GOV['y'], GOV['z'] - 0.5), bevel=0.02)
        for sy in (-1, 1): cyl(0.012, H + 1.95, rope, (GOV['x'], GOV['y'] + sy * GOV['r'], (GOV['z'] - 1.2) / 2), seg=6)
        # tension sheave in pit
        cyl(0.25, 0.06, m_steel(0x9aa0a6), (GOV['x'], GOV['y'], -1.2), (0, 90, 0), seg=30)
    # pit buffers (springs)
    if pit_buffers:
        sp = m_paint(0xd8a01c, 0.3, 0.35)
        for sx in (-0.45, 0.45):
            x = CAR['x'] + sx
            box((0.45, 0.45, 0.06), m_paint(0x3a3e44, 0.2), (x, 0, -1.47))
            for ph in (0.0,):
                helix(0.16, 1.15, 7, 0.028, sp, (x, 0, -1.45), phase=ph)
            box((0.38, 0.38, 0.05), m_paint(0x3a3e44, 0.2), (x, 0, -0.28))
        sp2 = m_paint(0xd8a01c, 0.3)
        helix(0.12, 0.9, 6, 0.022, sp2, (CW['x'], 0.35, -1.45))
    # work lights inside shaft
    for z in (FH * 1.5, FH * 4.5, FH * 7):
        point_light((0.2, -1.2, z), 140, (1, 0.95, 0.85), 0.6)

    def set_car(z, cables_on=True):
        r.car.location.z = z
        cwz = H - 2.9 - z
        r.cw.location.z = cwz
        top = SHEAVE['z']
        a = z + CAR['h'] + 0.9
        b = cwz + CW['h'] + 0.3
        for c in r.ropes_car:
            c.location.x = SHEAVE['x'] - SHEAVE['r']; c.location.z = (a + top) / 2; c.scale.z = max(0.01, top - a); c.hide_render = not cables_on
        for c in r.ropes_cw:
            c.location.x = SHEAVE['x'] + SHEAVE['r']; c.location.y = c.location.y; c.location.z = (b + top) / 2; c.scale.z = max(0.01, top - b); c.hide_render = not cables_on
        if r.sheave: r.sheave.rotation_euler = (R(90), 0, -z / SHEAVE['r'])
        if r.motor: r.motor.rotation_euler = (R(90), 0, -z / SHEAVE['r'])
        if r.gov: r.gov.rotation_euler = (z / GOV['r'], R(90), 0)
    r.set_car = set_car
    set_car(car_z)
    return r

def exterior_building(x=0, y=6, floors=9, w=12, d=10, glass_lift=True):
    """office block with a glass panoramic lift on its front face (front at y - d/2)"""
    h = floors * 3.6
    box((w, d, h), m_facade(0xd2cbbd, 0x4f6170, cols=8, rows=floors, w=w, h=h, frame=0.18), (x, y + d / 2, h / 2), bevel=0.05)
    box((w + 0.4, d + 0.4, 0.6), m_concrete(0x9a958c), (x, y + d / 2, h + 0.3))
    car = None
    if glass_lift:
        box((2.6, 2.4, h + 2.2), m_glass(0xcfe3ee, 0.02, alpha_like=True), (x, y - 1.25, (h + 2.2) / 2))
        for sx in (-1.3, 1.3):
            for sy in (-2.4, -0.1): box((0.14, 0.14, h + 2.2), m_steel(0x8d939a, 0.3), (x + sx, y + sy, (h + 2.2) / 2))
        car = empty((x, y - 1.25, 0))
        box((1.9, 1.8, 2.4), m_steel(0xc8ccd0, 0.25), (0, 0, 1.2), parent=car, bevel=0.05)
        box((1.92, 1.82, 0.12), m_paint(BLUE, 0.1), (0, 0, 1.35), parent=car)
        box((1.3, 0.02, 1.3), m_emit(0xfff1d6, 3), (0, -0.91, 1.5), parent=car)
    return car, h

def billboard(text, loc=(0, 0, 0), w=6, h=2.2, rot=0):
    g = empty(loc, rot=(0, 0, rot))
    box((w, 0.12, h), m_paint(0xf2b822, 0.15, 0.3), (0, 0, 3.2), parent=g, bevel=0.03)
    box((w - 0.25, 0.02, h - 0.25), m_plain(0x1d1f23, 0.6), (0, -0.07, 3.2), parent=g)
    lines = text.split('\n')
    for i, l in enumerate(lines):
        text_obj(l, h * 0.42, m_plain(0xf2b822, 0.4), (0, -0.1, 3.2 + (len(lines) / 2 - i - 0.5) * h * 0.34), parent=g, extrude=0.01, font_path=FONT)
    for sx in (-w / 2 + 0.4, w / 2 - 0.4): box((0.14, 0.14, 2.3), m_steel(0x6e737a), (sx, 0.05, 1.15), parent=g)
    return g
