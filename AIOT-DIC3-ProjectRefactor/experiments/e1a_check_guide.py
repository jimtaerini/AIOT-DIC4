"""E1a: data checks before aggregation (task 1.2 of build-soc-triage-agent).

1. Placeholder IDs: for each anonymized entity column, the most frequent value
   and how often it appears on rows whose EntityType is NOT that entity.
   A value that dominates unrelated rows is a "no such entity" placeholder.
2. Label consistency: do all rows of one incident (OrgId, IncidentId) carry the
   same IncidentGrade?
3. Train/test overlap: do official train and test share incident keys or orgs?

Usage (run from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e0b_convert.py   # (once) CSV -> Parquet
    ../.venv/bin/python experiments/e1a_check_guide.py > experiments/results/e1a_guide_checks.json
"""
import json
import duckdb

TRAIN = "data/processed/guide_train.parquet"
TEST = "data/processed/guide_test.parquet"

# entity column -> EntityType values that legitimately carry it
ENTITY_COLS = {
    "DeviceId": ["Machine"], "DeviceName": ["Machine"],
    "Sha256": ["File", "Process"], "FileName": ["File", "Process"], "FolderPath": ["File", "Process"],
    "IpAddress": ["Ip"], "Url": ["Url"],
    "AccountSid": ["User", "Account"], "AccountUpn": ["User", "Account", "Mailbox"],
    "AccountObjectId": ["User", "Account"], "AccountName": ["User", "Account"],
    "NetworkMessageId": ["MailMessage"], "EmailClusterId": ["MailCluster"],
    "RegistryKey": ["RegistryKey", "RegistryValue"], "RegistryValueName": ["RegistryValue"],
    "RegistryValueData": ["RegistryValue"],
    "ApplicationId": ["CloudApplication", "OAuthApplication"], "ApplicationName": ["CloudApplication", "OAuthApplication"],
    "OAuthApplicationId": ["OAuthApplication"], "ResourceIdName": ["AzureResource"],
    "OSFamily": ["Machine"], "OSVersion": ["Machine"],
    "CountryCode": ["Ip"], "State": ["Ip"], "City": ["Ip"],
}

con = duckdb.connect()
out = {"placeholders": {}, "label_consistency": {}, "train_test_overlap": {}}

total = con.execute(f"select count(*) from '{TRAIN}'").fetchone()[0]
for col, types in ENTITY_COLS.items():
    tlist = ", ".join(f"'{t}'" for t in types)
    top, n = con.execute(
        f"select {col}, count(*) c from '{TRAIN}' group by 1 order by c desc limit 1").fetchone()
    unrelated, unrelated_top = con.execute(f"""
        select count(*), count(*) filter (where {col} = ?)
        from '{TRAIN}' where EntityType not in ({tlist})""", [top]).fetchone()
    out["placeholders"][col] = {
        "top_value": top, "top_share_all_rows": round(n / total, 4),
        "top_share_on_unrelated_rows": round(unrelated_top / unrelated, 4) if unrelated else None,
    }

# label consistency per incident
r = con.execute(f"""
    with g as (
      select OrgId, IncidentId, count(distinct IncidentGrade) k,
             count(*) filter (where IncidentGrade is null) nulls
      from '{TRAIN}' group by 1, 2)
    select count(*), count(*) filter (where k > 1), count(*) filter (where k = 0),
           count(*) filter (where nulls > 0 and k = 1)
    from g""").fetchone()
out["label_consistency"] = {
    "incidents": r[0], "incidents_with_conflicting_grades": r[1],
    "incidents_without_grade": r[2], "incidents_with_some_null_rows": r[3],
}

# official train/test overlap
out["train_test_overlap"] = {
    "test_incidents": con.execute(f"select count(*) from (select distinct OrgId, IncidentId from '{TEST}')").fetchone()[0],
    "shared_incident_keys": con.execute(f"""select count(*) from
        (select distinct OrgId, IncidentId from '{TRAIN}') a join
        (select distinct OrgId, IncidentId from '{TEST}') b using (OrgId, IncidentId)""").fetchone()[0],
    "test_orgs": con.execute(f"select count(distinct OrgId) from '{TEST}'").fetchone()[0],
    "test_orgs_also_in_train": con.execute(f"""select count(*) from
        (select distinct OrgId from '{TEST}') b where OrgId in (select distinct OrgId from '{TRAIN}')""").fetchone()[0],
    "train_time_range": [str(x) for x in con.execute(f"select min(Timestamp), max(Timestamp) from '{TRAIN}'").fetchone()],
    "test_time_range": [str(x) for x in con.execute(f"select min(Timestamp), max(Timestamp) from '{TEST}'").fetchone()],
}
print(json.dumps(out, indent=1, default=str))
