"""TASK-PRA-004 — trình bày Bán hàng: nhãn, ``—``, coverage, lý do.

Nhóm test này canh tầng ĐỨNG GIỮA truy vấn và template. Nó tồn tại vì hai
nhánh sai chỉ lộ ra ở đây: một ``{{ value or 0 }}`` lỡ tay biến "chưa biết"
thành "bằng không", và một ô lợi nhuận render mà quên mẫu số của nó.
"""

from __future__ import annotations

import ast
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.beta_presentation import REASON_DISPLAY_LABELS
from app.modules.pricing.resolution.composition import PriceResolutionReason
from app.modules.validation.models import CATEGORIES
from app.web import sales_presentation as sp
from app.web.analytics_presentation import UNKNOWN_EMPLOYEE

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORTER = REPO_ROOT / "app/modules/exporting/excel_exporter.py"
PRESENTATION_MODULE = REPO_ROOT / "app/web/sales_presentation.py"

# Bảy nhãn của S069, chép NGUYÊN VĂN từ frozen contract mục 8.3 — chúng đang
# hiển thị cho Owner ở Owner Launcher và trang `/`, nên đổi một chữ là đổi một
# UI đã được chấp nhận ở nơi khác.
S069_LABELS = {
    "IDENTITY_UNRESOLVED": "Chưa nhận diện sản phẩm",
    "TRACKING_HISTORY_PENDING": "Thiếu giá lịch sử Tracking",
    "Missing.PurchasePrice": "Thiếu giá mua tham chiếu",
    "Pending.accounting_purchase_price": "Thiếu giá nhập kế toán",
    "Pending.accounting_profit": "Thiếu lợi nhuận kế toán",
    "Pending.eligible_kpi_profit": "Thiếu lợi nhuận KPI",
    "Suspicious": "Bất thường",
}

# Mục 14.3 — từ vựng nội bộ, bị cấm khỏi UI quản lý y như PII.
INTERNAL_VOCABULARY = (
    "snapshot_id", "run_id", "coverage_state", "source_version", "result_version",
    "reconciliation_flag", "PIPELINE_GENERATED", "LEGACY_REFERENCE", "price_source",
    "kpi_purchase_provenance", "composition_rule", "identity_namespace",
    "result_fingerprint", "row_hash", "line_fingerprint", "product_key",
    "occurrence_index",
)


def pending_fields_from_source() -> set[str]:
    """Ba chuỗi ``Pending.<field>`` DẪN XUẤT từ chính vòng lặp sinh ra chúng.

    Đọc AST của ``excel_exporter`` thay vì chép tay ba tên: một danh sách chép
    tay chỉ chứng minh test khớp với chính nó, và sẽ tiếp tục xanh sau ngày ai
    đó thêm trường thứ tư.
    """
    tree = ast.parse(EXPORTER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.For) and isinstance(node.target, ast.Tuple)):
            continue
        if [element.id for element in node.target.elts] != ["field", "label"]:
            continue
        return {pair.elts[0].value for pair in node.iter.elts}
    raise AssertionError("không tìm thấy vòng lặp sinh mã Pending.<field>")


def reason_universe() -> set[str]:
    """O-D1 — vũ trụ ĐÓNG, dẫn xuất TỪ MÃ NGUỒN, không chép tay."""
    return ({reason.value for reason in PriceResolutionReason}
            | set(CATEGORIES)
            | {f"Pending.{field}" for field in pending_fields_from_source()})


def order(**overrides) -> dict:
    row = {
        "order_key": "BH1", "sale_date_from": date(2026, 1, 5),
        "sale_date_to": date(2026, 1, 5), "employees": ["VuHanhLy"], "lines": 4,
        "quantity": Decimal("5"), "total_sales": Decimal("66000000"),
        "kpi_profit": Decimal("400000"), "kpi_lines": 1,
        "accounting_profit": Decimal("500000"), "accounting_lines": 1,
        "review": True,
    }
    return {**row, **overrides}


def line(**overrides) -> dict:
    row = {
        "product_raw": "Điều hòa Daikin FTHF25XVMV", "quantity": Decimal("2"),
        "sell_price": Decimal("10500000"), "discount": Decimal("100000"),
        "total_sales": Decimal("20900000"),
        "accounting_purchase_price": Decimal("10250000"),
        "kpi_purchase_price": Decimal("10250000"),
        "accounting_profit": Decimal("500000"),
        "eligible_kpi_profit": Decimal("400000"),
        "status": "AUTO", "employee": "VuHanhLy", "reasons": [],
    }
    return {**row, **overrides}


# --- Vũ trụ reason code (CHECK-PRA004-04) --------------------------------

def test_the_reason_universe_derived_from_source_is_closed_at_21_codes():
    """O-D1 — 10 ``PriceResolutionReason`` + 8 ``CATEGORIES`` + 3 ``Pending``."""
    universe = reason_universe()
    assert len(PriceResolutionReason) == 10
    assert len(CATEGORIES) == 8
    assert pending_fields_from_source() == {
        "accounting_purchase_price", "accounting_profit", "eligible_kpi_profit"}
    assert len(universe) == 21


def test_the_label_table_covers_the_whole_closed_universe():
    """O-D2 — TOÀN PHẦN. Nhánh dự phòng "hiện nguyên mã" vì vậy không bao giờ
    chạy trên dữ liệu thật, và nó vẫn tồn tại cho ngày engine mở thêm mã."""
    assert reason_universe() - set(REASON_DISPLAY_LABELS) == set()


def test_the_label_table_invents_no_code_of_its_own():
    """Bảng nhãn KHÔNG được rộng hơn vũ trụ đóng: một khoá thừa ở đây là một
    mã không tồn tại ở engine, tức một taxonomy mới đang lén hình thành."""
    assert set(REASON_DISPLAY_LABELS) - reason_universe() == set()


def test_the_seven_s069_labels_are_unchanged_word_for_word():
    """O-D3 — bảy nhãn này đang chạy production ở nơi khác."""
    for code, label in S069_LABELS.items():
        assert REASON_DISPLAY_LABELS[code] == label


def test_no_label_leaks_internal_vocabulary():
    """O-D4 — không nhãn nào chứa tên bảng/cột/enum hay ID nội bộ."""
    for code, label in REASON_DISPLAY_LABELS.items():
        for word in INTERNAL_VOCABULARY:
            assert word.lower() not in label.lower(), f"{code} → {label}"


def test_reasons_are_shown_all_of_them_in_the_persisted_order():
    """Mục 8.4 — hiện TẤT CẢ, không gộp, không chọn "lý do chính"."""
    codes = ["IDENTITY_SOURCES_UNAVAILABLE", "Missing.PurchasePrice",
             "Pending.accounting_purchase_price"]
    assert sp.reason_labels(codes) == [
        "Chưa có dữ liệu để nhận diện sản phẩm", "Thiếu giá mua tham chiếu",
        "Thiếu giá nhập kế toán"]


def test_an_unlabelled_code_is_shown_verbatim_not_swallowed():
    """Fail-safe: một lý do khó đọc vẫn là một lý do; bỏ im lặng thì dòng đó
    mất luôn câu trả lời cho "tại sao cần kiểm tra"."""
    assert sp.reason_labels(["MA_CHUA_CO_NHAN"]) == ["MA_CHUA_CO_NHAN"]


# --- Trạng thái ----------------------------------------------------------

def test_there_are_exactly_two_status_labels():
    assert sp.status(True) == "CẦN KIỂM TRA"
    assert sp.status(False) == "AUTO"


INVENTED_STATUSES = ("PARTIAL", "WARNING", "RESOLVED", "APPROVED", "REJECTED")


def emitted_strings(path: Path) -> str:
    """Chuỗi module CÓ THỂ in ra + tên định danh của nó — KHÔNG gồm docstring.

    Xét văn xuôi giải thích cũng như văn bản hiển thị là sai: chính docstring
    của module nói rõ "không PARTIAL, không WARNING", và một test đỏ vì tài
    liệu gọi tên thứ nó cấm là một test đo nhầm thứ.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (isinstance(body, list) and body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            docstrings.add(id(body[0].value))
    values = [node.value for node in ast.walk(tree)
              if isinstance(node, ast.Constant) and isinstance(node.value, str)
              and id(node) not in docstrings]
    values += [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
    return " ".join(values)


def template_text(name: str) -> str:
    """Template, đã bỏ chú thích Jinja ``{# … #}`` — cùng lý do như trên."""
    raw = (REPO_ROOT / "app/web/templates" / name).read_text(encoding="utf-8")
    return re.sub(r"\{#.*?#\}", " ", raw, flags=re.S)


def test_the_presentation_module_names_no_third_status():
    """CHECK-PRA004-05(c) — không ``PARTIAL``/``WARNING``/``RESOLVED``/
    ``APPROVED`` len vào tầng trình bày."""
    text = emitted_strings(PRESENTATION_MODULE)
    for invented in INVENTED_STATUSES:
        assert not re.search(rf"\b{invented}\b", text), invented


def test_neither_new_template_names_a_third_status():
    for name in ("ban_hang.html", "ban_hang_chi_tiet.html"):
        text = template_text(name)
        for invented in INVENTED_STATUSES:
            assert not re.search(rf"\b{invented}\b", text), f"{name} → {invented}"


# --- ``NULL`` ≠ ``0`` và coverage ----------------------------------------

def test_a_missing_profit_renders_as_a_dash_never_as_zero():
    """INV-6 — ô trống nghĩa là chưa biết, không phải lãi bằng không."""
    cell = sp.order_row(order(accounting_profit=None, accounting_lines=0))
    assert cell["accounting_profit"]["text"] == "—"
    assert cell["accounting_profit"]["missing"] is True
    assert "0" not in cell["accounting_profit"]["text"]


def test_a_real_zero_profit_still_renders_as_zero():
    """Phía đối xứng: ``0`` là một câu trả lời THẬT và phải hiện ra như vậy."""
    cell = sp.order_row(order(accounting_profit=Decimal("0"), accounting_lines=4))
    assert cell["accounting_profit"]["text"] == "0"
    assert cell["accounting_profit"]["missing"] is False


def test_every_order_profit_cell_carries_its_own_coverage():
    """INV-7 — không có đường nào render lợi nhuận đơn mà thiếu mẫu số."""
    row = sp.order_row(order())
    assert row["kpi_profit"]["coverage"] == "1 / 4 dòng"
    assert row["accounting_profit"]["coverage"] == "1 / 4 dòng"


def test_the_two_coverages_can_have_different_numerators():
    row = sp.order_row(order(kpi_lines=1, accounting_lines=3))
    assert row["kpi_profit"]["coverage"] == "1 / 4 dòng"
    assert row["accounting_profit"]["coverage"] == "3 / 4 dòng"


def test_partial_coverage_is_flagged_so_the_page_can_say_it_out_loud():
    """Đơn 66 triệu, lợi nhuận của 1/4 dòng — đây là failure path nghiêm trọng
    nhất của slice, nên nó có một cờ riêng chứ không trông chờ người đọc nhìn
    xuống mẫu số."""
    detail = sp.order_detail({**order(), "lines_detail": []})
    assert detail["partial_coverage"] is True
    assert "KHÔNG phải" in detail["coverage_note"]


def test_full_coverage_raises_no_warning():
    detail = sp.order_detail({**order(lines=1, kpi_lines=1, accounting_lines=1),
                              "lines_detail": []})
    assert detail["partial_coverage"] is False


# --- Nhân viên và ngày ---------------------------------------------------

def test_all_employees_of_an_order_are_shown():
    assert sp.employees(["TranMinh", "VuHanhLy"]) == "TranMinh · VuHanhLy"
    assert sp.order_row(order(employees=["A", "B"]))["multi_employee"] is True


def test_a_missing_employee_gets_the_shared_unknown_label():
    assert sp.employees([None]) == UNKNOWN_EMPLOYEE
    assert sp.employees([]) == UNKNOWN_EMPLOYEE


def test_one_sale_date_shows_one_date_and_two_show_a_range():
    """KHÔNG chọn một ngày làm đại diện cho đơn."""
    assert sp.sale_dates(order()) == "05/01/2026"
    row = order(sale_date_to=date(2026, 1, 9))
    assert sp.sale_dates(row) == "05/01/2026 – 09/01/2026"
    assert sp.order_row(row)["multi_date"] is True


# --- Dòng hàng -----------------------------------------------------------

def test_a_pending_line_renders_every_missing_money_cell_as_a_dash():
    row = sp.line_row(line(status="PENDING", accounting_purchase_price=None,
                           kpi_purchase_price=None, accounting_profit=None,
                           eligible_kpi_profit=None,
                           reasons=["Missing.PurchasePrice"]))
    assert row["status"] == "CẦN KIỂM TRA"
    for metric in ("accounting_purchase_price", "kpi_purchase_price",
                   "accounting_profit", "kpi_profit"):
        assert row[metric] == "—"
    assert row["reasons"] == ["Thiếu giá mua tham chiếu"]


def test_an_auto_line_shows_both_purchase_prices_and_both_profits():
    """Hai lợi nhuận có HAI cơ sở giá; hiện một giá cho hai con số là để một
    trong hai vĩnh viễn không kiểm được (mục 12.C)."""
    row = sp.line_row(line())
    assert row["status"] == "AUTO"
    assert row["accounting_purchase_price"] == "10.250.000"
    assert row["kpi_purchase_price"] == "10.250.000"
    assert row["accounting_profit"] == "500.000"
    assert row["kpi_profit"] == "400.000"
    assert row["reasons"] == []


def test_the_line_shows_the_product_name_it_was_given():
    assert sp.line_row(line())["product"] == "Điều hòa Daikin FTHF25XVMV"
    assert sp.line_row(line(product_raw=None))["product"] == "—"


def test_the_line_columns_expose_no_internal_field():
    """Tám cột (OWNER_PRESENTATION_DECISION KPI-first, mục 6/17 task) — và
    KHÔNG ``price_source``/``kpi_purchase_provenance``, chúng là từ vựng nội
    bộ."""
    assert len(sp.LINE_COLUMNS) == 8
    joined = " ".join(sp.ORDER_COLUMNS + sp.LINE_COLUMNS)
    for word in INTERNAL_VOCABULARY:
        assert word.lower() not in joined.lower()


def test_the_kpi_first_columns_drop_accounting_and_rename_the_purchase_price():
    """OWNER_PRESENTATION_DECISION — management UI mặc định không còn "LN kế
    toán"/"Giá vốn (kế toán)"; "Giá vốn (KPI)" đổi tên "Giá mua tham chiếu"."""
    assert "LN kế toán" not in sp.ORDER_COLUMNS
    assert "LN kế toán" not in sp.LINE_COLUMNS
    assert "Giá vốn (kế toán)" not in sp.LINE_COLUMNS
    assert "Giá vốn (KPI)" not in sp.LINE_COLUMNS
    assert "Giá mua tham chiếu" in sp.LINE_COLUMNS
    assert "LN KPI" in sp.ORDER_COLUMNS and "LN KPI" in sp.LINE_COLUMNS


def test_the_presentation_object_of_a_line_carries_no_prohibited_field():
    """Ranh giới PII đặt Ở ĐÂY, không chỉ ở template: object đi tới Jinja
    không được chứa ``imei``/``note_raw``/``employee_raw``/``source_profit``."""
    keys = set(sp.line_row(line())) | set(sp.order_row(order()))
    assert keys.isdisjoint({"imei", "note_raw", "employee_raw", "source_profit",
                            "customer", "phone", "address"})
