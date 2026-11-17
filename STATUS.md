# Status

Project: StateOperatingDashboard (Ohio county operating dashboard, working name)
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: none yet
Step: 1
Since: 2026-11-09

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | | v1 demo build: Ohio 88-county map, four issue areas, county scorecard |
| 2a | Draft with brackets resolved | | |
| 2b | Eric's edit, Claude's look-over | | |
| 2c | Slice markup | | |
| 2d | Hero 1680x1080 + alt text | | |
| 2e | SEO | | |
| 2f | Pushed to Prismic (draft) | | |
| 2g | Mailchimp teaser | | |

## Stale

None.

## Scope decisions (2026-11-09)

- Ohio only, county level (88 counties). Tract level later.
- Themes labeled as issue areas, not as a person's promises. Issue list follows the governor's stated priorities (cost of living, health care, jobs, schools, addiction).
- v1 layers: jobs and industry (LAUS, QCEW), income and near-poverty (ACS), health (SAHIE, CDC overdose, ACS), housing, schools and people (ACS, Census population estimates).
- Demo was a local file until 2026-11-13, when Eric asked to make the repo public with Pages on so he can share the pages. The district pages and later Ohio additions still need the independent tie-out.
- Later phases: named largest employers, IRS migration, OEWS metro wage distributions, ALICE, peer-state benchmarks (South Carolina), Ohio state databases.

## Log

- 2026-11-09 Step 1 opened. Scope set from Eric's voice memo; demo due within two hours.
- 2026-11-13 Repo published as Data4ThePeople/StateOperatingDashboard with GitHub Pages serving dist/ (Ohio page, OH-10, IL-6).
- 2026-11-16 Built the Ohio Community Well-Being page (dist/wellbeing/) from Nina's notes: nine areas, county / 2025 district / tract switch, experience vs access vs public money, Healthy People 2030 targets, no combined score. Paused here. Next: Eric saves ODEW grad-rate and District Details files by hand (list in docs/datasets/schools.md); review with Nina via docs/MEASURES.md; independent tie-out of the new page and layers.
- 2026-11-17 Applied the statewide tie-out fixes (same-method Ohio crime rate, blank-year changes, medians, tied ranks, wording). Ran the independent tie-out of the Well-Being page and its three new layers (two agents): no wrong numbers in the layers; fixed district commute blanks, 39 unplaced child care programs, the 200%-poverty dollar figure, uncertainty flags at every level, and same-method Ohio for school finance and membership groups. Open: District 13 Silver/Gold share gap (44.3 vs 43.8), district pages still without an independent tie-out, ODEW grad-rate files, Nina's review of docs/MEASURES.md.
