"""
Authoritative Official Statutory Corpus for Verified Citizen Welfare Schemes.
Provides comprehensive, structure-aware statutory clauses, progressive benefit tranches,
tables, exclusion criteria, and document requirements for all 29 certified citizen schemes.
"""
from typing import Any, Dict

CERTIFIED_SCHEMES_OFFICIAL_CORPUS: Dict[str, Dict[str, Any]] = {
    "dbtbharat_central_schemes_pm_kisan": {
        "scheme_name": "PM KISAN",
        "doc_title": "DA&FW PM-KISAN Operational Guidelines with Mandatory eKYC and Statutory Exclusions",
        "doc_type": "operational_guidelines",
        "source_url": "https://pmkisan.gov.in",
        "effective_from": "2019-02-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Core Scheme Objectives & Direct Benefit Transfer Tranches",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, DA&FW PM-KISAN Operational Guidelines",
                "content": (
                    "Under Pradhan Mantri Kisan Samman Nidhi (PM-KISAN), eligible landholding farmer families "
                    "receive direct financial support of ₹6,000 per financial year. The financial assistance is disbursed "
                    "in three equal four-monthly installments/tranches of ₹2,000 each (Period 1: April-July, Period 2: August-November, "
                    "Period 3: December-March) directly into the bank accounts of beneficiaries through Direct Benefit Transfer (DBT) via PFMS."
                ),
                "tranches": [
                    {
                        "tranche_name": "Period 1 (April-July)",
                        "amount": "₹2,000",
                        "tenure": "4 months",
                        "conditions": "1st four-monthly installment transferred via DBT to Aadhaar-seeded bank account."
                    },
                    {
                        "tranche_name": "Period 2 (August-November)",
                        "amount": "₹2,000",
                        "tenure": "4 months",
                        "conditions": "2nd four-monthly installment transferred via DBT upon active land record validation."
                    },
                    {
                        "tranche_name": "Period 3 (December-March)",
                        "amount": "₹2,000",
                        "tenure": "4 months",
                        "conditions": "3rd four-monthly installment transferred via DBT upon mandatory eKYC completion."
                    }
                ],
                "tables": [
                    {
                        "title": "PM-KISAN Installment Tranches Schedule",
                        "headers": ["Installment / Tranche", "Period", "Amount (₹)", "Disbursement Mode"],
                        "rows": [
                            ["1st Installment", "April - July", "₹2,000", "Direct Benefit Transfer (DBT)"],
                            ["2nd Installment", "August - November", "₹2,000", "Direct Benefit Transfer (DBT)"],
                            ["3rd Installment", "December - March", "₹2,000", "Direct Benefit Transfer (DBT)"],
                            ["Annual Total Benefit", "Full Financial Year", "₹6,000", "Direct Benefit Transfer (DBT)"]
                        ]
                    }
                ]
            },
            {
                "heading": "Landholding Eligibility & Family Definition",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, DA&FW PM-KISAN Operational Guidelines",
                "content": (
                    "All landholding farmer families having cultivable landholding in their names are eligible for benefits under the scheme. "
                    "A farmer family is defined as a family comprising husband, wife, and minor children who own cultivable land as per the "
                    "land records of the respective State or Union Territory. Benefits are restricted to one entitlement per farmer family. "
                    "Land ownership transfer cutoff applies: land transfers after 01 February 2019 are not eligible for scheme benefits for 5 years, "
                    "except in cases of succession or inheritance upon death of the original landowner."
                )
            },
            {
                "heading": "Statutory Institutional & Post-Holder Exclusions (Category A)",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.2(A), DA&FW PM-KISAN Statutory Exclusions",
                "content": (
                    "The following categories of beneficiaries are strictly EXCLUDED from PM-KISAN entitlement under Category A: "
                    "(a) All institutional landholders; "
                    "(b) Farmer families where one or more of its members belong to the following categories: "
                    "Former and present holders of constitutional posts; "
                    "Former and present Ministers, Ministers of State, Members of Parliament (MPs), Members of Legislative Assemblies (MLAs), "
                    "Members of Legislative Councils (MLCs), Mayors of Municipal Corporations, and Chairpersons of District Panchayats."
                ),
                "nested_items": [
                    {
                        "item_title": "Category A Constitutional & Public Office Exclusions",
                        "items": [
                            "All institutional landholders",
                            "Former and present holders of constitutional posts",
                            "Former and present Ministers and Ministers of State",
                            "Former and present Members of Parliament (Lok Sabha and Rajya Sabha)",
                            "Former and present Members of Legislative Assemblies and Councils (MLAs and MLCs)",
                            "Former and present Mayors of Municipal Corporations and Chairpersons of District Panchayats"
                        ]
                    }
                ]
            },
            {
                "heading": "Statutory Income Tax, Pensioner & Professional Exclusions (Category B)",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.2(B), DA&FW PM-KISAN Statutory Exclusions",
                "content": (
                    "The following categories of farmers are strictly EXCLUDED under Category B: "
                    "(a) All serving or retired officers and employees of Central/State Government Ministries, Offices, Departments, "
                    "and Public Sector Undertakings (excluding Multi-Tasking Staff / Class IV / Group D employees); "
                    "(b) All superannuated/retired pensioners whose monthly pension is ₹10,000 or more (excluding Group D / MTS pensioners); "
                    "(c) All persons who paid Income Tax in the last assessment year; "
                    "(d) Professionals like Doctors, Engineers, Lawyers, Chartered Accountants (CAs), and Architects registered with "
                    "professional bodies and carrying on practice."
                ),
                "nested_items": [
                    {
                        "item_title": "Category B Income Tax, Pensioner & Professional Exclusions",
                        "items": [
                            "Serving or retired government employees of Central/State Govt and PSUs (excluding MTS / Class IV / Group D)",
                            "Retired pensioners receiving monthly pension of ₹10,000 or more (excluding Group D / MTS pensioners)",
                            "All persons who paid Income Tax in the last assessment year",
                            "Registered practicing professionals: Doctors, Engineers, Lawyers, Chartered Accountants (CAs), Architects"
                        ]
                    }
                ]
            },
            {
                "heading": "Mandatory Documents & eKYC Requirements",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, DA&FW PM-KISAN Operational Guidelines",
                "content": (
                    "Mandatory documentation requirements for PM-KISAN include: "
                    "(1) Aadhaar Card: Mandatory identity credential linked to active bank account; "
                    "(2) Land ownership records: Up-to-date Land Records / RoR / Khatauni showing cultivable land ownership in applicant's name; "
                    "(3) Bank Account Details: Aadhaar-seeded active bank account with correct IFSC; "
                    "(4) Mandatory eKYC: eKYC verification is compulsory for all beneficiaries, completed via OTP on the PM-KISAN portal (https://pmkisan.gov.in), "
                    "biometric verification at Common Service Centres (CSC), or facial recognition via PM-KISAN Mobile App."
                )
            },
            {
                "heading": "Application Procedure & Portal Registration",
                "section_type": "application_process",
                "citation_clause": "Clause 5.1, DA&FW PM-KISAN Operational Guidelines",
                "content": (
                    "Farmers can register through the official PM-KISAN portal (https://pmkisan.gov.in) under the 'Farmer Corner' -> 'New Farmer Registration', "
                    "or by visiting the nearest Common Service Centre (CSC) or State Agriculture Department nodal office. "
                    "State and Union Territory Governments carry out land verification and approval of applications before forward transmission for payment."
                )
            },
            {
                "heading": "Statutory Grievance Redressal Mechanism & Farmer Helpdesk",
                "section_type": "application_process",
                "citation_clause": "Clause 6.1, DA&FW PM-KISAN Grievance Redressal Guidelines",
                "content": (
                    "PM-KISAN provides a multi-tier grievance redressal mechanism for farmers: "
                    "(1) Farmers can register complaints online on the PM-KISAN portal under 'Farmer Corner' -> 'Help Desk / Grievance Redressal'; "
                    "(2) Dedicated National Toll-Free Helplines are operational: 155261, 1800-115-526, and 011-24300606; "
                    "(3) District Grievance Redressal Committees chaired by the District Collector / District Magistrate resolve land record corrections, "
                    "Aadhaar seeding mismatches, and delayed DBT installment releases within 30 days."
                )
            }
        ]
    },

    "dbtbharat_central_schemes_pradhan_mantri_ujjwala_yojana": {
        "scheme_name": "Pradhan Mantri Ujjwala Yojana (Ujjwala 2.0)",
        "doc_title": "MoPNG Pradhan Mantri Ujjwala Yojana (Ujjwala 2.0) Comprehensive Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://pmuy.gov.in",
        "effective_from": "2021-08-10",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Ujjwala 2.0 Free Connection & Stove Entitlement",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, MoPNG Ujjwala 2.0 Comprehensive Guidelines",
                "content": (
                    "Under Ujjwala 2.0 (PMUY), eligible poor households receive a deposit-free LPG connection. "
                    "The Central Government provides financial assistance covering the security deposit of cylinder (₹1,250 for 14.2 kg or ₹800 for 5 kg), "
                    "pressure regulator (₹150), LPG hose pipe (₹100), domestic gas consumer card (₹25), and installation/inspection charges (₹75), "
                    "totaling ₹1,600 financial assistance per connection. "
                    "In addition, Ujjwala 2.0 provides the FIRST REFILL OF 14.2 KG CYLINDER COMPLETELY FREE OF COST and a FREE DOUBLE-BURNER HOTPLATE (STOVE) "
                    "provided to the beneficiary at connection release without any loan burden."
                )
            },
            {
                "heading": "₹1,600 Financial Assistance & Subsidy Breakdown Table",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.2, MoPNG Ujjwala 2.0 Financial Structure Guidelines",
                "content": (
                    "The Central Government provides financial assistance of ₹1,600 for each new deposit-free LPG connection released under PMUY Ujjwala 2.0. "
                    "The item-wise subsidy breakdown is as follows: "
                    "1. Security deposit of 14.2 kg cylinder: ₹1,250 (or ₹800 for 5 kg cylinder); "
                    "2. Security deposit of pressure regulator: ₹150; "
                    "3. Suraksha LPG hose pipe: ₹100; "
                    "4. Domestic Gas Consumer Card (DGCC passbook): ₹25; "
                    "5. Installation and demonstration charges: ₹75. "
                    "Total Central Government Subsidy: ₹1,600. "
                    "Beneficiaries also receive a free first refill of 14.2 kg cylinder and a free double-burner hotplate (stove) at connection release."
                ),
                "tables": [
                    {
                        "title": "₹1,600 Subsidy Component Breakdown",
                        "headers": ["Component Description", "Prescribed Subsidy Amount (₹)", "Statutory Coverage"],
                        "rows": [
                            ["Security Deposit of 14.2 kg LPG Cylinder", "₹1,250", "Full deposit covered by Central Govt (₹800 for 5 kg)"],
                            ["Security Deposit of Pressure Regulator", "₹150", "Full regulator cost covered"],
                            ["Suraksha LPG Hose Pipe", "₹100", "Certified ISI safety hose pipe"],
                            ["Domestic Gas Consumer Card (DGCC)", "₹25", "Official gas connection consumer card"],
                            ["Installation and Inspection Charges", "₹75", "Authorized technician charges"],
                            ["Total Central Financial Assistance", "₹1,600", "100% deposit-free connection subsidy"],
                            ["First Refill of 14.2 kg Cylinder", "Free of Cost", "Additional Ujjwala 2.0 benefit"],
                            ["Double-Burner Hotplate (Stove)", "Free of Cost", "Additional Ujjwala 2.0 benefit"]
                        ]
                    }
                ]
            },
            {
                "heading": "Target Beneficiary & Adult Female Applicant Criteria across Priority Categories",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, MoPNG Ujjwala 2.0 Guidelines",
                "content": (
                    "To qualify for PMUY Ujjwala 2.0: "
                    "(a) The applicant MUST BE AN ADULT WOMAN aged 18 years or above; no male member can apply; "
                    "(b) The applicant must belong to a poor household meeting any of the identified categories: "
                    "SC/ST households, Pradhan Mantri Awas Yojana (Gramin) beneficiaries, Antyodaya Anna Yojana (AAY) ration card holders, "
                    "Forest Dwellers, Most Backward Classes (MBC), Tea and Ex-Tea Garden Tribes, Island/River Island dwellers, "
                    "or poor households identified under the 14-point deprivation declaration."
                ),
                "nested_items": [
                    {
                        "item_title": "Ujjwala 2.0 Eligible Priority Categories",
                        "items": [
                            "Adult woman aged 18 years or above belonging to poor household",
                            "Scheduled Caste (SC) and Scheduled Tribe (ST) households",
                            "Pradhan Mantri Awas Yojana (Gramin) - PMAY(G) beneficiaries",
                            "Antyodaya Anna Yojana (AAY) ration card holder households",
                            "Forest Dwellers and traditional forest forest communities",
                            "Most Backward Classes (MBC) households",
                            "Tea and Ex-Tea Garden Tribes",
                            "Residents of Islands and River Islands",
                            "Poor households qualified under the 14-point deprivation declaration"
                        ]
                    }
                ]
            },
            {
                "heading": "14-Point Deprivation Declaration & Poor Household Self-Certification",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.2, MoPNG Ujjwala 2.0 Deprivation Declaration Guidelines",
                "content": (
                    "Poor households not listed in SECC or priority ration card lists can establish eligibility through the statutory 14-Point Deprivation Declaration. "
                    "The applicant woman self-certifies that her household does not own: (1) motorized two/three/four wheeler; (2) mechanized 3-4 wheeler agricultural equipment; "
                    "(3) Kisan Credit Card with credit limit of ₹50,000 or above; (4) household member in government employment; (5) registered non-agricultural enterprise; "
                    "(6) paying income tax or professional tax; (7) pucca house with 3 or more rooms; or (8) owning 5 acres or more of irrigated agricultural land. "
                    "Meeting the 14-point deprivation criteria qualifies the household as BPL for release of a deposit-free Ujjwala 2.0 connection."
                )
            },
            {
                "heading": "Household Deduplication & OMC Exclusion Rule",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, MoPNG Ujjwala 2.0 Guidelines",
                "content": (
                    "Strict household deduplication applies: There must be NO EXISTING LPG CONNECTION in the same household in the name of "
                    "the applicant or ANY MEMBER OF THE HOUSEHOLD (defined as applicant, spouse, and unmarried children) from any Oil Marketing Company "
                    "(IOCL - Indane, BPCL - Bharat Gas, HPCL - HP Gas). Any existing active connection in the household permanently excludes the applicant. "
                    "All adult members' Aadhaar details are verified against the inter-OMC national deduplication portal."
                )
            },
            {
                "heading": "Mandatory Documents & Migrant Declaration (Annexure I)",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, MoPNG Ujjwala 2.0 Guidelines",
                "content": (
                    "Mandatory documentation for Ujjwala 2.0: "
                    "(1) Aadhaar Card: Mandatory proof of identity and proof of address for adult woman applicant; "
                    "(2) Aadhaar of all adult family members listed in ration card; "
                    "(3) Ration Card or Family Composition Certificate issued by State Government (migrant workers can submit self-declaration Annexure I in lieu of ration card and local address proof); "
                    "(4) Active Bank Account details (Bank Name, Account Number, IFSC) for DBT transfer; "
                    "(5) Supplementary 14-point declaration form proving BPL/poor household status."
                )
            },
            {
                "heading": "Application Procedure via OMC Distributors & Online Portal",
                "section_type": "application_process",
                "citation_clause": "Clause 5.1, MoPNG Ujjwala 2.0 Guidelines",
                "content": (
                    "Eligible women can apply online at the official portal (https://pmuy.gov.in) or submit paper applications at nearest "
                    "LPG distributor of IOCL (Indane), BPCL (Bharat Gas), or HPCL (HP Gas). Distributors verify documents, perform biometric eKYC, "
                    "and carry out electronic deduplication before releasing the gas connection with free stove and free first refill."
                )
            }
        ]
    },

    "dbtbharat_central_schemes_pm_street_vendor_atmanirbhar_nidhi_pm_svanidhi": {
        "scheme_name": "PM SVANidhi",
        "doc_title": "MoHUA PM SVANidhi Scheme Restructuring Guidelines (Cabinet Decision 27 August 2025)",
        "doc_type": "cabinet_decision_guidelines",
        "source_url": "https://pmsvanidhi.mohua.gov.in",
        "effective_from": "2025-08-27",
        "effective_to": "2030-03-31",
        "currentness": "current",
        "sections": [
            {
                "heading": "Restructured Working Capital Loan Tranches (Cabinet 27 Aug 2025)",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, MoHUA Restructured PM SVANidhi Guidelines (27 Aug 2025)",
                "effective_from": "2025-08-27",
                "effective_to": "2030-03-31",
                "currentness": "current",
                "content": (
                    "As restructured by the Union Cabinet on 27 August 2025, PM SVANidhi provides progressive collateral-free credit in three tranches: "
                    "1st Tranche: Working capital loan up to ₹15,000 with a repayment tenure of 12 months; "
                    "2nd Tranche: Enhanced working capital loan up to ₹25,000 with a tenure of 18 months upon timely or early repayment of the 1st tranche; "
                    "3rd Tranche: Business expansion loan up to ₹50,000 with a tenure of 36 months upon timely or early repayment of the 2nd tranche. "
                    "The scheme is valid up to 31 March 2030."
                ),
                "tranches": [
                    {
                        "tranche_name": "1st Tranche",
                        "amount": "₹15,000",
                        "tenure": "12 months",
                        "conditions": "Collateral-free initial working capital loan; unlocked for eligible urban street vendors with CoV or LOR."
                    },
                    {
                        "tranche_name": "2nd Tranche",
                        "amount": "₹25,000",
                        "tenure": "18 months",
                        "conditions": "Enhanced working capital loan unlocked upon timely or early repayment of the 1st tranche."
                    },
                    {
                        "tranche_name": "3rd Tranche",
                        "amount": "₹50,000",
                        "tenure": "36 months",
                        "conditions": "Business expansion loan unlocked upon timely or early repayment of the 2nd tranche."
                    }
                ],
                "tables": [
                    {
                        "title": "Restructured PM SVANidhi Loan Tranches Schedule (2025)",
                        "headers": ["Tranche Level", "Maximum Loan Amount (₹)", "Repayment Tenure", "Prerequisite Qualification"],
                        "rows": [
                            ["1st Tranche", "₹15,000", "12 months (1 year)", "Street Vendor with CoV / ID Card / LOR"],
                            ["2nd Tranche", "₹25,000", "18 months (1.5 years)", "Timely or early full repayment of 1st Tranche"],
                            ["3rd Tranche", "₹50,000", "36 months (3 years)", "Timely or early full repayment of 2nd Tranche"]
                        ]
                    }
                ]
            },
            {
                "heading": "Interest Subsidy & Digital Cashback Incentives",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.2, MoHUA Restructured PM SVANidhi Guidelines",
                "content": (
                    "Beneficiaries who repay loans on or before scheduled due dates receive an INTEREST SUBSIDY OF 7% PER ANNUM. "
                    "The subsidy is credited quarterly directly into the vendor's bank account through DBT. "
                    "Vendors also receive digital transaction cashback up to ₹100 per month (maximum ₹1,200 per year) for adopting QR code digital payments "
                    "(incentive of ₹1 per eligible transaction up to 100 transactions per month). "
                    "There is ZERO PENALTY for early or prepayment of loans."
                )
            },
            {
                "heading": "Geographic Scope & Vendor Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, MoHUA PM SVANidhi Guidelines",
                "content": (
                    "The scheme is available to all street vendors, hawkers, thelewale, and rehri-patri vendors engaged in vending in "
                    "statutory urban towns, peri-urban areas, census towns, and rural-urban interface growth centres. "
                    "Vendors must possess a Certificate of Vending (CoV) or Identity Card issued by the Urban Local Body (ULB) / Town Vending Committee (TVC), "
                    "or a Letter of Recommendation (LOR) issued by ULB/TVC."
                )
            },
            {
                "heading": "Mandatory Documents & Vending Proof",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoHUA PM SVANidhi Guidelines",
                "content": (
                    "Mandatory documentation required for PM SVANidhi: "
                    "(1) Certificate of Vending (CoV) or Identity Card issued by ULB/Town Vending Committee, OR Letter of Recommendation (LOR); "
                    "(2) Aadhaar Card: Mandatory identity and address proof; "
                    "(3) Aadhaar-linked active Mobile Number; "
                    "(4) Bank Account details (Account Number, Bank Passbook, IFSC) for loan disbursement."
                )
            },
            {
                "heading": "Application Procedure & Lending Partners",
                "section_type": "application_process",
                "citation_clause": "Section 5.1, MoHUA PM SVANidhi Guidelines",
                "content": (
                    "Street vendors can apply online via the PM SVANidhi portal (https://pmsvanidhi.mohua.gov.in) or PM SVANidhi Mobile App, "
                    "or through Common Service Centres (CSC), Banking Correspondents (BCs), or Urban Local Body (ULB) helpdesks. "
                    "Loans are disbursed by Scheduled Commercial Banks, Regional Rural Banks (RRBs), Small Finance Banks, and NBFC-MFIs."
                )
            }
        ]
    },

    "dbtbharat_central_schemes_pm_vishwakarma": {
        "scheme_name": "PM Vishwakarma",
        "doc_title": "MoMSME Operational Guidelines for PM Vishwakarma Scheme",
        "doc_type": "operational_guidelines",
        "source_url": "https://pmvishwakarma.gov.in",
        "effective_from": "2023-09-17",
        "effective_to": "2028-03-31",
        "currentness": "current",
        "sections": [
            {
                "heading": "Notified 18 Traditional Trades & Coverage",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, MoMSME PM Vishwakarma Operational Guidelines",
                "content": (
                    "PM Vishwakarma covers traditional artisans and craftspeople working with hands and tools across 18 notified trades: "
                    "(1) Carpenter (Suthar), (2) Boat Maker, (3) Armourer, (4) Blacksmith (Lohar), (5) Hammer and Tool Kit Maker, "
                    "(6) Locksmith, (7) Sculptor (Moortikar / Stone Carver / Stone Breaker), (8) Stone Breaker, (9) Cobbler (Charmkar / Shoesmith / Footwear Artisan), "
                    "(10) Mason (Rajmistri), (11) Basket / Mat / Broom Maker / Coir Weaver, (12) Doll & Toy Maker (Traditional), "
                    "(13) Barber (Naai), (14) Garland Maker (Malakaar), (15) Washerman (Dhobi), (16) Tailor (Darzi), "
                    "(17) Fishing Net Maker, (18) Goldsmith (Sonar)."
                ),
                "tables": [
                    {
                        "title": "18 Notified Traditional Trades Schedule",
                        "headers": ["Trade Category", "Trade Name", "Traditional Craft Description"],
                        "rows": [
                            ["Wood-based", "Carpenter (Suthar)", "Woodworking, wooden implement and furniture maker"],
                            ["Wood-based", "Boat Maker", "Traditional wooden boat builder and repairer"],
                            ["Iron/Metal-based", "Armourer", "Traditional arms and protective wear maker"],
                            ["Iron/Metal-based", "Blacksmith (Lohar)", "Iron forging and agricultural iron implement maker"],
                            ["Iron/Metal-based", "Hammer and Tool Kit Maker", "Manual hammer and artisan hand-tool maker"],
                            ["Iron/Metal-based", "Locksmith", "Traditional key and lock maker/repairer"],
                            ["Stone-based", "Sculptor (Moortikar / Stone Carver)", "Traditional stone sculptor and idol carver"],
                            ["Stone-based", "Stone Breaker", "Manual quarry stone cutter and dresser"],
                            ["Leather-based", "Cobbler (Charmkar / Shoesmith)", "Footwear craftsman and leather artisan"],
                            ["Construction", "Mason (Rajmistri)", "Traditional building mason and brickworker"],
                            ["Fibre/Grass-based", "Basket / Mat / Broom Maker / Coir Weaver", "Natural fibre weaver and broom maker"],
                            ["Clay/Toy-based", "Doll & Toy Maker (Traditional)", "Traditional heritage toy and doll artisan"],
                            ["Personal Service", "Barber (Naai)", "Traditional hair-grooming and shaving service provider"],
                            ["Floral/Plant-based", "Garland Maker (Malakaar)", "Traditional garland and ritual flower decorator"],
                            ["Personal Service", "Washerman (Dhobi)", "Traditional clothes washer and laundry artisan"],
                            ["Textile-based", "Tailor (Darzi)", "Garment stitcher and tailoring craftsperson"],
                            ["Aquatic/Marine", "Fishing Net Maker", "Manual fishing net maker and repair artisan"],
                            ["Precious Metal", "Goldsmith (Sonar)", "Gold and silver traditional jewelry maker"]
                        ]
                    }
                ]
            },
            {
                "heading": "Age, Family Limitation & Credit Overlap Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.2, MoMSME PM Vishwakarma Guidelines",
                "content": (
                    "Eligibility and strict exclusion criteria: "
                    "(a) Minimum age: An artisan must be at least 18 years of age on the date of registration; "
                    "(b) One Member Per Family: Benefits are strictly restricted to ONLY ONE MEMBER PER FAMILY (family defined as husband, wife, and unmarried children); "
                    "(c) Credit Overlap Exclusion: The applicant must not have availed loans under similar credit-based schemes of Central/State Government "
                    "for self-employment or business development (such as PMEGP, PM SVANidhi, Mudra) in the past 5 years, unless such loans have been fully repaid; "
                    "(d) Government Employee Exclusion: A person in government service (Central/State) and their family members are strictly NOT ELIGIBLE."
                ),
                "nested_items": [
                    {
                        "item_title": "PM Vishwakarma Statutory Exclusions",
                        "items": [
                            "Persons below 18 years of age on registration date",
                            "More than one member from the same family (husband, wife, unmarried children)",
                            "Persons who availed unpaid government self-employment loans (PMEGP, PM SVANidhi, Mudra) within past 5 years",
                            "Persons in government service (Central/State Govt or PSUs) and their family members"
                        ]
                    }
                ]
            },
            {
                "heading": "Comprehensive Benefits (Stipend, Toolkit & Concessional Credit)",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 4.1, MoMSME PM Vishwakarma Guidelines",
                "content": (
                    "Comprehensive benefit package under PM Vishwakarma: "
                    "(1) Recognition: PM Vishwakarma Certificate and ID Card; "
                    "(2) Skill Training: Basic training (5-7 days) and Advanced training (15 days or more) with a training STIPEND OF ₹500 PER DAY; "
                    "(3) Modern Toolkit Incentive: A financial grant of ₹15,000 provided via e-voucher for modern tool purchase upon basic skill completion; "
                    "(4) Concessional Enterprise Credit: Collateral-free credit up to ₹3,00,000 at a concessional interest rate of 5% "
                    "(1st Tranche: up to ₹1,00,000 with 18-month tenure; 2nd Tranche: up to ₹2,00,000 with 30-month tenure after timely repayment of Tranche 1 and digital adoption); "
                    "(5) Digital Incentives: Cashback of ₹1 per transaction up to 100 transactions per month (₹100/month)."
                ),
                "tranches": [
                    {
                        "tranche_name": "1st Tranche",
                        "amount": "₹1,00,000",
                        "tenure": "18 months",
                        "conditions": "Collateral-free credit at 5% concessional interest rate; unlocked after basic skill training completion."
                    },
                    {
                        "tranche_name": "2nd Tranche",
                        "amount": "₹2,00,000",
                        "tenure": "30 months",
                        "conditions": "Collateral-free credit at 5% concessional interest rate; unlocked after timely repayment of 1st tranche and digital transaction adoption."
                    }
                ],
                "tables": [
                    {
                        "title": "PM Vishwakarma Concessional Enterprise Credit Schedule",
                        "headers": ["Tranche Level", "Maximum Credit Amount (₹)", "Concessional Interest", "Tenure", "Prerequisite"],
                        "rows": [
                            ["1st Tranche", "₹1,00,000", "5% (8% subvention by GoI)", "18 months", "Completion of 5-7 days basic skill training"],
                            ["2nd Tranche", "₹2,00,000", "5% (8% subvention by GoI)", "30 months", "Timely repayment of 1st tranche + digital adoption"],
                            ["Total Credit Facility", "₹3,00,000", "5% concessional interest", "Up to 48 months combined", "Progressive artisan enterprise scaling"]
                        ]
                    }
                ]
            },
            {
                "heading": "Skill Training & Stipend Package",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 4.2, MoMSME PM Vishwakarma Guidelines",
                "content": (
                    "The scheme offers progressive skill development with stipend: "
                    "1. Basic Skill Training: 5 to 7 days duration (40 hours) covering tool handling and digital awareness; "
                    "2. Advanced Skill Training: 15 days or more duration (120 hours) covering modern trade techniques; "
                    "3. Training Stipend: ₹500 per day provided directly to the artisan's bank account for every day of training attended; "
                    "4. Toolkit Incentive: ₹15,000 provided as an electronic voucher (e-voucher) upon completion of basic skill training."
                )
            },
            {
                "heading": "Mandatory Documents & Verification Tiers",
                "section_type": "documents_required",
                "citation_clause": "Section 5.1, MoMSME PM Vishwakarma Guidelines",
                "content": (
                    "Mandatory documentation requirements: "
                    "(1) Aadhaar Card: Mandatory biometric identity proof; "
                    "(2) Active Mobile Number linked to Aadhaar; "
                    "(3) Bank Account Details (Passbook, IFSC); "
                    "(4) Ration Card / Family verification proof for 1-member-per-family rule; "
                    "(5) Self-declaration of engaging in one of the 18 traditional trades and having no outstanding overlapping government loans. "
                    "Verification proceeds through 3 stages: Gram Panchayat / ULB verification (Stage 1), District Implementation Committee (Stage 2), "
                    "and National Steering Committee (Stage 3)."
                )
            },
            {
                "heading": "Application Procedure via CSC & Biometric Portal",
                "section_type": "application_process",
                "citation_clause": "Section 6.1, MoMSME PM Vishwakarma Guidelines",
                "content": (
                    "Registration is conducted online through Common Service Centres (CSC) via the official PM Vishwakarma portal (https://pmvishwakarma.gov.in). "
                    "Artisans undergo Aadhaar-based biometric authentication at CSC. The registration is completely free of cost to artisans."
                )
            }
        ]
    },

    # ── 5. Ayushman Bharat PM-JAY ────────────────────────────────────────────
    "dbtbharat_central_schemes_ayushman_bharat_pradhan_mantri_jan_arogya_yojana_ab_pmjay": {
        "scheme_name": "Ayushman Bharat PM-JAY",
        "doc_title": "National Health Authority PM-JAY Operational Guidelines 2024 and Senior Citizen 70+ Expansion",
        "doc_type": "operational_guidelines",
        "source_url": "https://pmjay.gov.in",
        "effective_from": "2018-09-23",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Secondary and Tertiary Hospitalization Health Cover",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, NHA PM-JAY Operational Guidelines",
                "content": (
                    "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) provides a completely cashless and paperless "
                    "health insurance cover of ₹5,00,000 (₹5 Lakhs) per eligible family per year for secondary and tertiary care hospitalization. "
                    "The coverage extends across all public hospitals and empanelled private healthcare providers (EHCPs) nationwide. "
                    "The scheme covers up to 3 days of pre-hospitalization expenses (consultations, diagnostics) and 15 days of post-hospitalization "
                    "follow-up care, medicines, and diagnostic tests. All pre-existing conditions and diseases are covered from Day 1 of enrolment."
                ),
                "tranches": [
                    {
                        "tranche_name": "Family Floater Annual Limit",
                        "amount": "₹5,00,000",
                        "tenure": "Per financial year",
                        "conditions": "Cashless hospitalization across 1,949 notified medical and surgical health benefit packages."
                    },
                    {
                        "tranche_name": "Senior Citizens 70+ Top-Up",
                        "amount": "₹5,00,000",
                        "tenure": "Per financial year",
                        "conditions": "Dedicated distinct top-up cover for senior citizens aged 70 and above, regardless of family income."
                    }
                ],
                "tables": [
                    {
                        "title": "AB-PMJAY Core Benefit Package",
                        "headers": ["Benefit Component", "Coverage Ceiling", "Co-payment / Premium", "Service Mode"],
                        "rows": [
                            ["Hospitalization Health Cover", "₹5,00,000 per family per year", "Zero (100% cashless)", "Empanelled Public and Private Hospitals"],
                            ["Senior Citizens 70+ Top-Up", "Additional ₹5,00,000 per year", "Zero (100% cashless)", "Empanelled Healthcare Providers (EHCPs)"],
                            ["Pre-Hospitalization Expenses", "Up to 3 days diagnostics/medicines", "Included in package", "Direct Hospital Desk"],
                            ["Post-Hospitalization Care", "Up to 15 days follow-up/medicines", "Included in package", "Direct Hospital Desk"]
                        ]
                    }
                ]
            },
            {
                "heading": "Beneficiary Eligibility Criteria & Senior Citizen Enrolment",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, NHA PM-JAY Eligibility Criteria",
                "content": (
                    "AB-PMJAY covers bottom 40% vulnerable population defined by Socio-Economic Caste Census (SECC 2011) deprivation criteria "
                    "(D1 to D7 categories in rural areas, and 11 occupational categories in urban areas such as ragpickers, beggars, domestic workers, "
                    "street vendors, construction workers, and transport workers). There is no restriction on family size, age, or gender. "
                    "All senior citizens aged 70 years and above are universally eligible under the expanded PM-JAY Senior Citizen tier, "
                    "irrespective of their socio-economic status or family income."
                )
            },
            {
                "heading": "Statutory Duplicate Coverage Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, NHA Statutory Benefit Coordination",
                "content": (
                    "Beneficiaries who are already covered under other statutory government healthcare schemes such as Central Government Health "
                    "Scheme (CGHS), Employees' State Insurance Scheme (ESIS/ESIC), or Ex-Servicemen Contributory Health Scheme (ECHS) are strictly "
                    "EXCLUDED from duplicate claims for the same hospitalization episode. Senior citizens aged 70+ holding existing private health "
                    "insurance or ESIC/CGHS must elect coordination or top-up per statutory NHA guidelines."
                )
            },
            {
                "heading": "Mandatory Identification Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, NHA Documentation Standard",
                "content": (
                    "Mandatory documentation for availing PM-JAY benefits: "
                    "(1) Aadhaar Card: Mandatory biometric identity proof for beneficiary eKYC; "
                    "(2) Ration Card / Family Composition Certificate: To verify family membership; "
                    "(3) Ayushman Card (PVC or digital e-card from beneficiary.nha.gov.in portal); "
                    "(4) Age proof confirming age >= 70 years for the universal Senior Citizen cover."
                )
            }
        ]
    },

    # ── 6. PMAY-Urban (PMAY-U / CLSS) ────────────────────────────────────────
    "pmay_home_loan": {
        "scheme_name": "PMAY-Urban 2.0 (PMAY-U 2.0 - Interest Subsidy Scheme)",
        "doc_title": "MoHUA Pradhan Mantri Awas Yojana - Urban 2.0 (PMAY-U 2.0) Operational Guidelines (September 2024)",
        "doc_type": "operational_guidelines",
        "source_url": "https://pmay-urban.gov.in",
        "effective_from": "2024-09-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "PMAY-U 2.0 Interest Subsidy Scheme (ISS) Financial Parameters",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1 & 3.2, MoHUA PMAY-U 2.0 Guidelines (Sept 2024)",
                "content": (
                    "Under PMAY-U 2.0 Interest Subsidy Scheme (ISS), eligible urban families purchasing or constructing their first pucca house "
                    "receive an interest subsidy of 4.0% per annum on the first ₹8,00,000 (₹8 Lakhs) of home loan for a tenure up to 12 years. "
                    "The maximum actual interest subsidy payable is ₹1,80,000 (₹1.80 Lakhs) with a maximum Net Present Value (NPV) cap of ₹1,50,000 (₹1.50 Lakhs). "
                    "The subsidy is released directly to the beneficiary's loan account through Aadhaar-enabled DBT in five (5) equal yearly installments of up to ₹36,000 each. "
                    "Additionally, under Beneficiary-Led Construction (BLC), eligible EWS families receive a direct central grant of ₹1,50,000 (₹1.50 Lakhs) in three stages."
                ),
                "tranches": [
                    {
                        "tranche_name": "ISS Year 1 Installment",
                        "amount": "Up to ₹36,000",
                        "tenure": "Year 1 post-disbursement",
                        "conditions": "1st annual interest subsidy credit transferred via DBT upon successful Aadhaar-seeded loan validation."
                    },
                    {
                        "tranche_name": "ISS Year 2 Installment",
                        "amount": "Up to ₹36,000",
                        "tenure": "Year 2",
                        "conditions": "2nd annual interest subsidy credit transferred upon active loan repayment status."
                    },
                    {
                        "tranche_name": "ISS Year 3 Installment",
                        "amount": "Up to ₹36,000",
                        "tenure": "Year 3",
                        "conditions": "3rd annual interest subsidy credit transferred upon ongoing regular loan servicing."
                    },
                    {
                        "tranche_name": "ISS Year 4 Installment",
                        "amount": "Up to ₹36,000",
                        "tenure": "Year 4",
                        "conditions": "4th annual interest subsidy credit transferred upon ongoing regular loan servicing."
                    },
                    {
                        "tranche_name": "ISS Year 5 Installment",
                        "amount": "Up to ₹36,000",
                        "tenure": "Year 5",
                        "conditions": "5th and final annual installment completing up to ₹1,80,000 total subsidy."
                    }
                ],
                "tables": [
                    {
                        "title": "PMAY-U 2.0 ISS Eligible Brackets and Ceiling Limits",
                        "headers": ["Income Bracket", "Annual Household Income Ceiling (₹)", "Max Loan for Subsidy (₹)", "Max House Property Value (₹)", "Interest Subsidy Rate", "Max Actual Subsidy (₹)"],
                        "rows": [
                            ["Economically Weaker Section (EWS)", "Up to ₹3,00,000", "Up to ₹25,00,000", "Up to ₹35,00,000", "4.0% on first ₹8 Lakh", "Up to ₹1,80,000 (NPV ₹1,50,000)"],
                            ["Lower Income Group (LIG)", "₹3,00,001 to ₹6,00,000", "Up to ₹25,00,000", "Up to ₹35,00,000", "4.0% on first ₹8 Lakh", "Up to ₹1,80,000 (NPV ₹1,50,000)"],
                            ["Middle Income Group (MIG)", "₹6,00,001 to ₹9,00,000", "Up to ₹25,00,000", "Up to ₹35,00,000", "4.0% on first ₹8 Lakh", "Up to ₹1,80,000 (NPV ₹1,50,000)"],
                            ["BLC Direct Financial Grant (EWS)", "Up to ₹3,00,000", "Direct Grant", "N/A (Individual Construction)", "N/A", "₹1,50,000 Central Share"]
                        ]
                    }
                ]
            },
            {
                "heading": "PMAY-U 2.0 Eligibility Criteria & Loan Sanction Window",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1 & 3.3, MoHUA PMAY-U 2.0 Guidelines",
                "content": (
                    "To qualify under PMAY-U 2.0 Interest Subsidy Scheme (ISS): "
                    "(1) Eligible home loans must be sanctioned and disbursed on or after 1st September 2024 from scheduled commercial banks, "
                    "housing finance companies, or primary lending institutions; "
                    "(2) Annual household income must NOT exceed ₹9,00,000 (₹9 Lakhs); "
                    "(3) The total sanctioned home loan amount must not exceed ₹25,00,000 (₹25 Lakhs); "
                    "(4) The total property value of the house must not exceed ₹35,00,000 (₹35 Lakhs); "
                    "(5) The carpet area of the house must be up to 120 sq. meters; "
                    "(6) The beneficiary family must consist of husband, wife, and unmarried children; "
                    "(7) For EWS and LIG categories, the house title must be registered in the name of the female head of the household "
                    "or in joint ownership with the female member."
                )
            },
            {
                "heading": "PMAY-U 2.0 Statutory Pucca House & Prior Benefit Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.4, MoHUA PMAY-U 2.0 Statutory Exclusions",
                "content": (
                    "The beneficiary family must NOT own a pucca house (an all-weather dwelling unit) anywhere in India either in their own name "
                    "or in the name of any family member. Families with annual household income exceeding ₹9,00,000 (₹9 Lakhs) are strictly EXCLUDED. "
                    "Home loans with property value exceeding ₹35,00,000 or loan amount exceeding ₹25,00,000 are EXCLUDED. "
                    "Families who have previously availed central assistance under PMAY-U 1.0, PMAY-G, or any central housing subsidy scheme are EXCLUDED."
                )
            },
            {
                "heading": "PMAY-U 2.0 Application Process & Verification Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, MoHUA PMAY-U 2.0 Document Checklist",
                "content": (
                    "Applications must be registered through the official PMAY-U 2.0 Unified Web Portal (pmay-urban.gov.in) or CSC centers. "
                    "Mandatory verification documents: "
                    "(1) Aadhaar numbers with active biometric/OTP eKYC of all family members; "
                    "(2) Income Certificate / Form 16 / ITR / salary slip confirming household income <= ₹9 Lakh; "
                    "(3) Bank home loan sanction letter and disbursement certificate showing sanction on/after 1 September 2024; "
                    "(4) Property valuation report confirming property value <= ₹35 Lakh and carpet area <= 120 sq.m.; "
                    "(5) Self-declaration affidavit affirming no prior pucca house ownership in India; "
                    "(6) Title deed showing female ownership or joint ownership for EWS/LIG."
                )
            },
            {
                "heading": "Historical Credit Linked Subsidy Scheme (CLSS) Archive (Prior to PMAY-U 2.0)",
                "section_type": "historical_policy_archive",
                "citation_clause": "Historical Section, MoHUA PMAY 1.0 Guidelines (Archived)",
                "content": (
                    "HISTORICAL ARCHIVE NOTE: Under the original PMAY-U 1.0 Credit Linked Subsidy Scheme (CLSS) in effect prior to PMAY-U 2.0, "
                    "interest subsidies of up to ₹2,67,000 (at rates of 6.5% for EWS/LIG, 4.0% for MIG-I, and 3.0% for MIG-II) were provided "
                    "as an upfront lump-sum net present value credit. That original CLSS ended, and for all new home loans sanctioned on or after "
                    "1 September 2024, the applicable scheme is PMAY-U 2.0 ISS with maximum actual subsidy of ₹1,80,000 disbursed over 5 annual installments."
                )
            }
        ]
    },

    # ── 7. PMAY-Gramin (PMAY-G) ──────────────────────────────────────────────
    "dbtbharat_central_schemes_pradhan_mantri_awas_yojna_grameen": {
        "scheme_name": "PMAY-Gramin (PMAY-G)",
        "doc_title": "MoRD Pradhan Mantri Awaas Yojana - Gramin Operational Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://pmayg.nic.in",
        "effective_from": "2016-04-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Rural Housing Assistance Tranches & Labor Wages",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, MoRD PMAY-G Guidelines",
                "content": (
                    "Under Pradhan Mantri Awaas Yojana - Gramin, eligible rural houseless households receive a financial grant of "
                    "₹1,20,000 (₹1.20 Lakhs) in plain areas and ₹1,30,000 (₹1.30 Lakhs) in hilly states, difficult areas, and IAP districts. "
                    "In addition, the beneficiary is entitled to 90 to 95 person-days of unskilled manual labor under MGNREGA "
                    "(approximately ₹25,000 to ₹30,000) and ₹12,000 assistance for toilet construction under Swachh Bharat Mission - Gramin (SBM-G), "
                    "taking the total comprehensive benefit to approximately ₹1.57 Lakhs to ₹1.72 Lakhs."
                ),
                "tranches": [
                    {
                        "tranche_name": "1st Installment",
                        "amount": "₹40,000",
                        "tenure": "Sanction stage",
                        "conditions": "Transferred via DBT on issue of sanction order and geo-tagged zero-level site verification."
                    },
                    {
                        "tranche_name": "2nd Installment",
                        "amount": "₹40,000 (₹50,000 in hilly areas)",
                        "tenure": "Plinth / Lintel stage",
                        "conditions": "Transferred upon geo-tagged photo verification of plinth construction."
                    },
                    {
                        "tranche_name": "3rd Installment",
                        "amount": "₹40,000",
                        "tenure": "Roof / Completion stage",
                        "conditions": "Transferred upon completion of roof casting and complete house finishing."
                    }
                ],
                "tables": [
                    {
                        "title": "PMAY-G Financial Assistance Breakdown",
                        "headers": ["Component", "Plain Areas (₹)", "Hilly / Difficult / IAP Areas (₹)", "Source Scheme"],
                        "rows": [
                            ["Housing Construction Grant", "₹1,20,000", "₹1,30,000", "PMAY-G (60:40 or 90:10 ratio)"],
                            ["Unskilled Labour Support", "90 person-days (~₹25,000)", "95 person-days (~₹28,000)", "MGNREGA Wages via DBT"],
                            ["Individual Sanitary Latrine", "₹12,000", "₹12,000", "Swachh Bharat Mission (Gramin)"],
                            ["Total Combined Entitlement", "≈ ₹1,57,000", "≈ ₹1,70,000", "Convergent Welfare Package"]
                        ]
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria & Deprivation Ranking",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, MoRD PMAY-G Guidelines",
                "content": (
                    "Eligible households are identified from the Socio-Economic and Caste Census (SECC 2011) deprivation list "
                    "and the supplementary Awaas+ verified survey. Houseless families and families living in zero, one, or two-room houses "
                    "with kutcha walls and kutcha roof are prioritized. The selection is scrutinized and ratified by the Gram Sabha."
                )
            },
            {
                "heading": "13-Point Statutory Exclusion Criteria",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, MoRD PMAY-G Statutory Exclusions",
                "content": (
                    "Households meeting any of the following 13 criteria are strictly EXCLUDED: "
                    "(1) Owning motorized two/three/four wheeler or fishing boat; "
                    "(2) Owning mechanized three/four wheeler agricultural equipment; "
                    "(3) Having Kisan Credit Card (KCC) with credit limit >= ₹50,000; "
                    "(4) Household having any member as a government employee; "
                    "(5) Household having non-agricultural enterprises registered with government; "
                    "(6) Any member earning > ₹10,000/month; "
                    "(7) Household paying income tax; "
                    "(8) Household paying professional tax; "
                    "(9) Household owning refrigerator; "
                    "(10) Household owning landline phone; "
                    "(11) Household owning 2.5 acres of irrigated land with irrigation equipment; "
                    "(12) Household owning 5 acres or more of irrigated land for two or more crop seasons; "
                    "(13) Owning a pucca house anywhere in India."
                )
            },
            {
                "heading": "Verification & Documentation",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoRD PMAY-G Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card of beneficiary and family members; "
                    "(2) Bank Account Passbook with Aadhaar seeding and DBT enablement; "
                    "(3) MGNREGA Job Card number; "
                    "(4) Geo-tagged photography of the proposed site via AwaasApp."
                )
            }
        ]
    },

    # ── 8. Atal Pension Yojana (APY) ─────────────────────────────────────────
    "dbtbharat_central_schemes_atal_pension_yojana": {
        "scheme_name": "Atal Pension Yojana (APY)",
        "doc_title": "PFRDA Atal Pension Yojana Scheme Guidelines and Tax-Payee Amendment",
        "doc_type": "operational_guidelines",
        "source_url": "https://pfrda.org.in",
        "effective_from": "2015-05-09",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Guaranteed Monthly Pension Tiers & Corpus Return",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, PFRDA APY Guidelines",
                "content": (
                    "Atal Pension Yojana guarantees a fixed monthly pension of ₹1,000, ₹2,000, ₹3,000, ₹4,000, or ₹5,000 per month "
                    "starting from age 60 until death of the subscriber. Upon subscriber's demise, the exact same pension amount is paid "
                    "to the surviving spouse for life. Upon the demise of both subscriber and spouse, the total accumulated pension corpus "
                    "(from ₹1.7 Lakhs for ₹1,000 pension up to ₹8.5 Lakhs for ₹5,000 pension) is returned in full to the designated nominee."
                ),
                "tranches": [
                    {
                        "tranche_name": "Pension Tier 1",
                        "amount": "₹1,000 per month",
                        "tenure": "Lifetime from age 60",
                        "conditions": "Corpus return of ₹1,70,000 to nominee upon death of spouse."
                    },
                    {
                        "tranche_name": "Pension Tier 5",
                        "amount": "₹5,000 per month",
                        "tenure": "Lifetime from age 60",
                        "conditions": "Corpus return of ₹8,50,000 to nominee upon death of spouse."
                    }
                ],
                "tables": [
                    {
                        "title": "APY Monthly Contribution Schedule by Entry Age",
                        "headers": ["Entry Age", "Vesting Period (Yrs)", "₹1,000/mo Pension Contribution", "₹3,000/mo Pension Contribution", "₹5,000/mo Pension Contribution"],
                        "rows": [
                            ["18 Years", "42 Years", "₹42 / month", "₹126 / month", "₹210 / month"],
                            ["25 Years", "35 Years", "₹76 / month", "₹226 / month", "₹376 / month"],
                            ["30 Years", "30 Years", "₹116 / month", "₹347 / month", "₹577 / month"],
                            ["35 Years", "25 Years", "₹181 / month", "₹543 / month", "₹902 / month"],
                            ["40 Years", "20 Years", "₹291 / month", "₹873 / month", "₹1,454 / month"]
                        ]
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria & Age Limits",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, PFRDA APY Guidelines",
                "content": (
                    "APY is open to all Indian citizens aged between 18 and 40 years. "
                    "The subscriber must possess an active savings bank account or post office savings account with an auto-debit facility."
                )
            },
            {
                "heading": "Statutory Income Tax Payee Exclusion",
                "section_type": "exclusions",
                "citation_clause": "Notification No. 16/1/2015-PR, Department of Financial Services (w.e.f. 01 Oct 2022)",
                "content": (
                    "From 1st October 2022 onwards, any citizen who is or has been an INCOME TAX PAYEE under the Income Tax Act 1961 "
                    "is strictly EXCLUDED from enrolling in Atal Pension Yojana. If a subscriber who joined on or after 01 October 2022 "
                    "is found to have been an income tax payee on or before the application date, the APY account will be closed immediately "
                    "and the accumulated subscriber contribution will be refunded without government co-contribution."
                )
            },
            {
                "heading": "Enrolment Documentation",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, PFRDA Documentation Standard",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card: Mandatory identity proof; "
                    "(2) Savings Bank Account details with IFSC; "
                    "(3) Mobile Number linked to bank account for debit SMS alerts; "
                    "(4) Auto-debit authorization consent mandate; "
                    "(5) Spouse and Nominee details (Aadhaar and relationship)."
                )
            }
        ]
    },

    # ── 9. PM Jeevan Jyoti Bima Yojana (PMJJBY) ──────────────────────────────
    "pm_jeevan_jyoti_bima_v2": {
        "scheme_name": "PM Jeevan Jyoti Bima Yojana (PMJJBY)",
        "doc_title": "DFS Ministry of Finance PMJJBY Rules and Revised Premium Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://financialservices.gov.in",
        "effective_from": "2015-06-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Life Insurance Coverage and Annual Premium",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, DFS PMJJBY Guidelines",
                "content": (
                    "Pradhan Mantri Jeevan Jyoti Bima Yojana provides a term life insurance cover of ₹2,00,000 (₹2 Lakhs) payable to the nominee "
                    "upon the death of the insured member due to ANY cause. The annual premium is ₹436 per subscriber per year, which is auto-debited "
                    "in a single installment from the subscriber's bank or post office savings account between 25th May and 31st May annually. "
                    "The cover is renewable annually on 1st June."
                ),
                "tables": [
                    {
                        "title": "PMJJBY Premium & Benefit Summary",
                        "headers": ["Benefit Component", "Coverage Ceiling (₹)", "Annual Premium (₹)", "Risk Covered"],
                        "rows": [
                            ["Life Insurance Cover", "₹2,00,000", "₹436 / annum", "Death due to any cause (natural or accidental)"],
                            ["Administrative Breakup", "₹2,00,000", "₹395 to Insurer + ₹30 to Bank + ₹11 to Agent", "Standardized annual distribution"]
                        ]
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria & Entry Age Bracket",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, DFS PMJJBY Eligibility",
                "content": (
                    "The scheme is available to individuals aged between 18 years (completed) and 50 years. "
                    "The subscriber must maintain a savings bank account with a participating bank or post office and give consent for auto-debit. "
                    "Life cover terminates upon attaining age 55 years (subject to regular annual renewals until then)."
                )
            },
            {
                "heading": "Lien Period & Multiple Account Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, DFS PMJJBY Statutory Exclusions",
                "content": (
                    "Individuals aged below 18 or above 50 at enrolment are strictly EXCLUDED. "
                    "A 30-day statutory lien period applies from the date of enrolment: deaths occurring during the first 30 days are NOT covered, "
                    "except in cases of death caused by an accident. Only one policy is allowed per person across all bank accounts: if multiple policies "
                    "are taken, insurance cover is restricted to ₹2 Lakhs only and premium paid on redundant policies is forfeited."
                )
            },
            {
                "heading": "Claim & Enrolment Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, DFS Claim Procedure",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Bank Passbook with auto-debit consent form; "
                    "(3) Nominee identity proof; "
                    "(4) In case of claim: Original Death Certificate, Claim Form, and Nominee Bank Passbook cancelled cheque."
                )
            }
        ]
    },

    # ── 10. Pradhan Mantri Mudra Yojana (PMMY) ───────────────────────────────
    "js_mudra_all": {
        "scheme_name": "Pradhan Mantri Mudra Yojana (PMMY)",
        "doc_title": "DFS & MUDRA Ltd Operational Guidelines and Union Budget 2024 Tarun Plus Enhancement",
        "doc_type": "operational_guidelines",
        "source_url": "https://mudra.org.in",
        "effective_from": "2015-04-08",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Collateral-Free Micro Enterprise Loan Tiers",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, PMMY Operational Guidelines",
                "content": (
                    "Pradhan Mantri Mudra Yojana (PMMY) provides collateral-free institutional credit up to ₹20,00,000 (₹20 Lakhs) to non-corporate, "
                    "non-farm micro and small enterprises. Credit is structured across four progressive tiers: "
                    "1. Shishu: Loans up to ₹50,000 (for nascent micro businesses); "
                    "2. Kishore: Loans from ₹50,001 up to ₹5,00,000 (for expanding micro units); "
                    "3. Tarun: Loans from ₹5,00,001 up to ₹10,00,000 (for established small enterprises); "
                    "4. Tarun Plus: Loans from ₹10,00,001 up to ₹20,00,000 (enhanced in Union Budget 2024 for entrepreneurs who have previously repaid Tarun loans)."
                ),
                "tranches": [
                    {
                        "tranche_name": "Shishu Tier",
                        "amount": "Up to ₹50,000",
                        "tenure": "Up to 5 years",
                        "conditions": "Zero collateral, zero processing fee for start-ups and micro traders."
                    },
                    {
                        "tranche_name": "Kishore Tier",
                        "amount": "₹50,001 to ₹5,00,000",
                        "tenure": "Up to 5 years",
                        "conditions": "Working capital or term loan for machinery purchase and expansion."
                    },
                    {
                        "tranche_name": "Tarun Tier",
                        "amount": "₹5,00,001 to ₹10,00,000",
                        "tenure": "Up to 5 years",
                        "conditions": "Collateral-free credit covered under CGFMU guarantee pool."
                    },
                    {
                        "tranche_name": "Tarun Plus Tier",
                        "amount": "₹10,00,001 to ₹20,00,000",
                        "tenure": "Up to 7 years",
                        "conditions": "Available to entrepreneurs who have successfully availed and repaid Tarun loans."
                    }
                ],
                "tables": [
                    {
                        "title": "Mudra Loan Categories & Limits",
                        "headers": ["Loan Category", "Loan Limit (₹)", "Target Beneficiary Stage", "Collateral Requirement"],
                        "rows": [
                            ["Shishu", "Up to ₹50,000", "Nascent & First-Time Micro Borrowers", "Zero (No Collateral)"],
                            ["Kishore", "₹50,001 to ₹5,00,000", "Mid-Stage Micro Business Units", "Zero (No Collateral)"],
                            ["Tarun", "₹5,00,001 to ₹10,00,000", "Established Scaling Enterprises", "Zero (No Collateral)"],
                            ["Tarun Plus", "₹10,00,001 to ₹20,00,000", "Proven Past Borrowers with Clean Track Record", "Zero (No Collateral)"]
                        ]
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria & Eligible Activities",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, PMMY Eligibility Framework",
                "content": (
                    "Any Indian citizen who has a viable business proposal for a non-farm income-generating activity such as manufacturing, "
                    "processing, trading, or service sector, or activities allied to agriculture (such as dairy, poultry, bee-keeping, fisheries, "
                    "grading, sorting, agri-clinic, and food processing) is eligible."
                )
            },
            {
                "heading": "Statutory Bank Defaulter & Corporate Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, PMMY Exclusions",
                "content": (
                    "The applicant must NOT be a DEFAULTER to any bank, financial institution, or NBFC. "
                    "Corporate entities, large industrial houses, and non-income-generating personal consumption loans are strictly EXCLUDED. "
                    "Direct agricultural crop loans (covered under KCC) are excluded from Mudra financing."
                )
            },
            {
                "heading": "Application Process & Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, PMMY Application Standard",
                "content": (
                    "Required documentation: "
                    "(1) Identity Proof (Aadhaar / Voter ID / PAN Card); "
                    "(2) Residence Proof and Business Address Proof; "
                    "(3) Udyam Registration Certificate (for micro enterprise); "
                    "(4) Quotation for machinery / items to be purchased; "
                    "(5) Bank Statement for past 6 months. "
                    "Applications can be submitted online via JanSamarth portal (jansamarth.in) or directly at any public/private bank."
                )
            }
        ]
    },

    # ── 11. PM Shram Yogi Maan-dhan (PM-SYM) ─────────────────────────────────
    "dbtbharat_central_schemes_pradhan_mantri_shram_yogi_maan_dhan_pm_sym": {
        "scheme_name": "PM Shram Yogi Maan-dhan (PM-SYM)",
        "doc_title": "Ministry of Labour & Employment PM-SYM Operational Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://maandhan.in",
        "effective_from": "2019-02-15",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Assured Old-Age Pension for Unorganized Workers",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, MoLE PM-SYM Guidelines",
                "content": (
                    "PM-SYM is a voluntary and contributory pension scheme that provides an assured minimum pension of ₹3,000 per month "
                    "to unorganized workers on attaining the age of 60 years. The scheme operates on a 50:50 matching basis: the subscriber deposits "
                    "a monthly contribution (between ₹55 and ₹200 depending on entry age), and the Central Government deposits an equal matching amount "
                    "into the pension fund administered by LIC. If the subscriber dies while receiving pension, the spouse is entitled to receive "
                    "50% of the pension (₹1,500 per month) as family pension."
                ),
                "tables": [
                    {
                        "title": "PM-SYM Monthly Contribution Chart by Entry Age",
                        "headers": ["Entry Age", "Superannuation Age", "Subscriber Share (₹)", "Central Govt Share (₹)", "Total Monthly Pension Deposit (₹)"],
                        "rows": [
                            ["18 Years", "60 Years", "₹55", "₹55", "₹110"],
                            ["25 Years", "60 Years", "₹80", "₹80", "₹160"],
                            ["30 Years", "60 Years", "₹105", "₹105", "₹210"],
                            ["35 Years", "60 Years", "₹150", "₹150", "₹300"],
                            ["40 Years", "60 Years", "₹200", "₹200", "₹400"]
                        ]
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria & Unorganized Worker Definition",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, MoLE PM-SYM Eligibility",
                "content": (
                    "Eligible applicants: Unorganized workers (home-based workers, street vendors, mid-day meal workers, head loaders, "
                    "brick kiln workers, cobblers, ragpickers, domestic workers, rickshaw pullers, landless agricultural laborers, construction workers, "
                    "beedi workers, handloom and leather workers) aged between 18 and 40 years, whose monthly income does not exceed ₹15,000."
                )
            },
            {
                "heading": "Statutory EPFO, ESIC & Income Tax Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, MoLE PM-SYM Exclusions",
                "content": (
                    "The following categories are strictly EXCLUDED: "
                    "(1) Any worker covered under statutory social security schemes including Employees' Provident Fund Organization (EPFO), "
                    "Employees' State Insurance Corporation (ESIC), or National Pension System (NPS); "
                    "(2) Any individual who is an Income Tax Payee; "
                    "(3) Individuals aged below 18 or above 40 years at the time of application."
                )
            },
            {
                "heading": "Enrolment & Documentation",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoLE PM-SYM Enrolment",
                "content": (
                    "Mandatory documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Savings Bank Account / Jan Dhan Account with IFSC; "
                    "(3) Mobile Number; "
                    "(4) Auto-debit authorization form signed by subscriber."
                )
            }
        ]
    },

    # ── 12. Indira Gandhi National Widow Pension (IGNWPS) ────────────────────
    "dbtbharat_central_schemes_indira_gandhi_national_widow_pension_scheme_ignwps": {
        "scheme_name": "Indira Gandhi National Widow Pension Scheme (IGNWPS)",
        "doc_title": "MoRD National Social Assistance Programme (NSAP) Operational Guidelines for Widow Pension",
        "doc_type": "operational_guidelines",
        "source_url": "https://nsap.nic.in",
        "effective_from": "2009-02-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Monthly Pension Assistance for Widows",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 3.1, MoRD NSAP Guidelines",
                "content": (
                    "Under IGNWPS, eligible BPL widows receive non-contributory monthly financial assistance: "
                    "Central Government contributes ₹300 per month for widows aged 40 to 79 years, and ₹500 per month for widows aged 80 years and above. "
                    "States provide supplementary matching contributions ranging from ₹700 to ₹2,500 per month, bringing the total monthly pension "
                    "to between ₹1,000 and ₹3,000 per month credited directly via DBT."
                )
            },
            {
                "heading": "Eligibility Criteria & Age Limits",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.2, MoRD NSAP Guidelines",
                "content": (
                    "The applicant must be a widow aged between 40 and 79 years (and 80+ for higher tier) living below the poverty line (BPL) "
                    "as per criteria specified by Government of India."
                )
            },
            {
                "heading": "Statutory Remarriage & APL Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.4, MoRD NSAP Exclusions",
                "content": (
                    "The widow is strictly EXCLUDED and pension terminates immediately upon REMARRIAGE. "
                    "Widows belonging to non-BPL (Above Poverty Line) households are excluded. "
                    "Widows having gainful regular employment in government/statutory bodies are excluded."
                )
            },
            {
                "heading": "Mandatory Verification Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoRD NSAP Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Death Certificate of Husband; "
                    "(3) BPL Ration Card / Socio-Economic Survey proof; "
                    "(4) Bank Account Passbook with IFSC; "
                    "(5) Non-remarriage self-declaration certificate."
                )
            }
        ]
    },

    # ── 13. Indira Gandhi National Old Age Pension (IGNOAPS) ──────────────────
    "dbtbharat_central_schemes_indira_gandhi_national_old_age_pension_scheme_ignoaps": {
        "scheme_name": "Indira Gandhi National Old Age Pension Scheme (IGNOAPS)",
        "doc_title": "MoRD National Social Assistance Programme (NSAP) IGNOAPS Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://nsap.nic.in",
        "effective_from": "2007-11-19",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Monthly Old Age Pension Support",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, MoRD NSAP Guidelines",
                "content": (
                    "Under IGNOAPS, destitute elderly citizens living below the poverty line receive direct monthly pension: "
                    "Central assistance of ₹200 per month for persons aged 60 to 79 years, and ₹500 per month for senior citizens aged 80 years and above. "
                    "States add top-ups of ₹800 to ₹2,500/month, providing a total monthly benefit of ₹1,000 to ₹3,000 per month via DBT."
                )
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 2.2, MoRD NSAP Guidelines",
                "content": (
                    "The applicant must be aged 60 years or above and belong to a household living Below the Poverty Line (BPL) "
                    "according to the criteria prescribed by the Government of India."
                )
            },
            {
                "heading": "Statutory BPL Status Exclusion",
                "section_type": "exclusions",
                "citation_clause": "Section 2.4, MoRD NSAP Exclusions",
                "content": (
                    "Households that are not certified as Below Poverty Line (BPL_STATUS) or whose members have formal pensions/gainful employment "
                    "are strictly EXCLUDED. Persons below 60 years of age are excluded."
                )
            },
            {
                "heading": "Verification Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoRD Documentation",
                "content": (
                    "Required documents: "
                    "(1) Aadhaar Card; "
                    "(2) Proof of Age (Voter ID / Birth certificate / Medical Board certificate); "
                    "(3) BPL Card / BPL Survey enumeration number; "
                    "(4) Bank Account Passbook seeded with Aadhaar."
                )
            }
        ]
    },

    # ── 14. Indira Gandhi National Disability Pension (IGNDPS) ────────────────
    "dbtbharat_central_schemes_indira_gandhi_national_disability_pension_scheme_igndps": {
        "scheme_name": "Indira Gandhi National Disability Pension Scheme (IGNDPS)",
        "doc_title": "MoRD National Social Assistance Programme (NSAP) IGNDPS Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://nsap.nic.in",
        "effective_from": "2009-02-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Monthly Disability Pension Assistance",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 4.1, MoRD NSAP Guidelines",
                "content": (
                    "Under IGNDPS, persons with severe or multiple disabilities receive monthly pension: "
                    "Central assistance of ₹300 per month for beneficiaries aged 18 to 79 years, and ₹500 per month for persons aged 80 years and above. "
                    "State matching shares increase the total pension to ₹1,000 to ₹3,500 per month credited directly through DBT."
                )
            },
            {
                "heading": "Eligibility Criteria & Severe Disability Definition",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 4.2, MoRD NSAP Guidelines",
                "content": (
                    "The applicant must be aged between 18 and 79 years (80+ receives higher tier), belong to a Below Poverty Line (BPL) household, "
                    "and have severe or multiple disabilities with a benchmark disability degree of 80% or higher as certified by a competent medical board."
                )
            },
            {
                "heading": "Statutory Disability Threshold Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 4.4, MoRD NSAP Exclusions",
                "content": (
                    "Persons with disability percentage below 80% (DISABILITY_THRESHOLD) are strictly EXCLUDED from IGNDPS. "
                    "Non-BPL households and individuals below 18 years of age are excluded."
                )
            },
            {
                "heading": "Required Documentation",
                "section_type": "documents_required",
                "citation_clause": "Section 5.1, MoRD Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Disability Certificate / UDID Card showing >= 80% severe or multiple disability; "
                    "(3) BPL Card / SECC census record; "
                    "(4) Bank Account Passbook with Aadhaar linkage."
                )
            }
        ]
    },

    # ── 15. Pradhan Mantri Vaya Vandana Yojana (PMVVY) ────────────────────────
    "dbtbharat_central_schemes_pradhan_mantri_vaya_vandana_yojana": {
        "scheme_name": "Pradhan Mantri Vaya Vandana Yojana (PMVVY)",
        "doc_title": "DFS Ministry of Finance & LIC PMVVY Operational Guidelines and Withdrawal Notice",
        "doc_type": "operational_guidelines",
        "source_url": "https://financialservices.gov.in",
        "effective_from": "2017-05-04",
        "effective_to": "2023-03-31",
        "currentness": "withdrawn",
        "sections": [
            {
                "heading": "Official Scheme Withdrawal Notice (Closed to New Subscriptions on 31 March 2023)",
                "section_type": "historical_closure_notice",
                "citation_clause": "LIC Official Public Notice & MoF DFS Guidelines",
                "content": (
                    "OFFICIAL WITHDRAWAL NOTICE: Pradhan Mantri Vaya Vandana Yojana (PMVVY) was formally WITHDRAWN from sale "
                    "and permanently closed to new subscribers effective 31st March 2023 per Life Insurance Corporation of India (LIC) "
                    "and Ministry of Finance directives. Existing policies purchased on or before 31 March 2023 continue to receive their "
                    "contracted guaranteed monthly pension payouts for the remainder of their 10-year policy term, but NO new applications, "
                    "registrations, or policy purchases can be made under this scheme. It is preserved strictly as a historical reference."
                )
            },
            {
                "heading": "Historical 7.4% Senior Citizen Pension Payout Parameters",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, DFS PMVVY Guidelines",
                "content": (
                    "Under the historical PMVVY scheme (active 2017 to 31 March 2023, administered through LIC), senior citizens received an assured return "
                    "of 7.40% per annum payable monthly for 10 years. The minimum pension was ₹1,000 per month (purchase price ₹1,62,162) and maximum "
                    "pension was ₹9,250 per month (purchase price ₹15,00,000). On survival of the subscriber at the end of the 10-year policy term, "
                    "purchase price is refunded in full. Loan facility up to 75% of purchase price is available after 3 policy years."
                )
            },
            {
                "heading": "Historical Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, DFS PMVVY Eligibility",
                "content": (
                    "Historical eligibility: The applicant had to be a senior citizen aged 60 years or above (completed) at the time of policy purchase."
                )
            },
            {
                "heading": "Historical ₹15 Lakh Investment Cap Exclusion",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, DFS PMVVY Exclusions",
                "content": (
                    "Total investment across all PMVVY policies purchased by a single senior citizen could not exceed the statutory ceiling "
                    "of ₹15,00,000 (₹15 Lakhs). Persons aged below 60 years were excluded."
                )
            },
            {
                "heading": "Historical Enrolment Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, DFS PMVVY Documentation",
                "content": (
                    "Historical documents required: "
                    "(1) Aadhaar Card; "
                    "(2) Age Proof (Birth Certificate / Voter ID / Passport / School Certificate); "
                    "(3) Bank Account Details / Cancelled Cheque for NEFT pension credits; "
                    "(4) Cheque / Demand Draft for Purchase Price."
                )
            }
        ]
    },

    # ── 16. Employees Pension Scheme 1995 (EPS-95) ────────────────────────────
    "dbtbharat_central_schemes_employees_pension_scheme_for_epf_members": {
        "scheme_name": "Employees Pension Scheme 1995 (EPS-95)",
        "doc_title": "EPFO Employees Pension Scheme 1995 Rules and Minimum Pension Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://epfindia.gov.in",
        "effective_from": "1995-11-16",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Monthly Superannuation Pension & Pension Formula",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Paragraph 12, EPFO EPS-95 Rules",
                "content": (
                    "Under EPS-95, members receive guaranteed monthly superannuation pension on retiring at age 58 years. "
                    "Minimum guaranteed pension is ₹1,000 per month. Monthly member pension is calculated as: "
                    "(Pensionable Salary x Pensionable Service) / 70. Early pension can be drawn from age 50 with 4% reduction per year. "
                    "Spouse receives 50% of member pension upon death of member, plus 25% each for up to two children until age 25."
                )
            },
            {
                "heading": "Eligibility Criteria & Contributory Service",
                "section_type": "eligibility_criteria",
                "citation_clause": "Paragraph 9, EPFO EPS-95 Rules",
                "content": (
                    "The member must be an active contributor to the Employees' Provident Fund (EPF), must have completed a minimum of "
                    "10 years of eligible contributory pension service (EPF_SERVICE), and must have attained the age of 58 years (or 50 years for early pension)."
                )
            },
            {
                "heading": "Statutory Minimum Service & Non-EPF Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Paragraph 14, EPFO EPS-95 Exclusions",
                "content": (
                    "Members with less than 10 years of contributory service are strictly EXCLUDED from regular monthly pension "
                    "(they are eligible only for withdrawal lump sum benefit under Scheme Certificate / Form 10C). Non-EPF establishments are excluded."
                )
            },
            {
                "heading": "Claim Procedure & Documents",
                "section_type": "documents_required",
                "citation_clause": "Paragraph 17, EPFO Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Universal Account Number (UAN) with Aadhaar and bank details seeded; "
                    "(2) Form 10D (Claim for Monthly Pension); "
                    "(3) Cancelled bank cheque showing member's name and IFSC; "
                    "(4) Joint photograph with spouse for family pension."
                )
            }
        ]
    },

    # ── 17. National Means-cum-Merit Scholarship (NMMSS) ─────────────────────
    "dbtbharat_central_schemes_national_means_cum_merit_scholarship_scheme": {
        "scheme_name": "National Means-cum-Merit Scholarship Scheme (NMMSS)",
        "doc_title": "DoSEL Ministry of Education NMMSS Scheme Guidelines and Portal Instructions",
        "doc_type": "operational_guidelines",
        "source_url": "https://scholarships.gov.in",
        "effective_from": "2008-05-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Annual Secondary Education Scholarship Tranches",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, DoSEL NMMSS Guidelines",
                "content": (
                    "Under NMMSS, 1,00,000 meritorious students from economically weaker sections receive a scholarship of ₹12,000 per annum "
                    "(₹1,000 per month) to arrest dropout at Class VIII and encourage continuation of study through secondary stage (Classes IX to XII). "
                    "The scholarship is disbursed annually in a single lump sum via DBT into the student's bank account through the National Scholarship Portal (NSP)."
                ),
                "tranches": [
                    {
                        "tranche_name": "Class IX Grant",
                        "amount": "₹12,000",
                        "tenure": "1 academic year",
                        "conditions": "Cleared State NMMSS selection test in Class VIII and secured >= 55% marks in Class VII."
                    },
                    {
                        "tranche_name": "Class X to XII Renewal",
                        "amount": "₹12,000 per year",
                        "tenure": "1 academic year per class",
                        "conditions": "Promotion to next class with minimum 55% marks (50% for SC/ST) on first attempt."
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, DoSEL NMMSS Guidelines",
                "content": (
                    "The student must be enrolled as a regular student in Class IX in a Government, Local Body, or Government-aided school. "
                    "Parental annual income from all sources must not exceed ₹3,50,000 (₹3.5 Lakhs). "
                    "The candidate must have secured minimum 55% marks (50% for SC/ST) in Class VII and qualified the state NMMSS exam."
                )
            },
            {
                "heading": "Statutory Residential School & Income Ceiling Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, DoSEL NMMSS Exclusions",
                "content": (
                    "Students of Kendriya Vidyalayas (KVs), Jawahar Navodaya Vidyalayas (JNVs), Sainik Schools, and residential schools "
                    "run by State Governments where boarding, lodging, and education are provided free are strictly EXCLUDED (RESIDENTIAL_SCHOOL). "
                    "Students whose parental annual income exceeds ₹3.5 Lakhs (INCOME_CEILING) are strictly excluded. "
                    "Students studying in private un-aided schools are excluded."
                )
            },
            {
                "heading": "Application & Required Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, DoSEL Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card of student; "
                    "(2) Class VII and VIII Marksheets; "
                    "(3) Income Certificate issued by competent revenue authority (<= ₹3.5 Lakhs); "
                    "(4) Bank Account Passbook in student's name; "
                    "(5) Bonafide Student Certificate from school principal."
                )
            }
        ]
    },

    # ── 18. Begum Hazrat Mahal National Scholarship ──────────────────────────
    "dbtbharat_central_schemes_begum_hazrat_mahal_national_scholarship_scheme": {
        "scheme_name": "Begum Hazrat Mahal National Scholarship",
        "doc_title": "MoMA Begum Hazrat Mahal Scholarship Guidelines and Subsumption Notice",
        "doc_type": "operational_guidelines",
        "source_url": "https://scholarships.gov.in",
        "effective_from": "2003-05-03",
        "effective_to": "2022-03-31",
        "currentness": "subsumed",
        "sections": [
            {
                "heading": "Official Scheme Subsumption Notice (Subsumed into Pre-Matric and Post-Matric Minority Schemes)",
                "section_type": "historical_subsumption_notice",
                "citation_clause": "Ministry of Minority Affairs Guidelines & Notification 2022-23",
                "content": (
                    "OFFICIAL SUBSUMPTION NOTICE: Begum Hazrat Mahal National Scholarship (BHMNS) was formally SUBSUMED into the "
                    "Pre-Matric Scholarship Scheme for Minorities (for classes IX and X) and the Post-Matric Scholarship Scheme for Minorities "
                    "(for classes XI and XII) starting from academic year 2022-23 onwards per Ministry of Minority Affairs directives. "
                    "BHMNS is NO LONGER operated as an independent standalone open scholarship. Eligible minority girl students now apply directly "
                    "under the unified Pre-Matric or Post-Matric Scholarship schemes for Minorities through the National Scholarship Portal (NSP)."
                )
            },
            {
                "heading": "Historical Minority Girl Student Financial Assistance",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, MoMA BHMNS Guidelines",
                "content": (
                    "Historical scholarship rates (prior to 2022-23 subsumption): Meritorious minority girl students received ₹5,000 per year for Class IX and X, "
                    "and ₹6,000 per year for Class XI and XII via DBT to cover school fees, textbook purchase, stationery, and boarding charges."
                )
            },
            {
                "heading": "Historical Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, MoMA BHMNS Guidelines",
                "content": (
                    "Historical eligibility: Girl students belonging to notified national minorities (Muslims, Christians, Sikhs, Buddhists, Jains, and Parsis) "
                    "studying in classes IX to XII with at least 50% marks in previous annual exams and family income not exceeding ₹2,00,000."
                )
            },
            {
                "heading": "Historical Duplicate Scholarship & Income Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, MoMA BHMNS Exclusions",
                "content": (
                    "Students receiving any other scholarship under Central or State Government DBT schemes for the same course were strictly EXCLUDED. "
                    "Male students were excluded. Families with annual income > ₹2 Lakhs were excluded."
                )
            },
            {
                "heading": "Historical Verification Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, MoMA Documentation",
                "content": (
                    "Historical required documents: "
                    "(1) Aadhaar Card; "
                    "(2) Self-declaration of minority community membership; "
                    "(3) Marksheet of previous class showing >= 50% marks; "
                    "(4) Competent Authority Income Certificate (<= ₹2 Lakhs); "
                    "(5) School Verification Form signed by Principal."
                )
            }
        ]
    },

    # ── 19. PG Indira Gandhi Scholarship for Single Girl Child ───────────────
    "dbtbharat_central_schemes_p_g_indira_gandhi_scholarship_for_single_girl_child": {
        "scheme_name": "PG Indira Gandhi Scholarship for Single Girl Child",
        "doc_title": "UGC Post-Graduate Indira Gandhi Scholarship Scheme Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://scholarships.gov.in",
        "effective_from": "2005-09-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Postgraduate Education Scholarship Stipend",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, UGC Guidelines",
                "content": (
                    "Under this UGC scheme, eligible single girl children receive a scholarship of ₹36,200 per annum (₹3,100 per month) for 2 years "
                    "(10 months in an academic year, full normal duration of a master's degree). No tuition fee waiver is required; the amount is "
                    "credited directly through DBT to assist with living and study expenses."
                )
            },
            {
                "heading": "Eligibility Criteria & Single Girl Definition",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, UGC Guidelines",
                "content": (
                    "Any single girl child who is the only child of her parents (twin/fraternal daughters are also eligible) and who has taken admission "
                    "to regular, full-time 1st year Master's Degree program in any designated university or postgraduate college is eligible. "
                    "The upper age limit is 30 years at the time of admission to the PG course."
                )
            },
            {
                "heading": "Distance Education & Non-Single Child Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, UGC Exclusions",
                "content": (
                    "Students pursuing postgraduate courses through DISTANCE_EDUCATION, correspondence, or part-time mode are strictly EXCLUDED. "
                    "Female students having brothers or sisters (non-single girl child) are excluded. Students aged over 30 years at admission are excluded."
                )
            },
            {
                "heading": "Affidavit & Documents Required",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, UGC Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Notarized Affidavit on ₹50/₹100 stamp paper attested by SDM or First Class Judicial Magistrate certifying Single Girl Child status; "
                    "(3) PG Admission Proof and Fee Receipt; "
                    "(4) Undergraduate final marksheet; "
                    "(5) Bank Passbook with IFSC."
                )
            }
        ]
    },

    # ── 20. Pragati Scholarship for Girls (AICTE) ────────────────────────────
    "dbtbharat_central_schemes_pragati_scholarship_for_girls_in_degree_colleges": {
        "scheme_name": "Pragati Scholarship for Girls in Degree Colleges",
        "doc_title": "AICTE Pragati Scholarship Scheme Guidelines for Technical Education",
        "doc_type": "operational_guidelines",
        "source_url": "https://scholarships.gov.in",
        "effective_from": "2014-09-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Technical Degree Education Scholarship Package",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, AICTE Pragati Guidelines",
                "content": (
                    "AICTE awards ₹50,000 per annum for every year of technical degree study (up to 4 years for 1st year admitted students, "
                    "3 years for lateral entry) towards payment of college fees, purchase of computers, software, books, and equipment. "
                    "The amount is disbursed as a single lump sum via DBT annually."
                )
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, AICTE Pragati Guidelines",
                "content": (
                    "Girl students admitted to 1st year of Degree level course OR 2nd year of Degree level course through lateral entry "
                    "in any AICTE-approved institution. Family annual income from all sources must not exceed ₹8,00,000 (₹8 Lakhs)."
                )
            },
            {
                "heading": "Family Limit & Income Ceiling Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, AICTE Pragati Exclusions",
                "content": (
                    "The scheme is restricted to a maximum of TWO girl children per family (FAMILY_LIMIT). More than 2 girls from the same family "
                    "are excluded. Families with annual income exceeding ₹8 Lakhs (INCOME_CEILING) are strictly EXCLUDED. "
                    "Students in non-AICTE approved colleges or general non-technical courses are excluded."
                )
            },
            {
                "heading": "Verification Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, AICTE Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) AICTE Centralized Admission Allotment Letter; "
                    "(3) Class 10 and 12 marksheets; "
                    "(4) Family Income Certificate issued by Tahsildar/SDM (<= ₹8 Lakhs); "
                    "(5) Declaration from parents that family has not exceeded 2-girl-child limit."
                )
            }
        ]
    },

    # ── 21. Saksham Scholarship for Differently Abled Students ────────────────
    "dbtbharat_central_schemes_saksham_scholarship_for_differently_abled_students_of_degree": {
        "scheme_name": "Saksham Scholarship for Differently Abled Students",
        "doc_title": "AICTE Saksham Scholarship Scheme Guidelines for Technical Education",
        "doc_type": "operational_guidelines",
        "source_url": "https://scholarships.gov.in",
        "effective_from": "2014-09-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Technical Degree Scholarship for Students with Disabilities",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, AICTE Saksham Guidelines",
                "content": (
                    "Saksham scheme provides ₹50,000 per annum for each year of study in an AICTE-approved technical degree course "
                    "to differently abled students towards tuition fees, books, software, and specialized assistive devices. Disbursed via DBT annually."
                )
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, AICTE Saksham Guidelines",
                "content": (
                    "Differently abled students having not less than 40% benchmark disability, admitted to 1st year Degree level course "
                    "(or 2nd year through lateral entry) in any AICTE approved institution. Annual family income <= ₹8,00,000 (₹8 Lakhs)."
                )
            },
            {
                "heading": "Disability Threshold & Income Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, AICTE Saksham Exclusions",
                "content": (
                    "Students with disability degree below 40% (DISABILITY_THRESHOLD) are strictly EXCLUDED. "
                    "Students with family annual income > ₹8 Lakhs (INCOME_CEILING) are excluded. General non-technical courses are excluded."
                )
            },
            {
                "heading": "Mandatory Verification Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, AICTE Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Unique Disability ID (UDID) / Disability Certificate certifying >= 40% disability; "
                    "(3) AICTE Allotment Letter & College Fee Receipt; "
                    "(4) Family Income Certificate (<= ₹8 Lakhs); "
                    "(5) Bank Passbook with IFSC."
                )
            }
        ]
    },

    # ── 22. Ishan Uday Special Scholarship for NER ───────────────────────────
    "dbtbharat_central_schemes_ishan_uday_special_scholarship_scheme_for_north_eastern_regi": {
        "scheme_name": "Ishan Uday Special Scholarship Scheme for NER",
        "doc_title": "UGC Guidelines for Ishan Uday Special Scholarship Scheme for North Eastern Region",
        "doc_type": "operational_guidelines",
        "source_url": "https://scholarships.gov.in",
        "effective_from": "2014-08-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Higher Education Monthly Stipend for North Eastern Students",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, UGC Ishan Uday Guidelines",
                "content": (
                    "Ishan Uday awards 10,000 fresh scholarships annually to students from the North Eastern Region: "
                    "₹5,400 per month for general degree courses (Humanities, Social Sciences, Commerce, Science) and "
                    "₹7,800 per month for technical, professional, medical, and paramedical degree courses, for the full duration of the degree."
                ),
                "tranches": [
                    {
                        "tranche_name": "General Degree Rate",
                        "amount": "₹5,400 per month",
                        "tenure": "Full 3-year course duration",
                        "conditions": "Regular undergraduate admission in recognized university."
                    },
                    {
                        "tranche_name": "Technical / Medical Rate",
                        "amount": "₹7,800 per month",
                        "tenure": "Full 4 or 5-year course duration",
                        "conditions": "Regular professional degree enrolment."
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria & NER Domicile Mandate",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, UGC Ishan Uday Guidelines",
                "content": (
                    "The student must have permanent domicile in any of the 8 North Eastern States (Assam, Arunachal Pradesh, Manipur, "
                    "Meghalaya, Mizoram, Nagaland, Sikkim, Tripura). The candidate must have passed Class XII or equivalent and secured "
                    "admission to 1st year of general or professional degree in recognized college/university. Family income <= ₹4,50,000."
                )
            },
            {
                "heading": "Domicile & Income Ceiling Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, UGC Ishan Uday Exclusions",
                "content": (
                    "Students who do not possess permanent resident status / DOMICILE in the North Eastern Region are strictly EXCLUDED. "
                    "Students with parental annual income exceeding ₹4.5 Lakhs (INCOME_CEILING) are excluded. "
                    "Students pursuing courses through distance education or open university are excluded."
                )
            },
            {
                "heading": "Required Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, UGC Documentation",
                "content": (
                    "Required documents: "
                    "(1) Aadhaar Card; "
                    "(2) Permanent Resident Certificate (PRC) / Domicile Certificate of NER state; "
                    "(3) Class XII Marksheet; "
                    "(4) Parental Income Certificate issued by authorized revenue official (<= ₹4.5 Lakhs); "
                    "(5) Admission verification certificate from Head of Institution."
                )
            }
        ]
    },

    # ── 23. Pre-Matric Scholarship for Minorities ────────────────────────────
    "dbtbharat_central_schemes_pre_matric_scholarship_for_minorities": {
        "scheme_name": "Pre-Matric Scholarship for Minorities",
        "doc_title": "Ministry of Minority Affairs Pre-Matric Scholarship Scheme Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://scholarships.gov.in",
        "effective_from": "2008-01-30",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Secondary School Scholarship Assistance",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, MoMA Pre-Matric Guidelines",
                "content": (
                    "Under the Pre-Matric Scholarship Scheme for Minorities, eligible students in Classes IX and X receive up to ₹4,000 per annum: "
                    "admission fee up to ₹500/year, tuition fee up to ₹350/month, and maintenance allowance up to ₹600/month for hostellers "
                    "(₹100/month for day scholars), credited via DBT directly into the student's bank account."
                )
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, MoMA Pre-Matric Guidelines",
                "content": (
                    "Students belonging to notified minority communities (Muslims, Christians, Sikhs, Buddhists, Jains, Parsis) studying in "
                    "Class IX or Class X in a government or recognized private school, who secured not less than 50% marks in previous final exam. "
                    "Annual family income from all sources must not exceed ₹1,00,000 (₹1 Lakh)."
                )
            },
            {
                "heading": "Primary Class Discontinuation & Income Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, MoMA Pre-Matric Exclusions",
                "content": (
                    "Students in Classes I to VIII are EXCLUDED (discontinued in 2022 to align with free education under RTE Act 2009). "
                    "Families with annual income exceeding ₹1 Lakh (INCOME_CEILING) are strictly EXCLUDED. Non-minority students excluded."
                )
            },
            {
                "heading": "Required Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoMA Documentation",
                "content": (
                    "Required documents: "
                    "(1) Aadhaar Card; "
                    "(2) Self-declaration of minority community membership; "
                    "(3) Previous class marksheet showing >= 50% marks; "
                    "(4) Competent Authority Income Certificate (<= ₹1 Lakh); "
                    "(5) Bank Passbook with IFSC."
                )
            }
        ]
    },

    # ── 24. Post-Matric Scholarship for Minorities ───────────────────────────
    "dbtbharat_central_schemes_post_matric_scholarship_for_minorities": {
        "scheme_name": "Post-Matric Scholarship for Minorities",
        "doc_title": "Ministry of Minority Affairs Post-Matric Scholarship Scheme Guidelines",
        "doc_type": "operational_guidelines",
        "source_url": "https://scholarships.gov.in",
        "effective_from": "2007-11-29",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Higher Education Fee & Maintenance Allowances",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, MoMA Post-Matric Guidelines",
                "content": (
                    "Post-Matric Scholarship provides financial support for higher education from Class XI through PhD: "
                    "Admission and tuition fee up to ₹10,000 per annum for technical and vocational courses (Classes XI-XII), "
                    "and maintenance allowance up to ₹1,200 per month for hostellers (₹550/month for day scholars) pursuing degree, PG, or research degrees."
                )
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, MoMA Post-Matric Guidelines",
                "content": (
                    "Students from notified minority communities pursuing higher studies in Class XI, XII, ITI, Polytechnic, Diploma, Undergraduate, "
                    "Postgraduate, or Doctoral levels in recognized government or private institutions. Minimum 50% marks in previous exam; "
                    "annual family income <= ₹2,00,000 (₹2 Lakhs)."
                )
            },
            {
                "heading": "Minority Community & Income Ceiling Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, MoMA Post-Matric Exclusions",
                "content": (
                    "Applicants not belonging to notified MINORITY_COMMUNITY are strictly EXCLUDED. "
                    "Family income exceeding ₹2 Lakhs (INCOME_CEILING) is strictly excluded. "
                    "Students receiving another central/state DBT scholarship for the same academic year are excluded."
                )
            },
            {
                "heading": "Required Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoMA Documentation",
                "content": (
                    "Required documents: "
                    "(1) Aadhaar Card; "
                    "(2) Minority community self-declaration certificate; "
                    "(3) Previous degree/class marksheet showing >= 50% marks; "
                    "(4) Income Certificate issued by designated state authority (<= ₹2 Lakhs); "
                    "(5) Fee receipt and Bonafide student certificate."
                )
            }
        ]
    },

    # ── 25. Swachh Bharat Mission Urban (IHHL) ───────────────────────────────
    "dbtbharat_central_schemes_swachh_bharat_mission_urban": {
        "scheme_name": "Swachh Bharat Mission Urban (IHHL)",
        "doc_title": "MoHUA Swachh Bharat Mission - Urban 2.0 Operational Guidelines for Individual Household Latrines",
        "doc_type": "operational_guidelines",
        "source_url": "https://sbmurban.org",
        "effective_from": "2014-10-02",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Direct Household Latrine Construction Incentive",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, MoHUA SBM-U IHHL Guidelines",
                "content": (
                    "Under SBM-U, households without a sanitary toilet receive direct incentive assistance for Individual Household Latrine (IHHL) construction: "
                    "Central Government share of ₹4,000 per toilet unit, matched with a mandatory State share of minimum ₹1,333 (with total assistance "
                    "reaching ₹5,333 to ₹12,000 depending on state top-up). The incentive is disbursed via DBT in two equal installments: "
                    "50% on construction up to substructure/pit level, and 50% on complete functional superstructure completion with a geo-tagged photograph."
                ),
                "tranches": [
                    {
                        "tranche_name": "1st Installment (50%)",
                        "amount": "₹2,000 Central + State Share",
                        "tenure": "Pit/Base construction stage",
                        "conditions": "Verified by ULB ward officer with initial geo-tagged site photo."
                    },
                    {
                        "tranche_name": "2nd Installment (50%)",
                        "amount": "₹2,000 Central + State Share",
                        "tenure": "Functional completion",
                        "conditions": "Verified with functional sanitary toilet and beneficiary geo-tagged photo."
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, MoHUA SBM-U Guidelines",
                "content": (
                    "Urban households residing within statutory towns or notified municipal jurisdictions that do not possess a sanitary toilet "
                    "(households practicing open defecation or having insanitary single-pit or dry latrines)."
                )
            },
            {
                "heading": "Existing Sanitary Toilet & Rural Area Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, MoHUA SBM-U Exclusions",
                "content": (
                    "Households already possessing a functional sanitary flush/pour-flush latrine (EXISTING_TOILET) are strictly EXCLUDED. "
                    "Households situated outside statutory municipal/urban local body jurisdiction (URBAN_JURISDICTION) are excluded (covered under SBM-Gramin)."
                )
            },
            {
                "heading": "Application Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, MoHUA Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card of head of household; "
                    "(2) Bank Account Passbook with IFSC; "
                    "(3) Geo-tagged photograph of applicant at proposed toilet construction location; "
                    "(4) Municipal ward residential proof."
                )
            }
        ]
    },

    # ── 26. Pradhan Mantri Matsya Sampada Yojana (PMMSY) ─────────────────────
    "dbtbharat_central_schemes_pradhan_mantri_matsya_sampada_yojana": {
        "scheme_name": "Pradhan Mantri Matsya Sampada Yojana (PMMSY)",
        "doc_title": "Department of Fisheries PMMSY Operational Guidelines and Financial Norms",
        "doc_type": "operational_guidelines",
        "source_url": "https://pmmsy.dof.gov.in",
        "effective_from": "2020-05-20",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Aquaculture & Fisheries Capital Subsidies",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, DoF PMMSY Guidelines",
                "content": (
                    "PMMSY provides financial subsidies for fish farming infrastructure: "
                    "40% government subsidy for general category beneficiaries and up to 60% for SC, ST, and Women beneficiaries. "
                    "Covered activities include: construction of new aquaculture ponds (unit cost ₹7 Lakhs/ha, subsidy up to ₹4.2 Lakhs), "
                    "biofloc fish farming units (unit cost ₹7.5 Lakhs, subsidy up to ₹4.5 Lakhs), recirculatory aquaculture systems (RAS), "
                    "deep-sea fishing vessels (subsidy up to ₹36 Lakhs), and motorcycle with ice-box (subsidy up to ₹45,000)."
                )
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, DoF PMMSY Guidelines",
                "content": (
                    "Fishers, fish farmers, fish workers, fish vendors, fisheries self-help groups (SHGs), fisheries cooperatives, "
                    "and youth entrepreneurs having title deed or long-term lease rights over suitable land or water bodies."
                )
            },
            {
                "heading": "Duplicate Claim Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, DoF PMMSY Exclusions",
                "content": (
                    "Submitting a duplicate subsidy claim for the same water body or equipment unit that previously availed government subsidy "
                    "(DUPLICATE_CLAIM) is strictly EXCLUDED. Non-fisheries commercial projects are excluded."
                )
            },
            {
                "heading": "Required Project Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, DoF Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Land / Water Body Ownership Records or registered lease deed (minimum 7-10 years); "
                    "(3) Detailed Project Report (DPR) with technical layout; "
                    "(4) Bank Account Passbook with IFSC; "
                    "(5) Valid dealer quotation for machinery / biofloc equipment."
                )
            }
        ]
    },

    # ── 27. Sub-Mission on Agricultural Mechanization (SMAM) ─────────────────
    "dbtbharat_central_schemes_sub_mission_on_agriculture_mechanization_central_sector": {
        "scheme_name": "Sub-Mission on Agricultural Mechanization (SMAM)",
        "doc_title": "DA&FW SMAM Operational Guidelines and Agricultural Machinery Portal Rules",
        "doc_type": "operational_guidelines",
        "source_url": "https://agrimachinery.nic.in",
        "effective_from": "2014-04-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Agricultural Machinery Purchase Subsidies",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Clause 2.1, DA&FW SMAM Guidelines",
                "content": (
                    "Under SMAM, farmers receive capital subsidies for the procurement of tested and certified farm machinery: "
                    "40% subsidy for general category farmers and up to 50% subsidy for SC, ST, Small & Marginal farmers, and Women farmers "
                    "(e.g., tractors, power tillers, rotavators, laser land levelers, multi-crop threshers, and combine harvesters). "
                    "Financial assistance up to 80% is provided for establishing Custom Hiring Centres (CHCs) by farmer cooperative groups."
                )
            },
            {
                "heading": "Eligibility Criteria",
                "section_type": "eligibility_criteria",
                "citation_clause": "Clause 3.1, DA&FW SMAM Eligibility",
                "content": (
                    "Individual farmers and landholding farmer families who own cultivable land in their name and have not availed subsidy "
                    "for the same implement in the past 5 years. Small & Marginal farmers (landholding <= 2 hectares) are prioritized."
                )
            },
            {
                "heading": "5-Year Lock-in & Prior Subsidy Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Clause 3.3, DA&FW SMAM Exclusions",
                "content": (
                    "Farmers who have availed subsidy for the same type of agricultural machinery or implement under any central or state scheme "
                    "within the preceding 5 years (PRIOR_SUBSIDY) are strictly EXCLUDED. Non-landholding individuals and non-certified dealers excluded."
                )
            },
            {
                "heading": "Application Documents",
                "section_type": "documents_required",
                "citation_clause": "Clause 4.1, DA&FW Documentation",
                "content": (
                    "Required documents: "
                    "(1) Aadhaar Card; "
                    "(2) Record of Rights (RoR / 7-12 / Khatauni / Khasra) proving cultivable land ownership; "
                    "(3) Bank Passbook seeded with Aadhaar; "
                    "(4) Valid proforma invoice from an authorized registered machinery manufacturer/dealer."
                )
            }
        ]
    },

    # ── 28. PM-DAKSH Scheme ──────────────────────────────────────────────────
    "dbtbharat_central_schemes_pm_daksh_scheme": {
        "scheme_name": "PM-DAKSH Scheme",
        "doc_title": "MoSJE PM-DAKSH Portal Guidelines for Skill Development",
        "doc_type": "operational_guidelines",
        "source_url": "https://pmdaksh.dosje.gov.in",
        "effective_from": "2020-01-01",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Free Skill Training Programs & Daily Stipend",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, MoSJE PM-DAKSH Guidelines",
                "content": (
                    "PM-DAKSH offers completely free skill development programs across four tiers: "
                    "1. Up-skilling / Re-skilling (35-80 hours) with ₹2,500 wage compensation; "
                    "2. Short-Term Training (200-600 hours) with ₹1,500 per month stipend; "
                    "3. Long-Term Training (5-12 months) with ₹1,500 per month stipend; "
                    "4. Entrepreneurship Development Programs (EDP) of 80-90 hours. "
                    "Stipends are credited directly via DBT to candidates maintaining minimum 80% course attendance."
                )
            },
            {
                "heading": "Eligibility Criteria & Target Disadvantaged Groups",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, MoSJE PM-DAKSH Guidelines",
                "content": (
                    "Youth aged between 18 and 45 years belonging to target disadvantaged groups: "
                    "(a) Scheduled Castes (SC); "
                    "(b) Other Backward Classes (OBC) with annual family income <= ₹3,00,000; "
                    "(c) Economically Backward Classes (EBC) with annual family income <= ₹1,00,000; "
                    "(d) De-notified, Nomadic, and Semi-Nomadic Tribes (DNT); "
                    "(e) Safai Karamcharis (including manual scavengers and waste pickers) with no income limit."
                )
            },
            {
                "heading": "Prior Training & Income Ceiling Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, MoSJE PM-DAKSH Exclusions",
                "content": (
                    "Candidates who have undergone skill development training under any government scheme in the past 2 years (PRIOR_TRAINING) "
                    "are strictly EXCLUDED. OBC/EBC candidates with family income exceeding statutory ceilings (INCOME_CEILING) are excluded. "
                    "Persons aged under 18 or above 45 years are excluded."
                )
            },
            {
                "heading": "Required Enrolment Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoSJE Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Caste Certificate (for SC/OBC) or Safai Karamchari ID card; "
                    "(3) Income Certificate (<= ₹3 Lakh for OBC, <= ₹1 Lakh for EBC); "
                    "(4) Bank Passbook with IFSC; "
                    "(5) Minimum educational qualification certificate."
                )
            }
        ]
    },

    # ── 29. Deen Dayal Upadhyay Grameen Kaushalya Yojana (DDU-GKY) ───────────
    "dbtbharat_central_schemes_deen_dayal_upadhyay_grameen_kaushalya_yojna": {
        "scheme_name": "Deen Dayal Upadhyay Grameen Kaushalya Yojna (DDU-GKY)",
        "doc_title": "MoRD DDU-GKY Operational Guidelines and Placement Framework",
        "doc_type": "operational_guidelines",
        "source_url": "http://ddugky.gov.in",
        "effective_from": "2014-09-25",
        "effective_to": None,
        "currentness": "current",
        "sections": [
            {
                "heading": "Placement-Linked Skill Training & Post-Placement Support",
                "section_type": "benefits_and_tranches",
                "citation_clause": "Section 2.1, MoRD DDU-GKY Guidelines",
                "content": (
                    "DDU-GKY provides completely free residential and non-residential market-relevant skill training with guaranteed placement: "
                    "Minimum 70% of trained candidates must be placed in formal wage employment. Benefits include free boarding, lodging, "
                    "uniforms, study materials, tablet computers, and post-placement financial support: "
                    "₹1,000 per month for 2 months (placement within home district), ₹1,000 per month for 3 months (within home state), "
                    "or ₹1,000 per month for 6 months (interstate placement outside home state) credited via DBT."
                ),
                "tables": [
                    {
                        "title": "DDU-GKY Post-Placement Support Allowance",
                        "headers": ["Placement Location", "Monthly Allowance (₹)", "Duration", "Total Support (₹)"],
                        "rows": [
                            ["Placement within Home District", "₹1,00,0 / month", "2 Months", "₹2,000 via DBT"],
                            ["Placement within Home State (outside district)", "₹1,000 / month", "3 Months", "₹3,000 via DBT"],
                            ["Placement outside Home State", "₹1,000 / month", "6 Months", "₹6,000 via DBT"]
                        ]
                    }
                ]
            },
            {
                "heading": "Eligibility Criteria & Rural Domicile Mandate",
                "section_type": "eligibility_criteria",
                "citation_clause": "Section 3.1, MoRD DDU-GKY Guidelines",
                "content": (
                    "Rural youth aged between 15 and 35 years belonging to poor rural households (identified via SECC 2011, BPL card, "
                    "Antyodaya Anna Yojana card, or family having MGNREGA job card with at least 15 days work in preceding year). "
                    "Upper age limit is relaxed up to 45 years for women, persons with disabilities (PwD), and primitive tribal groups."
                )
            },
            {
                "heading": "Urban Domicile & Age Bracket Exclusions",
                "section_type": "exclusions",
                "citation_clause": "Section 3.3, MoRD DDU-GKY Exclusions",
                "content": (
                    "Youth residing in urban areas (RURAL_DOMICILE) are strictly EXCLUDED. "
                    "Candidates outside the 15 to 35 age bracket (AGE_BRACKET, or outside 15-45 for affirmative action categories) are excluded. "
                    "Candidates from non-poor rural families are excluded."
                )
            },
            {
                "heading": "Verification Documents",
                "section_type": "documents_required",
                "citation_clause": "Section 4.1, MoRD Documentation",
                "content": (
                    "Required documentation: "
                    "(1) Aadhaar Card; "
                    "(2) Age proof (School Certificate / Birth Certificate); "
                    "(3) Rural Domicile verification; "
                    "(4) BPL Card / AAY Card / MGNREGA Job Card of family member; "
                    "(5) Bank Passbook with IFSC."
                )
            }
        ]
    }
}

