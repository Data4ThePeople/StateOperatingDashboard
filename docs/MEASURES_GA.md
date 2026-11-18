# Measures on the Georgia Community Well-Being page

Written by `scripts/72_wb_build.py` from `scripts/wellbeing_measures.py` and the built data. Edit the measure list in `wellbeing_measures.py`, not here.

Levels: C = counties, D = congressional districts (2023 map), T = census tracts. Role: Experience = what residents experience; Access = services and access; Public money = spending shown beside conditions.

## Child care

_Can families find licensed, rated child care near home?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Licensed child care programs per 1,000 children under 5 (headline) | Access | C D | 6.0 | higher |  | Georgia Department of Early Care and Learning, provider data export; ACS 2020-2024 (children under 5) | programs listed on 2026-11-18 |
| Licensed programs rated 2 or 3 stars | Access | C D | 55.9% | higher |  | Georgia Department of Early Care and Learning, provider data export (Quality Rated) | programs listed on 2026-11-18 |
| Children 3 and 4 enrolled in school or preschool | Access | C D T | 46.7% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |

Who runs services: Georgia Department of Early Care and Learning (licensing, Quality Rated, the Childcare and Parent Services subsidy program and Georgia's Pre-K Program); U.S. Department of Health and Human Services, Administration for Children and Families (Child Care and Development Fund, Head Start).

Main public programs: Childcare and Parent Services (CAPS) subsidies, Quality Rated, Georgia's Pre-K Program, Head Start and Early Head Start.

## Education

_Are students learning, showing up and finishing school?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Third graders proficient or above in English language arts (state test) (headline) | Experience | C | 35.2% | higher |  | Georgia Governor's Office of Student Achievement (GOSA), Georgia Milestones End-of-Grade results; NCES Common Core of Data for school system counties | 2024-2025 school year |
| Third graders proficient in math (proficient or above on the state math test) | Experience | C | 44.5% | higher |  | Georgia Governor's Office of Student Achievement (GOSA), Georgia Milestones End-of-Grade results; NCES Common Core of Data for school system counties | 2024-2025 school year |
| Students chronically absent (missed 10% or more of school) | Experience | C | 20.2% | lower |  | Georgia Governor's Office of Student Achievement (GOSA), attendance files; NCES Common Core of Data for school system counties | 2024-2025 school year |
| Adults with a high school diploma or more | Experience | C D T | 89.2% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults with a bachelor's degree or more | Experience | C D T | 34.9% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| School spending per pupil (day-to-day costs) | Public money | C | 15,771 | none |  | U.S. Census Bureau, Annual Survey of School System Finances | School year 2023-2024 |
| Share of school district revenue from state sources | Public money | C | 39.4% | none |  | U.S. Census Bureau, Annual Survey of School System Finances | School year 2023-2024 |

Who runs services: Local school districts and charter schools; Georgia Department of Education; Governor's Office of Student Achievement; U.S. Department of Education (Title I, special education).

Main public programs: Quality Basic Education state funding, Title I, IDEA special education, school meals.

## Economic security

_Do households have enough income to cover basic needs?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| People below 200% of the poverty line (headline) | Experience | C D T | 30.5% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| People in poverty | Experience | C D T | 13.4% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Child poverty rate, ages 0 to 17 (annual) | Experience | C | 16.9% | lower |  | U.S. Census Bureau, Small Area Income and Poverty Estimates (SAIPE) | 2024 |
| Median household income | Experience | C D T | 77,353 | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults with food insecurity in the past year | Experience | C D T | 18.7% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Income inequality (Gini index) | Experience | C | 0.477 | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Households that got SNAP food aid (survey) | Access | C D T | 12.3% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| People getting SNAP food aid | Access | C | 13.5% | none |  | USDA Food and Nutrition Service, SNAP Data Tables (county participation, form FNS-388A); Census Bureau population estimates | July 2023 |
| SNAP food benefits per resident | Public money | C | 419 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |
| Supplemental Security Income per resident | Public money | C | 166 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |
| Earned income tax credit per resident | Public money | C | 306 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |
| Veterans' benefits per resident | Public money | C | 695 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |

Who runs services: Georgia Department of Human Services, Division of Family and Children Services (SNAP, TANF cash aid); USDA Food and Nutrition Service (SNAP); Social Security Administration (SSI); Internal Revenue Service (Earned Income Tax Credit).

Main public programs: SNAP, TANF, SSI, Earned Income Tax Credit, WIC, school meals, home energy assistance.

## Jobs and workforce

_Can working-age residents find work that pays?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Unemployment rate (headline) | Experience | C | 3.4% | lower |  | BLS Local Area Unemployment Statistics | 2025 annual average |
| Prime-age workers: share of people 25 to 54 with a job | Experience | C D T | 78.5% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Average weekly wage | Experience | C | 1,404 | higher |  | BLS Quarterly Census of Employment and Wages | 2025 annual average |
| Change in labor force since 2019 | Experience | C | 5.4% | higher |  | BLS Local Area Unemployment Statistics | 2019 to 2025 annual averages |
| Average commute to work | Access | C D T | 28.3 | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Unemployment benefits per resident | Public money | C | 15 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |

Who runs services: Georgia Department of Labor (unemployment insurance, career centers); local workforce development boards; Technical College System of Georgia; U.S. Department of Labor.

Main public programs: Unemployment insurance, Workforce Innovation and Opportunity Act training, apprenticeships, technical college programs.

## Housing

_Is housing affordable, stable and in decent shape?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Renters paying 30% or more of income on rent (headline) | Experience | C D T | 52.4% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Owners with a mortgage paying 30% or more on housing | Experience | C D T | 26.3% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults with housing insecurity in the past year | Experience | C D T | 15.6% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults threatened with a utility shutoff in the past year | Experience | C D T | 10.3% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Homes with more than one person per room | Experience | C D T | 2.4% | lower |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Homes lived in by their owners | Experience | C D T | 65.7% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Vacant homes | Experience | C D T | 10.3% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Homes built before 1950 | Experience | C D T | 6.4% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Households in HUD-subsidized housing, per 1,000 households | Access | C T | 27.7 | none |  | HUD Picture of Subsidized Households; Census Bureau American Community Survey and population estimates | Dec. 31, 2025 |
| HUD rental aid spending per resident | Public money | C T | 120 | none |  | HUD Picture of Subsidized Households; Census Bureau American Community Survey and population estimates | Dec. 31, 2025 snapshot, annualized |

Who runs services: Local public housing authorities (vouchers, public housing); Georgia Department of Community Affairs (Low-Income Housing Tax Credits, vouchers where there is no local authority, Community Development Block Grants and HOME for smaller communities); U.S. Department of Housing and Urban Development.

Main public programs: Housing Choice Vouchers, public housing, project-based rental assistance, Low-Income Housing Tax Credits, HOME, CDBG.

## Physical health

_Are residents healthy, covered and able to see a doctor?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Adults in fair or poor health (headline) | Experience | C D T | 20.7% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults with diagnosed diabetes | Experience | C D T | 13.2% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults with obesity | Experience | C D T | 35.2% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults who currently smoke cigarettes | Experience | C D T | 14.0% | lower | 6.1 (Healthy People 2030 national target (TU-02)) | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| People under 65 without health insurance | Access | C D T | 14.4% | lower | 7.6 (Healthy People 2030 national target (AHS-01: 92.4% of people under 65 insured)) | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults with a routine checkup in the past year | Access | C D T | 78.1% | higher |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults who saw a dentist in the past year | Access | C D T | 58.9% | higher |  | CDC PLACES: Local Data for Better Health, 2025 release | 2022 estimate |
| Primary care doctors per 100,000 people | Access | C | 67 | higher |  | HRSA Area Health Resources Files (American Medical Association Physician Masterfile), via County Health Rankings & Roadmaps | 2022 (CHR&R March 2026 update) |
| Dentists per 100,000 people | Access | C | 54 | higher |  | HRSA Area Health Resources Files (CMS National Provider Identifier file), via County Health Rankings & Roadmaps | 2023 (CHR&R March 2026 update) |
| Medicaid and other public medical aid per resident | Public money | C | 1,318 | none |  | U.S. Bureau of Economic Analysis, Regional Accounts table CAINC35; Census Bureau population estimates | 2022 |

Who runs services: Georgia Department of Community Health (Medicaid, PeachCare for Kids); Georgia Department of Public Health and county health departments; federally funded community health centers (HRSA).

Main public programs: Medicaid, PeachCare for Kids, Georgia Pathways to Coverage, Medicare, community health centers, local public health programs.

## Mental health

_Are residents in distress, and can they get treatment?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Adults with frequent mental distress (headline) | Experience | C D T | 17.3% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults ever told they have depression | Experience | C D T | 19.3% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Drug overdose deaths per 100,000 people, past 12 months | Experience | C | 14.0 | lower | 20.7 (Healthy People 2030 national target (SU-03)) | CDC NCHS, VSRR Provisional County-Level Drug Overdose Death Counts; Census Bureau population estimates | 12 months ending March 2026 |
| Suicide deaths per 100,000 people (age-adjusted) | Experience | C | 14.6 | lower | 12.8 (Healthy People 2030 national target (MHMD-01)) | CDC National Center for Health Statistics mortality files, via County Health Rankings & Roadmaps | 2019-2023 (five years combined) |
| Mental health providers per 100,000 people | Access | C | 201 | higher |  | CMS National Plan and Provider Enumeration System (NPI file), via County Health Rankings & Roadmaps | 2025 (CHR&R March 2026 update) |

Who runs services: Georgia Department of Behavioral Health and Developmental Disabilities and community service boards; Georgia Department of Community Health (Medicaid); 988 crisis line.

Main public programs: Medicaid behavioral health, community service board services, federal opioid response and settlement funds, crisis services.

## Public safety

_Are residents safe from crime and crashes?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Violent crime rate (headline) | Experience | C | 299 | lower |  | FBI Uniform Crime Reporting Program, Return A master files | 2025 calendar year |
| Property crime rate | Experience | C | 1,404 | lower |  | FBI Uniform Crime Reporting Program, Return A master files | 2025 calendar year |
| Traffic deaths per 100,000 people | Experience | C | 15.4 | lower | 10.1 (Healthy People 2030 national target (IVP-06)) | NHTSA Fatality Analysis Reporting System (FARS); Census Bureau population estimates | 2019-2023 (five years combined) |

Who runs services: City police, county sheriffs and the courts; Georgia Department of Public Safety (Georgia State Patrol); Governor's Office of Highway Safety; Criminal Justice Coordinating Council; Georgia Attorney General.

Main public programs: Local police and fire budgets, victim services, highway safety grants, violence prevention grants.

## Social well-being

_Are residents connected to each other and to community resources?_

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Adults who feel lonely always, usually or sometimes (headline) | Experience | C D T | 37.5% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Adults who lack social and emotional support | Experience | C D T | 24.6% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Voter turnout, 2024 presidential election | Experience | C | 67.0% | higher |  | Georgia Secretary of State official results, as compiled by the MIT Election Data + Science Lab; Census Bureau American Community Survey | November 2024 general election |
| Households with a broadband internet subscription | Access | C D T | 91.0% | higher |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Adults without reliable transportation in the past year | Access | C D T | 10.1% | lower |  | CDC PLACES: Local Data for Better Health, 2025 release | 2023 estimate |
| Households without a vehicle | Access | C D T | 5.9% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Public library visits per person | Access | C | 1.6 | higher |  | Institute of Museum and Library Services, Public Libraries Survey; Census Bureau population estimates | FY 2024 (July 2023 to June 2024 in Georgia) |
| Membership groups per 10,000 people | Access | C | 8.3 | higher |  | Census Bureau County Business Patterns; Census Bureau population estimates (definition from County Health Rankings & Roadmaps) | 2023 |
| Public library spending per person | Public money | C | 22.61 | higher |  | Institute of Museum and Library Services, Public Libraries Survey; Census Bureau population estimates | FY 2024 (July 2023 to June 2024 in Georgia) |

Who runs services: Local and regional library systems (with state support through Georgia Public Library Service); transit agencies; the state broadband office; county boards of elections and registration.

Main public programs: State library funding, transit funding, broadband expansion grants, park and recreation programs.

## Who lives here (context, not judged)

| Measure | Role | Levels | Georgia | Better | Standard | Source | Period |
|---|---|---|---|---|---|---|---|
| Population | Context | C D T | 10,940,407 | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Residents 65 and older | Context | C D T | 15.0% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Residents ages 25 to 54 | Context | C D T | 40.0% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| White, not Hispanic | Context | C D T | 49.1% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Black, not Hispanic | Context | C D T | 30.7% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Hispanic or Latino (any race) | Context | C D T | 11.0% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| Foreign-born residents | Context | C D T | 11.2% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
| People with a disability | Context | C D T | 13.1% | none |  | U.S. Census Bureau, American Community Survey 5-year estimates | 2020-2024 ACS 5-year |
