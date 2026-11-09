"""Health layer plus annual model-based income and poverty series.

Sources
  1. Census SAHIE (uninsured rates, under 65), 2008-latest
  2. CDC NCHS VSRR provisional county drug overdose deaths (12-month-ending), plus the
     VSRR state file for the Ohio figure; Census county population estimates for rates
  3. CDC PLACES county data, latest release (model-based BRFSS prevalence)
  4. Census SAIPE (poverty rates and median household income), 2000-latest

Writes data/processed/health.json. Run: .venv/bin/python scripts/30_health.py
"""
import csv
import datetime as dt
import io
import json
import urllib.parse

from common import RAW, STATE, cached, census, write_json

TODAY = dt.date.today().isoformat()
COUNTIES = [f"39{n:03d}" for n in range(1, 176, 2)]
assert len(COUNTIES) == 88

metrics = {}
counties = {f: {} for f in COUNTIES}
ohio = {}
extras = {}


def num(x):
    if x is None:
        return None
    x = str(x).strip()
    if x in ("", ".", "-", "N/A", "null"):
        return None
    return float(x)


def check_series(series, where):
    periods = [p for p, _ in series]
    if len(periods) != len(set(periods)):
        raise SystemExit(f"duplicate periods in {where}")
    if periods != sorted(periods):
        raise SystemExit(f"series out of order in {where}")


def entry(series, moe=None, flag=None):
    """Build one county/ohio metric entry from a chronological series of (period, value)."""
    series = sorted(series)
    if not series:
        return {"latest": None, "period": None, "series": [], "moe": None, "flag": flag or "no data"}
    p, v = series[-1]
    return {"latest": v, "period": p, "series": [list(s) for s in series], "moe": moe,
            "flag": flag if flag else (None if v is not None else "missing")}


def put(metric_id, geo, e):
    if geo == "ohio":
        ohio[metric_id] = e
    else:
        counties[geo][metric_id] = e


# --------------------------------------------------------------------------- 1. SAHIE
SAHIE_FIRST = 2008  # ACS-based SAHIE starts in 2008; 2006-2007 are not comparable


def sahie(iprcat, metric_id, label, note):
    base = {"get": "NAME,PCTUI_PT,PCTUI_MOE,PCTUI_LB90,PCTUI_UB90,YEAR",
            "AGECAT": "0", "IPRCAT": iprcat, "SEXCAT": "0", "RACECAT": "0"}
    cty = census("timeseries/healthins/sahie", dict(base, **{"for": "county:*", "in": f"state:{STATE}"}),
                 f"sahie_county_ipr{iprcat}.json")
    st = census("timeseries/healthins/sahie", dict(base, **{"for": f"state:{STATE}"}),
                f"sahie_state_ipr{iprcat}.json")
    years = set()
    for geo, rows in [("ohio", st)] + [(f, [r for r in cty if STATE + r["county"] == f]) for f in COUNTIES]:
        rows = [r for r in rows if int(r["YEAR"]) >= SAHIE_FIRST]
        ser = sorted((r["YEAR"], num(r["PCTUI_PT"])) for r in rows)
        check_series(ser, f"{metric_id} {geo}")
        years.update(p for p, _ in ser)
        last = max(rows, key=lambda r: int(r["YEAR"])) if rows else None
        put(metric_id, geo, entry(ser, moe=num(last["PCTUI_MOE"]) if last else None))
    latest = max(years)
    metrics[metric_id] = {
        "label": label, "theme": "health", "unit": "pct", "decimals": 1, "better": "lower",
        "source": "U.S. Census Bureau, Small Area Health Insurance Estimates (SAHIE)",
        "vintage": f"annual {min(years)}-{latest}; pulled {TODAY}",
        "period_label": latest, "note": note,
    }


sahie("0", "uninsured_under65", "Uninsured rate, under age 65",
      "Share of people under 65 with no health insurance. SAHIE is a model-based estimate that "
      "combines survey and administrative records; the margin shown is the 90% margin of error.")
sahie("1", "uninsured_under65_low_income", "Uninsured rate, under 65 with low income",
      "Share of people under 65 with income at or below 200% of the poverty line with no health "
      "insurance. Model-based estimate; the margin shown is the 90% margin of error.")

# --------------------------------------------------------------------------- 2. Overdose deaths
CDC = "https://data.cdc.gov/resource/{}.json?"


def socrata(ds, params, name):
    url = CDC.format(ds) + urllib.parse.urlencode(params)
    return json.loads(cached(RAW / "cdc" / name, url))


od = socrata("gb4e-yj24", {"$where": "st_abbrev='OH'", "$limit": "50000", "$order": "fips,monthendingdate"},
             "vsrr_county_overdose_oh.json")
od_state = socrata("xkb8-kh2a", {"$where": "state='OH' and indicator='Number of Drug Overdose Deaths'",
                                 "$limit": "50000"}, "vsrr_state_overdose_oh.json")

# Census county population estimates (July 1), vintage 2025
pop_raw = cached(RAW / "census_pep" / "co-est2025-alldata.csv",
                 "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv")
pop = {}
for r in csv.DictReader(io.StringIO(pop_raw.decode("latin-1"))):
    if r["STATE"] != STATE:
        continue
    geo = "ohio" if r["SUMLEV"] == "040" else STATE + r["COUNTY"]
    pop[geo] = {y: int(r[f"POPESTIMATE{y}"]) for y in range(2020, 2026)}
POP_LAST = 2025
assert all(f in pop for f in COUNTIES), "population file missing a county"


def popfor(geo, year):
    return pop[geo][min(int(year), POP_LAST)]


SUPP = "suppressed (1-9 deaths)"
monthly = {f: [] for f in COUNTIES}  # (period, value, flag)
as_of = set()
for r in od:
    f = r["fips"].zfill(5)
    if f not in monthly:
        continue
    period = r["monthendingdate"][:7]
    v = num(r.get("provisional_drug_overdose"))
    flag = None
    if v is None:
        flag = SUPP if "suppress" in (r.get("footnote") or "").lower() else "missing"
    monthly[f].append((period, v, flag))
    as_of.add(r["data_as_of"][:10])

all_months = sorted({p for m in monthly.values() for p, _, _ in m})
od_latest = all_months[-1]
keep = sorted({p for p in all_months if p.endswith("-12")} | {od_latest})
supp_counts = {"latest": 0, "any_kept_period": 0}
od_monthly_extra = {}
for f in COUNTIES:
    m = sorted(monthly[f])
    check_series([(p, v) for p, v, _ in m], f"overdose {f}")
    if len(m) != len(all_months):
        raise SystemExit(f"overdose {f}: {len(m)} months, expected {len(all_months)}")
    kept = [x for x in m if x[0] in keep]
    od_monthly_extra[f] = [[p, v] for p, v, _ in m]
    last = kept[-1]
    supp_counts["latest"] += last[2] == SUPP
    supp_counts["any_kept_period"] += any(x[2] == SUPP for x in kept)
    put("overdose_deaths_12mo", f, entry([(p, v) for p, v, _ in kept], flag=last[2]))
    rate = [(p, (v / popfor(f, p[:4]) * 1e5) if v is not None else None) for p, v, _ in kept]
    put("overdose_rate_per100k", f, entry(rate, flag=last[2]))

MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                      "September", "October", "November", "December"], 1)}
st_ser = {}
st_note = {}
for r in od_state:
    if r.get("period") != "12 month-ending":
        continue
    p = f"{r['year']}-{MONTHS[r['month']]:02d}"
    if p in st_ser:
        raise SystemExit(f"duplicate Ohio overdose period {p}")
    st_ser[p] = num(r.get("data_value"))
    st_note[p] = r.get("footnote")
oh_kept = [(p, st_ser.get(p)) for p in keep]
put("overdose_deaths_12mo", "ohio", entry(oh_kept))
put("overdose_rate_per100k", "ohio",
    entry([(p, v / popfor("ohio", p[:4]) * 1e5 if v is not None else None) for p, v in oh_kept]))
od_monthly_extra["ohio"] = [[p, st_ser[p]] for p in sorted(st_ser) if p >= all_months[0]]
extras["overdose_12mo_monthly"] = od_monthly_extra

od_label = f"12 months ending {dt.date(int(od_latest[:4]), int(od_latest[5:]), 1).strftime('%B %Y')}"
od_vintage = (f"CDC provisional data as of {', '.join(sorted(as_of))}; 12-month periods ending "
              f"{all_months[0]} to {od_latest}; one point per December plus the latest month; pulled {TODAY}")
metrics["overdose_deaths_12mo"] = {
    "label": "Drug overdose deaths, past 12 months", "theme": "health", "unit": "count", "decimals": 0,
    "better": "lower", "source": "CDC NCHS, VSRR Provisional County-Level Drug Overdose Death Counts",
    "vintage": od_vintage, "period_label": od_label,
    "note": "Deaths of county residents from drug overdose in the 12 months ending in the month shown. "
            "Counts are provisional and tend to rise as records come in; CDC hides counts of 1 to 9. "
            "The Ohio figure comes from CDC's state file, which counts deaths that occurred in Ohio.",
}
metrics["overdose_rate_per100k"] = {
    "label": "Drug overdose deaths per 100,000 people, past 12 months", "theme": "health", "unit": "per100k",
    "decimals": 1, "better": "lower",
    "source": "CDC NCHS, VSRR Provisional County-Level Drug Overdose Death Counts; Census Bureau population estimates",
    "vintage": od_vintage + "; population estimates vintage 2025",
    "period_label": od_label,
    "note": "Our calculation: provisional 12-month deaths divided by the Census July 1 population for the "
            "year the period ends (2025 population for 2026 periods), times 100,000. Not age-adjusted; "
            "blank where CDC hides counts of 1 to 9.",
}

# --------------------------------------------------------------------------- 3. CDC PLACES
PLACES_DS = "swc5-untb"
pl_meta = json.loads(cached(RAW / "cdc" / "places_county_meta.json", f"https://data.cdc.gov/api/views/{PLACES_DS}.json"))
places = socrata(PLACES_DS, {"$where": "stateabbr='OH' and datavaluetypeid='AgeAdjPrv'", "$limit": "50000"},
                 "places_county_oh_ageadj.json")
PLACES = [  # metric id, PLACES measureid, label, better
    ("places_depression", "DEPRESSION", "Adults ever told they have depression", "lower"),
    ("places_mental_distress", "MHLTH", "Adults with frequent mental distress", "lower"),
    ("places_diabetes", "DIABETES", "Adults with diagnosed diabetes", "lower"),
    ("places_obesity", "OBESITY", "Adults with obesity", "lower"),
    ("places_smoking", "CSMOKING", "Adults who currently smoke cigarettes", "lower"),
    ("places_no_insurance_18_64", "ACCESS2", "Adults 18 to 64 without health insurance", "lower"),
    ("places_checkup", "CHECKUP", "Adults with a routine checkup in the past year", "higher"),
    ("places_food_insecurity", "FOODINSECU", "Adults with food insecurity in the past year", "lower"),
    ("places_housing_insecurity", "HOUSINSECU", "Adults with housing insecurity in the past year", "lower"),
    ("places_no_transportation", "LACKTRPT", "Adults without reliable transportation in the past year", "lower"),
]
pl_ci = {}
pl_supp = 0
for mid, code, label, better in PLACES:
    rows = {}
    for r in places:
        if r["measureid"] != code:
            continue
        f = r["locationid"]
        if f in rows:
            raise SystemExit(f"duplicate PLACES row {code} {f}")
        rows[f] = r
    years = {r["year"] for r in rows.values()}
    if len(years) != 1:
        raise SystemExit(f"PLACES {code}: more than one year {years}")
    year = years.pop()
    measure_text = next(iter(rows.values()))["measure"]
    for f in COUNTIES:
        r = rows.get(f)
        v = num(r.get("data_value")) if r else None
        flag = None
        if v is None:
            flag = (r.get("data_value_footnote") or "missing") if r else "missing"
            pl_supp += 1
        put(mid, f, {"latest": v, "period": year, "series": [[year, v]], "moe": None, "flag": flag})
        if r:
            pl_ci.setdefault(f, {})[mid] = [num(r.get("low_confidence_limit")), num(r.get("high_confidence_limit"))]
    put(mid, "ohio", {"latest": None, "period": year, "series": [], "moe": None,
                      "flag": "no state figure in PLACES county file"})
    metrics[mid] = {
        "label": label, "theme": "health", "unit": "pct", "decimals": 1, "better": better,
        "source": "CDC PLACES: Local Data for Better Health, County Data",
        "vintage": f"{pl_meta['name'].split(',')[-1].strip()} (BRFSS {year}); pulled {TODAY}",
        "period_label": f"{year} estimate, age-adjusted",
        "note": f"PLACES measure: {measure_text}. A model-based estimate built from the CDC BRFSS survey and "
                "Census population data, not a count; age-adjusted. The PLACES county file has no Ohio figure.",
    }
extras["places_ci95"] = pl_ci

# --------------------------------------------------------------------------- 4. SAIPE
SAIPE_FIRST = 2000
sp_vars = ("NAME,YEAR,SAEPOVRTALL_PT,SAEPOVRTALL_MOE,SAEPOVRT0_17_PT,SAEPOVRT0_17_MOE,"
           "SAEMHI_PT,SAEMHI_MOE")
sp_c = census("timeseries/poverty/saipe", {"get": sp_vars, "for": "county:*", "in": f"state:{STATE}"},
              "saipe_county.json")
sp_s = census("timeseries/poverty/saipe", {"get": sp_vars, "for": f"state:{STATE}"}, "saipe_state.json")
SAIPE = [
    ("saipe_poverty_rate", "SAEPOVRTALL", "Poverty rate, all ages (annual)", "pct", 1, "lower",
     "Share of people below the federal poverty line."),
    ("saipe_child_poverty_rate", "SAEPOVRT0_17", "Child poverty rate, ages 0 to 17 (annual)", "pct", 1, "lower",
     "Share of children under 18 below the federal poverty line."),
    ("saipe_median_income", "SAEMHI", "Median household income (annual)", "usd", 0, "higher",
     "Median household income in dollars of each year, not adjusted for inflation."),
]
sp_years = set()
for mid, var, label, unit, dec, better, what in SAIPE:
    for geo, rows in [("ohio", sp_s)] + [(f, [r for r in sp_c if STATE + r["county"] == f]) for f in COUNTIES]:
        rows = [r for r in rows if int(r["YEAR"]) >= SAIPE_FIRST]
        ser = sorted((r["YEAR"], num(r[var + "_PT"])) for r in rows)
        check_series(ser, f"{mid} {geo}")
        sp_years.update(p for p, _ in ser)
        last = max(rows, key=lambda r: int(r["YEAR"]))
        put(mid, geo, entry(ser, moe=num(last[var + "_MOE"])))
    metrics[mid] = {
        "label": label, "theme": "income", "unit": unit, "decimals": dec, "better": better,
        "source": "U.S. Census Bureau, Small Area Income and Poverty Estimates (SAIPE)",
        "vintage": f"annual {min(sp_years)}-{max(sp_years)}; pulled {TODAY}",
        "period_label": max(sp_years),
        "note": what + " SAIPE is a model-based estimate that combines survey, tax and SNAP records, "
                       "so it gives one value per year; the margin shown is the 90% margin of error.",
    }

# --------------------------------------------------------------------------- checks and write
for f in COUNTIES:
    missing = set(metrics) - set(counties[f])
    if missing:
        raise SystemExit(f"{f} missing {missing}")
write_json("health.json", {"metrics": metrics, "counties": counties, "ohio": ohio, "extras": extras})

print(f"counties: {len(counties)}; metrics: {len(metrics)}")
print(f"overdose latest {od_latest}; suppressed at latest: {supp_counts['latest']}; "
      f"suppressed in at least one kept period: {supp_counts['any_kept_period']}; PLACES nulls: {pl_supp}")
for f in ("39049", "39163", "ohio"):
    src = ohio if f == "ohio" else counties[f]
    print(f, {k: (v["period"], v["latest"], v["moe"], v["flag"]) for k, v in src.items()})
