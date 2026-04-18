from __future__ import annotations

"""
CivixAI Production ML Service — FastAPI Entry Point
====================================================
Refactored to use the modular 5-agent pipeline:
  Stage 1  InputAgent         — validate & clean user input
  Stage 2  EligibilityEngine  — hard rules + CatBoost ML ranking
  Stage 3  RetrievalAgent     — keyword + optional FAISS retrieval
  Stage 4  ReasoningAgent     — personalised GenAI explanations
  Stage 5  OutputAgent        — format final JSON for frontend
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

# ── Ensure project root is first on sys.path ──────────────────────────────────
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) in sys.path:
    sys.path.remove(str(root_dir))
sys.path.insert(0, str(root_dir))

# Load .env early so services have API keys
load_dotenv(dotenv_path=str(root_dir / ".env"))

# ── Path constants ─────────────────────────────────────────────────────────────
APP_ROOT       = Path(__file__).resolve().parent.parent
MODELS_DIR     = Path(__file__).resolve().parent / "models"
DATA_DIR       = APP_ROOT.parent / "data"
MASTER_PATH    = DATA_DIR / "master" / "schemes_master.csv"
ML_SRC_DIR     = APP_ROOT / "ml"
LOG_DIR        = DATA_DIR / "logs"
SHADOW_LOG_PATH= LOG_DIR / "shadow_logs.jsonl"
DIRECTIVES_PATH= DATA_DIR / "master" / "policy_directives.json"
FAISS_INDEX    = DATA_DIR / "master" / "schemes.index"

if str(ML_SRC_DIR) not in sys.path:
    sys.path.append(str(ML_SRC_DIR))

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("civixai.main")

# ── Import existing services (used by the agents) ─────────────────────────────
from services.ml_api.services.eligibility import EligibilityService  # type: ignore
from services.ml_api.services.ranking     import RankingService       # type: ignore
from services.ml_api.services.benefit     import BenefitService       # type: ignore
from services.ml_api.services.behavior    import BehaviorService      # type: ignore
from services.ml_api.services.genai       import PersonalizedGenAIService  # type: ignore
from services.ml_api.agents              import AgentPipeline          # type: ignore
from utils import engineer_features                                    # type: ignore


# ── Pydantic Models ────────────────────────────────────────────────────────────
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
    maritalStatus: Optional[str] = Field(default=None, alias="marital_status")
    isBPL: Optional[bool] = Field(default=None, alias="is_bpl")
    isMinority: Optional[bool] = Field(default=None, alias="is_minority")
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
    knowledge_graph: List[Dict[str, Any]]


from prometheus_fastapi_instrumentator import Instrumentator

# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CivixAI Production ML Service",
    description="Modular 5-agent pipeline for Indian government scheme recommendations.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app)



# ── Startup ────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    logger.info("⚙️  CivixAI startup — loading models and initialising agents...")

    # Load ML models
    eligibility_model = joblib.load(MODELS_DIR / "eligibility_model.pkl")
    benefit_model     = joblib.load(MODELS_DIR / "benefit_model.pkl")
    schema_path = MODELS_DIR / "feature_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else {}

    # Load schemes master
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing schemes master: {MASTER_PATH}")
    schemes = pd.read_csv(MASTER_PATH)
    for col in [
        "scheme_id", "scheme_name", "ministry", "scheme_level", "scheme_type",
        "scheme_category", "min_age", "max_age", "income_limit",
        "applicable_states", "benefit_amount", "benefit_description",
        "documents_required", "application_url", "gender_eligibility",
        "caste_eligibility", "occupation_eligibility",
    ]:
        if col not in schemes.columns:
            schemes[col] = np.nan

    # Load policy directives
    directives = {}
    if DIRECTIVES_PATH.exists():
        with open(DIRECTIVES_PATH, "r", encoding="utf-8") as f:
            directives = json.load(f)

    # Instantiate existing services
    eligibility_service = EligibilityService(eligibility_model, schema)
    ranking_service     = RankingService(directives)
    benefit_service     = BenefitService()
    behavior_service    = BehaviorService(SHADOW_LOG_PATH)
    genai_service       = PersonalizedGenAIService()

    # ── Build the agent pipeline ───────────────────────────────────────────────
    pipeline = AgentPipeline(
        eligibility_service=eligibility_service,
        ranking_service=ranking_service,
        benefit_service=benefit_service,
        ml_model=eligibility_model,
        benefit_model=benefit_model,
        schema=schema,
        build_features_fn=build_feature_rows,
        normalize_fn=normalize_feature_frame,
        schemes_df=schemes,
        genai_service=genai_service,
        faiss_index_path=str(FAISS_INDEX),
        top_k=10,
    )

    # Store in app state (shared across requests)
    app.state.pipeline        = pipeline
    app.state.schemes         = schemes
    app.state.schema          = schema
    app.state.eligibility_model = eligibility_model
    app.state.benefit_model   = benefit_model
    app.state.behavior_service= behavior_service
    app.state.genai_service   = genai_service

    logger.info("✅ CivixAI startup complete — 5-agent pipeline ready.")


# ── Helper functions (reused by pipeline) ─────────────────────────────────────
def build_feature_rows(user: Any, schemes: pd.DataFrame) -> pd.DataFrame:
    user_dict = user.model_dump() if hasattr(user, "model_dump") else dict(user._d)
    rows = []
    for _, row in schemes.iterrows():
        scheme_row = {
            "scheme_id":          row.get("scheme_id"),
            "scheme_type":        row.get("scheme_type", "central"),
            "scheme_category":    row.get("scheme_category", "general"),
            "min_age":            row.get("min_age"),
            "max_age":            row.get("max_age"),
            "income_limit":       row.get("income_limit"),
            "applicable_states":  row.get("applicable_states"),
            "gender_eligibility": row.get("gender_eligibility", "all"),
            "caste_eligibility":  row.get("caste_eligibility", "all"),
            "disability_required":row.get("disability_required", "false"),
            "occupation_eligibility": row.get("occupation_eligibility", "all"),
            "popularity_score":   row.get("popularity_score", "5.0"),
            "scheme_name":        row.get("scheme_name", ""),
            "benefit_description":row.get("benefit_description", ""),
        }
        rows.append({**user_dict, **scheme_row})
    return pd.DataFrame(rows)


def normalize_feature_frame(X: pd.DataFrame, schema: Dict[str, Any]) -> pd.DataFrame:
    X = engineer_features(X)
    feature_defs   = schema.get("features", [])
    text_features  = schema.get("text_features", ["benefit_description", "scheme_name"])
    if not text_features:
        text_features = ["benefit_description", "scheme_name"]
    base_feature_names = [f["name"] for f in feature_defs] if feature_defs else list(X.columns)
    categorical = set(schema.get("categorical", []))

    feature_names: List[str] = []
    for f in base_feature_names:
        if f not in feature_names:
            feature_names.append(f)
    for f in text_features:
        if f not in feature_names:
            feature_names.append(f)

    for col in feature_names:
        if col not in X.columns:
            X[col] = np.nan

    final_cols = [c for c in feature_names if c in X.columns]
    X = X[final_cols].copy()

    for col in X.columns:
        if col in text_features:
            X[col] = X[col].fillna("Information not available").astype(str)
        elif col in categorical:
            X[col] = X[col].fillna("").astype(str)
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0.0)
    return X


# ── API Endpoints ──────────────────────────────────────────────────────────────

@app.post("/api/recommend", response_model=RecommendationResponse)
def recommend(user: UserProfile):
    """
    Full 5-agent pipeline: Input → Eligibility → Retrieval → Reasoning → Output.
    Returns a rich, personalised scheme recommendation response.
    """
    try:
        result = app.state.pipeline.run(user)
    except Exception as e:
        logger.exception("[/api/recommend] Pipeline error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    app.state.behavior_service.log_event("recommendation", {
        "user_profile":  user.model_dump(),
        "total_results": result.get("summary", {}).get("total", 0),
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    })

    # Map to legacy RecommendationResponse shape
    ranked   = result.get("ranked_schemes", result.get("recommended", []))
    schemes  = result.get("recommended", ranked)

    return {
        "ranked_schemes":    ranked,
        "benefit_estimates": [
            {"scheme_id": s.get("scheme_id"), "estimate": {"summary": s.get("benefit_amount", "Varies")}}
            for s in schemes
        ],
        "required_documents": [
            {"scheme_id": s.get("scheme_id"), "documents_required": s.get("documents_required", [])}
            for s in schemes
        ],
        "why_this_scheme": [
            {
                "scheme_id":          s.get("scheme_id"),
                "reasons":            s.get("reasons", []),
                "path_to_eligibility":s.get("path_to_eligibility", []),
            }
            for s in schemes
        ],
        "knowledge_graph": result.get("knowledge_graph", []),
    }


@app.post("/api/check-eligibility", response_model=EligibilityResponse)
def check_eligibility(user: UserProfile):
    """
    Runs only Stages 1–2 (InputAgent + EligibilityEngine).
    Faster than /api/recommend — no GenAI calls.
    """
    try:
        result = app.state.pipeline.run_eligibility_only(user)
    except Exception as e:
        logger.exception("[/api/check-eligibility] Error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    app.state.behavior_service.log_event("eligibility_check", {
        "user_profile":  user.model_dump(),
        "total_eligible":len(result.get("eligible_schemes", [])),
    })

    return result


@app.post("/api/feedback")
def submit_feedback(feedback: Dict[str, Any]):
    app.state.behavior_service.log_event("click_feedback", feedback)
    return {"status": "recorded"}


@app.post("/api/compare")
def compare_schemes(request_data: Dict[str, Any]):
    scheme_ids = request_data.get("scheme_ids", [])
    if not scheme_ids:
        raise HTTPException(status_code=400, detail="Must provide list of scheme_ids to compare")

    df = app.state.schemes
    comparison_data = []
    for sid in scheme_ids:
        rows = df[df["scheme_id"] == sid]
        if rows.empty:
            continue
        scheme = rows.iloc[0].to_dict()
        comparison_data.append({
            "id":          scheme["scheme_id"],
            "name":        scheme["scheme_name"],
            "benefit":     scheme.get("benefit_amount", "Varies"),
            "documents":   str(scheme.get("documents_required", "")).split(","),
            "ministry":    scheme.get("ministry", "Central"),
            "url":         scheme.get("application_url", ""),
            "description": str(scheme.get("benefit_description", ""))[:300],
        })
    return comparison_data


@app.get("/api/scheme-details/{scheme_id}")
def scheme_details(scheme_id: str):
    """
    Returns structured data for the Scheme Details page (tldr, docs, apply steps).
    """
    df   = app.state.schemes
    rows = df[df["scheme_id"] == scheme_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail="Scheme not found")

    scheme = rows.iloc[0].to_dict()

    raw_docs = str(scheme.get("documents_required", ""))
    if raw_docs and raw_docs.lower() != "nan":
        doc_checklist = [
            {"name": d.strip(), "checked": False}
            for d in raw_docs.split(",") if d.strip()
        ]
    else:
        doc_checklist = [
            {"name": "Aadhar Card", "checked": False},
            {"name": "Bank Passbook", "checked": False},
        ]

    genai = app.state.genai_service
    return {
        "scheme_id":       scheme_id,
        "scheme_name":     scheme.get("scheme_name", "Unknown Scheme"),
        "tldr_bullets":    genai.generate_tldr(scheme),
        "doc_checklist":   doc_checklist,
        "how_to_apply_steps": genai.generate_application_steps(scheme),
        "application_url": scheme.get("application_url", ""),
        "full_description":scheme.get("benefit_description", ""),
        "agency":          scheme.get("ministry", "Central Government"),
        "level":           scheme.get("scheme_level", "Central"),
    }


@app.get("/api/health")
def health_check():
    """Pipeline health check endpoint."""
    return {
        "status":   "ok",
        "pipeline": "5-agent",
        "agents":   ["InputAgent", "EligibilityEngine", "RetrievalAgent", "ReasoningAgent", "OutputAgent"],
        "version":  "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
