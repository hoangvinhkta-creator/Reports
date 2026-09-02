"""Nền history DB (TASK-PRA-001.1): cấu hình fail-closed + migration 0001_legacy.

Điểm cần chứng minh không phải "database chạy được" mà là: cấu hình sai thì
app CHẾT NGAY, chứ không chạy lên rồi hiển thị lịch sử rỗng — CHECK-PRA001-06.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

import tools.db as history_db
from tools.db import schema

REPO_ROOT = Path(__file__).resolve().parent.parent


# --- Cấu hình -------------------------------------------------------------

def test_default_url_is_sqlite_under_the_data_root(tmp_path):
    url = history_db.resolve_url({"REPORTS_DATA_ROOT": str(tmp_path)})
    assert url.startswith("sqlite:///")
    assert str(tmp_path) in url


def test_explicit_history_database_url_wins_over_the_default(tmp_path):
    url = history_db.resolve_url({
        "REPORTS_DATA_ROOT": str(tmp_path),
        "HISTORY_DATABASE_URL": "postgresql+psycopg://user@host/db",
    })
    assert url == "postgresql+psycopg://user@host/db"


def test_production_without_a_database_url_fails_closed():
    with pytest.raises(history_db.HistoryConfigurationError) as exc:
        history_db.resolve_url({"REPORTS_REQUIRE_HISTORY_DB": "1"})
    assert "HISTORY_DATABASE_URL" in str(exc.value)


def test_production_never_silently_falls_back_to_sqlite(tmp_path):
    """Fallback ngầm sang SQLite trên filesystem tạm là điều bị cấm: nó làm
    production TRÔNG NHƯ đã lưu lịch sử trong khi dữ liệu mất mỗi lần redeploy."""
    with pytest.raises(history_db.HistoryConfigurationError):
        history_db.resolve_url({
            "REPORTS_REQUIRE_HISTORY_DB": "1", "REPORTS_DATA_ROOT": str(tmp_path),
        })


def test_empty_database_url_in_production_is_treated_as_missing():
    with pytest.raises(history_db.HistoryConfigurationError):
        history_db.resolve_url({
            "REPORTS_REQUIRE_HISTORY_DB": "1", "HISTORY_DATABASE_URL": "   ",
        })


def test_schema_check_rejects_a_database_with_no_schema():
    engine = create_engine("sqlite://")
    with pytest.raises(history_db.HistoryConfigurationError) as exc:
        history_db.assert_schema_current(engine)
    assert "alembic upgrade head" in str(exc.value)


def test_schema_check_rejects_an_out_of_date_revision():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("UPDATE alembic_version SET version_num = '0000_old'")
    with pytest.raises(history_db.HistoryConfigurationError) as exc:
        history_db.assert_schema_current(engine)
    assert "0001_legacy" in str(exc.value)


def test_schema_check_accepts_a_database_at_head(history_engine):
    history_db.assert_schema_current(history_engine)


# --- Migration ------------------------------------------------------------

def _alembic(command: str, db_path: Path):
    return subprocess.run(
        [sys.executable, "-m", "alembic", command if command != "downgrade" else "downgrade",
         "head" if command == "upgrade" else "base"],
        cwd=REPO_ROOT, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HISTORY_DATABASE_URL": f"sqlite:///{db_path}",
             "PYTHONPATH": str(REPO_ROOT)},
    )


LEGACY_TABLES = {
    "legacy_import", "legacy_summary_row", "legacy_daily_sales",
    "legacy_monthly_reference",
}


def test_migration_upgrade_then_downgrade_round_trips(tmp_path):
    db_path = tmp_path / "history.db"
    up = _alembic("upgrade", db_path)
    assert up.returncode == 0, up.stderr
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        assert LEGACY_TABLES <= set(inspect(connection).get_table_names())
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar() == "0001_legacy"
    engine.dispose()

    down = _alembic("downgrade", db_path)
    assert down.returncode == 0, down.stderr
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        assert not (LEGACY_TABLES & set(inspect(connection).get_table_names()))
    engine.dispose()


def test_migration_chain_contains_only_the_legacy_revision():
    """PRA-002 (snapshot/version/reconciliation) KHÔNG được prebuild ở slice này."""
    versions = sorted(
        path.name for path in (REPO_ROOT / "tools/db/migrations/versions").glob("*.py")
    )
    assert versions == ["0001_legacy.py"]


def test_schema_declares_exactly_the_four_frozen_legacy_tables():
    assert set(schema.METADATA.tables) == LEGACY_TABLES


def test_every_fact_table_carries_an_explicit_origin_column():
    for name in LEGACY_TABLES:
        table = schema.METADATA.tables[name]
        assert "origin" in table.c, name
        assert any(
            "origin" in str(constraint.sqltext)
            for constraint in table.constraints
            if hasattr(constraint, "sqltext")
        ), name


def test_no_module_under_app_imports_a_database_driver_or_alembic():
    """ADR-101: driver DB sống ở tools/, không phải app/."""
    offenders = []
    for path in (REPO_ROOT / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for banned in ("import psycopg", "import alembic", "from alembic"):
            if banned in text:
                offenders.append(f"{path}: {banned}")
    assert offenders == []
