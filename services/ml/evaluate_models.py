import json
from pathlib import Path

import joblib
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from utils import load_dataset, split_features_targets


def evaluate(
    dataset_path: str = "data/processed/eligibility_train.csv",
    models_dir: str = "services/ml/models",
):
    df = load_dataset(dataset_path)
    X, y_class, y_reg = split_features_targets(df)

    models_path = Path(models_dir)
    eligibility_model = joblib.load(models_path / "eligibility_model.pkl")
    benefit_model = joblib.load(models_path / "benefit_model.pkl")

    probs = eligibility_model.predict_proba(X)[:, 1]
    preds = (probs >= 0.5).astype(int)
    eligibility_metrics = {
        "accuracy": float(accuracy_score(y_class, preds)),
        "precision": float(precision_score(y_class, preds, zero_division=0)),
        "recall": float(recall_score(y_class, preds, zero_division=0)),
        "f1": float(f1_score(y_class, preds, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_class, probs)),
    }

    reg_preds = benefit_model.predict(X)
    benefit_metrics = {
        "rmse": float(mean_squared_error(y_reg, reg_preds) ** 0.5),
        "mae": float(mean_absolute_error(y_reg, reg_preds)),
        "r2": float(r2_score(y_reg, reg_preds)),
    }

    metrics = {"eligibility_full": eligibility_metrics, "benefit_full": benefit_metrics}
    metrics_path = models_path / "metrics.json"
    if metrics_path.exists():
        existing = json.loads(metrics_path.read_text(encoding="utf-8"))
    else:
        existing = {}
    existing.update(metrics)
    metrics_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    evaluate()
