"""Evidence fusion and escalation: Algorithm 2 and lines 18–21 of Algorithm 1.

OpenSpec triage-decision:
- s = w_ml * p + w_llm * q; label = argmax(s); conf = max(s)
- the LLM reports confidence only as low / medium / high (c = 0.5 / 0.7 / 0.9)
- conflict when argmax(p) differs from the LLM label
- high_risk (any of R1–R5) raises a non-TP label to TP when p_TP >= tau_safety
- NEEDS_HUMAN_REVIEW when conf < tau, conflict, high_risk, or insufficient
  evidence; every escalation lists all reasons

Without an LLM (llm=None) the fusion reduces to s = p, and no conflict can arise.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

LABELS = ["TP", "BP", "FP"]
CONFIDENCE_LEVELS = {"low": 0.5, "medium": 0.7, "high": 0.9}


def one_hot_with_confidence(label: str, level: str) -> np.ndarray:
    """The LLM label gets c; the other two classes share 1 - c equally."""
    c = CONFIDENCE_LEVELS[level]
    q = np.full(3, (1.0 - c) / 2.0)
    q[LABELS.index(label)] = c
    return q


@dataclass
class LLMJudgment:
    label: str                      # TP / BP / FP
    level: str                      # low / medium / high
    rationale: str = ""


@dataclass
class Decision:
    label: str
    conf: float
    scores: list[float]
    flags: list[str] = field(default_factory=list)
    conflict_detail: str = ""
    status: str = ""
    reasons: list[str] = field(default_factory=list)


def fuse_evidence(p, llm: LLMJudgment | None, rules_fired: list[str],
                  w_ml: float = 0.5, tau_safety: float = 0.3) -> Decision:
    """Algorithm 2 (FuseEvidence)."""
    p = np.asarray(p, dtype=float)
    assert p.shape == (3,) and np.isclose(p.sum(), 1.0), "p must be (p_TP, p_BP, p_FP) summing to 1"
    flags = []
    conflict_detail = ""
    if llm is None:
        s = p.copy()
    else:
        assert 0.0 <= w_ml <= 1.0
        s = w_ml * p + (1.0 - w_ml) * one_hot_with_confidence(llm.label, llm.level)
        ml_label = LABELS[int(p.argmax())]
        if ml_label != llm.label:
            flags.append("conflict")
            conflict_detail = (f"ML says {ml_label} (p={p.max():.2f}); LLM says {llm.label} "
                               f"({llm.level} confidence): {llm.rationale}".rstrip(": "))
    k = int(s.argmax())
    label, conf = LABELS[k], float(s[k])
    if rules_fired:
        flags.append("high_risk")
        if label != "TP" and p[0] >= tau_safety:
            label = "TP"
    return Decision(label=label, conf=conf, scores=[round(float(v), 6) for v in s], flags=flags,
                    conflict_detail=conflict_detail)


def decide(d: Decision, tau: float, sufficient: bool = True, rules_fired: list[str] | None = None) -> Decision:
    """Algorithm 1 lines 18–21: escalate on any condition and list every reason."""
    reasons = []
    if d.conf < tau:
        reasons.append(f"confidence {d.conf:.2f} below threshold {tau:.2f}")
    if "conflict" in d.flags:
        reasons.append("ML and LLM disagree: " + d.conflict_detail)
    if "high_risk" in d.flags:
        reasons.append("high-risk kill-chain pattern: " + ", ".join(rules_fired or []))
    if not sufficient:
        reasons.append("insufficient evidence")
    d.status = "NEEDS_HUMAN_REVIEW" if reasons else "AUTO_TRIAGED"
    d.reasons = reasons
    return d
