# Datasets: health layer (and annual income and poverty)

Built by `scripts/30_health.py` into `data/processed/health.json`. Raw pulls are cached under
`data/raw/census/`, `data/raw/cdc/` and `data/raw/census_pep/`. Pulled 2026-11-09.

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
