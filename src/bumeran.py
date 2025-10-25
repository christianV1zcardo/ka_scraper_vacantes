from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Any

import time
import traceback
from utils import guardar_resultados


class BumeranScraper:
    """
    Scraper de ofertas laborales para Bumeran Perú.
    Utiliza Selenium para automatizar la navegación y extracción de datos.
    """
    def __init__(self) -> None:
        """
        Inicializa el webdriver de Selenium (Firefox por defecto).
        """
        self.driver = webdriver.Firefox()

    def abrir_pagina_empleos(self, hoy: bool = False, dias: int = 0) -> None:
        """
        Abre la página de empleos de Bumeran según los filtros de fecha.
        Args:
            hoy: Si True, filtra solo empleos publicados hoy.
            dias: Si 2 o 3, filtra por empleos publicados en los últimos días.
        """
        
        # Mejorable y añadible mas condiciones
        if hoy:
            self.driver.get("https://www.bumeran.com.pe/empleos-publicacion-hoy.html")
        elif not hoy:
            if dias == 2:
                self.driver.get("https://www.bumeran.com.pe/empleos-publicacion-menor-a-2-dias.html")
            elif dias == 3:
                self.driver.get("https://www.bumeran.com.pe/empleos-publicacion-menor-a-3-dias.html")
            else:
                self.driver.get("https://www.bumeran.com.pe/empleos-busqueda.html")

    # Errores aqui
    def buscar_vacante(self, palabra_clave: str = '') -> None:
        """
        Busca una vacante usando la palabra clave en el buscador de la web.
        Args:
            palabra_clave: Término a buscar en el input principal.
        """
        # El id del box de texto
        placeholder_name = "react-select-4-input"
        elem = self.driver.find_element(By.ID, placeholder_name)
        elem.send_keys(palabra_clave)
        elem.send_keys(Keys.RETURN)
        print(f"[debug] buscar_vacante: enviado '{palabra_clave}' al input y enviado RETURN")


    def extraer_puestos(self, timeout: int = 10) -> List[Dict[str, Any]]:
        """
        Wrapper que intenta extraer puestos usando varias estrategias.
        Actualmente delega en `extraer_por_enlaces`.
        Args:
            timeout: Tiempo máximo de espera para cargar los elementos.
        Returns:
            Lista de diccionarios con información de los puestos.
        """
        """Wrapper que intenta extraer puestos usando varias estrategias.

        Actualmente delega en `extraer_por_enlaces`, que es robusta cuando cada oferta
        está representada por un enlace con href.
        """
        try:
            return self.extraer_por_enlaces(timeout=timeout)
        except Exception as e:
            print(f"[error][extraer_puestos] Fallo usando extraer_por_enlaces: {e}")
            return []

    def extraer_por_enlaces(self, timeout: int = 10, max_details: int = 20) -> List[Dict[str, Any]]:
        """
        Extrae ofertas buscando anchors dentro del contenedor de resultados.
        Args:
            timeout: Tiempo máximo de espera para cargar los elementos.
            max_details: Máximo de detalles a extraer (no usado actualmente).
        Returns:
            Lista de diccionarios con información de los puestos.
        """
        """Extrae ofertas buscando anchors dentro del contenedor de resultados.

        Estrategia:
        - Espera el contenedor principal (ID `listado-avisos`).
        - Busca todos los anchors (`a`) dentro del contenedor.
        - Filtra anchors con href que parezcan apuntar a avisos/ofertas.
        - Extrae título (h1-h5 dentro del anchor), empresa y ubicación de forma defensiva.
        """
        puestos: List[Dict[str, Any]] = []
        wait = WebDriverWait(self.driver, timeout)
        container = wait.until(EC.presence_of_element_located((By.ID, "listado-avisos")))

        # busca anchors dentro del contenedor
        anchors = container.find_elements(By.TAG_NAME, "a")

        # Debug: si no hay anchors, imprimimos información útil
        if not anchors:
            print("[debug][extraer_por_enlaces] No se encontraron anchors dentro del contenedor 'listado-avisos'.")
            hijos = container.find_elements(By.XPATH, "./*")
            print(f"[debug][extraer_por_enlaces] Hijos directos del contenedor: {len(hijos)}")
            for i, h in enumerate(hijos[:10], start=1):
                tag = h.tag_name
                classes = h.get_attribute("class")
                html = (h.get_attribute("outerHTML") or "")[:300]
                print(f"[debug][extraer_por_enlaces] Hijo {i}: tag={tag} classes={classes} html-snippet={html!r}")

        seen_hrefs = set()
        details_requested = 0
        for a in anchors:
            try:
                href = a.get_attribute("href")
                if not href:
                    continue
                # filtro heurístico inicial: url que contenga '/empleos/' y no sea una página de búsqueda
                if '/empleos/' not in href:
                    continue
                # excluir urls de tipo 'busqueda' o listados (ej: ...-busqueda-...)
                if 'busqueda-' in href or 'publicacion-menor' in href or 'relevantes=' in href or 'recientes=' in href:
                    continue
                if href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                # título: busca etiquetas h1..h5 dentro del anchor
                title = ""
                for tag in ("h1", "h2", "h3", "h4", "h5"):
                    elems = a.find_elements(By.TAG_NAME, tag)
                    if elems and elems[0].text.strip():
                        title = elems[0].text.strip()
                        break
                if not title:
                    # fallback: primera línea del texto del anchor
                    title = (a.text or "").split("\n")[0].strip()

                if title:  # solo añadimos si tiene título
                    puestos.append({
                        "titulo": title,
                        "url": href,
                    })

            except Exception as e:
                print(f"[error][extraer_por_enlaces] Error procesando anchor: {e}")
                continue
                
        # Debug resumen si no encontramos puestos
        if not puestos:
            print(f"[debug][extraer_por_enlaces] No se extrajeron puestos. Anchors totales en contenedor: {len(anchors)}")
            for i, a in enumerate(anchors[:20], start=1):
                try:
                    print(f"[debug][anchor {i}] href={a.get_attribute('href')!r} class={a.get_attribute('class')!r} text_snippet={((a.text or '')[:60]).replace('\n',' ')}")
                except Exception:
                    pass

        return puestos


    def close(self) -> None:
        """
        Cierra el navegador y libera recursos del webdriver.
        """
        self.driver.quit()


    def inspeccionar_estructura(self) -> None:
        """
        Muestra la estructura HTML de la primera card de resultados (debug).
        """
        """Método temporal para debug: muestra la estructura HTML de la primera card"""
        try:
            # Espera por el contenedor principal
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "listado-avisos"))
            )
            
            # Encuentra la primera card
            cards = container.find_elements(By.CSS_SELECTOR, "div[data-id]")  # Busca cards por atributo data-id
            if cards:
                primera_card = cards[0]
                print("\nEstructura de la primera card:")
                print("HTML:", primera_card.get_attribute('outerHTML'))
                print("\nClases disponibles:", primera_card.get_attribute('class'))
                
                # Intentar varios selectores comunes
                for selector in ['h2', 'h3', 'a', '[data-id]', '[title]']:
                    elementos = primera_card.find_elements(By.CSS_SELECTOR, selector)
                    if elementos:
                        print(f"\nElementos encontrados con {selector}:")
                        for elem in elementos:
                            print(f"- {elem.tag_name}: '{elem.text}' (class='{elem.get_attribute('class')}')")
        except Exception as e:
            print(f"[error][inspeccionar_estructura] {e}")

    def debug_containers(self) -> None:
        """
        Intenta localizar diferentes selectores de contenedor y lista lo que encuentre (debug).
        """
        """Intenta localizar diferentes selectores de contenedor y lista lo que encuentre.

        Útil cuando no estamos seguros de cuál es el contenedor que envuelve las ofertas.
        """
        selectors = [
            (By.ID, "listado-avisos"),
            (By.CSS_SELECTOR, "#listado-avisos"),
            (By.CSS_SELECTOR, "div[id*='listado']"),
            (By.CSS_SELECTOR, "div[class*='listado']"),
            (By.CSS_SELECTOR, "section[data-qa*='list']"),
            (By.CSS_SELECTOR, "ul[data-qa*='list']"),
        ]
        found = []
        for by, sel in selectors:
            try:
                elems = self.driver.find_elements(by, sel)
                if elems:
                    found.append((sel, len(elems), elems[0].tag_name, elems[0].get_attribute('class')))
            except Exception:
                pass

        if not found:
            print("[debug][debug_containers] No se encontraron selectores comunes de contenedor.")
        else:
            print("[debug][debug_containers] Posibles contenedores encontrados:")
            for sel, count, tag, classes in found:
                print(f"  - selector={sel!r} count={count} first_tag={tag} classes={classes}")

    def parse_job_detail(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Abre la página de detalle de una oferta y extrae campos relevantes.
        Args:
            url: URL de la oferta.
            timeout: Tiempo máximo de espera para cargar los elementos.
        Returns:
            Diccionario con empresa, ubicación, fecha y descripción.
        """
        """Abre la página de detalle en una pestaña nueva, extrae campos y regresa.

        Retorna un dict con keys posibles: empresa, ubicacion, fecha, descripcion.
        """
        result: Dict[str, Any] = {"empresa": "", "ubicacion": "", "fecha": "", "descripcion": ""}
        original_handle = None
        try:
            original_handle = self.driver.current_window_handle
        except Exception:
            original_handle = None

        try:
            # abrir nueva pestaña con la URL
            self.driver.execute_script("window.open(arguments[0]);", url)
            handles = self.driver.window_handles
            # cambiar a la nueva pestaña
            self.driver.switch_to.window(handles[-1])
            wait = WebDriverWait(self.driver, timeout)
            # esperar por un contenedor representativo en la página de detalle
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article, main, .job-detail, .detalle-aviso")))
            except Exception:
                # siga intentándolo un poco más; algunos detalles cargan despacio
                time.sleep(1)

            # intentos para empresa
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, ".employer, .company, .empresa, [data-employer]")
                result['empresa'] = el.text.strip()
            except Exception:
                # fallback: buscar por etiqueta que contenga 'Empresa' en el texto
                try:
                    el = self.driver.find_element(By.XPATH, "//*[contains(translate(text(), 'EMPRESA', 'empresa'), 'empresa')][1]")
                    result['empresa'] = el.text.strip()
                except Exception:
                    pass

            # ubicación
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, ".location, .ubicacion, .city, [data-location]")
                result['ubicacion'] = el.text.strip()
            except Exception:
                pass

            # fecha publicada
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, ".posted-date, .fecha, .date, [data-posted]")
                result['fecha'] = el.text.strip()
            except Exception:
                pass

            # descripcion
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, ".description, .job-description, .detalle-aviso, .aviso-descripcion")
                result['descripcion'] = el.text.strip()
            except Exception:
                try:
                    el = self.driver.find_element(By.TAG_NAME, "main")
                    result['descripcion'] = el.text.strip()
                except Exception:
                    pass

        except Exception as e:
            print(f"[error][parse_job_detail] Excepción navegando {url}: {e}")
        finally:
            # cerrar la pestaña actual si está abierta y volver a la original
            try:
                handles = self.driver.window_handles
                # si hay más de una pestaña, cerramos la actual (última) y volvemos a la primera
                if len(handles) > 1:
                    try:
                        self.driver.close()
                    except Exception:
                        pass
                    # cambiar a la primera si existe
                    handles2 = self.driver.window_handles
                    if original_handle and original_handle in handles2:
                        self.driver.switch_to.window(original_handle)
                    elif handles2:
                        self.driver.switch_to.window(handles2[0])
            except Exception:
                pass

        return result

    def obtener_ultima_pagina(self) -> int:
        """
        Detecta el número de la última página disponible de resultados.
        Returns:
            Número de la última página (int).
        """
        """Detecta el número de la última página disponible.
        
        Estrategia:
        1. Busca elementos de paginación
        2. Extrae números de página
        3. Retorna el máximo encontrado
        """
        try:
            # Intenta varios selectores comunes para paginación
            for selector in [
                "ul.pagination li", 
                "[aria-label*='página'] button",
                "[data-page]",
                "a[href*='page=']"
            ]:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    # Extrae números de página de texto o atributos
                    paginas = []
                    for el in elementos:
                        # Intenta obtener número del texto
                        texto = el.text.strip()
                        if texto.isdigit():
                            paginas.append(int(texto))
                        # Intenta obtener número del href si es un link
                        href = el.get_attribute("href") or ""
                        if "page=" in href:
                            try:
                                num = int(href.split("page=")[1].split("&")[0])
                                paginas.append(num)
                            except ValueError:
                                continue
                    if paginas:
                        return max(paginas)
            
            # Si no encontró paginación, asume que solo hay una página
            return 1
        except Exception as e:
            print(f"[error][obtener_ultima_pagina] Error detectando última página: {e}")
            return 1

    def navegar_a_pagina(self, numero: int) -> bool:
        """
        Navega a una página específica de resultados.
        Args:
            numero: Número de página a navegar.
        Returns:
            True si la navegación fue exitosa, False en caso contrario.
        """
        """Navega a una página específica de resultados."""
        try:
            # Construye URL con número de página
            url_actual = self.driver.current_url
            if "page=" in url_actual:
                nueva_url = url_actual.split("page=")[0] + f"page={numero}"
            else:
                if "?" in url_actual:
                    nueva_url = f"{url_actual}&page={numero}"
                else:
                    nueva_url = f"{url_actual}?page={numero}"

            self.driver.get(nueva_url)
            time.sleep(1)  # pequeña pausa para carga
            return True
        except Exception as e:
            print(f"[error][navegar_a_pagina] Error navegando a página {numero}: {e}")
            return False


    def guardar_resultados(self, puestos: List[Dict[str, Any]], query: str):
        """
        Guarda los resultados en formato JSON y CSV usando la función utilitaria.
        Args:
            puestos: Lista de diccionarios con los puestos encontrados
            query: Palabra clave usada en la búsqueda (se usa para el nombre del archivo)
        """
        guardar_resultados(puestos, query)


if __name__ == "__main__":
    scraper = BumeranScraper()
    query = 'Analista'  # término de búsqueda
    try:
        # Búsqueda inicial
        scraper.abrir_pagina_empleos(dias=2)
        scraper.buscar_vacante(query)
        time.sleep(2)  # espera inicial

        # Detecta última página
        ultima_pagina = scraper.obtener_ultima_pagina()
        print(f"\nDetectadas {ultima_pagina} páginas de resultados")
        
        # Recorre todas las páginas
        todos_los_puestos = []
        for pagina in range(1, ultima_pagina + 1):
            if pagina > 1:
                if not scraper.navegar_a_pagina(pagina):
                    print(f"Error navegando a página {pagina}, saltando...")
                    continue
                time.sleep(1)  # pausa entre páginas
            
            # Extrae puestos de la página actual
            puestos = scraper.extraer_puestos()
            todos_los_puestos.extend(puestos)
            print(f"\nPágina {pagina}/{ultima_pagina}: {len(puestos)} puestos")
            
            # Muestra los resultados de esta página
            for i, p in enumerate(puestos, start=1):
                print(f"[{i}] {p['titulo']} - {p['url']}")

        # Guarda todos los resultados en archivos
        scraper.guardar_resultados(todos_los_puestos, query)

    except Exception as main_e:
        print(f"[fatal] excepción en main: {main_e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            scraper.close()
            print("[debug] driver cerrado correctamente")
        except Exception as e:
            print(f"[debug] fallo cerrando driver: {e}")