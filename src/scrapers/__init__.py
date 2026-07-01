import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import Optional

from src.scrapers.base_scraper import BaseScraper

# Name of the abstract base class itself, excluded when scanning module members.
_BASE_SCRAPER_NAME = BaseScraper.__name__


def discover_scraper_classes(package: Optional[ModuleType] = None) -> list[type[BaseScraper]]:
    """Dynamically discover all concrete BaseScraper subclasses in a package.

    Iterates over every submodule of the given package (defaults to this
    package), imports it, and collects classes that inherit from BaseScraper.
    Abstract classes and BaseScraper itself are skipped. This removes the need
    to manually register every new scraper class.
    """
    target_package = package if package is not None else importlib.import_module(__name__)
    discovered: list[type[BaseScraper]] = []

    for _, module_name, _ in pkgutil.iter_modules(target_package.__path__, prefix=f"{target_package.__name__}."):
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name == _BASE_SCRAPER_NAME:
                continue
            if not issubclass(obj, BaseScraper) or inspect.isabstract(obj):
                continue
            if obj not in discovered:
                discovered.append(obj)

    return discovered


__all__ = ["BaseScraper", "discover_scraper_classes"]