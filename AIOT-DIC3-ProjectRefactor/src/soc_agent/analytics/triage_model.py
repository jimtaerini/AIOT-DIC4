"""Triage classifier: P(TP), P(BP), P(FP) from incident features (OpenSpec triage-classification).

Histogram GBDT from scikit-learn (same algorithm family as LightGBM; LightGBM and
XGBoost need Homebrew libomp on macOS). Probabilities come from a model trained
on analyst-labeled incidents, never from the LLM alone.
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from .features import CLASSES, SHORT

GBDT_PARAMS = dict(learning_rate=0.1, max_iter=500, max_leaf_nodes=63, min_samples_leaf=40,
                   l2_regularization=1.0, max_features=0.8, early_stopping=True, n_iter_no_change=20,
                   class_weight="balanced")


@dataclass
class TriageModel:
    seed: int = 0
    params: dict = field(default_factory=lambda: dict(GBDT_PARAMS))
    clf: HistGradientBoostingClassifier | None = None
    feature_names: list[str] | None = None

    def fit(self, X: pd.DataFrame, y, X_val: pd.DataFrame | None = None, y_val=None) -> "TriageModel":
        self.feature_names = list(X.columns)
        self.clf = HistGradientBoostingClassifier(random_state=self.seed, **self.params)
        if X_val is not None:
            self.clf.fit(X, y, X_val=X_val[self.feature_names], y_val=y_val)
        else:
            self.clf.fit(X, y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Rows are incidents; columns are (p_TP, p_BP, p_FP) and each row sums to 1."""
        p = self.clf.predict_proba(X[self.feature_names])
        assert np.allclose(p.sum(axis=1), 1.0), "class probabilities must sum to 1"
        return p

    @staticmethod
    def label(p_row) -> str:
        return SHORT[CLASSES[int(np.argmax(p_row))]]

    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path) -> "TriageModel":
        with open(path, "rb") as f:
            return pickle.load(f)
