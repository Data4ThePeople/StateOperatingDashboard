# Datasets: public safety layer (crime)

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

## Sources checked and not used

- **CDE API at api.usa.gov.** Works with `DEMO_KEY`, but the limit was 10 requests per hour, too low for about 950 agencies. Without a key it returns 403. The CDE site's own backend (`cde.ucr.cjis.gov/LATEST/...`) answers without a key, and we used it only to check our reporting flags and counts.
- **Ohio Office of Criminal Justice Services (OIBRS).** The OCJS website returned "not found" to plain scripted requests on 2026-11-09, so we could not reach its OIBRS data or dashboards. Ohio agencies' OIBRS data reach the FBI through the state program, so the FBI files carry the same reports in a form that is consistent across states and years.
