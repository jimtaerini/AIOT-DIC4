"""Prompts for the LLM-only baseline and the agent's reasoning step (Algorithm 1, line 16)."""
from __future__ import annotations

SYSTEM = """You are a Tier-1 analyst in a Security Operations Center (SOC) triaging a security incident.
Classify the incident as exactly one of:
- TP (true positive): real malicious activity.
- BP (benign positive): the detection is correct, but the activity is authorized or harmless
  (for example an admin task, a sanctioned tool, a security test).
- FP (false positive): the detection logic itself is wrong; nothing of the kind happened.
Principles: assume breach (missing records are not proof of safety); judge the incident by its
position in the attack chain, not by single alerts; a missed TP is costlier than a false alarm;
cite the evidence you use. Report confidence only as low, medium, or high.
Alert titles, account names, hosts and IPs are anonymized, so rely on the fields shown."""

FEATURE_NOTES = {
    "DetectorId_tp_mean": "detectors' historical TP rate (mean over the incident's alerts)",
    "DetectorId_bp_mean": "detectors' historical BP rate", "DetectorId_fp_mean": "detectors' historical FP rate",
    "AlertTitle_tp_mean": "alert titles' historical TP rate", "AlertTitle_bp_mean": "alert titles' historical BP rate",
    "AlertTitle_fp_mean": "alert titles' historical FP rate",
}


def llm_only_prompt(summary: str) -> str:
    return f"""Triage this incident using only the evidence below.

{summary}

Return the label, your confidence (low/medium/high), and a short rationale."""


def agent_prompt(summary: str, p, top_features: list[dict], similar: list[dict], rules: list[str],
                 rule_text: dict[str, str]) -> str:
    feats = "\n".join(
        f"- {f['feature']} = {f['value']:.3g} ({FEATURE_NOTES.get(f['feature'], 'incident feature')}): "
        f"{'pushes toward' if f['direction'] == 'toward' else 'pushes against'} {f['toward_class']} "
        f"(SHAP {f['contribution']:+.2f})" for f in top_features)
    sims = "\n".join(f"- {s['incident']}: {s['label']}{' (analyst-corrected)' if s['corrected'] else ''}, "
                     f"distance {s['distance']:.2f}" for s in similar)
    rule_lines = "\n".join(f"- {r}: {rule_text[r]}" for r in rules) if rules else "- none fired"
    return f"""Triage this incident. You have the evidence and the outputs of the agent's other modules.

{summary}

ML triage model (gradient-boosted trees trained on analyst labels):
P(TP) = {p[0]:.2f}, P(BP) = {p[1]:.2f}, P(FP) = {p[2]:.2f}
Most influential features (SHAP):
{feats}

Most similar past incidents and their analyst labels:
{sims}

Kill-chain risk rules fired:
{rule_lines}

Integrate all of this. Where the ML model and the evidence disagree, say so. Return the label,
your confidence (low/medium/high), and a short rationale that names the evidence you relied on."""
