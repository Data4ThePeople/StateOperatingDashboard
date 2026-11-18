"""Public money layer: what public programs spend in each county, per resident, per household or per pupil.
Theme "money". Spending is shown next to conditions, not as a cause of them.

Sources
  1. BEA Regional Accounts, table CAINC35 "Personal current transfer receipts" (county), bulk zip
     https://apps.bea.gov/regional/zip/CAINC35.zip. BEA discontinued CAINC35 on Nov. 1, 2024, so the zip
     is the last release (Nov. 16, 2023): 1969-2022, revised 2013-2021. We use 2010-2022.
  2. HUD Picture of Subsidized Households, county and state extracts 2015-2025 and the 2025 census tract
     extract (2020 tract GEOIDs), https://www.huduser.gov/portal/datasets/assthsg.html.
  3. Census Bureau Annual Survey of School System Finances, per-district files and summary tables,
     fiscal years 2022-2024, https://www.census.gov/programs-surveys/school-finances/data/tables.html.
Denominators
  - Population: Census July 1 estimates. 2020 on from data/processed/popest.json (vintage 2025);
    2010-2019 from the Census 2010-2020 intercensal county file (co-est2020int-pop-39.xlsx).
  - Households (HUD measure): ACS 5-year table B11001. Tract population for tract spending: ACS 5-year
    B01003 (the Census Bureau does not publish July 1 estimates for tracts).

Rules kept: each program is its own measure, never added to another; tax credits (EITC) are never added to
benefits; the school measures stay separate from the benefit measures. Ohio values are the publisher's own
state figure (BEA state row, HUD state extract), divided by Census state population or ACS state households
where a denominator is needed. School finance is the exception: Ohio is the sum of all traditional districts,
built the same way as the counties, with the published all-systems figure in extras.

Writes data/processed/public_money.json. Run: .venv/bin/python scripts/46_public_money.py
"""
import csv
import datetime as dt
import glob
import io
import json
import re
import time
import zipfile

import openpyxl

from common import ABBR, CFG, COUNTIES, NRAW, PROC, RAW, SK, SNAME, ST_ID, STATE, census, get, write_json

TODAY = dt.date.today().isoformat()
THEME = "money"
NATIONAL = ("bea_cainc35", "hud_picture", "census_school_finance")   # whole-nation files, shared by every state
NOTE_TAIL = " It describes spending, not results. Dollars are not adjusted for inflation."


def fetch(folder, name, url, magic):
    """Download once into data/raw/<folder>/; refuse a reply that is not the expected file type
    (HUD sometimes answers 202 with an empty body)."""
    path = (NRAW if folder in NATIONAL else RAW) / folder / name
    if not path.exists():
        body = get(url)
        if not body.startswith(magic):
            raise SystemExit(f"{url}: got {len(body)} bytes that are not a {magic!r} file; try again later")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        (path.parent / "pulled.txt").write_text(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n")
        time.sleep(1)
    return path


def check_series(series, where):
    ps = [p for p, _ in series]
    if len(ps) != len(set(ps)):
        raise SystemExit(f"duplicate periods in {where}")
    if ps != sorted(ps):
        raise SystemExit(f"series out of order in {where}")


def entry(series, flags=None):
    """series: [(period, value or None)]. flags: {period: reason} for null values."""
    check_series(series, "entry")
    flags = flags or {}
    p, v = series[-1]
    flag = None if v is not None else flags.get(p, "missing")
    return {"latest": v, "period": p, "series": [[a, b] for a, b in series], "moe": None, "flag": flag}


# --------------------------------------------------------------------------- population
geo = json.loads((PROC / "geo.json").read_text())["counties"]
NAME2FIPS = {v["name"].strip().lower(): f for f, v in geo.items()}
assert sorted(NAME2FIPS.values()) == COUNTIES

pe = json.loads((PROC / "popest.json").read_text())
POP = {f: {int(y): v for y, v in pe["counties"][f]["population_estimate"]["series"]} for f in COUNTIES}
POP[SK] = {int(y): v for y, v in pe[SK]["population_estimate"]["series"]}
POPEST_VINTAGE = pe["metrics"]["population_estimate"]["vintage"]

INT_URL = ("https://www2.census.gov/programs-surveys/popest/tables/2010-2020/intercensal/county/"
           f"co-est2020int-pop-{STATE}.xlsx")
wb = openpyxl.load_workbook(fetch("popest_int", f"co-est2020int-pop-{STATE}.xlsx", INT_URL, b"PK"), read_only=True)
rows = list(wb[wb.sheetnames[0]].iter_rows(values_only=True))
hdr_i = [i for i, r in enumerate(rows) if r[2] == 2010][0]
years_cols = {int(y): j for j, y in enumerate(rows[hdr_i]) if isinstance(y, int) and 2010 <= y <= 2019}
assert sorted(years_cols) == list(range(2010, 2020)), years_cols
for r in rows[hdr_i + 1:]:
    if not r[0]:
        continue
    name = str(r[0]).strip()
    if name == SNAME:
        key = SK
    else:
        m = re.fullmatch(r"\.(.+) County, " + SNAME, name)
        if not m:
            continue
        key = NAME2FIPS[m.group(1).strip().lower()]
    for y, j in years_cols.items():
        POP[key][y] = float(r[j])
for k in COUNTIES + [SK]:
    missing = [y for y in range(2010, 2026) if y not in POP[k]]
    if missing:
        raise SystemExit(f"no population for {k} in {missing}")


def pop(geo_key, year):
    return POP[geo_key][year]


# =========================================================================== 1. BEA CAINC35
BEA_URL = "https://apps.bea.gov/regional/zip/CAINC35.zip"
bz = zipfile.ZipFile(fetch("bea_cainc35", "CAINC35.zip", BEA_URL, b"PK"))
oh_name = [n for n in bz.namelist() if re.fullmatch(rf"CAINC35_{ABBR}_1969_\d{{4}}\.csv", n)]
if len(oh_name) != 1:
    raise SystemExit(f"{SNAME} file not found in CAINC35.zip: {bz.namelist()[:5]}")
oh_name = oh_name[0]
BEA_LAST = int(oh_name[-8:-4])
BEA_YEARS = list(range(2010, BEA_LAST + 1))
text = bz.read(oh_name).decode("latin-1")
bea_rows = list(csv.reader(io.StringIO(text)))
bea_head = bea_rows[0]
bea_updated = [r[0] for r in bea_rows if r and r[0].startswith("Last updated")]
BEA_UPDATED = bea_updated[0] if bea_updated else "unknown"

# metric id -> (line code, words that must appear in BEA's line description)
BEA_LINES = {
    "bea_medicaid_per_resident": ("2220", "public assistance medical care"),
    "bea_snap_per_resident": ("2330", "supplemental nutrition assistance program"),
    "bea_ssi_per_resident": ("2310", "supplemental security income"),
    "bea_eitc_per_resident": ("2320", "earned income tax credit"),
    "bea_unemployment_per_resident": ("2400", "unemployment insurance compensation"),
    "bea_veterans_per_resident": ("2500", "veterans' benefits"),
}
bea = {}   # (geofips, line) -> {year: raw string}
for r in bea_rows[1:]:
    if len(r) < len(bea_head):
        continue
    d = dict(zip(bea_head, r))
    g = d["GeoFIPS"].strip().strip('"').strip()
    line = d["LineCode"].strip()
    for mid, (code, words) in BEA_LINES.items():
        if line == code:
            if words not in d["Description"].strip().lower():
                raise SystemExit(f"BEA line {code} is {d['Description']!r}, expected {words!r}")
            bea[(g, code)] = {y: d[str(y)].strip() for y in BEA_YEARS}


def bea_num(s):
    try:
        return float(s) * 1000.0      # thousands of dollars -> dollars
    except ValueError:
        return None


bea_check = {}
for mid, (code, _) in BEA_LINES.items():
    for g in COUNTIES + [STATE + "000"]:
        if (g, code) not in bea:
            raise SystemExit(f"BEA: no line {code} for {g}")
    gaps = {}
    for y in BEA_YEARS:
        vals = [bea_num(bea[(g, code)][y]) for g in COUNTIES]
        st = bea_num(bea[(STATE + "000", code)][y])
        if None in vals or st is None:
            gaps[str(y)] = "a county or state value is not a number"
            continue
        gaps[str(y)] = sum(vals) - st
    bea_check[code] = gaps

counties = {f: {} for f in COUNTIES}
ohio = {}
extras = {}

for mid, (code, _) in BEA_LINES.items():
    extras[mid.replace("_per_resident", "_dollars")] = {}
    for g in COUNTIES + [SK]:
        src = STATE + "000" if g == SK else g
        ser, flags, dollars = [], {}, []
        for y in BEA_YEARS:
            raw = bea[(src, code)][y]
            v = bea_num(raw)
            p = str(y)
            if v is None:
                ser.append((p, None))
                flags[p] = f"BEA code {raw}"
            else:
                ser.append((p, v / pop(g, y)))
            dollars.append([p, v])
        e = entry(ser, flags)
        (ohio if g == SK else counties[g])[mid] = e
        extras[mid.replace("_per_resident", "_dollars")][g] = dollars

# =========================================================================== 2. HUD Picture
HUD = "https://www.huduser.gov/portal/datasets/pictures/files/"
HUD_YEARS = list(range(2015, 2026))
HUD_CODES = {-1: "missing (HUD code -1)", -4: "suppressed (HUD code -4: fewer than 11 households reported)",
             -5: "non-reporting (HUD code -5: under 50% of households reported)"}


def hud_file(kind, y):
    name = f"{kind}_{y}.xlsx" if y <= 2021 else f"{kind}_{y}_2020census.xlsx"
    return fetch("hud_picture", name, HUD + name, b"PK"), name


def hud_rows(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    it = wb[wb.sheetnames[0]].iter_rows(values_only=True)
    h = [str(x).strip().lower() if x is not None else "" for x in next(it)]
    for r in it:
        yield dict(zip(h, r))


def hud_num(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def hud_summary(d):
    """Occupied units (households) and annual HUD spending from one 'Summary of All HUD Programs' row.
    Returns (occupied, annual_dollars, units, exact_occupied, flag)."""
    units = hud_num(d.get("total_units"))
    occ = hud_num(d.get("total_occupied"))
    pct = hud_num(d.get("pct_occupied"))
    spend = hud_num(d.get("spending_per_month"))
    exact = occ is not None
    for v in (units, occ if exact else pct, spend):
        if v is not None and v < 0:
            return None, None, units, exact, HUD_CODES.get(int(v), f"HUD code {int(v)}")
    if not exact:
        if units is None or pct is None:
            return None, None, units, exact, "missing"
        occ = units * pct / 100.0
    annual = occ * 12.0 * spend if spend is not None else None
    return occ, annual, units, exact, None


hud_cty = {f: {} for f in COUNTIES}   # fips -> {year: (occ, annual, units, exact, flag)}
hud_oh = {}
hud_unplaced = {}
for y in HUD_YEARS:
    cpath, cname = hud_file("COUNTY", y)
    seen = set()
    for d in hud_rows(cpath):
        code = str(d.get("code") or "").strip()
        if not code.startswith(STATE) or str(d.get("program")).strip() != "1":
            continue
        if code == STATE + "XXX":
            hud_unplaced[str(y)] = {"units": hud_num(d.get("total_units")), "pct_occupied": hud_num(d.get("pct_occupied")),
                                    "occupied": hud_num(d.get("total_occupied"))}
            continue
        if code not in hud_cty:
            raise SystemExit(f"{cname}: unknown county code {code!r}")
        if code in seen:
            raise SystemExit(f"{cname}: duplicate summary row for {code}")
        seen.add(code)
        hud_cty[code][y] = hud_summary(d)
    if seen != set(COUNTIES):
        raise SystemExit(f"{cname}: missing counties {sorted(set(COUNTIES) - seen)}")
    spath, sname = hud_file("STATE", y)
    got = [d for d in hud_rows(spath) if str(d.get("code") or "").strip() == STATE and str(d.get("program")).strip() == "1"]
    if len(got) != 1:
        raise SystemExit(f"{sname}: expected one {SNAME} summary row, found {len(got)}")
    hud_oh[y] = hud_summary(got[0])

# ACS households (and state) for each HUD year: 5-year period ending in that year, or the latest one.
ACS_LAST = 2024


def acs_year(y):
    return min(y, ACS_LAST)


hh = {}
for ay in sorted({acs_year(y) for y in HUD_YEARS}):
    for geo_for, extra in (("county:*", {"in": f"state:{STATE}"}), (f"state:{STATE}", {})):
        params = {"get": "B11001_001E", "for": geo_for}
        params.update(extra)
        level = geo_for.split(":")[0]
        for r in census(f"{ay}/acs/acs5", params, f"public_money_acs5_{ay}_B11001_{level}.json"):
            key = SK if level == "state" else r["state"] + r["county"]
            hh[(key, ay)] = float(r["B11001_001E"])

for g in COUNTIES + [SK]:
    src = hud_oh if g == SK else hud_cty[g]
    s_hh, s_sp, f_hh, f_sp = [], [], {}, {}
    for y in HUD_YEARS:
        occ, annual, units, exact, flag = src[y]
        p = str(y)
        if occ is None:
            s_hh.append((p, None))
            f_hh[p] = flag
        else:
            s_hh.append((p, occ / hh[(g, acs_year(y))] * 1000.0))
        if annual is None:
            s_sp.append((p, None))
            f_sp[p] = flag
        else:
            s_sp.append((p, annual / pop(g, y)))
    target = ohio if g == SK else counties[g]
    target["hud_households_per_1000"] = entry(s_hh, f_hh)
    target["hud_spending_per_resident"] = entry(s_sp, f_sp)

extras["hud_counts"] = {}
for g in COUNTIES + [SK]:
    src = hud_oh if g == SK else hud_cty[g]
    extras["hud_counts"][g] = {str(y): {"units": src[y][2], "occupied": src[y][0], "occupied_is_published": src[y][3],
                                        "annual_spending_usd": src[y][1]} for y in HUD_YEARS}
extras["hud_units_not_placed_in_a_county"] = {SK: hud_unplaced}

# ---- tracts, latest year only
TRACT_YEAR = 2025
tpath, tname = fetch("hud_picture", f"TRACT_MO_WY_{TRACT_YEAR}_2020census.xlsx",
                     HUD + f"TRACT_MO_WY_{TRACT_YEAR}_2020census.xlsx", b"PK"), f"TRACT_MO_WY_{TRACT_YEAR}_2020census.xlsx"
acs_tr = {}
for r in census(f"{ACS_LAST}/acs/acs5", {"get": "B11001_001E,B01003_001E", "for": "tract:*", "in": f"state:{STATE}"},
                f"public_money_acs5_{ACS_LAST}_B11001_B01003_tract.json"):
    acs_tr[r["state"] + r["county"] + r["tract"]] = (float(r["B11001_001E"]), float(r["B01003_001E"]))

tracts = {}
tract_skipped = []
tract_flags = {}
for d in hud_rows(tpath):
    code = str(d.get("code") or "").strip()
    if not code.startswith(STATE) or str(d.get("program")).strip() != "1":
        continue
    if "XXX" in code or code.endswith("999999"):
        tract_skipped.append({"code": code, "units": hud_num(d.get("total_units")),
                              "occupied": hud_num(d.get("total_occupied"))})
        continue
    if not re.fullmatch(STATE + r"\d{9}", code) or code[:5] not in counties:
        raise SystemExit(f"{tname}: odd tract code {code!r}")
    if code in tracts:
        raise SystemExit(f"{tname}: duplicate tract {code}")
    occ, annual, units, exact, flag = hud_summary(d)
    hhs, people = acs_tr.get(code, (None, None))
    m_hh = {"latest": None, "period": str(TRACT_YEAR), "flag": flag}
    m_sp = {"latest": None, "period": str(TRACT_YEAR), "flag": flag}
    if flag is None:
        if not hhs:
            m_hh["flag"] = "no households in ACS"
        else:
            m_hh["latest"] = occ / hhs * 1000.0
        if annual is None:
            m_sp["flag"] = "missing"
        elif not people:
            m_sp["flag"] = "no residents in ACS"
        else:
            m_sp["latest"] = annual / people
    for m in (m_hh, m_sp):
        tract_flags[m["flag"]] = tract_flags.get(m["flag"], 0) + 1
    tracts[code] = {"hud_households_per_1000": m_hh, "hud_spending_per_resident": m_sp}
not_in_hud = sorted(set(acs_tr) - set(tracts))
not_in_acs = sorted(set(tracts) - set(acs_tr))

# =========================================================================== 3. School finances
SF = "https://www2.census.gov/programs-surveys/school-finances/tables/{y}/secondary-education-finance/{f}"
SF_YEARS = [2022, 2023, 2024]
URBAN = "https://educationdata.urban.org/api/v1"


def urban(path, name):
    out, url, page = [], f"{URBAN}/{path}", 0
    while url:
        page += 1
        raw = json.loads(fetch("urban_ccd", f"{name}_p{page}.json", url, b"{").read_bytes())
        out += raw["results"]
        url = raw.get("next")
    return out


# NCES district ID -> Ohio IRN (CCD directory), IRN -> county (ODEW District Details, as in 40_reading.py)
nces2irn = {}
for y in (2022, 2023, 2024):
    for r in urban(f"school-districts/ccd/directory/{y}/?fips={int(STATE)}", f"lea_dir_{y}"):
        if r.get("state_leaid"):
            nces2irn[r["leaid"]] = r["state_leaid"].replace(f"{ABBR}-", "").zfill(6)
irn2cty = {}
dd_path = RAW / "odew" / "2026_District_Details.xlsx"
if dd_path.exists():
    wb = openpyxl.load_workbook(dd_path, read_only=True)
    ws = wb["District_Details"]
    ws.reset_dimensions()
    it = ws.iter_rows(values_only=True)
    h = list(next(it))
    for r in it:
        d = dict(zip(h, r))
        c = NAME2FIPS.get(str(d["County"]).strip().lower())
        if c:
            irn2cty[str(d["District IRN"]).strip().zfill(6)] = c
elif ST_ID == "oh":
    print("ODEW District Details not found; districts are placed by the Census county code only")


def sf_num(v):
    if v is None or v == "":
        return 0.0
    return float(v)


sf_assign = {}      # (year, PID6) -> how the county was chosen
sf_diff = {}        # NCESID -> (name, census county, ODEW county)
sf_by_cty = {}      # year -> fips -> sums
sf_ohio = {}        # year -> published state figures
sf_ohio_regular = {}
sf_districts = {}   # year -> fips -> [names]
for y in SF_YEARS:
    yy = y % 100
    path = fetch("census_school_finance", f"elsec{yy}.xlsx", SF.format(y=y, f=f"elsec{yy}.xlsx"), b"PK")
    wb = openpyxl.load_workbook(path, read_only=True)
    it = wb[f"elsec{yy}"].iter_rows(values_only=True)
    h = [str(x).strip() for x in next(it)]
    rows = [dict(zip(h, r)) for r in it]
    oh_rows = [d for d in rows if str(d["FIPST"]).zfill(2) == STATE]
    lo_n, hi_n = CFG["sf_rows"]
    if not lo_n < len(oh_rows) < hi_n:
        raise SystemExit(f"elsec{yy}: {len(oh_rows)} {SNAME} rows")
    sums = {f: {"spend": 0.0, "enroll": 0.0, "rev": 0.0, "fed": 0.0, "state": 0.0, "local": 0.0, "n": 0} for f in COUNTIES}
    all_units = {"spend": 0.0, "enroll": 0.0, "rev": 0.0, "fed": 0.0, "state": 0.0, "local": 0.0}
    names = {f: [] for f in COUNTIES}
    for d in oh_rows:
        spend, enroll = sf_num(d["TCURELSC"]), sf_num(d["V33"])
        rev, fed, st, loc, inter = (sf_num(d[k]) for k in ("TOTALREV", "TFEDREV", "TSTREV", "TLOCREV", "D11"))
        if abs(fed + st + loc - rev) > 2:
            raise SystemExit(f"elsec{yy} {d['NAME']}: revenue parts do not add to total")
        for k, v in (("spend", spend), ("enroll", enroll), ("rev", rev - inter), ("fed", fed), ("state", st), ("local", loc - inter)):
            all_units[k] += v
        if str(d["SCHLEV"]).zfill(2) != "03":
            continue
        census_cty = str(d["CONUM"]).zfill(5)
        nces = str(d["NCESID"]).zfill(7)
        irn = nces2irn.get(nces)
        if irn in irn2cty:
            f, how = irn2cty[irn], "ODEW"
            if f != census_cty:
                sf_diff[nces] = (d["NAME"], census_cty, f)
        else:
            f, how = census_cty, "Census CONUM"
        sf_assign[(y, d["PID6"])] = how
        if f not in sums:
            raise SystemExit(f"elsec{yy}: county {f} for {d['NAME']}")
        if enroll <= 0:
            if spend > 0:
                print(f"FY{y}: {d['NAME']} has spending but no enrollment; left out of per pupil")
        else:
            sums[f]["spend"] += spend
            sums[f]["enroll"] += enroll
        sums[f]["rev"] += rev - inter
        sums[f]["fed"] += fed
        sums[f]["state"] += st
        sums[f]["local"] += loc - inter
        sums[f]["n"] += 1
        names[f].append(d["NAME"])
    sf_by_cty[y] = sums
    sf_districts[y] = names
    sf_ohio_regular[y] = {k: sum(s[k] for s in sums.values()) for k in ("spend", "enroll", "rev", "fed", "state", "local")}

    # Published state figures: Table 1 (revenue by source, thousands) and Table 8 (per pupil current spending)
    spath = fetch("census_school_finance", f"elsec{yy}_sumtables.xlsx", SF.format(y=y, f=f"elsec{yy}_sumtables.xlsx"), b"PK")
    wb = openpyxl.load_workbook(spath, read_only=True)

    def ohio_row(sheet):
        for r in wb[sheet].iter_rows(values_only=True):
            if r and str(r[0] or "").startswith(SNAME + "."):
                return [x for x in r[1:] if isinstance(x, (int, float))]
        raise SystemExit(f"elsec{yy}_sumtables sheet {sheet}: no {SNAME} row")

    t1 = ohio_row("1")
    t8 = ohio_row("8")
    tot, fed, st, loc = t1[:4]
    if abs(fed + st + loc - tot) > 3:
        raise SystemExit(f"FY{y} Table 1 {SNAME}: parts {fed}+{st}+{loc} != {tot}")
    sf_ohio[y] = {"per_pupil": t8[0], "fed": fed / tot * 100, "state": st / tot * 100, "local": loc / tot * 100,
                  "total_rev_thousands": tot}
    # cross-checks against the per-district file (all units)
    if abs(all_units["fed"] - fed) > 2 or abs(all_units["rev"] - tot) > 5:
        print(f"FY{y}: district file sums differ from Table 1 (fed {all_units['fed']} vs {fed}, rev {all_units['rev']} vs {tot})")
    pp_units = all_units["spend"] / all_units["enroll"] * 1000
    if abs(pp_units / t8[0] - 1) > 0.02:
        raise SystemExit(f"FY{y}: per pupil from district file {pp_units:.0f} vs Table 8 {t8[0]:.0f}")


def sy(y):
    return f"{y - 1}-{y}"


for g in COUNTIES + [SK]:
    ser = {"pp": [], "fed": [], "state": [], "local": []}
    for y in SF_YEARS:
        p = sy(y)
        if g == SK:
            # Ohio is built the same way as the counties: traditional districts only. The Census Bureau's published
            # all-systems figures (Tables 1 and 8, which add joint vocational districts and service centers) are kept
            # in extras and named in the note.
            r = sf_ohio_regular[y]
            ser["pp"].append((p, r["spend"] / r["enroll"] * 1000))
            for k in ("fed", "state", "local"):
                ser[k].append((p, r[k] / r["rev"] * 100))
            tot = {k: sum(sf_by_cty[y][c][k] for c in COUNTIES) for k in ("spend", "enroll", "rev")}
            assert all(abs(tot[k] - r[k]) <= 1e-6 * max(1, r[k]) for k in tot), (y, tot, {k: r[k] for k in tot})
            continue
        s = sf_by_cty[y][g]
        ser["pp"].append((p, s["spend"] / s["enroll"] * 1000 if s["enroll"] else None))
        for k in ("fed", "state", "local"):
            ser[k].append((p, s[k] / s["rev"] * 100 if s["rev"] else None))
    target = ohio if g == SK else counties[g]
    target["school_spending_per_pupil"] = entry(ser["pp"], {})
    target["school_revenue_federal_share"] = entry(ser["fed"], {})
    target["school_revenue_state_share"] = entry(ser["state"], {})
    target["school_revenue_local_share"] = entry(ser["local"], {})

extras["school_districts_counted"] = {g: {sy(y): sf_districts[y][g] for y in SF_YEARS} for g in COUNTIES}
extras["school_district_totals"] = {g: {sy(y): {"current_spending_thousands": sf_by_cty[y][g]["spend"],
                                                "fall_enrollment": sf_by_cty[y][g]["enroll"],
                                                "revenue_thousands_excl_other_school_systems": sf_by_cty[y][g]["rev"]}
                                         for y in SF_YEARS} for g in COUNTIES}
extras[f"school_{SK}_published_all_systems"] = {SK: {sy(y): {"per_pupil": o["per_pupil"], "federal_share": o["fed"],
                                                                "state_share": o["state"], "local_share": o["local"]}
                                                       for y, o in sf_ohio.items()}}
extras[f"school_{SK}_traditional_districts_only"] = {SK: {
    sy(y): {"per_pupil": r["spend"] / r["enroll"] * 1000, "federal_share": r["fed"] / r["rev"] * 100,
            "state_share": r["state"] / r["rev"] * 100, "local_share": r["local"] / r["rev"] * 100}
    for y, r in sf_ohio_regular.items()}}
extras["school_district_county_differences"] = {SK: [
    {"nces_id": k, "name": v[0], "census_county": v[1], "odew_county": v[2]} for k, v in sorted(sf_diff.items())]}

# =========================================================================== metrics
BEA_SRC = "U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates"
_upd = re.search(r"Last updated: ([A-Za-z]+ \d+, \d{4})", BEA_UPDATED)
BEA_VINT = (f"CAINC35 bulk file, last updated {_upd.group(1) if _upd else 'unknown'}; table discontinued "
            f"by BEA Nov. 1, 2024; {BEA_YEARS[0]}-{BEA_LAST}; population: Census intercensal 2010-2019 and "
            f"vintage 2025 estimates 2020 on; pulled {TODAY}")
HUD_SRC = "HUD Picture of Subsidized Households; Census Bureau American Community Survey and population estimates"
HUD_VINT = (f"Picture of Subsidized Households {HUD_YEARS[0]}-{HUD_YEARS[-1]} county and state extracts "
            f"(2022 on in 2020 census geography); ACS 5-year households; pulled {TODAY}")
SF_SRC = "U.S. Census Bureau, Annual Survey of School System Finances"
SF_VINT = (f"Fiscal years {SF_YEARS[0]}-{SF_YEARS[-1]} per-district files (elsec22-24.xlsx) and summary tables; "
           f"FY2024 released May 7, 2026; pulled {TODAY}")


def bea_metric(label, note):
    return {"label": label, "theme": THEME, "unit": "usd", "decimals": 0, "better": "none", "source": BEA_SRC,
            "vintage": BEA_VINT, "period_label": str(BEA_LAST), "note": note + NOTE_TAIL}


metrics = {
    "bea_medicaid_per_resident": bea_metric(
        "Medicaid and other public medical aid per resident",
        "Dollars paid for residents' care under Medicaid, the Children's Health Insurance Program and state and "
        "local medical aid (BEA line 2220), divided by population. BEA bases county figures on state payment "
        "records by county where a state supplies them and spreads the rest using other county data."),
    "bea_snap_per_resident": bea_metric(
        "SNAP food benefits per resident",
        "SNAP benefits paid to residents (BEA line 2330), divided by population. BEA starts from USDA's state "
        "total and splits it among counties using state payment records, or Census estimates of SNAP "
        "recipients where those records are missing."),
    "bea_ssi_per_resident": bea_metric(
        "Supplemental Security Income per resident",
        "Federal and state SSI payments to residents who are 65 or older, blind or disabled and have low "
        "incomes (BEA line 2310), divided by population. County figures come from Social Security payment data."),
    "bea_eitc_per_resident": bea_metric(
        "Earned income tax credit per resident",
        "The federal earned income tax credit for residents (BEA line 2320), divided by population. This is a "
        "tax credit: BEA counts the full credit, both the part that lowers taxes owed and the part paid as a "
        "refund. County figures come from IRS tax return data."),
    "bea_unemployment_per_resident": bea_metric(
        "Unemployment benefits per resident",
        "Unemployment insurance paid to residents (BEA line 2400: state programs plus programs for federal "
        "workers, railroad workers and former service members), divided by population. Starting with 2022, BEA "
        "uses BLS counts of unemployed people to split the state total among counties. "
        "2020 and 2021 include federal pandemic unemployment programs."),
    "bea_veterans_per_resident": bea_metric(
        "Veterans' benefits per resident",
        "VA pension, disability, education and life insurance benefits and other aid to veterans paid to "
        "residents (BEA line 2500), divided by population. County figures come mainly from the VA's report on "
        "spending by county."),
    "hud_households_per_1000": {
        "label": "Households in HUD-subsidized housing, per 1,000 households",
        "theme": THEME, "unit": "per1000", "decimals": 1, "better": "none", "source": HUD_SRC, "vintage": HUD_VINT,
        "period_label": f"Dec. 31, {HUD_YEARS[-1]}",
        "note": "Occupied homes in all HUD rental programs (public housing, Housing Choice Vouchers, "
                "project-based Section 8, Section 202 and 811 and smaller programs) on Dec. 31, per 1,000 "
                "households in the latest ACS 5-year data. Before 2025 HUD published a rounded occupancy "
                "rate, not a count, so earlier years are estimates. It counts help received, not results."},
    "hud_spending_per_resident": {
        "label": "HUD rental aid spending per resident",
        "theme": THEME, "unit": "usd", "decimals": 0, "better": "none", "source": HUD_SRC, "vintage": HUD_VINT,
        "period_label": f"Dec. 31, {HUD_YEARS[-1]} snapshot, annualized",
        "note": "HUD's average monthly spending per occupied home, times occupied homes, times 12, divided by "
                "population. This is a yearly estimate built from a December snapshot, not HUD's reported "
                "outlays. Homes HUD could not place in a county are left out of county figures." + NOTE_TAIL},
    "school_spending_per_pupil": {
        "label": "School spending per pupil (day-to-day costs)",
        "theme": THEME, "unit": "usd", "decimals": 0, "better": "none", "source": SF_SRC, "vintage": SF_VINT,
        "period_label": f"School year {sy(SF_YEARS[-1])}",
        "note": "Current spending (pay, benefits, supplies, transportation and other day-to-day costs, not "
                "buildings or debt) of the traditional school districts based in the county, divided by their "
                f"fall enrollment. {SNAME}'s figure is built the same way, from all traditional districts. "
                f"{CFG['sf_other']} are left out; with them, the Census Bureau's "
                f"published {SNAME} figure is ${sf_ohio[SF_YEARS[-1]]['per_pupil']:,.0f}. {CFG['sf_charter']}" + NOTE_TAIL},
}
for k, who in (("federal", "the federal government"), ("state", f"the state of {SNAME}"), ("local", CFG["sf_local"])):
    metrics[f"school_revenue_{k}_share"] = {
        "label": f"Share of school district revenue from {k} sources",
        "theme": THEME, "unit": "pct", "decimals": 1, "better": "none", "source": SF_SRC, "vintage": SF_VINT,
        "period_label": f"School year {sy(SF_YEARS[-1])}",
        "note": f"Percent of the revenue of the county's traditional school districts that came from {who}. "
                f"Money one school system pays another is left out so it is not counted twice. {SNAME}'s figure "
                "is built the same way, from all traditional districts (the Census Bureau's published figure also "
                f"includes {CFG['sf_other_short']}: {sf_ohio[SF_YEARS[-1]][k[:3] if k == 'federal' else k]:.1f}%). "
                "It describes where the money comes from, not results."}

out = {"metrics": metrics, "counties": counties, SK: ohio, "extras": extras, "tracts": tracts}

# --------------------------------------------------------------------------- final checks and write
for f in COUNTIES:
    if set(counties[f]) != set(metrics):
        raise SystemExit(f"{f}: metrics {set(metrics) ^ set(counties[f])}")
if set(ohio) != set(metrics):
    raise SystemExit(f"{SK} metrics incomplete")
write_json("public_money.json", out)

print(f"\nBEA CAINC35 {BEA_UPDATED}; county sum minus state row, dollars (thousands as published x 1000):")
for code, gaps in bea_check.items():
    worst = max((abs(v) for v in gaps.values() if isinstance(v, float)), default=None)
    print(f"  line {code}: largest gap {worst}")
print(f"HUD tracts: {len(tracts)} {SNAME} tracts written; skipped {len(tract_skipped)} not-placed rows; "
      f"ACS tracts not in HUD file {len(not_in_hud)}; HUD tracts not in ACS {len(not_in_acs)}")
print("  flags (both tract metrics):", tract_flags)
print("School districts: county differences between Census and ODEW:", len(sf_diff),
      "| assigned by Census code:", sorted({k[1] for k, v in sf_assign.items() if v != "ODEW"}))
print(f"\nmetric | period | {SNAME} | min county | max county")
for mid in metrics:
    vals = [(counties[f][mid]["latest"], f) for f in COUNTIES if counties[f][mid]["latest"] is not None]
    lo, hi = min(vals), max(vals)
    print(f"  {mid} | {ohio[mid]['period']} | {ohio[mid]['latest']:.1f} | {lo[0]:.1f} {geo[lo[1]]['name']} | "
          f"{hi[0]:.1f} {geo[hi[1]]['name']} | n={len(vals)}")
