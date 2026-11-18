"""Georgia schools layers: third grade reading and math results and chronic absence, from GOSA files.

The Georgia counterpart of 40_reading.py and 44_schools.py. Run with D4TP_STATE=ga.

Sources
  1. Georgia Governor's Office of Student Achievement (GOSA) downloadable data, https://download.gosa.ga.gov/
     (open files, one folder per year; saved in data/raw/ga/gosa/):
       EOG_by_GRADE files    Georgia Milestones End-of-Grade results by grade, school years 2017-18 to 2024-25
                             (no test in 2019-20). One row per system or school, grade, subgroup and subject.
       Attendance files      Share of students absent more than 10% of enrolled days, 2017-18 to 2024-25.
  2. NCES Common Core of Data (CCD) district and school directories, from the Urban Institute Education Data
     Portal API (cached in data/raw/ga/urban_ccd/): the county of each school system and the virtual flag for
     state charter schools.

Method (the same shape as Ohio's layers, with Georgia's own counts as weights)
  grade3_ela_proficient, grade3_math_proficient: share of tested third graders at Proficient or Distinguished.
    County = sum(proficient_or_above_s) / sum(tested_s) over the county's school system, any city school systems
    in the county, and in-person state charter schools in the county (counties from CCD). Virtual state charter
    schools and the state schools for the deaf and blind are left out. Systems whose counts GOSA suppresses
    ("TFS", too few students) are left out. Georgia = the same sum over every county.
  chronic_absent_rate: share of students absent more than 10% of enrolled days. County and city school systems
    only (as in Ohio, where only traditional districts are used), weighted by GOSA's student count.
    Georgia = the same weighted sum. 2019-20 is left out because school buildings closed in March 2020.

GOSA's own statewide figures, which include every school, are kept in extras for the tie-out.

Writes data/processed/ga/reading.json and data/processed/ga/schools.json.
Run: D4TP_STATE=ga .venv/bin/python scripts/47_schools_ga.py
"""
import csv
import datetime as dt
import io
import json

from common import COUNTIES, RAW, SK, SNAME, ST_ID, cached, write_json

if ST_ID != "ga":
    raise SystemExit("This layer reads Georgia GOSA files. Run it with D4TP_STATE=ga.")

GOSA = "https://download.gosa.ga.gov/"
EOG = {   # GOSA folder year (spring of the school year) -> file
    2018: "2018/EOG_2018_By_Grad_FEB_24_2020.csv",
    2019: "2019/EOG_2019_By_Grad_FEB_24_2020.csv",
    2021: "2021/EOG_2021_by_grade_March_7_2022.csv",
    2022: "2022/EOG_by_GRADE_2022_Dec08_2022.csv",
    2023: "2023/EOG_by_GRADE_2022-23__GA_TST_AGGR_2023-12-15_18_54_21.csv",
    2024: "2024/EOG_by_GRADE_2023-24__GA_TST_AGGR_2025-01-14_16_19_30.csv",
    2025: "2025/EOG_by_GRADE_2024-25__GA_TST_AGGR_2026-02-19_00_31_27.csv",
}
ATT = {
    2018: "2018/Attendance_2018_DEC_10th_2018.csv",
    2019: "2019/Attendance_2019_Dec2nd_2019.csv",
    2021: "2021/Attendance_2021_Dec062021.csv",
    2022: "2022/Attendance_2022_Dec072022.csv",
    2023: "2023/Attendance_2022-23_2025-06-17_14_52_53.csv",
    2024: "2024/Attendance_2023-24_2025-06-17_15_16_08.csv",
    2025: "2025/Attendance_2024-25_2026-02-19_00_32_26.csv",
}
SUBJ = {"grade3_ela_proficient": "English Language Arts", "grade3_math_proficient": "Mathematics"}
TODAY = dt.date.today().isoformat()


def label(y):
    return f"{y - 1}-{y}"


def num(x):
    x = (x or "").strip().replace(",", "")
    try:
        return float(x)
    except ValueError:
        return None      # "TFS" (too few students) and blanks


def gosa(rel):
    body = cached(RAW / "gosa" / rel.split("/")[-1], GOSA + rel)
    return list(csv.DictReader(io.StringIO(body.decode("latin-1"))))


# --------------------------------------------------------------------------- CCD: county and virtual flag
URBAN = "https://educationdata.urban.org/api/v1"


def urban(path, name):
    out, url, page = [], f"{URBAN}/{path}", 0
    while url:
        page += 1
        raw = json.loads(cached(RAW / "urban_ccd" / f"{name}_p{page}.json", url))
        out += raw["results"]
        url = raw.get("next")
    return out


county_of, virtual, kind = {}, {}, {}
for y in range(2017, 2025):
    for r in urban(f"school-districts/ccd/directory/{y}/?fips=13", f"lea_dir_{y}"):
        code = (r.get("state_leaid") or "").replace("GA-", "")
        if code and r.get("county_code"):
            county_of[code] = str(r["county_code"]).zfill(5)     # the latest year wins
            kind[code] = r.get("agency_type")
    for r in urban(f"schools/ccd/directory/{y}/?fips=13", f"sch_dir_{y}"):
        code = (r.get("state_leaid") or "").replace("GA-", "")
        if code[:3] in ("782", "783") and r.get("virtual") is not None and r["virtual"] >= 0:
            # CCD codes 1+ mean full or mostly virtual; kept by year, since some in-person schools were flagged in 2020
            virtual[(code, y)] = max(virtual.get((code, y), 0), r["virtual"])


def is_virtual(code, year):
    """CCD virtual flag for the school year ending in `year` (CCD year = year - 1), else the nearest year CCD has."""
    have = sorted((abs(yy - (year - 1)), yy) for (c, yy) in virtual if c == code)
    return bool(have) and virtual[(code, have[0][1])] >= 1


def system_type(code):
    if code.isdigit() and len(code) == 3 and 601 <= int(code) <= 759:
        return "county"
    if code.isdigit() and len(code) == 3 and 760 <= int(code) <= 798:
        return "city"
    if code[:3] in ("782", "783"):
        return "charter"
    return "other"      # 799 state schools, and anything else


def place(code, charters, year):
    """County FIPS for a system, or None with the reason."""
    t = system_type(code)
    if t == "other":
        return None, "state schools"
    if t == "charter":
        if not charters:
            return None, "state charter school"
        if is_virtual(code, year):
            return None, "virtual state charter school"
    f = county_of.get(code)
    if f is None:
        raise SystemExit(f"system {code}: no county in the CCD directory")
    if t == "county":
        # county systems are 601-759 in near-alphabetical order (McDuffie and McIntosh follow Marion), so the county
        # comes from CCD; it must be a Georgia county
        assert f in COUNTIES, (code, f)
    return f, None


# --------------------------------------------------------------------------- tests
def rollup(rows, value, weight, charters, year):
    """{county: (numerator, denominator, systems)} plus a list of systems left out and why."""
    agg = {f: [0.0, 0.0, []] for f in COUNTIES}
    left = []
    for r in rows:
        code = r["code"]
        f, why = place(code, charters, year)
        w, v = weight(r), value(r)
        if f is None:
            left.append((code, r["name"], why, w))
            continue
        if w is None or v is None or w <= 0:
            left.append((code, r["name"], "suppressed", w))
            continue
        agg[f][0] += v
        agg[f][1] += w
        agg[f][2].append(code)
    return agg, left


tests, gosa_state, tested_state, test_left = {m: {} for m in SUBJ}, {m: {} for m in SUBJ}, {}, {}
for y, rel in EOG.items():
    rows = gosa(rel)
    g3 = [r for r in rows if r["ACDMC_LVL"].strip().lstrip("0") == "3" and r["SUBGROUP_NAME"] == "All Students"]
    assert g3, f"{rel}: no grade 3 rows"
    for mid, subj in SUBJ.items():
        sys_rows = []
        for r in g3:
            if r["TEST_CMPNT_TYP_NM"] != subj or r["INSTN_NUMBER"] != "ALL":
                continue
            if r["SCHOOL_DISTRCT_CD"] == "ALL":
                gosa_state[mid][y] = num(r["PROFICIENT_PCT"]) + num(r["DISTINGUISHED_PCT"])
                tested_state[(mid, y)] = num(r["NUM_TESTED_CNT"])
                continue
            n = num(r["NUM_TESTED_CNT"])
            pc, dc = num(r["PROFICIENT_CNT"]), num(r["DISTINGUISHED_CNT"])
            pp, dp = num(r["PROFICIENT_PCT"]), num(r["DISTINGUISHED_PCT"])
            if pc is not None and dc is not None:
                prof = pc + dc
            elif n is not None and pp is not None and dp is not None:
                prof = n * (pp + dp) / 100
            else:
                prof = None
            sys_rows.append({"code": r["SCHOOL_DISTRCT_CD"].strip(), "name": r["SCHOOL_DSTRCT_NM"], "n": n, "prof": prof})
        codes = [r["code"] for r in sys_rows]
        assert len(codes) == len(set(codes)), f"{rel} {subj}: duplicate system rows"
        agg, left = rollup(sys_rows, lambda r: r["prof"], lambda r: r["n"], charters=True, year=y)
        tests[mid][y] = agg
        test_left[(mid, y)] = left
        assert y in gosa_state[mid], f"{rel} {subj}: no state row"

# --------------------------------------------------------------------------- attendance
absent, gosa_absent, absent_left = {}, {}, {}
for y, rel in ATT.items():
    rows = [r for r in gosa(rel) if r["INSTN_NUMBER"] == "ALL"]
    sys_rows = []
    for r in rows:
        code = r["SCHOOL_DSTRCT_CD"].strip()
        if code == "ALL":
            gosa_absent[y] = num(r["CHRONIC_ABSENT_PERC_ALL"])
            continue
        n, p = num(r["STUDENT_COUNT_ALL"]), num(r["CHRONIC_ABSENT_PERC_ALL"])
        sys_rows.append({"code": code, "name": r["SCHOOL_DSTRCT_NM"], "n": n,
                         "abs": n * p / 100 if n is not None and p is not None else None})
    codes = [r["code"] for r in sys_rows]
    assert len(codes) == len(set(codes)), f"{rel}: duplicate system rows"
    agg, left = rollup(sys_rows, lambda r: r["abs"], lambda r: r["n"], charters=False, year=y)
    absent[y] = agg
    absent_left[y] = left
    assert y in gosa_absent, f"{rel}: no state row"


# --------------------------------------------------------------------------- assemble
def series_of(by_year, f=None):
    out = []
    for y in sorted(by_year):
        agg = by_year[y]
        if f is None:
            num_, den = sum(v[0] for v in agg.values()), sum(v[1] for v in agg.values())
        else:
            num_, den = agg[f][0], agg[f][1]
        out.append([label(y), num_ / den * 100 if den else None])
    return out


def cell(s):
    have = [(p, v) for p, v in s if v is not None]
    last_p = s[-1][0]
    if not have or have[-1][0] != last_p:
        return {"latest": None, "period": last_p, "series": s, "moe": None, "flag": "missing"}
    return {"latest": have[-1][1], "period": last_p, "series": s, "moe": None, "flag": None}


SRC = ("Georgia Governor's Office of Student Achievement (GOSA), Georgia Milestones End-of-Grade results; "
       "NCES Common Core of Data for school system counties")
ASRC = "Georgia Governor's Office of Student Achievement (GOSA), attendance files; NCES Common Core of Data for school system counties"
TVINT = (f"school years {', '.join(label(y) for y in EOG)} (no test in 2019-2020); GOSA files dated 2020-02 to "
         f"2026-02-19; pulled {TODAY}")
AVINT = f"school years {', '.join(label(y) for y in ATT)} (2019-2020 left out); GOSA files dated 2018-12 to 2026-02-19; pulled {TODAY}"
LATEST = label(max(EOG))
SMALL = sorted(f for f in COUNTIES if 0 < tests["grade3_ela_proficient"][max(EOG)][f][1] < 30)
SMALL_NOTE = (f" In {LATEST}, {len(SMALL)} {'county' if len(SMALL) == 1 else 'counties'} tested fewer than 30 third "
              f"graders, so {'its figure' if len(SMALL) == 1 else 'their figures'} can swing a lot from year to year.") if SMALL else ""
TEST_NOTE = ("Share of tested third graders who scored Proficient or Distinguished on the Georgia Milestones "
             "{subj} test. County figures combine the county school system, any city school systems in the county "
             "and in-person state charter schools, weighted by the number of students tested; virtual state "
             "charter schools and systems too small for GOSA to report are left out. Fewer students tested in "
             f"2020-2021. The {SNAME} figure is built the same way from the same systems so counties compare on "
             "equal terms; GOSA's own statewide figure, which counts every school, was {gosa:.1f}% in {latest}." + SMALL_NOTE)
METRICS = {
    "grade3_ela_proficient": {
        "label": "Third graders proficient or above in English language arts (state test)", "theme": "people",
        "unit": "pct", "decimals": 1, "better": "higher", "source": SRC, "vintage": TVINT,
        "period_label": f"{LATEST} school year",
        "note": TEST_NOTE.format(subj="English language arts", gosa=gosa_state["grade3_ela_proficient"][max(EOG)],
                                 latest=LATEST)},
    "grade3_math_proficient": {
        "label": "Third graders proficient in math (proficient or above on the state math test)", "theme": "education",
        "unit": "pct", "decimals": 1, "better": "higher", "source": SRC, "vintage": TVINT,
        "period_label": f"{LATEST} school year",
        "note": TEST_NOTE.format(subj="math", gosa=gosa_state["grade3_math_proficient"][max(EOG)], latest=LATEST)
        + " Georgia began testing new math standards in 2023-2024, so earlier years may not compare."},
    "chronic_absent_rate": {
        "label": "Students chronically absent (missed 10% or more of school)", "theme": "education",
        "unit": "pct", "decimals": 1, "better": "lower", "source": ASRC, "vintage": AVINT,
        "period_label": f"{label(max(ATT))} school year",
        "note": ("Share of students absent more than 10% of the days they were enrolled, for any reason, excused or "
                 "not. County figures cover county and city school systems only, weighted by GOSA's student count; "
                 f"state charter schools are left out. The {SNAME} figure is built the same way from all county and "
                 f"city systems; GOSA's own statewide figure, which counts every school, was "
                 f"{gosa_absent[max(ATT)]:.1f}% in {label(max(ATT))}. 2019-2020 is left out because school "
                 "buildings closed in March 2020.")},
}

by_metric = {"grade3_ela_proficient": tests["grade3_ela_proficient"],
             "grade3_math_proficient": tests["grade3_math_proficient"], "chronic_absent_rate": absent}
counties = {f: {} for f in COUNTIES}
state = {}
for mid, by_year in by_metric.items():
    for f in COUNTIES:
        counties[f][mid] = cell(series_of(by_year, f))
    state[mid] = cell(series_of(by_year))


def detail(by_year, left):
    return {label(y): {"systems_by_county": {f: v[2] for f, v in by_year[y].items() if v[2]},
                       "left_out": [{"code": c, "name": n, "why": w, "weight": wt} for c, n, w, wt in left[y]]}
            for y in by_year}


extras_r = {"reading_rollup_detail": detail(tests["grade3_ela_proficient"],
                                             {y: test_left[("grade3_ela_proficient", y)] for y in EOG}),
            "gosa_state_published": {label(y): v for y, v in gosa_state["grade3_ela_proficient"].items()}}
extras_s = {"schools_rollup_detail": {
                "grade3_math_proficient": detail(tests["grade3_math_proficient"],
                                                 {y: test_left[("grade3_math_proficient", y)] for y in EOG}),
                "chronic_absent_rate": detail(absent, absent_left)},
            "gosa_state_published": {
                "grade3_math_proficient": {label(y): v for y, v in gosa_state["grade3_math_proficient"].items()},
                "chronic_absent_rate": {label(y): v for y, v in gosa_absent.items()}}}

write_json("reading.json", {"metrics": {"grade3_ela_proficient": METRICS["grade3_ela_proficient"]},
                            "counties": {f: {"grade3_ela_proficient": c["grade3_ela_proficient"]} for f, c in counties.items()},
                            SK: {"grade3_ela_proficient": state["grade3_ela_proficient"]}, "extras": extras_r})
write_json("schools.json", {"metrics": {k: METRICS[k] for k in ("grade3_math_proficient", "chronic_absent_rate")},
                            "counties": {f: {k: c[k] for k in ("grade3_math_proficient", "chronic_absent_rate")}
                                         for f, c in counties.items()},
                            SK: {k: state[k] for k in ("grade3_math_proficient", "chronic_absent_rate")},
                            "extras": extras_s})

# --------------------------------------------------------------------------- report
for mid in by_metric:
    pub = gosa_state.get(mid) or gosa_absent
    s = state[mid]["series"]
    print(f"\n{mid}")
    for p, v in s:
        y = int(p[-4:])
        n_c = sum(1 for f in COUNTIES if by_metric[mid][y][f][1] > 0)
        print(f"  {p}: built {v:5.1f}  GOSA {pub[y]:5.1f}  counties with a value {n_c}/159"
              + (f"  state tested {tested_state[(mid, y)]:,.0f}" if (mid, y) in tested_state else ""))
    lv = [c[mid]["latest"] for c in counties.values() if c[mid]["latest"] is not None]
    print(f"  latest county range {min(lv):.1f} to {max(lv):.1f}, n={len(lv)}")
left_latest = test_left[("grade3_ela_proficient", max(EOG))]
print("\nleft out of grade 3 ELA, latest year:", sorted({w for _, _, w, _ in left_latest}),
      sum(wt or 0 for _, _, w, wt in left_latest if w != "suppressed"), "students tested")
