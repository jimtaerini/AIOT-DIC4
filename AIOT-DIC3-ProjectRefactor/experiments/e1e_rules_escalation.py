"""E1e: kill-chain rules R1–R5 and confidence escalation without an LLM (tasks 4.3, 5.2–5.4 partial).

Incident split, GBDT seed 0 (model from e1d). With no LLM, fusion reduces to
s = p, so conflict never fires; GUIDE has no raw logs, so the sufficiency
check is not applied here. Two escalation policies are compared:
  conf        escalate when max(p) < tau
  conf+rules  escalate when max(p) < tau or any of R1–R5 fires
For each policy and tau in [0.50, 0.95] (step 0.05) we compute
  MR = TP incidents auto-triaged with a non-TP label / all TP incidents
  ER = escalated incidents / all incidents
Operating points are chosen on the validation split only: the lowest MR with
ER <= ER_BUDGET (and the R5 threshold in {3, 4, 5}), then reported on test.

Usage (run from AIOT-DIC3-ProjectRefactor/, after e1d):
    ../.venv/bin/python experiments/e1e_rules_escalation.py
Writes experiments/results/e1e_rules_escalation.json and e1e_curve.csv.
"""
import json
import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.analytics.features import build_matrix, load_tables, make_splits  # noqa: E402
from soc_agent.analytics.triage_model import TriageModel  # noqa: E402
from soc_agent.knowledge.rules import CATEGORY_TO_TACTIC, RULE_IDS, RuleInput, fired_rules  # noqa: E402

ER_BUDGET = 0.20
TAUS = np.round(np.arange(0.50, 0.951, 0.05), 2)
R5_OPTIONS = [3, 4, 5]
t0 = time.time()

inc, alerts = load_tables()
lab = make_splits(inc)["incident"]
X, y, idx, _, _ = build_matrix(inc, alerts, lab)
model = TriageModel.load("data/processed/models/e1_gbdt_incident_seed0.pkl")
print(f"[{time.time() - t0:5.0f}s] features built", flush=True)

# --- rule inputs per incident: categories (cat_* counts) and T1070 presence ---
I = inc.set_index("kid")
cat_cols = [c for c in I.columns if c.startswith("cat_")]
cats = {c[4:]: I[c].to_numpy() > 0 for c in cat_cols}
tactic = {}
for cat, t in CATEGORY_TO_TACTIC.items():
    if cat in cats:
        tactic[t] = tactic.get(t, np.zeros(len(I), bool)) | cats[cat]
n_tactics = np.sum(np.stack(list(tactic.values())), axis=0)
t1070 = duckdb.sql("""
  SELECT source || ':' || OrgId || ':' || IncidentId AS kid FROM (
    SELECT 'train' AS source, * FROM 'data/processed/guide_train.parquet'
    UNION ALL BY NAME SELECT 'test' AS source, * FROM 'data/processed/guide_test.parquet')
  WHERE regexp_matches(MitreTechniques, '(^|;)T1070(\\.|;|$)')
  GROUP BY 1""").df()["kid"]
has_t1070 = I.index.isin(set(t1070))
z = np.zeros(len(I), bool)
R = pd.DataFrame({
    "R1": tactic.get("Exfiltration", z) | tactic.get("Impact", z) | cats.get("Ransomware", z),
    "R2": tactic.get("CredentialAccess", z) & tactic.get("LateralMovement", z),
    "R3": tactic.get("InitialAccess", z) & (tactic.get("Execution", z) | tactic.get("Persistence", z)
                                            | tactic.get("PrivilegeEscalation", z)),
    "R4": has_t1070,
}, index=I.index)
for k in R5_OPTIONS:
    R[f"R5_{k}"] = n_tactics >= k

# cross-check the vectorized rules against the reference implementation
rng = np.random.default_rng(0)
for key in rng.choice(I.index.to_numpy(), size=3000, replace=False):
    row = I.loc[key]
    present = [c[4:] for c in cat_cols if row[c] > 0]
    ref = fired_rules(RuleInput.from_categories(present, ["T1070"] if R.at[key, "R4"] else []), r5_min_tactics=4)
    vec = [r for r in ["R1", "R2", "R3", "R4"] if R.at[key, r]] + (["R5"] if R.at[key, "R5_4"] else [])
    assert ref == vec, (key, ref, vec)
print(f"[{time.time() - t0:5.0f}s] rules computed and cross-checked", flush=True)

out = {"er_budget": ER_BUDGET, "taus": TAUS.tolist(), "rule_stats_val": {}, "curves": [], "selected": {}}

# --- rule statistics on validation: firing rate and TP share when fired ---
yv = y[idx["val"]]
base_tp = float((yv == 0).mean())
for r in ["R1", "R2", "R3", "R4"] + [f"R5_{k}" for k in R5_OPTIONS]:
    f = R.loc[idx["val"], r].to_numpy()
    out["rule_stats_val"][r] = {"fire_rate": round(float(f.mean()), 4),
                                "tp_share_when_fired": round(float((yv[f] == 0).mean()), 4) if f.any() else None,
                                "tp_share_base": round(base_tp, 4)}


def evaluate(keys, p, risk, tau):
    yy = y[keys].to_numpy()
    esc = (p.max(axis=1) < tau) | risk
    auto = ~esc
    tp = yy == 0
    mr = float((tp & auto & (p.argmax(axis=1) != 0)).sum() / tp.sum())
    er = float(esc.mean())
    acc_auto = float((p.argmax(axis=1)[auto] == yy[auto]).mean()) if auto.any() else None
    return {"mr": mr, "er": er, "auto_accuracy": acc_auto}


probs = {s: model.predict_proba(X.loc[idx[s]]) for s in ["val", "test"]}
policies = {"conf": None} | {f"conf+rules(R5>={k})": k for k in R5_OPTIONS}
for split in ["val", "test"]:
    keys = idx[split]
    for pol, k in policies.items():
        risk = np.zeros(len(keys), bool) if k is None else \
            R.loc[keys, ["R1", "R2", "R3", "R4", f"R5_{k}"]].any(axis=1).to_numpy()
        for tau in [0.0] + TAUS.tolist():   # tau = 0: escalate on rules only
            m = evaluate(keys, probs[split], risk, tau)
            out["curves"].append({"split": split, "policy": pol, "tau": tau, **{a: round(b, 4) if b is not None else None
                                                                                 for a, b in m.items()}})
    nores = evaluate(keys, probs[split], np.zeros(len(keys), bool), 0.0)
    out["curves"].append({"split": split, "policy": "gbdt_no_escalation", "tau": 0.0,
                          **{a: round(b, 4) for a, b in nores.items()}})

curves = pd.DataFrame(out["curves"])
curves.to_csv("experiments/results/e1e_curve.csv", index=False)
val = curves[curves.split == "val"]
for fam, mask in {"conf": val.policy == "conf", "conf+rules": val.policy.str.startswith("conf+rules")}.items():
    ok = val[mask & (val.er <= ER_BUDGET)]
    best = ok.sort_values(["mr", "er"]).iloc[0] if len(ok) else None
    if best is None:
        out["selected"][fam] = {"note": f"no point with ER <= {ER_BUDGET} on validation"}
        continue
    test_row = curves[(curves.split == "test") & (curves.policy == best.policy) & (curves.tau == best.tau)].iloc[0]
    out["selected"][fam] = {"policy": best.policy, "tau": float(best.tau),
                            "val": {"mr": float(best.mr), "er": float(best.er)},
                            "test": {"mr": float(test_row.mr), "er": float(test_row.er),
                                     "auto_accuracy": float(test_row.auto_accuracy)}}
out["seconds"] = round(time.time() - t0)
json.dump(out, open("experiments/results/e1e_rules_escalation.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ["rule_stats_val", "selected"]}, indent=1))
print(curves[(curves.split == "test")].to_string(index=False))
