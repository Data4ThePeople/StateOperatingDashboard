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

Built by `scripts/42_enrollment.py` into `data/processed/enrollment.json`. Raw files are cached under
`data/raw/fns/`. Pulled 2026-11-09. This layer has SNAP only. County Medicaid enrollment is not in it.

## SNAP county participation, form FNS-388A (USDA Food and Nutrition Service)

**What it is.** For each SNAP project area (in Ohio, a county agency), the number of people and households that got SNAP benefits in January and in July, plus the dollars issued. We use "Calc: SNAP Total PA and Non-PA People," the sum of people in households that also get cash aid (PA) and those that do not (non-PA). The metric `snap_persons_share` is that count divided by the Census July 1 population of the same year, times 100. The counts are in `extras.snap_persons_count`.

**Where it comes from.** FNS SNAP Data Tables page, `https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap`, section "Bi-Annual (January and July) State Project Area/County Level Participation and Issuance Data." File `https://www.fns.usda.gov/sites/default/files/resource-files/snap-zip-fns388a-2.zip` (14.8 MB zip, "FY 89 through July 2025"), one Excel sheet per month: `.xls` through 2019 and January 2021, `.xlsx` from January 2020. No login. FNS returned HTTP 403 to the script's Python request on 2026-11-09, so the zip was saved with curl to `data/raw/fns/` and the script reads it from there.

**Version and vintage.** The zip held January 1989 through July 2025 at pull time. The July 2025 sheet is dated 2026-02-12. FNS says January data is reported to it in May and July data in December, so the newest county month is about 16 months old by the time it is posted.

**Coverage.** All 88 Ohio counties appear as project areas, coded `39` + county FIPS + a two-digit office number. We use July 2021 through July 2025, one point per July. The population estimates run 2020-2025, and each July count is matched to the July 1 estimate of the same year, so the dates line up. These are counts from program records, not estimates.

**Changes over time.** Hocking, Ross and Vinton are served by one agency, South Central Ohio Job and Family Services. In every file from January 2020 on, nearly all of their cases sit on the Ross line (20,616 people in July 2025); the Hocking and Vinton lines hold between 0 and 42 people. We do not report a share for any of the three. They carry `null` with a flag, and `extras.snap_south_central_combined` holds one share for the three counties together (17.7% in July 2025). We did not check when this grouping began. Defiance and Paulding also share one agency, but FNS still reports them on separate lines with plausible counts, so we keep both.

**Suppressed, censored or masked values.** None. A few blank household cells appear (for example Vinton households in January 2025); the persons column has a number for every Ohio line in the years we use.

**Missing data.** None in the persons column for 2021-2025.

**Revisions.** FNS marks every sheet "Data is Subject to Revision. The data reflected is the latest available data." It replaces sheets in the zip when it revises; file dates inside the zip range from 2012 to 2026. We refresh the whole series by re-downloading the zip.

**Units and rounding.** People, whole numbers. The share is our calculation, stored at full precision.

**Known quirks.**
- Cuyahoga has two lines: the regular EBT office and an "SSI" line (6,504 people in July 2025), which we take to be SNAP for SSI recipients who apply through Social Security. We add them. With both lines included, the 88 counties add exactly to the FNS Ohio state total in every July from 2021 to 2025.
- July 2020 is left out. Ohio's statewide count that month (1,538,558) is about 10% above June 2020 (1,403,021) and August 2020 (1,399,895), and the county sheet shows the same jump. FNS does not explain it. Keeping it would make 2020 to 2021 look like a large drop.
- The count is by the county agency that handles the case. That is usually the county where the household lives.

**Uncertainty.** No error bars; these are administrative counts. As a cross-check, Ohio's own monthly report (ODJFS Public Assistance Monthly Statistics, Caseload Summary Statistics Report, July 2025, `https://dam.assets.ohio.gov/image/upload/jfs.ohio.gov/PRC/CaseloadSummaryReportJuly2025.pdf`) counts "individuals in receipt" a little lower than FNS: 1,389,247 statewide versus 1,446,062 (3.9% lower), and 163,303 in Franklin versus 170,410 (4.2% lower). The Ohio report combines Hocking, Ross and Vinton as "South Central" (20,036 versus 20,662 from FNS) and Defiance with Paulding (5,804 versus 6,013). We did not find a published reason for the gap.

**License and attribution.** Public domain. Credit: USDA Food and Nutrition Service, SNAP Data Tables.

## SNAP monthly state participation (USDA Food and Nutrition Service)

**What it is.** Monthly SNAP households, persons and benefit cost by state, one Excel file per fiscal year (October to September). We use Ohio's "Persons" column for the Ohio figure.

**Where it comes from.** Same FNS page, file `https://www.fns.usda.gov/sites/default/files/resource-files/snap-zip-fy69tocurrent-10.zip` (1.7 MB), files `FY20.xlsx` through `FY26.xlsx`, Ohio block on the `MWRO` sheet. Saved with curl to `data/raw/fns/` for the same reason as above.

**Version and vintage.** The FY23 to FY26 files are dated 2026-10-07 inside the zip; the sheet header reads "Data as of October 9, 2026." Ohio runs through July 2026.

**Coverage.** Ohio, every month from October 2019 to July 2026. The sheet title says P-EBT (pandemic school meal benefits) and "other" are excluded. The full monthly run is in `extras.snap_persons_ohio_monthly`.

**Changes over time.** None noted for 2019-2026.

**Suppressed, censored or masked values.** None. August and September 2026 show "--" (not yet reported) and are dropped.

**Missing data.** Only the not-yet-reported months above.

**Revisions.** FNS's state persons table says the latest two months are preliminary and "subject to significant revision." The July values we use are at least 15 months old.

**Units and rounding.** People, whole numbers.

**Known quirks.** The state persons table notes that the data "may include disaster assistance." The July 2020 spike described above is in this file too.

**Uncertainty.** No error bars.

**License and attribution.** Public domain. Credit: USDA Food and Nutrition Service, SNAP Data Tables.

## Population denominator

Census Bureau county and state population estimates, vintage 2025, as built in `data/processed/popest.json` (metric `population_estimate`, July 1, 2020-2025). See `docs/datasets/popest.md`. Each July SNAP count is divided by the July 1 estimate of the same year.

Built by `scripts/41_childcare.py`.

## Licensed early care and education programs (Ohio Department of Children and Youth)

**What it is.** A list of early care and education programs in Ohio, one row per program, with its county,
program type, status, address and Step Up To Quality rating. It is the data behind DCY's Step Up To Quality
program locator map. We count the licensed programs that are open in each county.

**Where it comes from.** State of Ohio ArcGIS layer `Ohio_Daycares_view`:
`https://maps.ohio.gov/arcgis/rest/services/Hosted/Ohio_Daycares_view/FeatureServer/0` (portal item
`e7b80e83d8764427b5de7fde6f67f83d`, title "Ohio Daycare Centers", owner `oitogrip`). Queried as JSON through
the public ArcGIS REST query endpoint, 1,000 records per request. No login. Each row links to the program's
page on Ohio Child Care Search (`https://childcaresearch.ohio.gov/provider/<number>`). Saved at
`data/raw/dcy/ohio_daycares_<pull date>.json`.

**Version and vintage.** The item description says the layer is updated weekly. It keeps no history: each
update replaces the list. The portal item was last modified October 21, 2026; we pulled it November 9, 2026
(8,707 rows). Values are a snapshot on the pull date, so `series` has one point.

**Coverage.** All 88 counties. We keep five licensed program types: child care centers (4,242 open), family
child care Type B homes (1 to 6 children; 1,635), preschools (1,494), family child care Type A homes (7 to 12
children; 335) and school-age child care (241), for 7,947 in all. "Open" includes 17 programs whose status is
"Enforcement" (licensed, under an enforcement action). We drop 392 inactive programs of these five types,
288 day camps (registered with the state, not licensed), 17 certified in-home aides and 63 out-of-state
programs registered to take Ohio subsidy. Preschools and school-age programs run by school districts,
nonpublic schools, county developmental disabilities boards and community schools used to be licensed by the
Ohio Department of Education; DCY's SFY 2025 licensing report lists them among the program types DCY now
licenses. The layer has no
licensed capacity (number of children a program may serve), no ages served and no enrollment.

**Fields used and metrics built.**

| Metric | Built from |
|---|---|
| childcare_providers | Count of rows per `county` where `program_type` is one of the five licensed types and `program_status` is Open or Enforcement |
| extras.providers_by_type | The same count split by `program_type` |

County names in the layer are matched to FIPS codes using the Census Bureau county names. Every licensed,
open program matched a county.

**Changes over time.** Not applicable to a single snapshot. DCY's own yearly totals use a different basis:
the SFY 2025 licensing report counts 8,950 programs licensed at any time from July 1, 2024 to June 30, 2025
(4,586 centers, 397 Type A, 2,111 Type B, 1,539 preschools, 317 school-age). Our point-in-time count is lower
because programs that closed during the year are not in today's list.

**Suppressed, censored or masked values.** None. Type B homes are listed under the provider's name.

**Missing data.** 993 Type B homes and 26 out-of-state programs have no program number. Each still has a
unique provider link, which we use as the record key. No licensed, open program lacks a county.

**Revisions.** The list is replaced weekly. We keep the dated snapshot and reuse it on later runs; pass
`--refresh` to pull a new one.

**Units and rounding.** Programs, as whole numbers. Ohio is the sum of the 88 counties, because the state does
not publish a point-in-time total on the same basis.

**Known quirks.** A program counts once regardless of size: a six-child Type B home and a 300-child center
each count as one. One school building can hold two licenses, a preschool and a school-age program, and then
counts twice (Vinton County's 8 programs are 1 Head Start center, 3 school preschools and 4 school-age
programs at the same or nearby school buildings). Program type labels use the layer's spelling ("Pre School").

**Uncertainty.** None published. The state's license text says the layer is provided "as is" without a
guarantee that it is complete or error free.

**License and attribution.** State of Ohio geospatial data, public use. Credit: "Ohio Department of Children
and Youth, licensed early care and education programs, via the State of Ohio GIS (maps.ohio.gov)."

Built by `scripts/43_crime.py` into `data/processed/crime.json`. Raw files are cached under
`data/raw/fbi_cde/`. Pulled 2026-11-09.

Metrics: `violent_crime_rate` and `property_crime_rate`, per 100,000 people, 2015 through 2025.
The owner asked for "petty crime." The FBI has no category by that name; property crime
(burglary, larceny-theft, motor vehicle theft) is the closest standard category.

## Return A master files (FBI Uniform Crime Reporting Program)

**What it is.** One fixed-width record per law enforcement agency per year. Each record holds the agency's population, the counties it serves, and for each month the count of offenses known to police ("actual" offenses, after unfounded reports are removed) for the Part I crimes. We use murder and nonnegligent manslaughter, rape, robbery and aggravated assault (violent), and burglary, larceny-theft and motor vehicle theft (property).

**Where it comes from.** FBI Crime Data Explorer (CDE), Documents and Downloads, Master Files, "Return A". The page asks `https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=master_files/reta/reta-<year>.zip` for a short-lived download link. No key or login. One zip per year, about 6 MB, holding one text file (about 195 MB) for the whole country. Ohio rows have UCR state code 34. The record layout comes from the FBI's "Ret A Rec Descrip.pdf" (in `reta-help.zip`, a scanned image) and matches the public setup file by Jacob Kaplan (`jacobkap/crime_data`, `setup_files/ucr_return_a.sps`). Header: ORI in columns 4-10, population group 11-12, "covered by" ORI 24-30, three population and county pairs in 45-89. Months start at column 306, 590 columns each; within a month, columns 3-8 are the date of last update and the actual-offense card starts at column 158 of the block.

**Version and vintage.** The 2025 file is dated 2026-05-07. The CDE site says its crime data were refreshed 2026-10-15, so the website can show counts a little higher than the master file. Example: Columbus Police, 2025 violent crime, 3,517 in the master file and 3,590 on the CDE agency page (most of the gap is rape, 987 vs. 1,040). Vinton County Sheriff: 21 vs. 22 violent, 40 vs. 40 property.

**Coverage.** 2015 through 2025. Ohio has about 950 agencies in each file. About half of them sent all 12 months in a given year. Statewide, agencies that sent all 12 months served 84.7% to 90.4% of Ohioans, depending on the year (86.3% in 2025).

How we build a county figure:

- **Reported month.** A month counts as reported when the record shows a nonzero date of last update, or an actual-offense card marked as sent. We checked this against the participation numbers on the CDE agency pages for 24 Ohio agencies in 2019, 2021 and 2025: 859 of 864 agency-months agreed. In the other 5, the CDE page showed a report that the master file did not.
- **Full-year agencies only.** An agency counts toward a county's rate only if it reported all 12 months. We do not fill in missing months.
- **County assignment.** The FBI codes each agency's population to up to three counties. UCR county codes number Ohio's counties A to Z (1 = Adams, 88 = Wyandot), so FIPS = 2 x code - 1. We use the FBI's county fields, not our own geography.
- **Agencies spanning counties.** 54 Ohio agencies had population in more than one county in 2025 (Columbus covers parts of Franklin, Delaware and Fairfield). We split the population as the FBI does. The FBI does not split offenses by county, so we split them in the same shares as the population. This assumes crime is spread evenly across an agency's area.
- **Agencies covered by another agency.** Some small departments do not report on their own; a sheriff or nearby city reports for them. The FBI puts their offenses and their population in the covering agency's record, so we skip the covered agency to avoid counting it twice. With this rule, the FBI's county populations add up to the Census estimate for Ohio exactly in 2025 (11,900,510), and each county is within 2.3% of its Census estimate.
- **Agencies with no resident population.** Campus police, park districts, airport police and drug task forces have population 0. Their offenses count in the county the FBI codes them to, if they reported all 12 months. They add crimes but no people, so they raise a county's rate a little.
- **State police and statewide agencies.** The Ohio State Highway Patrol (population groups 8E and 9E, and ORIs starting OHOHP), statewide state agencies such as the Bureau of Criminal Investigation and Department of Natural Resources, and federal agencies (U.S. Marshals, Secret Service, National Park Service units) are left out of county figures. Some have no county code. Others are coded to the county of a post or headquarters, not where the crimes happened.
- **Rate.** Offenses of full-year agencies divided by the population those same agencies serve, times 100,000. The denominator is the covered population, not the full county.
- **Coverage.** Population served by full-year agencies divided by the population of all agencies coded to the county, as a percent. Stored by year in `extras.coverage`. When it is below 80%, the county value is null with the flag "low reporting (<80% of people covered)".

Counties below 80% coverage, by year: 2015: 22; 2016: 21; 2017: 24; 2018: 21; 2019: 24; 2020: 27; 2021: 31; 2022: 24; 2023: 25; 2024: 22; 2025: 29. The 2025 list includes some large counties (for example Lorain, Mahoning, Greene, Clark, Trumbull and Wood), where a main department sent fewer than 12 months to the FBI in time for the master file.

**Changes over time.** On January 1, 2021, the FBI stopped taking summary (SRS) reports and moved to NIBRS-only collection. Agencies that had not switched to NIBRS had no way to send data for 2021. From 2022 the FBI again accepted SRS reports from agencies that had not switched. Ohio has run its own incident-based system (OIBRS) for many years, so most Ohio agencies were already on NIBRS, and the effect was smaller than in many states: statewide coverage fell from 87.2% in 2020 to 85.3% in 2021, and counties below 80% rose from 27 to 31, then came back to 24 in 2022. Vinton County fell to 12.4% coverage in 2021 and is null that year. For NIBRS agencies, the FBI converts incident reports into Return A counts by applying the Hierarchy Rule (only the most serious offense in an incident counts), so NIBRS and SRS agencies are counted the same way in this file. The FBI broadened its rape definition in 2013 and stopped accepting the old definition in 2017; in 2015 and 2016 a few SRS agencies may still have used the old, narrower definition.

**Suppressed, censored or masked values.** None. Counts are not suppressed. Some monthly cells are negative (an overpunch letter in the last digit, for example `0001J` = -11) when an agency removes offenses reported in an earlier month. We keep them, so yearly sums are net.

**Missing data.** A month with no report looks like a month with zero crimes in the count fields. That is why we use the reporting flags and only full-year agencies. A county value is null when coverage is below 80%.

**Revisions.** Agencies can send late or corrected data. The CDE site updates; the master file for a year is a snapshot. Re-running with a newer master file can change recent years. Delete `data/raw/fbi_cde/reta-<year>.zip` to pull a new copy.

**Units and rounding.** Counts are whole numbers. Rates are our calculation, stored at full precision. Offenses of multi-county agencies are split by population share, so county counts in `extras.crime_counts` can have decimals.

**Known quirks.** Two Ohio ORIs appear twice in the 2020 and later files; we keep the row with more reported months. Big-city ORIs use letters (OHCOP00 is Columbus) and are kept. Agency records with population 0 and no county code are dropped. The "number of months reported" field in the header does not match the monthly flags (it behaves more like the last month reported), so we do not use it.

**Uncertainty.** No error bars. Small counties have small counts: Vinton County's 2025 violent rate rests on 21 offenses, and its rates swing widely from year to year (from 70 to 237 per 100,000 between 2015 and 2025). Rates only cover the people served by full-year agencies; if the agencies that did not report have different crime levels, the county rate is off by an unknown amount.

**License and attribution.** Public domain (U.S. government work). Credit: FBI, Uniform Crime Reporting Program, Return A master files, via the Crime Data Explorer.

## Crime in the United States, state estimates (FBI)

**What it is.** The FBI's estimated number of violent and property crimes for Ohio, and its population, for each year. Used for the Ohio statewide figure.

**Where it comes from.** CDE Documents and Downloads, "Crime in the United States," estimations zip for each edition (`cius/<year>/cius-estimations-<year>.zip`), Table 4 "Crime in the United States by Region, Geographic Division, and State," xlsx. Each edition has two years. We read the 2022 through 2025 editions and keep each year from the latest edition that has it. Rate = estimated count / population x 100,000 at full precision (the table rounds to one decimal).

**Version and vintage.** 2025 edition files dated 2026-08-03.

**Coverage.** Ohio, 2021 through 2025. The FBI publishes estimates for earlier years too, but those editions are old `.xls` files that the project's Python setup cannot read, so the `ohio` series starts in 2021. `extras.ohio_reported_agencies` gives a statewide rate for every year built the same way as the counties (all full-year local agencies); it runs higher than the FBI estimate (for 2025, 293.8 vs. 275.6 violent and 1,513 vs. 1,429 property per 100,000).

**Changes over time.** The FBI estimates crime for agencies that sent fewer than 12 months: for 3 to 11 months it scales up the agency's own data; for fewer than 3 months it uses similar agencies in the state. The 2021 estimates came out as a limited release because national NIBRS participation was low that year.

**Suppressed, censored or masked values.** None for Ohio.

**Missing data.** None for Ohio, 2021 through 2025.

**Revisions.** Each edition can revise the prior year. We use the later edition.

**Units and rounding.** Counts, whole numbers. Published rates to one decimal.

**Known quirks.** Table 4 file names start with `Table_4` in the 2022 and 2023 editions and `CIUS_Table_4` in later ones.

**Uncertainty.** The FBI does not publish error bars for these estimates.

**License and attribution.** Public domain. Credit: FBI, Crime in the United States.

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
| Six race and ethnicity groups, `female_share` | Vintage 2025 state file `sc-est2025-alldata6.csv` (sex, Hispanic origin, six race groups), all ages. Checked: each state's total equals its NST total, and the six groups add to it. U.S.: sum of the 50 states and DC, checked equal to the NST U.S. total | July 1, 2025 |
| `foreign_born_share` | ACS 5-year B05012 for every state; U.S. from the publisher's own U.S. row (us:1) | 2020-2024 |
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

Built by `scripts/40_reading.py` into `data/processed/reading.json`. The ODEW files were downloaded by hand into
`data/raw/odew/`. The script does not fetch them. CCD pulls are cached under `data/raw/urban_ccd/`. Built 2026-11-09.

## School report card achievement files (Ohio Department of Education and Workforce)

**What it is.** One row per traditional public school district (`*_Achievement_District.xlsx`) or per community school building (`*_Achievement_CS.xlsx`). We use one field: the percent of the district's or school's third graders who scored proficient or above on the Ohio State Test in English language arts. ODEW reports it on the report card as a "report only" indicator (`grade3_ela_proficient`).

**Where it comes from.** ODEW report card "Download Data" page, https://reportcard.education.ohio.gov/download, categories "District Data" and "School Building Data". Files:
- `18-19`, `21-22`, `22-23`, `23-24`, `24-25` and `25-26_Achievement_District.xlsx`
- the same years of `_Achievement_CS.xlsx`
- `2026_District_Details.xlsx`, used only to check district counties

The data sheet is `Performance_Indicators` in 2018-19 and `Report_Only_Indicators` from 2021-22 on. The column was named "3rd Grade Reading ... % at or above Proficient" in 2018-19 and "3rd Grade English Language Arts ... Percent Proficient or above" from 2021-22 on. Each file also has the district's or building's value for the year before, and that is where 2017-18 and 2020-21 come from. The download links on the site need an access token that the page adds, so these files were saved by hand.

**Version and vintage.** The files were created between October 2019 (2018-19) and 2026-09-11 (2025-26). Each prior-year column matches the earlier year's own file, except that a few community schools are labeled "NC" in one file and "NA" in the next. Both mean no value. When the two disagree, we keep the value from that year's own file.

**Coverage.** School years 2017-18, 2018-19, and 2020-21 through 2025-26. There was no state testing in 2019-20. The district files cover 607 traditional districts (608 in 2018-19). Joint vocational districts and educational service centers are not in them, and they have no third graders. The community school files cover 246 to 258 buildings. Each row carries ODEW's county, and we use it to place districts and schools. A district that spans counties counts in the one county ODEW lists. The county in `2026_District_Details.xlsx` matches the achievement files for every district. Three community schools changed county between years, and we use each year's own county.

**Changes over time.** Ohio rewrote its report card law in July 2021. From 2021-22 on, the third grade measure is "report only" rather than a graded indicator, and the level names changed ("Accelerated" became "Accomplished"). The underlying measure, proficient or above on the grade 3 ELA test, has the same name in every file. ODEW's Spring 2026 technical summary puts the grade 3 ELA proficient cut at a scale score of 700. We did not confirm the cut for earlier years against ODEW's technical documents, because those documents are behind the same token-gated download.

**Suppressed, censored or masked values.** ODEW prints "NC" (not calculated) when a district or school has too few tested students. ODEW's Early Literacy technical guidance sets the minimum at 10. It prints "NA" (2025-26 file only) for community schools whose grades do not include grade 3.
- No masked value is ever treated as 0. A masked district or school drops out of its county's average.
- To show how much that matters, we count its CCD grade 3 enrollment as "masked enrollment" (`extras.reading_rollup_detail`).
- Statewide, masked enrollment is 0.1% to 0.4% of grade 3 enrollment each year: 323 of about 123,000 in 2025-26.
- Masked districts: Put-In-Bay Local (Ottawa County, most years), Vanlue Local (Hancock County, 2021-22 through 2024-25) and Bloomfield-Mespo Local (2020-21). The rest are small community schools.
- We flag a county when 5% or more of its grade 3 enrollment is in masked cells. No county reaches that in 2025-26. The highest is Harrison at 4.3%.
- Earlier years: Harrison reached 5.4% in 2020-21 and Hocking 5.7% in 2023-24. Those flags are not in the series because the flag field covers only the latest year.

**Missing data.** All 88 counties have a value in every school year. We could not weight two community schools in 2025-26 because CCD had no grade 3 enrollment for them: LINC Academy Columbus and Virtual Preparatory Academy of Ohio. Both are left out.

**Revisions.** ODEW does not reissue these files once the report card is final. We keep each year's own file.

**Units and rounding.** Percent, published to one decimal place, as text, sometimes padded with spaces (2025-26).

**Known quirks.**
- ODEW does not publish the number of students tested in these files. We weight each district and school by its grade 3 fall enrollment from the NCES Common Core of Data (next section). Enrollment is a close stand-in for students tested but is not the same count.
- Online (virtual) community schools are left out of county figures, because their students live all over the state while ODEW lists one county for the school. We take the virtual flag from the CCD school directory, and seven schools are left out (the script prints the names).
- The Ohio figure on the page is the enrollment-weighted sum of the same district and school figures the counties use, for every school year. Counties are compared with a statewide number built the same way.
- ODEW also prints its own state number in the same files, for 2018-19 and 2021-22 through 2025-26. It runs about 2 to 2.5 points below our statewide sum in every year we can compare, with or without the online schools. We think the cause is the students ODEW counts at the state level but not in any one district's or school's result (for example, students who were not enrolled for the full year). We did not confirm this. Both numbers are in `extras.reading_rollup_detail.ohio`, and the page's note gives ODEW's latest figure.
- 2020-21 was tested during the pandemic, and fewer students took the test than usual.

**Uncertainty.** These are counts of all tested students, not a sample, so there is no margin of error. In small counties a single district of 100 to 200 third graders sets the figure, and year-to-year swings of 10 points or more happen (Vinton County went from 64.3% in 2022-23 to 81.4% in 2023-24).

**License and attribution.** Public data. Credit: Ohio Department of Education and Workforce, Ohio School Report Cards.

## Common Core of Data, grade 3 membership and school directory (NCES, via the Urban Institute Education Data Portal)

**What it is.** The number of students enrolled in grade 3 on or near October 1, for each district (local education agency, or LEA) and each school. We use it only as the weight for averaging district and school percentages into a county figure. We also use the school directory's `virtual` flag.

**Where it comes from.** Urban Institute Education Data Portal API, no key:
- `https://educationdata.urban.org/api/v1/school-districts/ccd/enrollment/{year}/grade-3/?fips=39`
- `.../school-districts/ccd/directory/{year}/?fips=39`
- `.../schools/ccd/enrollment/{year}/grade-3/?fips=39`
- `.../schools/ccd/directory/{year}/?fips=39`

We match a district on `state_leaid` = "OH-" plus its ODEW IRN, and a community school on the building IRN at the end of `seasch`.

**Version and vintage.** CCD years 2017 to 2024, where "2024" means fall of the 2024-25 school year. CCD for fall 2025 was not in the API at pull time, so the 2025-26 figures use 2024-25 enrollment. Any district or school with no enrollment in a given year uses its nearest available year.

**Coverage.** All Ohio public districts and schools that report to NCES. We keep the all-students row only (race 99, sex 99). Codes below 0 (missing or not applicable) are treated as no data.

**Changes over time.** None that affect grade 3 counts.

**Suppressed, censored or masked values.** None for grade 3 totals.

**Missing data.** Two 2025-26 community schools are not matched (see above).

**Revisions.** NCES finalizes each year once.

**Units and rounding.** Students, whole numbers.

**Known quirks.** Fall enrollment differs from the spring tested count because of moves, absences and students taking the alternate test. This changes the weights a little. It does not change any district's or school's percentage.

**Uncertainty.** Not applicable.

**License and attribution.** Public domain. Credit: U.S. Department of Education, National Center for Education Statistics, Common Core of Data, via the Urban Institute Education Data Portal.

## Race and ethnicity, sex, and place of birth

**Race, Hispanic origin and sex.** U.S. Census Bureau, Population Estimates Program, Vintage 2025, county
characteristics by age, sex, race and Hispanic origin (`cc-est2025-alldata-39.csv`), all ages, July 1 of 2020
through 2025. Script: `scripts/24_demographics.py`. Ohio is the sum of its 88 counties, since the file has no
state row.

Six groups that do not overlap and add to 100% of residents:
- Hispanic or Latino, of any race (`H`).
- Not Hispanic, by race alone: White (`NHWA`), Black (`NHBA`), Asian (`NHAA`), and American Indian, Alaska
  Native, Native Hawaiian or Pacific Islander (`NHIA` plus `NHNA`, combined because each is under 0.3% in Ohio).
- Not Hispanic, two or more races (`NHTOM`).

The script checks that the six groups add exactly to the total population in every county and year. The
estimates program has no "some other race" group; it assigns those responses to a listed race.

Female share is `TOT_FEMALE` over `TOT_POP`. The Census Bureau counts sex (male or female) and does not publish
gender identity by county.

These are modeled estimates, and each new vintage revises every year back to 2020. All are descriptive: the
page compares them with Ohio but does not call a value better or worse, and none is in the overview or the
Priorities tab.

**Place of birth.** ACS 5-year table B05012 (Nativity in the United States), foreign-born (`B05012_003`) over
total (`B05012_001`), for 2010-2014, 2015-2019 and 2020-2024. Foreign-born means not a U.S. citizen at birth. It
includes naturalized citizens and noncitizens. People born in Puerto Rico or other U.S. territories, or abroad
to U.S.-citizen parents, are native-born. The 90% margin of error uses the Census approximation for proportions.
Negative margin codes are counted as 0.

## Priorities tab: how the page combines measures (derived, not a dataset)

**Gap.** For each judged measure, a county's gap is its distance from Ohio's value, signed so that positive means
worse, divided by Ohio's value or by the spread of the measure across counties (standard deviation), whichever is
larger, and capped at 100%. The spread is used for measures near zero, such as labor force growth since 2019.
Measures with no statewide figure (CDC PLACES) compare with the median county. Prime-age work rates flagged for
group quarters (5% or more of residents in prisons, dorms or nursing homes) are left out of every count.

**Issues.** Ten groups of measures, set in `scripts/90_build.py` (`ISSUES`); an issue keeps only the measures that
are on the page. A county's issue gap is the average of its measure gaps. "Behind" means an issue gap above 3%, the
same "near Ohio" band used on the other tabs.

**By issue.** For each issue: counties behind; residents of those counties (Census estimate, July 1, 2025); the
middle issue gap among those counties; counties that worsened on more of the issue's measures than they improved on
(using the "since 2019 / 10 years" switch; dollar measures left out because they are not adjusted for inflation);
and Ohio against the U.S. on measures with a same-definition state figure (`scripts/50_national.py`). The order is a
weighted average of the five factors, each scaled from 0 (lowest issue) to 1 (highest issue), with weights the
viewer sets. Equal weights by default.

**By place.** Counties ranked by the number of issues they are behind on, then by their average issue gap. County
groups come from k-means clustering (six groups) on each county's issue gaps, started from six counties spread
evenly across the overall gap, so the result is the same on every load. Groups are named by their largest shared
gaps. They describe which problems occur together, not causes.

**Change window.** "Since 2019" compares the latest value with the period ending in 2019 (2015-2019 for ACS
five-year data). "Over 10 years" compares with the period ending ten years before the latest (2010-2014 for ACS).
A source with less history uses its earliest period, and the page names it.
