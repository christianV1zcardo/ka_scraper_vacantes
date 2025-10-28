import sys
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.selenium_stub import ensure_selenium_stub

ensure_selenium_stub()

from src import pipeline


class PipelineTests(unittest.TestCase):
    def test_run_combined_merges_and_deduplicates(self) -> None:
        bumeran_instance = Mock()
        bumeran_instance.driver = None
        bumeran_instance.extraer_todos_los_puestos.return_value = [
            {"url": "https://jobs.com/a", "titulo": "Role A"},
            {"url": "https://jobs.com/b", "titulo": "Role B"},
        ]

        computrabajo_instance = Mock()
        computrabajo_instance.driver = None
        computrabajo_instance.extraer_todos_los_puestos.return_value = [
            {"url": "https://jobs.com/b", "titulo": "Role B"},
            {"url": "https://jobs.com/c", "titulo": "Role C"},
        ]

        with patch("src.pipeline.BumeranScraper", return_value=bumeran_instance), patch(
            "src.pipeline.ComputrabajoScraper", return_value=computrabajo_instance
        ), patch("src.pipeline.guardar_resultados") as mock_save, patch("src.pipeline._cleanup_driver") as mock_cleanup:
            pipeline.run_combined("Analista", dias=1, initial_wait=0, page_wait=0)

        bumeran_instance.abrir_pagina_empleos.assert_called_once()
        bumeran_instance.buscar_vacante.assert_called_once_with("Analista")
        bumeran_instance.extraer_todos_los_puestos.assert_called_once()
        bumeran_instance.close.assert_called_once()
        mock_cleanup.assert_called_once_with(bumeran_instance)

        computrabajo_instance.abrir_pagina_empleos.assert_called_once_with(dias=1)
        computrabajo_instance.buscar_vacante.assert_called_once_with("Analista")
        computrabajo_instance.extraer_todos_los_puestos.assert_called_once()
        computrabajo_instance.close.assert_called_once()

        mock_save.assert_called_once()
        saved_records = mock_save.call_args.args[0]
        self.assertEqual(
            saved_records,
            [
                {"url": "https://jobs.com/a", "titulo": "Role A"},
                {"url": "https://jobs.com/b", "titulo": "Role B"},
                {"url": "https://jobs.com/c", "titulo": "Role C"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
