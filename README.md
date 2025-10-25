
# orem_scraper_vacantes

Scraper de vacantes laborales de Bumeran Perú usando Selenium.

## Requisitos

- Python 3.10+
- Selenium
- Firefox (y geckodriver en PATH)

Instala dependencias:

```bash
pip install -r requirements.txt
# o usa poetry si tienes pyproject.toml
```

## Uso rápido

Modo interactivo:

```bash
python main.py
```

Modo por argumentos:

```bash
python main.py "Analista" --dias 2
```

Archivos de resultados se guardan en la carpeta `output/` en formato CSV y JSON.

## Estructura

- `src/bumeran.py`: Lógica principal del scraper.
- `src/utils.py`: Utilidades para guardado de resultados.
- `main.py`: CLI para lanzar el scraper.

## Ejemplo de salida

```
Página 1/2: 20 puestos
[1] Analista de Datos - https://www.bumeran.com.pe/empleos/analista-datos-123.html
...
Resultados guardados en JSON: output/bumeran_analista_2025-10-25.json
Resultados guardados en CSV: output/bumeran_analista_2025-10-25.csv
```
