import argparse
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np  # type: ignore
import pandas as pd  # type: ignore


ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "data" / "master" / "schemes_master.csv"
OUT_PATH = ROOT / "data" / "processed" / "eligibility_train.csv"


STATES = [
    "Andhra Pradesh",
    "Bihar",
    "Delhi",
    "Gujarat",
    "Haryana",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Tamil Nadu",
    "Telangana",
    "Uttar Pradesh",
    "West Bengal",
]

STATE_DISTRICTS: Dict[str, List[str]] = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur"],
    "Delhi": ["Central Delhi", "North Delhi", "South Delhi"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "Haryana": ["Gurugram", "Faridabad", "Hisar"],
    "Karnataka": ["Bengaluru", "Mysuru", "Belagavi"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Kota"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
    "West Bengal": ["Kolkata", "Howrah", "Siliguri"],
}

OCCUPATIONS = [
    "farmer",
    "student",
    "worker",
    "self_employed",
    "unemployed",
    "government_employee",
    "private_employee",
]

EDU_LEVELS = [
    "none",
    "primary",
    "secondary",
    "higher_secondary",
    "graduate",
    "postgraduate",
]


def _infer_scheme_category(name: str, fallback: str) -> str:
    text = (name or "").lower()
    if "scholarship" in text or "education" in text or "student" in text:
        return "education"
    if "health" in text or "medical" in text or "ayushman" in text:
        return "health"
    if "pension" in text or "senior" in text or "old age" in text:
        return "pension"
    if "loan" in text or "credit" in text or "mudra" in text:
        return "loan"
    if "employment" in text or "rojgar" in text or "skill" in text:
        return "employment"
    if "housing" in text or "awas" in text:
        return "housing"
    if "agri" in text or "krishi" in text or "farmer" in text:
        return "agriculture"
    return fallback if fallback and fallback != "mixed" else "general"


def _scheme_constraints(name: str, category: str) -> Tuple[int, int, int, List[str]]:
    text = (name or "").lower()
    min_age, max_age, income_limit = 18, 65, 800000
    conditions: List[str] = []

    if category == "education":
        min_age, max_age, income_limit = 16, 30, 800000
        conditions.append("student")
    elif category == "pension":
        min_age, max_age, income_limit = 55, 90, 500000
    elif category == "health":
        min_age, max_age, income_limit = 0, 90, 1200000
    elif category == "loan":
        min_age, max_age, income_limit = 21, 60, 1500000
    elif category == "employment":
        min_age, max_age, income_limit = 18, 45, 1000000
    elif category == "agriculture":
        min_age, max_age, income_limit = 18, 70, 1200000
        conditions.append("farmer")
    elif category == "housing":
        min_age, max_age, income_limit = 21, 70, 900000

    if any(k in text for k in ["women", "mahila", "girl", "balika", "maternity"]):
        conditions.append("female")
    if any(k in text for k in ["sc", "st", "tribal"]):
        conditions.append("sc_st")
    if any(k in text for k in ["obc", "backward"]):
        conditions.append("obc")
    if any(k in text for k in ["disability", "divyang"]):
        conditions.append("disability")
    if any(k in text for k in ["minority"]):
        conditions.append("minority")
    if any(k in text for k in ["rural", "gramin"]):
        conditions.append("rural")
    if any(k in text for k in ["urban", "city"]):
        conditions.append("urban")

    return min_age, max_age, income_limit, sorted(set(conditions))


def _make_user() -> Dict[str, Any]:
    state = random.choice(STATES)
    district = random.choice(STATE_DISTRICTS[state])
    
    # ML Edge Cases Injection (5% extreme population)
    if random.random() < 0.05:
        age = random.choice([16, 17, 95, 99])
        annual_income = random.choice([0, 5000, 5000000])
        family_size = random.choice([1, 10, 15])
        gender = random.choice(["male", "female"])
        category = "GEN" if annual_income > 100000 else "SC"
        minority = 1
        occupation = "unemployed" if age > 60 else "worker"
        land = 0.0 if annual_income == 0 else 5.0
        education = "none"
        disability = 1 if age > 90 else 0
        urban_rural = "rural"
    else:
        age = int(np.random.triangular(16, 29, 80))
        annual_income = int(np.random.lognormal(mean=12.3, sigma=0.7))
        annual_income = int(max(50000, min(annual_income, 2500000)))
        family_size = random.randint(1, 6)

        gender = random.choices(["male", "female", "other"], weights=[0.51, 0.48, 0.01])[0]
        category = random.choices(["GEN", "OBC", "SC", "ST"], weights=[0.33, 0.41, 0.19, 0.07])[0]
        minority = int(random.random() < 0.2)
        disability = int(random.random() < 0.08)
        urban_rural = random.choices(["urban", "rural"], weights=[0.4, 0.6])[0]

        if age <= 24 and random.random() < 0.45:
            occupation = "student"
        else:
            occupation = random.choice([o for o in OCCUPATIONS if o != "student"])

        if age < 18:
            education = random.choice(["secondary", "higher_secondary"])
        elif occupation == "student":
            education = random.choice(["higher_secondary", "graduate", "postgraduate"])
        else:
            education = random.choice(EDU_LEVELS)

        if occupation == "farmer":
            land = float(round(float(np.random.gamma(shape=2.2, scale=1.2)), 2))  # type: ignore
        else:
            land = float(round(float(np.random.gamma(shape=1.2, scale=0.4)), 2))  # type: ignore
            if random.random() < 0.7:
                land = 0.0

    return {
        "age": age,
        "annualIncome": annual_income,
        "state": state,
        "caste": category,
        "occupation": occupation,
        "gender": gender,
        "hasLand": 1 if land > 0 else 0,
        "hasDisability": disability,
        "familyIncome": annual_income,
        "hasAvailedSimilarScheme": 0,
        "landSize": land,
        "familySize": family_size,
        "isSingleGirlChild": 1 if gender == "female" and random.random() < 0.1 else 0,
        "isWidowOrSenior": 1 if (age > 60 or (gender == "female" and random.random() < 0.05)) else 0,
        "isTaxPayer": 1 if annual_income > 500000 else 0,
        "isBankLinked": 1 if random.random() < 0.9 else 0,
        "educationLevel": education,
        "digitalLiteracy": random.choice(["high", "medium", "low"]),
        "urbanRural": urban_rural,
        "monthlyExpenses": int(annual_income / 12 * 0.8),
        "hasSmartphone": 1 if random.random() < 0.8 else 0,
        "hasInternet": 1 if random.random() < 0.7 else 0,
        "employmentType": "self_employed" if occupation == "self_employed" else "salaried",
        "skillCertification": random.choice(["none", "iti", "diploma"]),
        "loanRequirement": "business" if occupation == "self_employed" else "none",
        "monthlySavings": int(annual_income / 12 * 0.2),
        "hasInsurance": 1 if random.random() < 0.3 else 0,
        "hasPension": 1 if age > 60 and random.random() < 0.4 else 0,
        "prioritySchemes": "",
    }


def _eligible(user: Dict[str, Any], scheme: Dict[str, Any]) -> int:
    if int(user["age"]) < int(scheme["min_age"]) or int(user["age"]) > int(scheme["max_age"]):
        return 0
    if int(user["annualIncome"]) > int(scheme["income_limit"]):
        return 0

    app_states = str(scheme["applicable_states"]).strip()
    if app_states and app_states.upper() != "ALL":
        states = {s.strip().lower() for s in app_states.replace("|", ",").split(",") if s.strip()}
        if states and str(user["state"]).strip().lower() not in states:
            return 0

    conditions = str(scheme["special_conditions_required"]).strip().split("|")
    conditions = [c for c in conditions if c]
    for c in conditions:
        if c == "female" and user["gender"] != "female":
            return 0
        if c == "student" and user["occupation"] != "student":
            return 0
        if c == "farmer" and user["occupation"] != "farmer":
            return 0
        if c == "disability" and user["hasDisability"] != 1:
            return 0
        if c == "rural" and user["urbanRural"] != "rural":
            return 0
        if c == "urban" and user["urbanRural"] != "urban":
            return 0
        if c == "sc_st" and user["caste"] not in {"SC", "ST"}:
            return 0
        if c == "obc" and user["caste"] != "OBC":
            return 0

    return 1


def _benefit_score(user: Dict[str, Any], scheme: Dict[str, Any], eligible: int) -> float:
    category = scheme["scheme_category"]
    base = float({
        "health": 0.82,
        "education": 0.76,
        "pension": 0.74,
        "housing": 0.72,
        "agriculture": 0.7,
        "loan": 0.68,
        "employment": 0.66,
        "general": 0.6,
    }.get(str(category), 0.6))

    income_factor = max(0.0, min(1.0, 1.0 - (float(user["annualIncome"]) / 2500000)))
    vulnerability_bonus = 0.0
    vulnerability_bonus += 0.05 if user["caste"] in {"SC", "ST"} else 0.0
    vulnerability_bonus += 0.04 if user["hasDisability"] == 1 else 0.0
    vulnerability_bonus += 0.03 if user["urbanRural"] == "rural" else 0.0

    if eligible == 0:
        score = 0.05 + 0.2 * income_factor + np.random.normal(0, 0.03)
    else:
        score = base + 0.2 * income_factor + vulnerability_bonus + np.random.normal(0, 0.04)
    return float(max(0.0, min(1.0, score)))


def _load_schemes(master_path: Path) -> pd.DataFrame:
    df = pd.read_csv(master_path)
    if df.empty:
        raise ValueError(f"No scheme rows found in {master_path}")

    out_rows = []
    for _, r in df.iterrows():
        name = str(r.get("scheme_name", "") or "")
        category = _infer_scheme_category(name, str(r.get("scheme_category", "general") or "general"))
        min_age, max_age, income_limit, cond = _scheme_constraints(name, category)

        existing_min = pd.to_numeric(r.get("min_age"), errors="coerce")
        existing_max = pd.to_numeric(r.get("max_age"), errors="coerce")
        existing_inc = pd.to_numeric(r.get("income_limit"), errors="coerce")

        out_rows.append(
            {
                "scheme_id": str(r.get("scheme_id")),
                "scheme_type": str(r.get("scheme_type") or r.get("scheme_level") or "central"),
                "scheme_category": category,
                "min_age": int(existing_min) if not math.isnan(existing_min) else min_age,
                "max_age": int(existing_max) if not math.isnan(existing_max) else max_age,
                "income_limit": int(existing_inc) if not math.isnan(existing_inc) else income_limit,
                "applicable_states": str(r.get("applicable_states") or "ALL"),
                "special_conditions_required": str(r.get("special_conditions_required") or "|".join(cond)),
                "benefit_description": str(r.get("benefit_description", "")),
            }
        )
    return pd.DataFrame(out_rows).drop_duplicates(subset=["scheme_id"])


def generate(
    master_path: Path = MASTER_PATH,
    out_path: Path = OUT_PATH,
    n_users: int = 1400,
    schemes_per_user: int = 90,
    random_seed: int = 42,
) -> pd.DataFrame:
    random.seed(random_seed)
    np.random.seed(random_seed)

    schemes = _load_schemes(master_path)
    n_scheme_rows = len(schemes)

    records = []
    for uid in range(n_users):
        user = _make_user()
        k = min(schemes_per_user, n_scheme_rows)
        chosen_idx = np.random.choice(n_scheme_rows, size=k, replace=False)
        user_rows_idx = []
        for idx in chosen_idx:
            scheme = schemes.iloc[int(idx)].to_dict()
            y = _eligible(user, scheme)
            if random.random() < 0.02:
                y = 1 - y
            b = _benefit_score(user, scheme, y)
            row = {
                **user,
                "scheme_id": scheme["scheme_id"],
                "scheme_type": scheme["scheme_type"],
                "scheme_category": scheme["scheme_category"],
                "min_age": int(scheme["min_age"]),
                "max_age": int(scheme["max_age"]),
                "income_limit": int(scheme["income_limit"]),
                "applicable_states": scheme["applicable_states"],
                "special_conditions_required": scheme["special_conditions_required"],
                "benefit_description": scheme["benefit_description"],
                "eligible": int(y),
                "benefit_score": float(round(float(b), 4)),  # type: ignore
                "priority_rank": 999,
                "group_id": uid,
            }
            records.append(row)
            user_rows_idx.append(len(records) - 1)

        eligible_rows = []
        for i in user_rows_idx:
            if int(records[i].get("eligible", 0)) == 1:  # type: ignore
                eligible_rows.append(i)

        eligible_rows.sort(key=lambda i: float(records[i].get("benefit_score", 0.0)), reverse=True)  # type: ignore
        for rank, ridx in enumerate(eligible_rows, start=1):
            records[ridx].update({"priority_rank": rank})  # type: ignore

    out_df = pd.DataFrame(records)
    out_df.sort_values(["group_id"], inplace=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False, encoding="utf-8")
    return out_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic eligibility training dataset.")
    parser.add_argument("--master-path", default=str(MASTER_PATH))
    parser.add_argument("--out-path", default=str(OUT_PATH))
    parser.add_argument("--n-users", type=int, default=10000)
    parser.add_argument("--schemes-per-user", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = generate(
        master_path=Path(args.master_path),
        out_path=Path(args.out_path),
        n_users=args.n_users,
        schemes_per_user=args.schemes_per_user,
        random_seed=args.seed,
    )
    print(f"Generated {len(df)} rows at {args.out_path}")
    print(f"Eligible rate: {df['eligible'].mean():.4f}")

