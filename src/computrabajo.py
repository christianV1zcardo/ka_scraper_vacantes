"""Computrabajo scraper implementation."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .core.base import BaseScraper

JobData = Dict[str, Any]


class ComputrabajoScraper(BaseScraper):
    BASE_URL = "https://www.computrabajo.com.pe/"
    SITE_ROOT = "https://pe.computrabajo.com"

    def __init__(self, driver=None) -> None:
        super().__init__(driver=driver)
        self.pubdate = 0
        self.last_keyword = ""

    def abrir_pagina_empleos(self, hoy: bool = False, dias: int = 0) -> None:
        if dias == 1:
            self.pubdate = 1
        elif dias == 3:
            self.pubdate = 3
        else:
            self.pubdate = 0
        self.driver.get(self.BASE_URL)

    def buscar_vacante(self, palabra_clave: str = "") -> None:
        keyword = palabra_clave.replace(" ", "-").lower()
        url = f"{self.SITE_ROOT}/trabajo-de-{keyword}"
        if self.pubdate:
            url = f"{url}?pubdate={self.pubdate}"
        try:
            self.driver.get(url)
            self.last_keyword = palabra_clave
        except Exception:
            pass

    def extraer_puestos(self, timeout: int = 10) -> List[JobData]:
        wait = WebDriverWait(self.driver, timeout)
        try:
            container = wait.until(EC.presence_of_element_located((By.ID, "offersGridOfferContainer")))
        except Exception:
            container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
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
            payloads.append({"titulo": text.split("\n")[0], "url": detail_url})
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
            self.driver.get(target)
            time.sleep(1)
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