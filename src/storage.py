import csv
import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE  = Path("data.db")
CSV_FILE = Path("data.csv")

TABLE_NAME = "kravi_hora"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                time  INTEGER PRIMARY KEY,
                val   INTEGER NOT NULL
            )
        """)


def migrate_from_csv():
    if not CSV_FILE.exists():
        return

    print(f"[MIGRATION] Found {CSV_FILE}, migrating to SQLite...")

    migrated = 0
    skipped  = 0

    with _connect() as conn, open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 2:
                skipped += 1
                continue
            try:
                ts  = int(float(row[0]))
                val = int(row[1])
                conn.execute(
                    f"INSERT OR IGNORE INTO {TABLE_NAME} (time, val) VALUES (?, ?)",
                    (ts, val),
                )
                migrated += 1
            except (ValueError, sqlite3.Error) as e:
                print(f"[MIGRATION] Skipping row {row}: {e}")
                skipped += 1

    CSV_FILE.rename(CSV_FILE.with_suffix(".csv.bak"))
    print(f"[MIGRATION] Done: {migrated} records migrated, {skipped} skipped. "
          f"Original file renamed to {CSV_FILE.with_suffix('.csv.bak')}")


def append_record(value: int):
    ts = int(datetime.now().timestamp())
    with _connect() as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO {TABLE_NAME} (time, val) VALUES (?, ?)",
            (ts, value),
        )


def read_records(start: str = None, end: str = None) -> list[dict]:
    query  = f"SELECT time, val FROM {TABLE_NAME}"
    params = []

    conditions = []
    if start:
        conditions.append("time >= ?")
        params.append(int(datetime.fromisoformat(start).timestamp()))
    if end:
        conditions.append("time <= ?")
        params.append(int(datetime.fromisoformat(end).timestamp()))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY time"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    return [{"time": row["time"], "val": row["val"]} for row in rows]