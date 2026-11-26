"""E1d: SHAP explanations and similar incidents on the incident split (task 3.3).

Trains the GBDT (seed 0, incident split; same settings as e1c), then:
  - global SHAP importance on a stratified sample of test incidents
  - full triage results (p, label, top-5 SHAP features, 5 similar training
    incidents) for a stratified sample of test incidents, checking that every
    result carries both explanations
  - how often the similar incidents share the true label (usefulness check)

Usage (run from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e1d_explain_similar.py
Writes experiments/results/e1d_shap_importance.csv, e1d_summary.json,
e1d_triage_samples.jsonl, and the model to data/processed/models/ (git-ignored).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.analytics.explain import Explainer  # noqa: E402
from soc_agent.analytics.features import CLASSES, SHORT, build_matrix, load_tables, make_splits  # noqa: E402
from soc_agent.analytics.similar import SimilarIncidents  # noqa: E402
from soc_agent.analytics.triage import classify  # noqa: E402
from soc_agent.analytics.triage_model import TriageModel  # noqa: E402

SEED, K, TOP_K = 0, 5, 5
N_SHAP, N_RESULTS = 6000, 300  # stratified test samples (per class: 1/3 each)
t0 = time.time()

inc, alerts = load_tables()
lab = make_splits(inc)["incident"]
X, y, idx, _, _ = build_matrix(inc, alerts, lab)
model = TriageModel(seed=SEED).fit(X.loc[idx["train"]], y[idx["train"]],
                                   X_val=X.loc[idx["val"]], y_val=y[idx["val"]])
Path("data/processed/models").mkdir(parents=True, exist_ok=True)
model.save("data/processed/models/e1_gbdt_incident_seed0.pkl")
print(f"[{time.time() - t0:5.0f}s] model trained, n_iter={model.clf.n_iter_}", flush=True)

rng = np.random.default_rng(SEED)
yt = y[idx["test"]]


def stratified(n):
    keys = []
    for c in range(3):
        pool = yt[yt == c].index.to_numpy()
        keys += list(rng.choice(pool, size=n // 3, replace=False))
    return keys


explainer = Explainer(model)
shap_keys = stratified(N_SHAP)
values = explainer.shap_values(X.loc[shap_keys])
imp = explainer.global_importance(X.loc[shap_keys], values=values)
imp.round(5).to_csv("experiments/results/e1d_shap_importance.csv")
print(f"[{time.time() - t0:5.0f}s] SHAP on {len(shap_keys)} incidents", flush=True)

similar = SimilarIncidents(k=K).fit(X.loc[idx["train"]], y[idx["train"]])
res_keys = stratified(N_RESULTS)
results = classify(X.loc[res_keys], model, explainer, similar, top_k=TOP_K)
assert all(len(r["top_features"]) == TOP_K and len(r["similar_incidents"]) == K for r in results)
with open("experiments/results/e1d_triage_samples.jsonl", "w") as f:
    for r, key in zip(results, res_keys):
        r["true_label"] = SHORT[CLASSES[int(y[key])]]
        f.write(json.dumps(r) + "\n")
print(f"[{time.time() - t0:5.0f}s] {len(results)} triage results with SHAP + similar incidents", flush=True)

# usefulness of similar incidents: share of neighbors with the true label, and k-NN majority vote
agree, knn_correct, gbdt_correct = [], 0, 0
for r in results:
    labels = [s["label"] for s in r["similar_incidents"]]
    agree.append(np.mean([lbl == r["true_label"] for lbl in labels]))
    knn_correct += max(set(labels), key=labels.count) == r["true_label"]
    gbdt_correct += r["label"] == r["true_label"]

top_by_tp = imp.sort_values("mean_abs_shap_TP", ascending=False).head(10)
summary = {
    "split": "incident", "seed": SEED, "k": K, "top_k": TOP_K,
    "n_shap_sample": len(shap_keys), "n_result_sample": len(results),
    "every_result_has_shap_and_similar": True,
    "top10_features_overall": imp.head(10)["mean_abs_shap_all"].round(4).to_dict(),
    "top10_features_for_TP": top_by_tp["mean_abs_shap_TP"].round(4).to_dict(),
    "similar_same_label_share": round(float(np.mean(agree)), 4),
    "knn_majority_accuracy": round(knn_correct / len(results), 4),
    "gbdt_accuracy_same_sample": round(gbdt_correct / len(results), 4),
    "note": "samples are class-balanced (1/3 TP, BP, FP), so accuracies are not comparable to Table VI",
    "seconds": round(time.time() - t0),
}
json.dump(summary, open("experiments/results/e1d_summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
