# Datasets

One section per dataset, written before the analysis and kept current. Layer files in `data/processed/` follow `docs/LAYER_CONTRACT.md`. Built page: `dist/index.html` (from `scripts/90_build.py`).

## Ohio county outlines (Census Bureau, via us-atlas)

**What it is.** Census cartographic boundary file for U.S. counties at 1:10,000,000 scale, published as TopoJSON by the us-atlas project (version 3). We keep the 88 Ohio counties and draw them as SVG paths (`scripts/05_geo.py`).

**Known quirks.** The 1:10m generalization smooths the Lake Erie shore and the Ohio River. Good for a statewide map, not for measuring area.

**License and attribution.** Census boundary files are public domain; us-atlas is ISC licensed.


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


Built by `scripts/20_acs.py`.

## American Community Survey 5-year estimates (U.S. Census Bureau)

**What it is.** Survey-based estimates of income, poverty, housing costs, schooling, health insurance and
disability for every Ohio county and the state. Each 5-year estimate pools survey responses collected
over five calendar years. It describes the period as a whole, not its last year.

**Where it comes from.** Census Data API, `https://api.census.gov/data/<year>/acs/acs5`, detailed tables,
pulled whole with `get=group(<table>)` for `for=county:*&in=state:39` and `for=state:39`. Free key
required. Raw responses are cached in `data/raw/census/`; table metadata (line labels) in
`data/raw/census/groups/`.

**Version and vintage.** Three non-overlapping periods: 2010-2014, 2015-2019 and 2020-2024 (released
December 2025). Overlapping 5-year periods share years of data, so only non-overlapping ones are used for
trends.

**Coverage.** All 88 counties and Ohio. Ohio values come from the Census Bureau's own state estimate, not
a sum of counties. Tables used:

| Metric | Table and lines | Universe |
|---|---|---|
| median_household_income | B19013_001 | Households |
| poverty_rate | C17002 lines 2-3 / line 1 | People whose poverty status is determined |
| near_poverty_share | C17002 lines 4-7 (1.00 to 1.99 ratio) / line 1 | Same |
| below_200_share | C17002 lines 2-7 / line 1 | Same |
| snap_households_share | B22003_002 / B22003_001 | Households |
| gini | B19083_001 | Households |
| extras.income_distribution | B19001 lines 2-17 / line 1, each period | Households |
| extras.poverty_ratio_bands | C17002 lines 2-8 / line 1, 2020-2024 | People whose poverty status is determined |
| population | B01003_001 | Total population |
| median_age | B01002_001 | Total population |
| bachelors_or_higher | B15003 lines 22-25 / line 1 | Age 25 and older |
| hs_or_higher | B15003 lines 17-25 / line 1 | Age 25 and older |
| rent_burden | B25070 lines 7-10 / (line 1 minus line 11, not computed) | Renter-occupied units paying cash rent |
| owner_cost_burden | B25091 lines 8-11 / (line 2 minus line 12, not computed) | Owner-occupied units with a mortgage |
| medicaid_share | C27007, lines labeled "With Medicaid/means-tested public coverage" / line 1 | Civilian noninstitutionalized population |
| uninsured_acs | B27010, lines labeled "No health insurance coverage" / line 1 | Civilian noninstitutionalized population |
| disability_share | B18101, lines labeled "With a disability" / line 1 | Civilian noninstitutionalized population |

The poverty universe leaves out people in institutions, college dorms and military group quarters, and
children under 15 who are not related to anyone in the household.

**Changes over time.** Every table above exists in all three periods with the same line numbers. Two
label changes: C27007 age groups were "Under 18 / 18 to 64" in 2010-2014 and "Under 19 / 19 to 64" from
later years on; the all-ages total used here is not affected. Label text gained trailing colons in newer
vintages. The script finds the Medicaid, uninsured and disability lines by label so a renumbering would
not silently break a sum. The 2010-2014 health insurance figures mostly predate Ohio's Medicaid expansion
(January 2014). The 2020-2024 period includes 2020, when the Census Bureau collected fewer responses than
usual because of the pandemic.

**Suppressed, censored or masked values.** The API returns large negative codes (for example -666666666)
where an estimate cannot be computed; the script turns them into null with flag "suppressed". None
occurred for Ohio counties in these tables. Medians are top-coded (household income at $250,000+); no Ohio
county comes near that. A margin of error of -555555555 means the value is controlled to the population
estimates and has no sampling error; it is stored as 0 in sums.

**Missing data.** All 88 counties have all metrics for all three periods.

**Revisions.** The Census Bureau does not revise published ACS 5-year estimates. We pin these three
periods.

**Units and rounding.** Shares are percents (0-100) at full precision. Dollar values are nominal: each
period is in dollars of its final year (2014, 2019, 2024), with no inflation adjustment in the data. The page's
income-distribution chart moves each period's bracket edges into 2024 dollars with R-CPI-U-RS (see "Price
index" below), so the three periods compare in real terms. A switch shows the as-published dollars instead. Median household
income tiles stay nominal and say so.

**Known quirks.** The poverty line is a single federal measure that does not change with local living
costs. Near-poverty and below-200% counts are people, not households or families. Survey answers tend to
undercount SNAP and Medicaid use compared with program records.

**Uncertainty.** Each latest value carries a 90% margin of error in `moe`. Single-line values use the
published MOE. Derived shares use the Census Bureau's approximation for proportions: MOE of a sum of lines
is the square root of the sum of squared line MOEs, and MOE of a share p = X/Y is
sqrt(MOE_X^2 - p^2 x MOE_Y^2) / Y, using a plus sign when the term under the root is negative. These are
approximations; for sums of many lines (high school or higher adds nine lines) they tend to run larger than
the published subject-table MOE. A latest value is flagged "high_moe" when its coefficient of variation
(MOE / 1.645 / estimate) is above 30%. In 2020-2024 only Noble County's rent burden (23.1%, plus or minus
12.4 points) crosses that line. Housing-cost measures in small counties are the least precise: the median
county's rent burden MOE is about 5.6 points. Historic `series` values carry no MOE.

**License and attribution.** Public domain U.S. government data. Credit: "U.S. Census Bureau, American
Community Survey 5-year estimates."


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


Built by `scripts/30_health.py` into `data/processed/health.json`. Raw pulls are cached under
`data/raw/census/`, `data/raw/cdc/` and `data/raw/census_pep/`. Pulled 2026-11-09.

## Age structure and fertility (U.S. Census Bureau: Population Estimates Program and ACS table B23001)

**What it is.** Four measures built in `scripts/23_age.py`:
- Residents 25 to 54 and residents 65 and older, as shares of all residents, July 1 of 2020 to 2025.
- Prime-age workers: people 25 to 54 with a job (civilian employed plus armed forces) as a share of all
  people 25 to 54, from ACS 5-year table B23001, for 2010-2014, 2015-2019 and 2020-2024.
- Fertility rate: births per 1,000 women ages 15 to 44 (the general fertility rate), for years ending June 30,
  2021 to 2025.

**Where it comes from.** County characteristics by age and sex, Vintage 2025,
https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/asrh/cc-est2025-agesex-39.csv
(YEAR 1 is the April 1, 2020 base and is dropped; YEAR 2 to 7 are July 1, 2020 to 2025). Births are
BIRTHS2021 to BIRTHS2025 from co-est2025-alldata.csv (the same file as the population estimates section).
B23001 comes from the Census Data API with `group(B23001)`.

**Method.** Prime-age share sums the six five-year groups from 25-29 through 50-54. The fertility rate divides
births in the year ending June 30 by the average of the July 1 counts of women 15 to 44 at the start and end
of that year. The age file has no state row; Ohio is the sum of its 88 counties, which in the estimates
program equals the state total (the script checks that county births sum to the state's births). B23001 lines
are found by label; the 2014 table labels the armed forces line "In Armed Forces", later years "Armed Forces".

**Changes over time.** The B23001 universe is people 16 and older, including people in group quarters (prisons,
nursing homes, college dorms), so a county with a large prison or college reads lower on prime-age work than
its household population would. The page flags every county where 5% or more of residents live in group
quarters (ACS 2020-2024 B26001 over B01003).

**Uncertainty.** Estimates-program figures carry no margin of error and are revised back to 2020 with each new
vintage. Births for the latest year are partly estimated by the Census Bureau and revised the next year. B23001
shares carry a 90% margin of error by the Census approximation for proportions (Pike County, 2020-2024: 70.8%
±4.1 points).

**Why not births per woman.** The total fertility rate (births per woman over a lifetime) is not published by
CDC for counties under 100,000 people, so it cannot cover all 88 counties. The general fertility rate can.

**License and attribution.** U.S. government work, public domain. Credit the U.S. Census Bureau.

## Small Area Health Insurance Estimates, SAHIE (U.S. Census Bureau)

**What it is.** Model-based estimates of the share of people without health insurance, by county and state, for each year. We use people under 65, both sexes, all races, at two income levels: all incomes (`uninsured_under65`) and at or below 200% of the poverty line (`uninsured_under65_low_income`).

**Where it comes from.** Census Data API, `https://api.census.gov/data/timeseries/healthins/sahie`, JSON, free key. Query: `AGECAT=0` (under 65), `IPRCAT=0` (all incomes) or `IPRCAT=1` (at or below 200% of poverty), `SEXCAT=0`, `RACECAT=0`, `for=county:*&in=state:39` and `for=state:39`. Fields: `PCTUI_PT` (percent uninsured), `PCTUI_MOE` (90% margin of error), `PCTUI_LB90`/`PCTUI_UB90`.

**Version and vintage.** One release per year, about two years after the reference year. The API held 2006 through 2024 at pull time.

**Coverage.** All 88 Ohio counties and Ohio, 2008 through 2024. The estimates combine the American Community Survey (ACS) with administrative records (federal tax returns, SNAP, Medicaid and CHIP enrollment) and population estimates in a statistical model. No county value is a direct survey count.

**Changes over time.** We start in 2008. SAHIE for 2006 and 2007 was built on a different survey base and Census says it is not comparable with 2008 and later. The 2020 ACS had low response during the pandemic, and Census changed its methods for 2020 estimates; treat 2020 with extra care.

**Suppressed, censored or masked values.** None found for Ohio counties at these categories.

**Missing data.** None found.

**Revisions.** Census does not revise earlier years when a new year is released. Each year is its own model run.

**Units and rounding.** Percent, published to one decimal. The margin of error is a 90% margin in percentage points.

**Known quirks.** The low-income category uses income relative to the poverty line, so its population changes as incomes and poverty thresholds change.

**Uncertainty.** Margins in small counties run about 1 to 4 points for the low-income rate. Year-to-year changes smaller than the margin may not be real.

**License and attribution.** Public domain. Credit: U.S. Census Bureau, Small Area Health Insurance Estimates.

## VSRR Provisional County-Level Drug Overdose Death Counts (CDC, National Center for Health Statistics)

**What it is.** For each county, the number of drug overdose deaths of county residents in the 12 months ending in each month. We keep one point per December plus the latest month (`overdose_deaths_12mo`), and the full monthly run in `extras.overdose_12mo_monthly`. We also compute a rate per 100,000 (`overdose_rate_per100k`).

**Where it comes from.** data.cdc.gov Socrata dataset `gb4e-yj24`, filtered `st_abbrev='OH'`. Field `provisional_drug_overdose` is the 12-month count; `monthendingdate` is the end of the period; `footnote` marks suppression. The Ohio figure comes from the state file, dataset `xkb8-kh2a`, indicator "Number of Drug Overdose Deaths", period "12 month-ending", field `data_value`.

**Version and vintage.** County file data as of 2026-10-04; periods ending January 2020 through March 2026. CDC updates it quarterly. The state file runs about two months further (May 2026 at pull time); we use only the months the county file has.

**Coverage.** All 88 counties, 75 monthly periods each. Drug overdose deaths are deaths with an underlying cause coded ICD-10 X40-X44, X60-X64, X85 or Y10-Y14 (accidental, suicide, homicide and undetermined intent).

**Changes over time.** None noted in the file for this period.

**Suppressed, censored or masked values.** CDC hides counts from 1 to 9. We store them as null with flag "suppressed (1-9 deaths)". At the latest period, 45 of 88 counties are suppressed; 50 counties are suppressed in at least one kept period. A published 0 is kept as 0. Because of suppression, county counts do not add up to the state total.

**Missing data.** No missing values beyond suppression.

**Revisions.** Provisional. Counts rise as delayed records and pending investigations come in, most for the latest months. Each refresh replaces the whole series. CDC also gives a percentage of records pending investigation (field `percentage_of_records_pending`), which we did not use.

**Units and rounding.** Deaths, whole numbers. The rate is our calculation: count divided by the Census July 1 county population for the year the period ends, times 100,000. Periods ending in 2026 use the 2025 population. Population file: Census Bureau county population estimates, vintage 2025, `co-est2025-alldata.csv` from www2.census.gov. The rate is not age-adjusted.

**Known quirks.** The county file counts by county of residence. The state file counts deaths that occurred in Ohio, so the Ohio figure is not the sum of counties. The state file marks its most recent months "Underreported due to incomplete data." CDC's file description notes that provisional counts are reported with a 6-month lag.

**Uncertainty.** No error bars. Small counts swing a lot from year to year; a rate based on 10 to 20 deaths is unstable.

**License and attribution.** Public domain. Credit: CDC, National Center for Health Statistics, National Vital Statistics System, provisional mortality data.

## PLACES: Local Data for Better Health, County Data (CDC)

**What it is.** Model-based estimates of the share of adults with a health condition, behavior, care use, or social need, by county. We use the age-adjusted prevalence for ten measures: depression (`DEPRESSION`), frequent mental distress (`MHLTH`), diagnosed diabetes (`DIABETES`), obesity (`OBESITY`), current cigarette smoking (`CSMOKING`), lack of health insurance among adults 18 to 64 (`ACCESS2`), routine checkup in the past year (`CHECKUP`), food insecurity (`FOODINSECU`), housing insecurity (`HOUSINSECU`), and lack of reliable transportation (`LACKTRPT`).

**Where it comes from.** data.cdc.gov Socrata dataset `swc5-untb` ("PLACES: Local Data for Better Health, County Data, 2025 release"), filtered `stateabbr='OH'` and `datavaluetypeid='AgeAdjPrv'`. Fields: `data_value`, `low_confidence_limit`, `high_confidence_limit`, `locationid` (county FIPS), `year`.

**Version and vintage.** 2025 release. All ten measures use 2023 survey data. CDC releases PLACES about once a year.

**Coverage.** All 88 counties; no Ohio row. The estimates come from the CDC Behavioral Risk Factor Surveillance System (BRFSS) survey, using a multilevel regression model with Census population data to estimate each county. They are not counts and not direct survey results for the county.

**Changes over time.** We keep only the latest release. PLACES changes measures and methods between releases, so values from different releases should not be compared as a trend. The social needs measures (food, housing, transportation) are newer additions to PLACES.

**Suppressed, censored or masked values.** None found for these measures in Ohio.

**Missing data.** None.

**Revisions.** Each release replaces the last.

**Units and rounding.** Percent of adults 18 and older (18 to 64 for the insurance measure), one decimal. The 95% confidence interval is in `extras.places_ci95` as [low, high].

**Known quirks.** No state figure in the county file. The page compares each county with the median of Ohio's 88 counties instead, labels it "median county", and leaves these measures out of the overview count. The PLACES insurance measure (adults 18 to 64, survey-based) differs from the SAHIE rate (under 65, Census model); expect them to disagree.

**Uncertainty.** Model-based. Counties with similar population makeup get similar estimates, so real local differences can be muted.

**License and attribution.** Public domain. Credit: Centers for Disease Control and Prevention, PLACES.

## Small Area Income and Poverty Estimates, SAIPE (U.S. Census Bureau)

**What it is.** Model-based annual estimates of the poverty rate for all ages (`saipe_poverty_rate`), the poverty rate for children 0 to 17 (`saipe_child_poverty_rate`), and median household income (`saipe_median_income`), by county and state.

**Where it comes from.** Census Data API, `https://api.census.gov/data/timeseries/poverty/saipe`, JSON, free key. Fields: `SAEPOVRTALL_PT`/`_MOE`, `SAEPOVRT0_17_PT`/`_MOE`, `SAEMHI_PT`/`_MOE`.

**Version and vintage.** One release per year, about a year after the reference year. We use 2000 through 2024.

**Coverage.** All 88 counties and Ohio, every year 2000 to 2024. The model combines survey data with federal tax return data, SNAP counts and population estimates. Since 2005 the survey base is the ACS; before that it was the Current Population Survey.

**Changes over time.** The switch from the CPS to the ACS in 2005 can shift levels; read changes across 2004 to 2005 with care. The 2020 ACS had low response during the pandemic and Census changed its methods for 2020.

**Suppressed, censored or masked values.** None found.

**Missing data.** None found for Ohio counties in 2000 to 2024.

**Revisions.** Earlier years are not revised.

**Units and rounding.** Poverty rates in percent, one decimal. Median income in dollars of each year, not adjusted for inflation. The margins are 90% margins of error.

**Known quirks.** These are a single value per year, unlike ACS 5-year estimates, which average five years. SAIPE and ACS values for the same county and year will differ.

**Uncertainty.** Margins are wide in small counties, for example about 7 points on the child poverty rate in Vinton County in 2024.

**License and attribution.** Public domain. Credit: U.S. Census Bureau, Small Area Income and Poverty Estimates.


## Price index, R-CPI-U-RS (U.S. Bureau of Labor Statistics)

**What it is.** The Consumer Price Index retroactive series, all items, U.S. city average, not seasonally
adjusted, December 1977 = 100. It applies today's CPI methods to past years, and it is the index the Census
Bureau uses to compare household income across years.

**Where it comes from.** https://www.bls.gov/cpi/research-series/r-cpi-u-rs-allitems.xlsx, one sheet,
monthly values plus an annual average column. `scripts/22_prices.py` keeps the annual averages.

**How we use it.** ACS 5-year dollars are in the final year of the period. To put a 2010-2014 bracket edge in
2024 dollars we multiply it by index(2024) / index(2014) = 462.511 / 347.7 = 1.3302; for 2015-2019, by
462.511 / 375.813. Only the income-distribution chart uses it.

**Known quirks.** October 2025 is missing because of the 2025 lapse in appropriations; BLS computed the 2025
annual average from 11 months. We use only 2014, 2019 and 2024.

**Revisions.** The research series is revised each year when BLS updates it; we pull the current file.

**License and attribution.** U.S. government work, public domain. Credit the U.S. Bureau of Labor Statistics.
