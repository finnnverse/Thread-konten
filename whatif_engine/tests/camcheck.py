"""Measure camera motion per frame of a rendered video (map only: caption strip & centre masked lightly)
and report jumps: |v[i]-v[i-1]| relative to local speed."""
import sys, cv2, numpy as np, json
cap = cv2.VideoCapture(sys.argv[1]); orb = cv2.ORB_create(1500)
mask = np.full((640, 360), 255, np.uint8); mask[490:540] = 0; mask[60:90] = 0
prev = None; v = []
while True:
    ok, f = cap.read()
    if not ok: break
    g = cv2.cvtColor(cv2.resize(f, (360, 640), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    kp, de = orb.detectAndCompute(g, mask); r = None
    if prev is not None and de is not None and prev[1] is not None:
        m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(prev[1], de)
        if len(m) > 20:
            a = np.float32([prev[0][x.queryIdx].pt for x in m]); b = np.float32([kp[x.trainIdx].pt for x in m])
            M, inl = cv2.estimateAffinePartial2D(a, b, ransacReprojThreshold=1.5)
            if M is not None and inl.sum() > 40:
                c = M @ np.array([180, 320, 1.0]); r = [(c[0] - 180) * 3, (c[1] - 320) * 3, float(np.hypot(M[0, 0], M[1, 0]))]
    v.append(r); prev = (kp, de)
fps = 60; bad = []
for i in range(2, len(v)):
    if v[i] is None or v[i - 1] is None: continue
    d = np.hypot(v[i][0] - v[i - 1][0], v[i][1] - v[i - 1][1]); sp = np.hypot(*v[i][:2])
    dz = abs(np.log(v[i][2]) - np.log(v[i - 1][2]))
    if d > max(3.0, 0.35 * sp) or dz > 0.006: bad.append((round(i / fps, 3), round(sp, 1), round(d, 1), round(dz, 4)))
sp = [np.hypot(*x[:2]) for x in v if x]
print(f"frames {len(v)} measured {len(sp)}  max speed {max(sp):.1f}px/frame(1080p)  jump-candidates {len(bad)}")
for b in bad[:40]: print("  t,speed,dv,dzoom:", b)
