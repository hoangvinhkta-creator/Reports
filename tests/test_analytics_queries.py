"""TASK-PRA-003 — ngữ nghĩa tầng truy vấn (CHECK-PRA003-01/03/04/05/08/09/10).

Dữ liệu ở đây là dữ liệu TỔNG HỢP CÓ KIỂM SOÁT, dựng bằng chính hàm dựng dòng
của ``tests/test_snapshot_repository.py``. Nó phủ đúng hai vùng mà oracle
golden KHÔNG phủ được (fixture golden chỉ có MỘT nhân viên và MỌI dòng đều
``price_source = Pending``): phân rã nhiều nhân viên, và các giá trị lợi nhuận
khác ``NULL``. Không có fixture nào ở đây được gọi là "giống production".
"""

from __future__ import annotations

import ast
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.web import analytics_queries as aq
from app.web import history_store
from tests.test_snapshot_repository import result_line, source_line, write

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERY_MODULE = REPO_ROOT / "app/web/analytics_queries.py"


@pytest.fixture
def repository(history_engine):
    return history_store.SnapshotRepository(history_engine)


@pytest.fixture
def engine(repository):
    return repository.engine


def line(order, *, day=5, month=1, employee="VuHanhLy", group="G1", status="AUTO",
         quantity="1", sales="8000000", kpi="3000000", accounting="2000000",
         product="Tủ lạnh", occurrence=1):
    """Một cặp (dòng nguồn, dòng kết quả) đã khớp khoá, tuỳ biến đủ để dựng
    mọi tình huống mà tầng trình bày phải chịu được."""
    sale_date = date(2026, month, day) if day else None
    source = source_line(order, product, occurrence, sale_date=sale_date,
                         sell_price=sales, quantity=Decimal(quantity))
    result = result_line(source, status=status)
    result = type(result)(**{
        **{field: getattr(result, field) for field in result.__dataclass_fields__},
        "employee_normalized": employee, "employee_group": group,
        "total_sales": Decimal(sales),
        "eligible_kpi_profit": None if kpi is None else Decimal(kpi),
        "accounting_profit": None if accounting is None else Decimal(accounting),
    })
    return source, result


def persist(repository, pairs, *, run_id="run-1", at="2026-02-01T00:00:00",
            fingerprint="fp-a"):
    sources = [pair[0] for pair in pairs]
    return write(repository, sources, run_id=run_id, created_at=at,
                 fingerprint=fingerprint, results=[pair[1] for pair in pairs])


JANUARY = {"date_from": date(2026, 1, 1), "date_to": date(2026, 1, 31)}


# --- CHECK-PRA003-01 · trạng thái hiện hành, không double-count -----------

def test_the_query_module_never_writes_and_never_reads_a_run_summary():
    """Bằng chứng CẤU TRÚC: tầng truy vấn không có đường nào để ghi, và không
    có đường nào để cộng số của từng run lại với nhau."""
    tree = ast.parse(QUERY_MODULE.read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) for alias in node.names}
    # Không import được ``insert``/``update``/``delete`` thì không dựng được
    # câu ghi nào; không ``begin()``/``commit()`` thì kể cả SQL thô cũng không
    # bao giờ được commit (SQLAlchemy 2.0 không autocommit).
    assert imported.isdisjoint({"insert", "update", "delete", "text"})
    called = {node.func.attr for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert called.isdisjoint({"begin", "commit", "execution_options"})
    assert "connect" in called, "tầng này chỉ mở kết nối CHỈ-ĐỌC"

    # Chỉ xét ĐỊNH DANH, không xét docstring/comment — hai tên bảng dưới đây
    # được NHẮC TỚI trong tài liệu của chính module để nói rõ vì sao không dùng.
    names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    names |= {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {alias.name for node in ast.walk(tree)
              if isinstance(node, ast.ImportFrom) for alias in node.names}
    assert "summary_json" not in names, "cộng summary_json qua các run là double-count"
    assert "source_snapshot" not in names


def test_a_half_month_book_then_the_full_month_totals_the_full_month_alone(repository):
    """Đẳng thức, không phải niềm tin: state(A rồi B) == state(B một mình)."""
    half = [line("BH1", day=3), line("BH2", day=4)]
    full = half + [line("BH3", day=20), line("BH4", day=21)]

    persist(repository, half, run_id="seq-1", fingerprint="fp-a")
    persist(repository, full, run_id="seq-2", at="2026-02-02T00:00:00",
            fingerprint="fp-b")
    sequential = aq.period_totals(repository.engine, **JANUARY)

    alone = history_store.SnapshotRepository(
        _fresh_engine())
    persist(alone, full, run_id="only-1", fingerprint="fp-b")

    assert sequential == aq.period_totals(alone.engine, **JANUARY)
    assert (sequential["lines"], sequential["orders"]) == (4, 4)
    assert sequential["total_sales"] == Decimal("32000000")


def _fresh_engine():
    from sqlalchemy import create_engine

    import tools.db as history_db

    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


def test_only_the_current_version_of_a_changed_line_is_counted(repository):
    """``SOURCE_CHANGED``: version cũ vẫn nằm trong bảng audit nhưng KHÔNG
    được cộng — nếu cộng cả hai thì một lần sửa giá thành hai lần bán."""
    persist(repository, [line("BH1", sales="8000000")], run_id="v1", fingerprint="fp-a")
    persist(repository, [line("BH1", sales="9000000")], run_id="v2",
            at="2026-02-02T00:00:00", fingerprint="fp-b")

    totals = aq.period_totals(repository.engine, **JANUARY)
    assert totals["lines"] == 1
    assert totals["total_sales"] == Decimal("9000000")


def test_reuploading_the_same_book_moves_nothing(repository):
    pairs = [line("BH1"), line("BH2", day=9)]
    persist(repository, pairs, run_id="run-1", fingerprint="fp-a")
    before = aq.period_totals(repository.engine, **JANUARY)
    persist(repository, pairs, run_id="run-2", at="2026-02-02T00:00:00",
            fingerprint="fp-a")
    assert aq.period_totals(repository.engine, **JANUARY) == before


# --- CHECK-PRA003-03 · NULL không phải 0 ---------------------------------

def test_an_empty_period_returns_none_for_money_not_zero(repository):
    """Bảo vệ khỏi việc tái dụng khuôn coalesce của ``current_totals``
    (``history_store.py:1073``): không dòng nào ⟹ ``None``, KHÔNG ``Decimal(0)``."""
    persist(repository, [line("BH1", month=1)])
    empty = aq.period_totals(repository.engine, date_from=date(2026, 3, 1),
                             date_to=date(2026, 3, 31))
    assert empty["lines"] == 0 and empty["orders"] == 0
    for field in ("total_sales", "quantity", "kpi_profit", "accounting_profit"):
        assert empty[field] is None, field
        assert empty[field] != Decimal("0")


def test_a_period_with_lines_but_no_profit_values_returns_none(repository):
    """Kỳ golden thu nhỏ: có dòng, có doanh thu, nhưng CHƯA có giá nhập nào —
    lợi nhuận phải là ``None`` để trang hiện ``—``, không phải "lãi 0 đồng"."""
    persist(repository, [line("BH1", status="PENDING", kpi=None, accounting=None),
                         line("BH2", day=9, status="PENDING", kpi=None, accounting=None)])
    totals = aq.period_totals(repository.engine, **JANUARY)
    assert totals["lines"] == 2
    assert totals["total_sales"] == Decimal("16000000")
    assert totals["kpi_profit"] is None
    assert totals["accounting_profit"] is None
    assert (totals["kpi_lines"], totals["accounting_lines"]) == (0, 0)


# --- CHECK-PRA003-04 · LN KPI chỉ AUTO + hai coverage --------------------

def test_a_pending_line_with_a_kpi_profit_never_enters_the_kpi_total(repository):
    """Quy tắc P1 ở dạng gay gắt nhất: dòng PENDING CÓ ``eligible_kpi_profit``
    khác ``NULL``. Nó vẫn phải bị loại — "chỉ cộng dòng AUTO" là một quy tắc
    trình bày có định nghĩa chặt, không phải một phép lọc tuỳ tiện."""
    persist(repository, [
        line("BH1", status="AUTO", kpi="3000000"),
        line("BH2", day=9, status="PENDING", kpi="5000000"),
    ])
    totals = aq.period_totals(repository.engine, **JANUARY)

    assert totals["kpi_profit"] == Decimal("3000000"), "dòng PENDING đã lọt vào tổng"
    assert (totals["kpi_lines"], totals["lines"]) == (1, 2)


def test_the_two_coverages_have_the_same_denominator_but_count_different_lines(
    repository,
):
    """Hai coverage KHÁC nhau ở TỬ SỐ và phải được trả về tách biệt: một dòng
    có thể ``PENDING`` (ngoài LN KPI) mà vẫn có lợi nhuận kế toán."""
    persist(repository, [
        line("BH1", status="AUTO", kpi="3000000", accounting="2000000"),
        line("BH2", day=9, status="PENDING", kpi=None, accounting="1000000"),
        line("BH3", day=10, status="PENDING", kpi=None, accounting=None),
    ])
    totals = aq.period_totals(repository.engine, **JANUARY)

    assert totals["lines"] == 3
    assert (totals["kpi_lines"], totals["kpi_profit"]) == (1, Decimal("3000000"))
    assert (totals["accounting_lines"], totals["accounting_profit"]) \
        == (2, Decimal("3000000"))
    assert totals["kpi_lines"] != totals["accounting_lines"]


def test_a_kpi_coverage_of_zero_over_many_lines_is_a_valid_answer(repository):
    """Quy tắc P5: ``0/3`` nói "chưa có gì chắc chắn", khác hẳn "lãi bằng 0"."""
    persist(repository, [line(f"BH{i}", day=i + 1, status="PENDING", kpi=None)
                         for i in range(3)])
    totals = aq.period_totals(repository.engine, **JANUARY)
    assert (totals["kpi_lines"], totals["lines"]) == (0, 3)
    assert totals["kpi_profit"] is None


# --- CHECK-PRA003-04 · AUTO/Review THEO ĐƠN ------------------------------

def test_an_order_is_review_when_any_single_line_of_it_is_pending(repository):
    """Đếm theo ĐƠN, không theo dòng: đơn hai dòng mà một dòng PENDING là một
    đơn cần kiểm tra, không phải nửa đơn."""
    persist(repository, [
        line("BH1", product="Tủ lạnh", status="AUTO"),
        line("BH1", product="Máy giặt", occurrence=1, status="PENDING"),
        line("BH2", day=9, status="AUTO"),
    ])
    totals = aq.period_totals(repository.engine, **JANUARY)

    assert totals["orders"] == 2
    assert (totals["auto_orders"], totals["review_orders"]) == (1, 1)
    assert totals["auto_orders"] + totals["review_orders"] == totals["orders"]


# --- CHECK-PRA003-05 · đối soát nhân viên --------------------------------

ADDITIVE = ("lines", "quantity", "total_sales", "kpi_profit", "accounting_profit")


def _summed(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    return sum(values) if values else None


def test_employee_rows_add_up_to_the_period_totals_on_the_additive_metrics(repository):
    persist(repository, [
        line("BH1", employee="VuHanhLy", quantity="2", sales="8000000"),
        line("BH2", day=9, employee="TranB", quantity="3", sales="5000000"),
        line("BH3", day=10, employee="TranB", status="PENDING", kpi=None,
             accounting=None, quantity="1", sales="1000000"),
    ])
    totals = aq.period_totals(repository.engine, **JANUARY)
    rows = aq.employee_totals(repository.engine, **JANUARY)

    assert len(rows) == 2
    for field in ADDITIVE:
        assert _summed(rows, field) == totals[field], field


def test_the_order_column_is_deliberately_not_additive(repository):
    """O-D′: một đơn có hai nhân viên được đếm ở CẢ HAI dòng. Test này khoá
    hành vi đó lại để không ai "sửa" nó thành một bất biến sai."""
    persist(repository, [
        line("BH1", product="Tủ lạnh", employee="VuHanhLy"),
        line("BH1", product="Máy giặt", employee="TranB"),
    ])
    totals = aq.period_totals(repository.engine, **JANUARY)
    rows = aq.employee_totals(repository.engine, **JANUARY)

    assert totals["orders"] == 1
    assert sum(row["orders"] for row in rows) == 2
    assert sum(row["orders"] for row in rows) != totals["orders"]


def test_lines_without_an_employee_become_one_row_and_are_never_dropped(repository):
    persist(repository, [
        line("BH1", employee="VuHanhLy"),
        line("BH2", day=9, employee=None),
        line("BH3", day=10, employee=""),
    ])
    rows = aq.employee_totals(repository.engine, **JANUARY)
    unknown = [row for row in rows if row["employee"] is None]

    assert len(unknown) == 1, "NULL và chuỗi rỗng phải gộp thành MỘT dòng"
    assert unknown[0]["lines"] == 2
    assert sum(row["lines"] for row in rows) == 3


def test_the_employee_group_is_carried_through_unchanged(repository):
    persist(repository, [line("BH1", employee="VuHanhLy", group="NOI_THANH")])
    assert aq.employee_totals(repository.engine, **JANUARY)[0]["employee_group"] \
        == "NOI_THANH"


# --- CHECK-PRA003-08 · mô hình kỳ ----------------------------------------

def test_available_periods_lists_only_months_that_really_have_lines(repository):
    persist(repository, [line("BH1", month=1), line("BH2", month=3, day=4)])
    assert aq.available_periods(repository.engine) == [(2026, 3), (2026, 1)]


def test_available_periods_on_an_empty_database_is_empty_not_an_error(repository):
    assert aq.available_periods(repository.engine) == []


def test_a_month_with_no_lines_at_all_is_absent_from_the_period_list(repository):
    persist(repository, [line("BH1", month=1)])
    assert (2025, 12) not in aq.available_periods(repository.engine)
    previous = aq.period_totals(repository.engine,
                                **dict(zip(("date_from", "date_to"),
                                           aq.month_bounds(2025, 12))))
    assert previous["lines"] == 0
    assert previous["total_sales"] is None


def test_month_bounds_and_previous_month_cross_the_year_correctly():
    assert aq.month_bounds(2026, 2) == (date(2026, 2, 1), date(2026, 2, 28))
    assert aq.month_bounds(2024, 2)[1] == date(2024, 2, 29)
    assert aq.previous_month(2026, 1) == (2025, 12)
    assert aq.previous_month(2026, 9) == (2026, 8)


def test_the_whole_dataset_view_counts_every_dated_line(repository):
    persist(repository, [line("BH1", month=1), line("BH2", month=6, day=4)])
    everything = aq.period_totals(repository.engine)
    assert everything["lines"] == 2
    assert aq.period_totals(repository.engine, **JANUARY)["lines"] == 1


# --- CHECK-PRA003-09 · dòng thiếu ngày bán -------------------------------

def test_lines_without_a_sale_date_fall_out_of_every_period_and_are_counted(repository):
    persist(repository, [line("BH1", month=1), line("BH2", day=None)])

    assert aq.period_totals(repository.engine, **JANUARY)["lines"] == 1
    assert aq.period_totals(repository.engine)["lines"] == 1, \
        "dòng không ngày bán rơi khỏi cả 'toàn bộ dữ liệu' — vì thế phải đếm riêng"
    assert aq.undated_lines(repository.engine) == 1


def test_the_undated_count_ignores_the_selected_period(repository):
    persist(repository, [line("BH1", day=None), line("BH2", day=None,
                                                     product="Máy giặt")])
    assert aq.undated_lines(repository.engine) == 2
    assert aq.available_periods(repository.engine) == []


# --- CHECK-PRA003-10 · không đọc cột PII ---------------------------------

def test_the_query_module_never_selects_a_personal_data_column():
    text = QUERY_MODULE.read_text(encoding="utf-8")
    code = "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))
    for column in ("imei", "note_raw", "employee_raw", "product_raw", "customer",
                   "phone", "address"):
        assert not re.search(rf"\.c\.{column}\b", code), column
