from __future__ import annotations

from datetime import date

from app.modules.importing.raw_reader import read_raw_rows


def test_reads_correct_row_and_order_count(synthetic_raw_path):
    rows = read_raw_rows(synthetic_raw_path)
    # BH0001(1) + BH0002(2) + BH0003(1) + BH0004(1) + BH0005(1) + BH0006(1) + BH0007(1)
    assert len(rows) == 8
    assert len({row.order_id for row in rows}) == 7


def test_skips_secondary_header_row(synthetic_raw_path):
    # Row 5 ("Diễn giải chung") has no OrderID and must never appear as data.
    rows = read_raw_rows(synthetic_raw_path)
    assert all(row.order_id for row in rows)
    assert min(row.source_row for row in rows) == 6


def test_parses_date_as_date_object(synthetic_raw_path):
    rows = read_raw_rows(synthetic_raw_path)
    first = next(row for row in rows if row.order_id == "BH0001")
    assert first.date == date(2026, 1, 15)


def test_missing_quantity_stays_none_not_zero(synthetic_raw_path):
    rows = read_raw_rows(synthetic_raw_path)
    row = next(row for row in rows if row.order_id == "BH0007")
    assert row.quantity is None


def test_source_provenance_recorded(synthetic_raw_path):
    rows = read_raw_rows(synthetic_raw_path)
    row = next(row for row in rows if row.order_id == "BH0001")
    assert row.source_file == synthetic_raw_path.name
    assert row.source_sheet == "SỔ CHI TIẾT BÁN HÀNG"
    assert row.row_hash
