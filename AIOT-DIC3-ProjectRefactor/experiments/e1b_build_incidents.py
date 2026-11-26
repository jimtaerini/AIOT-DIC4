"""E1b: aggregate GUIDE evidence rows into one row per incident (task 1.3, 3.1).

Output (git-ignored, data/processed/):
  incidents.parquet  one row per (source, OrgId, IncidentId) with label and
                     label-free count features
  alerts.parquet     one row per (source, OrgId, IncidentId, AlertId) with
                     DetectorId and AlertTitle, used later for train-only
                     target encoding (detector / title historical rates)

Design notes
- Unit of analysis = incident (M2). Incidents without IncidentGrade are dropped.
- No raw IP / hash / entity values are used as features (M4). Entity columns
  only contribute *counts of distinct real entities*; the per-column
  placeholder value meaning "no such entity" (found by e1a_check_guide.py) is
  treated as missing.
- Category is mapped to ATT&CK tactics to compute tactic coverage and the
  furthest kill-chain stage.

Usage (run from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e1b_build_incidents.py
"""
import json
import duckdb

SRC = {"train": "data/processed/guide_train.parquet", "test": "data/processed/guide_test.parquet"}
CHECKS = json.load(open("experiments/results/e1a_guide_checks.json"))
PH = {c: v["top_value"] for c, v in CHECKS["placeholders"].items() if v["top_value"] is not None}

# ATT&CK enterprise tactic order (kill-chain stage index); GUIDE categories that
# are not tactics (Malware, Ransomware, SuspiciousActivity, ...) get no stage.
TACTIC_ORDER = ["InitialAccess", "Execution", "Persistence", "PrivilegeEscalation",
                "DefenseEvasion", "CredentialAccess", "Discovery", "LateralMovement",
                "Collection", "CommandAndControl", "Exfiltration", "Impact"]
CATEGORIES = TACTIC_ORDER + ["CredentialStealing", "Exploit", "Malware", "Ransomware",
                             "SuspiciousActivity", "UnwantedSoftware", "Weaponization", "WebExploit"]
ENTITY_TYPES = ["Ip", "User", "MailMessage", "Machine", "File", "Url", "CloudLogonRequest",
                "Mailbox", "Process", "MailCluster", "CloudApplication", "CloudLogonSession"]
DISTINCT_ENTITIES = {"n_devices": "DeviceId", "n_accounts": "AccountObjectId", "n_ips": "IpAddress",
                     "n_files": "Sha256", "n_urls": "Url", "n_mails": "NetworkMessageId",
                     "n_apps": "ApplicationId", "n_countries": "CountryCode"}

con = duckdb.connect()
stage_case = "CASE Category " + " ".join(
    f"WHEN '{t}' THEN {i + 1}" for i, t in enumerate(TACTIC_ORDER)) + " ELSE NULL END"

def q(s):
    return s.replace("'", "''")

feats = [
    "count(*) AS n_evidence",
    "count(DISTINCT AlertId) AS n_alerts",
    "count(DISTINCT DetectorId) AS n_detectors",
    "count(DISTINCT AlertTitle) AS n_alert_titles",
    "count(DISTINCT Category) AS n_categories",
    "count(DISTINCT CASE WHEN stage IS NOT NULL THEN Category END) AS n_tactics",
    "coalesce(max(stage), 0) AS max_stage",
    "coalesce(min(stage), 0) AS min_stage",
    "epoch(max(Timestamp)) - epoch(min(Timestamp)) AS duration_s",
    "hour(min(Timestamp)) AS first_hour",
    "isodow(min(Timestamp)) AS first_dow",
    "avg(CASE WHEN MitreTechniques IS NOT NULL THEN 1 ELSE 0 END) AS mitre_row_share",
    "count(*) FILTER (WHERE EvidenceRole = 'Impacted') AS n_impacted",
    "count(*) FILTER (WHERE EvidenceRole = 'Related') AS n_related",
    "count(*) FILTER (WHERE SuspicionLevel = 'Suspicious') AS n_susp_suspicious",
    "count(*) FILTER (WHERE SuspicionLevel = 'Incriminated') AS n_susp_incriminated",
    "count(*) FILTER (WHERE LastVerdict = 'Malicious') AS n_verdict_malicious",
    "count(*) FILTER (WHERE LastVerdict = 'Suspicious') AS n_verdict_suspicious",
    "count(*) FILTER (WHERE LastVerdict = 'NoThreatsFound') AS n_verdict_nothreat",
    "count(*) FILTER (WHERE ThreatFamily IS NOT NULL) AS n_threatfamily",
    "count(*) FILTER (WHERE AntispamDirection = 'Inbound') AS n_mail_inbound",
    "count(*) FILTER (WHERE AntispamDirection = 'Outbound') AS n_mail_outbound",
    "count(*) FILTER (WHERE AntispamDirection = 'Intraorg') AS n_mail_intraorg",
    "count(*) FILTER (WHERE ResourceType IS NOT NULL) AS n_resource",
    "count(*) FILTER (WHERE Roles IS NOT NULL) AS n_roles",
]
feats += [f"count(DISTINCT AlertId) FILTER (WHERE Category = '{q(c)}') AS cat_{c}" for c in CATEGORIES]
feats += [f"count(*) FILTER (WHERE EntityType = '{q(t)}') AS ent_{t}" for t in ENTITY_TYPES]
feats.append("count(*) FILTER (WHERE EntityType NOT IN (" + ", ".join(f"'{t}'" for t in ENTITY_TYPES) + ")) AS ent_Other")
for name, col in DISTINCT_ENTITIES.items():
    feats.append(f"count(DISTINCT CASE WHEN {col} <> {PH[col]} THEN {col} END) AS {name}")

parts = []
for source, path in SRC.items():
    parts.append(f"""
      SELECT '{source}' AS source, OrgId, IncidentId,
             any_value(IncidentGrade) AS label,
             min(Timestamp) AS first_ts,
             {", ".join(feats)}
      FROM (SELECT *, {stage_case} AS stage FROM '{path}')
      GROUP BY OrgId, IncidentId
      HAVING count(IncidentGrade) > 0""")
con.execute("COPY (" + " UNION ALL ".join(parts) + ") TO 'data/processed/incidents.parquet' (FORMAT parquet)")

# distinct ATT&CK techniques per incident (MitreTechniques is ';'-separated)
tech_parts = [f"""
  SELECT '{s}' AS source, OrgId, IncidentId, count(DISTINCT t) AS n_techniques
  FROM (SELECT OrgId, IncidentId, unnest(string_split(MitreTechniques, ';')) AS t
        FROM '{p}' WHERE MitreTechniques IS NOT NULL)
  GROUP BY 1, 2, 3""" for s, p in SRC.items()]
con.execute(f"""
  COPY (SELECT i.*, coalesce(t.n_techniques, 0) AS n_techniques
        FROM 'data/processed/incidents.parquet' i
        LEFT JOIN ({" UNION ALL ".join(tech_parts)}) t USING (source, OrgId, IncidentId))
  TO 'data/processed/incidents_full.parquet' (FORMAT parquet)""")

alert_parts = [f"""
  SELECT DISTINCT '{s}' AS source, OrgId, IncidentId, AlertId, DetectorId, AlertTitle
  FROM '{p}'""" for s, p in SRC.items()]
con.execute("COPY (" + " UNION ALL ".join(alert_parts) + ") TO 'data/processed/alerts.parquet' (FORMAT parquet)")

summary = con.execute("""
  SELECT source, count(*) AS incidents, count(DISTINCT (source, OrgId, IncidentId)) AS unique_keys,
         count(*) FILTER (WHERE label = 'TruePositive') AS tp,
         count(*) FILTER (WHERE label = 'BenignPositive') AS bp,
         count(*) FILTER (WHERE label = 'FalsePositive') AS fp
  FROM 'data/processed/incidents_full.parquet' GROUP BY 1 ORDER BY 1""").fetchall()
for row in summary:
    print(dict(zip(["source", "incidents", "unique_keys", "tp", "bp", "fp"], row)))
print("alerts rows:", con.execute("select count(*) from 'data/processed/alerts.parquet'").fetchone()[0])
print("feature columns:", len(con.execute("describe select * from 'data/processed/incidents_full.parquet'").fetchall()))
