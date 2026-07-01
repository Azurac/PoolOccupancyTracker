import asyncio

from src.collectors.schedule_helper import ScheduleHelper
from src.scrapers.base_scraper import BaseScraper
from src.storage.occupancy_repository import OccupancyRepository


class CollectorLoop:
    def __init__(self, scraper: BaseScraper, repository: OccupancyRepository, schedule: ScheduleHelper):
        self._scraper = scraper
        self._repository = repository
        self._schedule = schedule
        self._name = scraper.config.name

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self._seconds_until_next_collection())
                await self._collect()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[ERROR] Collector {self._name} failed: {e}")

    def _seconds_until_next_collection(self) -> float:
        cfg = self._scraper.config
        if self._schedule.is_within_hours(cfg.visit_hours_start, cfg.visit_hours_end):
            return self._schedule.seconds_until_next_interval(cfg.interval_minutes)
        return self._schedule.seconds_until_hour(cfg.visit_hours_start)

    async def _collect(self):
        value = asyncio.to_thread(self._scraper.fetch_occupancy)
        if value is not None:
            self._repository.save(value)
            print(f"[COLLECTED] {self._name} has {value}")
        else:
            print(f"[COLLECTED] {self._name} has no data")