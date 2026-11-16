# Datasets: schools layer

Built by `scripts/44_schools.py` into `data/processed/schools.json`. It reads the same ODEW files the reading layer uses, which were downloaded by hand into `data/raw/odew/`. The script does not fetch them. It reads the reading layer's cached CCD pulls in `data/raw/urban_ccd/`. Built 2026-11-16.

Two measures are built: third graders proficient in math (`grade3_math_proficient`) and students chronically absent (`chronic_absent_rate`). Three asked-for pieces are not built, because the files are not on disk: the four-year graduation rate, chronic absence for 2019-20 through 2024-25, and kindergarten readiness. The last section lists the files that would add them.

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
- Math, same as the reading layer: an average of district and in-person community school percents, weighted by grade 3 fall enrollment from CCD (next section). Online (virtual) community schools are left out, because their students live all over the state. Seven schools are left out.
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

## Files that would add the missing measures

All are on the same ODEW "Download Data" page and would be saved by hand into `data/raw/odew/`. The script does not read them yet.
- Four-year graduation rate: `1819_DISTRICT_GRAD_RATE.xlsx`, `1920_`, `2021_`, `2122_`, `2023_`, `2024_`, `2025_` and `2026_DISTRICT_GRAD_RATE.xlsx` (District Data), and the matching `*_CS_GRAD_RATE.xlsx` files (School Building Data). ODEW labels a graduation file by the report card year, and the four-year rate in it is usually for the class that graduated the year before. That needs to be checked in the files.
- Chronic absence, 2021-22 through 2024-25: `2122_District_Details.xlsx`, `2023_`, `2024_` and `2025_District_Details.xlsx`. For 2019-20 and 2020-21, `DISTRICT_HIGH_LEVEL_1920.xlsx` and `20-21_Achievement_District.xlsx` may carry it. For community schools, the `*_Building_Details.xlsx` files.
- Kindergarten readiness: the download site lists file types named "District Kindergarten Readiness Assessment (KRA) Data" for 2023-24 and 2024-25, but in November 2026 its file list showed no files attached to them. The achievement and District Details files do not carry KRA results.
