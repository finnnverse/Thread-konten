"""Smooth camera.

Keys: (t, lon, lat, width_km, roll_deg, tilt_deg). Each parameter is interpolated with a
monotone cubic (PCHIP) in time -> C1-continuous velocity, no overshoot, no jumps.
Zoom is interpolated in log(width) so zoom speed feels constant. Position is interpolated in
Mercator space (what the viewer sees).

A key may set hold=True: the camera then *stops* there (velocity 0) — use sparingly; the
reference style never fully stops (always a slow drift).
"""
import math
import numpy as np
from scipy.interpolate import PchipInterpolator
from .geo import merc, unmerc, width_km_to_norm


class Camera:
    def __init__(self, keys, W=1080, H=1920):
        keys = sorted(keys, key=lambda k: k["t"])
        self.W, self.H = W, H
        t = np.array([k["t"] for k in keys], float)
        lon = np.unwrap(np.radians([k["lon"] for k in keys]))
        lon = np.degrees(lon)
        mx, my = merc(lon, [k["lat"] for k in keys])
        logw = np.log([width_km_to_norm(k["width_km"], k["lat"]) for k in keys])
        roll = np.array([k.get("roll", 0.0) for k in keys], float)
        tilt = np.array([k.get("tilt", 10.0) for k in keys], float)
        if len(t) == 1:
            t = np.array([t[0], t[0] + 1]); mx, my, logw, roll, tilt = [np.repeat(a, 2) for a in (mx, my, logw, roll, tilt)]
        self.t0, self.t1 = t[0], t[-1]
        self.f = {n: PchipInterpolator(t, v) for n, v in
                  dict(mx=mx, my=my, logw=logw, roll=roll, tilt=tilt).items()}

    def state(self, t):
        t = min(max(t, self.t0), self.t1)
        return {n: float(f(t)) for n, f in self.f.items()}

    def matrix(self, t, extra_zoom=1.0, shake=(0.0, 0.0)):
        """3x3 homography: normalized mercator (x,y,1) -> screen px."""
        s = self.state(t)
        scale = self.W / math.exp(s["logw"]) * extra_zoom          # px per normalized unit
        a = math.radians(s["roll"])
        c, si = math.cos(a), math.sin(a)
        A = np.array([[scale * c, -scale * si, 0], [scale * si, scale * c, 0], [0, 0, 1.0]])
        T = np.array([[1, 0, -s["mx"]], [0, 1, -s["my"]], [0, 0, 1.0]])
        f = self.H * 1.25                                            # focal length (px)
        k = -math.tan(math.radians(s["tilt"])) / f
        P = np.array([[1, 0, 0], [0, 1, 0], [0, k, 1.0]])
        C = np.array([[1, 0, self.W / 2 + shake[0]], [0, 1, self.H * 0.5 + shake[1]], [0, 0, 1.0]])
        return C @ P @ A @ T, scale

    @staticmethod
    def project(M, x, y):
        p = M @ np.vstack([np.asarray(x, float), np.asarray(y, float), np.ones(np.size(x))])
        w = np.where(np.abs(p[2]) < 1e-9, 1e-9, p[2])
        return p[0] / w, p[1] / w

    def geo_to_screen(self, t, lon, lat):
        M, _ = self.matrix(t)
        s = self.state(t)
        clon = unmerc(s["mx"], s["my"])[0]
        lon = np.asarray(lon, float)
        lon = lon + 360.0 * np.round((clon - lon) / 360.0)
        x, y = merc(lon, lat)
        return self.project(M, x, y)

    def px_per_km(self, t):
        s = self.state(t)
        lat = unmerc(s["mx"], s["my"])[1]
        _, scale = self.matrix(t)
        return scale / (40075.016686 * max(0.05, math.cos(math.radians(lat))))
