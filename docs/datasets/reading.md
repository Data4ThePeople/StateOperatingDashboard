# Datasets: reading layer

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
