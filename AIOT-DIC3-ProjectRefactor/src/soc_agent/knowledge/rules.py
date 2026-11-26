"""Kill-chain risk rules R1–R5 (DESIGN.md §4 ⑥; OpenSpec attack-mapping).

Rules only flag `high_risk` and bias the decision toward escalation; they never
set the triage label on their own. All conditions are evaluated within one
incident and do not require any order (GUIDE timestamps are noised), so R3
holds whenever its tactics co-occur.

Tactic names follow ATT&CK Enterprise (GUIDE's `Category` field uses the same
names without spaces). GUIDE's non-tactic category CredentialStealing is
treated as Credential Access.
"""
from __future__ import annotations

from dataclasses import dataclass

TACTICS = ["InitialAccess", "Execution", "Persistence", "PrivilegeEscalation", "DefenseEvasion",
           "CredentialAccess", "Discovery", "LateralMovement", "Collection", "CommandAndControl",
           "Exfiltration", "Impact"]
CATEGORY_TO_TACTIC = {t: t for t in TACTICS} | {"CredentialStealing": "CredentialAccess"}
RULE_IDS = ["R1", "R2", "R3", "R4", "R5"]


@dataclass(frozen=True)
class RuleInput:
    """What the rules need about one incident."""
    tactics: frozenset[str]          # ATT&CK tactics present (any order)
    categories: frozenset[str]       # raw GUIDE categories (for Ransomware)
    techniques: frozenset[str]       # ATT&CK technique IDs, e.g. "T1070.001"

    @staticmethod
    def from_categories(categories, techniques=()) -> "RuleInput":
        cats = frozenset(categories)
        tactics = frozenset(CATEGORY_TO_TACTIC[c] for c in cats if c in CATEGORY_TO_TACTIC)
        return RuleInput(tactics=tactics, categories=cats, techniques=frozenset(techniques))


def fired_rules(x: RuleInput, r5_min_tactics: int = 4) -> list[str]:
    """IDs of the rules R1–R5 that fire for this incident."""
    t = x.tactics
    fired = []
    if {"Exfiltration", "Impact"} & t or "Ransomware" in x.categories:
        fired.append("R1")
    if {"CredentialAccess", "LateralMovement"} <= t:
        fired.append("R2")
    if "InitialAccess" in t and {"Execution", "Persistence", "PrivilegeEscalation"} & t:
        fired.append("R3")
    if any(tech == "T1070" or tech.startswith("T1070.") for tech in x.techniques):
        fired.append("R4")
    if len(t) >= r5_min_tactics:
        fired.append("R5")
    return fired


RULE_DESCRIPTIONS = {
    "R1": "late kill-chain stage: Exfiltration or Impact, or Ransomware",
    "R2": "Credential Access together with Lateral Movement",
    "R3": "Initial Access together with Execution, Persistence, or Privilege Escalation",
    "R4": "T1070 Indicator Removal (log deletion)",
    "R5": "many distinct tactics",
}
