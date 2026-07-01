import re
from functools import cached_property
from typing import Union

import requests
from bs4 import BeautifulSoup

from src.pools.pool_config import PoolConfig
from src.scrapers.base_scraper import BaseScraper

_URL_INSIDE = "https://www.zabreh-bazen.cz/kryty-bazen"
_URL_OUTSIDE = "https://www.zabreh-bazen.cz/venkovni-areal"
_OCCUPANCY_PREFIX = "bazén:"
_REQUEST_TIMEOUT = 10


class ZabrehPoolInsideScraper(BaseScraper):
    @cached_property
    def config(self) -> PoolConfig:
        return PoolConfig(
            id="zabreh_inside",
            name="Bazén Zábřeh - Krytý",
            interval_minutes=10,
            visit_hours_start=8,
            visit_hours_end=20,
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

        for p in soup.find_all("div", {"class":"item obsazenost"}):
            text = p.get_text(strip=True).lower()
            if not text.startswith(_OCCUPANCY_PREFIX):
                continue

            # "Bazén:  lidí      Obsazenost drah:  "
            if m:=re.match(rf"{_OCCUPANCY_PREFIX}\s*(\d+)\s*lidí", text):
                return int(m.group(1))

        return None


class ZabrehPoolOutsideScraper(BaseScraper):
    @cached_property
    def config(self) -> PoolConfig:
        return PoolConfig(
            id="zabreh_outside",
            name="Bazén Zábřeh - Venkovní",
            interval_minutes=10,
            visit_hours_start=10,
            visit_hours_end=20,
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

        occupancy_item = soup.find("div", {"class": "item obsazenost"})
        if not occupancy_item:
            return None

        for p in occupancy_item.find_all("div"):
            text = p.get_text(strip=True).lower()
            if not text.startswith("venkovní"):
                continue

            # "Venkovní bazén: 0"
            if m := re.match(rf"venkovní bazén:\s*(\d+)", text):
                return int(m.group(1))

        return None
