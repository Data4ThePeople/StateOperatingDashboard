# Datasets: population estimates layer (popest.json)

Built by `scripts/21_popest.py`.

## County population estimates, Vintage 2025 (U.S. Census Bureau, Population Estimates Program)

**What it is.** Yearly estimates of each county's resident population on July 1, and the parts of each
year's change: births, deaths, net international migration and net domestic migration (moves between
U.S. counties). One row per county and one for the state.

**Where it comes from.**
`https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv`
(CSV, Latin-1 text, no login). Cached at `data/raw/popest/co-est2025-alldata.csv`. The script falls back
to the Vintage 2024 file (`co-est2024-alldata.csv`) if the 2025 file cannot be read.

**Version and vintage.** Vintage 2025, covering April 1, 2020 to July 1, 2025. Each December to March the
Census Bureau posts a new vintage that replaces the whole 2020-to-date series.

**Coverage.** All 88 Ohio counties (SUMLEV 050) and Ohio (SUMLEV 040). Ohio values are the Census
Bureau's own state row. The numbers are model estimates, not counts. They start from the April 1, 2020
estimates base (the 2020 Census count with Census Bureau adjustments) and add births and deaths from
vital records, domestic migration from tax returns, Medicare and Social Security records, and
international migration mostly from the ACS. The Census Bureau's method statement for each vintage
explains the inputs.

**Fields used and metrics built.**

| Metric | Built from |
|---|---|
| population_estimate | POPESTIMATE2020 to POPESTIMATE2025 (July 1 each year) |
| pop_change_pct | (POPESTIMATE{year} minus ESTIMATESBASE2020) / ESTIMATESBASE2020 x 100 |
| natural_change_rate | Sum of NATURALCHG2020-2025 per 1,000 of ESTIMATESBASE2020 |
| net_international_migration_rate | Sum of INTERNATIONALMIG2020-2025 per 1,000 of ESTIMATESBASE2020 |
| net_domestic_migration_rate | Sum of DOMESTICMIG2020-2025 per 1,000 of ESTIMATESBASE2020 |
| extras.components | Annual NATURALCHG, INTERNATIONALMIG, DOMESTICMIG and RESIDUAL by year, plus the base |

For the three rate metrics, `series` is the running total since April 2020 through July 1 of each year,
per 1,000 base residents; `latest` is the full April 2020 to July 2025 total. The unit is "per1000",
which is not in the layer contract's unit list.

**Changes over time.** The 2020 component columns cover only April 1 to July 1, 2020. Later columns
cover July 1 of the prior year to July 1 of the named year.

**Suppressed, censored or masked values.** None. Small counties can show zero international migration
in every year (Vinton County does).

**Missing data.** None for Ohio.

**Revisions.** Every vintage revises all years back to April 2020. We pin Vintage 2025 and refresh the
whole series when a new vintage comes out.

**Units and rounding.** People, as whole numbers. The components plus a small residual add to the
change in population; the residual is kept in `extras.components`.

**Known quirks.** The estimates base differs slightly from the 2020 Census count. Starting with
Vintage 2024 the Census Bureau changed how it estimates international migration, which raised those
estimates, so the international column is not comparable with Vintage 2023 or earlier files.

**Uncertainty.** The Census Bureau does not publish margins of error for these estimates. `moe` is null.

**License and attribution.** Public domain U.S. government data. Credit: "U.S. Census Bureau, Population
Estimates Program, Vintage 2025."
