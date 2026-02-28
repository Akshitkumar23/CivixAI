from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field


APP_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = APP_ROOT / "ml" / "models"
DATA_DIR = APP_ROOT.parent / "data"
MASTER_PATH = DATA_DIR / "master" / "schemes_master.csv"
ML_SRC_DIR = APP_ROOT / "ml"
LOG_DIR = DATA_DIR / "logs"
SHADOW_LOG_PATH = LOG_DIR / "shadow_logs.jsonl"

if str(ML_SRC_DIR) not in sys.path:
    sys.path.append(str(ML_SRC_DIR))


class UserProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    age: Optional[int] = None
    annualIncome: Optional[int] = Field(default=None, alias="annual_income")
    state: Optional[str] = None
    caste: Optional[str] = Field(default=None, alias="category")
    occupation: Optional[str] = None
    gender: Optional[str] = None
    hasLand: Optional[bool] = Field(default=None, alias="has_land")
    hasDisability: Optional[bool] = Field(default=None, alias="has_disability")
    familyIncome: Optional[int] = Field(default=None, alias="family_income")
    hasAvailedSimilarScheme: Optional[bool] = Field(default=None, alias="has_availed_similar_scheme")
    landSize: Optional[float] = Field(default=None, alias="land_size")
    familySize: Optional[int] = Field(default=None, alias="family_size")
    isSingleGirlChild: Optional[bool] = Field(default=None, alias="is_single_girl_child")
    isWidowOrSenior: Optional[bool] = Field(default=None, alias="is_widow_or_senior")
    isTaxPayer: Optional[bool] = Field(default=None, alias="is_tax_payer")
    isBankLinked: Optional[bool] = Field(default=None, alias="is_bank_linked")
    educationLevel: Optional[str] = Field(default=None, alias="education_level")
    digitalLiteracy: Optional[str] = Field(default=None, alias="digital_literacy")
    urbanRural: Optional[str] = Field(default=None, alias="urban_rural")
    monthlyExpenses: Optional[int] = Field(default=None, alias="monthly_expenses")
    hasSmartphone: Optional[bool] = Field(default=None, alias="has_smartphone")
    hasInternet: Optional[bool] = Field(default=None, alias="has_internet")
    employmentType: Optional[str] = Field(default=None, alias="employment_type")
    skillCertification: Optional[str] = Field(default=None, alias="skill_certification")
    loanRequirement: Optional[str] = Field(default=None, alias="loan_requirement")
    monthlySavings: Optional[int] = Field(default=None, alias="monthly_savings")
    hasInsurance: Optional[bool] = Field(default=None, alias="has_insurance")
    hasPension: Optional[bool] = Field(default=None, alias="has_pension")
    prioritySchemes: Optional[Any] = Field(default=None, alias="priority_schemes")


class EligibilityResponse(BaseModel):
    eligible_schemes: List[Dict[str, Any]]
    eligibility_reasoning: List[Dict[str, Any]]
    missing_criteria: List[Dict[str, Any]]
    confidence_score: float


class RecommendationResponse(BaseModel):
    ranked_schemes: List[Dict[str, Any]]
    benefit_estimates: List[Dict[str, Any]]
    required_documents: List[Dict[str, Any]]
    why_this_scheme: List[Dict[str, Any]]


app = FastAPI(title="CivixAI ML Service")


def _safe_json(value: Any) -> Any:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if not isinstance(value, str):
        return value
    v = value.strip()
    if not v:
        return None
    if (v.startswith("[") and v.endswith("]")) or (v.startswith("{") and v.endswith("}")):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return value
    return value


def _normalize_states(value: Any) -> List[str]:
    parsed = _safe_json(value)
    if parsed is None:
        return []
    if isinstance(parsed, list):
        return [str(x).strip().lower() for x in parsed if str(x).strip()]
    if isinstance(parsed, str):
        parts = [p.strip().lower() for p in parsed.replace("|", ",").split(",")]
        return [p for p in parts if p]
    return []


def load_models():
    eligibility_model = joblib.load(MODELS_DIR / "eligibility_model.pkl")
    benefit_model = joblib.load(MODELS_DIR / "benefit_model.pkl")
    schema_path = MODELS_DIR / "feature_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else {}
    return eligibility_model, benefit_model, schema


def load_schemes() -> pd.DataFrame:
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing schemes master: {MASTER_PATH}")
    df = pd.read_csv(MASTER_PATH)
    # Normalize expected columns
    if "scheme_level" in df.columns and "scheme_type" not in df.columns:
        df["scheme_type"] = df["scheme_level"]
    if "scheme_category" not in df.columns:
        df["scheme_category"] = "general"
    if "min_age" not in df.columns:
        df["min_age"] = np.nan
    if "max_age" not in df.columns:
        df["max_age"] = np.nan
    if "income_limit" not in df.columns:
        df["income_limit"] = np.nan
    if "applicable_states" not in df.columns:
        df["applicable_states"] = ""
    if "special_conditions_required" not in df.columns:
        df["special_conditions_required"] = ""
    if "ministry" not in df.columns:
        df["ministry"] = ""
    return df


def build_feature_rows(user: UserProfile, schemes: pd.DataFrame) -> pd.DataFrame:
    user_dict = user.model_dump()
    rows = []
    for _, row in schemes.iterrows():
        scheme_row = {
            "scheme_id": row.get("scheme_id"),
            "scheme_type": row.get("scheme_type"),
            "scheme_category": row.get("scheme_category"),
            "min_age": row.get("min_age"),
            "max_age": row.get("max_age"),
            "income_limit": row.get("income_limit"),
            "applicable_states": row.get("applicable_states"),
            "special_conditions_required": row.get("special_conditions_required"),
        }
        combined = {**user_dict, **scheme_row}
        rows.append(combined)
    return pd.DataFrame(rows)


def normalize_feature_frame(X: pd.DataFrame, schema: Dict[str, Any]) -> pd.DataFrame:
    feature_defs = schema.get("features", [])
    feature_names = [f["name"] for f in feature_defs] if feature_defs else list(X.columns)
    categorical = set(schema.get("categorical", []))

    for col in feature_names:
        if col not in X.columns:
            X[col] = np.nan

    X = X[feature_names].copy()

    for col in X.columns:
        if col in categorical:
            X[col] = X[col].fillna("").astype(str)
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)
    return X


def rule_based_explain(user: UserProfile, scheme: Dict[str, Any]) -> Dict[str, Any]:
    reasons = []
    missing = []
    eligible = True

    # 1. Age check
    if scheme.get("min_age") is not None and not np.isnan(scheme.get("min_age", np.nan)):
        if user.age is None:
            missing.append("age")
        elif user.age < scheme["min_age"]:
            eligible = False
            reasons.append(f"Umar kam hai (Min: {scheme['min_age']})")
    if scheme.get("max_age") is not None and not np.isnan(scheme.get("max_age", np.nan)):
        if user.age is None:
            missing.append("age")
        elif user.age > scheme["max_age"]:
            eligible = False
            reasons.append(f"Umar zyada hai (Max: {scheme['max_age']})")

    # 2. Income check
    if scheme.get("income_limit") is not None and not np.isnan(scheme.get("income_limit", np.nan)):
        if user.annualIncome is None:
            missing.append("annualIncome")
        elif user.annualIncome > scheme["income_limit"]:
            eligible = False
            reasons.append(f"Aay zyada hai (Limit: {scheme['income_limit']})")

    # 3. State check
    states = _normalize_states(scheme.get("applicable_states"))
    if states:
        if not user.state:
            missing.append("state")
        else:
            state_val = str(user.state).strip().lower()
            if state_val not in states:
                eligible = False
                reasons.append("Aapka rajya (state) match nahi karta")

    # 4. Keyword-based Hard Rejection (Occupation & Gender)
    name_text = str(scheme.get("scheme_name", "")).lower()
    desc_text = str(scheme.get("benefit_description", "")).lower()
    cat_text = str(scheme.get("scheme_category", "")).lower()
    combined_text = name_text + " " + desc_text + " " + cat_text

    # Gender Check
    if "women" in combined_text or "female" in combined_text or "mahila" in combined_text or "girl" in combined_text:
        if str(user.gender or "").lower() == "male":
            eligible = False
            reasons.append("Sirf mahilaon (women) ke liye")
    
    # 5. Caste/Category Check
    user_caste = str(user.category or "").lower()
    if "sc" in combined_text or "scheduled caste" in combined_text:
        if user_caste != "sc":
            eligible = False
            reasons.append("Sirf SC category ke liye")
    elif "st" in combined_text or "scheduled tribe" in combined_text:
        if user_caste != "st":
            eligible = False
            reasons.append("Sirf ST category ke liye")
    elif "obc" in combined_text or "backward class" in combined_text:
        if user_caste not in ["obc", "sc", "st"]: # Usually SC/ST are eligible for OBC schemes too, but OBC is strict
            eligible = False
            reasons.append("Sirf OBC category ke liye")

    # Occupation Check
    farmer_keywords = ["farmer", "kisan", "krishi", "agriculture", "cultivator"]
    if any(k in combined_text for k in farmer_keywords):
        if str(user.occupation or "").lower() == "student":
            eligible = False
            reasons.append("Sirf kisano (farmers) ke liye")
    
    student_keywords = ["student", "scholarship", "education", "padhai", "shiksha"]
    if any(k in combined_text for k in student_keywords):
        if str(user.occupation or "").lower() == "farmer":
            eligible = False
            # Allow farmers to have education schemes if they are young, but usually they are distinct
            pass

    if eligible and not reasons:
        reasons.append("Aapke profile ke hisaab se fit hai")

    return {"eligible_rules": eligible, "reasons": reasons, "missing": list(set(missing))}


@app.on_event("startup")
def startup():
    app.state.eligibility_model, app.state.benefit_model, app.state.schema = load_models()
    app.state.schemes = load_schemes()
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _append_shadow_log(payload: Dict[str, Any]) -> None:
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(SHADOW_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


@app.post("/api/check-eligibility", response_model=EligibilityResponse)
def check_eligibility(user: UserProfile):
    schemes = app.state.schemes
    X = build_feature_rows(user, schemes)
    X = normalize_feature_frame(X, app.state.schema)
    model = app.state.eligibility_model

    probs = model.predict_proba(X)[:, 1]
    threshold = 0.6  # minimize false positives
    eligible_mask = probs >= threshold

    eligible_schemes = []
    eligibility_reasoning = []
    missing_criteria = []
    ml_prediction = []

    for i, row in schemes.iterrows():
        scheme_dict = row.to_dict()
        explanation = rule_based_explain(user, scheme_dict)
        
        rule_eligible = explanation["eligible_rules"]
        ml_prob = probs[i]
        
        # Consistent logic with recommend endpoint
        is_truly_eligible = rule_eligible or (ml_prob > 0.95)
        
        if not is_truly_eligible or ml_prob < 0.70: # slightly lower threshold for quick check
            continue

        payload = {
            "scheme_id": scheme_dict.get("scheme_id"),
            "scheme_name": scheme_dict.get("scheme_name", scheme_dict.get("scheme_id")),
            "eligible": True,
            "confidence": float(ml_prob),
            "threshold": threshold,
        }
        eligible_schemes.append(payload)
        ml_prediction.append(payload)
        eligibility_reasoning.append(
            {
                "scheme_id": payload["scheme_id"],
                "reasons": explanation["reasons"],
                "eligible_by_rules": rule_eligible,
            }
        )
        if explanation["missing"]:
            missing_criteria.append(
                {"scheme_id": payload["scheme_id"], "missing": explanation["missing"]}
            )

    confidence_score = float(np.mean(probs)) if len(probs) else 0.0

    _append_shadow_log(
        {
            "input": user.model_dump(),
            "rule_output": eligibility_reasoning,
            "ml_prediction": ml_prediction,
            "confidence": confidence_score,
        }
    )

    return {
        "eligible_schemes": eligible_schemes,
        "eligibility_reasoning": eligibility_reasoning,
        "missing_criteria": missing_criteria,
        "confidence_score": confidence_score,
    }


@app.post("/api/recommend", response_model=RecommendationResponse)
def recommend(user: UserProfile):
    schemes = app.state.schemes
    X = build_feature_rows(user, schemes)
    X = normalize_feature_frame(X, app.state.schema)
    eligibility_model = app.state.eligibility_model
    benefit_model = app.state.benefit_model

    probs = eligibility_model.predict_proba(X)[:, 1]
    benefit_scores = benefit_model.predict(X)
    threshold = 0.6

    ranked = []
    benefits = []
    docs = []
    why = []

    for i, row in schemes.iterrows():
        scheme_dict = row.to_dict()
        explanation = rule_based_explain(user, scheme_dict)
        
        # Hard constraint: If rule-based says ineligible AND ML confidence is not extremely high, reject.
        rule_eligible = explanation["eligible_rules"]
        ml_prob = probs[i]
        
        # We only consider it truly eligible if it passes rules, OR if ML is 95%+ sure
        is_truly_eligible = rule_eligible or (ml_prob > 0.95)
        
        # High threshold for detailed view
        if not is_truly_eligible or ml_prob < 0.75:
            continue

        score = float(ml_prob * float(benefit_scores[i]))
        if rule_eligible:
            score *= 1.3 # Higher bonus for meeting all rules
        
        entry = {
            "scheme_id": scheme_dict.get("scheme_id"),
            "name": scheme_dict.get("scheme_name", scheme_dict.get("scheme_id")),
            "eligible": True,
            "confidence": float(ml_prob),
            "benefit_score": float(benefit_scores[i]),
            "rank_score": score,
            "category": scheme_dict.get("scheme_category", "General"),
            "description": scheme_dict.get("benefit_description", scheme_dict.get("benefits", "")),
            "url": scheme_dict.get("application_url", ""),
            "documents": str(scheme_dict.get("documents_required", "")),
            "reasons": explanation["reasons"],
            "missing": explanation["missing"]
        }
        ranked.append(entry)
        # ... (rest of metadata)
        benefits.append({"scheme_id": entry["scheme_id"], "benefit_score": entry["benefit_score"]})
        docs.append({"scheme_id": entry["scheme_id"], "documents_required": entry["documents"], "application_url": entry["url"]})
        why.append({"scheme_id": entry["scheme_id"], "reasons": entry["reasons"], "eligible_by_rules": rule_eligible, "missing": entry["missing"]})

    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    limit = 50
    # Use standard slicing which is safer for type checkers
    top_ranked = [ranked[i] for i in range(min(len(ranked), limit))]
    top_benefits = [benefits[i] for i in range(min(len(benefits), limit))]
    top_docs = [docs[i] for i in range(min(len(docs), limit))]
    top_why = [why[i] for i in range(min(len(why), limit))]

    return {
        "ranked_schemes": top_ranked,
        "benefit_estimates": top_benefits,
        "required_documents": top_docs,
        "why_this_scheme": top_why,
    }
