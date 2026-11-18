"""Statewide map shapes for a state's Community Well-Being page (Ohio unless D4TP_STATE says otherwise): every 2020
census tract, every county and every congressional district, in one projection. Writes <PROC>/wellbeing/geo.json.
Run: .venv/bin/python scripts/70_wb_geo.py

- Tracts, counties: Census TIGERweb (2020 census layers), simplified by the server (about 40 meters).
- Congressional districts: for Ohio, the Ohio Redistricting Commission's block assignment file for the map adopted
  October 31, 2025; for other states, the Census Bureau's 119th Congress block file. Joined to 2020 census block population (P.L. 94-171, P1_001N). Each tract records how many of its 2020
  residents live in each district. District outlines are TIGERweb Current layer 54 (120th Congressional Districts);
  the script checks that every tract wholly inside a district by block population falls inside that outline.
- Lake Erie: TIGER counties and districts reach into the lake. The Well-Being page clips the map to the land tracts
  merged into one outline (built in 72_wb_build.py), so county and district shapes stop at the shore.
- Tract names: the city, village or Census-designated place holding at least half of the tract's 2020 residents
  (Census 2020 block assignment file for places), or else the township holding the tract's internal point (states
  with township governments, such as Ohio) or the county.
- Coordinates: an equirectangular projection scaled by the cosine of the state's middle latitude, in whole units of a
  6,000-wide box, written as relative SVG path commands to keep the page small.
"""
import io
import json
import math
import zipfile
from urllib.parse import urlencode

import pandas as pd

from common import ABBR, CFG, COUNTIES, NRAW, RAW, ST_ID, STATE, census, cached, write_json

STF, ST = STATE, ABBR
KEY = "wellbeing"
ORC = "https://redistricting.ohio.gov/api/public/districtmaps/430/download"
BAF_PLACE = f"https://www2.census.gov/geo/docs/maps-data/data/baf2020/BlockAssign_ST{STF}_{ST}.zip"
TIGER = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/{}/query?"
CD_LINE = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/54/query?"
W = 6000
OH_POP_2020 = CFG["pop2020"]    # official 2020 census count for the state
CD119 = "https://www2.census.gov/programs-surveys/decennial/rdo/mapping-files/2025/119-congressional-district-befs/cd119.zip"


def tidy(name):
    """'Kettering city' -> 'Kettering'; 'Washington township' -> 'Washington Township'."""
    for suf in (" city", " village", " CDP"):
        if name.endswith(suf):
            return name[: -len(suf)]
    return name.replace(" township", " Township")


def inside(x, y, ring):
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def rings(geom):
    return geom["coordinates"] if geom["type"] == "Polygon" else [r for p in geom["coordinates"] for r in p]


def tiger(layer, where, name, fields="GEOID,COUNTY", geometry=True, fmt="geojson", url=TIGER, offset="0.0004"):
    q = dict(where=where, outFields=fields, returnGeometry="true" if geometry else "false", outSR="4326",
             maxAllowableOffset=offset, geometryPrecision="5", f=fmt)
    j = json.loads(cached(RAW / KEY / name, url.format(layer) + urlencode(q)))
    assert not j.get("exceededTransferLimit") and not j.get("properties", {}).get("exceededTransferLimit"), name
    return j


if __name__ == "__main__":
    cname = {r["county"]: r["NAME"].split(" County,")[0]
             for r in census("2020/dec/pl", {"get": "NAME", "for": "county:*", "in": f"state:{STF}"}, f"{KEY}/pl2020_counties.json")}
    cos = sorted(cname)
    assert [STF + c for c in cos] == COUNTIES

    # blocks: district and 2020 population
    if ST_ID == "oh":
        z = zipfile.ZipFile(io.BytesIO(cached(RAW / "oh10" / "orc_430.zip", ORC)))
        b = pd.read_excel(io.BytesIO(z.read("October 31 2025 CD BAF.xlsx")), dtype=str).rename(columns={"DistrictID:1": "cd"})
        assert len(b) == 276428 and b.Block.str.len().eq(15).all()
    else:
        z = zipfile.ZipFile(io.BytesIO(cached(NRAW / "census_cd119" / "cd119.zip", CD119)))
        b = pd.read_csv(z.open("NationalCD119.txt"), dtype=str).rename(columns={"GEOID": "Block", "CDFP": "cd"})
        b = b[b.Block.str[:2] == STF][["Block", "cd"]]
        # Illinois has water-only blocks in Lake Michigan assigned to no district (ZZ). They stay in, so their water
        # tracts keep their shapes, but they have no residents and count toward no district.
        zzb = set(b.Block[b.cd == "ZZ"])
        print(f"blocks with no district (ZZ): {len(zzb)}")
        assert b.Block.str.len().eq(15).all()
    rows = []
    for c in cos:
        for r in census("2020/dec/pl", {"get": "P1_001N", "for": "block:*", "in": f"state:{STF} county:{c} tract:*"},
                        f"{KEY}/pl2020_block_{c}.json"):
            rows.append((r["state"] + r["county"] + r["tract"] + r["block"], int(r["P1_001N"])))
    m = b.merge(pd.DataFrame(rows, columns=["Block", "pop"]), on="Block", how="left")
    assert m["pop"].notna().all() and int(m["pop"].sum()) == OH_POP_2020, int(m["pop"].sum())
    if ST_ID != "oh":
        assert sum(n for blk, n in rows if blk in zzb) == 0, "a block with no district has residents"
    m["cd"] = m.cd.str.zfill(2)
    m["tract"] = m.Block.str[:11]
    cdpop = m[m.cd != "ZZ"].groupby("cd")["pop"].sum()
    print("district 2020 populations:", dict(cdpop))
    assert len(cdpop) == CFG["districts"] and cdpop.max() - cdpop.min() <= CFG["pop_spread"], "districts should be within a person or two of each other"

    # place names
    zp = zipfile.ZipFile(io.BytesIO(cached(RAW / KEY / BAF_PLACE.rsplit("/", 1)[1], BAF_PLACE)))
    plc = pd.read_csv(zp.open(f"BlockAssign_ST{STF}_{ST}_INCPLACE_CDP.txt"), sep="|", dtype=str).rename(columns={"BLOCKID": "Block"})
    plc_name = {r["place"]: tidy(r["NAME"].split(",")[0])
                for r in census("2020/dec/pl", {"get": "NAME", "for": "place:*", "in": f"state:{STF}"}, f"{KEY}/pl2020_places.json")}
    m = m.merge(plc, on="Block", how="left")
    mcds, tpts = {}, {}
    for c in cos:
        mcds[c] = []
        for f in tiger(20, f"STATE='{STF}' AND COUNTY='{c}'", f"tiger_cousub_{c}.geojson", fields="GEOID,NAME,COUNTY")["features"]:
            g = f["geometry"]
            mcds[c].append((tidy(f["properties"]["NAME"]), [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]))
        for f in tiger(6, f"STATE='{STF}' AND COUNTY='{c}'", f"tiger_tractpts_{c}.json", fields="GEOID,INTPTLAT,INTPTLON,AREALAND",
                       geometry=False, fmt="json")["features"]:
            a = f["attributes"]
            tpts[a["GEOID"]] = (float(a["INTPTLON"]), float(a["INTPTLAT"]), float(a["AREALAND"]))

    def township(t):
        x, y, _ = tpts[t]
        if not CFG["townships"]:
            return None
        hits = [n for n, polys in mcds[t[2:5]] if any(inside(x, y, [tuple(p) for p in poly[0]]) for poly in polys)]
        return hits[0] if hits else None

    tracts = {}
    for t, g in m.groupby("tract"):
        pop = int(g["pop"].sum())
        by = g.dropna(subset=["PLACEFP"]).groupby("PLACEFP")["pop"].sum().sort_values(ascending=False)
        place = plc_name[by.index[0]] if len(by) and pop and by.iloc[0] / pop >= 0.5 else (township(t) or f"{cname[t[2:5]]} County")
        cd = {k: int(v) for k, v in g.groupby("cd")["pop"].sum().items() if v > 0 and k != "ZZ"}
        tracts[t] = {"county": t[2:5], "pop2020": pop, "cd": cd,
                     "label": f"{place}, tract {int(t[5:9])}" + (f".{t[9:]}" if t[9:] != "00" else "")}

    # outlines
    feats = []
    for c in cos:
        feats += tiger(6, f"STATE='{STF}' AND COUNTY='{c}'", f"tiger_tracts_{c}.geojson")["features"]
    assert {f["properties"]["GEOID"] for f in feats} == set(tracts)
    water = {t for t, (_, _, al) in tpts.items() if al == 0}
    land = [f for f in feats if f["properties"]["GEOID"] not in water]
    print(f"{len(tracts)} tracts; {len(water)} water-only tracts (population {sum(tracts[t]['pop2020'] for t in water)})")
    pts = [p for f in land for r in rings(f["geometry"]) for p in r]
    lon0, lon1 = min(p[0] for p in pts), max(p[0] for p in pts)
    lat0, lat1 = min(p[1] for p in pts), max(p[1] for p in pts)
    k = math.cos(math.radians((lat0 + lat1) / 2))
    sc = W / ((lon1 - lon0) * k)
    H = round((lat1 - lat0) * sc)
    xy = lambda p: (round((p[0] - lon0) * k * sc), round((lat1 - p[1]) * sc))   # noqa: E731

    def path(geom):
        """Relative SVG path; repeated points after rounding are dropped."""
        out = []
        for r in rings(geom):
            q = []
            for p in map(xy, r):
                if not q or p != q[-1]:
                    q.append(p)
            if len(q) < 4:
                continue
            s = f"M{q[0][0]},{q[0][1]}"
            for (x0, y0), (x1, y1) in zip(q, q[1:]):
                s += f"l{x1 - x0},{y1 - y0}"
            out.append(s + "z")
        return "".join(out)

    def centroid(geom):
        best = max(rings(geom), key=len)
        ps = [xy(p) for p in best]
        return round(sum(p[0] for p in ps) / len(ps)), round(sum(p[1] for p in ps) / len(ps))

    tout = {}
    for f in land:
        t = f["properties"]["GEOID"]
        x, y, _ = tpts[t]
        tout[t] = dict(tracts[t], d=path(f["geometry"]), p=list(xy((x, y))))
    lake = "".join(path(f["geometry"]) for f in feats if f["properties"]["GEOID"] in water)
    cfeat = tiger(82, f"STATE='{STF}'", "tiger_counties.geojson")["features"]
    counties = {}
    for f in cfeat:
        c = f["properties"]["COUNTY"]
        lp = [tpts[t] for t in tracts if t[2:5] == c and t not in water]
        # label point: the internal point of the county's land tract nearest the middle of its land tracts
        mx, my = sum(p[0] for p in lp) / len(lp), sum(p[1] for p in lp) / len(lp)
        near = min(lp, key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2)
        counties[STF + c] = {"name": cname[c], "d": path(f["geometry"]), "p": list(xy(near[:2])),
                             "pop2020": sum(v["pop2020"] for t, v in tracts.items() if t[2:5] == c)}
    assert sorted(counties) == COUNTIES

    dfeat = tiger(54, f"STATE='{STF}'", f"tiger_cd120_{ST.lower()}.geojson", fields="GEOID,CDSESSN,NAME", url=CD_LINE, offset="0.0004")["features"]
    dfeat = [f for f in dfeat if f["properties"]["GEOID"][2:] != "ZZ"]   # Illinois: Lake Michigan water, no district
    assert len(dfeat) == CFG["districts"], len(dfeat)
    dists = {}
    for f in dfeat:
        cd = f["properties"]["GEOID"][2:]
        lr = [[xy(p) for p in r] for r in rings(f["geometry"])]
        whole = [t for t, v in tracts.items() if v["pop2020"] and v["cd"] == {cd: v["pop2020"]}]
        held = lambda t: sum(inside(*xy(tpts[t][:2]), r) for r in lr) % 2 == 1   # noqa: E731
        bad = [t for t in whole if not held(t)]
        ins = [tpts[t] for t in whole]
        mx, my = sum(p[0] for p in ins) / len(ins), sum(p[1] for p in ins) / len(ins)
        near = min(ins, key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2)
        dists[cd] = {"name": f"District {int(cd)}", "d": path(f["geometry"]), "p": list(xy(near[:2])),
                     "pop2020": int(cdpop[cd]), "whole_tracts": len(whole), "outline_misses": bad}
        print(f"district {cd}: {len(whole)} whole tracts, {len(bad)} outside the TIGERweb outline {bad[:3]}")
        assert len(bad) <= 2, bad
    split = sum(1 for v in tracts.values() if len(v["cd"]) > 1)
    print(f"tracts split between districts: {split}")

    geo = {"viewBox": f"0 0 {W} {H}", "tracts": tout, "counties": counties, "districts": dists, "lake": lake,
           "proj": {"lon0": lon0, "lat1": lat1, "k": k, "sc": sc},
           "source": "Census TIGERweb 2020 tracts and counties; TIGERweb Current 120th Congressional Districts; "
                     + CFG["district_src"] + "; Census 2020 P.L. 94-171 "
                     "block population; Census 2020 place block assignment file"}
    write_json(f"{KEY}/geo.json", geo)
    size = {k_: len(json.dumps(v, separators=(",", ":"))) // 1024 for k_, v in geo.items() if isinstance(v, (dict, str))}
    print("sizes (KB):", size)
