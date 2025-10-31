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
            {"url": "https://jobs.com/a", "titulo": "Role A", "empresa": "A"},
            {"url": "https://jobs.com/b", "titulo": "Role B", "empresa": "B"},
        ]

        computrabajo_instance = Mock()
        computrabajo_instance.driver = None
        computrabajo_instance.extraer_todos_los_puestos.return_value = [
            {"url": "https://jobs.com/b", "titulo": "Role B", "empresa": "B"},
            {"url": "https://jobs.com/c", "titulo": "Role C", "empresa": "C"},
        ]

        indeed_instance = Mock()
        indeed_instance.driver = None
        indeed_instance.extraer_todos_los_puestos.return_value = [
            {"url": "https://jobs.com/c", "titulo": "Role C", "empresa": "C"},
            {"url": "https://jobs.com/d", "titulo": "Role D", "empresa": "D"},
        ]

        with patch("src.pipeline.BumeranScraper", return_value=bumeran_instance), patch(
            "src.pipeline.ComputrabajoScraper", return_value=computrabajo_instance
        ), patch("src.pipeline.IndeedScraper", return_value=indeed_instance), patch(
            "src.pipeline.guardar_resultados"
        ) as mock_save, patch("src.pipeline._cleanup_driver") as mock_cleanup:
            result = pipeline.run_combined("Analista", dias=1, initial_wait=0, page_wait=0)

        bumeran_instance.abrir_pagina_empleos.assert_called_once()
        bumeran_instance.buscar_vacante.assert_called_once_with("Analista")
        bumeran_instance.extraer_todos_los_puestos.assert_called_once()
        bumeran_instance.close.assert_called_once()
        mock_cleanup.assert_called_once_with(bumeran_instance, "bumeran")

        computrabajo_instance.abrir_pagina_empleos.assert_called_once_with(dias=1)
        computrabajo_instance.buscar_vacante.assert_called_once_with("Analista")
        computrabajo_instance.extraer_todos_los_puestos.assert_called_once()
        computrabajo_instance.close.assert_called_once()

        indeed_instance.abrir_pagina_empleos.assert_called_once_with(dias=1)
        indeed_instance.buscar_vacante.assert_called_once_with("Analista")
        indeed_instance.extraer_todos_los_puestos.assert_called_once()
        indeed_instance.close.assert_called_once()

        mock_save.assert_called_once()
        saved_records = mock_save.call_args.args[0]
        expected = [
            {"fuente": "Bumeran", "url": "https://jobs.com/a", "titulo": "Role A", "empresa": "A"},
            {"fuente": "Bumeran", "url": "https://jobs.com/b", "titulo": "Role B", "empresa": "B"},
            {"fuente": "Computrabajo", "url": "https://jobs.com/c", "titulo": "Role C", "empresa": "C"},
            {"fuente": "Indeed", "url": "https://jobs.com/d", "titulo": "Role D", "empresa": "D"},
        ]
        self.assertEqual(saved_records, expected)
        self.assertEqual(result, expected)

    def test_run_combined_filters_sources(self) -> None:
        indeed_instance = Mock()
        indeed_instance.driver = None
        indeed_instance.extraer_todos_los_puestos.return_value = [
            {"url": "https://jobs.com/only", "titulo": "Only", "empresa": "OnlyCorp"}
        ]

        with patch("src.pipeline.BumeranScraper") as bumeran_cls, patch(
            "src.pipeline.ComputrabajoScraper"
        ) as computrabajo_cls, patch(
            "src.pipeline.IndeedScraper", return_value=indeed_instance
        ), patch("src.pipeline.guardar_resultados") as mock_save, patch(
            "src.pipeline._cleanup_driver"
        ) as mock_cleanup:
            result = pipeline.run_combined(
                "Analista", dias=0, initial_wait=0, page_wait=0, sources=["indeed"]
            )

        bumeran_cls.assert_not_called()
        computrabajo_cls.assert_not_called()
        indeed_instance.abrir_pagina_empleos.assert_called_once_with(dias=0)
        indeed_instance.buscar_vacante.assert_called_once_with("Analista")
        indeed_instance.extraer_todos_los_puestos.assert_called_once()
        indeed_instance.close.assert_called_once()
        mock_cleanup.assert_not_called()
        mock_save.assert_called_once()
        saved_records = mock_save.call_args.args[0]
        expected = [
            {
                "fuente": "Indeed",
                "url": "https://jobs.com/only",
                "titulo": "Only",
                "empresa": "OnlyCorp",
            }
        ]
        self.assertEqual(saved_records, expected)
        self.assertEqual(result, expected)

    def test_collect_jobs_logs_duration_and_totals(self) -> None:
        fake_scraper = Mock()
        fake_scraper.close = Mock()

        def fake_factory(headless=None):
            return fake_scraper

        def fake_collector(scraper, busqueda, dias, initial_wait, page_wait):
            return [
                {
                    "fuente": "Fake",
                    "url": "https://jobs.com/fake",
                    "titulo": "Role",
                    "empresa": "FakeCorp",
                }
            ]

        with patch.dict(
            "src.pipeline.SCRAPER_REGISTRY",
            {"fake": (fake_factory, fake_collector, False)},
            clear=True,
        ), patch("src.pipeline.logger") as mock_logger, patch(
            "src.pipeline.time.perf_counter", side_effect=[100.0, 101.5]
        ):
            combined, executed = pipeline.collect_jobs(
                busqueda="Analista",
                dias=0,
                initial_wait=0,
                page_wait=0,
                sources=["fake"],
            )

        self.assertEqual(executed, ["fake"])
        self.assertEqual(
            combined,
            [
                {
                    "fuente": "Fake",
                    "url": "https://jobs.com/fake",
                    "titulo": "Role",
                    "empresa": "FakeCorp",
                }
            ],
        )
        fake_scraper.close.assert_called_once()
        mock_logger.info.assert_any_call("Iniciando scraper '%s'", "fake")
        mock_logger.info.assert_any_call(
            "Scraper '%s' finalizado en %.2fs con %d ofertas", "fake", 1.5, 1
        )
        mock_logger.info.assert_any_call(
            "Total ofertas combinadas tras deduplicación: %d", 1
        )

    def test_collect_jobs_logs_exception_and_skips_results(self) -> None:
        failing_scraper = Mock()
        failing_scraper.close = Mock()

        def failing_factory(headless=None):
            return failing_scraper

        def failing_collector(scraper, busqueda, dias, initial_wait, page_wait):
            raise RuntimeError("boom")

        with patch.dict(
            "src.pipeline.SCRAPER_REGISTRY",
            {"failing": (failing_factory, failing_collector, False)},
            clear=True,
        ), patch("src.pipeline.logger") as mock_logger, patch(
            "src.pipeline.time.perf_counter", side_effect=[5.0, 7.0]
        ):
            combined, executed = pipeline.collect_jobs(
                busqueda="Analista",
                dias=0,
                initial_wait=0,
                page_wait=0,
                sources=["failing"],
            )

        self.assertEqual(combined, [])
        self.assertEqual(executed, [])
        failing_scraper.close.assert_called_once()
        mock_logger.exception.assert_any_call(
            "Error no controlado ejecutando scraper '%s'", "failing"
        )
        mock_logger.info.assert_any_call(
            "Scraper '%s' finalizado en %.2fs con %d ofertas", "failing", 2.0, 0
        )
        mock_logger.info.assert_any_call("Scraper '%s' no produjo resultados.", "failing")
        mock_logger.info.assert_any_call(
            "Total ofertas combinadas tras deduplicación: %d", 0
        )


if __name__ == "__main__":
    unittest.main()
