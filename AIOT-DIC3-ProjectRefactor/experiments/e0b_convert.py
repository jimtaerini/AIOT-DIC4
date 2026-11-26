"""Convert the GUIDE CSVs to Parquet once, for fast DuckDB queries.

Usage (run from AIOT-DIC3-ProjectRefactor/):
    ../.venv/bin/python experiments/e0b_convert.py
Writes data/processed/guide_train.parquet and guide_test.parquet (git-ignored).
"""
from pathlib import Path
import duckdb

Path("data/processed").mkdir(parents=True, exist_ok=True)
con = duckdb.connect()
for name in ["Train", "Test"]:
    src, dst = f"data/archive/GUIDE_{name}.csv", f"data/processed/guide_{name.lower()}.parquet"
    con.execute(f"COPY (SELECT * FROM read_csv('{src}', header=true, sample_size=-1)) TO '{dst}' (FORMAT parquet)")
    print(dst, con.execute(f"select count(*) from '{dst}'").fetchone()[0], "rows")
