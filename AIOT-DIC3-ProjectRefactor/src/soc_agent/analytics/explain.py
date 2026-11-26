"""Feature-contribution explanations with SHAP (OpenSpec triage-classification, M5).

For each incident the explainer lists the features that most influenced the
predicted class, with their value and the direction of their contribution
(positive = pushes toward the predicted class), plus each feature's
contribution toward TP, since a missed TP is the costliest error (M3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from .features import CLASSES, SHORT
from .triage_model import TriageModel


class Explainer:
    def __init__(self, model: TriageModel):
        self.model = model
        self.explainer = shap.TreeExplainer(model.clf)

    def shap_values(self, X: pd.DataFrame) -> np.ndarray:
        """Array of shape (n_incidents, n_features, n_classes) in log-odds units."""
        v = self.explainer.shap_values(X[self.model.feature_names])
        v = np.asarray(v)
        if v.ndim == 3 and v.shape[0] == len(CLASSES) and v.shape[2] != len(CLASSES):
            v = np.transpose(v, (1, 2, 0))  # older SHAP: list of per-class arrays
        return v

    def top_features(self, X: pd.DataFrame, k: int = 5, values: np.ndarray | None = None) -> list[list[dict]]:
        """For each row: the k features with the largest |SHAP| toward its predicted class."""
        values = self.shap_values(X) if values is None else values
        pred = self.model.predict_proba(X).argmax(axis=1)
        names = self.model.feature_names
        out = []
        for i in range(len(X)):
            contrib = values[i, :, pred[i]]
            order = np.argsort(-np.abs(contrib))[:k]
            out.append([{
                "feature": names[j],
                "value": float(X.iloc[i][names[j]]),
                "contribution": round(float(contrib[j]), 4),
                "direction": "toward" if contrib[j] > 0 else "against",
                "toward_class": SHORT[CLASSES[pred[i]]],
                "contribution_to_TP": round(float(values[i, j, 0]), 4),
            } for j in order])
        return out

    def global_importance(self, X: pd.DataFrame, values: np.ndarray | None = None) -> pd.DataFrame:
        """Mean |SHAP| per feature and class over the given incidents."""
        values = self.shap_values(X) if values is None else values
        imp = np.abs(values).mean(axis=0)
        df = pd.DataFrame(imp, index=self.model.feature_names,
                          columns=[f"mean_abs_shap_{SHORT[c]}" for c in CLASSES])
        df["mean_abs_shap_all"] = df.mean(axis=1)
        return df.sort_values("mean_abs_shap_all", ascending=False)
