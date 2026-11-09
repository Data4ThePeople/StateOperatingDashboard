# Datasets: ACS layers (income.json, people.json)

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
period is in dollars of its final year (2014, 2019, 2024), with no inflation adjustment. Income brackets in
`extras.income_distribution` are the same nominal dollar cutoffs in every period, so part of any shift up
the brackets is inflation.

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
