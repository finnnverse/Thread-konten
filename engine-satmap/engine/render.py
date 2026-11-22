import os, sys, math, subprocess, importlib.util, time, numpy as np
from PIL import Image
proj = os.path.abspath(sys.argv[1]); mode = sys.argv[2]
spec = importlib.util.spec_from_file_location('video', os.path.join(proj, 'video.py')); V = importlib.util.module_from_spec(spec); spec.loader.exec_module(V)
W, H, FPS = V.W, V.H, V.FPS
def to_img(arr): return Image.fromarray(arr[..., [2, 1, 0]].copy())
if mode == 'stills':
    ts = [float(x) for x in sys.argv[3].split(',')]; ims = []
    for t in ts:
        t0 = time.time(); im = to_img(V.frame(t)); print(f'{t:.2f} {time.time()-t0:.2f}s', flush=True)
        ims.append(im.resize((270, 480)))
    cols = 8; rows = math.ceil(len(ims) / cols)
    sh = Image.new('RGB', (cols * 270, rows * 480))
    for i, im in enumerate(ims): sh.paste(im, ((i % cols) * 270, (i // cols) * 480))
    sh.save(os.path.join(proj, sys.argv[4] if len(sys.argv) > 4 else 'contact.jpg'), quality=88)
elif mode == 'one':
    t = float(sys.argv[3]); to_img(V.frame(t)).save(os.path.join(proj, f'still_{t:.2f}.jpg'), quality=90)
elif mode == 'seg':
    i0, i1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(i0, i1):
        p.stdin.write(V.frame(i / FPS).tobytes())
        if (i - i0) % 60 == 0: print(f'{out} {i-i0}/{i1-i0} {time.time()-t0:.0f}s', flush=True)
    p.stdin.close(); p.wait(); print('done', out, flush=True)
elif mode == 'full':
    n = int(math.ceil(V.TAIL * FPS)); k = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    seg = os.path.join(proj, 'seg'); os.makedirs(seg, exist_ok=True)
    b = [round(n * j / k) for j in range(k + 1)]; procs = []
    for j in range(k):
        out = os.path.join(seg, f'{j:02d}.mp4')
        procs.append(subprocess.Popen([sys.executable, '-I', __file__, proj, 'seg', str(b[j]), str(b[j + 1]), out]))
    for p in procs: p.wait()
    with open(os.path.join(seg, 'list.txt'), 'w') as f:
        for j in range(k): f.write(f"file '{j:02d}.mp4'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(seg, 'list.txt'), '-c', 'copy', os.path.join(proj, 'video_silent.mp4')])
    print('FULL DONE')
