from datetime import datetime

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

    def find_by_range(self, start: str = None, end: str = None, limit: int = DEFAULT_QUERY_LIMIT) -> list[
        OccupancyRecord]:
        limit = min(limit, DEFAULT_QUERY_LIMIT)

        query = f"SELECT time, val FROM {self._table_name}"
        params: list = []
        conditions = []

        if start:
            conditions.append("time >= ?")
            params.append(int(datetime.fromisoformat(start).timestamp()))
        if end:
            conditions.append("time <= ?")
            params.append(int(datetime.fromisoformat(end).timestamp()))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY time LIMIT ?"
        params.append(limit)

        with self._db.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [OccupancyRecord(time=row["time"], val=row["val"]) for row in rows]
