from dataclasses import dataclass


@dataclass(frozen=True)
class OccupancyRecord:
    time: int
    val: int

    def to_dict(self) -> dict:
        return {"time": self.time, "val": self.val}