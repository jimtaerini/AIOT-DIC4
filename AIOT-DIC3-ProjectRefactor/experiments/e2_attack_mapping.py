"""E2: ATT&CK technique and tactic mapping on GUIDE alerts (LLM only vs. LLM + RAG).

Ground truth: GUIDE's MitreTechniques per alert (test split), normalized to the
pinned ATT&CK Enterprise v20.1: revoked IDs follow revoked-by to their
replacement; deprecated IDs and ICS-matrix IDs (T08xx) are dropped; alerts with
no remaining technique are excluded.
Sample: stratified by alert Category, up to N_PER_CAT alerts each (fixed seed).
The LLM never sees MitreTechniques, AlertTitle or DetectorId (anonymized or label).

Methods
  category_prior  most frequent technique set of the alert's Category in train (non-LLM)
  detector_lookup most frequent technique set of the alert's DetectorId in train,
                  falling back to category_prior (memorization reference, non-LLM)
  llm_only        Gemini proposes up to 5 techniques from the readable alert fields
  llm_rag         same, plus the top-K ATT&CK v20.1 techniques retrieved by embedding
                  similarity, each with its technique ID as source
Metrics: micro precision / recall / F1 over alerts at three levels (exact technique,
parent technique, tactic), hallucination rate (predicted IDs that do not exist in
v20.1), and 95% bootstrap intervals for F1.

Usage (from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e2_attack_mapping.py --n-per-cat 20 --workers 8
Writes experiments/results/e2_sample.csv, e2_llm_cache.jsonl, e2_attack_mapping.json.
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.agent.llm import GeminiJudge, ModelUnavailable, QuotaExhausted  # noqa: E402
from soc_agent.knowledge.attack_kb import TECH_RE, AttackKB  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n-per-cat", type=int, default=20)
ap.add_argument("--model", default="gemini-3.8-flash")
ap.add_argument("--k", type=int, default=10, help="retrieved techniques for llm_rag")
ap.add_argument("--workers", type=int, default=8)
ap.add_argument("--limit", type=int, default=0, help="only the first N sampled alerts (pilot)")
args = ap.parse_args()
t0 = time.time()
R = Path("experiments/results")
SEED = 303
B = 2000


class Mapping(BaseModel):
    techniques: list[str] = Field(description="1 to 5 ATT&CK technique IDs such as T1566 or T1566.001, most likely first")
    rationale: str = Field(description="At most two sentences citing the alert fields used")


SYSTEM = """You are a SOC analyst mapping a security alert to MITRE ATT&CK Enterprise (v20.1) techniques.
Return 1 to 5 technique IDs (format T1234 or T1234.001), most likely first. Use sub-techniques
only when the evidence supports them. Include only techniques the evidence supports.
Alert titles, account names, hosts and IPs are anonymized, so rely on the fields shown."""

AGG = """
  SELECT OrgId, IncidentId, AlertId,
         any_value(Category) AS category, any_value(DetectorId) AS detector,
         string_agg(DISTINCT MitreTechniques, ';') AS techniques_raw,
         count(*) AS n_evidence,
         string_agg(DISTINCT EntityType || '/' || EvidenceRole, ', ') AS entities,
         string_agg(DISTINCT SuspicionLevel, ', ') AS suspicion,
         string_agg(DISTINCT LastVerdict, ', ') FILTER (WHERE LastVerdict NOT LIKE 'DomainPII%') AS verdict,
         string_agg(DISTINCT ThreatFamily, ', ') AS threat_family,
         string_agg(DISTINCT AntispamDirection, ', ') AS mail_direction,
         string_agg(DISTINCT ResourceType, ', ') AS resource_type
  FROM '{path}' WHERE MitreTechniques IS NOT NULL
  GROUP BY OrgId, IncidentId, AlertId"""

kb = AttackKB()


def norm_set(raw) -> list[str]:
    ids = {x for s in str(raw).split(";") for x in [s.strip()] if x}
    return sorted({n for x in ids if (n := kb.normalize(x))})


con = duckdb.connect()
test = con.execute(AGG.format(path="data/processed/guide_test.parquet")).df()
test["truth"] = test["techniques_raw"].map(norm_set)
n_before = len(test)
test = test[test["truth"].map(len) > 0].reset_index(drop=True)
print(f"[{time.time() - t0:5.0f}s] test alerts with techniques: {n_before}, after v{kb.version} normalization: {len(test)}",
      flush=True)
rng = np.random.default_rng(SEED)
parts = []
for cat, g in test.groupby("category"):
    parts.append(g.iloc[rng.permutation(len(g))[:args.n_per_cat]])
sample = pd.concat(parts).reset_index(drop=True)
sample["key"] = "test:" + sample["OrgId"].astype(str) + ":" + sample["IncidentId"].astype(str) + ":" + \
    sample["AlertId"].astype(str)
if args.limit:
    sample = sample.iloc[rng.permutation(len(sample))[:args.limit]].reset_index(drop=True)

# non-LLM baselines from the training split
train = con.execute(AGG.format(path="data/processed/guide_train.parquet")).df()
train["truth"] = train["techniques_raw"].map(norm_set).map(lambda x: ";".join(x))
train = train[train["truth"] != ""]
cat_prior = train.groupby("category")["truth"].agg(lambda s: s.value_counts().index[0])
det_prior = train.groupby("detector")["truth"].agg(lambda s: s.value_counts().index[0])
sample["category_prior"] = sample["category"].map(cat_prior).fillna("").map(lambda s: [x for x in s.split(";") if x])
sample["detector_lookup"] = [
    [x for x in (det_prior.get(d) or cat_prior.get(c, "")).split(";") if x]
    for d, c in zip(sample["detector"], sample["category"])]
sample["detector_seen_in_train"] = sample["detector"].isin(det_prior.index)
print(f"[{time.time() - t0:5.0f}s] sample: {len(sample)} alerts in {sample['category'].nunique()} categories", flush=True)


def describe(r) -> str:
    lines = [f"Alert category: {r['category']}. Evidence rows: {r['n_evidence']}.",
             f"Entities (type/role): {r['entities']}."]
    for col, name in [("suspicion", "Suspicion level"), ("verdict", "Last verdict"), ("threat_family", "Threat family"),
                      ("mail_direction", "Mail direction"), ("resource_type", "Resource type")]:
        if isinstance(r[col], str) and r[col]:
            lines.append(f"{name}: {r[col]}.")
    return "\n".join(lines)


sample["description"] = [describe(r) for _, r in sample.iterrows()]
judge = GeminiJudge(model=args.model, min_interval_s=0.2, cache_path=R / "e2_llm_cache.jsonl", schema=Mapping)
retrieved = kb.search(judge.client, sample["description"].tolist(), k=args.k)
sample["retrieved"] = [[h["id"] for h in hits] for hits in retrieved]


def rag_block(hits) -> str:
    out = []
    for h in hits:
        t = kb.techniques[h["id"]]
        out.append(f"- [source: {h['source']}] {h['id']} {t['full_name']} (tactics: {', '.join(t['tactics'])}): "
                   f"{t['description'][:220]}")
    return "\n".join(out)


def run(i: int) -> None:
    r = sample.iloc[i]
    judge.judge("llm_only", r["key"], SYSTEM,
                f"Map this alert to ATT&CK techniques.\n\n{r['description']}\n\n"
                "Return the technique IDs and a short rationale.")
    judge.judge("llm_rag", r["key"], SYSTEM,
                f"Map this alert to ATT&CK techniques.\n\n{r['description']}\n\n"
                f"Candidate techniques retrieved from the ATT&CK v{kb.version} knowledge base "
                f"(most similar first):\n{rag_block(retrieved[i])}\n\n"
                "Prefer techniques the evidence supports; you may choose techniques outside the list. "
                "Return the technique IDs and a short rationale that cites the sources used.")


done = 0
try:
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for f in [ex.submit(run, i) for i in range(len(sample))]:
            f.result()
            done += 1
            if done % 50 == 0:
                print(f"[{time.time() - t0:5.0f}s] {done}/{len(sample)} alerts", flush=True)
except (QuotaExhausted, ModelUnavailable) as e:
    print(f"Stopped after {done} alerts; rerun to resume. {e}", flush=True)

for mode in ["llm_only", "llm_rag"]:
    recs = {k[2]: v for k, v in judge.cache.items() if k[0] == mode and k[1] == args.model}
    sample[mode] = sample["key"].map(lambda k: (recs.get(k) or {}).get("techniques"))
sample = sample[sample["llm_only"].notna() & sample["llm_rag"].notna()].reset_index(drop=True)


def clean(pred) -> tuple[list[str], int]:
    """Uppercase and dedupe predicted IDs; normalize revoked ones; count IDs absent from v20.1."""
    out, bad = [], 0
    for x in pred[:5]:
        x = str(x).strip().upper()
        n = kb.normalize(x) if TECH_RE.match(x) else None
        if n is None:
            bad += 1
            out.append(x)          # kept as a (wrong) prediction
        elif n not in out:
            out.append(n)
    return out, bad


def levels(ids):
    return {"technique": set(ids), "parent": {x.split(".")[0] for x in ids}, "tactic": kb.tactics_of(ids)}


def prf(rows):
    out = {}
    for lv in ["technique", "parent", "tactic"]:
        tp = sum(len(levels(p)[lv] & levels(t)[lv]) for p, t in rows)
        np_ = sum(len(levels(p)[lv]) for p, _ in rows)
        nt = sum(len(levels(t)[lv]) for _, t in rows)
        pr, rc = tp / max(1, np_), tp / max(1, nt)
        out[lv] = {"precision": round(pr, 4), "recall": round(rc, 4),
                   "f1": round(2 * pr * rc / max(1e-9, pr + rc), 4)}
    return out


res = {"model": args.model, "attack_version": kb.version, "k": args.k, "seed": SEED, "n_per_cat": args.n_per_cat,
       "n_alerts": len(sample), "categories": sample["category"].value_counts().to_dict(),
       "detector_seen_in_train": round(float(sample["detector_seen_in_train"].mean()), 4),
       "mean_truth_size": round(float(sample["truth"].map(len).mean()), 2), "methods": {}}
rng = np.random.default_rng(0)
boot_idx = [rng.integers(0, len(sample), len(sample)) for _ in range(B)]
for m in ["category_prior", "detector_lookup", "llm_only", "llm_rag"]:
    cleaned = [clean(p) if m.startswith("llm") else (p, 0) for p in sample[m]]
    rows = [(c[0], t) for c, t in zip(cleaned, sample["truth"])]
    r = prf(rows)
    n_pred = sum(len(c[0]) for c in cleaned)
    r["mean_predicted"] = round(n_pred / len(rows), 2)
    r["hallucinated_ids"] = int(sum(c[1] for c in cleaned))
    r["hallucination_rate"] = round(sum(c[1] for c in cleaned) / max(1, n_pred), 4)
    ci = {}
    for lv in ["technique", "tactic"]:
        f1s = sorted(prf([rows[j] for j in idx])[lv]["f1"] for idx in boot_idx[:500])
        ci[lv] = [f1s[12], f1s[487]]   # 95% interval from 500 resamples
    r["f1_ci95"] = ci
    res["methods"][m] = r
    sample[m + "_clean"] = [";".join(c[0]) for c in cleaned]
# how often the retrieved list contains a true technique (retrieval recall@K)
res["retrieval_recall_at_k"] = {
    "technique": round(float(np.mean([len(set(r) & set(t)) / len(t) for r, t in zip(sample["retrieved"], sample["truth"])])), 4),
    "parent": round(float(np.mean([len({x.split('.')[0] for x in r} & {x.split('.')[0] for x in t})
                                   / len({x.split('.')[0] for x in t}) for r, t in zip(sample["retrieved"], sample["truth"])])), 4)}
c = pd.DataFrame([v for k, v in judge.cache.items() if k[1] == args.model and k[2] in set(sample["key"])])
res["cost"] = {m: {"calls": int((c["mode"] == m).sum()), "mean_tokens_in": round(float(c.loc[c["mode"] == m, "tokens_in"].mean())),
                   "mean_tokens_out": round(float(c.loc[c["mode"] == m, "tokens_out"].mean())),
                   "mean_latency_s": round(float(c.loc[c["mode"] == m, "latency_s"].mean()), 2)}
               for m in ["llm_only", "llm_rag"]}
res["seconds"] = round(time.time() - t0)
out = sample[["key", "category", "detector_seen_in_train", "techniques_raw"]].assign(
    truth=sample["truth"].map(";".join), retrieved=sample["retrieved"].map(";".join),
    **{m: sample[m + "_clean"] for m in ["category_prior", "detector_lookup", "llm_only", "llm_rag"]})
out.to_csv(R / ("e2_sample.csv" if not args.limit else "e2_pilot_sample.csv"), index=False)
json.dump(res, open(R / ("e2_attack_mapping.json" if not args.limit else "e2_pilot.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
