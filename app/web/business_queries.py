"""PHB-03 — đọc các dòng hàng hiện hành và dựng `BusinessLine`.

Tầng này là nơi DUY NHẤT của PHB-03 nói SQL ĐỌC. Nó giữ nguyên ba kỷ luật đã
freeze ở `analytics_queries` (`TASK-PRA-003`) và `sales_queries`
(`TASK-PRA-004`):

1. **CHỈ ĐỌC.** Không `INSERT`/`UPDATE`/`DELETE` nào. Mọi đường ghi của PHB-03
   nằm ở `app/web/business_store.py`, tách bạch và kiểm được bằng cấu trúc.
2. **Chỉ trạng thái hiện hành.** Mọi dòng đi qua `order_line_current` và hai
   con trỏ `current_source_version_id`/`current_result_version_id`. PK của
   bảng đó là `(order_key, product_key, occurrence_index)` nên mỗi khoá góp
   ĐÚNG một dòng. Không bao giờ cộng `summary_json` qua các run.
3. **`NULL` không phải `0`.** Không coalesce gì. Việc phân biệt "chưa biết"
   với "bằng không" được `business_metrics` giữ tiếp.

## Hàng rào PII — hẹp hơn PRA-003 đúng một trường, và nói ra

Tầng này ĐỌC `product_raw`, giống `sales_queries` và vì cùng một lý do đã
được nghiệm thu (`TASK-PRA-004`, frozen contract mục 14.4): danh sách "dòng
còn thiếu giá nhập" và danh sách "mặt hàng cần tick Gia dụng" phải cho Owner
biết ĐANG NÓI VỀ MẶT HÀNG NÀO. `canonical_product_code` rỗng trên dữ liệu
thật nên không thay thế được, và `product_key` là một hash.

Cột KHÔNG được đọc ở đây (PII theo
`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`): `imei`, `note_raw`,
`employee_raw`, và mọi cột khách hàng. Danh sách này được test canh bằng grep.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import distinct, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.modules.reporting.business_metrics import BusinessLine
from app.modules.reporting.rate_routing import ConversionRateRouter
from app.web.history_store import HistoryUnavailableError
from tools.db.schema import (
    order_line_current, order_line_result_version, order_line_source_version,
)

_RESULT = order_line_result_version.c
_SOURCE = order_line_source_version.c
_CURRENT = order_line_current.c


def _joined():
    """`order_line_current` nối sang ĐÚNG version hiện hành của nó."""
    return order_line_current.join(
        order_line_result_version,
        _RESULT.id == _CURRENT.current_result_version_id,
    ).join(
        order_line_source_version,
        _SOURCE.id == _CURRENT.current_source_version_id,
    )


def _period(date_from: Optional[date], date_to: Optional[date]) -> list:
    """`sale_date IS NOT NULL` LUÔN có mặt — dòng thiếu ngày bán rơi khỏi MỌI
    kỳ một cách nhất quán, đúng ngữ nghĩa kỳ đã freeze ở PRA-003."""
    conditions = [_CURRENT.sale_date.is_not(None)]
    if date_from is not None:
        conditions.append(_CURRENT.sale_date >= date_from)
    if date_to is not None:
        conditions.append(_CURRENT.sale_date <= date_to)
    return conditions


def _read(engine: Engine, statement) -> list[dict]:
    """Lỗi database KHÔNG BAO GIỜ được biến thành "chưa có dữ liệu"."""
    try:
        with engine.connect() as connection:
            return [dict(row._mapping) for row in connection.execute(statement)]
    except SQLAlchemyError as exc:
        raise HistoryUnavailableError(str(exc)) from exc


_COLUMNS = (
    _CURRENT.order_key, _CURRENT.product_key, _CURRENT.occurrence_index,
    _CURRENT.sale_date,
    _RESULT.status, _RESULT.employee_normalized, _RESULT.employee_group,
    _RESULT.lead_source_final, _RESULT.total_sales, _RESULT.kpi_purchase_price,
    _RESULT.kpi_purchase_provenance, _RESULT.eligible_kpi_profit,
    _RESULT.product_group_final, _RESULT.conversion_rate_final,
    _SOURCE.product_raw, _SOURCE.quantity, _SOURCE.sell_price, _SOURCE.discount,
)


def raw_lines(
    engine: Engine, *, date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[dict]:
    """Các dòng hiện hành của kỳ, chưa hợp nhất quyết định của Owner."""
    statement = select(*_COLUMNS).select_from(_joined())
    for condition in _period(date_from, date_to):
        statement = statement.where(condition)
    return _read(engine, statement.order_by(
        _CURRENT.sale_date, _CURRENT.order_key, _CURRENT.occurrence_index))


def employee_names(
    engine: Engine, *, date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[tuple[Optional[str], Optional[str]]]:
    """`(nhân viên, nhóm)` có dòng trong kỳ, đã sắp theo tên.

    Chuỗi rỗng và `NULL` là CÙNG một tình trạng nghiệp vụ ("chưa xác định được
    ai bán") — gộp về `None` ở đây đúng như PRA-003/PRA-004 đã làm, để bộ chọn
    nhân viên không hiện hai mục trống cạnh nhau như thể đó là hai người.
    """
    statement = select(
        distinct(_RESULT.employee_normalized).label("employee"),
        _RESULT.employee_group.label("employee_group"),
    ).select_from(_joined())
    for condition in _period(date_from, date_to):
        statement = statement.where(condition)
    seen: dict[Optional[str], Optional[str]] = {}
    for row in _read(engine, statement):
        name = row["employee"] or None
        seen.setdefault(name, row["employee_group"])
    return sorted(seen.items(), key=lambda item: (item[0] is None, item[0] or ""))


def undated_lines(engine: Engine) -> int:
    """Dòng hiện hành KHÔNG có `sale_date`, đếm KHÔNG lọc kỳ (`R-S5`)."""
    rows = _read(engine, select(func.count().label("total"))
                 .select_from(order_line_current)
                 .where(_CURRENT.sale_date.is_(None)))
    return int(rows[0]["total"] or 0)


def build_lines(
    rows: list[dict], *, overrides: dict, classifications: dict,
    router: ConversionRateRouter,
) -> list[BusinessLine]:
    """Hợp nhất dòng pipeline + quyết định Owner thành `BusinessLine`.

    Đây là điểm hợp nhất DUY NHẤT của hai thẩm quyền, và nó xảy ra lúc ĐỌC —
    không có bản ghi nào bị sửa để đạt được kết quả này.

    `discount` được coalesce về `0` (và CHỈ nó): công thức đã freeze của
    `DEC-143` là `(SellPrice − KpiPurchasePrice) × Quantity − Discount`, trong
    đó `Discount` là một khoản TRỪ, nên "không có chiết khấu" đúng nghĩa là
    "trừ đi 0". Điều đó khác hẳn `sell_price`/`quantity` vắng mặt — hai cái đó
    làm lợi nhuận KHÔNG XÁC ĐỊNH và vẫn phải là `None`.
    """
    lines = []
    for row in rows:
        key = (row["order_key"], row["product_key"], int(row["occurrence_index"]))
        override = overrides.get(key)
        classified = classifications.get(row["product_key"])
        lines.append(BusinessLine(
            order_key=row["order_key"],
            employee=row["employee_normalized"] or None,
            employee_group=row["employee_group"],
            status=row["status"],
            sell_price=row["sell_price"],
            quantity=row["quantity"],
            discount=row["discount"] if row["discount"] is not None else Decimal(0),
            total_sales=row["total_sales"],
            auto_purchase_price=row["kpi_purchase_price"],
            auto_kpi_profit=row["eligible_kpi_profit"],
            manual_purchase_price=(
                None if override is None else override["purchase_price"]),
            manual_provenance=(
                None if override is None else override["provenance"]),
            conversion_rate=router.rate_for(
                stored_rate=row["conversion_rate_final"],
                classified_group=(
                    None if classified is None else classified["product_group"]),
                employee=row["employee_normalized"] or None,
                employee_group=row["employee_group"],
                lead_source=row["lead_source_final"],
                sale_date=row["sale_date"],
            ),
        ))
    return lines


def line_details(
    rows: list[dict], lines: list[BusinessLine], *, classifications: dict,
) -> list[dict]:
    """Ghép mỗi `BusinessLine` với các trường CHỈ dùng để hiển thị/định danh.

    `BusinessLine` cố ý không mang `product_raw`, `product_key` hay `sale_date`
    — nó là ngữ nghĩa nghiệp vụ thuần, và nhồi thêm trường trình bày vào đó sẽ
    làm mọi test nghiệp vụ phải dựng dữ liệu mà chúng không quan tâm. Hai danh
    sách đi song song vì `build_lines` giữ nguyên thứ tự của `rows`.
    """
    details = []
    for row, line in zip(rows, lines):
        classified = classifications.get(row["product_key"])
        details.append({
            "order_key": row["order_key"],
            "product_key": row["product_key"],
            "occurrence_index": int(row["occurrence_index"]),
            "product_raw": row["product_raw"],
            "sale_date": row["sale_date"],
            "auto_provenance": row["kpi_purchase_provenance"],
            "pipeline_product_group": row["product_group_final"],
            "classified_product_group": (
                None if classified is None else classified["product_group"]),
            "line": line,
        })
    return details


__all__ = [
    "build_lines", "employee_names", "line_details", "raw_lines", "undated_lines",
]
