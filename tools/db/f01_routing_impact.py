"""F-01 — kiểm tra CHỈ ĐỌC tác động của `BUSINESS_ROUTING_FIX` trên dữ liệu thật.

`DEC-184` sửa một lỗ đã có sẵn: `build_lines` trước đây hỏi tỉ lệ quy đổi bằng
nhóm nhân viên THÔ của pipeline, nên sau một lần Owner gán lại dòng, một dòng
đã tick Gia dụng vẫn quy đổi theo nhóm cũ. Bản sửa hỏi lại resolver bằng danh
tính HIỆU LỰC của dòng.

Script này trả lời đúng MỘT câu hỏi trước khi tích hợp: *trên database thật,
có bao nhiêu dòng mà con số DS quy đổi sẽ đổi vì bản sửa đó?* — và với những
dòng ấy, in ra bảng so sánh trước/sau.

Nó KHÔNG ghi một byte nào: chỉ `SELECT`, không `INSERT`/`UPDATE`/`DELETE`,
không `alembic upgrade`, không tạo file database nếu chưa có. Chạy được trên
chính production PostgreSQL mà không đổi trạng thái gì.

    HISTORY_DATABASE_URL=postgresql+psycopg://... python -m tools.db.f01_routing_impact

Tập dòng bị ảnh hưởng hẹp theo CẤU TẠO, và ba điều kiện dưới đây là đúng ba
điều kiện cần để `rate_for` trả về một giá trị khác:

    1. dòng ĐÃ được phân loại nhóm mặt hàng (mặt hàng hoặc cấp dòng) —
       `classified_group is None` thì `rate_for` trả nguyên `stored_rate`;
    2. dòng CÓ quyết định gán lại nhân viên của Owner;
    3. nhóm nhân viên hiệu lực KHÁC nhóm mà pipeline đã ghi — nếu bằng nhau
       thì resolver nhận cùng đầu vào và trả cùng một tỉ lệ.
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from typing import Optional

from app.modules.reporting.business_metrics import converted_sales
from app.web import business_queries
from app.web.business_queries import effective_product_group
from app.web.business_service import CONVERSION_RATES_PATH
from app.modules.reporting.rate_routing import ConversionRateRouter
from app.web.business_store import BusinessDecisionStore
from tools.db import build_engine


def _fmt(value: Optional[Decimal]) -> str:
    return "—" if value is None else f"{value}"


def matches(engine, store: BusinessDecisionStore, router: ConversionRateRouter) -> list[dict]:
    """Các dòng thoả cả ba điều kiện, kèm tỉ lệ/DS quy đổi cũ và mới.

    Đọc qua đúng những hàm mà báo cáo thật dùng (`raw_lines`,
    `effective_product_group`, `ConversionRateRouter.rate_for`) thay vì viết
    lại một câu SQL riêng: một bản sao của luật định tuyến ở đây sẽ trả lời
    câu hỏi về một hệ thống KHÁC với hệ thống sắp được tích hợp.
    """
    rows = business_queries.raw_lines(engine)
    overrides = store.purchase_price_overrides()
    classifications = store.product_groups()
    line_classifications = store.line_product_groups()
    employee_overrides = store.employee_overrides()
    exclusions = store.line_exclusions()

    found = []
    for row in rows:
        key = (row["order_key"], row["product_key"], int(row["occurrence_index"]))
        assigned = employee_overrides.get(key)
        if assigned is None:
            continue
        classified_group = effective_product_group(
            product_key=row["product_key"], key=key,
            classifications=classifications,
            line_classifications=line_classifications)
        if classified_group is None:
            continue
        old_group = row["employee_group"]
        new_group = assigned["employee_group"]
        if old_group == new_group:
            continue

        common = dict(
            stored_rate=row["conversion_rate_final"],
            classified_group=classified_group,
            lead_source=row["lead_source_final"],
            sale_date=row["sale_date"],
        )
        old_rate = router.rate_for(
            employee=row["employee_normalized"] or None,
            employee_group=old_group, **common)
        new_rate = router.rate_for(
            employee=assigned["employee_normalized"],
            employee_group=new_group, **common)
        profit = row["eligible_kpi_profit"]
        old_converted = converted_sales(profit, old_rate)
        new_converted = converted_sales(profit, new_rate)
        delta = (None if old_converted is None or new_converted is None
                 else Decimal(new_converted) - Decimal(old_converted))
        found.append({
            "order_key": row["order_key"],
            "product_key": row["product_key"],
            "occurrence_index": int(row["occurrence_index"]),
            "old_employee": row["employee_normalized"] or None,
            "old_group": old_group,
            "employee": assigned["employee_normalized"],
            "new_group": new_group,
            "classification": classified_group,
            "old_rate": old_rate,
            "new_rate": new_rate,
            "profit": profit,
            "old_converted": old_converted,
            "new_converted": new_converted,
            "delta": delta,
            "excluded": key in exclusions,
        })
    return found


def render(found: list[dict]) -> str:
    lines = [f"F01_MATCH_COUNT = {len(found)}"]
    if not found:
        lines.append("F01_PRODUCTION_IMPACT = NONE")
        lines.append("BUSINESS_TOTALS_UNEXPECTEDLY_CHANGED = NO_CONFIRMED")
        return "\n".join(lines)
    lines.append("F01_PRODUCTION_IMPACT = LISTED")
    header = ("BH | product_key | occ | old_employee | old_group | employee | "
              "new_group | classification | old_rate | new_rate | profit | "
              "old_converted | new_converted | delta | excluded")
    lines.append(header)
    lines.append("-" * len(header))
    for item in found:
        lines.append(" | ".join([
            item["order_key"], item["product_key"], str(item["occurrence_index"]),
            item["old_employee"] or "—", item["old_group"] or "—",
            item["employee"], item["new_group"] or "—", item["classification"],
            _fmt(item["old_rate"]), _fmt(item["new_rate"]), _fmt(item["profit"]),
            _fmt(item["old_converted"]), _fmt(item["new_converted"]),
            _fmt(item["delta"]), "YES" if item["excluded"] else "NO",
        ]))
    total = sum((item["delta"] for item in found if item["delta"] is not None),
                Decimal(0))
    lines.append(f"TOTAL_DS_QUY_DOI_DELTA = {total}")
    return "\n".join(lines)


class NotAProductionDatabaseError(RuntimeError):
    """Database được trỏ tới KHÔNG chứa sổ đã nạp, nên không trả lời được F-01."""


def assert_has_ledger(engine) -> int:
    """Số dòng hiện hành — và từ chối nếu database rỗng hoặc chưa migrate.

    Đây là van QUAN TRỌNG NHẤT của script. Không có nó, chạy nhầm trên một
    SQLite dev trống sẽ in ra ``F01_MATCH_COUNT = 0`` — một con số đúng về
    database đang mở nhưng là BẰNG CHỨNG BỊA về production. "Không có dòng nào
    bị ảnh hưởng" và "không có dòng nào để mà xét" là hai kết luận khác nhau,
    và chỉ cái thứ nhất mới trả lời được câu hỏi trước khi tích hợp.
    """
    from sqlalchemy import func, select as _select

    from tools.db.schema import order_line_current

    try:
        with engine.connect() as connection:
            total = connection.execute(
                _select(func.count()).select_from(order_line_current)).scalar_one()
    except Exception as exc:  # noqa: BLE001 — chưa migrate cũng là "không trả lời được"
        raise NotAProductionDatabaseError(
            f"Không đọc được `order_line_current`: {exc}") from exc
    if not total:
        raise NotAProductionDatabaseError(
            "`order_line_current` RỖNG — database này chưa nạp sổ nào. "
            "F-01 cần chạy trên chính database production "
            "(`HISTORY_DATABASE_URL`), không phải một SQLite dev trống.")
    return int(total)


def main(argv: Optional[list[str]] = None) -> int:
    engine = build_engine(os.environ)
    try:
        total = assert_has_ledger(engine)
    except NotAProductionDatabaseError as exc:
        print(f"F01_MATCH_COUNT = NOT_MEASURABLE\nF01_REASON = {exc}",
              file=sys.stderr)
        return 2
    store = BusinessDecisionStore(engine)
    router = ConversionRateRouter.from_yaml(CONVERSION_RATES_PATH)
    print(f"F01_LINES_SCANNED = {total}")
    print(render(matches(engine, store, router)))
    return 0


if __name__ == "__main__":  # pragma: no cover — điểm vào dòng lệnh
    sys.exit(main())
