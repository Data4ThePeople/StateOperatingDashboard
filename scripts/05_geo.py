"""Ohio county outlines as SVG paths, from us-atlas counties-10m (Census cartographic boundary files, 1:10m, as TopoJSON).

Projection: equirectangular scaled by cos(40.3 deg), which keeps Ohio's shape within a percent or two.
Output: data/processed/geo.json  {"viewBox": "...", "counties": {fips: {"name", "d", "cx", "cy"}}, "outline": d}
"""
import json
import math

from common import RAW, STATE, cached, write_json

URL = "https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json"
W = 600


def decode_arcs(topo):
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    out = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        out.append(pts)
    return out


def ring(arcs, idx):
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts


if __name__ == "__main__":
    topo = json.loads(cached(RAW / "geo" / "counties-10m.json", URL))
    arcs = decode_arcs(topo)
    geoms = [g for g in topo["objects"]["counties"]["geometries"] if g["id"].startswith(STATE)]
    assert len(geoms) == 88, len(geoms)
    polys = {}
    for g in geoms:
        rings = g["arcs"] if g["type"] == "Polygon" else [r for p in g["arcs"] for r in p]
        polys[g["id"]] = (g["properties"]["name"], [ring(arcs, r) for r in rings])
    k = math.cos(math.radians(40.3))
    allpts = [p for _, rs in polys.values() for r in rs for p in r]
    minx = min(p[0] for p in allpts) * k; maxx = max(p[0] for p in allpts) * k
    miny = min(p[1] for p in allpts); maxy = max(p[1] for p in allpts)
    s = W / (maxx - minx)
    H = round((maxy - miny) * s)

    def xy(p):
        return (p[0] * k - minx) * s, (maxy - p[1]) * s

    out = {}
    for fips, (name, rs) in sorted(polys.items()):
        d = ""
        area_sum = cxs = cys = 0.0
        for r in rs:
            q = [xy(p) for p in r]
            d += "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in q) + "Z"
            for (x1, y1), (x2, y2) in zip(q, q[1:] + q[:1]):
                c = x1 * y2 - x2 * y1
                area_sum += c; cxs += (x1 + x2) * c; cys += (y1 + y2) * c
        out[fips] = {"name": name, "d": d, "cx": round(cxs / (3 * area_sum), 1), "cy": round(cys / (3 * area_sum), 1)}
    write_json("geo.json", {"viewBox": f"0 0 {W} {H}", "counties": out})
    print(len(out), "counties; viewBox", W, H)
