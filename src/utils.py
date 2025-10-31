"""Result persistence utilities."""

from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List

JobRecord = Dict[str, Any]

logger = logging.getLogger(__name__)


def guardar_resultados(
    puestos: Iterable[JobRecord],
    query: str,
    output_dir: str = "output",
    source: str = "bumeran",
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    base_name = f"{source}_{query.lower()}_{timestamp}"

    records = list(puestos)
    json_path = os.path.join(output_dir, f"{base_name}.json")
    csv_path = os.path.join(output_dir, f"{base_name}.csv")
    _save_json(records, json_path)
    _save_csv(records, csv_path)
    logger.info("Resultados persistidos en %s y %s", json_path, csv_path)


def _save_json(records: List[JobRecord], path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    logger.info("Resultados guardados en JSON: %s", path)


def _save_csv(records: List[JobRecord], path: str) -> None:
    # Ensure fixed base order with the new Empresa column between fuente and titulo
    base_fields = ["fuente", "empresa", "titulo", "url"]
    if records:
        dynamic_fields = [key for key in records[0].keys() if key not in base_fields]
        fieldnames = base_fields + dynamic_fields
    else:
        fieldnames = base_fields
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    logger.info("Resultados guardados en CSV: %s", path)
