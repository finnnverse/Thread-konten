"""Satellite tile source (Web Mercator, 256 px tiles) with disk + memory cache.

Default source: EOX Sentinel-2 cloudless 2016 (CC BY 4.0, commercial use allowed with attribution):
  "Sentinel-2 cloudless - https://s2maps.eu by EOX IT Services GmbH
   (Contains modified Copernicus Sentinel data 2016)"
"""
import os, io, threading, urllib.request, ssl, time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image

S2_2016 = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg"
ATTRIBUTION = ("Satellite imagery: Sentinel-2 cloudless 2016 - https://s2maps.eu by EOX IT Services GmbH "
               "(contains modified Copernicus Sentinel data 2016), CC BY 4.0. "
               "Borders: Natural Earth (public domain).")
OFFMAP = np.array([25, 25, 25], np.uint8)  # #191919 measured "outside map plane" colour


def _ssl_ctx():
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca):
        return ssl.create_default_context(cafile=ca)
    return ssl.create_default_context()


class TileSource:
    def __init__(self, cache_dir, url=S2_2016, max_zoom=12, mem_tiles=6000):
        self.url, self.cache_dir, self.max_zoom = url, cache_dir, max_zoom
        os.makedirs(cache_dir, exist_ok=True)
        self.mem = OrderedDict(); self.mem_max = mem_tiles
        self.lock = threading.Lock(); self.ctx = _ssl_ctx()
        self.offmap = np.broadcast_to(OFFMAP, (256, 256, 3)).copy()

    def _path(self, z, x, y):
        return os.path.join(self.cache_dir, str(z), str(x), f"{y}.jpg")

    def _download(self, z, x, y):
        p = self._path(z, x, y)
        if os.path.exists(p):
            return p
        os.makedirs(os.path.dirname(p), exist_ok=True)
        req = urllib.request.Request(self.url.format(z=z, x=x, y=y), headers={"User-Agent": "map-video-engine/1.0"})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=30, context=self.ctx) as r:
                    data = r.read()
                tmp = p + ".tmp"; open(tmp, "wb").write(data); os.replace(tmp, p)
                return p
            except Exception:
                time.sleep(1.5 * (attempt + 1))
        return None

    def get(self, z, x, y):
        n = 1 << z
        if y < 0 or y >= n:
            return self.offmap
        x %= n
        key = (z, x, y)
        with self.lock:
            if key in self.mem:
                self.mem.move_to_end(key); return self.mem[key]
        p = self._download(z, x, y)
        arr = self.offmap if p is None else np.asarray(Image.open(p).convert("RGB"))
        with self.lock:
            self.mem[key] = arr
            while len(self.mem) > self.mem_max:
                self.mem.popitem(last=False)
        return arr

    def prefetch(self, keys, workers=16):
        keys = [(z, x % (1 << z), y) for z, x, y in keys if 0 <= y < (1 << z)]
        todo = [k for k in set(keys) if not os.path.exists(self._path(*k))]
        if todo:
            with ThreadPoolExecutor(workers) as ex:
                list(ex.map(lambda k: self._download(*k), todo))
        return len(todo)

    def mosaic(self, z, tx0, ty0, tx1, ty1):
        """Tiles [tx0..tx1] x [ty0..ty1] inclusive -> uint8 array."""
        w, h = tx1 - tx0 + 1, ty1 - ty0 + 1
        out = np.empty((h * 256, w * 256, 3), np.uint8)
        for j, ty in enumerate(range(ty0, ty1 + 1)):
            for i, tx in enumerate(range(tx0, tx1 + 1)):
                out[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = self.get(z, tx, ty)
        return out
