from typing import Union

from src.collectors import ScheduleHelper, CollectorLoop
from src.scrapers import KraviHoraScraper, BaseScraper
from src.storage import Database, OccupancyRepository

_scrapers: list[BaseScraper] = [
    KraviHoraScraper()
]
_repositories: dict[str, OccupancyRepository] = {}


def create_collectors(db: Database, schedule: ScheduleHelper) -> list[CollectorLoop]:
    global _repositories
    _repositories = _create_repositories(db)
    return [
        CollectorLoop(s, r, schedule)
        for s, r in zip(_scrapers, _repositories.values())
    ]


def get_all_scrapers() -> list[BaseScraper]:
    return list(_scrapers)


def get_repository(id: str) -> OccupancyRepository:
    return _repositories[id]


def get_scraper(id: str) -> Union[BaseScraper, None]:
    return next(filter(lambda s: s.config.id == id, _scrapers), None)


def _create_repositories(db: Database) -> dict[str, OccupancyRepository]:
    _init_db_tables(db)
    return {s.config.id: OccupancyRepository(db, s.config.id) for s in _scrapers}


def _init_db_tables(db: Database):
    for scraper in _scrapers:
        db.init(scraper.config.id)