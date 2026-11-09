"""Ohio's 10th Congressional District (map adopted October 31, 2025): which 2020 census tracts are in it, their
outlines, and a place name for each. Writes data/processed/oh10/geo.json.

- District: the Ohio Redistricting Commission's block assignment file for the adopted plan (map 430 on
  redistricting.ohio.gov, "October 31 2025 CD BAF.xlsx"), joined to 2020 census block population (P.L. 94-171,
  P1_001N). A tract is in the district when most of its 2020 population is.
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
from urllib.parse import urlencode

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import RAW, census, cached, write_json  # noqa: E402

ORC = "https://redistricting.ohio.gov/api/public/districtmaps/430/download"
BAF_MCD = "https://www2.census.gov/geo/docs/maps-data/data/baf2020/BlockAssign_ST39_OH.zip"
TIGER = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/{}/query?"
COUNTIES = {"017": "Butler", "057": "Greene", "113": "Montgomery"}
W = 600


def district_blocks():
    z = zipfile.ZipFile(io.BytesIO(cached(RAW / "oh10" / "orc_430.zip", ORC)))
    name = [n for n in z.namelist() if n.endswith("BAF.xlsx")]
    assert name == ["October 31 2025 CD BAF.xlsx"], z.namelist()
    b = pd.read_excel(io.BytesIO(z.read(name[0])), dtype=str).rename(columns={"DistrictID:1": "cd"})
    assert len(b) == 276428 and b.Block.str.len().eq(15).all()   # every 2020 Ohio block
    return b


def block_pop(counties):
    rows = []
    for c in counties:
        for r in census("2020/dec/pl", {"get": "P1_001N", "for": "block:*", "in": f"state:39 county:{c} tract:*"},
                        f"oh10/pl2020_block_{c}.json"):
            rows.append((r["state"] + r["county"] + r["tract"] + r["block"], int(r["P1_001N"])))
    return pd.DataFrame(rows, columns=["Block", "pop"])


def tidy(name):
    """'Kettering city' -> 'Kettering'; 'Washington township' -> 'Washington Township'."""
    for suf in (" city", " village", " CDP"):
        if name.endswith(suf):
            return name[: -len(suf)]
    return name.replace(" township", " Township")


def place_of_block():
    z = zipfile.ZipFile(io.BytesIO(cached(RAW / "oh10" / "BlockAssign_ST39_OH.zip", BAF_MCD)))
    m = pd.read_csv(z.open("BlockAssign_ST39_OH_INCPLACE_CDP.txt"), sep="|", dtype=str).rename(columns={"BLOCKID": "Block"})
    names = {r["place"]: tidy(r["NAME"].split(",")[0])
             for r in census("2020/dec/pl", {"get": "NAME", "for": "place:*", "in": "state:39"}, "oh10/pl2020_places.json")}
    return m, names


def inside(x, y, ring):
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def tiger(layer, where, name, fields="GEOID,COUNTY", geometry=True, fmt="geojson"):
    q = dict(where=where, outFields=fields, returnGeometry="true" if geometry else "false", outSR="4326",
             maxAllowableOffset="0.0004", geometryPrecision="5", f=fmt)
    return json.loads(cached(RAW / "oh10" / name, TIGER.format(layer) + urlencode(q)))


if __name__ == "__main__":
    b = district_blocks()
    b["county"] = b.Block.str[2:5]
    b["tract"] = b.Block.str[:11]
    cos = sorted(b[b.cd == "10"].county.unique())
    assert cos == sorted(COUNTIES), cos
    m = b[b.county.isin(cos)].merge(block_pop(cos), on="Block", how="left")
    assert m["pop"].notna().all()
    m["in10"] = m.cd == "10"
    plc, plc_name = place_of_block()
    m = m.merge(plc, on="Block", how="left")
    # townships: the county subdivision whose outline holds the tract's internal point
    mcds = []
    for c in cos:
        for f in tiger(20, f"STATE='39' AND COUNTY='{c}'", f"tiger_cousub_{c}.geojson", fields="GEOID,NAME,COUNTY")["features"]:
            g = f["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            mcds.append((tidy(f["properties"]["NAME"]), polys))
    tpts = {}
    for c in cos:
        for f in tiger(6, f"STATE='39' AND COUNTY='{c}'", f"tiger_tractpts_{c}.json", fields="GEOID,INTPTLAT,INTPTLON",
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
        by = g.dropna(subset=["PLACEFP"]).groupby("PLACEFP")["pop"].sum().sort_values(ascending=False)
        if len(by) and pop and by.iloc[0] / pop >= 0.5:
            place = plc_name[by.index[0]]
        else:
            place = township(t) or f"{COUNTIES[t[2:5]]} County"
        tracts[t] = {"county": COUNTIES[t[2:5]], "pop2020": pop, "pop2020_in_district": pop10,
                     "in_district": pop > 0 and pop10 / pop > 0.5, "place": place,
                     "label": f"{place}, tract {int(t[5:9])}" + (f".{t[9:]}" if t[9:] != "00" else "")}
    total10 = int(m.loc[m.in10, "pop"].sum())
    assert total10 == 786629, total10                      # Secretary of State: 81,354 + 167,966 + 537,309
    split = {t: v for t, v in tracts.items() if 0 < v["pop2020_in_district"] < v["pop2020"]}
    inside = sorted(t for t, v in tracts.items() if v["in_district"])
    print(f"tracts in district: {len(inside)}; split tracts: " +
          "; ".join(f"{t} {v['pop2020_in_district']}/{v['pop2020']} {'in' if v['in_district'] else 'out'}" for t, v in split.items()))

    # outlines: tracts of all three counties (Butler's outside part is drawn gray for context), county lines
    feats = []
    for c in cos:
        feats += tiger(6, f"STATE='39' AND COUNTY='{c}'", f"tiger_tracts_{c}.geojson")["features"]
    cfeat = tiger(82, "STATE='39' AND COUNTY IN ('017','057','113')", "tiger_counties.geojson")["features"]
    geoids = {f["properties"]["GEOID"] for f in feats}
    assert geoids == set(tracts), (len(geoids), len(tracts), sorted(geoids ^ set(tracts))[:5])

    def rings(geom):
        return geom["coordinates"] if geom["type"] == "Polygon" else [r for p in geom["coordinates"] for r in p]

    allpts = [p for f in feats for r in rings(f["geometry"]) for p in r]
    lon0, lon1 = min(p[0] for p in allpts), max(p[0] for p in allpts)
    lat0, lat1 = min(p[1] for p in allpts), max(p[1] for p in allpts)
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
    counties = {f["properties"]["GEOID"]: {"name": COUNTIES[f["properties"]["COUNTY"]], "d": path(f["geometry"])} for f in cfeat}
    write_json("oh10/geo.json", {"viewBox": f"0 0 {W} {H}", "tracts": out, "counties": counties,
                                 "proj": {"lon0": lon0, "lat1": lat1, "k": k, "sc": sc, "bbox": [lon0, lat0, lon1, lat1]},
                                 "district_pop2020": total10, "split": split,
                                 "source": "Ohio Redistricting Commission block assignment file (map adopted Oct. 31, 2025); "
                                           "Census 2020 P.L. 94-171 block population; Census TIGERweb 2020 tracts"})
