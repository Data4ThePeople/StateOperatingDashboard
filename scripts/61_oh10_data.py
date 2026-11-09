"""Tract and district data for Ohio's 10th Congressional District (2025 map). Writes data/processed/oh10/data.json.

- ACS 5-year 2020-2024 for every 2020 census tract in Butler, Greene and Montgomery counties, plus Ohio (state:39)
  and the U.S. (us:1), all computed with the same code (20_acs.compute and the additions below).
- District values: the ACS table lines summed over the district's 220 tracts (margins of error combined as the
  square root of the sum of squares), then computed the same way. Medians cannot be summed, so the district's
  median household income is interpolated from its income brackets (B19001).
- CDC PLACES 2025 release, census tract data: modeled crude prevalence for adults 18 and older. District value
  = tract values weighted by adults 18 and older.
- County table: county-only measures for the three counties, read from the state dashboard's processed layers
  (same values the state page shows), with Ohio and U.S. figures where the state page has them.
"""
import importlib
import json
import math
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent))
from common import PROC, RAW, cached, census, write_json  # noqa: E402

acs = importlib.import_module("20_acs")
YEAR, PERIOD = 2024, "2020-2024"
COUNTIES = ["017", "057", "113"]
GEO = json.loads((PROC / "oh10" / "geo.json").read_text())
INSIDE = sorted(t for t, v in GEO["tracts"].items() if v["in_district"])
assert len(INSIDE) == 220
CV_MAX = 30.0          # an estimate whose coefficient of variation is above this is shown as unreliable
EXTRA = ["B23001", "B05012", "B03002", "B01001"]
TABLES = [t for t in acs.TABLES if t not in ("B19083", "B01002")] + EXTRA
PRIME_GROUPS = ("25 to 29 years", "30 to 34 years", "35 to 44 years", "45 to 54 years")
BRACKETS = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 75, 100, 125, 150, 200]   # B19001_002.._017 lower bounds, $000


def pull():
    """{geo: {var: (est, moe)}} for each tract ('39113000100'), 'ohio' and 'us'."""
    out = {}
    for t in TABLES:
        geos = [("tract_" + c, {"for": "tract:*", "in": f"state:39 county:{c}"}) for c in COUNTIES]
        geos += [("state", {"for": "state:39"}), ("us", {"for": "us:1"})]
        for tag, g in geos:
            rows = census(f"{YEAR}/acs/acs5", dict(get=f"NAME,group({t})", **g), f"oh10/acs5_{YEAR}_{t}_{tag}.json")
            for r in rows:
                key = "us" if tag == "us" else "ohio" if tag == "state" else r["state"] + r["county"] + r["tract"]
                d = out.setdefault(key, {})
                for k, v in r.items():
                    if k.startswith(t + "_") and k.endswith("E") and not k.endswith("EA"):
                        d[k[:-1]] = (acs.num(v), acs.moe_num(r.get(k[:-1] + "M")))
    return out


def b23001_lines():
    lab = acs.labels(YEAR, "B23001")
    tot, emp = [], []
    for k, l in lab.items():
        parts = [p.rstrip(":") for p in l.split("!!")]
        if not any(g in parts for g in PRIME_GROUPS):
            continue
        if parts[-1] in PRIME_GROUPS:
            tot.append(k)
        elif parts[-1] in ("Armed Forces", "In Armed Forces") or (parts[-1] == "Employed" and "Civilian" in parts):
            emp.append(k)
    assert len(tot) == 8 and len(emp) == 16, (len(tot), len(emp))
    return tot, emp


def b01001_lines():
    """Prime-age (25 to 54) and 65+ lines of B01001, both sexes."""
    lab = acs.labels(YEAR, "B01001")
    prime, old = [], []
    for k, l in lab.items():
        a = l.split("!!")[-1]
        if a in ("25 to 29 years", "30 to 34 years", "35 to 39 years", "40 to 44 years", "45 to 49 years", "50 to 54 years"):
            prime.append(k)
        elif a in ("65 and 66 years", "67 to 69 years", "70 to 74 years", "75 to 79 years", "80 to 84 years", "85 years and over"):
            old.append(k)
    assert len(prime) == 12 and len(old) == 12, (len(prime), len(old))
    return prime, old


def median_from_brackets(d):
    """Median household income ($) by linear interpolation within the B19001 bracket that holds the middle household."""
    n = [d.get(f"B19001_{i:03d}", (None,))[0] for i in range(2, 18)]
    if any(x is None for x in n) or sum(n) <= 0:
        return None
    half, c = sum(n) / 2, 0.0
    for i, x in enumerate(n):
        if c + x >= half and x > 0:
            if i == 15:
                return None          # middle household is in the open $200,000+ bracket
            lo, hi = BRACKETS[i], BRACKETS[i + 1]
            return 1000 * (lo + (half - c) / x * (hi - lo))
        c += x
    return None


PRIME_TOT, PRIME_EMP = b23001_lines()
AGE_PRIME, AGE_OLD = b01001_lines()


def compute(d):
    base = acs.compute(YEAR, d)
    out = {k: base[k] for k in ("median_household_income", "poverty_rate", "near_poverty_share", "below_200_share",
                                "snap_households_share", "population", "bachelors_or_higher", "hs_or_higher",
                                "rent_burden", "owner_cost_burden", "medicaid_share", "uninsured_acs", "disability_share")}
    s = acs.single
    out["prime_age_epop"] = acs.share(acs.total(d, PRIME_EMP), acs.total(d, PRIME_TOT))
    out["prime_age_share"] = acs.share(acs.total(d, AGE_PRIME), s(d, "B01001_001"))
    out["age65_share"] = acs.share(acs.total(d, AGE_OLD), s(d, "B01001_001"))
    out["female_share"] = acs.share(s(d, "B01001_026"), s(d, "B01001_001"))
    out["foreign_born_share"] = acs.share(s(d, "B05012_003"), s(d, "B05012_001"))
    tot = s(d, "B03002_001")
    out["nh_white_share"] = acs.share(s(d, "B03002_003"), tot)
    out["nh_black_share"] = acs.share(s(d, "B03002_004"), tot)
    out["hispanic_share"] = acs.share(s(d, "B03002_012"), tot)
    out["nh_asian_share"] = acs.share(s(d, "B03002_006"), tot)
    out["nh_multi_share"] = acs.share(s(d, "B03002_009"), tot)
    out["nh_other_share"] = acs.share(acs.total(d, ["B03002_005", "B03002_007", "B03002_008"]), tot)
    return out


def aggregate(dicts):
    keys = set().union(*dicts)
    out = {}
    for k in keys:
        vals = [d.get(k, (None, None)) for d in dicts]
        if any(v[0] is None for v in vals):
            out[k] = (None, None)
            continue
        m = None if any(v[1] is None for v in vals) else math.sqrt(sum(v[1] ** 2 for v in vals))
        out[k] = (sum(v[0] for v in vals), m)
    return out


NOTE_MOE = " ± is the 90% margin of error."
M = {   # id: label, theme, unit, decimals, better, note
    "poverty_rate": ("People in poverty", "income", "pct", 1, "lower", "People whose family income is below the federal poverty line (C17002)."),
    "near_poverty_share": ("People just above the poverty line (100% to 199%)", "income", "pct", 1, "lower", "People whose family income is between 100% and 199% of the federal poverty line (C17002)."),
    "below_200_share": ("People below 200% of the poverty line", "income", "pct", 1, "lower", "People in poverty plus those just above it (C17002). For a family of four in 2024, 200% of the poverty line was about $62,400 a year."),
    "median_household_income": ("Median household income", "income", "usd", 0, "higher", "Half of households earn more and half earn less, in 2024 dollars (B19013). The district figure is estimated from its income brackets (B19001), because medians cannot be added up across tracts."),
    "snap_households_share": ("Households that got SNAP food aid", "income", "pct", 1, "none", "Households that received SNAP at any time in the past 12 months, as reported in the survey (B22003). Surveys tend to undercount program use."),
    "rent_burden": ("Renters paying 30% or more of income on rent", "housing", "pct", 1, "lower", "Renter households whose gross rent is 30% or more of household income (B25070)."),
    "owner_cost_burden": ("Owners with a mortgage paying 30% or more on housing", "housing", "pct", 1, "lower", "Owner households with a mortgage whose monthly costs are 30% or more of household income (B25091)."),
    "prime_age_epop": ("Prime-age workers: share of people 25 to 54 with a job", "work", "pct", 1, "higher", "People 25 to 54 who are employed (civilian jobs plus armed forces) as a share of all people 25 to 54 (B23001). Tracts with a prison, college dorms or a nursing home can show a low rate because those residents rarely hold jobs."),
    "bachelors_or_higher": ("Adults with a bachelor's degree or more", "work", "pct", 1, "higher", "Adults 25 and older whose highest degree is a bachelor's or higher (B15003)."),
    "hs_or_higher": ("Adults with a high school diploma or more", "work", "pct", 1, "higher", "Adults 25 and older with a high school diploma, GED or higher (B15003)."),
    "uninsured_acs": ("People without health insurance", "health", "pct", 1, "lower", "Civilians not in institutions with no health insurance at the time of the survey (B27010)."),
    "medicaid_share": ("People with Medicaid or other means-tested coverage", "health", "pct", 1, "none", "Civilians not in institutions with Medicaid or other means-tested public coverage (C27007). The survey tends to undercount Medicaid."),
    "disability_share": ("People with a disability", "health", "pct", 1, "none", "Civilians not in institutions reporting a hearing, vision, thinking, walking, self-care or independent-living difficulty (B18101)."),
    "population": ("Population (ACS)", "people", "count", 0, "none", "Total residents (B01003)."),
    "prime_age_share": ("Residents ages 25 to 54", "people", "pct", 1, "none", "Share of all residents who are 25 to 54 (B01001)."),
    "age65_share": ("Residents 65 and older", "people", "pct", 1, "none", "Share of all residents who are 65 or older (B01001)."),
    "nh_white_share": ("White, not Hispanic", "people", "pct", 1, "none", "Share of all residents (B03002). Race groups are people who reported one race and are not Hispanic."),
    "nh_black_share": ("Black, not Hispanic", "people", "pct", 1, "none", "Share of all residents (B03002)."),
    "hispanic_share": ("Hispanic or Latino (any race)", "people", "pct", 1, "none", "Share of all residents (B03002). Hispanic or Latino people can be of any race."),
    "nh_asian_share": ("Asian, not Hispanic", "people", "pct", 1, "none", "Share of all residents (B03002)."),
    "nh_multi_share": ("Two or more races, not Hispanic", "people", "pct", 1, "none", "Share of all residents (B03002)."),
    "nh_other_share": ("Another race, not Hispanic", "people", "pct", 1, "none", "American Indian or Alaska Native, Native Hawaiian or Pacific Islander, or some other race, not Hispanic (B03002). With the five groups above, the groups add to 100%."),
    "foreign_born_share": ("Foreign-born residents", "people", "pct", 1, "none", "Residents who were not U.S. citizens at birth, including naturalized citizens (B05012). People born abroad to U.S.-citizen parents, or in Puerto Rico or another U.S. territory, are native-born."),
    "female_share": ("Residents who are female", "people", "pct", 1, "none", "Share of all residents who are female (B01001). The survey counts sex, not gender identity."),
}
PLACES = [  # id, PLACES measureid, label, better
    ("places_diabetes", "DIABETES", "Adults with diagnosed diabetes", "lower"),
    ("places_obesity", "OBESITY", "Adults with obesity", "lower"),
    ("places_depression", "DEPRESSION", "Adults ever told they have depression", "lower"),
    ("places_mental_distress", "MHLTH", "Adults with frequent mental distress", "lower"),
    ("places_smoking", "CSMOKING", "Adults who currently smoke cigarettes", "lower"),
    ("places_checkup", "CHECKUP", "Adults with a routine checkup in the past year", "higher"),
    ("places_food_insecurity", "FOODINSECU", "Adults with food insecurity in the past year", "lower"),
    ("places_no_transportation", "LACKTRPT", "Adults without reliable transportation in the past year", "lower"),
]
COUNTY_ONLY = ["unemployment_rate", "avg_weekly_wage", "uninsured_under65", "saipe_child_poverty_rate", "snap_persons_share",
               "overdose_rate_per100k", "violent_crime_rate", "property_crime_rate", "grade3_ela_proficient",
               "childcare_providers", "pop_change_pct"]


def cell(v):
    est, moe = v
    if est is None:
        return {"v": None, "moe": None, "weak": True}
    cv = None if moe is None or est == 0 else moe / 1.645 / abs(est) * 100
    return {"v": est, "moe": moe, "weak": cv is not None and cv > CV_MAX}


if __name__ == "__main__":
    raw = pull()
    tr = {t: d for t, d in raw.items() if len(t) == 11}
    assert set(INSIDE) <= set(tr), sorted(set(INSIDE) - set(tr))[:5]
    district = compute(aggregate([tr[t] for t in INSIDE]))
    district["median_household_income"] = (median_from_brackets(aggregate([tr[t] for t in INSIDE])), None)
    # check: the bracket method against the published Ohio and U.S. medians
    for g in ("ohio", "us"):
        pub, est = raw[g]["B19013_001"][0], median_from_brackets(raw[g])
        print(f"{g} median income: published {pub:,.0f}, from brackets {est:,.0f} ({(est - pub) / pub * 100:+.1f}%)")
    race = ["nh_white_share", "nh_black_share", "hispanic_share", "nh_asian_share", "nh_multi_share", "nh_other_share"]
    assert abs(sum(district[r][0] for r in race) - 100) < 1e-6

    metrics = {k: dict(label=a, theme=b, unit=c, decimals=d_, better=e, note=n + (NOTE_MOE if c == "pct" else ""),
                       source="U.S. Census Bureau, American Community Survey 5-year estimates", period=PERIOD)
               for k, (a, b, c, d_, e, n) in M.items()}
    tracts = {t: {k: cell(v) for k, v in compute(tr[t]).items()} for t in INSIDE}
    dist = {k: {"v": v[0], "moe": v[1]} for k, v in district.items()}
    ohio = {k: {"v": v[0], "moe": v[1]} for k, v in compute(raw["ohio"]).items()}
    us = {k: {"v": v[0], "moe": v[1]} for k, v in compute(raw["us"]).items()}

    # CDC PLACES tract data
    q = {"$where": "countyfips in ('39017','39057','39113') and datavaluetypeid='CrdPrv'", "$limit": "50000"}
    rows = json.loads(cached(RAW / "oh10" / "places_tract_2025.json", "https://data.cdc.gov/resource/cwsq-ngmh.json?" + urlencode(q)))
    meta = json.loads(cached(RAW / "oh10" / "places_tract_meta.json", "https://data.cdc.gov/api/views/cwsq-ngmh.json"))
    for mid, code, label, better in PLACES:
        rs = {r["locationname"]: r for r in rows if r["measureid"] == code}
        years = {r["year"] for r in rs.values()}
        assert len(years) == 1, (code, years)
        metrics[mid] = dict(label=label, theme="health", unit="pct", decimals=1, better=better, period=years.pop(),
                            source=f"CDC, {meta['name']}",
                            note="Modeled estimate for adults 18 and older (crude prevalence), from the Behavioral Risk Factor "
                                 "Surveillance System and Census data. Not a direct count; tracts close to each other can look alike "
                                 "because the model shares information across areas. ± is half the width of the 95% interval.")
        num = den = 0.0
        for t in INSIDE:
            r = rs.get(t)
            if not r or r.get("data_value") in (None, ""):
                tracts[t][mid] = {"v": None, "moe": None, "weak": True}
                continue
            v, lo, hi = float(r["data_value"]), float(r["low_confidence_limit"]), float(r["high_confidence_limit"])
            tracts[t][mid] = {"v": v, "moe": (hi - lo) / 2, "weak": False}
            w = float(r["totalpop18plus"])
            num, den = num + v * w, den + w
        dist[mid] = {"v": num / den, "moe": None}
        missing = [t for t in INSIDE if tracts[t][mid]["v"] is None]
        if missing:
            print(f"PLACES {code}: no value for {missing}")

    # county-only measures from the state dashboard's layers
    lay = {}
    for p in PROC.glob("*.json"):
        j = json.loads(p.read_text())
        if isinstance(j, dict) and "metrics" in j and "counties" in j:
            for k in j["metrics"]:
                lay[k] = j
    nat = json.loads((PROC / "national.json").read_text())["national"]
    ctab = {}
    for k in COUNTY_ONLY:
        j = lay[k]
        m = j["metrics"][k]
        row = {"label": m["label"], "unit": m["unit"], "decimals": m["decimals"], "better": m["better"],
               "source": m["source"], "period_label": m.get("period_label"), "note": m.get("note")}
        for f, name in (("39113", "Montgomery"), ("39057", "Greene"), ("39017", "Butler")):
            c = j["counties"].get(f, {}).get(k) or {}
            row[name] = {"v": c.get("latest"), "period": c.get("period"), "flag": c.get("flag")}
        o = j["ohio"].get(k) or {}
        row["Ohio"] = {"v": o.get("latest"), "period": o.get("period")}
        row["U.S."] = {"v": nat[k]["us"], "period": nat[k]["period"]} if k in nat else {"v": None}
        ctab[k] = row

    write_json("oh10/data.json", {"metrics": metrics, "tracts": tracts, "district": dist, "ohio": ohio, "us": us,
                                  "county_table": ctab, "cv_max": CV_MAX, "period": PERIOD})
    weak = {k: sum(tracts[t][k]["weak"] for t in INSIDE) for k in metrics}
    print("tracts with unreliable estimates, by measure:", {k: v for k, v in weak.items() if v})
    for k in ("poverty_rate", "below_200_share", "median_household_income", "uninsured_acs", "prime_age_epop", "places_diabetes"):
        print(f"{k:28} district {dist[k]['v']:>10.1f}  ohio {ohio.get(k, {}).get('v') or float('nan'):>10.1f}  us {us.get(k, {}).get('v') or float('nan'):>10.1f}")
