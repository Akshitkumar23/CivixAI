import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
MASTER_PATH = DATA_DIR / "master" / "schemes_master.csv"

# Predefined list of real Loans and Insurance from various portals 
# (Jan Samarth, Vidya Lakshmi, PMJAY, LIC, etc.)
FINANCIAL_SCHEMES = [
    # ---- TOP PROFITABLE INVESTMENTS / SAVINGS ----
    {
        "scheme_id": "ppf_india",
        "scheme_name": "Public Provident Fund (PPF)",
        "ministry": "Ministry of Finance",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "investment",
        "documents_required": "Aadhaar, PAN, Passport Size Photos",
        "application_url": "https://www.indiapost.gov.in/",
        "benefit_description": "A long-term, tax-free investment scheme backed by the Govt of India, offering high guaranteed returns and EEE tax benefits.",
        "min_age": 18,
        "max_age": "",
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Lock-in period of 15 years.",
        "source_url": "https://www.indiapost.gov.in/",
        "benefit_type": "investment"
    },
    {
        "scheme_id": "sukanya_samriddhi",
        "scheme_name": "Sukanya Samriddhi Yojana (SSY)",
        "ministry": "Ministry of Finance",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "investment",
        "documents_required": "Birth Certificate of Girl Child, Aadhaar, PAN of Parent",
        "application_url": "https://www.indiapost.gov.in/",
        "benefit_description": "High-interest savings scheme exclusively for the parents of a girl child to secure her education and marriage expenses.",
        "min_age": 0,
        "max_age": 10,  # Max age of girl child to open account
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "For girl child only. Max 2 accounts per family.",
        "source_url": "https://www.indiapost.gov.in/",
        "benefit_type": "investment"
    },
    {
        "scheme_id": "nps_india",
        "scheme_name": "National Pension System (NPS)",
        "ministry": "PFRDA / Ministry of Finance",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "pension",
        "documents_required": "Aadhaar, PAN, Bank Details",
        "application_url": "https://enps.nsdl.com/",
        "benefit_description": "Market-linked retirement savings scheme offering huge tax savings (up to ₹2L) and substantial wealth corpus on retirement.",
        "min_age": 18,
        "max_age": 70,
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "",
        "source_url": "https://enps.nsdl.com/",
        "benefit_type": "investment"
    },
    {
        "scheme_id": "zerodha_groww_sip",
        "scheme_name": "Mutual Funds & SIPs via Top Brokers (Groww/Zerodha)",
        "ministry": "Private Platforms",
        "scheme_level": "private",
        "scheme_type": "private",
        "scheme_category": "investment",
        "documents_required": "PAN, Aadhaar, Bank Statement (KYC)",
        "application_url": "https://groww.in/",
        "benefit_description": "Invest in top-performing mutual funds and Direct Equity to beat inflation and achieve huge long-term compounding profits.",
        "min_age": 18,
        "max_age": "",
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Subject to market risks.",
        "source_url": "https://zerodha.com/",
        "benefit_type": "investment"
    },

    # ---- TOP LOANS (BUSINESS & PERSONAL) ----
    {
        "scheme_id": "pmegp_business_loan",
        "scheme_name": "Prime Minister's Employment Generation Programme (PMEGP)",
        "ministry": "Ministry of MSME",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "business",
        "documents_required": "Aadhaar, Project Report, Education Certificate, Caste Certificate",
        "application_url": "https://www.kviconline.gov.in/pmegpeportal/",
        "benefit_description": "Get credit-linked subsidy up to 35% on business loans ranging from ₹20 Lakhs to ₹50 Lakhs for setting up new enterprises.",
        "min_age": 18,
        "max_age": 65,
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Must be 8th pass for projects above 10L (manufacturing).",
        "source_url": "https://msme.gov.in/",
        "benefit_type": "loan"
    },
    {
        "scheme_id": "stand_up_india",
        "scheme_name": "Stand-Up India Scheme",
        "ministry": "Ministry of Finance",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "business",
        "documents_required": "Aadhaar, PAN, Project Report, SC/ST Certificate",
        "application_url": "https://www.standupmitra.in/",
        "benefit_description": "Bank loans between ₹10 lakh and ₹1 Crore for SC/ST and women entrepreneurs for greenfield enterprises.",
        "min_age": 18,
        "max_age": 65,
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Must be Women or SC/ST entrepreneur.",
        "source_url": "https://www.standupmitra.in/",
        "benefit_type": "loan"
    },
    {
        "scheme_id": "pmay_home_loan",
        "scheme_name": "Pradhan Mantri Awas Yojana (PMAY) - Home Loan Subsidy",
        "ministry": "Ministry of Housing and Urban Affairs",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "housing",
        "documents_required": "Aadhaar, PAN, Income Proof, Property Documents",
        "application_url": "https://pmay-urban.gov.in/pma-online-application",
        "benefit_description": "Interest subsidy up to ₹2.67 Lakhs on home loans for purchasing or constructing your first house.",
        "min_age": 18,
        "max_age": 70,
        "income_limit": 1800000,
        "applicable_states": "ALL",
        "special_conditions_required": "Applicant must not own a pucca house in India.",
        "source_url": "https://pmay-urban.gov.in/",
        "benefit_type": "loan"
    },
    {
        "scheme_id": "bajaj_sbi_personal_loan",
        "scheme_name": "Top NBFC/Bank Instant Loans (Bajaj Finserv & SBI)",
        "ministry": "Private / Corporate",
        "scheme_level": "private",
        "scheme_type": "private",
        "scheme_category": "personal",
        "documents_required": "PAN, Aadhaar, Salary Slips, Bank Statements",
        "application_url": "https://www.bajajfinserv.in/",
        "benefit_description": "Instant approvals and high disbursal amounts for salaried and business professionals. Quick processing with low documentation.",
        "min_age": 21,
        "max_age": 60,
        "income_limit": 300000,
        "applicable_states": "ALL",
        "special_conditions_required": "Good CIBIL score (700+) and steady income required.",
        "source_url": "https://www.onlinesbi.sbi/",
        "benefit_type": "loan"
    },
    {
        "scheme_id": "hdfc_credila_education_loan",
        "scheme_name": "HDFC Credila Higher Education Loans",
        "ministry": "Private NBFC",
        "scheme_level": "private",
        "scheme_type": "private",
        "scheme_category": "education",
        "documents_required": "Admission Letter, PAN, Aadhaar, Co-borrower Income Proof",
        "application_url": "https://www.hdfccredila.com/",
        "benefit_description": "Customized education loans covering 100% of study expenses for premium domestic and international universities.",
        "min_age": 18,
        "max_age": 35,
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Confirmed admission to a recognized institute.",
        "source_url": "https://www.hdfccredila.com/",
        "benefit_type": "loan"
    },

    # ---- TOP INSURANCE PLAYS ----
    {
        "scheme_id": "star_niva_health_insurance",
        "scheme_name": "Top Private Health Insurance (Star Health / Niva Bupa)",
        "ministry": "Private Insurance Sector",
        "scheme_level": "private",
        "scheme_type": "private",
        "scheme_category": "health",
        "documents_required": "Aadhaar, PAN, Medical History",
        "application_url": "https://www.policybazaar.com/health-insurance/",
        "benefit_description": "Comprehensive cashless family health covers up to ₹1 Crore with no room-rent capping and free annual checkups.",
        "min_age": 18,
        "max_age": 65,
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Pre-existing diseases might have a waiting period.",
        "source_url": "https://www.policybazaar.com/",
        "benefit_type": "insurance"
    },
    {
        "scheme_id": "hdfc_icici_term_life",
        "scheme_name": "Premium Term Life Insurance (HDFC Life / ICICI Pru)",
        "ministry": "Private Insurance Sector",
        "scheme_level": "private",
        "scheme_type": "private",
        "scheme_category": "health",
        "documents_required": "Aadhaar, PAN, Income Proof, Medical Tests",
        "application_url": "https://www.policybazaar.com/life-insurance/term-insurance/",
        "benefit_description": "High coverage term plans up to ₹5 Crores at nominal monthly premiums starting at ₹500, securing your family's future.",
        "min_age": 18,
        "max_age": 60,
        "income_limit": 300000,
        "applicable_states": "ALL",
        "special_conditions_required": "Requires steady income proof for high covers.",
        "source_url": "https://www.policybazaar.com/",
        "benefit_type": "insurance"
    },
    {
        "scheme_id": "ayushman_bharat_v2",
        "scheme_name": "Ayushman Bharat PM-JAY (Government Top-Tier Cover)",
        "ministry": "Ministry of Health and Family Welfare",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "health",
        "documents_required": "Aadhaar, Ration Card, PMJAY Card",
        "application_url": "https://beneficiary.nha.gov.in/",
        "benefit_description": "India's largest health assurance scheme covering up to ₹5 lakh per family per year for most severe medical conditions entirely free.",
        "min_age": 0,
        "max_age": "",
        "income_limit": 500000,
        "applicable_states": "ALL",
        "special_conditions_required": "Listed in SEC-2011/BPL category.",
        "source_url": "https://nha.gov.in/PM-JAY",
        "benefit_type": "insurance"
    },
    
    # ---- BUSINESS & STARTUPS ----
    {
        "scheme_id": "startup_india_seed_fund",
        "scheme_name": "Startup India Seed Fund Scheme (SISFS)",
        "ministry": "DPIIT",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "business",
        "documents_required": "DPIIT Recognition, Pitch Deck, Incorporation Docs",
        "application_url": "https://seedfund.startupindia.gov.in/",
        "benefit_description": "Provides financial assistance to startups for proof of concept, prototype development, and highly profitable early revenue scaling.",
        "min_age": 18,
        "max_age": "",
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Must be a DPIIT recognized startup incorporated < 2 years ago.",
        "source_url": "https://seedfund.startupindia.gov.in/",
        "benefit_type": "scheme"
    },
    
    # ---- ESSENTIAL GOVT LOANS & INSURANCES (Quick & Accessible) ----
    {
        "scheme_id": "js_mudra_all",
        "scheme_name": "Pradhan Mantri Mudra Yojana (PMMY) - Up to 10 Lakhs",
        "ministry": "Ministry of Finance",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "business",
        "documents_required": "Aadhaar Card, PAN Card, Business Plan, Bank Statement",
        "application_url": "https://www.jansamarth.in",
        "benefit_description": "Easy collateral-free loans up to Rs. 10 Lakhs (Shishu, Kishor, Tarun) to quickly kickstart or expand highly profitable micro-enterprises.",
        "min_age": 18,
        "max_age": 65,
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Must not be a defaulter of any bank.",
        "source_url": "https://www.jansamarth.in",
        "benefit_type": "loan"
    },
    {
        "scheme_id": "pm_jeevan_jyoti_bima_v2",
        "scheme_name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "ministry": "Ministry of Finance",
        "scheme_level": "central",
        "scheme_type": "central",
        "scheme_category": "health",
        "documents_required": "Aadhaar, Bank Account passbook",
        "application_url": "https://nationalinsurance.nic.co.in",
        "benefit_description": "Ultra-cheap life insurance scheme offering a coverage of ₹2 lakh for death due to any reason at a premium of just ₹436 per annum.",
        "min_age": 18,
        "max_age": 50,
        "income_limit": "",
        "applicable_states": "ALL",
        "special_conditions_required": "Auto-debit required.",
        "source_url": "https://financialservices.gov.in",
        "benefit_type": "insurance"
    }
]

def append_financials():
    if not MASTER_PATH.exists():
        print("Master CSV does not exist. Run scrape_schemes.py first.")
        return

    df_original = pd.read_csv(MASTER_PATH, dtype=str)
    
    # Check if we already added these (to avoid duplication if run multiple times)
    existing_ids = df_original['scheme_id'].fillna('').tolist()
    
    new_rows = []
    for item in FINANCIAL_SCHEMES:
        if item['scheme_id'] not in existing_ids:
            new_rows.append(item)
            
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        # Ensure all columns match master
        for col in df_original.columns:
            if col not in df_new.columns:
                df_new[col] = ""
        
        df_new = df_new[df_original.columns]
        
        df_final = pd.concat([df_original, df_new], ignore_index=True)
        df_final.to_csv(MASTER_PATH, index=False, encoding="utf-8")
        print(f"Successfully appended {len(new_rows)} Loans/Insurance schemes to master dataset!")
    else:
        print("Financial schemes already exist in the master dataset.")

if __name__ == "__main__":
    append_financials()
