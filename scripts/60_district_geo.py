"""A congressional district's 2020 census tracts, their outlines, and a place name for each.
Writes data/processed/<key>/geo.json. Run: .venv/bin/python scripts/60_district_geo.py <key> (keys in districts.py)

- District: a block assignment file (see districts.py: the Ohio Redistricting Commission's file for OH-10, the
  Census Bureau's 119th Congress file for IL-6), joined to 2020 census block population (P.L. 94-171, P1_001N).
  A tract is in the district when most of its 2020 population is. The district's total is checked against the
  official 2020 count.
- Tract outlines: Census TIGERweb, 2020 census tracts, simplified by the server (about 40 meters).
- Place names: a tract takes the name of the city, village or Census-designated place holding at least half of
  its 2020 population (Census 2020 block assignment file for places). Otherwise it takes the township (county
  subdivision, TIGERweb 2020) that contains the tract's internal point.
"""
import io
import json
import math
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import districts  # noqa: E402
from common import RAW, census, cached, write_json  # noqa: E402

CFG = districts.get(sys.argv)
KEY, STF = CFG["key"], CFG["state"]
ORC = "https://redistricting.ohio.gov/api/public/districtmaps/430/download"
CD119 = "https://www2.census.gov/programs-surveys/decennial/rdo/mapping-files/2025/119-congressional-district-befs/cd119.zip"
BAF_PLACE = f"https://www2.census.gov/geo/docs/maps-data/data/baf2020/BlockAssign_ST{STF}_{CFG['st']}.zip"
TIGER = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/{}/query?"
# district outline: TIGERweb Current (January 1, 2026 vintage), layer 54 = 120th Congressional Districts
CD_LINE = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/54/query?"
W = 600
PAD = 0.06          # "bbox" maps: margin around the district, as a share of its width and height


def district_blocks():
    """DataFrame of Block (15-digit 2020 block GEOID) and cd (district number as text) for the whole state."""
    if CFG["baf"] == "orc430":
        z = zipfile.ZipFile(io.BytesIO(cached(RAW / "oh10" / "orc_430.zip", ORC)))
        name = [n for n in z.namelist() if n.endswith("BAF.xlsx")]
        assert name == ["October 31 2025 CD BAF.xlsx"], z.namelist()
        b = pd.read_excel(io.BytesIO(z.read(name[0])), dtype=str).rename(columns={"DistrictID:1": "cd"})
        assert len(b) == 276428 and b.Block.str.len().eq(15).all()   # every 2020 Ohio block
        return b
    cached(RAW / "census_cd119" / "cd119.zip", CD119)
    z = zipfile.ZipFile(RAW / "census_cd119" / "cd119.zip")
    b = pd.read_csv(z.open("NationalCD119.txt"), dtype=str).rename(columns={"GEOID": "Block", "CDFP": "cd"})
    b = b[b.Block.str[:2] == STF].reset_index(drop=True)
    assert b.Block.str.len().eq(15).all() and b.Block.is_unique
    return b


def block_pop(counties):
    rows = []
    for c in counties:
        for r in census("2020/dec/pl", {"get": "P1_001N", "for": "block:*", "in": f"state:{STF} county:{c} tract:*"},
                        f"{KEY}/pl2020_block_{c}.json"):
            rows.append((r["state"] + r["county"] + r["tract"] + r["block"], int(r["P1_001N"])))
    return pd.DataFrame(rows, columns=["Block", "pop"])


def tidy(name):
    """'Kettering city' -> 'Kettering'; 'Washington township' -> 'Washington Township'."""
    for suf in (" city", " village", " CDP"):
        if name.endswith(suf):
            return name[: -len(suf)]
    return name.replace(" township", " Township")


def place_of_block():
    z = zipfile.ZipFile(io.BytesIO(cached(RAW / KEY / BAF_PLACE.rsplit("/", 1)[1], BAF_PLACE)))
    m = pd.read_csv(z.open(f"BlockAssign_ST{STF}_{CFG['st']}_INCPLACE_CDP.txt"), sep="|", dtype=str).rename(columns={"BLOCKID": "Block"})
    names = {r["place"]: tidy(r["NAME"].split(",")[0])
             for r in census("2020/dec/pl", {"get": "NAME", "for": "place:*", "in": f"state:{STF}"}, f"{KEY}/pl2020_places.json")}
    return m, names


def inside(x, y, ring):
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def tiger(layer, where, name, fields="GEOID,COUNTY", geometry=True, fmt="geojson", envelope=None):
    q = dict(where=where, outFields=fields, returnGeometry="true" if geometry else "false", outSR="4326",
             maxAllowableOffset="0.0004", geometryPrecision="5", f=fmt)
    if envelope:
        q.update(geometry=",".join(map(str, envelope)), geometryType="esriGeometryEnvelope", inSR="4326",
                 spatialRel="esriSpatialRelIntersects")
    j = json.loads(cached(RAW / KEY / name, TIGER.format(layer) + urlencode(q)))
    assert not j.get("exceededTransferLimit") and not j.get("properties", {}).get("exceededTransferLimit"), name
    return j


def rings(geom):
    return geom["coordinates"] if geom["type"] == "Polygon" else [r for p in geom["coordinates"] for r in p]


if __name__ == "__main__":
    b = district_blocks()
    b["county"] = b.Block.str[2:5]
    b["tract"] = b.Block.str[:11]
    cos = sorted(b[b.cd == CFG["cd"]].county.unique())
    cname = {r["county"]: r["NAME"].split(" County,")[0]
             for r in census("2020/dec/pl", {"get": "NAME", "for": "county:*", "in": f"state:{STF}"}, f"{KEY}/pl2020_counties.json")}
    print("district counties:", {c: cname[c] for c in cos})
    m = b[b.county.isin(cos)].merge(block_pop(cos), on="Block", how="left")
    assert m["pop"].notna().all()
    m["in10"] = m.cd == CFG["cd"]
    plc, plc_name = place_of_block()
    m = m.merge(plc, on="Block", how="left")
    # townships: the county subdivision whose outline holds the tract's internal point
    mcds = []
    for c in cos:
        for f in tiger(20, f"STATE='{STF}' AND COUNTY='{c}'", f"tiger_cousub_{c}.geojson", fields="GEOID,NAME,COUNTY")["features"]:
            g = f["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            mcds.append((tidy(f["properties"]["NAME"]), polys))
    tpts = {}
    for c in cos:
        for f in tiger(6, f"STATE='{STF}' AND COUNTY='{c}'", f"tiger_tractpts_{c}.json", fields="GEOID,INTPTLAT,INTPTLON",
                       geometry=False, fmt="json")["features"]:
            a = f["attributes"]
            tpts[a["GEOID"]] = (float(a["INTPTLON"]), float(a["INTPTLAT"]))

    def township(t):
        x, y = tpts[t]
        hits = [n for n, polys in mcds if any(inside(x, y, [tuple(p) for p in poly[0]]) for poly in polys)]
        return hits[0] if hits else None

    tracts = {}
    for t, g in m.groupby("tract"):
        pop, pop10 = int(g["pop"].sum()), int(g.loc[g.in10, "pop"].sum())
        rec = {"county": cname[t[2:5]], "pop2020": pop, "pop2020_in_district": pop10,
               "in_district": pop > 0 and pop10 / pop > 0.5}
        if CFG["context"] == "counties" or pop10 > 0:          # names are shown only for district tracts
            by = g.dropna(subset=["PLACEFP"]).groupby("PLACEFP")["pop"].sum().sort_values(ascending=False)
            if len(by) and pop and by.iloc[0] / pop >= 0.5:
                place = plc_name[by.index[0]]
            else:
                place = township(t) or f"{cname[t[2:5]]} County"
            rec.update(place=place, label=f"{place}, tract {int(t[5:9])}" + (f".{t[9:]}" if t[9:] != "00" else ""))
        tracts[t] = rec
    total = int(m.loc[m.in10, "pop"].sum())
    assert total == CFG["pop2020"], (total, CFG["pop2020"])
    split = {t: v for t, v in tracts.items() if 0 < v["pop2020_in_district"] < v["pop2020"]}
    ins = sorted(t for t, v in tracts.items() if v["in_district"])
    print(f"2020 population {total:,} (official {CFG['pop2020']:,}); tracts in district: {len(ins)}; split tracts: " +
          "; ".join(f"{t} {v['pop2020_in_district']}/{v['pop2020']} {'in' if v['in_district'] else 'out'}" for t, v in split.items()))

    # outlines
    feats = []
    for c in cos:
        feats += tiger(6, f"STATE='{STF}' AND COUNTY='{c}'", f"tiger_tracts_{c}.geojson")["features"]
    geoids = {f["properties"]["GEOID"] for f in feats}
    assert geoids == set(tracts), (len(geoids), len(tracts), sorted(geoids ^ set(tracts))[:5])
    if CFG["context"] == "counties":
        # all tracts of the district's counties (the outside part is drawn gray), map fitted to them
        allpts = [p for f in feats for r in rings(f["geometry"]) for p in r]
        lon0, lon1 = min(p[0] for p in allpts), max(p[0] for p in allpts)
        lat0, lat1 = min(p[1] for p in allpts), max(p[1] for p in allpts)
        cfeat = tiger(82, f"STATE='{STF}' AND COUNTY IN ({','.join(repr(c) for c in cos)})", "tiger_counties.geojson")["features"]
    else:
        # the district plus a margin; every tract touching that box is drawn, in any county
        pts = [p for f in feats if tracts[f["properties"]["GEOID"]]["in_district"] for r in rings(f["geometry"]) for p in r]
        lon0, lon1 = min(p[0] for p in pts), max(p[0] for p in pts)
        lat0, lat1 = min(p[1] for p in pts), max(p[1] for p in pts)
        dx, dy = (lon1 - lon0) * PAD, (lat1 - lat0) * PAD
        lon0, lon1, lat0, lat1 = lon0 - dx, lon1 + dx, lat0 - dy, lat1 + dy
        env = [lon0, lat0, lon1, lat1]
        near = tiger(6, f"STATE='{STF}'", "tiger_tracts_bbox.geojson", fields="GEOID,COUNTY", envelope=env)["features"]
        keep = {f["properties"]["GEOID"] for f in feats if tracts[f["properties"]["GEOID"]]["in_district"]}
        keep |= {f["properties"]["GEOID"] for f in near}
        byid = {f["properties"]["GEOID"]: f for f in feats + near}
        feats = [byid[t] for t in sorted(keep)]
        for t in keep - set(tracts):
            tracts[t] = {"county": cname[t[2:5]], "pop2020": None, "pop2020_in_district": 0, "in_district": False}
        tracts = {t: tracts[t] for t in keep}
        cfeat = tiger(82, f"STATE='{STF}'", "tiger_counties_bbox.geojson", envelope=env)["features"]
    k = math.cos(math.radians((lat0 + lat1) / 2))
    sc = W / ((lon1 - lon0) * k)
    H = round((lat1 - lat0) * sc)
    xy = lambda p: (round((p[0] - lon0) * k * sc, 1), round((lat1 - p[1]) * sc, 1))

    def path(geom):
        return "".join("M" + "L".join(f"{x},{y}" for x, y in map(xy, r)) + "Z" for r in rings(geom))

    out = {}
    for f in feats:
        t = f["properties"]["GEOID"]
        pts = [xy(p) for p in rings(f["geometry"])[0]]
        out[t] = dict(tracts[t], d=path(f["geometry"]),
                      cx=round(sum(p[0] for p in pts) / len(pts), 1), cy=round(sum(p[1] for p in pts) / len(pts), 1))
    counties = {f["properties"]["GEOID"]: {"name": cname[f["properties"]["COUNTY"]], "d": path(f["geometry"])} for f in cfeat}
    if CFG["context"] == "bbox":
        # county name: on the gray tract of that county farthest from the district's middle, inside the view
        mx = sum(out[t]["cx"] for t in ins) / len(ins)
        my = sum(out[t]["cy"] for t in ins) / len(ins)
        for g, c in counties.items():
            cand = [v for v in out.values() if not v["in_district"] and v["county"] == c["name"]
                    and 60 <= v["cx"] <= W - 60 and 20 <= v["cy"] <= H - 20]
            best = max(cand, key=lambda v: math.hypot(v["cx"] - mx, v["cy"] - my), default=None)
            c["lx"], c["ly"] = (best["cx"], best["cy"]) if best else (None, None)
    line = None
    if CFG.get("outline"):
        q = dict(where=f"GEOID='{STF}{CFG['cd']}'", outFields="GEOID,CDSESSN", returnGeometry="true", outSR="4326",
                 maxAllowableOffset="0.0002", geometryPrecision="5", f="geojson")
        lf = json.loads(cached(RAW / KEY / "tiger_cd120.geojson", CD_LINE + urlencode(q)))["features"]
        assert len(lf) == 1, len(lf)
        line = path(lf[0]["geometry"])
        # check: the outline should hold the internal point of every tract that is wholly inside the district, and
        # of none that has no district residents
        lrings = [[xy(p) for p in r] for r in rings(lf[0]["geometry"])]
        def held(t):
            x, y = xy(tpts[t])
            return sum(inside(x, y, r) for r in lrings) % 2 == 1
        whole = [t for t, v in tracts.items() if v["pop2020"] and v["pop2020_in_district"] == v["pop2020"]]
        none = [t for t, v in tracts.items() if v["pop2020"] and v["pop2020_in_district"] == 0 and t in tpts]
        bad = [t for t in whole if not held(t)] + [t for t in none if held(t)]
        print(f"outline check: {len(whole)} whole tracts, {len(none)} outside tracts, {len(bad)} disagree {bad[:5]}")
        assert len(bad) <= 2, bad
    cpop = {}
    for t, v in tracts.items():
        if v["pop2020"] is not None:
            p = cpop.setdefault(v["county"], [0, 0])
            p[0] += v["pop2020"]
            p[1] += v["pop2020_in_district"]
    src = ("Ohio Redistricting Commission block assignment file (map adopted Oct. 31, 2025)" if CFG["baf"] == "orc430"
           else "Census Bureau block equivalency file, 119th Congress")
    write_json(f"{KEY}/geo.json", {"viewBox": f"0 0 {W} {H}", "tracts": out, "counties": counties,
                                   "proj": {"lon0": lon0, "lat1": lat1, "k": k, "sc": sc, "bbox": [lon0, lat0, lon1, lat1]},
                                   "district_pop2020": total, "split": split, "context": CFG["context"],
                                   **({"district_line": line} if line else {}),
                                   "county_pop2020": cpop,
                                   "source": src + "; Census 2020 P.L. 94-171 block population; Census TIGERweb 2020 tracts"})
