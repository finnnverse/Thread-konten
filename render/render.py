"""Render frames [a,b) of the Egypt explainer to an H.264 chunk.  usage: render.py a b out.mp4 | --still t out.png"""
import os, sys, math, subprocess, time
import numpy as np, cv2
from PIL import Image
from engine import *
import scene as S
import elements as E

TEX = os.environ['TEX_DIR']
base = Tex(f'{TEX}/base.png', f'{TEX}/base.txt', alpha=False)
_P = [
    ('p1_egypt_z8', 45),
    ('p2_delta_z10', 182),
    ('p2_aswan_z10', 182),
    ('p3_cairo_z13', 728),
    ('p3_suez_z12', 728),
    ('p3_aswan_z12', 728),
    ('p3_abusimbel_z13', 728),
]
patches = [Tex(f'{TEX}/{n}.png', f'{TEX}/{n}.txt', prev_ppd=p) for n, p in _P if os.path.exists(f'{TEX}/{n}.png')]

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - .32 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2)[..., None].astype(np.float32)
del yy, xx
FLIGHTS = S.flight_windows()
_ty = np.arange(H, dtype=np.float32)
TS = np.clip((0.30 * H - _ty) / (0.30 * H), 0, 1)[:, None, None] ** 1.3  # blur weight, strongest at the top edge


def tiltshift(fr):
    small = cv2.resize(fr, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bl = cv2.resize(cv2.GaussianBlur(small, (0, 0), 2.2), (W, H), interpolation=cv2.INTER_LINEAR)
    return fr * (1 - TS) + bl * TS


def bloom(fr):
    small = cv2.resize(fr, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 205, 0, None)
    b = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 6), (W, H), interpolation=cv2.INTER_LINEAR)
    return np.minimum(fr + b * .18, 255)


def cam_speed(t):
    c0, c1 = S.cam_at(t), S.cam_at(t + 1 / 30)
    x, y = c0.plane_to_px(c1.cx, c1.cy)
    return math.hypot(x - W / 2, y - H / 2) + W / 2 * abs(math.log(c1.vw / c0.vw)) + abs(c1.rot - c0.rot) * 15


def frame(t):
    if t >= S.END0:
        fr = S.endscreen(t)
        return fr
    if S.DIAG[0] <= t < S.DIAG[1]:
        fr = S.diagram(t)
        # counter inside diagram
        u = t - S.DIAG[0]
        if u > .9:
            c = DIAG_COUNTER
            c.draw(fr, None, t)
        return fr
    cam = S.cam_at(t)
    sp = cam_speed(t)
    if sp > 18:  # motion blur, shutter 1/60 -> 5 sub-frames over half a frame interval
        n = int(min(11, max(5, sp / 10)))
        acc = None
        for i in range(n):
            ts = t + (i / (n - 1) - .5) * (1 / 60)
            m = render_map(S.cam_at(ts), base, patches)
            acc = m if acc is None else acc + m
        fr = acc / n
    else:
        fr = render_map(cam, base, patches)
    fr = tiltshift(fr) * VIG
    for e in S.EL:
        if e.geo and e.active(t): e.draw(fr, cam, t)
    fr = bloom(fr)
    for e in S.EL:
        if not e.geo and e.active(t): e.draw(fr, cam, t)
    return fr


DIAG_COUNTER = S.DIAG_COUNTER


def badge_overlay(fr, t):
    return fr


if __name__ == '__main__':
    if sys.argv[1] == '--still':
        for t in map(float, sys.argv[2].split(',')):
            fr = frame(t)
            Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).save(sys.argv[3].replace('%', f'{t:07.2f}'))
        sys.exit()
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', '30', out], stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(a, b):
        fr = frame(f / 30)
        p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
        if (f - a) % 60 == 0: print(f'{out} {f} {time.time() - t0:.0f}s', flush=True)
    p.stdin.close(); p.wait()
    print('done', out, time.time() - t0, flush=True)
