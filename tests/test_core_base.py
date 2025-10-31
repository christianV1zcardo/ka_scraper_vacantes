import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.selenium_stub import ensure_selenium_stub

ensure_selenium_stub()

from src.core.base import BaseScraper


class DummyScraper(BaseScraper):
    def __init__(self) -> None:
        super().__init__(driver=Mock())
        self.max_pages = 5


class BaseScraperTests(unittest.TestCase):
    def test_gather_paginated_deduplicates_results(self) -> None:
        scraper = DummyScraper()
        pages = [
            [{"url": "u1", "titulo": "Job 1"}, {"url": "u2", "titulo": "Job 2"}],
            [{"url": "u2", "titulo": "Job 2 updated"}, {"url": "u3", "titulo": "Job 3"}],
        ]
        call_index = {"value": 0}
        visited_pages = []

        def extractor():
            index = min(call_index["value"], len(pages) - 1)
            call_index["value"] += 1
            return pages[index]

        def navigator(page: int) -> bool:
            visited_pages.append(page)
            return page <= len(pages)

        results = scraper.gather_paginated(extractor=extractor, navigator=navigator, page_wait=0)

        self.assertEqual(
            results,
            [
                {"url": "u1", "titulo": "Job 1"},
                {"url": "u2", "titulo": "Job 2"},
                {"url": "u3", "titulo": "Job 3"},
            ],
        )
        self.assertEqual(visited_pages, [2, 3])

    def test_gather_paginated_stops_when_no_new_results(self) -> None:
        scraper = DummyScraper()
        pages = [
            [{"url": "u1", "titulo": "Job 1"}],
            [{"url": "u1", "titulo": "Job 1 duplicate"}],
        ]
        call_index = {"value": 0}

        def extractor():
            index = min(call_index["value"], len(pages) - 1)
            call_index["value"] += 1
            return pages[index]

        results = scraper.gather_paginated(extractor=extractor, navigator=None, page_wait=0)

        self.assertEqual(results, [{"url": "u1", "titulo": "Job 1"}])

    def test_gather_paginated_respects_navigator_abort(self) -> None:
        scraper = DummyScraper()
        pages = [
            [{"url": "u1", "titulo": "Job 1"}],
            [{"url": "u2", "titulo": "Job 2"}],
        ]
        call_index = {"value": 0}
        visited_pages = []

        def extractor():
            index = min(call_index["value"], len(pages) - 1)
            call_index["value"] += 1
            return pages[index]

        def navigator(page: int) -> bool:
            visited_pages.append(page)
            return False

        results = scraper.gather_paginated(extractor=extractor, navigator=navigator, page_wait=0)

        self.assertEqual(results, [{"url": "u1", "titulo": "Job 1"}])
        self.assertEqual(visited_pages, [2])


if __name__ == "__main__":
    unittest.main()
