"""TASK-PRA-002 — persistence: append-only, con trỏ hiện hành, fail-safe.

Đây là tầng nơi "không đếm hai lần" phải là tính chất của CẤU TRÚC (PK/UNIQUE)
chứ không của việc câu truy vấn có nhớ lọc đúng hay không. Test ở đây dựng
database thật (SQLite tạm) và hỏi database, không hỏi code.
"""

from __future__ import annotations

import ast
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError

import tools.db as history_db
from app.history import keys
from app.history.models import (
    COLLISION_DAY_THRESHOLD, LineKey, ResultLine, SourceLine,
)
from app.web import history_store
from tools.db import schema

REPO_ROOT = Path(__file__).resolve().parents[1]

PII_COLUMNS = {"customer", "customer_code", "phone", "address", "shipper_raw"}

PIPELINE_TABLES = (
    "source_snapshot", "order_line_source_version", "snapshot_line",
    "order_line_result_version", "order_line_current", "reconciliation_flag",
)


@pytest.fixture
def repository(history_engine):
    return history_store.SnapshotRepository(history_engine)


def source_line(order="BH1", product="Tủ lạnh", occurrence=1, *, row=6,
                sale_date=date(2026, 1, 5), sell_price="8000000", **overrides):
    values = dict(
        sale_date=sale_date, product_raw=product, quantity=Decimal("1"),
        sell_price=Decimal(sell_price), discount=Decimal("0"),
        total_sales_raw=Decimal(sell_price), delivery_cost=None, imei=None,
        note_raw=None, employee_raw="Vũ Hạnh Ly", source_profit=Decimal("500000"),
    )
    values.update(overrides)
    ordered = tuple(values[name] for name in keys.FINGERPRINT_FIELDS)
    number, year_hint = keys.bh_parts(order, values["sale_date"])
    return SourceLine(
        key=LineKey(order, keys.product_key(product), occurrence), source_row=row,
        row_hash="hash", fingerprint=keys.line_fingerprint(ordered),
        bh_number=number, bh_year_hint=year_hint, **values,
    )


def result_line(line: SourceLine, *, status="AUTO", purchase="5000000", kpi="3000000"):
    return ResultLine(
        key=line.key, status=status, pending_reasons=() if status == "AUTO" else ("x",),
        total_sales=line.total_sales_raw, employee_normalized="VuHanhLy",
        employee_group="G1", lead_source_final="PERSONAL",
        identity_namespace="TRACKING", canonical_product_code="A1",
        accounting_purchase_price=Decimal(purchase), price_source="TRACKING_PRICE_HISTORY",
        composition_rule="TRACKING_HISTORY_AUTHORITY",
        accounting_profit=Decimal("3000000"), kpi_purchase_price=Decimal(purchase),
        kpi_purchase_provenance="Config:NoConfirmedAdjustment",
        eligible_kpi_profit=Decimal(kpi), product_group_final="DIEN_MAY",
        conversion_scheme_final="S1", conversion_rate_final=Decimal("1"),
        result_fingerprint=keys.result_fingerprint(status, Decimal(purchase), Decimal(kpi)),
    )


def write(repository, lines, *, run_id, created_at, fingerprint="fp-a", **kwargs):
    return repository.write_snapshot(
        run_id=run_id, created_at=created_at, source_file_name="so.xlsx",
        file_fingerprint=fingerprint, file_size=1024,
        header_text="Nhân viên: Tín Phát, Tháng 1 năm 2026",
        sheet_data_rows=len(lines) + 1, rows_without_order_id=1,
        source_lines=lines, result_lines=[result_line(line) for line in lines],
        evidence={"tracking_catalog_capture_id": "cap-1"},
        summary={"input_orders": len(lines)}, **kwargs,
    )


def count(engine, table) -> int:
    with engine.connect() as connection:
        return connection.execute(select(func.count()).select_from(table)).scalar()


def rows(engine, table, *order_by):
    with engine.connect() as connection:
        statement = select(table)
        if order_by:
            statement = statement.order_by(*order_by)
        return [dict(row._mapping) for row in connection.execute(statement)]


# --- INSERT vertical ------------------------------------------------------

def test_one_upload_writes_snapshot_source_result_and_current_together(repository, history_engine):
    lines = [source_line("BH1", row=6), source_line("BH2", row=7)]
    outcome = write(repository, lines, run_id="run-1", created_at="2026-02-01T00:00:00")

    assert outcome.counts["INSERT"] == 2
    assert outcome.duplicate_of_snapshot_id is None
    assert outcome.snapshot_id.startswith("SNAP-20260201000000-")
    assert count(history_engine, schema.order_line_source_version) == 2
    assert count(history_engine, schema.order_line_result_version) == 2
    assert count(history_engine, schema.order_line_current) == 2
    assert count(history_engine, schema.snapshot_line) == 2
    assert [row["version_no"] for row in rows(history_engine, schema.order_line_source_version)] == [1, 1]
    assert repository.current_totals() == {
        "lines": 2, "orders": 2, "total_sales": Decimal("16000000"),
    }


def test_the_snapshot_row_records_coverage_measured_from_the_data(repository):
    outcome = write(repository, [source_line(sale_date=date(2026, 1, 5))],
                    run_id="run-1", created_at="2026-02-01T00:00:00")
    snapshot = repository.get_snapshot(outcome.snapshot_id)
    assert snapshot["detected_date_min"] == date(2026, 1, 5)
    assert snapshot["coverage_state"] == "HEADER_CONSISTENT"
    assert snapshot["origin"] == "PIPELINE_GENERATED"


def test_coverage_is_never_confirmed_complete_without_an_explicit_confirmation(repository):
    """Slice A KHÔNG có đường nào tạo ra `CONFIRMED_COMPLETE` — đó là slice B."""
    outcome = write(repository, [source_line()], run_id="run-1",
                    created_at="2026-02-01T00:00:00")
    assert repository.get_snapshot(outcome.snapshot_id)["coverage_state"] != (
        "CONFIRMED_COMPLETE"
    )


# --- SAME / no double count -----------------------------------------------

def test_uploading_the_same_book_again_adds_no_version_and_no_money(repository, history_engine):
    lines = [source_line("BH1", row=6), source_line("BH2", row=7)]
    first = write(repository, lines, run_id="run-1", created_at="2026-02-01T00:00:00")
    before = repository.current_totals()

    second = write(repository, lines, run_id="run-2", created_at="2026-02-02T00:00:00")

    assert second.counts == {"INSERT": 0, "SAME": 2, "SOURCE_CHANGED": 0,
                             "ORDER_KEY_COLLISION": 0}
    assert second.duplicate_of_snapshot_id == first.snapshot_id
    assert count(history_engine, schema.order_line_source_version) == 2, "0 version mới"
    assert count(history_engine, schema.order_line_current) == 2
    assert repository.current_totals() == before, "tổng hiện hành KHÔNG đổi"
    # Run mới ĐÃ chạy pipeline thật → result version mới; audit tăng, business không.
    assert count(history_engine, schema.order_line_result_version) == 4
    assert repository.count_flags() == 0


def test_the_current_pointer_follows_the_latest_snapshot_that_saw_the_line(repository):
    lines = [source_line("BH1")]
    first = write(repository, lines, run_id="run-1", created_at="2026-02-01T00:00:00")
    second = write(repository, lines, run_id="run-2", created_at="2026-02-02T00:00:00")
    current, = _current(repository)
    assert current["first_seen_snapshot_id"] == first.snapshot_id
    assert current["last_seen_snapshot_id"] == second.snapshot_id


def _current(repository):
    with repository.engine.connect() as connection:
        return [dict(row._mapping)
                for row in connection.execute(select(schema.order_line_current))]


# --- SOURCE_CHANGED -------------------------------------------------------

def test_an_edited_line_keeps_the_old_version_readable_and_moves_current(repository, history_engine):
    write(repository, [source_line("BH1", sell_price="8000000")],
          run_id="run-1", created_at="2026-02-01T00:00:00")
    edited = source_line("BH1", sell_price="9000000", total_sales_raw=Decimal("9000000"))
    outcome = write(repository, [edited], run_id="run-2",
                    created_at="2026-02-02T00:00:00", fingerprint="fp-b")

    assert outcome.counts["SOURCE_CHANGED"] == 1
    versions = rows(history_engine, schema.order_line_source_version,
                    schema.order_line_source_version.c.version_no)
    assert [row["version_no"] for row in versions] == [1, 2]
    assert versions[0]["sell_price"] == Decimal("8000000"), "version cũ đọc lại nguyên văn"
    assert versions[0]["changed_fields_json"] is None
    assert versions[1]["changed_fields_json"] == (
        '{"sell_price": {"new": "9000000", "old": "8000000"}, '
        '"total_sales_raw": {"new": "9000000", "old": "8000000"}}'
    )
    current, = _current(repository)
    assert current["current_source_version_id"] == versions[1]["id"]
    assert repository.current_totals()["total_sales"] == Decimal("9000000")

    flag, = repository.list_flags()
    assert flag["kind"] == "SOURCE_CHANGED"
    assert (flag["from_version_id"], flag["to_version_id"]) == (
        versions[0]["id"], versions[1]["id"]
    )
    assert flag["detail_json"]["sell_price"] == {"old": "8000000", "new": "9000000"}


def test_a_changed_field_record_never_carries_a_customer_field(repository):
    write(repository, [source_line("BH1", sell_price="8000000")],
          run_id="run-1", created_at="2026-02-01T00:00:00")
    write(repository, [source_line("BH1", sell_price="9000000")], run_id="run-2",
          created_at="2026-02-02T00:00:00", fingerprint="fp-b")
    flag, = repository.list_flags()
    assert PII_COLUMNS.isdisjoint(flag["detail_json"])


# --- COLLISION ------------------------------------------------------------

def test_a_colliding_key_is_stored_flagged_and_left_out_of_the_current_state(
    repository, history_engine,
):
    write(repository, [source_line("BH1", sale_date=date(2026, 1, 5))],
          run_id="run-1", created_at="2026-02-01T00:00:00")
    far = date(2026, 1, 5) + timedelta(days=COLLISION_DAY_THRESHOLD + 1)
    outcome = write(repository, [source_line("BH1", sale_date=far)], run_id="run-2",
                    created_at="2026-02-02T00:00:00", fingerprint="fp-b")

    assert outcome.counts["ORDER_KEY_COLLISION"] == 1
    assert count(history_engine, schema.order_line_source_version) == 2, "không mất bản ghi"
    current, = _current(repository)
    assert current["order_key_collision"] is True
    assert current["sale_date"] == date(2026, 1, 5), "hiện trạng cũ giữ nguyên"
    assert count(history_engine, schema.order_line_result_version) == 1, (
        "khoá tranh chấp KHÔNG đóng góp kết quả nào vào hiện trạng"
    )
    membership, = [row for row in rows(history_engine, schema.snapshot_line)
                   if row["snapshot_id"] == outcome.snapshot_id]
    assert membership["outcome"] == "ORDER_KEY_COLLISION"
    flag, = repository.list_flags()
    assert flag["kind"] == "ORDER_KEY_COLLISION"
    assert flag["detail_json"]["day_gap"] == COLLISION_DAY_THRESHOLD + 1


# --- append-only / bất biến cấu trúc --------------------------------------

def test_three_snapshots_only_ever_add_versions(repository, history_engine):
    for index, price in enumerate(("8000000", "9000000", "10000000"), start=1):
        write(repository, [source_line("BH1", sell_price=price)], run_id=f"run-{index}",
              created_at=f"2026-02-0{index}T00:00:00", fingerprint=f"fp-{index}")
    versions = rows(history_engine, schema.order_line_source_version,
                    schema.order_line_source_version.c.version_no)
    assert [row["version_no"] for row in versions] == [1, 2, 3]
    assert [row["sell_price"] for row in versions] == [
        Decimal("8000000"), Decimal("9000000"), Decimal("10000000"),
    ]
    assert len(_current(repository)) == 1, "một khoá — đúng một dòng hiện hành"


def _called_with(path: Path, function: str) -> set:
    """Tên bảng làm đối số đầu tiên của mọi lời gọi ``function(...)`` trong file.

    Đọc bằng AST chứ không bằng grep chuỗi: một câu văn xuôi nhắc tới
    ``delete()`` trong tài liệu KHÔNG phải là một lời gọi, và ngược lại một
    lời gọi thật không được phép trốn sau cách viết khác.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    targets = set()
    for node in ast.walk(tree):
        # Chỉ lời gọi tên trần (`update(...)`) — đúng cách tầng này dùng
        # SQLAlchemy Core. `some_set.update(...)` của Python KHÔNG phải câu
        # lệnh SQL và không được đếm nhầm vào đây.
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id != function:
            continue
        first = node.args[0] if node.args else None
        targets.add(getattr(first, "id", None) or getattr(first, "attr", None) or "?")
    return targets


def _imported_from_sqlalchemy(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {alias.name for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("sqlalchemy")
            for alias in node.names}


def test_the_write_path_contains_no_delete_and_updates_only_the_pointer_table():
    """CHECK-PRA002-09 tĩnh: append-only phải đọc được từ chính mã nguồn."""
    store = REPO_ROOT / "app/web/history_store.py"
    writer = REPO_ROOT / "app/web/history_writer.py"
    assert _called_with(store, "delete") == set()
    assert _called_with(writer, "delete") == set()
    # Câu lệnh DELETE của SQLAlchemy Core thậm chí không được import vào đây.
    assert "delete" not in _imported_from_sqlalchemy(store)
    # `legacy_import` là bảng con trỏ của PRA-001 (`is_current`); PRA-002 chỉ
    # được UPDATE bảng con trỏ của chính nó.
    assert _called_with(store, "update") <= {"legacy_import", "order_line_current"}


def test_the_schema_makes_two_current_rows_for_one_key_impossible():
    table = schema.METADATA.tables["order_line_current"]
    assert [column.name for column in table.primary_key.columns] == [
        "order_key", "product_key", "occurrence_index",
    ]


def test_a_second_write_of_the_same_version_is_rejected_by_the_database(history_engine):
    """Hai transaction chen nhau cùng INSERT version 1 → cái sau bị chặn.

    Fail-safe bằng UNIQUE + transaction, không bằng distributed locking: race
    hiếm, và một lần 500 rồi chạy lại (ra SAME) rẻ hơn nhiều so với một khoá
    có hai version 1.
    """
    repository = history_store.SnapshotRepository(history_engine)
    write(repository, [source_line("BH1")], run_id="run-1", created_at="2026-02-01T00:00:00")
    with history_engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(schema.order_line_source_version.insert().values(
                origin="PIPELINE_GENERATED", order_key="BH1",
                product_key=keys.product_key("Tủ lạnh"), occurrence_index=1,
                version_no=1, snapshot_id=None, row_hash="h",
                line_fingerprint="f", created_at="2026-02-02T00:00:00",
            ))
    assert count(history_engine, schema.order_line_source_version) == 1


def test_a_failure_inside_the_unit_of_work_rolls_the_whole_snapshot_back(
    repository, history_engine,
):
    """R2 lỗi → KHÔNG có snapshot 'một nửa', không có run COMPLETE."""
    def explode():
        raise RuntimeError("R2 không khả dụng")

    with pytest.raises(RuntimeError):
        write(repository, [source_line("BH1"), source_line("BH2", row=7)],
              run_id="run-1", created_at="2026-02-01T00:00:00", on_persisted=explode)
    for name in PIPELINE_TABLES:
        assert count(history_engine, schema.METADATA.tables[name]) == 0, name


def test_a_database_error_is_reported_as_unavailable_not_as_empty_history(repository):
    repository.engine.dispose()
    broken = history_store.SnapshotRepository(create_engine("sqlite:///:memory:"))
    with pytest.raises(history_store.HistoryUnavailableError):
        broken.list_snapshots()


# --- đọc lại / truy vấn ---------------------------------------------------

def test_the_history_and_the_current_state_answer_two_different_questions(
    repository, history_engine,
):
    """Bằng chứng lịch sử KHÁC trạng thái hiện hành — đó là lý do có hai trục."""
    write(repository, [source_line("BH1", sell_price="8000000")],
          run_id="run-1", created_at="2026-02-01T00:00:00")
    write(repository, [source_line("BH1", sell_price="9000000")], run_id="run-2",
          created_at="2026-02-02T00:00:00", fingerprint="fp-b")
    assert count(history_engine, schema.order_line_source_version) == 2, "lịch sử: 2"
    assert repository.current_totals()["lines"] == 1, "hiện hành: 1"
    assert repository.current_totals()["total_sales"] == Decimal("9000000")


def test_current_totals_can_be_read_back_for_one_period_only(repository):
    write(repository, [
        source_line("BH1", sale_date=date(2026, 1, 5)),
        source_line("BH2", row=7, sale_date=date(2026, 2, 20)),
    ], run_id="run-1", created_at="2026-03-01T00:00:00")
    january = repository.current_totals(date_from=date(2026, 1, 1), date_to=date(2026, 1, 31))
    assert january == {"lines": 1, "orders": 1, "total_sales": Decimal("8000000")}


def test_a_fresh_repository_reads_the_same_state_back_from_the_database(history_engine):
    """Reload proof: trạng thái sống trong database, không trong tiến trình."""
    writer = history_store.SnapshotRepository(history_engine)
    write(writer, [source_line("BH1"), source_line("BH2", row=7)],
          run_id="run-1", created_at="2026-02-01T00:00:00")
    reader = history_store.SnapshotRepository(history_engine)
    assert reader.current_totals() == {
        "lines": 2, "orders": 2, "total_sales": Decimal("16000000"),
    }
    assert len(reader.current_fingerprints()) == 2
    assert len(reader.list_snapshots()) == 1


def test_run_ids_without_a_snapshot_are_reported_as_missing(repository):
    write(repository, [source_line("BH1")], run_id="run-1", created_at="2026-02-01T00:00:00")
    assert repository.run_ids_with_snapshot(["run-1", "run-ghost"]) == {"run-1"}


# --- PII ------------------------------------------------------------------

def test_no_pra002_table_declares_a_customer_column():
    """CHECK-PRA002-13: PII không có CHỖ để lọt vào, không chỉ là 'chưa lọt'."""
    for name in PIPELINE_TABLES:
        columns = set(schema.METADATA.tables[name].c.keys())
        assert PII_COLUMNS.isdisjoint(columns), f"{name}: {columns & PII_COLUMNS}"
