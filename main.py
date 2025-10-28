import argparse
import os
import sys
from dataclasses import dataclass
from typing import Optional

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.pipeline import run_combined


@dataclass
class RunParameters:
    busqueda: str
    dias: int
    initial_wait: float
    page_wait: float


def prompt_interactive() -> Optional[RunParameters]:
    busqueda = input("Nombre del puesto a buscar (ej. Analista): ").strip()
    if not busqueda:
        print("No se ingresó un término de búsqueda. Abortando.")
        return None
    while True:
        dias = input("Filtrar por días (0=Todos,1=Desde ayer,2=últimos 2 días,3=últimos 3 días) [0]: ").strip()
        dias = dias or "0"
        if dias in {"0", "1", "2", "3"}:
            return RunParameters(busqueda=busqueda, dias=int(dias), initial_wait=2.0, page_wait=1.0)
        print("Opción inválida. Ingresa 0, 1, 2 o 3.")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecuta los scrapers de Bumeran y Computrabajo y guarda resultados combinados"
    )
    parser.add_argument(
        "busqueda",
        nargs="?",
        help='Palabra clave para buscar (ej: "Analista"). Si se omite, se activa el modo interactivo.',
    )
    parser.add_argument(
        "--dias",
        type=int,
        choices=[0, 1, 2, 3],
        default=0,
        help="Filtrar por días de publicación",
    )
    parser.add_argument("--hoy", action="store_true", help="Equivale a --dias 1")
    parser.add_argument("--initial-wait", type=float, help="Espera inicial antes de extraer")
    parser.add_argument("--page-wait", type=float, help="Espera entre páginas")
    parser.add_argument("--interactive", action="store_true", help="Forzar modo interactivo")
    return parser.parse_args()


def resolve_parameters(args: argparse.Namespace) -> Optional[RunParameters]:
    if args.interactive or not args.busqueda:
        return prompt_interactive()
    return RunParameters(
        busqueda=args.busqueda,
        dias=1 if args.hoy else args.dias,
        initial_wait=args.initial_wait if args.initial_wait is not None else 2.0,
        page_wait=args.page_wait if args.page_wait is not None else 1.0,
    )


def main() -> None:
    args = parse_arguments()
    params = resolve_parameters(args)
    if not params:
        return
    run_combined(
        busqueda=params.busqueda,
        dias=params.dias,
        initial_wait=params.initial_wait,
        page_wait=params.page_wait,
    )


if __name__ == "__main__":
    main()
