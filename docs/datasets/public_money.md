# Datasets: public money layer

Built by `scripts/46_public_money.py` into `data/processed/public_money.json` (theme "money"). Raw files are cached under `data/raw/bea_cainc35/`, `data/raw/hud_picture/`, `data/raw/census_school_finance/`, `data/raw/popest_int/`, `data/raw/urban_ccd/` and `data/raw/census/` (files named `public_money_*`). Pulled 2026-11-16.

The layer shows what public programs spend in each place. It sits next to the conditions in other layers and is not a cause of them. Each program is its own measure. No measure adds programs together, and the tax credit (EITC) is never added to benefits. Every spending measure has `better: "none"`. Dollars are not adjusted for inflation.

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

**Coverage.** In fiscal 2024 the file has 711 Ohio school systems (710 in fiscal 2022): 609 traditional districts, 49 joint vocational districts, 51 educational service centers and 2 nonoperating districts (Middle Bass and North Bass). County figures use the traditional districts only (609 in each year). Joint vocational districts and service centers serve students from several counties, and service centers report no enrollment, so they are left out of counties. Community (charter) schools run by nongovernmental bodies are outside the survey. Ohio's figures are the Census Bureau's own state figures (Table 8 for per pupil, Table 1 for revenue), which include all school systems. For a like-for-like comparison, `extras.school_ohio_traditional_districts_only` has the statewide traditional-district figures (fiscal 2024: $16,217 per pupil against $17,257 in Table 8).

**County assignment.** As in `scripts/40_reading.py`, a district goes to the county named in Ohio's own files: the Census NCES ID is matched to Ohio's district number (IRN) through the NCES Common Core of Data directory (Urban Institute Education Data Portal, cached in `data/raw/urban_ccd/`), and the IRN to the county in ODEW's `2026_District_Details.xlsx`. For 9 districts that cross county lines, ODEW and the Census county code differ: Delphos City, Fostoria City, Bradford, Conotton Valley Union, Black River, Plymouth, Woodmore, Sandy Valley and Mogadore (`extras.school_district_county_differences`). We use ODEW's county. Two districts not in the ODEW file (College Corner Local and Kelleys Island Local) use the Census county code (`CONUM`). Each district counts in one county only.

**Changes over time.** Fiscal 2022 and 2023 include large federal pandemic relief (ESSER) funds; Ohio's federal share falls from 14.0% in 2021-2022 to 11.8% in 2023-2024. Column order differs between years (the 2022 file has an extra `IDCENSUS` column), so the script reads columns by name.

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
