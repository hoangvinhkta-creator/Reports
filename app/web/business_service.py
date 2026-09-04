"""PHB-03 — ráp một trang nghiệp vụ từ ba nguồn, không thêm luật nào.

Module này là ĐIỂM RÁP, không phải một tầng nghiệp vụ mới. Nó gọi:

    business_queries   (dòng hiện hành — CHỈ ĐỌC)
  + business_store     (quyết định của Owner)
  + rate_routing       (tỉ lệ hiệu lực sau tick Gia dụng)
  → business_metrics   (ngữ nghĩa đã freeze)

và không có phép tính nghiệp vụ nào của riêng nó. Lý do tồn tại: nếu ráp trực
tiếp trong `server.py`, mỗi route sẽ tự lặp lại thứ tự bốn bước trên, và lần
thứ tư ai đó quên áp override giá nhập sẽ là một trang hiện số sai mà không
test nào bắt được.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.modules.reporting import business_metrics as bm
from app.modules.reporting.rate_routing import ConversionRateRouter
from app.web import business_queries
from app.web.business_store import BusinessDecisionStore

REPO_ROOT = Path(__file__).resolve().parents[2]
CONVERSION_RATES_PATH = REPO_ROOT / "config" / "conversion_rates.yaml"


@dataclass(frozen=True)
class PeriodData:
    """Mọi thứ một trang nghiệp vụ cần cho MỘT kỳ, đọc đúng một lần."""

    lines: list
    details: list
    totals: bm.BusinessTotals

    def for_employee(self, employee: Optional[str]) -> "PeriodData":
        """Lát cắt của một nhân viên — cùng cấu trúc, để trang dùng chung code."""
        keep = [index for index, line in enumerate(self.lines)
                if line.employee == employee]
        lines = [self.lines[index] for index in keep]
        return PeriodData(lines=lines, details=[self.details[i] for i in keep],
                          totals=bm.totals(lines))


class BusinessReportService:
    def __init__(
        self, *, engine, store: BusinessDecisionStore,
        router: Optional[ConversionRateRouter] = None,
    ) -> None:
        self._engine = engine
        self._store = store
        self._router = router or ConversionRateRouter.from_yaml(CONVERSION_RATES_PATH)

    @property
    def store(self) -> BusinessDecisionStore:
        return self._store

    def period(
        self, *, date_from: Optional[date] = None, date_to: Optional[date] = None,
    ) -> PeriodData:
        rows = business_queries.raw_lines(
            self._engine, date_from=date_from, date_to=date_to)
        overrides = self._store.purchase_price_overrides()
        classifications = self._store.product_groups()
        lines = business_queries.build_lines(
            rows, overrides=overrides, classifications=classifications,
            router=self._router)
        details = business_queries.line_details(
            rows, lines, classifications=classifications)
        return PeriodData(lines=lines, details=details, totals=bm.totals(lines))

    def employees(
        self, *, date_from: Optional[date] = None, date_to: Optional[date] = None,
    ) -> list[tuple[Optional[str], Optional[str]]]:
        return business_queries.employee_names(
            self._engine, date_from=date_from, date_to=date_to)

    def undated_lines(self) -> int:
        return business_queries.undated_lines(self._engine)

    def auto_price_of(
        self, *, order_key: str, product_key: str, occurrence_index: int,
        data: PeriodData,
    ) -> tuple[bool, Optional[Decimal]]:
        """`(dòng có tồn tại, giá AUTO của nó)` — nguồn sự thật cho provenance.

        Provenance `MANUAL` vs `MANUAL_OVERRIDE` KHÔNG được lấy từ form của
        trình duyệt: đó là một khẳng định về dữ liệu hiện có, và để client tự
        khai nó là mở đúng cánh cửa mà `DEC-PHB02-02` §3 đóng lại ("KHÔNG được
        âm thầm coi một manual override là AUTO"). Giá AUTO vì vậy luôn được
        đọc lại từ server, ngay trước khi ghi.
        """
        for detail in data.details:
            if (detail["order_key"] == order_key
                    and detail["product_key"] == product_key
                    and detail["occurrence_index"] == occurrence_index):
                return True, detail["line"].auto_purchase_price
        return False, None

    @staticmethod
    def products(data: PeriodData) -> list[dict]:
        """Các MẶT HÀNG của lát dữ liệu, gộp theo `product_key`.

        Nhãn hiển thị là `min(product_raw)` của nhóm — đúng quy ước đã nghiệm
        thu ở `sales_queries.product_totals`, để hai trang không gọi cùng một
        mặt hàng bằng hai cái tên.
        """
        buckets: dict[str, dict] = {}
        for detail in data.details:
            product_key = detail["product_key"]
            bucket = buckets.setdefault(product_key, {
                "product_key": product_key, "product_label": None,
                "lines": 0, "sales": None,
                "classified": detail["classified_product_group"] is not None,
                "current_group": (
                    detail["classified_product_group"]
                    or detail["pipeline_product_group"]),
            })
            label = detail["product_raw"]
            if label and (bucket["product_label"] is None
                          or label < bucket["product_label"]):
                bucket["product_label"] = label
            bucket["lines"] += 1
            sales = detail["line"].total_sales
            if sales is not None:
                bucket["sales"] = (bucket["sales"] or Decimal(0)) + sales
        return sorted(
            buckets.values(),
            key=lambda item: (-(item["sales"] or Decimal(0)),
                              item["product_label"] or ""),
        )


__all__ = ["BusinessReportService", "CONVERSION_RATES_PATH", "PeriodData"]
