# Ohio County Dashboard, Community Well-Being pages and congressional district pages

Interactive pages built from public federal and state data by Data 4 The People. This is a draft.

- **Ohio County Dashboard:** https://data4thepeople.github.io/StateOperatingDashboard/
  All 88 Ohio counties on one map: jobs and wages, income and poverty, health, housing, schools, child care,
  crime and population. Each county has a scorecard that compares it with Ohio and the U.S.
- **Ohio Community Well-Being:** https://data4thepeople.github.io/StateOperatingDashboard/wellbeing/
  Every Ohio county, congressional district and census tract in nine areas of daily life: child care, education,
  economic security, jobs, housing, physical health, mental health, public safety and social well-being. Each
  measure is shown in its own units next to Ohio, the U.S. and, where one exists, a national target, with no
  combined score. Public spending is shown beside conditions. The measure list is in `docs/MEASURES.md`.
- **Georgia Community Well-Being:** https://data4thepeople.github.io/StateOperatingDashboard/georgia/
  The same page for Georgia's 159 counties, 14 congressional districts and census tracts, built from the same
  national sources plus Georgia's own school and child care data. The measure list is in `docs/MEASURES_GA.md`.
- **Illinois Community Well-Being:** https://data4thepeople.github.io/StateOperatingDashboard/illinois/
  The same page for Illinois's 102 counties, 17 congressional districts and census tracts, with Illinois school
  data from the State Board of Education and child care ratings from the Illinois Early Childhood Asset Map. The
  measure list is in `docs/MEASURES_IL.md`.
- **Ohio's 10th Congressional District:** https://data4thepeople.github.io/StateOperatingDashboard/oh10/
  Census tracts under the congressional map the Ohio Redistricting Commission adopted on October 31, 2025.
- **Illinois's 6th Congressional District:** https://data4thepeople.github.io/StateOperatingDashboard/il06/
  Census tracts under the congressional map Illinois enacted in 2021.

## What's in the repo

| Path | What it holds |
|---|---|
| `dist/` | The built pages. GitHub Pages serves this folder. Each page is one self-contained HTML file, except the Well-Being page, which loads its census tract layer from `dist/wellbeing/tracts.json` after the first map is drawn. |
| `scripts/` | Python that pulls each source and writes one layer file, plus the page builders and HTML templates. |
| `data/processed/` | The layer files the pages are built from (JSON). Ohio's are at the top level; Georgia's and Illinois's are in `data/processed/ga/` and `data/processed/il/`. Raw downloads are not kept in the repo. |
| `DATASETS.md` | Every source: what it is, where it comes from, vintage, coverage, quirks and how we use it. |
| `TIEOUT.md` | Checks of the built pages against the sources, including what has not been checked yet. |
| `docs/` | The layer file format and notes on each dataset. |

## Data sources

- U.S. Bureau of Economic Analysis: county transfer receipts (CAINC35). HUD: Picture of Subsidized Households.
  NHTSA: Fatality Analysis Reporting System. IMLS: Public Libraries Survey. County Health Rankings & Roadmaps
  (provider counts and suicide rates, from HRSA, CMS and CDC). MIT Election Data + Science Lab (2024 results).
- U.S. Bureau of Labor Statistics: Local Area Unemployment Statistics, Quarterly Census of Employment and Wages,
  and the R-CPI-U-RS price index.
- U.S. Census Bureau: American Community Survey 5-year estimates, population estimates (Vintage 2025), Small Area
  Health Insurance Estimates, Small Area Income and Poverty Estimates, Annual Survey of School System Finances,
  County Business Patterns, the 2020 census, and TIGERweb boundaries.
- CDC: provisional county drug overdose death counts (NCHS VSRR) and PLACES.
- USDA Food and Nutrition Service: SNAP participation.
- FBI Uniform Crime Reporting Program: Return A files and state estimates.
- Ohio Department of Education and Workforce report cards, NCES Common Core of Data, and the Ohio Department of
  Children and Youth licensed program list.
- Georgia Governor's Office of Student Achievement (Georgia Milestones and attendance files) and the Georgia
  Department of Early Care and Learning provider list.
- Illinois State Board of Education Report Card data and the Illinois Early Childhood Asset Map (University of
  Illinois) child care layers.
- District lines: the Ohio Redistricting Commission's block assignment file (Ohio) and the Census Bureau's
  119th Congress block file (Georgia, Illinois and IL-6).

`DATASETS.md` has the details for each one.

## How to rebuild

The scripts need Python 3 with `pandas`, `openpyxl` and `shapely`. Census and BLS API keys come from the environment
(`CENSUS_API_KEY`, `BLS_API_KEY`), along with `D4TP_CONTACT_EMAIL` for the request header.

```
# Ohio County Dashboard
python scripts/05_geo.py
python scripts/10_jobs_industry.py   # then each numbered script through 50_national.py
python scripts/90_build.py           # writes dist/index.html

# Ohio Community Well-Being (after the county layers, including 44_schools, 45_access and 46_public_money)
python scripts/70_wb_geo.py
python scripts/71_wb_data.py
python scripts/72_wb_build.py         # writes dist/wellbeing/index.html and docs/MEASURES.md

# Georgia Community Well-Being: the same scripts with D4TP_STATE=ga, which reads and writes
# data/raw/ga and data/processed/ga. 47_schools_ga.py replaces 40_reading.py and 44_schools.py;
# 41_childcare.py is Ohio only (Georgia's child care measures are built in 71_wb_data.py).
export D4TP_STATE=ga
python scripts/05_geo.py              # then 10 through 46, 47_schools_ga.py, 50_national.py, 70, 71 and 72
python scripts/72_wb_build.py         # writes dist/georgia/index.html and docs/MEASURES_GA.md
unset D4TP_STATE

# Illinois Community Well-Being: the same with D4TP_STATE=il; 48_schools_il.py replaces 40_reading.py and
# 44_schools.py, and child care comes from IECAM inside 71_wb_data.py. Writes dist/illinois/.

# District pages (key: oh10 or il06)
python scripts/60_district_geo.py il06
python scripts/61_district_data.py il06
python scripts/63_district_basemap.py il06
python scripts/62_district_build.py il06   # writes dist/il06/index.html
```

Downloads are cached in `data/raw/`, so a second run does not pull them again.

## Method notes

- **Counties are compared with their state.** "Near Ohio" (or "Near Georgia", "Near Illinois") means within 3% of the state's value
  or 0.3 points, whichever is larger. Where a source has no statewide figure (CDC PLACES), counties are compared with the median county.
- **Survey figures have margins of error.** Tiles show the 90% margin where the publisher gives one.
- **District tracts.** A tract is mapped and given a scorecard when most of its 2020 residents live in the
  district. Those figures cover the whole tract.
- **District totals.** IL-6 survey figures are the Census Bureau's own estimates for the district. OH-10 has no
  published estimates for its 2025 lines yet, so its totals add up every tract with district residents, weighted
  by the share of each tract's 2020 residents who live inside the line.
- **County tables on district pages** cover each whole county, including parts outside the district.
- **Prison and college towns.** On the Community Well-Being pages, places where adults in prisons and jails were 5%
  or more of residents 18 to 64 at the 2020 census are outlined on prime-age employment and adult education. Places
  where leaving out college and graduate students lowers the poverty rate by 3 points or more are outlined on the
  two poverty measures. Each has a note in the place's profile. No value is changed.
- **Comparing two measures.** The Community Well-Being page can plot any two measures for every place at one level.
  The pattern is described with a rank (Spearman) correlation, which compares the order of places on each measure.
  Each place counts the same, whatever its population. No pattern is given for fewer than 30 places (districts). A
  pattern means the two measures move together across places; it does not show that one causes the other.
- **Checks.** Two independent checks of the Ohio County Dashboard recomputed every measure from the publishers
  and matched every value. Ohio's crime rate is built the same way as the county rates, not taken from the FBI's
  statewide estimate. The Ohio Community Well-Being page had its own independent check on November 17, 2026. The
  Georgia and Illinois pages had theirs on November 18, 2026. The district pages have not had one yet. `TIEOUT.md` lists
  what has been checked and what has not.
