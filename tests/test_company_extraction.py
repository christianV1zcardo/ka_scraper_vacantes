import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.selenium_stub import ensure_selenium_stub

ensure_selenium_stub()

from selenium.webdriver.common.by import By  # type: ignore

from src.bumeran import BumeranScraper
from src.computrabajo import ComputrabajoScraper


def build_element(text: str = "", css_map=None, xpath_parent=None):
    css_map = css_map or {}
    element = Mock()
    element.text = text

    def find_elements(by, selector):
        return css_map.get((by, selector), [])

    element.find_elements.side_effect = find_elements

    if xpath_parent is not None:
        def find_element(by, selector):
            if (by, selector) == (By.XPATH, "ancestor::article[1]"):
                return xpath_parent
            raise Exception("not found")

        element.find_element.side_effect = find_element
    else:
        def not_found(by, selector):
            raise Exception("not found")

        element.find_element.side_effect = not_found

    return element


class CompanyExtractionTests(unittest.TestCase):
    def test_bumeran_prefers_specific_company_selectors(self) -> None:
        company_node = build_element(text="TalentoHumano.pe")
        title_node = build_element(text="Analista de Datos")
        anchor = build_element(
            css_map={
                (By.CSS_SELECTOR, "h2"): [title_node],
                (By.CSS_SELECTOR, "span.sc-Ehqfj h3"): [company_node],
            }
        )
        scraper = BumeranScraper(driver=Mock())
        company = scraper._extract_company(anchor)
        self.assertEqual(company, "TalentoHumano.pe")

    def test_bumeran_filters_non_company_text(self) -> None:
        company_node = build_element(text="Publicado hace 5 días")
        fallback_node = build_element(text="Empresa Confidencial")
        anchor = build_element(
            css_map={
                (By.CSS_SELECTOR, "h2"): [build_element(text="Analista QA")],
                (By.CSS_SELECTOR, "span.sc-Ehqfj h3"): [company_node],
                (By.CSS_SELECTOR, "h3"): [company_node, fallback_node],
            }
        )
        scraper = BumeranScraper(driver=Mock())
        company = scraper._extract_company(anchor)
        self.assertEqual(company, "Empresa Confidencial")

    def test_bumeran_accepts_alternative_h3_selector(self) -> None:
        anchor = build_element(
            css_map={
                (By.CSS_SELECTOR, "h2"): [build_element(text="Analista QA")],
                (By.CSS_SELECTOR, "h3.sc-ebDnpS"): [build_element(text="FinCorp")],
            }
        )
        scraper = BumeranScraper(driver=Mock())
        company = scraper._extract_company(anchor)
        self.assertEqual(company, "FinCorp")

    def test_computrabajo_extracts_from_card_wrapper(self) -> None:
        company_node = build_element(text="Tech Corp")
        parent = build_element(
            css_map={
                (By.CSS_SELECTOR, "span.fs16.fc_base.mt5.fc_base.fc_base"): [company_node]
            }
        )
        anchor = build_element(
            css_map={
                (By.CSS_SELECTOR, "span.fs16.fc_base.mt5.fc_base.fc_base"): [],
            },
            xpath_parent=parent,
        )
        scraper = ComputrabajoScraper(driver=Mock())
        company = scraper._extract_company(anchor, title_text="Analista Jr")
        self.assertEqual(company, "Tech Corp")

    def test_computrabajo_skips_title_matches(self) -> None:
        parent = build_element(
            css_map={
                (By.CSS_SELECTOR, "span.fs16.fc_base.mt5.fc_base.fc_base"): [build_element(text="Analista Jr")]
            }
        )
        anchor = build_element(
            css_map={
                (By.CSS_SELECTOR, "span.fs13.fc_aux.tx_ellipsis"): [
                    build_element(text="Analista Jr"),
                    build_element(text="MegaCorp"),
                ]
            },
            xpath_parent=parent,
        )
        scraper = ComputrabajoScraper(driver=Mock())
        company = scraper._extract_company(anchor, title_text="Analista Jr")
        self.assertEqual(company, "MegaCorp")

    def test_computrabajo_skips_relative_time_entries(self) -> None:
        parent = build_element(
            css_map={
                (By.CSS_SELECTOR, "span.fs13.fc_aux.tx_ellipsis"): [
                    build_element(text="Hace 2 días"),
                    build_element(text="DataCorp"),
                ]
            }
        )
        anchor = build_element(css_map={}, xpath_parent=parent)
        scraper = ComputrabajoScraper(driver=Mock())
        company = scraper._extract_company(anchor, title_text="Analista")
        self.assertEqual(company, "DataCorp")


if __name__ == "__main__":
    unittest.main()
