"""National benchmark: each dashboard measure for every state, DC and the United States.

Writes data/processed/national.json:
  {"national": {"<metric_id>": {"period", "us", "us_source", "states": {"AL": ..}, "flags": {"OH": ..}}},
   "omitted": {"<metric_id>": "reason"}, "checks": {"<metric_id>": {...}}}

Every measure uses the same table lines, periods and vintage as the layer script that builds the
county figure. The Ohio value computed here must equal data/processed/<layer>.json "ohio" to display
precision; a mismatch is printed and the run fails. The U.S. value is the publisher's own national figure
wherever one exists. Puerto Rico is left out.

Run: .venv/bin/python scripts/50_national.py
"""
import csv
import datetime as dt
import importlib
import io
import json
import math
import sys
import urllib.parse

from common import PROC, RAW, cached, census, write_json

acs = importlib.import_module("20_acs")
jobs = importlib.import_module("10_jobs_industry")

TODAY = dt.date.today().isoformat()
USPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC",
        "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
        "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT",
        "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
        "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
        "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY"}
assert len(USPS) == 51
FIPS = {v: k for k, v in USPS.items()}

LAYERS = {}
for name in ("jobs", "income", "people", "popest", "age", "demographics", "health"):
    LAYERS[name] = json.loads((PROC / f"{name}.json").read_text())

OUT = {}
OMITTED = {}
CHECKS = {}
MISMATCH = []


def layer_of(mid):
    for name, lay in LAYERS.items():
        if mid in lay["metrics"]:
            return name, lay
    sys.exit(f"metric {mid} is in no layer")


def add(mid, period, us, us_source, states, flags=None):
    """Store one measure after checking it against the layer's Ohio figure."""
    name, lay = layer_of(mid)
    meta, oh = lay["metrics"][mid], lay["ohio"][mid]
    states = {k: states[k] for k in sorted(states)}
    if sorted(states) != sorted(USPS.values()):
        sys.exit(f"{mid}: states {sorted(set(USPS.values()) ^ set(states))} missing or extra")
    flags = flags or {}
    bad = [g for g, v in states.items() if v is None or math.isnan(v)]
    if us is None or "OH" in bad or any(flags.get(g) != "suppressed" for g in bad):
        sys.exit(f"{mid}: null value without a suppressed flag: {bad}")
    if str(oh["period"]) != str(period):
        sys.exit(f"{mid}: period {period} but the layer's Ohio period is {oh['period']}")
    dec = meta["decimals"]
    mine, theirs = states["OH"], oh["latest"]
    ok = round(mine, dec) == round(theirs, dec)
    CHECKS[mid] = {"layer": name, "ohio_here": mine, "ohio_layer": theirs, "difference": mine - theirs,
                   "match_at_display_precision": ok}
    if not ok:
        MISMATCH.append(mid)
    OUT[mid] = {"period": str(period), "us": us, "us_source": us_source, "states": states, "flags": flags}


# ================================================================ ACS 5-year 2020-2024 (20_acs.py, 23_age.py)
ACS_YEAR, ACS_PERIOD = acs.LATEST


def acs_pull(table):
    """{"OH": {var: (est, moe)}, ..., "US": {...}} for one table, same parsing as 20_acs.pull."""
    out = {}
    for tag, geo in (("states", {"for": "state:*"}), ("us", {"for": "us:1"})):
        rows = census(f"{ACS_YEAR}/acs/acs5", dict(get=f"NAME,group({table})", **geo),
                      f"national/acs5_{ACS_YEAR}_{table}_{tag}.json")
        for r in rows:
            if tag == "us":
                key = "US"
            elif r["state"] in USPS:
                key = USPS[r["state"]]
            else:
                continue                                           # Puerto Rico
            d = out.setdefault(key, {})
            for k, v in r.items():
                if k.startswith(table + "_") and k.endswith("E") and not k.endswith("EA"):
                    d[k[:-1]] = (acs.num(v), acs.moe_num(r.get(k[:-1] + "M")))
    return out


def acs_measures():
    data = {}
    for t in acs.TABLES:
        for g, d in acs_pull(t).items():
            data.setdefault(g, {}).update(d)
    vals = {g: acs.compute(ACS_YEAR, d) for g, d in data.items()}
    skip = {"population"}                                          # a count: no fair state comparison
    for mid in list(acs.INCOME) + list(acs.PEOPLE):
        if mid in skip:
            continue
        add(mid, ACS_PERIOD, vals["US"][mid][0], "publisher's own U.S. figure (ACS us:1)",
            {g: vals[g][mid][0] for g in USPS.values()})


GQ_FLAG = 5.0
PRIME_GROUPS = ("25 to 29 years", "30 to 34 years", "35 to 44 years", "45 to 54 years")


def b23001_lines(year):
    """Same label search as 23_age.acs_epop."""
    j = json.loads(cached(RAW / "census" / "groups" / f"{year}_B23001.json",
                          f"https://api.census.gov/data/{year}/acs/acs5/groups/B23001.json"))
    lab = {k[:-1]: v["label"] for k, v in j["variables"].items() if k.startswith("B23001_") and k.endswith("E")}
    tot, emp, af = [], [], []
    for k, l in lab.items():
        parts = [p.rstrip(":") for p in l.split("!!")]
        if not any(g in parts for g in PRIME_GROUPS):
            continue
        if parts[-1] in PRIME_GROUPS:
            tot.append(k)
        elif parts[-1] in ("Armed Forces", "In Armed Forces"):
            af.append(k)
        elif parts[-1] == "Employed" and "Civilian" in parts:
            emp.append(k)
    assert len(tot) == 8 and len(emp) == 8 and len(af) == 8
    return tot, emp + af


def epop_measure():
    tot, num_ = b23001_lines(ACS_YEAR)
    d = acs_pull("B23001")
    val = {g: sum(d[g][k][0] for k in num_) / sum(d[g][k][0] for k in tot) * 100 for g in d}
    # group-quarters share, as in 23_age.group_quarters, so states get the same flag the counties do
    flags = {}
    for tag, geo in (("states", {"for": "state:*"}), ("us", {"for": "us:1"})):
        for r in census(f"{ACS_YEAR}/acs/acs5", dict(geo, get="B26001_001E,B01003_001E"),
                        f"national/{ACS_YEAR}_B26001_{tag}.json"):
            if tag == "states" and r["state"] in USPS:
                gq = float(r["B26001_001E"]) / float(r["B01003_001E"]) * 100
                if gq >= GQ_FLAG:
                    flags[USPS[r["state"]]] = (f"{gq:.0f}% of residents live in group quarters such as prisons, "
                                               "dorms or nursing homes, which pulls this rate down")
    add("prime_age_epop", ACS_PERIOD, val["US"], "publisher's own U.S. figure (ACS us:1)",
        {g: val[g] for g in USPS.values()}, flags)


# ================================================================ Population estimates, Vintage 2025
PEP = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025"


def pep_csv(path, name):
    return list(csv.DictReader(io.StringIO(cached(RAW / "census_pep" / name, f"{PEP}/{path}").decode("latin-1"))))


def pep_totals():
    """State rows from the county file (the one 21_popest.py and 30_health.py read) and the U.S. row from
    the national/state file."""
    co = pep_csv("counties/totals/co-est2025-alldata.csv", "co-est2025-alldata.csv")
    st = {USPS[r["STATE"]]: r for r in co if r["SUMLEV"] == "040" and r["STATE"] in USPS}
    nst = pep_csv("state/totals/NST-EST2025-ALLDATA.csv", "NST-EST2025-ALLDATA.csv")
    us = [r for r in nst if r["SUMLEV"] == "010"]
    assert len(us) == 1 and len(st) == 51
    # the two files must agree for every state
    for r in nst:
        if r["SUMLEV"] == "040" and r["STATE"] in USPS:
            assert r["POPESTIMATE2025"] == st[USPS[r["STATE"]]]["POPESTIMATE2025"], r["NAME"]
    return st, us[0]


def popest_measures(st, us):
    years = range(2020, 2026)

    def vals(r):
        base = float(r["ESTIMATESBASE2020"])
        out = {"pop_change_pct": 100 * (float(r["POPESTIMATE2025"]) - base) / base}
        for name, col in (("natural_change_rate", "NATURALCHG"), ("net_international_migration_rate", "INTERNATIONALMIG"),
                          ("net_domestic_migration_rate", "DOMESTICMIG")):
            out[name] = 1000 * sum(float(r[f"{col}{y}"]) for y in years) / base
        return out

    v = {g: vals(r) for g, r in st.items()}
    vu = vals(us)
    for mid in ("pop_change_pct", "natural_change_rate", "net_international_migration_rate", "net_domestic_migration_rate"):
        add(mid, "2025", vu[mid], "publisher's own U.S. figure (NST-EST2025 U.S. row)", {g: v[g][mid] for g in v})


PRIME = ["AGE2529_TOT", "AGE3034_TOT", "AGE3539_TOT", "AGE4044_TOT", "AGE4549_TOT", "AGE5054_TOT"]


def age_measures(st, us):
    """Same method as 23_age.pep: state = sum of its counties in cc-est2025-agesex."""
    rows = pep_csv("counties/asrh/cc-est2025-agesex-all.csv", "cc-est2025-agesex-all.csv")
    agg = {}
    for r in rows:
        if r["SUMLEV"] != "050" or r["STATE"] not in USPS or int(r["YEAR"]) < 6:
            continue                                               # YEAR 6 = July 1, 2024; 7 = July 1, 2025
        k = (USPS[r["STATE"]], int(r["YEAR"]) + 2018)
        a = agg.setdefault(k, {"pop": 0.0, "prime": 0.0, "s65": 0.0, "fem": 0.0})
        a["pop"] += float(r["POPESTIMATE"])
        a["prime"] += sum(float(r[c]) for c in PRIME)
        a["s65"] += float(r["AGE65PLUS_TOT"])
        a["fem"] += float(r["AGE1544_FEM"])
    for g in USPS.values():
        assert abs(agg[(g, 2025)]["pop"] - float(st[g]["POPESTIMATE2025"])) < 1, f"{g} counties do not sum to state"

    nat = pep_csv("national/asrh/nc-est2025-agesex-res.csv", "nc-est2025-agesex-res.csv")

    def nsum(sex, lo, hi, year):
        return sum(float(r[f"POPESTIMATE{year}"]) for r in nat
                   if r["SEX"] == str(sex) and r["AGE"] != "999" and lo <= int(r["AGE"]) <= hi)

    us_pop = [float(r["POPESTIMATE2025"]) for r in nat if r["SEX"] == "0" and r["AGE"] == "999"][0]
    assert us_pop == float(us["POPESTIMATE2025"])
    src = "publisher's own U.S. figure (NC-EST2025-AGESEX-RES national file)"
    add("prime_age_share", "2025", nsum(0, 25, 54, 2025) / us_pop * 100, src,
        {g: agg[(g, 2025)]["prime"] / agg[(g, 2025)]["pop"] * 100 for g in USPS.values()})
    add("age65_share", "2025", nsum(0, 65, 200, 2025) / us_pop * 100, src,
        {g: agg[(g, 2025)]["s65"] / agg[(g, 2025)]["pop"] * 100 for g in USPS.values()})
    us_fem = (nsum(2, 15, 44, 2024) + nsum(2, 15, 44, 2025)) / 2
    add("general_fertility_rate", "2025", float(us["BIRTHS2025"]) / us_fem * 1000,
        "publisher's own U.S. figures (NST-EST2025 births, national women 15 to 44)",
        {g: float(st[g]["BIRTHS2025"]) / ((agg[(g, 2024)]["fem"] + agg[(g, 2025)]["fem"]) / 2) * 1000
         for g in USPS.values()})


# race groups as in 24_demographics.GROUPS, by race code in the state file (1 White, 2 Black, 3 AIAN, 4 Asian,
# 5 NHPI, 6 two or more); None = Hispanic of any race
RACE_GROUPS = {"nh_white_share": ["1"], "nh_black_share": ["2"], "hispanic_share": None, "nh_asian_share": ["4"],
               "nh_multi_share": ["6"], "nh_native_share": ["3", "5"]}


def demographic_measures(st, us):
    """Race and ethnicity and female share from the state file sc-est2025-alldata6 (sex, Hispanic origin, six
    race groups, single years of age), July 1, 2025. U.S. = sum of the 50 states and DC, checked against the
    U.S. total. Foreign-born share from ACS B05012, the U.S. figure from the ACS us:1 row."""
    rows = pep_csv("state/asrh/sc-est2025-alldata6.csv", "sc-est2025-alldata6.csv")
    agg = {}
    for r in rows:
        if r["STATE"] not in USPS:
            continue
        a = agg.setdefault(USPS[r["STATE"]], {k: 0.0 for k in list(RACE_GROUPS) + ["tot", "fem"]})
        v = float(r["POPESTIMATE2025"])
        if r["SEX"] == "0" and r["ORIGIN"] == "0":
            a["tot"] += v
        if r["SEX"] == "2" and r["ORIGIN"] == "0":
            a["fem"] += v
        if r["SEX"] == "0":
            for mid, codes in RACE_GROUPS.items():
                if (codes is None and r["ORIGIN"] == "2") or (codes and r["ORIGIN"] == "1" and r["RACE"] in codes):
                    a[mid] += v
    for g, a in agg.items():
        assert abs(a["tot"] - float(st[g]["POPESTIMATE2025"])) < 1, f"{g}: state race file total differs"
        assert abs(sum(a[m] for m in RACE_GROUPS) - a["tot"]) < 1, f"{g}: race groups do not add to total"
    usa = {k: sum(a[k] for a in agg.values()) for k in list(RACE_GROUPS) + ["tot", "fem"]}
    assert abs(usa["tot"] - float(us["POPESTIMATE2025"])) < 1, "states do not sum to the U.S. total"
    src = "sum of the 50 states and DC (SC-EST2025-ALLDATA6), equal to the U.S. total"
    for mid in list(RACE_GROUPS) + ["female_share"]:
        k = "fem" if mid == "female_share" else mid
        add(mid, "2025", usa[k] / usa["tot"] * 100, src, {g: a[k] / a["tot"] * 100 for g, a in agg.items()})
    fb = acs_pull("B05012")
    share = lambda d: d["B05012_003"][0] / d["B05012_001"][0] * 100
    add("foreign_born_share", ACS_PERIOD, share(fb["US"]), "publisher's own U.S. figure (ACS us:1)",
        {g: share(fb[g]) for g in USPS.values()})


# ================================================================ LAUS (10_jobs_industry.py)
def laus_measures():
    lay = LAYERS["jobs"]
    year = lay["ohio"]["unemployment_rate"]["period"]
    base = str(jobs.LAUS_BASE_YEAR)
    ids = {g: (f"LAUST{f}00000000000{3:02d}", f"LAUST{f}00000000000{6:02d}") for f, g in USPS.items()}
    ids["US"] = ("LNU04000000", "LNU01000000")                      # CPS, not seasonally adjusted
    flat = [i for p in ids.values() for i in p]
    got = jobs.bls_annual(flat, int(base), int(year), "bls_laus_national")

    def annual(sid, y):
        v = [jobs.num(val) for yy, p, val, f in got[sid] if p == "M13" and str(yy) == y]
        if len(v) != 1 or v[0] is None:
            sys.exit(f"no {y} annual average for {sid}")
        return v[0]

    rate = {g: annual(ids[g][0], year) for g in ids}
    lf = {g: (annual(ids[g][1], year) / annual(ids[g][1], base) - 1) * 100 for g in ids}
    src = "publisher's own U.S. figure (CPS LNU04000000 / LNU01000000 annual average)"
    add("unemployment_rate", year, rate.pop("US"), src.replace(" / LNU01000000", ""), rate)
    add("labor_force_change_pct", f"{base}-{year}", lf.pop("US"), src.replace("LNU04000000 / ", ""), lf)


# ================================================================ QCEW (10_jobs_industry.py)
def qcew_measures():
    year = int(LAYERS["jobs"]["ohio"]["avg_weekly_wage"]["period"])
    areas = {g: f"{f}000" for f, g in USPS.items()}
    areas["US"] = "US000"
    wage, mfg, hc = {}, {}, {}
    for g, a in areas.items():
        d = jobs.parse(a, jobs.qcew_file(year, a), year)
        lv = 0 if g == "US" else 40                                # national agglvl 1x, state 5x
        L = lambda n: str(n + lv)                                   # noqa: E731
        wage[g] = d[("0", "10", L(10))][1]
        pt = d[("5", "10", L(11))][0]
        for code, out in (("31-33", mfg), ("62", hc)):
            j = d.get(("5", code, L(14)), (0.0, None))[0]
            out[g] = None if j is None else j / pt * 100
    src = "publisher's own U.S. figure (QCEW US000)"
    add("avg_weekly_wage", str(year), wage.pop("US"), src, wage)
    for mid, d in (("manufacturing_share", mfg), ("health_care_share", hc)):
        us = d.pop("US")
        # BLS withholds a few state sector totals to protect employer privacy: null with a flag, as in the layers
        add(mid, str(year), us, src, d, {g: "suppressed" for g, v in d.items() if v is None})


# ================================================================ SAHIE and SAIPE (30_health.py)
def sahie_measures():
    for ipr, mid in (("0", "uninsured_under65"), ("1", "uninsured_under65_low_income")):
        year = LAYERS["health"]["ohio"][mid]["period"]
        base = {"get": "NAME,PCTUI_PT,PCTUI_MOE,YEAR", "AGECAT": "0", "IPRCAT": ipr, "SEXCAT": "0",
                "RACECAT": "0", "time": year}
        st = census("timeseries/healthins/sahie", dict(base, **{"for": "state:*"}), f"national/sahie_states_ipr{ipr}_{year}.json")
        us = census("timeseries/healthins/sahie", dict(base, **{"for": "us:*"}), f"national/sahie_us_ipr{ipr}_{year}.json")
        assert len(us) == 1 and us[0]["YEAR"] == year
        add(mid, year, float(us[0]["PCTUI_PT"]), "publisher's own U.S. figure (SAHIE U.S. row)",
            {USPS[r["state"]]: float(r["PCTUI_PT"]) for r in st if r["state"] in USPS and r["YEAR"] == year})


def saipe_measures():
    for mid, var in (("saipe_poverty_rate", "SAEPOVRTALL"), ("saipe_child_poverty_rate", "SAEPOVRT0_17"),
                     ("saipe_median_income", "SAEMHI")):
        year = LAYERS["health"]["ohio"][mid]["period"]
        p = {"get": f"NAME,YEAR,{var}_PT", "time": year}
        st = census("timeseries/poverty/saipe", dict(p, **{"for": "state:*"}), f"national/saipe_states_{var}_{year}.json")
        us = census("timeseries/poverty/saipe", dict(p, **{"for": "us:*"}), f"national/saipe_us_{var}_{year}.json")
        assert len(us) == 1
        add(mid, year, float(us[0][var + "_PT"]), "publisher's own U.S. figure (SAIPE U.S. row)",
            {USPS[r["state"]]: float(r[var + "_PT"]) for r in st if r["state"] in USPS})


# ================================================================ CDC overdose (30_health.py, state file)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def overdose_measure(st, us):
    period = LAYERS["health"]["ohio"]["overdose_rate_per100k"]["period"]       # "2026-03"
    y, m = period.split("-")
    q = {"$where": f"indicator='Number of Drug Overdose Deaths' and period='12 month-ending' "
                   f"and year='{y}' and month='{MONTHS[int(m) - 1]}'", "$limit": "500"}
    url = "https://data.cdc.gov/resource/xkb8-kh2a.json?" + urllib.parse.urlencode(q)
    rows = json.loads(cached(RAW / "cdc" / "national" / f"vsrr_state_overdose_{period}.json", url))
    by = {}
    for r in rows:
        if r["state"] in by:
            sys.exit(f"duplicate overdose row {r['state']}")
        by[r["state"]] = r
    # CDC reports New York City (YC) apart from the rest of New York (NY); the state is the two together
    ny = by.pop("NY"), by.pop("YC")
    by["NY"] = dict(ny[0], data_value=str(float(ny[0]["data_value"]) + float(ny[1]["data_value"])),
                    predicted_value=str(float(ny[0]["predicted_value"]) + float(ny[1]["predicted_value"])),
                    footnote=ny[0].get("footnote") or ny[1].get("footnote"))
    year = min(int(y), 2025)                                     # same rule as 30_health.popfor
    pop = {g: float(st[g][f"POPESTIMATE{year}"]) for g in USPS.values()}
    rate = {g: float(by[g]["data_value"]) / pop[g] * 1e5 for g in USPS.values()}
    us_rate = float(by["US"]["data_value"]) / float(us[f"POPESTIMATE{year}"]) * 1e5
    flags = {g: by[g]["footnote"] for g in USPS.values() if by[g].get("footnote")}
    gap = {g: float(by[g]["predicted_value"]) / float(by[g]["data_value"]) * 100 - 100
           for g in list(USPS.values()) + ["US"]}
    add("overdose_rate_per100k", period, us_rate, "publisher's own U.S. count (CDC VSRR U.S. row) over Census U.S. population",
        rate, flags)
    OUT["overdose_rate_per100k"]["predicted_minus_reported_pct"] = {g: round(v, 2) for g, v in sorted(gap.items())}
    us_foot = by["US"].get("footnote")
    if us_foot:
        OUT["overdose_rate_per100k"]["flags"]["US"] = us_foot


# ================================================================ run
LEFT_OUT = {
    "labor_force": "a count of people; a state total does not compare with a county total",
    "employed": "a count of people",
    "private_jobs": "a count of jobs",
    "population": "a count of people",
    "population_estimate": "a count of people",
    "overdose_deaths_12mo": "a count of deaths; the rate per 100,000 is benchmarked instead",
    "top_industry_share": "a county concept (largest disclosed 3-digit industry); state files withhold different "
                          "industries, so the figure would not mean the same thing",
    "concentration_hhi": "a county concept built on disclosed county supersectors",
}


def main():
    st, us = pep_totals()
    for step in (acs_measures, epop_measure, laus_measures, qcew_measures, sahie_measures, saipe_measures):
        step()
    popest_measures(st, us)
    age_measures(st, us)
    demographic_measures(st, us)
    overdose_measure(st, us)

    for mid, why in LEFT_OUT.items():
        layer_of(mid)
        OMITTED[mid] = why
    for mid in LAYERS["health"]["metrics"]:
        if mid.startswith("places_"):
            OMITTED[mid] = "the CDC PLACES county file has no state rows, so the dashboard has no Ohio figure to check against"
    every = {m for lay in LAYERS.values() for m in lay["metrics"]}
    unhandled = every - set(OUT) - set(OMITTED)
    if unhandled:
        sys.exit(f"measures neither benchmarked nor listed as left out: {sorted(unhandled)}")

    write_json("national.json", {"national": OUT, "omitted": OMITTED, "checks": CHECKS,
                                 "note": f"States are the 50 states and DC, keyed by USPS code; Puerto Rico left out. Pulled {TODAY}."})

    print(f"\n{'metric':34} {'period':10} {'US':>10} {'OH':>10}  rank  better")
    for mid, o in OUT.items():
        name, lay = layer_of(mid)
        meta = lay["metrics"][mid]
        better, dec = meta["better"], meta["decimals"]
        v = o["states"]
        rv = {g: round(x, dec) for g, x in v.items() if x is not None}
        hi_first = better != "lower"
        rank = 1 + sum((x > rv["OH"]) if hi_first else (x < rv["OH"]) for x in rv.values())
        ties = sum(x == rv["OH"] for x in rv.values()) - 1
        print(f"{mid:34} {o['period']:10} {o['us']:10.{dec}f} {v['OH']:10.{dec}f}  {rank:>3}{'=' if ties else ' '}/{len(rv)} "
              f"{better}{' (ranked highest first)' if better == 'none' else ''}")
    print("\nOhio check (here vs layer):")
    for mid, c in CHECKS.items():
        print(f"  {mid:34} {'ok' if c['match_at_display_precision'] else 'MISMATCH'}  diff {c['difference']:+.6g}")
    if MISMATCH:
        sys.exit(f"Ohio mismatch: {MISMATCH}")


if __name__ == "__main__":
    main()
