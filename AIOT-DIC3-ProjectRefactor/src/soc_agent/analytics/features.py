"""Incident-level features, leakage-free splits, and train-only target encoding.

Inputs are the tables written by experiments/e1b_build_incidents.py:
  incidents_full.parquet  one row per (source, OrgId, IncidentId) with count features
  alerts.parquet          one row per alert with DetectorId and AlertTitle

Design (DESIGN.md §5–§6, OpenSpec triage-classification / triage-evaluation):
- the unit of analysis is the incident (M2);
- raw entity values (IPs, hashes, accounts, ...) are never features, only counts (M4);
- detector and alert-title historical label rates are target-encoded from the
  training incidents only (5-fold out-of-fold for training rows), so no label
  from validation or test leaks into features.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

CLASSES = ["TruePositive", "BenignPositive", "FalsePositive"]
SHORT = {"TruePositive": "TP", "BenignPositive": "BP", "FalsePositive": "FP"}
SMOOTH = 20.0  # target-encoding smoothing toward the class prior
TE_COLUMNS = ["DetectorId", "AlertTitle"]
META_COLUMNS = {"source", "OrgId", "IncidentId", "label", "first_ts", "y", "kid"}
# raw entity columns (IOC-like values) must never be features (M4); only counts are allowed
FORBIDDEN_FEATURES = {"IpAddress", "Sha256", "Url", "DeviceId", "DeviceName", "AccountSid", "AccountUpn",
                      "AccountObjectId", "AccountName", "FileName", "FolderPath", "NetworkMessageId",
                      "RegistryKey", "RegistryValueName", "RegistryValueData", "OrgId", "IncidentId", "AlertId"}


def load_tables(incidents_path="data/processed/incidents_full.parquet",
                alerts_path="data/processed/alerts.parquet"):
    """Load incidents and alerts and add the label index `y` and incident key `kid`."""
    inc = pd.read_parquet(incidents_path)
    alerts = pd.read_parquet(alerts_path)
    inc["y"] = inc["label"].map({c: i for i, c in enumerate(CLASSES)}).astype(int)
    inc["kid"] = incident_key(inc)
    alerts["kid"] = incident_key(alerts)
    alerts = alerts[alerts["kid"].isin(set(inc["kid"]))]
    return inc, alerts


def incident_key(df):
    return df["source"] + ":" + df["OrgId"].astype(str) + ":" + df["IncidentId"].astype(str)


def base_features(inc):
    feats = [c for c in inc.columns if c not in META_COLUMNS]
    bad = FORBIDDEN_FEATURES & set(feats)
    assert not bad, f"raw entity columns must not be features: {bad}"
    return feats


def make_splits(inc, rng_seed=42):
    """incident / org / time splits; each value is a Series kid -> train|val|test."""
    rng = np.random.default_rng(rng_seed)
    s = {}
    tr = inc[inc.source == "train"]["kid"].to_numpy()
    val = rng.choice(tr, size=len(tr) // 10, replace=False)
    lab = pd.Series("train", index=inc["kid"])
    lab[inc.loc[inc.source == "test", "kid"]] = "test"
    lab[val] = "val"
    s["incident"] = lab
    orgs = np.sort(inc["OrgId"].unique())
    test_orgs = set(rng.choice(orgs, size=len(orgs) // 5, replace=False))
    rest = np.array([o for o in orgs if o not in test_orgs])
    val_orgs = set(rng.choice(rest, size=len(rest) // 10, replace=False))
    s["org"] = pd.Series(np.where(inc["OrgId"].isin(test_orgs), "test",
                         np.where(inc["OrgId"].isin(val_orgs), "val", "train")), index=inc["kid"])
    order = inc.sort_values(["first_ts", "kid"])["kid"].to_numpy()
    n = len(order)
    lab = pd.Series("train", index=inc["kid"])
    lab[order[int(n * 0.8):]] = "test"
    lab[order[int(n * 0.72):int(n * 0.8)]] = "val"
    s["time"] = lab
    return s


def check_split(inc, name, lab):
    """Assert every incident key is in exactly one set (and orgs are disjoint for the org split)."""
    sets = {k: set(lab[lab == k].index) for k in ["train", "val", "test"]}
    assert not (sets["train"] & sets["val"]) and not (sets["train"] & sets["test"]) \
        and not (sets["val"] & sets["test"]), f"{name}: incident key in more than one set"
    assert sum(len(v) for v in sets.values()) == len(inc)
    out = {k: len(v) for k, v in sets.items()}
    if name == "org":
        org_of = inc.set_index("kid")["OrgId"]
        assert not set(org_of[list(sets["train"])]) & set(org_of[list(sets["test"])]), "org leak"
        out["test_orgs_in_train"] = 0
    return out


def rate_table(a, col, y_by_kid, prior):
    """Smoothed per-value label rates computed from alerts of the given incidents."""
    d = a[[col, "kid"]].drop_duplicates().copy()
    d["y"] = d["kid"].map(y_by_kid)
    cnt = pd.crosstab(d[col], d["y"]).reindex(columns=range(3), fill_value=0)
    n = cnt.sum(axis=1).to_numpy()[:, None]
    rates = (cnt.to_numpy() + SMOOTH * prior) / (n + SMOOTH)
    return pd.DataFrame(rates, index=cnt.index, columns=[f"r{c}" for c in range(3)])


def encode(a, col, table, prior):
    m = a[["kid", col]].merge(table, left_on=col, right_index=True, how="left")
    for c in range(3):
        m[f"r{c}"] = m[f"r{c}"].fillna(prior[c])
    g = m.groupby("kid")
    out = pd.DataFrame(index=g.size().index)
    for c in range(3):
        short = SHORT[CLASSES[c]].lower()
        out[f"{col}_{short}_mean"] = g[f"r{c}"].mean()
        out[f"{col}_{short}_max"] = g[f"r{c}"].max()
    seen = m[col].isin(table.index)
    out[f"{col}_unseen_share"] = (~seen).groupby(m["kid"]).mean()
    return out


def target_features(inc, alerts, lab):
    """Detector/title encodings: OOF for train, train-only statistics for val/test.

    Returns (encodings indexed by kid, {column: rate table from all training incidents}, prior).
    """
    y_by_kid = inc.set_index("kid")["y"]
    tr_kids = lab[lab == "train"].index
    prior = np.bincount(y_by_kid[tr_kids], minlength=3) / len(tr_kids)
    a_tr = alerts[alerts["kid"].isin(set(tr_kids))]
    a_other = alerts[~alerts["kid"].isin(set(tr_kids))]
    parts = []
    kids = np.array(sorted(set(a_tr["kid"])))
    for fit_idx, enc_idx in GroupKFold(n_splits=5).split(kids, groups=kids):
        fit_k, enc_k = set(kids[fit_idx]), set(kids[enc_idx])
        a_fit, a_enc = a_tr[a_tr["kid"].isin(fit_k)], a_tr[a_tr["kid"].isin(enc_k)]
        parts.append(pd.concat([encode(a_enc, c, rate_table(a_fit, c, y_by_kid, prior), prior)
                                for c in TE_COLUMNS], axis=1))
    full = {c: rate_table(a_tr, c, y_by_kid, prior) for c in TE_COLUMNS}
    parts.append(pd.concat([encode(a_other, c, full[c], prior) for c in TE_COLUMNS], axis=1))
    return pd.concat(parts), full, prior


def build_matrix(inc, alerts, lab):
    """Feature matrix X (indexed by kid), labels y, split index, and train-only statistics."""
    te, tables, prior = target_features(inc, alerts, lab)
    X = inc.set_index("kid")[base_features(inc)].join(te).fillna(0)
    y = inc.set_index("kid")["y"]
    idx = {k: lab[lab == k].index for k in ["train", "val", "test"]}
    return X, y, idx, tables, prior
