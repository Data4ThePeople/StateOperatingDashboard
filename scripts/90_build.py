"""Merge every processed layer into one self-contained page: dist/index.html.

Layers are data/processed/*.json in the shape set by docs/LAYER_CONTRACT.md. A metric id that
appears in two layers is a hard failure. ORDER sets which measures show first in each issue tab;
HIDE drops measures from the page (kept in the data).
"""
import datetime as dt
import json

from common import DIST, PROC, ROOT

LAYERS = ["jobs", "income", "people", "popest", "age", "reading", "enrollment", "childcare", "crime", "health", "prices"]
ORDER = {
    "jobs": ["unemployment_rate", "labor_force_change_pct", "labor_force", "private_jobs", "avg_weekly_wage",
             "top_industry_share", "concentration_hhi", "manufacturing_share", "health_care_share"],
    "income": ["near_poverty_share", "poverty_rate", "below_200_share", "saipe_poverty_rate", "saipe_child_poverty_rate",
               "median_household_income", "saipe_median_income", "snap_households_share", "rent_burden", "owner_cost_burden", "gini"],
    "health": ["uninsured_under65", "uninsured_under65_low_income", "overdose_rate_per100k", "overdose_deaths_12mo", "medicaid_share",
               "uninsured_acs", "disability_share"],
    "childcare": ["childcare_need_per_slot", "slots_per_100_under6"],
    "safety": ["violent_crime_rate", "property_crime_rate"],
    "people": ["population_estimate", "population", "pop_change_pct", "prime_age_share", "prime_age_epop", "age65_share",
               "general_fertility_rate", "net_domestic_migration_rate", "net_intl_migration_rate", "natural_change_rate",
               "median_age", "bachelors_or_higher", "hs_or_higher"],
}
# housing cost burden is a cost-of-living measure, shown with income
THEME_OVERRIDE = {"rent_burden": "income", "owner_cost_burden": "income"}
HIDE = {"employed", "uninsured_acs", "population"}
# concentration is compared across counties, not with the state: a whole state is always more diverse than one county
NO_JUDGMENT = {"top_industry_share", "concentration_hhi"}
# measures that are already a change; a "change over time" view of them would be a change of a change
IS_CHANGE = {"labor_force_change_pct", "pop_change_pct", "natural_change_rate", "net_international_migration_rate", "net_domestic_migration_rate"}
# value carries a flag that makes it unfit to judge (prisons, dorms): left out of overview and priority counts
EXCLUDE_FLAGGED = {"prime_age_epop"}
# national comparison hidden: the U.S. value is zero by definition
NO_NATIONAL = {"net_domestic_migration_rate"}
# issues for the Priorities tab: each is a group of judged measures already on the page
ISSUES = [
    ("work", "Work and wages", ["unemployment_rate", "prime_age_epop", "labor_force_change_pct", "avg_weekly_wage"]),
    ("poverty", "Poverty and near poverty", ["near_poverty_share", "poverty_rate", "saipe_child_poverty_rate", "median_household_income"]),
    ("housing", "Housing costs", ["rent_burden", "owner_cost_burden"]),
    ("coverage", "Health coverage", ["uninsured_under65", "uninsured_under65_low_income"]),
    ("addiction", "Addiction and mental health", ["overdose_rate_per100k", "places_depression", "places_mental_distress", "places_smoking"]),
    ("chronic", "Chronic disease", ["places_diabetes", "places_obesity", "places_checkup"]),
    ("needs", "Food, housing and transportation needs", ["places_food_insecurity", "places_housing_insecurity", "places_no_transportation"]),
    ("education", "Education", ["grade3_ela_proficient", "hs_or_higher", "bachelors_or_higher"]),
    ("childcare", "Childcare", ["childcare_need_per_slot", "infant_price_pct_income"]),
    ("safety", "Public safety", ["violent_crime_rate", "property_crime_rate"]),
]

# measures shown but left out of the overview count, because a sibling measure already covers them
# overdose rate: CDC withholds 45 of 88 counties, so "worst fourth" would be of 43 counties, not 88
NOT_IN_OVERVIEW = {"overdose_rate_per100k", "below_200_share", "medicaid_share", "saipe_poverty_rate", "saipe_median_income", "overdose_deaths_12mo", "uninsured_under65_low_income"}

LABELS = {
    "near_poverty_share": "Near poverty: people at 100% to 199% of the poverty line",
    "health_care_share": "Health care and social assistance share of private jobs",
    "below_200_share": "People below 200% of the poverty line",
}
# CDC flags every 2026 month of the statewide file "Underreported due to incomplete data"
OHIO_FLAGS = {"overdose_deaths_12mo": "CDC marks this statewide figure as underreported due to incomplete data",
              "overdose_rate_per100k": "CDC marks this statewide figure as underreported due to incomplete data"}

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
        m["label"] = LABELS.get(mid, m["label"])
        if mid in OHIO_FLAGS and mid in out["ohio"] and out["ohio"][mid].get("period", "")[:4] >= "2026":
            out["ohio"][mid]["flag"] = OHIO_FLAGS[mid]
            m["note"] = m["note"] + " The statewide figure counts deaths that happened in Ohio; county figures count residents. CDC marks recent statewide months as underreported because records are still coming in."
        if mid in HIDE:
            m["hidden"] = True
        if mid in NOT_IN_OVERVIEW:
            m["overview"] = False
        if mid in EXCLUDE_FLAGGED:
            m["exclude_flagged"] = True
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
    # issues keep only measures that are on the page and carry a judgment
    out["issues"] = []
    for iid, label, ids in ISSUES:
        keep = [i for i in ids if i in out["metrics"] and out["metrics"][i]["better"] != "none" and not out["metrics"][i].get("hidden")]
        if keep:
            out["issues"].append({"id": iid, "label": label, "measures": keep})
    print("issues:", [(i["id"], len(i["measures"])) for i in out["issues"]])
    # national benchmark: same-definition state and U.S. values (scripts/50_national.py)
    nat = PROC / "national.json"
    out["national"] = {}
    if nat.exists():
        n = json.loads(nat.read_text())["national"]
        for mid, v in n.items():
            if mid in out["metrics"] and mid not in NO_NATIONAL:
                if v.get("states", {}).get("OH") is not None and out["ohio"].get(mid, {}).get("latest") is not None:
                    assert abs(v["states"]["OH"] - out["ohio"][mid]["latest"]) < 1e-6 * max(1, abs(v["states"]["OH"])), f"national Ohio mismatch on {mid}"
                out["national"][mid] = v
        print("national:", len(out["national"]), "measures")
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
