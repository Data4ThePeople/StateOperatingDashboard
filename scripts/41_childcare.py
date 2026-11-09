"""Licensed child care programs by county. Writes data/processed/childcare.json (theme "childcare").

Built:
- childcare_providers: licensed early care and education programs open on the pull date (status "Open" or
  "Enforcement"), from the Ohio Department of Children and Youth (DCY) program layer on the State of Ohio's
  ArcGIS server (the layer behind DCY's Step Up To Quality program locator; updated weekly). Five licensed
  types: child care centers, family child care Type A and Type B homes, preschools and school-age child care.
  Day camps (registered, not licensed), in-home aides (certified), out-of-state registrations and inactive
  programs are left out. Counts by type go in extras.providers_by_type.

Not built (see docs/datasets/childcare.md for why):
- NDCP childcare prices: the DOL file server refuses scripted downloads and the DOL API needs a key we lack.
- Licensed capacity (slots), slots per 100 children, and children per slot: no public county or program
  capacity field was found (not in the program layer, the Ohio Child Care Search pages, or DCY's reports).
- Publicly funded child care by county: ODJFS stopped publishing the county table after October 2023, and
  that table has inconsistent values in at least 13 counties.

The layer changes weekly. The first run saves a dated snapshot under data/raw/dcy/; later runs reuse the
newest snapshot. Pass --refresh to pull a new one.
"""
import datetime as dt
import io
import json
import sys
from collections import Counter

import pandas as pd

from common import RAW, cached, get, write_json

LAYER = "https://maps.ohio.gov/arcgis/rest/services/Hosted/Ohio_Daycares_view/FeatureServer/0"
ITEM = "https://maps.ohio.gov/portal/sharing/rest/content/items/e7b80e83d8764427b5de7fde6f67f83d?f=json"
AGESEX = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/asrh/cc-est2025-agesex-39.csv"
SNAP_DIR = RAW / "dcy"

LICENSED = {  # program_type in the layer -> short key
    "Child Care Center": "center",
    "FCC - Type A Home": "fcc_type_a",
    "FCC - Type B Home": "fcc_type_b",
    "Pre School": "preschool",
    "School Age Child Care": "school_age",
}
NOT_LICENSED = {"Day Camp", "In-Home Aide", "Out of State Registration"}
ACTIVE = {"Open", "Enforcement"}


def snapshot(refresh):
    """Return (rows, pulled_date, item_modified_date) from the newest saved snapshot, pulling one if needed."""
    have = sorted(SNAP_DIR.glob("ohio_daycares_*.json"))
    if have and not refresh:
        d = json.loads(have[-1].read_bytes())
        return d["rows"], d["pulled"], d["item_modified"]
    n = json.loads(get(LAYER + "/query?where=1%3D1&returnCountOnly=true&f=json"))["count"]
    rows = []
    for off in range(0, n, 1000):
        url = (LAYER + "/query?where=1%3D1&outFields=*&returnGeometry=false&orderByFields=objectid"
               f"&resultRecordCount=1000&resultOffset={off}&f=json")
        res = json.loads(get(url))
        if "error" in res:
            sys.exit(f"layer query failed: {res['error']}")
        rows += [f["attributes"] for f in res["features"]]
    if len(rows) != n:
        sys.exit(f"expected {n} records, got {len(rows)}")
    item = json.loads(get(ITEM))
    mod = dt.datetime.fromtimestamp(item["modified"] / 1000, dt.timezone.utc).date().isoformat()
    pulled = dt.date.today().isoformat()
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    (SNAP_DIR / f"ohio_daycares_{pulled}.json").write_text(
        json.dumps({"source": LAYER, "pulled": pulled, "item_modified": mod, "rows": rows}))
    return rows, pulled, mod


def county_fips():
    a = pd.read_csv(io.BytesIO(cached(RAW / "census_pep" / "cc-est2025-agesex-39.csv", AGESEX)), encoding="latin-1")
    a = a[(a.SUMLEV == 50) & (a.YEAR == 7)]
    out = {}
    for _, r in a.iterrows():
        name = r.CTYNAME.replace(" County", "").upper()
        out[name] = f"39{int(r.COUNTY):03d}"
    if len(out) != 88:
        sys.exit(f"expected 88 county names, got {len(out)}")
    return out


def main():
    rows, pulled, item_mod = snapshot("--refresh" in sys.argv)
    fips = county_fips()

    types = Counter(r["program_type"] for r in rows)
    unknown = set(types) - set(LICENSED) - NOT_LICENSED
    if unknown:
        sys.exit(f"new program types in the layer, decide how to treat them: {unknown}")
    statuses = set(r["program_status"] for r in rows)
    if statuses - ACTIVE - {"Inactive"}:
        sys.exit(f"new program status values: {statuses - ACTIVE - {'Inactive'} }")

    # One record per program. Program numbers are missing for most Type B homes; the provider link is unique.
    links = Counter(r["link"] for r in rows)
    dups = [k for k, v in links.items() if v > 1]
    if dups or any(not r["link"] for r in rows):
        sys.exit(f"duplicate or empty provider links: {dups[:5]}")

    keep = [r for r in rows if r["program_type"] in LICENSED and r["program_status"] in ACTIVE]
    by = {g: Counter() for g in fips.values()}
    off_map = Counter()
    for r in keep:
        g = fips.get((r["county"] or "").strip().upper())
        if g is None:
            off_map[r["county"]] += 1
            continue
        by[g][LICENSED[r["program_type"]]] += 1
    if off_map:
        sys.exit(f"licensed programs with a county we cannot match: {dict(off_map)}")

    period = pulled
    out = {"metrics": {}, "counties": {}, "ohio": {}, "extras": {"providers_by_type": {}}}
    for g in sorted(by):
        n = sum(by[g].values())
        out["counties"][g] = {"childcare_providers": {"latest": float(n), "period": period,
                                                      "series": [[period, float(n)]], "moe": None, "flag": None}}
        out["extras"]["providers_by_type"][g] = {k: by[g].get(k, 0) for k in LICENSED.values()}
    tot = Counter()
    for c in by.values():
        tot.update(c)
    n_oh = sum(tot.values())
    out["ohio"]["childcare_providers"] = {"latest": float(n_oh), "period": period, "series": [[period, float(n_oh)]],
                                          "moe": None, "flag": None}
    out["extras"]["providers_by_type"]["ohio"] = {k: tot.get(k, 0) for k in LICENSED.values()}
    out["extras"]["providers_by_type"]["note"] = (
        "Licensed programs open on the pull date, by type: center = child care center; fcc_type_a = family "
        "child care Type A home (7 to 12 children); fcc_type_b = Type B home (1 to 6 children); preschool = "
        "preschool run by a school district, nonpublic school, county DD board or community school; school_age "
        "= school-age child care.")

    out["metrics"]["childcare_providers"] = {
        "label": "Licensed child care programs",
        "theme": "childcare",
        "unit": "count",
        "decimals": 0,
        "better": "none",
        "source": "Ohio Department of Children and Youth, licensed program list (State of Ohio ArcGIS layer "
                  "Ohio_Daycares_view)",
        "vintage": f"snapshot pulled {pulled}; layer updated weekly (item last modified {item_mod})",
        "period_label": f"open on {pulled}",
        "note": "Licensed child care centers, family child care homes (Type A and B), preschools and school-age "
                "programs that were open on the pull date. A program is counted once no matter its size, so this "
                "is not a count of slots. Ohio is the sum of the 88 counties; the state publishes no matching "
                "point-in-time total.",
    }

    # duplicate-period guard (contract: fail hard)
    for g, cells in list(out["counties"].items()) + [("ohio", out["ohio"])]:
        for m, c in cells.items():
            ps = [p for p, _ in c["series"]]
            if len(ps) != len(set(ps)):
                sys.exit(f"duplicate periods in {g} {m}")
    if len(out["counties"]) != 88:
        sys.exit("expected 88 counties")

    write_json("childcare.json", out)
    print(f"records in layer {len(rows)}; licensed and open {len(keep)}; Ohio by type {dict(tot)}")
    for g in ("39049", "39163"):
        print(g, out["extras"]["providers_by_type"][g], "total", out["counties"][g]["childcare_providers"]["latest"])


if __name__ == "__main__":
    main()
