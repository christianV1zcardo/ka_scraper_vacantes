import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.selenium_stub import ensure_selenium_stub

ensure_selenium_stub()

import importlib

browser_module = importlib.import_module("src.core.browser")
create_firefox_driver = browser_module.create_firefox_driver


class BrowserFactoryTests(unittest.TestCase):
    def test_default_driver_uses_options_instance(self) -> None:
        with patch.object(browser_module, "Options") as mock_options, patch.object(
            browser_module.webdriver, "Firefox"
        ) as mock_firefox:
            options_instance = mock_options.return_value
            create_firefox_driver()
            mock_firefox.assert_called_once_with(options=options_instance)
            options_instance.add_argument.assert_not_called()

    def test_env_headless_flag_enables_headless_argument(self) -> None:
        with patch.object(browser_module, "Options") as mock_options, patch.object(
            browser_module.webdriver, "Firefox"
        ) as mock_firefox:
            options_instance = mock_options.return_value
            with patch.dict(os.environ, {"SCRAPER_HEADLESS": "1"}, clear=True):
                create_firefox_driver()
        options_instance.add_argument.assert_called_once_with("-headless")
        mock_firefox.assert_called_once()

    def test_explicit_headless_true_overrides_env(self) -> None:
        with patch.object(browser_module, "Options") as mock_options, patch.object(
            browser_module.webdriver, "Firefox"
        ) as mock_firefox:
            options_instance = mock_options.return_value
            with patch.dict(os.environ, {"SCRAPER_HEADLESS": "0"}, clear=True):
                create_firefox_driver(headless=True)
        options_instance.add_argument.assert_called_once_with("-headless")
        mock_firefox.assert_called_once()


if __name__ == "__main__":
    unittest.main()
