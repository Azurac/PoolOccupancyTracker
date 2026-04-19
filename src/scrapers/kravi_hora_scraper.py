from typing import Union

import requests
from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper

_URL = "https://www.kravihora-brno.cz/kryta-plavecka-hala"
_OCCUPANCY_PREFIX = "obsazenost"
_REQUEST_TIMEOUT = 10


class KraviHoraScraper(BaseScraper):
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