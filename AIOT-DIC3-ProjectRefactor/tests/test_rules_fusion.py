"""Unit tests for R1–R5 (attack-mapping) and fusion/escalation (triage-decision).

Run from AIOT-DIC3-ProjectRefactor/:
    ../.venv/bin/python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.decision.fusion import (LLMJudgment, decide, fuse_evidence,  # noqa: E402
                                       one_hot_with_confidence)
from soc_agent.knowledge.rules import RuleInput, fired_rules  # noqa: E402


def rules(cats, techs=(), r5=4):
    return fired_rules(RuleInput.from_categories(cats, techs), r5_min_tactics=r5)


class TestRules(unittest.TestCase):
    def test_r1_late_stage(self):
        self.assertIn("R1", rules(["Exfiltration"]))
        self.assertIn("R1", rules(["Impact"]))
        self.assertIn("R1", rules(["Ransomware"]))
        self.assertNotIn("R1", rules(["Discovery"]))

    def test_r2_credentials_and_lateral_movement(self):
        self.assertIn("R2", rules(["CredentialAccess", "LateralMovement"]))
        self.assertIn("R2", rules(["CredentialStealing", "LateralMovement"]))
        self.assertNotIn("R2", rules(["CredentialAccess"]))

    def test_r3_any_order(self):
        for second in ["Execution", "Persistence", "PrivilegeEscalation"]:
            self.assertIn("R3", rules(["InitialAccess", second]))
            self.assertIn("R3", rules([second, "InitialAccess"]))  # order does not matter
        self.assertNotIn("R3", rules(["InitialAccess", "Discovery"]))

    def test_r4_indicator_removal(self):
        self.assertIn("R4", rules([], ["T1070"]))
        self.assertIn("R4", rules([], ["T1070.001"]))
        self.assertNotIn("R4", rules([], ["T1078", "T10700"]))

    def test_r5_threshold(self):
        four = ["InitialAccess", "Discovery", "Collection", "CommandAndControl"]
        self.assertIn("R5", rules(four))
        self.assertNotIn("R5", rules(four[:3]))
        self.assertNotIn("R5", rules(four, r5=5))

    def test_non_tactic_categories_are_not_tactics(self):
        self.assertEqual(rules(["Malware", "SuspiciousActivity", "UnwantedSoftware", "Exploit"]), [])


class TestFusion(unittest.TestCase):
    def test_one_hot_with_confidence(self):
        np.testing.assert_allclose(one_hot_with_confidence("TP", "medium"), [0.7, 0.15, 0.15])
        np.testing.assert_allclose(one_hot_with_confidence("FP", "high"), [0.05, 0.05, 0.9])

    def test_paper_example(self):
        d = fuse_evidence([0.46, 0.45, 0.09], LLMJudgment("TP", "medium"), [], w_ml=0.5)
        np.testing.assert_allclose(d.scores, [0.58, 0.30, 0.12])
        self.assertEqual(d.label, "TP")
        self.assertAlmostEqual(d.conf, 0.58)

    def test_conflict(self):
        d = fuse_evidence([0.2, 0.7, 0.1], LLMJudgment("TP", "low", "new admin tool on host"), [], w_ml=0.5)
        self.assertIn("conflict", d.flags)
        d = decide(d, tau=0.5)
        reason = next(r for r in d.reasons if r.startswith("ML and LLM disagree"))
        self.assertIn("ML says BP", reason)       # both conclusions are listed
        self.assertIn("LLM says TP", reason)
        self.assertIn("new admin tool", reason)   # with the LLM's rationale

    def test_high_risk_raises_to_tp(self):
        d = fuse_evidence([0.35, 0.55, 0.10], None, ["R1"], tau_safety=0.3)
        self.assertEqual(d.label, "TP")
        self.assertIn("high_risk", d.flags)

    def test_high_risk_with_low_tp_keeps_label(self):
        d = fuse_evidence([0.05, 0.85, 0.10], None, ["R5"], tau_safety=0.3)
        self.assertEqual(d.label, "BP")
        self.assertIn("high_risk", d.flags)

    def test_no_llm_means_scores_equal_p(self):
        d = fuse_evidence([0.1, 0.2, 0.7], None, [])
        np.testing.assert_allclose(d.scores, [0.1, 0.2, 0.7])
        self.assertEqual(d.flags, [])


class TestEscalation(unittest.TestCase):
    def test_low_confidence(self):
        d = decide(fuse_evidence([0.46, 0.45, 0.09], LLMJudgment("TP", "medium"), []), tau=0.7)
        self.assertEqual(d.status, "NEEDS_HUMAN_REVIEW")

    def test_insufficient_evidence_even_if_confident(self):
        d = decide(fuse_evidence([0.95, 0.03, 0.02], None, []), tau=0.7, sufficient=False)
        self.assertEqual(d.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("insufficient evidence", d.reasons)

    def test_all_conditions_pass(self):
        d = decide(fuse_evidence([0.95, 0.03, 0.02], None, []), tau=0.7)
        self.assertEqual(d.status, "AUTO_TRIAGED")
        self.assertEqual(d.reasons, [])

    def test_all_reasons_listed(self):
        r = ["R2"]
        d = decide(fuse_evidence([0.46, 0.45, 0.09], LLMJudgment("TP", "medium"), r), tau=0.7,
                   sufficient=False, rules_fired=r)
        self.assertEqual(d.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(len(d.reasons), 3)  # low confidence, R2, insufficient evidence
        self.assertTrue(any("R2" in x for x in d.reasons))

    def test_high_risk_always_escalates(self):
        d = decide(fuse_evidence([0.99, 0.005, 0.005], None, ["R4"]), tau=0.5, rules_fired=["R4"])
        self.assertEqual(d.status, "NEEDS_HUMAN_REVIEW")


if __name__ == "__main__":
    unittest.main()
