"""k most similar historical incidents and their labels (OpenSpec triage-classification).

Incidents are compared in a standardized feature space (log1p of counts, then
z-score). Labels shown for neighbors honor analyst corrections: a corrected
label always replaces the original one (triage-report: analyst feedback).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from .features import CLASSES, SHORT


class SimilarIncidents:
    def __init__(self, k: int = 5):
        self.k = k
        self.corrections: dict[str, str] = {}

    def _transform(self, X: pd.DataFrame) -> np.ndarray:
        Z = np.log1p(np.clip(X[self.columns].to_numpy(dtype=np.float64), 0, None))
        return ((Z - self.mu) / self.sd).astype(np.float32)

    def fit(self, X: pd.DataFrame, y) -> "SimilarIncidents":
        """X: reference (historical) incidents indexed by incident key; y: label index 0/1/2."""
        self.columns = list(X.columns)
        Z = np.log1p(np.clip(X.to_numpy(dtype=np.float64), 0, None))
        self.mu, self.sd = Z.mean(axis=0), Z.std(axis=0) + 1e-9
        self.keys = np.asarray(X.index)
        self.labels = np.asarray([SHORT[CLASSES[int(v)]] for v in np.asarray(y)])
        self.nn = NearestNeighbors(n_neighbors=self.k, algorithm="brute").fit(self._transform(X))
        return self

    def correct(self, key: str, label: str) -> None:
        """Record an analyst correction (label in TP/BP/FP); used immediately in later lookups."""
        assert label in {"TP", "BP", "FP"}
        self.corrections[key] = label

    def query(self, X: pd.DataFrame) -> list[list[dict]]:
        dist, ind = self.nn.kneighbors(self._transform(X))
        out = []
        for d_row, i_row in zip(dist, ind):
            row = []
            for d, i in zip(d_row, i_row):
                key = str(self.keys[i])
                orig = str(self.labels[i])
                row.append({"incident": key,
                            "label": self.corrections.get(key, orig),
                            "corrected": key in self.corrections,
                            "original_label": orig,
                            "distance": round(float(d), 4)})
            out.append(row)
        return out
