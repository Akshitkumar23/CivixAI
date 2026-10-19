import csv
import random
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "data" / "master" / "schemes_master.csv"
OUT_PATH = ROOT / "data" / "processed" / "eligibility_train.csv"

STATES = ["Andhra Pradesh", "Bihar", "Delhi", "Gujarat", "Haryana", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Odisha", "Punjab", "Rajasthan", "Tamil Nadu", "Telangana", "Uttar Pradesh", "West Bengal"]
OCCUPATIONS = ["farmer", "student", "worker", "self_employed", "unemployed", "government_employee", "private_employee"]
EDU_LEVELS = ["none", "primary", "secondary", "higher_secondary", "graduate", "postgraduate"]
MARITAL_STATUSES = ["single", "married", "widowed"]
EMPLOYMENT_TYPES = ["salaried", "self_employed", "informal"]

def _create_user() -> dict:
    age = int(np.random.triangular(0, 30, 95))
    gender = random.choices(["male", "female"], weights=[0.5, 0.5])[0]
    annual_income = int(np.random.lognormal(mean=12.5, sigma=0.8))
    annual_income = int(max(0, min(annual_income, 3000000)))
    
    state = random.choice(STATES)
    caste = random.choices(["GEN", "OBC", "SC", "ST"], weights=[0.4, 0.3, 0.2, 0.1])[0]
    urban_rural = random.choices(["urban", "rural"], weights=[0.4, 0.6])[0]
    
    # Logic-based attributes
    marital_status = random.choice(MARITAL_STATUSES) if age > 18 else "single"
    if age < 18:
        edu = random.choice(["none", "primary", "secondary"])
        occu = "student"
    elif age < 25:
        edu = random.choice(["secondary", "higher_secondary", "graduate"])
        occu = "student" if random.random() < 0.6 else random.choice(OCCUPATIONS)
    else:
        edu = random.choice(EDU_LEVELS)
        occu = random.choice([o for o in OCCUPATIONS if o != "student"])

    is_bpl = 1 if annual_income < 200000 else 0
    is_minority = 1 if random.random() < 0.2 else 0
    has_disability = 1 if random.random() < 0.05 else 0
    
    # NEW: Fill missing columns expected by utils.py
    family_size = random.randint(1, 6)
    land_size = float(round(float(np.random.gamma(shape=1.2, scale=0.4)), 2)) if occu == "farmer" else 0.0
    
    return {
        "age": age,
        "gender": gender,
        "annualIncome": annual_income,
        "familyIncome": annual_income + random.randint(0, 50000),
        "state": state,
        "caste": caste,
        "occupation": occu,
        "educationLevel": edu,
        "maritalStatus": marital_status,
        "urbanRural": urban_rural,
        "isBPL": is_bpl,
        "isMinority": is_minority,
        "hasDisability": has_disability,
        "hasLand": 1 if land_size > 0 else 0,
        "landSize": land_size,
        "familySize": family_size,
        "isSingleGirlChild": 1 if gender == "female" and family_size < 3 and random.random() < 0.3 else 0,
        "isWidowOrSenior": 1 if (age > 60 or (gender == "female" and marital_status == "widowed")) else 0,
        "isTaxPayer": 1 if annual_income > 700000 else 0,
        "isBankLinked": 1 if random.random() < 0.95 else 0,
        "digitalLiteracy": random.choice(["low", "medium", "high"]),
        "monthlyExpenses": int(annual_income / 12 * 0.7),
        "hasSmartphone": 1 if random.random() < 0.85 else 0,
        "hasInternet": 1 if random.random() < 0.8 else 0,
        "employmentType": random.choice(EMPLOYMENT_TYPES) if age > 20 else "none",
        "hasAvailedSimilarScheme": 0,
        "skillCertification": random.choice(["none", "iti", "diploma"]) if age > 18 else "none",
        "loanRequirement": "business" if occu == "self_employed" else "none",
        "monthlySavings": int(annual_income / 12 * 0.2),
        "hasInsurance": 1 if random.random() < 0.4 else 0,
        "hasPension": 1 if age > 60 else 0,
        "prioritySchemes": ""
    }

def check_eligibility(user, scheme) -> int:
    def safe_num(val, default):
        try:
            if pd.isna(val) or val == "" or val == "nan": return default
            return int(float(val))
        except: return default

    # 1. Basic Demographics
    min_age = safe_num(scheme.get('min_age'), 0)
    max_age = safe_num(scheme.get('max_age'), 100)
    if user['age'] < min_age or user['age'] > max_age: return 0
    
    income_limit = safe_num(scheme.get('income_limit'), 999999999)
    if user['annualIncome'] > income_limit: return 0
    
    # 2. Gender
    scheme_gender = str(scheme.get('gender_eligibility', 'all')).lower()
    if scheme_gender != 'all' and user['gender'] != scheme_gender: return 0
    
    # 3. State
    app_states = str(scheme.get('applicable_states', 'ALL')).upper()
    if app_states != 'ALL' and 'ALL' not in app_states and user['state'].lower() not in app_states.lower(): 
        return 0
    
    # 4. Caste / Minority
    scheme_caste = str(scheme.get('caste_eligibility', 'all')).upper()
    if scheme_caste != 'ALL' and 'ALL' not in scheme_caste:
        if 'MINORITY' in scheme_caste and user['isMinority'] == 0: return 0
        user_caste = str(user['caste']).upper()
        if user_caste not in scheme_caste: return 0
    
    # 5. Disability
    if str(scheme.get('disability_required', 'false')).lower() == 'true' and user['hasDisability'] == 0: return 0

    # 5.5 Occupation
    scheme_occ = str(scheme.get('occupation_eligibility', 'all')).lower()
    if scheme_occ != 'all' and scheme_occ != 'nan' and user['occupation']:
        valid_occs = [o.strip() for o in scheme_occ.split(",")]
        u_occ = str(user['occupation']).lower()
        if not any(u_occ == o or u_occ in o or o in u_occ for o in valid_occs): return 0
    
    # 6. Advanced Fields
    urban_rural = str(scheme.get('urban_rural_eligibility', 'both')).lower()
    if urban_rural != 'both' and user['urbanRural'] != urban_rural: return 0
    
    edu_req = str(scheme.get('education_level_required', 'any')).lower()
    if edu_req != 'any' and edu_req != 'none':
        ranks = {"none":0, "primary":1, "secondary":2, "10th_pass":2, "higher_secondary":3, "graduate":4, "postgraduate":5}
        if ranks.get(user['educationLevel'], 0) < ranks.get(edu_req, 0): return 0
        
    marital_req = str(scheme.get('marital_status_required', 'any')).lower()
    if marital_req != 'any' and user['maritalStatus'] != marital_req:
        return 0
        
    if str(scheme.get('is_bpl_only', 'false')).lower() == 'true' and user['isBPL'] == 0: return 0

    return 1

def generate_data(n_users=10000, schemes_per_user=50):
    print("Loading enriched master...")
    master_df = pd.read_csv(MASTER_PATH)
    schemes = master_df.to_dict('records')
    
    dataset = []
    print(f"Generating {n_users} users...")
    
    for uid in range(n_users):
        user = _create_user()
        selected_schemes = random.sample(schemes, min(schemes_per_user, len(schemes)))
        
        for scheme in selected_schemes:
            is_eligible = check_eligibility(user, scheme)
            
            # Simple benefit score
            score = 0.5 + (0.4 if is_eligible else 0.1) * (1 - user['annualIncome']/3000000)
            score += 0.1 if user['isBPL'] else 0
            
            row = {**user, **scheme}
            row['eligible'] = is_eligible
            row['benefit_score'] = round(score, 4)
            row['group_id'] = uid
            dataset.append(row)
            
    out_df = pd.DataFrame(dataset)
    out_df.to_csv(OUT_PATH, index=False)
    print(f"✅ Success! Saved {len(out_df)} rows to {OUT_PATH}")

if __name__ == "__main__":
    generate_data(n_users=1000, schemes_per_user=40)
