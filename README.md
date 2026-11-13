# Ohio County Dashboard and congressional district pages

Interactive pages built from public federal and state data by Data 4 The People. This is a draft.

- **Ohio County Dashboard:** https://data4thepeople.github.io/StateOperatingDashboard/
  All 88 Ohio counties on one map: jobs and wages, income and poverty, health, housing, schools, child care,
  crime and population. Each county has a scorecard that compares it with Ohio and the U.S.
- **Ohio's 10th Congressional District:** https://data4thepeople.github.io/StateOperatingDashboard/oh10/
  Census tracts under the congressional map the Ohio Redistricting Commission adopted on October 31, 2025.
- **Illinois's 6th Congressional District:** https://data4thepeople.github.io/StateOperatingDashboard/il06/
  Census tracts under the congressional map Illinois enacted in 2021.

## What's in the repo

| Path | What it holds |
|---|---|
| `dist/` | The built pages. Each is one self-contained HTML file. GitHub Pages serves this folder. |
| `scripts/` | Python that pulls each source and writes one layer file, plus the page builders and HTML templates. |
| `data/processed/` | The layer files the pages are built from (JSON). Raw downloads are not kept in the repo. |
| `DATASETS.md` | Every source: what it is, where it comes from, vintage, coverage, quirks and how we use it. |
| `TIEOUT.md` | Checks of the built pages against the sources, including what has not been checked yet. |
| `docs/` | The layer file format and notes on each dataset. |

## Data sources

- U.S. Bureau of Labor Statistics: Local Area Unemployment Statistics, Quarterly Census of Employment and Wages,
  and the R-CPI-U-RS price index.
- U.S. Census Bureau: American Community Survey 5-year estimates, population estimates (Vintage 2025), Small Area
  Health Insurance Estimates, Small Area Income and Poverty Estimates, the 2020 census, and TIGERweb boundaries.
- CDC: provisional county drug overdose death counts (NCHS VSRR) and PLACES.
- USDA Food and Nutrition Service: SNAP participation.
- FBI Uniform Crime Reporting Program: Return A files and state estimates.
- Ohio Department of Education and Workforce report cards, NCES Common Core of Data, and the Ohio Department of
  Children and Youth licensed program list.
- District lines: the Ohio Redistricting Commission's block assignment file (OH-10) and the Census Bureau's
  119th Congress block file (IL-6).

`DATASETS.md` has the details for each one.

## How to rebuild

The scripts need Python 3 with `pandas` and `openpyxl`. Census and BLS API keys come from the environment
(`CENSUS_API_KEY`, `BLS_API_KEY`), along with `D4TP_CONTACT_EMAIL` for the request header.

```
# Ohio County Dashboard
python scripts/05_geo.py
python scripts/10_jobs_industry.py   # then each numbered script through 50_national.py
python scripts/90_build.py           # writes dist/index.html

# District pages (key: oh10 or il06)
python scripts/60_district_geo.py il06
python scripts/61_district_data.py il06
python scripts/63_district_basemap.py il06
python scripts/62_district_build.py il06   # writes dist/il06/index.html
```

Downloads are cached in `data/raw/`, so a second run does not pull them again.

## Method notes

- **Counties are compared with Ohio.** "Near Ohio" means within 3% of Ohio's value or 0.3 points, whichever is
  larger. Where a source has no statewide figure (CDC PLACES), counties are compared with the median county.
- **Survey figures have margins of error.** Tiles show the 90% margin where the publisher gives one.
- **District tracts.** A tract is mapped and given a scorecard when most of its 2020 residents live in the
  district. Those figures cover the whole tract.
- **District totals.** IL-6 survey figures are the Census Bureau's own estimates for the district. OH-10 has no
  published estimates for its 2025 lines yet, so its totals add up every tract with district residents, weighted
  by the share of each tract's 2020 residents who live inside the line.
- **County tables on district pages** cover each whole county, including parts outside the district.
- **Checks.** An independent check of the Ohio County Dashboard matched every value at the precision shown.
  The district pages and some later additions to the Ohio page have not had that check yet. `TIEOUT.md` lists
  what has been checked and what has not.
