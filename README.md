
# orem_scraper_vacantes

Scraper de vacantes laborales para Bumeran, Computrabajo e Indeed, con arquitectura modular, pruebas unitarias y salida en CSV/JSON.

## Requisitos

- Python 3.10+
- Firefox y geckodriver en PATH (para Selenium)
- Dependencias Python: selenium, pandas

macOS (Homebrew):

```bash
brew install --cask firefox
brew install geckodriver
```

## Instalación

Con pip:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Variables útiles:

- `SCRAPER_HEADLESS=1` ejecuta Firefox en modo headless (sin ventana) si lo deseas.

## Uso

Modo interactivo:

```bash
python3 main.py
```

El asistente pregunta por la búsqueda, filtro de días y plataformas (Bumeran, Computrabajo, Indeed o `all`).

Modo por argumentos (ejemplos):

```bash
python3 main.py "Analista de datos" --dias 1
python3 main.py "Analista" --dias 2 --initial-wait 2 --page-wait 1
python3 main.py "Desarrollador" --source indeed
python3 main.py "Fullstack" --source bumeran --source computrabajo
```

- `--source` puede repetirse para elegir plataformas específicas o usar `--source all` para ejecutar todas (valor por defecto).

Salida: los archivos se guardan en `output/` con nombre `<fuente>_<query>_<YYYY-MM-DD>.(json|csv)`.

## Estructura del proyecto

- `src/core/`: Infraestructura compartida
	- `base.py`: Clase base para scrapers (gestión de paginación, cierre)
	- `browser.py`: Factoría de WebDriver (Firefox) con soporte para `SCRAPER_HEADLESS`
- `src/bumeran.py`: Scraper de Bumeran (hereda de `BaseScraper`)
- `src/computrabajo.py`: Scraper de Computrabajo (hereda de `BaseScraper`)
- `src/indeed.py`: Scraper de Indeed (hereda de `BaseScraper`)
- `src/pipeline.py`: Orquestación para ejecutar los scrapers y combinar resultados
- `src/utils.py`: Guardado de resultados a JSON/CSV
- `main.py`: CLI que delega en `pipeline.run_combined`

## Pruebas

El proyecto incluye pruebas unitarias con `unittest`. Durante las pruebas se stubbea Selenium para no requerir el navegador real.

Ejecuta las pruebas:

```bash
python3 -m unittest discover tests
```

## Notas

- Para entornos CI o servidores sin entorno gráfico, define `SCRAPER_HEADLESS=1`.
- Si necesitas bloquear versiones exactas, genera un lock con tu herramienta preferida (Poetry o pip-tools). Este repo incluye `requirements.txt` para instalaciones simples con pip.
