# Datasets: national benchmark

Built by `scripts/50_national.py` into `data/processed/national.json`. Raw pulls are cached under
`data/raw/census/national/`, `data/raw/census_pep/`, `data/raw/bls_laus_national/`, `data/raw/bls_qcew/`
and `data/raw/cdc/national/`. Pulled 2026-11-09.

## National benchmark (same sources as the county layers)

**What it is.** For each dashboard measure that has a same-definition state figure, the value for all
50 states and DC (keyed by USPS code) and for the United States. The page uses it to show the U.S. value
and Ohio's rank among the 51. Puerto Rico is left out.

**Where it comes from.** The same publishers, tables, lines, periods and vintages as the county layers:

| Measures | Source and query | Period |
|---|---|---|
| All ACS measures in `income.json` and `people.json` except population | ACS 5-year, same tables and lines as `20_acs.py` (its `compute` function is reused), `for=state:*` and `for=us:1` | 2020-2024 |
| `prime_age_epop` | ACS 5-year B23001, same lines as `23_age.py`; group-quarters flag from B26001 and B01003 at the same 5% cutoff | 2020-2024 |
| `unemployment_rate`, `labor_force_change_pct` | LAUS state series `LAUST{fips}00000000000{03,06}`, not seasonally adjusted, annual averages. U.S.: CPS `LNU04000000` (rate) and `LNU01000000` (labor force), annual averages | 2025; 2019 to 2025 |
| `avg_weekly_wage`, `manufacturing_share`, `health_care_share` | QCEW annual area files `{fips}000.csv` and `US000.csv`. Same cells as `10_jobs_industry.py` at the state (5x) and national (1x) aggregation levels | 2025 |
| `uninsured_under65`, `uninsured_under65_low_income` | SAHIE API, same categories as `30_health.py`, `for=state:*` and `for=us:*` | 2024 |
| `saipe_poverty_rate`, `saipe_child_poverty_rate`, `saipe_median_income` | SAIPE API, `for=state:*` and `for=us:*` | 2024 |
| `pop_change_pct` and the three components-of-change rates | Vintage 2025 `co-est2025-alldata.csv` state rows (the file `21_popest.py` reads); U.S. row from `NST-EST2025-ALLDATA.csv` | Apr. 2020 to July 2025 |
| `prime_age_share`, `age65_share`, `general_fertility_rate` | Vintage 2025 `cc-est2025-agesex-all.csv`, each state summed from its counties as `23_age.py` does for Ohio; births from the state rows above. U.S.: `nc-est2025-agesex-res.csv` and the NST U.S. births | July 1, 2025; year ending June 30, 2025 |
| `overdose_rate_per100k` | CDC VSRR state file `xkb8-kh2a`, indicator "Number of Drug Overdose Deaths", period "12 month-ending", field `data_value`, over the Census July 1, 2025 population | 12 months ending March 2026 |

**The U.S. value.** It is the publisher's own national figure in every case (ACS `us:1`, CPS annual
average, QCEW `US000`, SAHIE and SAIPE U.S. rows, the Census national population files, CDC's U.S. row),
not an average of states. `us_source` names it for each measure.

**Check against the Ohio figures.** The script computes Ohio the same way as every other state and stops
if Ohio does not equal the `ohio` value in the layer file at display precision. On the 2026-11-09 run
all 33 measures matched exactly. The check results are stored in `checks`.

**Suppressed values.** BLS withholds the 2025 private manufacturing total for Alaska, DC, Hawaii,
Louisiana, Maryland and Wyoming to protect employer privacy. Those six are null with the flag
"suppressed", so Ohio's manufacturing rank is out of 45 states.

**Overdose deaths.** The state file counts deaths that occurred in the state, not deaths of state
residents, as the Ohio figure on the dashboard does. CDC reports New York City apart from the rest of New
York; the New York value adds the two. Every state and the U.S. carry CDC's flag "Underreported due to
incomplete data" for this period, stored in `flags`. CDC also publishes a predicted count that adjusts
for records still coming in. We use the reported count, as the dashboard does; the gap between the two is
stored in `predicted_minus_reported_pct` (0% for Ohio, 0.8% for the U.S., up to 21% for Oregon and 13%
for Nevada), so those states' rates read low next to Ohio's. Rates are not age-adjusted.

**Known quirks.** U.S. net domestic migration is zero by definition, because moves between counties
cancel out nationally. The prime-age work rate flags DC, where 5% of residents live in group quarters.

**Left out, and why.**

| Measure | Reason |
|---|---|
| `labor_force`, `employed`, `private_jobs`, `population`, `population_estimate`, `overdose_deaths_12mo` | Counts. A state total does not compare with a county total; the matching rate or share is used where one exists. |
| `top_industry_share` | A county concept: the largest disclosed 3-digit industry, where the set of withheld industries differs by place. |
| `concentration_hhi` | A county concept built on disclosed county supersectors. |
| The ten `places_*` measures | The CDC PLACES county file has no state rows, so the dashboard has no Ohio figure to compare with. |

**License and attribution.** Public domain. Credit: U.S. Census Bureau (American Community Survey,
Population Estimates Program, SAHIE, SAIPE); U.S. Bureau of Labor Statistics (LAUS, CPS, QCEW); CDC,
National Center for Health Statistics.
