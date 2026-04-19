from dataclasses import dataclass


@dataclass(frozen=True)
class PoolConfig:
    id: str
    name: str
    interval_minutes: int
    visit_hours_start: int
    visit_hours_end: int

    def get_rollout_limit(self) -> int:
        rollout_hours = self.visit_hours_end - self.visit_hours_start
        return rollout_hours * (60 // self.interval_minutes) + 1