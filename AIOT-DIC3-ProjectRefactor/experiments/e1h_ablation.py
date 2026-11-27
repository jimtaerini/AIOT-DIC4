"""Ablation of the triage agent on the E1f samples (50 validation, 150 test incidents).

Configurations
  full            the agent of E1g (LLM sees ML, SHAP, similar incidents, rules; fusion + conflict escalation)
  no_analytics    module 5 removed: no GBDT probabilities, SHAP or similar incidents; the LLM decides
                  alone from evidence and rules, and escalation can use only its confidence and the rules
  no_knowledge    module 6 removed: no kill-chain rules in the prompt and none can force escalation
  no_llm          module 4's reasoning step removed: GBDT + confidence escalation (as in E1e)
  no_escalation   all escalation conditions removed: the full agent's label is final
Each configuration that has free parameters (w_ml, tau, rule policy) is tuned on the
validation sample with the same rule as E1g (lowest MR with ER <= 20%, ties by macro-F1),
then reported once on the test sample.

Usage (from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e1h_ablation.py --workers 8
Writes experiments/results/e1h_ablation.json (LLM calls cached in e1f_llm_cache.jsonl).
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.agent.evidence import load_alert_rows, summarize  # noqa: E402
from soc_agent.agent.llm import GeminiJudge  # noqa: E402
from soc_agent.agent.prompts import SYSTEM, ablation_prompt  # noqa: E402
from soc_agent.analytics.explain import Explainer  # noqa: E402
from soc_agent.analytics.features import build_matrix, load_tables, make_splits  # noqa: E402
from soc_agent.analytics.similar import SimilarIncidents  # noqa: E402
from soc_agent.analytics.triage_model import TriageModel  # noqa: E402
from soc_agent.decision.fusion import (CONFIDENCE_LEVELS, LLMJudgment, decide,  # noqa: E402
                                       fuse_evidence)
from soc_agent.knowledge.rules import RULE_DESCRIPTIONS, RuleInput, fired_rules  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="gemini-3.8-flash")
ap.add_argument("--workers", type=int, default=8)
args = ap.parse_args()
t0 = time.time()
R = Path("experiments/results")
LABELS = ["TP", "BP", "FP"]
ER_BUDGET, GBDT_TAU = 0.20, 0.50
W_GRID = np.round(np.arange(0.0, 1.01, 0.1), 2)
TAU_GRID = [0.0] + np.round(np.arange(0.50, 0.951, 0.05), 2).tolist()
RULE_POLICIES = ["none", "R2-R5", "all"]
N = {"val": 50, "test": 150}

# ---------------- context (same as E1f) ----------------
inc, alerts = load_tables()
lab = make_splits(inc)["incident"]
X, y, idx, _, _ = build_matrix(inc, alerts, lab)
model = TriageModel.load("data/processed/models/e1_gbdt_incident_seed0.pkl")
explainer = Explainer(model)
similar = SimilarIncidents(k=5).fit(X.loc[idx["train"]], y[idx["train"]])
data = {}
for split, n in N.items():
    keys = (R / f"e1f_keys_{split}.txt").read_text().split()[:n]
    s = pd.read_csv(R / f"e1f_sample_{split}.csv").set_index("incident").loc[keys].reset_index()
    assert len(s) == n, f"run e1f_llm.py --split {split} --n {n} first"
    Xs = X.loc[keys]
    rows = load_alert_rows(keys)
    rules = []
    for k in keys:
        a = rows[rows["kid"] == k]
        techs = {t for x in a["techniques"].dropna() for t in x.split(";") if t}
        rules.append(fired_rules(RuleInput.from_categories(set(a["category"]), techs)))
    data[split] = {"s": s, "keys": keys, "rows": rows, "p": model.predict_proba(Xs),
                   "tops": explainer.top_features(Xs, k=5), "sims": similar.query(Xs), "rules": rules}
print(f"[{time.time() - t0:5.0f}s] context ready", flush=True)

judge = GeminiJudge(model=args.model, min_interval_s=0.2, cache_path=R / "e1f_llm_cache.jsonl")


def run(split: str, i: int) -> None:
    d = data[split]
    k = d["keys"][i]
    summary = summarize(k, d["rows"])
    judge.judge("ablate_no_analytics", k, SYSTEM,
                ablation_prompt(summary, rules=d["rules"][i], rule_text=RULE_DESCRIPTIONS))
    judge.judge("ablate_no_knowledge", k, SYSTEM,
                ablation_prompt(summary, p=d["p"][i], top_features=d["tops"][i], similar=d["sims"][i]))


with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs = [ex.submit(run, sp, i) for sp in N for i in range(N[sp])]
    for n, f in enumerate(futs, 1):
        f.result()
        if n % 50 == 0:
            print(f"[{time.time() - t0:5.0f}s] {n}/{len(futs)} incidents", flush=True)


# ---------------- decisions ----------------
def llm(split: str, mode: str):
    c = {k[2]: v for k, v in judge.cache.items() if k[0] == mode and k[1] == args.model}
    return [c[k] for k in data[split]["keys"]]


def filt(rules, policy):
    return [] if policy == "none" else [r for r in rules if policy == "all" or r != "R1"]


def decide_with_ml(split, mode, w, tau, policy):
    d, J = data[split], llm(split, mode)
    lab_, esc = [], []
    for i in range(len(J)):
        rl = filt(d["rules"][i], policy)
        dec = decide(fuse_evidence(d["p"][i], LLMJudgment(J[i]["label"], J[i]["confidence"]), rl, w_ml=w),
                     tau=tau, rules_fired=rl)
        lab_.append(dec.label)
        esc.append(dec.status == "NEEDS_HUMAN_REVIEW")
    return np.array(lab_), np.array(esc)


def decide_llm_only(split, mode, _w, tau, policy):
    """No analytics: the label is the LLM's; escalate on its confidence or on a fired rule."""
    d, J = data[split], llm(split, mode)
    lab_ = np.array([j["label"] for j in J])
    conf = np.array([CONFIDENCE_LEVELS[j["confidence"]] for j in J])
    rl = np.array([bool(filt(r, policy)) for r in d["rules"]])
    return lab_, (conf < tau) | rl


def metrics(yy, lab_, esc):
    yy, lab_, esc = np.asarray(yy), np.asarray(lab_), np.asarray(esc, bool)
    tp = yy == "TP"
    return {"macro_f1": round(float(f1_score(yy, lab_, labels=LABELS, average="macro", zero_division=0)), 4),
            "tp_recall": round(float((tp & (lab_ == "TP")).sum() / tp.sum()), 4),
            "mr": round(float((tp & ~esc & (lab_ != "TP")).sum() / tp.sum()), 4),
            "er": round(float(esc.mean()), 4)}


def tune(fn, mode, ws):
    grid = []
    for pol in RULE_POLICIES:
        for w in ws:
            for tau in TAU_GRID:
                lab_, esc = fn("val", mode, float(w), tau, pol)
                grid.append({"policy": pol, "w": float(w), "tau": tau, **metrics(data["val"]["s"]["y"], lab_, esc)})
    g = pd.DataFrame(grid)
    ok = g[g["er"] <= ER_BUDGET]
    return (ok if len(ok) else g).sort_values(["mr", "macro_f1", "er"], ascending=[True, False, True]).iloc[0]


out = {"model": args.model, "n": N, "configs": {}}
B = 2000
rng = np.random.default_rng(0)
boot = [rng.integers(0, N["test"], N["test"]) for _ in range(B)]
yt = data["test"]["s"]["y"].to_numpy()


def report(name, lab_, esc, params):
    m = metrics(yt, lab_, esc)
    mrs = sorted(metrics(yt[b], lab_[b], esc[b])["mr"] for b in boot)
    m["mr_ci95"] = [mrs[int(0.025 * B)], mrs[int(0.975 * B) - 1]]
    out["configs"][name] = {**m, "params": params}


cfgs = {"full": (decide_with_ml, "agent", W_GRID), "no_knowledge": (decide_with_ml, "ablate_no_knowledge", W_GRID),
        "no_analytics": (decide_llm_only, "ablate_no_analytics", [0.0])}
for name, (fn, mode, ws) in cfgs.items():
    if name == "no_knowledge":   # rules are part of module 6: none may force escalation
        g = []
        for w in ws:
            for tau in TAU_GRID:
                lab_, esc = fn("val", mode, float(w), tau, "none")
                g.append({"policy": "none", "w": float(w), "tau": tau, **metrics(data["val"]["s"]["y"], lab_, esc)})
        g = pd.DataFrame(g)
        ok = g[g["er"] <= ER_BUDGET]
        best = (ok if len(ok) else g).sort_values(["mr", "macro_f1", "er"], ascending=[True, False, True]).iloc[0]
    else:
        best = tune(fn, mode, ws)
    lab_, esc = fn("test", mode, float(best["w"]), float(best["tau"]), best["policy"])
    report(name, lab_, esc, {"w_ml": float(best["w"]), "tau": float(best["tau"]), "rule_policy": best["policy"],
                             "val_mr": float(best["mr"]), "val_er": float(best["er"])})
    if name == "full":
        report("no_escalation", lab_, np.zeros(len(lab_), bool), {"from": "full, escalation off"})
pt = data["test"]["p"]
report("no_llm", np.array([LABELS[i] for i in pt.argmax(axis=1)]), pt.max(axis=1) < GBDT_TAU, {"tau": GBDT_TAU, "note": "GBDT + confidence escalation (E1e operating point)"})
out["llm_only_label_counts"] = {m: pd.Series([j["label"] for j in llm("test", m)]).value_counts().to_dict()
                                for m in ["ablate_no_analytics", "ablate_no_knowledge", "agent"]}
json.dump(out, open(R / "e1h_ablation.json", "w"), indent=1)
print(json.dumps(out, indent=1))
