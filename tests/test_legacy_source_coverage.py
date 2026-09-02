"""Repair FIND-PRA001-R01 — dòng nguồn bị bỏ qua phải FAIL TO, không im lặng.

Independent Review chứng minh một lỗ hổng thật: verifier duyệt từ DB → Excel
nên nó chỉ trả lời được "những gì ĐÃ nhập có đúng không", không bao giờ trả
lời được "có gì chưa được nhập không". Hệ quả: mất trọn `Summary 2025` mà
vẫn in `matched=372 mismatched=0`.

Chính sách Owner (DEC-168) áp dụng ở đây:

    dòng nguồn có giá trị nghiệp vụ
        → contract phân loại nhận ra?  ── CÓ ─→ nhập
                                       └─ KHÔNG ─→ FAIL TO

Không đoán `row_kind` từ việc "dòng có số". Không tự mở rộng semantics.
"""

from __future__ import annotations

import pytest

from app.legacy import LegacyImportError, parse_workbook
from tests.fixtures.legacy.build_legacy_workbook import (
    build_legacy_workbook, strip_formula_markers,
)
from tools.analysis.verify_legacy_import import verify


@pytest.fixture
def workbook_without_formula_markers(tmp_path):
    """Đúng case reviewer: giữ giá trị nghiệp vụ, bỏ dấu hiệu công thức."""
    return strip_formula_markers(build_legacy_workbook(tmp_path / "mat_formula.xlsx"))


# --- Parser: FAIL TO, không bỏ qua im lặng --------------------------------

def test_a_summary_sheet_that_would_import_nothing_fails_loudly(
    workbook_without_formula_markers,
):
    with pytest.raises(LegacyImportError) as exc:
        parse_workbook(workbook_without_formula_markers)
    message = str(exc.value)
    assert "Summary 2025" in message
    assert "OWNER_DECISION_REQUIRED" in message


def test_the_error_names_the_exact_unaccounted_source_rows(
    workbook_without_formula_markers,
):
    """Owner phải biết DÒNG NÀO, không chỉ 'có gì đó sai'."""
    with pytest.raises(LegacyImportError) as exc:
        parse_workbook(workbook_without_formula_markers)
    message = str(exc.value)
    assert "3 dòng" in message
    for row in ("4", "5", "6"):
        assert row in message


def test_a_single_unaccounted_row_also_fails_not_just_a_whole_sheet(
    legacy_workbook_path,
):
    """Mất MỘT dòng cũng là mất số của Owner — không có ngưỡng dung thứ."""
    from openpyxl import load_workbook

    workbook = load_workbook(legacy_workbook_path, data_only=False)
    sheet = workbook["Summary 2026"]
    for column in ("C", "D", "E", "F", "G", "H", "I", "J", "K"):
        cell = sheet[f"{column}4"]
        if isinstance(cell.value, str) and cell.value.startswith("="):
            cell.value = 1234
    workbook.save(legacy_workbook_path)

    with pytest.raises(LegacyImportError) as exc:
        parse_workbook(legacy_workbook_path)
    assert "Summary 2026" in str(exc.value)


def test_the_parser_never_guesses_a_row_kind_from_numbers_alone(
    workbook_without_formula_markers,
):
    """Chính sách Owner: không suy business semantics chỉ vì dòng có số."""
    with pytest.raises(LegacyImportError):
        parse_workbook(workbook_without_formula_markers)


def test_a_well_formed_workbook_still_imports_with_no_unaccounted_rows(
    legacy_workbook_path,
):
    """Guard KHÔNG được biến thành báo động giả trên workbook đúng hình dạng."""
    workbook = parse_workbook(legacy_workbook_path)
    assert len([r for r in workbook.summary_rows if r.sheet_name == "Summary 2025"]) == 3
    assert len(workbook.summary_rows) == 16


# --- Verifier: coverage từ phía Excel -------------------------------------

def test_the_verifier_reports_source_coverage_counts(
    legacy_repository, legacy_workbook_path,
):
    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    result = verify(legacy_workbook_path, legacy_repository)
    assert result.summary_source_rows_with_values == result.summary_imported_rows
    assert result.summary_unaccounted_rows == []
    assert result.ok is True


def test_the_verifier_flags_a_row_present_in_the_source_but_missing_from_the_import(
    legacy_repository, legacy_workbook_path, history_engine,
):
    """Đây chính là lỗ hổng cũ: trước repair, ca này in `mismatched=0`."""
    from sqlalchemy import text

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    with history_engine.begin() as connection:
        connection.execute(text(
            "DELETE FROM legacy_summary_row"
            " WHERE sheet_name = 'Summary 2025' AND sheet_row = 4"
        ))
    result = verify(legacy_workbook_path, legacy_repository)
    assert "Summary 2025!4" in result.summary_unaccounted_rows
    assert result.ok is False


def test_losing_an_entire_summary_sheet_is_no_longer_a_silent_pass(
    legacy_repository, legacy_workbook_path, history_engine,
):
    from sqlalchemy import text

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    with history_engine.begin() as connection:
        connection.execute(text(
            "DELETE FROM legacy_summary_row WHERE sheet_name = 'Summary 2025'"
        ))
    result = verify(legacy_workbook_path, legacy_repository)
    assert len(result.summary_unaccounted_rows) == 3
    assert result.matched > 0          # vẫn khớp giá trị ở phần còn lại...
    assert result.mismatches == []     # ...và không có ô nào SAI GIÁ TRỊ...
    assert result.ok is False          # ...nhưng vẫn PHẢI trượt vì thiếu dòng


def test_value_match_alone_is_not_accepted_as_completeness(
    legacy_repository, legacy_workbook_path, history_engine,
):
    """`matched>0 mismatched=0` không còn đủ để kết luận fidelity."""
    from sqlalchemy import text

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    with history_engine.begin() as connection:
        connection.execute(text(
            "DELETE FROM legacy_summary_row WHERE sheet_name = 'Summary 2025'"
        ))
    result = verify(legacy_workbook_path, legacy_repository)
    assert (result.matched > 0 and not result.mismatches) and not result.ok


def test_the_verifier_exits_non_zero_when_source_coverage_is_incomplete(
    legacy_repository, legacy_workbook_path, history_engine, monkeypatch, capsys,
):
    from sqlalchemy import text

    from tools.analysis import verify_legacy_import

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    with history_engine.begin() as connection:
        connection.execute(text(
            "DELETE FROM legacy_summary_row WHERE sheet_name = 'Summary 2025'"
        ))
    monkeypatch.setattr(verify_legacy_import.history_db, "build_engine", lambda: history_engine)
    monkeypatch.setattr(
        verify_legacy_import.history_store, "build", lambda **kw: legacy_repository,
    )
    exit_code = verify_legacy_import.main([str(legacy_workbook_path)])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "SUMMARY_UNACCOUNTED_ROWS        = 3" in output
    assert "UNACCOUNTED Summary 2025!4" in output


def test_the_verifier_exits_zero_on_a_complete_faithful_import(
    legacy_repository, legacy_workbook_path, history_engine, monkeypatch, capsys,
):
    from tools.analysis import verify_legacy_import

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    monkeypatch.setattr(verify_legacy_import.history_db, "build_engine", lambda: history_engine)
    monkeypatch.setattr(
        verify_legacy_import.history_store, "build", lambda **kw: legacy_repository,
    )
    exit_code = verify_legacy_import.main([str(legacy_workbook_path)])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "SUMMARY_UNACCOUNTED_ROWS        = 0" in output
    assert "mismatched=0" in output
