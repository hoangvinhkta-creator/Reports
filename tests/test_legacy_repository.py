"""LegacyRepository (TASK-PRA-001.3): khứ hồi đúng số, versioning, fail rõ.

Trọng tâm: giá trị đi qua database KHÔNG được đổi (kể cả phần thập phân của
một con số vốn đã sai), và lỗi kết nối KHÔNG được biến thành "chưa có dữ liệu".
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text

from app.legacy import parse_workbook
from app.web import history_store
from tools.db import schema


@pytest.fixture
def workbook(legacy_workbook_path):
    return parse_workbook(legacy_workbook_path)


def test_import_round_trips_every_summary_value_exactly(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    stored = {
        (row["sheet_name"], row["sheet_row"]): row
        for row in legacy_repository.query_summary(2026)
    }
    for source in workbook.summary_rows:
        if source.year != 2026:
            continue
        row = stored[(source.sheet_name, source.sheet_row)]
        for field, value in source.values.items():
            assert row[field] == value, f"{source.sheet_row}.{field}"


def test_a_non_integer_value_survives_the_database_unchanged(legacy_repository, workbook):
    """SQLite không có kiểu thập phân thật — 87,6 vẫn phải ra đúng 87,6."""
    legacy_repository.create_import(workbook)
    row = next(r for r in legacy_repository.query_summary(2026, 1) if r["sheet_row"] == 5)
    assert row["products"] == Decimal("87.6")


def test_a_value_contradicting_its_formula_survives_the_database(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    row = next(r for r in legacy_repository.query_summary(2026, 2) if r["sheet_row"] == 9)
    assert row["converted_revenue"] == Decimal("999")
    assert row["formula_text"]["F"] == "=G9/5.5%"


def test_known_defects_survive_as_structured_data(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    row = next(r for r in legacy_repository.query_summary(2026, 2) if r["sheet_row"] == 10)
    assert row["known_defects"]["D"] == ["A4"]


def test_every_stored_row_carries_the_legacy_origin(legacy_repository, workbook, history_engine):
    legacy_repository.create_import(workbook)
    with history_engine.connect() as connection:
        for table in ("legacy_summary_row", "legacy_daily_sales", "legacy_monthly_reference"):
            origins = {
                value for (value,) in connection.execute(text(f"SELECT origin FROM {table}"))
            }
            assert origins == {schema.ORIGIN_LEGACY}, table


def test_the_origin_check_constraint_rejects_a_foreign_origin(history_engine):
    with pytest.raises(Exception):
        with history_engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO legacy_import (import_id, origin, file_fingerprint, is_current)"
                " VALUES ('X', 'PIPELINE_GENERATED', 'f', 0)"
            ))


def test_reimporting_the_same_file_does_not_create_a_second_version(legacy_repository, workbook):
    first = legacy_repository.create_import(workbook)
    second = legacy_repository.create_import(workbook)
    assert first.created is True
    assert second == history_store.ImportResult(import_id=first.import_id, created=False)
    assert legacy_repository.count_imports() == 1


def test_a_second_distinct_file_becomes_the_current_version(legacy_repository, workbook, tmp_path):
    from tests.fixtures.legacy.build_legacy_workbook import build_legacy_workbook

    first = legacy_repository.create_import(workbook)
    other = parse_workbook(build_legacy_workbook(tmp_path / "ban_moi.xlsx"))
    object.__setattr__(other, "file_fingerprint", "fingerprint-khac")
    second = legacy_repository.create_import(other, version_label="bản mới")

    imports = {item["import_id"]: item for item in legacy_repository.list_imports()}
    assert len(imports) == 2
    assert imports[second.import_id]["is_current"] is True
    assert imports[first.import_id]["is_current"] is False
    assert legacy_repository.current_import()["version_label"] == "bản mới"


def test_choosing_an_older_version_switches_exactly_one_current(legacy_repository, workbook, tmp_path):
    from tests.fixtures.legacy.build_legacy_workbook import build_legacy_workbook

    first = legacy_repository.create_import(workbook)
    other = parse_workbook(build_legacy_workbook(tmp_path / "ban_moi.xlsx"))
    object.__setattr__(other, "file_fingerprint", "fingerprint-khac")
    legacy_repository.create_import(other)

    legacy_repository.set_current(first.import_id)
    current = [i for i in legacy_repository.list_imports() if i["is_current"]]
    assert [item["import_id"] for item in current] == [first.import_id]


def test_choosing_an_unknown_version_is_rejected(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    with pytest.raises(KeyError):
        legacy_repository.set_current("LEG-khong-ton-tai")


def test_query_by_month_returns_only_that_month(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    rows = legacy_repository.query_summary(2026, 2)
    assert {row["month"] for row in rows} == {2}
    assert [row["seller_label"] for row in rows] == [
        "NV-A", "NV-B", "Kênh-1", "NV-C", "Tổng T02"]


def test_query_by_year_includes_the_year_level_row(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    kinds = {row["row_kind"] for row in legacy_repository.query_summary(2026)}
    assert "YEAR_TOTAL" in kinds


def test_a_period_with_no_data_returns_an_empty_list_not_zeros(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    assert legacy_repository.query_summary(2019, 5) == []
    assert legacy_repository.query_daily(2019, 5) == []


def test_available_periods_lists_only_periods_that_exist(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    assert legacy_repository.available_periods() == [
        (2026, 3), (2026, 2), (2026, 1), (2025, 1)]


def test_queries_read_the_current_version_by_default(legacy_repository, workbook, tmp_path):
    from tests.fixtures.legacy.build_legacy_workbook import build_legacy_workbook

    first = legacy_repository.create_import(workbook)
    other = parse_workbook(build_legacy_workbook(tmp_path / "ban_moi.xlsx"))
    object.__setattr__(other, "file_fingerprint", "fingerprint-khac")
    second = legacy_repository.create_import(other)

    rows = legacy_repository.query_summary(2026, 1)
    assert {row["import_id"] for row in rows} == {second.import_id}
    pinned = legacy_repository.query_summary(2026, 1, import_id=first.import_id)
    assert {row["import_id"] for row in pinned} == {first.import_id}


def test_daily_rows_keep_vnd_and_their_source_sheet(legacy_repository, workbook):
    legacy_repository.create_import(workbook)
    rows = legacy_repository.query_daily(2026, 1)
    assert [(row["day"], row["sales_vnd"]) for row in rows] == [
        (1, Decimal("820000000")), (2, Decimal("910000000")), (3, Decimal("1050000000"))]
    assert {row["source_sheet"] for row in rows} == {"DataChart 2026"}


def test_no_legacy_table_stores_customer_personal_data():
    """PII của khách hàng KHÔNG được nhập (governance/product/17)."""
    banned = ("customer", "phone", "address", "khach", "dien_thoai", "dia_chi")
    for table in schema.METADATA.tables.values():
        for column in table.c:
            assert not any(word in column.name.lower() for word in banned), column.name


def test_a_broken_database_raises_unavailable_not_an_empty_result(legacy_repository, workbook):
    """Mất kết nối phải trả lỗi rõ — trang rỗng vì lỗi trông y hệt trang rỗng
    vì chưa nhập gì, và Owner sẽ đọc nhầm."""
    legacy_repository.create_import(workbook)
    broken = history_store.LegacyRepository(create_engine("sqlite://"))
    with pytest.raises(history_store.HistoryUnavailableError):
        broken.list_imports()


def test_build_refuses_an_unmigrated_database():
    with pytest.raises(Exception):
        history_store.build(engine=create_engine("sqlite://"))


def test_build_can_skip_schema_verification_for_dev_tools():
    repository = history_store.build(
        engine=create_engine("sqlite://"), verify_schema=False,
    )
    assert isinstance(repository, history_store.LegacyRepository)


# --- Script đối chiếu ô (CHECK-PRA001-01) ---------------------------------

def test_the_cell_by_cell_verifier_reports_zero_mismatches(
    legacy_repository, legacy_workbook_path,
):
    """Chính script mà Owner sẽ chạy trên file thật, chạy trên fixture."""
    from tools.analysis.verify_legacy_import import verify

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    matched, mismatches = verify(legacy_workbook_path, legacy_repository)
    assert mismatches == []
    assert matched > 500


def test_the_verifier_detects_a_value_that_drifted_from_the_source(
    legacy_repository, legacy_workbook_path, history_engine,
):
    """Nếu một ngày nào đó có đường code sửa số cũ, script phải kêu lên."""
    from sqlalchemy import text

    from tools.analysis.verify_legacy_import import verify

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    with history_engine.begin() as connection:
        connection.execute(text(
            "UPDATE legacy_summary_row SET sales = '1' WHERE sheet_row = 4"
        ))
    _, mismatches = verify(legacy_workbook_path, legacy_repository)
    assert any("E4" in line for line in mismatches)
