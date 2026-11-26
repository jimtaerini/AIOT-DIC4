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
import time
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import f1_score, precision_recall_fscore_support
from sklearn.model_selection import GroupKFold

SEEDS = [0, 1, 2]
CLASSES = ["TruePositive", "BenignPositive", "FalsePositive"]
SHORT = {"TruePositive": "TP", "BenignPositive": "BP", "FalsePositive": "FP"}
KEY = ["OrgId", "IncidentId"]
SMOOTH = 20.0  # target-encoding smoothing toward the global prior
# raw entity columns (IOC-like values) must never be features (M4); only counts are allowed
FORBIDDEN_FEATURES = {"IpAddress", "Sha256", "Url", "DeviceId", "DeviceName", "AccountSid", "AccountUpn",
                      "AccountObjectId", "AccountName", "FileName", "FolderPath", "NetworkMessageId",
                      "RegistryKey", "RegistryValueName", "RegistryValueData", "OrgId", "IncidentId", "AlertId"}

inc = pd.read_parquet("data/processed/incidents_full.parquet")
alerts = pd.read_parquet("data/processed/alerts.parquet")
inc["y"] = inc["label"].map({c: i for i, c in enumerate(CLASSES)}).astype(int)
inc["kid"] = inc["source"] + ":" + inc["OrgId"].astype(str) + ":" + inc["IncidentId"].astype(str)
alerts["kid"] = alerts["source"] + ":" + alerts["OrgId"].astype(str) + ":" + alerts["IncidentId"].astype(str)
alerts = alerts[alerts["kid"].isin(set(inc["kid"]))]
BASE_FEATURES = [c for c in inc.columns if c not in
                 {"source", "OrgId", "IncidentId", "label", "first_ts", "y", "kid"}]
assert not FORBIDDEN_FEATURES & set(BASE_FEATURES), FORBIDDEN_FEATURES & set(BASE_FEATURES)


def make_splits(rng_seed=42):
    rng = np.random.default_rng(rng_seed)
    s = {}
    # incident split
    tr = inc[inc.source == "train"]["kid"].to_numpy()
    val = rng.choice(tr, size=len(tr) // 10, replace=False)
    lab = pd.Series("train", index=inc["kid"])
    lab[inc.loc[inc.source == "test", "kid"]] = "test"
    lab[val] = "val"
    s["incident"] = lab
    # org split (OrgIds are shared between official train and test)
    orgs = np.sort(inc["OrgId"].unique())
    test_orgs = set(rng.choice(orgs, size=len(orgs) // 5, replace=False))
    rest = np.array([o for o in orgs if o not in test_orgs])
    val_orgs = set(rng.choice(rest, size=len(rest) // 10, replace=False))
    lab = pd.Series(np.where(inc["OrgId"].isin(test_orgs), "test",
                    np.where(inc["OrgId"].isin(val_orgs), "val", "train")), index=inc["kid"])
    s["org"] = lab
    # time split
    order = inc.sort_values(["first_ts", "kid"])["kid"].to_numpy()
    n = len(order)
    lab = pd.Series("train", index=inc["kid"])
    lab[order[int(n * 0.8):]] = "test"
    lab[order[int(n * 0.72):int(n * 0.8)]] = "val"
    s["time"] = lab
    return s


def check_split(name, lab):
    sets = {k: set(lab[lab == k].index) for k in ["train", "val", "test"]}
    assert not (sets["train"] & sets["val"]) and not (sets["train"] & sets["test"]) and not (sets["val"] & sets["test"])
    assert sum(len(v) for v in sets.values()) == len(inc)
    out = {k: len(v) for k, v in sets.items()}
    if name == "org":
        org_of = inc.set_index("kid")["OrgId"]
        tr_orgs = set(org_of[list(sets["train"])])
        assert not tr_orgs & set(org_of[list(sets["test"])]), "org leak"
        out["test_orgs_in_train"] = 0
    return out


def rate_table(a, col, y_by_kid, prior):
    """Smoothed per-value label rates computed from alerts of the given incidents."""
    d = a[[col, "kid"]].drop_duplicates().copy()
    d["y"] = d["kid"].map(y_by_kid)
    cnt = pd.crosstab(d[col], d["y"]).reindex(columns=range(3), fill_value=0)
    n = cnt.sum(axis=1).to_numpy()[:, None]
    rates = (cnt.to_numpy() + SMOOTH * prior) / (n + SMOOTH)
    return pd.DataFrame(rates, index=cnt.index, columns=[f"r{c}" for c in range(3)]), cnt.sum(axis=1)


def encode(a, col, table, prior):
    m = a[["kid", col]].merge(table, left_on=col, right_index=True, how="left")
    for c in range(3):
        m[f"r{c}"] = m[f"r{c}"].fillna(prior[c])
    g = m.groupby("kid")
    out = pd.DataFrame(index=g.size().index)
    for c in range(3):
        short = SHORT[CLASSES[c]].lower()
        out[f"{col}_{short}_mean"] = g[f"r{c}"].mean()
        out[f"{col}_{short}_max"] = g[f"r{c}"].max()
    seen = m[col].isin(table.index)
    out[f"{col}_unseen_share"] = (~seen).groupby(m["kid"]).mean()
    return out


def target_features(lab):
    """Detector/title encodings: OOF for train, train-only statistics for val/test."""
    y_by_kid = inc.set_index("kid")["y"]
    tr_kids = lab[lab == "train"].index
    prior = np.bincount(y_by_kid[tr_kids], minlength=3) / len(tr_kids)
    a_tr = alerts[alerts["kid"].isin(set(tr_kids))]
    a_other = alerts[~alerts["kid"].isin(set(tr_kids))]
    parts = []
    # out-of-fold for training incidents
    kids = np.array(sorted(set(a_tr["kid"])))
    for fit_idx, enc_idx in GroupKFold(n_splits=5).split(kids, groups=kids):
        fit_k, enc_k = set(kids[fit_idx]), set(kids[enc_idx])
        a_fit, a_enc = a_tr[a_tr["kid"].isin(fit_k)], a_tr[a_tr["kid"].isin(enc_k)]
        cols = [encode(a_enc, c, rate_table(a_fit, c, y_by_kid, prior)[0], prior)
                for c in ["DetectorId", "AlertTitle"]]
        parts.append(pd.concat(cols, axis=1))
    full = {c: rate_table(a_tr, c, y_by_kid, prior)[0] for c in ["DetectorId", "AlertTitle"]}
    parts.append(pd.concat([encode(a_other, c, full[c], prior) for c in full], axis=1))
    te = pd.concat(parts)
    return te, full["DetectorId"], prior


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
for split_name, lab in make_splits().items():
    sizes = check_split(split_name, lab)
    te, det_table, prior = target_features(lab)
    X = inc.set_index("kid")[BASE_FEATURES].join(te).fillna(0)
    feat_names = list(X.columns)
    results["features"] = feat_names
    y = inc.set_index("kid")["y"]
    idx = {k: lab[lab == k].index for k in ["train", "val", "test"]}
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
        clf = HistGradientBoostingClassifier(
            learning_rate=0.1, max_iter=500, max_leaf_nodes=63, min_samples_leaf=40,
            l2_regularization=1.0, max_features=0.8, early_stopping=True, n_iter_no_change=20,
            class_weight="balanced", random_state=seed)
        clf.fit(X.loc[idx["train"]], y[idx["train"]], X_val=X.loc[idx["val"]], y_val=y[idx["val"]])
        pr = clf.predict_proba(X.loc[idx["test"]])
        assert np.allclose(pr.sum(axis=1), 1.0)
        mm = metrics(yt, pr.argmax(axis=1))
        mm["n_iter"] = int(clf.n_iter_)
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
