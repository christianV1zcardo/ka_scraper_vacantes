"""
utils.py - Funciones utilitarias para el scraper Bumeran

Incluye funciones de guardado de resultados en JSON y CSV.
"""
from typing import List, Dict, Any
import os
import json
import csv
from datetime import datetime

def guardar_resultados(puestos: List[Dict[str, Any]], query: str, output_dir: str = "output", source: str = "bumeran") -> None:
    """
    Guarda los resultados en formato JSON y CSV en la carpeta output/.
    Args:
        puestos: Lista de diccionarios con los puestos encontrados
        query: Palabra clave usada en la búsqueda (se usa para el nombre del archivo)
        output_dir: Carpeta donde guardar los archivos
    Returns:
        None
    """
    """
    Guarda los resultados en formato JSON y CSV en la carpeta output/.
    Args:
        puestos: Lista de diccionarios con los puestos encontrados
        query: Palabra clave usada en la búsqueda (se usa para el nombre del archivo)
        output_dir: Carpeta donde guardar los archivos
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    base_nombre = f"{source}_{query.lower()}_{timestamp}"

    # Guardar JSON
    json_path = os.path.join(output_dir, f"{base_nombre}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(puestos, f, ensure_ascii=False, indent=2)
    print(f"\nResultados guardados en JSON: {json_path}")

    # Guardar CSV
    csv_path = os.path.join(output_dir, f"{base_nombre}.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        if puestos:
            fieldnames = list(puestos[0].keys())
        else:
            fieldnames = ["titulo", "url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(puestos)
    print(f"Resultados guardados en CSV: {csv_path}")
