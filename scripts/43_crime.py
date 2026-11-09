"""Public safety layer: violent and property crime rates by county, with reporting coverage.

Sources
  1. FBI Uniform Crime Reporting (UCR) Program, Return A master files, one per year
     (offenses known to law enforcement, by agency and month). Downloaded from the FBI Crime
     Data Explorer (CDE) "Master Files" page. No key needed: the CDE hands out a short-lived
     signed S3 link for each file.
  2. FBI Crime in the United States (CIUS) estimation tables, Table 4 (state estimates),
     for the Ohio statewide figure.

Method in brief (full write-up in docs/datasets/crime.md)
  - An agency "reported" a month when the FBI file shows a submission for that month
    (a nonzero date of last update, or an actual-offense card marked as submitted).
  - Only agencies that reported all 12 months count toward a county's rate.
  - Agencies covering more than one county: population is split by the FBI's own county
    fields (up to three); offenses are split in the same proportions.
  - An agency "covered by" another agency is skipped: the FBI puts its offenses and its
    population in the covering agency's record.
  - Agencies with no resident population (campus, park, airport, drug task force) count in
    the county the FBI codes them to. State police, statewide state agencies and federal
    agencies are left out of county figures.
  - Rate = offenses of 12-month agencies / population those agencies cover x 100,000.
  - Coverage = population of 12-month agencies / population of all agencies in the county,
    as a percent. Below 80%, the county value is null with a flag.

Writes data/processed/crime.json. Run: .venv/bin/python scripts/43_crime.py
"""
import datetime as dt
import io
import json
import zipfile

from common import RAW, cached, get, write_json

TODAY = dt.date.today().isoformat()
YEARS = list(range(2015, 2026))
COVERAGE_MIN = 80.0
COUNTIES = [f"39{n:03d}" for n in range(1, 176, 2)]
assert len(COUNTIES) == 88
OH_UCR_STATE = "34"   # UCR numeric state code for Ohio
FOLDER = RAW / "fbi_cde"
SIGN = "https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key="

# Return A layout (FBI Return A record description; positions match the public setup file
# by Jacob Kaplan, crime_data/setup_files/ucr_return_a.sps). 0-based slices.
HDR = {
    "ori": (3, 10), "group": (10, 12), "covered_by": (23, 30),
    "pop1": (44, 53), "cty1": (53, 56), "pop2": (59, 68), "cty2": (68, 71),
    "pop3": (74, 83), "cty3": (83, 86), "name": (120, 144),
}
MONTH0, MONTH_LEN = 305, 590           # January block starts at column 306; 590 columns per month
ACTUAL0 = 17 + 28 * 5                  # actual-offense card starts after the unfounded card
FIELDS = {"murder": 0, "rape": 2, "robbery": 5, "assault_total": 10, "assault_simple": 15,
          "burglary": 16, "larceny": 20, "mvt": 21}
NEG = {"}": 0, "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9}
STATE_POLICE_GROUPS = ("8E", "9E")


def fetch(key, dest):
    """Signed links expire; only ask for one when the file is not cached yet."""
    if not dest.exists():
        cached(dest, json.loads(get(SIGN + key))[key], timeout=600)
    return dest.read_bytes()


def val(s):
    """Return A counts are 5-character signed fields; negatives use a trailing overpunch letter."""
    s = s.strip()
    if not s:
        return 0
    if s[-1] in NEG:
        return -int((s[:-1] or "0") + str(NEG[s[-1]]))
    return int(s)


def parse_year(year):
    raw = fetch(f"master_files/reta/reta-{year}.zip", FOLDER / f"reta-{year}.zip")
    z = zipfile.ZipFile(io.BytesIO(raw))
    text = z.read(z.namelist()[0]).decode("latin-1")
    out = {}
    for r in text.splitlines():
        if r[1:3] != OH_UCR_STATE:
            continue
        a = {k: r[i:j] for k, (i, j) in HDR.items()}
        months, off = [], {"violent": 0, "property": 0}
        for m in range(12):
            b = MONTH0 + m * MONTH_LEN
            upd = r[b + 2:b + 8].strip("0 ") != ""
            months.append(upd or r[b + 9] == "5")
            c = {k: val(r[b + ACTUAL0 + 5 * i:b + ACTUAL0 + 5 * i + 5]) for k, i in FIELDS.items()}
            off["violent"] += c["murder"] + c["rape"] + c["robbery"] + c["assault_total"] - c["assault_simple"]
            off["property"] += c["burglary"] + c["larceny"] + c["mvt"]
        pops = []
        for p, cc in (("pop1", "cty1"), ("pop2", "cty2"), ("pop3", "cty3")):
            n, code = int(a[p] or 0), a[cc].strip()
            if code.isdigit() and 1 <= int(code) <= 88:
                pops.append((f"39{2 * int(code) - 1:03d}", n))   # UCR county code n = nth county A-Z
        rec = {"ori": a["ori"], "group": a["group"], "covered_by": a["covered_by"].strip(),
               "name": a["name"].strip(), "months": months, "off": off, "pops": pops}
        if rec["ori"] in out:   # a few duplicate rows: keep the one with more reported months
            if sum(out[rec["ori"]]["months"]) >= sum(months):
                continue
        out[rec["ori"]] = rec
    return out


def excluded(a):
    """State police, statewide state agencies and federal agencies stay out of county figures."""
    if a.get("covered"):
        return "covered by another agency"
    if a["group"] in STATE_POLICE_GROUPS or a["ori"].startswith("OHOHP"):
        return "state police"
    if not a["ori"][2:5].isdigit():
        if sum(n for _, n in a["pops"]) > 0:
            return None         # big-city ORIs such as OHCOP00 (Columbus) have letters too
        return "state or federal agency"
    if not a["pops"]:
        return "no county code"
    return None


def county_year(year):
    ag = parse_year(year)
    # An agency "covered by" another sends no report of its own: its offenses are in the
    # covering agency's report and its population is already in the covering agency's population.
    for a in ag.values():
        if a["covered_by"] and a["covered_by"] in ag:
            a["covered"] = True
    tot = {f: 0.0 for f in COUNTIES}
    cov = {f: 0.0 for f in COUNTIES}
    v = {f: 0.0 for f in COUNTIES}
    p = {f: 0.0 for f in COUNTIES}
    n_ag = {f: [0, 0] for f in COUNTIES}
    skipped = {}
    for a in ag.values():
        why = excluded(a)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        full = all(a["months"])
        agency_pop = sum(n for _, n in a["pops"])
        for i, (f, n) in enumerate(a["pops"]):
            if agency_pop > 0:
                share = n / agency_pop
            else:
                share = 1.0 if i == 0 else 0.0      # zero-population agency: first coded county
            if agency_pop > 0 and n == 0:
                continue
            tot[f] += n
            n_ag[f][1] += 1
            if full:
                cov[f] += n
                v[f] += a["off"]["violent"] * share
                p[f] += a["off"]["property"] * share
                n_ag[f][0] += 1
    res = {}
    for f in COUNTIES:
        res[f] = {"pop_all": tot[f], "pop_covered": cov[f],
                  "coverage": 100.0 * cov[f] / tot[f] if tot[f] else None,
                  "violent": v[f], "property": p[f],
                  "agencies_full": n_ag[f][0], "agencies_all": n_ag[f][1]}
    # Statewide aggregate built the same way (for comparison with the FBI estimate).
    st = {k: sum(res[f][k] for f in COUNTIES) for k in ("pop_all", "pop_covered", "violent", "property")}
    st["coverage"] = 100.0 * st["pop_covered"] / st["pop_all"]
    return res, st, skipped


def ohio_estimates():
    """FBI state estimates, CIUS Table 4. Each edition has two years; the later edition wins."""
    import openpyxl
    out = {}
    for ed in (2022, 2023, 2024, 2025):
        raw = fetch(f"cius/{ed}/cius-estimations-{ed}.zip", FOLDER / "cius" / f"cius-estimations-{ed}.zip")
        z = zipfile.ZipFile(io.BytesIO(raw))
        name = [n for n in z.namelist() if "Table_4" in n and n.endswith(".xlsx")][0]
        ws = openpyxl.load_workbook(io.BytesIO(z.read(name)), data_only=True, read_only=True).active
        rows = list(ws.iter_rows(values_only=True))
        for i, r in enumerate(rows):
            if r[0] and str(r[0]).strip() == "Ohio":
                for rr in rows[i:i + 2]:
                    yr, pop = int(rr[1]), float(rr[2])
                    out[str(yr)] = {"pop": pop, "violent": float(rr[3]), "property": float(rr[13]),
                                    "edition": ed}
    return out


def entry(series, flag=None):
    series = sorted(series)
    periods = [s[0] for s in series]
    if len(periods) != len(set(periods)):
        raise SystemExit("duplicate periods")
    if not series:
        return {"latest": None, "period": None, "series": [], "moe": None, "flag": flag or "no data"}
    pr, v = series[-1]
    return {"latest": v, "period": pr, "series": [list(s) for s in series], "moe": None,
            "flag": flag if (flag or v is not None) else "missing"}


def main():
    data, state, skipped_by_year = {}, {}, {}
    for y in YEARS:
        data[str(y)], state[str(y)], skipped_by_year[str(y)] = county_year(y)
        print(y, "statewide coverage %.1f%%" % state[str(y)]["coverage"],
              "counties below %d%%: %d" % (COVERAGE_MIN, sum(
                  1 for f in COUNTIES if (data[str(y)][f]["coverage"] or 0) < COVERAGE_MIN)))

    est = ohio_estimates()
    latest = str(YEARS[-1])
    note_cov = ("Counts only agencies that reported all 12 months, and divides by the population "
                "those agencies serve, not the full county. Left blank when those agencies cover "
                "less than 80% of the county's people.")
    metrics = {
        "violent_crime_rate": {
            "label": "Violent crime rate", "theme": "safety", "unit": "per100k", "decimals": 0,
            "better": "lower", "source": "FBI Uniform Crime Reporting Program, Return A master files",
            "vintage": f"annual {YEARS[0]}-{YEARS[-1]}; 2025 file dated 2026-05-07; pulled {TODAY}",
            "period_label": f"{latest} calendar year",
            "note": ("Murder, rape, robbery and aggravated assault reported to police, per 100,000 "
                     "people. " + note_cov)},
        "property_crime_rate": {
            "label": "Property crime rate", "theme": "safety", "unit": "per100k", "decimals": 0,
            "better": "lower", "source": "FBI Uniform Crime Reporting Program, Return A master files",
            "vintage": f"annual {YEARS[0]}-{YEARS[-1]}; 2025 file dated 2026-05-07; pulled {TODAY}",
            "period_label": f"{latest} calendar year",
            "note": ("Burglary, theft and motor vehicle theft reported to police, per 100,000 people. "
                     "This is the FBI's standard category closest to petty crime. " + note_cov)},
    }
    counties, extras = {f: {} for f in COUNTIES}, {"coverage": {}, "crime_counts": {}}
    for f in COUNTIES:
        sv, sp, cv, cn = [], [], [], []
        for y in YEARS:
            d = data[str(y)][f]
            ok = d["coverage"] is not None and d["coverage"] >= COVERAGE_MIN and d["pop_covered"] > 0
            sv.append((str(y), 1e5 * d["violent"] / d["pop_covered"] if ok else None))
            sp.append((str(y), 1e5 * d["property"] / d["pop_covered"] if ok else None))
            cv.append([str(y), d["coverage"]])
            cn.append({"year": str(y), "violent": d["violent"], "property": d["property"],
                       "pop_covered": d["pop_covered"], "pop_all": d["pop_all"],
                       "agencies_full_year": d["agencies_full"], "agencies_all": d["agencies_all"]})
        flag = None if sv[-1][1] is not None else "low reporting (<80% of people covered)"
        counties[f]["violent_crime_rate"] = entry(sv, flag)
        counties[f]["property_crime_rate"] = entry(sp, flag)
        extras["coverage"][f] = cv
        extras["crime_counts"][f] = cn
    ohio = {}
    for mid, k in (("violent_crime_rate", "violent"), ("property_crime_rate", "property")):
        ohio[mid] = entry([(y, 1e5 * e[k] / e["pop"]) for y, e in est.items()])
    extras["coverage"]["ohio"] = [[y, state[y]["coverage"]] for y in sorted(state)]
    extras["crime_counts"]["ohio"] = [{"year": y, "violent": state[y]["violent"], "property": state[y]["property"],
                                       "pop_covered": state[y]["pop_covered"], "pop_all": state[y]["pop_all"]}
                                      for y in sorted(state)]
    extras["ohio_reported_agencies"] = {"ohio": {
        "note": "Same method as the counties, all Ohio local agencies with 12 months of reports.",
        "violent_crime_rate": [[y, 1e5 * state[y]["violent"] / state[y]["pop_covered"]] for y in sorted(state)],
        "property_crime_rate": [[y, 1e5 * state[y]["property"] / state[y]["pop_covered"]] for y in sorted(state)]}}
    extras["ohio_fbi_estimate_counts"] = {"ohio": est}
    extras["coverage_threshold_pct"] = {"ohio": COVERAGE_MIN}
    extras["agencies_left_out"] = {"ohio": skipped_by_year}
    write_json("crime.json", {"metrics": metrics, "counties": counties, "ohio": ohio, "extras": extras})


if __name__ == "__main__":
    main()
