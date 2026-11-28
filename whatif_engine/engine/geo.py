"""Geography helpers: Web Mercator maths + Natural Earth country geometry."""
import json, math, os
import numpy as np

EARTH_KM = 40075.016686


def merc(lon, lat):
    """lon/lat (deg) -> normalized Web Mercator (0..1, y down)."""
    lon = np.asarray(lon, float); lat = np.clip(np.asarray(lat, float), -85.05112878, 85.05112878)
    x = (lon + 180.0) / 360.0
    y = (1.0 - np.log(np.tan(np.radians(lat)) + 1.0 / np.cos(np.radians(lat))) / math.pi) / 2.0
    return x, y


def unmerc(x, y):
    lon = np.asarray(x) * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * np.asarray(y)))))
    return lon, lat


def width_km_to_norm(width_km, lat):
    """Ground width (km) at latitude -> width in normalized mercator units."""
    return width_km / (EARTH_KM * max(0.05, math.cos(math.radians(lat))))


class Countries:
    """Natural Earth admin-0. Lookup by ISO_A3 / ADM0_A3 / NAME (case-insensitive)."""

    def __init__(self, data_dir, res="10m", layer="admin_0_countries"):
        """layer: 'admin_0_countries' (default) or 'lakes' (ne_10m_lakes.geojson, lookup by `name`)."""
        p = os.path.join(data_dir, f"ne_{res}_{layer}.geojson")
        self.features = json.load(open(p))["features"]
        self._cache = {}

    def find(self, key):
        k = key.lower()
        for f in self.features:
            pr = f["properties"]
            for fld in ("ADM0_A3", "ISO_A3", "NAME", "NAME_LONG", "ADMIN", "NAME_EN", "name", "name_alt"):
                v = pr.get(fld)
                if isinstance(v, str) and v.lower() == k:
                    return f
        raise KeyError(key)

    def rings(self, key, exclude_bbox=None):
        """-> list of dict(lon, lat, hole, area_deg2, mainland) ; exclude_bbox=(lon0,lat0,lon1,lat1) drops parts inside it
        (e.g. Alaska/Hawaii for the contiguous US)."""
        ck = (key, exclude_bbox)
        if ck in self._cache:
            return self._cache[ck]
        g = self.find(key)["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        out = []
        for poly in polys:
            ext = np.asarray(poly[0], float)
            if exclude_bbox:
                cx, cy = ext[:, 0].mean(), ext[:, 1].mean()
                x0, y0, x1, y1 = exclude_bbox
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    continue
            for i, ring in enumerate(poly):
                r = np.asarray(ring, float)
                x, y = r[:, 0], r[:, 1]
                area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
                out.append(dict(lon=x, lat=y, hole=i > 0, area=area))
        big = max((r["area"] for r in out if not r["hole"]), default=0)
        for r in out:
            r["mainland"] = (not r["hole"]) and r["area"] >= 0.02 * big
        self._cache[ck] = out
        return out
