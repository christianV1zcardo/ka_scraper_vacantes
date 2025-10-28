"""Scraper orchestration utilities."""

from __future__ import annotations

import gc
import time
from typing import Dict, List, Set

from .bumeran import BumeranScraper
from .computrabajo import ComputrabajoScraper
from .utils import guardar_resultados

JobRecord = Dict[str, str]


def run_combined(busqueda: str, dias: int, initial_wait: float, page_wait: float) -> None:
    combined: List[JobRecord] = []
    seen: Set[str] = set()

    bumeran = BumeranScraper()
    try:
        _collect_bumeran(bumeran, busqueda, dias, initial_wait, page_wait, combined, seen)
    finally:
        bumeran.close()
        _cleanup_driver(bumeran)

    computrabajo = ComputrabajoScraper()
    try:
        _collect_computrabajo(computrabajo, busqueda, dias, initial_wait, page_wait, combined, seen)
    finally:
        computrabajo.close()

    print(f"Guardando {len(combined)} ofertas combinadas para '{busqueda}'...")
    guardar_resultados(combined, busqueda, output_dir="output", source="combined")
    print("Guardado completado.")


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
                combined.append(puesto)
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
                combined.append(puesto)
    except Exception as exc:
        print(f"[fatal computrabajo] {exc}")


def _cleanup_driver(scraper: BumeranScraper) -> None:
    try:
        if hasattr(scraper, "driver") and scraper.driver:
            scraper.driver.quit()
    except Exception:
        pass
    gc.collect()
    time.sleep(1)
