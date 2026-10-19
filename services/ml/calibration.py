from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression


class IsotonicCalibratedClassifier:
    """Thin wrapper that calibrates binary probabilities using isotonic regression."""

    def __init__(self, base_model):
        self.base_model = base_model
        self.calibrator = IsotonicRegression(out_of_bounds="clip")

    def fit_calibrator(self, X_cal, y_cal):
        raw = self.base_model.predict_proba(X_cal)[:, 1]
        self.calibrator.fit(raw, y_cal)
        return self

    def predict_proba(self, X):
        raw = self.base_model.predict_proba(X)[:, 1]
        calibrated = self.calibrator.transform(raw)
        calibrated = np.clip(calibrated, 0.0, 1.0)
        return np.column_stack([1.0 - calibrated, calibrated])

    def predict(self, X):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= 0.5).astype(int)

