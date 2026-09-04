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
    assert history_db.ALEMBIC_HEAD in str(exc.value)


def test_schema_check_accepts_a_database_at_head(history_engine):
    history_db.assert_schema_current(history_engine)


# --- Migration ------------------------------------------------------------

def _alembic(command: str, db_path: Path, target: str | None = None):
    return subprocess.run(
        [sys.executable, "-m", "alembic", command,
         target or ("head" if command == "upgrade" else "base")],
        cwd=REPO_ROOT, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HISTORY_DATABASE_URL": f"sqlite:///{db_path}",
             "PYTHONPATH": str(REPO_ROOT)},
    )


LEGACY_TABLES = {
    "legacy_import", "legacy_summary_row", "legacy_daily_sales",
    "legacy_monthly_reference",
}

# TASK-PRA-002 mục 4 — sáu bảng origin PIPELINE_GENERATED của `0002_snapshots`.
PIPELINE_TABLES = {
    "source_snapshot", "order_line_source_version", "snapshot_line",
    "order_line_result_version", "order_line_current", "reconciliation_flag",
}

# PHB-03 mục 3 + mục 4 — hai bảng QUYẾT ĐỊNH CỦA NGƯỜI của `0003_business`.
# Chúng được thêm vào bản kiểm kê đã freeze vì `DEC-PHB02-02` (giá nhập phải
# nhập/sửa được, có provenance) và `DEC-PHB02-05` (tick Gia dụng phải lưu lại
# được) YÊU CẦU persistence — không phải vì một agent thấy tiện. Hai bảng, và
# đúng hai bảng: PHB-03 §3 cấm dựng subsystem quanh chúng.
BUSINESS_TABLES = {"kpi_purchase_price_override", "product_group_classification"}

# PHB-03 REPAIR (`OD-5`) — bảng thứ ba của cùng loại: Owner gán lại nhân viên
# cho một dòng hàng. Nó ở migration riêng `0004` chứ không nhét vào `0003` vì
# `0003` đã chạy trên production — sửa một migration đã chạy là viết lại lịch
# sử của một database đang sống.
EMPLOYEE_TABLES = {"employee_attribution_override"}

# Ba bảng chứa thứ DUY NHẤT không tái tạo lại được từ file sổ gốc. Danh sách
# này là đầu vào của test rollback-an-toàn bên dưới (`B04`).
OWNER_INPUT_TABLES = BUSINESS_TABLES | EMPLOYEE_TABLES


def test_migration_upgrade_then_downgrade_round_trips(tmp_path):
    db_path = tmp_path / "history.db"
    up = _alembic("upgrade", db_path)
    assert up.returncode == 0, up.stderr
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        names = set(inspect(connection).get_table_names())
        assert LEGACY_TABLES <= names
        assert PIPELINE_TABLES <= names
        assert OWNER_INPUT_TABLES <= names
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar() == history_db.ALEMBIC_HEAD
    engine.dispose()

    down = _alembic("downgrade", db_path)
    assert down.returncode == 0, down.stderr
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        assert not ((LEGACY_TABLES | PIPELINE_TABLES | OWNER_INPUT_TABLES)
                    & set(inspect(connection).get_table_names()))
    engine.dispose()


_SEED_PRICE = (
    "INSERT INTO kpi_purchase_price_override"
    " (order_key, product_key, occurrence_index, origin, purchase_price,"
    "  provenance, auto_price_at_entry, entered_at, entered_by)"
    " VALUES ('BTL00300', 'pk-panasonic', 1, 'PIPELINE_GENERATED', 6200000,"
    "         'MANUAL', NULL, '2026-09-04T09:00:00', 'owner')"
)
_SEED_GROUP = (
    "INSERT INTO product_group_classification"
    " (product_key, origin, product_group, product_label, classified_at,"
    "  classified_by)"
    " VALUES ('pk-noicom', 'PIPELINE_GENERATED', 'GIA_DUNG', 'Nồi cơm',"
    "         '2026-09-04T09:00:00', 'owner')"
)
_SEED_EMPLOYEE = (
    "INSERT INTO employee_attribution_override"
    " (order_key, product_key, occurrence_index, origin, employee_normalized,"
    "  employee_group, source_employee_at_entry, assigned_at, assigned_by)"
    " VALUES ('BTL00300', 'pk-panasonic', 1, 'PIPELINE_GENERATED', 'Vinh',"
    "         'NOI_THANH', NULL, '2026-09-04T09:00:00', 'owner')"
)


def test_rollback_never_destroys_what_the_owner_typed_in(tmp_path):
    """`B04` — `alembic downgrade` KHÔNG được xoá dữ liệu Owner nhập tay.

    Giá nhập Owner gõ, tick Gia dụng và việc gán nhân viên là thứ DUY NHẤT
    trong database không tái tạo lại được: chạy lại pipeline dựng lại mọi bảng
    khác từ file sổ gốc, nhưng không dựng lại được những con số nằm trong đầu
    Owner. Một lệnh rollback thường được gõ vội lúc đang có sự cố khác — đúng
    lúc không ai kịp nghĩ tới hậu quả đó.

    Test đi hết vòng THẬT qua alembic (không gọi hàm trực tiếp): nạp dữ liệu →
    downgrade → dữ liệu còn nguyên trong két → upgrade → dữ liệu về đúng chỗ
    cũ, và cái két rỗng đi.
    """
    db_path = tmp_path / "history.db"
    assert _alembic("upgrade", db_path).returncode == 0
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        for statement in (_SEED_PRICE, _SEED_GROUP, _SEED_EMPLOYEE):
            connection.exec_driver_sql(statement)
    engine.dispose()

    assert _alembic("downgrade", db_path, "0002_snapshots").returncode == 0
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        names = set(inspect(connection).get_table_names())
        # Bảng thật đã biến mất — downgrade vẫn làm đúng việc của nó...
        assert not (OWNER_INPUT_TABLES & names)
        # ...nhưng KHÔNG một dòng nào của Owner bị mất theo.
        for table in OWNER_INPUT_TABLES:
            backup = schema.owner_backup_name(table)
            assert backup in names, table
            assert connection.exec_driver_sql(
                f"SELECT COUNT(*) FROM {backup}").scalar() == 1
    engine.dispose()

    assert _alembic("upgrade", db_path, "head").returncode == 0
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        names = set(inspect(connection).get_table_names())
        assert OWNER_INPUT_TABLES <= names
        # Cái két rỗng đi sau khi đã trả hàng: để nó nằm lại thì lần rollback
        # sau sẽ chèn thêm vào một két đã có nội dung cũ.
        assert not any(schema.owner_backup_name(t) in names
                       for t in OWNER_INPUT_TABLES)
        assert connection.exec_driver_sql(
            "SELECT purchase_price, provenance, entered_by"
            " FROM kpi_purchase_price_override").fetchall() == [
            ("6200000", "MANUAL", "owner")]
        assert connection.exec_driver_sql(
            "SELECT product_group FROM product_group_classification"
        ).fetchall() == [("GIA_DUNG",)]
        assert connection.exec_driver_sql(
            "SELECT employee_normalized, employee_group"
            " FROM employee_attribution_override").fetchall() == [
            ("Vinh", "NOI_THANH")]
    engine.dispose()


def test_rollback_of_an_empty_database_leaves_no_leftover_backup(tmp_path):
    """Không có gì để mất ⟹ không tạo két.

    Một cái két rỗng nằm lại trong database production là rác, và tệ hơn: lần
    sau người vận hành nhìn thấy nó sẽ không biết nó rỗng vì chưa có dữ liệu
    hay vì đã có ai xoá mất.
    """
    db_path = tmp_path / "history.db"
    assert _alembic("upgrade", db_path).returncode == 0
    assert _alembic("downgrade", db_path, "0002_snapshots").returncode == 0
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        names = set(inspect(connection).get_table_names())
    engine.dispose()
    assert not [name for name in names
                if name.endswith(schema.OWNER_BACKUP_SUFFIX)]


def test_migration_0002_is_additive_and_leaves_legacy_rows_untouched(tmp_path):
    """CHECK-PRA002-01: nâng cấp 0001 → 0002 KHÔNG chạm dữ liệu PRA-001.

    Đây là điều kiện để migration này chạy được trên production đang có dữ
    liệu legacy thật: một bản nâng cấp làm mất một dòng legacy nào cũng là
    hỏng, kể cả khi sáu bảng mới dựng lên đúng.
    """
    db_path = tmp_path / "history.db"
    assert _alembic("upgrade", db_path, "0001_legacy").returncode == 0
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO legacy_import (import_id, origin, file_fingerprint, is_current)"
            " VALUES ('LEG-TEST', 'LEGACY_REFERENCE', 'abc123', 0)"
        )
        before = connection.exec_driver_sql(
            "SELECT import_id, file_fingerprint FROM legacy_import"
        ).fetchall()
        assert not ((PIPELINE_TABLES | OWNER_INPUT_TABLES)
                    & set(inspect(connection).get_table_names()))
    engine.dispose()

    assert _alembic("upgrade", db_path, "head").returncode == 0
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        assert (PIPELINE_TABLES | OWNER_INPUT_TABLES) <= set(
            inspect(connection).get_table_names())
        assert connection.exec_driver_sql(
            "SELECT import_id, file_fingerprint FROM legacy_import"
        ).fetchall() == before
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar() == history_db.ALEMBIC_HEAD
    engine.dispose()


def test_migration_chain_is_exactly_the_frozen_revisions():
    """Chain đúng bằng những revision đã freeze — không prebuild vertical sau.

    `0003_business` gia nhập danh sách này khi PHB-03 implement hai quyết định
    Owner `DEC-PHB02-02`/`DEC-PHB02-05`; nó KHÔNG mở đường cho một migration
    "để dành" cho vertical chưa có hợp đồng.
    """
    versions = sorted(
        path.name for path in (REPO_ROOT / "tools/db/migrations/versions").glob("*.py")
    )
    assert versions == ["0001_legacy.py", "0002_snapshots.py",
                        "0003_business.py", "0004_employee_attribution.py"]


def test_schema_declares_exactly_the_frozen_tables():
    assert set(schema.METADATA.tables) == (
        LEGACY_TABLES | PIPELINE_TABLES | OWNER_INPUT_TABLES)


def test_the_owner_backup_table_is_not_part_of_the_schema():
    """Cái két của `B04` KHÔNG phải một bảng của lược đồ.

    Nó chỉ tồn tại giữa một lần rollback và lần nâng cấp lại. Khai nó trong
    `METADATA` sẽ khiến `create_all` dựng một bảng rỗng vĩnh viễn nằm đó, và
    người vận hành sau này phải đoán nó là gì.
    """
    for name in OWNER_INPUT_TABLES:
        assert schema.owner_backup_name(name) not in schema.METADATA.tables


def test_every_fact_table_carries_an_explicit_origin_column():
    for name in (LEGACY_TABLES | OWNER_INPUT_TABLES
                 | (PIPELINE_TABLES - {"snapshot_line", "reconciliation_flag"})):
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
