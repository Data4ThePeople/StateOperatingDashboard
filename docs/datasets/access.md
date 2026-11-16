# Datasets: access and community layer (access)

Built by `scripts/45_access.py` into `data/processed/access.json`. Raw files are cached under
`data/raw/chr/`, `data/raw/fars/`, `data/raw/imls_pls/`, `data/raw/medsl/`,
`data/raw/popest_intercensal/` and `data/raw/census/` (County Business Patterns and ACS calls).
Pulled 2026-11-16.

Metrics, all "higher is better" except suicide and traffic deaths:

| Metric | Source used | Latest period |
|---|---|---|
| `pcp_per100k` | CHR&R, from HRSA Area Health Resources Files (AMA data) | 2022 |
| `dentists_per100k` | CHR&R, from HRSA Area Health Resources Files (CMS NPI data) | 2023 |
| `mh_providers_per100k` | CHR&R, from CMS NPPES (NPI file) | 2025 |
| `suicide_rate` | CHR&R, from CDC NCHS mortality files | 2019-2023 |
| `traffic_deaths_per100k` | NHTSA FARS, our calculation | 2019-2023 |
| `library_spend_per_capita`, `library_visits_per_capita` | IMLS Public Libraries Survey, our calculation | FY 2024 |
| `social_associations_per10k` | Census County Business Patterns, our calculation (CHR&R definition) | 2023 |
| `voter_turnout` | Ohio Secretary of State results via MIT Election Data + Science Lab; ACS citizen population | Nov. 2024 |

Population denominators for our own calculations: Census Vintage 2025 estimates from
`data/processed/popest.json` for 2020 on, and the 2010-2020 intercensal estimates for 2015-2019
(see the last section).

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

**Suppressed, censored or masked values.** A county-industry cell with 1 or 2 establishments is dropped, not shown as a number. We cannot tell a dropped cell from a true zero, so we count it as zero. This undercounts small counties. The 88 counties add up to 12,442 in 2023, 294 fewer than the state count of 12,736.

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
