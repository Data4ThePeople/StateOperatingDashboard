"""Build dist/<key>/index.html from scripts/district_template.html and data/processed/<key>/{data,geo,basemap}.json.
Run: .venv/bin/python scripts/62_district_build.py <key> (keys in districts.py)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import districts  # noqa: E402

CFG = districts.get(sys.argv)
KEY = CFG["key"]
ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data/processed" / KEY
data = json.loads((P / "data.json").read_text())
geo = json.loads((P / "geo.json").read_text())
split = geo.pop("split", {})
base = json.loads((P / "basemap.json").read_text())
cpop = geo["county_pop2020"]
order = data["county_order"]
mapped = sum(v["in_district"] for v in geo["tracts"].values())
touched = sum(1 for v in geo["tracts"].values() if v["pop2020_in_district"])
sn = CFG["state_name"]


def words(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


whole = [c for c in order if cpop[c][1] == cpop[c][0]]
part = [c for c in order if cpop[c][1] < cpop[c][0]]
bits = []
if whole:
    bits.append(f"all of {words(whole)} {'county' if len(whole) == 1 else 'counties'}")
if part:
    bits.append(f"{'part' if len(part) == 1 else 'parts'} of {words(part)} {'County' if len(part) == 1 else 'counties'}")
where = " and ".join(bits)
where = where[0].upper() + where[1:]
pop = geo["district_pop2020"]
if len(split) / touched > 0.1:
    tracts_txt = (f"{pop:,} residents in the 2020 census. The district line cuts through {len(split)} of the {touched} "
                  f"census tracts it touches, so the map shows the {mapped} tracts where most residents live inside the district.")
else:
    tracts_txt = f"{pop:,} residents in the 2020 census, in {mapped} census tracts."
intro = (f"{where}, {CFG['plan']}. {tracts_txt} Tracts are neighborhoods of about 4,000 people that the Census Bureau "
         f"draws to stay fixed for a decade.")

share = lambda c: round(cpop[c][1] / cpop[c][0] * 100)          # noqa: E731
cnote = []
if whole:
    cnote.append(f"{words(whole)} {'is' if len(whole) == 1 else 'are'} entirely in the district.")
if len(part) == 1:
    cnote.append(f"{part[0]} County figures cover the whole county, and only about {share(part[0])}% of {part[0]} "
                 f"County residents live in the district.")
elif part:
    cnote.append("Figures cover each whole county; only about " +
                 words([f"{share(c)}% of {c} County residents" for c in part]) + " live in the district.")
cnote.append("Values are the same ones the statewide county dashboard shows." if CFG["county_from_state_page"] else
             f"{sn} and U.S. figures come from the same publishers for the same period.")

outside = (f"{part[0]} County outside the district" if geo["context"] == "counties" and len(part) == 1
           else "Outside the district")
line_txt = " The dark outline is the district boundary (Census Bureau TIGERweb, current congressional districts)." if geo.get("district_line") else ""
sums = ("every tract with district residents; a tract split by the district line "
        f"({len(split)} of them) counts by the share of its 2020 residents who live inside the line, which assumes "
        "residents on both sides are alike")
dist_txt = (f"District survey figures on the District tab are the Census Bureau's own estimates for the district. "
            f"District health figures add up {sums}." if data.get("district_published") else
            f"District totals add up {sums}.")
foot = (f"<p>District: {CFG['plan_source']}, with 2020 census block population. {dist_txt} The map, rankings "
        f"and tract scorecards show the {mapped} tracts where most 2020 residents live inside the district, with "
        f"figures for the whole tract.{line_txt} Tract outlines: Census Bureau TIGERweb (2020 tracts). Major roads, "
        f"rivers, lakes and place names: Census Bureau TIGERweb. Tract names: the city, village or Census-designated "
        f"place holding at least half of the tract's residents, or else the township containing its center.</p>"
        f"<p>Census figures: American Community Survey 5-year estimates, 2020-2024, tables B01001, B03002, B05012, "
        f"B15003, B18101, B19001, B19013, B22003, B23001, B25070, B25091, B27010, C17002, C27007. Health: CDC PLACES, "
        f"census tract data, 2025 release. County table: {CFG['county_sources']}. Built by Data 4 The People.</p>")

cfg = {"short": CFG["short"], "title": CFG["title"], "state": sn, "intro": intro, "foot": foot,
       "county_note": " ".join(cnote), "county_note_extra": CFG["county_note_extra"], "outside": outside,
       "touched": touched, "split": len(split)}
desc = f"{CFG['h1']} by census tract and county, from public Census Bureau and CDC data. Draft."
html = (ROOT / "scripts/district_template.html").read_text()
for k in ("__DATA__", "__GEO__", "__BASE__", "__CFG__", "__TITLE__", "__H1__", "__DESC__"):
    assert html.count(k) == 1, k
dump = lambda o: json.dumps(o, separators=(",", ":"))           # noqa: E731
html = (html.replace("__TITLE__", CFG["title"]).replace("__H1__", CFG["h1"]).replace("__DESC__", desc)
        .replace("__CFG__", dump(cfg)).replace("__DATA__", dump(data)).replace("__GEO__", dump(geo)).replace("__BASE__", dump(base)))
out = ROOT / "dist" / KEY / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html)
print(f"wrote dist/{KEY}/index.html ({len(html)//1024} KB), {len(data['metrics'])} measures, {mapped} mapped tracts")
