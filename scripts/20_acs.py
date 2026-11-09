"""ACS 5-year layers for the 88 Ohio counties and Ohio: income.json (theme income) and people.json
(themes people and health).

Three non-overlapping 5-year vintages: 2010-2014, 2015-2019, 2020-2024. Whole tables are pulled with
the API's group() call, and table lines for Medicaid, uninsured and disability are found by label,
so a line renumbered between vintages still counts. Dollar values are nominal (not inflation-adjusted).

Derived shares carry a 90% margin of error from the Census Bureau's approximation for proportions
(ACS General Handbook, ch. 8): MOE_p = sqrt(MOE_x^2 - p^2 * MOE_y^2) / y, switching to the ratio
form (plus sign) when the term under the root is negative. Sums of lines use sqrt(sum of MOE^2).
"""
import datetime as dt
import json
import math
import sys

from common import RAW, STATE, cached, census, write_json

VINTAGES = [(2014, "2010-2014"), (2019, "2015-2019"), (2024, "2020-2024")]
LATEST = VINTAGES[-1]
TABLES = ["B19013", "C17002", "B22003", "B19001", "B19083", "B01003", "B01002", "B15003",
          "B25070", "B25091", "C27007", "B27010", "B18101"]
PULLED = dt.date.today().isoformat()
CV_FLAG = 30.0   # flag a latest value whose coefficient of variation is above this, in percent


def num(v):
    """API value to float. Census special codes (large negatives such as -666666666) become None."""
    if v is None or v == "":
        return None
    x = float(v)
    return None if x <= -100000000 else x


def moe_num(v):
    """MOE to float. -555555555 means a controlled estimate with no sampling error: 0.
    Other special codes mean no MOE is available: None."""
    if v is None or v == "":
        return None
    x = float(v)
    if x == -555555555:
        return 0.0
    return None if x < 0 else x


def labels(year, table):
    j = json.loads(cached(RAW / "census" / "groups" / f"{year}_{table}.json",
                          f"https://api.census.gov/data/{year}/acs/acs5/groups/{table}.json"))
    return {k[:-1]: v["label"] for k, v in j["variables"].items() if k.endswith("E") and k.startswith(table)}


def pull(year):
    """{geo: {var: (estimate, moe)}} for every Ohio county ('39001') and the state ('ohio')."""
    out = {}
    for t in TABLES:
        for tag, geo in (("county", {"for": "county:*", "in": f"state:{STATE}"}),
                         ("state", {"for": f"state:{STATE}"})):
            rows = census(f"{year}/acs/acs5", dict(get=f"NAME,group({t})", **geo), f"acs5_{year}_{t}_{tag}.json")
            for r in rows:
                key = "ohio" if tag == "state" else r["state"] + r["county"]
                d = out.setdefault(key, {})
                for k, v in r.items():
                    if k.startswith(t + "_") and k.endswith("E") and not k.endswith("EA"):
                        d[k[:-1]] = (num(v), moe_num(r.get(k[:-1] + "M")))
    return out


def lines(table, a, b):
    return [f"{table}_{i:03d}" for i in range(a, b + 1)]


def by_label(year, table, suffix):
    found = [k for k, lab in labels(year, table).items() if lab.rstrip(":").endswith(suffix)]
    if not found:
        sys.exit(f"{year} {table}: no line ends with {suffix!r}")
    return found


def total(d, keys):
    vals = [d.get(k, (None, None)) for k in keys]
    if any(v[0] is None for v in vals):
        return None, None
    est = sum(v[0] for v in vals)
    moe = None if any(v[1] is None for v in vals) else math.sqrt(sum(v[1] ** 2 for v in vals))
    return est, moe


def diff(a, b):
    if a[0] is None or b[0] is None:
        return None, None
    m = None if a[1] is None or b[1] is None else math.sqrt(a[1] ** 2 + b[1] ** 2)
    return a[0] - b[0], m


def share(num_, den):
    """Percent and its MOE (Census approximation for a proportion)."""
    x, mx = num_
    y, my = den
    if x is None or y is None or y <= 0:
        return None, None
    p = x / y
    if mx is None or my is None:
        return 100 * p, None
    under = mx ** 2 - p ** 2 * my ** 2
    if under < 0:
        under = mx ** 2 + p ** 2 * my ** 2
    return 100 * p, 100 * math.sqrt(under) / y


def single(d, k):
    return d.get(k, (None, None))


def compute(year, d):
    """All metrics for one geography and one vintage: {metric: (value, moe)}."""
    pov = lines("C17002", 2, 3)
    near = lines("C17002", 4, 7)
    rent_den = diff(single(d, "B25070_001"), single(d, "B25070_011"))
    own_den = diff(single(d, "B25091_002"), single(d, "B25091_012"))
    return {
        "median_household_income": single(d, "B19013_001"),
        "poverty_rate": share(total(d, pov), single(d, "C17002_001")),
        "near_poverty_share": share(total(d, near), single(d, "C17002_001")),
        "below_200_share": share(total(d, pov + near), single(d, "C17002_001")),
        "snap_households_share": share(single(d, "B22003_002"), single(d, "B22003_001")),
        "gini": single(d, "B19083_001"),
        "population": single(d, "B01003_001"),
        "median_age": single(d, "B01002_001"),
        "bachelors_or_higher": share(total(d, lines("B15003", 22, 25)), single(d, "B15003_001")),
        "hs_or_higher": share(total(d, lines("B15003", 17, 25)), single(d, "B15003_001")),
        "rent_burden": share(total(d, lines("B25070", 7, 10)), rent_den),
        "owner_cost_burden": share(total(d, lines("B25091", 8, 11)), own_den),
        "medicaid_share": share(total(d, by_label(year, "C27007", "With Medicaid/means-tested public coverage")),
                                single(d, "C27007_001")),
        "uninsured_acs": share(total(d, by_label(year, "B27010", "No health insurance coverage")),
                               single(d, "B27010_001")),
        "disability_share": share(total(d, by_label(year, "B18101", "With a disability")),
                                  single(d, "B18101_001")),
    }


SRC = "U.S. Census Bureau, American Community Survey 5-year estimates"
VINT = f"ACS 5-year 2010-2014, 2015-2019 and 2020-2024 (released Dec. 2025); pulled {PULLED}"
PL = "2020-2024 ACS 5-year"
NOTE_MOE = " Margins of error are at 90% confidence; for this share they use the Census Bureau's approximation for proportions."

INCOME = {
    "median_household_income": dict(
        label="Median household income", unit="usd", decimals=0, better="higher",
        note="Half of households earn more and half earn less. Dollars are nominal: each 5-year period is in its own "
             "final year's dollars, so older values are not adjusted for inflation."),
    "poverty_rate": dict(
        label="Share of people in poverty", unit="pct", decimals=1, better="lower",
        note="People whose family income is below the federal poverty line (table C17002). The poverty line is the "
             "same across the country and does not change with local living costs." + NOTE_MOE),
    "near_poverty_share": dict(
        label="Share of people just above the poverty line", unit="pct", decimals=1, better="lower",
        note="People, not households, whose family income is between 100% and 199% of the federal poverty line "
             "(C17002). The poverty line is a federal measure that does not change with local living costs." + NOTE_MOE),
    "below_200_share": dict(
        label="Share of people below twice the poverty line", unit="pct", decimals=1, better="lower",
        note="People whose family income is below 200% of the federal poverty line (C17002): those in poverty plus "
             "those just above it." + NOTE_MOE),
    "snap_households_share": dict(
        label="Households that got SNAP food aid", unit="pct", decimals=1, better="none",
        note="Households that received SNAP (food stamps) at any time in the past 12 months, as reported in the "
             "survey (B22003). Surveys tend to undercount program use." + NOTE_MOE),
    "gini": dict(
        label="Income inequality (Gini index)", unit="index", decimals=3, better="lower",
        note="Household income inequality on a scale from 0 (all equal) to 1 (one household has all income) (B19083)."),
}
PEOPLE = {
    "population": dict(
        label="Population (ACS)", unit="count", decimals=0, better="none", theme="people",
        note="Total residents from the ACS (B01003). County totals are set to match the Census Bureau's population "
             "estimates, so they carry no margin of error."),
    "median_age": dict(
        label="Median age", unit="years", decimals=1, better="none", theme="people",
        note="Half of residents are older and half are younger (B01002)."),
    "bachelors_or_higher": dict(
        label="Adults with a bachelor's degree or more", unit="pct", decimals=1, better="higher", theme="people",
        note="Share of adults age 25 and older whose highest degree is a bachelor's or higher (B15003)." + NOTE_MOE),
    "hs_or_higher": dict(
        label="Adults with a high school diploma or more", unit="pct", decimals=1, better="higher", theme="people",
        note="Share of adults age 25 and older with a high school diploma, GED or higher (B15003)." + NOTE_MOE),
    "rent_burden": dict(
        label="Renters paying 30% or more of income on rent", unit="pct", decimals=1, better="lower", theme="people",
        note="Renter households whose gross rent is 30% or more of household income (B25070). Households where the "
             "share could not be computed (no income or no cash rent) are left out." + NOTE_MOE),
    "owner_cost_burden": dict(
        label="Owners with a mortgage paying 30% or more on housing", unit="pct", decimals=1, better="lower",
        theme="people",
        note="Owner households with a mortgage whose monthly owner costs are 30% or more of household income "
             "(B25091). Not-computed households are left out." + NOTE_MOE),
    "medicaid_share": dict(
        label="People with Medicaid or other means-tested coverage", unit="pct", decimals=1, better="none",
        theme="health",
        note="Share of the civilian population not in institutions with Medicaid or other means-tested public "
             "coverage, alone or with other insurance (C27007). The survey tends to undercount Medicaid enrollment."
             + NOTE_MOE),
    "uninsured_acs": dict(
        label="People without health insurance (ACS)", unit="pct", decimals=1, better="lower", theme="health",
        note="Share of the civilian population not in institutions with no health insurance at the time of the "
             "survey (B27010). The 2010-2014 period mostly predates Ohio's 2014 Medicaid expansion." + NOTE_MOE),
    "disability_share": dict(
        label="People with a disability", unit="pct", decimals=1, better="none", theme="health",
        note="Share of the civilian population not in institutions reporting a hearing, vision, thinking, walking, "
             "self-care or independent-living difficulty (B18101)." + NOTE_MOE),
}

C17_BANDS = ["Under 50%", "50% to 99%", "100% to 124%", "125% to 149%", "150% to 184%", "185% to 199%", "200% and over"]


def bracket_labels():
    lab = labels(LATEST[0], "B19001")
    return [lab[f"B19001_{i:03d}"].split("!!")[-1] for i in range(2, 18)]


def build():
    data = {y: pull(y) for y, _ in VINTAGES}
    geos = sorted(k for k in data[LATEST[0]] if k != "ohio")
    if len(geos) != 88:
        sys.exit(f"expected 88 counties, got {len(geos)}")
    for y, _ in VINTAGES:
        missing = set(geos) - set(data[y])
        if missing:
            sys.exit(f"{y}: counties missing {sorted(missing)}")
    vals = {y: {g: compute(y, data[y][g]) for g in geos + ["ohio"]} for y, _ in VINTAGES}

    def cell(g, m):
        series = [[p, vals[y][g][m][0]] for y, p in VINTAGES if vals[y][g][m][0] is not None]
        periods = [s[0] for s in series]
        if len(periods) != len(set(periods)):
            sys.exit(f"duplicate periods {g} {m}")
        v, moe = vals[LATEST[0]][g][m]
        flag = None
        if v is None:
            flag = "suppressed"
        elif moe is not None and v > 0 and 100 * (moe / 1.645) / v > CV_FLAG:
            flag = "high_moe"
        return {"latest": v, "period": LATEST[1], "series": series, "moe": moe, "flag": flag}

    def layer(spec, theme_default):
        metrics = {}
        for m, s in spec.items():
            s = dict(s)
            metrics[m] = {"label": s["label"], "theme": s.get("theme", theme_default), "unit": s["unit"],
                          "decimals": s["decimals"], "better": s["better"], "source": SRC, "vintage": VINT,
                          "period_label": PL, "note": s["note"]}
        return {"metrics": metrics,
                "counties": {g: {m: cell(g, m) for m in spec} for g in geos},
                "ohio": {m: cell("ohio", m) for m in spec},
                "extras": {}}

    inc = layer(INCOME, "income")
    brackets = bracket_labels()
    dist, bands = {}, {}
    for g in geos + ["ohio"]:
        per = {}
        for y, p in VINTAGES:
            d = data[y][g]
            tot = d["B19001_001"][0]
            per[p] = [100 * d[k][0] / tot if tot else None for k in lines("B19001", 2, 17)]
        dist[g] = {"brackets": brackets, "shares": per,
                   "note": "Share of households by income in the past 12 months, nominal dollars of each period (B19001)."}
        d = data[LATEST[0]][g]
        tot = d["C17002_001"][0]
        bands[g] = {"period": LATEST[1], "bands": C17_BANDS,
                    "shares": [100 * d[k][0] / tot if tot else None for k in lines("C17002", 2, 8)],
                    "note": "Share of people by family income as a percent of the federal poverty line (C17002)."}
    inc["extras"] = {"income_distribution": dist, "poverty_ratio_bands": bands}
    write_json("income.json", inc)
    write_json("people.json", layer(PEOPLE, "people"))
    return data, vals


if __name__ == "__main__":
    data, vals = build()
    y = LATEST[0]
    for g in ("39049", "39163", "ohio"):
        d = data[y][g]
        print(g, "B19013", d["B19013_001"], "C17002_001", d["C17002_001"])
        for m in ("median_household_income", "poverty_rate", "near_poverty_share", "rent_burden", "uninsured_acs"):
            print("   ", m, vals[y][g][m])
