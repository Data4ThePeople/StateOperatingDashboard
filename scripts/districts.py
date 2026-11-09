"""Settings for the congressional district pages. Scripts 60-63 take one of these keys as their argument:

    .venv/bin/python scripts/60_district_geo.py il06

Output goes to data/processed/<key>/ and dist/<key>/index.html.

- baf: where the block-to-district file comes from. "orc430" is the Ohio Redistricting Commission's file for the
  map adopted October 31, 2025. "cd119" is the Census Bureau's national block file for the 119th Congress
  (https://www2.census.gov/programs-surveys/decennial/rdo/mapping-files/2025/119-congressional-district-befs/).
- context: which tracts outside the district are drawn in gray. "counties" draws the rest of the district's
  counties (and fits the map to them). "bbox" draws the tracts around the district, in any county (for a district
  inside a large county, where the whole county would make the district small on screen).
- acs_district: when the Census Bureau publishes ACS 5-year estimates for the district itself (119th Congress
  lines), the District tab uses them, and the figures built from tracts are printed only as a check.
- county_source: "state_layers" reads the county table from the Ohio statewide dashboard's layers;
  "national" pulls the county figures that every state has (BLS, Census, CDC) and benchmarks them against the
  state and U.S. figures in data/processed/national.json.
"""

DISTRICTS = {
    "oh10": dict(
        state="39", st="OH", state_name="Ohio", cd="10", short="OH-10",
        title="Ohio's 10th District", h1="Ohio's 10th Congressional District",
        baf="orc430", context="counties", county_source="state_layers",
        pop2020=786629,                       # Ohio Secretary of State: 81,354 + 167,966 + 537,309
        plan="under the congressional map the Ohio Redistricting Commission adopted on October 31, 2025",
        plan_source="Ohio Redistricting Commission block assignment file for the plan adopted October 31, 2025",
        county_note_extra=" For crime, it means agencies covering at least 80% of the county's residents did not "
                          "report a full year; Greene County fell below that in 2025.",
        county_sources="BLS, CDC, FBI, USDA FNS, Ohio Department of Education and Workforce, Ohio Department of "
                       "Children and Youth, Census Bureau, as listed on the statewide dashboard",
        county_from_state_page=True,
    ),
    "il06": dict(
        state="17", st="IL", state_name="Illinois", cd="06", short="IL-6",
        title="Illinois's 6th District", h1="Illinois's 6th Congressional District",
        baf="cd119", context="bbox", county_source="national",
        pop2020=753677,                       # Census Bureau, 2020 census for the 119th Congress (api 2020/dec/cd119)
        plan="under the congressional map Illinois enacted in 2021, first used in the 2022 election",
        plan_source="Census Bureau block equivalency file for the 119th Congress (the map Illinois enacted in 2021)",
        county_note_extra="",
        county_sources="BLS Local Area Unemployment Statistics and Quarterly Census of Employment and Wages; Census "
                       "Bureau SAHIE, SAIPE and population estimates; CDC NCHS provisional overdose deaths",
        county_from_state_page=False,
        outline=True,                         # draw the district line (TIGERweb, 120th Congress layer)
        acs_district="congressional district:06",   # the Census Bureau publishes ACS for this district's lines
    ),
}


def get(argv):
    if len(argv) != 2 or argv[1] not in DISTRICTS:
        raise SystemExit(f"usage: {argv[0]} <{'|'.join(DISTRICTS)}>")
    return dict(DISTRICTS[argv[1]], key=argv[1])
