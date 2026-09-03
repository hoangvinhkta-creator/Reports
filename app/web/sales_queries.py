"""TASK-PRA-004 — truy vấn CHỈ-ĐỌC cho Bán hàng và chi tiết đơn/dòng.

Tầng này là nơi DUY NHẤT của PRA-004 nói SQL, và nó tồn tại TÁCH KHỎI
``analytics_queries`` vì đúng một lý do đã ghi thành văn trong frozen contract
mục 14.4: trang chi tiết PHẢI hiển thị ``product_raw`` để Owner phân biệt các
dòng trong một đơn (``canonical_product_code`` rỗng trên 0/351 dòng nên không
thay thế được), trong khi hàng rào PII của PRA-003 xếp ``product_raw`` chung
nhóm với ``imei``/``note_raw``/``employee_raw``. Nới hàng rào đó là làm yếu
một gate đã được nghiệm thu, nên PRA-004 dựng hàng rào RIÊNG, hẹp hơn ĐÚNG
một trường, và phát biểu nó tường minh thay vì thừa kế ngầm.

Ba kỷ luật, không cái nào là khuyến nghị:

1. **CHỈ ĐỌC.** Không một câu ``INSERT``/``UPDATE``/``DELETE`` nào. PRA-004 là
   TRUY VẾT, không phải một hệ thống duyệt đơn: không có approve/reject/
   resolve/assign/comment, và vì vậy không có đường ghi nào cần tồn tại.
2. **Chỉ trạng thái hiện hành.** Mọi con số đi qua ``order_line_current`` và
   hai con trỏ ``current_source_version_id`` / ``current_result_version_id``.
   PK của bảng đó là ``(order_key, product_key, occurrence_index)`` và cả hai
   join đều trỏ vào cột ``id`` PRIMARY KEY của bảng version, nên mỗi khoá dòng
   góp ĐÚNG MỘT bản ghi — no-double-count là tính chất của CẤU TRÚC BẢNG,
   không phải của việc câu truy vấn có nhớ ``DISTINCT`` hay không. TUYỆT ĐỐI
   KHÔNG cộng số của từng lần chạy, không đọc version cũ.
3. **``NULL`` không phải ``0``.** Không coalesce gì ở đây. Tập cộng rỗng ⟹
   ``None``, và tầng trình bày hiển thị ``—``. Một đơn 66 triệu có 1/4 dòng đủ
   thẩm quyền phải nói "chưa biết ba dòng kia", không được nói "lãi 0".

Cột KHÔNG được đọc ở đây (PII theo
``governance/product/17_DATA_GOVERNANCE_PRIVACY.md``): ``imei``, ``note_raw``,
``employee_raw``, và mọi cột khách hàng. Danh sách này được test canh bằng
grep. ``product_raw`` CỐ Ý nằm ngoài hàng rào — lý do ở đoạn mở đầu.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Optional

from sqlalchemy import case, func, select
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
# ("chưa xác định được ai bán") — gộp ở tầng SQL đúng như PRA-003 đã làm, để
# một đơn không hiện hai tên trống cạnh nhau như thể đó là hai người.
_EMPLOYEE = case(
    (order_line_result_version.c.employee_normalized == "", None),
    else_=order_line_result_version.c.employee_normalized,
).label("employee")


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
    """Điều kiện kỳ — GIỐNG HỆT ``analytics_queries._period``.

    ``sale_date IS NOT NULL`` LUÔN có mặt, kể cả với "Toàn bộ dữ liệu". Đây là
    điều kiện để Owner chọn cùng một tháng ở Tổng quan và ở Bán hàng rồi thấy
    CÙNG một tập đơn; lệch một chữ ở đây là hai trang nói hai con số khác nhau
    về cùng một kỳ.
    """
    conditions = [order_line_current.c.sale_date.is_not(None)]
    if date_from is not None:
        conditions.append(order_line_current.c.sale_date >= date_from)
    if date_to is not None:
        conditions.append(order_line_current.c.sale_date <= date_to)
    return conditions


def _read(engine: Engine, statement) -> list[dict]:
    """Lỗi database KHÔNG BAO GIỜ được biến thành "chưa có dữ liệu"."""
    try:
        with engine.connect() as connection:
            return [dict(row._mapping) for row in connection.execute(statement)]
    except SQLAlchemyError as exc:
        raise HistoryUnavailableError(str(exc)) from exc


def _order_metrics() -> tuple:
    """Chỉ tiêu cấp ĐƠN. Không hàm nào coalesce về ``0``.

    ``kpi_lines`` và ``accounting_lines`` là TỬ SỐ coverage của chính hai ô lợi
    nhuận đứng cạnh chúng, và chúng có tử số KHÁC nhau: LN KPI chỉ cộng dòng
    ``AUTO``, LN kế toán cộng mọi dòng ĐÃ CÓ giá trị. Mẫu số chung là ``lines``.
    """
    return (
        func.count().label("lines"),
        func.min(order_line_current.c.sale_date).label("sale_date_from"),
        func.max(order_line_current.c.sale_date).label("sale_date_to"),
        func.sum(order_line_source_version.c.quantity).label("quantity"),
        func.sum(order_line_result_version.c.total_sales).label("total_sales"),
        func.sum(case((_STATUS == "AUTO", _KPI_PROFIT))).label("kpi_profit"),
        func.sum(case((_STATUS == "AUTO", 1), else_=0)).label("kpi_lines"),
        func.sum(_ACCOUNTING_PROFIT).label("accounting_profit"),
        func.sum(case((_ACCOUNTING_PROFIT.is_not(None), 1), else_=0))
            .label("accounting_lines"),
        # Đơn có ≥1 dòng PENDING ⟹ CẦN KIỂM TRA (mục 7). Đây là ngữ nghĩa
        # NGUYÊN VẸN của PRA-003; một triển khai lấy trạng thái dòng ĐẦU TIÊN
        # sẽ hiện BH62439 (1 AUTO + 3 PENDING) thành AUTO.
        func.max(case((_STATUS == "PENDING", 1), else_=0)).label("has_pending"),
    )


def _shaped(row: dict) -> dict:
    """Ép các ô ĐẾM về ``int``, giữ NGUYÊN ``None`` của các ô TIỀN."""
    return {
        "order_key": row["order_key"],
        "sale_date_from": row["sale_date_from"],
        "sale_date_to": row["sale_date_to"],
        "lines": int(row["lines"] or 0),
        "quantity": row["quantity"],
        "total_sales": row["total_sales"],
        "kpi_profit": row["kpi_profit"],
        "kpi_lines": int(row["kpi_lines"] or 0),
        "accounting_profit": row["accounting_profit"],
        "accounting_lines": int(row["accounting_lines"] or 0),
        "review": bool(row["has_pending"]),
    }


def _grouped(engine: Engine, conditions: list) -> list[dict]:
    statement = (select(order_line_current.c.order_key, *_order_metrics())
                 .select_from(_joined()))
    for condition in conditions:
        statement = statement.where(condition)
    statement = statement.group_by(order_line_current.c.order_key)
    return _read(engine, statement.order_by(
        func.min(order_line_current.c.sale_date).desc(),
        order_line_current.c.order_key,
    ))


def _employees(engine: Engine, conditions: list) -> dict[str, list]:
    """Tập ``DISTINCT employee_normalized`` của TỪNG đơn.

    Truy vấn riêng rồi gộp trong Python thay vì một hàm nối chuỗi của
    database: ``string_agg``/``group_concat`` viết khác nhau giữa PostgreSQL
    (production) và SQLite (dev/test), và số nhân viên trên một đơn luôn nhỏ.

    KHÔNG lấy nhân viên của dòng đầu tiên. ``order_builder`` làm vậy và
    ``renderer.py::_order_inconsistency`` gọi đúng tên hành vi đó là "hành vi
    legacy, KHÔNG phải quyền sở hữu đã được xác minh" — chép nó vào một màn
    hình quản lý là biến một hành vi legacy thành một khẳng định về quyền sở
    hữu mà chưa ai quyết.
    """
    statement = (select(order_line_current.c.order_key, _EMPLOYEE)
                 .select_from(_joined()))
    for condition in conditions:
        statement = statement.where(condition)
    grouped: dict[str, list] = {}
    for row in _read(engine, statement.group_by(
            order_line_current.c.order_key, _EMPLOYEE)):
        grouped.setdefault(row["order_key"], []).append(row["employee"])
    return {key: sorted(values, key=lambda name: (name is None, name or ""))
            for key, values in grouped.items()}


def order_list(
    engine: Engine, *, date_from: Optional[date] = None, date_to: Optional[date] = None,
) -> list[dict]:
    """Các đơn của một kỳ, mới nhất trước, trên trạng thái hiện hành."""
    conditions = _period(date_from, date_to)
    employees = _employees(engine, conditions)
    return [{**_shaped(row), "employees": employees.get(row["order_key"], [])}
            for row in _grouped(engine, conditions)]


def _line_columns() -> tuple:
    """Đúng các cột mục 12.B yêu cầu — không cột nào khác.

    Không có ``imei``/``note_raw``/``employee_raw`` ở đây, và cũng không có
    ``price_source``/``kpi_purchase_provenance``/``composition_rule``: chúng là
    từ vựng nội bộ, bị cấm khỏi UI quản lý (mục 14.3).
    """
    return (
        order_line_source_version.c.product_raw,
        order_line_source_version.c.quantity,
        order_line_source_version.c.sell_price,
        order_line_source_version.c.discount,
        # Doanh thu dòng ĐỌC THẲNG giá trị đã lưu — PRA-004 không tính lại nó
        # từ (số lượng × đơn giá − chiết khấu). Tính lại là dựng một nguồn sự
        # thật thứ hai cạnh nguồn đã được nghiệm thu.
        order_line_result_version.c.total_sales,
        order_line_result_version.c.accounting_purchase_price,
        order_line_result_version.c.kpi_purchase_price,
        order_line_result_version.c.accounting_profit,
        order_line_result_version.c.eligible_kpi_profit,
        order_line_result_version.c.status,
        order_line_result_version.c.pending_reasons_json,
        _EMPLOYEE,
    )


def _reasons(raw: Optional[str]) -> list[str]:
    """Mã lý do đã lưu, khử trùng lặp, GIỮ NGUYÊN thứ tự đã persist.

    JSON hỏng ⟹ danh sách rỗng chứ KHÔNG phải HTTP 500: một dòng mất lý do vẫn
    hiện đúng trạng thái ``CẦN KIỂM TRA``, còn một trang trắng thì không nói
    được gì cả. Không gộp, không chọn "lý do chính", không cắt bớt — mọi quy
    tắc ưu tiên đều là nghiệp vụ mới chưa ai quyết (mục 8.4).
    """
    try:
        parsed = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []
    return list(dict.fromkeys(str(value) for value in parsed)) if parsed else []


def _line(row: dict) -> dict:
    """Dòng đem ra trình bày: mã lý do đã giải mã, KHÔNG kèm chuỗi JSON thô."""
    return {**row, "reasons": _reasons(row.pop("pending_reasons_json"))}


def order_detail(
    engine: Engine, order_key: str, *,
    date_from: Optional[date] = None, date_to: Optional[date] = None,
) -> Optional[dict]:
    """Một đơn: khối tổng hợp + các dòng hiện hành của nó.

    ``None`` ⟹ đơn không có dòng hiện hành nào trong kỳ; route trả 404 chứ
    KHÔNG dựng một trang rỗng trông như "đơn này không có dòng nào".

    Thứ tự dòng: ``occurrence_index`` rồi ``current_source_version_id``.
    ``occurrence_index`` một mình KHÔNG đủ — nó đếm theo (đơn, sản phẩm) nên
    bốn dòng khác sản phẩm của BH62439 đều mang giá trị ``1``. Id version
    nguồn tăng dần theo ``source_row`` (``extraction.build_source_lines`` sắp
    xếp theo đúng cột đó trước khi ghi), nên nó khôi phục thứ tự dòng trong sổ
    mà không cần đọc thêm bảng nào. Một dòng bị SỬA nhận version mới và vì thế
    chuyển xuống cuối đơn — thứ tự vẫn ỔN ĐỊNH và vẫn phản ánh trạng thái hiện
    hành, chỉ không còn trùng vị trí trong sổ gốc.
    """
    conditions = [*_period(date_from, date_to),
                  order_line_current.c.order_key == order_key]
    rows = _grouped(engine, conditions)
    if not rows:
        return None
    statement = select(*_line_columns()).select_from(_joined())
    for condition in conditions:
        statement = statement.where(condition)
    lines = _read(engine, statement.order_by(
        order_line_current.c.occurrence_index,
        order_line_current.c.current_source_version_id,
    ))
    employees = _employees(engine, conditions)
    return {
        **_shaped(rows[0]),
        "employees": employees.get(order_key, []),
        "lines_detail": [_line(row) for row in lines],
    }


__all__ = ["order_detail", "order_list"]
