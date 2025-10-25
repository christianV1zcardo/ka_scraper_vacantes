
import sys
import os
import time
import argparse

# --- PATH SETUP ---
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.bumeran import BumeranScraper
from src.computrabajo import ComputrabajoScraper
from src.utils import guardar_resultados

def prompt_interactive() -> dict | None:
    """Solicita al usuario los parámetros de búsqueda de forma interactiva."""
    busqueda = input("Nombre del puesto a buscar (ej. Analista): ").strip()
    if not busqueda:
        print("No se ingresó un término de búsqueda. Abortando.")
        return None

    while True:
        d = input("Filtrar por días (0=Todos,1=Desde ayer,2=últimos 2 días,3=últimos 3 días) [0]: ").strip()
        if not d:
            d = "0"
        if d in ("0", "1", "2", "3"):
            d_val = int(d)
            break
        print("Opción inválida. Ingresa 0, 1, 2 o 3.")
    # Devolvemos el valor numérico tal cual: 0,1,2 o 3
    return {
        "busqueda": busqueda,
        "initial_wait": 2,
        "page_wait": 1,
        "dias": d_val,
    }

def run_combined(busqueda: str, dias: int, initial_wait: float, page_wait: float):
    """Ejecuta ambos scrapers (Bumeran y Computrabajo), combina y guarda resultados."""
    combined: list[dict] = []
    seen = set()

    # ----- Bumeran -----
    b = BumeranScraper()
    try:
        # Para Bumeran, interpretamos dias==1 como 'hoy'
        b_hoy = True if dias == 1 else False
        b_dias = dias if dias in (2, 3) else 0
        b.abrir_pagina_empleos(hoy=b_hoy, dias=b_dias)
        b.buscar_vacante(busqueda)
        print(f"[bumeran] Esperando {initial_wait} segundos para que cargue la página...")
        time.sleep(initial_wait)


        # Recolectar todas las páginas de forma robusta (iterativa hasta no hallar nuevos)
        try:
            puestos_todos = b.extraer_todos_los_puestos(timeout=10, page_wait=page_wait)
            print(f"[bumeran] puestos extraídos en total: {len(puestos_todos)}")
            for p in puestos_todos:
                url = p.get('url')
                if url and url not in seen:
                    seen.add(url)
                    combined.append(p)
        except Exception as e:
            print(f"[fatal bumeran] fallo recolectando todas las páginas: {e}")

    except Exception as e:
        print(f"[fatal bumeran] {e}")
    finally:
        try:
            b.close()
        except Exception:
            pass

    # Ensure the Bumeran driver is fully closed and the object removed before
    # instantiating the next scraper. In some environments the browser can
    # continue executing JS or retain focus which leads to unexpected actions
    # after the loop; explicitly quit, delete and pause to make the transition
    # deterministic.
    try:
        print("[debug] cerrando session de Bumeran y liberando recursos...")
        try:
            # defensive double-close in case close() didn't fully quit
            if hasattr(b, 'driver') and b.driver:
                try:
                    b.driver.quit()
                except Exception:
                    pass
        except Exception:
            pass
        del b
    except Exception:
        pass
    import gc
    gc.collect()
    time.sleep(1)

    # ----- Computrabajo -----
    c = ComputrabajoScraper()
    try:
        c.abrir_pagina_empleos(dias=dias)
        c.buscar_vacante(busqueda)
        print(f"[computrabajo] Esperando {initial_wait} segundos para que cargue la página...")
        time.sleep(initial_wait)

        resultados = c.extraer_todos_los_puestos(timeout=10, page_wait=page_wait)
        print(f"[computrabajo] páginas recorridas, puestos encontrados: {len(resultados)}")
        for p in resultados:
            url = p.get('url')
            if url and url not in seen:
                seen.add(url)
                combined.append(p)

    except Exception as e:
        print(f"[fatal computrabajo] {e}")
    finally:
        try:
            c.close()
        except Exception:
            pass

    # Guardar combinados
    print(f"Guardando {len(combined)} ofertas combinadas para '{busqueda}'...")
    guardar_resultados(combined, busqueda, output_dir='output', source='combined')
    print("Guardado completado.")

def main():
    parser = argparse.ArgumentParser(description='Lanzador que ejecuta los scrapers Bumeran y Computrabajo y guarda resultados combinados')
    parser.add_argument('busqueda', nargs='?', help='Palabra clave para buscar (ej: "Analista"). Si se omite, entra en modo interactivo.')
    parser.add_argument('--dias', type=int, choices=[0, 1, 2, 3], default=0,
                        help='Filtrar por días de publicación (0=todos, 1=desde ayer/pubdate=1, 2=últimos 2 días, 3=últimos 3 días)')
    parser.add_argument('--hoy', action='store_true', help='Compatibilidad: equivale a --dias 1')
    parser.add_argument('--initial-wait', type=float, default=None, help='Espera inicial en segundos antes de extraer')
    parser.add_argument('--page-wait', type=float, default=None, help='Espera entre páginas en segundos')
    parser.add_argument('--interactive', action='store_true', help='Forzar modo interactivo con prompts')
    args = parser.parse_args()

    if args.interactive or not args.busqueda:
        vals = prompt_interactive()
        if vals is None:
            return
        busqueda = vals['busqueda']
        initial_wait = vals['initial_wait']
        page_wait = vals['page_wait']
        dias = vals['dias']
    else:
        busqueda = args.busqueda
        initial_wait = args.initial_wait if args.initial_wait is not None else 2
        page_wait = args.page_wait if args.page_wait is not None else 1
        # --hoy compatibility: treat as dias=1
        dias = 1 if args.hoy else args.dias

    # Ejecutar ambos scrapers y guardar resultados combinados
    run_combined(busqueda, dias, initial_wait, page_wait)


if __name__ == '__main__':
    main()
