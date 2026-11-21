# render.py <proj> [--stills] [--only name,name] [--fps 30] [--scale 0.5] [--samples 20] [--from idx] [--to idx]
import sys, os, json, time, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
import bpy
from lib import *
import shots as S

proj = argv[0]
opt = {'stills': '--stills' in argv}
def arg(name, default, cast=str):
    return cast(argv[argv.index(name) + 1]) if name in argv else default
fps = arg('--fps', 30, int); scale = arg('--scale', 0.5, float); samples = arg('--samples', 20, int)
only = arg('--only', '', str); i0 = arg('--from', 0, int); i1 = arg('--to', 999, int)
tl = json.load(open(os.path.join(proj, 'timeline.json')))
shots = tl['shots']
outdir = os.path.join(proj, 'stills' if opt['stills'] else 'frames'); os.makedirs(outdir, exist_ok=True)
res = (int(1080 * scale) // 2 * 2, int(1920 * scale) // 2 * 2)

def kf(spec, t, u):
    if callable(spec): return spec(t, u)
    a, b = spec; e = ease(u)
    return dict(pos=lerpv(a['pos'], b['pos'], e), look=lerpv(a['look'], b['look'], e), fov=lerp(a.get('fov', 45), b.get('fov', a.get('fov', 45)), e))

total_frames = 0
for idx, sh in enumerate(shots):
    if idx < i0 or idx > i1: continue
    name = sh['scene']
    if only and name not in only.split(','): continue
    start, end = sh['start'], sh['end']
    if idx == len(shots) - 1: end = max(end, tl['duration'] + 0.7)
    dur = end - start
    random.seed(idx * 7 + 1)
    sc = reset(res=res, samples=samples, fps=fps)
    spec = S.SHOTS[name]({'dur': dur, 'index': idx})
    cam = camera(45)
    dof = spec.get('dof')
    if dof is not None:
        cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = dof[1]
    else:
        cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 5.6
    if spec.get('motion_blur'):
        pass
    # frame boundaries on the global 30fps timeline so cuts land exactly
    f0 = round(start * fps); f1 = round(end * fps)
    frames = list(range(f0, f1))
    if opt['stills']: frames = [f0 + int((f1 - f0) * 0.2), f0 + int((f1 - f0) * 0.8)]
    t_shot = time.time()
    for fi in frames:
        out = os.path.join(outdir, f'{fi:05d}.jpg') if not opt['stills'] else os.path.join(outdir, f'{idx:02d}_{name}_{fi:05d}.jpg')
        if not opt['stills'] and os.path.exists(out): continue
        t = fi / fps - start; u = clamp(t / dur)
        spec['update'](t, u)
        k = kf(spec['cam'], t, u)
        focus = dof[0] if (dof is not None and dof[0] is not None) else None
        look(cam, k['pos'], k['look'], k.get('fov', 45), focus)
        if spec.get('motion_blur'):
            # cheap velocity blur: shutter fraction via scene frame + keyframes not used; skip
            pass
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True)
        total_frames += 1
    print(f'SHOT {idx:02d} {name:16s} {len(frames):4d} frames {time.time() - t_shot:7.1f}s', flush=True)
print('DONE', total_frames, flush=True)
