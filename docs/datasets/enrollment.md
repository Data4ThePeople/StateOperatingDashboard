# Datasets: enrollment layer

Built by `scripts/42_enrollment.py` into `data/processed/enrollment.json`. Raw files are cached under
`data/raw/fns/`. Pulled 2026-11-09. This layer has SNAP only. County Medicaid enrollment is not in it.

## SNAP county participation, form FNS-388A (USDA Food and Nutrition Service)

**What it is.** For each SNAP project area (in Ohio, a county agency), the number of people and households that got SNAP benefits in January and in July, plus the dollars issued. We use "Calc: SNAP Total PA and Non-PA People," the sum of people in households that also get cash aid (PA) and those that do not (non-PA). The metric `snap_persons_share` is that count divided by the Census July 1 population of the same year, times 100. The counts are in `extras.snap_persons_count`.

**Where it comes from.** FNS SNAP Data Tables page, `https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap`, section "Bi-Annual (January and July) State Project Area/County Level Participation and Issuance Data." File `https://www.fns.usda.gov/sites/default/files/resource-files/snap-zip-fns388a-2.zip` (14.8 MB zip, "FY 89 through July 2025"), one Excel sheet per month: `.xls` through 2019 and January 2021, `.xlsx` from January 2020. No login. FNS returned HTTP 403 to the script's Python request on 2026-11-09, so the zip was saved with curl to `data/raw/fns/` and the script reads it from there.

**Version and vintage.** The zip held January 1989 through July 2025 at pull time. The July 2025 sheet is dated 2026-02-12. FNS says January data is reported to it in May and July data in December, so the newest county month is about 16 months old by the time it is posted.

**Coverage.** All 88 Ohio counties appear as project areas, coded `39` + county FIPS + a two-digit office number. We use July 2021 through July 2025, one point per July. The population estimates run 2020-2025, and each July count is matched to the July 1 estimate of the same year, so the dates line up. These are counts from program records, not estimates.

**Changes over time.** Hocking, Ross and Vinton are served by one agency, South Central Ohio Job and Family Services. In every file from January 2020 on, nearly all of their cases sit on the Ross line (20,616 people in July 2025); the Hocking and Vinton lines hold between 0 and 42 people. We do not report a share for any of the three. They carry `null` with a flag, and `extras.snap_south_central_combined` holds one share for the three counties together (17.7% in July 2025). We did not check when this grouping began. Defiance and Paulding also share one agency, but FNS still reports them on separate lines with plausible counts, so we keep both.

**Suppressed, censored or masked values.** None. A few blank household cells appear (for example Vinton households in January 2025); the persons column has a number for every Ohio line in the years we use.

**Missing data.** None in the persons column for 2021-2025.

**Revisions.** FNS marks every sheet "Data is Subject to Revision. The data reflected is the latest available data." It replaces sheets in the zip when it revises; file dates inside the zip range from 2012 to 2026. We refresh the whole series by re-downloading the zip.

**Units and rounding.** People, whole numbers. The share is our calculation, stored at full precision.

**Known quirks.**
- Cuyahoga has two lines: the regular EBT office and an "SSI" line (6,504 people in July 2025), which we take to be SNAP for SSI recipients who apply through Social Security. We add them. With both lines included, the 88 counties add exactly to the FNS Ohio state total in every July from 2021 to 2025.
- July 2020 is left out. Ohio's statewide count that month (1,538,558) is about 10% above June 2020 (1,403,021) and August 2020 (1,399,895), and the county sheet shows the same jump. FNS does not explain it. Keeping it would make 2020 to 2021 look like a large drop.
- The count is by the county agency that handles the case. That is usually the county where the household lives.

**Uncertainty.** No error bars; these are administrative counts. As a cross-check, Ohio's own monthly report (ODJFS Public Assistance Monthly Statistics, Caseload Summary Statistics Report, July 2025, `https://dam.assets.ohio.gov/image/upload/jfs.ohio.gov/PRC/CaseloadSummaryReportJuly2025.pdf`) counts "individuals in receipt" a little lower than FNS: 1,389,247 statewide versus 1,446,062 (3.9% lower), and 163,303 in Franklin versus 170,410 (4.2% lower). The Ohio report combines Hocking, Ross and Vinton as "South Central" (20,036 versus 20,662 from FNS) and Defiance with Paulding (5,804 versus 6,013). We did not find a published reason for the gap.

**License and attribution.** Public domain. Credit: USDA Food and Nutrition Service, SNAP Data Tables.

## SNAP monthly state participation (USDA Food and Nutrition Service)

**What it is.** Monthly SNAP households, persons and benefit cost by state, one Excel file per fiscal year (October to September). We use Ohio's "Persons" column for the Ohio figure.

**Where it comes from.** Same FNS page, file `https://www.fns.usda.gov/sites/default/files/resource-files/snap-zip-fy69tocurrent-10.zip` (1.7 MB), files `FY20.xlsx` through `FY26.xlsx`, Ohio block on the `MWRO` sheet. Saved with curl to `data/raw/fns/` for the same reason as above.

**Version and vintage.** The FY23 to FY26 files are dated 2026-10-07 inside the zip; the sheet header reads "Data as of October 9, 2026." Ohio runs through July 2026.

**Coverage.** Ohio, every month from October 2019 to July 2026. The sheet title says P-EBT (pandemic school meal benefits) and "other" are excluded. The full monthly run is in `extras.snap_persons_ohio_monthly`.

**Changes over time.** None noted for 2019-2026.

**Suppressed, censored or masked values.** None. August and September 2026 show "--" (not yet reported) and are dropped.

**Missing data.** Only the not-yet-reported months above.

**Revisions.** FNS's state persons table says the latest two months are preliminary and "subject to significant revision." The July values we use are at least 15 months old.

**Units and rounding.** People, whole numbers.

**Known quirks.** The state persons table notes that the data "may include disaster assistance." The July 2020 spike described above is in this file too.

**Uncertainty.** No error bars.

**License and attribution.** Public domain. Credit: USDA Food and Nutrition Service, SNAP Data Tables.

## Population denominator

Census Bureau county and state population estimates, vintage 2025, as built in `data/processed/popest.json` (metric `population_estimate`, July 1, 2020-2025). See `docs/datasets/popest.md`. Each July SNAP count is divided by the July 1 estimate of the same year.
