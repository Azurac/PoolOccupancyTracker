import csv
from datetime import datetime, UTC
from pathlib import Path

FILE = Path("data.csv")


def append_record(value: int):
    with open(FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(UTC).timestamp(), value])

def read_records(start=None, end=None):
    if not FILE.exists():
        return []

    results = []

    with open(FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            ts, value = row
            ts = float(ts)

            if start and ts < datetime.fromisoformat(start).timestamp():
                continue
            if end and ts > datetime.fromisoformat(end).timestamp():
                continue

            results.append({
                "timestamp": ts,
                "value": int(value)
            })

    return results
