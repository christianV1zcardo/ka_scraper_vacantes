"""Core utilities for scraper infrastructure."""

from .browser import create_firefox_driver
from .base import BaseScraper

__all__ = [
    "BaseScraper",
    "create_firefox_driver",
]
