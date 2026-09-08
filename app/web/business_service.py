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

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.modules.exporting import business_export
from app.modules.kpi.kpi_profit_engine import load_eligible_costs_authority
from app.modules.mapping.employee_mapper import load_employee_master
from app.modules.reporting import business_metrics as bm
from app.modules.reporting import line_type as line_type_module
from app.modules.reporting import line_type_config
from app.modules.reporting import reporting_sheets
from app.modules.reporting.rate_routing import ConversionRateRouter
from app.web import business_queries
from app.web.binding_exceptions import BindingExceptionStore
from app.web.business_store import BusinessDecisionStore
from app.web.period_lock import (
    ClosedPeriod, PeriodCloseStore, PeriodClosedError, content_fingerprint,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONVERSION_RATES_PATH = REPO_ROOT / "config" / "conversion_rates.yaml"
ELIGIBLE_COSTS_PATH = REPO_ROOT / "config" / "eligible_costs.yaml"
EMPLOYEES_PATH = REPO_ROOT / "config" / "employees.yaml"
LINE_TYPES_PATH = REPO_ROOT / "config" / "line_types.yaml"


class LineTypeAuthorityError(RuntimeError):
    """`config/line_types.yaml` không đọc được — DỪNG, không rơi về mặc định.

    Một mặc định "coi mọi dòng là hàng bán" chạy được và SAI theo hướng im
    lặng: luật giá nhập 0 theo chính sách (`OD-105B-01` §3) biến mất, mọi dòng
    phí quay lại `PENDING`, coverage tụt khỏi 100 % và cả kỳ mất trạng thái
    `OFFICIAL` — mà không màn hình nào nói vì sao. Cùng kỷ luật fail-closed của
    `DEC-143` §1: thà không ra số còn hơn ra một bộ số khác mà không ai biết
    nó khác.
    """



@dataclass(frozen=True)
class PeriodData:
    """Mọi thứ một trang nghiệp vụ cần cho MỘT kỳ, đọc đúng một lần.

    `lines`/`details` là các dòng ĐANG ĐƯỢC BÁO CÁO. Dòng mà Owner đã loại
    (`DEC-PHB02-08` §30) KHÔNG có mặt ở đây và vì thế không thể lọt vào một
    phép gộp nào — `totals` cộng trên chính `lines`, nên `§30` đúng theo cấu
    tạo chứ không nhờ mỗi metric tự nhớ trừ ra.

    `excluded` giữ RIÊNG các dòng đó, để màn hình khôi phục được chúng
    (`§56` CASE EX-07). Nó cố ý không phải một phần của `lines`: một danh sách
    mà "có mặt nhưng không tính" là đúng lớp lỗi mà việc tách này đóng lại.
    """

    lines: list
    details: list
    totals: bm.BusinessTotals
    excluded: list = field(default_factory=list)
    # R3 §1 — `khoá dòng → ngoại lệ gắn dòng còn mở`. Đi CÙNG kỳ chứ không
    # được tra riêng ở từng route: bảng nhân viên, tổng kỳ và hàng đợi ngoại
    # lệ phải đọc cùng một ảnh chụp, nếu không hai màn hình sẽ nói hai câu về
    # cùng một dòng.
    binding_exceptions: dict = field(default_factory=dict)
    # R3 §2 — các đơn có nguy cơ TRỪ CHIẾT KHẤU HAI LẦN (`DEC-180`).
    discount_double_count: tuple = ()
    # R3 §5 — lần chốt đang hiệu lực của kỳ này, `None` = kỳ đang mở.
    closed: Optional[ClosedPeriod] = None

    def _slice(self, keep: list) -> "PeriodData":
        """Lát cắt giữ NGUYÊN mọi lớp phủ của kỳ.

        Viết một lần cho cả hai phép chiếu (nhân viên, sheet): mỗi lần một
        phép chiếu quên chở theo một lớp phủ là một màn hình con nói khác màn
        hình cha về cùng một dòng.
        """
        lines = [self.lines[index] for index in keep]
        return PeriodData(
            lines=lines, details=[self.details[i] for i in keep],
            totals=bm.totals(lines), binding_exceptions=self.binding_exceptions,
            discount_double_count=self.discount_double_count, closed=self.closed)

    def for_employee(self, employee: Optional[str]) -> "PeriodData":
        """Lát cắt của một nhân viên — cùng cấu trúc, để trang dùng chung code."""
        return self._slice([index for index, line in enumerate(self.lines)
                            if line.employee == employee])

    def sheet_assignments(self) -> list[tuple[str, Optional[str]]]:
        """`(khoá sheet, nhân viên)` của TỪNG dòng đang được báo cáo."""
        return [
            (reporting_sheets.sheet_key_of(
                employee=detail["line"].employee,
                employee_group=detail["line"].employee_group,
                product_group=detail["classified_product_group"]),
             detail["line"].employee)
            for detail in self.details
        ]

    def for_sheet(self, sheet: reporting_sheets.Sheet) -> "PeriodData":
        """Lát cắt của MỘT sheet — cùng cấu trúc, cùng code trình bày.

        Đây là phép chiếu duy nhất của toàn bộ không gian làm việc, và nó là
        một PHÂN HOẠCH: `sheet_key_of` là hàm toàn phần, nên mọi dòng thuộc
        đúng một sheet và tổng của các sheet luôn đúng bằng tổng kỳ (`§42`).
        """
        return self._slice([index for index, (key, _employee)
                            in enumerate(self.sheet_assignments())
                            if key == sheet.key])


def bm_unknown_employee_label() -> str:
    """Nhãn của nhóm "chưa xác định nhân viên" trong file xuất.

    Một sheet Excel BẮT BUỘC có tên; `None` không phải một tên. Đây là chỗ
    duy nhất cái nhãn ấy được đặt cho đường xuất file.
    """
    return "Chưa xác định nhân viên"


def snapshot_of(totals: bm.BusinessTotals) -> dict:
    """Chỉ tiêu của một kỳ → dict JSON được, để lưu kèm một lần chốt.

    Chỉ những con số CỘNG ĐƯỢC và trạng thái coverage. Không lưu từng dòng:
    bản chụp là bằng chứng "bộ số nào đã được duyệt", không phải một bản sao
    thứ hai của báo cáo — và một bản sao thứ hai là một nguồn sự thật thứ hai.

    `Decimal` viết ra chuỗi, không float: `str(Decimal)` khứ hồi đúng, còn
    float thì không (`ADR-103`).
    """
    return {
        "lines": totals.lines,
        "orders": totals.orders,
        "sales_revenue": _text(totals.sales_revenue),
        "qualifying_quantity": _text(totals.qualifying_quantity),
        "kpi_profit": _text(totals.kpi_profit),
        "converted_sales": _text(totals.converted_sales),
        "employee_attributed_profit": _text(totals.employee_attributed_profit),
        "unattributed_profit": _text(totals.unattributed_profit),
        "state": totals.state,
        "coverage_covered_lines": totals.coverage.covered_lines,
        "coverage_total_lines": totals.coverage.total_lines,
    }


def _text(value) -> Optional[str]:
    return None if value is None else str(value)


class BusinessReportService:
    def __init__(
        self, *, engine, store: BusinessDecisionStore,
        router: Optional[ConversionRateRouter] = None,
        eligible_costs_path: Optional[Path] = None,
        employees_path: Optional[Path] = None,
        line_types_path: Optional[Path] = None,
        period_store: Optional[PeriodCloseStore] = None,
        binding_store: Optional[BindingExceptionStore] = None,
    ) -> None:
        self._engine = engine
        self._store = store
        self._router = router or ConversionRateRouter.from_yaml(CONVERSION_RATES_PATH)
        self._eligible_costs_path = eligible_costs_path or ELIGIBLE_COSTS_PATH
        self._employees_path = employees_path or EMPLOYEES_PATH
        self._line_types_path = line_types_path or LINE_TYPES_PATH
        # Cùng `Engine` với mọi thẩm quyền khác của vertical: một lần chốt kỳ
        # và các con số nó chốt phải nằm trong cùng một database.
        self._period_store = period_store or PeriodCloseStore(engine)
        self._binding_store = binding_store or BindingExceptionStore(engine)

    @property
    def store(self) -> BusinessDecisionStore:
        return self._store

    @property
    def period_store(self) -> PeriodCloseStore:
        return self._period_store

    @property
    def binding_store(self) -> BindingExceptionStore:
        return self._binding_store

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

    def line_type_vocabulary(self) -> line_type_module.LineTypeVocabulary:
        """Từ vựng loại dòng của R3, đọc lại ở mỗi lần dựng kỳ.

        Đọc lại chứ không nhớ vào bộ nhớ, đúng cùng lý do như
        `kpi_authority_valid`: một file cấu hình vừa được sửa (hay vừa hỏng)
        phải có hiệu lực NGAY, chứ không phải sau lần khởi động lại tiếp theo.
        """
        try:
            return line_type_config.load_vocabulary(self._line_types_path)
        except Exception as exc:  # noqa: BLE001 — mọi lỗi đọc/parse đều fail-closed
            raise LineTypeAuthorityError(
                f"Không đọc được {self._line_types_path}: {exc}") from exc

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
        period: Optional[tuple[int, int]] = None,
    ) -> PeriodData:
        """Kỳ đã hợp nhất MỌI quyết định của Owner, sẵn sàng để gộp.

        Thứ tự ở đây là một hợp đồng, không phải sở thích:

        1. Đọc dòng hiện hành (`raw_lines`) — CHỈ ĐỌC.
        2. Hợp nhất quyết định làm ĐỔI GIÁ TRỊ của một dòng: giá nhập, nhân
           viên, phân loại Gia dụng (mặt hàng + dòng).
        3. TÁCH RA các dòng Owner đã loại khỏi báo cáo (`DEC-PHB02-08` §30).
        4. Gộp — trên đúng tập còn lại.

        Bước 3 nằm SAU bước 2 và TRƯỚC bước 4, và cả hai vị trí đều bắt buộc.
        Sau bước 2 vì một dòng bị loại vẫn phải hiện đúng giá và đúng tên
        người bán trên danh sách khôi phục; trước bước 4 vì `§30` yêu cầu dòng
        đó không góp vào BẤT KỲ chỉ tiêu nào — và cách duy nhất bảo đảm điều
        đó cho cả những chỉ tiêu chưa được viết ra là không đưa nó vào tập
        được cộng.
        """
        rows = business_queries.raw_lines(
            self._engine, date_from=date_from, date_to=date_to)
        overrides = self._store.purchase_price_overrides()
        classifications = self._store.product_groups()
        line_classifications = self._store.line_product_groups()
        lines = business_queries.build_lines(
            rows, overrides=overrides, classifications=classifications,
            router=self._router,
            kpi_authority_valid=self.kpi_authority_valid(),
            employee_overrides=self._store.employee_overrides(),
            line_classifications=line_classifications,
            line_type_vocabulary=self.line_type_vocabulary())
        details = business_queries.line_details(
            rows, lines, classifications=classifications, overrides=overrides,
            line_classifications=line_classifications)

        exclusions = self._store.line_exclusions()
        kept, dropped = [], []
        for detail in details:
            key = (detail["order_key"], detail["product_key"],
                   detail["occurrence_index"])
            excluded = exclusions.get(key)
            if excluded is None:
                kept.append(detail)
            else:
                dropped.append({**detail, "exclusion": excluded})
        kept_lines = [detail["line"] for detail in kept]
        return PeriodData(
            lines=kept_lines, details=kept, totals=bm.totals(kept_lines),
            excluded=dropped,
            # Ba lớp phủ của R3, đọc MỘT lần cho cả kỳ. Chúng nằm ở đây —
            # cùng chỗ, cùng lượt đọc với override giá nhập và phân loại — vì
            # đó là toàn bộ ý nghĩa của "một effective data": bảng nhân viên,
            # tổng kỳ và hàng đợi ngoại lệ không được đi ba đường khác nhau.
            binding_exceptions=self._binding_store.open_keys(),
            discount_double_count=bm.discount_double_count_orders(kept_lines),
            closed=(None if period is None
                    else self._period_store.closed(year=period[0],
                                                   month=period[1])))

    # --- R3 §5: chốt kỳ ------------------------------------------------

    def guard_period_open(self, period: Optional[tuple[int, int]]) -> None:
        """Chặn MỌI lần ghi quyết định rơi vào một kỳ đã chốt.

        Gọi ở tầng dịch vụ chứ không ở `BusinessDecisionStore`: store không
        biết — và theo hàng rào của PHB-03, không được biết — `sale_date` của
        một dòng, vì biết nó nghĩa là đọc `order_line_current`. Kỳ là dữ kiện
        mà tầng route đã có sẵn trong tay.
        """
        if self._period_store.is_closed(period):
            raise PeriodClosedError(period[0], period[1])

    def guard_line_open(self, detail: Optional[dict]) -> None:
        """Chặn theo NGÀY BÁN của chính dòng, không theo kỳ đang xem.

        Hai thứ đó khác nhau ở đúng chỗ nguy hiểm: khung nhìn "toàn bộ dữ
        liệu" không có kỳ, và sửa một dòng của tháng 01 đã chốt từ màn hình
        đó vẫn phải bị chặn.
        """
        sale_date = None if detail is None else detail.get("sale_date")
        if sale_date is None:
            return
        self.guard_period_open((sale_date.year, sale_date.month))

    def guard_product_open(self, product_key: str) -> None:
        """Chặn một quyết định cấp MẶT HÀNG khi nó chạm vào một kỳ đã chốt."""
        closed = self._period_store.closed_periods()
        if not closed:
            return
        touched = business_queries.periods_for_product(self._engine, product_key)
        overlap = sorted(touched & closed)
        if overlap:
            raise PeriodClosedError(*overlap[0])

    def closed_period(self, period: Optional[tuple[int, int]]):
        if period is None:
            return None
        return self._period_store.closed(year=period[0], month=period[1])

    def close_period(
        self, *, period: tuple[int, int], data: PeriodData,
        closed_by: Optional[str] = None, note: Optional[str] = None,
    ) -> ClosedPeriod:
        """Chốt kỳ, kèm bản chụp chỉ tiêu và vân tay của bộ số đã chốt.

        Bản chụp lấy từ CHÍNH `data` mà màn hình vừa hiển thị — không tính
        lại: nếu chốt kỳ đi một đường tính riêng thì con số được duyệt có thể
        khác con số người duyệt đã nhìn, và đó đúng là điều một lần chốt phải
        loại trừ.
        """
        totals = snapshot_of(data.totals)
        return self._period_store.close(
            year=period[0], month=period[1], closed_by=closed_by, note=note,
            totals=totals, line_count=len(data.lines),
            # CÙNG một `totals` đi vào cả bản chụp lẫn vân tay: hai thứ đó
            # không thể trôi khỏi nhau, vì chúng là hai cách viết của cùng một
            # payload (`FIND-R3-IR-01`).
            fingerprint=content_fingerprint(
                details=data.details, totals=totals))

    def reopen_period(
        self, *, period: tuple[int, int], reason: str,
        reopened_by: Optional[str] = None,
    ) -> None:
        self._period_store.reopen(
            year=period[0], month=period[1], reason=reason,
            reopened_by=reopened_by)

    def period_drift(
        self, *, period: Optional[tuple[int, int]], data: PeriodData,
    ) -> bool:
        """Bộ số HIỆN TẠI đã khác bộ số lúc chốt chưa?

        `False` khi kỳ chưa chốt, hoặc khi vân tay trùng. `True` là một sự
        thật cần nói ra: một kỳ đã duyệt mà số đã đổi (vì một lần nạp lại sổ,
        hay một quyết định lọt qua trước khi chốt) thì bản chụp và màn hình
        không còn nói cùng một câu.

        `data` phải là kỳ ĐẦY ĐỦ, không phải một lát cắt theo nhân viên/sheet
        — xem `period_lock.content_fingerprint`. Hai nơi gọi trong `server.py`
        đều truyền `view["data"]`, tức cả kỳ.
        """
        if period is None or data.closed is None:
            return False
        if data.closed.content_fingerprint is None:
            return False
        return data.closed.content_fingerprint != content_fingerprint(
            details=data.details, totals=snapshot_of(data.totals))

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


    # --- Không gian làm việc theo SHEET (DEC-PHB02-08) ------------------

    def sheets(self, data: PeriodData) -> list:
        """Các sheet của kỳ, dựng từ chính tập dòng đang được báo cáo.

        Nguồn là dữ liệu ĐÃ HỢP NHẤT, không phải danh sách thô của pipeline —
        cùng lý do đã nghiệm thu ở `merge_assigned_names` (`OD-5`): ngay sau
        khi Owner chuyển một dòng sang Gia dụng hay gán lại nhân viên, thanh
        tab phải phản ánh điều đó ở lần tải trang kế tiếp, không phải sau một
        lần chạy lại pipeline.
        """
        return reporting_sheets.sheets_for(data.sheet_assignments())

    def export_sheets(self, data: PeriodData) -> list:
        """Các sheet của FILE XUẤT — đúng phân hoạch mà màn hình đang dùng.

        Không có một cách chia thứ hai cho file xuất. `reporting_sheets` là
        phân hoạch đã nghiệm thu của không gian làm việc (`DEC-PHB02-08`
        `§42`): mỗi dòng thuộc ĐÚNG một sheet, nên tổng các sheet luôn bằng
        tổng kỳ. Dựng một cách chia riêng cho file xuất sẽ tạo ra hai câu trả
        lời cho câu hỏi "doanh thu của Nội thành là bao nhiêu".

        Dòng Owner đã LOẠI khỏi báo cáo không có mặt: `data.details` không
        chứa chúng, và file xuất phải nói đúng những gì màn hình nói (`§30`).
        Chúng được đếm riêng ở sheet Tổng kỳ.
        """
        assignments = data.sheet_assignments()
        buckets: dict = {}
        for detail, (key, _employee) in zip(data.details, assignments):
            buckets.setdefault(key, []).append(detail)
        return [
            business_export.ExportSheet(
                key=sheet.key,
                label=sheet.label or bm_unknown_employee_label(),
                details=buckets.get(sheet.key, []))
            for sheet in reporting_sheets.sheets_for(assignments)
        ]

    def export_workbook(
        self, *, data: PeriodData, period_label: str,
        generated_at: Optional[datetime] = None,
    ):
        """Workbook của kỳ, dựng từ ĐÚNG `data` mà màn hình vừa hiển thị.

        Nhận `data` chứ không tự đọc lại kỳ: đọc lại mở ra một khe thời gian
        trong đó một lần lưu có thể chen vào giữa "cái Owner nhìn" và "cái
        Owner tải về", và hai bộ số lệch nhau mà không ai giải thích được.
        """
        return business_export.build_workbook(
            period_label=period_label,
            sheets=self.export_sheets(data),
            period_totals=data.totals,
            generated_at=generated_at,
            closed=data.closed,
            binding_exceptions=data.binding_exceptions,
            discount_double_count=data.discount_double_count,
            excluded=data.excluded,
        )

    def sheet_target(
        self, *, sheet, period: Optional[tuple[int, int]],
    ) -> Optional[Decimal]:
        """Target VND của MỘT sheet trong MỘT tháng, hoặc `None`.

        Đây là chỗ DUY NHẤT quyết định "Target của đơn vị báo cáo này nằm ở
        bảng nào", và nó chỉ có hai nhánh:

            sheet NHÓM     → `group_target`     (`§7`, `§13`)
            sheet NHÂN VIÊN → `employee_target` (PHB-05, `DEC-PHB02-06`)

        Không nhánh nào CỘNG gì lại. Target của Nội thành là con số Owner tự
        đặt, không phải tổng target của Vinh · Quý · Hiệp (`§7`/`§53` CASE
        TG-09), và Gia dụng có Target riêng chứ không mượn của Nội thành
        (`§53` CASE TG-08). Cả hai khẳng định đó đúng ở đây theo cấu tạo: hai
        khoá khác nhau trong hai bảng khác nhau, và không phép cộng nào.

        Sheet "chưa xác định nhân viên" KHÔNG có Target: đặt chỉ tiêu cho một
        tập dòng chưa biết của ai là một con số không ai chịu trách nhiệm.
        """
        if period is None or sheet is None or sheet.unresolved:
            return None
        year, month = period
        if sheet.is_group:
            row = self._store.group_targets(year=year, month=month).get(
                sheet.group_key)
            return None if row is None else row["target_vnd"]
        if not sheet.employee:
            return None
        row = self._store.employee_targets(year=year, month=month).get(
            sheet.employee)
        return None if row is None else row["target_vnd"]

    def set_sheet_target(
        self, *, sheet, period: tuple[int, int], target_vnd: Decimal,
    ) -> None:
        """Ghi Target của một sheet vào ĐÚNG bảng của nó."""
        year, month = period
        if sheet.is_group:
            self._store.set_group_target(
                year=year, month=month, group_key=sheet.group_key,
                target_vnd=target_vnd)
            return
        self._store.set_employee_target(
            year=year, month=month, employee_key=sheet.employee,
            target_vnd=target_vnd)

    def clear_sheet_target(self, *, sheet, period: tuple[int, int]) -> None:
        """Gỡ Target của một sheet — về CHƯA THIẾT LẬP, không phải `0`."""
        year, month = period
        if sheet.is_group:
            self._store.clear_group_target(
                year=year, month=month, group_key=sheet.group_key)
            return
        self._store.clear_employee_target(
            year=year, month=month, employee_key=sheet.employee)

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
