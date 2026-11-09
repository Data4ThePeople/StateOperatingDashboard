"""Race and ethnicity, sex, and place of birth for Ohio counties. Writes data/processed/demographics.json (theme "people").

- Race and Hispanic origin, and sex: Census population estimates (Vintage 2025, county characteristics by
  age, sex, race and Hispanic origin, cc-est2025-alldata-39.csv), all ages, July 1 of 2020-2025. Ohio = sum of
  its 88 counties (the file has no state row). Groups do not overlap: Hispanic or Latino of any race, then
  non-Hispanic people by race alone, plus non-Hispanic people of two or more races. They add to 100%.
- foreign_born_share: ACS 5-year table B05012, foreign-born residents as a share of all residents. Periods
  2010-2014, 2015-2019, 2020-2024. 90% margin of error by the Census approximation for proportions.
"""
import io
import math

import pandas as pd

from common import RAW, STATE, cached, census, write_json

ALLDATA = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/asrh/cc-est2025-alldata-39.csv"
ACS = {"2014": "2010-2014", "2019": "2015-2019", "2024": "2020-2024"}
SRC = "U.S. Census Bureau, Population Estimates Program (Vintage 2025)"
VIN = "July 1, 2020-2025; pulled 2026-11-09"
EST = ("Modeled estimates; each new vintage revises back to 2020. Race groups are people who reported one race "
       "and are not Hispanic; Hispanic or Latino people can be of any race. The groups add to 100%.")

# id: (label, columns summed over _MALE and _FEMALE)
GROUPS = {
    "nh_white_share": ("White, not Hispanic", ["NHWA"]),
    "nh_black_share": ("Black, not Hispanic", ["NHBA"]),
    "hispanic_share": ("Hispanic or Latino (any race)", ["H"]),
    "nh_asian_share": ("Asian, not Hispanic", ["NHAA"]),
    "nh_multi_share": ("Two or more races, not Hispanic", ["NHTOM"]),
    "nh_native_share": ("American Indian, Alaska Native, Native Hawaiian or Pacific Islander, not Hispanic", ["NHIA", "NHNA"]),
}


def pep():
    a = pd.read_csv(io.BytesIO(cached(RAW / "census_pep" / "cc-est2025-alldata-39.csv", ALLDATA)), encoding="latin-1")
    a = a[(a.SUMLEV == 50) & (a.YEAR >= 2) & (a.AGEGRP == 0)].copy()   # YEAR 2..7 = July 1, 2020..2025; AGEGRP 0 = all ages
    a["year"] = (a.YEAR + 2018).astype(str)
    a["fips"] = STATE + a.COUNTY.astype(int).map("{:03d}".format)
    assert a.fips.nunique() == 88 and not a.duplicated(["fips", "year"]).any()
    for g, (_, cols) in GROUPS.items():
        a[g] = sum(a[c + "_MALE"] + a[c + "_FEMALE"] for c in cols)
    keep = ["TOT_POP", "TOT_FEMALE"] + list(GROUPS)
    oh = a.groupby("year", as_index=False)[keep].sum()
    oh["fips"] = "ohio"
    a = pd.concat([a[["fips", "year"] + keep], oh[["fips", "year"] + keep]])
    # the six groups must add to the total population in every county and year
    gap = (a[list(GROUPS)].sum(axis=1) - a.TOT_POP).abs().max()
    assert gap == 0, f"groups do not add to total population (max gap {gap})"
    for g in GROUPS:
        a[g] = a[g] / a.TOT_POP * 100
    a["female_share"] = a.TOT_FEMALE / a.TOT_POP * 100
    return a


def acs_foreign_born(year):
    out = {}
    for geo, params in (("county", {"for": "county:*", "in": f"state:{STATE}"}), ("state", {"for": f"state:{STATE}"})):
        rows = census(f"{year}/acs/acs5", dict(params, get="B05012_001E,B05012_001M,B05012_003E,B05012_003M"),
                      f"{year}_B05012_{geo}.json")
        for r in rows:
            f = "ohio" if geo == "state" else STATE + r["county"]
            n, d = float(r["B05012_003E"]), float(r["B05012_001E"])
            mn, md = max(float(r["B05012_003M"]), 0), max(float(r["B05012_001M"]), 0)   # negative = Census annotation code
            p = n / d
            inner = mn ** 2 - p ** 2 * md ** 2
            moe = math.sqrt(inner if inner > 0 else mn ** 2 + p ** 2 * md ** 2) / d
            out[f] = (p * 100, moe * 100)
    assert len(out) == 89
    return out


if __name__ == "__main__":
    a = pep()
    fb = {p: acs_foreign_born(y) for y, p in ACS.items()}
    fips = sorted(f for f in a.fips.unique() if f != "ohio")
    metrics = {g: dict(label=lab, theme="people", unit="pct", decimals=1, better="none", source=SRC, vintage=VIN,
                       period_label="July 1, 2025", note=f"Share of all residents. {EST}")
               for g, (lab, _) in GROUPS.items()}
    metrics["female_share"] = dict(
        label="Residents who are female", theme="people", unit="pct", decimals=1, better="none", source=SRC, vintage=VIN,
        period_label="July 1, 2025",
        note="Share of all residents who are female. The Census Bureau counts sex (male or female); it does not publish "
             "gender identity by county. Modeled estimates; each new vintage revises back to 2020.")
    metrics["foreign_born_share"] = dict(
        label="Residents born outside the U.S.", theme="people", unit="pct", decimals=1, better="none",
        source="U.S. Census Bureau, American Community Survey 5-year estimates, table B05012",
        vintage="2010-2014, 2015-2019, 2020-2024; pulled 2026-11-09", period_label="2020-2024 ACS 5-year",
        note="Foreign-born residents as a share of all residents: people who were not U.S. citizens at birth, "
             "including naturalized citizens, permanent residents, students, workers and others. People born in "
             "Puerto Rico, other U.S. territories or abroad to U.S.-citizen parents count as native-born. Survey "
             "estimate; ± is the 90% margin of error by the Census approximation for proportions.")
    counties, ohio = {}, None
    for f in fips + ["ohio"]:
        g = a[a.fips == f].sort_values("year")
        row = {m: {"latest": g[m].iloc[-1], "period": "2025", "series": [[y, v] for y, v in zip(g.year, g[m])],
                   "moe": None, "flag": None} for m in list(GROUPS) + ["female_share"]}
        row["foreign_born_share"] = {"latest": fb["2020-2024"][f][0], "period": "2020-2024",
                                     "series": [[p, fb[p][f][0]] for p in ACS.values()],
                                     "moe": fb["2020-2024"][f][1], "flag": None}
        if f == "ohio":
            ohio = row
        else:
            counties[f] = row
    big = [(f, round(r["foreign_born_share"]["moe"], 1)) for f, r in counties.items() if r["foreign_born_share"]["moe"] > 10]
    assert not big, f"implausible margins: {big}"
    write_json("demographics.json", {"metrics": metrics, "counties": counties, "ohio": ohio,
                                     "extras": {"race_groups": list(GROUPS)}})
    for f in ("39049", "39035", "39163", "ohio"):
        r = counties.get(f, ohio)
        print(f, {k: round(v["latest"], 1) for k, v in r.items()}, "fb moe", round(r["foreign_born_share"]["moe"], 1))
