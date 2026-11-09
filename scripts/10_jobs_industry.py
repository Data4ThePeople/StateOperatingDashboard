"""Jobs and industry layer for the Ohio county dashboard.

- LAUS (BLS Local Area Unemployment Statistics): unemployment rate, employed, labor force, annual
  averages 2000 to the latest full year, plus the latest month, for all 88 counties and Ohio.
  People are counted where they live. County figures are modeled, not surveyed directly.
- QCEW (BLS Quarterly Census of Employment and Wages): annual averages 2014 to the latest year,
  from the open-data area files. Jobs are counted where the job is.

Writes data/processed/jobs.json (theme "jobs"). Run: .venv/bin/python scripts/10_jobs_industry.py
"""
import csv
import datetime as dt
import io
import json
import re
import sys
import urllib.error
from concurrent.futures import ThreadPoolExecutor

from common import RAW, STATE, cached, get, get_key, write_json

TODAY = dt.date.today().isoformat()
COUNTIES = [f"{STATE}{c:03d}" for c in range(1, 176, 2)]
assert len(COUNTIES) == 88
AREAS = COUNTIES + ["ohio"]
LAUS_START = 2000
LAUS_BASE_YEAR = 2019
QCEW_START = 2014
SUPPRESS_FLAG_PCT = 20.0


def die(msg):
    sys.exit(f"ERROR: {msg}")


# ---------------------------------------------------------------- LAUS

def laus_id(area, measure):
    if area == "ohio":
        return f"LAUST{STATE}00000000000{measure:02d}"    # not seasonally adjusted, like the counties
    return f"LAUCN{area}00000000{measure:02d}"


def bls_annual(ids, start, end, folder):
    """BLS API v2 with annual averages (M13) included. common.bls_series does not ask for M13,
    so this local copy adds annualaverage=true. 50 series and 20 years per request."""
    out = {i: [] for i in ids}
    for k in range(0, len(ids), 50):
        chunk = ids[k:k + 50]
        y = start
        while y <= end:
            y2 = min(y + 19, end)
            path = RAW / folder / f"{chunk[0]}_{chunk[-1]}_{len(chunk)}_{y}_{y2}.json"
            if not path.exists():
                body = json.dumps({"seriesid": chunk, "startyear": str(y), "endyear": str(y2),
                                   "annualaverage": True,
                                   "registrationkey": get_key("BLS_API_KEY")}).encode()
                raw = get("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=body,
                          headers={"Content-Type": "application/json"})
                res = json.loads(raw)
                if res.get("status") != "REQUEST_SUCCEEDED":
                    die(f"BLS request failed: {res.get('message')}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                (path.parent / "pulled.txt").write_text(
                    dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n")
            res = json.loads(path.read_bytes())
            for s in res["Results"]["series"]:
                for o in s["data"]:
                    codes = "".join(f.get("code", "") for f in o.get("footnotes", []) if f)
                    out[s["seriesID"]].append((int(o["year"]), o["period"], o["value"], codes))
            y = y2 + 1
    for i in out:
        out[i].sort()
        keys = [(a, b) for a, b, _, _ in out[i]]
        if len(keys) != len(set(keys)):
            die(f"duplicate keys in {i}")
        if not out[i]:
            die(f"no data for {i}")
    return out


def num(v):
    v = (v or "").strip()
    if v in ("", "-", "(N)", "N"):
        return None
    return float(v.replace(",", ""))


def laus():
    end = dt.date.today().year
    measures = {3: "unemployment_rate", 5: "employed", 6: "labor_force"}
    ids = [laus_id(a, m) for a in AREAS for m in measures]
    if len(ids) != len(set(ids)):
        die("duplicate LAUS series ids")
    got = bls_annual(ids, LAUS_START, end, "bls_laus")

    annual, monthly = {}, {}
    for a in AREAS:
        for m, name in measures.items():
            rows = got[laus_id(a, m)]
            annual[(a, name)] = {str(y): num(v) for y, p, v, f in rows if p == "M13"}
            monthly[(a, name)] = [(f"{y}-{p[1:]}", num(v), "preliminary" if "P" in f else None)
                                  for y, p, v, f in rows if p != "M13"]
    years = sorted({y for k in annual for y in annual[k]})
    latest_year = max(y for y in years if all(annual[(a, "labor_force")].get(y) is not None for a in AREAS))
    latest_month = max(m for m, v, _ in monthly[("ohio", "unemployment_rate")] if v is not None)
    print(f"LAUS: annual {years[0]}-{latest_year}, latest month {latest_month}")

    per = {a: {} for a in AREAS}
    extras = {a: {} for a in AREAS}
    for a in AREAS:
        for name in measures.values():
            s = [[y, v] for y, v in sorted(annual[(a, name)].items()) if y <= latest_year and v is not None]
            last = annual[(a, name)].get(latest_year)
            per[a][name] = {"latest": last, "period": latest_year, "series": s, "moe": None,
                            "flag": None if last is not None else "missing"}
        base = annual[(a, "labor_force")].get(str(LAUS_BASE_YEAR))
        s = [[y, (v / base - 1) * 100] for y, v in sorted(annual[(a, "labor_force")].items())
             if y <= latest_year and v is not None and base]
        last = dict(s).get(latest_year)
        per[a]["labor_force_change_pct"] = {"latest": last, "period": f"{LAUS_BASE_YEAR}-{latest_year}",
                                            "series": s, "moe": None,
                                            "flag": None if last is not None else "missing"}
        lm = {}
        for name in measures.values():
            d = {m: (v, f) for m, v, f in monthly[(a, name)]}
            v, f = d.get(latest_month, (None, None))
            lm[name] = v
            if f:
                lm["flag"] = f
        lm["period"] = latest_month
        lm["seasonally_adjusted"] = False
        extras[a]["laus_latest_month"] = lm

    meta_common = {"theme": "jobs", "source": "BLS Local Area Unemployment Statistics",
                   "vintage": f"annual averages {LAUS_START}-{latest_year}; pulled {TODAY}"}
    where = "People are counted where they live, not where they work. County figures come from a BLS model, not a direct count."
    metrics = {
        "unemployment_rate": dict(meta_common, label="Unemployment rate", unit="pct", decimals=1, better="lower",
                                  period_label=f"{latest_year} annual average",
                                  note="Share of the labor force without a job and looking for one. " + where),
        "labor_force": dict(meta_common, label="Labor force", unit="count", decimals=0, better="none",
                            period_label=f"{latest_year} annual average",
                            note="Residents 16 and older who have a job or are looking for one. " + where),
        "employed": dict(meta_common, label="Employed residents", unit="count", decimals=0, better="none",
                         period_label=f"{latest_year} annual average",
                         note="Residents who had a job, wherever the job is. " + where),
        "labor_force_change_pct": dict(meta_common, label=f"Change in labor force since {LAUS_BASE_YEAR}",
                                       unit="pct", decimals=1, better="higher",
                                       period_label=f"{LAUS_BASE_YEAR} to {latest_year} annual averages",
                                       note=f"Percent change in the labor force from the {LAUS_BASE_YEAR} annual average. "
                                            f"Each series point is that year's change from {LAUS_BASE_YEAR}. " + where),
    }
    return metrics, per, extras, latest_year, latest_month


# ---------------------------------------------------------------- QCEW

def qcew_file(year, area):
    fips = "39000" if area == "ohio" else area
    url = f"https://data.bls.gov/cew/data/api/{year}/a/area/{fips}.csv"
    return cached(RAW / "bls_qcew" / str(year) / f"{fips}.csv", url, tries=3).decode("utf-8-sig")


def qcew_years():
    y = dt.date.today().year
    while y > QCEW_START:
        try:
            qcew_file(y, "ohio")
            return list(range(QCEW_START, y + 1))
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            y -= 1
    die("no QCEW annual file found")


def titles():
    txt = cached(RAW / "bls_qcew" / "industry_titles.csv",
                 "https://data.bls.gov/cew/doc/titles/industry/industry_titles.csv").decode("utf-8-sig", "replace")
    out = {}
    for r in csv.DictReader(io.StringIO(txt)):
        t = r["industry_title"].strip()
        t = re.sub(r"^(NAICS\s+)?\S+\s+", "", t)      # drop leading "NAICS 722 " or "1011 "
        out[r["industry_code"].strip()] = t
    return out


def lvl(area, county_code):
    """County agglvl codes are 7x; the statewide file uses 5x. Same second digit."""
    return str(county_code - 20) if area == "ohio" else str(county_code)


def parse(area, txt, year):
    """Return dict of (own_code, industry_code, agglvl) -> (jobs or None, wage or None)."""
    out = {}
    fips = "39000" if area == "ohio" else area
    for r in csv.DictReader(io.StringIO(txt)):
        if r["area_fips"] != fips or r["qtr"] != "A" or r["size_code"] != "0" or r["year"] != str(year):
            die(f"unexpected row in {year} {fips}: {r['area_fips']} {r['qtr']} {r['size_code']} {r['year']}")
        k = (r["own_code"], r["industry_code"], r["agglvl_code"])
        if k in out:
            die(f"duplicate key {year} {fips} {k}")
        hidden = r["disclosure_code"].strip() == "N"
        out[k] = (None if hidden else float(r["annual_avg_emplvl"]),
                  None if hidden else float(r["annual_avg_wkly_wage"]))
    return out


def qcew():
    years = qcew_years()
    first, last = years[0], years[-1]
    print(f"QCEW: annual {first}-{last}")
    tasks = [(y, a) for y in years for a in AREAS]
    with ThreadPoolExecutor(8) as ex:
        texts = list(ex.map(lambda t: qcew_file(*t), tasks))
    data = {(a, y): parse(a, txt, y) for (y, a), txt in zip(tasks, texts)}
    T = titles()

    def private_total(a, y):
        return data[(a, y)].get(("5", "10", lvl(a, 71)), (None, None))[0]

    def cells(a, y, level):
        """Private cells at an agglvl: list of (code, jobs or None, wage or None)."""
        L = lvl(a, level)
        return [(i, j, w) for (o, i, g), (j, w) in data[(a, y)].items() if o == "5" and g == L]

    per = {a: {} for a in AREAS}
    extras = {a: {} for a in AREAS}
    supp_stats = {}

    for a in AREAS:
        s_priv, s_wage, s_mfg, s_hc, s_top, s_hhi = [], [], [], [], [], []
        flags = {}
        for y in years:
            ys = str(y)
            pt = private_total(a, y)
            s_priv.append([ys, pt])
            w = data[(a, y)].get(("0", "10", lvl(a, 70)), (None, None))[1]
            s_wage.append([ys, w])
            sectors = {i: (j, wg) for i, j, wg in cells(a, y, 74)}
            for code, s in (("31-33", s_mfg), ("62", s_hc)):
                j = sectors.get(code, (0.0, None))[0] if code in sectors else 0.0
                # a sector with no row has no establishments: zero jobs is a real zero
                s.append([ys, None if (j is None or not pt) else j / pt * 100])
            # 3-digit concentration
            three = cells(a, y, 75)
            known = [(i, j) for i, j, _ in three if j is not None]
            supp = (pt - sum(j for _, j in known)) / pt * 100 if pt else None
            top = max(known, key=lambda x: x[1]) if known else None
            s_top.append([ys, top[1] / pt * 100 if top and pt else None])
            supp_stats[(a, y, "3digit")] = supp
            # HHI over private NAICS supersectors (level 73), disclosed cells only. Supersectors are
            # withheld far less often than 2-digit sectors (see the printed summary below).
            supp_stats[(a, y, "sector")] = (
                (pt - sum(j for j, _ in sectors.values() if j is not None)) / pt * 100 if pt else None)
            known2 = [j for _, j, _ in cells(a, y, 73) if j is not None]
            supp2 = (pt - sum(known2)) / pt * 100 if pt else None
            supp_stats[(a, y, "supersector")] = supp2
            s_hhi.append([ys, sum((j / pt * 100) ** 2 for j in known2) if pt else None])
            if y == last:
                flags["top"] = supp
                flags["hhi"] = supp2
                flags["mfg"] = sectors.get("31-33", (0.0,))[0] is None
                flags["hc"] = sectors.get("62", (0.0,))[0] is None

        def m(series, flag=None):
            d = dict(series)
            v = d[str(last)]
            return {"latest": v, "period": str(last), "series": [p for p in series if p[1] is not None],
                    "moe": None, "flag": flag if flag else (None if v is not None else "suppressed")}

        per[a]["private_jobs"] = m(s_priv)
        per[a]["avg_weekly_wage"] = m(s_wage)
        per[a]["manufacturing_share"] = m(s_mfg, "suppressed" if flags["mfg"] else None)
        per[a]["health_care_share"] = m(s_hc, "suppressed" if flags["hc"] else None)
        per[a]["top_industry_share"] = m(s_top, f"{flags['top']:.0f}% of private jobs in suppressed industries"
                                         if flags["top"] is not None and flags["top"] > SUPPRESS_FLAG_PCT else None)
        per[a]["concentration_hhi"] = m(s_hhi, f"{flags['hhi']:.0f}% of private jobs in suppressed supersectors"
                                        if flags["hhi"] is not None and flags["hhi"] > SUPPRESS_FLAG_PCT else None)

        # extras for the latest year
        pt = private_total(a, last)
        first_sectors = {i: j for i, j, _ in cells(a, first, 74)}
        mix = []
        for i, j, wg in cells(a, last, 74):
            mix.append({"code": i, "title": T.get(i, i), "jobs": j, "share": j / pt * 100 if j is not None else None,
                        "wage": wg, "jobs_first": first_sectors[i] if i in first_sectors else 0.0,
                        "suppressed": j is None})
        mix.sort(key=lambda r: (r["jobs"] is None, -(r["jobs"] or 0), r["code"]))
        extras[a]["industry_mix"] = {"year": str(last), "first_year": str(first), "private_jobs": pt, "sectors": mix}
        three = sorted([(i, j) for i, j, _ in cells(a, last, 75) if j is not None], key=lambda x: (-x[1], x[0]))
        extras[a]["top3"] = [{"code": i, "title": T.get(i, i), "jobs": j, "share": j / pt * 100} for i, j in three[:3]]
        extras[a]["suppressed_share"] = {"year": str(last),
                                         "naics_3digit_pct": supp_stats[(a, last, "3digit")],
                                         "naics_sector_pct": supp_stats[(a, last, "sector")],
                                         "supersector_pct": supp_stats[(a, last, "supersector")]}

    # location quotients vs Ohio, latest year, disclosed sectors only
    oh = {r["code"]: r["share"] for r in extras["ohio"]["industry_mix"]["sectors"] if r["share"] is not None}
    for a in COUNTIES:
        lq = [{"code": r["code"], "title": r["title"], "jobs": r["jobs"], "share": r["share"],
               "ohio_share": oh[r["code"]], "lq": r["share"] / oh[r["code"]]}
              for r in extras[a]["industry_mix"]["sectors"] if r["share"] is not None and oh.get(r["code"])]
        lq.sort(key=lambda r: -r["lq"])
        extras[a]["location_quotient"] = {"year": str(last), "vs": "Ohio", "sectors": lq}
    extras["ohio"]["location_quotient"] = None

    # suppression summary, used to pick and document the HHI level
    for lev in ("supersector", "sector", "3digit"):
        vals = [supp_stats[(a, last, lev)] for a in COUNTIES]
        print(f"  suppressed share of private jobs at {lev} level, {last}: "
              f"median {sorted(vals)[44]:.1f}%, max {max(vals):.1f}%, counties >20%: {sum(v > 20 for v in vals)}")

    src = "BLS Quarterly Census of Employment and Wages"
    vint = f"annual averages {first}-{last}; pulled {TODAY}"
    where = "Jobs are counted where the job is, not where the worker lives. Covers jobs under state unemployment insurance and, in the all-ownership total, federal civilian jobs."
    base = {"theme": "jobs", "source": src, "vintage": vint, "period_label": f"{last} annual average"}
    metrics = {
        "private_jobs": dict(base, label="Private-sector jobs", unit="count", decimals=0, better="none",
                             note="Average number of private-sector jobs in the county during the year. " + where),
        "avg_weekly_wage": dict(base, label="Average weekly wage", unit="usd", decimals=0, better="higher",
                                note="Average weekly pay per job, all employers including government. "
                                     "Dollars are not adjusted for inflation. " + where),
        "manufacturing_share": dict(base, label="Manufacturing share of private jobs", unit="pct", decimals=1,
                                    better="none",
                                    note="Private manufacturing jobs (NAICS 31-33) as a share of private jobs. "
                                         "Blank where BLS withholds the figure to protect employer privacy."),
        "health_care_share": dict(base, label="Health care share of private jobs", unit="pct", decimals=1,
                                  better="none",
                                  note="Private health care and social assistance jobs (NAICS 62) as a share of "
                                       "private jobs. Blank where BLS withholds the figure."),
        "top_industry_share": dict(base, label="Largest industry's share of private jobs", unit="pct", decimals=1,
                                   better="lower",
                                   note="Share of private jobs in the county's single largest industry "
                                        "(3-digit NAICS) among industries BLS discloses. Withheld industries "
                                        "could be larger; the flag shows when more than 20% of private jobs "
                                        "sit in withheld industries."),
        "concentration_hhi": dict(base, label="Job concentration index", unit="index", decimals=0, better="lower",
                                  note="Herfindahl index of private jobs across the 10 private NAICS supersectors plus BLS's unclassified group, 0 to 10,000; "
                                       "higher means jobs depend on fewer sectors. Computed on disclosed sectors "
                                       "only, so it reads low where sectors are withheld."),
    }
    if per["ohio"]["private_jobs"]["latest"] is None:
        die("Ohio private jobs missing")
    return metrics, per, extras, first, last


def main():
    m1, p1, e1, laus_year, laus_month = laus()
    m2, p2, e2, q_first, q_last = qcew()
    metrics = {}
    for m in (m1, m2):
        for k, v in m.items():
            if k in metrics:
                die(f"duplicate metric {k}")
            metrics[k] = v
    counties, ohio, extras = {}, {}, {}
    for a in AREAS:
        row = {}
        for p in (p1, p2):
            for k, v in p[a].items():
                if k in row:
                    die(f"duplicate metric {k} for {a}")
                periods = [s[0] for s in v["series"]]
                if periods != sorted(periods) or len(periods) != len(set(periods)):
                    die(f"bad series periods {a} {k}")
                row[k] = v
        if a == "ohio":
            ohio = row
        else:
            counties[a] = row
        for e in (e1, e2):
            for name, val in e[a].items():
                extras.setdefault(name, {})
                if a in extras[name]:
                    die(f"duplicate extra {name} {a}")
                extras[name][a] = val
    if sorted(counties) != COUNTIES:
        die("county list mismatch")
    write_json("jobs.json", {"metrics": metrics, "counties": counties, "ohio": ohio, "extras": extras})
    print(f"counties: {len(counties)}; LAUS latest {laus_year} / {laus_month}; QCEW {q_first}-{q_last}")


if __name__ == "__main__":
    main()
