"""E1g: evaluate the LLM-only baseline and the proposed agent from the E1f cache.

Inputs (from e1f_llm.py): experiments/results/e1f_sample_{val,test}.csv and the
cached LLM judgments in experiments/results/e1f_llm_cache.jsonl.

Methods compared on the SAME sampled test incidents:
  gbdt            argmax of GBDT probabilities, no escalation
  gbdt_esc        GBDT with confidence escalation at the E1e operating point (tau = 0.50)
  llm_only        LLM label from the evidence summary alone, no escalation
  agent_llm       the LLM's own label when it also sees ML, SHAP, similar cases and rules
  agent           proposed agent: fuse_evidence (s = w_ml p + (1 - w_ml) q) + decide()
                  escalation on low confidence, ML/LLM conflict, and (optionally) fired rules
The agent's w_ml, tau and rule policy are chosen on the validation sample only
(lowest MR with ER <= ER_BUDGET, ties broken by higher macro-F1), then applied
once to the test sample. 95% bootstrap intervals (2,000 resamples) are reported.

MR = TP incidents auto-triaged with a non-TP label / all TP incidents
ER = escalated incidents / all incidents
Macro-F1 and TP recall use the final label of every incident (escalated or not).

Usage (run from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e1g_agent_eval.py --model gemini-3.8-flash
Writes experiments/results/e1g_agent_eval.json.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.agent.evidence import load_alert_rows  # noqa: E402
from soc_agent.decision.fusion import LLMJudgment, decide, fuse_evidence  # noqa: E402
from soc_agent.knowledge.rules import RuleInput, fired_rules  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="gemini-3.8-flash")
args = ap.parse_args()
R = Path("experiments/results")
LABELS = ["TP", "BP", "FP"]
ER_BUDGET = 0.20
GBDT_TAU = 0.50          # E1e operating point (selected on the full validation split)
W_GRID = np.round(np.arange(0.0, 1.01, 0.1), 2)
TAU_GRID = [0.0] + np.round(np.arange(0.50, 0.951, 0.05), 2).tolist()
RULE_POLICIES = ["none", "R2-R5", "all"]  # R1 is a weak signal (E1e), so it can be left out
B = 2000

cache = [json.loads(line) for line in (R / "e1f_llm_cache.jsonl").read_text().splitlines()]
cache = pd.DataFrame([c for c in cache if c["model"] == args.model])


def load(split: str) -> pd.DataFrame:
    s = pd.read_csv(R / f"e1f_sample_{split}.csv")
    for mode in ["llm_only", "agent"]:
        c = cache[cache["mode"] == mode].set_index("incident")
        s[f"{mode}_label"] = s["incident"].map(c["label"])
        s[f"{mode}_conf"] = s["incident"].map(c["confidence"])
    missing = s[["llm_only_label", "agent_label"]].isna().any(axis=1)
    if missing.any():
        print(f"{split}: {missing.sum()} incidents without both judgments are dropped")
    s = s[~missing].reset_index(drop=True)
    rows = load_alert_rows(s["incident"].tolist())
    fired = []
    for k in s["incident"]:
        a = rows[rows["kid"] == k]
        techs = {t for x in a["techniques"].dropna() for t in x.split(";") if t}
        fired.append(fired_rules(RuleInput.from_categories(set(a["category"]), techs)))
    s["rules"] = fired
    return s


def metrics(y, label, esc):
    y, label, esc = np.asarray(y), np.asarray(label), np.asarray(esc, bool)
    tp = y == "TP"
    return {"macro_f1": float(f1_score(y, label, labels=LABELS, average="macro", zero_division=0)),
            "tp_recall": float((tp & (label == "TP")).sum() / max(1, tp.sum())),
            "mr": float((tp & ~esc & (label != "TP")).sum() / max(1, tp.sum())),
            "er": float(esc.mean()),
            "auto_accuracy": float((label[~esc] == y[~esc]).mean()) if (~esc).any() else None}


def agent_run(s, w, tau, rule_policy):
    labels, esc = [], []
    for _, r in s.iterrows():
        rules = [] if rule_policy == "none" else \
            [x for x in r["rules"] if rule_policy == "all" or x != "R1"]
        d = fuse_evidence([r.p_tp, r.p_bp, r.p_fp], LLMJudgment(r.agent_label, r.agent_conf), rules, w_ml=w)
        d = decide(d, tau=tau, rules_fired=rules)
        labels.append(d.label)
        esc.append(d.status == "NEEDS_HUMAN_REVIEW")
    return np.array(labels), np.array(esc)


def methods(s, w, tau, rule_policy):
    p = s[["p_tp", "p_bp", "p_fp"]].to_numpy()
    none = np.zeros(len(s), bool)
    a_lab, a_esc = agent_run(s, w, tau, rule_policy)
    return {"gbdt": (s["gbdt"].to_numpy(), none),
            "gbdt_esc": (s["gbdt"].to_numpy(), p.max(axis=1) < GBDT_TAU),
            "llm_only": (s["llm_only_label"].to_numpy(), none),
            "agent_llm": (s["agent_label"].to_numpy(), none),
            "agent": (a_lab, a_esc)}


def bootstrap(y, label, esc, seed=0):
    rng = np.random.default_rng(seed)
    y, label, esc = np.asarray(y), np.asarray(label), np.asarray(esc)
    vals = {k: [] for k in ["macro_f1", "tp_recall", "mr", "er"]}
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        m = metrics(y[i], label[i], esc[i])
        for k in vals:
            vals[k].append(m[k])
    return {k: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
            for k, v in vals.items()}


val, test = load("val"), load("test")
out = {"model": args.model, "er_budget": ER_BUDGET, "gbdt_tau": GBDT_TAU,
       "n": {"val": len(val), "test": len(test)},
       "class_counts": {"val": val["y"].value_counts().to_dict(), "test": test["y"].value_counts().to_dict()}}

# select the agent's operating point on validation only
grid = []
for rp in RULE_POLICIES:
    for w in W_GRID:
        for tau in TAU_GRID:
            lab, esc = agent_run(val, float(w), tau, rp)
            grid.append({"rule_policy": rp, "w_ml": float(w), "tau": tau, **metrics(val["y"], lab, esc)})
grid = pd.DataFrame(grid)
ok = grid[grid["er"] <= ER_BUDGET]
best = (ok if len(ok) else grid).sort_values(["mr", "macro_f1", "er"], ascending=[True, False, True]).iloc[0]
out["selected_on_val"] = {k: (float(best[k]) if k != "rule_policy" else best[k])
                          for k in ["rule_policy", "w_ml", "tau", "mr", "er", "macro_f1"]}
if not len(ok):
    out["selected_on_val"]["note"] = f"no point with ER <= {ER_BUDGET}; lowest MR overall"
grid.round(4).to_csv(R / "e1g_val_grid.csv", index=False)

w, tau, rp = float(best["w_ml"]), float(best["tau"]), best["rule_policy"]
for split, s in [("val", val), ("test", test)]:
    out[split] = {}
    for name, (lab, esc) in methods(s, w, tau, rp).items():
        m = {k: (round(v, 4) if v is not None else None) for k, v in metrics(s["y"], lab, esc).items()}
        if split == "test":
            m["ci95"] = bootstrap(s["y"], lab, esc)
        out[split][name] = m

# agent MR-ER curve on test at the selected w_ml and rule policy (for Fig. 2)
curve = []
for t in TAU_GRID:
    lab, esc = agent_run(test, w, t, rp)
    m = metrics(test["y"], lab, esc)
    curve.append({"tau": t, "mr": round(m["mr"], 4), "er": round(m["er"], 4)})
out["test_agent_curve"] = curve

# where the agent's LLM overrode the ML label, and whether that helped (test)
t = test.copy()
t["agent_label_final"], _ = agent_run(t, w, tau, rp)
dis = t[t["agent_label"] != t["gbdt"]]
out["test_llm_vs_ml_disagreements"] = {"n": len(dis),
                                       "llm_right": int((dis["agent_label"] == dis["y"]).sum()),
                                       "ml_right": int((dis["gbdt"] == dis["y"]).sum())}

c = cache[cache["incident"].isin(set(val["incident"]) | set(test["incident"]))]
out["cost"] = {mode: {"calls": int((c["mode"] == mode).sum()),
                      "mean_tokens_in": round(float(c.loc[c["mode"] == mode, "tokens_in"].mean())),
                      "mean_tokens_out": round(float(c.loc[c["mode"] == mode, "tokens_out"].mean())),
                      "mean_tokens_thinking": round(float(c.loc[c["mode"] == mode, "tokens_thinking"].mean())),
                      "mean_latency_s": round(float(c.loc[c["mode"] == mode, "latency_s"].mean()), 2)}
               for mode in ["llm_only", "agent"]}
json.dump(out, open(R / "e1g_agent_eval.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ["n", "class_counts", "selected_on_val", "test",
                                      "test_llm_vs_ml_disagreements", "cost"]}, indent=1))
