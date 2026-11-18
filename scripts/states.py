"""Per-state settings. Pick the state with the environment variable D4TP_STATE (oh or ga; Ohio when unset).

Ohio keeps the original paths (data/raw, data/processed, dist/wellbeing) so its pages and files do not move. Every
other state reads and writes its own folders (data/raw/<id>, data/processed/<id>), so two states never share a cached
state-level download. Files that hold the whole nation (BEA, FARS, FBI Return A, County Health Rankings and so on)
are read from the shared data/raw folder by both states.
"""

STATES = {
    "oh": {
        "fips": "39", "abbr": "OH", "name": "Ohio", "key": "ohio",
        "counties": [f"39{n:03d}" for n in range(1, 176, 2)],
        "lat": 40.3,              # middle latitude, for the map projection
        "ucr": "34",              # FBI UCR numeric state code
        "state_police_ori": "OHOHP",
        "page": "wellbeing",      # dist/<page>/ for the Community Well-Being page
        "district_map": "2025 map, first used in 2026",
        "district_year": "2025",
        "districts": 15,
        "pop2020": 11799448,      # official 2020 census count
        "pop_spread": 1,          # largest gap in 2020 population between districts
        "townships": True,        # name tracts outside places by township
        "district_src": "Ohio Redistricting Commission block assignment file (map adopted Oct. 31, 2025)",
        "medicaid_note": " The 2010-2014 period mostly predates Ohio's 2014 Medicaid expansion.",
        "medsl_date": "2026-04-28",       # date on the MEDSL 2024 precinct file
        "lib_fy": "calendar year {fy} in Ohio",   # IMLS library fiscal year
        "sf_rows": (650, 800),    # Ohio rows expected in the Census school finance file
        "sf_levels": ("03",),     # Census SCHLEV codes counted as traditional districts (03 = elementary-secondary)
        "sf_other": "Joint vocational districts and educational service centers",
        "sf_other_short": "joint vocational districts and service centers",
        "sf_charter": "Community schools (charter schools) are not in this Census survey.",
        "sf_local": "local sources (mostly property and income taxes)",
    },
    "ga": {
        "fips": "13", "abbr": "GA", "name": "Georgia", "key": "georgia",
        # 13041 and 13203 are unused: no Georgia county has those codes
        "counties": [f"13{n:03d}" for n in range(1, 322, 2) if n not in (41, 203)],
        "lat": 32.7,
        "ucr": "10",
        "state_police_ori": "GAGSP",
        "page": "georgia",
        "district_map": "2023 map, first used in 2024",
        "district_year": "2023",
        "district_foot": ("the map Georgia enacted in December 2023 after a federal court ruling, first used in the 2024 "
                          "election, from the Census Bureau's 119th Congress block file."),
        "districts": 14,
        "pop2020": 10711908,
        "pop_spread": 2,          # the 2023 map runs from 765,135 to 765,137
        "townships": False,       # Georgia has no township governments; tracts outside places use the county
        "district_src": "Census Bureau 119th Congress block assignment file (the map Georgia enacted in December 2023)",
        "medicaid_note": " Georgia has not adopted the full Medicaid expansion for low-income adults.",
        "medsl_date": "2026-04-28",
        "lib_fy": "July {fy0} to June {fy} in Georgia",
        "sf_rows": (150, 400),
        # 01 elementary-only (Clay, Webster), 06 (Taliaferro) and 03 are all local districts; 07 are the RESAs
        "sf_levels": ("01", "02", "03", "06"),
        "sf_other": "Regional educational service agencies",
        "sf_other_short": "regional educational service agencies",
        "sf_charter": "State charter schools are not in this Census survey.",
        "sf_local": "local sources (mostly property taxes)",
    },
}
