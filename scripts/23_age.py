"""Age structure, prime-age work and fertility for Ohio counties. Writes data/processed/age.json (theme "people").

- prime_age_share, age65_share: Census population estimates (Vintage 2025, county characteristics by age
  and sex, cc-est2025-agesex-39.csv), July 1 of 2020-2025. Ohio = sum of its 88 counties (the file has no
  state row; in the estimates program the state total equals the sum of its counties).
- prime_age_epop: ACS 5-year table B23001, people 25 to 54 with a job (civilian employed plus armed forces)
  as a share of all people 25 to 54. Periods 2010-2014, 2015-2019, 2020-2024. 90% margin of error by the
  Census approximation for proportions.
- general_fertility_rate: births per 1,000 women ages 15 to 44. Births are the estimates program's births for
  the year ending June 30 (co-est2025-alldata.csv, BIRTHS2021..BIRTHS2025); women 15 to 44 are the average of
  the July 1 estimates at the start and end of that year.
"""
import io
import json
import math

import pandas as pd

from common import RAW, STATE, cached, census, write_json

AGESEX = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/asrh/cc-est2025-agesex-39.csv"
ALLDATA = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv"
PRIME = ["AGE2529_TOT", "AGE3034_TOT", "AGE3539_TOT", "AGE4044_TOT", "AGE4549_TOT", "AGE5054_TOT"]
ACS = {"2014": "2010-2014", "2019": "2015-2019", "2024": "2020-2024"}
PRIME_GROUPS = ("25 to 29 years", "30 to 34 years", "35 to 44 years", "45 to 54 years")


def pep():
    a = pd.read_csv(io.BytesIO(cached(RAW / "census_pep" / "cc-est2025-agesex-39.csv", AGESEX)), encoding="latin-1")
    a = a[(a.SUMLEV == 50) & (a.YEAR >= 2)].copy()           # YEAR 1 is the April 1, 2020 base; 2..7 are July 1, 2020..2025
    a["year"] = (a.YEAR + 2018).astype(str)
    a["fips"] = STATE + a.COUNTY.astype(int).map("{:03d}".format)
    assert a.fips.nunique() == 88 and not a.duplicated(["fips", "year"]).any()
    a["prime"] = a[PRIME].sum(axis=1)
    cols = ["POPESTIMATE", "prime", "AGE65PLUS_TOT", "AGE1544_FEM"]
    oh = a.groupby("year", as_index=False)[cols].sum()
    oh["fips"] = "ohio"
    a = pd.concat([a[["fips", "year"] + cols], oh[["fips", "year"] + cols]])
    a["prime_share"] = a.prime / a.POPESTIMATE * 100
    a["s65"] = a.AGE65PLUS_TOT / a.POPESTIMATE * 100

    b = pd.read_csv(io.BytesIO(cached(RAW / "census_pep" / "co-est2025-alldata.csv", ALLDATA)), encoding="latin-1")
    b = b[b.STATE == int(STATE)].copy()
    b["fips"] = b.apply(lambda r: "ohio" if r.SUMLEV == 40 else STATE + f"{int(r.COUNTY):03d}", axis=1)
    births = b.set_index("fips")[[f"BIRTHS{y}" for y in range(2021, 2026)]]
    fem = a.pivot(index="fips", columns="year", values="AGE1544_FEM")
    gfr = {}
    for f in fem.index:
        gfr[f] = [[str(y), births.loc[f, f"BIRTHS{y}"] / ((fem.loc[f, str(y - 1)] + fem.loc[f, str(y)]) / 2) * 1000]
                  for y in range(2021, 2026)]
    # the state row's births must equal the sum of its counties
    assert abs(births.drop("ohio").sum().sum() - births.loc["ohio"].sum()) < 1, "county births do not sum to Ohio"
    return a, gfr


def acs_epop(year):
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
        elif parts[-1] in ("Armed Forces", "In Armed Forces"):   # the 2014 table says "In Armed Forces"
            af.append(k)
        elif parts[-1] == "Employed" and "Civilian" in parts:
            emp.append(k)
    assert len(tot) == 8 and len(emp) == 8 and len(af) == 8, (year, len(tot), len(emp), len(af))
    out = {}
    for geo, params in (("county", {"for": "county:*", "in": f"state:{STATE}"}), ("state", {"for": f"state:{STATE}"})):
        rows = census(f"{year}/acs/acs5", dict(params, get="group(B23001)"), f"{year}_B23001_{geo}.json")
        for r in rows:
            f = "ohio" if geo == "state" else STATE + r["county"]
            n = sum(float(r[k + "E"]) for k in emp + af)
            d = sum(float(r[k + "E"]) for k in tot)
            # negative margins are Census annotation codes (e.g. -555555555: controlled, no sampling error); count them as 0
            mn = math.sqrt(sum(max(float(r[k + "M"]), 0) ** 2 for k in emp + af))
            md = math.sqrt(sum(max(float(r[k + "M"]), 0) ** 2 for k in tot))
            p = n / d
            inner = mn ** 2 - p ** 2 * md ** 2
            moe = math.sqrt(inner if inner > 0 else mn ** 2 + p ** 2 * md ** 2) / d   # Census approximation; ratio form if negative
            out[f] = (p * 100, moe * 100)
    assert len(out) == 89
    return out


GQ_FLAG = 5.0   # percent of residents living in group quarters at which the prime-age work rate gets a flag


def group_quarters():
    """Share of residents in group quarters (prisons, college dorms, nursing homes, military barracks),
    ACS 2020-2024 B26001 total over B01003 total population."""
    out = {}
    for geo, params in (("county", {"for": "county:*", "in": f"state:{STATE}"}), ("state", {"for": f"state:{STATE}"})):
        rows = census("2024/acs/acs5", dict(params, get="B26001_001E,B01003_001E"), f"2024_B26001_{geo}.json")
        for r in rows:
            out["ohio" if geo == "state" else STATE + r["county"]] = float(r["B26001_001E"]) / float(r["B01003_001E"]) * 100
    return out


if __name__ == "__main__":
    a, gfr = pep()
    gq = group_quarters()
    epop = {ACS[y]: acs_epop(y) for y in ACS}
    fips = sorted(f for f in a.fips.unique() if f != "ohio")
    metrics = {
        "prime_age_share": dict(label="Residents in their prime working years (ages 25 to 54)", theme="people", unit="pct", decimals=1,
                                better="none", source="U.S. Census Bureau, Population Estimates Program (Vintage 2025)",
                                vintage="July 1, 2020-2025; pulled 2026-11-09", period_label="July 1, 2025",
                                note="Share of all residents who are 25 to 54, the ages when most people work. Modeled estimates; each new vintage revises back to 2020."),
        "age65_share": dict(label="Residents 65 and older", theme="people", unit="pct", decimals=1, better="none",
                            source="U.S. Census Bureau, Population Estimates Program (Vintage 2025)",
                            vintage="July 1, 2020-2025; pulled 2026-11-09", period_label="July 1, 2025",
                            note="Share of all residents who are 65 or older. Modeled estimates; each new vintage revises back to 2020."),
        "prime_age_epop": dict(label="Prime-age workers: share of people 25 to 54 with a job", theme="people", unit="pct", decimals=1,
                               better="higher", source="U.S. Census Bureau, American Community Survey 5-year estimates, table B23001",
                               vintage="2010-2014, 2015-2019, 2020-2024; pulled 2026-11-09", period_label="2020-2024 ACS 5-year",
                               note="People 25 to 54 who are employed (civilian jobs plus armed forces) as a share of all people 25 to 54, including those in group quarters. Counties where 5% or more of residents live in group quarters (prisons, college dorms, nursing homes) are flagged, because those residents rarely hold jobs. Survey estimate; ± is the 90% margin of error by the Census approximation for proportions."),
        "general_fertility_rate": dict(label="Fertility rate: births per 1,000 women ages 15 to 44", theme="people", unit="per1000", decimals=1,
                                       better="none", source="U.S. Census Bureau, Population Estimates Program (Vintage 2025): births and women 15 to 44",
                                       vintage="years ending June 30, 2021-2025; pulled 2026-11-09", period_label="July 2024 to June 2025",
                                       note="The general fertility rate: births in the year ending June 30, per 1,000 women ages 15 to 44 (average of the July 1 estimates at the start and end of the year). Births come from National Center for Health Statistics records; the latest year is partly estimated and is revised in the next vintage. CDC's births-per-woman measure is not published for small counties."),
    }
    counties, ohio = {}, None
    for f in fips + ["ohio"]:
        g = a[a.fips == f].sort_values("year")
        row = {
            "prime_age_share": {"latest": g.prime_share.iloc[-1], "period": "2025", "series": [[y, v] for y, v in zip(g.year, g.prime_share)], "moe": None, "flag": None},
            "age65_share": {"latest": g.s65.iloc[-1], "period": "2025", "series": [[y, v] for y, v in zip(g.year, g.s65)], "moe": None, "flag": None},
            "prime_age_epop": {"latest": epop["2020-2024"][f][0], "period": "2020-2024",
                               "series": [[p, epop[p][f][0]] for p in ACS.values()], "moe": epop["2020-2024"][f][1],
                               "flag": (f"{gq[f]:.0f}% of residents live in group quarters such as prisons, dorms or nursing homes, which pulls this rate down"
                                        if gq[f] >= GQ_FLAG else None)},
            "general_fertility_rate": {"latest": gfr[f][-1][1], "period": "2025", "series": gfr[f], "moe": None, "flag": None},
        }
        if f == "ohio":
            ohio = row
        else:
            counties[f] = row
    for r in list(counties.values()) + [ohio]:
        for m in r.values():
            ps = [p for p, _ in m["series"]]
            assert len(ps) == len(set(ps)), "duplicate periods"
    flagged = sorted((round(gq[f], 1), f) for f in fips if gq[f] >= GQ_FLAG)
    print("group-quarters flag:", flagged)
    big = [(f, round(r["prime_age_epop"]["moe"], 1)) for f, r in counties.items() if r["prime_age_epop"]["moe"] > 10]
    assert not big, f"implausible margins: {big}"
    write_json("age.json", {"metrics": metrics, "counties": counties, "ohio": ohio, "extras": {}})
    for f in ("39049", "39163", "39131", "ohio"):
        r = counties.get(f, ohio)
        print(f, {k: round(v["latest"], 1) for k, v in r.items()}, "epop moe", round(r["prime_age_epop"]["moe"], 1))
