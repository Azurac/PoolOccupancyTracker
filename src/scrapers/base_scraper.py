from abc import ABC, abstractmethod
from typing import Union

from src.pools.pool_config import PoolConfig


class BaseScraper(ABC):
    @property
    @abstractmethod
    def config(self) -> PoolConfig: ...

    @abstractmethod
    def fetch_occupancy(self) -> Union[int, None]:
        """Fetch current pool occupancy. Returns None on failure."""
        ...