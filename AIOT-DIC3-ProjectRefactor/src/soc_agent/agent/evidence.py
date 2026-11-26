"""Readable evidence summaries for the LLM (GUIDE version of the Evidence Store, module ④).

GUIDE alert titles and entity values are anonymized numeric IDs, so the LLM only
sees fields with readable semantics: ATT&CK category and techniques, entity
types and roles, suspicion level, last verdict, threat family, mail
direction, resource type, and counts. No IP, hash, account, or other raw IOC
value is ever shown (M4). Every alert line carries its source reference
(AlertId and evidence row count) so conclusions stay traceable (NFR1).
"""
from __future__ import annotations

import duckdb
import pandas as pd

SRC = {"train": "data/processed/guide_train.parquet", "test": "data/processed/guide_test.parquet"}


def load_alert_rows(keys: list[str]) -> pd.DataFrame:
    """Per-alert readable aggregates for the given incident keys ('source:OrgId:IncidentId')."""
    k = pd.DataFrame([kk.split(":") for kk in keys], columns=["source", "OrgId", "IncidentId"])
    k["OrgId"] = k["OrgId"].astype("int64")
    k["IncidentId"] = k["IncidentId"].astype("int64")
    con = duckdb.connect()
    con.register("k", k)
    parts = []
    for source, path in SRC.items():
        parts.append(f"""
          SELECT '{source}' AS source, e.OrgId, e.IncidentId, e.AlertId,
                 min(e.Timestamp) AS ts,
                 any_value(e.Category) AS category,
                 string_agg(DISTINCT e.MitreTechniques, ';') AS techniques,
                 count(*) AS n_evidence,
                 string_agg(DISTINCT e.EntityType || '/' || e.EvidenceRole, ', ') AS entities,
                 string_agg(DISTINCT e.SuspicionLevel, ', ') AS suspicion,
                 string_agg(DISTINCT e.LastVerdict, ', ') FILTER (WHERE e.LastVerdict NOT LIKE 'DomainPII%') AS verdict,
                 string_agg(DISTINCT e.ThreatFamily, ', ') AS threat_family,
                 string_agg(DISTINCT e.AntispamDirection, ', ') AS mail_direction,
                 string_agg(DISTINCT e.ResourceType, ', ') AS resource_type
          FROM '{path}' e JOIN k ON k.source = '{source}' AND e.OrgId = k.OrgId AND e.IncidentId = k.IncidentId
          GROUP BY e.OrgId, e.IncidentId, e.AlertId""")
    df = con.execute(" UNION ALL ".join(parts) + " ORDER BY source, OrgId, IncidentId, ts").df()
    df["kid"] = df["source"] + ":" + df["OrgId"].astype(str) + ":" + df["IncidentId"].astype(str)
    return df


def summarize(kid: str, rows: pd.DataFrame, max_alerts: int = 30) -> str:
    """Compact text summary of one incident; alerts in time order (timestamps are noised)."""
    a = rows[rows["kid"] == kid]
    if a.empty:
        return f"Incident {kid}: no alerts found."
    t0 = a["ts"].min()
    span_h = (a["ts"].max() - t0).total_seconds() / 3600
    cats = a["category"].value_counts()
    lines = [f"Incident {kid}: {len(a)} alerts, {int(a['n_evidence'].sum())} evidence rows, "
             f"time span {span_h:.1f} h.",
             "Alert categories: " + ", ".join(f"{c} x{n}" for c, n in cats.items()) + "."]
    techs = sorted({t for s in a["techniques"].dropna() for t in s.split(";") if t})
    lines.append("ATT&CK techniques: " + (", ".join(techs) if techs else "none recorded") + ".")
    lines.append("Alerts (time order; source = AlertId):")
    for _, r in a.head(max_alerts).iterrows():
        mins = (r["ts"] - t0).total_seconds() / 60
        extra = []
        for col, name in [("suspicion", "suspicion"), ("verdict", "last verdict"), ("threat_family", "threat family"),
                          ("mail_direction", "mail"), ("resource_type", "resource")]:
            if isinstance(r[col], str) and r[col]:
                extra.append(f"{name}: {r[col]}")
        tech = r["techniques"].replace(";", ", ") if isinstance(r["techniques"], str) and r["techniques"] else "none"
        lines.append(f"- +{mins:.0f} min [{r['category']}] techniques: {tech}; "
                     f"entities: {r['entities']}" + ("; " + "; ".join(extra) if extra else "")
                     + f" (source: alert {r['AlertId']}, {r['n_evidence']} evidence rows)")
    if len(a) > max_alerts:
        lines.append(f"- ... {len(a) - max_alerts} more alerts omitted")
    return "\n".join(lines)
