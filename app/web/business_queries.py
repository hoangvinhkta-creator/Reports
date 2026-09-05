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

import json
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
    _RESULT.status, _RESULT.pending_reasons_json,
    _RESULT.employee_normalized, _RESULT.employee_group,
    _RESULT.lead_source_final, _RESULT.total_sales, _RESULT.kpi_purchase_price,
    _RESULT.kpi_purchase_provenance, _RESULT.eligible_kpi_profit,
    _RESULT.product_group_final, _RESULT.conversion_rate_final,
    _SOURCE.product_raw, _SOURCE.quantity, _SOURCE.sell_price, _SOURCE.discount,
)


def reasons(raw: Optional[str]) -> tuple[str, ...]:
    """`pending_reasons_json` đã lưu → tuple mã, khử trùng lặp, GIỮ thứ tự.

    Cùng cách giải mã đã nghiệm thu ở `sales_queries._reasons` (TASK-PRA-004),
    và cùng lý do: JSON hỏng trả về tuple RỖNG chứ không phải HTTP 500 — một
    dòng mất danh sách lý do vẫn hiện đúng mọi con số, còn một trang trắng thì
    không nói được gì cả.

    Các mã này KHÔNG tham gia vào cửa chặn lợi nhuận (`OD-6`). Chúng chỉ dùng
    để dựng cảnh báo (`Duplicate`) và để hiện cho Owner biết pipeline đã ghi
    chú gì trên dòng.
    """
    try:
        parsed = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return ()
    if not parsed:
        return ()
    return tuple(dict.fromkeys(str(value) for value in parsed))


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


def merge_assigned_names(
    names: list[tuple[Optional[str], Optional[str]]], lines: list[BusinessLine],
) -> list[tuple[Optional[str], Optional[str]]]:
    """Bộ chọn nhân viên phải phản ánh CẢ những lần Owner gán lại (`OD-5`).

    `employee_names` đọc thẳng cột của pipeline, nên nó không thấy một người
    vừa được gán lại — và nếu bộ chọn không có tên đó thì trang nhân viên trả
    404 ngay sau khi Owner vừa lưu thành công. Ngược lại, nhóm "chưa xác định"
    phải BIẾN MẤT khỏi bộ chọn khi dòng cuối cùng của nó đã được gán, nếu
    không Owner sẽ mở ra một trang trống và tưởng mất dữ liệu.

    Vì vậy danh sách được dựng lại từ chính tập dòng ĐÃ HỢP NHẤT — một nguồn
    sự thật, không phải hai.
    """
    seen: dict[Optional[str], Optional[str]] = {}
    for line in lines:
        seen.setdefault(line.employee or None, line.employee_group)
    for name, group in names:
        # Giữ tên chỉ có trong bộ chọn cũ (ví dụ nhân viên có dòng ngoài kỳ
        # đang xem) thay vì âm thầm bỏ đi — trừ mục "chưa xác định", vốn phải
        # tự tắt khi không còn dòng nào vô chủ.
        if name is not None:
            seen.setdefault(name, group)
    return sorted(seen.items(), key=lambda item: (item[0] is None, item[0] or ""))


def undated_lines(engine: Engine) -> int:
    """Dòng hiện hành KHÔNG có `sale_date`, đếm KHÔNG lọc kỳ (`R-S5`)."""
    rows = _read(engine, select(func.count().label("total"))
                 .select_from(order_line_current)
                 .where(_CURRENT.sale_date.is_(None)))
    return int(rows[0]["total"] or 0)


def build_lines(
    rows: list[dict], *, overrides: dict, classifications: dict,
    router: ConversionRateRouter, kpi_authority_valid: bool,
    employee_overrides: Optional[dict] = None,
) -> list[BusinessLine]:
    """Hợp nhất dòng pipeline + quyết định Owner thành `BusinessLine`.

    Đây là điểm hợp nhất DUY NHẤT của các thẩm quyền, và nó xảy ra lúc ĐỌC —
    không có bản ghi nào bị sửa để đạt được kết quả này. Đó cũng là lý do việc
    Owner sửa giá nhập hay gán lại nhân viên có hiệu lực NGAY ở lần tải trang
    kế tiếp, không cần chạy lại pipeline (`OD-5`, chỉ thị `PURCHASE PRICE
    EDITING`).

    `kpi_authority_valid` KHÔNG có giá trị mặc định: nó là van fail-closed của
    `DEC-143` §1, và một van an toàn có giá trị mặc định "mở" thì không phải
    van an toàn. Tầng gọi phải đọc `config/eligible_costs.yaml` và nói ra kết
    quả.

    `discount` được coalesce về `0` (và CHỈ nó): công thức đã freeze của
    `DEC-143` là `(SellPrice − KpiPurchasePrice) × Quantity − Discount`, trong
    đó `Discount` là một khoản TRỪ, nên "không có chiết khấu" đúng nghĩa là
    "trừ đi 0". Điều đó khác hẳn `sell_price`/`quantity` vắng mặt — hai cái đó
    làm lợi nhuận KHÔNG XÁC ĐỊNH và vẫn phải là `None`.
    """
    employee_overrides = employee_overrides or {}
    lines = []
    for row in rows:
        key = (row["order_key"], row["product_key"], int(row["occurrence_index"]))
        override = overrides.get(key)
        assigned = employee_overrides.get(key)
        classified = classifications.get(row["product_key"])
        # Bằng chứng gốc ĐI KÈM chứ không bị thay thế: `source_employee` giữ
        # nguyên tên mà sổ ghi, `employee` mới là tên có hiệu lực để cộng KPI.
        source_employee = row["employee_normalized"] or None
        lines.append(BusinessLine(
            order_key=row["order_key"],
            employee=(source_employee if assigned is None
                      else assigned["employee_normalized"]),
            employee_group=(row["employee_group"] if assigned is None
                            else assigned["employee_group"]),
            source_employee=source_employee,
            employee_provenance="SOURCE" if assigned is None else "MANUAL",
            pending_reasons=reasons(row["pending_reasons_json"]),
            kpi_authority_valid=kpi_authority_valid,
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
    overrides: Optional[dict] = None,
) -> list[dict]:
    """Ghép mỗi `BusinessLine` với các trường CHỈ dùng để hiển thị/định danh.

    `BusinessLine` cố ý không mang `product_raw`, `product_key` hay `sale_date`
    — nó là ngữ nghĩa nghiệp vụ thuần, và nhồi thêm trường trình bày vào đó sẽ
    làm mọi test nghiệp vụ phải dựng dữ liệu mà chúng không quan tâm. Hai danh
    sách đi song song vì `build_lines` giữ nguyên thứ tự của `rows`.

    `R2` — `overrides` chỉ để LẤY LẠI hai trường đã lưu sẵn từ lúc Owner bấm
    LƯU: `auto_price_at_entry` (giá tự động ngay TRƯỚC lần sửa đó) và
    `entered_at`. Không có kiến trúc lịch sử mới nào ở đây, và hai trường này
    KHÔNG tham gia bất kỳ phép tính nào — chúng là bối cảnh để Owner đọc lại
    quyết định của chính mình. `auto_price_at_entry` khác `line.auto_purchase
    _price`: cái sau là giá tự động HÔM NAY, cái trước là giá tự động LÚC ĐÓ.
    """
    overrides = overrides or {}
    details = []
    for row, line in zip(rows, lines):
        classified = classifications.get(row["product_key"])
        override = overrides.get(
            (row["order_key"], row["product_key"], int(row["occurrence_index"])))
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
            "override_auto_price_at_entry": (
                None if override is None else override["auto_price_at_entry"]),
            "override_entered_at": (
                None if override is None else override["entered_at"]),
            "line": line,
        })
    return details


__all__ = [
    "build_lines", "employee_names", "line_details", "merge_assigned_names",
    "raw_lines", "reasons", "undated_lines",
]
