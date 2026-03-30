import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add current directory to sys.path for local imports
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

import joblib  # type: ignore
import numpy as np  # type: ignore
from sklearn.metrics import (  # type: ignore
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.compose import ColumnTransformer  # type: ignore
from sklearn.preprocessing import OneHotEncoder  # type: ignore
from sklearn.pipeline import Pipeline  # type: ignore

try:
    from catboost import CatBoostClassifier  # type: ignore
except ImportError:
    CatBoostClassifier = None

try:
    from xgboost import XGBClassifier  # type: ignore
except ImportError:
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier  # type: ignore
except ImportError:
    LGBMClassifier = None

# Local imports
from calibration import IsotonicCalibratedClassifier  # type: ignore
from utils import load_dataset, split_features_targets, feature_schema, infer_categorical_features  # type: ignore


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _build_catboost(X_train, y_train, X_val, y_val):
    if CatBoostClassifier is None:
        raise ImportError("catboost is not installed")

    cat_features = infer_categorical_features(X_train)
    text_features = ["benefit_description"] if "benefit_description" in X_train.columns else None

    model = CatBoostClassifier(
        iterations=500,
        depth=8,
        learning_rate=0.08,
        loss_function="Logloss",
        eval_metric="AUC",
        verbose=False,
    )
    model.fit(
        X_train,
        y_train,
        cat_features=cat_features,
        text_features=text_features,
        eval_set=(X_val, y_val),
        use_best_model=True,
    )

    # Calibrate on holdout set to reduce false positives.
    calibrated = IsotonicCalibratedClassifier(model).fit_calibrator(X_val, y_val)
    return calibrated, cat_features


def _build_xgboost(X_train, y_train, X_val, y_val):
    if XGBClassifier is None:
        raise ImportError("xgboost is not installed")

    cat_cols = infer_categorical_features(X_train)
    num_cols = [c for c in X_train.columns if c not in cat_cols and c != "benefit_description"]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )

    model = XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="auc",
        n_jobs=-1,
    )

    pipe = Pipeline([("pre", pre), ("model", model)])
    pipe.fit(X_train, y_train)

    calibrated = IsotonicCalibratedClassifier(pipe).fit_calibrator(X_val, y_val)
    return calibrated, cat_cols


def _evaluate(model, X_test, y_test) -> Dict[str, float]:
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(y_test, preds)),
        "precision": float(precision_score(y_test, preds, zero_division=0)),
        "recall": float(recall_score(y_test, preds, zero_division=0)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
    }


def train(
    dataset_path: str = "data/processed/eligibility_train.csv",
    output_dir: str = "services/ml/models",
    use_lightgbm: bool = False,
):
    df = load_dataset(dataset_path)
    X, y_class, _, _ = split_features_targets(df)

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y_class, test_size=0.2, random_state=42, stratify=y_class
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    metrics = {}

    print(f"Building CatBoost with {len(X_train)} rows...")
    cat_model, cat_features = _build_catboost(X_train, y_train, X_val, y_val)
    print("CatBoost Fit Complete.")
    metrics["catboost"] = _evaluate(cat_model, X_test, y_test)

    xgb_model, _ = _build_xgboost(X_train, y_train, X_val, y_val)
    metrics["xgboost"] = _evaluate(xgb_model, X_test, y_test)

    # CatBoost is primary model by design; XGBoost remains a tracked baseline.
    best_model = cat_model
    best_name = "catboost"

    if use_lightgbm:
        try:
            if LGBMClassifier is None:
                raise ImportError("lightgbm is not installed")

            cat_cols = infer_categorical_features(X_train)
            num_cols = [c for c in X_train.columns if c not in cat_cols and c != "benefit_description"]
            pre = ColumnTransformer(
                transformers=[
                    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
                    ("num", "passthrough", num_cols),
                ]
            )
            lgbm = LGBMClassifier(
                n_estimators=400,
                learning_rate=0.08,
                num_leaves=64,
                subsample=0.9,
                colsample_bytree=0.9,
                objective="binary",
            )
            pipe = Pipeline([("pre", pre), ("model", lgbm)])
            pipe.fit(X_train, y_train)
            calibrated = IsotonicCalibratedClassifier(pipe).fit_calibrator(X_val, y_val)
            metrics["lightgbm"] = _evaluate(calibrated, X_test, y_test) # type: ignore
        except Exception as e:
            metrics["lightgbm"] = {"error": f"LGBM Error: {str(e)}"} # type: ignore

    out_dir = Path(output_dir)
    _ensure_dir(out_dir)
    joblib.dump(best_model, out_dir / "eligibility_model.pkl")

    # Merge with existing schema if it exists
    schema_path = out_dir / "feature_schema.json"
    existing_schema: Dict[str, Any] = {}
    if schema_path.exists():
        try:
            val = json.loads(schema_path.read_text(encoding="utf-8"))
            if isinstance(val, dict):
                existing_schema = val
        except Exception:
            pass
    
    schema = feature_schema(X)
    schema["best_model_eligibility"] = best_name
    schema["cat_features_eligibility"] = cat_features
    existing_schema.update(schema)
    
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(existing_schema, f, indent=2)

    # Merge with existing metrics if it exists
    metrics_path = out_dir / "metrics.json"
    existing_metrics: Dict[str, Any] = {}
    if metrics_path.exists():
        try:
            val = json.loads(metrics_path.read_text(encoding="utf-8"))
            if isinstance(val, dict):
                existing_metrics = val
        except Exception:
            pass
    
    existing_metrics.update({"eligibility": metrics})
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(existing_metrics, f, indent=2)

    return metrics, best_name


if __name__ == "__main__":
    train()
