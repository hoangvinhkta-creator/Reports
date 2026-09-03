"""TASK-PRA-003 — tổng hợp CHỈ-ĐỌC trên trạng thái hiện hành của pipeline.

Tầng này là nơi DUY NHẤT của PRA-003 nói SQL. Ba kỷ luật, không cái nào là
khuyến nghị:

1. **CHỈ ĐỌC.** Không một câu ``INSERT``/``UPDATE``/``DELETE`` nào. Blast
   radius của PRA-003 là "một ô hiển thị sai", không bao giờ là "dữ liệu đã
   lưu bị ghi đè".
2. **Chỉ trạng thái hiện hành.** Mọi tổng đi qua ``order_line_current`` và hai
   con trỏ ``current_source_version_id`` / ``current_result_version_id``. PK
   của bảng đó là ``(order_key, product_key, occurrence_index)`` nên mỗi khoá
   góp đúng MỘT dòng — no-double-count là tính chất của cấu trúc bảng, không
   phải của việc câu truy vấn có nhớ ``DISTINCT`` hay không. TUYỆT ĐỐI KHÔNG
   cộng ``source_snapshot.summary_json`` qua các run: nó là số của MỘT lần
   chạy, cộng lại chính là double-count mà TASK-PRA-002 sinh ra để chống.
3. **``NULL`` không phải ``0``.** Khác ``current_totals()``
   (``app/web/history_store.py:1073``) vốn coalesce doanh thu thiếu về
   ``Decimal("0")``, tầng này KHÔNG coalesce gì cả. Tập cộng rỗng ⟹ ``None``,
   và tầng trình bày hiển thị ``—``. "Chưa có gì chắc chắn" khác hẳn "lãi
   bằng không"; một dashboard nói nhầm hai điều đó sẽ khiến Owner ra quyết
   định trên một con số không tồn tại.

Cột KHÔNG được đọc ở đây (PII / dữ liệu cá nhân theo
``governance/product/17_DATA_GOVERNANCE_PRIVACY.md``): ``imei``, ``note_raw``,
``employee_raw``, ``product_raw``. Danh sách này được test canh bằng grep.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Optional

from sqlalchemy import case, distinct, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.web.history_store import HistoryUnavailableError
from tools.db.schema import (
    order_line_current, order_line_result_version, order_line_source_version,
)

_STATUS = order_line_result_version.c.status
_KPI_PROFIT = order_line_result_version.c.eligible_kpi_profit
_ACCOUNTING_PROFIT = order_line_result_version.c.accounting_profit

# ``employee_normalized`` rỗng và ``NULL`` là CÙNG một tình trạng nghiệp vụ
# ("chưa xác định được ai bán"). Gộp ngay ở tầng SQL để chúng thành MỘT dòng
# duy nhất trong bảng nhân viên, thay vì hai dòng trống cạnh nhau.
_EMPLOYEE = case(
    (order_line_result_version.c.employee_normalized == "", None),
    else_=order_line_result_version.c.employee_normalized,
).label("employee")


def _metrics() -> tuple:
    """Bảy chỉ tiêu tổng hợp, dùng chung cho tổng kỳ và cho từng nhân viên.

    Không hàm nào ở đây coalesce về ``0``: ``SUM`` trên tập rỗng trả ``NULL``
    và đó chính là câu trả lời đúng cho "chưa có giá trị nào".
    """
    return (
        func.count().label("lines"),
        func.count(distinct(order_line_current.c.order_key)).label("orders"),
        func.sum(order_line_source_version.c.quantity).label("quantity"),
        func.sum(order_line_result_version.c.total_sales).label("total_sales"),
        # LN KPI chỉ cộng dòng AUTO (D1/P1). Một dòng PENDING có
        # ``eligible_kpi_profit`` khác NULL vẫn KHÔNG được vào tổng.
        func.sum(case((_STATUS == "AUTO", _KPI_PROFIT))).label("kpi_profit"),
        func.sum(case((_STATUS == "AUTO", 1), else_=0)).label("kpi_lines"),
        # LN kế toán chỉ cộng dòng có giá trị (P2); ``SUM`` tự bỏ qua NULL.
        func.sum(_ACCOUNTING_PROFIT).label("accounting_profit"),
        func.sum(case((_ACCOUNTING_PROFIT.is_not(None), 1), else_=0))
            .label("accounting_lines"),
    )


def _joined():
    """``order_line_current`` nối sang ĐÚNG version hiện hành của nó."""
    return order_line_current.join(
        order_line_result_version,
        order_line_result_version.c.id == order_line_current.c.current_result_version_id,
    ).join(
        order_line_source_version,
        order_line_source_version.c.id == order_line_current.c.current_source_version_id,
    )


def _period(date_from: Optional[date], date_to: Optional[date]) -> list:
    """Điều kiện kỳ. ``sale_date IS NOT NULL`` LUÔN có mặt, kể cả với "Toàn bộ
    dữ liệu" — kỳ đó là khoảng ``min(sale_date)…max(sale_date)``, không phải
    "mọi dòng trong bảng". Dòng thiếu ngày bán vì vậy rơi khỏi MỌI kỳ một
    cách nhất quán, và ``undated_lines()`` là chỗ DUY NHẤT phơi chúng ra."""
    conditions = [order_line_current.c.sale_date.is_not(None)]
    if date_from is not None:
        conditions.append(order_line_current.c.sale_date >= date_from)
    if date_to is not None:
        conditions.append(order_line_current.c.sale_date <= date_to)
    return conditions


def _read(engine: Engine, statement) -> list[dict]:
    """Lỗi database KHÔNG BAO GIỜ được biến thành "chưa có dữ liệu" — một
    trang rỗng vì mất kết nối trông y hệt trang rỗng vì chưa nhập gì."""
    try:
        with engine.connect() as connection:
            return [dict(row._mapping) for row in connection.execute(statement)]
    except SQLAlchemyError as exc:
        raise HistoryUnavailableError(str(exc)) from exc


def _shaped(row: dict) -> dict:
    """Ép kiểu các ô ĐẾM về ``int`` và giữ nguyên ``None`` của các ô TIỀN."""
    return {
        "lines": int(row["lines"] or 0),
        "orders": int(row["orders"] or 0),
        "quantity": row["quantity"],
        "total_sales": row["total_sales"],
        "kpi_profit": row["kpi_profit"],
        "kpi_lines": int(row["kpi_lines"] or 0),
        "accounting_profit": row["accounting_profit"],
        "accounting_lines": int(row["accounting_lines"] or 0),
    }


def month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def available_periods(engine: Engine) -> list[tuple[int, int]]:
    """Các tháng THỰC SỰ có dòng hiện hành, mới nhất trước.

    Đọc ``DISTINCT sale_date`` rồi rút tháng trong Python thay vì gọi hàm
    ngày của database: số ngày phân biệt luôn nhỏ, và câu truy vấn giữ được
    tính di động giữa SQLite (dev/test) và PostgreSQL (production) mà không
    phải viết hai phương ngữ SQL.
    """
    rows = _read(engine, select(distinct(order_line_current.c.sale_date))
                 .where(order_line_current.c.sale_date.is_not(None)))
    months = {(value.year, value.month)
              for value in (row["sale_date"] for row in rows) if value is not None}
    return sorted(months, reverse=True)


def period_totals(
    engine: Engine, *, date_from: Optional[date] = None, date_to: Optional[date] = None,
) -> dict:
    """Tổng của một kỳ trên trạng thái hiện hành.

    ``auto_orders`` / ``review_orders`` đếm theo ĐƠN, không theo dòng: một đơn
    là "cần kiểm tra" khi có ÍT NHẤT MỘT dòng ``PENDING``. Số này dẫn xuất từ
    ``order_line_result_version.status`` của các version hiện hành, KHÔNG
    cộng số AUTO/Review mà từng run đã ghi trong ``summary_json``.
    """
    statement = select(*_metrics()).select_from(_joined())
    for condition in _period(date_from, date_to):
        statement = statement.where(condition)
    return {**_shaped(_read(engine, statement)[0]),
            **_order_status(engine, date_from, date_to)}


def _order_status(engine: Engine, date_from, date_to) -> dict:
    pending = func.max(case((_STATUS == "PENDING", 1), else_=0)).label("has_pending")
    per_order = select(order_line_current.c.order_key, pending).select_from(_joined())
    for condition in _period(date_from, date_to):
        per_order = per_order.where(condition)
    per_order = per_order.group_by(order_line_current.c.order_key).subquery()
    row = _read(engine, select(
        func.count().label("orders"),
        func.sum(per_order.c.has_pending).label("review"),
    ).select_from(per_order))[0]
    review = int(row["review"] or 0)
    return {"review_orders": review, "auto_orders": int(row["orders"] or 0) - review}


def undated_lines(engine: Engine) -> int:
    """Dòng hiện hành KHÔNG có ``sale_date`` — đếm KHÔNG lọc kỳ.

    ``sale_date`` nullable và mọi bộ lọc kỳ dùng ``>=``/``<=``, nên các dòng
    này rơi khỏi MỌI kỳ trong im lặng. Không phơi con số ra thì tổng của
    "Toàn bộ dữ liệu" có thể nhỏ hơn tổng thật mà không ai biết.
    """
    return int(_read(engine, select(func.count().label("total"))
                     .select_from(order_line_current)
                     .where(order_line_current.c.sale_date.is_(None)))[0]["total"] or 0)


def employee_totals(
    engine: Engine, *, date_from: Optional[date] = None, date_to: Optional[date] = None,
) -> list[dict]:
    """Cùng bảy chỉ tiêu, nhóm theo nhân viên đã chuẩn hoá.

    ``GROUP BY`` là một phân hoạch của cùng tập dòng, nên năm chỉ tiêu CỘNG
    ĐƯỢC (dòng, số lượng, doanh thu, hai lợi nhuận) cộng lại đúng bằng tổng
    kỳ. Cột ``orders`` thì KHÔNG: một đơn có hai nhân viên được đếm ở cả hai
    dòng — đó là sự thật nghiệp vụ, và trang phải nói rõ nó.
    """
    group = order_line_result_version.c.employee_group
    statement = (
        select(_EMPLOYEE, group.label("employee_group"), *_metrics())
        .select_from(_joined())
    )
    for condition in _period(date_from, date_to):
        statement = statement.where(condition)
    rows = _read(engine, statement.group_by(_EMPLOYEE, group)
                 .order_by(func.sum(order_line_result_version.c.total_sales).desc()))
    return [
        {"employee": row["employee"], "employee_group": row["employee_group"],
         **_shaped(row)}
        for row in rows
    ]


__all__ = [
    "available_periods", "employee_totals", "month_bounds", "period_totals",
    "previous_month", "undated_lines",
]
