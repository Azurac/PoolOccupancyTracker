import csv
from datetime import datetime
from pathlib import Path

FILE = Path("data.csv")


def append_record(value: int):
    with open(FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.utcnow().isoformat(), value])


def read_records(start=None, end=None):
    if not FILE.exists():
        return []

    results = []

    with open(FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            ts, value = row

            if start and ts < start:
                continue
            if end and ts > end:
                continue

            results.append({
                "timestamp": ts,
                "value": int(value)
            })

    return results
