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

**Added after the tie-out, not yet re-checked by it.** Inflation adjustment of the income-distribution chart
(R-CPI-U-RS, see DATASETS.md), with a switch back to as-published dollars. Label change: `below_200_share` is
now "People below 200% of the poverty line" (values unchanged).

## Added after the independent tie-out, not yet re-checked by it (November 9, 2026)

- `scripts/23_age.py`: residents 25 to 54, residents 65 and older, prime-age workers (ACS B23001), fertility rate
  (births per 1,000 women 15 to 44), and the group-quarters flag on prime-age workers (ACS B26001, 5% threshold).
  Claude's own checks: county births sum to Ohio's births; B23001 found 8 total, 8 employed and 8 armed-forces
  lines in each of 2014, 2019 and 2024. These need the independent tie-out before Step 1 closes.
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
