import argparse
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.selenium_stub import ensure_selenium_stub

ensure_selenium_stub()

import main  # type: ignore


class MainModuleTests(unittest.TestCase):
    def test_resolve_parameters_non_interactive(self) -> None:
        args = argparse.Namespace(
            busqueda="Analista",
            dias=2,
            hoy=False,
            initial_wait=None,
            page_wait=None,
            interactive=False,
            source=None,
        )
        params = main.resolve_parameters(args)
        self.assertIsInstance(params, main.RunParameters)
        assert params is not None
        self.assertEqual(params.busqueda, "Analista")
        self.assertEqual(params.dias, 2)
        self.assertEqual(params.initial_wait, 2.0)
        self.assertEqual(params.page_wait, 1.0)
        self.assertEqual(params.sources, list(main.DEFAULT_SOURCES))

    def test_resolve_parameters_interactive_uses_prompt(self) -> None:
        interactive_params = main.RunParameters(
            busqueda="Data Scientist",
            dias=1,
            initial_wait=3.0,
            page_wait=1.5,
            sources=["indeed"],
        )
        args = argparse.Namespace(
            busqueda=None,
            dias=0,
            hoy=False,
            initial_wait=None,
            page_wait=None,
            interactive=True,
            source=None,
        )
        with patch("main.prompt_interactive", return_value=interactive_params) as mock_prompt:
            params = main.resolve_parameters(args)
        mock_prompt.assert_called_once()
        self.assertIsInstance(params, main.RunParameters)
        self.assertEqual(params, interactive_params)

    def test_prompt_interactive_validates_input(self) -> None:
        user_inputs = ["Analista", "5", "2", ""]
        with patch("builtins.input", side_effect=user_inputs):
            params = main.prompt_interactive()
        self.assertIsInstance(params, main.RunParameters)
        assert params is not None
        self.assertEqual(params.busqueda, "Analista")
        self.assertEqual(params.dias, 2)
        self.assertEqual(params.initial_wait, 2.0)
        self.assertEqual(params.page_wait, 1.0)
        self.assertEqual(params.sources, list(main.DEFAULT_SOURCES))

    def test_prompt_interactive_returns_none_on_empty_search(self) -> None:
        with patch("builtins.input", side_effect=["   "]):
            params = main.prompt_interactive()
        self.assertIsNone(params)


if __name__ == "__main__":
    unittest.main()
