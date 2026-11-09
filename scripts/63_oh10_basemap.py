"""Base map for the OH-10 tract map: roads, water and place names, drawn as SVG in the page itself (the shared
page cannot load map tiles from other sites). Writes data/processed/oh10/basemap.json.

Sources, all U.S. Census Bureau TIGERweb (public domain), clipped to the map's bounding box:
- Transportation layer 2 (primary roads: interstates and other limited-access highways), layer 6 (secondary
  roads: U.S. and state routes) and layer 8 (local roads), current TIGER.
- Hydro layer 1 (area water: rivers wide enough to map as areas, lakes, reservoirs); small ponds dropped.
- 2020 incorporated places (layer 26) and Census-designated places (layer 28): name and internal point, with
  2020 census population (P.L. 94-171) to decide which names show at full view.
Same projection as data/processed/oh10/geo.json.
"""
import json
import math
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent))
from common import PROC, RAW, cached, census, write_json  # noqa: E402

GEO = json.loads((PROC / "oh10" / "geo.json").read_text())
P = GEO["proj"]
BB = P["bbox"]
W, H = map(float, GEO["viewBox"].split()[2:])
BASE = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/{}/MapServer/{}/query?"


def xy(p):
    return ((p[0] - P["lon0"]) * P["k"] * P["sc"], (P["lat1"] - p[1]) * P["sc"])


def query(svc, layer, name, fields, offset=0.0001, geometry=True):
    feats, start = [], 0
    while True:
        q = dict(geometry=",".join(map(str, BB)), geometryType="esriGeometryEnvelope", inSR="4326",
                 spatialRel="esriSpatialRelIntersects", where="1=1", outFields=fields, outSR="4326",
                 returnGeometry="true" if geometry else "false", maxAllowableOffset=str(offset), geometryPrecision="5",
                 resultOffset=str(start), resultRecordCount="5000", f="geojson" if geometry else "json")
        j = json.loads(cached(RAW / "oh10" / "basemap" / f"{name}_{start}.json", BASE.format(svc, layer) + urlencode(q)))
        got = j["features"]
        feats += got
        if len(got) < 5000:
            return feats
        start += 5000


def lines(feats):
    for f in feats:
        g = f["geometry"]
        if not g:
            continue
        for ln in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]):
            yield f["properties"], [xy(p) for p in ln]


def inside_view(pts, pad=20):
    return any(-pad <= x <= W + pad and -pad <= y <= H + pad for x, y in pts)


def path(polys, closed=False):
    """Compact SVG path: absolute move, then relative steps, one decimal."""
    out = []
    for pts in polys:
        x0, y0 = round(pts[0][0], 1), round(pts[0][1], 1)
        seg = [f"M{x0:g},{y0:g}"]
        steps = []
        for x, y in pts[1:]:
            x, y = round(x, 1), round(y, 1)
            dx, dy = round(x - x0, 1), round(y - y0, 1)
            if dx or dy:
                steps.append(f"{dx:g},{dy:g}")
                x0, y0 = x, y
        if not steps:
            continue
        seg.append("l" + " ".join(steps))
        out.append("".join(seg) + ("z" if closed else ""))
    return "".join(out)


def area(pts):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


if __name__ == "__main__":
    out = {}
    route_pts = {}
    for key, layer, off in (("primary", 2, 0.0001), ("secondary", 6, 0.0001), ("local", 8, 0.00008)):
        polys = []
        for props, pts in lines(query("Transportation", layer, key, "NAME,RTTYP,MTFCC", off)):
            if len(pts) < 2 or not inside_view(pts):
                continue
            polys.append(pts)
            nm = (props.get("NAME") or "").replace("- ", "-").strip()
            if key in ("primary", "secondary") and props.get("RTTYP") in ("I", "U"):
                route_pts.setdefault(nm, []).append(pts)
        out[key] = path(polys)
        print(f"{key}: {len(polys)} lines, {len(out[key]) // 1024} KB")

    water = []
    for f in query("Hydro", 1, "water", "NAME", 0.0001):
        g = f["geometry"]
        for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            pts = [xy(p) for p in poly[0]]
            if area(pts) >= 4 and inside_view(pts):      # about 4 square map units; drops farm ponds
                water.append(pts)
    out["water"] = path(water, closed=True)
    print(f"water: {len(water)} areas, {len(out['water']) // 1024} KB")

    # route labels: one per interstate or U.S. route, at the middle of its longest piece inside the view
    labels = []
    for nm, pieces in route_pts.items():
        if not nm.startswith(("I-", "US Hwy")):
            continue
        best = max(pieces, key=lambda ps: sum(math.dist(a, b) for a, b in zip(ps, ps[1:]) if 0 <= a[0] <= W and 0 <= a[1] <= H))
        vis = [p for p in best if 15 <= p[0] <= W - 15 and 15 <= p[1] <= H - 15]
        if not vis:
            continue
        x, y = vis[len(vis) // 2]
        labels.append({"t": nm.replace("US Hwy ", "US "), "x": round(x, 1), "y": round(y, 1), "kind": "route"})

    # place names: 2020 incorporated places and CDPs whose internal point is in view
    pops = {r["place"]: int(r["P1_001N"]) for r in
            census("2020/dec/pl", {"get": "NAME,P1_001N", "for": "place:*", "in": "state:39"}, "oh10/pl2020_place_pop.json")}
    seen = set()
    for layer, nm in ((26, "places_inc"), (28, "places_cdp")):
        q = BASE.format("tigerWMS_Census2020", layer) + urlencode(dict(
            where="STATE='39'", geometry=",".join(map(str, BB)), geometryType="esriGeometryEnvelope", inSR="4326",
            spatialRel="esriSpatialRelIntersects", outFields="PLACE,BASENAME,INTPTLAT,INTPTLON", returnGeometry="false", f="json"))
        for f in json.loads(cached(RAW / "oh10" / "basemap" / f"{nm}.json", q))["features"]:
            a = f["attributes"]
            x, y = xy((float(a["INTPTLON"]), float(a["INTPTLAT"])))
            if not (10 <= x <= W - 10 and 10 <= y <= H - 10) or a["PLACE"] in seen:
                continue
            seen.add(a["PLACE"])
            pop = pops.get(a["PLACE"], 0)
            labels.append({"t": a["BASENAME"], "x": round(x, 1), "y": round(y, 1), "pop": pop,
                           "kind": "city" if pop >= 25000 else "town" if pop >= 5000 else "small"})
    # keep labels whose anchor is inside one of the three counties (the street layer is clipped to them)
    rings = []
    for f in json.loads((RAW / "oh10" / "tiger_counties.geojson").read_text())["features"]:
        g = f["geometry"]
        for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            rings.append([xy(p) for p in poly[0]])

    def inside(x, y, ring):
        c = False
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c
    labels = [l for l in labels if any(inside(l["x"], l["y"], r) for r in rings)]
    out["labels"] = sorted(labels, key=lambda l: -l.get("pop", 10**9))
    print("labels:", len(labels), [l["t"] for l in out["labels"][:12]])
    out["source"] = "U.S. Census Bureau TIGERweb: roads, area water, 2020 places"
    write_json("oh10/basemap.json", out)
    print("basemap KB:", len(json.dumps(out)) // 1024)
