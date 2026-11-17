"""Build dist/wellbeing/index.html from scripts/wellbeing_template.html and data/processed/wellbeing/{data,geo}.json,
and write docs/MEASURES.md (the measure list, for review) from the same data.

The page is split in two to load faster. index.html holds the counties, districts, Ohio and U.S. figures and the trend
series. tracts.json holds the 3,161 tract values, margins of error and shapes; the page requests it right after the
first map is drawn, so the two downloads do not compete, and shows counties and districts without waiting for it. Values on the page are written with 8 significant digits
(data.json keeps full precision); tract figures are written as they are in data.json.
Run: .venv/bin/python scripts/72_wb_build.py"""
import datetime as dt
import hashlib
import json
import re
from decimal import ROUND_HALF_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import wellbeing_measures as WM
from common import DIST, PROC, ROOT

data = json.loads((PROC / "wellbeing" / "data.json").read_text())
geo = json.loads((PROC / "wellbeing" / "geo.json").read_text())
M = data["measures"]
# split combined source strings so each publisher is listed once; drop fragments that only name a table or period
srcs = sorted({part.strip() for m in M.values() if m.get("source") for part in m["source"].split(";")
               if part.strip() and not part.strip().startswith(("ACS ", "ACS,"))})
foot = ("<p><b>How the three levels are built.</b> Counties: each source's published county figures. Census tracts: "
        "2020 tracts, with American Community Survey 2020-2024 estimates and CDC PLACES model estimates; a survey "
        "estimate whose margin of error is large next to its value is hatched. Congressional districts: the map the "
        "Ohio Redistricting Commission adopted on October 31, 2025, first used in the 2026 election. No published "
        "estimates exist for these lines, so each district adds up the tracts with district residents; a tract split "
        "by a district line counts by the share of its 2020 residents inside the line. Average commute leaves out the 10 "
        "tracts with residents that have no travel time figure (8 have no commuters at all, 2 have 3 to 5). Measures that sources publish "
        "only for whole counties are not shown for districts or tracts. HUD subsidized housing is shown for counties and "
        "tracts but not districts, because HUD withholds or leaves out many tract values, so a district total would be "
        "incomplete. An estimate is hatched when its margin of error is more than about half its value (coefficient of "
        "variation above 30%); an estimate of zero cannot be judged this way and is not hatched, so check its margin.</p>"
        "<p><b>Comparisons.</b> Ohio and U.S. figures come from the same source and method as the local figures, with one "
        "exception: district median household income is estimated from income brackets, while Ohio's is the published "
        "median (the bracket method gives $71,503 for Ohio, against $71,389 published). For CDC "
        "PLACES, Ohio is the tract values weighted by adults, since CDC publishes no state value in this form. "
        "\"Near Ohio\" means within 3% of Ohio's value, or 0.3 points for percentages. U.S. targets are Healthy People "
        "2030 national targets where one exists for a close match; most are age-adjusted and the local figures are not. "
        "Public money is shown beside conditions. It does not show what the money caused.</p>"
        "<p><b>Sources.</b> " + "; ".join(srcs) + ". Map: Census Bureau TIGERweb (2020 tracts and counties; 120th "
        "Congressional Districts), Ohio Redistricting Commission block assignment file, 2020 census block population.</p>"
        "<p>Built by Data 4 The People. Method notes for every source are in DATASETS.md in the project repository.</p>")
desc = ("Ohio's counties, congressional districts and census tracts across nine areas of daily life, from public "
        "federal and state data. Draft.")
html = (ROOT / "scripts/wellbeing_template.html").read_text()
for k in ("__DATA__", "__GEO__", "__FOOT__", "__DESC__", "__DATE__"):
    assert html.count(k) == 1, k
assert html.count("__TRACTS__") == 1
dump = lambda o: json.dumps(o, separators=(",", ":"))           # noqa: E731


STEPS = [Decimal(1).scaleb(-n) for n in range(5)]
MODES = (ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN)


def num(x, sig=None):
    """A number as the page needs it: whole numbers without ".0", and `sig` significant digits when given. A value is
    shortened only if it shows the same at 0 to 4 decimals under every rounding rule; a float like 3.8499999999999996
    (shown as 3.8) is kept whole, since 3.85 could show as 3.9."""
    if isinstance(x, list):
        return [num(v, sig) for v in x]
    if not isinstance(x, float):
        return x
    if sig:
        r = float(f"{x:.{sig}g}")
        dx, dr = Decimal(x), Decimal(r)
        if all(dx.quantize(q, m) == dr.quantize(q, m) for q in STEPS for m in MODES):
            x = r
    return int(x) if x.is_integer() and abs(x) < 2 ** 53 else x


page = {k: v for k, v in data.items() if not k.startswith("tract")}
for k in ("county", "district"):
    page[k] = {i: {p: num(v, 8) for p, v in byp.items()} for i, byp in data[k].items()}
for k in ("ohio", "ohio_moe", "us"):
    page[k] = {i: num(v, 8) for i, v in data[k].items()}
# trend series: every place has the same periods in the same order, so write the periods once per measure
page["series"] = {}
for i, s in data["series"].items():
    per = [p for p, _ in next(iter(s.values()))] if s else []
    assert all([p for p, _ in v] == per for v in s.values()), i
    page["series"][i] = {"p": per, "d": {k: [num(v, 8) for _, v in pts] for k, pts in s.items()}}
tracts = {"ids": data["tract_ids"], "tract": {i: num(a) for i, a in data["tract"].items()},
          "tract_moe": {i: num(a) for i, a in data["tract_moe"].items()}, "tract_weak": data["tract_weak"],
          "shapes": geo["tracts"]}
tjson = dump(tracts)
tname = f"tracts.json?v={hashlib.sha256(tjson.encode()).hexdigest()[:10]}"   # a new name whenever the tract data changes


def land_outline(shapes):
    """Ohio's land as one path: the land tracts merged. Census county and district shapes reach into Lake Erie, and the
    page clips them to this outline. Each tract was simplified on its own, so neighbors leave hairline gaps; a 1-unit
    closing (about 55 meters) fills them, and any hole left under 1,000 square units is such a gap, not water."""
    def rings(d):
        for sub in re.findall(r"M[^Mz]*z", d):
            n = list(map(int, re.findall(r"-?\d+", sub)))
            x, y, pts = n[0], n[1], [(n[0], n[1])]
            for i in range(2, len(n), 2):
                x += n[i]
                y += n[i + 1]
                pts.append((x, y))
            yield pts
    tr = []
    for v in shapes.values():
        g = None
        for r in rings(v["d"]):
            q = Polygon(r).buffer(0)
            g = q if g is None else g.symmetric_difference(q)
        tr.append(g)
    land = unary_union(tr).buffer(1, join_style=2).buffer(-1, join_style=2).simplify(0.3)
    out = []
    for poly in (land.geoms if isinstance(land, MultiPolygon) else [land]):
        poly = orient(poly)
        for ring in [poly.exterior] + [h for h in poly.interiors if Polygon(h).area >= 1000]:
            q = []
            for x, y in ring.coords[:-1]:
                if not q or (round(x), round(y)) != q[-1]:
                    q.append((round(x), round(y)))
            if len(q) >= 3:
                out.append(f"M{q[0][0]},{q[0][1]}" + "".join(f"l{b[0] - a[0]},{b[1] - a[1]}" for a, b in zip(q, q[1:])) + "z")
    return "".join(out)


geo_page = {k: v for k, v in geo.items() if k not in ("tracts", "lake")}
geo_page["land"] = land_outline(geo["tracts"])
today = dt.date.today()
html = (html.replace("__DESC__", desc).replace("__DATE__", f"{today:%B} {today.day}, {today.year}").replace("__FOOT__", dump(foot))
        .replace("__TRACTS__", tname).replace("__DATA__", dump(page)).replace("__GEO__", dump(geo_page)))
out = DIST / "wellbeing" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html)
(DIST / "wellbeing" / "tracts.json").write_text(tjson)
print(f"wrote dist/wellbeing/index.html ({len(html) // 1024} KB) and tracts.json ({len(tjson) // 1024} KB), {len(M)} measures")

# docs/MEASURES.md: one table per dimension
ROLE = {"lives": "Experience", "access": "Access", "money": "Public money", "context": "Context"}
LV = {"county": "C", "district": "D", "tract": "T"}
lines = ["# Measures on the Ohio Community Well-Being page", "",
         "Written by `scripts/72_wb_build.py` from `scripts/wellbeing_measures.py` and the built data. Edit the measure "
         "list in `wellbeing_measures.py`, not here.", "",
         "Levels: C = counties, D = congressional districts (2025 map), T = census tracts. Role: Experience = what "
         "residents experience; Access = services and access; Public money = spending shown beside conditions.", ""]
for d in WM.DIMENSIONS + [{"id": "context", "label": "Who lives here (context, not judged)", "question": ""}]:
    ids = [i for i, m in M.items() if m["dim"] == d["id"]]
    lines += [f"## {d['label']}", ""] + ([f"_{d['question']}_", ""] if d["question"] else [])
    lines += ["| Measure | Role | Levels | Ohio | Better | Standard | Source | Period |", "|---|---|---|---|---|---|---|---|"]
    for i in ids:
        m = M[i]
        o = data["ohio"].get(i)
        ov = "" if o is None else (f"{o:,.{m['decimals']}f}" + ("%" if m["unit"] == "pct" else ""))
        std = f"{m['standard']['v']} ({m['standard']['src']})" if m.get("standard") else ""
        lines.append(f"| {m['label']}{' (headline)' if m.get('headline') else ''} | {ROLE[m['role']]} | "
                     f"{' '.join(LV[x] for x in m['levels'])} | {ov} | {m['better']} | {std} | {m['source']} | {m.get('period_label') or ''} |")
    if d.get("agencies"):
        lines += ["", f"Who runs services: {d['agencies']}", "", f"Main public programs: {d['programs']}"]
    lines.append("")
(ROOT / "docs" / "MEASURES.md").write_text("\n".join(lines))
print("wrote docs/MEASURES.md")
