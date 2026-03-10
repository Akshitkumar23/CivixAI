import pandas as pd
import re
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MASTER_CSV = DATA_DIR / "master" / "schemes_master.csv"

# ==========================================
# DYNAMIC HEURISTIC NLP RULES FOR ALL SCHEMES
# ==========================================

# 1. Categories based on keywords
CATEGORY_RULES = {
    "agriculture": ["kisan", "krishi", "agriculture", "crop", "farmer", "irrigation", "soil", "seed", "horticulture", "agri"],
    "education": ["scholarship", "fellowship", "education", "student", "school", "college", "university", "vidya", "shiksha", "padhai", "academic", "hostel"],
    "health": ["health", "medical", "swasthya", "arogya", "ayushman", "hospital", "disease", "treatment", "maternity", "medicine", "suraksha"],
    "housing": ["housing", "awas", "shelter", "ghar"],
    "pension": ["pension", "old age", "widow", "vridha", "vidhwa", "senior citizen", "retirement"],
    "employment": ["employment", "rozgar", "nrega", "job", "shramik", "worker", "labour", "skill", "kaushal", "training"],
    "business": ["business", "loan", "micro", "enterprise", "mudra", "startup", "stand-up", "msme", "udyog", "vyapar", "industry"],
    "women_welfare": ["mahila", "women", "maternity", "pregnant", "girl", "beti", "sukanya", "kanya", "matru", "widow", "mother"],
    "child_welfare": ["child", "bal", "infant", "anganwadi", "nutrition", "poshan", "orphan", "kids"],
    "infrastructure": ["road", "sadak", "gramin", "village", "water", "jal", "electricity", "urja"],
}

# 2. Age Limits logic
AGE_RULES = [
    ({"student", "scholarship", "child", "school", "bal", "kanya"}, {"min_age": 5, "max_age": 25}),
    ({"old age", "vridha", "senior citizen", "retirement"}, {"min_age": 60, "max_age": None}),
    ({"widow", "vidhwa"}, {"min_age": 18, "max_age": 60}),
    ({"youth", "employment", "skill", "kaushal", "rozgar", "startup"}, {"min_age": 18, "max_age": 35}),
    ({"kisan", "farmer", "business", "loan", "worker", "shramik", "msme"}, {"min_age": 18, "max_age": 60}),
    ({"maternity", "pregnant", "matru", "mahila"}, {"min_age": 18, "max_age": 45}),
]

# 3. Required Documents logic
DOC_RULES = {
    "agriculture": "Aadhaar Card, Land Ownership Papers (Khasra/Khatauni), Bank Passbook, Passport Size Photo",
    "education": "Aadhaar Card, Previous Year Marksheets, School/College ID, Income Certificate, Caste Certificate (if applicable)",
    "health": "Aadhaar Card, Medical Reports/Certificate, Ration Card, Bank Details",
    "housing": "Aadhaar Card, Residence Proof, Income Certificate, Bank Details",
    "pension": "Aadhaar Card, Age/Death/Disability Certificate (as applicable), Bank Passbook, Income Certificate",
    "employment": "Aadhaar Card, Educational Certificates, Job Card (if applicable), Bank Details",
    "business": "Aadhaar Card, Business Plan, PAN Card, Bank Statement, ITR (if applicable)",
    "women_welfare": "Aadhaar Card, Bank Passbook, Relevant Certificates (Marriage/Birth/Maternity)",
    "child_welfare": "Birth Certificate, Aadhaar Card of Parents, Ration Card",
    "infrastructure": "Aadhaar Card, Address Proof, Community Application / Panchayat Approval"
}

# 4. Smart Benefit Description Generators
BENEFIT_TEMPLATES = {
    "agriculture": "Provides financial, technical, or resource assistance to farmers to improve agricultural productivity and secure rural livelihood.",
    "education": "Offers financial support, scholarships, or educational resources to students to encourage higher learning and reduce financial burdens.",
    "health": "Covers medical expenses, hospitalization, or provides maternity benefits to ensure better, affordable healthcare access.",
    "housing": "Provides financial aid or subsidies for the construction, purchase, or renovation of houses for eligible working-class beneficiaries.",
    "pension": "Ensures financial security through regular monthly pension disbursements to vulnerable groups like the elderly, widows, or differently-abled individuals.",
    "employment": "Facilitates job creation, skill development, or guaranteed wage employment to enhance livelihood opportunities for youth and workers.",
    "business": "Offers easy credit, subsidies, or institutional support to promote entrepreneurship, MSMEs, and self-reliant small businesses.",
    "women_welfare": "Aims to empower women and girls through targeted financial, educational, or health-related interventions to promote gender equality.",
    "child_welfare": "Focuses on the nutrition, health, and well-being of children to ensure their holistic development and early childcare protection.",
    "infrastructure": "Aims to develop robust rural or urban infrastructure, improving basic amenities like roads, water, and electricity."
}

# 5. Benefit Type Classifiers (Schemes, Loans, Insurance)
BENEFIT_TYPE_RULES = {
    "loan": ["loan", "credit", "mudra", "nabard", "financing", "subsidy", "startup funding", "capital", "kcc", "kisan credit card", "bima"],
    "insurance": ["insurance", "bima", "pension", "suraksha", "jeevan jyoti", "suraksha bima", "ayushman", "health cover"],
}

def infer_category(text):
    text = text.lower()
    for cat, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if re.search(r'\b' + kw + r'\b', text):
                return cat
    return "general_welfare"

def infer_age(text):
    text = text.lower()
    for keywords, ages in AGE_RULES:
        if any(re.search(r'\b' + kw + r'\b', text) for kw in keywords):
            return ages
    return {"min_age": None, "max_age": None}

def infer_docs(category):
    return DOC_RULES.get(category, "Aadhaar Card, Residence Proof, Income Certificate, Bank Passbook, Passport Size Photograph")

def infer_benefit(category, scheme_name, ministry):
    template = BENEFIT_TEMPLATES.get(category, f"The scheme provides targeted benefits under the {ministry}. It is designed to uplift eligible citizens by offering specialized assistance and resources.")
    return f"This {category.replace('_', ' ')} program aims to support eligible citizens. {template} This specific program is formally mapped as '{scheme_name}'."

def infer_benefit_type(text):
    text = text.lower()
    # Check insurance first as it's more specific
    for kw in BENEFIT_TYPE_RULES["insurance"]:
        if re.search(r'\b' + kw + r'\b', text):
            return "insurance"
            
    # Then check for loans/credit
    for kw in BENEFIT_TYPE_RULES["loan"]:
        if re.search(r'\b' + kw + r'\b', text):
            return "loan"
            
    # Default is a standard scheme
    return "scheme"

def enrich_data():
    if not MASTER_CSV.exists():
        print(f"File not found: {MASTER_CSV}")
        return

    df = pd.read_csv(MASTER_CSV, dtype=str)
    
    # Ensure all columns exist and are of object dtype
    cols_to_check = ['benefit_description', 'documents_required', 'min_age', 'max_age', 'income_limit', 'scheme_category', 'benefit_type']
    for col in cols_to_check:
        if col not in df.columns:
             df[col] = ''
        df[col] = df[col].astype('object')
    
    enriched_count = 0
    
    for i, row in df.iterrows():
        name = str(row.get('scheme_name', ''))
        ministry = str(row.get('ministry', ''))
        desc = str(row.get('benefit_description', ''))
        
        # We combine text from name, ministry, and current description to analyze the context
        combined_text = f"{name} {ministry} {desc}".lower()
        
        # 1. Infer Category Dynamically
        if pd.isna(row.get('scheme_category')) or str(row.get('scheme_category')).strip() in ['', 'mixed', 'general', 'nan']:
            cat = infer_category(combined_text)
            df.at[i, 'scheme_category'] = cat
        else:
            cat = str(row.get('scheme_category')).strip()
            
        # 2. Infer Age Limits Dynamically
        inferred_ages = infer_age(combined_text)
        if pd.isna(row.get('min_age')) or str(row.get('min_age')).strip() in ['', 'nan']:
            if inferred_ages['min_age'] is not None:
                df.at[i, 'min_age'] = inferred_ages['min_age']
                
        if pd.isna(row.get('max_age')) or str(row.get('max_age')).strip() in ['', 'nan']:
            if inferred_ages['max_age'] is not None:
                df.at[i, 'max_age'] = inferred_ages['max_age']
                
        # 3. Infer Documents Dynamically
        if pd.isna(row.get('documents_required')) or str(row.get('documents_required')).strip() in ['', 'nan']:
            df.at[i, 'documents_required'] = infer_docs(cat)
            
        # 4. Infer description Dynamically
        if pd.isna(row.get('benefit_description')) or str(row.get('benefit_description')).strip() in ['', 'nan'] or "provides targeted benefits" in desc:
            df.at[i, 'benefit_description'] = infer_benefit(cat, name, ministry.strip() or 'Government')
            
        # 5. Infer Benefit Type (Scheme vs Loan vs Insurance)
        if pd.isna(row.get('benefit_type')) or str(row.get('benefit_type')).strip() in ['', 'nan']:
            df.at[i, 'benefit_type'] = infer_benefit_type(combined_text)
             
        enriched_count += 1

    # Save to CSV
    df.to_csv(MASTER_CSV, index=False)
    print(f"Successfully ran DYNAMIC NLP enrichment on {enriched_count} schemes based on intelligent heuristics.")


if __name__ == "__main__":
    enrich_data()
