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
- Ohio Community Well-Being page (DATASETS.md "Ohio Community Well-Being page") and the three new county layers
  (`44_schools.py`, `45_access.py`, `46_public_money.py`): not yet through any independent tie-out. Claude's checks:
  district block populations sum to Ohio's official 2020 count; District 10 values match the OH-10 page exactly;
  ACS Ohio values equal the county layers' Ohio values for every measure both build from the ACS; BEA counties add to BEA's Ohio row for
  every line and year; school revenue shares match Census Table 1; the page renders every measure at every level
  without a script error.
