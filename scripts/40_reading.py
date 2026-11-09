"""Early reading layer: third grade English language arts (ELA) results on the Ohio State Test.

Sources
  1. Ohio Department of Education and Workforce (ODEW) report card download files, saved by hand in
     data/raw/odew/ (the ODEW storage hosts are not fetched by this script):
       {18-19,21-22,22-23,23-24,24-25,25-26}_Achievement_District.xlsx  traditional public districts
       {same years}_Achievement_CS.xlsx                                community schools (one row per building)
       2026_District_Details.xlsx                                      used only to cross-check district counties
     Each file also carries the prior year's district or building value, which gives 2017-18 and 2020-21.
  2. NCES Common Core of Data (CCD) grade 3 fall membership, district (LEA) and school level, plus the
     CCD school directory (virtual-school flag), from the Urban Institute Education Data Portal API.
     ODEW's files give a percent proficient but no count of students tested, so CCD grade 3 enrollment
     is the weight for the county rollup.

County value = sum(pct_d * grade3_enrollment_d) / sum(grade3_enrollment_d) over traditional districts and
brick-and-mortar community schools assigned to the county in ODEW's own files. Online (virtual) community
schools are left out of counties because their students live all over the state. Ohio = ODEW's state figure.

Writes data/processed/reading.json. Run: .venv/bin/python scripts/40_reading.py
"""
import datetime as dt
import json
import re

import openpyxl

from common import PROC, RAW, cached, write_json

TODAY = dt.date.today().isoformat()
COUNTIES = [f"39{n:03d}" for n in range(1, 176, 2)]
assert len(COUNTIES) == 88
ODEW = RAW / "odew"
FILE_YEARS = ["18-19", "21-22", "22-23", "23-24", "24-25", "25-26"]
MATERIAL = 5.0   # flag a county when this share (%) or more of its grade 3 enrollment sits in masked cells
MID = "grade3_ela_proficient"


def sy(start):
    """School year label used as the period: 2018 -> '2018-2019'."""
    return f"{start}-{start + 1}"


def pct(v):
    """ODEW publishes values as text, sometimes left-padded with spaces. NC = not calculated, NA = not applicable."""
    if v is None:
        return None, "blank"
    s = str(v).strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return float(s), None
    return None, s


def sheet_rows(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    names = [ws.title for ws in wb.worksheets]
    want = [n for n in names if n in ("Report_Only_Indicators", "Performance_Indicators")]
    if len(want) != 1:
        raise SystemExit(f"{path.name}: expected one indicator sheet, found {names}")
    ws = wb[want[0]]
    ws.reset_dimensions()   # some files carry a wrong sheet size, which hides every row in read-only mode
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h) if h is not None else "" for h in rows[0]]
    return want[0], [dict(zip(hdr, r)) for r in rows[1:] if r and r[0]], hdr


def g3_cols(hdr, unit):
    """Map school-year start -> column for 3rd grade reading/ELA at `unit` level (District or Building), plus state."""
    out, state = {}, {}
    for h in hdr:
        m = re.match(r"3rd Grade (Reading|English Language Arts) (\d{4})-(\d{2,4}) .*- (District|Building|State)$", h)
        if not m:
            continue
        y = int(m.group(2))
        if m.group(4) == "State":
            state[y] = h
        elif m.group(4) == unit:
            out[y] = h
    return out, state


# --------------------------------------------------------------------------- county names -> FIPS
geo = json.loads((PROC / "geo.json").read_text())["counties"]
NAME2FIPS = {re.sub(r"\s+county$", "", v["name"].strip().lower()): f for f, v in geo.items()}
assert len(NAME2FIPS) == 88 and set(NAME2FIPS.values()) == set(COUNTIES)


def county_fips(name):
    f = NAME2FIPS.get(str(name).strip().lower())
    if not f:
        raise SystemExit(f"unknown county name {name!r}")
    return f


# --------------------------------------------------------------------------- 1. ODEW files
dist = {}       # (irn, year) -> (pct, code)
dist_cty = {}   # irn -> fips (latest file wins; changes are reported)
dist_name = {}
cs = {}         # (building irn, year) -> (pct, code)
cs_cty, cs_name, cs_lea = {}, {}, {}
state = {}      # year -> ODEW state value
cty_changes = []
ycty = {}       # (kind, irn, year) -> fips from the file that reports that year

for fy in FILE_YEARS:
    for kind in ("District", "CS"):
        path = ODEW / f"{fy}_Achievement_{kind}.xlsx"
        sheet, rows, hdr = sheet_rows(path)
        unit = "District" if kind == "District" else "Building"
        cols, scols = g3_cols(hdr, unit)
        if len(cols) != 2 or len(scols) != 1:
            raise SystemExit(f"{path.name}: unexpected grade 3 columns {cols} {scols}")
        for y, h in scols.items():
            vals = {pct(r[h])[0] for r in rows}
            if len(vals) != 1:
                raise SystemExit(f"{path.name}: state column not constant {vals}")
            v = vals.pop()
            if y in state and state[y] != v:
                raise SystemExit(f"state {y}: {state[y]} vs {v}")
            state[y] = v
        current = max(cols)
        for r in rows:
            irn = str(r["Building IRN" if kind == "CS" else "District IRN"]).strip().zfill(6)
            f = county_fips(r["County"])
            store, ctys = (dist, dist_cty) if kind == "District" else (cs, cs_cty)
            if irn in ctys and ctys[irn] != f:
                cty_changes.append((kind, irn, ctys[irn], f, fy))
            ctys[irn] = f
            if kind == "District":
                dist_name[irn] = r["District Name"]
            else:
                cs_name[irn] = r["Building Name"]
                cs_lea[irn] = str(r["District IRN"]).strip().zfill(6)
            for y, h in cols.items():
                v = pct(r[h])
                key = (irn, y)
                if key in store:
                    if store[key] != v and y != current:
                        # a prior-year column disagreeing with that year's own file: keep the year's own file
                        cty_changes.append((kind, irn, "prior-year value differs", f"{store[key]} vs {v}", fy))
                    if y != current:
                        continue
                store[key] = v
                ycty[(kind, irn, y)] = f   # county as listed in that school year's own file

YEARS = sorted({y for _, y in dist})
print("school years:", [sy(y) for y in YEARS], "| state figures:", {sy(y): v for y, v in sorted(state.items())})

# Cross-check district counties against ODEW's District Details file (2025-26)
dd_path = ODEW / "2026_District_Details.xlsx"
dd_mismatch = []
if dd_path.exists():
    wb = openpyxl.load_workbook(dd_path, read_only=True)
    ws = wb["District_Details"]
    ws.reset_dimensions()
    it = ws.iter_rows(values_only=True)
    h = list(next(it))
    for r in it:
        d = dict(zip(h, r))
        irn = str(d["District IRN"]).strip().zfill(6)
        if irn in dist_cty and county_fips(d["County"]) != dist_cty[irn]:
            dd_mismatch.append(irn)
print(f"district county checks: {len(dd_mismatch)} mismatches with District Details; "
      f"{len(cty_changes)} county or prior-year differences across files")

# --------------------------------------------------------------------------- 2. CCD grade 3 enrollment
URBAN = "https://educationdata.urban.org/api/v1"


def urban(path, name):
    out, url = [], f"{URBAN}/{path}"
    page = 0
    while url:
        page += 1
        raw = json.loads(cached(RAW / "urban_ccd" / f"{name}_p{page}.json", url))
        out += raw["results"]
        url = raw.get("next")
    return out


CCD_YEARS = list(range(min(YEARS), 2025))   # CCD fall 2024 (school year 2024-25) is the latest in the API
lea_enr, sch_enr, virtual = {}, {}, {}
lea_state = {}   # NCES leaid -> state IRN
for y in CCD_YEARS:
    if y == 2019:
        continue
    for r in urban(f"school-districts/ccd/directory/{y}/?fips=39", f"lea_dir_{y}"):
        if r.get("state_leaid"):
            lea_state[r["leaid"]] = r["state_leaid"].replace("OH-", "").zfill(6)
for y in CCD_YEARS:
    if y == 2019:
        continue
    for r in urban(f"school-districts/ccd/enrollment/{y}/grade-3/?fips=39", f"lea_enr_g3_{y}"):
        if r["race"] == 99 and r["sex"] == 99 and r["leaid"] in lea_state and (r["enrollment"] or -1) >= 0:
            lea_enr[(lea_state[r["leaid"]], y)] = r["enrollment"]
    sid = {}
    for r in urban(f"schools/ccd/directory/{y}/?fips=39", f"sch_dir_{y}"):
        seasch = (r.get("seasch") or "").split("-")[-1].zfill(6)
        sid[r["ncessch"]] = seasch
        if r.get("charter") == 1:
            virtual[(seasch, y)] = r.get("virtual")
    for r in urban(f"schools/ccd/enrollment/{y}/grade-3/?fips=39", f"sch_enr_g3_{y}"):
        if r["race"] == 99 and r["sex"] == 99 and r["ncessch"] in sid and (r["enrollment"] or -1) >= 0:
            sch_enr[(sid[r["ncessch"]], y)] = r["enrollment"]


def weight(table, irn, y):
    """Grade 3 fall enrollment for the same school year; if CCD has none for that year, the nearest year."""
    if (irn, y) in table:
        return table[(irn, y)], y
    have = sorted((abs(yy - y), yy) for (i, yy) in table if i == irn)
    if have:
        return table[(irn, have[0][1])], have[0][1]
    return None, None


def is_virtual(irn):
    vals = [v for (i, _), v in virtual.items() if i == irn and v is not None and v >= 0]
    return bool(vals) and max(vals) >= 1   # CCD codes 1+ mean full or mostly virtual


# --------------------------------------------------------------------------- 3. roll up
NOT_SERVED = ("NA",)
agg = {f: {} for f in COUNTIES}
stats = {"no_weight": [], "nearest_year": 0, "virtual": set(), "units": {}}
for y in YEARS:
    acc = {f: {"num": 0.0, "den": 0.0, "masked": 0, "masked_units": 0, "units": 0, "cs_units": 0} for f in COUNTIES}
    units = []
    for (irn, yy), (v, code) in dist.items():
        if yy == y:
            units.append(("district", irn, ycty[("District", irn, y)], v, code, lea_enr))
    for (irn, yy), (v, code) in cs.items():
        if yy == y:
            units.append(("cs", irn, ycty[("CS", irn, y)], v, code, sch_enr))
    for kind, irn, f, v, code, table in units:
        if kind == "cs" and is_virtual(irn):
            stats["virtual"].add(irn)
            continue
        w, wy = weight(table, irn, y)
        if v is None:
            # masked or not calculated: count the grade 3 students it hides
            if w:
                acc[f]["masked"] += w
                acc[f]["masked_units"] += 1
            continue
        if w is None or w == 0:
            stats["no_weight"].append((sy(y), kind, irn, v))
            continue
        stats["nearest_year"] += wy != y
        acc[f]["num"] += v * w
        acc[f]["den"] += w
        acc[f]["units"] += 1
        acc[f]["cs_units"] += kind == "cs"
    for f in COUNTIES:
        a = acc[f]
        tot = a["den"] + a["masked"]
        agg[f][y] = {"value": a["num"] / a["den"] if a["den"] else None, "enrolled": a["den"],
                     "masked_enrolled": a["masked"], "masked_units": a["masked_units"], "units": a["units"],
                     "community_schools": a["cs_units"],
                     "masked_share": 100.0 * a["masked"] / tot if tot else None}

# --------------------------------------------------------------------------- 4. write
counties, extras_detail, flagged = {}, {}, []
for f in COUNTIES:
    ser = [[sy(y), agg[f][y]["value"]] for y in YEARS]
    periods = [p for p, _ in ser]
    if len(periods) != len(set(periods)) or periods != sorted(periods):
        raise SystemExit(f"bad series {f}")
    last = agg[f][YEARS[-1]]
    flag = None
    if last["value"] is None:
        flag = "suppressed"
    elif last["masked_share"] is not None and last["masked_share"] >= MATERIAL:
        flag = f"{last['masked_share']:.0f}% of grade 3 enrollment in masked schools"
        flagged.append(f)
    counties[f] = {MID: {"latest": last["value"], "period": sy(YEARS[-1]), "series": ser, "moe": None, "flag": flag}}
    extras_detail[f] = {sy(y): {k: agg[f][y][k] for k in ("enrolled", "masked_enrolled", "masked_units", "units",
                                                          "community_schools", "masked_share")} for y in YEARS}

# Ohio = the enrollment-weighted sum of the same district and school figures the counties use, so a county is
# compared with a statewide number built the same way. ODEW's own state figure runs about 2.4 points lower in
# every year (its state total includes students not in any one district's or school's result); it is kept in
# extras and named in the note.
check = {}
for y in YEARS:
    num = sum(agg[f][y]["value"] * agg[f][y]["enrolled"] for f in COUNTIES if agg[f][y]["value"] is not None)
    den = sum(agg[f][y]["enrolled"] for f in COUNTIES)
    check[sy(y)] = {"weighted_sum_of_counties": num / den, "odew_state": state.get(y)}
extras_detail["ohio"] = check
oh_ser = [[sy(y), check[sy(y)]["weighted_sum_of_counties"]] for y in YEARS]
ohio = {MID: {"latest": oh_ser[-1][1], "period": oh_ser[-1][0], "series": oh_ser, "moe": None, "flag": None}}
odew_latest = state[YEARS[-1]]

latest = sy(YEARS[-1])
metrics = {MID: {
    "label": "Third graders reading at grade level (proficient or above on the state English test)",
    "theme": "people", "unit": "pct", "decimals": 1, "better": "higher",
    "source": "Ohio Department of Education and Workforce, school report card data; NCES Common Core of Data for weights",
    "vintage": (f"school years {', '.join(sy(y) for y in YEARS)} (no test in 2019-2020); ODEW files created "
                f"2019-10 to 2026-09-11; CCD grade 3 enrollment fall 2017-2024; pulled {TODAY}"),
    "period_label": f"{latest} school year",
    "note": ("Share of tested third graders who scored proficient or above on Ohio's third grade English test. "
             "County figures combine public school districts and in-person community schools, weighted by grade 3 "
             "enrollment; schools too small for ODEW to report are left out. Fewer students tested in 2020-2021. "
             f"The Ohio figure is built the same way from all districts and schools so counties compare on equal "
             f"terms; ODEW's published state figure is lower ({odew_latest:.1f}% in {latest}), most likely because it also counts "
             f"students who are not in any one district's or school's result."),
}}
write_json("reading.json", {"metrics": metrics, "counties": counties, "ohio": ohio,
                            "extras": {"reading_rollup_detail": extras_detail}})

# --------------------------------------------------------------------------- 5. report
print(f"counties with a value, latest year: {sum(counties[f][MID]['latest'] is not None for f in COUNTIES)} of 88")
print(f"virtual community schools left out: {len(stats['virtual'])}: "
      f"{sorted(cs_name.get(i, i) for i in stats['virtual'])}")
print(f"reported units with no CCD weight (left out): {len(stats['no_weight'])}")
for x in stats["no_weight"]:
    print("   ", x, dist_name.get(x[2]) or cs_name.get(x[2]))
print(f"unit-years weighted with a nearby year's enrollment: {stats['nearest_year']}")
for y in YEARS:
    m = sum(agg[f][y]["masked_enrolled"] for f in COUNTIES)
    t = sum(agg[f][y]["enrolled"] for f in COUNTIES) + m
    mat = sum(1 for f in COUNTIES if (agg[f][y]["masked_share"] or 0) >= MATERIAL)
    print(f"{sy(y)}: masked grade 3 enrollment {m:.0f} of {t:.0f} ({100*m/t:.2f}%); "
          f"counties at {MATERIAL:.0f}%+ masked: {mat}; ODEW state {state.get(y)} vs our sum "
          f"{check[sy(y)]['weighted_sum_of_counties']:.1f}")
print("flagged counties (latest):", flagged)
for f in ("39049", "39163"):
    print(f, geo[f]["name"], [(p, round(v, 1) if v is not None else None) for p, v in counties[f][MID]["series"]],
          extras_detail[f][latest])
