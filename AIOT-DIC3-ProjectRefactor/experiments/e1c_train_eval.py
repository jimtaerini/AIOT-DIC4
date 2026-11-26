"""E1c: splits, GBDT triage model, and non-LLM baselines (tasks 1.4, 3.1, 3.2, 3.4).

Splits (all keyed by (OrgId, IncidentId); a key is in exactly one set):
  incident  train/val = official GUIDE train (90/10 by incident), test = official
            GUIDE test (verified to share no incident keys with train)
  org       pool train+test; 20% of OrgIds -> test, 10% of the rest -> val
  time      pool train+test; latest 20% of incidents by first timestamp -> test,
            the previous 10% -> val (GUIDE timestamps are noised)

Models
  majority        always predicts the most frequent training class
  detector_rule   per-detector historical label rates from training incidents;
                  an incident gets the argmax of the mean rates of its alerts
  gbdt            scikit-learn HistGradientBoostingClassifier, class_weight
                  "balanced", early stopping on the validation set; 3 seeds

Detector and alert-title rates are target encodings computed only from the
training set (5-fold out-of-fold for training rows), so no label leaks from
validation or test.

Metrics on the test set: macro-F1, per-class precision/recall, TP recall,
TP miss rate (MR) and escalation rate (ER). These models never escalate, so
ER = 0 and MR = 1 - TP recall; escalation comes with the full agent.

Usage (run from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e1c_train_eval.py
Writes experiments/results/e1_results.json and e1_results.md, and test-set
GBDT probabilities to data/processed/e1_gbdt_probs_<split>.parquet.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_recall_fscore_support

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.analytics.features import (CLASSES, SHORT, build_matrix, check_split,  # noqa: E402
                                          load_tables, make_splits)
from soc_agent.analytics.triage_model import TriageModel  # noqa: E402

SEEDS = [0, 1, 2]
inc, alerts = load_tables()


def metrics(y, pred):
    p, r, f, _ = precision_recall_fscore_support(y, pred, labels=[0, 1, 2], zero_division=0)
    tp_recall = float(r[0])
    return {
        "macro_f1": float(f1_score(y, pred, average="macro")),
        "precision": {SHORT[c]: float(p[i]) for i, c in enumerate(CLASSES)},
        "recall": {SHORT[c]: float(r[i]) for i, c in enumerate(CLASSES)},
        "tp_recall": tp_recall,
        "mr": 1.0 - tp_recall,   # no escalation: every TP not labeled TP is missed
        "er": 0.0,
    }


results = {"seeds": SEEDS, "splits": {}, "features": None}
t0 = time.time()
for split_name, lab in make_splits(inc).items():
    sizes = check_split(inc, split_name, lab)
    X, y, idx, tables, prior = build_matrix(inc, alerts, lab)
    det_table = tables["DetectorId"]
    results["features"] = list(X.columns)
    yt = y[idx["test"]].to_numpy()
    out = {"sizes": sizes, "test_label_counts": {SHORT[c]: int((yt == i).sum()) for i, c in enumerate(CLASSES)}}

    # majority baseline
    maj = int(np.bincount(y[idx["train"]]).argmax())
    out["majority"] = metrics(yt, np.full(len(yt), maj))

    # detector historical-rate rule (train-only statistics)
    a_test = alerts[alerts["kid"].isin(set(idx["test"]))]
    m = a_test[["kid", "DetectorId"]].drop_duplicates().merge(det_table, left_on="DetectorId", right_index=True, how="left")
    for c in range(3):
        m[f"r{c}"] = m[f"r{c}"].fillna(prior[c])
    det_pred = m.groupby("kid")[["r0", "r1", "r2"]].mean().reindex(idx["test"]).fillna(pd.Series(prior, index=["r0", "r1", "r2"]))
    out["detector_rule"] = metrics(yt, det_pred.to_numpy().argmax(axis=1))

    # GBDT, several seeds
    runs, probs = [], None
    for seed in SEEDS:
        model = TriageModel(seed=seed).fit(X.loc[idx["train"]], y[idx["train"]],
                                           X_val=X.loc[idx["val"]], y_val=y[idx["val"]])
        pr = model.predict_proba(X.loc[idx["test"]])  # asserts each row sums to 1
        mm = metrics(yt, pr.argmax(axis=1))
        mm["n_iter"] = int(model.clf.n_iter_)
        runs.append(mm)
        probs = pr if probs is None else probs + pr
    agg = {k: (float(np.mean([r[k] for r in runs])), float(np.std([r[k] for r in runs])))
           for k in ["macro_f1", "tp_recall", "mr"]}
    out["gbdt"] = {"runs": runs, "mean_std": agg}
    pd.DataFrame(probs / len(SEEDS), index=idx["test"], columns=["p_tp", "p_bp", "p_fp"]).assign(
        y=yt).reset_index().to_parquet(f"data/processed/e1_gbdt_probs_{split_name}.parquet")
    results["splits"][split_name] = out
    print(f"[{time.time() - t0:6.0f}s] {split_name}: sizes={sizes} "
          f"majority F1={out['majority']['macro_f1']:.3f} detector F1={out['detector_rule']['macro_f1']:.3f} "
          f"gbdt F1={agg['macro_f1'][0]:.4f}±{agg['macro_f1'][1]:.4f} TP recall={agg['tp_recall'][0]:.4f}", flush=True)

json.dump(results, open("experiments/results/e1_results.json", "w"), indent=1)

lines = ["# E1 results (non-LLM baselines)", "",
         "Generated by `experiments/e1c_train_eval.py`. Test-set metrics; GBDT is mean ± std over seeds "
         f"{SEEDS}. These models never escalate, so ER = 0 and MR = 1 − TP recall.", ""]
for split_name, out in results["splits"].items():
    lines += [f"## {split_name} split", "",
              f"Sizes: {out['sizes']}; test labels: {out['test_label_counts']}", "",
              "| Method | Macro-F1 | TP recall | MR | ER | P(TP) | P(BP) | P(FP) | R(BP) | R(FP) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for name in ["majority", "detector_rule"]:
        mm = out[name]
        lines.append(f"| {name} | {mm['macro_f1']:.3f} | {mm['tp_recall']:.3f} | {mm['mr']:.3f} | 0 | "
                     f"{mm['precision']['TP']:.3f} | {mm['precision']['BP']:.3f} | {mm['precision']['FP']:.3f} | "
                     f"{mm['recall']['BP']:.3f} | {mm['recall']['FP']:.3f} |")
    g = out["gbdt"]
    def ms(k):
        return f"{g['mean_std'][k][0]:.3f} ± {g['mean_std'][k][1]:.3f}"
    r0 = g["runs"]
    pm = {k: np.mean([r["precision"][k] for r in r0]) for k in ["TP", "BP", "FP"]}
    rm = {k: np.mean([r["recall"][k] for r in r0]) for k in ["BP", "FP"]}
    lines.append(f"| gbdt | {ms('macro_f1')} | {ms('tp_recall')} | {ms('mr')} | 0 | {pm['TP']:.3f} | "
                 f"{pm['BP']:.3f} | {pm['FP']:.3f} | {rm['BP']:.3f} | {rm['FP']:.3f} |")
    lines.append("")
open("experiments/results/e1_results.md", "w").write("\n".join(lines))
print("done in", round(time.time() - t0), "s")
