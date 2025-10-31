"""Public package interface for scraper components."""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = ["BumeranScraper", "ComputrabajoScraper", "IndeedScraper", "run_combined"]

if TYPE_CHECKING:  # pragma: no cover
	from .bumeran import BumeranScraper as _BumeranScraper
	from .computrabajo import ComputrabajoScraper as _ComputrabajoScraper
	from .indeed import IndeedScraper as _IndeedScraper
	from .pipeline import run_combined as _run_combined

try:
	from .bumeran import BumeranScraper  # type: ignore[no-redef]
except ModuleNotFoundError:  # pragma: no cover
	BumeranScraper = None  # type: ignore[assignment]

try:
	from .computrabajo import ComputrabajoScraper  # type: ignore[no-redef]
except ModuleNotFoundError:  # pragma: no cover
	ComputrabajoScraper = None  # type: ignore[assignment]

try:
	from .indeed import IndeedScraper  # type: ignore[no-redef]
except ModuleNotFoundError:  # pragma: no cover
	IndeedScraper = None  # type: ignore[assignment]

try:
	from .pipeline import run_combined  # type: ignore[no-redef]
except ModuleNotFoundError:  # pragma: no cover
	run_combined = None  # type: ignore[assignment]
