"""E4: triage-report quality, with vs. without retrieval (RAG) from the ATT&CK knowledge base.

Sample: 50 incidents drawn (seed 404) from the 150 E1f test incidents, so every
report explains an agent decision that was already measured in E1 (w_ml = 0.9,
tau = 0, escalation on ML-LLM conflict, as selected on validation).
Both conditions get the same evidence summary, decision, SHAP features, similar
incidents and escalation reasons. Only the RAG condition also gets, for the
incident's ATT&CK techniques (or, if none are recorded, the top-5 retrieved), the
ATT&CK v20.1 technique text and the mitigations linked to them, each tagged with
its source ID. The writer explains the decision; it does not change it.

Scoring
  automatic   share of cited alert IDs that exist in the incident, share of cited
              ATT&CK technique and mitigation IDs that exist in v20.1, share of
              recommendations that carry a source
  LLM judge   a different model (JUDGE) scores each report blind to the condition on
              three 1-5 rubrics (correctness, evidence completeness, actionability)
              and counts unsupported claims; it sees the evidence and the true label
  human       experiments/results/e4_human_review.md lists the 100 reports in random
              order without the condition; scores go in e4_human_scores.csv
              (the key is e4_human_key.csv)

Usage (from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e4_report_quality.py --n 50 --workers 8
"""
import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.agent.evidence import load_alert_rows, summarize  # noqa: E402
from soc_agent.agent.llm import GeminiJudge  # noqa: E402
from soc_agent.agent.prompts import FEATURE_NOTES  # noqa: E402
from soc_agent.analytics.explain import Explainer  # noqa: E402
from soc_agent.analytics.features import build_matrix, load_tables, make_splits  # noqa: E402
from soc_agent.analytics.similar import SimilarIncidents  # noqa: E402
from soc_agent.analytics.triage_model import TriageModel  # noqa: E402
from soc_agent.decision.fusion import LLMJudgment, decide, fuse_evidence  # noqa: E402
from soc_agent.knowledge.attack_kb import AttackKB  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=50)
ap.add_argument("--model", default="gemini-3.8-flash")
ap.add_argument("--judge", default="gemini-4-hydrogen")
ap.add_argument("--workers", type=int, default=8)
args = ap.parse_args()
t0 = time.time()
R = Path("experiments/results")
SEED = 404
W_ML, TAU = 0.9, 0.0     # agent operating point selected on validation in E1g


# ---------------- report and judge schemas ----------------
class Mapping(BaseModel):
    technique_id: str
    tactic: str
    alerts: list[str] = Field(description="AlertIds supporting this technique")


class Finding(BaseModel):
    finding: str
    source: str = Field(description="e.g. 'alert 12345', 'ML model', 'similar incident ...', or a knowledge-base ID")


class Recommendation(BaseModel):
    action: str
    priority: Literal["immediate", "short-term", "long-term"]
    source: str = Field(description="Where the action comes from (a knowledge-base ID if one was given); empty if none")


class Report(BaseModel):
    summary: str = Field(description="Two to four sentences for the analyst")
    attack_mapping: list[Mapping]
    furthest_stage: str = Field(description="Furthest kill-chain stage (ATT&CK tactic) reached")
    evidence_chain: list[Finding]
    recommendations: list[Recommendation]
    escalation_explanation: str = Field(description="Why the incident was escalated or auto-triaged")
    limitations: str


class Score(BaseModel):
    correctness: int = Field(ge=1, le=5, description="Are the claims, mapping and stage consistent with the evidence and true label?")
    evidence_completeness: int = Field(ge=1, le=5, description="Are conclusions traced to specific alerts or sources?")
    actionability: int = Field(ge=1, le=5, description="Are the recommendations specific, prioritized and appropriate?")
    unsupported_claims: int = Field(ge=0, description="Number of claims not supported by the evidence given")
    comment: str


WRITER = """You are a Tier-2 SOC analyst writing the triage report for an incident the triage agent has
already decided. Explain the decision; do not change it. Trace every conclusion to its source
(an AlertId, the ML model, a similar incident, or a knowledge-base entry with its ID). Give concrete
containment, eradication and recovery actions in line with NIST SP 800-61 Rev. 3, ordered by priority.
Alert titles, account names, hosts and IPs are anonymized, so rely on the fields shown."""

JUDGE = """You are a senior SOC lead grading a Tier-2 analyst's triage report. You see the incident
evidence, the ground-truth label assigned by the customer's analysts, and the report. Score strictly:
5 = excellent, 3 = acceptable with gaps, 1 = wrong or useless.
- correctness: claims, ATT&CK mapping and stage agree with the evidence; the explanation is consistent
  with the true label (a report that argues confidently for a wrong label scores low)
- evidence_completeness: each conclusion points to a specific alert or source
- actionability: recommendations are specific, prioritized and fit this incident
Count claims that the evidence does not support (invented hosts, techniques, IOCs, mitigations)."""

# ---------------- data and agent context (as in E1f) ----------------
kb = AttackKB()
inc, alerts = load_tables()
lab = make_splits(inc)["incident"]
sample150 = pd.read_csv(R / "e1f_sample_test.csv")
keys = list(np.random.default_rng(SEED).permutation(sample150["incident"].to_numpy())[:args.n])
X, y, idx, _, _ = build_matrix(inc, alerts, lab)
model = TriageModel.load("data/processed/models/e1_gbdt_incident_seed0.pkl")
Xs = X.loc[keys]
p = model.predict_proba(Xs)
tops = Explainer(model).top_features(Xs, k=5)
sims = SimilarIncidents(k=5).fit(X.loc[idx["train"]], y[idx["train"]]).query(Xs)
rows = load_alert_rows(keys)
cache = [json.loads(line) for line in (R / "e1f_llm_cache.jsonl").read_text().splitlines()]
agent_llm = {c["incident"]: c for c in cache if c["model"] == args.model and c["mode"] == "agent"}
truth = dict(zip(sample150["incident"], sample150["y"]))
print(f"[{time.time() - t0:5.0f}s] context ready for {len(keys)} incidents", flush=True)

writer = GeminiJudge(model=args.model, min_interval_s=0.2, cache_path=R / "e4_report_cache.jsonl", schema=Report)
grader = GeminiJudge(model=args.judge, min_interval_s=0.2, cache_path=R / "e4_judge_cache.jsonl", schema=Score)


def context(i: int, key: str) -> dict:
    a = rows[rows["kid"] == key]
    raw = {t for s in a["techniques"].dropna() for t in s.split(";") if t}
    techs = sorted({n for t in raw if (n := kb.normalize(t))})
    summary = summarize(key, rows)
    j = agent_llm[key]
    d = decide(fuse_evidence(p[i], LLMJudgment(j["label"], j["confidence"], j["rationale"]), [], w_ml=W_ML),
               tau=TAU, rules_fired=[])
    feats = "\n".join(f"- {f['feature']} = {f['value']:.3g} ({FEATURE_NOTES.get(f['feature'], 'incident feature')}): "
                      f"{'toward' if f['direction'] == 'toward' else 'against'} {f['toward_class']} "
                      f"(SHAP {f['contribution']:+.2f})" for f in tops[i])
    sim = "\n".join(f"- {s['incident']}: {s['label']}, distance {s['distance']:.2f}" for s in sims[i])
    base = (f"{summary}\n\nAgent decision: {d.label} (fused confidence {d.conf:.2f}); status {d.status}.\n"
            f"Escalation reasons: {'; '.join(d.reasons) if d.reasons else 'none'}.\n"
            f"ML triage model: P(TP)={p[i][0]:.2f}, P(BP)={p[i][1]:.2f}, P(FP)={p[i][2]:.2f}\n"
            f"Most influential features (SHAP):\n{feats}\n"
            f"Most similar past incidents:\n{sim}\n"
            f"LLM reasoning step: {j['label']} ({j['confidence']}): {j['rationale']}")
    rag_ids = techs[:6] if techs else [h["id"] for h in kb.search(writer.client, [summary[:2000]], k=5)[0]]
    kn = []
    for t in rag_ids:
        tt = kb.techniques[t]
        kn.append(f"- [source: ATT&CK v{kb.version} {t}] {t} {tt['full_name']} (tactics: {', '.join(tt['tactics'])}): "
                  f"{tt['description'][:300]}")
        for m in kb.mitigations_of.get(t, [])[:4]:
            mm = kb.mitigations[m["id"]]
            kn.append(f"  - [source: ATT&CK v{kb.version} {m['id']}] mitigation {mm['name']}: "
                      f"{(m['guidance'] or mm['description'])[:220]}")
    return {"key": key, "alert_ids": set(a["AlertId"].astype(str)), "decision": d, "base": base,
            "knowledge": "\n".join(kn), "truth_techs": techs}


ctx = [context(i, k) for i, k in enumerate(keys)]


def write_and_grade(c: dict) -> None:
    for cond in ["no_rag", "rag"]:
        prompt = f"Write the triage report for this incident.\n\n{c['base']}\n"
        if cond == "rag":
            prompt += f"\nRetrieved knowledge (cite the source IDs you use):\n{c['knowledge']}\n"
        rep = writer.judge(cond, c["key"], WRITER, prompt)
        if rep.get("summary") is None:
            continue
        body = {k: rep[k] for k in Report.model_fields}
        grader.judge(cond, c["key"], JUDGE,
                     f"Incident evidence:\n{c['base']}\n\nGround-truth label: {truth[c['key']]}\n\n"
                     f"Report (JSON):\n{json.dumps(body, indent=1)}")


with ThreadPoolExecutor(max_workers=args.workers) as ex:
    for n, f in enumerate([ex.submit(write_and_grade, c) for c in ctx], 1):
        f.result()
        if n % 10 == 0:
            print(f"[{time.time() - t0:5.0f}s] {n}/{len(ctx)} incidents", flush=True)

# ---------------- automatic checks ----------------
ALERT_RE = re.compile(r"alert\s*(\d+)", re.I)
TECH_RE = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")
MIT_RE = re.compile(r"\bM\d{4}\b")


def auto(rep: dict, c: dict) -> dict:
    txt = json.dumps({k: rep[k] for k in Report.model_fields})
    cited_alerts = set(ALERT_RE.findall(txt)) | {a for m in rep["attack_mapping"] for a in
                                                 re.findall(r"\d+", " ".join(m["alerts"]))}
    techs = set(TECH_RE.findall(txt))
    mits = set(MIT_RE.findall(txt))
    mapped = {m["technique_id"].strip().upper() for m in rep["attack_mapping"]}
    mapped_ok = {kb.normalize(t) for t in mapped} - {None}
    return {"alert_citations": len(cited_alerts),
            "alert_citation_valid": len(cited_alerts & c["alert_ids"]) / max(1, len(cited_alerts)),
            "technique_ids": len(techs),
            "technique_id_valid": sum(kb.normalize(t) is not None for t in techs) / max(1, len(techs)),
            "mitigation_ids": len(mits),
            "mitigation_id_valid": sum(m in kb.mitigations for m in mits) / max(1, len(mits)),
            "mapping_recall": len(mapped_ok & set(c["truth_techs"])) / len(c["truth_techs"]) if c["truth_techs"] else None,
            "recommendations": len(rep["recommendations"]),
            "rec_with_source": sum(bool(r["source"].strip()) for r in rep["recommendations"]) / max(1, len(rep["recommendations"])),
            "findings": len(rep["evidence_chain"])}


recs = []
for c in ctx:
    for cond in ["no_rag", "rag"]:
        rep = writer.cache.get((cond, args.model, c["key"]))
        sc = grader.cache.get((cond, args.judge, c["key"]))
        if not rep or rep.get("summary") is None or not sc or sc.get("correctness") is None:
            continue
        recs.append({"incident": c["key"], "condition": cond, "label": c["decision"].label,
                     "true": truth[c["key"]], **auto(rep, c),
                     **{k: sc[k] for k in ["correctness", "evidence_completeness", "actionability", "unsupported_claims"]},
                     "writer_tokens_in": rep["tokens_in"], "writer_tokens_out": rep["tokens_out"],
                     "writer_latency_s": rep["latency_s"]})
df = pd.DataFrame(recs)
df.to_csv(R / "e4_scores.csv", index=False)
paired = df.pivot(index="incident", columns="condition")
both = paired.dropna(subset=[("correctness", "rag"), ("correctness", "no_rag")]).index
rng = np.random.default_rng(0)
out = {"model": args.model, "judge": args.judge, "attack_version": kb.version, "n_incidents": len(both),
       "decision_correct": round(float((df.drop_duplicates("incident")["label"] == df.drop_duplicates("incident")["true"]).mean()), 4),
       "conditions": {}}
metrics = ["correctness", "evidence_completeness", "actionability", "unsupported_claims", "alert_citation_valid",
           "technique_id_valid", "mitigation_ids", "mitigation_id_valid", "mapping_recall", "rec_with_source",
           "writer_tokens_in", "writer_tokens_out", "writer_latency_s"]
for cond in ["no_rag", "rag"]:
    d = df[(df["condition"] == cond) & df["incident"].isin(both)]
    out["conditions"][cond] = {m: round(float(d[m].mean()), 4) for m in metrics}
out["paired_diff_rag_minus_no_rag"] = {}
for m in ["correctness", "evidence_completeness", "actionability", "unsupported_claims"]:
    diff = (paired.loc[both, (m, "rag")] - paired.loc[both, (m, "no_rag")]).to_numpy(float)
    boots = [diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(2000)]
    out["paired_diff_rag_minus_no_rag"][m] = {"mean": round(float(diff.mean()), 3),
                                               "ci95": [round(float(np.percentile(boots, 2.5)), 3),
                                                        round(float(np.percentile(boots, 97.5)), 3)],
                                               "rag_higher": int((diff > 0).sum()), "tie": int((diff == 0).sum()),
                                               "rag_lower": int((diff < 0).sum())}

# ---------------- blind sheet for human scoring ----------------
items = [(c["key"], cond) for c in ctx for cond in ["no_rag", "rag"] if (cond, args.model, c["key"]) in writer.cache]
order = rng.permutation(len(items))
key_rows, md = [], ["# E4 human review (blind)\n",
                    "Score each report 1-5 on correctness, evidence completeness and actionability in "
                    "`e4_human_scores.csv`. The condition (with or without RAG) is hidden.\n"]
for n, j in enumerate(order, 1):
    k, cond = items[j]
    c = next(x for x in ctx if x["key"] == k)
    rep = writer.cache[(cond, args.model, k)]
    key_rows.append({"report_no": n, "incident": k, "condition": cond})
    md += [f"\n---\n## Report {n}\n", f"True label: {truth[k]}\n", "### Evidence\n```", c["base"], "```",
           "### Report\n```json", json.dumps({f: rep[f] for f in Report.model_fields}, indent=1), "```"]
(R / "e4_human_review.md").write_text("\n".join(md) + "\n")
pd.DataFrame(key_rows).to_csv(R / "e4_human_key.csv", index=False)
if not (R / "e4_human_scores.csv").exists():
    pd.DataFrame({"report_no": range(1, len(items) + 1), "correctness": "", "evidence_completeness": "",
                  "actionability": "", "comment": ""}).to_csv(R / "e4_human_scores.csv", index=False)
out["seconds"] = round(time.time() - t0)
json.dump(out, open(R / "e4_report_quality.json", "w"), indent=1)
print(json.dumps(out, indent=1))
