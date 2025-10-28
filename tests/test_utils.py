import json
import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.selenium_stub import ensure_selenium_stub

ensure_selenium_stub()

from datetime import datetime as real_datetime

from src.utils import guardar_resultados


class GuardarResultadosTests(unittest.TestCase):
    def test_guardar_resultados_creates_json_and_csv(self) -> None:
        records = [
            {"titulo": "Analista", "url": "https://example.com/a"},
            {"titulo": "Cientifico", "url": "https://example.com/b"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.utils.datetime") as mock_datetime:
                mock_datetime.now.return_value = real_datetime(2025, 1, 15)
                guardar_resultados(records, "Analista", output_dir=tmpdir, source="combined")

            base_path = os.path.join(tmpdir, "combined_analista_2025-01-15")
            json_path = f"{base_path}.json"
            csv_path = f"{base_path}.csv"

            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(csv_path))

            with open(json_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data, records)

            with open(csv_path, "r", encoding="utf-8") as handle:
                rows = handle.read().splitlines()
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0], "titulo,url")

    def test_guardar_resultados_handles_empty_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.utils.datetime") as mock_datetime:
                mock_datetime.now.return_value = real_datetime(2025, 6, 2)
                guardar_resultados([], "Data", output_dir=tmpdir, source="bumeran")

            base_path = os.path.join(tmpdir, "bumeran_data_2025-06-02")
            csv_path = f"{base_path}.csv"

            with open(csv_path, "r", encoding="utf-8") as handle:
                rows = handle.read().splitlines()

            self.assertEqual(rows, ["titulo,url"])


if __name__ == "__main__":
    unittest.main()
