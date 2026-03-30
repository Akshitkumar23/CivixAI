from __future__ import annotations

# Trigger reload for new model schemas
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

from utils import engineer_features  # type: ignore


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
    knowledge_graph: List[Dict[str, Any]]  # New field for related schemes


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
            "gender_eligibility": row.get("gender_eligibility", "all"),
            "caste_eligibility": row.get("caste_eligibility", "all"),
            "disability_required": row.get("disability_required", "false"),
            "occupation_eligibility": row.get("occupation_eligibility", "all"),
            "education_level_required": row.get("education_level_required", "any"),
            "urban_rural_eligibility": row.get("urban_rural_eligibility", "both"),
            "marital_status_required": row.get("marital_status_required", "any"),
            "employment_type_eligibility": row.get("employment_type_eligibility", "any"),
            "is_bpl_only": row.get("is_bpl_only", "false"),
            "popularity_score": row.get("popularity_score", "5.0"),
        }
        combined = {**user_dict, **scheme_row}
        rows.append(combined)
    return pd.DataFrame(rows)


def normalize_feature_frame(X: pd.DataFrame, schema: Dict[str, Any]) -> pd.DataFrame:
    X = engineer_features(X)
    
    feature_defs = schema.get("features", [])
    feature_names = [f["name"] for f in feature_defs] if feature_defs else list(X.columns)
    categorical = set(schema.get("categorical", []))
    text_cols = set()

    for col in feature_names:
        if col not in X.columns:
            X[col] = np.nan

    X = X[feature_names].copy()

    for col in X.columns:
        if col in categorical or col in text_cols:
            X[col] = X[col].fillna("").astype(str)
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0.0)
    return X


def rule_based_explain(user: UserProfile, scheme: Dict[str, Any]) -> Dict[str, Any]:
    reasons = []
    missing = []
    eligible = True
    hard_reject = False
    match_score = 0.80
    path_to_eligibility = []

    # Helper: Check numeric limit safely
    def check_limit(val, limit, field_name, is_max=True):
        if limit is None or np.isnan(float(limit)): return True, 0
        limit = float(limit)
        if val is None:
            if field_name not in missing: missing.append(field_name)
            return True, 0 # Keep eligible for now, but flag as missing
        
        if is_max:
            if val > limit: return False, limit
        else:
            if val < limit: return False, limit
        return True, 0

    # 1. Complex Age & Income Solver
    ok_age, limit_age = check_limit(user.age, scheme.get("min_age"), "age", is_max=False)
    if not ok_age:
        eligible = False
        reasons.append(f"Age criteria not met (Min: {int(limit_age)} years)")
        # Negotiation Step
        if (user.age or 0) >= int(limit_age) - 2:
            path_to_eligibility.append(f"Almost at the age limit. Check if age relaxation applies for your category (SC/ST/OBC).")
    
    ok_age_max, limit_age_max = check_limit(user.age, scheme.get("max_age"), "age", is_max=True)
    if not ok_age_max:
        eligible = False
        reasons.append(f"Age threshold exceeded (Max: {int(limit_age_max)} years)")

    ok_inc, limit_inc = check_limit(user.annualIncome, scheme.get("income_limit"), "annualIncome", is_max=True)
    if not ok_inc:
        eligible = False
        reasons.append(f"Income exceeds limit (Limit: ₹{int(limit_inc)})")
        # AI Negotiation (#30)
        gap = (user.annualIncome or 0) - limit_inc
        if gap <= limit_inc * 0.25:
            path_to_eligibility.append(f"Income slightly exceeds ₹{int(limit_inc)}. Check for legal deductions or apply via EWS.")

    # 2. Smart Condition Logic (Graph-like Branching)
    name_text = str(scheme.get("scheme_name", "")).lower()
    desc_text = str(scheme.get("benefit_description", "")).lower()
    combined_text = f"{name_text} {desc_text}".lower()

    # Small/Marginal Farmer Check (Logic Branch)
    if any(k in combined_text for k in ["farmer", "smf", "marginal", "kisan", "agriculture", "krishi", "kheti", "kisani"]):
        if str(user.occupation).lower().strip() != "farmer" and not user.hasLand:
            eligible = False
            hard_reject = True
            reasons.append("Strictly for Farmers / Agricultural Activities")
        elif (user.landSize or 0) > 2.0 and ("small" in combined_text or "marginal" in combined_text):
            eligible = False
            hard_reject = True
            reasons.append("Land size exceeds Small/Marginal Farmer threshold")
        else:
            match_score += 0.15

    # Student / Scholarship Check
    if any(k in combined_text for k in ["student", "scholar", "scholarship", "fellowship", "school", "education"]):
        if str(user.occupation).lower().strip() not in ["student", "unemployed"]:
            eligible = False
            hard_reject = True
            reasons.append("Strictly for Students / Education")
        else:
            match_score += 0.15

    # Single Girl Child / Minority / Caste (Branching OR logic)
    if "minority" in combined_text:
        is_minority = str(user.caste or "").lower() in ["muslim", "sikh", "christian", "jain", "buddhist", "parsi", "minority"]
        if not is_minority:
            eligible = False
            hard_reject = True
            reasons.append("Scheme intended for Minority communities")
        else:
            match_score += 0.10

    if any(k in combined_text for k in ["scheduled caste", " sc ", "st/sc", "sc/st", "harijan"]):
        if str(user.caste or "").lower().strip() not in ["sc", "scheduled caste"]:
            eligible = False
            hard_reject = True
            reasons.append("Reserved for SC category applicants")

    if any(k in combined_text for k in ["scheduled tribe", " st ", "st/sc", "sc/st", "adivasi"]):
        if str(user.caste or "").lower().strip() not in ["st", "scheduled tribe"]:
            eligible = False
            hard_reject = True
            reasons.append("Reserved for ST category applicants")

    if any(k in combined_text for k in ["obc", "backward class"]):
        if str(user.caste or "").lower().strip() not in ["obc", "other backward class"]:
            eligible = False
            hard_reject = True
            reasons.append("Reserved for OBC category applicants")

    if any(k in combined_text for k in ["disability", "disabled", "pwd", "handicap", "divyang", "blind"]):
        if user.hasDisability is False:
            eligible = False
            hard_reject = True
            reasons.append("Reserved for persons with disabilities (PwD)")

    if "girl" in combined_text or "daughter" in combined_text or "women" in combined_text or "mother" in combined_text or "maternity" in combined_text:
        if str(user.gender or "").lower() == "male":
            eligible = False
            hard_reject = True
            reasons.append("Reserved for female applicants only")
        elif user.isSingleGirlChild:
            match_score += 0.20 
            reasons.append("Matched via Single Girl Child quota")
        else:
            path_to_eligibility.append("Obtain an 'Affidavit for Single Girl Child' from a First Class Magistrate to claim this quota.")

    # Education-level filtering
    if "graduate" in combined_text or "degree" in combined_text:
        edu = str(user.educationLevel or "").lower()
        if edu not in ["graduate", "post_graduate", "phd"]:
            eligible = False
            reasons.append("Completion of a Graduate degree is mandatory")
            path_to_eligibility.append("If currently in final year, checking for 'Awaiting Results' provision in manual guidelines.")

    # Document-based Negotiation (#30)
    docs_required = str(scheme.get("documents_required", "")).lower()
    if "aadhaar" in docs_required and not user.state: # Dummy check for missing state
         path_to_eligibility.append("Ensure your Aadhaar is linked to your current mobile number for e-KYC.")
    if "caste" in docs_required:
         path_to_eligibility.append("Apply for a digital Caste Certificate on your state's Saral/e-District portal.")

    # 3. Strict Schema Core Restrictions (Gender, Occupation, Disability, Caste)
    # Gender Limitation
    req_gender = str(scheme.get("gender_eligibility", "all")).lower().strip()
    if req_gender and req_gender not in ["all", "nan", "any"] and user.gender:
        if req_gender != str(user.gender).lower().strip():
            eligible = False
            hard_reject = True
            reasons.append(f"Reserved for {req_gender.capitalize()} applicants only")

    # Occupation Limitation
    req_occ = str(scheme.get("occupation_eligibility", "all")).lower().strip()
    if req_occ and req_occ not in ["all", "nan", "any"] and user.occupation:
        valid_occs = [o.strip() for o in req_occ.split(",") if o.strip()]
        u_occ = str(user.occupation).lower().strip()
        if not any(u_occ == o or u_occ in o or o in u_occ for o in valid_occs):
            eligible = False
            hard_reject = True
            reasons.append(f"Occupation requirement not met. Required: {req_occ.title()}")

    # Category/Caste Check
    req_caste = str(scheme.get("caste_eligibility", "all")).lower().strip()
    if req_caste and req_caste not in ["all", "nan", "any"] and user.caste:
        valid_castes = [c.strip() for c in req_caste.split(",") if c.strip()]
        u_caste = str(user.caste).lower().strip()
        if not any(u_caste == c or u_caste in c for c in valid_castes):
            eligible = False
            hard_reject = True
            reasons.append(f"Scheme restricted to specific categories: {req_caste.upper()}")

    # Disability Check
    if str(scheme.get("disability_required", "false")).lower().strip() == "true":
        if user.hasDisability is False:
            eligible = False
            hard_reject = True
            reasons.append(f"Reserved for persons with disabilities (PwD)")
        elif user.hasDisability is None:
            if "hasDisability" not in missing: missing.append("hasDisability")

    if eligible and not reasons:
        reasons.append("Matches demographic profile and criteria")

    return {
        "eligible_rules": eligible, 
        "hard_reject": hard_reject,
        "reasons": reasons, 
        "missing": list(set(missing)), 
        "match_score": min(1.0, match_score),
        "path_to_eligibility": path_to_eligibility
    }


@app.on_event("startup")
def startup():
    app.state.eligibility_model, app.state.benefit_model, app.state.schema = load_models()
    app.state.schemes = load_schemes()
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _append_shadow_log(payload: Dict[str, Any]) -> None:
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(SHADOW_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


class FeedbackEvent(BaseModel):
    user_id: Optional[str] = None
    scheme_id: str
    accepted: int

@app.post("/api/feedback")
def submit_feedback(feedback: FeedbackEvent):
    payload = feedback.model_dump()
    payload["event_type"] = "click_feedback"
    _append_shadow_log(payload)
    return {"status": "recorded"}


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
        
        # Rule-based eligible schemes always pass. 
        # Only allow ML predictions if there's a practical pathway to becoming eligible
        has_pathway = len(explanation.get("path_to_eligibility", [])) > 0
        hard_reject = explanation.get("hard_reject", False)
        is_truly_eligible = rule_eligible or (has_pathway and ml_prob > 0.40 and not hard_reject)
        
        if not is_truly_eligible:
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
                "path_to_eligibility": explanation.get("path_to_eligibility", []),
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
        
        rule_eligible = explanation["eligible_rules"]
        ml_prob = probs[i]
        match_score = explanation["match_score"]
        has_pathway = len(explanation.get("path_to_eligibility", [])) > 0
        hard_reject = explanation.get("hard_reject", False)
        
        # ---------------------------------------------------------
        # AI Strategic Directive Layer (#25)
        # ---------------------------------------------------------
        directive_boost = 1.0
        directives_path = DATA_DIR / "master" / "policy_directives.json"
        
        if directives_path.exists():
            try:
                with open(directives_path, "r", encoding="utf-8") as f:
                    policy_data = json.load(f)
                    for ad in policy_data.get("active_directives", []):
                        # Match Location
                        state_match = "all" in [s.lower() for s in ad.get("target_states", [])] or \
                                      (user.state and user.state.lower() in [s.lower() for s in ad.get("target_states", [])])
                        
                        if state_match:
                            # Match Semantic Tags / Keywords
                            keywords = [k.lower() for k in ad.get("keywords", [])]
                            scheme_text = f"{scheme_dict.get('scheme_name', '')} {scheme_dict.get('tags', '')} {scheme_dict.get('scheme_category', '')}".lower()
                            
                            if any(k in scheme_text for k in keywords):
                                directive_boost = max(directive_boost, float(ad.get("boost_factor", 1.0)))
            except:
                pass

        # Include if truly eligible OR if there's a legal pathway to become eligible
        is_candidate = rule_eligible or (has_pathway and ml_prob > 0.40 and not hard_reject)
        
        if not is_candidate:
            continue
        
        # Blend ML probability with deterministic heuristic match_score
        if rule_eligible:
            penalty = len(explanation["missing"]) * 0.05
            base_score = max(0.90, match_score) - penalty
            blended_prob = min(1.0, float(base_score + (ml_prob * 0.10)))
        else:
            base = 0.50 if has_pathway else (0.20 + (match_score * 0.4))
            blended_prob = float(base + (ml_prob * 0.3) - (len(explanation["missing"]) * 0.08))
            blended_prob = max(0.10, min(0.99, blended_prob))

        # Multi-objective Optimization: Max(Benefit) + Min(Effort/Docs) + Max(Confidence)
        doc_list = str(scheme_dict.get("documents_required", "")).split(",")
        effort_penalty = len(doc_list) * 0.02 # Small penalty for each document
        
        # RL Influence: Popularity Score (#22)
        pop_score = float(scheme_dict.get("popularity_score", 5.0))
        pop_multiplier = 0.8 + (pop_score / 25.0) # 5.0 -> 1.0 multiplier
        
        score = float(blended_prob * float(benefit_scores[i]))
        score = score * (1.1 - min(0.3, effort_penalty)) # Optimization for less effort
        score = score * pop_multiplier # Reinforcement Learning Boost
        score = score * directive_boost # AI Strategic Directive Boost (#25)
        
        if rule_eligible:
            score *= 1.4 # High bonus for meeting all deterministic rules
            
        # Clean Description logic
        raw_desc = str(scheme_dict.get("benefit_description", ""))
        custom_desc = ""
        if "This education program aims" in raw_desc or raw_desc in ["", "nan", "None"]:
            ministry = str(scheme_dict.get('ministry', 'India'))
            ministry = ministry.replace("Department of ", "").replace("Ministry of ", "")
            category = str(scheme_dict.get('scheme_category', 'general')).title()
            custom_desc = f"A {category} initiative by {ministry} offering direct benefits, financial aid, or relevant services to eligible candidates."
        else:
            custom_desc = raw_desc[:150] + "..." if len(raw_desc) > 150 else raw_desc
        
        entry = {
            "scheme_id": scheme_dict.get("scheme_id"),
            "name": scheme_dict.get("scheme_name", scheme_dict.get("scheme_id")),
            "eligible": True,
            "confidence": blended_prob,
            "benefit_score": float(benefit_scores[i]),
            "rank_score": score,
            "category": scheme_dict.get("scheme_category", "General"),
            "description": custom_desc,
            "ministry": scheme_dict.get("ministry", "Central Government"),
            "level": scheme_dict.get("scheme_level", "central"),
            "url": scheme_dict.get("application_url", ""),
            "documents": str(scheme_dict.get("documents_required", "")),
            "reasons": explanation["reasons"],
            "missing": explanation["missing"],
            "benefit_type": scheme_dict.get("benefit_type", "scheme"),
            "benefit_amount": str(scheme_dict.get("benefit_amount", "")),
            "tags": str(scheme_dict.get("tags", "")),
            "application_deadline": str(scheme_dict.get("application_deadline", "")),
            "processing_time": str(scheme_dict.get("processing_time", "")),
            "popularity_score": str(scheme_dict.get("popularity_score", "5.0")),
            "path_to_eligibility": explanation.get("path_to_eligibility", []),
        }
        ranked.append(entry)
        # ... (rest of metadata)
        benefits.append({"scheme_id": entry["scheme_id"], "benefit_score": entry["benefit_score"]})
        docs.append({"scheme_id": entry["scheme_id"], "documents_required": entry["documents"], "application_url": entry["url"]})
        why.append({"scheme_id": entry["scheme_id"], "reasons": entry["reasons"], "eligible_by_rules": rule_eligible, "missing": entry["missing"], "path_to_eligibility": entry["path_to_eligibility"]})

    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    limit = 500
    # Use standard slicing which is safer for type checkers
    top_ranked = [ranked[i] for i in range(min(len(ranked), limit))]
    top_benefits = [benefits[i] for i in range(min(len(benefits), limit))]
    top_docs = [docs[i] for i in range(min(len(docs), limit))]
    top_why = [why[i] for i in range(min(len(why), limit))]

    # Knowledge Graph (Link related schemes)
    knowledge_graph = []
    for s in top_ranked:
        related = [
            {"id": rs["scheme_id"], "name": rs["name"]} 
            for rs in top_ranked 
            if rs["scheme_id"] != s["scheme_id"] and rs["category"] == s["category"]
        ][:3]
        knowledge_graph.append({"scheme_id": s["scheme_id"], "related": related})

    return {
        "ranked_schemes": top_ranked,
        "benefit_estimates": top_benefits,
        "required_documents": top_docs,
        "why_this_scheme": top_why,
        "knowledge_graph": knowledge_graph,
    }
