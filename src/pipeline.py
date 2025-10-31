"""Scraper orchestration utilities."""

from __future__ import annotations

import gc
import time
from typing import Callable, Dict, Iterable, List, Sequence, Set, Tuple

from .bumeran import BumeranScraper
from .computrabajo import ComputrabajoScraper
from .indeed import IndeedScraper
from .core.base import BaseScraper
from .utils import guardar_resultados

JobRecord = Dict[str, str]

DEFAULT_SOURCES: Sequence[str] = ("bumeran", "computrabajo", "indeed")


def _collect_bumeran(
    scraper: BumeranScraper,
    busqueda: str,
    dias: int,
    initial_wait: float,
    page_wait: float,
    combined: List[JobRecord],
    seen: Set[str],
) -> None:
    try:
        scraper.abrir_pagina_empleos(hoy=dias == 1, dias=dias if dias in (2, 3) else 0)
        scraper.buscar_vacante(busqueda)
        print(f"[bumeran] Esperando {initial_wait} segundos para que cargue la página...")
        time.sleep(initial_wait)
        puestos = scraper.extraer_todos_los_puestos(timeout=10, page_wait=page_wait)
        print(f"[bumeran] puestos extraídos en total: {len(puestos)}")
        for puesto in puestos:
            url = puesto.get("url")
            if url and url not in seen:
                seen.add(url)
                combined.append({"fuente": "Bumeran", **puesto})
    except Exception as exc:
        print(f"[fatal bumeran] {exc}")


def _collect_computrabajo(
    scraper: ComputrabajoScraper,
    busqueda: str,
    dias: int,
    initial_wait: float,
    page_wait: float,
    combined: List[JobRecord],
    seen: Set[str],
) -> None:
    try:
        scraper.abrir_pagina_empleos(dias=dias)
        scraper.buscar_vacante(busqueda)
        print(f"[computrabajo] Esperando {initial_wait} segundos para que cargue la página...")
        time.sleep(initial_wait)
        puestos = scraper.extraer_todos_los_puestos(timeout=10, page_wait=page_wait)
        print(f"[computrabajo] páginas recorridas, puestos encontrados: {len(puestos)}")
        for puesto in puestos:
            url = puesto.get("url")
            if url and url not in seen:
                seen.add(url)
                combined.append({"fuente": "Computrabajo", **puesto})
    except Exception as exc:
        print(f"[fatal computrabajo] {exc}")


def _collect_indeed(
    scraper: IndeedScraper,
    busqueda: str,
    dias: int,
    initial_wait: float,
    page_wait: float,
    combined: List[JobRecord],
    seen: Set[str],
) -> None:
    try:
        scraper.abrir_pagina_empleos(dias=dias)
        scraper.buscar_vacante(busqueda)
        # Indeed tends to render progressively; use smaller effective waits
        effective_initial_wait = min(initial_wait, 1.0)
        effective_page_wait = max(0.1, page_wait * 0.5)
        print(
            f"[indeed] Esperando {effective_initial_wait} s (efectivo) y page_wait={effective_page_wait}s entre páginas..."
        )
        time.sleep(effective_initial_wait)
        puestos = scraper.extraer_todos_los_puestos(timeout=4, page_wait=effective_page_wait)
        print(f"[indeed] páginas recorridas, puestos encontrados: {len(puestos)}")
        for puesto in puestos:
            url = puesto.get("url")
            if url and url not in seen:
                seen.add(url)
                combined.append({"fuente": "Indeed", **puesto})
    except Exception as exc:
        print(f"[fatal indeed] {exc}")


def _cleanup_driver(scraper: BaseScraper) -> None:
    try:
        if hasattr(scraper, "driver") and scraper.driver:
            scraper.driver.quit()
    except Exception:
        pass
    gc.collect()
    time.sleep(1)


SCRAPER_REGISTRY: Dict[str, Tuple[Callable[[], BaseScraper], Callable[..., None], bool]] = {
    "bumeran": (lambda: BumeranScraper(), _collect_bumeran, True),
    "computrabajo": (lambda: ComputrabajoScraper(), _collect_computrabajo, False),
    "indeed": (lambda: IndeedScraper(), _collect_indeed, False),
}


def _normalize_sources(sources: Iterable[str] | None) -> List[str]:
    if not sources:
        return list(DEFAULT_SOURCES)
    expanded: List[str] = []
    for source in sources:
        normalized = source.lower()
        if normalized == "all":
            expanded.extend(DEFAULT_SOURCES)
        else:
            expanded.append(normalized)
    # Preserve order while removing duplicates
    ordered_unique: List[str] = []
    seen = set()
    for item in expanded:
        if item not in seen:
            seen.add(item)
            ordered_unique.append(item)
    return ordered_unique or list(DEFAULT_SOURCES)


def run_combined(
    busqueda: str,
    dias: int,
    initial_wait: float,
    page_wait: float,
    sources: Iterable[str] | None = None,
) -> None:
    selected_sources = _normalize_sources(sources)
    combined: List[JobRecord] = []
    seen: Set[str] = set()
    executed: List[str] = []

    for source in selected_sources:
        entry = SCRAPER_REGISTRY.get(source)
        if not entry:
            print(f"[warn] Fuente desconocida '{source}', se omite.")
            continue
        factory, collector, needs_cleanup = entry
        scraper = factory()
        try:
            collector(scraper, busqueda, dias, initial_wait, page_wait, combined, seen)
            executed.append(source)
        finally:
            scraper.close()
            if needs_cleanup:
                _cleanup_driver(scraper)

    if not executed:
        print("No se ejecutó ningún scraper válido.")
        return

    label = "combined" if len(executed) > 1 else executed[0]
    print(f"Guardando {len(combined)} ofertas combinadas para '{busqueda}'...")
    guardar_resultados(combined, busqueda, output_dir="output", source=label)
    print("Guardado completado.")
