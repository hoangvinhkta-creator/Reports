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


def result_line(line: SourceLine, *, status="AUTO", purchase="5000000", kpi="3000000",
                price_source="TRACKING_PRICE_HISTORY"):
    return ResultLine(
        key=line.key, status=status, pending_reasons=() if status == "AUTO" else ("x",),
        total_sales=line.total_sales_raw, employee_normalized="VuHanhLy",
        employee_group="G1", lead_source_final="PERSONAL",
        identity_namespace="TRACKING", canonical_product_code="A1",
        accounting_purchase_price=Decimal(purchase), price_source=price_source,
        composition_rule="TRACKING_HISTORY_AUTHORITY",
        accounting_profit=Decimal("3000000"), kpi_purchase_price=Decimal(purchase),
        kpi_purchase_provenance="Config:NoConfirmedAdjustment",
        eligible_kpi_profit=Decimal(kpi), product_group_final="DIEN_MAY",
        conversion_scheme_final="S1", conversion_rate_final=Decimal("1"),
        result_fingerprint=keys.result_fingerprint(status, Decimal(purchase), Decimal(kpi)),
    )


def write(repository, lines, *, run_id, created_at, fingerprint="fp-a",
          header_text="Nhân viên: Tín Phát, Tháng 1 năm 2026", results=None,
          evidence=None, **kwargs):
    """``results``/``evidence`` cho phép chạy LẠI cùng một sổ với bằng chứng
    Tracking khác — đúng kịch bản mà RESULT_REVISED tồn tại để mô tả."""
    return repository.write_snapshot(
        run_id=run_id, created_at=created_at, source_file_name="so.xlsx",
        file_fingerprint=fingerprint, file_size=1024,
        header_text=header_text,
        sheet_data_rows=len(lines) + 1, rows_without_order_id=1,
        source_lines=lines,
        result_lines=results if results is not None else [result_line(line) for line in lines],
        evidence=evidence or {"tracking_catalog_capture_id": "cap-1"},
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


def test_uploading_again_after_a_collision_still_works(repository, history_engine):
    """Sau một cờ tranh chấp, mọi lần upload SAU vẫn phải chạy được.

    Bản ghi collision được lưu nhưng KHÔNG làm hiện hành, nên số version hiện
    hành tụt lại phía sau số version lớn nhất. Nếu version mới được đánh số
    theo hiện hành thay vì theo max (mục 5.3), lần upload kế tiếp sẽ đụng
    UNIQUE ``(khoá, version_no)`` và cả lần chạy bị rollback — Owner mất
    luôn báo cáo, không chỉ mất lịch sử.
    """
    far = date(2026, 1, 5) + timedelta(days=COLLISION_DAY_THRESHOLD + 1)
    write(repository, [source_line("BH1", sale_date=date(2026, 1, 5))],
          run_id="run-1", created_at="2026-02-01T00:00:00")
    write(repository, [source_line("BH1", sale_date=far)], run_id="run-2",
          created_at="2026-02-02T00:00:00", fingerprint="fp-b")

    # (a) nạp lại ĐÚNG file đã gây tranh chấp — thao tác bình thường của Owner.
    again = write(repository, [source_line("BH1", sale_date=far)], run_id="run-3",
                  created_at="2026-02-03T00:00:00", fingerprint="fp-b")
    assert again.counts["ORDER_KEY_COLLISION"] == 1
    # (b) kế toán sửa chính dòng đang hiện hành → vẫn lên version được.
    edited = write(repository, [source_line("BH1", sale_date=date(2026, 1, 5),
                                            sell_price="9000000")],
                   run_id="run-4", created_at="2026-02-04T00:00:00", fingerprint="fp-c")
    assert edited.counts["SOURCE_CHANGED"] == 1

    versions = [row["version_no"] for row in
                rows(history_engine, schema.order_line_source_version,
                     schema.order_line_source_version.c.id)]
    assert versions == [1, 2, 3, 4], "mỗi version một số riêng, không đánh trùng"
    current, = _current(repository)
    assert current["order_key_collision"] is True
    assert current["sale_date"] == date(2026, 1, 5), "hiện trạng vẫn là dòng không tranh chấp"
    assert repository.current_totals()["total_sales"] == Decimal("9000000")


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
    # `legacy_import` là bảng con trỏ của PRA-001 (`is_current`); PRA-002 được
    # UPDATE bảng con trỏ của chính nó, và — CHỈ TỪ SLICE B — các cột xác nhận
    # coverage trên `source_snapshot` (mục 4 của task cho phép đúng ngoại lệ
    # này). Ràng buộc hẹp hơn nằm ở hai test ngay dưới đây.
    assert _called_with(store, "update") <= {
        "legacy_import", "order_line_current", "source_snapshot",
    }


CONFIRM_COLUMNS = {
    "coverage_state", "confirmed_range_start", "confirmed_range_end",
    "confirmed_at", "n_removed_candidate",
}


def _function_named(tree: ast.AST, name: str) -> ast.FunctionDef:
    match, = [node for node in ast.walk(tree)
              if isinstance(node, ast.FunctionDef) and node.name == name]
    return match


def test_only_the_confirmation_function_updates_the_snapshot_row():
    """`source_snapshot` là bảng fact — chỉ cột xác nhận được sửa, chỉ ở một chỗ.

    Nới lỏng append-only là chỗ dễ trượt nhất của slice B: một `update(
    source_snapshot)` lọt vào đường ghi bình thường sẽ cho phép ghi đè lịch sử
    một lần chạy. Test đọc thẳng AST nên nó chặn được cả những lần sửa tương
    lai, không chỉ lần này.
    """
    store = REPO_ROOT / "app/web/history_store.py"
    # MỘT lần parse cho cả hai phép so: định danh node chỉ có nghĩa trong
    # cùng một cây AST.
    tree = ast.parse(store.read_text(encoding="utf-8"))
    confirm = _function_named(tree, "confirm_coverage")
    inside = {id(node) for node in ast.walk(confirm)}
    updates = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "update" and node.args
        and getattr(node.args[0], "id", None) == "source_snapshot"
    ]
    assert updates, "phải có đúng đường ghi xác nhận"
    assert all(id(node) in inside for node in updates), (
        "chỉ `confirm_coverage` được UPDATE source_snapshot"
    )
    written = {
        keyword.arg
        for node in ast.walk(confirm)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "values"
        for keyword in node.keywords
    }
    assert written == CONFIRM_COLUMNS, "không cột nào khác của snapshot được sửa"


def test_confirmed_complete_is_written_by_exactly_one_function():
    """CHECK-PRA002-06 tĩnh: `CONFIRMED_COMPLETE` chỉ ra khỏi một cửa.

    Toàn bộ `app/` chỉ có MỘT nơi gán giá trị đó cho `coverage_state`, và nơi
    đó là hàm repository do route xác nhận gọi. Nếu một route/aut path thứ hai
    xuất hiện, test này đỏ trước khi dữ liệu sai kịp sinh ra.
    """
    writers = set()
    for path in sorted((REPO_ROOT / "app").rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "values"):
                continue
            for keyword in node.keywords:
                if keyword.arg != "coverage_state":
                    continue
                source = ast.unparse(keyword.value)
                if "CONFIRMED_COMPLETE" in source:
                    writers.add(path.relative_to(REPO_ROOT).as_posix())
    assert writers == {"app/web/history_store.py"}


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


# --- RESULT_REVISED vertical (slice C1) -----------------------------------
#
# Bất biến sống hay chết của slice C1: kết quả đổi KHÔNG được giả vờ là nguồn
# đổi. Các test dưới đây hỏi thẳng database — số source version, số result
# version, hai con trỏ hiện hành, và bản ghi cũ có còn nguyên vẹn không.

def revised(line, **overrides):
    """Cùng khoá, cùng nguồn — chỉ khác kết quả pipeline."""
    return result_line(line, **overrides)


def flags_of(engine, kind):
    return [row for row in rows(engine, schema.reconciliation_flag, "id")
            if row["kind"] == kind]


def test_rerunning_the_same_source_with_a_changed_result_revises_without_touching_source(
        repository, history_engine):
    lines = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, lines, run_id="run-1", created_at="2026-02-01T00:00:00")
    before = rows(history_engine, schema.order_line_current, "order_key")

    outcome = write(
        repository, lines, run_id="run-2", created_at="2026-02-02T00:00:00",
        results=[revised(lines[0], purchase="5100000"), result_line(lines[1])],
    )

    # Nguồn KHÔNG đổi: cùng số source version, cùng con trỏ nguồn, 0 SOURCE_CHANGED.
    assert outcome.counts["SAME"] == 2
    assert outcome.counts["SOURCE_CHANGED"] == 0
    assert count(history_engine, schema.order_line_source_version) == 2
    snapshots = rows(history_engine, schema.source_snapshot, "created_at")
    assert snapshots[1]["n_source_changed"] == 0
    assert snapshots[1]["n_result_revised"] == 1

    # Kết quả: mỗi khoá vẫn có result version mới (hợp đồng SAME của slice A).
    assert count(history_engine, schema.order_line_result_version) == 4

    after = rows(history_engine, schema.order_line_current, "order_key")
    for old, new in zip(before, after):
        assert old["current_source_version_id"] == new["current_source_version_id"]
    assert after[0]["current_result_version_id"] != before[0]["current_result_version_id"]
    assert after[1]["current_result_version_id"] != before[1]["current_result_version_id"]

    # Đúng MỘT cờ, trên đúng khoá đã đổi.
    flag, = flags_of(history_engine, "RESULT_REVISED")
    assert flag["order_key"] == "BH1"
    assert ast.literal_eval(flag["detail_json"]) == {
        "accounting_purchase_price": {"old": "5000000", "new": "5100000"},
    }


def test_a_result_revision_flag_points_at_result_versions_not_source_versions(
        repository, history_engine):
    line = source_line("BH1")
    write(repository, [line], run_id="run-1", created_at="2026-02-01T00:00:00")
    first = rows(history_engine, schema.order_line_result_version, "id")[0]

    write(repository, [line], run_id="run-2", created_at="2026-02-02T00:00:00",
          results=[revised(line, status="PENDING")])

    second = rows(history_engine, schema.order_line_result_version, "id")[1]
    flag, = flags_of(history_engine, "RESULT_REVISED")
    assert (flag["from_version_id"], flag["to_version_id"]) == (first["id"], second["id"])

    # Bản cũ còn NGUYÊN VẸN, và con trỏ hiện hành đã sang bản mới.
    assert first["status"] == "AUTO"
    assert second["status"] == "PENDING"
    current, = rows(history_engine, schema.order_line_current)
    assert current["current_result_version_id"] == second["id"]
    source_version, = rows(history_engine, schema.order_line_source_version)
    assert current["current_source_version_id"] == source_version["id"]
    assert source_version["version_no"] == 1


def test_rerunning_with_an_identical_result_still_writes_a_version_but_raises_no_flag(
        repository, history_engine):
    line = source_line("BH1")
    write(repository, [line], run_id="run-1", created_at="2026-02-01T00:00:00")
    write(repository, [line], run_id="run-2", created_at="2026-02-02T00:00:00")

    assert count(history_engine, schema.order_line_result_version) == 2
    assert count(history_engine, schema.order_line_source_version) == 1
    assert flags_of(history_engine, "RESULT_REVISED") == []
    assert rows(history_engine, schema.source_snapshot, "created_at")[1]["n_result_revised"] == 0


def test_a_changed_source_reports_source_changed_and_no_result_revision(
        repository, history_engine):
    line = source_line("BH1", sell_price="8000000")
    write(repository, [line], run_id="run-1", created_at="2026-02-01T00:00:00")

    moved = source_line("BH1", sell_price="8500000")
    write(repository, [moved], run_id="run-2", created_at="2026-02-02T00:00:00",
          fingerprint="fp-b", results=[revised(moved, purchase="5100000")])

    assert count(history_engine, schema.order_line_source_version) == 2
    snapshot = rows(history_engine, schema.source_snapshot, "created_at")[1]
    assert (snapshot["n_source_changed"], snapshot["n_result_revised"]) == (1, 0)
    assert len(flags_of(history_engine, "SOURCE_CHANGED")) == 1
    assert flags_of(history_engine, "RESULT_REVISED") == []


def test_a_collision_raises_no_result_revision_and_leaves_the_current_result_alone(
        repository, history_engine):
    line = source_line("BH1", sale_date=date(2026, 1, 5))
    write(repository, [line], run_id="run-1", created_at="2026-02-01T00:00:00")
    before, = rows(history_engine, schema.order_line_current)

    far = source_line("BH1", sale_date=date(2026, 1, 5) + timedelta(
        days=COLLISION_DAY_THRESHOLD + 1))
    write(repository, [far], run_id="run-2", created_at="2026-02-02T00:00:00",
          fingerprint="fp-b", results=[revised(far, purchase="5100000")])

    assert flags_of(history_engine, "RESULT_REVISED") == []
    assert rows(history_engine, schema.source_snapshot, "created_at")[1]["n_result_revised"] == 0
    # Khoá tranh chấp: KHÔNG ghi result version, con trỏ kết quả giữ nguyên.
    assert count(history_engine, schema.order_line_result_version) == 1
    after, = rows(history_engine, schema.order_line_current)
    assert after["current_result_version_id"] == before["current_result_version_id"]
    assert after["current_source_version_id"] == before["current_source_version_id"]


def test_a_change_outside_the_three_fingerprint_fields_writes_a_version_without_a_flag(
        repository, history_engine):
    line = source_line("BH1")
    write(repository, [line], run_id="run-1", created_at="2026-02-01T00:00:00")

    write(repository, [line], run_id="run-2", created_at="2026-02-02T00:00:00",
          results=[revised(line, price_source="CONFIRMED_ADJUSTMENT")])

    versions = rows(history_engine, schema.order_line_result_version, "id")
    assert len(versions) == 2
    assert versions[1]["price_source"] == "CONFIRMED_ADJUSTMENT"
    assert versions[1]["result_fingerprint"] == versions[0]["result_fingerprint"]
    assert flags_of(history_engine, "RESULT_REVISED") == []


def test_the_revision_counter_matches_the_number_of_revised_lines_in_the_run(
        repository, history_engine):
    lines = [source_line(f"BH{n}", row=5 + n) for n in range(1, 5)]
    write(repository, lines, run_id="run-1", created_at="2026-02-01T00:00:00")

    write(repository, lines, run_id="run-2", created_at="2026-02-02T00:00:00", results=[
        revised(lines[0], status="PENDING"),
        revised(lines[1], purchase="5100000"),
        revised(lines[2], kpi="2900000"),
        result_line(lines[3]),
    ])

    assert rows(history_engine, schema.source_snapshot, "created_at")[1]["n_result_revised"] == 3
    assert {f["order_key"] for f in flags_of(history_engine, "RESULT_REVISED")} == {
        "BH1", "BH2", "BH3",
    }


def test_a_failure_after_detection_leaves_no_partial_result_revision(
        repository, history_engine):
    """Cùng một transaction: cờ, result version và con trỏ cùng sống hoặc cùng chết."""
    line = source_line("BH1")
    write(repository, [line], run_id="run-1", created_at="2026-02-01T00:00:00")
    before, = rows(history_engine, schema.order_line_current)

    def boom():
        raise RuntimeError("R2 down")

    with pytest.raises(RuntimeError):
        write(repository, [line], run_id="run-2", created_at="2026-02-02T00:00:00",
              results=[revised(line, purchase="5100000")], on_persisted=boom)

    assert count(history_engine, schema.source_snapshot) == 1
    assert count(history_engine, schema.order_line_result_version) == 1
    assert flags_of(history_engine, "RESULT_REVISED") == []
    assert rows(history_engine, schema.order_line_current) == [before]


def test_absence_keys_never_produce_a_result_revision(repository, history_engine):
    """Slice B an toàn: khoá VẮNG MẶT không có kết quả mới, nên không có gì để sửa."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")

    write(repository, [both[0]], run_id="run-2", created_at="2026-02-02T00:00:00",
          fingerprint="fp-b", results=[revised(both[0], purchase="5100000")])

    assert len(flags_of(history_engine, "NOT_SEEN_IN_LATEST_SNAPSHOT")) == 1
    revisions = flags_of(history_engine, "RESULT_REVISED")
    assert [f["order_key"] for f in revisions] == ["BH1"]
    assert rows(history_engine, schema.source_snapshot, "created_at")[1]["n_result_revised"] == 1


def test_two_captures_of_the_same_workbook_revise_results_without_a_source_conflict(
        repository, history_engine):
    """Vertical hai lần capture: cùng sổ, bằng chứng Tracking khác nhau.

    Đây là hình chiếu ở tầng persistence của CHECK-PRA002-08: cùng
    ``file_fingerprint`` (đúng một sổ), hai ``tracking_catalog_capture_id``
    khác nhau, một dòng PENDING → AUTO. Không dựng tooling mới — chỉ dùng
    đúng các object đã có.
    """
    lines = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, lines, run_id="run-1", created_at="2026-02-01T00:00:00",
          fingerprint="fp-book", evidence={"tracking_catalog_capture_id": "cap-A"},
          results=[result_line(lines[0], status="PENDING"), result_line(lines[1])])
    before = rows(history_engine, schema.order_line_current, "order_key")

    outcome = write(
        repository, lines, run_id="run-2", created_at="2026-02-02T00:00:00",
        fingerprint="fp-book", evidence={"tracking_catalog_capture_id": "cap-B"},
        results=[result_line(lines[0], status="AUTO"), result_line(lines[1])],
    )

    # Cùng sổ → snapshot thứ hai là bản trùng của bản đầu, KHÔNG phải sổ mới.
    assert outcome.duplicate_of_snapshot_id is not None
    snapshot = rows(history_engine, schema.source_snapshot, "created_at")[1]
    assert (snapshot["n_source_changed"], snapshot["n_result_revised"]) == (0, 1)
    assert count(history_engine, schema.order_line_source_version) == 2

    after = rows(history_engine, schema.order_line_current, "order_key")
    assert [r["current_source_version_id"] for r in after] == [
        r["current_source_version_id"] for r in before
    ]
    assert after[0]["current_result_version_id"] != before[0]["current_result_version_id"]

    flag, = flags_of(history_engine, "RESULT_REVISED")
    assert ast.literal_eval(flag["detail_json"]) == {
        "status": {"old": "PENDING", "new": "AUTO"},
    }
