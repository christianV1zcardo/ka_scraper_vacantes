import sys
import os
import time
import argparse

# Asegurarnos de que 'src' esté en el path para poder importar bumeran.py
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "src")
if SRC_DIR not in sys.path:
	sys.path.insert(0, SRC_DIR)

from src.bumeran import BumeranScraper


def prompt_interactive():
	"""Pide al usuario los inputs que necesita el scraper: término de búsqueda y tiempos."""
	busqueda = input("Nombre del puesto a buscar (ej. Analista): ").strip()
	if not busqueda:
		print("No se ingresó un término de búsqueda. Abortando.")
		return None

	# Pedimos únicamente un número para indicar el filtro de días:
	# 1 = publicaciones de hoy
	# 2 = publicaciones menores a 2 días
	# 3 = publicaciones menores a 3 días
	# 0 = todos (por defecto)
	while True:
		d = input("Filtrar por días (1=Hoy,2=últimos 2 días,3=últimos 3 días,0=Todos) [0]: ").strip()
		if not d:
			d = "0"
		if d in ("0", "1", "2", "3"):
			d_val = int(d)
			break
		print("Opción inválida. Ingresa 0, 1, 2 o 3.")

	# Mapear el valor a los parámetros de abrir_pagina_empleos
	if d_val == 1:
		hoy = True
		dias = 0
	else:
		hoy = False
		dias = d_val if d_val in (2, 3) else 0

	# No preguntamos por tiempos en modo interactivo; usamos valores por defecto
	initial_wait = 2
	page_wait = 1

	return {
		"busqueda": busqueda,
		"initial_wait": initial_wait,
		"page_wait": page_wait,
		"dias": dias,
		"hoy": hoy,
	}


def main():
	parser = argparse.ArgumentParser(description='Lanzador amigable del scraper Bumeran (usa src/bumeran.py)')
	parser.add_argument('busqueda', nargs='?', help='Palabra clave para buscar (ej: "Analista"). Si se omite, entra en modo interactivo.')
	parser.add_argument('--dias', type=int, choices=[0, 2, 3], default=0,
					help='Filtrar por días de publicación (0=todos, 2=últimos 2 días, 3=últimos 3 días)')
	parser.add_argument('--hoy', action='store_true', help='Buscar solo publicaciones de hoy')
	parser.add_argument('--initial-wait', type=float, default=None, help='Espera inicial en segundos antes de extraer')
	parser.add_argument('--page-wait', type=float, default=None, help='Espera entre páginas en segundos')
	parser.add_argument('--interactive', action='store_true', help='Forzar modo interactivo con prompts')
	args = parser.parse_args()

	# Si el usuario pidió interactivo o no pasó busqueda, pedimos por inputs
	if args.interactive or not args.busqueda:
		vals = prompt_interactive()
		if vals is None:
			return
		busqueda = vals['busqueda']
		initial_wait = vals['initial_wait']
		page_wait = vals['page_wait']
		dias = vals['dias']
		hoy = vals['hoy']
	else:
		busqueda = args.busqueda
		initial_wait = args.initial_wait if args.initial_wait is not None else 2
		page_wait = args.page_wait if args.page_wait is not None else 1
		dias = args.dias
		hoy = args.hoy

	scraper = BumeranScraper()
	try:
		scraper.abrir_pagina_empleos(hoy=hoy, dias=dias)
		scraper.buscar_vacante(busqueda)
		print(f"Esperando {initial_wait} segundos para que cargue la página...")
		time.sleep(initial_wait)

		# Fallback: algunas búsquedas desde la página "publicacion-hoy" cargan
		# enlaces de filtro (relevantes/recientes) en lugar de las ofertas.
		# Si detectamos que no hay ofertas visibles y la URL contiene
		# 'publicacion-hoy', intentamos una URL alternativa que fuerza la
		# página de búsqueda normal (quitar el prefijo 'empleos-publicacion-hoy-...').
		try:
			current = scraper.driver.current_url or ""
			if 'publicacion-hoy' in current:
				# construimos una URL alternativa sin el segmento 'publicacion-hoy'
				base = current.split('?')[0]
				if 'empleos-publicacion-hoy-busqueda-' in base:
					alt = base.replace('empleos-publicacion-hoy-busqueda-', 'empleos-busqueda-')
					print(f"[debug] página 'hoy' detectada; intentando URL alternativa: {alt}")
					scraper.driver.get(alt)
					time.sleep(1)
		except Exception:
			# no fatal; seguimos con el flujo normal
			pass

		ultima_pagina = scraper.obtener_ultima_pagina()
		print(f"\nDetectadas {ultima_pagina} páginas de resultados")

		todos_los_puestos = []
		for pagina in range(1, ultima_pagina + 1):
			if pagina > 1:
				if not scraper.navegar_a_pagina(pagina):
					print(f"Error navegando a página {pagina}, saltando...")
					continue
				print(f"Esperando {page_wait} segundos antes de extraer la página {pagina}...")
				time.sleep(page_wait)

			puestos = scraper.extraer_puestos()
			todos_los_puestos.extend(puestos)
			print(f"\nPágina {pagina}/{ultima_pagina}: {len(puestos)} puestos")
			for i, p in enumerate(puestos, start=1):
				print(f"[{i}] {p['titulo']} - {p['url']}")

		scraper.guardar_resultados(todos_los_puestos, busqueda)

	except Exception as e:
		print(f"[fatal] excepción en main: {e}")
		import traceback
		traceback.print_exc()
	finally:
		try:
			scraper.close()
			print("[debug] driver cerrado correctamente")
		except Exception as e:
			print(f"[debug] fallo cerrando driver: {e}")


if __name__ == '__main__':
	main()


