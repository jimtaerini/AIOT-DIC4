"""E1f: LLM-only baseline and LLM-in-the-loop agent on GUIDE (incident split).

Model: Gemini via the free API tier (GEMINI_API_KEY), temperature 0, low thinking.
Two modes per sampled incident:
  llm_only  the LLM sees only the readable evidence summary (no ML, no KB)
  agent     the LLM also sees GBDT probabilities, top-5 SHAP features, 5 similar
            past incidents with labels, and the risk rules that fired
            (no ATT&CK retrieval yet: "agent without RAG")
Samples are drawn at random (natural class mix) from the validation or test
split with a fixed seed, so the same incidents are reused across runs. Calls
are cached in experiments/results/e1f_llm_cache.jsonl; rerunning resumes.

Usage (run from AIOT-DIC3-ProjectRefactor/, after e1d):
    ../.venv/bin/python experiments/e1f_llm.py --split val --n 20
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.agent.evidence import load_alert_rows, summarize  # noqa: E402
from soc_agent.agent.llm import GeminiJudge, ModelUnavailable, QuotaExhausted  # noqa: E402
from soc_agent.agent.prompts import SYSTEM, agent_prompt, llm_only_prompt  # noqa: E402
from soc_agent.analytics.explain import Explainer  # noqa: E402
from soc_agent.analytics.features import build_matrix, load_tables, make_splits  # noqa: E402
from soc_agent.analytics.similar import SimilarIncidents  # noqa: E402
from soc_agent.analytics.triage_model import TriageModel  # noqa: E402
from soc_agent.knowledge.rules import RULE_DESCRIPTIONS, RuleInput, fired_rules  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--split", choices=["val", "test"], required=True)
ap.add_argument("--n", type=int, required=True)
ap.add_argument("--modes", default="llm_only,agent")
ap.add_argument("--model", default="gemini-4-hydrogen")
ap.add_argument("--interval", type=float, default=4.0, help="seconds between call starts (free-tier rate limit)")
ap.add_argument("--workers", type=int, default=1, help="parallel calls (paid tier)")
args = ap.parse_args()
t0 = time.time()
CACHE = "experiments/results/e1f_llm_cache.jsonl"
SAMPLE_SEED = {"val": 101, "test": 202}

inc, alerts = load_tables()
lab = make_splits(inc)["incident"]
pool = lab[lab == args.split].index.to_numpy()
order = np.random.default_rng(SAMPLE_SEED[args.split]).permutation(pool)
keys = list(order[:args.n])  # prefix of a fixed permutation: larger n extends the same sample
Path(f"experiments/results/e1f_keys_{args.split}.txt").write_text("\n".join(keys) + "\n")

X, y, idx, _, _ = build_matrix(inc, alerts, lab)
model = TriageModel.load("data/processed/models/e1_gbdt_incident_seed0.pkl")
explainer = Explainer(model)
similar = SimilarIncidents(k=5).fit(X.loc[idx["train"]], y[idx["train"]])
Xs = X.loc[keys]
p = model.predict_proba(Xs)
tops = explainer.top_features(Xs, k=5)
sims = similar.query(Xs)
rows = load_alert_rows(keys)
print(f"[{time.time() - t0:5.0f}s] context ready for {len(keys)} {args.split} incidents", flush=True)

judge = GeminiJudge(model=args.model, min_interval_s=args.interval, cache_path=CACHE)
modes = args.modes.split(",")


def run_incident(i: int, key: str) -> None:
    summary = summarize(key, rows)
    a = rows[rows["kid"] == key]
    techs = {t for s in a["techniques"].dropna() for t in s.split(";") if t}
    rules = fired_rules(RuleInput.from_categories(set(a["category"]), techs))
    for mode in modes:
        prompt = llm_only_prompt(summary) if mode == "llm_only" else \
            agent_prompt(summary, p[i], tops[i], sims[i], rules, RULE_DESCRIPTIONS)
        judge.judge(mode, key, SYSTEM, prompt)


done = 0
try:
    with ThreadPoolExecutor(max_workers=args.workers) as pool_ex:
        for fut in [pool_ex.submit(run_incident, i, k) for i, k in enumerate(keys)]:
            fut.result()
            done += 1
            if done % 10 == 0:
                print(f"[{time.time() - t0:5.0f}s] {done}/{len(keys)} incidents", flush=True)
except QuotaExhausted as e:
    print(f"Quota exhausted after {done} incidents; rerun later to resume. {e}", flush=True)
except ModelUnavailable as e:
    print(f"Model overloaded (503) after {done} incidents; rerun later to resume. {e}", flush=True)

# summary of this sample (only incidents with cached results for every mode)
recs = pd.DataFrame([r for k, r in judge.cache.items() if k[1] == args.model and k[2] in set(keys)])
sample = pd.DataFrame({"incident": keys, "y": [["TP", "BP", "FP"][int(v)] for v in y[keys]],
                       "p_tp": p[:, 0], "p_bp": p[:, 1], "p_fp": p[:, 2],
                       "gbdt": [["TP", "BP", "FP"][int(v)] for v in p.argmax(axis=1)]})
sample.to_csv(f"experiments/results/e1f_sample_{args.split}.csv", index=False)
out = {"split": args.split, "model": args.model, "n_requested": len(keys), "incidents_done": done,
       "seconds": round(time.time() - t0)}
for mode in modes:
    r = recs[recs["mode"] == mode].merge(sample, on="incident")
    if r.empty:
        continue
    out[mode] = {"n": len(r), "parse_errors": int(r["label"].isna().sum()),
                 "accuracy": round(float((r["label"] == r["y"]).mean()), 4),
                 "gbdt_accuracy_same_incidents": round(float((r["gbdt"] == r["y"]).mean()), 4),
                 "tp_recall": round(float(((r["y"] == "TP") & (r["label"] == "TP")).sum()
                                          / max(1, (r["y"] == "TP").sum())), 4),
                 "mean_tokens_in": round(float(r["tokens_in"].mean())),
                 "mean_tokens_out": round(float(r["tokens_out"].mean())),
                 "mean_tokens_thinking": round(float(r["tokens_thinking"].mean())),
                 "mean_latency_s": round(float(r["latency_s"].mean()), 2),
                 "confidence_counts": r["confidence"].value_counts().to_dict()}
print(json.dumps(out, indent=1))
