# lib.py — realistic-ish procedural world kit for Blender/Cycles (Bongkarinsemua)
import bpy, math, random
from mathutils import Vector, Euler

D = bpy.data
R = math.radians

# ---------------------------------------------------------------- scene setup
def reset(res=(540, 960), samples=20, fps=30):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for m in list(D.materials): D.materials.remove(m)
    _MAT.clear()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 4; sc.cycles.volume_bounces = 0; sc.cycles.transparent_max_bounces = 6
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.fps = fps
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 92
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.view_settings.exposure = 0.0
    return sc

# ---------------------------------------------------------------- node helpers
def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bs.outputs[0], out.inputs[0])
    return nt, bs, out

def _ramp(nt, src, stops):
    r = nt.nodes.new('ShaderNodeValToRGB')
    el = r.color_ramp.elements
    while len(el) > 2: el.remove(el[-1])
    for i, (p, c) in enumerate(stops):
        e = el[i] if i < 2 else el.new(p)
        e.position = p; e.color = (*c, 1) if len(c) == 3 else c
    nt.links.new(src, r.inputs[0])
    return r

def _noise(nt, scale, detail=6, rough=0.6, coord=None, dim='3D'):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.noise_dimensions = dim
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    if coord is not None: nt.links.new(coord, n.inputs['Vector'])
    return n

def _coord(nt, kind='Object'):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    return tc.outputs[kind]

def _bump(nt, h, strength=0.3, dist=0.02, normal=None):
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = dist
    nt.links.new(h, b.inputs['Height'])
    if normal is not None: nt.links.new(normal, b.inputs['Normal'])
    return b.outputs[0]

def _mix(nt, a, b, fac, mode='MIX'):
    m = nt.nodes.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = mode
    for k, v in ((6, a), (7, b)):
        if isinstance(v, (tuple, list)): m.inputs[k].default_value = (*v, 1) if len(v) == 3 else v
        else: nt.links.new(v, m.inputs[k])
    if isinstance(fac, (int, float)): m.inputs[0].default_value = fac
    else: nt.links.new(fac, m.inputs[0])
    return m.outputs[2]

def srgb(h):
    """hex int -> linear rgb tuple"""
    c = [((h >> s) & 255) / 255 for s in (16, 8, 0)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

_MAT = {}
def _cached(key, fn):
    if key not in _MAT: _MAT[key] = fn()
    return _MAT[key]

# ---------------------------------------------------------------- materials
def m_plain(color, rough=0.5, metal=0.0, name=None, emission=None, estr=0.0, alpha=1.0, coat=0.0):
    def mk():
        m = D.materials.new(name or f'plain_{color:06x}')
        nt, bs, _ = _nodes(m)
        bs.inputs['Base Color'].default_value = (*srgb(color), 1)
        bs.inputs['Roughness'].default_value = rough
        bs.inputs['Metallic'].default_value = metal
        if coat: bs.inputs['Coat Weight'].default_value = coat
        if emission is not None:
            bs.inputs['Emission Color'].default_value = (*srgb(emission), 1)
            bs.inputs['Emission Strength'].default_value = estr
        if alpha < 1: bs.inputs['Alpha'].default_value = alpha
        return m
    return _cached(('plain', color, rough, metal, emission, estr, alpha, coat, name), mk)

def m_dirt(base=0x8a6a4a):
    def mk():
        m = D.materials.new('dirt'); nt, bs, _ = _nodes(m)
        co = _coord(nt, 'Object')
        n1 = _noise(nt, 0.35, 8, 0.6, co); n2 = _noise(nt, 6.0, 10, 0.7, co)
        vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 22; nt.links.new(co, vor.inputs['Vector'])
        c1 = _ramp(nt, n1.outputs['Fac'], [(0.35, srgb(0x6e5038)), (0.65, srgb(base))])
        c2 = _ramp(nt, n2.outputs['Fac'], [(0.3, (0.55, 0.55, 0.55)), (0.7, (1.1, 1.05, 1.0))])
        col = _mix(nt, c1.outputs[0], c2.outputs[0], 1.0, 'MULTIPLY')
        pebbles = _ramp(nt, vor.outputs['Distance'], [(0.0, (0.75, 0.72, 0.68)), (0.12, (1, 1, 1))])
        col = _mix(nt, col, pebbles.outputs[0], 0.6, 'MULTIPLY')
        nt.links.new(col, bs.inputs['Base Color'])
        bs.inputs['Roughness'].default_value = 0.95
        h = _mix(nt, n2.outputs['Fac'], vor.outputs['Distance'], 0.5)
        nt.links.new(_bump(nt, h, 0.6, 0.05), bs.inputs['Normal'])
        return m
    return _cached(('dirt', base), mk)

def m_soil_section():
    """cut-away soil face: layered brown/red bands + grain"""
    def mk():
        m = D.materials.new('soil'); nt, bs, _ = _nodes(m)
        co = _coord(nt, 'Object')
        n = _noise(nt, 3.0, 8, 0.65, co)
        sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(co, sep.inputs[0])
        add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
        nt.links.new(sep.outputs['Z'], add.inputs[0])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.35
        nt.links.new(n.outputs['Fac'], mul.inputs[0]); nt.links.new(mul.outputs[0], add.inputs[1])
        bands = _ramp(nt, add.outputs[0], [(0.0, srgb(0x6b5a48)), (0.5, srgb(0x7a5a3e))])
        # map z range roughly -12..0 into ramp: use Map Range
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value = -14; mr.inputs[2].default_value = 0.5
        nt.links.new(add.outputs[0], mr.inputs[0]); nt.links.new(mr.outputs[0], bands.inputs[0])
        bands.color_ramp.elements[0].position = 0.0; bands.color_ramp.elements[0].color = (*srgb(0xb9a58a), 1)
        e = bands.color_ramp.elements.new(0.55); e.color = (*srgb(0x9a4a2a), 1)
        e = bands.color_ramp.elements.new(0.7); e.color = (*srgb(0x8a6448), 1)
        bands.color_ramp.elements[1].position = 1.0; bands.color_ramp.elements[1].color = (*srgb(0x7a5a40), 1)
        g = _noise(nt, 40, 4, 0.7, co)
        gr = _ramp(nt, g.outputs['Fac'], [(0.3, (0.7, 0.7, 0.7)), (0.7, (1.1, 1.1, 1.1))])
        col = _mix(nt, bands.outputs[0], gr.outputs[0], 1.0, 'MULTIPLY')
        nt.links.new(col, bs.inputs['Base Color'])
        bs.inputs['Roughness'].default_value = 1.0
        nt.links.new(_bump(nt, g.outputs['Fac'], 0.5, 0.03), bs.inputs['Normal'])
        return m
    return _cached(('soil',), mk)

def m_concrete(tint=0xbdb8ae, scale=1.0, stains=True):
    def mk():
        m = D.materials.new(f'concrete_{tint:06x}'); nt, bs, _ = _nodes(m)
        co = _coord(nt, 'Object')
        n1 = _noise(nt, 0.8 * scale, 8, 0.6, co); n2 = _noise(nt, 18 * scale, 6, 0.6, co)
        base = _ramp(nt, n1.outputs['Fac'], [(0.3, tuple(x * 0.8 for x in srgb(tint))), (0.7, srgb(tint))])
        fine = _ramp(nt, n2.outputs['Fac'], [(0.3, (0.85, 0.85, 0.85)), (0.7, (1.05, 1.05, 1.05))])
        col = _mix(nt, base.outputs[0], fine.outputs[0], 1.0, 'MULTIPLY')
        if stains:
            st = _noise(nt, 2.5 * scale, 4, 0.5, co)
            sr = _ramp(nt, st.outputs['Fac'], [(0.55, (1, 1, 1)), (0.75, (0.72, 0.7, 0.66))])
            col = _mix(nt, col, sr.outputs[0], 1.0, 'MULTIPLY')
        nt.links.new(col, bs.inputs['Base Color'])
        rr = _ramp(nt, n2.outputs['Fac'], [(0.2, (0.78, 0.78, 0.78)), (0.8, (0.95, 0.95, 0.95))])
        nt.links.new(rr.outputs[0], bs.inputs['Roughness'])
        nt.links.new(_bump(nt, n2.outputs['Fac'], 0.25, 0.01), bs.inputs['Normal'])
        return m
    return _cached(('concrete', tint, scale, stains), mk)

def m_paint(color, rust=0.35, rough=0.45, diamond=False, metal=0.0):
    """painted steel with procedural wear/rust; diamond=True adds tread-plate bump"""
    def mk():
        m = D.materials.new(f'paint_{color:06x}'); nt, bs, _ = _nodes(m)
        co = _coord(nt, 'Object')
        n = _noise(nt, 2.5, 10, 0.7, co); n2 = _noise(nt, 12, 8, 0.7, co)
        mask_src = _mix(nt, n.outputs['Fac'], n2.outputs['Fac'], 0.35)
        lo = 0.72 - rust * 0.25
        mask = _ramp(nt, mask_src, [(lo, (0, 0, 0)), (lo + 0.06, (1, 1, 1))])
        rustc = _ramp(nt, n2.outputs['Fac'], [(0.3, srgb(0x5a3018)), (0.7, srgb(0x8a4a22))])
        dirt = _ramp(nt, n.outputs['Fac'], [(0.4, (1, 1, 1)), (0.8, (0.78, 0.74, 0.68))])
        col = _mix(nt, (*srgb(color),), dirt.outputs[0], 1.0, 'MULTIPLY')
        col = _mix(nt, col, rustc.outputs[0], mask.outputs[0])
        nt.links.new(col, bs.inputs['Base Color'])
        rr = _mix(nt, (rough, rough, rough), (0.9, 0.9, 0.9), mask.outputs[0])
        nt.links.new(rr, bs.inputs['Roughness'])
        bs.inputs['Metallic'].default_value = metal
        h = n2.outputs['Fac']
        if diamond:
            # tread plate: two rotated wave textures, product → raised diamonds
            mp1 = nt.nodes.new('ShaderNodeMapping'); mp1.inputs['Rotation'].default_value = (0, 0, R(45)); mp1.inputs['Scale'].default_value = (14, 14, 14)
            mp2 = nt.nodes.new('ShaderNodeMapping'); mp2.inputs['Rotation'].default_value = (0, 0, R(-45)); mp2.inputs['Scale'].default_value = (14, 14, 14)
            uv = _coord(nt, 'UV')
            nt.links.new(uv, mp1.inputs[0]); nt.links.new(uv, mp2.inputs[0])
            w1 = nt.nodes.new('ShaderNodeTexWave'); w1.wave_profile = 'SIN'; nt.links.new(mp1.outputs[0], w1.inputs[0])
            w2 = nt.nodes.new('ShaderNodeTexWave'); w2.wave_profile = 'SIN'; nt.links.new(mp2.outputs[0], w2.inputs[0])
            for w in (w1, w2): w.inputs['Scale'].default_value = 3; w.inputs['Distortion'].default_value = 0
            mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'
            nt.links.new(w1.outputs['Fac'], mm.inputs[0]); nt.links.new(w2.outputs['Fac'], mm.inputs[1])
            th = nt.nodes.new('ShaderNodeMath'); th.operation = 'GREATER_THAN'; th.inputs[1].default_value = 0.55
            nt.links.new(mm.outputs[0], th.inputs[0])
            h = th.outputs[0]
            nt.links.new(_bump(nt, h, 0.35, 0.004), bs.inputs['Normal'])
        else:
            nt.links.new(_bump(nt, h, 0.12, 0.004), bs.inputs['Normal'])
        return m
    return _cached(('paint', color, rust, rough, diamond, metal), mk)

def m_steel(color=0xb8bcc2, rough=0.32, brushed=True):
    def mk():
        m = D.materials.new(f'steel_{color:06x}'); nt, bs, _ = _nodes(m)
        bs.inputs['Metallic'].default_value = 1.0
        co = _coord(nt, 'Object')
        if brushed:
            mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, 60); nt.links.new(co, mp.inputs[0])
            n = _noise(nt, 30, 4, 0.5, mp.outputs[0])
            rr = _ramp(nt, n.outputs['Fac'], [(0.3, (rough - 0.08,) * 3), (0.7, (rough + 0.08,) * 3)])
            nt.links.new(rr.outputs[0], bs.inputs['Roughness'])
        else:
            bs.inputs['Roughness'].default_value = rough
        sm = _noise(nt, 3, 6, 0.6, co)
        cr = _ramp(nt, sm.outputs['Fac'], [(0.3, tuple(x * 0.82 for x in srgb(color))), (0.7, srgb(color))])
        nt.links.new(cr.outputs[0], bs.inputs['Base Color'])
        return m
    return _cached(('steel', color, rough, brushed), mk)

def m_glass(tint=0xbfd8e8, rough=0.03, alpha_like=False):
    def mk():
        m = D.materials.new(f'glass_{tint:06x}'); nt, bs, _ = _nodes(m)
        bs.inputs['Base Color'].default_value = (*srgb(tint), 1)
        bs.inputs['Roughness'].default_value = rough
        bs.inputs['Transmission Weight'].default_value = 1.0
        bs.inputs['IOR'].default_value = 1.2 if alpha_like else 1.45
        return m
    return _cached(('glass', tint, rough, alpha_like), mk)

def m_asphalt():
    def mk():
        m = D.materials.new('asphalt'); nt, bs, _ = _nodes(m)
        co = _coord(nt, 'Object')
        n = _noise(nt, 60, 4, 0.7, co); n2 = _noise(nt, 0.5, 6, 0.6, co)
        c = _ramp(nt, n.outputs['Fac'], [(0.35, srgb(0x2a2b2e)), (0.65, srgb(0x4a4b4e))])
        c2 = _ramp(nt, n2.outputs['Fac'], [(0.3, (0.8, 0.8, 0.8)), (0.7, (1.05, 1.05, 1.05))])
        nt.links.new(_mix(nt, c.outputs[0], c2.outputs[0], 1, 'MULTIPLY'), bs.inputs['Base Color'])
        bs.inputs['Roughness'].default_value = 0.9
        nt.links.new(_bump(nt, n.outputs['Fac'], 0.3, 0.005), bs.inputs['Normal'])
        return m
    return _cached(('asphalt',), mk)

def m_facade(wall=0xd9d2c3, glass=0x6f8fa8, cols=6, rows=10, w=10.0, h=32.0, frame=0.22, lit=0.0):
    """window grid via brick texture on Object coords (x across, z up). Works for front faces (x/z) and side (y/z)."""
    def mk():
        m = D.materials.new(f'facade_{wall:06x}_{glass:06x}_{cols}_{rows}'); nt, bs, _ = _nodes(m)
        co = _coord(nt, 'Object')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(co, sep.inputs[0])
        addxy = nt.nodes.new('ShaderNodeMath'); addxy.operation = 'ADD'
        nt.links.new(sep.outputs['X'], addxy.inputs[0]); nt.links.new(sep.outputs['Y'], addxy.inputs[1])
        comb = nt.nodes.new('ShaderNodeCombineXYZ')
        sx = nt.nodes.new('ShaderNodeMath'); sx.operation = 'MULTIPLY'; sx.inputs[1].default_value = cols / w
        sz = nt.nodes.new('ShaderNodeMath'); sz.operation = 'MULTIPLY'; sz.inputs[1].default_value = rows / h
        nt.links.new(addxy.outputs[0], sx.inputs[0]); nt.links.new(sep.outputs['Z'], sz.inputs[0])
        fx = nt.nodes.new('ShaderNodeMath'); fx.operation = 'FRACT'; nt.links.new(sx.outputs[0], fx.inputs[0])
        fz = nt.nodes.new('ShaderNodeMath'); fz.operation = 'FRACT'; nt.links.new(sz.outputs[0], fz.inputs[0])
        def band(src, a, b):
            g1 = nt.nodes.new('ShaderNodeMath'); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = a; nt.links.new(src, g1.inputs[0])
            g2 = nt.nodes.new('ShaderNodeMath'); g2.operation = 'LESS_THAN'; g2.inputs[1].default_value = b; nt.links.new(src, g2.inputs[0])
            mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(g1.outputs[0], mm.inputs[0]); nt.links.new(g2.outputs[0], mm.inputs[1])
            return mm.outputs[0]
        wx = band(fx.outputs[0], frame, 1 - frame); wz = band(fz.outputs[0], frame * 1.2, 1 - frame * 0.5)
        win = nt.nodes.new('ShaderNodeMath'); win.operation = 'MULTIPLY'; nt.links.new(wx, win.inputs[0]); nt.links.new(wz, win.inputs[1])
        # per-window variation (curtains/reflection)
        flx = nt.nodes.new('ShaderNodeMath'); flx.operation = 'FLOOR'; nt.links.new(sx.outputs[0], flx.inputs[0])
        flz = nt.nodes.new('ShaderNodeMath'); flz.operation = 'FLOOR'; nt.links.new(sz.outputs[0], flz.inputs[0])
        nt.links.new(flx.outputs[0], comb.inputs[0]); nt.links.new(flz.outputs[0], comb.inputs[1])
        wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '3D'; nt.links.new(comb.outputs[0], wn.inputs[0])
        gcol = _ramp(nt, wn.outputs['Value'], [(0.0, tuple(x * 0.35 for x in srgb(glass))), (1.0, tuple(x * 0.8 for x in srgb(glass)))])
        n = _noise(nt, 1.5, 6, 0.6, co)
        wcol = _ramp(nt, n.outputs['Fac'], [(0.3, tuple(x * 0.82 for x in srgb(wall))), (0.7, srgb(wall))])
        col = _mix(nt, wcol.outputs[0], gcol.outputs[0], win.outputs[0])
        nt.links.new(col, bs.inputs['Base Color'])
        rr = _mix(nt, (0.85, 0.85, 0.85), (0.08, 0.08, 0.08), win.outputs[0])
        nt.links.new(rr, bs.inputs['Roughness'])
        met = _mix(nt, (0, 0, 0), (0.85, 0.85, 0.85), win.outputs[0])
        nt.links.new(met, bs.inputs['Metallic'])
        if lit:
            lm = nt.nodes.new('ShaderNodeMath'); lm.operation = 'GREATER_THAN'; lm.inputs[1].default_value = 1 - lit
            nt.links.new(wn.outputs['Value'], lm.inputs[0])
            l2 = nt.nodes.new('ShaderNodeMath'); l2.operation = 'MULTIPLY'; nt.links.new(lm.outputs[0], l2.inputs[0]); nt.links.new(win.outputs[0], l2.inputs[1])
            bs.inputs['Emission Color'].default_value = (*srgb(0xffd9a0), 1)
            m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = 3.0
            nt.links.new(l2.outputs[0], m2.inputs[0]); nt.links.new(m2.outputs[0], bs.inputs['Emission Strength'])
        return m
    return _cached(('facade', wall, glass, cols, rows, w, h, frame, lit), mk)

def m_corrugated(color=0xb8bcc0, stripe=None):
    def mk():
        m = D.materials.new(f'corr_{color:06x}'); nt, bs, _ = _nodes(m)
        co = _coord(nt, 'Object')
        w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.bands_direction = 'X'
        w.inputs['Scale'].default_value = 30; w.inputs['Distortion'].default_value = 0
        nt.links.new(co, w.inputs['Vector'])
        n = _noise(nt, 2, 6, 0.6, co)
        c = _ramp(nt, n.outputs['Fac'], [(0.3, tuple(x * 0.75 for x in srgb(color))), (0.7, srgb(color))])
        col = c.outputs[0]
        if stripe is not None:
            sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(co, sep.inputs[0])
            b = nt.nodes.new('ShaderNodeMath'); b.operation = 'GREATER_THAN'; b.inputs[1].default_value = stripe[0]
            nt.links.new(sep.outputs['Z'], b.inputs[0])
            b2 = nt.nodes.new('ShaderNodeMath'); b2.operation = 'LESS_THAN'; b2.inputs[1].default_value = stripe[1]
            nt.links.new(sep.outputs['Z'], b2.inputs[0])
            mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(b.outputs[0], mm.inputs[0]); nt.links.new(b2.outputs[0], mm.inputs[1])
            col = _mix(nt, col, (*srgb(stripe[2]),), mm.outputs[0])
        nt.links.new(col, bs.inputs['Base Color'])
        bs.inputs['Metallic'].default_value = 0.6; bs.inputs['Roughness'].default_value = 0.5
        nt.links.new(_bump(nt, w.outputs['Fac'], 0.6, 0.03), bs.inputs['Normal'])
        return m
    return _cached(('corr', color, stripe), mk)

def m_wood(color=0x8a5a36):
    def mk():
        m = D.materials.new(f'wood_{color:06x}'); nt, bs, _ = _nodes(m)
        co = _coord(nt, 'Object')
        mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, 0.08); nt.links.new(co, mp.inputs[0])
        w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'RINGS'; w.inputs['Scale'].default_value = 6; w.inputs['Distortion'].default_value = 6
        nt.links.new(mp.outputs[0], w.inputs['Vector'])
        c = _ramp(nt, w.outputs['Fac'], [(0.2, tuple(x * 0.6 for x in srgb(color))), (0.8, srgb(color))])
        nt.links.new(c.outputs[0], bs.inputs['Base Color'])
        bs.inputs['Roughness'].default_value = 0.75
        nt.links.new(_bump(nt, w.outputs['Fac'], 0.15, 0.003), bs.inputs['Normal'])
        return m
    return _cached(('wood', color), mk)

def m_emit(color, strength=5.0):
    def mk():
        m = D.materials.new(f'emit_{color:06x}_{strength}')
        m.use_nodes = True; nt = m.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
        e.inputs[0].default_value = (*srgb(color), 1); e.inputs[1].default_value = strength
        nt.links.new(e.outputs[0], out.inputs[0])
        return m
    return _cached(('emit', color, strength), mk)

def _unused(): pass

def m_smoke(color=0x3a3a3c):
    def mk():
        m = D.materials.new('smoke'); m.use_nodes = True; nt = m.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        v = nt.nodes.new('ShaderNodeVolumePrincipled')
        v.inputs['Color'].default_value = (*srgb(color), 1)
        co = _coord(nt, 'Object')
        n = _noise(nt, 2.5, 6, 0.6, co)
        r = _ramp(nt, n.outputs['Fac'], [(0.45, (0, 0, 0)), (0.65, (1, 1, 1))])
        mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = 4.0
        nt.links.new(_sph_falloff(nt, r.outputs[0]), mm.inputs[0]); nt.links.new(mm.outputs[0], v.inputs['Density'])
        nt.links.new(v.outputs[0], out.inputs['Volume'])
        return m
    return _cached(('smoke', color), mk)

# ---------------------------------------------------------------- world / lighting
def world(sun_elev=48, sun_rot=35, strength=1.0, clouds=0.55, time='day', haze=0.0):
    sc = bpy.context.scene
    w = D.worlds.new('W'); sc.world = w
    w.use_nodes = True; nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky')
    for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING'):
        try: sky.sky_type = t; break
        except Exception: pass
    if time == 'dusk': sun_elev = 6
    if time == 'night': sun_elev = -4
    try:
        sky.sun_elevation = R(sun_elev); sky.sun_rotation = R(sun_rot)
        sky.air_density = 1.0; sky.aerosol_density = 1.0 + haze * 4
        sky.sun_disc = True
    except Exception: pass
    skycol = sky.outputs[0]
    # cloud layer: project view dir onto a plane above
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; mx.inputs[1].default_value = 0.04; nt.links.new(sep.outputs['Z'], mx.inputs[0])
    dx = nt.nodes.new('ShaderNodeMath'); dx.operation = 'DIVIDE'; nt.links.new(sep.outputs['X'], dx.inputs[0]); nt.links.new(mx.outputs[0], dx.inputs[1])
    dy = nt.nodes.new('ShaderNodeMath'); dy.operation = 'DIVIDE'; nt.links.new(sep.outputs['Y'], dy.inputs[0]); nt.links.new(mx.outputs[0], dy.inputs[1])
    cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(dx.outputs[0], cb.inputs[0]); nt.links.new(dy.outputs[0], cb.inputs[1])
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 0.9; n.inputs['Detail'].default_value = 10; n.inputs['Roughness'].default_value = 0.62
    nt.links.new(cb.outputs[0], n.inputs['Vector'])
    lo = 0.62 - clouds * 0.22
    cm = _ramp(nt, n.outputs['Fac'], [(lo, (0, 0, 0)), (lo + 0.14, (1, 1, 1))])
    hz = _ramp(nt, sep.outputs['Z'], [(0.02, (0, 0, 0)), (0.18, (1, 1, 1))])
    cmask = nt.nodes.new('ShaderNodeMath'); cmask.operation = 'MULTIPLY'
    nt.links.new(cm.outputs[0], cmask.inputs[0]); nt.links.new(hz.outputs[0], cmask.inputs[1])
    shade = _ramp(nt, n.outputs['Fac'], [(lo, (0.55, 0.58, 0.64)), (lo + 0.3, (1.0, 1.0, 1.0))])
    ccol = {'day': 2.2, 'dusk': 0.9, 'night': 0.03}[time]
    cl = nt.nodes.new('ShaderNodeMix'); cl.data_type = 'RGBA'; cl.blend_type = 'MULTIPLY'
    cl.inputs[0].default_value = 1; nt.links.new(shade.outputs[0], cl.inputs[6])
    tint = {'day': (1, 1, 1), 'dusk': (1.0, 0.62, 0.45), 'night': (0.4, 0.45, 0.6)}[time]
    cl.inputs[7].default_value = (tint[0] * ccol, tint[1] * ccol, tint[2] * ccol, 1)
    final = _mix(nt, skycol, cl.outputs[2], cmask.outputs[0])
    nt.links.new(final, bg.inputs[0])
    bg.inputs[1].default_value = strength * {'day': 0.35, 'dusk': 0.5, 'night': 0.6}[time]
    if time == 'night':
        nm = nt.nodes.new('ShaderNodeMix'); nm.data_type = 'RGBA'; nm.blend_type = 'ADD'; nm.inputs[0].default_value = 1
        nt.links.new(final, nm.inputs[6]); nm.inputs[7].default_value = (0.004, 0.007, 0.018, 1)
        nt.links.new(nm.outputs[2], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    # sun lamp to match
    s = D.lights.new('Sun', 'SUN')
    s.energy = {'day': 4.2, 'dusk': 1.8, 'night': 0.15}[time]
    s.color = {'day': (1.0, 0.96, 0.9), 'dusk': (1.0, 0.62, 0.38), 'night': (0.6, 0.7, 1.0)}[time]
    s.angle = R(1.5)
    o = D.objects.new('Sun', s); bpy.context.scene.collection.objects.link(o)
    el = max(sun_elev, 8) if time != 'night' else 35
    o.rotation_euler = Euler((R(90 - el), 0, R(sun_rot + 90)))
    return o

# ---------------------------------------------------------------- object helpers
def _link(o, parent=None):
    bpy.context.scene.collection.objects.link(o)
    if parent is not None: o.parent = parent
    return o

def empty(loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    o = D.objects.new('E', None); o.location = loc; o.rotation_euler = Euler(tuple(R(a) for a in rot)); return _link(o, parent)

def _mesh_obj(name, bm_fn, mat, loc, rot, parent, bevel=0.0, smooth=False):
    import bmesh
    me = D.meshes.new(name); bm = bmesh.new(); bm_fn(bm); bm.to_mesh(me); bm.free()
    o = D.objects.new(name, me); o.location = loc
    o.rotation_euler = Euler(tuple(R(a) for a in rot))
    if mat is not None: me.materials.append(mat)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    _link(o, parent)
    if bevel > 0:
        md = o.modifiers.new('bev', 'BEVEL'); md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'
        md.harden_normals = False
    return o

def box(size, mat, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, bevel=0.0, uv=False):
    import bmesh
    sx, sy, sz = size
    def f(bm):
        bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
        for v in bm.verts: v.co.x *= sx; v.co.y *= sy; v.co.z *= sz
    return _mesh_obj('box', f, mat, loc, rot, parent, bevel)

def cyl(r, h, mat, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, seg=32, r2=None, bevel=0.0, cap=True):
    import bmesh
    def f(bm):
        bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h, calc_uvs=True)
    return _mesh_obj('cyl', f, mat, loc, rot, parent, bevel, smooth=True)

def sphere(r, mat, loc=(0, 0, 0), parent=None, seg=24, scale=(1, 1, 1)):
    import bmesh
    def f(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r, calc_uvs=True)
        for v in bm.verts: v.co.x *= scale[0]; v.co.y *= scale[1]; v.co.z *= scale[2]
    return _mesh_obj('sph', f, mat, loc, (0, 0, 0), parent, smooth=True)

def torus(R_, r, mat, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R_, minor_radius=r, major_segments=40, minor_segments=12, location=loc, rotation=tuple(math.radians(a) for a in rot))
    o = bpy.context.object
    o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    if parent is not None: o.parent = parent
    return o

def plane(size, mat, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    import bmesh
    def f(bm):
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
        for v in bm.verts: v.co.x *= size[0]; v.co.y *= size[1]
    return _mesh_obj('plane', f, mat, loc, rot, parent)

def tube(points, r, mat, parent=None):
    """cable along points (list of xyz)"""
    cu = D.curves.new('cable', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); sp.points.add(len(points) - 1)
    for i, p in enumerate(points): sp.points[i].co = (*p, 1)
    o = D.objects.new('cable', cu); cu.materials.append(mat); return _link(o, parent)

def text_obj(txt, size, mat, loc, rot=(90, 0, 0), parent=None, extrude=0.02, align='CENTER', font_path=None):
    cu = D.curves.new('txt', 'FONT'); cu.body = txt; cu.size = size; cu.extrude = extrude
    cu.align_x = align; cu.align_y = 'CENTER'
    if font_path:
        cu.font = D.fonts.load(font_path, check_existing=True)
    o = D.objects.new('txt', cu); o.location = loc; o.rotation_euler = Euler(tuple(R(a) for a in rot))
    cu.materials.append(mat); return _link(o, parent)

def camera(fov=45, dof=None, fstop=2.8):
    c = D.cameras.new('Cam'); c.lens_unit = 'FOV'; c.angle = R(fov); c.sensor_fit = 'VERTICAL'
    c.clip_start = 0.05; c.clip_end = 2000
    o = D.objects.new('Cam', c); _link(o); bpy.context.scene.camera = o
    if dof is not None:
        c.dof.use_dof = True; c.dof.focus_distance = dof; c.dof.aperture_fstop = fstop
    return o

def look(cam, pos, target, fov=None, focus=None):
    cam.location = Vector(pos)
    d = Vector(target) - Vector(pos)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if fov is not None:
        cam.data.angle = R(fov)
        # vertical sensor fit: angle applies to vertical in portrait
    if cam.data.dof.use_dof:
        cam.data.dof.focus_distance = focus if focus is not None else d.length

def point_light(loc, energy=200, color=(1, 0.95, 0.85), radius=0.3, parent=None):
    l = D.lights.new('P', 'POINT'); l.energy = energy; l.color = color; l.shadow_soft_size = radius
    o = D.objects.new('P', l); o.location = loc; return _link(o, parent)

def area_light(loc, rot, size=2, energy=300, color=(1, 0.97, 0.9), parent=None):
    l = D.lights.new('A', 'AREA'); l.energy = energy; l.size = size; l.color = color
    o = D.objects.new('A', l); o.location = loc; o.rotation_euler = Euler(tuple(R(a) for a in rot)); return _link(o, parent)

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def ease(u): u = clamp(u); return u * u * (3 - 2 * u)
def ease_out(u): u = clamp(u); return 1 - (1 - u) ** 3
def ease_in(u): u = clamp(u); return u ** 3
def lerp(a, b, u): return a + (b - a) * u
def lerpv(a, b, u): return tuple(lerp(x, y, u) for x, y in zip(a, b))


def _sph_falloff(nt, src_out):
    co = _coord(nt, 'Object')
    g = nt.nodes.new('ShaderNodeTexGradient'); g.gradient_type = 'QUADRATIC_SPHERE'; nt.links.new(co, g.inputs[0])
    m = nt.nodes.new('ShaderNodeMath'); m.operation = 'MULTIPLY'
    nt.links.new(src_out, m.inputs[0]); nt.links.new(g.outputs['Fac'], m.inputs[1])
    return m.outputs[0]

def m_fire():
    def mk():
        m = D.materials.new('fire'); m.use_nodes = True; nt = m.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumePrincipled')
        co = _coord(nt, 'Object'); n = _noise(nt, 2.2, 8, 0.65, co)
        r = _ramp(nt, n.outputs['Fac'], [(0.42, (0, 0, 0)), (0.62, (1, 1, 1))])
        d = nt.nodes.new('ShaderNodeMath'); d.operation = 'MULTIPLY'; d.inputs[1].default_value = 3.0
        fo = _sph_falloff(nt, r.outputs[0])
        nt.links.new(fo, d.inputs[0]); nt.links.new(d.outputs[0], v.inputs['Density'])
        v.inputs['Color'].default_value = (0.05, 0.04, 0.035, 1)
        e = nt.nodes.new('ShaderNodeMath'); e.operation = 'MULTIPLY'; e.inputs[1].default_value = 25.0
        nt.links.new(fo, e.inputs[0]); nt.links.new(e.outputs[0], v.inputs['Emission Strength'])
        v.inputs['Emission Color'].default_value = (1.0, 0.32, 0.05, 1)
        nt.links.new(v.outputs[0], out.inputs['Volume'])
        return m
    return _cached(('fire',), mk)
