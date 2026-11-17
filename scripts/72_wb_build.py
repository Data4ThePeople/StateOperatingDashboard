"""Build dist/wellbeing/index.html from scripts/wellbeing_template.html and data/processed/wellbeing/{data,geo}.json,
and write docs/MEASURES.md (the measure list, for review) from the same data.
Run: .venv/bin/python scripts/72_wb_build.py"""
import datetime as dt
import json

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
dump = lambda o: json.dumps(o, separators=(",", ":"))           # noqa: E731
today = dt.date.today()
html = (html.replace("__DESC__", desc).replace("__DATE__", f"{today:%B} {today.day}, {today.year}").replace("__FOOT__", dump(foot))
        .replace("__DATA__", dump(data)).replace("__GEO__", dump(geo)))
out = DIST / "wellbeing" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html)
print(f"wrote dist/wellbeing/index.html ({len(html) // 1024} KB), {len(M)} measures")

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
