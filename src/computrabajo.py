from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Any
import time
import traceback
import re

from utils import guardar_resultados


class ComputrabajoScraper:
    """Scraper inicial para Computrabajo.

    Esta clase es una implementación mínima y defensiva que sigue la misma
    interfaz que `BumeranScraper` para facilitar su integración en `main.py`.

    Métodos públicos:
    - abrir_pagina_empleos(hoy: bool = False, dias: int = 0)
    - buscar_vacante(palabra_clave: str)
    - extraer_puestos(timeout: int = 10) -> List[Dict[str, Any]]
    - guardar_resultados(puestos, query)
    - close()

    Notes:
        - Esta versión inicial intenta ser tolerante a cambios en el DOM y
          extraer títulos y URLs de los anchors dentro del contenedor de
          resultados. Es probable que haya que afinar selectores para mayor
          precisión en producción.
    """

    BASE_URL = "https://www.computrabajo.com.pe/"
    SITE_ROOT = "https://pe.computrabajo.com"

    def __init__(self):
        # Usamos Firefox por consistencia con el resto del proyecto
        self.driver = webdriver.Firefox()
        self.pubdate = 0
        self.last_keyword = ""

    def abrir_pagina_empleos(self, hoy: bool = False, dias: int = 0):
        """Navega a la página principal de Computrabajo.

        Computrabajo no dispone del mismo sistema de rutas que Bumeran, así que
        aquí simplemente abrimos la página principal. El filtrado por días se
        aplicará mediante parámetros o selectores en `buscar_vacante` si es
        necesario en el futuro.
        """
        # Computrabajo no tiene 'hoy' como opción; usamos solo 'dias' mapeado a pubdate:
        # dias == 1 -> pubdate=1 (desde ayer)
        # dias == 3 -> pubdate=3 (últimos 3 días)
        # cualquier otro valor -> sin filtro (pubdate=0)
        if dias == 1:
            self.pubdate = 1
        elif dias == 3:
            self.pubdate = 3
        else:
            self.pubdate = 0

        # Abrimos la homepage inicialmente; la búsqueda construirá la URL con la palabra clave
        self.driver.get(self.BASE_URL)

    def buscar_vacante(self, palabra_clave: str = ''):
        """Busca la vacante en la página principal usando el input de búsqueda.

        Intentamos varios selectores comunes para encontrar el campo de búsqueda
        y enviar la palabra clave + ENTER.
        """
        # Construimos y navegamos directamente a la URL de búsqueda según el patrón
        try:
            kw = palabra_clave.replace(' ', '-').lower()
            url = f"{self.SITE_ROOT}/trabajo-de-{kw}"
            if self.pubdate:
                url = f"{url}?pubdate={self.pubdate}"
            self.driver.get(url)
            self.last_keyword = palabra_clave
            print(f"[debug] buscar_vacante: navegando a {url}")
        except Exception as e:
            print(f"[debug] buscar_vacante fallo navegando a URL: {e}")

    def extraer_puestos(self, timeout: int = 10) -> List[Dict[str, Any]]:
        """Extrae puestos de la página actual.

        Estrategia defensiva:
        - Espera por un contenedor principal (article, main, .results, .box)
        - Recolecta anchors con href dentro del contenedor
        - Filtra enlaces que sean claramente paginación o filtros
        - Devuelve lista de dicts con keys 'titulo' y 'url'
        """
        puestos: List[Dict[str, Any]] = []
        try:
            wait = WebDriverWait(self.driver, timeout)
            # Esperamos por el contenedor específico que mencionaste
            try:
                container = wait.until(EC.presence_of_element_located((By.ID, 'offersGridOfferContainer')))
            except Exception:
                # fallback a main/article
                container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'main')))

            # dentro del contenedor, cada card es un <article> que contiene un anchor con clase 'js-o-link fc_base'
            anchors = container.find_elements(By.CSS_SELECTOR, "article a.js-o-link.fc_base")
            seen = set()
            # Construir base de búsqueda según la keyword y pubdate para construir URLs de detalle como solicitaste
            base_search = None
            try:
                kw = self.last_keyword.replace(' ', '-').lower() if self.last_keyword else ''
                base_search = f"{self.SITE_ROOT}/trabajo-de-{kw}"
                if self.pubdate:
                    base_search = f"{base_search}?pubdate={self.pubdate}"
            except Exception:
                base_search = self.SITE_ROOT

            for a in anchors:
                try:
                    href = a.get_attribute('href') or ''
                    text = (a.text or '').strip()
                    if not href or not text:
                        continue
                    # Extraer token final (ej: 7CA717AA1F08490661373E686DCF3405) que aparece antes del optional '#'
                    tokens = re.findall(r"([A-Za-z0-9]{8,})", href)
                    token = None
                    # Preferimos tokens que contengan al menos un dígito (evita palabras como 'computrabajo')
                    for t in tokens:
                        if re.search(r"\d", t):
                            token = t
                            break
                    if not token and tokens:
                        # fallback al token más largo
                        token = max(tokens, key=len)

                    if token and base_search:
                        # construir URL de detalle según tu regla: base_search + '#' + token
                        url = f"{base_search}#{token}"
                    else:
                        # fallback a url absoluta si es posible
                        if href.startswith('/'):
                            url = f"{self.SITE_ROOT}{href}"
                        else:
                            url = href

                    if url in seen:
                        continue
                    seen.add(url)
                    puestos.append({'titulo': text.split('\n')[0], 'url': url})
                except Exception:
                    continue

        except Exception as e:
            print(f"[debug extraer_puestos computrabajo] excepción: {e}")

        if not puestos:
            print("[debug] computrabajo: no se extrajeron puestos. Revisa selectores o la carga de la página.")
        return puestos

    def extraer_todos_los_puestos(self, timeout: int = 10, page_wait: float = 1.0) -> List[Dict[str, Any]]:
        """Recorre todas las páginas de resultados y devuelve una lista deduplicada de puestos.

        Usa `obtener_ultima_pagina` y `navegar_a_pagina` para iterar. Deduplica por URL.
        """
        todos = []
        seen = set()
        pagina = 1
        max_pages = 50  # safeguard

        while pagina <= max_pages:
            if pagina > 1:
                ok = self.navegar_a_pagina(pagina)
                if not ok:
                    print(f"[debug] navegacion fallo en pagina {pagina}, deteniendo.")
                    break
                time.sleep(page_wait)

            actuales = self.extraer_puestos(timeout=timeout)
            new_found = 0
            for p in actuales:
                url = p.get('url')
                if not url or url in seen:
                    continue
                seen.add(url)
                todos.append(p)
                new_found += 1

            # Si en una página no se encontró nada nuevo, asumimos que no hay más
            if new_found == 0:
                break

            pagina += 1

        return todos

    def obtener_ultima_pagina(self) -> int:
        """Detecta la última página de resultados buscando enlaces de paginación."""
        try:
            elementos = self.driver.find_elements(By.CSS_SELECTOR, "ul.pagination li, nav.pagination a, .paginador a, a[href*='p=']")
            paginas = []
            for el in elementos:
                texto = (el.text or "").strip()
                if texto.isdigit():
                    paginas.append(int(texto))
                href = el.get_attribute('href') or ''
                if 'p=' in href:
                    try:
                        num = int(href.split('p=')[1].split('&')[0])
                        paginas.append(num)
                    except Exception:
                        pass
            if paginas:
                return max(paginas)
            return 1
        except Exception as e:
            print(f"[debug] computrabajo: error detectando última página: {e}")
            return 1

    def navegar_a_pagina(self, numero: int) -> bool:
        """Navega a una página específica, intentando modificar el parámetro p= en la URL."""
        try:
            url_actual = self.driver.current_url or ''
            if 'p=' in url_actual:
                nueva_url = re.sub(r'p=\d+', f'p={numero}', url_actual)
            else:
                if '?' in url_actual:
                    nueva_url = f"{url_actual}&p={numero}"
                else:
                    nueva_url = f"{url_actual}?p={numero}"
            self.driver.get(nueva_url)
            time.sleep(1)
            return True
        except Exception as e:
            print(f"[debug] computrabajo: error navegando a página {numero}: {e}")
            return False

    def guardar_resultados(self, puestos: List[Dict[str, Any]], query: str, output_dir: str = 'output'):
        """Guarda usando la utilidad común, pero con el prefijo 'computrabajo'."""
        guardar_resultados(puestos, query, output_dir=output_dir, source='computrabajo')

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass


if __name__ == '__main__':
    # Pequeño sanity-check si se ejecuta directamente
    s = ComputrabajoScraper()
    try:
        # ejemplo: buscar sin filtro (dias=0), o dias=1/3 según necesidad
        s.abrir_pagina_empleos(dias=1)
        s.buscar_vacante('Analista de datos')
        # Recolectar TODOS los puestos en todas las páginas
        resultados = s.extraer_todos_los_puestos(timeout=10, page_wait=1)
        print(f"Total puestos extraídos: {len(resultados)}")
        for i, r in enumerate(resultados[:50], start=1):
            print(f"[{i}] {r['titulo']} - {r['url']}")
    finally:
        s.close()