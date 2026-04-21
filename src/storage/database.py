import csv
import sqlite3
from pathlib import Path


class Database:

    def __init__(self, db_file: Path):
        self._db_file = db_file

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self, table_name):
        with self.connect() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    time  INTEGER PRIMARY KEY,
                    val   INTEGER NOT NULL
                )
            """)

    def migrate_from_csv(self, csv_file: Path, table_name: str):
        if not csv_file.exists():
            return

        print(f"[MIGRATION] Found {csv_file}, migrating to SQLite...")

        migrated = 0
        skipped = 0

        with self.connect() as conn, open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) != 2:
                    skipped += 1
                    continue
                try:
                    ts = int(float(row[0]))
                    val = int(row[1])
                    conn.execute(
                        f"INSERT OR IGNORE INTO {table_name} (time, val) VALUES (?, ?)",
                        (ts, val),
                    )
                    migrated += 1
                except (ValueError, sqlite3.Error) as e:
                    print(f"[MIGRATION] Skipping row {row}: {e}")
                    skipped += 1

        csv_file.rename(csv_file.with_suffix(".csv.bak"))
        print(
            f"[MIGRATION] Done: {migrated} records migrated to {table_name}, {skipped} skipped. "
            f"Original file renamed to {csv_file.with_suffix('.csv.bak')}"
        )