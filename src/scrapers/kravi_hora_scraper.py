from functools import cached_property
from typing import Union

import requests
from bs4 import BeautifulSoup

from src.pools.pool_config import PoolConfig
from src.scrapers.base_scraper import BaseScraper

_URL_INSIDE = "https://www.kravihora-brno.cz/kryta-plavecka-hala"
_URL_OUTSIDE = "https://www.kravihora-brno.cz/venkovni-bazeny"
_OCCUPANCY_PREFIX = "obsazenost"
_REQUEST_TIMEOUT = 10


class KraviHoraInsideScraper(BaseScraper):
    @cached_property
    def config(self) -> PoolConfig:
        return PoolConfig(
            id="kravi_hora",
            name="Kraví Hora - Vnitřní",
            interval_minutes=10,
            visit_hours_start=6,
            visit_hours_end=22,
            occupancy_thresholds=(30, 50, 80),
        )

    def fetch_occupancy(self) -> Union[int, None]:
        try:
            response = requests.get(_URL_INSIDE, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
            return self._parse_occupancy(response.text)
        except Exception as e:
            print(f"[SCRAPER ERROR] {e}")
            return None

    def _parse_occupancy(self, html: str) -> Union[int, None]:
        soup = BeautifulSoup(html, "html.parser")

        for p in soup.find_all("p"):
            text = p.get_text(strip=True).lower()
            if not text.startswith(_OCCUPANCY_PREFIX):
                continue

            strong = p.find("strong")
            if not strong:
                continue

            value_text = strong.get_text(strip=True)  # e.g. "0 / 135"
            if "/" not in value_text:
                return None

            return int(value_text.split("/")[0].strip())

        return None


class KraviHoraOutsideScraper(BaseScraper):
    @cached_property
    def config(self) -> PoolConfig:
        return PoolConfig(
            id="kravi_hora_outside",
            name="Kraví Hora - Venkovní",
            interval_minutes=10,
            visit_hours_start=7,
            visit_hours_end=21,
            occupancy_thresholds=(100, 300, 500),
        )

    def fetch_occupancy(self) -> Union[int, None]:
        try:
            response = requests.get(_URL_OUTSIDE, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
            return self._parse_occupancy(response.text)
        except Exception as e:
            print(f"[SCRAPER ERROR] {e}")
            return None

    def _parse_occupancy(self, html: str) -> Union[int, None]:
        soup = BeautifulSoup(html, "html.parser")

        for p in soup.find_all("p"):
            text = p.get_text(strip=True).lower()
            if not text.startswith(_OCCUPANCY_PREFIX):
                continue

            strong = p.find("strong")
            if not strong:
                continue

            value_text = strong.get_text(strip=True)

            return int(value_text.strip())

        return None