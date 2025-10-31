"""Computrabajo scraper implementation."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .core.base import BaseScraper

JobData = Dict[str, Any]


class ComputrabajoScraper(BaseScraper):
    BASE_URL = "https://www.computrabajo.com.pe/"
    SITE_ROOT = "https://pe.computrabajo.com"

    def __init__(self, driver=None, headless: Optional[bool] = True) -> None:
        super().__init__(driver=driver, headless=headless)
        self.pubdate = 0
        self.last_keyword = ""
        self._last_page_url: str = ""

    def abrir_pagina_empleos(self, hoy: bool = False, dias: int = 0) -> None:
        if dias == 1:
            self.pubdate = 1
        elif dias == 3:
            self.pubdate = 3
        else:
            self.pubdate = 0
        self.driver.get(self.BASE_URL)
        self._last_page_url = getattr(self.driver, "current_url", self.BASE_URL)

    def buscar_vacante(self, palabra_clave: str = "") -> None:
        keyword = palabra_clave.replace(" ", "-").lower()
        url = f"{self.SITE_ROOT}/trabajo-de-{keyword}"
        if self.pubdate:
            url = f"{url}?pubdate={self.pubdate}"
        try:
            self.driver.get(url)
            self.last_keyword = palabra_clave
            self._last_page_url = getattr(self.driver, "current_url", url)
        except Exception:
            pass

    def extraer_puestos(self, timeout: int = 10) -> List[JobData]:
        primary_wait = WebDriverWait(self.driver, min(timeout, 3))
        try:
            container = primary_wait.until(
                EC.presence_of_element_located((By.ID, "offersGridOfferContainer"))
            )
        except Exception:
            fallback_wait = WebDriverWait(self.driver, min(timeout, 3))
            container = fallback_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        anchors = container.find_elements(By.CSS_SELECTOR, "article a.js-o-link.fc_base")
        base_url = self._build_base_search_url()
        payloads: List[JobData] = []
        seen = set()
        for anchor in anchors:
            href = anchor.get_attribute("href") or ""
            text = (anchor.text or "").strip()
            if not href or not text:
                continue
            detail_url = self._build_detail_url(href, base_url)
            if not detail_url or detail_url in seen:
                continue
            title_text = text.split("\n")[0]
            company = self._extract_company(anchor, title_text)
            payloads.append({"titulo": title_text, "url": detail_url, "empresa": company})
            seen.add(detail_url)
        return payloads

    def extraer_todos_los_puestos(self, timeout: int = 10, page_wait: float = 1.0) -> List[JobData]:
        return self.gather_paginated(
            extractor=lambda: self.extraer_puestos(timeout=timeout),
            navigator=self.navegar_a_pagina,
            page_wait=page_wait,
        )

    def navegar_a_pagina(self, numero: int) -> bool:
        try:
            current = self.driver.current_url or ""
            if "p=" in current:
                target = re.sub(r"p=\d+", f"p={numero}", current)
            else:
                separator = "&" if "?" in current else "?"
                target = f"{current}{separator}p={numero}"
            if self._last_page_url and target == self._last_page_url:
                return False
            self.driver.get(target)
            new_url = getattr(self.driver, "current_url", target)
            # Si la URL no cambia, asumimos que no hay más páginas
            if self._last_page_url and new_url == self._last_page_url:
                return False
            self._last_page_url = new_url
            time.sleep(0.2)
            return True
        except Exception:
            return False

    def _build_base_search_url(self) -> str:
        keyword = self.last_keyword.replace(" ", "-").lower() if self.last_keyword else ""
        url = f"{self.SITE_ROOT}/trabajo-de-{keyword}"
        if self.pubdate:
            url = f"{url}?pubdate={self.pubdate}"
        return url

    def _build_detail_url(self, href: str, base_search: str) -> str:
        tokens = re.findall(r"([A-Za-z0-9]{8,})", href)
        token = None
        for candidate in tokens:
            if re.search(r"\d", candidate):
                token = candidate
                break
        if not token and tokens:
            token = max(tokens, key=len)
        if token:
            return f"{base_search}#{token}"
        if href.startswith("/"):
            return f"{self.SITE_ROOT}{href}"
        return href

    def _extract_company(self, anchor, title_text: str) -> str:
        # In Computrabajo, the company name is usually within the same article card.
        try:
            card = anchor.find_element(By.XPATH, "ancestor::article[1]")
        except Exception:
            card = None

        selectors = [
            "span.fs16.fc_base.mt5.fc_base.fc_base",
            "span.fs13.fc_aux.tx_ellipsis",
            "a.fc_base",
            "span[class*='fc_aux']",
        ]

        search_roots = [anchor]
        if card:
            search_roots.insert(0, card)

        for root in search_roots:
            for sel in selectors:
                elems = root.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    txt = e.text.strip()
                    if not txt:
                        continue
                    # Evita confundir el título con la empresa y textos relativos al tiempo
                    if txt == title_text:
                        continue
                    if txt.lower().startswith("hace "):
                        continue
                    return txt.split("\n")[0]
        return ""