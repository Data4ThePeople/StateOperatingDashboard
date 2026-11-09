"""County table for a district page in a state without a statewide dashboard (used by 61_district_data.py).

Six measures every state has, pulled for the district's counties with the same method the Ohio statewide
layers use, for the same period as the state and U.S. figures in data/processed/national.json:

- unemployment_rate: BLS LAUS county annual average (series LAUCN<fips>0000000003, period M13).
- avg_weekly_wage: BLS QCEW county annual averages file, all ownerships, all industries (own 0, industry 10,
  aggregation level 70).
- uninsured_under65: Census SAHIE, all incomes, under 65 (AGECAT 0, IPRCAT 0, both sexes, all races).
- saipe_child_poverty_rate: Census SAIPE, ages 0 to 17.
- overdose_rate_per100k: CDC NCHS VSRR provisional county overdose deaths (gb4e-yj24) for the 12 months ending
  in national.json's period, over the Census July 1 population for that year (2025 population for 2026 periods).
- pop_change_pct: Census population estimates, Vintage 2025, April 1, 2020 estimates base to July 1, 2025.

Labels, units and notes come from the Ohio statewide layers, so the measure means the same thing on both pages.
"""
import csv
import importlib
import io
import json
import urllib.parse

from common import PROC, RAW, cached, census

jobs = importlib.import_module("10_jobs_industry")
IDS = ["unemployment_rate", "avg_weekly_wage", "uninsured_under65", "saipe_child_poverty_rate",
       "overdose_rate_per100k", "pop_change_pct"]
PEP = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv"


def num(x):
    x = (x or "").strip()
    return None if x in ("", ".", "-", "N/A", "null") else float(x.replace(",", ""))


def table(key, st, st_abbr, state_name, counties):
    """counties: {3-digit code: name}. Returns {measure id: row} with one cell per county, the state and the U.S."""
    nat = json.loads((PROC / "national.json").read_text())["national"]
    meta = {}
    for name in ("jobs", "health", "popest"):
        j = json.loads((PROC / f"{name}.json").read_text())
        for k in IDS:
            if k in j["metrics"]:
                meta[k] = j["metrics"][k]
    assert set(meta) == set(IDS), set(IDS) - set(meta)
    fips = {c: st + c for c in counties}
    val = {k: {} for k in IDS}
    flag = {k: {} for k in IDS}

    # LAUS
    year = nat["unemployment_rate"]["period"]
    sid = {c: jobs.laus_id(f, 3) for c, f in fips.items()}
    got = jobs.bls_annual(list(sid.values()), int(year), int(year), f"{key}/bls_laus")
    for c, s in sid.items():
        v = [jobs.num(x) for y, p, x, _ in got[s] if p == "M13" and str(y) == year]
        assert len(v) == 1, (s, v)
        val["unemployment_rate"][c] = v[0]

    # QCEW
    year = int(nat["avg_weekly_wage"]["period"])
    for c, f in fips.items():
        d = jobs.parse(f, jobs.qcew_file(year, f), year)
        val["avg_weekly_wage"][c] = d[("0", "10", "70")][1]

    # SAHIE and SAIPE
    year = nat["uninsured_under65"]["period"]
    rows = census("timeseries/healthins/sahie", {"get": "NAME,PCTUI_PT,PCTUI_MOE,YEAR", "AGECAT": "0", "IPRCAT": "0",
                  "SEXCAT": "0", "RACECAT": "0", "time": year, "for": "county:*", "in": f"state:{st}"},
                  f"{key}/sahie_county_{year}.json")
    by = {r["county"]: r for r in rows}
    for c in counties:
        val["uninsured_under65"][c] = num(by[c]["PCTUI_PT"])
    year = nat["saipe_child_poverty_rate"]["period"]
    rows = census("timeseries/poverty/saipe", {"get": "NAME,YEAR,SAEPOVRT0_17_PT", "time": year, "for": "county:*",
                  "in": f"state:{st}"}, f"{key}/saipe_county_{year}.json")
    by = {r["county"]: r for r in rows}
    for c in counties:
        val["saipe_child_poverty_rate"][c] = num(by[c]["SAEPOVRT0_17_PT"])

    # population estimates
    pep = {r["COUNTY"]: r for r in csv.DictReader(io.StringIO(cached(RAW / "census_pep" / "co-est2025-alldata.csv", PEP)
                                                             .decode("latin-1")))
           if r["STATE"] == st and r["SUMLEV"] == "050"}
    for c in counties:
        base = float(pep[c]["ESTIMATESBASE2020"])
        val["pop_change_pct"][c] = 100 * (float(pep[c]["POPESTIMATE2025"]) - base) / base

    # overdose deaths
    period = nat["overdose_rate_per100k"]["period"]                   # "2026-03"
    q = {"$where": f"st_abbrev='{st_abbr}'", "$limit": "50000", "$order": "fips,monthendingdate"}
    od = json.loads(cached(RAW / key / f"vsrr_county_overdose_{st_abbr.lower()}.json",
                           "https://data.cdc.gov/resource/gb4e-yj24.json?" + urllib.parse.urlencode(q)))
    py = min(int(period[:4]), 2025)
    for c, f in fips.items():
        r = [x for x in od if x["fips"].zfill(5) == f and x["monthendingdate"][:7] == period]
        assert len(r) == 1, (f, period, len(r))
        v = num(r[0].get("provisional_drug_overdose"))
        val["overdose_rate_per100k"][c] = None if v is None else v / float(pep[c][f"POPESTIMATE{py}"]) * 1e5
        if v is None:
            flag["overdose_rate_per100k"][c] = "suppressed (1-9 deaths)" if "suppress" in (r[0].get("footnote") or "").lower() else "missing"

    out = {}
    for k in IDS:
        m, n = meta[k], nat[k]
        row = {"label": m["label"], "unit": m["unit"], "decimals": m["decimals"], "better": m["better"],
               "source": m["source"], "period_label": m.get("period_label"), "note": m.get("note")}
        for c, name in counties.items():
            row[name] = {"v": val[k][c], "period": n["period"], "flag": flag[k].get(c)}
        row[state_name] = {"v": n["states"][st_abbr], "period": n["period"], "flag": (n.get("flags") or {}).get(st_abbr)}
        row["U.S."] = {"v": n["us"], "period": n["period"]}
        out[k] = row
    return out
