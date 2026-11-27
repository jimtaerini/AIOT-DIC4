"""E5: cost of the LLM steps, compiled from every recorded call (no new API calls).

Sources: e1f_llm_cache.jsonl (triage), e2_llm_cache.jsonl (ATT&CK mapping),
e4_report_cache.jsonl (report writing), e4_judge_cache.jsonl (evaluation only,
not part of the agent). Prices are the Gemini API list prices per 1M tokens
(output includes thinking tokens), checked on 2026-11-27.

Usage (from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e5_cost.py
Writes experiments/results/e5_cost.json.
"""
import json
from pathlib import Path

import pandas as pd

R = Path("experiments/results")
PRICES = {  # USD per 1M tokens: (input, output incl. thinking)
    "gemini-3.8-flash": {"until_2026-12-31": (0.75, 3.75), "from_2027-01-01": (1.50, 7.50)},
    "gemini-4-hydrogen": {"until_2026-12-31": (1.50, 7.50), "from_2027-01-01": (1.50, 7.50)},
}
F, H = "gemini-3.8-flash", "gemini-4-hydrogen"
STEPS = [("e1f_llm_cache.jsonl", "llm_only", F, "E1 triage, LLM only"),
         ("e1f_llm_cache.jsonl", "agent", F, "E1 triage, agent reasoning step"),
         ("e2_llm_cache.jsonl", "llm_only", F, "E2 ATT&CK mapping, LLM only"),
         ("e2_llm_cache.jsonl", "llm_rag", F, "E2 ATT&CK mapping, LLM + RAG"),
         ("e4_report_cache.jsonl", "no_rag", F, "E4 report, without RAG"),
         ("e4_report_cache.jsonl", "rag", F, "E4 report, with RAG"),
         ("e4_judge_cache.jsonl", "no_rag", H, "E4 LLM judge, report without RAG (evaluation only)"),
         ("e4_judge_cache.jsonl", "rag", H, "E4 LLM judge, report with RAG (evaluation only)")]

out = {"prices_usd_per_1m_tokens": PRICES, "steps": [], "totals": {}}
spent = {"until_2026-12-31": 0.0, "from_2027-01-01": 0.0}
for fname, mode, model, name in STEPS:
    f = R / fname
    if not f.exists():
        continue
    df = pd.DataFrame([json.loads(x) for x in f.read_text().splitlines()])
    df = df[(df["mode"] == mode) & (df["model"] == model) & (df["tokens_in"] > 0)]
    if df.empty:
        continue
    tin, tout = df["tokens_in"].mean(), (df["tokens_out"] + df["tokens_thinking"]).mean()
    row = {"step": name, "model": model, "calls": len(df), "mean_tokens_in": round(float(tin)),
           "mean_tokens_out_incl_thinking": round(float(tout)),
           "mean_latency_s": round(float(df["latency_s"].mean()), 2),
           "p95_latency_s": round(float(df["latency_s"].quantile(0.95)), 2),
           "mean_attempts": round(float(df["attempts"].mean()), 2)}
    for period, (pi, po) in PRICES[model].items():
        row[f"usd_per_call_{period}"] = round((tin * pi + tout * po) / 1e6, 6)
        spent[period] += float((df["tokens_in"].sum() * pi + (df["tokens_out"] + df["tokens_thinking"]).sum() * po) / 1e6)
    out["steps"].append(row)

steps = {s["step"]: s for s in out["steps"]}
# the agent's per-incident LLM cost = one reasoning call + one RAG report (no planner tool calls yet)
per_inc = {}
for period in ["until_2026-12-31", "from_2027-01-01"]:
    k = f"usd_per_call_{period}"
    parts = [steps[s][k] for s in ["E1 triage, agent reasoning step", "E4 report, with RAG"] if s in steps]
    per_inc[period] = round(sum(parts), 6)
out["totals"] = {"agent_llm_usd_per_incident": per_inc,
                 "agent_llm_latency_s_per_incident": round(sum(steps[s]["mean_latency_s"] for s in
                                                               ["E1 triage, agent reasoning step", "E4 report, with RAG"]
                                                               if s in steps), 2),
                 "tool_calls_per_incident": 0,
                 "note": "The ReAct planner (tool calls) is not used in E1/E2/E4; E3 will add it.",
                 "all_calls": int(sum(s["calls"] for s in out["steps"])),
                 "usd_spent_on_these_calls": {k: round(v, 4) for k, v in spent.items()}}
json.dump(out, open(R / "e5_cost.json", "w"), indent=1)
print(pd.DataFrame(out["steps"]).to_string(index=False))
print(json.dumps(out["totals"], indent=1))
