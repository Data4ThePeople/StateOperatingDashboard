"""The measure list for the Community Well-Being page (Ohio, and other states set in states.py): which measures sit in which of the nine dimensions,
whether each describes what residents experience or the services they can reach, and where a published standard
exists. 71_wb_data.py and 72_wb_build.py read this file; docs/MEASURES.md is written from it.

role:
  "lives"   What residents experience (conditions and outcomes).
  "access"  Services and access: what is available and whether people use it.
  "money"   Public money: what public programs spend or pay out in the place. Shown beside conditions, never as a
            cause of them.
headline: the measure the dimension opens on.
standard: a published target or benchmark with the same definition, or close enough that the note says how it
          differs. Most measures have none; they compare with Ohio and the U.S.
"""

DIMENSIONS = [
    {"id": "childcare", "label": "Child care",
     "question": "Can families find licensed, rated child care near home?",
     "agencies": "Ohio Department of Children and Youth (licensing, Step Up To Quality ratings and publicly funded child "
                 "care); county departments of job and family services (eligibility for publicly funded care); U.S. "
                 "Department of Health and Human Services, Administration for Children and Families (Child Care and "
                 "Development Fund, Head Start).",
     "programs": "Publicly funded child care, Step Up To Quality, Head Start and Early Head Start, public preschool."},
    {"id": "education", "label": "Education",
     "question": "Are students learning, showing up and finishing school?",
     "agencies": "Local school districts and community schools; Ohio Department of Education and Workforce; U.S. "
                 "Department of Education (Title I, special education).",
     "programs": "State foundation funding, Third Grade Reading Guarantee, Title I, IDEA special education, school meals."},
    {"id": "economic", "label": "Economic security",
     "question": "Do households have enough income to cover basic needs?",
     "agencies": "Ohio Department of Job and Family Services and county job and family services offices (SNAP, Ohio "
                 "Works First cash aid); USDA Food and Nutrition Service (SNAP); Social Security Administration (SSI); "
                 "Internal Revenue Service (Earned Income Tax Credit).",
     "programs": "SNAP, Ohio Works First (TANF), SSI, Earned Income Tax Credit, WIC, school meals, home energy assistance."},
    {"id": "jobs", "label": "Jobs and workforce",
     "question": "Can working-age residents find work that pays?",
     "agencies": "Ohio Department of Job and Family Services (unemployment insurance, OhioMeansJobs centers); local "
                 "workforce development boards; U.S. Department of Labor.",
     "programs": "Unemployment insurance, Workforce Innovation and Opportunity Act training, apprenticeships, career-technical education."},
    {"id": "housing", "label": "Housing",
     "question": "Is housing affordable, stable and in decent shape?",
     "agencies": "Local public housing authorities (vouchers, public housing); Ohio Housing Finance Agency (Low-Income "
                 "Housing Tax Credits, housing development); Ohio Department of Development (Community Development "
                 "Block Grants and HOME for smaller communities); U.S. Department of Housing and Urban Development.",
     "programs": "Housing Choice Vouchers, public housing, project-based rental assistance, Low-Income Housing Tax Credits, HOME, CDBG."},
    {"id": "physical", "label": "Physical health",
     "question": "Are residents healthy, covered and able to see a doctor?",
     "agencies": "Ohio Department of Medicaid; Ohio Department of Health and local health districts; federally "
                 "funded community health centers (HRSA).",
     "programs": "Medicaid, Medicare, community health centers, local public health programs."},
    {"id": "mental", "label": "Mental health",
     "question": "Are residents in distress, and can they get treatment?",
     "agencies": "Ohio Department of Behavioral Health; county alcohol, drug addiction and mental health (ADAMH) "
                 "boards; Ohio Department of Medicaid (including OhioRISE for young people); 988 crisis line.",
     "programs": "Medicaid behavioral health, ADAMH board services, federal opioid response and settlement funds, crisis services."},
    {"id": "safety", "label": "Public safety",
     "question": "Are residents safe from crime and crashes?",
     "agencies": "City police, county sheriffs and the courts; Ohio Department of Public Safety (Ohio State Highway "
                 "Patrol, Office of Criminal Justice Services, traffic safety office); Ohio Attorney General.",
     "programs": "Local police and fire budgets, victim services, highway safety grants, violence prevention grants."},
    {"id": "social", "label": "Social well-being",
     "question": "Are residents connected to each other and to community resources?",
     "agencies": "Local library systems (largely funded by Ohio's Public Library Fund); park districts; transit "
                 "agencies; BroadbandOhio (Ohio Department of Development); county boards of elections.",
     "programs": "Public Library Fund, transit funding, broadband expansion grants, park and recreation levies."},
]

HP = "Healthy People 2030 national target"
MEASURES = [
    # child care
    dict(id="childcare_programs_per1k", dim="childcare", role="access", headline=True),
    dict(id="childcare_rated_share", dim="childcare", role="access"),
    dict(id="preschool_enrolled", dim="childcare", role="access"),
    # education
    dict(id="grade3_ela_proficient", dim="education", role="lives", headline=True),
    dict(id="grade3_math_proficient", dim="education", role="lives"),
    dict(id="chronic_absent_rate", dim="education", role="lives"),
    dict(id="hs_or_higher", dim="education", role="lives"),
    dict(id="bachelors_or_higher", dim="education", role="lives"),
    # economic security
    dict(id="below_200_share", dim="economic", role="lives", headline=True),
    dict(id="poverty_rate", dim="economic", role="lives"),
    dict(id="saipe_child_poverty_rate", dim="economic", role="lives"),
    dict(id="median_household_income", dim="economic", role="lives"),
    dict(id="places_food_insecurity", dim="economic", role="lives"),
    dict(id="gini", dim="economic", role="lives"),
    dict(id="snap_households_share", dim="economic", role="access"),
    dict(id="snap_persons_share", dim="economic", role="access"),
    # jobs
    dict(id="unemployment_rate", dim="jobs", role="lives", headline=True),
    dict(id="prime_age_epop", dim="jobs", role="lives"),
    dict(id="avg_weekly_wage", dim="jobs", role="lives"),
    dict(id="labor_force_change_pct", dim="jobs", role="lives"),
    dict(id="mean_commute", dim="jobs", role="access"),
    # housing
    dict(id="rent_burden", dim="housing", role="lives", headline=True),
    dict(id="owner_cost_burden", dim="housing", role="lives"),
    dict(id="places_housing_insecurity", dim="housing", role="lives"),
    dict(id="places_utility_shutoff", dim="housing", role="lives"),
    dict(id="overcrowded_share", dim="housing", role="lives"),
    dict(id="homeownership", dim="housing", role="lives"),
    dict(id="vacancy_rate", dim="housing", role="lives"),
    dict(id="old_housing_share", dim="housing", role="lives"),
    dict(id="hud_households_per_1000", dim="housing", role="access"),
    # physical health
    dict(id="places_ghlth", dim="physical", role="lives", headline=True),
    dict(id="places_diabetes", dim="physical", role="lives"),
    dict(id="places_obesity", dim="physical", role="lives"),
    dict(id="places_smoking", dim="physical", role="lives",
         standard=dict(v=6.1, src=HP + " (TU-02)", note="The target is age-adjusted and comes from a national survey; "
                                                         "the local figures here are not age-adjusted.")),
    dict(id="uninsured_u65", dim="physical", role="access",
         standard=dict(v=7.6, src=HP + " (AHS-01: 92.4% of people under 65 insured)",
                       note="The target comes from a different national survey (NHIS).")),
    dict(id="places_checkup", dim="physical", role="access"),
    dict(id="places_dental", dim="physical", role="access"),
    dict(id="pcp_per100k", dim="physical", role="access"),
    dict(id="dentists_per100k", dim="physical", role="access"),
    # mental health
    dict(id="places_mental_distress", dim="mental", role="lives", headline=True),
    dict(id="places_depression", dim="mental", role="lives"),
    dict(id="overdose_rate_per100k", dim="mental", role="lives",
         standard=dict(v=20.7, src=HP + " (SU-03)", note="The target is age-adjusted; the local rates here are not.")),
    dict(id="suicide_rate", dim="mental", role="lives",
         standard=dict(v=12.8, src=HP + " (MHMD-01)", note="The target is age-adjusted.")),
    dict(id="mh_providers_per100k", dim="mental", role="access"),
    # public safety
    dict(id="violent_crime_rate", dim="safety", role="lives", headline=True),
    dict(id="property_crime_rate", dim="safety", role="lives"),
    dict(id="traffic_deaths_per100k", dim="safety", role="lives",
         standard=dict(v=10.1, src=HP + " (IVP-06)", note="The target is age-adjusted and counts deaths where the person lived; "
                                                                "the local rates here are not age-adjusted and count deaths where the crash happened.")),
    # social well-being
    dict(id="places_loneliness", dim="social", role="lives", headline=True),
    dict(id="places_emotional_support", dim="social", role="lives"),
    dict(id="voter_turnout", dim="social", role="lives"),
    dict(id="broadband_share", dim="social", role="access"),
    dict(id="places_no_transportation", dim="social", role="access"),
    dict(id="no_vehicle_share", dim="social", role="access"),
    dict(id="library_visits_per_capita", dim="social", role="access"),
    dict(id="social_associations_per10k", dim="social", role="access"),
]

# Public money: spending and benefit measures shown in the dimension they relate to. Filled from
# data/processed/public_money.json; ids that are not in that file are skipped with a warning.
MONEY = {
    "economic": ["bea_snap_per_resident", "bea_ssi_per_resident", "bea_eitc_per_resident", "bea_veterans_per_resident"],
    "jobs": ["bea_unemployment_per_resident"],
    "housing": ["hud_spending_per_resident"],
    "physical": ["bea_medicaid_per_resident"],
    "education": ["school_spending_per_pupil", "school_revenue_state_share"],
    "social": ["library_spend_per_capita"],
}

# who lives here: shown on every place profile, not judged
CONTEXT = ["population", "age65_share", "prime_age_share", "nh_white_share", "nh_black_share", "hispanic_share",
           "foreign_born_share", "disability_share"]

# Who runs services and the main public programs, for states other than Ohio. Same dimensions and questions; only the
# agencies and program names change.
STATE_TEXT = {
    "ga": {
        "childcare": ("Georgia Department of Early Care and Learning (licensing, Quality Rated, the Childcare and Parent "
                      "Services subsidy program and Georgia's Pre-K Program); U.S. Department of Health and Human "
                      "Services, Administration for Children and Families (Child Care and Development Fund, Head Start).",
                      "Childcare and Parent Services (CAPS) subsidies, Quality Rated, Georgia's Pre-K Program, Head Start and "
                      "Early Head Start."),
        "education": ("Local school districts and charter schools; Georgia Department of Education; Governor's Office of "
                      "Student Achievement; U.S. Department of Education (Title I, special education).",
                      "Quality Basic Education state funding, Title I, IDEA special education, school meals."),
        "economic": ("Georgia Department of Human Services, Division of Family and Children Services (SNAP, TANF cash aid); "
                     "USDA Food and Nutrition Service (SNAP); Social Security Administration (SSI); Internal Revenue "
                     "Service (Earned Income Tax Credit).",
                     "SNAP, TANF, SSI, Earned Income Tax Credit, WIC, school meals, home energy assistance."),
        "jobs": ("Georgia Department of Labor (unemployment insurance, career centers); local workforce development "
                 "boards; Technical College System of Georgia; U.S. Department of Labor.",
                 "Unemployment insurance, Workforce Innovation and Opportunity Act training, apprenticeships, technical "
                 "college programs."),
        "housing": ("Local public housing authorities (vouchers, public housing); Georgia Department of Community Affairs "
                    "(Low-Income Housing Tax Credits, vouchers where there is no local authority, Community Development "
                    "Block Grants and HOME for smaller communities); U.S. Department of Housing and Urban Development.",
                    "Housing Choice Vouchers, public housing, project-based rental assistance, Low-Income Housing Tax "
                    "Credits, HOME, CDBG."),
        "physical": ("Georgia Department of Community Health (Medicaid, PeachCare for Kids); Georgia Department of Public "
                     "Health and county health departments; federally funded community health centers (HRSA).",
                     "Medicaid, PeachCare for Kids, Georgia Pathways to Coverage, Medicare, community health centers, local "
                     "public health programs."),
        "mental": ("Georgia Department of Behavioral Health and Developmental Disabilities and community service boards; "
                   "Georgia Department of Community Health (Medicaid); 988 crisis line.",
                   "Medicaid behavioral health, community service board services, federal opioid response and "
                   "settlement funds, crisis services."),
        "safety": ("City police, county sheriffs and the courts; Georgia Department of Public Safety (Georgia State "
                   "Patrol); Governor's Office of Highway Safety; Criminal Justice Coordinating Council; Georgia "
                   "Attorney General.",
                   "Local police and fire budgets, victim services, highway safety grants, violence prevention grants."),
        "social": ("Local and regional library systems (with state support through Georgia Public Library Service); "
                   "transit agencies; the state broadband office; county boards of elections and registration.",
                   "State library funding, transit funding, broadband expansion grants, park and recreation programs."),
    },
    "il": {
        "childcare": ("Illinois Department of Early Childhood (child care licensing, the Child Care Assistance Program and "
                      "Preschool for All, since July 2026; licensing was with the Department of Children and Family "
                      "Services before then); ExceleRate Illinois; U.S. Department of Health and Human Services, "
                      "Administration for Children and Families (Child Care and Development Fund, Head Start).",
                      "Child Care Assistance Program, ExceleRate Illinois, Preschool for All, Head Start and Early Head "
                      "Start."),
        "education": ("Local school districts and charter schools; Illinois State Board of Education and Regional Offices "
                      "of Education; U.S. Department of Education (Title I, special education).",
                      "Evidence-Based Funding state aid, Title I, IDEA special education, school meals."),
        "economic": ("Illinois Department of Human Services (SNAP, TANF cash aid); USDA Food and Nutrition Service (SNAP); "
                     "Social Security Administration (SSI); Internal Revenue Service and Illinois Department of Revenue "
                     "(federal and state Earned Income Tax Credits).",
                     "SNAP, TANF, SSI, federal and Illinois Earned Income Tax Credits, WIC, school meals, home energy "
                     "assistance."),
        "jobs": ("Illinois Department of Employment Security (unemployment insurance); Illinois Department of Commerce "
                 "and Economic Opportunity and local workforce boards; Illinois Community College Board; U.S. "
                 "Department of Labor.",
                 "Unemployment insurance, Workforce Innovation and Opportunity Act training, apprenticeships, community "
                 "college career programs."),
        "housing": ("Local public housing authorities (vouchers, public housing); Illinois Housing Development Authority "
                    "(Low-Income Housing Tax Credits, rental help); Illinois Department of Commerce and Economic "
                    "Opportunity (Community Development Block Grants for smaller communities); U.S. Department of "
                    "Housing and Urban Development.",
                    "Housing Choice Vouchers, public housing, project-based rental assistance, Low-Income Housing Tax "
                    "Credits, HOME, CDBG."),
        "physical": ("Illinois Department of Healthcare and Family Services (Medicaid, All Kids); Illinois Department of "
                     "Public Health and local health departments; federally funded community health centers (HRSA).",
                     "Medicaid, All Kids, Medicare, community health centers, local public health programs."),
        "mental": ("Illinois Department of Human Services (mental health and substance use programs); Illinois "
                   "Department of Healthcare and Family Services (Medicaid); county and township mental health boards; "
                   "988 crisis line.",
                   "Medicaid behavioral health, community mental health services, federal opioid response and "
                   "settlement funds, crisis services."),
        "safety": ("City police, county sheriffs and the courts; Illinois State Police; Illinois Criminal Justice "
                   "Information Authority; Illinois Department of Transportation (highway safety); Illinois Attorney "
                   "General.",
                   "Local police and fire budgets, victim services, highway safety grants, violence prevention grants."),
        "social": ("Local public libraries and library districts (with state grants through the Illinois State Library); "
                   "transit agencies; the state broadband office; county clerks and election boards.",
                   "State library grants, transit funding, broadband expansion grants, park district and recreation "
                   "programs."),
    },
}


def _apply_state_text():
    from common import ST_ID
    for d in DIMENSIONS:
        if ST_ID in STATE_TEXT:
            d["agencies"], d["programs"] = STATE_TEXT[ST_ID][d["id"]]


_apply_state_text()
