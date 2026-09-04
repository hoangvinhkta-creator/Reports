"""PHB-04 — Legacy Reference V1: hợp đồng ngữ nghĩa của số cũ, viết bằng mã.

Module này KHÔNG đọc database, KHÔNG tính lại số nghiệp vụ và KHÔNG ghi gì.
Nó chỉ làm ba việc, và ba việc đó là toàn bộ PHB-04 V1:

1. **Phân loại** mỗi chỉ tiêu legacy vào đúng một lớp bằng chứng
   (``COMPARABLE`` / ``REFERENCE_ONLY`` / ``UNAVAILABLE`` /
   ``OWNER_DECISION_REQUIRED``), kèm lý do truy được về bằng chứng đã chấp
   nhận.
2. **Chiếu** kỳ lịch sử của năm trước ra thành kỳ đọc được, từ ĐÚNG một
   nguồn đã được chấp nhận: cột ``AH`` của ``DataChart 2026``
   (``legacy_monthly_reference.sales_prev_year_vnd``, xem
   ``docs/tasks/PHB-02-business-parity-contract.md`` mục 5.6 `L2`).
3. **Chặn** mọi phép so sánh giữa số cũ và số của pipeline hiện hành trừ khi
   hợp đồng chứng minh được hai bên cùng một nghĩa nghiệp vụ.

Vì sao không có bảng mới, không có migration: đường lưu số cũ ĐÃ tồn tại và
đã được nghiệm thu ở ``TASK-PRA-001`` (bốn bảng ``legacy_*``, cột ``origin``
có CHECK constraint ``origin = 'LEGACY_REFERENCE'``). PHB-04 là một phép
CHIẾU CHỈ-ĐỌC trên dữ liệu đó — nên nó không thể tạo dòng hàng giả, không
chạm Product Identity, không chạm Tracking, và xoá/nhập lại dữ liệu kế toán
hiện hành không thể làm đổi một con số lịch sử nào.

Ranh giới cứng — điều module này KHÔNG BAO GIỜ làm:
- không tự tính một tỉ lệ tăng trưởng nào giữa số cũ và số mới;
- không biến ô trống thành ``0``;
- không suy ra một chỉ tiêu lịch sử còn thiếu từ những chỉ tiêu đang có.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Optional

# --------------------------------------------------------------------------
# Lớp bằng chứng của một chỉ tiêu legacy (PHB-04 mục 5).
# --------------------------------------------------------------------------

COMPARABLE = "COMPARABLE"
REFERENCE_ONLY = "REFERENCE_ONLY"
UNAVAILABLE = "UNAVAILABLE"
OWNER_DECISION_REQUIRED = "OWNER_DECISION_REQUIRED"

METRIC_CLASSES = (COMPARABLE, REFERENCE_ONLY, UNAVAILABLE, OWNER_DECISION_REQUIRED)

CLASS_LABELS = {
    COMPARABLE: "So được với số mới",
    REFERENCE_ONLY: "Chỉ để tham chiếu",
    UNAVAILABLE: "Không có bằng chứng",
    OWNER_DECISION_REQUIRED: "Chờ chủ dự án quyết",
}

PROVENANCE = "LEGACY_REFERENCE"
PROVENANCE_LABEL = "Dữ liệu tham chiếu lịch sử"
PROVENANCE_NOTE = (
    "Số cũ lấy nguyên trạng từ báo cáo tay. KHÔNG do công cụ hiện tại tính lại, "
    "và KHÔNG được coi là số kế toán chính thức của kỳ."
)

# Hai lớp kỳ legacy. Cả hai cùng `origin = LEGACY_REFERENCE`; khác nhau ở CHỖ
# lấy số trong workbook, nên khác nhau ở tập chỉ tiêu có bằng chứng.
PERIOD_REFERENCE_YEAR = "REFERENCE_YEAR"   # năm trước, chỉ có cột AH
PERIOD_WORKBOOK_YEAR = "WORKBOOK_YEAR"     # năm của workbook: Summary + DataChart

PERIOD_CLASS_LABELS = {
    PERIOD_REFERENCE_YEAR: "Kỳ tham chiếu (chỉ có doanh số tháng)",
    PERIOD_WORKBOOK_YEAR: "Kỳ báo cáo tay đầy đủ",
}


@dataclass(frozen=True)
class MetricRule:
    """Một dòng của hợp đồng: chỉ tiêu này thuộc lớp nào, và vì sao."""

    key: str
    label: str
    unit_kind: str
    metric_class: str
    reason: str
    evidence: str

    @property
    def displayable(self) -> bool:
        return self.metric_class in (COMPARABLE, REFERENCE_ONLY)

    @property
    def class_label(self) -> str:
        return CLASS_LABELS[self.metric_class]


def _rule(key, label, unit_kind, metric_class, reason, evidence) -> MetricRule:
    return MetricRule(key=key, label=label, unit_kind=unit_kind,
                      metric_class=metric_class, reason=reason, evidence=evidence)


# --------------------------------------------------------------------------
# HỢP ĐỒNG A — kỳ tham chiếu năm trước (2025 với workbook 2026).
#
# Bằng chứng DUY NHẤT đã được chấp nhận cho năm 2025 là cột `AH3:AH14` của
# `DataChart 2026` — "Doanh số cùng kỳ 2025 — số cứng"
# (`docs/analysis/02_FORMULA_MAPPING.md` §5), đã nhập sẵn thành
# `legacy_monthly_reference.sales_prev_year_vnd` (PHB-02 mục 5.6 `L2`).
#
# Sheet `Summary 2025` KHÔNG phải nguồn: `DEC-169` là quyết định của chủ dự
# án — không import, không persist, không query, không display. Sheet đó
# cũng không có MỘT ô công thức nào trên toàn bộ 755 dòng, nên không dòng nào
# phân loại được. PHB-04 KHÔNG mở lại quyết định đó.
# --------------------------------------------------------------------------

REFERENCE_YEAR_CONTRACT: tuple[MetricRule, ...] = (
    _rule(
        "sales_vnd", "Doanh số tháng", "vnd", REFERENCE_ONLY,
        "Số tổng nhập tay trong workbook. Báo cáo tay trừ chiết khấu khác cách "
        "công cụ hiện tại trừ, nên KHÔNG cùng nghĩa với Doanh thu bán hàng của "
        "số mới — hiện được, so thì không.",
        "PHB-02 §5.2 S3 · DEC-114 · docs/analysis/02_FORMULA_MAPPING.md §5 (AH3:AH14)",
    ),
    _rule(
        "orders", "Tổng đơn", "count", UNAVAILABLE,
        "Không có ô nào của năm trước ghi số đơn.",
        "docs/analysis/02_FORMULA_MAPPING.md §5 — DataChart chỉ có doanh số",
    ),
    _rule(
        "products", "Tổng số SP", "count", UNAVAILABLE,
        "Không có ô nào của năm trước ghi số sản phẩm.",
        "docs/analysis/02_FORMULA_MAPPING.md §5",
    ),
    _rule(
        "converted_revenue", "DS quy đổi", "kvnd", UNAVAILABLE,
        "Không có ô nào của năm trước ghi doanh số quy đổi.",
        "docs/analysis/02_FORMULA_MAPPING.md §5",
    ),
    _rule(
        "profit", "Tổng lợi nhuận", "kvnd", UNAVAILABLE,
        "Không có ô nào của năm trước ghi lợi nhuận.",
        "docs/analysis/02_FORMULA_MAPPING.md §5",
    ),
    _rule(
        "target", "Target", "kvnd", UNAVAILABLE,
        "Target trong workbook là target của NĂM WORKBOOK (J15/AJ2), không "
        "phải của năm trước.",
        "docs/analysis/02_FORMULA_MAPPING.md §5 · PHB-02 §5.6 L3",
    ),
    _rule(
        "by_employee", "Chi tiết theo nhân viên", "count", UNAVAILABLE,
        "Chia theo người bán của năm trước chỉ có ở sheet `Summary 2025`, mà "
        "`DEC-169` đã chốt là KHÔNG import / persist / query / display.",
        "DEC-169",
    ),
    _rule(
        "daily_sales", "Doanh số theo ngày", "vnd", UNAVAILABLE,
        "Lưới ngày `B3:AF14` là của năm workbook. Năm trước chỉ có MỘT ô tổng "
        "mỗi tháng — không có bằng chứng ngày.",
        "docs/analysis/02_FORMULA_MAPPING.md §5",
    ),
)

# --------------------------------------------------------------------------
# HỢP ĐỒNG B — kỳ báo cáo tay của năm workbook (Summary 2026).
#
# Những dòng này ĐÃ hiển thị từ TASK-PRA-001 (trang Nhân viên / Doanh số
# ngày). PHB-04 không đổi cách hiển thị chúng; nó chỉ nói RÕ lớp bằng chứng
# của từng chỉ tiêu, để không ai lấy chúng ra so với số mới.
#
# Không chỉ tiêu nào ở đây là `COMPARABLE`: mọi phân kỳ ngữ nghĩa dưới đây là
# CÓ CHỦ ĐÍCH và đã được freeze ở PHB-02, chứ không phải sai số cần vá.
# --------------------------------------------------------------------------

WORKBOOK_YEAR_CONTRACT: tuple[MetricRule, ...] = (
    _rule(
        "orders", "Tổng đơn", "count", REFERENCE_ONLY,
        "Báo cáo tay đếm đơn theo cách của người lập; số mới đếm "
        "`COUNT DISTINCT order_key`. Không có bằng chứng hai cách cho cùng kết quả.",
        "PHB-02 §11 (M1)",
    ),
    _rule(
        "products", "Tổng số SP", "count", REFERENCE_ONLY,
        "Ô nguồn `E1` bị trừ một tỉ lệ phần trăm khỏi một số lượng (lỗi A1) "
        "nên có kỳ ra số không nguyên. Số mới dùng ngưỡng đơn giá > 1.000.000.",
        "PHB-02 §5.5 X1 · DEC-PHB02-03 · docs/analysis/05_EXCEPTIONS.md",
    ),
    _rule(
        "sales", "Tổng bán", "kvnd", REFERENCE_ONLY,
        "Chiết khấu trừ khác nhau: Doanh thu bán hàng của số mới là số NET "
        "theo `DEC-114`, khác `Tổng bán` của báo cáo tay — phân kỳ có chủ đích.",
        "PHB-02 §5.2 S3 · DEC-114 · DEC-122 (C4b)",
    ),
    _rule(
        "converted_revenue", "DS quy đổi", "kvnd", REFERENCE_ONLY,
        "Dòng tổng tháng của workbook cộng thiếu người bán (lỗi A2) và có kỳ "
        "dùng số `X` gõ tay. Số mới quy đổi bằng PHÉP CHIA theo từng nhóm.",
        "PHB-02 §5.5 X2/X6 · DEC-PHB02-04 · DEC-119 · DEC-120",
    ),
    _rule(
        "profit", "Tổng lợi nhuận", "kvnd", REFERENCE_ONLY,
        "Lợi nhuận cũ dựa trên giá nhập sửa tay trong Excel. Lợi nhuận KPI của "
        "số mới chỉ CHÍNH THỨC khi coverage giá nhập đạt 100 %. Hai nghĩa khác "
        "nhau — cấm sinh tỉ lệ tăng trưởng giữa chúng.",
        "PHB-02 §5.2 S14 · DEC-143 · DEC-PHB02-02",
    ),
    _rule(
        "vs_prev_month_ratio", "So tháng trước", "ratio", REFERENCE_ONLY,
        "Cột `I` của workbook so trên DS QUY ĐỔI và có kỳ dùng mẫu số gõ cứng "
        "(lỗi A6). Chỉ tiêu được so của số mới là DOANH THU BÁN HÀNG.",
        "PHB-02 §5.5 X5/X9 · DEC-PHB02-07",
    ),
    _rule(
        "target", "Target", "kvnd", REFERENCE_ONLY,
        "Target lịch sử là số chỉ-đọc; target thật đến từ cấu hình do chủ dự "
        "án nhập (PHB-05). Cấm gộp số lịch sử vào chỉ tiêu của số mới.",
        "PHB-02 §5.6 L3 · DEC-PHB02-06",
    ),
    _rule(
        "vs_target_ratio", "So target", "ratio", REFERENCE_ONLY,
        "Mẫu số là target lịch sử chỉ-đọc ở trên, nên tỉ lệ thừa hưởng đúng "
        "giới hạn đó.",
        "PHB-02 §5.6 L3 · DEC-PHB02-06",
    ),
    _rule(
        "margin_ratio", "Tỉ suất lợi nhuận", "ratio", REFERENCE_ONLY,
        "Có trong workbook nhưng số mới CHƯA có chỉ tiêu tương ứng (đã hoãn "
        "`D1`), nên không có gì để so.",
        "PHB-02 §5.4 D1",
    ),
    _rule(
        "stock_ratio", "Tỉ lệ tồn kho", "ratio", UNAVAILABLE,
        "Cột `Nơi nhập` không tồn tại trong file ERP nên số mới không dựng "
        "được chỉ tiêu này; giá trị cũ giữ trong kho lưu, không đưa lên V1.",
        "PHB-02 §5.4 D8",
    ),
    _rule(
        "actual_profit", "Lợi nhuận thực nhận", "kvnd", REFERENCE_ONLY,
        "Số cũ giữ nguyên trạng; không có định nghĩa tương ứng đã freeze ở số mới.",
        "PHB-02 §5.2 S12",
    ),
    _rule(
        "bonus", "Thưởng", "kvnd", UNAVAILABLE,
        "Thưởng / ngày công / lương là luật nhân sự, đã hoãn khỏi V1.",
        "PHB-02 §5.4 D7",
    ),
    _rule(
        "workdays", "Ngày công", "count", UNAVAILABLE,
        "Cùng lý do với Thưởng.", "PHB-02 §5.4 D7",
    ),
    _rule(
        "base_salary", "Lương cơ bản", "kvnd", UNAVAILABLE,
        "Cùng lý do với Thưởng.", "PHB-02 §5.4 D7",
    ),
    _rule(
        "allowance", "Phụ cấp", "kvnd", UNAVAILABLE,
        "Cùng lý do với Thưởng.", "PHB-02 §5.4 D7",
    ),
    _rule(
        "total_salary", "Tổng lương", "kvnd", UNAVAILABLE,
        "Cùng lý do với Thưởng.", "PHB-02 §5.4 D7",
    ),
)

CONTRACTS: dict[str, tuple[MetricRule, ...]] = {
    PERIOD_REFERENCE_YEAR: REFERENCE_YEAR_CONTRACT,
    PERIOD_WORKBOOK_YEAR: WORKBOOK_YEAR_CONTRACT,
}


def rules(period_class: str) -> tuple[MetricRule, ...]:
    return CONTRACTS[period_class]


def rule_for(period_class: str, metric_key: str) -> Optional[MetricRule]:
    for item in CONTRACTS[period_class]:
        if item.key == metric_key:
            return item
    return None


def supported_metrics(period_class: str) -> tuple[MetricRule, ...]:
    return tuple(item for item in CONTRACTS[period_class] if item.displayable)


def unavailable_metrics(period_class: str) -> tuple[MetricRule, ...]:
    return tuple(
        item for item in CONTRACTS[period_class] if item.metric_class == UNAVAILABLE
    )


# --------------------------------------------------------------------------
# CHIẾU KỲ THAM CHIẾU NĂM TRƯỚC.
#
# `legacy_monthly_reference` khoá theo NĂM WORKBOOK; giá trị của năm trước
# nằm ở cột `sales_prev_year_vnd` của chính dòng đó. Chiếu = ĐỔI KHOÁ, không
# phải tính: giá trị đi thẳng từ ô Excel ra màn hình, y hệt nguyên tắc "no
# recalculation" của TASK-PRA-001 §20.
# --------------------------------------------------------------------------

REFERENCE_YEAR_SOURCE = "DataChart 2026!AH — Doanh số cùng kỳ năm trước (số cứng)"
REFERENCE_YEAR_UNIT = "vnd"


@dataclass(frozen=True)
class ReferencePeriod:
    """Một tháng lịch sử đọc được, kèm đủ dấu vết nguồn.

    ``value is None`` KHÔNG BAO GIỜ được hiểu thành 0 — nó có nghĩa là ô
    nguồn trống, tức kỳ đó không có bằng chứng.
    """

    year: int
    month: int
    metric_key: str
    value: Optional[Decimal]
    unit_kind: str
    period_class: str
    provenance: str
    source: str
    derived_from_year: int
    derived_from_month: int

    @property
    def available(self) -> bool:
        return self.value is not None


def reference_periods(monthly_rows: list[dict]) -> list[ReferencePeriod]:
    """Kỳ năm-trước suy ra từ các dòng `legacy_monthly_reference`.

    Năm trước = ``row["year"] - 1``: không hard-code 2025 ở bất kỳ đâu, để
    workbook của năm sau tự động sinh ra kỳ tham chiếu đúng của nó.
    """
    periods = [
        ReferencePeriod(
            year=int(row["year"]) - 1,
            month=int(row["month"]),
            metric_key="sales_vnd",
            value=row.get("sales_prev_year_vnd"),
            unit_kind=REFERENCE_YEAR_UNIT,
            period_class=PERIOD_REFERENCE_YEAR,
            provenance=PROVENANCE,
            source=REFERENCE_YEAR_SOURCE,
            derived_from_year=int(row["year"]),
            derived_from_month=int(row["month"]),
        )
        for row in monthly_rows
        if row.get("year") is not None and row.get("month") is not None
    ]
    return sorted(periods, key=lambda item: (item.year, item.month))


def reference_years(periods: list[ReferencePeriod]) -> list[int]:
    return sorted({item.year for item in periods})


def has_any_value(periods: list[ReferencePeriod]) -> bool:
    """Có ít nhất một ô nguồn thật sự mang số.

    Dùng để phân biệt "chưa nhập workbook nào" với "đã nhập nhưng cột năm
    trước trống" — hai tình huống dẫn tới hai câu khác nhau cho chủ dự án.
    """
    return any(item.available for item in periods)


# --------------------------------------------------------------------------
# CỔNG SO SÁNH.
#
# Quy tắc: so sánh giữa MỘT số cũ và MỘT số của pipeline chỉ được phép khi
# hợp đồng chứng minh hai bên cùng nghĩa nghiệp vụ. Ở V1 KHÔNG chỉ tiêu nào
# đạt điều đó — mọi cặp đều có ít nhất một phân kỳ ngữ nghĩa đã freeze ở
# PHB-02. Vì vậy cổng này trả "không so được" cho mọi cặp thật.
#
# Cổng vẫn được viết như một cổng THẬT, không phải một hằng `False`: bảng
# `CROSS_ORIGIN_CONTRACT` là dữ liệu, và `compare()` nhận bảng qua tham số.
# Ngày nào một chỉ tiêu được chứng minh là `COMPARABLE`, chỉ cần thêm một
# dòng dữ liệu — không phải sửa nhánh điều khiển. Test chĩa một bảng cho
# phép vào cùng hàm này để chứng minh cổng đọc hợp đồng chứ không cứng hoá
# câu trả lời.
# --------------------------------------------------------------------------

COMPARISON_UNAVAILABLE_NOTE = "Không so được — số cũ và số mới không cùng một nghĩa"


@dataclass(frozen=True)
class CrossOriginRule:
    """Một cặp (chỉ tiêu legacy → chỉ tiêu số mới) và phán quyết của hợp đồng."""

    legacy_key: str
    current_key: str
    allowed: bool
    reason: str


@dataclass(frozen=True)
class ComparisonResult:
    allowed: bool
    note: str
    percent: Optional[Decimal] = None


# V1: MỌI cặp đều bị chặn. Mỗi dòng ghi rõ bằng chứng của phân kỳ, để lần sau
# ai muốn mở một cặp phải bác được đúng lý do đó.
CROSS_ORIGIN_CONTRACT: tuple[CrossOriginRule, ...] = (
    CrossOriginRule(
        "sales_vnd", "sales_revenue", False,
        "Doanh số tay là số gộp; Doanh thu bán hàng của số mới đã trừ chiết "
        "khấu theo DEC-114 — phân kỳ có chủ đích (PHB-02 §5.2 S3).",
    ),
    CrossOriginRule(
        "sales", "sales_revenue", False,
        "Cùng lý do: `Tổng bán` của báo cáo tay ≠ doanh thu NET (PHB-02 §5.2 S3).",
    ),
    CrossOriginRule(
        "profit", "kpi_profit", False,
        "Lợi nhuận cũ dùng giá nhập sửa tay; lợi nhuận KPI chỉ chính thức khi "
        "coverage = 100 % (PHB-02 §5.2 S14, DEC-PHB02-02).",
    ),
    CrossOriginRule(
        "converted_revenue", "converted_sales", False,
        "Workbook cộng thiếu người bán ở dòng tổng và có số `X` gõ tay; số mới "
        "quy đổi bằng phép chia theo nhóm (PHB-02 §5.5 X2/X6, DEC-PHB02-04).",
    ),
    CrossOriginRule(
        "orders", "orders", False,
        "Không có bằng chứng hai cách đếm đơn cho cùng kết quả (PHB-02 §11 M1).",
    ),
    CrossOriginRule(
        "products", "qualifying_quantity", False,
        "Ô nguồn cũ mang lỗi A1; số mới dùng ngưỡng đơn giá đã freeze "
        "(PHB-02 §5.5 X1, DEC-PHB02-03).",
    ),
)


def cross_origin_rule(
    legacy_key: str, current_key: str, *,
    contract: tuple[CrossOriginRule, ...] = CROSS_ORIGIN_CONTRACT,
) -> Optional[CrossOriginRule]:
    for item in contract:
        if item.legacy_key == legacy_key and item.current_key == current_key:
            return item
    return None


def compare(
    legacy_value: Optional[Decimal], current_value: Optional[Decimal], *,
    legacy_key: str, current_key: str,
    contract: tuple[CrossOriginRule, ...] = CROSS_ORIGIN_CONTRACT,
) -> ComparisonResult:
    """So sánh liên-origin — CHỈ khi hợp đồng cho phép.

    Ba nhánh "không có số", cố ý không gộp, vì chúng dẫn tới ba câu khác nhau:
    hợp đồng chưa nói tới cặp này · hợp đồng cấm cặp này · hợp đồng cho phép
    nhưng thiếu số. Không nhánh nào trả về 0 hay ``-100 %``.
    """
    rule = cross_origin_rule(legacy_key, current_key, contract=contract)
    if rule is None:
        return ComparisonResult(
            allowed=False,
            note="Hợp đồng Legacy Reference V1 chưa xét cặp chỉ tiêu này — không so.",
        )
    if not rule.allowed:
        return ComparisonResult(
            allowed=False, note=f"{COMPARISON_UNAVAILABLE_NOTE}. {rule.reason}",
        )
    if legacy_value is None or current_value is None or current_value == 0:
        return ComparisonResult(
            allowed=True, note="Thiếu số ở một trong hai kỳ — không tính được tỉ lệ.",
        )
    return ComparisonResult(
        allowed=True, note="",
        percent=(Decimal(current_value) - Decimal(legacy_value))
        / Decimal(legacy_value) * 100,
    )


def comparison_summary(
    contract: tuple[CrossOriginRule, ...] = CROSS_ORIGIN_CONTRACT,
) -> list[dict]:
    """Bảng "so được ở đâu" để hiển thị nguyên văn cho chủ dự án."""
    return [
        {
            "legacy_key": item.legacy_key,
            "current_key": item.current_key,
            "allowed": item.allowed,
            "verdict": "So được" if item.allowed else "Không so được",
            "reason": item.reason,
        }
        for item in contract
    ]


def has_comparable_metric(
    contract: tuple[CrossOriginRule, ...] = CROSS_ORIGIN_CONTRACT,
) -> bool:
    return any(item.allowed for item in contract)


# --------------------------------------------------------------------------
# ĐIỀU HƯỚNG KỲ — legacy và số mới nằm cạnh nhau, KHÔNG trộn vào một dòng số.
# --------------------------------------------------------------------------

ORIGIN_PIPELINE = "PIPELINE_GENERATED"

ORIGIN_LABELS = {
    PROVENANCE: "SỐ CŨ",
    ORIGIN_PIPELINE: "SỐ MỚI",
}


@dataclass(frozen=True)
class PeriodNavigationRow:
    """Một kỳ và những origin THỰC SỰ có dữ liệu cho kỳ đó."""

    year: int
    month: int
    origins: tuple[str, ...]

    @property
    def has_legacy(self) -> bool:
        return PROVENANCE in self.origins

    @property
    def has_pipeline(self) -> bool:
        return ORIGIN_PIPELINE in self.origins

    @property
    def both(self) -> bool:
        return self.has_legacy and self.has_pipeline

    @property
    def origin_labels(self) -> list[str]:
        return [ORIGIN_LABELS[origin] for origin in self.origins]


def period_navigation(
    *,
    legacy_summary_periods: list[tuple[int, Optional[int]]],
    legacy_reference_periods: list[ReferencePeriod],
    pipeline_periods: list[tuple[int, int]],
) -> list[PeriodNavigationRow]:
    """Danh mục kỳ, mới nhất trước, mỗi kỳ ghi rõ có origin nào.

    Một kỳ có CẢ HAI origin vẫn là MỘT dòng với HAI nhãn — chưa bao giờ là
    một con số hợp nhất. `DEC-166 E`: số cũ và số mới không bao giờ cộng chung.
    Kỳ tham chiếu chỉ được tính là "có số cũ" khi ô nguồn thật sự mang giá
    trị; một ô trống không được biến thành một kỳ có dữ liệu.
    """
    origins: dict[tuple[int, int], set[str]] = {}

    def _add(year: int, month: int, origin: str) -> None:
        origins.setdefault((int(year), int(month)), set()).add(origin)

    for year, month in legacy_summary_periods:
        if month is not None:
            _add(year, month, PROVENANCE)
    for item in legacy_reference_periods:
        if item.available:
            _add(item.year, item.month, PROVENANCE)
    for year, month in pipeline_periods:
        _add(year, month, ORIGIN_PIPELINE)

    return [
        PeriodNavigationRow(
            year=key[0], month=key[1],
            origins=tuple(sorted(origins[key], reverse=True)),
        )
        for key in sorted(origins, reverse=True)
    ]
