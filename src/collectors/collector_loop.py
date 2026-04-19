import asyncio

from src.collectors.schedule_helper import ScheduleHelper
from src.config import COLLECTOR_INTERVAL_MINUTES, VISIT_HOURS_START, VISIT_HOURS_END
from src.scrapers.base_scraper import BaseScraper
from src.storage.occupancy_repository import OccupancyRepository


class CollectorLoop:
    def __init__(self, scraper: BaseScraper, repository: OccupancyRepository, schedule: ScheduleHelper):
        self._scraper = scraper
        self._repository = repository
        self._schedule = schedule

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self._seconds_until_next_collection())
                self._collect()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[ERROR] Collector failed: {e}")

    def _seconds_until_next_collection(self) -> float:
        if self._schedule.is_within_hours(VISIT_HOURS_START, VISIT_HOURS_END):
            return self._schedule.seconds_until_next_interval(COLLECTOR_INTERVAL_MINUTES)
        return self._schedule.seconds_until_hour(VISIT_HOURS_START)

    def _collect(self):
        value = self._scraper.fetch_occupancy()
        if value is not None:
            self._repository.save(value)
            print(f"[COLLECTED] {value}")
        else:
            print("[COLLECTED] no data")