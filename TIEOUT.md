# Tie-out

## Independent tie-out, November 9, 2026

A fresh agent that had not seen the build re-pulled every source from the publishers, recomputed with its
own code, and compared against the data embedded in `dist/index.html`. It did not read `scripts/` or
`data/processed/`.

**Numbers.** All 47 measures for all 88 counties and Ohio (4,183 values) match at displayed precision.
History points match for LAUS 2017-2025, ACS 2010-2014/2015-2019/2020-2024, QCEW 2019 and 2025, SAHIE
2008-2024, SAIPE 2000-2024 and overdose counts each December. Suppressed cells match the publishers'
suppression. Derived checks match: Pike County worst-fourth count, two "worse than Ohio" badges, and the
concentration callouts for Pike (waste management, 22.9%) and Vinton (social assistance, 19.8%).

**Words: fixed after the tie-out.**

| Finding | Fix |
|---|---|
| "Near Ohio" tolerance described as 0.3 points; code uses the larger of 3% and 0.3 points | Note says "whichever is larger" |
| "Publisher's own statewide figure" not true for PLACES (median county) or overdose (deaths in Ohio vs residents) | Both exceptions named in the notes and in the overdose note |
| Ohio overdose figure carries CDC's "underreported due to incomplete data" mark, not shown | Flag shown on the Ohio tile |
| Overdose rate ranked among 43 counties but counted in "worst fourth of 88" | Removed from the overview count (now 14 measures) |
| "Just above the poverty line" for 100% to 199% | Label now "Near poverty: people at 100% to 199% of the poverty line" |
| "Health care share" is NAICS 62, which includes social assistance | Label now "Health care and social assistance share of private jobs" |
| Weekly wage note omitted federal civilian jobs | Note corrected at the source |
| SAHIE low income said "in households" | Now "with income at or below 200% of the poverty line" |
| HHI "11 NAICS supersectors" | Now "10 private NAICS supersectors plus BLS's unclassified group" |
| Margins of error described but never shown | Tiles now show ± (90%) where the publisher gives one |
| "Getting worse" base for ACS fell back to 2010-2014 | Base is now the period ending in 2019 (2015-2019 for ACS) |
| Components column "Moved in from abroad" is net | Now "Net international migration" |
| "A single statewide policy could reach the most people" is an inference | Replaced with "shows which problems are shared across many counties and which sit in a few" |
| Concentration callout too firm where many jobs are withheld | Now "Among the industries BLS publishes for this county, the largest is..." when flagged |
| DATASETS.md said PLACES Ohio entries are null | Corrected to the median-county method |

**Could not check.** Whether CDC's state overdose file counts by place of occurrence (dataset description
does not say outright); exact PLACES measure wording (file gives short names only); margin-of-error values
themselves; whether SAHIE's income-to-poverty ratio uses family or household income; map color breaks and
reach-table population totals (inputs match; outputs not recomputed).

**Added after the tie-out, checked by the second tie-out below.** Inflation adjustment of the income-distribution chart
(R-CPI-U-RS, see DATASETS.md), with a switch back to as-published dollars. Label change: `below_200_share` is
now "People below 200% of the poverty line" (values unchanged).

## Second independent tie-out, November 9, 2026

Three fresh agents, with no access to the build code, re-pulled every source and recomputed everything added after
the first tie-out (the list below), plus the Priorities tab logic and the inflation switch.

**Numbers.** No differences: 8,804 Census values (age, race and ethnicity, sex, foreign-born, prime-age work, the
U.S. and all 51 state values), every reading, SNAP, child care and crime value, all 48 price index values and every
BLS and CDC state benchmark match exactly. Not checked: the ODEW files were read from the saved copies (the site
needs a sign-in token); CCD fall 2025 (the API returned errors); FNS files before 2021; the crime reporting-month
rule was checked on a sample of 30 agencies against the CDE site, not every agency.

**Fixed after the second tie-out (November 17, 2026).**

| Finding | Fix |
|---|---|
| When a county's latest value was blank, the page still showed a change between two earlier years. This put 9 counties in "getting worse" on Addiction and 4 on Public safety; the right count is 0. A blank base year was replaced by the next year with data. | A change is shown only when both the latest and the base-period value exist. Addiction and Public safety now show 0 counties getting worse in both windows. |
| Ohio's crime figure was the FBI statewide estimate, built differently from the county rates, which made counties read about 6% worse. | Ohio is now built the same way as the counties: 293.8 violent and 1,513.3 property crimes per 100,000 in 2025 (FBI estimate 275.6 and 1,428.8, named in the note). The Ohio series now runs from 2015. |
| "Typical gap" and "typical rank" took the upper middle value, not the median. | True medians, labeled "median". |
| Ohio's rank among states broke ties alphabetically (42nd of 51 on unemployment). | Tied states share a rank: 40th of 51, tied with 2 other states; uninsured under 65, 21st, tied with 3. |
| Two county groups had the same name. | Names extend until they differ. |
| "A group that shares the same problems may be served by the same kind of effort" implies cause. | Removed. |
| "Counties that are struggling the most" overstates a count of issues. | "Counties behind Ohio on the most issues", with a note that it counts issues, not how far behind. |
| Notes said "behind Ohio" where CDC PLACES measures compare with the median county. | Notes name the median county for those measures. |
| "Residents born outside the U.S." is the wrong term for the measure. | "Foreign-born residents", with the definition on the page. |
| The two-or-more-races measure shared a note saying groups are people who reported one race. | Note covers both, and says the groups add to 100% before rounding. |
| "Reading at grade level" is an interpretation. | ODEW's term: "proficient or above in English language arts". |
| Reading note said Ohio is built "from all districts and schools". | "From the same districts and schools"; it now also says the latest year uses the prior fall's enrollment and that a district counts in one county. |
| Property crime "closest to petty crime" could mislead; crime notes left out three cautions. | Removed; notes now name zero-population agencies, multi-county splits and later FBI revisions. |
| Prime-age work note: "those residents rarely hold jobs" is over-certain. | "Most of those residents are not in the labor force, which can pull the rate down." |
| 15 counties' foreign-born shares have a coefficient of variation above 30% but were not flagged. | Flagged, the same rule as the other ACS measures. |
| DATASETS.md: "Ten groups" (there are nine); "all 33 measures matched" (41); "the publisher's own U.S. figure in every case" (race, sex and fertility are built); B23001 label claim; the reporting-month rule and aggravated-assault fields not named; Hocking's 5.7% masked share is an artifact; Put-in-Bay masked every year; ODEW gap 1.9 to 2.6 points; virtual-school rule; Priorities factors, cap, blank gaps and grouping sensitivity not described. | All corrected in DATASETS.md. |

**Noted, not changed.** The headings "What to work on" and "Where to work" read as directions; the subtitle says the
order is a way to sort, not a verdict. The county groups are sensitive to starting points (other starts agree on
about half of county pairs); DATASETS.md now says so. The group-quarters flag uses all residents while the rate
covers ages 25 to 54. Hocking, Ross and Vinton SNAP shares are blank (the combined share is in the data but not
shown). The child care count is a raw count, so it tracks county size.

## Checked by the second independent tie-out (added November 9, 2026)

- `scripts/23_age.py`: residents 25 to 54, residents 65 and older, prime-age workers (ACS B23001), fertility rate
  (births per 1,000 women 15 to 44), and the group-quarters flag on prime-age workers (ACS B26001, 5% threshold).
  Claude's own checks: county births sum to Ohio's births; B23001 found 8 total, 8 employed and 8 armed-forces
  lines in each of 2014, 2019 and 2024. 
- `scripts/40_reading.py`: third graders proficient or above in English (ODEW report card files, weighted by NCES
  grade 3 enrollment). Ohio's value is our enrollment-weighted sum of the same district and school figures
  (65.9% in 2025-26), not ODEW's published 63.4%, so counties compare with a number built the same way.
  Claude's checks: prior-year columns match each earlier year's own file; county assignment matches ODEW's
  District Details file for all 607 districts; Vinton equals its single district (82.9%).
- `scripts/42_enrollment.py` (SNAP persons, FNS July counts), `scripts/41_childcare.py` (open licensed programs,
  DCY), `scripts/43_crime.py` (violent and property crime, FBI Return A, 80% coverage rule),
  `scripts/50_national.py` (Ohio against all states; every Ohio value matched the page's).
- Priorities tab logic in `scripts/template.html` (issue gaps, "behind" rule, weights, county groups, change window).
- `scripts/24_demographics.py`: race and ethnicity (six groups, Census estimates), female share, and
  foreign-born share (ACS B05012). Claude's checks: the six groups add exactly to total population in every
  county and year; Franklin 56.0% White not Hispanic, 24.0% Black not Hispanic, 8.9% Hispanic, 13.0% foreign-born.
- Labels: the three population-change rates now say "since 2020" (values unchanged; they were already sums
  from April 2020, as their notes said).
- `scripts/50_national.py`: U.S. and state figures for the six race and ethnicity groups, female share and
  foreign-born share. Ohio's value from the state files matches the county-built value for all eight.
## Not yet through an independent tie-out

- Congressional district pages (OH-10 and IL-6, DATASETS.md "Congressional district pages"): not yet through any
  independent tie-out. Claude's checks: block sums equal the official 2020 counts for both districts; IL-6's outline
  agrees with block assignment for every whole-inside and zero-resident tract; IL-6 figures built from tracts agree with
  the Census Bureau's published district estimates on 23 of 24 measures (Black, not Hispanic: 5.3% built, 5.0%
  published); OH-10's bracket-interpolated median is within 0.2% of Ohio's published median when applied to Ohio.

## Independent tie-out of the Ohio Community Well-Being page, November 17, 2026

Two fresh agents, with no access to the build code, the processed data or Claude's numbers, re-pulled the sources
and recomputed the page (`dist/wellbeing/index.html`) and the three new county layers (`44_schools.py`,
`45_access.py`, `46_public_money.py`).

**Numbers that matched.**
- ACS 2020-2024: 27 measures for 88 counties (2,376 values and 2,376 margins), Ohio and the U.S.; 26 measures for all
  3,162 tracts (82,212 values and every margin); the 30% uncertainty marking on every tract.
- Districts: the block file joins to 276,428 census blocks with none left over; blocks sum to 11,799,448; every
  district has 786,629 or 786,630 people; tract residents by district match for all 3,162 tracts; 25 of 26 ACS
  measures and median income match in all 15 districts; all 14 PLACES measures match in all 15.
- CDC PLACES: 44,268 tract values and their ±, 1,232 county values and their ±, and all 14 Ohio values.
- Schools: 801 math values and 356 chronic absence values. Access: every doctor, dentist, mental health provider,
  suicide, traffic death, library, membership group and turnout value, with the suppression rules as written.
- Public money: every BEA line 2010-2022, every HUD county and tract value, every school finance value. All five
  Healthy People 2030 targets and objective codes match health.gov.
- No em dashes; no claim that spending caused or did not cause an outcome.

**Fixed after the tie-out (November 17, 2026).**

| Finding | Fix |
|---|---|
| Average commute was blank for 8 of 15 districts, because the Census Bureau withholds aggregate travel time for 10 tracts with 0 to 5 commuters. | Those tracts are left out of both parts of the ratio. All 8 districts now match the checker's values (for example District 1, 23.8 minutes ±0.6). |
| 39 child care programs were dropped because the map's simplified tract shapes missed points near edges and the lake shore. | Programs are placed with full-resolution tract shapes; all 7,706 are placed. Ohio is now 11.51 per 1,000 children under 5 (was 11.45); Monroe 14.54 (was 12.92). |
| The 200%-of-poverty note gave $62,400, which is from HHS poverty guidelines, not the Census thresholds the measure uses. | "For two adults and two children in 2024, 200% of the Census Bureau's poverty threshold was about $63,600" (thresh24: $31,812). Same fix on the district pages. |
| County and district values were not marked uncertain by the 30% rule; 70 county values qualified. Noble County showed the raw code "high_moe". | The rule now applies at every level; uncertain values are hatched and the legend counts them. No raw codes show. |
| Ohio figures built differently from the counties: school spending per pupil and revenue shares (all school systems), and membership groups (the state count, which includes places withheld in county cells). For membership groups this changed the comparison for 4 counties. | Ohio is built the same way as the counties: $16,217 per pupil (published $17,257), 34.9% state share (34.6%), 10.54 membership groups per 10,000 (10.79). Published figures are named in each note. |
| School spending note said community schools are in Ohio's figure; they are not in the Census survey. | Corrected. |
| Footer said Ohio always uses the same method; district median income is from brackets while Ohio's is published. | Footer names the exception ($71,503 by brackets, $71,389 published). |
| HUD measures shown for tracts but not districts, with no reason given. | Footer explains: too many tract values are withheld for a complete district total. |
| Wording: "rarely hold jobs" and "which pulls this rate down" (prime-age work); "some households choose not to own one" (no source); reading note's "most likely because"; doctors note missing "general"; the uninsured target's "same age group" (not confirmed); the traffic target counts deaths where people lived. | All reworded or removed; the traffic target note now names the place-of-residence difference. |
| Footer listed "Census Bureau population estimates" five times; the tract note for child care showed for only one of the two measures; zero estimates' treatment by the 30% rule was not stated. | Fixed; DATASETS.md now says a zero estimate cannot be judged by the rule and is not hatched. |
| DATASETS.md: "39 not placed", "only Noble County" crosses the 30% line, district child care split not described, "seven" online schools in the math layer (six have a math value). | Corrected. |

**Noted, not changed.** District 13's share of programs rated Silver or Gold is 44.3% after the fix; the checker got
43.8% with all programs placed. Both use the resident-share split for split tracts, so the gap is unexplained and
should be looked at in the next check. Ohio's HUD figures include the few hundred homes HUD could not place in a
county, and Ohio's turnout includes 2,771 write-in votes the county figures cannot include; both differences are
under 1%. Ohio has no margin of error shown for Gini or turnout. Not checked: the trend series for 2010-2014 and
2015-2019, map shapes and tract names, the OH-10 match, and the ODEW files (read from saved copies; the site needs a
sign-in token).

## Recheck of the Well-Being fixes, November 17, 2026

A fresh agent, with no access to the build code or Claude's numbers, recomputed only what changed after the
tie-out above and what it had not covered. No wrong numbers.

- Average commute: 15 of 15 districts match, value and margin, within 0.0005.
- Child care: 7,706 programs counted and all 7,706 placed in full-resolution TIGER/Line tracts; 88 of 88 counties,
  15 of 15 districts and Ohio match on both measures. District 13's Silver or Gold share is 44.3%, as the page shows;
  the earlier 43.8% came from the first checker's own calculation.
- Ohio school spending per pupil and state revenue share (all three years) and membership groups (all five years)
  are built the same way as the counties; the published figures named in the notes are correct.
- Uncertainty marking: 2,376 county and 390 district values, no differences (70 county values marked).
- Trends: 5,696 of 5,696 values for 2010-2014, 2015-2019 and 2020-2024 match.

**Fixed after the recheck.** Homes built before 1950 had no 2010-2014 point (the table's line numbers shift that
year; now found by label, Ohio 27.5%). The median income note said "2024 dollars" while the trend shows each period's
own dollars (note corrected). The draft notice claimed every figure was recomputed (reworded). The margin-of-error
line said only tracts are hatched (now every level). The footer's commute wording said "withholds" (8 of the 10
tracts have no commuters). A stray "ACS 2020-2024 (children under 5)" entry in the source list (removed). An
unsourced claim about lead paint in older homes (removed). DATASETS.md now says county child care counts come from
where each program falls (33 programs, 19 counties differ from DCY's county field) and that district median income
has no margin of error.

**Not checked.** The claim that the simplified map shapes missed 39 programs (not rebuilt). Map shapes and tract
names. ODEW files were read from saved copies (the site needs a sign-in token).

## Page split for speed, November 17, 2026

The Well-Being page now loads the tract layer from a second file (`dist/wellbeing/tracts.json`), writes county,
Ohio, U.S. and trend values with 8 significant digits (a value keeps full precision when shortening could change
how it shows at 0 to 4 decimals), and clips Lake Erie with one merged land outline instead of all 3,161 tract
shapes. No data changed: `data.json` is untouched. Claude rendered the old and new pages in Chrome and compared
every value, margin, hatching and map color for every measure at every county, district and tract; every map
card, ranking and legend; every place's profile on every tab; and every trend chart. All match except one trend
chart axis label: Morgan County rent burden's top gridline reads 56.2% instead of 56.3% (a computed axis value
near 56.25, not a data point). The new land outline matches the old clip on 29.19 million of 29.19 million land
pixels at full map scale; 217 pixels along the shore differ by 2 units or less, and 6,963 hairline gaps between
tracts are now filled.

## Compare two measures, November 17, 2026

The Well-Being page has a "Compare two measures" view: a scatterplot of every place at the current level, with the
mapped measure across and a second measure up, and a rank (Spearman) correlation in words. It is worked out in the
browser from the same values the map uses. Claude checked the page's place counts and correlations against pandas
(Pearson correlation of average ranks, from `data.json`) for five pairs at the county and tract levels, such as
people below 200% of poverty against adults in fair or poor health (0.88 for 88 counties and for 3,151 tracts) and
violent crime against poverty (0.50 for 59 counties). All match to two decimals. District counts (15) match; the
page gives no pattern for fewer than 30 places.

## Georgia Community Well-Being page, November 18, 2026

The Georgia page (`dist/georgia/`) is built by the same scripts as the Ohio page with `D4TP_STATE=ga`. Before
building it, Claude made the scripts state-aware and showed that Ohio did not change. Rerunning Ohio from cached
downloads reproduces every Ohio layer file, `tracts.json` and `docs/MEASURES.md` exactly, apart from pull dates. The
Ohio page renders the same values, maps, rankings, profiles and trend charts in all 1,867 views compared.

**Checked by Claude's own scripts (not independent):**
- **National checks.** All 41 Georgia figures in `50_national.py` match their county layers at display precision.
- **Schools.** Georgia figures built from the county and city systems are within 0.3 points of GOSA's published
  statewide figures in every year: grade 3 English 35.2 vs 35.1 in 2024-2025, math 44.5 vs 44.3, and chronic
  absence 20.2 vs 20.4.
- **District lines.** The 14 districts have 765,135 to 765,137 residents in 2020, and the blocks sum to 10,711,908.
  Every tract wholly inside a district falls within that district's TIGERweb outline.
- **Crime county codes.** Checked against known agencies, including the five counties whose order differs between
  sources (McDuffie, McIntosh, Macon, Madison, Marion).
- **Rendering.** The page renders without errors for every measure at every level, and for every county and
  district profile on every tab.

**Independent tie-out, November 18, 2026.** A fresh agent that had not seen the build pulled every source again
and recomputed 23 measures from the method in `DATASETS.md`. It covered ACS, LAUS, PLACES, GOSA, FBI, FNS, IMLS,
HUD, Census school finance and MEDSL, for Quitman, Taliaferro, Echols, Fulton, DeKalb, Chatham, Cobb, Ware and
Georgia, plus districts and tracts. It also confirmed that the page's embedded data matches `data.json` exactly.

Findings and fixes:
- **Third grade results (fixed).** Two in-person state charter schools, Dubois Integrity (Clayton) and Pataula
  (Calhoun), were left out as virtual because CCD flagged them virtual in 2019-2020 only. Each year now uses its own
  flag. Calhoun English is 32.3 (was 20.0), Calhoun math 36.8 (was 16.0) and Clayton math 22.5 (was 22.8), matching
  the agent.
- **Chatham County crime (fixed).** Savannah's 2025 file is marked complete but lists no thefts in 8 months, which
  gave Chatham an implausibly low rate. The new zero-month rule (DATASETS.md) treats those months as unreported, so
  Chatham shows as low reporting.
- **Method wording (fixed in DATASETS.md).** How suppressed GOSA counts are rebuilt, FIPS order in FBI county codes,
  HUD's missing Echols rows in every year, where the Georgia SNAP figure comes from, library building counties and
  population, and the school finance county.
- **Rounding at display edges (not changed).** Tract values are stored to two extra decimals, so a value like
  13.8504 is stored as 13.85 and can round the other way at one decimal. The same applies to the Ohio page.

All other values matched.

**Not checked.**
- BEA transfers, QCEW wages, County Health Rankings measures, FARS, County Business Patterns, SAIPE, overdose deaths
  and HUD spending.
- Trend lines.
- The SNAP 28% gap against FNS's state table.
- Map shapes.
- Child care: the DECAL file has not been saved yet, so the page has no child care measures.

## Illinois Community Well-Being page, November 18, 2026

The Illinois page (`dist/illinois/`) uses the same scripts with `D4TP_STATE=il`. Ohio's layer files and page data
were rerun after the Illinois changes and still match the earlier build exactly, apart from pull dates.

**Checked by Claude's own scripts (not independent):**
- **National checks.** All 41 Illinois figures in `50_national.py` match their county layers at display precision.
- **Schools.** Illinois figures built from district rows are within 0.4 points of ISBE's published statewide figures:
  - Grade 3 English: 47.9 vs 47.7 in 2025-2026, and 47.1 vs 47.3 in 2024-2025.
  - Grade 3 math: 49.5 vs 49.2 in 2025-2026.
  - Chronic absence: 23.8 vs 23.5 in 2025-2026, and within 0.4 points in every year.
- **District lines.** The 17 districts have 753,676 or 753,677 residents in 2020. Four lakeshore and Chicago tracts
  wholly in one district have their internal point just outside TIGERweb's simplified outline (17031030706,
  17031420100, 17031410900, 17031320600).
- **Turnout.** The county vote sum is within 919 votes of the official state total once non-vote rows and the
  uncounted write-in lump are left out.
- **Child care.** All 6,124 IECAM programs were placed in a tract.
- **Rendering.** The page renders without errors for every measure at every level, and for every county and
  district profile on every tab.

**Not checked yet.** No independent tie-out of the Illinois page.
