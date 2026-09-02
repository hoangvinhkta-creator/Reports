from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.legacy.build_legacy_workbook import build_legacy_workbook
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


@pytest.fixture
def legacy_workbook_path(tmp_path: Path) -> Path:
    """Workbook legacy tổng hợp (anonymized) có cài sẵn A1/A2/A4/A6."""
    return build_legacy_workbook(tmp_path / "bao_cao_kinh_doanh_fixture.xlsx")


@pytest.fixture
def history_engine():
    """Engine SQLite trong bộ nhớ đã dựng schema — không chạm filesystem."""
    from sqlalchemy import create_engine

    import tools.db as history_db

    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def legacy_repository(history_engine):
    from app.web import history_store

    return history_store.build(engine=history_engine)
