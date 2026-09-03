"""TASK-PRA-004 — ngữ nghĩa tầng truy vấn Bán hàng.

Hai loại dữ liệu, cố ý tách bạch:

* **Oracle golden** (``period_2026_01.xlsx``) đi qua ĐƯỜNG PRODUCTION THẬT —
  ``run_import_production`` → ``present_lines`` → ``extraction.build_*_lines``
  → ``history_writer.write_run_history`` — rồi mới bị truy vấn. Không bảng nào
  dựng bằng tay, không một byte nào của ``tests/fixtures/golden/**`` bị sửa.
* **Dữ liệu tổng hợp có kiểm soát** phủ đúng những vùng oracle golden KHÔNG
  phủ được: đơn nhiều nhân viên (fixture đã ẩn danh nên chỉ có một tên), lợi
  nhuận bằng 0 thật, và một dòng bị SỬA qua hai lần chạy.
"""

from __future__ import annotations

import ast
import re
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.composition import build_price_composition, run_import_production
from app.demo import DemoRun
from app.modules.exporting.excel_exporter import export_report, present_lines
from app.modules.importing.raw_reader import read_raw_rows
from app.web import history_store, history_writer
from app.web import sales_queries as sq
from tests.test_snapshot_repository import result_line, source_line, write

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERY_MODULE = REPO_ROOT / "app/web/sales_queries.py"
GOLDEN = REPO_ROOT / "tests/fixtures/golden/period_2026_01.xlsx"
CONFIG_DIR = REPO_ROOT / "config"

JANUARY = {"date_from": date(2026, 1, 1), "date_to": date(2026, 1, 31)}
FEBRUARY = {"date_from": date(2026, 2, 1), "date_to": date(2026, 2, 28)}


def fresh_engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def engine():
    return fresh_engine()


# --- Oracle golden: qua ĐƯỜNG PRODUCTION ----------------------------------

def load_golden(engine, *, run_id="golden-1") -> None:
    """Chạy đúng đường production rồi persist kết quả của nó.

    Không mock, không DI test-only: ``run_import_production`` nạp chính các
    nguồn canonical đã commit, nên các con số dưới đây là kết quả THẬT của
    pipeline chứ không phải một fixture ai đó gõ tay.
    """
    composition = build_price_composition(CONFIG_DIR)
    result = run_import_production(GOLDEN, config_dir=CONFIG_DIR,
                                   price_composition=composition)
    raw_rows = read_raw_rows(GOLDEN)
    output = Path(tempfile.mkdtemp()) / "golden-report.xlsx"
    summary = export_report(result, composition.records, raw_rows, sales_path=GOLDEN,
                            tracking_capture=GOLDEN, tracking_catalog=GOLDEN,
                            output_path=output,
                            processed_at=datetime.now().astimezone())
    run = DemoRun(result, composition.records, summary, output, tuple(raw_rows),
                  tuple(present_lines(result, composition.records, raw_rows)))
    history_writer.write_run_history(
        history_store.SnapshotRepository(engine), demo_run=run, run_id=run_id,
        workbook_path=GOLDEN, display_name=GOLDEN.name,
        created_at="2026-02-01T00:00:00")


@pytest.fixture(scope="module")
def golden_engine():
    """Dựng MỘT lần cho cả module: đường production đọc nhiều nguồn canonical
    và chạy lại nó cho từng test là trả giá mà không mua thêm bằng chứng nào."""
    engine = fresh_engine()
    load_golden(engine)
    return engine


# --- Dữ liệu tổng hợp có kiểm soát ----------------------------------------

def pair(order, *, product="Tủ lạnh", occurrence=1, row=6, day=5, month=1,
         employee="VuHanhLy",
         status="AUTO", quantity="1", sell="8000000", discount="0", sales="8000000",
         purchase="5000000", kpi_purchase="5000000", accounting="3000000",
         kpi="3000000", reasons=()):
    """Một cặp (dòng nguồn, dòng kết quả) đã khớp khoá.

    ``None`` truyền vào một ô tiền nghĩa là "chưa có giá trị" — KHÁC HẲN
    ``"0"``, và phân biệt đó chính là thứ nhóm test này tồn tại để canh.
    """
    source = source_line(order, product, occurrence, row=row,
                         sale_date=date(2026, month, day) if day else None,
                         sell_price=sell, quantity=Decimal(quantity),
                         discount=Decimal(discount))
    result = result_line(source, status=status)
    return source, type(result)(**{
        **{field: getattr(result, field) for field in result.__dataclass_fields__},
        "employee_normalized": employee, "pending_reasons": tuple(reasons),
        "total_sales": None if sales is None else Decimal(sales),
        "accounting_purchase_price": None if purchase is None else Decimal(purchase),
        "kpi_purchase_price": None if kpi_purchase is None else Decimal(kpi_purchase),
        "accounting_profit": None if accounting is None else Decimal(accounting),
        "eligible_kpi_profit": None if kpi is None else Decimal(kpi),
    })


def persist(engine, pairs, *, run_id="run-1", at="2026-02-01T00:00:00",
            fingerprint="fp-a"):
    return write(history_store.SnapshotRepository(engine), [p[0] for p in pairs],
                 run_id=run_id, created_at=at, fingerprint=fingerprint,
                 results=[p[1] for p in pairs])


def by_key(orders: list[dict]) -> dict[str, dict]:
    return {order["order_key"]: order for order in orders}


# --- CHECK-PRA004-01 · CHỈ-ĐỌC và chỉ trạng thái hiện hành ----------------

def test_the_sales_query_module_has_no_path_that_writes():
    """Bằng chứng CẤU TRÚC bằng AST, không phải grep chuỗi: không import được
    câu ghi nào, và không ``begin()``/``commit()`` thì SQLAlchemy 2.0 không
    autocommit ⟹ đường ghi KHÔNG TỒN TẠI, chứ không phải "chưa ai viết"."""
    tree = ast.parse(QUERY_MODULE.read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) for alias in node.names}
    assert imported.isdisjoint({"insert", "update", "delete", "text"})
    called = {node.func.attr for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert called.isdisjoint({"begin", "commit", "execution_options"})
    assert "connect" in called, "tầng này chỉ mở kết nối CHỈ-ĐỌC"


def test_the_sales_query_module_never_aggregates_run_history():
    names = _identifiers(QUERY_MODULE)
    assert "summary_json" not in names, "cộng summary_json qua các run là double-count"
    assert "source_snapshot" not in names


def test_every_sales_query_starts_from_the_current_pointers():
    """Mọi truy vấn xuất phát từ ``order_line_current`` và đi qua ĐÚNG hai con
    trỏ hiện hành — không có đường nào đọc thẳng một bảng version."""
    names = _identifiers(QUERY_MODULE)
    assert {"order_line_current", "current_source_version_id",
            "current_result_version_id"} <= names


def _identifiers(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    names |= {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    return names | {alias.name for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) for alias in node.names}


def test_only_the_current_version_of_a_changed_line_reaches_the_detail(engine):
    """``SOURCE_CHANGED``: version cũ vẫn nằm trong bảng audit nhưng KHÔNG
    được hiện — nếu cả hai lọt vào thì một lần sửa giá thành hai lần bán."""
    persist(engine, [pair("BH1", sell="8000000", sales="8000000")],
            run_id="v1", fingerprint="fp-a")
    persist(engine, [pair("BH1", sell="9000000", sales="9000000")],
            run_id="v2", at="2026-02-02T00:00:00", fingerprint="fp-b")

    detail = sq.order_detail(engine, "BH1", **JANUARY)
    assert detail["lines"] == 1
    assert detail["total_sales"] == Decimal("9000000")
    assert [line["sell_price"] for line in detail["lines_detail"]] == [Decimal("9000000")]


# --- CHECK-PRA004-02 · oracle golden + no-double-count --------------------

def test_the_golden_period_lists_the_orders_the_production_path_produced(golden_engine):
    """O-A1 · O-A3 — 254 đơn, 351 dòng, và phân hoạch AUTO/Review là ĐẦY ĐỦ."""
    orders = sq.order_list(golden_engine)
    assert len(orders) == 254
    assert sum(order["lines"] for order in orders) == 351
    auto = [order for order in orders if not order["review"]]
    review = [order for order in orders if order["review"]]
    assert len(auto) + len(review) == len(orders)


def test_the_golden_period_has_exactly_one_all_auto_order(golden_engine):
    """O-A2 — 1 đơn AUTO thuần, 253 đơn cần kiểm tra."""
    orders = sq.order_list(golden_engine)
    assert [order["order_key"] for order in orders if not order["review"]] == ["BH62063"]
    assert sum(1 for order in orders if order["review"]) == 253


def test_the_line_count_distribution_adds_back_up_to_every_line(golden_engine):
    """O-A4 + INV-3 — Σ(số dòng × số đơn) = 351.

    Đây là hình thức đo được của no-double-count: nếu một dòng bị đếm hai lần
    ở đâu đó, phân bố này lệch và tổng không còn bằng số dòng của kỳ.
    """
    orders = sq.order_list(golden_engine)
    distribution: dict[int, int] = {}
    for order in orders:
        distribution[order["lines"]] = distribution.get(order["lines"], 0) + 1
    assert distribution == {1: 191, 2: 41, 3: 16, 4: 3, 5: 1, 6: 1, 7: 1}
    assert sum(size * many for size, many in distribution.items()) == 351


def test_reuploading_the_same_book_moves_no_order_total(engine):
    """Nạp lại ĐÚNG cùng một sổ không nhân đôi bất cứ con số nào."""
    pairs = [pair("BH1"), pair("BH2", day=9, row=7)]
    persist(engine, pairs, run_id="run-1", fingerprint="fp-a")
    before = sq.order_list(engine, **JANUARY)
    persist(engine, pairs, run_id="run-2", at="2026-02-02T00:00:00", fingerprint="fp-a")

    assert sq.order_list(engine, **JANUARY) == before
    assert [order["lines"] for order in before] == [1, 1]


def test_a_multi_line_order_aggregates_its_lines_exactly_once(engine):
    """INV-1 + INV-2 — tổng của đơn ĐÚNG BẰNG tổng các dòng của nó."""
    persist(engine, [
        pair("BH9", product="Tủ lạnh", row=6, quantity="2", sales="10000000"),
        pair("BH9", product="Máy giặt", row=7, quantity="3", sales="7000000"),
    ])
    order = sq.order_list(engine, **JANUARY)[0]
    detail = sq.order_detail(engine, "BH9", **JANUARY)

    assert order["lines"] == 2
    assert order["quantity"] == Decimal("5") == sum(
        line["quantity"] for line in detail["lines_detail"])
    assert order["total_sales"] == Decimal("17000000") == sum(
        line["total_sales"] for line in detail["lines_detail"])


# --- CHECK-PRA004-03 · Oracle B và Oracle C ------------------------------

def test_the_pure_auto_order_bh62063_reads_exactly_as_the_oracle(golden_engine):
    """Oracle B — đơn AUTO thuần, coverage ĐẦY ĐỦ 1/1, không lý do nào."""
    detail = sq.order_detail(golden_engine, "BH62063")

    assert detail["review"] is False
    assert detail["lines"] == 1
    assert (detail["sale_date_from"], detail["sale_date_to"]) == (
        date(2026, 1, 2), date(2026, 1, 2))
    assert detail["quantity"] == Decimal("1")
    assert detail["total_sales"] == Decimal("7500000")
    assert (detail["accounting_profit"], detail["accounting_lines"]) == (
        Decimal("500000"), 1)
    assert (detail["kpi_profit"], detail["kpi_lines"]) == (Decimal("500000"), 1)

    line = detail["lines_detail"][0]
    assert line["accounting_purchase_price"] == Decimal("7000000")
    assert line["kpi_purchase_price"] == Decimal("7000000")
    assert line["reasons"] == []


def test_the_mixed_order_bh62439_is_review_even_though_one_line_is_auto(golden_engine):
    """Oracle C — ca TRỘN. Một triển khai lấy trạng thái dòng ĐẦU TIÊN vẫn
    tình cờ đúng ở đây (dòng đầu là PENDING), nên test kế tiếp canh phía kia."""
    detail = sq.order_detail(golden_engine, "BH62439")

    assert detail["review"] is True
    assert detail["lines"] == 4
    statuses = [line["status"] for line in detail["lines_detail"]]
    assert statuses.count("AUTO") == 1 and statuses.count("PENDING") == 3
    assert (detail["sale_date_from"], detail["sale_date_to"]) == (
        date(2026, 1, 8), date(2026, 1, 8))
    assert detail["quantity"] == Decimal("5")
    assert detail["total_sales"] == Decimal("66000000")
    assert len(detail["employees"]) == 1


def test_an_order_whose_first_line_is_auto_is_still_review(engine):
    """CHECK-PRA004-05(b) — canh CHÍNH nhánh mà oracle golden không canh được.

    Đơn dưới đây có dòng ĐẦU TIÊN là ``AUTO`` và dòng sau là ``PENDING``. Một
    triển khai đọc trạng thái của dòng đầu sẽ hiện nó là AUTO, và Owner sẽ tin
    một con số chưa chắc chắn.
    """
    persist(engine, [
        pair("BH7", product="Tủ lạnh", row=6, status="AUTO"),
        pair("BH7", product="Máy giặt", row=7, status="PENDING",
             purchase=None, kpi_purchase=None, accounting=None, kpi=None,
             reasons=("Missing.PurchasePrice",)),
    ])
    assert sq.order_list(engine, **JANUARY)[0]["review"] is True


def test_the_mixed_order_reports_partial_coverage_on_both_profits(golden_engine):
    """Cốt lõi của Blast Radius: 66 triệu doanh thu, nhưng CHỈ 1/4 dòng có
    thẩm quyền. Con số lợi nhuận đúng, mẫu số nói nó chỉ đúng cho một dòng."""
    detail = sq.order_detail(golden_engine, "BH62439")

    assert (detail["accounting_profit"], detail["accounting_lines"],
            detail["lines"]) == (Decimal("500000"), 1, 4)
    assert (detail["kpi_profit"], detail["kpi_lines"],
            detail["lines"]) == (Decimal("400000"), 1, 4)


def test_the_three_pending_lines_of_bh62439_carry_no_value_at_all(golden_engine):
    """INV-6 ở tầng dữ liệu: mọi giá vốn và mọi lợi nhuận của ba dòng PENDING
    là ``NULL``. Tầng truy vấn KHÔNG coalesce chúng về ``0``."""
    pending = [line for line in sq.order_detail(golden_engine, "BH62439")["lines_detail"]
               if line["status"] == "PENDING"]
    assert len(pending) == 3
    for line in pending:
        assert line["accounting_purchase_price"] is None
        assert line["kpi_purchase_price"] is None
        assert line["accounting_profit"] is None
        assert line["eligible_kpi_profit"] is None


def test_the_auto_line_of_bh62439_carries_both_purchase_prices(golden_engine):
    """Hai giá vốn là hai CƠ SỞ khác nhau cho hai lợi nhuận (mục 12.C). Ở dòng
    này chúng TRÙNG số — đó là quan sát, không phải bằng chứng luôn trùng."""
    auto = next(line for line in sq.order_detail(golden_engine, "BH62439")["lines_detail"]
                if line["status"] == "AUTO")
    assert auto["quantity"] == Decimal("2")
    assert auto["sell_price"] == Decimal("10500000")
    assert auto["discount"] == Decimal("100000")
    assert auto["total_sales"] == Decimal("20900000")
    assert auto["accounting_purchase_price"] == Decimal("10250000")
    assert auto["kpi_purchase_price"] == Decimal("10250000")
    assert auto["accounting_profit"] == Decimal("500000")
    assert auto["eligible_kpi_profit"] == Decimal("400000")


def test_the_persisted_reason_codes_of_bh62439_are_read_back_in_order(golden_engine):
    """Ba dòng PENDING, mỗi dòng ĐÚNG 3 mã theo ĐÚNG thứ tự đã persist.

    Trước DEC-PAN-001 con số này là 5: hai mã `Pending.accounting_*` đi kèm.
    Chúng đã bị gỡ khỏi đường SINH reason (Reports không có nguồn giá nhập kế
    toán độc lập), nên một lần chạy MỚI như `golden_engine` persist ba mã.
    Đây KHÔNG phải backfill: các result version cũ vẫn giữ nguyên 5 mã của
    chúng — xem `RETIRED_PENDING_REASONS`.
    """
    expected = ["IDENTITY_SOURCES_UNAVAILABLE", "Missing.PurchasePrice",
                "Pending.eligible_kpi_profit"]
    pending = [line for line in sq.order_detail(golden_engine, "BH62439")["lines_detail"]
               if line["status"] == "PENDING"]
    assert [line["reasons"] for line in pending] == [expected] * 3


def test_the_line_revenue_is_the_persisted_value_not_a_recomputation(golden_engine):
    """Doanh thu dòng ĐỌC THẲNG ``total_sales`` đã lưu.

    Dòng AUTO của BH62439 có ``2 × 10.500.000 − 100.000 = 20.900.000``; nếu
    tầng truy vấn tự nhân lại, một đổi công thức ở engine sẽ khiến trang và sổ
    nói hai con số khác nhau mà không test nào bắt được.
    """
    auto = next(line for line in sq.order_detail(golden_engine, "BH62439")["lines_detail"]
                if line["status"] == "AUTO")
    assert auto["total_sales"] == Decimal("20900000")
    assert auto["total_sales"] != auto["quantity"] * auto["sell_price"]


def test_the_detail_lines_follow_the_order_they_had_in_the_book(golden_engine):
    """Thứ tự dòng ổn định và khớp thứ tự trong sổ gốc.

    Cả bốn dòng của BH62439 mang ``occurrence_index = 1`` (khác sản phẩm), nên
    riêng ``occurrence_index`` KHÔNG đủ để sắp xếp — test này đỏ nếu ai đó bỏ
    khoá phụ đi.
    """
    products = [line["product_raw"]
                for line in sq.order_detail(golden_engine, "BH62439")["lines_detail"]]
    assert products == [
        "Tủ lạnh Panasonic NR-BX471GPKV",
        "Máy Giặt Sấy LG FV1414H3BA",
        "Điều hòa Daikin FTHF25XVMV",
        "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV",
    ]


# --- Lợi nhuận: NULL, 0, và coverage một phần ----------------------------

def test_a_real_zero_profit_stays_a_real_zero(engine):
    """``0`` KHÔNG bị nhầm thành "chưa biết": nó vào tổng và vào coverage."""
    persist(engine, [pair("BH1", accounting="0", kpi="0")])
    order = sq.order_list(engine, **JANUARY)[0]
    assert order["accounting_profit"] == Decimal("0")
    assert order["accounting_lines"] == 1
    assert order["kpi_profit"] == Decimal("0")
    assert order["kpi_lines"] == 1


def test_an_order_with_no_authoritative_line_reports_no_profit_not_zero(engine):
    """Tập cộng rỗng ⟹ ``None``, và coverage vẫn nói TRUNG THỰC 0/N dòng."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, status="PENDING",
             accounting=None, kpi=None, reasons=("Missing.PurchasePrice",)),
        pair("BH1", product="Máy giặt", row=7, status="PENDING",
             accounting=None, kpi=None, reasons=("Missing.PurchasePrice",)),
    ])
    order = sq.order_list(engine, **JANUARY)[0]
    assert order["accounting_profit"] is None and order["accounting_lines"] == 0
    assert order["kpi_profit"] is None and order["kpi_lines"] == 0
    assert order["lines"] == 2


def test_a_pending_line_with_a_kpi_value_still_stays_out_of_the_kpi_total(engine):
    """LN KPI chỉ cộng dòng ``AUTO`` — kể cả khi dòng ``PENDING`` có sẵn số."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, status="AUTO", kpi="1000000"),
        pair("BH1", product="Máy giặt", row=7, status="PENDING", kpi="9000000",
             reasons=("Missing.PurchasePrice",)),
    ])
    order = sq.order_list(engine, **JANUARY)[0]
    assert order["kpi_profit"] == Decimal("1000000")
    assert (order["kpi_lines"], order["lines"]) == (1, 2)
    # LN kế toán thì cộng MỌI dòng có giá trị — hai coverage có tử số khác nhau.
    assert order["accounting_lines"] == 2


# --- Nhân viên -----------------------------------------------------------

def test_an_order_touched_by_two_employees_reports_both(engine):
    """Mục 9 — KHÔNG chọn chủ đơn. Fixture golden chỉ có một tên vì đã ẩn danh,
    nên nhánh này chỉ kiểm được bằng dữ liệu tổng hợp (FIND-PRA004-03)."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, employee="VuHanhLy"),
        pair("BH1", product="Máy giặt", row=7, employee="TranMinh"),
    ])
    assert sq.order_list(engine, **JANUARY)[0]["employees"] == ["TranMinh", "VuHanhLy"]


def test_a_missing_employee_is_one_condition_not_two(engine):
    """``NULL`` và chuỗi rỗng là CÙNG một tình trạng nghiệp vụ."""
    persist(engine, [
        pair("BH1", product="Tủ lạnh", row=6, employee=None),
        pair("BH1", product="Máy giặt", row=7, employee=""),
    ])
    assert sq.order_list(engine, **JANUARY)[0]["employees"] == [None]


# --- Kỳ ------------------------------------------------------------------

def test_a_month_shows_only_the_orders_of_that_month(engine):
    """Bộ lọc kỳ là bộ lọc THẬT, và danh sách xếp theo ngày bán mới nhất trước."""
    persist(engine, [pair("BH1", day=5, row=6), pair("BH2", day=20, row=7),
                     pair("BH3", day=12, month=2, row=8)])

    assert [order["order_key"] for order in sq.order_list(engine, **JANUARY)] == \
        ["BH2", "BH1"]
    assert [order["order_key"] for order in sq.order_list(engine, **FEBRUARY)] == ["BH3"]
    assert len(sq.order_list(engine)) == 3


def test_a_line_without_a_sale_date_falls_out_of_every_period(engine):
    """``sale_date IS NOT NULL`` có mặt kể cả ở "Toàn bộ dữ liệu" — GIỐNG HỆT
    PRA-003, để hai trang không bao giờ nói hai tập đơn khác nhau."""
    persist(engine, [pair("BH1", day=5, row=6), pair("BH2", day=None, row=7)])
    assert [order["order_key"] for order in sq.order_list(engine)] == ["BH1"]
    assert sq.order_detail(engine, "BH2") is None


def test_an_order_outside_the_selected_month_is_not_reachable_by_detail(engine):
    """Chi tiết dùng CÙNG bộ lọc kỳ với danh sách: một đơn không có trong danh
    sách của kỳ cũng không mở được từ kỳ đó."""
    persist(engine, [pair("BH1", day=5)])
    assert sq.order_detail(engine, "BH1", **JANUARY) is not None
    assert sq.order_detail(engine, "BH1", **FEBRUARY) is None


def test_an_unknown_order_key_has_no_detail(engine):
    persist(engine, [pair("BH1")])
    assert sq.order_detail(engine, "BH-KHONG-CO") is None


# --- Ranh giới PII và nguồn ----------------------------------------------

def test_the_sales_query_module_never_selects_a_personal_data_column():
    """Hàng rào PII RIÊNG của PRA-004 — hẹp hơn PRA-003 ĐÚNG một trường.

    ``product_raw`` CỐ Ý vắng mặt khỏi danh sách: trang chi tiết cần tên sản
    phẩm để phân biệt các dòng của một đơn, và ``anonymize.py`` (đo trên
    workbook production thật) xếp nó là dữ liệu NGHIỆP VỤ. Xem mục 14.4.
    """
    text = QUERY_MODULE.read_text(encoding="utf-8")
    code = "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))
    for column in ("imei", "note_raw", "employee_raw", "customer", "phone", "address"):
        assert not re.search(rf"\.c\.{column}\b", code), column


def test_the_sales_query_module_does_read_product_raw():
    """Khẳng định PHÍA CÒN LẠI: nếu ai đó "dọn dẹp" cho khớp hàng rào PRA-003,
    trang chi tiết mất khả năng phân biệt các dòng và test này đỏ trước."""
    assert re.search(r"\.c\.product_raw\b", QUERY_MODULE.read_text(encoding="utf-8"))


def test_no_legacy_row_can_reach_the_sales_pages(golden_engine):
    """Tách nguồn là tính chất CẤU TRÚC: ba bảng pipeline đều mang
    ``CheckConstraint(origin = 'PIPELINE_GENERATED')`` nên dòng
    ``LEGACY_REFERENCE`` KHÔNG THỂ tồn tại trong đó về mặt vật lý."""
    from tools.db.schema import order_line_current

    with golden_engine.connect() as connection:
        from sqlalchemy import distinct, select

        origins = {row[0] for row in connection.execute(
            select(distinct(order_line_current.c.origin)))}
    assert origins == {"PIPELINE_GENERATED"}


def test_a_corrupt_reason_payload_degrades_to_no_reason_not_to_a_crash(engine):
    """JSON hỏng ⟹ danh sách rỗng. Dòng vẫn hiện đúng ``PENDING``: mất lý do
    là mất một phần câu trả lời, mất cả trang là mất tất cả."""
    assert sq._reasons("{ khong phai json") == []
    assert sq._reasons(None) == []
    assert sq._reasons('["A", "A", "B"]') == ["A", "B"]
