from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.synthetic_workbook import build_synthetic_workbook

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"


@pytest.fixture
def synthetic_raw_path(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic_raw_sample.xlsx"
    build_synthetic_workbook(path)
    return path


@pytest.fixture
def config_dir() -> Path:
    return CONFIG_DIR
