"""Schools layer: third grade math results and chronic absence, from Ohio report card files.

Sources
  1. Ohio Department of Education and Workforce (ODEW) report card download files, saved by hand in
     data/raw/odew/ (the ODEW storage hosts are not fetched by this script; their links need a token
     that the download page adds). The same files the reading layer (40_reading.py) uses:
       {18-19,21-22,22-23,23-24,24-25,25-26}_Achievement_District.xlsx  traditional public districts
       {same years}_Achievement_CS.xlsx                                community schools (one row per building)
       2026_District_Details.xlsx                                      2025-26 district chronic absence and enrollment
     Each achievement file also carries the prior year's value, which gives 2017-18 and 2020-21.
  2. NCES Common Core of Data (CCD), from the Urban Institute Education Data Portal API (the reading
     layer's cached pulls in data/raw/urban_ccd/, read only): grade 3 fall membership as the math weight,
     total district membership as the chronic absence weight for 2017-18 and 2018-19, and the school
     directory's virtual flag.

grade3_math_proficient is built exactly like the reading layer's grade3_ela_proficient: county value =
sum(pct_d * grade3_enrollment_d) / sum(grade3_enrollment_d) over traditional districts and in-person community
schools assigned to the county in ODEW's own files. Ohio = the same weighted sum over every county.

chronic_absent_rate uses traditional districts only (the 2025-26 community school figures are in a file that is
not on disk), weighted by total enrollment: CCD membership for 2017-18 and 2018-19, ODEW's own enrollment count
from the same District Details file for 2025-26. Ohio = the same weighted sum over every county.

Not built (files not on disk): four-year graduation rate, chronic absence for 2019-20 through 2024-25, and
kindergarten readiness. See docs/datasets/schools.md.

Writes data/processed/schools.json. Run: .venv/bin/python scripts/44_schools.py
"""
import datetime as dt
import json
import re

import openpyxl

from common import PROC, RAW, cached, write_json
from common import ST_ID

if ST_ID != "oh":
    raise SystemExit("This layer reads Ohio report card files. For Georgia run scripts/47_schools_ga.py; for Illinois, scripts/48_schools_il.py.")

TODAY = dt.date.today().isoformat()
COUNTIES = [f"39{n:03d}" for n in range(1, 176, 2)]
assert len(COUNTIES) == 88
ODEW = RAW / "odew"
FILE_YEARS = ["18-19", "21-22", "22-23", "23-24", "24-25", "25-26"]
MATERIAL = 5.0   # flag a county when this share (%) or more of its weight sits in masked cells
MATH = "grade3_math_proficient"
ABS = "chronic_absent_rate"


def sy(start):
    """School year label used as the period: 2018 -> '2018-2019'."""
    return f"{start}-{start + 1}"


def pct(v):
    """ODEW publishes values as text, sometimes left-padded with spaces. Anything that is not a number
    ("NC" not calculated, "NA" not applicable, "<10", "--", blank) comes back as (None, code), never 0."""
    if v is None:
        return None, "blank"
    s = str(v).strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return float(s), None
    return None, s or "blank"


def sheet(path, names):
    wb = openpyxl.load_workbook(path, read_only=True)
    want = [ws.title for ws in wb.worksheets if ws.title in names]
    if len(want) != 1:
        raise SystemExit(f"{path.name}: expected one of {names}, found {[ws.title for ws in wb.worksheets]}")
    ws = wb[want[0]]
    ws.reset_dimensions()   # some files carry a wrong sheet size, which hides every row in read-only mode
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h) if h is not None else "" for h in rows[0]]
    return [dict(zip(hdr, r)) for r in rows[1:] if r and r[0]], hdr


def g3_math_cols(hdr, unit):
    """Map school-year start -> column for 3rd grade math at `unit` level (District or Building), plus state."""
    out, state = {}, {}
    for h in hdr:
        m = re.match(r"3rd Grade Math (\d{4})-(\d{2,4}) .*- (District|Building|State)$", h)
        if not m:
            continue
        y = int(m.group(1))
        if m.group(3) == "State":
            state[y] = h
        elif m.group(3) == unit:
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


def irn_of(v):
    return str(v).strip().zfill(6)


# --------------------------------------------------------------------------- 1. ODEW files
math = {"District": {}, "CS": {}}   # kind -> (irn, year) -> (pct, code)
ycty = {}                           # (kind, irn, year) -> fips from the file that reports that year
names = {"District": {}, "CS": {}}
math_state = {}                     # year -> ODEW state value
diffs = []

for fy in FILE_YEARS:
    for kind in ("District", "CS"):
        path = ODEW / f"{fy}_Achievement_{kind}.xlsx"
        rows, hdr = sheet(path, ("Report_Only_Indicators", "Performance_Indicators"))
        unit = "District" if kind == "District" else "Building"
        cols, scols = g3_math_cols(hdr, unit)
        if len(cols) != 2 or len(scols) != 1:
            raise SystemExit(f"{path.name}: unexpected grade 3 math columns {cols} {scols}")
        for y, h in scols.items():
            vals = {pct(r[h])[0] for r in rows}
            if len(vals) != 1:
                raise SystemExit(f"{path.name}: state column not constant {vals}")
            v = vals.pop()
            if y in math_state and math_state[y] != v:
                raise SystemExit(f"state {y}: {math_state[y]} vs {v}")
            math_state[y] = v
        current = max(cols)
        for r in rows:
            irn = irn_of(r["Building IRN" if kind == "CS" else "District IRN"])
            names[kind][irn] = r["Building Name" if kind == "CS" else "District Name"]
            for y, h in cols.items():
                v = pct(r[h])
                key = (irn, y)
                if key in math[kind]:
                    if math[kind][key] != v and y != current:
                        diffs.append((kind, irn, y, math[kind][key], v, fy))
                    if y != current:
                        continue   # keep the value from that school year's own file
                math[kind][key] = v
                ycty[(kind, irn, y)] = county_fips(r["County"])

MATH_YEARS = sorted({y for _, y in math["District"]})
print("math school years:", [sy(y) for y in MATH_YEARS], "| ODEW state:", {sy(y): v for y, v in sorted(math_state.items())})
print(f"prior-year columns that differ from the year's own file: {len(diffs)}")

# Chronic absence, traditional districts. 2017-18 and 2018-19 from the 2018-19 achievement file;
# 2025-26 from the 2025-26 District Details file ("All Students" row).
absn = {}      # (irn, year) -> (pct, code)
abs_cty = {}   # (irn, year) -> fips
abs_enr_odew = {}   # (irn, year) -> ODEW enrollment
rows, hdr = sheet(ODEW / "18-19_Achievement_District.xlsx", ("Performance_Indicators",))
for r in rows:
    irn = irn_of(r["District IRN"])
    for y in (2017, 2018):
        absn[(irn, y)] = pct(r[f"Chronic Absenteeism Rate {y}-{str(y + 1)[2:]}"])
        abs_cty[(irn, y)] = county_fips(r["County"])
rows, hdr = sheet(ODEW / "2026_District_Details.xlsx", ("District_Details",))
seen = set()
for r in rows:
    if str(r["Student Group"]).strip() != "All Students":
        continue
    irn = irn_of(r["District IRN"])
    if irn in seen:
        raise SystemExit(f"duplicate All Students row for {irn}")
    seen.add(irn)
    names["District"].setdefault(irn, r["District Name"])
    absn[(irn, 2025)] = pct(r["Chronic Absenteeism Rate"])
    abs_cty[(irn, 2025)] = county_fips(r["County"])
    abs_enr_odew[(irn, 2025)] = pct(r["Enrollment"])[0]
ABS_YEARS = sorted({y for _, y in absn})
print("chronic absence school years:", [sy(y) for y in ABS_YEARS], f"| 2025-26 districts: {len(seen)}")

# --------------------------------------------------------------------------- 2. CCD weights (reading layer's cache)
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


CCD_YEARS = [y for y in range(min(MATH_YEARS), 2025) if y != 2019]
lea_g3, sch_g3, lea_tot, virtual = {}, {}, {}, {}
for y in CCD_YEARS:
    lea_state = {}
    for r in urban(f"school-districts/ccd/directory/{y}/?fips=39", f"lea_dir_{y}"):
        if r.get("state_leaid"):
            irn = r["state_leaid"].replace("OH-", "").zfill(6)
            lea_state[r["leaid"]] = irn
            if (r.get("enrollment") or -1) >= 0:
                lea_tot[(irn, y)] = r["enrollment"]
    for r in urban(f"school-districts/ccd/enrollment/{y}/grade-3/?fips=39", f"lea_enr_g3_{y}"):
        if r["race"] == 99 and r["sex"] == 99 and r["leaid"] in lea_state and (r["enrollment"] or -1) >= 0:
            lea_g3[(lea_state[r["leaid"]], y)] = r["enrollment"]
    sid = {}
    for r in urban(f"schools/ccd/directory/{y}/?fips=39", f"sch_dir_{y}"):
        seasch = (r.get("seasch") or "").split("-")[-1].zfill(6)
        sid[r["ncessch"]] = seasch
        if r.get("charter") == 1:
            virtual[(seasch, y)] = r.get("virtual")
    for r in urban(f"schools/ccd/enrollment/{y}/grade-3/?fips=39", f"sch_enr_g3_{y}"):
        if r["race"] == 99 and r["sex"] == 99 and r["ncessch"] in sid and (r["enrollment"] or -1) >= 0:
            sch_g3[(sid[r["ncessch"]], y)] = r["enrollment"]


def weight(table, irn, y):
    """Enrollment for the same school year; if CCD has none for that year, the nearest year."""
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
def rollup(units, years):
    """units: list of (year, kind, irn, fips, value, code, weight, weight_year). Returns agg[f][y] and stats."""
    agg = {f: {} for f in COUNTIES}
    stats = {"no_weight": [], "nearest_year": 0}
    for y in years:
        acc = {f: {"num": 0.0, "den": 0.0, "masked": 0, "masked_units": 0, "units": 0, "cs_units": 0} for f in COUNTIES}
        for yy, kind, irn, f, v, code, w, wy in units:
            if yy != y:
                continue
            if v is None:
                if w:
                    acc[f]["masked"] += w
                    acc[f]["masked_units"] += 1
                continue
            if not w:
                stats["no_weight"].append((sy(y), kind, irn, v))
                continue
            stats["nearest_year"] += wy != y
            acc[f]["num"] += v * w
            acc[f]["den"] += w
            acc[f]["units"] += 1
            acc[f]["cs_units"] += kind == "CS"
        for f in COUNTIES:
            a = acc[f]
            tot = a["den"] + a["masked"]
            agg[f][y] = {"value": a["num"] / a["den"] if a["den"] else None, "weight": a["den"],
                         "masked_weight": a["masked"], "masked_units": a["masked_units"], "units": a["units"],
                         "community_schools": a["cs_units"],
                         "masked_share": 100.0 * a["masked"] / tot if tot else None}
    return agg, stats


math_units, left_virtual = [], set()
for kind, table in (("District", lea_g3), ("CS", sch_g3)):
    for (irn, y), (v, code) in math[kind].items():
        if kind == "CS" and is_virtual(irn):
            left_virtual.add(irn)
            continue
        w, wy = weight(table, irn, y)
        math_units.append((y, kind, irn, ycty[(kind, irn, y)], v, code, w, wy))
math_agg, math_stats = rollup(math_units, MATH_YEARS)

abs_units = []
for (irn, y), (v, code) in absn.items():
    if (irn, y) in abs_enr_odew and abs_enr_odew[(irn, y)]:
        w, wy = abs_enr_odew[(irn, y)], y          # ODEW's own enrollment, same file and year
    else:
        w, wy = weight(lea_tot, irn, y)            # CCD total membership
    abs_units.append((y, "District", irn, abs_cty[(irn, y)], v, code, w, wy))
abs_agg, abs_stats = rollup(abs_units, ABS_YEARS)


# --------------------------------------------------------------------------- 4. write
def series_block(agg, years, all_years, what):
    counties, flagged = {}, []
    for f in COUNTIES:
        ser = [[sy(y), agg[f][y]["value"] if y in years else None] for y in all_years]
        periods = [p for p, _ in ser]
        if len(periods) != len(set(periods)) or periods != sorted(periods):
            raise SystemExit(f"bad series {f}: {periods}")
        last = agg[f][years[-1]]
        flag = None
        if last["value"] is None:
            flag = "suppressed"
        elif last["masked_share"] is not None and last["masked_share"] >= MATERIAL:
            flag = f"{last['masked_share']:.0f}% of {what} in masked districts or schools"
            flagged.append(f)
        counties[f] = {"latest": last["value"], "period": sy(years[-1]), "series": ser, "moe": None, "flag": flag}
    return counties, flagged


def ohio_block(agg, years, all_years):
    vals = {}
    for y in years:
        num = sum(agg[f][y]["value"] * agg[f][y]["weight"] for f in COUNTIES if agg[f][y]["value"] is not None)
        den = sum(agg[f][y]["weight"] for f in COUNTIES)
        vals[y] = num / den
    ser = [[sy(y), vals.get(y)] for y in all_years]
    return {"latest": vals[years[-1]], "period": sy(years[-1]), "series": ser, "moe": None, "flag": None}, vals


# Series periods: math skips 2019-20 (no test). Chronic absence lists 2019-20 through 2024-25 as null so a
# chart does not draw a straight line across years whose files are not on disk.
ABS_SERIES_YEARS = [y for y in range(min(ABS_YEARS), max(ABS_YEARS) + 1)]
math_c, math_flagged = series_block(math_agg, MATH_YEARS, MATH_YEARS, "grade 3 enrollment")
abs_c, abs_flagged = series_block(abs_agg, ABS_YEARS, ABS_SERIES_YEARS, "enrollment")
math_oh, math_oh_vals = ohio_block(math_agg, MATH_YEARS, MATH_YEARS)
abs_oh, abs_oh_vals = ohio_block(abs_agg, ABS_YEARS, ABS_SERIES_YEARS)

counties = {f: {MATH: math_c[f], ABS: abs_c[f]} for f in COUNTIES}
ohio = {MATH: math_oh, ABS: abs_oh}

# Rollup detail, by county and year, plus the statewide check against ODEW's own state figure
detail = {}
keys = ("weight", "masked_weight", "masked_units", "units", "community_schools", "masked_share")
for f in COUNTIES:
    detail[f] = {MATH: {sy(y): {k: math_agg[f][y][k] for k in keys} for y in MATH_YEARS},
                 ABS: {sy(y): {k: abs_agg[f][y][k] for k in keys} for y in ABS_YEARS}}
detail["ohio"] = {MATH: {sy(y): {"weighted_sum_of_counties": math_oh_vals[y], "odew_state": math_state.get(y)}
                         for y in MATH_YEARS},
                  ABS: {sy(y): {"weighted_sum_of_counties": abs_oh_vals[y], "odew_state": None} for y in ABS_YEARS}}

# District values for the latest year of each measure (traditional districts only), keyed by county
ML, AL = MATH_YEARS[-1], ABS_YEARS[-1]
dv = {f: [] for f in COUNTIES}
irns = sorted({i for (i, y) in math["District"] if y == ML} | {i for (i, y) in absn if y == AL})
for irn in irns:
    mv, mcode = math["District"].get((irn, ML), (None, "not in file"))
    av, acode = absn.get((irn, AL), (None, "not in file"))
    f = ycty.get(("District", irn, ML)) or abs_cty.get((irn, AL))
    g3w, g3y = weight(lea_g3, irn, ML)
    dv[f].append({
        "irn": irn, "name": names["District"].get(irn), "county": f,
        MATH: mv, MATH + "_flag": mcode, "grade3_enrollment_ccd": g3w, "grade3_enrollment_year": sy(g3y) if g3y else None,
        ABS: av, ABS + "_flag": acode, "enrollment_odew": abs_enr_odew.get((irn, AL)),
    })
dv["ohio"] = {"periods": {MATH: sy(ML), ABS: sy(AL)},
              "fields": {MATH: "percent proficient or above, ODEW",
                         "grade3_enrollment_ccd": "CCD fall grade 3 membership (the county weight; ODEW does not publish a tested count)",
                         ABS: "percent chronically absent, all students, ODEW",
                         "enrollment_odew": "ODEW enrollment, all students, same file (the county weight for this year)",
                         "*_flag": "ODEW code when the value is not a number (NC, <10, NA), else null"}}

latest_m, latest_a = sy(ML), sy(AL)
metrics = {
    MATH: {
        "label": "Third graders proficient in math (proficient or above on the state math test)",
        "theme": "education", "unit": "pct", "decimals": 1, "better": "higher",
        "source": "Ohio Department of Education and Workforce, school report card data; NCES Common Core of Data for weights",
        "vintage": (f"school years {', '.join(sy(y) for y in MATH_YEARS)} (no test in 2019-2020); ODEW files created "
                    f"2019-10 to 2026-09-11; CCD grade 3 enrollment fall 2017-2024; pulled {TODAY}"),
        "period_label": f"{latest_m} school year",
        "note": ("Share of tested third graders who scored proficient or above on Ohio's third grade math test. "
                 "County figures combine public school districts and in-person community schools, weighted by grade 3 "
                 "enrollment; schools too small for ODEW to report are left out. Fewer students tested in 2020-2021. "
                 "The Ohio figure is built the same way from the same districts and schools so counties compare on equal "
                 f"terms; ODEW's published state figure is {math_state[ML]:.1f}% for {latest_m}."),
    },
    ABS: {
        "label": "Students chronically absent (missed 10% or more of school)",
        "theme": "education", "unit": "pct", "decimals": 1, "better": "lower",
        "source": "Ohio Department of Education and Workforce, school report card data; NCES Common Core of Data for weights",
        "vintage": (f"school years 2017-2018, 2018-2019 and 2025-2026 only (2019-2020 through 2024-2025 not on disk); "
                    f"ODEW files created 2019-10 and 2026-09; pulled {TODAY}"),
        "period_label": f"{latest_a} school year",
        "note": ("Share of students who missed 10% or more of the school year, for any reason, excused or not. "
                 "County figures cover traditional public school districts only, weighted by enrollment; community "
                 "schools are left out. The Ohio figure is built the same way from all districts; ODEW's own state "
                 "figure covers all public schools and is not in the files used here."),
    },
}
write_json("schools.json", {"metrics": metrics, "counties": counties, "ohio": ohio,
                            "extras": {"schools_rollup_detail": detail, "district_values": dv}})

# --------------------------------------------------------------------------- 5. report
for mid, agg, years, stats in ((MATH, math_agg, MATH_YEARS, math_stats), (ABS, abs_agg, ABS_YEARS, abs_stats)):
    lv = [(counties[f][mid]["latest"], f) for f in COUNTIES if counties[f][mid]["latest"] is not None]
    print(f"\n{mid}: counties with a value {len(lv)} of 88; Ohio {ohio[mid]['latest']:.2f}; "
          f"min {min(lv)[0]:.1f} {geo[min(lv)[1]]['name']}; max {max(lv)[0]:.1f} {geo[max(lv)[1]]['name']}")
    print(f"  units with no weight (left out): {len(stats['no_weight'])} {stats['no_weight'][:6]}")
    print(f"  unit-years weighted with a nearby year's enrollment: {stats['nearest_year']}")
    for y in years:
        m = sum(agg[f][y]["masked_weight"] for f in COUNTIES)
        t = sum(agg[f][y]["weight"] for f in COUNTIES) + m
        vals = [agg[f][y]["value"] for f in COUNTIES if agg[f][y]["value"] is not None]
        st = math_state.get(y) if mid == MATH else None
        print(f"  {sy(y)}: counties {len(vals)}, range {min(vals):.1f}-{max(vals):.1f}, masked weight {m:.0f} of "
              f"{t:.0f} ({100 * m / t:.2f}%), ours {detail['ohio'][mid][sy(y)]['weighted_sum_of_counties']:.2f}"
              + (f", ODEW state {st}" if st is not None else ""))
print("\nvirtual community schools left out of math:", len(left_virtual))
print("flagged counties, latest:", {MATH: math_flagged, ABS: abs_flagged})
print("district rows in extras:", sum(len(v) for k, v in dv.items() if k != "ohio"))
