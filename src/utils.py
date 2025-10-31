"""Result persistence utilities."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List

JobRecord = Dict[str, Any]


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
    _save_json(records, os.path.join(output_dir, f"{base_name}.json"))
    _save_csv(records, os.path.join(output_dir, f"{base_name}.csv"))


def _save_json(records: List[JobRecord], path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    print(f"\nResultados guardados en JSON: {path}")


def _save_csv(records: List[JobRecord], path: str) -> None:
    base_fields = ["fuente", "titulo", "url"]
    if records:
        dynamic_fields = [key for key in records[0].keys() if key not in base_fields]
        fieldnames = base_fields + dynamic_fields
    else:
        fieldnames = base_fields
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Resultados guardados en CSV: {path}")
