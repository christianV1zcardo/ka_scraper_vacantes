"""Scraper orchestration utilities."""

from __future__ import annotations

import gc
import logging
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .bumeran import BumeranScraper
from .computrabajo import ComputrabajoScraper
from .indeed import IndeedScraper
from .core.base import BaseScraper
from .utils import guardar_resultados

JobRecord = Dict[str, str]

logger = logging.getLogger(__name__)

DEFAULT_SOURCES: Sequence[str] = ("bumeran", "computrabajo", "indeed")


def _collect_bumeran(
    scraper: BumeranScraper,
    busqueda: str,
    dias: int,
    initial_wait: float,
    page_wait: float,
) -> List[JobRecord]:
    results: List[JobRecord] = []
    seen: Set[str] = set()
    try:
        scraper.abrir_pagina_empleos(hoy=dias == 1, dias=dias if dias in (2, 3) else 0)
        scraper.buscar_vacante(busqueda)
        logger.info("[bumeran] Esperando %.1f s para carga inicial", initial_wait)
        time.sleep(initial_wait)
        puestos = scraper.extraer_todos_los_puestos(timeout=10, page_wait=page_wait)
        logger.info("[bumeran] puestos extraídos: %d", len(puestos))
        for puesto in puestos:
            url = puesto.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            results.append({"fuente": "Bumeran", **puesto})
    except Exception:
        logger.exception("[bumeran] Error durante la recolección")
    return results


def _collect_computrabajo(
    scraper: ComputrabajoScraper,
    busqueda: str,
    dias: int,
    initial_wait: float,
    page_wait: float,
) -> List[JobRecord]:
    results: List[JobRecord] = []
    seen: Set[str] = set()
    try:
        scraper.abrir_pagina_empleos(dias=dias)
        scraper.buscar_vacante(busqueda)
        logger.info("[computrabajo] Esperando %.1f s para carga inicial", initial_wait)
        time.sleep(initial_wait)
        puestos = scraper.extraer_todos_los_puestos(timeout=10, page_wait=page_wait)
        logger.info("[computrabajo] puestos extraídos: %d", len(puestos))
        for puesto in puestos:
            url = puesto.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            results.append({"fuente": "Computrabajo", **puesto})
    except Exception:
        logger.exception("[computrabajo] Error durante la recolección")
    return results


def _collect_indeed(
    scraper: IndeedScraper,
    busqueda: str,
    dias: int,
    initial_wait: float,
    page_wait: float,
) -> List[JobRecord]:
    results: List[JobRecord] = []
    seen: Set[str] = set()
    try:
        scraper.abrir_pagina_empleos(dias=dias)
        scraper.buscar_vacante(busqueda)
        effective_initial_wait = min(initial_wait, 1.0)
        effective_page_wait = max(0.1, page_wait * 0.5)
        logger.info(
            "[indeed] Esperando %.1f s inicial, page_wait=%.2f s", effective_initial_wait, effective_page_wait
        )
        time.sleep(effective_initial_wait)
        puestos = scraper.extraer_todos_los_puestos(timeout=4, page_wait=effective_page_wait)
        logger.info("[indeed] puestos extraídos: %d", len(puestos))
        for puesto in puestos:
            url = puesto.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            results.append({"fuente": "Indeed", **puesto})
    except Exception:
        logger.exception("[indeed] Error durante la recolección")
    return results


def _cleanup_driver(scraper: BaseScraper, label: str | None = None) -> None:
    source_label = label or scraper.__class__.__name__
    logger.debug("Liberando recursos adicionales para '%s'", source_label)
    try:
        if hasattr(scraper, "driver") and scraper.driver:
            scraper.driver.quit()
    except Exception:
        logger.exception("Fallo al cerrar driver para '%s'", source_label)
    gc.collect()
    time.sleep(1)


CollectorFn = Callable[[Any, str, int, float, float], List[JobRecord]]


SCRAPER_REGISTRY: Dict[str, Tuple[Callable[..., BaseScraper], CollectorFn, bool]] = {
    "bumeran": (lambda headless=None: BumeranScraper(headless=headless), _collect_bumeran, True),
    "computrabajo": (lambda headless=None: ComputrabajoScraper(headless=headless), _collect_computrabajo, False),
    "indeed": (lambda headless=None: IndeedScraper(headless=headless), _collect_indeed, False),
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
    headless: Optional[bool] = None,
) -> List[JobRecord]:
    combined, executed = collect_jobs(
        busqueda=busqueda,
        dias=dias,
        initial_wait=initial_wait,
        page_wait=page_wait,
        sources=sources,
        headless=headless,
    )
    if not executed:
        logger.warning("No se ejecutó ningún scraper válido.")
        return []

    label = "combined" if len(executed) > 1 else executed[0]
    logger.info("Guardando %d ofertas para '%s' con etiqueta '%s'", len(combined), busqueda, label)
    guardar_resultados(combined, busqueda, output_dir="output", source=label)
    logger.info("Guardado completado.")
    return combined


def collect_jobs(
    busqueda: str,
    dias: int,
    initial_wait: float,
    page_wait: float,
    sources: Iterable[str] | None = None,
    headless: Optional[bool] = None,
) -> Tuple[List[JobRecord], List[str]]:
    selected_sources = _normalize_sources(sources)
    combined: List[JobRecord] = []
    executed: List[str] = []
    seen_urls: Set[str] = set()

    for source in selected_sources:
        entry = SCRAPER_REGISTRY.get(source)
        if not entry:
            logger.warning("Fuente desconocida '%s', se omite.", source)
            continue

        factory, collector, needs_cleanup = entry
        scraper = factory(headless=headless)
        logger.info("Iniciando scraper '%s'", source)
        start_time = time.perf_counter()
        results: List[JobRecord] = []
        try:
            results = collector(scraper, busqueda, dias, initial_wait, page_wait)
        except Exception:
            logger.exception("Error no controlado ejecutando scraper '%s'", source)
        finally:
            try:
                scraper.close()
            except Exception:
                logger.exception("Error cerrando scraper '%s'", source)
            if needs_cleanup:
                _cleanup_driver(scraper, source)

        elapsed = time.perf_counter() - start_time
        logger.info("Scraper '%s' finalizado en %.2fs con %d ofertas", source, elapsed, len(results))

        if not results:
            logger.info("Scraper '%s' no produjo resultados.", source)
            continue

        executed.append(source)
        for job in results:
            url = job.get("url")
            if not url:
                logger.debug("Registro sin URL descartado de '%s'", source)
                continue
            if url in seen_urls:
                logger.debug("URL duplicada '%s' descartada (fuente '%s')", url, source)
                continue
            seen_urls.add(url)
            combined.append(job)

    logger.info("Total ofertas combinadas tras deduplicación: %d", len(combined))

    return combined, executed
