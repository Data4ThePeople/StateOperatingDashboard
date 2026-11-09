# Datasets: jobs and industry layer

Built by `scripts/10_jobs_industry.py`, which writes `data/processed/jobs.json` (theme "jobs").
Pulled 2026-11-09.

## Local Area Unemployment Statistics (U.S. Bureau of Labor Statistics)

**What it is.** Monthly and annual estimates of the labor force, employed and unemployed residents,
and the unemployment rate for each Ohio county and for Ohio. People are counted where they live,
not where they work.

**Where it comes from.** BLS Public Data API v2 (`api.bls.gov/publicAPI/v2/timeseries/data/`),
JSON, registered key, 50 series and 20 years per request, `annualaverage=true` so the M13 annual
average comes back. Series: `LAUCN{fips}0000000003` (rate), `...05` (employed), `...06` (labor
force); Ohio uses `LAUST390000000000003/05/06`. All not seasonally adjusted, so counties and state
match. Raw responses cached in `data/raw/bls_laus/`.

**Version and vintage.** Annual averages 2000 through 2025, plus the latest month, September 2026
(preliminary). County data come out monthly. Each spring BLS revises recent years when it
re-benchmarks the model.

**Coverage.** All 88 counties and Ohio. County figures are model-based: BLS builds them from the
statewide Current Population Survey estimate, payroll job counts, and unemployment insurance claims,
then shares the state total across counties. They are not a direct survey count of each county.

**Changes over time.** Labor force definitions are stable over 2000-2025. Annual population control
updates can shift levels between years.

**Suppressed, censored or masked values.** None suppressed. October 2025 shows "-" for every county
and the state: BLS did not collect data that month during the federal government shutdown. The 2025
annual average BLS publishes is therefore based on 11 months; our check (mean of the 11 available
months) matches the published M13 value for Franklin and Vinton.

**Missing data.** October 2025 only (see above). A "-" is stored as missing, never zero.

**Revisions.** Annual revisions each March. The latest month is preliminary and is revised the
next month. We refresh the full series on each run (delete the cache to re-pull).

**Units and rounding.** Rate in percent to one decimal; counts in persons. Small-county counts are
published to the person but carry model error well above that.

**Known quirks.** `labor_force_change_pct` is our own calculation: the percent change in the annual
average labor force from 2019. Each series point is that year's change from 2019 (2019 = 0), so the
latest value is the 2019-to-2025 change. The latest month is not seasonally adjusted, so compare it
only with the same month in other years, not with the annual average.

**Uncertainty.** BLS does not publish error ranges for county LAUS estimates. Estimates for small
counties are less reliable than for large ones.

**License and attribution.** Public domain U.S. government data. Credit: U.S. Bureau of Labor
Statistics, Local Area Unemployment Statistics.

## Quarterly Census of Employment and Wages (U.S. Bureau of Labor Statistics)

**What it is.** A count of jobs and wages from employers' unemployment insurance tax filings, by
county, ownership (private, federal, state, local) and NAICS industry. We use annual averages.
Jobs are counted where the job is, not where the worker lives.

**Where it comes from.** QCEW open data area files,
`https://data.bls.gov/cew/data/api/{year}/a/area/{fips}.csv`, one CSV per county per year and
`39000` for Ohio statewide, no login. Industry names from
`https://data.bls.gov/cew/doc/titles/industry/industry_titles.csv`. Raw files cached in
`data/raw/bls_qcew/{year}/`.

**Version and vintage.** Annual averages 2014 (the first year in the open data files) through 2025
(the latest annual file; 2026 is not out). Ohio statewide values come from the state file, not a
sum of counties.

**Coverage.** Covers about 95% of U.S. jobs: workers under state unemployment insurance and federal
civilian workers. It leaves out the self-employed, some farm and household workers, unpaid family
workers, railroad workers, and members of the armed forces. A job is a filled position, so a person
with two jobs counts twice.

**Changes over time.** NAICS was revised in 2017 and 2022. The 2022 revision merged retail
industries (for example, gas stations moved from 447 to the new 457), so a 3-digit industry may not
exist in every year. `top_industry_share` picks the largest industry in each year, so its series can
switch industries from one year to the next.

**Suppressed, censored or masked values.** BLS withholds a cell (`disclosure_code` "N", values 0)
when it could reveal a single employer. We store these as missing, never zero. A sector with no row
at all has no covered employers, and we treat that as a true zero. Withholding in 2025, as a share
of each county's private jobs:
- Supersectors (11 groups): median 0%, highest 32%, 4 counties above 20%.
- 2-digit sectors: median 10%, highest 69%, 27 counties above 20%.
- 3-digit industries: median 19%, highest 81% (Morgan County), 42 counties above 20%.

Health care and social assistance (NAICS 62) is withheld in 28 counties and manufacturing in 4 for
2025; those values are null with flag "suppressed".

**Missing data.** Withheld cells only. The share of private jobs in withheld cells is stored per
county in `extras.suppressed_share` (computed as private jobs minus the sum of disclosed cells at
that level).

**Revisions.** BLS revises the most recent quarters when it publishes the next ones; annual files
for earlier years rarely change.

**Units and rounding.** Jobs are annual averages of 12 monthly counts. Wages are dollars per week,
not adjusted for inflation. Shares are percent of private jobs, 0 to 100.

**Known quirks and our methods.**
- `private_jobs`: own_code 5, industry 10 (agglvl 71 county, 51 state).
- `avg_weekly_wage`: all ownerships, industry 10 (agglvl 70 county, 50 state). Nominal dollars.
- `manufacturing_share`, `health_care_share`: private NAICS 31-33 and 62 at the 2-digit sector
  level (agglvl 74 county, 54 state) divided by private jobs.
- `top_industry_share`: the largest disclosed private 3-digit NAICS industry (agglvl 75 county,
  55 state; 76 is 4-digit) as a share of private jobs. A withheld industry could be larger, so the
  value is a floor. When more than 20% of private jobs sit in withheld 3-digit cells, the flag says
  how much.
- `concentration_hhi`: Herfindahl index, the sum of squared percent shares of private jobs across
  NAICS supersectors (agglvl 73 county, 53 state; codes 1011-1029, including 1029 unclassified).
  We chose supersectors because they are withheld far less than 2-digit sectors. Computed on
  disclosed supersectors only, so it reads low where cells are withheld; flagged above 20%.
- `extras.industry_mix`: 2025 private 2-digit sectors with jobs, share, weekly wage, 2014 jobs
  (`jobs_first`) and a `suppressed` marker, sorted by jobs.
- `extras.top3`: the three largest disclosed private 3-digit industries in 2025.
- `extras.location_quotient`: county share of private jobs in a 2-digit sector divided by Ohio's
  share, 2025, disclosed sectors only. Above 1 means the county has more of that sector than Ohio.
  The file's own `lq_` columns compare with the U.S., so we compute the Ohio version ourselves.

**Uncertainty.** QCEW is a near-census of covered employers, not a sample, so BLS publishes no
error ranges. Errors come from employers coded to the wrong county or industry, and from a firm
reporting all its workers at one site.

**License and attribution.** Public domain U.S. government data. Credit: U.S. Bureau of Labor
Statistics, Quarterly Census of Employment and Wages.
