from functools import cached_property
from typing import Union

import requests
from bs4 import BeautifulSoup

from src.pools.pool_config import PoolConfig
from src.scrapers.base_scraper import BaseScraper

_URL = "https://www.sumperksportuje.cz/aquacentrum/kryty-bazen"
_REQUEST_TIMEOUT = 10


class SumperkAquacenterScraper(BaseScraper):
    @cached_property
    def config(self) -> PoolConfig:
        return PoolConfig(
            id="spk_aquacentrum",
            name="Aquacentrum Šumperk",
            interval_minutes=1,
            visit_hours_start=0,
            visit_hours_end=20,
            occupancy_thresholds=(30, 50, 80),
        )

    def fetch_occupancy(self) -> Union[int, None]:
        try:
            response = requests.get(_URL, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
            return self._parse_occupancy(response.text)
        except Exception as e:
            print(f"[SCRAPER ERROR] {e}")
            return None

    def _parse_occupancy(self, html: str) -> Union[int, None]:
        soup = BeautifulSoup(html, "html.parser")

        for p in soup.find_all("span", {"id": "pool-part-count"}):
            value_text = p.get_text(strip=True).lower() # e.g. "0 / 135"

            return int(value_text.split("/")[0].strip())

        return None
