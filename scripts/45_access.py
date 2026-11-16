"""Access and community layer: health care providers, suicide, traffic deaths, libraries, membership
associations and voter turnout for the 88 Ohio counties and Ohio.

Sources
  1. County Health Rankings & Roadmaps (CHR&R), Supplemental Data Release of March 25, 2026
     (analytic_supplement_20260325.csv) for primary care physicians (AHRF/AMA), dentists
     (AHRF/NPPES), mental health providers (CMS NPPES) and suicides (NCHS mortality files).
     CHR&R 2025 trends file for earlier years of physicians and dentists.
  2. NHTSA Fatality Analysis Reporting System (FARS), national CSV files, final years only, by
     county of crash. Census population estimates for the denominator (popest.json for 2020 on,
     the 2010-2020 intercensal estimates before that).
  3. IMLS Public Libraries Survey, administrative entity (AE) and outlet files, FY 2019-FY 2024.
  4. Census County Business Patterns (CBP), the ten NAICS codes CHR&R counts as membership
     associations, 2019-2023.
  5. MIT Election Data + Science Lab (MEDSL) 2024 official precinct returns for Ohio (compiled from
     the Ohio Secretary of State) and statewide totals; ACS 2020-2024 5-year citizen voting-age
     population (table B29001).

Method notes are in docs/datasets/access.md.
Writes data/processed/access.json. Run: .venv/bin/python scripts/45_access.py
"""
import csv
import datetime as dt
import io
import json
import re
import zipfile

from common import PROC, RAW, STATE, cached, census, write_json

TODAY = dt.date.today().isoformat()
COUNTIES = [f"39{n:03d}" for n in range(1, 176, 2)]
assert len(COUNTIES) == 88

CHR = "https://www.countyhealthrankings.org/sites/default/files/media/document/"
CHR_SUPP = ("analytic_supplement_20260325.csv", CHR + "analytic_supplement_20260325%5B1%5D.csv")
CHR_TRENDS = ("chr_trends_csv_2025.csv", CHR + "chr_trends_csv_2025.csv")
CHR_2025 = ("analytic_data2025_v3.csv", CHR + "analytic_data2025_v3.csv")
FARS_URL = "https://static.nhtsa.gov/nhtsa/downloads/FARS/{y}/National/FARS{y}NationalCSV.zip"
FARS_FINAL = list(range(2015, 2024))     # 2023 is the latest final file (2024 is an annual report file)
WINDOW = 5
MIN_DEATHS = 20                          # NCHS: rates on fewer than 20 deaths are unreliable
PLS = {2024: "2026-06/pls_fy2024_csv.zip", 2023: "2025-08/pls_fy2023_csv.zip",
       2022: "2024-06/pls_fy2022_csv.zip", 2021: "2023-06/pls_fy2021_csv.zip",
       2020: "2022-07/pls_fy2020_csv.zip", 2019: "2021-05/pls_fy2019_csv.zip"}
PLS_URL = "https://www.imls.gov/sites/default/files/"
CBP_YEARS = list(range(2019, 2024))
# CHR&R "Social Associations" numerator (measure page, 2025): these ten NAICS codes
ASSOC_NAICS = {"813410": "civic and social organizations", "713950": "bowling centers",
               "713910": "golf courses and country clubs", "713940": "fitness and recreational sports centers",
               "711211": "sports teams and clubs", "813110": "religious organizations",
               "813940": "political organizations", "813930": "labor unions",
               "813910": "business associations", "813920": "professional organizations"}
MEDSL_PREC = "https://github.com/MEDSL/2024-elections-official/raw/main/individual_states/oh24.zip"
MEDSL_STATE = "https://raw.githubusercontent.com/MEDSL/2024-elections-official/main/2024-president-state.csv"
INTERCENSAL = ("https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/intercensal/county/asrh/"
               "cc-est2020int-agesex-39.csv")


def num(x):
    if x is None:
        return None
    x = str(x).strip().replace(",", "")
    if x in ("", ".", "NA", "nan"):
        return None
    return float(x)


def entry(series, flag=None, moe=None):
    series = sorted(series)
    periods = [p for p, _ in series]
    if len(periods) != len(set(periods)):
        raise SystemExit("duplicate periods")
    if not series:
        return {"latest": None, "period": None, "series": [], "moe": None, "flag": flag or "no data"}
    p, v = series[-1]
    if v is None and not flag:
        flag = "missing"
    return {"latest": v, "period": p, "series": [list(s) for s in series], "moe": moe, "flag": flag}


# ---------------------------------------------------------------- population
def population():
    """July 1 resident population by county and year, 2010-2025. 2020 on: Vintage 2025 (popest.json).
    2010-2019: 2010-2020 intercensal estimates (YEAR code 2 = July 2010 ... 11 = July 2019)."""
    pop = {f: {} for f in COUNTIES + ["ohio"]}
    pe = json.loads((PROC / "popest.json").read_text())
    for f in COUNTIES:
        for y, v in pe["counties"][f]["population_estimate"]["series"]:
            pop[f][int(y)] = v
    for y, v in pe["ohio"]["population_estimate"]["series"]:
        pop["ohio"][int(y)] = v
    raw = cached(RAW / "popest_intercensal" / "cc-est2020int-agesex-39.csv", INTERCENSAL).decode("latin-1")
    oh = {}
    for r in csv.DictReader(io.StringIO(raw)):
        yc = int(r["YEAR"])
        if 2 <= yc <= 11:
            y = yc + 2008
            f = r["STATE"] + r["COUNTY"]
            pop[f][y] = float(r["POPESTIMATE"])
            oh[y] = oh.get(y, 0.0) + float(r["POPESTIMATE"])
    for y, v in oh.items():
        pop["ohio"][y] = v       # the state total is the sum of its counties in the intercensal series
    return pop, pe["metrics"]["population_estimate"]["vintage"]


# ---------------------------------------------------------------- CHR&R
def chr_rows(spec, skip_second_header=False):
    raw = cached(RAW / "chr" / spec[0], spec[1], timeout=600).decode("utf-8-sig", errors="replace")
    lines = raw.splitlines()
    if skip_second_header:
        lines = lines[1:]     # the annual file has a row of long names above the variable names
    return [r for r in csv.DictReader(lines) if r.get("statecode") == STATE]


def chr_trends():
    raw = cached(RAW / "chr" / CHR_TRENDS[0], CHR_TRENDS[1], timeout=600).decode("utf-8-sig", errors="replace")
    out = {}
    for r in csv.DictReader(io.StringIO(raw)):
        if r["statecode"] != STATE or r["measureid"] not in ("4", "88"):
            continue
        f = "ohio" if r["countycode"] == "000" else STATE + r["countycode"]
        n, d = num(r["numerator"]), num(r["denominator"])
        out.setdefault(r["measureid"], {}).setdefault(f, []).append((r["yearspan"], n, d))
    return out


# ---------------------------------------------------------------- FARS
def fars_year(y):
    raw = cached(RAW / "fars" / f"FARS{y}NationalCSV.zip", FARS_URL.format(y=y), timeout=600)
    z = zipfile.ZipFile(io.BytesIO(raw))
    name = [n for n in z.namelist() if n.lower().rsplit("/", 1)[-1] == "accident.csv"][0]
    text = z.read(name).decode("latin-1")
    if text.startswith("\xef\xbb\xbf"):     # some years start with a UTF-8 byte order mark
        text = text[3:]
    by, unknown, total = {}, 0, 0
    for r in csv.DictReader(io.StringIO(text)):
        if r["STATE"] != str(int(STATE)):
            continue
        k, c = int(r["FATALS"]), int(r["COUNTY"])
        total += k
        f = f"{STATE}{c:03d}"
        if f in by or f in COUNTIES:
            by[f] = by.get(f, 0) + k
        else:
            unknown += k
    return by, unknown, total


# ---------------------------------------------------------------- IMLS PLS
def pls_year(fy):
    raw = cached(RAW / "imls_pls" / PLS[fy].rsplit("/", 1)[1], PLS_URL + PLS[fy], timeout=600)
    z = zipfile.ZipFile(io.BytesIO(raw))
    ae_name = [n for n in z.namelist() if re.search(r"_AE_pud\d\di\.csv$", n, re.I)][0]
    out_name = [n for n in z.namelist() if re.search(r"outlet_pud\d\di\.csv$", n, re.I)][0]
    ae = [r for r in csv.DictReader(io.StringIO(z.read(ae_name).decode("latin-1"))) if r["STABR"] == "OH"]
    outlets = [r for r in csv.DictReader(io.StringIO(z.read(out_name).decode("latin-1"))) if r["STABR"] == "OH"]
    return ae, outlets



# ---------------------------------------------------------------- main
def main():
    pop, pop_vintage = population()
    names = {}
    pe_raw = (RAW / "popest" / "co-est2025-alldata.csv").read_text(encoding="latin-1")
    for r in csv.DictReader(io.StringIO(pe_raw)):
        if r["STATE"] == STATE and r["SUMLEV"] == "050":
            names[r["CTYNAME"].upper().replace(" COUNTY", "").strip()] = STATE + r["COUNTY"]
    assert len(names) == 88

    metrics, ohio = {}, {}
    counties = {f: {} for f in COUNTIES}
    extras = {}

    # ---- 1-3: providers (CHR&R supplement + trends)
    supp = {("ohio" if r["countycode"] == "000" else r["fipscode"]): r for r in chr_rows(CHR_SUPP)}
    assert set(COUNTIES) <= set(supp), "CHR supplement is missing Ohio counties"
    trends = chr_trends()
    prov = [("pcp_per100k", "004", "4", "2022", "Primary care doctors per 100,000 people",
             "HRSA Area Health Resources Files (American Medical Association Physician Masterfile), via County Health Rankings & Roadmaps",
             "Practicing non-federal doctors (M.D. and D.O.) under age 75 in general practice, family medicine, "
             "internal medicine and pediatrics, per 100,000 residents. Counted where the doctor practices, so "
             "people may get care in a nearby county."),
            ("dentists_per100k", "088", "88", "2023", "Dentists per 100,000 people",
             "HRSA Area Health Resources Files (CMS National Provider Identifier file), via County Health Rankings & Roadmaps",
             "Dentists with a National Provider Identifier, per 100,000 residents. Some may no longer practice "
             "or take new patients."),
            ("mh_providers_per100k", "062", None, "2025", "Mental health providers per 100,000 people",
             "CMS National Plan and Provider Enumeration System (NPI file), via County Health Rankings & Roadmaps",
             "Psychiatrists, psychologists, licensed clinical social workers, counselors, marriage and family "
             "therapists, addiction counselors and mental health nurse practitioners with an NPI, per 100,000 "
             "residents. Some may no longer practice or take new patients.")]
    extras["provider_counts"] = {}
    for mid, v, tid, yr, label, src, note in prov:
        metrics[mid] = {"label": label, "theme": "health", "unit": "per100k", "decimals": 0, "better": "higher",
                        "source": src, "vintage": f"CHR&R Supplemental Data Release, March 25, 2026; pulled {TODAY}",
                        "period_label": f"{yr} (CHR&R March 2026 update)", "note": note}
        if tid:
            metrics[mid]["vintage"] += "; earlier years from the CHR&R 2025 trends file"
        for f in COUNTIES + ["ohio"]:
            r = supp[f]
            n, d = num(r[f"v{v}_numerator"]), num(r[f"v{v}_denominator"])
            ser = []
            if tid:
                for span, tn, td in trends.get(tid, {}).get(f, []):
                    if span != yr and tn is not None and td:
                        ser.append((span, 1e5 * tn / td))
            flag = None
            if n is None or not d:
                val, flag = None, "suppressed"
            else:
                val = 1e5 * n / d
                if n == 0:
                    flag = "none counted in the county"
            ser.append((yr, val))
            e = entry(ser, flag)
            if f == "ohio":
                ohio[mid] = e
            else:
                counties[f][mid] = e
            extras["provider_counts"].setdefault(f, {})[mid] = {"providers": n, "population": d, "year": yr}

    # ---- 4: suicides (CHR&R supplement, NCHS 2019-2023, age-adjusted)
    metrics["suicide_rate"] = {
        "label": "Suicide deaths per 100,000 people (age-adjusted)", "theme": "health", "unit": "per100k", "decimals": 1, "better": "lower",
        "source": "CDC National Center for Health Statistics mortality files, via County Health Rankings & Roadmaps",
        "vintage": f"CHR&R Supplemental Data Release, March 25, 2026; pulled {TODAY}",
        "period_label": "2019-2023 (five years combined)",
        "note": ("Suicide deaths per 100,000 people, age-adjusted, five years combined, by the county where "
                 "the person lived. Left blank when there were fewer than 20 deaths in the five years.")}
    extras["suicide_deaths"] = {}
    for f in COUNTIES + ["ohio"]:
        r = supp[f]
        rate, n = num(r["v161_rawvalue"]), num(r["v161_numerator"])
        flag = None
        if rate is None:
            flag = "suppressed (fewer than 10 deaths)"
        elif f != "ohio" and n is not None and n < MIN_DEATHS:
            rate, flag = None, "unreliable (fewer than 20 deaths)"
        e = entry([("2019-2023", rate)], flag)
        (ohio if f == "ohio" else counties[f])["suicide_rate"] = e
        extras["suicide_deaths"][f] = {"deaths": n, "crude_rate": num(r["v161_other_data_1"]),
                                       "chr_age_adjusted_rate": num(r["v161_rawvalue"])}

    # ---- 5: traffic deaths (FARS, county of crash, five final years)
    fy = {y: fars_year(y) for y in FARS_FINAL}
    for y in FARS_FINAL:
        print(f"FARS {y}: Ohio deaths {fy[y][2]}, county unknown {fy[y][1]}")
    windows = [(y - WINDOW + 1, y) for y in FARS_FINAL if y - WINDOW + 1 >= FARS_FINAL[0]]
    last = windows[-1]
    metrics["traffic_deaths_per100k"] = {
        "label": "Traffic deaths per 100,000 people", "theme": "safety", "unit": "per100k", "decimals": 1,
        "better": "lower", "source": "NHTSA Fatality Analysis Reporting System (FARS); Census Bureau population estimates",
        "vintage": (f"FARS final files {FARS_FINAL[0]}-{FARS_FINAL[-1]}; population Vintage 2025 (2020 on) and "
                    f"2010-2020 intercensal estimates; pulled {TODAY}"),
        "period_label": f"{last[0]}-{last[1]} (five years combined)",
        "note": ("Deaths in motor vehicle crashes on public roads, counted in the county where the crash "
                 "happened, per 100,000 residents per year, five years combined. Not age-adjusted. Left blank "
                 "when there were fewer than 20 deaths in the five years.")}
    extras["traffic_deaths"] = {}
    for f in COUNTIES + ["ohio"]:
        ser, cnt = [], []
        flag = None
        for a, b in windows:
            yrs = range(a, b + 1)
            deaths = sum((fy[y][2] if f == "ohio" else fy[y][0].get(f, 0)) for y in yrs)
            p = sum(pop[f][y] for y in yrs)
            ok = f == "ohio" or deaths >= MIN_DEATHS
            ser.append((f"{a}-{b}", 1e5 * deaths / p if ok else None))
            cnt.append({"period": f"{a}-{b}", "deaths": deaths, "person_years": p})
        if ser[-1][1] is None:
            flag = "unreliable (fewer than 20 deaths)"
        (ohio if f == "ohio" else counties[f])["traffic_deaths_per100k"] = entry(ser, flag)
        extras["traffic_deaths"][f] = {"windows": cnt,
                                       "by_year": [[str(y), fy[y][2] if f == "ohio" else fy[y][0].get(f, 0)]
                                                   for y in FARS_FINAL]}
    extras["traffic_deaths"]["ohio"]["county_unknown_by_year"] = [[str(y), fy[y][1]] for y in FARS_FINAL]

    # ---- 6: libraries (IMLS PLS)
    lib = {}
    multi = {}
    for year in sorted(PLS):
        ae, outlets = pls_year(year)
        sp = {f: 0.0 for f in COUNTIES}
        vi = {f: 0.0 for f in COUNTIES}
        systems = {f: [] for f in COUNTIES}
        bad = []
        for r in ae:
            f = names.get(r["CNTY"].upper().strip())
            if f is None:
                raise SystemExit(f"FY{year}: unknown county {r['CNTY']!r} for {r['LIBNAME']}")
            e, v = num(r["TOTOPEXP"]), num(r["VISITS"])
            if e is None or v is None or e < 0 or v < 0:
                bad.append(r["LIBNAME"])
                continue
            sp[f] += e
            vi[f] += v
            systems[f].append({"name": r["LIBNAME"].title(), "operating_spending": e, "visits": v,
                               "legal_service_area_pop": num(r["POPU_LSA"]), "geocode": r.get("GEOCODE")})
        if bad:
            print(f"FY{year}: {len(bad)} Ohio systems with no spending or visits value: {bad}")
        # Systems with a central or branch library listed in a county other than the main office's.
        # (IMLS gives each outlet a county name; in Ohio these all match the main office so far.)
        ae_cty = {r["FSCSKEY"]: names[r["CNTY"].upper().strip()] for r in ae}
        m = {}
        for o in outlets:
            if o.get("C_OUT_TY") not in ("CE", "BR") or o["FSCSKEY"] not in ae_cty:
                continue
            of = names.get(o["CNTY"].upper().strip())
            if of is None:
                print(f"FY{year}: outlet {o['LIBNAME']!r} has county {o['CNTY']!r}, not an Ohio county name; skipped")
            elif of != ae_cty[o["FSCSKEY"]]:
                nm = [r["LIBNAME"].title() for r in ae if r["FSCSKEY"] == o["FSCSKEY"]][0]
                m.setdefault(nm, {"assigned_to": ae_cty[o["FSCSKEY"]], "outlets_elsewhere": []})
                m[nm]["outlets_elsewhere"].append({"outlet": o["LIBNAME"].title(), "county": of})
        multi[year] = m
        lib[year] = (sp, vi, systems, sum(sp.values()), sum(vi.values()), len(ae))
        print(f"PLS FY{year}: {len(ae)} Ohio systems, spending ${sum(sp.values()):,.0f}, visits {sum(vi.values()):,.0f}, "
              f"systems with a building in another county: {len(m)}")
    latest_fy = max(PLS)
    lib_note = ("Each library system is counted in the county of its main office and divided by the "
                "county's whole population. Some systems serve school districts that reach into a neighboring "
                "county. The Ohio figure adds up all Ohio systems.")
    metrics["library_spend_per_capita"] = {
        "label": "Public library spending per person", "theme": "people", "unit": "usd", "decimals": 2,
        "better": "higher", "source": "Institute of Museum and Library Services, Public Libraries Survey; Census Bureau population estimates",
        "vintage": f"FY {min(PLS)}-FY {latest_fy} public-use files (imputed); FY {latest_fy} file released 2026; pulled {TODAY}",
        "period_label": f"FY {latest_fy} (calendar year {latest_fy} in Ohio)",
        "note": "Total operating spending by public library systems (staff, materials and other costs; not "
                "building projects), in dollars of that year, per resident. " + lib_note}
    metrics["library_visits_per_capita"] = {
        "label": "Public library visits per person", "theme": "people", "unit": "per_capita", "decimals": 1,
        "better": "higher", "source": "Institute of Museum and Library Services, Public Libraries Survey; Census Bureau population estimates",
        "vintage": metrics["library_spend_per_capita"]["vintage"],
        "period_label": f"FY {latest_fy} (calendar year {latest_fy} in Ohio)",
        "note": "In-person visits to public libraries in a year, per resident. Some libraries count every visit; "
                "others estimate from a typical week. " + lib_note}
    extras["library_systems"] = {}
    for f in COUNTIES + ["ohio"]:
        s_sp, s_vi = [], []
        for year in sorted(lib):
            sp, vi, systems, tsp, tvi, _ = lib[year]
            p = pop[f][year]
            a, b = (tsp, tvi) if f == "ohio" else (sp[f], vi[f])
            has = f == "ohio" or bool(systems[f])
            s_sp.append((str(year), a / p if has else None))
            s_vi.append((str(year), b / p if has else None))
        flag = None if s_sp[-1][1] is not None else "no library system based in this county"
        tgt = ohio if f == "ohio" else counties[f]
        tgt["library_spend_per_capita"] = entry(s_sp, flag)
        tgt["library_visits_per_capita"] = entry(s_vi, flag)
        if f != "ohio":
            extras["library_systems"][f] = lib[latest_fy][2][f]
    extras["library_multi_county"] = {"ohio": {str(y): multi[y] for y in sorted(multi)}}

    # ---- 7: membership associations (CBP)
    assoc = {}
    for y in CBP_YEARS:
        c = {f: {} for f in COUNTIES}
        st = {}
        for code in ASSOC_NAICS:
            for r in census(f"{y}/cbp", {"get": "ESTAB,EMPSZES,LFO", "for": "county:*", "in": f"state:{STATE}",
                                         "NAICS2017": code}, f"cbp_{y}_{code}_county.json"):
                if r["EMPSZES"] == "001" and r["LFO"] == "001":
                    c[STATE + r["county"]][code] = int(r["ESTAB"])
            for r in census(f"{y}/cbp", {"get": "ESTAB,EMPSZES,LFO", "for": f"state:{STATE}", "NAICS2017": code},
                            f"cbp_{y}_{code}_state.json"):
                if r["EMPSZES"] == "001" and r["LFO"] == "001":
                    st[code] = int(r["ESTAB"])
        c["ohio"] = st
        assoc[y] = c
        print(f"CBP {y}: Ohio associations {sum(st.values())}, county sum {sum(sum(c[f].values()) for f in COUNTIES)}")
    metrics["social_associations_per10k"] = {
        "label": "Membership groups per 10,000 people", "theme": "people", "unit": "per10k", "decimals": 1,
        "better": "higher", "source": "Census Bureau County Business Patterns; Census Bureau population estimates (definition from County Health Rankings & Roadmaps)",
        "vintage": f"CBP {CBP_YEARS[0]}-{CBP_YEARS[-1]} (2023 is the latest year released); pulled {TODAY}",
        "period_label": f"{CBP_YEARS[-1]}",
        "note": ("Places of worship, civic and social clubs, unions, business and professional groups, political "
                 "groups, sports clubs, golf and country clubs, fitness centers and bowling alleys with paid staff, "
                 "per 10,000 residents. Census leaves out any industry with fewer than 3 such places in a county, "
                 "so small counties are undercounted a little.")}
    extras["association_counts"] = {}
    for f in COUNTIES + ["ohio"]:
        ser = [(str(y), 1e4 * sum(assoc[y][f].values()) / pop[f][y]) for y in CBP_YEARS]
        (ohio if f == "ohio" else counties[f])["social_associations_per10k"] = entry(ser)
        extras["association_counts"][f] = {str(y): assoc[y][f] for y in CBP_YEARS}

    # ---- 8: voter turnout 2024 (MEDSL precinct returns / ACS CVAP)
    raw = cached(RAW / "medsl" / "oh24.zip", MEDSL_PREC, timeout=600)
    z = zipfile.ZipFile(io.BytesIO(raw))
    votes = {f: 0 for f in COUNTIES}
    with z.open("oh24.csv") as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8")):
            if r["office"] == "US PRESIDENT":
                if r["mode"] != "TOTAL":
                    raise SystemExit("unexpected vote mode in Ohio file")
                votes[r["county_fips"]] += int(r["votes"])
    st_raw = cached(RAW / "medsl" / "2024-president-state.csv", MEDSL_STATE).decode("utf-8")
    st_rows = [r for r in csv.DictReader(io.StringIO(st_raw)) if r["state_po"] == "OH"]
    state_total = int(st_rows[0]["totalvotes"])
    assert all(int(r["totalvotes"]) == state_total for r in st_rows)
    cv = {STATE + r["county"]: (float(r["B29001_001E"]), float(r["B29001_001M"]))
          for r in census("2024/acs/acs5", {"get": "B29001_001E,B29001_001M", "for": "county:*", "in": f"state:{STATE}"},
                          "acs5_2024_B29001_county.json")}
    s = census("2024/acs/acs5", {"get": "B29001_001E,B29001_001M", "for": f"state:{STATE}"}, "acs5_2024_B29001_state.json")[0]
    cv["ohio"] = (float(s["B29001_001E"]), float(s["B29001_001M"]))
    votes["ohio"] = state_total
    print(f"2024 president: Ohio total {state_total:,}; county precinct sum {sum(votes[f] for f in COUNTIES):,} "
          f"(precinct file has no write-in votes)")
    chr25 = {("ohio" if r["countycode"] == "000" else r["fipscode"]): r for r in chr_rows(CHR_2025, skip_second_header=True)}
    metrics["voter_turnout"] = {
        "label": "Voter turnout, 2024 presidential election", "theme": "people", "unit": "pct", "decimals": 1,
        "better": "higher",
        "source": "Ohio Secretary of State official results, as compiled by the MIT Election Data + Science Lab; Census Bureau American Community Survey",
        "vintage": f"MEDSL 2024 precinct returns (Ohio file dated 2026-04-28); ACS 2020-2024 5-year table B29001; pulled {TODAY}",
        "period_label": "November 2024 general election",
        "note": ("Votes cast for president divided by U.S. citizens age 18 and older. Ballots left blank for "
                 "president are not counted. The citizen count is a survey estimate, and it includes some "
                 "people who cannot vote, such as people serving a felony prison term.")}
    extras["turnout_counts"] = {}
    for f in COUNTIES + ["ohio"]:
        v, (c, cm) = votes[f], cv[f]
        t = 100.0 * v / c
        moe = 100.0 * v * cm / (c * c)
        (ohio if f == "ohio" else counties[f])["voter_turnout"] = entry([("2024", t)], moe=moe)
        r = chr25.get(f, {})
        extras["turnout_counts"][f] = {"president_votes_2024": v, "citizens_18_plus": c, "citizens_18_plus_moe": cm,
                                       "chr_2020_turnout_pct": (100 * num(r.get("v177_rawvalue")) if num(r.get("v177_rawvalue")) is not None else None)}

    # ---- checks
    for f in COUNTIES:
        assert set(counties[f]) == set(metrics), f
    for mid in metrics:
        vals = [counties[f][mid]["latest"] for f in COUNTIES if counties[f][mid]["latest"] is not None]
        lo = min(COUNTIES, key=lambda f: counties[f][mid]["latest"] if counties[f][mid]["latest"] is not None else 1e18)
        hi = max(COUNTIES, key=lambda f: counties[f][mid]["latest"] if counties[f][mid]["latest"] is not None else -1)
        print(f"{mid}: Ohio {ohio[mid]['latest']:.2f} ({ohio[mid]['period']}); counties with value {len(vals)}/88; "
              f"min {counties[lo][mid]['latest']:.2f} ({lo}); max {counties[hi][mid]['latest']:.2f} ({hi})")
    write_json("access.json", {"metrics": metrics, "counties": counties, "ohio": ohio, "extras": extras})


if __name__ == "__main__":
    main()
