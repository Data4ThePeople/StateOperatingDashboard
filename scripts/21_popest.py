"""Census Bureau population estimates (Vintage 2025) for the 88 Ohio counties and Ohio: popest.json
(theme people).

Population on July 1, 2020-2025; change since the April 1, 2020 estimates base; and the components of
change (natural change, net international migration, net domestic migration) summed over April 1, 2020
to July 1, 2025, as rates per 1,000 people in the April 2020 base. Falls back to Vintage 2024 if the
Vintage 2025 file is not posted.
"""
import csv
import datetime as dt
import io
import sys

from common import RAW, STATE, cached, write_json

FILES = [(2025, "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv"),
         (2024, "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv")]
PULLED = dt.date.today().isoformat()


def load():
    for v, url in FILES:
        try:
            raw = cached(RAW / "popest" / url.rsplit("/", 1)[1], url)
        except Exception as e:  # noqa: BLE001
            print(f"Vintage {v} not available ({e}); trying the next one")
            continue
        return v, list(csv.DictReader(io.StringIO(raw.decode("latin-1"))))
    sys.exit("no population estimates file could be read")


COMPONENTS = [("natural_change", "NATURALCHG"), ("net_international_migration", "INTERNATIONALMIG"),
              ("net_domestic_migration", "DOMESTICMIG")]


def main():
    vint, rows = load()
    years = list(range(2020, vint + 1))
    oh = [r for r in rows if r["STATE"] == STATE]
    state = [r for r in oh if r["SUMLEV"] == "040"]
    counties = {r["STATE"] + r["COUNTY"]: r for r in oh if r["SUMLEV"] == "050"}
    if len(state) != 1 or len(counties) != 88:
        sys.exit(f"expected 1 state row and 88 counties, got {len(state)} and {len(counties)}")

    period_all = f"Apr. 2020 to July {vint}"

    def cells(r):
        base = float(r["ESTIMATESBASE2020"])
        pop = [[str(y), float(r[f"POPESTIMATE{y}"])] for y in years]
        latest_pop = pop[-1][1]
        out = {
            "population_estimate": {"latest": latest_pop, "period": str(vint), "series": pop, "moe": None, "flag": None},
            "pop_change_pct": {"latest": 100 * (latest_pop - base) / base, "period": str(vint),
                               "series": [[str(y), 100 * (p - base) / base] for y, p in [(int(a), b) for a, b in pop]],
                               "moe": None, "flag": None},
        }
        comp = {}
        for name, col in COMPONENTS:
            annual = [float(r[f"{col}{y}"]) for y in years]
            comp[name] = [[str(y), a] for y, a in zip(years, annual)]
            # running total since April 2020, per 1,000 base population
            run, series = 0.0, []
            for y, a in zip(years, annual):
                run += a
                series.append([str(y), 1000 * run / base])
            out[name + "_rate"] = {"latest": 1000 * sum(annual) / base, "period": str(vint),
                                   "series": series, "moe": None, "flag": None}
        comp["residual"] = [[str(y), float(r[f"RESIDUAL{y}"])] for y in years]
        comp["base_april_2020"] = base
        comp["note"] = ("Annual components, people. The 2020 value covers April 1 to July 1, 2020; each later value "
                        "covers July 1 of the prior year to July 1 of that year.")
        return out, comp

    out = {"metrics": {}, "counties": {}, "ohio": {}, "extras": {"components": {}}}
    for g, r in sorted(counties.items()):
        out["counties"][g], out["extras"]["components"][g] = cells(r)
    out["ohio"], out["extras"]["components"]["ohio"] = cells(state[0])

    src = "U.S. Census Bureau, Population Estimates Program"
    vs = f"Vintage {vint} county estimates (co-est{vint}-alldata.csv); pulled {PULLED}"
    rate = (" Summed from April 1, 2020 to July 1, {v}, per 1,000 residents in the April 2020 estimates base. "
            "These are modeled estimates, not counts, and each new vintage revises every year back to 2020.").format(v=vint)
    meta = {
        "population_estimate": ("Population (estimate)", "count", 0, f"July 1, {vint}",
                                "Estimated residents on July 1 of each year. Modeled from the 2020 Census plus births, "
                                "deaths and migration; each new vintage revises earlier years."),
        "pop_change_pct": ("Population change since 2020", "pct", 1, period_all,
                           "Percent change from the April 1, 2020 estimates base to July 1 of each year. "
                           "The base is the 2020 Census count adjusted by the Census Bureau, not the raw count."),
        "natural_change_rate": ("Births minus deaths, per 1,000 people", "per1000", 1, period_all,
                                "Births minus deaths." + rate),
        "net_international_migration_rate": ("Net international migration, per 1,000 people", "per1000", 1, period_all,
                                             "People moving in from abroad minus people moving abroad." + rate),
        "net_domestic_migration_rate": ("Net moves from other U.S. counties, per 1,000 people", "per1000", 1,
                                        period_all,
                                        "People moving in from other U.S. counties minus people moving out to them."
                                        + rate),
    }
    for m, (label, unit, dec, pl, note) in meta.items():
        out["metrics"][m] = {"label": label, "theme": "people", "unit": unit, "decimals": dec, "better": "none",
                             "source": src, "vintage": vs, "period_label": pl, "note": note}
    write_json("popest.json", out)

    for g in ("39049", "39163"):
        c = out["counties"][g]
        print(g, counties[g]["CTYNAME"], {k: round(v["latest"], 2) for k, v in c.items()})
    print("ohio", {k: round(v["latest"], 2) for k, v in out["ohio"].items()})


if __name__ == "__main__":
    main()
