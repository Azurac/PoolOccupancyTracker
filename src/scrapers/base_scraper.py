from abc import ABC, abstractmethod
from typing import Union


class BaseScraper(ABC):
    @abstractmethod
    def fetch_occupancy(self) -> Union[int, None]:
        """Fetch current pool occupancy. Returns None on failure."""
        ...