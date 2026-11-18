"""Illinois schools layers: third grade reading and math results and chronic absence, from ISBE Report Card files.

The Illinois counterpart of 40_reading.py and 44_schools.py. Run with D4TP_STATE=il.

Source
  Illinois State Board of Education (ISBE) Report Card Public Data Set, one Excel file per report card year
  (https://www.isbe.net/Pages/Illinois-State-Report-Card-Data.aspx), saved in data/raw/il/isbe/. Report card year
  Y covers the school year that ends in the spring of Y. Each file has one row per school, district and the state;
  the "General" sheet holds enrollment, chronic absence and the third grade IAR results.

Method (the same shape as Ohio's layers)
  grade3_ela_proficient, grade3_math_proficient: share of third graders proficient on the Illinois Assessment of
    Readiness (IAR). Illinois set new proficiency levels starting with the spring 2025 tests, and ISBE says not to
    compare those results with earlier years, so the figures start in 2024-2025. County = sum(rate_d * tested_d) /
    sum(tested_d) over district rows with a third grade result, placed by the county ISBE gives the district.
    tested_d = third grade enrollment times the IAR participation rate. Districts whose rate ISBE suppresses are left
    out; a county where they hold a quarter or more of third grade enrollment shows no value.
  chronic_absent_rate: share of students who missed 10% or more of school days. Elementary, high school and unit
    districts only (as in Ohio, where only traditional districts are used), weighted by total enrollment. Illinois
    students attend one district each, so elementary and high school districts that cover the same land do not
    double count. 2019-2020 is left out because school buildings closed in March 2020.
  The Illinois figure is built the same way from the same districts. ISBE's own statewide figures are kept in extras.

Writes data/processed/il/reading.json and data/processed/il/schools.json.
Run: D4TP_STATE=il .venv/bin/python scripts/48_schools_il.py
"""
import datetime as dt
import io
import json

import openpyxl

from common import COUNTIES, PROC, RAW, SK, SNAME, ST_ID, cached, write_json

if ST_ID != "il":
    raise SystemExit("This layer reads Illinois Report Card files. Run it with D4TP_STATE=il.")

ISBE = "https://www.isbe.net/_layouts/Download.aspx?SourceUrl=/Documents/"
FILES = {   # report card year -> file
    2018: "Report-Card-Public-Data-Set.xlsx",
    2019: "2019-Report-Card-Public-Data-Set.xlsx",
    2021: "2021-RC-Pub-Data-Set.xlsx",
    2022: "2022-Report-Card-Public-Data-Set.xlsx",
    2023: "23-RC-Pub-Data-Set.xlsx",
    2024: "24-RC-Pub-Data-Set.xlsx",
    2025: "2025-Report-Card-Public-Data-Set.xlsx",
    2026: "2026-RC-Public-Data-Set.xlsx",
}
TEST_YEARS = [2025, 2026]          # the new proficiency levels
SUBJ = {"grade3_ela_proficient": ("IAR ELA Proficiency Rate Grade 3 - Total", "IAR ELA Participation Rate Grade 3 - Total"),
        "grade3_math_proficient": ("IAR Math Proficiency Rate Grade 3 - Total", "IAR Math Participation Rate Grade 3 - Total")}
G3 = "# Student Enrollment -Grade 3"
# RCDTS district type codes for traditional districts: elementary 02-05, high school 13-17, unit 22-27
TRADITIONAL = {"02", "03", "04", "05", "13", "14", "15", "16", "17", "22", "23", "24", "25", "26", "27"}
SUPPRESSED_SHARE = 0.25
TODAY = dt.date.today().isoformat()


def label(y):
    return f"{y - 1}-{y}"


def num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip().replace(",", ""))
    except ValueError:
        return None       # "*", "*n<10", "Redacted"


def cname(n):
    n = n.upper().strip().replace("SAINT ", "ST ")
    return "".join(c for c in n if c.isalnum())


GEO = json.loads((PROC / "geo.json").read_text())
BYNAME = {cname(v["name"].replace(" County", "")): k for k, v in GEO["counties"].items()}
assert sorted(BYNAME.values()) == COUNTIES


def general_rows(y, want="General"):
    """Rows of one sheet (General by default) as dicts, with RCDTS without dashes and a level field."""
    body = cached(RAW / "isbe" / FILES[y], ISBE + FILES[y], timeout=600)
    wb = openpyxl.load_workbook(io.BytesIO(body), read_only=True, data_only=True)
    sheet = want if want in wb.sheetnames else None
    if sheet is None:
        for sn in wb.sheetnames:
            head = next(wb[sn].iter_rows(max_row=1, values_only=True))
            if "Chronic Absenteeism" in [str(h).strip() if h else "" for h in head]:
                sheet = sn
                break
    it = wb[sheet].iter_rows(values_only=True)
    head = [str(h).strip() if h is not None else "" for h in next(it)]
    out = []
    for r in it:
        d = dict(zip(head, r))
        d["rcdts"] = str(d.get("RCDTS") or "").replace("-", "").strip()
        d["level"] = str(d.get("Type") or d.get("Level") or "").strip()
        out.append(d)
    return out, head


tests = {m: {} for m in SUBJ}           # mid -> year -> county -> [num, den, n_districts, suppressed_g3, all_g3]
absent = {}                             # year -> county -> [num, den, n_districts]
isbe_state = {m: {} for m in list(SUBJ) + ["chronic_absent_rate"]}
left = {}
for y in FILES:
    rows, head = general_rows(y)
    wcol = "# Student Enrollment" if "# Student Enrollment" in head else "Student Enrollment - Total"
    assert wcol in head and "Chronic Absenteeism" in head, (y, wcol)
    dist = [d for d in rows if d["level"] == "District"]
    st = [d for d in rows if d["level"] == "Statewide"]
    assert len(st) == 1, (y, len(st))
    isbe_state["chronic_absent_rate"][y] = num(st[0]["Chronic Absenteeism"])
    a = {f: [0.0, 0.0, 0] for f in COUNTIES}
    out_of = {"not a traditional district": 0, "no county": 0, "suppressed": 0}
    for d in dist:
        f = BYNAME.get(cname(str(d.get("County") or "")))
        if f is None:
            out_of["no county"] += 1
            continue
        if d["rcdts"][9:11] not in TRADITIONAL:
            out_of["not a traditional district"] += 1
            continue
        n, p = num(d[wcol]), num(d["Chronic Absenteeism"])
        if n is None or p is None or n <= 0:
            out_of["suppressed"] += 1
            continue
        a[f][0] += n * p / 100
        a[f][1] += n
        a[f][2] += 1
    absent[y] = a
    left[("chronic_absent_rate", y)] = out_of
    if y in TEST_YEARS:
        # the IAR results are on their own sheet; third grade enrollment and the county are on General
        iar, ihead = general_rows(y, "IAR")
        iar = {d["rcdts"]: d for d in iar if d["level"] in ("District", "Statewide")}
        assert G3 in head, y
        for mid, (rc, pc) in SUBJ.items():
            assert rc in ihead and pc in ihead, (y, mid)
            isbe_state[mid][y] = num(iar[st[0]["rcdts"]][rc])
            t = {f: [0.0, 0.0, 0, 0.0, 0.0] for f in COUNTIES}
            out_t = {"no county": 0, "suppressed": 0, "no grade 3": 0}
            for d in dist:
                g3 = num(d.get(G3))
                if not g3:
                    out_t["no grade 3"] += 1
                    continue
                f = BYNAME.get(cname(str(d.get("County") or "")))
                if f is None:
                    out_t["no county"] += 1
                    continue
                t[f][4] += g3
                i = iar.get(d["rcdts"], {})
                rate, part = num(i.get(rc)), num(i.get(pc))
                if rate is None or part is None:
                    out_t["suppressed"] += 1
                    t[f][3] += g3
                    continue
                n = g3 * part / 100
                t[f][0] += rate * n / 100
                t[f][1] += n
                t[f][2] += 1
            tests[mid][y] = t
            left[(mid, y)] = out_t
    print(f"{y}: {len(dist)} district rows; chronic absence left out {out_of}"
          + "".join(f"; {m[:10]} left out {left[(m, y)]}" for m in SUBJ if (m, y) in left))


# --------------------------------------------------------------------------- assemble
def series_of(by_year, f=None, small=False):
    out, flagged = [], False
    for y in sorted(by_year):
        agg = by_year[y]
        if f is None:
            nm, den = sum(v[0] for v in agg.values()), sum(v[1] for v in agg.values())
        else:
            nm, den = agg[f][0], agg[f][1]
            if small and agg[f][4] and agg[f][3] / agg[f][4] >= SUPPRESSED_SHARE:
                nm, den = 0.0, 0.0
                flagged = y == max(by_year)
        out.append([label(y), nm / den * 100 if den else None])
    return out, flagged


def cell(s, flag=None):
    have = [(p, v) for p, v in s if v is not None]
    last_p = s[-1][0]
    if not have or have[-1][0] != last_p:
        return {"latest": None, "period": last_p, "series": s, "moe": None, "flag": flag or "missing"}
    return {"latest": have[-1][1], "period": last_p, "series": s, "moe": None, "flag": None}


SRC = "Illinois State Board of Education, Illinois Report Card Public Data Set"
LT, LA = label(max(TEST_YEARS)), label(max(FILES))
TVINT = f"report card years {', '.join(str(y) for y in TEST_YEARS)} (school years {', '.join(label(y) for y in TEST_YEARS)}); pulled {TODAY}"
AVINT = (f"report card years {', '.join(str(y) for y in FILES)} (school years {label(min(FILES))} to {LA}; 2019-2020 left out); "
         f"pulled {TODAY}")
n_flag = {m: sum(1 for f in COUNTIES if series_of(tests[m], f, small=True)[1]) for m in SUBJ}
TEST_NOTE = ("Share of tested third graders who scored Proficient or Above Proficient on the Illinois Assessment of "
             "Readiness (IAR) {subj} test. Illinois set new proficiency levels starting with the spring 2025 tests, "
             "and ISBE says not to compare those results with earlier years, so the figures start in 2024-2025. "
             "County figures combine every district with third graders, placed in the county ISBE lists for the "
             "district and weighted by third grade enrollment times the share tested. ISBE does not report a "
             "district's rate when fewer than 10 students were proficient (in 2025-2026) or tested; those districts "
             "are left out, which can raise a county's figure, and a county where they hold a quarter or more of "
             f"third graders shows no value ({{n}} in {LT}). The {SNAME} figure is built the same way from the same "
             f"districts; ISBE's own statewide figure was {{isbe:.1f}}% in {LT}.")
METRICS = {
    "grade3_ela_proficient": {
        "label": "Third graders proficient or above in English language arts (state test)", "theme": "people",
        "unit": "pct", "decimals": 1, "better": "higher", "source": SRC, "vintage": TVINT,
        "period_label": f"{LT} school year",
        "note": TEST_NOTE.format(subj="English language arts", n=n_flag["grade3_ela_proficient"],
                                 isbe=isbe_state["grade3_ela_proficient"][max(TEST_YEARS)])},
    "grade3_math_proficient": {
        "label": "Third graders proficient in math (proficient or above on the state math test)", "theme": "education",
        "unit": "pct", "decimals": 1, "better": "higher", "source": SRC, "vintage": TVINT,
        "period_label": f"{LT} school year",
        "note": TEST_NOTE.format(subj="math", n=n_flag["grade3_math_proficient"],
                                 isbe=isbe_state["grade3_math_proficient"][max(TEST_YEARS)])},
    "chronic_absent_rate": {
        "label": "Students chronically absent (missed 10% or more of school)", "theme": "education",
        "unit": "pct", "decimals": 1, "better": "lower", "source": SRC, "vintage": AVINT,
        "period_label": f"{LA} school year",
        "note": ("Share of students who missed 10% or more of school days, for any reason, excused or not. County "
                 "figures cover elementary, high school and unit districts, placed in the county ISBE lists for the "
                 "district and weighted by enrollment; charter schools that are their own districts and regional "
                 "programs are left out, and so are districts whose figure ISBE suppresses. Each student attends one "
                 f"district, so overlapping elementary and high school districts do not count anyone twice. The "
                 f"{SNAME} figure is built the same way; ISBE's own statewide figure was "
                 f"{isbe_state['chronic_absent_rate'][max(FILES)]:.1f}% in {LA}. 2019-2020 is left out because "
                 "school buildings closed in March 2020.")},
}

counties = {f: {} for f in COUNTIES}
state = {}
for mid in SUBJ:
    for f in COUNTIES:
        s, fl = series_of(tests[mid], f, small=True)
        counties[f][mid] = cell(s, "suppressed" if fl else None)
    state[mid] = cell(series_of(tests[mid])[0])
for f in COUNTIES:
    counties[f]["chronic_absent_rate"] = cell(series_of(absent, f)[0])
state["chronic_absent_rate"] = cell(series_of(absent)[0])

pub = {m: {label(y): v for y, v in isbe_state[m].items()} for m in isbe_state}
left_out = {m: {label(y): v for (mm, y), v in left.items() if mm == m} for m in isbe_state}
write_json("reading.json", {"metrics": {"grade3_ela_proficient": METRICS["grade3_ela_proficient"]},
                            "counties": {f: {"grade3_ela_proficient": c["grade3_ela_proficient"]} for f, c in counties.items()},
                            SK: {"grade3_ela_proficient": state["grade3_ela_proficient"]},
                            "extras": {"isbe_state_published": pub["grade3_ela_proficient"],
                                       "districts_left_out": left_out["grade3_ela_proficient"]}})
write_json("schools.json", {"metrics": {k: METRICS[k] for k in ("grade3_math_proficient", "chronic_absent_rate")},
                            "counties": {f: {k: c[k] for k in ("grade3_math_proficient", "chronic_absent_rate")}
                                         for f, c in counties.items()},
                            SK: {k: state[k] for k in ("grade3_math_proficient", "chronic_absent_rate")},
                            "extras": {"isbe_state_published": {k: pub[k] for k in ("grade3_math_proficient", "chronic_absent_rate")},
                                       "districts_left_out": {k: left_out[k] for k in ("grade3_math_proficient", "chronic_absent_rate")}}})

for mid in METRICS:
    print(f"\n{mid}")
    for p, v in state[mid]["series"]:
        print(f"  {p}: built {v:5.1f}  ISBE {isbe_state[mid][int(p[-4:])]:5.1f}")
    lv = [c[mid]["latest"] for c in counties.values() if c[mid]["latest"] is not None]
    print(f"  latest county range {min(lv):.1f} to {max(lv):.1f}, n={len(lv)}; "
          f"flags {sorted({c[mid]['flag'] for c in counties.values() if c[mid]['flag']})}")
