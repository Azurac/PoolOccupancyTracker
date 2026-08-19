from datetime import datetime
from typing import Optional

from src.storage.database import Database
from src.storage.occupancy_record import OccupancyRecord

DEFAULT_QUERY_LIMIT = 200

class OccupancyRepository:

    def __init__(self, db: Database, table_name: str):
        self._db = db
        self._table_name = table_name

    def save(self, value: int):
        ts = int(datetime.now().timestamp())
        with self._db.connect() as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {self._table_name} (time, val) VALUES (?, ?)",
                (ts, value),
            )

    def find_latest(self, n: int) -> list[OccupancyRecord]:
        if n <= 0:
            return []

        with self._db.connect() as conn:
            rows = conn.execute(
                f"SELECT time, val FROM {self._table_name} ORDER BY time DESC LIMIT ?",
                (n,),
            ).fetchall()
        return [OccupancyRecord(time=row["time"], val=row["val"]) for row in reversed(rows)]

    def find_by_range_str(self, start: Optional[str] = None, end: Optional[str] = None,
                          limit: int = DEFAULT_QUERY_LIMIT) -> list[OccupancyRecord]:
        limit = min(limit, DEFAULT_QUERY_LIMIT)

        return self.find_by_range(
            start=int(datetime.fromisoformat(start).timestamp()) if start else 0,
            end=int(datetime.fromisoformat(end).timestamp()) if end else 0,
            limit=limit
        )

    def find_by_range(self, start: int = 0, end: int = 0, limit: int = DEFAULT_QUERY_LIMIT) -> list[
        OccupancyRecord]:
        limit = min(limit, DEFAULT_QUERY_LIMIT)

        query = f"SELECT time, val FROM {self._table_name}"
        params: list = []
        conditions = []

        if start:
            conditions.append("time >= ?")
            params.append(start)
        if end:
            conditions.append("time <= ?")
            params.append(end)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY time LIMIT ?"
        params.append(limit)

        with self._db.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [OccupancyRecord(time=row["time"], val=row["val"]) for row in rows]
