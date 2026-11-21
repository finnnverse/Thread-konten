# shots.py — one builder per [shot] tag. Each returns dict(update=fn(t,u), cam=[k0,k1] | fn(t,u)->k)
# k = dict(pos=(x,y,z), look=(x,y,z), fov=deg). Blender coords: X right, Y away from camera, Z up.
from assets import *

def _ext_site(time='day', clouds=0.6, backdrop=True):
    world(sun_elev=50, sun_rot=40, time=time, clouds=clouds)
    ground_dirt()
    if backdrop:
        city_backdrop(y0=48, spread=140, lit=0.35 if time != 'day' else 0.0)
        site_fence(y=34, length=140)
        site_props()

def _shaft_world(time='day'):
    world(sun_elev=55, sun_rot=30, time=time, clouds=0.5)
    plane((400, 400), m_dirt(), (0, 0, -2.1))
    box((60, 2, 40), m_concrete(0x8f8a82), (0, 8, 20))
    bpy.context.scene.view_settings.exposure = -0.6

# ------------------------------------------------------------------ shots
def shaft_down(ctx):
    _shaft_world(); r = lift_rig(car_z=FH * 2, machine=False, governor=False, slabs=True)
    def up(t, u): r.set_car(FH * 2 + t * 1.3)
    return dict(update=up, cam=[dict(pos=(-0.2, -0.6, H + 2.2), look=(CAR['x'], 0.1, FH * 2), fov=52),
                                dict(pos=(-0.25, -0.55, H + 0.9), look=(CAR['x'], 0.1, FH * 2.2), fov=48)], dof=None)

def shaft_fall(ctx):
    _shaft_world(); r = lift_rig(car_z=FH * 6, people=2)
    def up(t, u): r.set_car(FH * 6 + math.sin(t * 1.4) * 0.02)
    def cam(t, u):
        e = ease(u)
        return dict(pos=(4.8, -10.5, lerp(FH * 6 + 2.8, 1.0, e)), look=(0.2, 0, lerp(FH * 6 + 1.0, -0.8, e)), fov=50)
    return dict(update=up, cam=cam)

def _tower_scene(time='day', brand=False):
    _ext_site(time)
    car, h = exterior_building(0, 6, floors=9)
    tower(-22, 14, 16, 14, 16); tower(22, 16, 14, 14, 20)
    billboard('BONGKARINSEMUA', (0, -11, 0), w=7.5, h=1.6) if brand else None
    if brand:
        person((2.6, -12.5, 0), 200, arm_up=0.6)
        person((-3.2, -13.0, 0), 160)
    return car, h

def city_tower(ctx):
    car, h = _tower_scene()
    def up(t, u): car.location.z = 2 + t * 4.0
    def cam(t, u):
        a = -0.45 + u * 0.3
        return dict(pos=(math.sin(a) * 34, -26 + u * 3, 4 + u * 3), look=(0, 6, 13 + u * 5), fov=50)
    return dict(update=up, cam=cam)

def brand(ctx):
    car, h = _tower_scene(brand=True)
    def up(t, u): car.location.z = 6 + t * 3.5
    return dict(update=up, cam=[dict(pos=(4.5, -24, 2.2), look=(0, -8, 6.5), fov=58), dict(pos=(3.0, -21, 2.6), look=(0, -8, 7.5), fov=58)])

def machine_room(ctx):
    _shaft_world(); r = lift_rig(car_z=FH * 4)
    def up(t, u): r.set_car(FH * 4 + t * 0.9)
    return dict(update=up, cam=[dict(pos=(3.6, -6.8, H + 2.6), look=(0.2, 0.3, H + 0.6), fov=46),
                                dict(pos=(2.7, -5.4, H + 2.1), look=(0.25, 0.3, H + 0.8), fov=44)])

def counter_reveal(ctx):
    _shaft_world(); r = lift_rig(car_z=FH * 3)
    def up(t, u): r.set_car(FH * 3 - t * 0.5)
    cwz = H - 2.9 - FH * 3
    return dict(update=up, cam=[dict(pos=(-2.2, -6.0, cwz + 2.6), look=(CAR['x'], 0, FH * 3 + 1.2), fov=46),
                                dict(pos=(2.6, -4.2, cwz + 1.9), look=(CW['x'], 0.35, cwz + 1.0), fov=40)])

def balance(ctx):
    _shaft_world(); z = (H - 2.9) / 2; r = lift_rig(car_z=z, open_doors=True, people=3)
    def up(t, u): r.set_car(z + math.sin(t * 2) * 0.02)
    return dict(update=up, cam=[dict(pos=(0.5, -7.4, z + 1.7), look=(0.35, 0, z + 1.2), fov=44),
                                dict(pos=(0.4, -6.2, z + 1.5), look=(0.35, 0, z + 1.2), fov=44)])

def balance_move(ctx):
    _ext_site(backdrop=True)
    box((1.4, 1.2, 1.1), m_concrete(0x9d978c), (0, -4, 0.55), bevel=0.05)
    pv = empty((0, -4, 1.2))
    box((6.2, 0.6, 0.16), m_wood(0x9a6a40), (0, 0, 0), parent=pv, bevel=0.02)
    c = empty((-2.2, 0, 0.08), pv)
    box((1.3, 1.0, 1.7), m_steel(0xc8ccd0), (0, 0, 0.85), parent=c, bevel=0.04)
    box((1.32, 1.02, 0.1), m_paint(BLUE, 0.1), (0, 0, 0.95), parent=c)
    box((1.0, 0.02, 1.4), m_plain(0x2a2c30, 0.2), (0, -0.51, 0.85), parent=c)
    w = empty((2.2, 0, 0.08), pv)
    for i in range(5): box((0.8, 0.6, 0.28), m_paint(0x3a3c40 if i % 2 else YEL, 0.5), (0, 0, 0.15 + i * 0.3), parent=w, bevel=0.01)
    person((3.6, -5.8, 0), 150)
    def up(t, u): pv.rotation_euler = (0, math.sin(t * 2.4) * 0.07 * math.exp(-t * 0.5), 0)
    return dict(update=up, cam=[dict(pos=(0.5, -19.5, 3.4), look=(0, -4, 1.6), fov=40), dict(pos=(1.2, -17.5, 3.0), look=(0, -4, 1.6), fov=40)])

def motor_push(ctx):
    _shaft_world(); r = lift_rig(car_z=FH * 5)
    def up(t, u): r.set_car(FH * 5 + seg(t, 0.1, 1.8) * 1.0)
    return dict(update=up, cam=[dict(pos=(2.4, -3.3, H + 1.9), look=(SHEAVE['x'], 0.2, SHEAVE['z'] - 0.1), fov=42),
                                dict(pos=(1.7, -2.6, H + 1.6), look=(SHEAVE['x'], 0.2, SHEAVE['z'] - 0.1), fov=42)])

def cables(ctx):
    _shaft_world(); z = FH * 5; r = lift_rig(car_z=z)
    top = z + CAR['h']
    return dict(update=lambda t, u: None, cam=[dict(pos=(0.9, -2.6, top + 1.6), look=(CAR['x'] + 0.4, 0, top + 0.9), fov=46),
                                               dict(pos=(0.9, -2.3, top + 3.4), look=(SHEAVE['x'] - SHEAVE['r'], 0, top + 6.5), fov=46)])

def cable_close(ctx):
    """macro of a steel wire rope: 6 strands twisted around a core"""
    world(time='day', clouds=0.4)
    box((20, 1, 20), m_concrete(0xb8b2a6), (0, 3, 0))
    g = empty((0, 0, 0))
    wire = m_steel(0x8c9096, 0.28, brushed=False)
    for k in range(6):
        helix(0.07, 3.0, 3.2, 0.032, wire, (0, 0, -1.5), parent=g, phase=k * math.pi / 3, n=160)
    cyl(0.045, 3.0, m_plain(0x2a2a2a, 0.6), (0, 0, 0), parent=g, seg=12)
    for k in range(3):
        g2 = empty((-0.5 + k * 0.5, 0.3, 0)); g2.rotation_euler = (0, 0, k)
        for j in range(6): helix(0.07, 3.0, 3.2, 0.032, wire, (0, 0, -1.5), parent=g2, phase=j * math.pi / 3, n=160)
    g.location.x = 0.0
    area_light((-1.5, -1.5, 1.5), (60, 0, -45), 2, 120)
    def up(t, u): g.rotation_euler = (0, 0, t * 0.5)
    return dict(update=up, cam=[dict(pos=(0.15, -0.75, 0.25), look=(0, 0, 0.05), fov=38), dict(pos=(0.1, -0.6, -0.1), look=(0, 0, -0.1), fov=38)], dof=(0.7, 2.0))

def cable_cut(ctx):
    _shaft_world(time='dusk'); z = FH * 5; r = lift_rig(car_z=z)
    sparks = []
    for i in range(14):
        s = sphere(0.025, m_emit(0xffb040, 40), (SHEAVE['x'] - SHEAVE['r'], -0.2 + random.random() * 0.4, z + 4.0), seg=6); sparks.append((s, random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.5, 2)))
    def up(t, u):
        cut = t > 0.6; k = max(0, t - 0.6)
        r.set_car(z - 0.5 * 9.8 * 0.12 * k * k, cables_on=not cut)
        for s, vx, vy, vz in sparks:
            s.hide_render = not cut or k > 0.8
            s.location = (SHEAVE['x'] - SHEAVE['r'] + vx * k * 1.5, vy * k * 1.5, z + 4.0 + vz * k - 4.9 * k * k)
    return dict(update=up, cam=[dict(pos=(3.0, -6.0, z + 3.6), look=(CAR['x'], 0, z + 3.0), fov=48), dict(pos=(2.8, -6.2, z + 3.0), look=(CAR['x'], 0, z + 2.0), fov=50)])

def governor_xray(ctx):
    _shaft_world(); r = lift_rig(car_z=FH * 4)
    def up(t, u): r.set_car(FH * 4 - t * 0.7)
    return dict(update=up, cam=[dict(pos=(1.8, -5.0, H + 1.6), look=(GOV['x'], GOV['y'], GOV['z'] - 0.3), fov=44),
                                dict(pos=(2.6, -7.5, H - 3.5), look=(GOV['x'] + 0.6, 0, H - 6.5), fov=48)])

def gov_wheel(ctx):
    _shaft_world(); r = lift_rig(car_z=FH * 4)
    def up(t, u): r.set_car(FH * 4 - t * 1.2)
    return dict(update=up, cam=[dict(pos=(GOV['x'] + 1.7, GOV['y'] - 0.9, GOV['z'] + 0.25), look=(GOV['x'], GOV['y'], GOV['z']), fov=38),
                                dict(pos=(GOV['x'] + 1.3, GOV['y'] - 0.6, GOV['z'] + 0.1), look=(GOV['x'], GOV['y'], GOV['z']), fov=36)], dof=(None, 2.0))

def safety_brake(ctx):
    _shaft_world(); stop = FH * 3 + 1.0; r = lift_rig(car_z=stop + 2.2)
    rx = CAR['x'] - CAR['w'] / 2 - 0.12
    sparks = [sphere(0.02, m_emit(0xffa030, 50), (rx, 0, stop), seg=6) for _ in range(16)]
    rnd = [(random.uniform(-1, 1), random.uniform(-1.2, -0.2), random.uniform(-0.5, 1.5)) for _ in sparks]
    def up(t, u):
        k = min(t, 0.85); z = stop + 2.2 - (2.2 / 0.85 ** 2) * k * k; r.set_car(z)
        c = ease_out(seg(t, 0.7, 0.9))
        for i, g in enumerate(r.gear): g.scale = (1 + c * 0.5, 1, 1)
        e = t - 0.85
        for s, (vx, vy, vz) in zip(sparks, rnd):
            s.hide_render = not (0 < e < 0.5)
            s.location = (rx + vx * e * 1.2, vy * e * 1.5, r.car.location.z + vz * e - 4.9 * e * e)
    return dict(update=up, cam=[dict(pos=(1.4, -4.2, stop + 1.6), look=(rx + 0.4, 0, stop + 0.6), fov=44), dict(pos=(0.9, -3.4, stop + 1.2), look=(rx + 0.2, 0, stop + 0.4), fov=42)])

def buffer(ctx):
    _shaft_world(); r = lift_rig(car_z=2.0, machine=False, governor=False)
    def up(t, u): r.set_car(lerp(2.0, -0.22, ease(seg(t, 0.2, 1.8))))
    return dict(update=up, cam=[dict(pos=(2.6, -4.4, 0.6), look=(CAR['x'], 0, -0.6), fov=46), dict(pos=(1.9, -3.5, 0.3), look=(CAR['x'], 0, -0.7), fov=44)])

def _otis(cut):
    world(sun_elev=12, sun_rot=60, time='day', clouds=0.3)
    plane((300, 300), m_wood(0x7a5a3c), (0, 0, 0))
    # exhibition hall: iron arches + glass roof hint
    for i in range(-4, 5):
        box((0.25, 0.25, 12), m_paint(0x5a6066, 0.3), (-14, i * 6, 6)); box((0.25, 0.25, 12), m_paint(0x5a6066, 0.3), (14, i * 6, 6))
    for i in range(-4, 5): box((28.5, 0.25, 0.3), m_paint(0x5a6066, 0.3), (0, i * 6, 12))
    wood = m_wood(0x7a4a2a); T = 10
    for x in (-1.3, 1.3):
        for y in (-1.1, 1.1): box((0.24, 0.24, T), wood, (x, y, T / 2))
        for i in range(30): box((0.08, 0.22, 0.12), m_plain(0x4a2e1a, 0.7), (x * 0.9, 0, 0.5 + i * 0.32), (0, 30, 0))
    box((3.0, 0.3, 0.3), wood, (0, -1.1, T)); box((3.0, 0.3, 0.3), wood, (0, 1.1, T)); box((0.3, 2.5, 0.3), wood, (0, 0, T + 0.3))
    plat = empty((0, 0, 6.0))
    box((2.2, 2.0, 0.16), m_wood(0xa8784a), (0, 0, 0), parent=plat)
    for x in (-1.05, 1.05): box((0.08, 2.0, 1.0), wood, (x, 0, 0.5), parent=plat)
    man, arms = person((0, 0.2, 0.08), 0, shirt=0x1d1f23, pants=0x1d1f23, helmet=False, parent=plat, arm_up=0.8 if cut else 0.4)
    cyl(0.12, 0.28, m_plain(0x111111, 0.4), (0, 0.2, 2.07), parent=plat, seg=16); cyl(0.2, 0.02, m_plain(0x111111, 0.4), (0, 0.2, 1.94), parent=plat, seg=16)
    rope = cyl(0.04, 1.0, m_plain(0xb8a47a, 0.9), (0, 0, 0), seg=10)
    random.seed(9)
    for i in range(16):
        a = -0.8 + i * 0.1; rr = 6 + (i % 3) * 1.1
        person((math.sin(a) * rr, -math.cos(a) * rr, 0), 180 - math.degrees(a), shirt=random.choice([0x4a3a2e, 0x2e3a4a, 0x4a4a3a, 0x5a2e2e]), pants=0x2a2a2a, helmet=False)
    point_light((3, -4, 8), 900, (1, 0.85, 0.6), 1.5)
    def up(t, u):
        tc = 0.6 if cut else 99; k = max(0, t - tc)
        drop = min(0.35, 0.5 * 9.8 * min(k, 0.27) ** 2) if cut else 0
        pz = 6.0 - drop; plat.location.z = pz
        rope.hide_render = t >= tc; a = pz + 0.1; rope.location = (0, 0, (a + T) / 2); rope.scale.z = T - a
    if cut: return dict(update=up, cam=[dict(pos=(4.0, -7.0, 6.8), look=(0, 0, 6.6), fov=44), dict(pos=(3.2, -5.6, 6.4), look=(0, 0, 6.3), fov=44)])
    def cam(t, u):
        a = 0.8 - u * 0.5
        return dict(pos=(math.sin(a) * 13, -math.cos(a) * 13, 2.5 + u * 1.5), look=(0, 0, 5.2), fov=46)
    return dict(update=up, cam=cam)

def otis(ctx): return _otis(False)
def otis_cut(ctx): return _otis(True)

def _bomber(hit):
    world(sun_elev=30, sun_rot=20, time='day', clouds=0.9, haze=1.0)
    ground_dirt()
    sc = bpy.context.scene
    # fog volume around the scene
    fog = box((400, 400, 160), None, (0, 0, 80))
    fm = D.materials.new('fog'); fm.use_nodes = True; nt = fm.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumeScatter'); v.inputs['Density'].default_value = 0.0018
    nt.links.new(v.outputs[0], o.inputs['Volume']); fog.data.materials.append(fm)
    # art-deco skyscraper: stepped tower
    TH = 0
    for (w, fl) in ((26, 22), (20, 30), (14, 18), (9, 8)):
        h = fl * 3.6
        box((w, w, h), m_facade(0xc9c1b0, 0x4d5d6c, cols=int(w / 2.0), rows=fl, w=w, h=h, frame=0.3), (0, 0, TH + h / 2))
        TH += h
    cyl(0.6, 18, m_steel(0x9aa1a8), (0, 0, TH + 9), seg=12, r2=0.15)
    for (x, y, f) in ((-45, 30, 14), (40, 35, 18), (-30, -40, 8), (35, -45, 10)):
        tower(x, y, 16, 16, f, 0xbfc0bb, 0x56677a)
    pl = empty((0, 0, 0)); pl.scale = (2.4,) * 3
    od = m_paint(0x55603f, 0.3, 0.45)
    cyl(0.55, 7.0, od, (0, 0, 0), (0, 90, 0), parent=pl, seg=24, r2=0.38)
    sphere(0.55, m_glass(0xbfd8e8, 0.05), (3.4, 0, 0.1), parent=pl)
    box((1.6, 10.5, 0.14), od, (0.4, 0, 0.15), parent=pl, bevel=0.05)
    for y in (-2.4, 2.4):
        cyl(0.33, 1.6, m_paint(0x3e4632, 0.3), (1.2, y, 0.05), (0, 90, 0), parent=pl, seg=16)
        cyl(0.6, 0.02, m_plain(0x222222, 0.4, alpha=0.4), (2.05, y, 0.05), (0, 90, 0), parent=pl, seg=16)
    box((1.0, 3.8, 0.1), od, (-3.2, 0, 0.35), parent=pl)
    for y in (-1.8, 1.8): box((0.9, 0.1, 1.3), od, (-3.3, y, 0.9), parent=pl)
    fx = []; smk = []
    if hit:
        for i in range(4):
            f = sphere(1, m_fire(), ((i - 1.5) * 3, -14, 78 + (i % 2) * 2), seg=16); fx.append(f)
        for i in range(5):
            s_ = sphere(1, m_smoke(0x2e2e30), ((i - 2) * 4, -14.5, 82 + (i % 2) * 3), seg=12); smk.append(s_)
    hitp = (0, -12.5, 78)
    start = (-70, -50, 84) if hit else (-120, -80, 88)
    end = hitp if hit else (-70, -50, 84)
    tHit = 0.75
    def up(t, u):
        k = min(1, t / tHit) if hit else u
        pl.location = lerpv(start, end, k)
        d = Vector(end) - Vector(start)
        pl.rotation_euler = (0.1, -0.06, math.atan2(d.y, d.x))
        pl.hide_render = hit and t >= tHit
        if hit:
            e = max(0, t - tHit)
            for i, f in enumerate(fx):
                f.hide_render = e <= 0
                f.scale = (min(7, 0.5 + e * (14 + i * 2)),) * 3 if e > 0 else (0.01,) * 3
            for i, s_ in enumerate(smk):
                sc_ = min(12, 0.5 + e * (6 + i)) if e > 0.15 else 0.01
                s_.scale = (sc_,) * 3; s_.location.z = 82 + (i % 2) * 3 + e * 4; s_.hide_render = e <= 0.15
    if hit: return dict(update=up, cam=[dict(pos=(60, -110, 40), look=(0, 0, 76), fov=40), dict(pos=(55, -100, 42), look=(0, 0, 78), fov=40)])
    return dict(update=up, cam=[dict(pos=(-60, -125, 70), look=(-110, -75, 88), fov=42), dict(pos=(-60, -122, 72), look=(-75, -52, 86), fov=42)])

def bomber(ctx): return _bomber(False)
def bomber_hit(ctx): return _bomber(True)

def fall75(ctx):
    _shaft_world(time='dusk'); r = lift_rig(car_z=FH * 7, people=1)
    T = max(1.2, ctx['dur'] * 0.85); z0 = FH * 7
    zf = lambda t: max(-0.22, z0 - (z0 + 0.22) * min(1, t / T) ** 2)
    def up(t, u): r.set_car(zf(t), cables_on=False)
    def cam(t, u):
        z = zf(t); return dict(pos=(4.6, -8.5, z + 2.6), look=(CAR['x'], 0, z + 1.0), fov=52)
    return dict(update=up, cam=cam, motion_blur=True)

def survive(ctx):
    _shaft_world(time='dusk'); r = lift_rig(car_z=-0.22, open_doors=True, people=0, light_on=False)
    r.set_car(-0.22, cables_on=False)
    p, arms = person((0, 0.1, 0.15), 180 - 10, shirt=0x2f6fd6, helmet=False, scale=0.92, parent=r.car)
    flick = point_light((0, -0.2, CAR['h'] - 0.2), 0, (1, 0.9, 0.7), 0.3, parent=r.car)
    for i in range(6):
        sphere(0.8, m_smoke(0x9a948a), (CAR['x'] + random.uniform(-1, 1), -0.5, -0.8 + random.uniform(0, 0.8)), seg=10).scale = (1.2, 1.0, 0.5)
    def up(t, u):
        k = ease_out(seg(t, 0.2, 1.5))
        p.scale = (0.92, 0.92, 0.92 * (0.55 + 0.45 * k))
        flick.data.energy = 40 if (int(t * 9) % 4) else 5
    return dict(update=up, cam=[dict(pos=(2.6, -6.2, 1.8), look=(CAR['x'], 0, 0.9), fov=44), dict(pos=(1.7, -4.6, 1.5), look=(CAR['x'], 0, 0.9), fov=42)])

def outro(ctx):
    world(time='day', clouds=0.3)
    plane((30, 30), m_plain(0xcfc6b6, 0.25), (0, 0, 0))
    box((14, 0.3, 7), m_concrete(0xe6e0d4, stains=False), (0, 0.15, 3.5))
    box((2.8, 0.1, 3.0), m_steel(0x9aa0a6, 0.3), (0, 0.0, 1.5))
    for x in (-0.62, 0.62): box((1.2, 0.06, 2.75), m_steel(0xd0d4d8, 0.2), (x, -0.06, 1.4))
    box((0.9, 0.06, 0.32), m_plain(0x111317, 0.3), (0, -0.05, 3.25))
    text_obj('8', 0.22, m_emit(0xff9a2a, 6), (0, -0.09, 3.24), font_path=FONT)
    box((0.24, 0.05, 0.5), m_steel(0x9aa1a8), (1.85, -0.03, 1.25))
    btn = sphere(0.05, m_emit(0xffb21f, 1), (1.85, -0.07, 1.32), seg=12)
    p, arms = person((1.2, -1.0, 0), 20, shirt=0x2f6fd6, helmet=False)
    area_light((0, -4, 4), (60, 0, 0), 4, 600)
    def up(t, u):
        k = (math.sin(t * 10) + 1) / 2
        arms[1].rotation_euler = (R(-70 - 10 * k), 0, R(-20))
        btn.data.materials[0].node_tree.nodes['Emission'].inputs[1].default_value = 8 if k > 0.8 else 1
    return dict(update=up, cam=[dict(pos=(3.2, -4.8, 1.8), look=(0.8, 0, 1.4), fov=44), dict(pos=(4.6, -6.8, 2.2), look=(0.6, 0, 1.6), fov=46)])

def outro_q(ctx):
    car, h = _tower_scene(time='dusk', brand=True)
    def up(t, u): car.location.z = 10 + t * 3
    return dict(update=up, cam=[dict(pos=(3.0, -21, 2.6), look=(0, -8, 7.5), fov=58), dict(pos=(6, -30, 5), look=(0, 0, 12), fov=56)])

SHOTS = {k: v for k, v in globals().items() if callable(v) and not k.startswith('_') and k in (
    'shaft_down shaft_fall city_tower brand machine_room counter_reveal balance balance_move motor_push cables cable_close cable_cut '
    'governor_xray gov_wheel safety_brake buffer otis otis_cut bomber bomber_hit fall75 survive outro outro_q').split()}
