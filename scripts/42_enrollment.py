"""Enrollment layer: people in public programs from program records, as a share of county population.

Sources
  1. USDA FNS, SNAP Data Tables: "Bi-Annual (January and July) State Project Area/County Level
     Participation and Issuance Data" (form FNS-388A), one Excel file per month in a zip.
  2. USDA FNS, SNAP Data Tables: "National Level Annual Summary / State Level" zip (FY69 to current),
     monthly state totals, for the Ohio figure.
  3. Census population estimates, vintage 2025, already built in data/processed/popest.json.

Medicaid by county is not in this layer: the Ohio Department of Medicaid site refused automated
requests when this was built. See docs/datasets/enrollment.md.

Writes data/processed/enrollment.json. Run: .venv/bin/python scripts/42_enrollment.py
"""
import datetime as dt
import io
import json
import zipfile

import openpyxl

from common import PROC, RAW, STATE, cached, write_json

TODAY = dt.date.today().isoformat()
COUNTIES = [f"39{n:03d}" for n in range(1, 176, 2)]
assert len(COUNTIES) == 88

FNS = "https://www.fns.usda.gov/sites/default/files/resource-files/"
COUNTY_ZIP = "snap-zip-fns388a-2.zip"        # FY89 through July 2025
STATE_ZIP = "snap-zip-fy69tocurrent-10.zip"  # monthly state totals

# July of each year, matched to the Census July 1 estimate of the same year. July 2020 is left out:
# Ohio's statewide count that month is about 10% above June and August 2020 (see the dataset notes).
YEARS = [2021, 2022, 2023, 2024, 2025]
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# South Central Ohio Job and Family Services serves Hocking, Ross and Vinton counties. FNS reports
# nearly all of its SNAP cases on the Ross line; the Hocking and Vinton lines hold a few dozen at most.
SOUTH_CENTRAL = ["39073", "39141", "39163"]
NAMES = {"39073": "Hocking", "39141": "Ross", "39163": "Vinton"}


def num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if x is None or not str(x).strip() or str(x).strip() in ("--", "-"):
        return None
    return float(str(x).replace(",", ""))


def sheet_rows(zf, name, sheet=None):
    wb = openpyxl.load_workbook(io.BytesIO(zf.read(name)), read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb[wb.sheetnames[0]]
    return list(ws.iter_rows(values_only=True))


# --------------------------------------------------------------------------- county file
cz = zipfile.ZipFile(io.BytesIO(cached(RAW / "fns" / COUNTY_ZIP, FNS + COUNTY_ZIP)))
by_upper = {n.upper(): n for n in cz.namelist()}
county_persons = {}   # year -> {fips: persons}
for y in YEARS:
    name = by_upper.get(f"JUL {y}.XLSX")
    if not name:
        raise SystemExit(f"county file for July {y} not in {COUNTY_ZIP}")
    rows = sheet_rows(cz, name)
    if str(rows[2][0]).strip() != f"Jul {y}":
        raise SystemExit(f"{name}: header month is {rows[2][0]!r}")
    head = [r for r in rows if r[0] == "Substate/Region"][0]
    col = head.index("Calc: SNAP Total PA and Non-PA People")
    got = {}
    for r in rows:
        code = str(r[0] or "")
        if code[:2] != STATE or " OH " not in code:
            continue
        f = code[:5]
        if f not in COUNTIES:
            raise SystemExit(f"{name}: unknown Ohio project area {code!r}")
        v = num(r[col])
        if v is None:
            raise SystemExit(f"{name}: no persons value for {code!r}")
        # Cuyahoga has two lines (regular EBT and the SSI combined application project); they add.
        got[f] = got.get(f, 0.0) + v
    missing = [f for f in COUNTIES if f not in got]
    if missing:
        raise SystemExit(f"{name}: no row for {missing}")
    county_persons[y] = got

# --------------------------------------------------------------------------- state file
sz = zipfile.ZipFile(io.BytesIO(cached(RAW / "fns" / STATE_ZIP, FNS + STATE_ZIP)))
state_monthly = {}    # "YYYY-MM" -> persons
for fy in range(min(YEARS), max(YEARS) + 3):
    name = f"FY{fy % 100:02d}.xlsx"
    if name not in sz.namelist():
        continue
    wb = openpyxl.load_workbook(io.BytesIO(sz.read(name)), read_only=True, data_only=True)
    found = False
    for sn in wb.sheetnames:
        rows = list(wb[sn].iter_rows(values_only=True))
        for i, r in enumerate(rows):
            if r[0] != "Ohio":
                continue
            found = True
            for x in rows[i + 1:i + 13]:
                m, yy = str(x[0]).split()
                p = f"{yy}-{MON.index(m) + 1:02d}"
                v = num(x[2])
                if p in state_monthly and v is not None and state_monthly[p] != v:
                    raise SystemExit(f"duplicate Ohio month {p} with different values")
                if v is not None:
                    state_monthly[p] = v
    if not found:
        raise SystemExit(f"{name}: no Ohio block")
for y in YEARS:
    if f"{y}-07" not in state_monthly:
        raise SystemExit(f"Ohio state total missing for July {y}")

# The county lines should add to the state total; record any gap rather than hide it.
county_sum_gap = {}
for y in YEARS:
    s = sum(county_persons[y].values())
    county_sum_gap[f"{y}-07"] = s - state_monthly[f"{y}-07"]

# --------------------------------------------------------------------------- population
pe = json.loads((PROC / "popest.json").read_text())


def pop(geo, year):
    d = pe["ohio"] if geo == "ohio" else pe["counties"][geo]
    ser = dict(d["population_estimate"]["series"])
    v = ser.get(str(year))
    if v is None:
        raise SystemExit(f"no July 1 {year} population for {geo}")
    return v


def check_series(series, where):
    ps = [p for p, _ in series]
    if len(ps) != len(set(ps)):
        raise SystemExit(f"duplicate periods in {where}")
    if ps != sorted(ps):
        raise SystemExit(f"series out of order in {where}")


def entry(series, flag=None):
    check_series(series, flag or "")
    p, v = series[-1]
    return {"latest": v, "period": p, "series": [list(s) for s in series], "moe": None,
            "flag": flag if flag else (None if v is not None else "missing")}


counties = {f: {} for f in COUNTIES}
ohio = {}
extras = {"snap_persons_count": {}, "snap_south_central_combined": {}}

for f in COUNTIES:
    cnt = [(f"{y}-07", county_persons[y][f]) for y in YEARS]
    if f in SOUTH_CENTRAL:
        others = " and ".join(NAMES[o] for o in SOUTH_CENTRAL if o != f)
        flag = f"reported with {others} (South Central Ohio JFS)"
        counties[f]["snap_persons_share"] = {
            "latest": None, "period": cnt[-1][0], "series": [[p, None] for p, _ in cnt],
            "moe": None, "flag": flag}
        extras["snap_persons_count"][f] = None
        continue
    share = [(p, v / pop(f, int(p[:4])) * 100) for p, v in cnt]
    counties[f]["snap_persons_share"] = entry(share)
    extras["snap_persons_count"][f] = [[p, v] for p, v in cnt]

# Combined South Central area: one share for the three counties together.
sc = []
for y in YEARS:
    persons = sum(county_persons[y][f] for f in SOUTH_CENTRAL)
    people = sum(pop(f, y) for f in SOUTH_CENTRAL)
    sc.append([f"{y}-07", persons / people * 100])
for f in SOUTH_CENTRAL:
    extras["snap_south_central_combined"][f] = {
        "counties": [NAMES[o] for o in SOUTH_CENTRAL],
        "share_series": sc,
        "persons_series": [[f"{y}-07", sum(county_persons[y][o] for o in SOUTH_CENTRAL)] for y in YEARS],
    }

oh_cnt = [(f"{y}-07", state_monthly[f"{y}-07"]) for y in YEARS]
ohio["snap_persons_share"] = entry([(p, v / pop("ohio", int(p[:4])) * 100) for p, v in oh_cnt])
extras["snap_persons_count"]["ohio"] = [[p, v] for p, v in oh_cnt]
# Statewide monthly persons, as published (later months are preliminary).
extras["snap_persons_ohio_monthly"] = {"ohio": [[p, state_monthly[p]] for p in sorted(state_monthly)]}
extras["snap_county_sum_minus_state"] = {"ohio": county_sum_gap}

last = max(YEARS)
vintage = (f"FNS-388A county file, July {YEARS[0]}-July {last} (zip {COUNTY_ZIP}); Ohio total from FNS "
           f"state file ({STATE_ZIP}); population: Census vintage 2025 July 1 estimates; pulled {TODAY}")
metrics = {
    "snap_persons_share": {
        "label": "People getting SNAP food aid",
        "theme": "income", "unit": "pct", "decimals": 1, "better": "none",
        "source": "USDA Food and Nutrition Service, SNAP Data Tables (county participation, form FNS-388A); "
                  "Census Bureau population estimates",
        "vintage": vintage,
        "period_label": f"July {last}",
        "note": "People in households that got SNAP benefits in July, from program records, divided by the "
                "Census July 1 population of the same year. Ross, Hocking and Vinton are reported together "
                "by one county agency, so they show no single-county value.",
    }
}

out = {"metrics": metrics, "counties": counties, "ohio": ohio, "extras": extras}
write_json("enrollment.json", out)
for f in ("39049", "39163", "39141"):
    e = counties[f]["snap_persons_share"]
    print(f, e["period"], e["latest"], e["flag"], extras["snap_persons_count"][f] and extras["snap_persons_count"][f][-1])
print("ohio", ohio["snap_persons_share"]["latest"], oh_cnt[-1])
print("county sum minus state total:", county_sum_gap)
