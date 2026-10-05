"""Smoke test — pagine dashboard compilano."""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

DASH_DIR = Path(__file__).resolve().parent.parent
PAGES_DIR = DASH_DIR / "pages"


@pytest.mark.parametrize("page", sorted(PAGES_DIR.glob("*.py")), ids=lambda p: p.stem)
def test_page_compiles(page: Path) -> None:
    py_compile.compile(str(page), doraise=True)


def test_app_compiles() -> None:
    py_compile.compile(str(DASH_DIR / "app.py"), doraise=True)


def test_sources_compiles() -> None:
    py_compile.compile(str(DASH_DIR / "sources.py"), doraise=True)
