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
(MOE / 1.645 / estimate) is above 30%. Among this layer's measures, only Noble County's rent burden in
2020-2024 (23.1%, plus or minus 12.4 points) crosses that line. Measures added later with small counts (the
foreign-born share, and on the Well-Being page overcrowding, preschool enrollment and the race groups) cross it in
more counties; the same rule flags them. Housing-cost measures in small counties are the least precise: the median
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
are found by label ("In Armed Forces" in every period; only trailing colons differ).

**Group quarters.** The B23001 universe is people 16 and older, including people in group quarters (prisons,
nursing homes, college dorms), so a county with a large prison can read lower on prime-age work than its
household population would. The page flags every county where 5% or more of residents live in group quarters
(ACS 2020-2024 B26001 over B01003). The flag uses all residents, while the rate covers ages 25 to 54, and dorm
and nursing home residents are mostly outside that age range, so the flag marks a possible effect, not a
measured one. The flag uses 2020-2024 only: Greene, Seneca, Union and Wood were at 5% or more in earlier periods
but not now, so their changes over time compare a base that may be affected with a latest value that is not.

**Changes over time.** None in the B23001 lines used.

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

## SNAP county participation, form FNS-388A (USDA Food and Nutrition Service)

Built by `scripts/42_enrollment.py` into `data/processed/enrollment.json`. Raw files are cached under
`data/raw/fns/`. Pulled 2026-11-09. This layer has SNAP only. County Medicaid enrollment is not in it.

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

## Licensed early care and education programs (Ohio Department of Children and Youth)

Built by `scripts/41_childcare.py`.

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

## Return A master files (FBI Uniform Crime Reporting Program)

Built by `scripts/43_crime.py` into `data/processed/crime.json`. Raw files are cached under
`data/raw/fbi_cde/`. Pulled 2026-11-09.

Metrics: `violent_crime_rate` and `property_crime_rate`, per 100,000 people, 2015 through 2025.
The owner asked for "petty crime." The FBI has no category by that name; property crime
(burglary, larceny-theft, motor vehicle theft) is the closest standard category.

**What it is.** One fixed-width record per law enforcement agency per year. Each record holds the agency's population, the counties it serves, and for each month the count of offenses known to police ("actual" offenses, after unfounded reports are removed) for the Part I crimes. We use murder and nonnegligent manslaughter, rape, robbery and aggravated assault (violent), and burglary, larceny-theft and motor vehicle theft (property).

**Where it comes from.** FBI Crime Data Explorer (CDE), Documents and Downloads, Master Files, "Return A". The page asks `https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=master_files/reta/reta-<year>.zip` for a short-lived download link. No key or login. One zip per year, about 6 MB, holding one text file (about 195 MB) for the whole country. Ohio rows have UCR state code 34. The record layout comes from the FBI's "Ret A Rec Descrip.pdf" (in `reta-help.zip`, a scanned image) and matches the public setup file by Jacob Kaplan (`jacobkap/crime_data`, `setup_files/ucr_return_a.sps`). Header: ORI in columns 4-10, population group 11-12, "covered by" ORI 24-30, three population and county pairs in 45-89. Months start at column 306, 590 columns each; within a month, columns 3-8 are the date of last update and the actual-offense card starts at column 158 of the block.

**Version and vintage.** The 2025 file is dated 2026-05-07. The CDE site says its crime data were refreshed 2026-10-15, so the website can show counts a little higher than the master file. Example: Columbus Police, 2025 violent crime, 3,517 in the master file and 3,590 on the CDE agency page (most of the gap is rape, 987 vs. 1,040). Vinton County Sheriff: 21 vs. 22 violent, 40 vs. 40 property.

**Coverage.** 2015 through 2025. Ohio has about 950 agencies in each file. About half of them sent all 12 months in a given year. Statewide, agencies that sent all 12 months served 84.7% to 90.4% of Ohioans, depending on the year (86.3% in 2025).

How we build a county figure:

- **Offenses.** Violent crime is murder and nonnegligent manslaughter, rape, robbery and aggravated assault. Return A's assault total includes simple assault, so aggravated assault is the assault total minus simple assault. Property crime is burglary, larceny-theft and motor vehicle theft.
- **Reported month.** A month counts as reported when the record shows a nonzero date of last update (including a month with card type 4, "not available", and zero counts), or an actual-offense card of type 5 (submitted). We checked this against the participation numbers on the CDE agency pages for 24 Ohio agencies in 2019, 2021 and 2025: 859 of 864 agency-months agreed. In the other 5, the CDE page showed a report that the master file did not.
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

**What it is.** The FBI's estimated number of violent and property crimes for Ohio, and its population, for each year. Named in the crime notes for reference. The page's Ohio figure is not this estimate: it is built the same way as the counties (see Coverage), so a county is not made to look worse by the method alone.

**Where it comes from.** CDE Documents and Downloads, "Crime in the United States," estimations zip for each edition (`cius/<year>/cius-estimations-<year>.zip`), Table 4 "Crime in the United States by Region, Geographic Division, and State," xlsx. Each edition has two years. We read the 2022 through 2025 editions and keep each year from the latest edition that has it. Rate = estimated count / population x 100,000 at full precision (the table rounds to one decimal).

**Version and vintage.** 2025 edition files dated 2026-08-03.

**Coverage.** Ohio, 2021 through 2025. The FBI publishes estimates for earlier years too, but those editions are old `.xls` files that the project's Python setup cannot read, so `extras.ohio_fbi_estimate_counts` starts in 2021. The page's `ohio` series, 2015 through 2025, is built the same way as the counties (all full-year local agencies, also in `extras.ohio_reported_agencies`); it runs higher than the FBI estimate (for 2025, 293.8 vs. 275.6 violent and 1,513 vs. 1,429 property per 100,000).

**Changes over time.** The FBI estimates crime for agencies that sent fewer than 12 months: for 3 to 11 months it scales up the agency's own data; for fewer than 3 months it uses similar agencies in the state. The 2021 estimates came out as a limited release because national NIBRS participation was low that year.

**Suppressed, censored or masked values.** None for Ohio.

**Missing data.** None for Ohio, 2021 through 2025.

**Revisions.** Each edition can revise the prior year. We use the later edition.

**Units and rounding.** Counts, whole numbers. Published rates to one decimal.

**Known quirks.** Table 4 file names start with `Table_4` in the 2022 and 2023 editions and `CIUS_Table_4` in later ones.

**Uncertainty.** The FBI does not publish error bars for these estimates.

**License and attribution.** Public domain. Credit: FBI, Crime in the United States.

## National benchmark (same sources as the county layers)

Built by `scripts/50_national.py` into `data/processed/national.json`. Raw pulls are cached under
`data/raw/census/national/`, `data/raw/census_pep/`, `data/raw/bls_laus_national/`, `data/raw/bls_qcew/`
and `data/raw/cdc/national/`. Pulled 2026-11-09.

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

**The U.S. value.** It is the publisher's own national figure (ACS `us:1`, CPS annual average, QCEW `US000`,
SAHIE and SAIPE U.S. rows, the Census national population files, CDC's U.S. row), not an average of states,
with two exceptions: the race groups and female share are the sum of the 50 states and DC (checked equal to the
national total), and the U.S. fertility rate is computed from the national births and women 15 to 44 the same
way as each state's. `us_source` names it for each measure.

**Check against the Ohio figures.** The script computes Ohio the same way as every other state and stops
if Ohio does not equal the `ohio` value in the layer file at display precision. On the 2026-11-09 run
all 41 measures matched exactly. The check results are stored in `checks`.

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

## School report card achievement files (Ohio Department of Education and Workforce)

Built by `scripts/40_reading.py` into `data/processed/reading.json`. The ODEW files were downloaded by hand into
`data/raw/odew/`. The script does not fetch them. CCD pulls are cached under `data/raw/urban_ccd/`. Built 2026-11-09.

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
- Masked districts: Put-In-Bay Local (Ottawa County, every year), Vanlue Local (Hancock County, 2021-22 through 2024-25) and Bloomfield-Mespo Local (2020-21). The rest are small community schools.
- We flag a county when 5% or more of its grade 3 enrollment is in masked cells. No county reaches that in 2025-26. The highest is Harrison at 4.3%.
- Earlier years: Harrison reached 5.4% in 2020-21. (Hocking shows 5.7% in 2023-24 only because Southeast Ohio Classical Academy, which first appears in the 2024-25 file, is listed there as "NC" for the prior year; by the rule above Harrison is highest that year at 3.2%. No shown value changes.) Those flags are not in the series because the flag field covers only the latest year.

**Missing data.** All 88 counties have a value in every school year. We could not weight two community schools in 2025-26 because CCD had no grade 3 enrollment for them: LINC Academy Columbus and Virtual Preparatory Academy of Ohio. Both are left out.

**Revisions.** ODEW does not reissue these files once the report card is final. We keep each year's own file.

**Units and rounding.** Percent, published to one decimal place, as text, sometimes padded with spaces (2025-26).

**Known quirks.**
- ODEW does not publish the number of students tested in these files. We weight each district and school by its grade 3 fall enrollment from the NCES Common Core of Data (next section). Enrollment is a close stand-in for students tested but is not the same count.
- Online (virtual) community schools are left out of county figures, because their students live all over the state while ODEW lists one county for the school. We take the virtual flag from the CCD school directory, counting a school as online if CCD flags it in any year 2017-2024, and seven schools are left out (the script prints the names).
- The Ohio figure on the page is the enrollment-weighted sum of the same district and school figures the counties use, for every school year. When CCD has no enrollment for a district or school in that year, the nearest year is used, and the earlier year when two are equally near.
- A district that spans counties counts in the one county ODEW lists for it in that year's file. Counties are compared with a statewide number built the same way.
- ODEW also prints its own state number in the same files, for 2018-19 and 2021-22 through 2025-26. It runs 1.9 to 2.6 points below our statewide sum in every year we can compare, with or without the online schools. We think the cause is the students ODEW counts at the state level but not in any one district's or school's result (for example, students who were not enrolled for the full year). We did not confirm this. Both numbers are in `extras.reading_rollup_detail.ohio`, and the page's note gives ODEW's latest figure.
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
larger, and capped at 100% in both directions. The spread is used for measures near zero, such as labor force
growth since 2019; 24 counties reach the cap on that measure, which raises the Work and wages issue's gaps.
Measures with no statewide figure (CDC PLACES) compare with the median county, so for an issue built only from
PLACES measures about half the counties are behind by construction. Overdose rates exist for 43 counties; the
other 45 get an Addiction gap from PLACES alone. Prime-age work rates flagged for
group quarters (5% or more of residents in prisons, dorms or nursing homes) are left out of every count.

**Issues.** Nine groups of measures, set in `scripts/90_build.py` (`ISSUES`); an issue keeps only the measures that
are on the page. A county's issue gap is the average of its measure gaps. "Behind" means an issue gap above 3%, the
same "near Ohio" band used on the other tabs.

**By issue.** For each issue: counties behind; residents of those counties (Census estimate, July 1, 2025); the
median issue gap among those counties (the average of the two middle values when the count is even); counties that worsened on more of the issue's measures than they improved on
(using the "since 2019 / 10 years" switch; dollar measures left out because they are not adjusted for inflation);
and Ohio against the other states on measures with a same-definition state figure (`scripts/50_national.py`),
scored as Ohio's average rank among the 50 states and DC (tied states share the best rank they tie for). The
order is a weighted average of the five factors, each scaled from 0 (lowest issue) to 1 (highest issue), with
weights the viewer sets. Equal weights by default. An issue with no value for a factor (no state figures, for
example) is scored on the factors it has.

**By place.** Counties ranked by the number of issues they are behind on, then by their average issue gap. County
groups come from k-means clustering (six groups) on each county's issue gaps, started from six counties spread
evenly across the overall gap, so the result is the same on every load. A blank issue gap (for example, a county
with no crime value) counts as 0, the same as Ohio. The grouping is sensitive to these choices: other starting
points give groups that agree on only about half of county pairs. Groups are named by their largest shared gaps,
with more issues added when two groups would otherwise share a name. Not every member is behind on every issue in
its group's name. They describe which problems occur together, not causes.

**Change window.** "Since 2019" compares the latest value with the period ending in 2019 (2015-2019 for ACS
five-year data). "Over 10 years" compares with the period ending ten years before the latest (2010-2014 for ACS).
A source that starts later uses its first period, and the page names it. When a place's latest value or its
base-period value is blank, no change is shown for it, and it is left out of the "getting worse" counts.

## Congressional district pages (derived from the sources above; OH-10 and IL-6)

**What it is.** One page per district, built by `scripts/60_district_geo.py`, `61_district_data.py`,
`63_district_basemap.py` and `62_district_build.py`, each run with a district key from `scripts/districts.py`
(`oh10`, `il06`). Output: `data/processed/<key>/` and `dist/<key>/index.html`.

**District lines.** OH-10: the Ohio Redistricting Commission's block assignment file for the map adopted October 31,
2025 (map 430 on redistricting.ohio.gov). IL-6: the Census Bureau's block equivalency file for the 119th Congress
(`NationalCD119.txt` in cd119.zip), which carries the map Illinois enacted in 2021. Each block gets its 2020 census
population (P.L. 94-171, P1_001N). The block sums match the official 2020 counts: 786,629 for OH-10 (Ohio Secretary of
State) and 753,677 for IL-6 (Census API, 2020/dec/cd119). IL-6's drawn outline is TIGERweb Current layer 54 (120th
Congressional Districts, January 1, 2026 vintage); every tract wholly inside the district by block population falls
inside that outline, and no tract with zero district residents does.

**Tracts.** 2020 census tracts. A tract is mapped, ranked and given a scorecard when most of its 2020 residents live
in the district; those figures cover the whole tract. OH-10: 220 mapped tracts, 4 split by the line. IL-6: 170 mapped
tracts, 57 split, 199 with any district residents. Names: the place holding at least half of a tract's 2020 residents
(Census 2020 place block assignment file), or else the township holding the tract's internal point.

**District figures.** IL-6: ACS 5-year 2020-2024 estimates the Census Bureau publishes for the district itself
(geography "congressional district", 119th Congress lines), with their margins of error. OH-10 (no published
estimates for the 2025 lines yet): each ACS table line summed over every tract with district residents, weighted by
the share of the tract's 2020 residents inside the district; margins of error weighted the same way and combined as
the square root of the sum of squares. This assumes residents on both sides of a split are alike. The district median
household income is interpolated from its B19001 brackets (the same method gives Ohio's published median within 0.2%).
Check of the tract method against IL-6's published figures: 23 of 24 measures fall within the published margin of error;
Black, not Hispanic is 5.3% built against 5.0% published (margin 0.3). CDC PLACES district figures (both pages): tract
values weighted by adults 18 and older times the same inside share.

**County table.** OH-10 reads the Ohio statewide layers, so its county values are the ones the state page shows. IL-6
(`scripts/district_counties.py`) pulls six measures for Cook and DuPage with the same methods as the Ohio layers, for
the period of the state and U.S. figures in `national.json`: LAUS unemployment (2025 annual average), QCEW average weekly
wage (2025, all ownerships), SAHIE uninsured under 65 (2024), SAIPE child poverty (2024), CDC VSRR provisional overdose
deaths per 100,000 (12 months ending March 2026, over 2025 population) and population change from the April 2020 base
to July 2025. Illinois and U.S. values come from `national.json`. Ohio-only sources (reading, child care, SNAP persons,
crime) are not on the IL-6 page.

**Base map.** TIGERweb primary and secondary roads, area water and 2020 place names (see the script docstring). For
IL-6, place names that would overlap a larger name at the zoom where they appear, or run past the map edge, are dropped.

<!-- from docs/datasets/schools.md (scripts/44_*.py) -->
## School report card achievement files and District Details file (Ohio Department of Education and Workforce)

**What it is.** One row per traditional public school district (`*_Achievement_District.xlsx`) or per community school building (`*_Achievement_CS.xlsx`). We use two fields:
- The percent of third graders who scored proficient or above on the Ohio State Test in math.
- The chronic absenteeism rate, which is the percent of students who missed 10% or more of the school year, excused or not.

The 2025-26 chronic absenteeism rate comes from `2026_District_Details.xlsx`. It has one row per district and student group. We use the "All Students" row and its enrollment count.

**Where it comes from.** ODEW report card "Download Data" page, https://reportcard.education.ohio.gov/download, categories "District Data" and "School Building Data". Files:
- `18-19`, `21-22`, `22-23`, `23-24`, `24-25` and `25-26_Achievement_District.xlsx`
- the same years of `_Achievement_CS.xlsx`
- `2026_District_Details.xlsx` (school year 2025-26)

The math column is "3rd Grade Math 2018-19 % at or above Proficient - District" in 2018-19 and "3rd Grade Math 2025-2026 Percent Proficient or above - District" from 2021-22 on. Each file also has the value for the year before, and that is where 2017-18 and 2020-21 come from. Chronic absence for 2017-18 and 2018-19 is in the 2018-19 district file, on the `Performance_Indicators` sheet. The later achievement files do not carry it. The download links on the site need an access token that the page adds, so these files were saved by hand.

**Version and vintage.** The files were created between October 2019 (2018-19) and September 2026 (2025-26). Each prior-year math column matches the earlier year's own file for every district. For 31 community schools, one file says "NC" and the next says "NA". Both mean no value. We keep the value from each year's own file.

**Coverage.**
- Math: school years 2017-18, 2018-19, and 2020-21 through 2025-26. There was no state testing in 2019-20. Districts: 607 (608 in 2017-18 and 2018-19). Community schools: 246 to 269.
- Chronic absence: school years 2017-18, 2018-19 and 2025-26 only, for traditional districts only. The series lists 2019-20 through 2024-25 as empty, because those files are not on disk. We did not check whether ODEW published district rates for 2019-20.
- Each row carries ODEW's county, and we use it to place districts and schools. A district that spans counties counts in the one county ODEW lists.

**How a county value is built.**
- Math, same as the reading layer: an average of district and in-person community school percents, weighted by grade 3 fall enrollment from CCD (next section). Online (virtual) community schools are left out, because their students live all over the state. The same seven schools are flagged as online; six of them have a math value to leave out.
- Chronic absence: an average of district percents, weighted by total enrollment. The weight is CCD total enrollment for 2017-18 and 2018-19, and ODEW's own enrollment from the same District Details file for 2025-26. Community schools are left out in every year. Their 2025-26 rates are in a file we do not have, and leaving them out in all years keeps the years comparable.
- The Ohio figure for both measures is built the same way, from every district and school the counties use.

**Changes over time.** Ohio rewrote its report card law in July 2021. From 2021-22 on, third grade math is a "report only" figure, and the level names changed ("Accelerated" became "Accomplished"). The measure itself, proficient or above on the grade 3 math test, has the same name in every file. We did not confirm the math cut score for each year against ODEW's technical documents. In 2018-19 chronic absence was one of the graded "indicators met" (the file's `Chronic Absenteeism Indicator` column). We read the column names and ODEW's "missed 10% or more" wording, but we could not extract the text of ODEW's attendance technical document (`Student-Attendance.pdf`), so the fine print on which students are counted is not confirmed here.

**Suppressed, censored or masked values.** ODEW prints "NC" (not calculated) when a district or school has too few students, "<10" for small enrollment counts, and "NA" for community schools whose grades do not include grade 3 (2024-25 and 2025-26 files).
- No masked value is ever treated as 0. Any cell that is not a number is stored as null with its ODEW code as the flag.
- A masked district or school drops out of its county's average. We count its CCD grade 3 enrollment as "masked weight" in `extras.schools_rollup_detail`.
- Math, statewide, masked weight is 0.1% to 0.7% of grade 3 enrollment each year. In 2025-26 it is 366 of about 123,000.
- Masked math districts: Put-In-Bay Local (every year), Vanlue Local (2021-22 through 2024-25), Bellaire Local, Berne Union Local and Bloomfield-Mespo Local (2020-21), and Vandalia-Butler City, Westfall Local and Wheelersburg Local (2023-24). The rest are small community schools.
- We flag a county when 5% or more of its weight is in masked cells. No county reaches that in 2025-26. The highest is Harrison at 4.3%. In an earlier year, Pickaway reached 13.5% (2023-24, when Westfall Local was not reported). That flag is not in the series, because the flag field covers only the latest year.
- Chronic absence: every district's "All Students" rate is a number in all three years. Rates for smaller student groups are often "NC", but we do not use them.

**Missing data.** All 88 counties have a value for both measures in every year listed. Two community schools in 2025-26 (IRNs 021547 and 022050) have a math value but no CCD grade 3 enrollment, so they are left out.

**Revisions.** ODEW does not reissue these files once the report card is final. We keep each year's own file.

**Units and rounding.** Percent, published to one decimal place, as text, sometimes padded with spaces (2025-26).

**Known quirks.**
- ODEW does not publish the number of students tested. We weight math by CCD grade 3 fall enrollment, which is a close stand-in but not the same count.
- Ohio math figure: ODEW prints its own state number in the same files (2018-19 and 2021-22 through 2025-26). Our statewide sum runs 1.1 to 1.5 points higher in every year we can compare (63.6% vs. 62.1% in 2025-26). This is the same pattern the reading layer shows. We think the cause is students ODEW counts at the state level but not in any one district's or school's result. We did not confirm this. Both numbers are in `extras.schools_rollup_detail.ohio`.
- Ohio chronic absence figure: the files we have do not include ODEW's state rate. News coverage of the 2025-26 report cards gives 23.9% (September 2026) or 23.7% (October 2026, citing ODEW). Our district-only sum is 22.4%, about 1.3 to 1.5 points lower. That fits with leaving out community schools, which have higher rates. We did not confirm the state figure in an ODEW file.
- Two Stark County districts report much lower chronic absence in 2018-19 than in 2017-18: Northwest Local (9.7% to 0.0%) and Tuslaw Local (9.8% to 0.5%). We keep ODEW's values as published. They pull Stark County's 2018-19 figure down a little.
- 2020-21 math was tested during the pandemic, and fewer students took the test than usual.
- The county chronic absence figure leaves out community school students. In CCD fall 2024 they were 7.4% of Ohio public school students. In-person community schools enroll the largest shares in Cuyahoga (12.7%), Franklin (12.4%), Lucas (10.3%) and Montgomery (10.1%) counties, so the gap may be largest there.

**Uncertainty.** These are counts of all students, not a sample, so there is no margin of error. In small counties one district sets the figure, and math can swing 10 points or more from year to year.

**License and attribution.** Public data. Credit: Ohio Department of Education and Workforce, Ohio School Report Cards.

## Common Core of Data, enrollment and school directory (NCES, via the Urban Institute Education Data Portal)

**What it is.** The number of students enrolled on or near October 1, for each district (local education agency, or LEA) and each school. We use grade 3 counts as the math weight and the district total as the chronic absence weight for 2017-18 and 2018-19. We also use the school directory's `virtual` flag.

**Where it comes from.** Urban Institute Education Data Portal API, no key. These are the reading layer's cached pulls, read only:
- `https://educationdata.urban.org/api/v1/school-districts/ccd/enrollment/{year}/grade-3/?fips=39`
- `.../school-districts/ccd/directory/{year}/?fips=39` (its `enrollment` field is the district total)
- `.../schools/ccd/enrollment/{year}/grade-3/?fips=39`
- `.../schools/ccd/directory/{year}/?fips=39`

We match a district on `state_leaid` = "OH-" plus its ODEW IRN, and a community school on the building IRN at the end of `seasch`.

**Version and vintage.** CCD years 2017, 2018 and 2020 to 2024, where "2024" means fall of the 2024-25 school year. CCD for fall 2025 was not in the API at pull time, so 2025-26 math uses 2024-25 grade 3 enrollment. Any district or school with no enrollment in a given year uses its nearest available year.

**Coverage.** All Ohio public districts and schools that report to NCES. We keep the all-students row only (race 99, sex 99). Codes below 0 (missing or not applicable) are treated as no data.

**Changes over time.** None that affect these counts.

**Suppressed, censored or masked values.** None for grade 3 or district totals.

**Missing data.** Two 2025-26 community schools are not matched (see above).

**Revisions.** NCES finalizes each year once.

**Units and rounding.** Students, whole numbers.

**Known quirks.** The CCD district total includes preschool and every grade. ODEW's chronic absence rate covers enrolled students as ODEW defines them. The weights are close but not the same group. This changes the weights a little. It does not change any district's percentage.

**Uncertainty.** Not applicable.

**License and attribution.** Public domain. Credit: U.S. Department of Education, National Center for Education Statistics, Common Core of Data, via the Urban Institute Education Data Portal.

<!-- from docs/datasets/access.md (scripts/45_*.py) -->
## County Health Rankings & Roadmaps national data (University of Wisconsin Population Health Institute)

**What it is.** One row per county, state and the nation, with a value, numerator and denominator for each measure. We use four measures: Primary Care Physicians (measure 4), Dentists (88), Mental Health Providers (62) and Suicides (161). CHR&R does not collect these data. It recomputes them from the original publishers: the HRSA Area Health Resources Files (doctor counts from the American Medical Association Physician Masterfile; dentist counts from the CMS National Provider Identifier file), the CMS NPPES file (mental health providers), and NCHS death records (suicides). We do not use CHR&R ranks, z-scores or health groups.

**Where it comes from.** countyhealthrankings.org, Health Data, Data & Documentation page. Files:
- `analytic_supplement_20260325.csv` (Supplemental Data Release, March 25, 2026; 10.8 MB) and its codebook `Analytic_Dataset_Codebook_Supplemental_Release_20260325.pdf`. This is the newest release; the data page lists no 2026 annual release.
- `chr_trends_csv_2025.csv` (60 MB) and `Trends documentation 2025.pdf`, for earlier years of doctors and dentists.
- `analytic_data2025_v3.csv` (2025 annual release), used only for the 2020 voter turnout comparison in `extras.turnout_counts`.
- `DataDictionary_2025.xlsx` and the 2025 technical document.
No login.

**Version and vintage.** Supplemental release of March 25, 2026. Years of data: doctors 2022, dentists 2023, mental health providers 2025, suicides 2019-2023 combined. Each CHR&R release can revise earlier values. The trends file marks some values as differing from the release they first appeared in.

**Coverage.** All 88 Ohio counties and Ohio.
- Doctors: practicing non-federal M.D.s and D.O.s under age 75 in general practice, family medicine, general internal medicine and general pediatrics. Subspecialists are left out. Nurse practitioners and physician assistants are not counted. Counted in the county of the practice address. The series runs 2010-2022 (2010-2021 from the trends file). CHR&R says trends should start with 2010 data (its 2013 release) because D.O.s were added then.
- Dentists: dentists with an NPI. Series 2010-2023 (2010-2022 from the trends file).
- Mental health providers: psychiatrists, psychologists, licensed clinical social workers, counselors, marriage and family therapists, providers who treat alcohol and drug use, and advanced practice nurses in mental health, with an NPI. Latest year only.
- Suicides: deaths coded ICD-10 X60-X84, by county of residence, 2019-2023 combined. Age-adjusted, so counties with older or younger populations can be compared. The denominator is the five-year sum of Census population estimates. We store the age-adjusted rate. The crude rate and the death count are in `extras.suicide_deaths`. Latest period only.

**Changes over time.** Mental health providers: marriage and family therapists and addiction providers were added in the 2015 release. In September 2025 CHR&R began placing providers in counties with mapping tools instead of ZIP codes alone; CHR&R warns this can shift values, most in small counties. This is why we keep only the latest year. Suicides: since the 2024 release, the denominator uses Census population estimates instead of NCHS bridged-race estimates.

**Suppressed, censored or masked values.** CHR&R leaves suicides blank with fewer than 10 deaths in five years (Holmes and Noble). We also leave blank any county with fewer than 20 deaths, because NCHS calls rates on fewer than 20 deaths unreliable. That blanks 11 more counties: Fayette, Harrison, Henry, Meigs, Mercer, Monroe, Morgan, Putnam, Van Wert, Vinton and Wyandot. In all, 75 of 88 counties have a suicide rate. The CHR&R value and death count for every county stay in `extras.suicide_deaths`. Provider rates: CHR&R leaves the rate blank for a county with more than 2,000 people and zero doctors (more than 4,000 for dentists; 1,000 for mental health providers). The file still gives the count. Morgan County has a count of 0 primary care doctors in 2022, so we store 0 with the flag "none counted in the county."

**Missing data.** None for Ohio counties besides the cases above.

**Revisions.** We pin the March 2026 supplement. A new release can change values.

**Units and rounding.** The file stores provider values as providers per person; we multiply by 100,000. Suicide rates are per 100,000.

**Known quirks.** Pike County shows 1,541 mental health providers per 100,000 people (417 providers for about 27,000 people), four times the Ohio figure. The 2025 annual release also showed a high count (364). Providers are counted at the address they list, which can be an office that serves people outside the county. Holmes County has the lowest value (18 per 100,000). The annual CSV has two header rows (long names, then variable names).

**Uncertainty.** CHR&R gives confidence intervals for suicides but not for provider counts. Provider files can include people who have stopped practicing.

**License and attribution.** Free to use with credit. Credit: University of Wisconsin Population Health Institute, County Health Rankings & Roadmaps 2025 (Supplemental Data Release, March 2026), with the original sources named above (HRSA Area Health Resources Files; CMS NPPES; CDC NCHS).

## Fatality Analysis Reporting System, FARS (NHTSA)

**What it is.** A census of every motor vehicle crash on a public road in the U.S. in which someone died within 30 days. The `accident.csv` file has one row per crash, with the state, county and number of deaths (`FATALS`).

**Where it comes from.** `https://static.nhtsa.gov/nhtsa/downloads/FARS/<year>/National/FARS<year>NationalCSV.zip`, about 25-35 MB each. No login. We read only `accident.csv` (named `accident.CSV` at the zip root in 2019).

**Version and vintage.** Release notes (`FARS<year> Release Notes.txt`) show 2023 as the latest final file (first released 2026-04-01). The 2024 file is an annual report file, released 2026-04-01; NHTSA updates it into a final file about 12 to 15 months later, so we do not use it yet. The 2021 zip was reposted 2026-06-24 and the 2022 and 2023 zips 2026-04-01.

**Coverage.** Ohio crashes, 2015-2023. Deaths are counted in the county where the crash happened, not where the person lived. That differs from CDC death records, which CHR&R uses for its own crash death measure. Counties with major highways or that border other states can look quite different on the two counts. For 2017-2023, FARS counts 8,500 deaths in Ohio crashes and the CDC-based CHR&R figure counts 9,139 Ohio residents.

How we build the rate: deaths in the five final years combined, divided by the sum of the five July 1 populations, times 100,000. This is a yearly rate. Not age-adjusted. The `series` holds five-year windows from 2015-2019 to 2019-2023. The Ohio figure is all Ohio crashes, built the same way. `extras.traffic_deaths` has deaths by year and person-years.

**Changes over time.** FARS county codes for Ohio match Census FIPS codes. No crash in 2015-2023 had an unknown county.

**Suppressed, censored or masked values.** None in the source. We leave a county blank when it had fewer than 20 deaths in the five years, following the NCHS rule for unreliable rates. Six counties are blank for 2019-2023: Jefferson (18 deaths), Monroe (17), Morgan (16), Putnam (14), Vinton (14) and Paulding (12).

**Missing data.** None for Ohio.

**Revisions.** Final files are not expected to change, but NHTSA does repost them. Delete the cached zip to pull a new copy.

**Units and rounding.** Whole deaths. Rates are ours, stored at full precision.

**Known quirks.** Some older zips have a byte order mark at the start of `accident.csv`; the script strips it. Noble County has the highest rate (32 per 100,000, on 23 deaths in 2019-2023). Because FARS counts deaths where the crash happened, deaths of people passing through count in the county.

**Uncertainty.** None published. Small counts swing from year to year.

**License and attribution.** Public domain. Credit: National Highway Traffic Safety Administration, Fatality Analysis Reporting System.

## Public Libraries Survey (Institute of Museum and Library Services)

**What it is.** A yearly survey of every public library system. The administrative entity (AE) file has one row per library system, with total operating spending (`TOTOPEXP`) and visits (`VISITS`). The outlet file has one row per building or bookmobile.

**Where it comes from.** imls.gov, Public Libraries Survey page. CSV zips: `pls_fy2024_csv.zip` (posted 2026-06; zip contents dated up to 2026-11-04) back to `pls_fy2019_csv.zip`, plus the FY 2024 Data Documentation and User's Guide. We use the imputed files (`PLS_FY24_AE_pud24i.csv` and the outlet file). No login.

**Version and vintage.** FY 2024 is the latest year. Ohio library fiscal years are calendar years (January 1 to December 31) in every year we use.

**Coverage.** 251 Ohio library systems each year. Ohio's systems are set up by county, school district, city or township. `TOTOPEXP` is staff, collection and other operating costs; it leaves out capital (building) spending. `VISITS` is people entering the library for any reason. In FY 2024, 250 of 251 Ohio systems estimated visits from a typical week (counted in October and multiplied by 52) instead of a full-year count.

How we build the rates: each system is assigned to the county named in its `CNTY` field (the county of the main office). We add up spending and visits for each county and divide by the county's July 1 population for that year. The Ohio figure is all 251 systems divided by Ohio's population. The Ohio totals match IMLS's own state totals (checked for FY 2020: $718,064,020 and 44,225,213 visits). IMLS's own per-person figures divide by the population of library service areas instead, so they differ a little from ours. The 2024 list of systems in each county is in `extras.library_systems`.

**Systems that serve more than one county.** IMLS lists every Ohio central and branch library in the same county as its system's main office, so no system has a building recorded in another county (`extras.library_multi_county` is empty for every year). Service areas are different. Many Ohio library systems serve a school district, and some school districts reach into a neighboring county. The survey does not say how much of a service area falls in each county, so we cannot split a system's spending or visits by county. Counties whose residents rely on a library based next door will look lower than their real use.

**Changes over time.** COVID-19 closures cut visits sharply in 2020 and 2021 (Ohio: 5.8 visits per person in 2019, 2.6 in 2021, 4.1 in 2024). Spending is in dollars of each year, not adjusted for inflation.

**Suppressed, censored or masked values.** For systems with 2 or fewer paid staff, IMLS hides salary detail, but not total operating spending. No Ohio values we use are suppressed.

**Missing data.** IMLS fills in missing values. In FY 2024, one Ohio system's spending was filled in (flag `IT24`) and all visits were reported. In FY 2020, visits for 183 of 251 Ohio systems were filled in from earlier years (flag `IG19`: the prior year's value times a growth rate), so 2020 visits are mostly estimates.

**Revisions.** Each year's file is a snapshot. We pin the files listed above.

**Units and rounding.** Dollars and visits as whole numbers. Per-person values are ours.

**Known quirks.** Pike County's only system reported 175,864 visits in FY 2019, then 7,800 to 8,320 a year in FY 2020-2022, 28,444 in FY 2023 and 21,892 in FY 2024. The survey does not say why. Pike has the lowest visit rate in FY 2024 (0.8 per person). The FY 2019-2021 outlet files spell one Fairfield County outlet's county "FARIFIELD."

**Uncertainty.** None published. Visits based on a typical week are estimates.

**License and attribution.** Public domain. Credit: Institute of Museum and Library Services, Public Libraries Survey, FY 2019-FY 2024.

## County Business Patterns (Census Bureau)

**What it is.** Counts of business establishments with paid employees, by industry (NAICS) and county, as of mid-March. We count the ten industries that CHR&R calls "membership associations": religious organizations (813110), civic and social organizations (813410), business associations (813910), professional organizations (813920), labor unions (813930), political organizations (813940), sports teams and clubs (711211), golf courses and country clubs (713910), fitness and recreational sports centers (713940) and bowling centers (713950). This list is broader than NAICS 813 alone; we follow CHR&R so the values match theirs.

**Where it comes from.** Census Data API, `https://api.census.gov/data/<year>/cbp`, variables `ESTAB`, `EMPSZES`, `LFO`, one call per industry, county and state level. We keep rows for all employment sizes (`EMPSZES=001`) and all legal forms (`LFO=001`). Needs the Census API key.

**Version and vintage.** 2023 is the latest year (2024 is not yet in the API or on the Census site). Years used: 2019-2023.

**Coverage.** All 88 counties and Ohio. Only places with paid employees are counted, so volunteer-run churches and clubs are missed. A business is coded by its main activity. Our 2023 counts match CHR&R's exactly (Ohio 12,736; Allen County 164). Rate = establishments / July 1 population x 10,000. The Ohio figure uses the Census state-level count.

**Changes over time.** The ten codes are the same in the 2017 and 2022 NAICS. Since 2017, CBP does not publish a cell with fewer than 3 establishments.

**Suppressed, censored or masked values.** A county-industry cell with 1 or 2 establishments is dropped, not shown as a number. We cannot tell a dropped cell from a true zero, so we count it as zero. This undercounts small counties. The 88 counties add up to 12,442 in 2023, 294 fewer than the state count of 12,736. Ohio's rate on the page is built the same way as the counties, from the county sum (10.54 per 10,000 in 2023), so counties are not compared with places their own counts leave out; the state count (10.79) is in `extras.association_counts_ohio_published` and named in the note.

**Missing data.** See above.

**Revisions.** None after release.

**Units and rounding.** Whole establishments.

**Known quirks.** The 2023 API still uses the variable name `NAICS2017`. Asking for more than one industry in one call returns only the first, so we make one call per industry.

**Uncertainty.** The Census Bureau does not publish error ranges for establishment counts.

**License and attribution.** Public domain. Credit: U.S. Census Bureau, County Business Patterns; measure definition from County Health Rankings & Roadmaps.

## 2024 election returns (MIT Election Data + Science Lab, from the Ohio Secretary of State)

**What it is.** Official November 5, 2024 general election results for Ohio, one row per precinct, office and candidate. We add up votes for president in each county.

**Where it comes from.** GitHub repository `MEDSL/2024-elections-official`: `individual_states/oh24.zip` (16.5 MB; the CSV inside is dated 2026-04-28) and `2024-president-state.csv` for the statewide total. MEDSL lists the Ohio Secretary of State's official results page as its source. We tried the Secretary of State's site first; during this pull the whole site showed a maintenance page. MEDSL's county-level file on Harvard Dataverse needs a guestbook form, so we used the precinct file.

**Version and vintage.** Results certified by Ohio's Secretary of State on December 2, 2024. MEDSL's Ohio file was added 2025-10-31.

**Coverage.** All 88 counties, 8,878 precincts, all modes combined (`mode = TOTAL`).

How we build the rate: votes cast for president divided by U.S. citizens age 18 and older (ACS, next section), times 100. This is CHR&R's voter turnout method. Ballots with no vote for president are not counted, so this runs a little lower than ballots cast: the Secretary of State reported 5,851,387 ballots cast statewide, and the presidential total is 5,767,788.

**Changes over time.** CHR&R's 2020 turnout figure for each county is in `extras.turnout_counts` for comparison. It used the same method (2020 votes for president and ACS 2016-2020 citizens).

**Suppressed, censored or masked values.** None.

**Missing data.** The precinct file has no write-in votes. Write-ins total 2,771 statewide, 0.05% of the presidential vote. County values leave them out; the Ohio value uses the official statewide total, which includes them.

**Revisions.** None expected.

**Units and rounding.** Whole votes.

**Known quirks.** The precinct file has zero-vote rows for write-in candidates in every precinct. Holmes County has the lowest turnout (39.9%) and Delaware County the highest (83.0%).

**Uncertainty.** Vote counts are exact. The uncertainty comes from the denominator.

**License and attribution.** MEDSL asks users to cite its data. Credit: MIT Election Data and Science Lab, 2024 precinct-level election returns, from the Ohio Secretary of State.

## American Community Survey 5-year, citizen voting-age population (Census Bureau)

**What it is.** Table B29001, estimated U.S. citizens age 18 and older, 2020-2024 5-year estimates, by county and for Ohio.

**Where it comes from.** Census Data API, `2024/acs/acs5`, variables `B29001_001E` and `B29001_001M`. Needs the Census API key.

**Version and vintage.** ACS 2020-2024 5-year release. CHR&R used the CVAP special tabulation from the same ACS survey; its county totals come from the same estimates.

**Coverage.** All counties and Ohio. Includes citizens who cannot vote (for example, people serving a felony prison term), so turnout is understated where many such people live.

**Changes over time.** Each 5-year release is a new estimate; we use the one that ends in the election year.

**Suppressed, censored or masked values.** None at the county level.

**Missing data.** None.

**Revisions.** None after release.

**Units and rounding.** People. Margins of error at the 90% level. We turn the margin of error of the denominator into a margin of error for turnout (votes x MOE / citizens squared x 100) and store it in `moe`. It is at most 0.8 points (in small counties).

**Known quirks.** None found.

**Uncertainty.** Survey estimate; see margins of error.

**License and attribution.** Public domain. Credit: U.S. Census Bureau, American Community Survey 2020-2024 5-year estimates, table B29001.

## Population estimates used as denominators (Census Bureau)

**What it is.** July 1 resident population by county.

**Where it comes from.** For 2020-2025, `data/processed/popest.json` (Vintage 2025, built by `scripts/21_popest.py`; see `docs/datasets/popest.md`). For 2015-2019, the 2010-2020 intercensal estimates, `cc-est2020int-agesex-39.csv` from `www2.census.gov/programs-surveys/popest/datasets/2010-2020/intercensal/county/asrh/` (released September 2025), field `POPESTIMATE`. In that file, `YEAR` codes 2 to 11 are July 1, 2010 to July 1, 2019. Ohio for 2015-2019 is the sum of its counties.

**Version and vintage.** Vintage 2025 and the 2010-2020 intercensal series. Both are tied to the 2020 Census, so the switch at 2020 does not create a jump.

**Coverage.** All 88 counties and Ohio, 2015-2025.

**Changes over time.** Each new vintage revises 2020 and later years.

**Suppressed, censored or masked values.** None.

**Missing data.** None.

**Revisions.** A new vintage will change the 2020-on denominators when `popest.json` is rebuilt.

**Units and rounding.** People.

**Known quirks.** CHR&R used its own (earlier) population vintages, so our 2023 association rate for Ohio (10.79 per 10,000) differs slightly from CHR&R's (10.81) even though the counts match.

**Uncertainty.** The Census Bureau does not publish error ranges for these estimates.

**License and attribution.** Public domain. Credit: U.S. Census Bureau, Population Estimates Program.

<!-- from docs/datasets/public_money.md (scripts/46_*.py) -->
## Personal current transfer receipts, table CAINC35 (U.S. Bureau of Economic Analysis)

**What it is.** BEA's estimate of benefits received by the residents of each county, in thousands of dollars per year. We use six lines and divide each by the Census July 1 population of the same year:

| Metric | BEA line | What BEA counts |
|---|---|---|
| `bea_medicaid_per_resident` | 2220 Public assistance medical care benefits | Medicaid, the Medicaid part of CHIP, the rest of CHIP and state and local medical aid, paid to providers for residents' care |
| `bea_snap_per_resident` | 2330 Supplemental Nutrition Assistance Program | SNAP benefits |
| `bea_ssi_per_resident` | 2310 Supplemental Security Income benefits | Federal SSI plus state supplements |
| `bea_eitc_per_resident` | 2320 Earned Income Tax Credit | The full federal EITC: the part that lowers taxes owed and the part paid as a refund (CAINC35 footnote 8) |
| `bea_unemployment_per_resident` | 2400 Unemployment insurance compensation | State UI, UI for federal workers, railroad workers and former service members, and trade adjustment aid |
| `bea_veterans_per_resident` | 2500 Veterans' benefits | VA pension and disability, readjustment (education), life insurance and other aid to veterans |

Dollar totals are in `extras.bea_*_dollars`.

**Where it comes from.** `https://apps.bea.gov/regional/zip/CAINC35.zip` (22.6 MB zip of CSV files, no login, no key). We read `CAINC35_OH_1969_2022.csv`. Line names and definitions are in `CAINC35__definition.xml` and `CAINC35__Footnotes.html` inside the zip. Method: BEA, "County Personal Income: Concepts and Methods," Part V, `https://www.bea.gov/system/files/methodologies/BEA-County-Personal-Income-Concepts-and-Methods.pdf`.

**Version and vintage.** The file says "Last updated: November 16, 2023-- new statistics for 2022; revised statistics for 2013-2021." BEA's "Discontinued or Delayed Statistics" page (`https://bea.gov/data/discontinued-or-delayed-statistics`) lists CAINC35 as discontinued on Nov. 1, 2024 and moved to its Regional Account Archive. So 2022 is the last year BEA published by program and county, and no later release will revise it.

**Coverage.** 2010-2022, all 88 counties and Ohio. Ohio is BEA's own state row (GeoFIPS 39000). The 88 counties add exactly to the state row for every line and year we use. BEA builds state totals from program records, then splits them among counties. How directly each county figure is measured differs by line, per BEA's method paper:
- SSI: county figures are based on Social Security Administration payment data.
- Veterans: state and county figures come from the VA's Geographic Distribution of VA Expenditures report (since 2009). State and local aid to veterans is split by veteran population.
- EITC: state totals from IRS Statistics of Income are split among counties using IRS tabulations; from 2016 on, from IRS individual return files.
- SNAP: USDA state totals are split among counties using state social services payment data. Where those are missing, BEA uses Census SNAP recipient estimates (SAIPE) to fill in years.
- Medicaid: state totals come from CMS. Only "a smaller portion of states" give BEA county payment data. For other states, BEA splits the state total in proportion to its own county estimates of family assistance (TANF). CHIP is split by state enrollment data or by Census estimates of children in poverty. The method paper does not say which group Ohio is in, so we cannot say how directly Ohio's county Medicaid figures are measured.
- Unemployment: state totals come from the Department of Labor. Through 2021, about one third of states gave BEA county payment data and the rest were split by BLS counts of unemployed people. Starting with 2022, all county estimates use BLS unemployment counts in the split. The paper does not say which group Ohio was in before 2022.

The method paper we read is the current edition (it describes 2024 estimates). The 2023 release used for this layer may differ in small details.

**Changes over time.** Line 2400 includes the federal pandemic unemployment programs, so 2020 ($15.7 billion in Ohio, $1,334 per resident) and 2021 are far above other years. Lost Wages Assistance is in a different line (2700) and is not counted here.

**Suppressed, censored or masked values.** BEA uses (D) for values withheld to avoid disclosing a single source, (NA) not available and (NM) not meaningful. None of these appear in the six lines for Ohio counties in 2010-2022. The script keeps any such code as `null` with the code in `flag`.

**Missing data.** None for 2010-2022.

**Revisions.** BEA revised 2013-2021 in the 2023 release. Since the table is discontinued, the values are now fixed.

**Units and rounding.** Thousands of current dollars as published; we multiply by 1,000. BEA notes that "statistics presented in thousands of dollars do not indicate more precision than statistics presented in millions of dollars."

**Known quirks.**
- These are benefits received by people who live in the county, by BEA's place-of-residence concept, not money spent by offices in the county.
- Medicaid counts payments to providers for residents' care, so it reflects care used, not only enrollment.
- Ohio dollar totals for 2022: Medicaid line $30.74 billion, SNAP $4.61 billion, SSI $2.22 billion, EITC $2.51 billion, unemployment $0.56 billion, veterans $4.88 billion.

**Uncertainty.** BEA publishes no error ranges. Lines that BEA splits by an indicator (see Coverage) are less exact at the county level than lines built from county payment data.

**License and attribution.** Public domain. Credit: U.S. Bureau of Economic Analysis.

## Picture of Subsidized Households (U.S. Department of Housing and Urban Development)

**What it is.** HUD's yearly snapshot of the homes in its rental aid programs, as of Dec. 31. We use the "Summary of All HUD Programs" row (program 1), which covers public housing, Housing Choice Vouchers (tenant- and project-based), Moderate Rehabilitation, project-based Section 8, Section 236/BMIR, Section 202 and 811 Project Rental Assistance Contracts and Section 811 Project Rental Assistance. Two measures:
- `hud_households_per_1000`: occupied homes (one household each) per 1,000 households in the ACS.
- `hud_spending_per_resident`: occupied homes x HUD's average spending per occupied home per month (`spending_per_month`) x 12, divided by population.

Counts and dollar totals are in `extras.hud_counts`.

**Where it comes from.** `https://www.huduser.gov/portal/datasets/assthsg.html`. Files under `https://www.huduser.gov/portal/datasets/pictures/files/`: `COUNTY_2015.xlsx` to `COUNTY_2021.xlsx`, `COUNTY_2022_2020census.xlsx` to `COUNTY_2025_2020census.xlsx`, the matching `STATE_*` files, and `TRACT_MO_WY_2025_2020census.xlsx` (70 MB; Ohio is in the Missouri-to-Wyoming tract file). Data dictionary: `https://www.huduser.gov/portal/datasets/pictures/dictionary_2025.pdf`. No login. HUD sometimes answers with HTTP 202 and an empty body; the script refuses to save a file that is not a spreadsheet.

**Version and vintage.** One file per year, each a Dec. 31 snapshot (the `Quarter` field reads `31DEC2025` for 2025). We use 2015-2025. From 2022 on we use the files in 2020 census geography (HUD also posts 2022 in 2010 geography). Ohio county boundaries did not change.

**Coverage.** All 88 counties in every year, plus HUD's Ohio state row for the Ohio figure. Housing Choice Vouchers are counted where the voucher holder lives. A row coded `39XXX` holds homes HUD could not place in a county (444 homes in 2015, 1,565 in 2023, 640 in 2025). They are in the Ohio figure but in no county (`extras.hud_units_not_placed_in_a_county`).

Census tracts: 2025 only, 2020 census tract GEOIDs. HUD lists all 3,168 Ohio tracts; all match ACS 2020-2024 tracts. The file also has 72 rows we skip: one "999999" row per county for homes HUD could place in a county but not a tract, and one `39XXX999999` row. Tract results are in the top-level `tracts` key.

**Changes over time.** Before 2025 the files have no count of occupied homes, only the number of homes under contract (`total_units`) and a whole-number occupancy rate (`pct_occupied`). For 2015-2024 we estimate occupied homes as `total_units x pct_occupied / 100`. The 2025 files add `total_occupied`, which we use. Because the rate is rounded, earlier years can be off by up to half a percentage point of occupancy. Example: Ohio 2025 has 198,038 occupied homes as published; the estimate from the rounded 87% would be 197,239 (0.4% lower). `extras.hud_counts` marks which years are published counts (`occupied_is_published`).

**Suppressed, censored or masked values.** HUD codes: -1 missing, -4 suppressed (fewer than 11 households reported), -5 non-reporting (under 50% of households reported). No county was suppressed in 2015-2025. In the 2025 tract file:
- 1,822 tracts have values.
- 939 are suppressed (-4). HUD still shows the number of homes under contract for these, but not occupied homes or spending. We do not fill them in.
- 405 are coded -1 in every field. HUD calls these missing. They appear to be tracts with no HUD-aided homes: all other rows add to 226,655 homes, 57 short of HUD's Ohio total of 226,712. HUD does not say so, so we leave them `null`.
- 2 are non-reporting (-5).
The `flag` field holds HUD's code and meaning.

**Missing data.** See above. A tract with no ACS households or residents would get a flag; none occurred.

**Revisions.** HUD does not revise past snapshots as far as we know; each year is a new file.

**Units and rounding.** `spending_per_month` is in whole dollars. HUD defines it as "average federal spending per unit-month": for public housing, the monthly operating subsidy plus capital cost divided by occupied homes; for vouchers, Moderate Rehabilitation and multifamily programs, the monthly housing assistance payment divided by occupied homes, plus an amount for administrative cost for vouchers and Moderate Rehabilitation. The summary row's average is the average of the programs weighted by occupied homes (Ohio 2025: 818.9 computed, 819 published). Ohio 2025 annual estimate: 198,038 x $819 x 12 = $1.95 billion.

**Known quirks.**
- The yearly dollar figure is our estimate built from one December snapshot, not HUD's reported outlays for the year. It assumes the December count and average held all year.
- Section 811 Project Rental Assistance shows 396 households reported in Ohio in 2025 but its occupied count is coded -5, so HUD's summary row leaves it out.
- Moderate Rehabilitation in Ohio shows 154 occupied homes against 85 under contract in 2025 (181% occupied). We use the summary row as published.
- Very small counties can swing from year to year. Paulding County had 12 occupied homes in 2025.

**Uncertainty.** HUD gives no error ranges for counts. The households denominator is an ACS survey estimate with its own margin of error, which is wide for small tracts.

**License and attribution.** Public domain. Credit: U.S. Department of Housing and Urban Development, Picture of Subsidized Households.

## Annual Survey of School System Finances (U.S. Census Bureau)

**What it is.** Revenue, spending and fall enrollment for every public school system, by fiscal year (July to June in Ohio). Measures:
- `school_spending_per_pupil`: current spending for elementary and secondary programs (`TCURELSC`, thousands of dollars) divided by fall membership (`V33`), summed over the traditional school districts in the county. Summing first is the same as weighting each district's per-pupil figure by its enrollment.
- `school_revenue_federal_share`, `_state_share`, `_local_share`: federal (`TFEDREV`), state (`TSTREV`) and local revenue as a percent of total revenue. Revenue from other school systems (`D11`) is taken out of both local revenue and the total, as the Census Bureau does for its state totals, so a dollar passed between districts is counted once.

Current spending covers salaries, benefits (including state payments for teacher retirement made on a district's behalf), supplies, transportation and other day-to-day costs. It leaves out buildings and equipment, debt interest, payments to other school systems, and adult education and community services.

**Where it comes from.** `https://www.census.gov/programs-surveys/school-finances/data/tables.html`. Files: `https://www2.census.gov/programs-surveys/school-finances/tables/{2022,2023,2024}/secondary-education-finance/elsec{22,23,24}.xlsx` (one row per school system, about 13 MB each) and `elsec{22,23,24}_sumtables.xlsx`. Field definitions: `school24doc.docx` in the 2024 folder. No login. The comma-delimited `elsec22.txt` on the server stops after 1,730 lines, so the script reads the Excel files.

**Version and vintage.** Fiscal 2024 (school year 2023-24) was released May 7, 2026. We use fiscal 2022-2024, shown as school years 2021-2022 to 2023-2024. Earlier years exist, but their summary tables are only in the old `.xls` format, which this project cannot read without adding a package.

**Coverage.** In fiscal 2024 the file has 711 Ohio school systems (710 in fiscal 2022): 609 traditional districts, 49 joint vocational districts, 51 educational service centers and 2 nonoperating districts (Middle Bass and North Bass). County figures use the traditional districts only (609 in each year). Joint vocational districts and service centers serve students from several counties, and service centers report no enrollment, so they are left out of counties. Community (charter) schools run by nongovernmental bodies are outside the survey. Ohio's figure is built the same way as the counties, from all 609 traditional districts (the script checks that it equals the sum of the 88 county totals), so counties compare on equal terms: fiscal 2024, $16,217 per pupil and a 34.9% state revenue share. The Census Bureau's own state figures (Table 8 for per pupil, Table 1 for revenue) include all school systems ($17,257 and 34.6%); they are in `extras.school_ohio_published_all_systems` and named in the notes.

**County assignment.** As in `scripts/40_reading.py`, a district goes to the county named in Ohio's own files: the Census NCES ID is matched to Ohio's district number (IRN) through the NCES Common Core of Data directory (Urban Institute Education Data Portal, cached in `data/raw/urban_ccd/`), and the IRN to the county in ODEW's `2026_District_Details.xlsx`. For 9 districts that cross county lines, ODEW and the Census county code differ: Delphos City, Fostoria City, Bradford, Conotton Valley Union, Black River, Plymouth, Woodmore, Sandy Valley and Mogadore (`extras.school_district_county_differences`). We use ODEW's county. Two districts not in the ODEW file (College Corner Local and Kelleys Island Local) use the Census county code (`CONUM`). Each district counts in one county only.

**Changes over time.** Fiscal 2022 and 2023 include large federal pandemic relief (ESSER) funds; Ohio's federal share (Table 1, all systems) falls from 14.0% in 2021-2022 to 11.8% in 2023-2024. Column order differs between years (the 2022 file has an extra `IDCENSUS` column), so the script reads columns by name.

**Suppressed, censored or masked values.** None. In the fiscal 2024 flag file (`elsec24f.xlsx`), Ohio revenue items are marked "R" (as reported by the state). One district's instructional staff support spending, a part of current spending, is marked "I" (imputed); other imputed items are debt, interest and salary detail, which we do not use. Enrollment is flagged "S" (from another source, the NCES Common Core of Data) for 702 systems and "N" (not applicable) for 9.

**Missing data.** None for traditional districts in the fields we use. The Census Bureau says it fills missing items by carrying forward the prior year. We checked flags for fiscal 2024 only.

**Revisions.** The Census Bureau posts errata notes but does not reissue past years as a rule. We use each year's file as posted.

**Units and rounding.** Thousands of dollars; enrollment in students. Shares are percents (0-100).

**Known quirks.**
- The Census Bureau warns that per-pupil spending can mislead because districts classify costs differently, and that revenue shares reflect how each state funds schools, not how committed it is.
- The Table 8 footnote says per-pupil enrollment is fall 2022 membership, but the technical document says fall 2023. The district file's `V33` is the fall membership the Census Bureau used. Ohio's fiscal 2024 per pupil from the district file ($17,268 for all systems) is within 0.1% of Table 8 ($17,257).
- Ohio's revenue shares: our method applied to all 711 systems reproduces Table 1 exactly (federal $3,709,527 thousand; total $31,534,772 thousand after removing $720,493 thousand of revenue from other school systems).
- Small districts with large local tax bases have high per-pupil spending (Monroe County, home of Switzerland of Ohio Local, is highest at $29,135 in 2023-2024).

**Uncertainty.** These are reported accounts, not samples, so there are no sampling errors. The Census Bureau notes nonsampling error from reporting differences.

**License and attribution.** Public domain. Credit: U.S. Census Bureau, Annual Survey of School System Finances.

## Denominators: population and households (U.S. Census Bureau)

**Population for county and Ohio per-resident figures.** Census July 1 estimates of the same year as the spending. 2020-2025 come from `data/processed/popest.json` (vintage 2025; see `docs/datasets/popest.md`). 2010-2019 come from the 2010-2020 intercensal estimates, `https://www2.census.gov/programs-surveys/popest/tables/2010-2020/intercensal/county/co-est2020int-pop-39.xlsx` (released November 2024), which revise the earlier estimates to agree with the 2020 Census. Ohio uses the file's state row. BEA's own per-capita figures use older estimates, so our per-resident values will not match BEA's exactly.

**Households for the HUD measure.** ACS 5-year table B11001 (total households), county and state, from the Census Data API. Each HUD year uses the 5-year period ending that year (2015 uses 2011-2015); 2025 uses 2020-2024, the latest available. ACS figures are survey estimates with margins of error.

**Tract denominators.** ACS 2020-2024 5-year B11001 (households) and B01003 (total population) for every Ohio tract, 2020 geography. The Census Bureau does not publish July 1 estimates for tracts, so tract spending per resident uses the ACS count. Tract values are not directly comparable with county values, which use July 1 estimates.

## Ohio Community Well-Being page (derived from the sources above)

**What it is.** One page, `dist/wellbeing/index.html`, that shows every measure in its own units for Ohio's 88
counties, its 15 congressional districts and its 3,162 land 2020 census tracts, in nine areas of daily life
(child care, education, economic security, jobs and workforce, housing, physical health, mental health, public safety
and social well-being). Built by `scripts/70_wb_geo.py`, `71_wb_data.py` and `72_wb_build.py`. The measure list,
each measure's area and role, and the published standards are in `scripts/wellbeing_measures.py`;
`docs/MEASURES.md` is written from it. There is no combined score.

**Roles.** Each measure is "what residents experience" (conditions), "services and access" (what is available and
whether people use it) or "public money" (what public programs spend or pay out). Public money is shown beside
conditions; the page says it does not show what the money caused.

**Map shapes.** Census TIGERweb 2020 tracts and counties, simplified by the server (about 40 meters). Congressional
districts: the Ohio Redistricting Commission's block assignment file for the map adopted October 31, 2025, joined to
2020 census block population; every district's 2020 population is 786,629 or 786,630 and the blocks sum to Ohio's
11,799,448. District outlines are TIGERweb Current layer 54 (120th Congressional Districts); every tract wholly in a
district by block population falls inside that outline except one (39035138105, District 7). TIGER county and
district shapes reach into Lake Erie, so the page clips the map to the land tracts. Tract names follow the district
pages (place with at least half the tract's 2020 residents, else township).

**Counties.** A measure already in a county layer is read from it, with its history. New American Community Survey
(ACS) measures (uninsured under 65, average commute, crowding, homeownership, vacancy, homes built before 1950,
broadband, households without a vehicle, children 3 and 4 enrolled in school) are pulled for counties, Ohio and the
U.S. for 2010-2014, 2015-2019 and 2020-2024 where the table exists (the internet table, B28002, has no 2010-2014
five-year release) and computed with the county layers' code (`20_acs.py`). Homes built before 1950 is found by
label, because B25034's line numbers for 1940-1949 and 1939-or-earlier shift by one in 2010-2014. Median household
income trends are in each period's own dollars; only the latest value is in 2024 dollars. The age and race shares on place profiles
use ACS at every level, so they differ slightly from the Census population estimates on the county dashboard.
Uninsured under 65 uses B27010's under-19, 19-34 and 35-64 groups (under-18 and 18-34 in 2010-2014).

**Tracts.** ACS 2020-2024 for every Ohio tract (one API call per table with `for=tract:*&in=state:39`), computed with
the same code. An estimate whose coefficient of variation is above 30% is marked uncertain and hatched. CDC PLACES
2025 release, tract crude prevalence, with ± as half of CDC's 95% interval; 4 populated tracts have no PLACES value.
An estimate of zero is never marked, because its coefficient of variation cannot be computed; its margin of
error is shown instead. HUD Picture of Subsidized Households 2025 tract values come from `public_money.json`.

**Congressional districts.** No published estimates exist for the 2025 lines. Each ACS table line is summed over
the tracts with district residents, weighted by the share of each tract's 2020 residents inside the district;
margins of error are weighted the same way and combined as the square root of the sum of squares. The same 30%
coefficient-of-variation rule marks uncertain county and district values. Twenty Ohio tracts have no aggregate
travel time (B08013); 10 of them have residents (8 with no commuters, 2 with 3 and 5). A district's average commute
uses its other tracts in both the numerator and the denominator. District median household income has no margin of
error; the page shows none. Median household
income is interpolated from the district's income brackets (B19001); the same method gives 71,503 for Ohio against
the published 71,389; districts are compared with the published Ohio median, and the footer says so. District 10's values match the OH-10 page exactly. PLACES: tract values weighted by adults 18
and older times the same share. 112 tracts are split between districts. Measures published only for whole counties
are not shown for districts.

**CDC PLACES at all three levels.** Crude prevalence (not age-adjusted) everywhere, so levels compare. County values
are CDC's county estimates (dataset swc5-untb, 2025 release); the county dashboard shows the age-adjusted ones, so the
two pages differ slightly. Ohio is the tract values weighted by adults 18 and older, since CDC publishes no state
value in this form. CDC says estimates from different PLACES releases should not be compared over time, so PLACES
measures have no trend line.

**Child care.** Licensed centers, family child care homes and preschools open on the pull date (the 41_childcare.py
snapshot of the DCY list; school-age-only programs left out), placed in tracts by their geocoded address: 7,706
programs. Placement uses full-resolution 2020 TIGER tract shapes (the map's simplified shapes missed 39 points near
tract edges and the lake shore). County values come from the tract each program falls in, not DCY's county field; 33 programs geocode
into a different county than the one DCY lists (mostly Franklin-listed programs in neighboring counties), so this
page's county figures differ from the county dashboard's for 19 counties. For districts, a split tract's programs
count by the share of its 2020 residents in each district, the same weight used for survey lines. Programs per 1,000 children under 5 (ACS B01001) and the share rated Silver or Gold in Step
Up To Quality (unrated programs count as not Silver or Gold). Shown for counties and districts only: a tract is too
small an area, since families often use care outside it.

**Standards.** Healthy People 2030 national targets, used only where the measure is close: uninsured under 65 (7.6%,
from AHS-01's 92.4% insured), adult smoking (6.1%, TU-02), drug overdose deaths (20.7 per 100,000, SU-03), suicide
(12.8, MHMD-01) and traffic deaths (10.1, IVP-06). Most targets are age-adjusted and come from national surveys; the
local figures for smoking, overdose and traffic deaths are not age-adjusted, and each note says so. Obesity and
dental visits have targets but are left without one, because the target's measure differs too much (measured weight
for adults 20+; dental visits for ages 2+).

**Comparisons and colors.** "Near Ohio" means within 3% of Ohio's value, or 0.3 points for percentages. For measures
with a better and worse direction, map colors step at 3%, 10% and 25% of Ohio's value and the legend gives the breaks
in the measure's units. Measures without a direction, and public money, use fifths of the places at the current level.

**Trends.** County history where the county layer has it (and the three ACS periods for new ACS measures). Tract
lines changed in 2020 and the district lines are new, so a tract shows its county's trend and a district shows
Ohio's.

## Georgia Community Well-Being page (same build, Georgia sources and differences)

**What it is.** `dist/georgia/index.html`, built by the same scripts as the Ohio page with `D4TP_STATE=ga`
(settings in `scripts/states.py`). It covers Georgia's 159 counties, its 14 congressional districts and its 2020
census tracts, with the same measures, roles, standards, colors and comparisons as the Ohio page, except where
noted here. Georgia's layer files are in `data/processed/ga/`; its raw downloads go in `data/raw/ga/`. Files
that cover the whole nation are shared with Ohio. `docs/MEASURES_GA.md` is written from the measure list.

**Congressional districts.** The map Georgia enacted in December 2023 after a federal court ruling, first used in
the 2024 election, from the Census Bureau's 119th Congress block assignment file (`NationalCD119.txt`), joined to
2020 census block population. Every district's 2020 population is 765,135 to 765,137, and the blocks sum to
Georgia's 10,711,908. Georgia has no township governments, so a tract outside a census place is named by its county.

**Schools (`scripts/47_schools_ga.py`).** Georgia Governor's Office of Student Achievement (GOSA) open files at
https://download.gosa.ga.gov/, one folder per year:
- Georgia Milestones End-of-Grade results by grade (`EOG_by_GRADE` files), school years 2017-2018 to 2024-2025.
  There was no test in 2019-2020.
- Attendance files for the same years.

Proficient or above means Proficient plus Distinguished. Third grade results use the "All Students" rows at the
system level (`INSTN_NUMBER` = ALL). County figures add up proficient students and tested students over:
- the county school system,
- any city school systems in the county, and
- in-person state charter schools in the county.

Each system's county comes from the NCES Common Core of Data district directory (Urban Institute Education Data
Portal). The county systems are codes 601 to 759, numbered almost in alphabetical order (Georgia lists McDuffie and
McIntosh after Marion), so the county comes from the directory, not the code. Atlanta Public Schools is placed in
Fulton County, where the directory puts it. Some systems are left out:
- virtual state charter schools (the CCD virtual flag for the same school year, or the nearest year CCD has; two
  in-person schools were flagged virtual only in 2019-2020),
- the state schools (code 799), and
- systems with no count of students tested.

When GOSA suppresses the proficient counts ("TFS") but gives the number tested and the percentages, the proficient
count is the number tested times the Proficient and Distinguished percentages. That is how the smallest counties
(Quitman, Taliaferro, Echols) get values.

Chronic absence is the share of students absent more than 10% of the days they were enrolled. It uses county and
city systems only, weighted by GOSA's student count. This matches Ohio, where only traditional districts are used.
The year 2019-2020 is left out because school buildings closed in March 2020.

The Georgia figure is built the same way from the same systems. It is within 0.3 points of GOSA's own statewide
figure in every year, and GOSA's figures are kept in the layer's extras. In 2024-2025, 8 counties tested fewer than
30 third graders, and their notes say so. Georgia began testing new math standards in 2023-2024.

**SNAP (FNS-388A county file).** FNS codes Echols County as 13100 instead of 13101, so that row is placed by county
name. The July 2024 file has no Georgia rows. The July 2025 Georgia county lines add up to 28% more than FNS's
Georgia total for that month. Georgia's county series therefore stops at July 2023, for counties and the state alike.
The Georgia figure comes from FNS's state table, as Ohio's does; in July 2023 the county lines add up to the same
total.

**Libraries (IMLS Public Libraries Survey).** Most Georgia library systems are regional and serve several counties
from one main office. Each system's spending and visits are split among the counties where it has a central or
branch library, by population, so every county in a regional system shows that system's per-person figure. A
building's county is the county name IMLS lists for it; three branches sit just across a county line from it (East
Atlanta and Kirkwood of the Fulton system are in DeKalb, and Maysville of the Jackson system is in Banks). Population
is the Census July 1 estimate for the same year. Georgia's library fiscal year runs July to June.

**HUD Picture of Subsidized Households.** Tract values come from HUD's `TRACT_AK_MN` file (Ohio uses `TRACT_MO_WY`).
HUD's county files have no row for Echols County in any year from 2015 to 2025, for Webster County in 2021 or for
Glascock County in 2022, so those values are blank.

**School finance (Census Annual Survey of School System Finances).** Local school systems are the rows with school
level codes 01, 02, 03 or 06, placed in the county the Census file gives (it agrees with CCD for every system). Clay and Webster are coded 01 and Taliaferro is coded 06. The regional educational
service agencies (07) are left out. State charter schools are not in this survey.

**Crime (FBI Return A).** Georgia's UCR state code is 10. Georgia State Patrol posts (ORI prefix GAGSP) are left out
of county totals, as the Ohio State Highway Patrol is for Ohio. The files number counties in FIPS order (McDuffie and
McIntosh before Macon), which was checked against known agencies (Atlanta in Fulton and DeKalb, Savannah in
Chatham, Augusta in Richmond, Thomson in McDuffie). Reporting coverage fell in 2019 as Georgia moved to the FBI's
newer reporting system, and many counties are below 80% coverage in later years. The same coverage rules as Ohio
apply, with one addition for Georgia and Illinois. A month marked as reported but with no burglary, theft or vehicle
theft at all counts as not reported when the agency averages 10 or more of those crimes in its other reported months.
Savannah's 2025 file is marked complete but has no thefts in 8 months, so Chatham County is shown as low reporting
for 2025.

**Age (ACS table B23001).** The sanity check on county margins of error allows up to 20 points, against 10 for Ohio.
Georgia's smallest counties have about 1,500 to 3,000 residents.

**Child care.** The Georgia Department of Early Care and Learning (DECAL) provider export, saved by hand from
https://families.decal.ga.gov/Provider/Data into `data/raw/ga/decal/`. Licensed child care learning centers and
family child care learning homes serving children under 5 are geocoded with the Census batch geocoder. The rated
share counts Quality Rated programs with 2 or 3 stars. Until that file is saved, the page has no child care
measures for Georgia.
