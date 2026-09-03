"""TASK-PRA-005 — ngữ nghĩa tầng truy vấn Sản phẩm (Mặt hàng trên chứng từ).

``product_totals()`` TÁI DỤNG NGUYÊN VẸN ``_joined()``/``_period()``/``_read()``
đã có ở PRA-004 trong CÙNG module (``app/web/sales_queries.py``) — nhóm test
này chỉ canh phần MỚI: khoá gộp ``product_key`` (OD-PRA005-01, DEC-173), bốn
chỉ tiêu mục 8 Contract, và tính chất PHÂN HOẠCH của ``GROUP BY`` (mục 12/13,
Acceptance C-F). Oracle THẬT là fixture golden ``period_2026_01.xlsx`` qua
ĐƯỜNG PRODUCTION (``tests/test_sales_queries.py::load_golden``) — không dựng
fixture "giống production" nào ở đây.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from app.web import analytics_queries as aq
from app.web import sales_presentation as sp
from app.web import sales_queries as sq
from tests.test_sales_queries import JANUARY, fresh_engine, load_golden, pair, persist

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERY_MODULE = REPO_ROOT / "app/web/sales_queries.py"
TEMPLATE = REPO_ROOT / "app/web/templates/san_pham.html"


@pytest.fixture
def engine():
    return fresh_engine()


@pytest.fixture(scope="module")
def golden_engine():
    """Dựng MỘT lần cho cả module — đường production đọc nhiều nguồn canonical."""
    engine = fresh_engine()
    load_golden(engine)
    return engine


# --- CHECK-PRA005-01 · CHỈ-ĐỌC, cấu trúc AST (delta product_totals()) -----

def test_the_query_module_still_has_no_write_path_after_the_product_delta():
    """Bằng chứng CẤU TRÚC: toàn module (gồm delta ``product_totals()``)
    không import câu ghi nào, không ``begin()``/``commit()``/
    ``execution_options()`` — cùng khuôn ``test_the_sales_query_module_has_
    no_path_that_writes`` của PRA-004."""
    tree = ast.parse(QUERY_MODULE.read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) for alias in node.names}
    assert imported.isdisjoint({"insert", "update", "delete", "text"})
    called = {node.func.attr for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert called.isdisjoint({"begin", "commit", "execution_options"})


def _identifiers(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    return names | {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def test_product_totals_starts_from_the_current_pointers():
    names = _identifiers(QUERY_MODULE)
    assert {"order_line_current", "current_source_version_id",
            "current_result_version_id"} <= names


# --- CHECK-PRA005-02 · khoá gộp đúng product_key, KHÔNG fuzzy/model-code --

def test_A_two_lines_with_the_identical_raw_name_group_into_one_row(engine):
    """A — cùng tên hàng trên hai đơn khác nhau ⟹ MỘT dòng mặt hàng."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh Panasonic NR-BX471GPKV", row=6,
             quantity="1", sales="8000000"),
        pair("BH2", product="Tủ lạnh Panasonic NR-BX471GPKV", row=6,
             quantity="2", sales="16000000"),
    ])
    rows = sq.product_totals(engine, **JANUARY)
    assert len(rows) == 1
    assert rows[0]["product_label"] == "Tủ lạnh Panasonic NR-BX471GPKV"


def test_B_two_different_raw_names_stay_on_separate_rows(engine):
    """B — KHÔNG fuzzy/substring merge: hai tên khác nhau ⟹ hai dòng."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh Panasonic NR-BX471GPKV", row=6),
        pair("BH1", product="Máy giặt LG", row=7),
    ])
    rows = sq.product_totals(engine, **JANUARY)
    assert {row["product_label"] for row in rows} == {
        "Tủ lạnh Panasonic NR-BX471GPKV", "Máy giặt LG"}


def test_grouping_is_case_and_diacritic_sensitive_no_extra_normalization(engine):
    """``product_key`` TÁI DỤNG nguyên vẹn — không casefold/bỏ dấu thêm ở
    PRA-005 (mục 3, D9 DEFER)."""
    persist(engine, [
        pair("BH1", product="Tủ Lạnh", row=6),
        pair("BH1", product="tủ lạnh", row=7),
    ])
    assert len(sq.product_totals(engine, **JANUARY)) == 2


def test_a_model_code_shared_by_two_real_different_skus_is_not_merged(engine):
    """Bằng chứng bác bỏ model-code merge (ca ``TD-H80SEV(SK)``/``(WK)``, mục
    3 Contract): mã model trùng KHÔNG được dùng làm khoá gộp thay thế."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh TD-H80SEV(SK)", row=6),
        pair("BH1", product="Tủ lạnh TD-H80SEV(WK)", row=7),
    ])
    assert len(sq.product_totals(engine, **JANUARY)) == 2


def test_product_totals_module_calls_no_fuzzy_matching_helper():
    """Xét ĐỊNH DANH thật (AST), không xét văn xuôi giải thích trong docstring
    — chính docstring của module nói rõ "KHÔNG fuzzy merge", và một test đỏ vì
    tài liệu gọi tên thứ nó cấm là một test đo nhầm thứ."""
    names = {name.lower() for name in _identifiers(QUERY_MODULE)}
    for forbidden in ("fuzz", "difflib", "levenshtein", "sequencematcher"):
        assert not any(forbidden in name for name in names), forbidden


# --- C/D/E — số lượng, số đơn, doanh thu -----------------------------------

def test_C_quantity_sums_across_every_contributing_line(engine):
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, quantity="2"),
        pair("BH2", product="Tủ lạnh", row=6, quantity="3"),
    ])
    assert sq.product_totals(engine, **JANUARY)[0]["quantity"] == Decimal("5")


def test_D_order_count_counts_distinct_orders_not_lines(engine):
    """D — hai dòng CÙNG một đơn (hai occurrence khác nhau, cùng mặt hàng) chỉ
    đếm MỘT đơn."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, occurrence=1),
        pair("BH1", product="Tủ lạnh", row=7, occurrence=2),
        pair("BH2", product="Tủ lạnh", row=6),
    ])
    row = sq.product_totals(engine, **JANUARY)[0]
    assert row["lines"] == 3
    assert row["order_count"] == 2


def test_E_revenue_sums_the_persisted_total_sales_not_a_recomputation(engine):
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, sell="8000000", discount="500000",
             sales="7500000"),
        pair("BH2", product="Tủ lạnh", row=6, sell="8000000", discount="0",
             sales="8000000"),
    ])
    assert sq.product_totals(engine, **JANUARY)[0]["total_sales"] == Decimal("15500000")


# --- F/G/H/I — coverage LN KPI ----------------------------------------------

def test_F_full_kpi_coverage_sums_every_known_line(engine):
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, status="AUTO", kpi="1000000"),
        pair("BH2", product="Tủ lạnh", row=6, status="AUTO", kpi="2000000"),
    ])
    row = sq.product_totals(engine, **JANUARY)[0]
    assert row["kpi_profit"] == Decimal("3000000")
    assert (row["kpi_lines"], row["lines"]) == (2, 2)


def test_G_partial_kpi_coverage_sums_only_the_known_lines(engine):
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, status="AUTO", kpi="1000000"),
        pair("BH2", product="Tủ lạnh", row=6, status="PENDING", kpi=None,
             purchase=None, kpi_purchase=None, accounting=None,
             reasons=("Missing.PurchasePrice",)),
    ])
    row = sq.product_totals(engine, **JANUARY)[0]
    assert row["kpi_profit"] == Decimal("1000000")
    assert (row["kpi_lines"], row["lines"]) == (1, 2)
    cell = sp.product_row(row)["kpi_profit"]
    assert cell["text"] == "1.000.000" and cell["coverage"] == "1 / 2 dòng"


def test_H_zero_known_kpi_lines_reports_none_not_zero(engine):
    """H/I — KHÔNG dòng ``AUTO`` nào ⟹ ``None``, KHÔNG BAO GIỜ ``0``."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, status="PENDING", kpi=None,
             purchase=None, kpi_purchase=None, accounting=None,
             reasons=("Missing.PurchasePrice",)),
    ])
    row = sq.product_totals(engine, **JANUARY)[0]
    assert row["kpi_profit"] is None
    assert (row["kpi_lines"], row["lines"]) == (0, 1)
    cell = sp.product_row(row)["kpi_profit"]
    assert cell["text"] == "—" and cell["missing"] is True
    assert "0" not in cell["text"]


def test_I_a_real_zero_kpi_profit_is_distinct_from_unknown(engine):
    """I — LN KPI biết CHẮC là ``0`` (dòng ``AUTO``, ``kpi=0``) khác hẳn
    KHÔNG BIẾT — cả hai không được lẫn vào nhau ở tầng trình bày."""
    persist(engine, [pair("BH1", product="Tủ lạnh", row=6, status="AUTO", kpi="0")])
    row = sq.product_totals(engine, **JANUARY)[0]
    assert row["kpi_profit"] == Decimal("0")
    assert row["kpi_lines"] == 1
    cell = sp.product_row(row)["kpi_profit"]
    assert cell["text"] == "0" and cell["missing"] is False


# --- J — dòng dịch vụ/phí không bị lọc (OD-PRA005-02) ----------------------

def test_J_a_service_looking_line_is_not_filtered_out(engine):
    persist(engine, [pair("BH1", product="Chi phí vận chuyển", row=6,
                          quantity="1", sales="500000")])
    rows = sq.product_totals(engine, **JANUARY)
    assert [row["product_label"] for row in rows] == ["Chi phí vận chuyển"]


def test_product_totals_module_never_calls_the_non_product_line_heuristic():
    assert "is_non_product_line" not in _identifiers(QUERY_MODULE)


def test_J_the_golden_periods_real_service_lines_still_reach_the_table(golden_engine):
    """J trên oracle THẬT — S105 đo được các mô tả dịch vụ/phí của kỳ 01/2026;
    chúng phải còn nguyên trong bảng, KHÔNG bị lọc bởi bất kỳ heuristic nào."""
    labels = {row["product_label"] for row in sq.product_totals(golden_engine)}
    for expected in ("Chi phí vận chuyển", "Giá treo Tivi", "Chi phí lắp đặt"):
        assert expected in labels, expected


# --- K — mặc định sắp Doanh thu giảm dần (mục 11, 17) ----------------------

def test_K_default_order_is_revenue_descending(engine):
    persist(engine, [
        pair("BH1", product="A", row=6, sales="1000000"),
        pair("BH2", product="B", row=6, sales="5000000"),
        pair("BH3", product="C", row=6, sales="3000000"),
    ])
    rows = sq.product_totals(engine, **JANUARY)
    assert [row["product_label"] for row in rows] == ["B", "C", "A"]


def test_K_equal_revenue_groups_sort_by_a_stable_key_not_load_order(engine):
    persist(engine, [
        pair("BH1", product="Z sản phẩm", row=6, sales="1000000"),
        pair("BH2", product="A sản phẩm", row=6, sales="1000000"),
    ])
    first = [row["product_key"] for row in sq.product_totals(engine, **JANUARY)]
    second = [row["product_key"] for row in sq.product_totals(engine, **JANUARY)]
    assert first == second


# --- L — reconciliation với /tong-quan (Acceptance C/D/E/F, oracle THẬT) --

def test_L_group_sums_reconcile_with_the_accepted_period_totals(golden_engine):
    """CHECK-PRA005-04/05 — Σ theo mặt hàng = tổng kỳ đã lọc, TRÊN ORACLE
    THẬT (period_2026_01, 226 nhóm — khớp số đo Discovery S105 §13)."""
    rows = sq.product_totals(golden_engine)
    totals = aq.period_totals(golden_engine)

    assert len(rows) == 226
    assert sum(row["quantity"] or 0 for row in rows) == totals["quantity"]
    assert sum(row["total_sales"] or 0 for row in rows) == totals["total_sales"]
    assert sum(row["kpi_profit"] or 0 for row in rows) == (totals["kpi_profit"] or 0)
    assert sum(row["kpi_lines"] for row in rows) == totals["kpi_lines"]
    assert sum(row["lines"] for row in rows) == totals["lines"] == 351


def test_order_count_must_not_be_summed_into_a_period_total(golden_engine):
    """Mục 17 — Σ(order_count theo mặt hàng) KHÔNG bằng tổng đơn của kỳ, vì
    một đơn nhiều mặt hàng được đếm ở nhiều dòng mặt hàng."""
    rows = sq.product_totals(golden_engine)
    totals = aq.period_totals(golden_engine)
    assert sum(row["order_count"] for row in rows) != totals["orders"]
    assert sum(row["order_count"] for row in rows) >= totals["orders"]


# --- Split oracle FROZEN (mục 16, FIND-PRA005-01) --------------------------

def test_the_daikin_ftkb50zvmv_split_survives_untouched(golden_engine):
    """Hai cách gọi tên của CÙNG một máy Daikin FTKB50ZVMV KHÔNG được gộp —
    bằng chứng cho hành vi GENERIC của ``product_key`` (hàm thuần của chuỗi),
    KHÔNG một luật riêng cho FTKB50ZVMV. Số liệu khớp S105 §9/§13 (đo trên
    CHÍNH fixture này qua đường production)."""
    rows = {row["product_label"]: row for row in sq.product_totals(golden_engine)}
    assert "Điều hoà Daikin  FTKB50ZVMV" in rows
    assert "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV" in rows
    assert rows["Điều hoà Daikin  FTKB50ZVMV"]["quantity"] == Decimal("7")
    assert rows["Điều hoà Daikin  FTKB50ZVMV"]["total_sales"] == Decimal("113750000")
    assert rows["Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV"]["quantity"] == Decimal("1")
    assert (rows["Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV"]["total_sales"]
            == Decimal("16250000"))


# --- M — trạng thái rỗng ----------------------------------------------------

def test_M_a_period_with_no_lines_returns_an_empty_list_not_an_exception(golden_engine):
    """Kỳ 02/2026 không có dữ liệu trong golden (chỉ nạp 01/2026) — trang
    phải render được, KHÔNG bịa coverage/LN KPI."""
    empty_bounds = {"date_from": __import__("datetime").date(2026, 2, 1),
                    "date_to": __import__("datetime").date(2026, 2, 28)}
    rows = sq.product_totals(golden_engine, **empty_bounds)
    assert rows == []
    empty_totals = aq.period_totals(golden_engine, **empty_bounds)
    assert sp.product_summary(rows, empty_totals) == {
        "item_count": "0", "quantity": "—", "total_sales": "—",
        "kpi_profit": {"text": "—", "coverage": "0 / 0 dòng", "missing": True},
    }


# --- N — KHÔNG aggregate PP cấp mặt hàng -----------------------------------

def test_N_product_totals_never_selects_a_purchase_price_column():
    """CHECK-PRA005-10 — khoản tra cứu SQL của bảng mặt hàng KHÔNG bao giờ
    chạm giá mua tham chiếu ở CẤP TỔNG HỢP (mục 14/15)."""
    tree = ast.parse(QUERY_MODULE.read_text(encoding="utf-8"))
    function = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and node.name == "product_totals")
    names = {n.attr for n in ast.walk(function) if isinstance(n, ast.Attribute)}
    assert "kpi_purchase_price" not in names
    assert "accounting_purchase_price" not in names


def test_N_the_product_template_never_renders_an_aggregate_purchase_price():
    text = TEMPLATE.read_text(encoding="utf-8")
    for forbidden in ("kpi_purchase_price", "accounting_purchase_price",
                      "Giá mua tham chiếu"):
        assert forbidden not in text


def test_N_the_product_template_renders_the_required_disclosure_note():
    """Mục 5/10 — ghi chú công khai BẮT BUỘC. Template đặt nó qua jinja global
    ``PRODUCT_GROUPING_NOTE`` (cùng khuôn ``QUANTITY_NOTE``/``ORDER_COLUMN_
    NOTE`` đã có); test web-level (``test_web_product_view.py``) khẳng định
    nguyên văn xuất hiện trên HTML đã render."""
    assert "PRODUCT_GROUPING_NOTE" in TEMPLATE.read_text(encoding="utf-8")


def test_N_the_summary_label_is_not_so_san_pham():
    """EAC-5 — CẤM "Số sản phẩm"; nhãn đúng là "Số mặt hàng trên chứng từ"."""
    assert sp.PRODUCT_ITEM_COUNT_LABEL == "Số mặt hàng trên chứng từ"
    assert "Số sản phẩm" not in TEMPLATE.read_text(encoding="utf-8")


# --- Hàng rào PII (EAC-9) ----------------------------------------------------

def test_product_totals_selects_no_personal_data_column():
    text = QUERY_MODULE.read_text(encoding="utf-8")
    code = "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))
    for column in ("imei", "note_raw", "employee_raw", "customer", "phone", "address"):
        assert f".c.{column}" not in code, column
