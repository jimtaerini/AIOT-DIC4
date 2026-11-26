"""Analytics step of Algorithm 1 (lines 10–13): p, SHAP top features, similar incidents."""
from __future__ import annotations

import pandas as pd

from .explain import Explainer
from .similar import SimilarIncidents
from .triage_model import TriageModel


def classify(X: pd.DataFrame, model: TriageModel, explainer: Explainer, similar: SimilarIncidents,
             top_k: int = 5) -> list[dict]:
    """One result per incident row: probabilities, label, top features, similar incidents."""
    p = model.predict_proba(X)
    tops = explainer.top_features(X, k=top_k)
    sims = similar.query(X)
    return [{
        "incident": str(key),
        "p": {"TP": round(float(pr[0]), 4), "BP": round(float(pr[1]), 4), "FP": round(float(pr[2]), 4)},
        "label": TriageModel.label(pr),
        "top_features": top,
        "similar_incidents": sim,
    } for key, pr, top, sim in zip(X.index, p, tops, sims)]
