"""Merge every processed layer into one self-contained page: dist/index.html.

Layers are data/processed/*.json in the shape set by docs/LAYER_CONTRACT.md. A metric id that
appears in two layers is a hard failure. ORDER sets which measures show first in each issue tab;
HIDE drops measures from the page (kept in the data).
"""
import datetime as dt
import json

from common import DIST, PROC, ROOT

LAYERS = ["jobs", "income", "people", "popest", "health"]
ORDER = {
    "jobs": ["unemployment_rate", "labor_force_change_pct", "labor_force", "private_jobs", "avg_weekly_wage",
             "top_industry_share", "concentration_hhi", "manufacturing_share", "health_care_share"],
    "income": ["near_poverty_share", "poverty_rate", "below_200_share", "saipe_poverty_rate", "saipe_child_poverty_rate",
               "median_household_income", "saipe_median_income", "snap_households_share", "rent_burden", "owner_cost_burden", "gini"],
    "health": ["uninsured_under65", "uninsured_under65_low_income", "overdose_rate_per100k", "overdose_deaths_12mo", "medicaid_share",
               "uninsured_acs", "disability_share"],
    "people": ["population", "pop_change_pct", "net_domestic_migration_rate", "net_intl_migration_rate", "natural_change_rate",
               "median_age", "bachelors_or_higher", "hs_or_higher"],
}
# housing cost burden is a cost-of-living measure, shown with income
THEME_OVERRIDE = {"rent_burden": "income", "owner_cost_burden": "income"}
HIDE = {"employed", "uninsured_acs", "population"}
# concentration is compared across counties, not with the state: a whole state is always more diverse than one county
NO_JUDGMENT = {"top_industry_share", "concentration_hhi"}
# measures that are already a change; a "change over time" view of them would be a change of a change
IS_CHANGE = {"labor_force_change_pct", "pop_change_pct", "natural_change_rate", "net_international_migration_rate", "net_domestic_migration_rate"}
# measures shown but left out of the overview count, because a sibling measure already covers them
NOT_IN_OVERVIEW = {"below_200_share", "medicaid_share", "saipe_poverty_rate", "saipe_median_income", "overdose_deaths_12mo", "uninsured_under65_low_income"}

if __name__ == "__main__":
    out = {"metrics": {}, "counties": {}, "ohio": {}, "extras": {}}
    for name in LAYERS:
        p = PROC / f"{name}.json"
        if not p.exists():
            print(f"skip {name}: not built yet")
            continue
        d = json.loads(p.read_text())
        for mid, m in d["metrics"].items():
            if mid in out["metrics"]:
                raise SystemExit(f"metric {mid} appears in two layers")
            out["metrics"][mid] = m
        for f, row in d["counties"].items():
            out["counties"].setdefault(f, {}).update(row)
        out["ohio"].update(d.get("ohio", {}))
        for k, v in (d.get("extras") or {}).items():
            if k in out["extras"]:
                raise SystemExit(f"extra {k} appears in two layers")
            out["extras"][k] = v
        print(f"{name}: {len(d['metrics'])} measures, {len(d['counties'])} counties")
    for mid, m in out["metrics"].items():
        m["theme"] = THEME_OVERRIDE.get(mid, m.get("theme"))
        if mid in HIDE:
            m["hidden"] = True
        if mid in NOT_IN_OVERVIEW:
            m["overview"] = False
        if mid in NO_JUDGMENT:
            m["better"] = "none"
            m["note"] = m["note"] + " Shaded from least to most concentrated across Ohio's counties rather than against the state, because a whole state is always more diverse than a single county."
        # a county count cannot be judged against the state total
        if m["unit"] == "count":
            m["better"] = "none"
        if mid in IS_CHANGE:
            m["no_change"] = True
        if m["unit"] == "usd":
            m["nominal"] = True
        # no statewide figure from the publisher: compare with the median county, and keep it out of the overview count
        if (out["ohio"].get(mid) or {}).get("latest") is None:
            vals = sorted(r[mid]["latest"] for r in out["counties"].values() if (r.get(mid) or {}).get("latest") is not None)
            med = (vals[len(vals) // 2] + vals[(len(vals) - 1) // 2]) / 2
            out["ohio"][mid] = {"latest": med, "period": (out["counties"]["39001"][mid] or {}).get("period"), "series": [],
                                "flag": "median of Ohio's 88 counties; the publisher gives no statewide figure"}
            m["ref"] = "the median Ohio county"
            m["overview"] = False
    rank = {mid: i for t in ORDER.values() for i, mid in enumerate(t)}
    out["metrics"] = dict(sorted(out["metrics"].items(), key=lambda kv: rank.get(kv[0], 99)))
    out["built"] = dt.date.today().strftime("%B %-d, %Y")
    geo = json.loads((PROC / "geo.json").read_text())
    missing = set(geo["counties"]) - set(out["counties"])
    if out["counties"] and missing:
        raise SystemExit(f"counties missing from data: {sorted(missing)}")
    html = (ROOT / "scripts" / "template.html").read_text()
    html = html.replace("/*DATA*/null", json.dumps(out, separators=(",", ":"))).replace("/*GEO*/null", json.dumps(geo, separators=(",", ":")))
    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(html)
    print(f"wrote dist/index.html ({len(html) // 1024} KB), {len(out['metrics'])} measures")
