import json
import sys
from pathlib import Path
from typing import Dict

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
    from catboost import CatBoostRanker, Pool  # type: ignore
except ImportError:
    CatBoostRanker = None

try:
    from xgboost import XGBRegressor  # type: ignore
except ImportError:
    XGBRegressor = None

from utils import load_dataset, split_features_targets, feature_schema, infer_categorical_features  # type: ignore


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _build_catboost_ranker(X_train, y_train, group_train, X_val, y_val, group_val):
    if CatBoostRanker is None:
        raise ImportError("catboost is not installed")

    cat_features = infer_categorical_features(X_train)
    text_features = ["benefit_description"] if "benefit_description" in X_train.columns else None

    # CatBoostRanker expects integer labels or floats for YetiRank. YetiRank is very stable.
    model = CatBoostRanker(
        iterations=500,
        depth=6,
        learning_rate=0.08,
        loss_function="YetiRank",
        eval_metric="NDCG",
        verbose=False,
    )
    
    train_pool = Pool(
        data=X_train,
        label=y_train,
        group_id=group_train,
        cat_features=cat_features,
        text_features=text_features
    )
    
    val_pool = Pool(
        data=X_val,
        label=y_val,
        group_id=group_val,
        cat_features=cat_features,
        text_features=text_features
    )

    model.fit(
        train_pool,
        eval_set=val_pool,
        use_best_model=True,
    )
    return model


def _build_xgboost_regressor(X_train, y_train):
    if XGBRegressor is None:
        raise ImportError("xgboost is not installed")

    cat_cols = infer_categorical_features(X_train)
    num_cols = [c for c in X_train.columns if c not in cat_cols and c != "benefit_description"]

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
    return {"rmse": float(rmse), "mae": float(mae)}


def train(
    dataset_path: str = "data/processed/eligibility_train.csv",
    output_dir: str = "services/ml/models",
):
    df = load_dataset(dataset_path)
    X, _, y_reg, group_id = split_features_targets(df)

    # Ranker requires contiguous groups
    sort_idx = group_id.argsort()
    X = X.iloc[sort_idx].reset_index(drop=True)
    y_reg = y_reg.iloc[sort_idx].reset_index(drop=True)
    group_id = group_id.iloc[sort_idx].reset_index(drop=True)

    unique_groups = group_id.unique()
    train_groups, temp_groups = train_test_split(unique_groups, test_size=0.2, random_state=42)
    val_groups, test_groups = train_test_split(temp_groups, test_size=0.5, random_state=42)

    X_train, y_train, group_train = X[group_id.isin(train_groups)], y_reg[group_id.isin(train_groups)], group_id[group_id.isin(train_groups)]
    X_val, y_val, group_val = X[group_id.isin(val_groups)], y_reg[group_id.isin(val_groups)], group_id[group_id.isin(val_groups)]
    X_test, y_test, group_test = X[group_id.isin(test_groups)], y_reg[group_id.isin(test_groups)], group_id[group_id.isin(test_groups)]

    metrics = {}

    cat_model = _build_catboost_ranker(X_train, y_train, group_train, X_val, y_val, group_val)
    metrics["catboost"] = _evaluate(cat_model, X_test, y_test)

    # XGBoost remains a baseline simple regressor
    xgb_model = _build_xgboost_regressor(X_train, y_train)
    metrics["xgboost"] = _evaluate(xgb_model, X_test, y_test)

    # Always prefer CatBoostRanker for ranking context
    best_model = cat_model
    best_name = "catboost"

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
