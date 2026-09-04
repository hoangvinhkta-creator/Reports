"""Repair FIND-PRA001-R01 — dòng nguồn bị bỏ qua phải FAIL TO, không im lặng.

Independent Review chứng minh một lỗ hổng thật: verifier duyệt từ DB → Excel
nên nó chỉ trả lời được "những gì ĐÃ nhập có đúng không", không bao giờ trả
lời được "có gì chưa được nhập không". Hệ quả: mất trọn một sheet Summary mà
vẫn in `matched=372 mismatched=0`.

Chính sách Owner (DEC-168) áp dụng cho các sheet REQUIRED_IMPORT:

    dòng nguồn có giá trị nghiệp vụ
        → contract phân loại nhận ra?  ── CÓ ─→ nhập
                                       └─ KHÔNG ─→ FAIL TO

Không đoán `row_kind` từ việc "dòng có số". Không tự mở rộng semantics.

DEC-169 thu hẹp PHẠM VI mà guard trên áp dụng, chứ không hạ ngưỡng của nó;
`DEC-177` (đính chính của chủ dự án) mở lại phạm vi đó: `Summary 2025` nay
là OPTIONAL_IMPORT — dòng phân loại được thì NHẬP, dòng không thì ĐẾM và báo
lên giao diện, và cả hai trường hợp đều KHÔNG được làm import trượt.
`Summary 2026` vẫn là REQUIRED_IMPORT nên đúng hình dạng value-only đó vẫn
PHẢI FAIL TO. Vì vậy mọi bài test guard trong file này chĩa vào
`Summary 2026` — giữ nguyên sức mạnh của R01 guard trên đúng phạm vi mà
Owner tuyên bố là production.
"""

from __future__ import annotations

import pytest

from app.legacy import LegacyImportError, parse_workbook
from tests.fixtures.legacy.build_legacy_workbook import (
    build_legacy_workbook, strip_formula_markers,
)
from tools.analysis.verify_legacy_import import verify


@pytest.fixture
def workbook_with_value_only_required_sheet(tmp_path):
    """Case reviewer, chĩa vào sheet REQUIRED_IMPORT: guard phải nổ."""
    return strip_formula_markers(
        build_legacy_workbook(tmp_path / "mat_formula_2026.xlsx"),
        sheet_name="Summary 2026",
    )


@pytest.fixture
def workbook_with_value_only_reference_sheet(tmp_path):
    """Hình dạng workbook THẬT: `Summary 2025` value-only, không công thức."""
    return strip_formula_markers(
        build_legacy_workbook(tmp_path / "mat_formula_2025.xlsx"),
        sheet_name="Summary 2025",
    )


# --- DEC-169: REFERENCE_ONLY nằm ngoài authoritative import scope ---------

def test_a_value_only_reference_sheet_does_not_fail_production_import(
    workbook_with_value_only_reference_sheet,
):
    """A. Đúng hình dạng workbook thật: 0 công thức trong `Summary 2025`.

    Trước DEC-169 ca này raise LegacyImportError và chặn toàn bộ acceptance.
    Sau DEC-169 nó phải nhập bình thường. `DEC-177` giữ NGUYÊN bất biến đó:
    mở phạm vi cho `Summary 2025` không được biến hình dạng value-only thành
    một lần nhập trượt.
    """
    workbook = parse_workbook(workbook_with_value_only_reference_sheet)
    assert workbook.summary_rows, "Sheet REQUIRED_IMPORT vẫn phải được nhập"
    assert [r for r in workbook.summary_rows if r.sheet_name == "Summary 2025"] == []


def test_b_a_classifiable_optional_sheet_is_parsed_into_summary_rows(
    legacy_workbook_path,
):
    """B. `DEC-177` — dòng `Summary 2025` phân loại được thì PHẢI được nhập."""
    workbook = parse_workbook(legacy_workbook_path)
    rows = [r for r in workbook.summary_rows if r.sheet_name == "Summary 2025"]
    assert {r.year for r in rows} == {2025}
    assert {r.row_kind for r in rows} == {"SELLER", "MONTH_TOTAL"}


def test_b_an_optional_sheet_is_persisted_with_the_legacy_origin(
    legacy_repository, legacy_workbook_path, history_engine,
):
    """B. Chứng minh ở tầng DB, không chỉ ở tầng parser."""
    from sqlalchemy import text

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    with history_engine.begin() as connection:
        persisted = connection.execute(text(
            "SELECT COUNT(*) FROM legacy_summary_row"
            " WHERE sheet_name = 'Summary 2025' AND origin = 'LEGACY_REFERENCE'"
        )).scalar_one()
    assert persisted == 3


def test_b_the_optional_sheet_is_recorded_in_the_import_provenance(
    legacy_workbook_path,
):
    """B. Bản ghi import phải nói RÕ sheet nào thuộc phạm vi nào."""
    workbook = parse_workbook(legacy_workbook_path)
    scopes = {item["sheet_name"]: item["scope"] for item in workbook.sheets_imported}
    assert scopes == {
        "Summary 2026": "REQUIRED_IMPORT",
        "DataChart 2026": "REQUIRED_IMPORT",
        "Summary 2025": "OPTIONAL_IMPORT",
    }


def test_b_an_unreadable_optional_sheet_is_counted_not_swallowed(tmp_path):
    """B. Không đoán, nhưng cũng KHÔNG im lặng: dòng chưa đọc được phải đếm."""
    stripped = strip_formula_markers(
        build_legacy_workbook(tmp_path / "unread.xlsx"), sheet_name="Summary 2025")
    workbook = parse_workbook(stripped)
    entry = next(item for item in workbook.sheets_imported
                 if item["sheet_name"] == "Summary 2025")
    assert entry["imported_rows"] == "0"
    assert entry["unclassified_rows"] == "3"
    assert entry["unclassified_preview"] == "4, 5, 6"


def test_c_the_required_summary_sheet_is_still_imported(legacy_workbook_path):
    """C. Summary 2026 không đổi semantics."""
    workbook = parse_workbook(legacy_workbook_path)
    rows = [r for r in workbook.summary_rows if r.sheet_name == "Summary 2026"]
    assert len(rows) == 13
    assert {r.row_kind for r in rows} == {
        "YEAR_TOTAL", "SELLER", "MONTH_TOTAL"}


def test_d_the_datachart_sheet_is_still_imported(legacy_workbook_path):
    """D. DataChart 2026 không đổi."""
    workbook = parse_workbook(legacy_workbook_path)
    assert {(item.month, item.day) for item in workbook.daily_sales} == {
        (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (3, 1)}
    assert len(workbook.monthly_reference) == 12


def test_the_verifier_checks_fidelity_of_imported_optional_rows(
    legacy_repository, legacy_workbook_path,
):
    """Dòng OPTIONAL đã nhập vẫn phải khớp giá trị nguồn như mọi dòng khác."""
    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    result = verify(legacy_workbook_path, legacy_repository)
    assert result.optional_imported_rows == 3
    assert result.optional_unimported_rows == []
    assert result.ok is True


def test_the_verifier_counts_unimported_optional_rows_without_failing(
    legacy_repository, tmp_path,
):
    """Thiếu dòng OPTIONAL là SỐ ĐO, không phải lỗi — thiếu dòng REQUIRED mới là lỗi.

    Bất đối xứng có chủ đích: thiếu một dòng production nghĩa là số hiển thị
    sai; thiếu một dòng lịch sử nghĩa là còn một phần chưa đọc được, và điều
    đó cần được NÓI RA chứ không cần chặn.
    """
    stripped = strip_formula_markers(
        build_legacy_workbook(tmp_path / "unread_verify.xlsx"),
        sheet_name="Summary 2025")
    legacy_repository.create_import(parse_workbook(stripped))
    result = verify(stripped, legacy_repository)
    assert result.optional_imported_rows == 0
    assert result.optional_unimported_rows == [
        "Summary 2025!4", "Summary 2025!5", "Summary 2025!6"]
    # ĐIỀU ĐANG ĐƯỢC KHẲNG ĐỊNH: dòng OPTIONAL chưa nhập KHÔNG rơi vào rổ
    # gây trượt (`summary_unaccounted_rows`) và không sinh mismatch nào.
    assert result.summary_unaccounted_rows == []
    assert [m for m in result.mismatches if "Summary 2025" in m] == []
    # KHÔNG khẳng định `result.ok` ở đây: `strip_formula_markers` lưu lại
    # workbook bằng openpyxl, thao tác đó xoá cached value của các sheet
    # KHÁC (`Summary 2026`), nên verifier báo lệch trên sheet đó. Đó là giới
    # hạn của fixture, không phải hành vi sản phẩm — và khẳng định nó ở đây
    # sẽ biến bài test thành bài test về fixture.


# --- DEC-168 guard, trên sheet REQUIRED_IMPORT (không bị nới lỏng) --------

def test_f_a_required_sheet_that_would_import_nothing_fails_loudly(
    workbook_with_value_only_required_sheet,
):
    """F. Đúng ca của reviewer, nay chĩa vào `Summary 2026`."""
    with pytest.raises(LegacyImportError) as exc:
        parse_workbook(workbook_with_value_only_required_sheet)
    message = str(exc.value)
    assert "Summary 2026" in message
    assert "OWNER_DECISION_REQUIRED" in message


def test_f_the_error_names_the_exact_unaccounted_source_rows(
    workbook_with_value_only_required_sheet,
):
    """Owner phải biết DÒNG NÀO, không chỉ 'có gì đó sai'."""
    with pytest.raises(LegacyImportError) as exc:
        parse_workbook(workbook_with_value_only_required_sheet)
    message = str(exc.value)
    for row in ("3", "4", "5", "6"):
        assert row in message


def test_f_a_single_unaccounted_row_also_fails_not_just_a_whole_sheet(
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


def test_f_the_parser_never_guesses_a_row_kind_from_numbers_alone(
    workbook_with_value_only_required_sheet,
):
    """Chính sách Owner: không suy business semantics chỉ vì dòng có số."""
    with pytest.raises(LegacyImportError):
        parse_workbook(workbook_with_value_only_required_sheet)


def test_a_well_formed_workbook_still_imports_with_no_unaccounted_rows(
    legacy_workbook_path,
):
    """Guard KHÔNG được biến thành báo động giả trên workbook đúng hình dạng."""
    workbook = parse_workbook(legacy_workbook_path)
    # 13 dòng `Summary 2026` (REQUIRED) + 3 dòng `Summary 2025` (OPTIONAL,
    # `DEC-177`). Tách theo sheet thay vì đếm gộp: một con số gộp không nói
    # được sheet nào đóng góp bao nhiêu.
    by_sheet = {}
    for row in workbook.summary_rows:
        by_sheet[row.sheet_name] = by_sheet.get(row.sheet_name, 0) + 1
    assert by_sheet == {"Summary 2026": 13, "Summary 2025": 3}


# --- Verifier: coverage từ phía Excel -------------------------------------

def test_e_the_verifier_reports_source_coverage_counts(
    legacy_repository, legacy_workbook_path,
):
    """E. Source coverage của `Summary 2026` vẫn được kiểm đầy đủ."""
    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    result = verify(legacy_workbook_path, legacy_repository)
    assert result.summary_source_rows_with_values > 0
    assert result.summary_source_rows_with_values == result.summary_imported_rows
    assert result.summary_unaccounted_rows == []
    assert result.ok is True


def test_e_the_verifier_flags_a_row_present_in_the_source_but_missing_from_the_import(
    legacy_repository, legacy_workbook_path, history_engine,
):
    """Đây chính là lỗ hổng cũ: trước repair, ca này in `mismatched=0`."""
    from sqlalchemy import text

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    with history_engine.begin() as connection:
        connection.execute(text(
            "DELETE FROM legacy_summary_row"
            " WHERE sheet_name = 'Summary 2026' AND sheet_row = 4"
        ))
    result = verify(legacy_workbook_path, legacy_repository)
    assert "Summary 2026!4" in result.summary_unaccounted_rows
    assert result.ok is False


def test_losing_an_entire_summary_sheet_is_no_longer_a_silent_pass(
    legacy_repository, legacy_workbook_path, history_engine,
):
    from sqlalchemy import text

    legacy_repository.create_import(parse_workbook(legacy_workbook_path))
    with history_engine.begin() as connection:
        connection.execute(text(
            "DELETE FROM legacy_summary_row WHERE sheet_name = 'Summary 2026'"
        ))
    result = verify(legacy_workbook_path, legacy_repository)
    assert len(result.summary_unaccounted_rows) == result.summary_source_rows_with_values
    assert result.summary_unaccounted_rows           # ...thật sự có dòng thiếu...
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
            "DELETE FROM legacy_summary_row WHERE sheet_name = 'Summary 2026'"
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
            "DELETE FROM legacy_summary_row WHERE sheet_name = 'Summary 2026'"
        ))
    monkeypatch.setattr(verify_legacy_import.history_db, "build_engine", lambda: history_engine)
    monkeypatch.setattr(
        verify_legacy_import.history_store, "build", lambda **kw: legacy_repository,
    )
    exit_code = verify_legacy_import.main([str(legacy_workbook_path)])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "UNACCOUNTED Summary 2026!4" in output


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
    assert "SUMMARY_OPTIONAL_IMPORTED       = 3" in output
    assert "SUMMARY_OPTIONAL_UNIMPORTED     = 0" in output
    assert "mismatched=0" in output
