import json
from typing import Any, Dict, List, Tuple

import numpy as np  # type: ignore
import pandas as pd  # type: ignore
from pandas.api.types import is_categorical_dtype, is_object_dtype, is_string_dtype  # type: ignore


USER_FEATURES = [
    "age",
    "annualIncome",
    "state",
    "caste",
    "occupation",
    "gender",
    "hasLand",
    "hasDisability",
    "familyIncome",
    "hasAvailedSimilarScheme",
    "landSize",
    "familySize",
    "isSingleGirlChild",
    "isWidowOrSenior",
    "isTaxPayer",
    "isBankLinked",
    "educationLevel",
    "digitalLiteracy",
    "urbanRural",
    "maritalStatus",
    "isBPL",
    "isMinority",
    "monthlyExpenses",
    "hasSmartphone",
    "hasInternet",
    "employmentType",
    "skillCertification",
    "loanRequirement",
    "monthlySavings",
    "hasInsurance",
    "hasPension",
    "prioritySchemes",
]

SCHEME_FEATURES = [
    "scheme_id",
    "scheme_type",
    "scheme_category",
    "min_age",
    "max_age",
    "income_limit",
    "applicable_states",
    "special_conditions_required",
    "gender_eligibility",
    "caste_eligibility",
    "disability_required",
    "occupation_eligibility",
    "education_level_required",
    "urban_rural_eligibility",
    "marital_status_required",
    "employment_type_eligibility",
    "is_bpl_only",
    "popularity_score",
]

TARGET_CLASS = "eligible"
TARGET_REG = "benefit_score"


def _maybe_json(value: Any) -> Any:
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


def _normalize_list(value: Any) -> str:
    parsed = _maybe_json(value)
    if parsed is None:
        return ""
    if isinstance(parsed, list):
        return "|".join(str(x).strip() for x in parsed if str(x).strip())
    if isinstance(parsed, dict):
        return "|".join(f"{k}:{v}" for k, v in parsed.items())
    return str(parsed)


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize complex fields into string tokens for modeling
    if "applicable_states" in df.columns:
        df["applicable_states"] = df["applicable_states"].apply(_normalize_list)
    if "special_conditions_required" in df.columns:
        df["special_conditions_required"] = df["special_conditions_required"].apply(_normalize_list)
    return df


def ensure_columns(df: pd.DataFrame, required: List[str]) -> pd.DataFrame:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def engineer_features(X: pd.DataFrame) -> pd.DataFrame:
    # Custom Feature: Per Capita Income
    if "annualIncome" in X.columns and "familySize" in X.columns:
        X["per_capita_income"] = X["annualIncome"] / np.maximum(X["familySize"].fillna(1).astype(float), 1.0)
    # Custom Feature: Age to Income Ratio
    if "annualIncome" in X.columns and "age" in X.columns:
        X["age_income_ratio"] = X["annualIncome"] / np.maximum(X["age"].fillna(1).astype(float), 1.0)
    return X


def split_features_targets(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series, Any]:
    features = USER_FEATURES + SCHEME_FEATURES
    
    # Ensure all features exist, fill missing with default/NaN
    for col in features:
        if col not in df.columns:
            if col in ["gender_eligibility", "caste_eligibility", "occupation_eligibility", "education_level_required", "urban_rural_eligibility", "marital_status_required", "employment_type_eligibility"]:
                df[col] = "all"
            elif col in ["is_bpl_only", "disability_required"]:
                df[col] = "false"
            elif col == "popularity_score":
                df[col] = 5.0
            else:
                df[col] = np.nan
    
    # Drop rows without target
    df = df.dropna(subset=[TARGET_CLASS, TARGET_REG])
    X = df[features].copy()
    
    # Normalize text features for stable downstream encoders/models.
    text_cols = ['state', 'caste', 'occupation', 'gender', 'educationLevel', 'digitalLiteracy', 'urbanRural', 'employmentType', 'skillCertification', 'loanRequirement', 'prioritySchemes', 'scheme_id', 'scheme_type', 'scheme_category', 'applicable_states', 'special_conditions_required', 'gender_eligibility', 'caste_eligibility', 'occupation_eligibility', 'education_level_required', 'urban_rural_eligibility', 'marital_status_required', 'employment_type_eligibility', 'is_bpl_only']
    
    for col in X.columns:
        if col in text_cols or is_object_dtype(X[col]) or is_string_dtype(X[col]) or is_categorical_dtype(X[col]):
            X[col] = X[col].fillna("").astype(str)
    X = engineer_features(X)
    
    y_class = df[TARGET_CLASS].astype(int)
    y_reg = df[TARGET_REG].astype(float)
    group_id = df["group_id"] if "group_id" in df.columns else None
    return X, y_class, y_reg, group_id


def infer_categorical_features(X: pd.DataFrame) -> List[str]:
    cat_cols = []
    # Force text features out of categorical because CatBoost handles them differently
    text_cols = ["benefit_description"] 
    for col in X.columns:
        if col in text_cols:
            continue
        if is_object_dtype(X[col]) or is_string_dtype(X[col]) or is_categorical_dtype(X[col]):
            cat_cols.append(col)
    return cat_cols


def feature_schema(X: pd.DataFrame) -> Dict[str, Any]:
    return {
        "features": [
            {"name": col, "dtype": str(X[col].dtype)} for col in X.columns
        ],
        "categorical": infer_categorical_features(X),
    }
