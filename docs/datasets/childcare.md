# Datasets: child care layer (childcare.json)

Built by `scripts/41_childcare.py`.

## Licensed early care and education programs (Ohio Department of Children and Youth)

**What it is.** A list of early care and education programs in Ohio, one row per program, with its county,
program type, status, address and Step Up To Quality rating. It is the data behind DCY's Step Up To Quality
program locator map. We count the licensed programs that are open in each county.

**Where it comes from.** State of Ohio ArcGIS layer `Ohio_Daycares_view`:
`https://maps.ohio.gov/arcgis/rest/services/Hosted/Ohio_Daycares_view/FeatureServer/0` (portal item
`e7b80e83d8764427b5de7fde6f67f83d`, title "Ohio Daycare Centers", owner `oitogrip`). Queried as JSON through
the public ArcGIS REST query endpoint, 1,000 records per request. No login. Each row links to the program's
page on Ohio Child Care Search (`https://childcaresearch.ohio.gov/provider/<number>`). Saved at
`data/raw/dcy/ohio_daycares_<pull date>.json`.

**Version and vintage.** The item description says the layer is updated weekly. It keeps no history: each
update replaces the list. The portal item was last modified October 21, 2026; we pulled it November 9, 2026
(8,707 rows). Values are a snapshot on the pull date, so `series` has one point.

**Coverage.** All 88 counties. We keep five licensed program types: child care centers (4,242 open), family
child care Type B homes (1 to 6 children; 1,635), preschools (1,494), family child care Type A homes (7 to 12
children; 335) and school-age child care (241), for 7,947 in all. "Open" includes 17 programs whose status is
"Enforcement" (licensed, under an enforcement action). We drop 392 inactive programs of these five types,
288 day camps (registered with the state, not licensed), 17 certified in-home aides and 63 out-of-state
programs registered to take Ohio subsidy. Preschools and school-age programs run by school districts,
nonpublic schools, county developmental disabilities boards and community schools used to be licensed by the
Ohio Department of Education; DCY's SFY 2025 licensing report lists them among the program types DCY now
licenses. The layer has no
licensed capacity (number of children a program may serve), no ages served and no enrollment.

**Fields used and metrics built.**

| Metric | Built from |
|---|---|
| childcare_providers | Count of rows per `county` where `program_type` is one of the five licensed types and `program_status` is Open or Enforcement |
| extras.providers_by_type | The same count split by `program_type` |

County names in the layer are matched to FIPS codes using the Census Bureau county names. Every licensed,
open program matched a county.

**Changes over time.** Not applicable to a single snapshot. DCY's own yearly totals use a different basis:
the SFY 2025 licensing report counts 8,950 programs licensed at any time from July 1, 2024 to June 30, 2025
(4,586 centers, 397 Type A, 2,111 Type B, 1,539 preschools, 317 school-age). Our point-in-time count is lower
because programs that closed during the year are not in today's list.

**Suppressed, censored or masked values.** None. Type B homes are listed under the provider's name.

**Missing data.** 993 Type B homes and 26 out-of-state programs have no program number. Each still has a
unique provider link, which we use as the record key. No licensed, open program lacks a county.

**Revisions.** The list is replaced weekly. We keep the dated snapshot and reuse it on later runs; pass
`--refresh` to pull a new one.

**Units and rounding.** Programs, as whole numbers. Ohio is the sum of the 88 counties, because the state does
not publish a point-in-time total on the same basis.

**Known quirks.** A program counts once regardless of size: a six-child Type B home and a 300-child center
each count as one. One school building can hold two licenses, a preschool and a school-age program, and then
counts twice (Vinton County's 8 programs are 1 Head Start center, 3 school preschools and 4 school-age
programs at the same or nearby school buildings). Program type labels use the layer's spelling ("Pre School").

**Uncertainty.** None published. The state's license text says the layer is provided "as is" without a
guarantee that it is complete or error free.

**License and attribution.** State of Ohio geospatial data, public use. Credit: "Ohio Department of Children
and Youth, licensed early care and education programs, via the State of Ohio GIS (maps.ohio.gov)."
