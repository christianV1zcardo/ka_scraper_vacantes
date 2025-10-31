"""Common scraper behaviour abstractions."""

from __future__ import annotations

import time
from typing import Callable, Dict, List, Optional

from selenium.webdriver.remote.webdriver import WebDriver

from .browser import create_firefox_driver

JobPayload = Dict[str, str]


class BaseScraper:
    """Base Selenium scraper with pagination helpers."""

    max_pages: int = 50

    def __init__(
        self,
        driver: Optional[WebDriver] = None,
        headless: Optional[bool] = True,
    ) -> None:
        self.driver: WebDriver = driver or create_firefox_driver(headless=headless)

    def close(self) -> None:
        """Terminate the underlying browser session."""
        if not getattr(self, "driver", None):
            return
        try:
            self.driver.quit()
        finally:
            self.driver = None  # type: ignore[assignment]

    def gather_paginated(
        self,
        extractor: Callable[[], List[JobPayload]],
        navigator: Optional[Callable[[int], bool]] = None,
        page_wait: float = 1.0,
    ) -> List[JobPayload]:
        """Aggregate job payloads across paginated listings."""
        results: List[JobPayload] = []
        seen: set[str] = set()
        page = 1
        while page <= self.max_pages:
            if page > 1:
                if navigator and not navigator(page):
                    break
                if page_wait:
                    time.sleep(page_wait)
            current = extractor()
            new_found = 0
            for payload in current:
                url = payload.get("url")
                if not url or url in seen:
                    continue
                seen.add(url)
                results.append(payload)
                new_found += 1
            if new_found == 0:
                break
            page += 1
        return results
