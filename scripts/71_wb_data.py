"""Data for the Ohio Community Well-Being page at three levels: counties, congressional districts (2025 map) and
census tracts. Writes data/processed/wellbeing/data.json. Run after 70_wb_geo.py and the county layers.

Which measures and where they come from: scripts/wellbeing_measures.py. How each level is built:

- Counties. Measures already in a county layer (data/processed/*.json) are read from it, with their history. New
  American Community Survey (ACS) measures are pulled for counties, Ohio and the U.S. for 2010-2014, 2015-2019 and
  2020-2024 (where the table exists) and computed the same way as the county layers (20_acs.py: shares carry the
  Census Bureau's margin-of-error approximation). CDC PLACES county values are the 2025 release's crude
  prevalence, so counties, districts and tracts use the same kind of estimate.
- Tracts. ACS 2020-2024 for every 2020 Ohio tract, computed with the same code. An estimate whose coefficient of
  variation is above 30% is marked uncertain. CDC PLACES 2025 release, tract crude prevalence.
- Congressional districts. No published estimates exist for the 2025 lines. Each ACS table line is summed over the
  tracts with district residents, weighted by the share of each tract's 2020 census residents who live in the
  district; margins of error are weighted the same way and combined as the square root of the sum of squares
  (the method on the OH-10 page). Median household income is interpolated from the district's income brackets.
  PLACES: tract values weighted by adults 18 and older times the same share.
- Ohio for PLACES: CDC publishes no state value in this form, so Ohio is the tract values weighted by adults 18
  and older.
- Child care: licensed programs open on the pull date (41_childcare.py snapshot), placed in tracts by their
  geocoded location, counted per 1,000 children under 5 (ACS). Shown for counties and districts only; a tract is
  too small an area, since families often use care outside their own tract.
"""
import importlib
import json
import math
from collections import Counter

import wellbeing_measures as WM
from common import PROC, RAW, cached, census, write_json

acs = importlib.import_module("20_acs")
STF = "39"
KEY = "wellbeing"
GEO = json.loads((PROC / KEY / "geo.json").read_text())
CV_MAX = 30.0
VINT = [(2014, "2010-2014"), (2019, "2015-2019"), (2024, "2020-2024")]
TRACT_TABLES = ["B19013", "C17002", "B22003", "B19001", "B01003", "B15003", "B25070", "B25091", "C27007", "B27010",
                "B18101", "B23001", "B05012", "B03002", "B01001", "B28002", "B25044", "B08303", "B08013", "B25014",
                "B25002", "B25003", "B25034", "B14003"]
NEW_ACS = ["mean_commute", "overcrowded_share", "homeownership", "vacancy_rate", "old_housing_share", "uninsured_u65",
           "broadband_share", "no_vehicle_share", "preschool_enrolled"]
L = acs.lines
S = acs.single


def ratio(num_, den):
    x, mx = num_
    y, my = den
    if x is None or y is None or y <= 0:
        return None, None
    r = x / y
    return r, (None if mx is None or my is None else math.sqrt(mx ** 2 + r ** 2 * my ** 2) / y)


def pull(year, tables, geos, tag):
    out = {}
    for t in tables:
        for g, q in geos:
            try:
                rows = census(f"{year}/acs/acs5", dict(get=f"NAME,group({t})", **q), f"{KEY}/acs5_{year}_{t}_{g}.json")
            except Exception as e:                              # table not published for this vintage
                print(f"   no {t} for {year} {g}: {str(e)[:60]}")
                continue
            for r in rows:
                key = {"state": "ohio", "us": "us"}.get(g) or (r["state"] + r["county"] + (r.get("tract") or ""))
                d = out.setdefault(key, {})
                for k, v in r.items():
                    if k.startswith(t + "_") and k.endswith("E") and not k.endswith("EA"):
                        d[k[:-1]] = (acs.num(v), acs.moe_num(r.get(k[:-1] + "M")))
    return out


def lab_lines(year, table, test):
    return [k for k, v in acs.labels(year, table).items() if test([p.rstrip(":") for p in v.split("!!")[1:]])]


def unins_lines(year):
    num_ = lab_lines(year, "B27010", lambda p: len(p) == 3 and p[1] != "65 years and over" and p[2] == "No health insurance coverage")
    den = lab_lines(year, "B27010", lambda p: len(p) == 2 and p[1] in ("Under 19 years", "19 to 34 years", "Under 18 years", "18 to 34 years", "35 to 64 years"))
    assert len(num_) == 3 and len(den) == 3, (year, num_, den)
    return num_, den


def prime_lines(year):
    groups = ("25 to 29 years", "30 to 34 years", "35 to 44 years", "45 to 54 years")
    tot, emp = [], []
    for k, v in acs.labels(year, "B23001").items():
        p = [x.rstrip(":") for x in v.split("!!")]
        if not any(g in p for g in groups):
            continue
        if p[-1] in groups:
            tot.append(k)
        elif p[-1] in ("Armed Forces", "In Armed Forces") or (p[-1] == "Employed" and "Civilian" in p):
            emp.append(k)
    assert len(tot) == 8 and len(emp) == 16
    return tot, emp


AGE65 = ("65 and 66 years", "67 to 69 years", "70 to 74 years", "75 to 79 years", "80 to 84 years", "85 years and over")
AGEP = ("25 to 29 years", "30 to 34 years", "35 to 39 years", "40 to 44 years", "45 to 49 years", "50 to 54 years")


def compute(year, d, full=True):
    """{measure: (value, moe)} for one geography."""
    out = {}
    nu, de = unins_lines(year)
    out["uninsured_u65"] = acs.share(acs.total(d, nu), acs.total(d, de))
    out["mean_commute"] = ratio(S(d, "B08013_001"), S(d, "B08303_001"))
    out["overcrowded_share"] = acs.share(acs.total(d, ["B25014_005", "B25014_006", "B25014_007", "B25014_011", "B25014_012", "B25014_013"]), S(d, "B25014_001"))
    out["homeownership"] = acs.share(S(d, "B25003_002"), S(d, "B25003_001"))
    out["vacancy_rate"] = acs.share(S(d, "B25002_003"), S(d, "B25002_001"))
    out["old_housing_share"] = acs.share(acs.total(d, ["B25034_010", "B25034_011"]), S(d, "B25034_001"))
    out["broadband_share"] = acs.share(S(d, "B28002_004"), S(d, "B28002_001"))
    out["no_vehicle_share"] = acs.share(acs.total(d, ["B25044_003", "B25044_010"]), S(d, "B25044_001"))
    enr = ["B14003_004", "B14003_013", "B14003_032", "B14003_041"]
    out["preschool_enrolled"] = acs.share(acs.total(d, enr), acs.total(d, enr + ["B14003_022", "B14003_050"]))
    out["kids_under5"] = acs.total(d, ["B01001_003", "B01001_027"])
    if not full:
        return out
    base = acs.compute(year, d)
    for k in ("median_household_income", "poverty_rate", "below_200_share", "snap_households_share", "population",
              "bachelors_or_higher", "hs_or_higher", "rent_burden", "owner_cost_burden", "disability_share"):
        out[k] = base[k]
    pt, pe = prime_lines(year)
    out["prime_age_epop"] = acs.share(acs.total(d, pe), acs.total(d, pt))
    lab = acs.labels(year, "B01001")
    pop = S(d, "B01001_001")
    out["prime_age_share"] = acs.share(acs.total(d, [k for k, v in lab.items() if v.split("!!")[-1] in AGEP]), pop)
    out["age65_share"] = acs.share(acs.total(d, [k for k, v in lab.items() if v.split("!!")[-1] in AGE65]), pop)
    tot = S(d, "B03002_001")
    out["nh_white_share"] = acs.share(S(d, "B03002_003"), tot)
    out["nh_black_share"] = acs.share(S(d, "B03002_004"), tot)
    out["hispanic_share"] = acs.share(S(d, "B03002_012"), tot)
    out["foreign_born_share"] = acs.share(S(d, "B05012_003"), S(d, "B05012_001"))
    return out


BRACKETS = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 75, 100, 125, 150, 200]


def median_from_brackets(d):
    n = [d.get(f"B19001_{i:03d}", (None,))[0] for i in range(2, 18)]
    if any(x is None for x in n) or sum(n) <= 0:
        return None
    half, c = sum(n) / 2, 0.0
    for i, x in enumerate(n):
        if c + x >= half and x > 0:
            if i == 15:
                return None
            return 1000 * (BRACKETS[i] + (half - c) / x * (BRACKETS[i + 1] - BRACKETS[i]))
        c += x
    return None


def aggregate(dicts, weights):
    keys = set().union(*dicts)
    out = {}
    for k in keys:
        vals = [(d.get(k, (None, None)), w) for d, w in zip(dicts, weights)]
        if any(v[0] is None for v, _ in vals):
            out[k] = (None, None)
            continue
        m = None if any(v[1] is None for v, _ in vals) else math.sqrt(sum((w * v[1]) ** 2 for v, w in vals))
        out[k] = (sum(w * v[0] for v, w in vals), m)
    return out


def weak(v):
    est, moe = v
    if est is None:
        return True
    return moe is not None and est != 0 and moe / 1.645 / abs(est) * 100 > CV_MAX


ACS_META = {  # id: label, unit, decimals, better, note
    "uninsured_u65": ("People under 65 without health insurance", "pct", 1, "lower",
                      "Civilians under 65 not living in institutions who had no health insurance when surveyed (B27010)."),
    "mean_commute": ("Average commute to work", "minutes", 1, "none",
                     "Average one-way travel time to work for workers 16 and older who do not work at home (B08013 divided by B08303)."),
    "overcrowded_share": ("Homes with more than one person per room", "pct", 1, "lower",
                          "Occupied homes with more than 1.0 occupant per room, owners and renters (B25014). HUD and the Census Bureau use this as a common crowding measure."),
    "homeownership": ("Homes lived in by their owners", "pct", 1, "none", "Occupied homes that are owner-occupied (B25003)."),
    "vacancy_rate": ("Vacant homes", "pct", 1, "none",
                     "Housing units with no one living in them when surveyed, including homes for sale or rent, seasonal homes and abandoned homes (B25002)."),
    "old_housing_share": ("Homes built before 1950", "pct", 1, "none",
                          "Housing units built in 1949 or earlier (B25034). Older homes are more likely to have lead paint and need repairs; age alone does not show condition."),
    "broadband_share": ("Households with a broadband internet subscription", "pct", 1, "higher",
                        "Households with a broadband subscription of any type, including a cellular data plan (B28002)."),
    "no_vehicle_share": ("Households without a vehicle", "pct", 1, "none",
                         "Occupied homes with no car, van or truck available (B25044)."),
    "preschool_enrolled": ("Children 3 and 4 enrolled in school or preschool", "pct", 1, "higher",
                           "Children ages 3 and 4 enrolled in public or private nursery school, preschool or kindergarten (B14003)."),
    "median_household_income": ("Median household income", "usd", 0, "higher", "Half of households earn more and half earn less, in 2024 dollars (B19013). District figures are estimated from income brackets (B19001)."),
    "poverty_rate": ("People in poverty", "pct", 1, "lower", "People whose family income is below the federal poverty line (C17002)."),
    "below_200_share": ("People below 200% of the poverty line", "pct", 1, "lower", "People in poverty plus those just above it (C17002). For two adults and two children in 2024, 200% of the Census Bureau's poverty threshold was about $63,600 a year."),
    "snap_households_share": ("Households that got SNAP food aid (survey)", "pct", 1, "none", "Households that received SNAP at any time in the past 12 months, as reported in the survey (B22003). Surveys tend to undercount program use."),
    "population": ("Population", "count", 0, "none", "Total residents (B01003)."),
    "bachelors_or_higher": ("Adults with a bachelor's degree or more", "pct", 1, "higher", "Adults 25 and older whose highest degree is a bachelor's or higher (B15003)."),
    "hs_or_higher": ("Adults with a high school diploma or more", "pct", 1, "higher", "Adults 25 and older with a high school diploma, GED or higher (B15003)."),
    "rent_burden": ("Renters paying 30% or more of income on rent", "pct", 1, "lower", "Renter households whose gross rent is 30% or more of household income (B25070). HUD calls these households cost-burdened."),
    "owner_cost_burden": ("Owners with a mortgage paying 30% or more on housing", "pct", 1, "lower", "Owner households with a mortgage whose monthly costs are 30% or more of household income (B25091)."),
    "disability_share": ("People with a disability", "pct", 1, "none", "Civilians not in institutions reporting a hearing, vision, thinking, walking, self-care or independent-living difficulty (B18101)."),
    "prime_age_epop": ("Prime-age workers: share of people 25 to 54 with a job", "pct", 1, "higher", "People 25 to 54 who are employed (civilian jobs plus armed forces) as a share of all people 25 to 54 (B23001). Places with a prison, college dorms or a nursing home may show a lower rate, since most of those residents are not in the labor force."),
    "prime_age_share": ("Residents ages 25 to 54", "pct", 1, "none", "Share of all residents who are 25 to 54 (B01001)."),
    "age65_share": ("Residents 65 and older", "pct", 1, "none", "Share of all residents who are 65 or older (B01001)."),
    "nh_white_share": ("White, not Hispanic", "pct", 1, "none", "Share of all residents (B03002)."),
    "nh_black_share": ("Black, not Hispanic", "pct", 1, "none", "Share of all residents (B03002)."),
    "hispanic_share": ("Hispanic or Latino (any race)", "pct", 1, "none", "Share of all residents (B03002)."),
    "foreign_born_share": ("Foreign-born residents", "pct", 1, "none", "Residents who were not U.S. citizens at birth, including naturalized citizens (B05012)."),
}
TRACT_ACS = [k for k in ACS_META]
PLACES = {  # id: measureid, label, better
    "places_food_insecurity": ("FOODINSECU", "Adults with food insecurity in the past year", "lower"),
    "places_housing_insecurity": ("HOUSINSECU", "Adults with housing insecurity in the past year", "lower"),
    "places_utility_shutoff": ("SHUTUTILITY", "Adults threatened with a utility shutoff in the past year", "lower"),
    "places_ghlth": ("GHLTH", "Adults in fair or poor health", "lower"),
    "places_diabetes": ("DIABETES", "Adults with diagnosed diabetes", "lower"),
    "places_obesity": ("OBESITY", "Adults with obesity", "lower"),
    "places_smoking": ("CSMOKING", "Adults who currently smoke cigarettes", "lower"),
    "places_checkup": ("CHECKUP", "Adults with a routine checkup in the past year", "higher"),
    "places_dental": ("DENTAL", "Adults who saw a dentist in the past year", "higher"),
    "places_mental_distress": ("MHLTH", "Adults with frequent mental distress", "lower"),
    "places_depression": ("DEPRESSION", "Adults ever told they have depression", "lower"),
    "places_loneliness": ("LONELINESS", "Adults who feel lonely always, usually or sometimes", "lower"),
    "places_emotional_support": ("EMOTIONSPT", "Adults who lack social and emotional support", "lower"),
    "places_no_transportation": ("LACKTRPT", "Adults without reliable transportation in the past year", "lower"),
}
PLACES_NOTE = ("CDC model estimate for adults 18 and older (crude prevalence), from the Behavioral Risk Factor Surveillance "
               "System and Census data. It is not a direct count, nearby places can look alike because the model shares "
               "information across areas, and CDC says estimates from different PLACES releases should not be compared "
               "over time. ± is half the width of CDC's 95% interval. Ohio is the tract values weighted by adults.")


def socrata(ds, where, name):
    rows, off = [], 0
    while True:
        q = {"$where": where, "$limit": "50000", "$offset": str(off), "$order": ":id"}
        from urllib.parse import urlencode
        page = json.loads(cached(RAW / KEY / f"{name}_{off}.json", f"https://data.cdc.gov/resource/{ds}.json?" + urlencode(q)))
        rows += page
        if len(page) < 50000:
            return rows
        off += 50000


def layers():
    lay = {}
    for p in sorted(PROC.glob("*.json")):
        j = json.loads(p.read_text())
        if isinstance(j, dict) and "metrics" in j and "counties" in j:
            for k in j["metrics"]:
                lay[k] = j
    return lay


def rnd(v, d):
    return None if v is None else round(v, d + 2)


def inside(x, y, ring):
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def childcare_by_tract():
    """Licensed programs (not school-age only) and those rated Silver or Gold, by tract. Uses 41_childcare's rules."""
    cc = importlib.import_module("41_childcare")
    snap = sorted((RAW / "dcy").glob("ohio_daycares_*.json"))[-1]
    d = json.loads(snap.read_text())
    keep = [r for r in d["rows"] if r["program_type"] in cc.LICENSED and r["program_status"] in cc.ACTIVE]
    young = [r for r in keep if cc.LICENSED[r["program_type"]] != "school_age"]
    # Full-resolution tract shapes (no server simplification), so points near a boundary or the Lake Erie shore are
    # placed in the right tract. The map itself uses the simplified shapes.
    geo70 = importlib.import_module("70_wb_geo")
    polys = {}
    for c in sorted({t[2:5] for t in GEO["tracts"]}):
        full = geo70.tiger(6, f"STATE='{STF}' AND COUNTY='{c}'", f"tiger_tracts_full_{c}.geojson", offset="0")
        for f in full["features"]:
            g = f["geometry"]
            rs = g["coordinates"] if g["type"] == "Polygon" else [r for p in g["coordinates"] for r in p]
            xs = [p[0] for r in rs for p in r]
            ys = [p[1] for r in rs for p in r]
            polys[f["properties"]["GEOID"]] = (min(xs), min(ys), max(xs), max(ys), rs)
    n, good, miss = Counter(), Counter(), []
    for r in young:
        x, y = r["x"], r["y"]
        hit = [t for t, (a, b, c_, e, rs) in polys.items() if a <= x <= c_ and b <= y <= e
               and sum(inside(x, y, ring) for ring in rs) % 2 == 1]
        if not hit:
            miss.append(r["program_name"])
            continue
        n[hit[0]] += 1
        good[hit[0]] += r["sutq_rating"] in ("Silver", "Gold")
    print(f"child care: {len(young)} programs for young children, {len(miss)} not placed in a tract ({miss[:3]})")
    return n, good, d["pulled"], len(young), len(miss)


if __name__ == "__main__":
    T = GEO["tracts"]
    tids = sorted(T)
    lay = layers()
    # --- ACS pulls
    tr_raw = pull(2024, TRACT_TABLES, [("tract", {"for": "tract:*", "in": f"state:{STF}"}), ("state", {"for": f"state:{STF}"}),
                                       ("us", {"for": "us:1"}), ("county", {"for": "county:*", "in": f"state:{STF}"})], "t")
    hist = {y: pull(y, ["B28002", "B25044", "B08303", "B08013", "B25014", "B25002", "B25003", "B25034", "B14003", "B27010", "B01001"],
                    [("state", {"for": f"state:{STF}"}), ("county", {"for": "county:*", "in": f"state:{STF}"}), ("us", {"for": "us:1"})], "h")
            for y, _ in VINT[:2]}
    missing = [t for t in tids if t not in tr_raw]
    assert not missing, missing[:5]

    tract_c = {t: compute(2024, tr_raw[t]) for t in tids}
    cnty_c = {f: compute(2024, tr_raw[f]) for f in tr_raw if len(f) == 5}
    oh_c, us_c = compute(2024, tr_raw["ohio"]), compute(2024, tr_raw["us"])
    hist_c = {y: {g: compute(y, d, full=False) for g, d in hist[y].items()} for y in hist}

    # --- districts: weighted sums of tract table lines
    cds = sorted(GEO["districts"])
    dist_raw, dist_c, dist_w, commute_skipped = {}, {}, {}, {}
    for cd in cds:
        w = {t: v["cd"][cd] / v["pop2020"] for t, v in T.items() if v["pop2020"] and cd in v["cd"]}
        dist_w[cd] = w
        agg = aggregate([tr_raw[t] for t in w], list(w.values()))
        dist_raw[cd] = agg
        dist_c[cd] = compute(2024, agg)
        dist_c[cd]["median_household_income"] = (median_from_brackets(agg), None)
        # The Census Bureau withholds aggregate travel time (B08013) for a few tracts with almost no commuters. Average
        # commute uses the tracts that have it, in both the numerator and the denominator.
        ok = [t for t in w if tr_raw[t].get("B08013_001", (None,))[0] is not None]
        if len(ok) < len(w):
            sub = aggregate([tr_raw[t] for t in ok], [w[t] for t in ok])
            dist_c[cd]["mean_commute"] = ratio(sub["B08013_001"], sub["B08303_001"])
            commute_skipped[cd] = sorted(set(w) - set(ok))
    print("average commute: tracts left out for withheld travel time:", {cd: v for cd, v in commute_skipped.items()},
          "total", len({t for v in commute_skipped.values() for t in v}))
    # check against the OH-10 page, which uses the same method and data
    oh10 = PROC / "oh10" / "data.json"
    if oh10.exists():
        o = json.loads(oh10.read_text())["district"]
        diffs = {k: round(dist_c["10"][k][0] - o[k]["v"], 6) for k in o if k in dist_c["10"] and o[k]["v"] is not None and dist_c["10"][k][0] is not None}
        print("district 10 vs OH-10 page (should be ~0):", {k: v for k, v in diffs.items() if abs(v) > 1e-6} or "all match")
    pub = median_from_brackets(tr_raw["ohio"])
    print(f"bracket median for Ohio {pub:,.0f} vs published {tr_raw['ohio']['B19013_001'][0]:,.0f}")

    # --- PLACES
    want = ",".join(f"'{v[0]}'" for v in PLACES.values())
    pt = socrata("cwsq-ngmh", f"stateabbr='OH' and datavaluetypeid='CrdPrv' and measureid in ({want})", "places_tract_oh")
    pc = socrata("swc5-untb", f"stateabbr='OH' and datavaluetypeid='CrdPrv' and measureid in ({want})", "places_county_oh_crude")
    ptr = {(r["measureid"], r["locationname"]): r for r in pt}
    pco = {(r["measureid"], r["locationid"]): r for r in pc}
    adults = {r["locationname"]: float(r["totalpop18plus"]) for r in pt if r.get("totalpop18plus")}
    pyear = {}
    for code, *_ in PLACES.values():
        ys = {r["year"] for r in pt if r["measureid"] == code}
        assert len(ys) == 1, (code, ys)
        pyear[code] = ys.pop()

    # --- child care
    ccn, ccg, cc_pulled, cc_total, cc_miss = childcare_by_tract()

    # --- assemble
    measures, county, series, district, tract, tract_moe, tract_weak = {}, {}, {}, {}, {}, {}, {}
    ohio, ohio_moe, us = {}, {}, {}
    ids = [m["id"] for m in WM.MEASURES] + [i for v in WM.MONEY.values() for i in v] + WM.CONTEXT
    reg = {m["id"]: m for m in WM.MEASURES}
    for dim, xs in WM.MONEY.items():
        for i in xs:
            reg[i] = {"id": i, "dim": dim, "role": "money"}
    for i in WM.CONTEXT:
        reg[i] = {"id": i, "dim": "context", "role": "context"}
    fips = sorted(GEO["counties"])
    skipped = []
    for i in ids:
        r = reg[i]
        meta = None
        if i in ACS_META and (i in NEW_ACS or i not in lay or i in TRACT_ACS):
            lab, unit, dec, better, note = ACS_META[i]
            meta = dict(label=lab, unit=unit, decimals=dec, better=better, note=note + (" ± is the 90% margin of error." if unit != "count" else ""),
                        source="U.S. Census Bureau, American Community Survey 5-year estimates", period_label="2020-2024 ACS 5-year")
            tract[i] = [rnd(tract_c[t][i][0], dec) for t in tids]
            tract_moe[i] = [rnd(tract_c[t][i][1], dec) for t in tids]
            tract_weak[i] = [n for n, t in enumerate(tids) if tract_c[t][i][0] is not None and weak(tract_c[t][i])]
            district[i] = {cd: [rnd(dist_c[cd][i][0], dec), rnd(dist_c[cd][i][1], dec),
                                "high_moe" if dist_c[cd][i][0] is not None and weak(dist_c[cd][i]) else None] for cd in cds}
            ohio[i], ohio_moe[i], us[i] = oh_c[i][0], oh_c[i][1], us_c[i][0]
            j = lay.get(i)
            same = j is not None and abs(j["ohio"][i]["latest"] - ohio[i]) < 1e-6 * max(1, abs(ohio[i]))
            if j is not None and not same:
                print(f"   {i}: county layer uses another source ({j['metrics'][i]['source'][:50]}); using ACS for counties")
            if same:      # county values and history from the county layer (same method, checked in the tie-out)
                county[i] = {f: [j["counties"][f][i].get("latest"), j["counties"][f][i].get("moe"),
                                 j["counties"][f][i].get("flag") or ("high_moe" if j["counties"][f][i].get("latest") is not None
                                                                     and weak((j["counties"][f][i].get("latest"), j["counties"][f][i].get("moe"))) else None)]
                             for f in fips}
                series[i] = {f: j["counties"][f][i].get("series") for f in fips}
                series[i]["ohio"] = j["ohio"][i].get("series")
            else:
                county[i] = {f: [cnty_c[f][i][0], cnty_c[f][i][1], "high_moe" if cnty_c[f][i][0] is not None and weak(cnty_c[f][i]) else None]
                             for f in fips}
                series[i] = {}
                for f in fips + ["ohio"]:
                    s = [[p, hist_c[y][f][i][0]] for y, p in VINT[:2] if f in hist_c[y] and i in hist_c[y][f] and hist_c[y][f][i][0] is not None]
                    s.append([VINT[2][1], (oh_c if f == "ohio" else cnty_c[f])[i][0]])
                    series[i][f] = s
        elif i in PLACES:
            code, lab, better = PLACES[i]
            meta = dict(label=lab, unit="pct", decimals=1, better=better, note=PLACES_NOTE,
                        source="CDC PLACES: Local Data for Better Health, 2025 release", period_label=f"{pyear[code]} estimate")
            def pv(r):
                if not r or r.get("data_value") in (None, ""):
                    return None, None
                return float(r["data_value"]), (float(r["high_confidence_limit"]) - float(r["low_confidence_limit"])) / 2
            tv = {t: pv(ptr.get((code, t))) for t in tids}
            tract[i] = [rnd(tv[t][0], 1) for t in tids]
            tract_moe[i] = [rnd(tv[t][1], 1) for t in tids]
            county[i] = {f: list(pv(pco.get((code, f)))) + [None] for f in fips}
            def wavg(w):
                num_ = den = 0.0
                for t, x in w.items():
                    if tv[t][0] is not None and t in adults:
                        num_ += tv[t][0] * adults[t] * x
                        den += adults[t] * x
                return num_ / den if den else None
            district[i] = {cd: [rnd(wavg(dist_w[cd]), 1), None] for cd in cds}
            ohio[i] = wavg({t: 1.0 for t in tids})
            nov = [t for t in tids if tv[t][0] is None and T[t]["pop2020"] > 0]
            if nov:
                print(f"PLACES {code}: {len(nov)} populated tracts without a value")
        elif i in ("childcare_programs_per1k", "childcare_rated_share"):
            kids_t = {t: tract_c[t]["kids_under5"][0] for t in tids}
            def rate(ts, w=None):
                w = w or {t: 1.0 for t in ts}
                n_ = sum(ccn[t] * x for t, x in w.items())
                k_ = sum((kids_t[t] or 0) * x for t, x in w.items())
                g_ = sum(ccg[t] * x for t, x in w.items())
                return (n_ / k_ * 1000 if k_ else None) if i == "childcare_programs_per1k" else (g_ / n_ * 100 if n_ else None)
            if i == "childcare_programs_per1k":
                meta = dict(label="Licensed child care programs per 1,000 children under 5", unit="rate", decimals=1, better="higher",
                            source="Ohio Department of Children and Youth, licensed program list; ACS 2020-2024 (children under 5)",
                            period_label=f"programs open on {cc_pulled}",
                            note="Licensed centers, family child care homes and preschools open on the pull date, placed by their "
                                 "address, per 1,000 children under 5. School-age-only programs are left out. A program counts once "
                                 "no matter its size, so this is not a count of slots. Not shown for tracts: families often use "
                                 "care outside their own tract. A tract split by a district line counts its programs by the share of "
                                 "its 2020 residents in each district."
                                 + (f" {cc_miss} of {cc_total} programs could not be placed and are left out." if cc_miss else ""))
            else:
                meta = dict(label="Licensed programs rated Silver or Gold", unit="pct", decimals=1, better="higher",
                            source="Ohio Department of Children and Youth, licensed program list (Step Up To Quality ratings)",
                            period_label=f"programs open on {cc_pulled}",
                            note="Share of licensed centers, family child care homes and preschools with a Silver or Gold rating in "
                                 "Step Up To Quality, Ohio's rating system (Bronze, Silver, Gold). Programs with no rating count as "
                                 "not rated Silver or Gold. A program counts once no matter its size. Not shown for tracts, for the same "
                                 "reason as programs per 1,000 children.")
            county[i] = {f: [rate([t for t in tids if t[:5] == f]), None, None] for f in fips}
            district[i] = {cd: [rnd(rate(None, dist_w[cd]), 1), None] for cd in cds}
            ohio[i] = rate(tids)
        elif i in lay:
            j = lay[i]
            m = j["metrics"][i]
            meta = {k: m.get(k) for k in ("label", "unit", "decimals", "better", "source", "period_label", "note")}
            county[i] = {f: [j["counties"].get(f, {}).get(i, {}).get("latest"), j["counties"].get(f, {}).get(i, {}).get("moe"),
                             j["counties"].get(f, {}).get(i, {}).get("flag")] for f in fips}
            series[i] = {f: j["counties"].get(f, {}).get(i, {}).get("series") for f in fips}
            series[i]["ohio"] = (j["ohio"].get(i) or {}).get("series")
            ohio[i] = (j["ohio"].get(i) or {}).get("latest")
            if any(i in v for v in j.get("tracts", {}).values()):     # a layer that also publishes tract values
                tc = {t: j["tracts"].get(t, {}).get(i) or {} for t in tids}
                tract[i] = [rnd(tc[t].get("latest"), m["decimals"]) for t in tids]
                tract_moe[i] = [None] * len(tids)
        else:
            skipped.append(i)
            continue
        meta.update(dim=r["dim"], role=r["role"], headline=bool(r.get("headline")), standard=r.get("standard"),
                    levels=[lv for lv, have in (("county", i in county), ("district", i in district), ("tract", i in tract)) if have])
        measures[i] = meta
    nat = json.loads((PROC / "national.json").read_text())["national"]
    for i in measures:
        if i not in us and i in nat:
            us[i] = nat[i]["us"]
    print("skipped (no data yet):", skipped)

    # trims: drop empty series
    series = {i: {g: s for g, s in v.items() if s and len(s) > 1} for i, v in series.items()}
    data = {"dims": WM.DIMENSIONS, "measures": measures, "tract_ids": tids, "county": county, "series": series,
            "district": district, "tract": tract, "tract_moe": tract_moe, "tract_weak": tract_weak,
            "ohio": ohio, "ohio_moe": ohio_moe, "us": us, "cv_max": CV_MAX,
            "district_note": {cd: {"tracts": len(dist_w[cd]), "split": sum(1 for x in dist_w[cd].values() if x < 1)} for cd in cds}}
    write_json(f"{KEY}/data.json", data)
    print({k: len(json.dumps(v, separators=(",", ":"))) // 1024 for k, v in data.items()}, "KB")
    for i in ("below_200_share", "uninsured_u65", "broadband_share", "places_loneliness", "childcare_programs_per1k", "childcare_rated_share"):
        if i in measures:
            cv = [v[0] for v in county[i].values() if v[0] is not None]
            print(f"{i:28} Ohio {ohio.get(i)}  US {us.get(i)}  counties {min(cv):.1f}-{max(cv):.1f}  district 10 {district.get(i, {}).get('10')}")
