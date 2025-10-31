"""Browser creation utilities."""

from __future__ import annotations

import os
from typing import Optional

from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def create_firefox_driver(headless: Optional[bool] = None) -> webdriver.Firefox:
    """Create a Firefox WebDriver instance.

    Headless mode is enabled by default. You can toggle it via the ``headless``
    argument or the ``SCRAPER_HEADLESS`` environment variable (set to ``0`` or
    ``false`` to disable).
    """
    options = Options()
    resolved_headless = headless
    if resolved_headless is None:
        env_value = os.getenv("SCRAPER_HEADLESS")
        if env_value is not None:
            resolved_headless = env_value not in {"0", "false", "False"}
    if resolved_headless is None:
        resolved_headless = True
    if resolved_headless:
        options.add_argument("-headless")
    return webdriver.Firefox(options=options)
