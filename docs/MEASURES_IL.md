# Measures on the Illinois Community Well-Being page

Written by `scripts/72_wb_build.py` from `scripts/wellbeing_measures.py` and the built data. Edit the measure list in `wellbeing_measures.py`, not here.

Levels: C = counties, D = congressional districts (2021 map), T = census tracts. Role: Experience = what residents experience; Access = services and access; Public money = spending shown beside conditions.

## Child care

_Can families find licensed, rated child care near home?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Licensed child care programs per 1,000 children under 5 (headline) | Access | C D | 8.9 | higher |  | Illinois Early Childhood Asset Map (IECAM, University of Illinois), licensed child care layers for fiscal year 2025; ACS 2020-2024 (children under 5) | IECAM fiscal year 2025 layers, last updated 2026-06-23 |
| Licensed programs rated Silver or Gold | Access | C D | 7.7% | higher |  | Illinois Early Childhood Asset Map (IECAM), licensed child care layers (ExceleRate Illinois ratings) | IECAM fiscal year 2025 layers, last updated 2026-06-23 |
| Children 3 and 4 enrolled in school or preschool | Access | C D T | 51.1% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |

Who runs services: Illinois Department of Early Childhood (child care licensing, the Child Care Assistance Program and Preschool for All, since July 2026; licensing was with the Department of Children and Family Services before then); ExceleRate Illinois; U.S. Department of Health and Human Services, Administration for Children and Families (Child Care and Development Fund, Head Start).

Main public programs: Child Care Assistance Program, ExceleRate Illinois, Preschool for All, Head Start and Early Head Start.

## Education

_Are students learning, showing up and finishing school?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Third graders proficient or above in English language arts (state test) (headline) | Experience | C | 47.9% | higher |  | Illinois State Board of Education, Illinois Report Card Public Data Set | 2025-2026 school year |
| Third graders proficient in math (proficient or above on the state math test) | Experience | C | 49.5% | higher |  | Illinois State Board of Education, Illinois Report Card Public Data Set | 2025-2026 school year |
| Students chronically absent (missed 10% or more of school) | Experience | C | 23.8% | lower |  | Illinois State Board of Education, Illinois Report Card Public Data Set | 2025-2026 school year |
| Adults with a high school diploma or more | Experience | C D T | 90.5% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults with a bachelor's degree or more | Experience | C D T | 37.8% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| School spending per pupil (day-to-day costs) | Public money | C | 21,384 | none |  | U.S. Census Bureau, Annual Survey of School System Finances | School year 2023-2024 |
| Share of school district revenue from state sources | Public money | C | 38.3% | none |  | U.S. Census Bureau, Annual Survey of School System Finances | School year 2023-2024 |

Who runs services: Local school districts and charter schools; Illinois State Board of Education and Regional Offices of Education; U.S. Department of Education (Title I, special education).

Main public programs: Evidence-Based Funding state aid, Title I, IDEA special education, school meals.

## Economic security

_Do households have enough income to cover basic needs?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| People below 200% of the poverty line (headline) | Experience | C D T | 26.1% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| People in poverty | Experience | C D T | 11.8% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Child poverty rate, ages 0 to 17 (annual) | Experience | C | 14.1% | lower |  | U.S. Census Bureau, Small Area Income and Poverty Estimates (SAIPE) | 2024 |
| Median household income | Experience | C D T | 83,390 | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults with food insecurity in the past year | Experience | C D T | 17.4% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Income inequality (Gini index) | Experience | C | 0.481 | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Households that got SNAP food aid (survey) | Access | C D T | 13.8% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| SNAP food benefits per resident | Public money | C | 499 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |
| Supplemental Security Income per resident | Public money | C | 152 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |
| Earned income tax credit per resident | Public money | C | 204 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |
| Veterans' benefits per resident | Public money | C | 302 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |

Who runs services: Illinois Department of Human Services (SNAP, TANF cash aid); USDA Food and Nutrition Service (SNAP); Social Security Administration (SSI); Internal Revenue Service and Illinois Department of Revenue (federal and state Earned Income Tax Credits).

Main public programs: SNAP, TANF, SSI, federal and Illinois Earned Income Tax Credits, WIC, school meals, home energy assistance.

## Jobs and workforce

_Can working-age residents find work that pays?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Unemployment rate (headline) | Experience | C | 4.6% | lower |  | BLS Local Area Unemployment Statistics | 2025 annual average |
| Prime-age workers: share of people 25 to 54 with a job | Experience | C D T | 80.6% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Average weekly wage | Experience | C | 1,539 | higher |  | BLS Quarterly Census of Employment and Wages | 2025 annual average |
| Change in labor force since 2019 | Experience | C | 0.6% | higher |  | BLS Local Area Unemployment Statistics | 2019 to 2025 annual averages |
| Average commute to work | Access | C D T | 27.8 | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Unemployment benefits per resident | Public money | C | 107 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |

Who runs services: Illinois Department of Employment Security (unemployment insurance); Illinois Department of Commerce and Economic Opportunity and local workforce boards; Illinois Community College Board; U.S. Department of Labor.

Main public programs: Unemployment insurance, Workforce Innovation and Opportunity Act training, apprenticeships, community college career programs.

## Housing

_Is housing affordable, stable and in decent shape?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Renters paying 30% or more of income on rent (headline) | Experience | C D T | 47.9% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Owners with a mortgage paying 30% or more on housing | Experience | C D T | 26.6% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults with housing insecurity in the past year | Experience | C D T | 14.1% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults threatened with a utility shutoff in the past year | Experience | C D T | 8.7% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Homes with more than one person per room | Experience | C D T | 2.5% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Homes lived in by their owners | Experience | C D T | 67.1% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Vacant homes | Experience | C D T | 7.7% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Homes built before 1950 | Experience | C D T | 25.8% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Households in HUD-subsidized housing, per 1,000 households | Access | C T | 40.2 | none |  | HUD Picture of Subsidized Households; Census Bureau American Community Survey and population estimates | Dec. 31, 2025 |
| HUD rental aid spending per resident | Public money | C T | 215 | none |  | HUD Picture of Subsidized Households; Census Bureau American Community Survey and population estimates | Dec. 31, 2025 snapshot, annualized |

Who runs services: Local public housing authorities (vouchers, public housing); Illinois Housing Development Authority (Low-Income Housing Tax Credits, rental help); Illinois Department of Commerce and Economic Opportunity (Community Development Block Grants for smaller communities); U.S. Department of Housing and Urban Development.

Main public programs: Housing Choice Vouchers, public housing, project-based rental assistance, Low-Income Housing Tax Credits, HOME, CDBG.

## Physical health

_Are residents healthy, covered and able to see a doctor?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Adults in fair or poor health (headline) | Experience | C D T | 19.1% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults with diagnosed diabetes | Experience | C D T | 11.6% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults with obesity | Experience | C D T | 34.2% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults who currently smoke cigarettes | Experience | C D T | 12.4% | lower | 6.1 (Healthy People 2030 national target (TU-02)) | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| People under 65 without health insurance | Access | C D T | 8.1% | lower | 7.6 (Healthy People 2030 national target (AHS-01: 92.4% of people under 65 insured)) | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults with a routine checkup in the past year | Access | C D T | 77.6% | higher |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults who saw a dentist in the past year | Access | C D T | 62.6% | higher |  | CDC PLACES: Local Data for Better Health, 2025 release | 2022 estimate |
| Primary care doctors per 100,000 people | Access | C | 82 | higher |  | HRSA Area Health Resources Files (American Medical Association Physician Masterfile), via County Health Rankings & Roadmaps | 2022 (CHR&R March 2026 update) |
| Dentists per 100,000 people | Access | C | 86 | higher |  | HRSA Area Health Resources Files (CMS National Provider Identifier file), via County Health Rankings & Roadmaps | 2023 (CHR&R March 2026 update) |
| Medicaid and other public medical aid per resident | Public money | C | 2,175 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |

Who runs services: Illinois Department of Healthcare and Family Services (Medicaid, All Kids); Illinois Department of Public Health and local health departments; federally funded community health centers (HRSA).

Main public programs: Medicaid, All Kids, Medicare, community health centers, local public health programs.

## Mental health

_Are residents in distress, and can they get treatment?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Adults with frequent mental distress (headline) | Experience | C D T | 15.9% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults ever told they have depression | Experience | C D T | 20.1% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Drug overdose deaths per 100,000 people, past 12 months | Experience | C | 14.9 | lower | 20.7 (Healthy People 2030 national target (SU-03)) | CDC NCHS, VSRR Provisional County-Level Drug Overdose Death Counts; Census Bureau population estimates | 12 months ending March 2026 |
| Suicide deaths per 100,000 people (age-adjusted) | Experience | C | 11.2 | lower | 12.8 (Healthy People 2030 national target (MHMD-01)) | CDC National Center for Health Statistics mortality files, via County Health Rankings & Roadmaps | 2019-2023 (five years combined) |
| Mental health providers per 100,000 people | Access | C | 355 | higher |  | CMS National Plan and Provider Enumeration System (NPI file), via County Health Rankings & Roadmaps | 2025 (CHR&R March 2026 update) |

Who runs services: Illinois Department of Human Services (mental health and substance use programs); Illinois Department of Healthcare and Family Services (Medicaid); county and township mental health boards; 988 crisis line.

Main public programs: Medicaid behavioral health, community mental health services, federal opioid response and settlement funds, crisis services.

## Public safety

_Are residents safe from crime and crashes?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Violent crime rate (headline) | Experience | C | 257 | lower |  | FBI Uniform Crime Reporting Program, Return A master files | 2025 calendar year |
| Property crime rate | Experience | C | 1,550 | lower |  | FBI Uniform Crime Reporting Program, Return A master files | 2025 calendar year |
| Traffic deaths per 100,000 people | Experience | C | 9.5 | lower | 10.1 (Healthy People 2030 national target (IVP-06)) | NHTSA Fatality Analysis Reporting System (FARS); Census Bureau population estimates | 2019-2023 (five years combined) |

Who runs services: City police, county sheriffs and the courts; Illinois State Police; Illinois Criminal Justice Information Authority; Illinois Department of Transportation (highway safety); Illinois Attorney General.

Main public programs: Local police and fire budgets, victim services, highway safety grants, violence prevention grants.

## Social well-being

_Are residents connected to each other and to community resources?_

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Adults who feel lonely always, usually or sometimes (headline) | Experience | C D T | 33.7% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults who lack social and emotional support | Experience | C D T | 25.6% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Voter turnout, 2024 presidential election | Experience | C | 61.9% | higher |  | Illinois Secretary of State official results, as compiled by the MIT Election Data + Science Lab; Census Bureau American Community Survey | November 2024 general election |
| Households with a broadband internet subscription | Access | C D T | 90.8% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults without reliable transportation in the past year | Access | C D T | 8.8% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Households without a vehicle | Access | C D T | 11.0% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Public library visits per person | Access | C | 3.2 | higher |  | Institute of Museum and Library Services, Public Libraries Survey; Census Bureau population estimates | FY 2024 (each library's own 12-month fiscal year ending in 2024 in Illinois) |
| Membership groups per 10,000 people | Access | C | 9.4 | higher |  | Census Bureau County Business Patterns; Census Bureau population estimates (definition from County Health Rankings & Roadmaps) | 2023 |
| Public library spending per person | Public money | C | 71.30 | higher |  | Institute of Museum and Library Services, Public Libraries Survey; Census Bureau population estimates | FY 2024 (each library's own 12-month fiscal year ending in 2024 in Illinois) |

Who runs services: Local public libraries and library districts (with state grants through the Illinois State Library); transit agencies; the state broadband office; county clerks and election boards.

Main public programs: State library grants, transit funding, broadband expansion grants, park district and recreation programs.

## Who lives here (context, not judged)

| Measure | Role | Levels | Illinois | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Population | Context | C D T | 12,694,798 | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Residents 65 and older | Context | C D T | 17.0% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Residents ages 25 to 54 | Context | C D T | 39.3% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| White, not Hispanic | Context | C D T | 58.1% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Black, not Hispanic | Context | C D T | 13.3% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Hispanic or Latino (any race) | Context | C D T | 18.8% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Foreign-born residents | Context | C D T | 14.7% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| People with a disability | Context | C D T | 12.1% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
