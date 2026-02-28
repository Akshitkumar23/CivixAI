import json
import sys
from pathlib import Path
from typing import Dict

# Add current directory to sys.path for local imports
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

import joblib  # type: ignore
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.compose import ColumnTransformer  # type: ignore
from sklearn.preprocessing import OneHotEncoder  # type: ignore
from sklearn.pipeline import Pipeline  # type: ignore

try:
    from catboost import CatBoostRegressor  # type: ignore
except ImportError:
    CatBoostRegressor = None

try:
    from xgboost import XGBRegressor  # type: ignore
except ImportError:
    XGBRegressor = None

from utils import load_dataset, split_features_targets, feature_schema, infer_categorical_features  # type: ignore


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _build_catboost_regressor(X_train, y_train, X_val, y_val):
    if CatBoostRegressor is None:
        raise ImportError("catboost is not installed")

    cat_features = infer_categorical_features(X_train)
    model = CatBoostRegressor(
        iterations=500,
        depth=8,
        learning_rate=0.08,
        loss_function="RMSE",
        eval_metric="RMSE",
        verbose=False,
    )
    model.fit(
        X_train,
        y_train,
        cat_features=cat_features,
        eval_set=(X_val, y_val),
        use_best_model=True,
    )
    return model


def _build_xgboost_regressor(X_train, y_train):
    if XGBRegressor is None:
        raise ImportError("xgboost is not installed")

    cat_cols = infer_categorical_features(X_train)
    num_cols = [c for c in X_train.columns if c not in cat_cols]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )

    model = XGBRegressor(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        n_jobs=-1,
    )
    pipe = Pipeline([("pre", pre), ("model", model)])
    pipe.fit(X_train, y_train)
    return pipe


def _evaluate(model, X_test, y_test) -> Dict[str, float]:
    preds = model.predict(X_test)
    rmse = mean_squared_error(y_test, preds) ** 0.5
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    return {"rmse": float(rmse), "mae": float(mae), "r2": float(r2)}


def train(
    dataset_path: str = "data/processed/eligibility_train.csv",
    output_dir: str = "services/ml/models",
):
    df = load_dataset(dataset_path)
    X, _, y_reg = split_features_targets(df)

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y_reg, test_size=0.2, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42
    )

    metrics = {}

    cat_model = _build_catboost_regressor(X_train, y_train, X_val, y_val)
    metrics["catboost"] = _evaluate(cat_model, X_test, y_test)

    xgb_model = _build_xgboost_regressor(X_train, y_train)
    metrics["xgboost"] = _evaluate(xgb_model, X_test, y_test)

    best_model = cat_model
    best_name = "catboost"
    if metrics["xgboost"]["rmse"] < metrics["catboost"]["rmse"]:
        best_model = xgb_model
        best_name = "xgboost"

    out_dir = Path(output_dir)
    _ensure_dir(out_dir)
    joblib.dump(best_model, out_dir / "benefit_model.pkl")

    schema = feature_schema(X)
    schema["best_model_benefit"] = best_name
    schema_path = out_dir / "feature_schema.json"
    if schema_path.exists():
        existing_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    else:
        existing_schema = {}
    existing_schema.update(schema)
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(existing_schema, f, indent=2)

    metrics_path = out_dir / "metrics.json"
    if metrics_path.exists():
        existing = json.loads(metrics_path.read_text(encoding="utf-8"))
    else:
        existing = {}
    existing.update({"benefit": metrics})
    metrics_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    return metrics, best_name


if __name__ == "__main__":
    train()
