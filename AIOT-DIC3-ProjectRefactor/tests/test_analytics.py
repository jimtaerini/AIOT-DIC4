"""Unit tests for the analytics module (OpenSpec triage-classification, triage-evaluation).

Run from AIOT-DIC3-ProjectRefactor/:
    ../.venv/bin/python -m unittest discover -s tests -v
Uses small synthetic data, so it runs in seconds and needs no GUIDE files.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soc_agent.analytics.explain import Explainer  # noqa: E402
from soc_agent.analytics.features import (FORBIDDEN_FEATURES, base_features, build_matrix,  # noqa: E402
                                          check_split, make_splits)
from soc_agent.analytics.similar import SimilarIncidents  # noqa: E402
from soc_agent.analytics.triage import classify  # noqa: E402
from soc_agent.analytics.triage_model import TriageModel  # noqa: E402


def synthetic(n=600, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 3, n)
    labels = np.array(["TruePositive", "BenignPositive", "FalsePositive"])[y]
    inc = pd.DataFrame({
        "source": np.where(np.arange(n) < int(n * 0.7), "train", "test"),
        "OrgId": rng.integers(0, 40, n),
        "IncidentId": np.arange(n),
        "label": labels,
        "first_ts": pd.date_range("2024-01-01", periods=n, freq="h"),
        "n_alerts": rng.integers(1, 10, n) + 3 * (y == 0),
        "n_tactics": rng.integers(0, 3, n) + 2 * (y == 0),
        "max_stage": rng.integers(0, 6, n) + 4 * (y == 0),
        "n_ips": rng.integers(0, 5, n),
    })
    inc["y"] = y
    inc["kid"] = inc["source"] + ":" + inc["OrgId"].astype(str) + ":" + inc["IncidentId"].astype(str)
    alerts = pd.DataFrame({
        "kid": np.repeat(inc["kid"].to_numpy(), 2),
        "DetectorId": np.concatenate([[d, d + 100] for d in (y * 3 + rng.integers(0, 3, n))]),
        "AlertTitle": rng.integers(0, 50, 2 * n),
    })
    return inc, alerts


class TestSplits(unittest.TestCase):
    def test_every_key_in_exactly_one_set(self):
        inc, _ = synthetic()
        for name, lab in make_splits(inc).items():
            sizes = check_split(inc, name, lab)
            self.assertEqual(sum(v for k, v in sizes.items() if k in {"train", "val", "test"}), len(inc))

    def test_org_split_has_no_shared_orgs(self):
        inc, _ = synthetic()
        lab = make_splits(inc)["org"]
        org = inc.set_index("kid")["OrgId"]
        self.assertFalse(set(org[lab[lab == "train"].index]) & set(org[lab[lab == "test"].index]))

    def test_same_seed_same_split(self):
        inc, _ = synthetic()
        a, b = make_splits(inc, 7), make_splits(inc, 7)
        for k in a:
            self.assertTrue(a[k].equals(b[k]))


class TestFeatures(unittest.TestCase):
    def test_no_raw_entity_columns(self):
        inc, _ = synthetic()
        feats = base_features(inc)
        self.assertFalse(FORBIDDEN_FEATURES & set(feats))
        bad = inc.assign(IpAddress=1)
        with self.assertRaises(AssertionError):
            base_features(bad)

    def test_target_encoding_uses_train_only(self):
        inc, alerts = synthetic()
        lab = make_splits(inc)["incident"]
        X, y, idx, tables, prior = build_matrix(inc, alerts, lab)
        # flipping every test label must not change any test feature
        inc2 = inc.copy()
        test_mask = inc2["kid"].isin(set(idx["test"]))
        inc2.loc[test_mask, "y"] = (inc2.loc[test_mask, "y"] + 1) % 3
        X2, *_ = build_matrix(inc2, alerts, lab)
        pd.testing.assert_frame_equal(X.loc[idx["test"]], X2.loc[idx["test"]])


class TestClassifyExplainSimilar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        inc, alerts = synthetic()
        lab = make_splits(inc)["incident"]
        cls.X, cls.y, cls.idx, *_ = build_matrix(inc, alerts, lab)
        params = dict(learning_rate=0.1, max_iter=30, early_stopping=False, class_weight="balanced")
        cls.model = TriageModel(seed=0, params=params).fit(cls.X.loc[cls.idx["train"]], cls.y[cls.idx["train"]])
        cls.explainer = Explainer(cls.model)
        cls.similar = SimilarIncidents(k=3).fit(cls.X.loc[cls.idx["train"]], cls.y[cls.idx["train"]])

    def test_probabilities_sum_to_one(self):
        p = self.model.predict_proba(self.X.loc[self.idx["test"]])
        self.assertEqual(p.shape[1], 3)
        np.testing.assert_allclose(p.sum(axis=1), 1.0)

    def test_every_result_has_features_and_similar_incidents(self):
        res = classify(self.X.loc[self.idx["test"]].head(20), self.model, self.explainer, self.similar, top_k=4)
        self.assertEqual(len(res), 20)
        for r in res:
            self.assertEqual(len(r["top_features"]), 4)
            self.assertEqual(len(r["similar_incidents"]), 3)
            self.assertIn(r["label"], {"TP", "BP", "FP"})
            for f in r["top_features"]:
                self.assertIn(f["direction"], {"toward", "against"})

    def test_shap_reconstructs_model_output(self):
        Xs = self.X.loc[self.idx["test"]].head(10)
        v = self.explainer.shap_values(Xs)
        self.assertEqual(v.shape, (10, Xs.shape[1], 3))
        raw = self.model.clf._raw_predict(Xs[self.model.feature_names].to_numpy())
        base = np.asarray(self.explainer.explainer.expected_value)
        np.testing.assert_allclose(v.sum(axis=1) + base, raw, atol=1e-4)

    def test_analyst_correction_is_shown(self):
        Xq = self.X.loc[self.idx["test"]].head(1)
        first = self.similar.query(Xq)[0][0]
        new = "TP" if first["label"] != "TP" else "FP"
        self.similar.correct(first["incident"], new)
        again = self.similar.query(Xq)[0][0]
        self.assertEqual(again["label"], new)
        self.assertTrue(again["corrected"])
        self.assertEqual(again["original_label"], first["original_label"])


if __name__ == "__main__":
    unittest.main()
