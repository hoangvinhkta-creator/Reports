"""TASK-PRA-002 — khoá, fingerprint, coverage: tầng thuần của `app/history`.

Điều cần chứng minh ở đây không phải "hàm chạy được" mà là: cùng một dòng bán
LUÔN ra cùng một khoá và cùng một fingerprint qua nhiều lần export, và những
thứ KHÔNG phải nội dung nghiệp vụ (PII, vị trí dòng, định dạng số) KHÔNG được
làm fingerprint đổi. Sai ở đây = một dòng bị đếm hai lần hoặc một lần sửa của
kế toán bị bỏ qua.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.history import coverage, extraction, keys
from app.history.models import COVERAGE_STATES, FLAG_KINDS_ALL, OUTCOMES_ALL
from tools.db import schema

REPO_ROOT = Path(__file__).resolve().parents[1]


def raw(**overrides):
    base = dict(
        source_file="s.xlsx", source_sheet="Sheet1", source_row=6, row_hash="h",
        date=date(2026, 1, 5), order_id="BH1", note_raw=None, product_raw="Tủ lạnh",
        customer_code="KH1", customer="Nguyễn Văn A", address="1 Lê Lợi",
        phone="0900000000", quantity=Decimal("1"), sell_price=Decimal("8000000"),
        total_sales_raw=Decimal("8000000"), discount=Decimal("0"),
        employee_raw="Vũ Hạnh Ly", shipper_raw="Shipper X",
        delivery_cost=None, imei=None, source_profit=Decimal("500000"),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def presented(**overrides):
    """`PresentedLine` giả lập ở mức thuộc tính — extraction chỉ đọc, không import."""
    row = raw(**{k: v for k, v in overrides.items() if k in raw().__dict__})
    line = SimpleNamespace(
        raw=row, order_id=row.order_id, total_sales=row.total_sales_raw,
        employee_normalized="VuHanhLy", employee_group="G1", lead_source_final="PERSONAL",
        accounting_purchase_price=None, price_source="Pending", accounting_profit=None,
        kpi_purchase_price=None, kpi_purchase_price_provenance="Pending",
        eligible_kpi_profit=None, product_group_final="DIEN_MAY",
        conversion_scheme_final=None, conversion_rate_final=None,
    )
    return SimpleNamespace(line=line, record=None, reasons=("Pending.x",),
                           details=(), status="PENDING")


def fingerprint_of(row) -> str:
    return keys.line_fingerprint((
        row.date, row.product_raw, row.quantity, row.sell_price, row.discount,
        row.total_sales_raw, row.delivery_cost, row.imei, row.note_raw,
        row.employee_raw, row.source_profit,
    ))


# --- canon / fingerprint --------------------------------------------------

@pytest.mark.parametrize("value", ["1000", "1000.0", "1000.00", "1E+3"])
def test_equal_decimals_canonicalise_to_one_string(value):
    """Một lần export khác định dạng số KHÔNG phải là 'kế toán đã sửa dòng này'."""
    assert keys.canon(Decimal(value)) == "1000"


def test_canon_keeps_a_real_difference_visible():
    assert keys.canon(Decimal("1000.5")) != keys.canon(Decimal("1000"))


def test_canon_of_missing_value_is_empty_and_not_zero():
    """`None` (chưa có) và `0` (bằng không) là hai sự thật khác nhau."""
    assert keys.canon(None) == ""
    assert keys.canon(Decimal("0")) == "0"


def test_same_source_row_gives_the_same_fingerprint_every_time():
    assert fingerprint_of(raw()) == fingerprint_of(raw())


@pytest.mark.parametrize("field,value", [
    ("customer", "Trần Thị B"), ("customer_code", "KH999"), ("phone", "0911111111"),
    ("address", "9 Trần Phú"), ("shipper_raw", "Shipper Y"), ("source_row", 99),
    ("row_hash", "khác"), ("source_file", "khac.xlsx"),
])
def test_pii_and_row_position_never_change_the_fingerprint(field, value):
    """Đổi tên khách hay chèn thêm dòng phía trên KHÔNG phải là sửa dòng bán."""
    assert fingerprint_of(raw(**{field: value})) == fingerprint_of(raw())


@pytest.mark.parametrize("field,value", [
    ("date", date(2026, 1, 6)), ("product_raw", "Máy giặt"), ("quantity", Decimal("2")),
    ("sell_price", Decimal("9000000")), ("discount", Decimal("100000")),
    ("total_sales_raw", Decimal("9000000")), ("delivery_cost", Decimal("50000")),
    ("imei", "IMEI-1"), ("note_raw", "ghi chú"), ("employee_raw", "Người khác"),
    ("source_profit", Decimal("600000")),
])
def test_every_business_field_changes_the_fingerprint(field, value):
    assert fingerprint_of(raw(**{field: value})) != fingerprint_of(raw())


def test_fingerprint_field_list_matches_what_the_test_feeds_it():
    assert len(keys.FINGERPRINT_FIELDS) == 11
    assert "customer" not in keys.FINGERPRINT_FIELDS
    assert "source_row" not in keys.FINGERPRINT_FIELDS


def test_changed_fields_names_both_the_old_and_the_new_value():
    before = fingerprint_values(raw())
    after = fingerprint_values(raw(sell_price=Decimal("9000000")))
    assert keys.changed_fields(before, after) == {
        "sell_price": {"old": "8000000", "new": "9000000"}
    }


def fingerprint_values(row):
    return (row.date, row.product_raw, row.quantity, row.sell_price, row.discount,
            row.total_sales_raw, row.delivery_cost, row.imei, row.note_raw,
            row.employee_raw, row.source_profit)


# --- product_key / bh -----------------------------------------------------

def test_product_key_is_stable_and_treats_missing_name_as_empty_string():
    assert keys.product_key("Tủ lạnh") == keys.product_key("  Tủ lạnh  ")
    assert keys.product_key(None) == keys.product_key("")


def test_product_key_does_not_fold_case():
    """D9 DEFER: gộp hoa/thường là một quyết định nghiệp vụ chưa có bằng chứng."""
    assert keys.product_key("Tủ Lạnh") != keys.product_key("tủ lạnh")


def test_bh_parts_reads_the_number_only_from_the_known_shape():
    assert keys.bh_parts("BH62063", date(2026, 1, 5)) == (62063, 2026)
    assert keys.bh_parts("BH-62063", date(2026, 1, 5)) == (None, 2026)
    assert keys.bh_parts("BH62063", None) == (62063, None)


# --- occurrence_index -----------------------------------------------------

def test_two_lines_of_the_same_product_in_one_order_get_distinct_keys():
    """Dữ liệu thật có đơn lặp một mặt hàng; thiếu occurrence_index là mất dòng."""
    lines = extraction.build_source_lines([
        presented(source_row=8, product_raw="Chi phí vận chuyển"),
        presented(source_row=6, product_raw="Chi phí vận chuyển"),
    ])
    assert [line.key.occurrence_index for line in lines] == [1, 2]
    assert [line.source_row for line in lines] == [6, 8]
    assert len({line.key for line in lines}) == 2


def test_occurrence_index_follows_source_row_not_input_order():
    lines = extraction.build_source_lines([
        presented(source_row=20, product_raw="A"), presented(source_row=7, product_raw="A"),
    ])
    assert lines[0].source_row == 7 and lines[0].key.occurrence_index == 1


def test_extraction_never_carries_pii_out_of_the_pipeline():
    line = extraction.build_source_lines([presented()])[0]
    text = repr(line)
    for secret in ("Nguyễn Văn A", "0900000000", "1 Lê Lợi", "KH1", "Shipper X"):
        assert secret not in text


# --- coverage -------------------------------------------------------------

def test_header_form_one_is_the_production_date_range():
    assert coverage.parse_header("Từ ngày 01/09/2026 đến ngày 10/09/2026") == (
        date(2026, 9, 1), date(2026, 9, 10)
    )


def test_header_form_two_is_the_monthly_export_and_spans_the_whole_month():
    assert coverage.parse_header("Nhân viên: Tín Phát 0869931931, Tháng 1 năm 2026") == (
        date(2026, 1, 1), date(2026, 1, 31)
    )


@pytest.mark.parametrize("text", [
    None, "", "Báo cáo tháng", "Từ ngày 1/9/2026 đến ngày 10/9/2026",
    "Nhân viên: X, Quý 1 năm 2026", "Từ ngày 31/02/2026 đến ngày 10/09/2026",
])
def test_an_unknown_header_shape_is_never_guessed(text):
    """Dạng thứ ba xuất hiện → không đoán; nới regex là escalation, không phải fix."""
    assert coverage.parse_header(text) is None


def test_coverage_is_header_consistent_only_when_the_header_covers_the_data():
    detected = (date(2026, 1, 2), date(2026, 1, 31))
    assert coverage.coverage_state((date(2026, 1, 1), date(2026, 1, 31)), detected) == (
        coverage.HEADER_CONSISTENT
    )
    assert coverage.coverage_state((date(2026, 1, 1), date(2026, 1, 10)), detected) == (
        coverage.DETECTED_ONLY
    )
    assert coverage.coverage_state(None, detected) == coverage.DETECTED_ONLY


def test_detected_range_ignores_lines_without_a_date_instead_of_inventing_one():
    assert coverage.detected_range([None, date(2026, 1, 5), None, date(2026, 1, 2)]) == (
        date(2026, 1, 2), date(2026, 1, 5)
    )
    assert coverage.detected_range([None]) == (None, None)


def test_scanning_the_golden_workbook_counts_rows_independently_of_the_reader():
    """`sheet_data_rows`/`rows_without_order_id` phải đếm ĐỘC LẬP với read_raw_rows —
    nếu không, "bao nhiêu dòng bị bỏ" là con số do chính bên bỏ dòng tự khai."""
    header, data_rows, missing = coverage.scan_sheet(
        REPO_ROOT / "tests/fixtures/golden/period_2026_01.xlsx"
    )
    assert header == "Nhân viên: Tín Phát 0869931931, Tháng 1 năm 2026"
    assert (data_rows, missing) == (352, 1)


def test_nothing_in_the_pure_history_layer_reaches_for_a_database_or_a_framework():
    """ADR-101 / CHECK-PRA002-12: `app/history` là tầng thuần."""
    banned = ("sqlalchemy", "psycopg", "alembic", "flask")
    for path in (REPO_ROOT / "app" / "history").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for name in banned:
            assert f"import {name}" not in text, f"{path}: {name}"
            assert f"from {name}" not in text, f"{path}: {name}"


def test_the_pure_vocabulary_and_the_ddl_check_constraints_stay_in_step():
    """Hai khai báo, một sự thật: test này là thứ buộc chúng không trôi khỏi nhau."""
    assert COVERAGE_STATES == schema.COVERAGE_STATES
    assert OUTCOMES_ALL == schema.OUTCOMES
    assert FLAG_KINDS_ALL == schema.FLAG_KINDS
