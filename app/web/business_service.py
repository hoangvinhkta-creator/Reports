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

PHB-05 thêm MỘT nguồn nữa vào cùng điểm ráp này — Target tháng của nhân viên —
và cố ý thêm nó ở ĐÂY chứ không vào `business_metrics`: Target ĐỌC kết quả báo
cáo (DS quy đổi) để tính "So target", nó không tham gia vào bất kỳ phép gộp
nghiệp vụ nào. Giữ nó ngoài `BusinessTotals` là cách bảo đảm bằng cấu trúc
rằng đặt/sửa Target không thể làm đổi một con số doanh thu, lợi nhuận hay DS
quy đổi nào (PHB-05 §21).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.modules.kpi.kpi_profit_engine import load_eligible_costs_authority
from app.modules.mapping.employee_mapper import load_employee_master
from app.modules.reporting import business_metrics as bm
from app.modules.reporting.rate_routing import ConversionRateRouter
from app.web import business_queries
from app.web.business_store import BusinessDecisionStore

REPO_ROOT = Path(__file__).resolve().parents[2]
CONVERSION_RATES_PATH = REPO_ROOT / "config" / "conversion_rates.yaml"
ELIGIBLE_COSTS_PATH = REPO_ROOT / "config" / "eligible_costs.yaml"
EMPLOYEES_PATH = REPO_ROOT / "config" / "employees.yaml"


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
        eligible_costs_path: Optional[Path] = None,
        employees_path: Optional[Path] = None,
    ) -> None:
        self._engine = engine
        self._store = store
        self._router = router or ConversionRateRouter.from_yaml(CONVERSION_RATES_PATH)
        self._eligible_costs_path = eligible_costs_path or ELIGIBLE_COSTS_PATH
        self._employees_path = employees_path or EMPLOYEES_PATH

    @property
    def store(self) -> BusinessDecisionStore:
        return self._store

    def kpi_authority_valid(self) -> bool:
        """`DEC-143` §1 — thẩm quyền chi phí KPI có đọc được HÔM NAY không.

        Đọc lại ở mỗi lần dựng kỳ, không nhớ vào bộ nhớ: một file cấu hình vừa
        hỏng phải làm báo cáo ngừng ra số NGAY, chứ không phải ở lần khởi động
        lại tiếp theo. Chi phí là một lần đọc file nhỏ cho mỗi lần tải trang.

        Đây là van fail-closed mà bản audit cảnh báo phải giữ: đường tính lại
        khi có giá tay trước đây áp thẳng công thức mà không hỏi van này, nên
        nó đi vòng qua đúng cái van được dựng để chặn.
        """
        return load_eligible_costs_authority(self._eligible_costs_path).is_valid

    def assignable_employees(self) -> list[tuple[str, Optional[str]]]:
        """`(tên chuẩn hoá, nhóm)` mà Owner được phép gán một dòng cho.

        Nguồn là master `config/employees.yaml` — thẩm quyền DUY NHẤT về "ai
        là nhân viên thật". Lấy từ dữ liệu đang có trong kỳ thay vì master sẽ
        khiến một nhân viên chưa có dòng nào không gán được, và mở đường cho
        việc gõ một cái tên chưa từng tồn tại vào KPI.

        Nhân viên `active: false` KHÔNG có mặt: gán một dòng mới cho người đã
        nghỉ là một quyết định nhân sự, không phải một lần sửa dữ liệu. Master
        hỏng ⟹ danh sách RỖNG, và tầng route biến điều đó thành "chưa gán được"
        thay vì một danh sách đoán mò.
        """
        try:
            master = load_employee_master(self._employees_path)
        except Exception:  # noqa: BLE001 — master hỏng là "chưa gán được"
            return []
        seen: dict[str, Optional[str]] = {}
        for record in master.records:
            if not record.active:
                continue
            seen.setdefault(record.normalized, record.group)
        return sorted(seen.items())

    def period(
        self, *, date_from: Optional[date] = None, date_to: Optional[date] = None,
    ) -> PeriodData:
        rows = business_queries.raw_lines(
            self._engine, date_from=date_from, date_to=date_to)
        overrides = self._store.purchase_price_overrides()
        classifications = self._store.product_groups()
        lines = business_queries.build_lines(
            rows, overrides=overrides, classifications=classifications,
            router=self._router,
            kpi_authority_valid=self.kpi_authority_valid(),
            employee_overrides=self._store.employee_overrides())
        details = business_queries.line_details(
            rows, lines, classifications=classifications, overrides=overrides)
        return PeriodData(lines=lines, details=details, totals=bm.totals(lines))

    def employees(
        self, *, date_from: Optional[date] = None, date_to: Optional[date] = None,
        data: Optional[PeriodData] = None,
    ) -> list[tuple[Optional[str], Optional[str]]]:
        """Bộ chọn nhân viên của kỳ, ĐÃ tính cả những lần Owner gán lại.

        `data` là lát dữ liệu đã hợp nhất của chính kỳ đó. Truyền vào thì danh
        sách phản ánh trạng thái hiện tại (một dòng vừa được gán làm tên người
        đó xuất hiện; nhóm "chưa xác định" tự tắt khi không còn dòng vô chủ).
        Không truyền thì đây là danh sách thô của pipeline, như trước.
        """
        names = business_queries.employee_names(
            self._engine, date_from=date_from, date_to=date_to)
        if data is None:
            return names
        return business_queries.merge_assigned_names(names, data.lines)

    def undated_lines(self) -> int:
        return business_queries.undated_lines(self._engine)

    # --- Target tháng của nhân viên (PHB-05, DEC-PHB02-06) ---------------

    def employee_targets(
        self, period: Optional[tuple[int, int]]
    ) -> dict[str, Decimal]:
        """`{tên nhân viên: Target VND}` của MỘT kỳ. Kỳ `None` ⟹ dict rỗng.

        "Toàn bộ dữ liệu" KHÔNG có Target: Target là con số của một THÁNG
        (`DEC-PHB02-06`, PHB-05 §4), và cộng target của nhiều tháng lại để lấp
        chỗ trống sẽ là một con số Owner chưa từng đặt. Dict rỗng làm mọi
        nhân viên hiện "chưa thiết lập" ở khung nhìn đó — đúng sự thật.

        Nhân viên KHÔNG có dòng trong bảng ⟹ vắng mặt khỏi dict. `None` (chưa
        thiết lập) và `0` (đặt bằng không) vì thế không bao giờ lẫn nhau.
        """
        if period is None:
            return {}
        year, month = period
        rows = self._store.employee_targets(year=year, month=month)
        return {name: row["target_vnd"] for name, row in rows.items()}

    def target_rows(
        self, *, period: Optional[tuple[int, int]], data: PeriodData,
    ) -> list[tuple[Optional[str], Optional[str], bm.BusinessTotals, Optional[Decimal]]]:
        """`(nhân viên, nhóm, chỉ tiêu kỳ, Target)` cho màn hình Target.

        Chỉ tiêu lấy NGUYÊN từ `group_by_employee` — cùng một phân hoạch mà
        trang Báo cáo đang hiện. Target là cột thứ tư ĐI KÈM, không phải một
        đầu vào của phép gộp: PHB-05 §21 nói rõ Target ĐỌC kết quả báo cáo,
        không làm thay đổi nó, và giữ nó ngoài `BusinessTotals` là cách bảo
        đảm điều đó bằng cấu trúc chứ bằng lời hứa.

        Nhân viên đã được đặt Target nhưng CHƯA có dòng nào trong kỳ vẫn có
        mặt (Target `>= 0`, chỉ tiêu rỗng): nếu không, Owner đặt target xong
        mở lại trang và không thấy nó đâu.
        """
        targets = self.employee_targets(period)
        grouped = bm.group_by_employee(data.lines)
        rows = [(name, group, totals, targets.get(name))
                for name, group, totals in grouped]
        seen = {name for name, _group, _totals in grouped}
        for name in sorted(set(targets) - seen):
            rows.append((name, None, bm.totals([]), targets[name]))
        return rows

    def set_employee_target(
        self, *, period: tuple[int, int], employee_key: str, target_vnd: Decimal,
    ) -> None:
        year, month = period
        self._store.set_employee_target(
            year=year, month=month, employee_key=employee_key,
            target_vnd=target_vnd)

    def clear_employee_target(
        self, *, period: tuple[int, int], employee_key: str,
    ) -> None:
        year, month = period
        self._store.clear_employee_target(
            year=year, month=month, employee_key=employee_key)


    def detail_of(
        self, *, order_key: str, product_key: str, occurrence_index: int,
        data: PeriodData,
    ) -> Optional[dict]:
        """Bản ghi hiển thị của MỘT dòng trong kỳ, hoặc `None` nếu không có.

        Mọi thao tác ghi đều phải đi qua đây trước: một khoá do trình duyệt
        gửi lên chỉ trở thành thật sau khi tìm thấy nó trong kỳ đang xem. Nếu
        không, một form dựng tay sẽ ghi được quyết định lên một dòng không tồn
        tại, và bản ghi đó nằm lại trong database mãi mãi.
        """
        for detail in data.details:
            if (detail["order_key"] == order_key
                    and detail["product_key"] == product_key
                    and detail["occurrence_index"] == occurrence_index):
                return detail
        return None

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
        detail = self.detail_of(order_key=order_key, product_key=product_key,
                                occurrence_index=occurrence_index, data=data)
        if detail is None:
            return False, None
        return True, detail["line"].auto_purchase_price

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
