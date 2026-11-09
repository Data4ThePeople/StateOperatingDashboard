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
