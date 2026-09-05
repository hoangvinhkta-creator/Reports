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

from app.legacy.models import SUMMARY_COLUMN_FIELDS, UNIT_SUMMARY

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
PERIOD_REFERENCE_YEAR = "REFERENCE_YEAR"   # chuỗi doanh số tháng từ cột AH
PERIOD_WORKBOOK_YEAR = "SUMMARY_SHEET"     # dòng của một sheet Summary (mọi năm)

PERIOD_CLASS_LABELS = {
    PERIOD_REFERENCE_YEAR: "Chuỗi doanh số tháng (từ DataChart)",
    PERIOD_WORKBOOK_YEAR: "Bảng Summary theo người bán",
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
# HỢP ĐỒNG A — chuỗi doanh số tháng của năm trước, suy từ `DataChart`.
#
# Nguồn: cột `AH3:AH14` của `DataChart 2026` — "Doanh số cùng kỳ 2025 — số
# cứng" (`docs/analysis/02_FORMULA_MAPPING.md` §5), đã nhập sẵn thành
# `legacy_monthly_reference.sales_prev_year_vnd` (PHB-02 mục 5.6 `L2`).
#
# ĐÂY KHÔNG PHẢI toàn bộ bằng chứng 2025 — đây là bằng chứng 2025 nằm trong
# sheet `DataChart`. Nguồn 2025 giàu hơn nhiều là sheet `Summary 2025`, đi
# theo `SUMMARY_SHEET_CONTRACT` bên dưới (`DEC-177`). Hai nguồn KHÔNG thay
# thế nhau và KHÔNG được cộng vào nhau: cột `AH` là số tổng tháng gõ cứng,
# `Summary 2025` là bảng người bán × chỉ tiêu.
#
# `UNAVAILABLE` ở bảng này vì vậy có nghĩa hẹp: *không có trong DataChart*.
# Nó KHÔNG còn là tuyên bố "năm 2025 không có chỉ tiêu này" — tuyên bố đó
# thuộc về tình trạng nhập của `Summary 2025`, đo bằng
# `summary_year_availability()`.
# --------------------------------------------------------------------------

REFERENCE_YEAR_CONTRACT: tuple[MetricRule, ...] = (
    _rule(
        "sales_vnd", "Doanh số tháng", "vnd", COMPARABLE,
        "`DEC-180` — cùng chỉ tiêu nghiệp vụ với Doanh thu bán hàng của số "
        "mới. Sổ tay cũ trừ chiết khấu bằng một dòng âm \u201cChiết khấu\u201d; "
        "sổ hiện hành trừ cùng khoản đó bằng cột `discount`. Khác CÁCH GHI, "
        "không khác NGHĨA. Ô này đã là VND nên không cần đổi đơn vị.",
        "DEC-180 (thẩm quyền chủ dự án) · PHB-02 §5.2 S3 · DEC-114 · "
        "docs/analysis/02_FORMULA_MAPPING.md §5 (AH3:AH14)",
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
        "Ô target trong `DataChart` là target của NĂM WORKBOOK (J15/AJ2), "
        "không phải của năm trước. Target lịch sử theo người bán, nếu có, "
        "nằm ở cột `M` của `Summary 2025`.",
        "docs/analysis/02_FORMULA_MAPPING.md §5 · PHB-02 §5.6 L3 · DEC-177",
    ),
    _rule(
        "by_employee", "Chi tiết theo nhân viên", "count", UNAVAILABLE,
        "Sheet `DataChart` không chia theo người bán. Chi tiết theo nhân viên "
        "của năm trước nằm ở `Summary 2025` và đi theo hợp đồng Summary — "
        "xem `summary_year_availability()`.",
        "docs/analysis/02_FORMULA_MAPPING.md §5 · DEC-177",
    ),
    _rule(
        "daily_sales", "Doanh số theo ngày", "vnd", UNAVAILABLE,
        "Lưới ngày `B3:AF14` là của năm workbook. Năm trước chỉ có MỘT ô tổng "
        "mỗi tháng — không có bằng chứng ngày.",
        "docs/analysis/02_FORMULA_MAPPING.md §5",
    ),
)

# --------------------------------------------------------------------------
# HỢP ĐỒNG B — dòng của MỘT SHEET SUMMARY, áp dụng cho MỌI NĂM.
#
# `Summary 2025` và `Summary 2026` có CÙNG 16 cột `C..S` với cùng ý nghĩa
# (PHB-02 mục 5.6 `L6`; `docs/analysis/02_FORMULA_MAPPING.md` §3). Vì vậy
# hợp đồng này KHÔNG gắn với một năm: một dòng `legacy_summary_row` bất kỳ,
# 2025 hay 2026, được đọc theo đúng bảng dưới đây.
#
# Đây là chỗ chi tiết theo NHÂN VIÊN của một năm lịch sử sống: mỗi dòng
# `row_kind = SELLER` là một (kỳ, người bán) với 16 chỉ tiêu.
#
# Không chỉ tiêu nào ở đây là `COMPARABLE`: mọi phân kỳ ngữ nghĩa dưới đây là
# CÓ CHỦ ĐÍCH và đã được freeze ở PHB-02, chứ không phải sai số cần vá. Điều
# đó KHÔNG ngăn việc HIỂN THỊ chúng — hiển thị và so sánh là hai câu hỏi
# khác nhau (`DEC-177`).
# --------------------------------------------------------------------------

SUMMARY_SHEET_CONTRACT: tuple[MetricRule, ...] = (
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
        "sales", "Tổng bán", "kvnd", COMPARABLE,
        "`DEC-180` — cùng chỉ tiêu nghiệp vụ với Doanh thu bán hàng của số "
        "mới. \u201cChiết khấu trừ khác nhau\u201d đã bị bác: sổ tay cũ trừ "
        "bằng một dòng âm, sổ hiện hành trừ bằng cột `discount`, kết quả là "
        "cùng một con số. CẢNH BÁO ĐƠN VỊ: cột này là kVND — mọi phép so với "
        "số mới phải đi qua `to_vnd()` trước.",
        "DEC-180 (thẩm quyền chủ dự án) · PHB-02 §5.2 S3 · DEC-114 · DEC-122 (C4b)",
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

# Tên cũ giữ lại: hợp đồng Summary không còn giới hạn ở năm workbook.
WORKBOOK_YEAR_CONTRACT = SUMMARY_SHEET_CONTRACT

CONTRACTS: dict[str, tuple[MetricRule, ...]] = {
    PERIOD_REFERENCE_YEAR: REFERENCE_YEAR_CONTRACT,
    PERIOD_WORKBOOK_YEAR: SUMMARY_SHEET_CONTRACT,
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
# hợp đồng chứng minh hai bên cùng nghĩa nghiệp vụ. V1 mở ra với bảng RỖNG
# cặp được phép, và `DEC-176` §2 đã viết sẵn cách mở: *"thêm một dòng vào
# `CROSS_ORIGIN_CONTRACT`, kèm bằng chứng bác lý do đang ghi"*.
#
# `DEC-180` là lần mở đầu tiên, và nó đi đúng con đường đó — ĐỔI DỮ LIỆU, giữ
# nguyên nhánh điều khiển. Chỉ hai cặp Tổng bán được mở; bốn cặp còn lại
# (lợi nhuận, DS quy đổi, số đơn, số SP) giữ nguyên `False` vì lý do chặn của
# chúng chưa ai bác. Mở lây sang chúng là làm đúng điều `DEC-176` cấm.
#
# Test chĩa một bảng tự dựng vào cùng hàm này để chứng minh cổng đọc hợp
# đồng chứ không cứng hoá câu trả lời.
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


# Mỗi dòng ghi rõ bằng chứng, để ai muốn mở một cặp phải bác được đúng lý do
# đang ghi ở đó. `DEC-180` là lần đầu điều đó xảy ra: chủ dự án đã bác lý do
# "chiết khấu trừ khác nhau" của hai cặp Tổng bán bằng chính cách sổ tay cũ
# ghi chiết khấu. Bốn cặp còn lại KHÔNG được mở lây — phân kỳ của chúng nằm ở
# chỗ khác và chưa ai bác.
OWNER_SAME_METRIC_REASON = (
    "`DEC-180` (thẩm quyền chủ dự án) — sổ tay cũ trừ chiết khấu bằng MỘT DÒNG "
    "ÂM \u201cChiết khấu\u201d ngay sau dòng hàng; sổ hiện hành trừ cùng khoản "
    "đó bằng cột `discount` (`DEC-114`). HAI CÁCH GHI, MỘT chỉ tiêu nghiệp vụ. "
    "Lý do chặn cũ (\u201cdoanh số tay là số gộp\u201d) đã bị bác bằng bằng "
    "chứng, nên cặp này so được. Đơn vị vẫn phải chuẩn hoá tường minh trước khi "
    "so (`to_vnd`)."
)

CROSS_ORIGIN_CONTRACT: tuple[CrossOriginRule, ...] = (
    CrossOriginRule(
        "sales_vnd", "sales_revenue", True, OWNER_SAME_METRIC_REASON,
    ),
    CrossOriginRule(
        "sales", "sales_revenue", True, OWNER_SAME_METRIC_REASON,
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


# --------------------------------------------------------------------------
# CHUẨN HOÁ ĐƠN VỊ — `DEC-180` §10.
#
# `Summary` ghi tiền bằng **kVND**; `DataChart` và toàn bộ số mới ghi bằng
# **VND**. Chừng nào hai bên không bao giờ gặp nhau trong một phép tính, chênh
# lệch 1.000 lần đó vô hại. `DEC-180` cho phép chúng gặp nhau, nên nó lập tức
# trở thành một lỗi im lặng hạng nặng: `1.000 kVND` vào mẫu số dưới dạng
# `1.000` thay vì `1.000.000`, và "So tháng trước" ra một tỉ lệ lớn gấp
# khoảng nghìn lần — một con số TRÔNG NHƯ một con số, không như một lỗi.
#
# Vì vậy KHÔNG phép so liên-origin nào được đọc thẳng giá trị đã lưu. Mọi
# đường đi qua `to_vnd()`, và một `unit_kind` lạ là LỖI chứ không phải một
# hệ số mặc định — mặc định `1` chính là cách quên nhân 1.000 sống sót.
# --------------------------------------------------------------------------

UNIT_VND = "vnd"
UNIT_KVND = "kvnd"

VND_PER_UNIT: dict[str, Decimal] = {
    UNIT_VND: Decimal(1),
    UNIT_KVND: Decimal(1000),
}

# Đơn vị của mỗi NGUỒN, đọc từ chính hằng số của tầng nhập để hai nơi không
# thể lệch nhau trong im lặng.
SUMMARY_ROW_UNIT = UNIT_SUMMARY.lower()          # "kvnd"
MONTHLY_REFERENCE_UNIT = UNIT_VND


class UnknownUnitError(ValueError):
    """Đơn vị không nằm trong bảng — dừng lại, không đoán một hệ số."""


def to_vnd(value: Optional[Decimal], unit_kind: str) -> Optional[Decimal]:
    """Đổi một số tiền legacy về VND. ``None`` giữ nguyên ``None``.

    ``None`` KHÔNG thành ``0``: ô trống nghĩa là không có bằng chứng, và một
    ``0`` ở đây sẽ đi thẳng vào mẫu số của một phép chia.
    """
    try:
        scale = VND_PER_UNIT[unit_kind]
    except KeyError as exc:
        raise UnknownUnitError(
            f"Không biết đổi đơn vị {unit_kind!r} sang VND — từ chối đoán."
        ) from exc
    return None if value is None else Decimal(value) * scale


# --------------------------------------------------------------------------
# NGUỒN CHUẨN CỦA MỘT KỲ — `DEC-180` §9.
#
# MỘT kỳ ⟹ MỘT nguồn ⟹ MỘT giá trị Tổng bán. Không cộng hai nguồn, không lấy
# trung bình, không trộn dòng thô. Thứ tự dưới đây là thứ tự THẨM QUYỀN, và
# nguồn đầu tiên CÓ SỐ thắng — không nguồn nào bổ sung cho nguồn nào:
#
#   1. Dòng `MONTH_TOTAL` của sheet Summary cho đúng (năm, tháng). Đây là ô
#      "Tổng bán" mà chính báo cáo tay công bố cho tháng đó, và bản nhập nào
#      được đọc cho năm đó đã do `DEC-178` chốt ở tầng history store.
#   2. Ô tháng của `DataChart` (`sales_current_year_vnd`) — dùng khi workbook
#      không có sheet Summary cho tháng đó.
#
# KHÔNG có nhánh "cộng các dòng người bán lại": dòng tổng tháng của workbook
# mang lỗi đã biết `A2` (cộng thiếu người bán), nhưng SỬA lỗi đó bằng cách tự
# cộng lại là công cụ hiện tại tính lại số cũ — đúng điều `TASK-PRA-001` §20
# cấm. Lỗi được NÓI RA (`defects`), không được vá lén.
# --------------------------------------------------------------------------

PERIOD_SOURCE_SUMMARY_MONTH_TOTAL = "LEGACY_SUMMARY_MONTH_TOTAL"
PERIOD_SOURCE_DATACHART_MONTH = "LEGACY_DATACHART_MONTH"

PERIOD_SOURCE_LABELS = {
    PERIOD_SOURCE_SUMMARY_MONTH_TOTAL: "Số cũ — dòng Tổng tháng của sheet Summary",
    PERIOD_SOURCE_DATACHART_MONTH: "Số cũ — ô doanh số tháng của DataChart",
}

MONTH_TOTAL_ROW_KIND = "MONTH_TOTAL"

# Cột Excel của mỗi trường Summary, để tra đúng ô khi đọc lỗi công thức.
_SUMMARY_FIELD_COLUMN = {field: column
                         for column, field in SUMMARY_COLUMN_FIELDS.items()}


@dataclass(frozen=True)
class AuthoritativePeriodSales:
    """Tổng bán CHUẨN của một kỳ lịch sử, đã chuẩn hoá về VND."""

    year: int
    month: int
    sales_vnd: Decimal
    metric_key: str
    raw_value: Decimal
    unit_kind: str
    source: str
    defects: tuple[str, ...] = ()
    origin: str = PROVENANCE

    @property
    def source_label(self) -> str:
        return PERIOD_SOURCE_LABELS[self.source]

    @property
    def origin_label(self) -> str:
        return ORIGIN_LABELS[self.origin]


def _summary_month_total(rows: list[dict], year: int, month: int):
    for row in rows:
        if row.get("row_kind") != MONTH_TOTAL_ROW_KIND:
            continue
        if row.get("year") is None or row.get("month") is None:
            continue
        if int(row["year"]) != year or int(row["month"]) != month:
            continue
        if row.get("sales") is None:
            continue
        return row
    return None


def _summary_defects(row: dict, field: str) -> tuple[str, ...]:
    """Mã lỗi công thức đã biết của ĐÚNG ô đó (`A1`/`A2`/`A4`/`A6`), nếu có.

    `known_defects` khoá theo CỘT Excel, không theo tên trường. Một bản ghi
    chưa giải mã (còn là chuỗi JSON) hay sai hình dạng trả về tuple RỖNG chứ
    không làm sập trang: mất danh sách mã lỗi là mất một chú thích, mất trang
    là mất cả con số.
    """
    defects = row.get("known_defects")
    if not isinstance(defects, Mapping):
        return ()
    codes = defects.get(_SUMMARY_FIELD_COLUMN.get(field)) or []
    if isinstance(codes, str):
        return ()
    return tuple(str(code) for code in codes)


def authoritative_period_sales(
    *, year: int, month: int, summary_rows: Optional[list[dict]] = None,
    monthly_rows: Optional[list[dict]] = None,
) -> Optional[AuthoritativePeriodSales]:
    """Tổng bán của MỘT kỳ theo nguồn có thẩm quyền cao nhất, hoặc ``None``.

    ``None`` nghĩa là *kỳ đó không có bằng chứng số cũ* — nó KHÔNG BAO GIỜ
    được đọc thành 0.
    """
    row = _summary_month_total(summary_rows or [], year, month)
    if row is not None:
        unit = (row.get("unit") or "").lower() or SUMMARY_ROW_UNIT
        raw = Decimal(row["sales"])
        return AuthoritativePeriodSales(
            year=year, month=month, sales_vnd=to_vnd(raw, unit),
            metric_key="sales", raw_value=raw, unit_kind=unit,
            source=PERIOD_SOURCE_SUMMARY_MONTH_TOTAL,
            defects=_summary_defects(row, "sales"),
        )
    for entry in monthly_rows or []:
        if entry.get("year") is None or entry.get("month") is None:
            continue
        if int(entry["year"]) != year or int(entry["month"]) != month:
            continue
        if entry.get("sales_current_year_vnd") is None:
            continue
        raw = Decimal(entry["sales_current_year_vnd"])
        return AuthoritativePeriodSales(
            year=year, month=month,
            sales_vnd=to_vnd(raw, MONTHLY_REFERENCE_UNIT),
            metric_key="sales_vnd", raw_value=raw,
            unit_kind=MONTHLY_REFERENCE_UNIT,
            source=PERIOD_SOURCE_DATACHART_MONTH,
        )
    return None


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


# --------------------------------------------------------------------------
# TÌNH TRẠNG BẰNG CHỨNG CỦA MỘT NĂM LỊCH SỬ (`DEC-177`).
#
# Câu hỏi *"năm 2025 có chỉ tiêu X không?"* KHÔNG được trả lời bằng một hằng
# số viết sẵn trong mã. Nó được ĐO trên chính những dòng đã nhập: chỉ tiêu
# nào có ít nhất một ô mang giá trị thì `AVAILABLE_WITH_ACCEPTED_EVIDENCE`;
# cột tồn tại nhưng mọi ô đều trống thì `NOT_AVAILABLE`.
#
# Cách này chịu được điều mà một danh sách cứng không chịu được: workbook
# thật của chủ dự án có thể mang nhiều hoặc ít cột hơn fixture, và câu trả
# lời phải theo FILE, không theo giả định của người viết mã.
# --------------------------------------------------------------------------

AVAILABLE_WITH_ACCEPTED_EVIDENCE = "AVAILABLE_WITH_ACCEPTED_EVIDENCE"
AVAILABLE_BUT_SEMANTICS_UNCERTAIN = "AVAILABLE_BUT_SEMANTICS_UNCERTAIN"
NOT_AVAILABLE = "NOT_AVAILABLE"

AVAILABILITY_LABELS = {
    AVAILABLE_WITH_ACCEPTED_EVIDENCE: "Có, kèm bằng chứng đã chấp nhận",
    AVAILABLE_BUT_SEMANTICS_UNCERTAIN: "Có số, nhưng ý nghĩa chưa chắc",
    NOT_AVAILABLE: "Không có",
}


@dataclass(frozen=True)
class MetricAvailability:
    rule: MetricRule
    availability: str
    filled_rows: int

    @property
    def availability_label(self) -> str:
        return AVAILABILITY_LABELS[self.availability]


# Dòng `PROGRESS` (`C = B/A`, số ngày đã qua ÷ số ngày trong tháng) mang một
# TỈ LỆ TIẾN ĐỘ ở cột `C`, không phải "Tổng đơn". Chúng có `month = NULL` nên
# đã tự nằm ngoài mọi khung nhìn theo kỳ; loại chúng khỏi phép ĐO tính sẵn có
# để một tỉ lệ tiến độ không bị đếm như một ô "Tổng đơn có giá trị".
MEASURED_ROW_KINDS = ("SELLER", "MONTH_TOTAL", "YEAR_TOTAL")


def summary_year_availability(summary_rows: list[dict]) -> list[MetricAvailability]:
    """Đo từng chỉ tiêu Summary trên những dòng THẬT của một năm.

    ``AVAILABLE_BUT_SEMANTICS_UNCERTAIN`` dành cho chỉ tiêu mà hợp đồng đã
    xếp `UNAVAILABLE` (ví dụ tỉ lệ tồn kho, các cột lương) nhưng file lại có
    số: không giấu số của chủ dự án, cũng không nâng nó lên thành chỉ tiêu
    được hỗ trợ khi ngữ nghĩa chưa được chốt.
    """
    measured = [row for row in summary_rows
                if row.get("row_kind") in MEASURED_ROW_KINDS]
    result: list[MetricAvailability] = []
    for rule in SUMMARY_SHEET_CONTRACT:
        filled = sum(1 for row in measured if row.get(rule.key) is not None)
        if filled == 0:
            availability = NOT_AVAILABLE
        elif rule.displayable:
            availability = AVAILABLE_WITH_ACCEPTED_EVIDENCE
        else:
            availability = AVAILABLE_BUT_SEMANTICS_UNCERTAIN
        result.append(MetricAvailability(
            rule=rule, availability=availability, filled_rows=filled))
    return result


@dataclass(frozen=True)
class SummaryYear:
    """Một năm lịch sử có dòng Summary, kèm những gì thật sự đọc được."""

    year: int
    months: tuple[int, ...]
    sellers: tuple[str, ...]
    seller_rows: int
    total_rows: int

    @property
    def has_employee_detail(self) -> bool:
        return bool(self.sellers)


def summary_years(summary_rows: list[dict]) -> list[SummaryYear]:
    """Gom dòng Summary đã nhập thành từng năm, mới nhất trước.

    Chỉ dòng ``row_kind = SELLER`` mới sinh ra tên người bán: dòng tổng
    tháng cũng có nhãn ở cột B ("Tổng T01") và gộp nó vào danh sách nhân
    viên sẽ dựng ra một "nhân viên" không tồn tại.
    """
    years: dict[int, dict] = {}
    for row in summary_rows:
        year = row.get("year")
        if year is None:
            continue
        bucket = years.setdefault(
            int(year), {"months": set(), "sellers": [], "seller_rows": 0, "rows": 0})
        bucket["rows"] += 1
        if row.get("month") is not None:
            bucket["months"].add(int(row["month"]))
        if row.get("row_kind") == "SELLER":
            bucket["seller_rows"] += 1
            label = row.get("seller_label")
            if label and label not in bucket["sellers"]:
                bucket["sellers"].append(label)
    return [
        SummaryYear(
            year=year,
            months=tuple(sorted(data["months"])),
            sellers=tuple(data["sellers"]),
            seller_rows=data["seller_rows"],
            total_rows=data["rows"],
        )
        for year, data in sorted(years.items(), reverse=True)
    ]


# --------------------------------------------------------------------------
# PHẦN LỊCH SỬ CHƯA ĐỌC ĐƯỢC — phải nói ra, không được im lặng.
# --------------------------------------------------------------------------

SHEET_SCOPE_OPTIONAL = "OPTIONAL_IMPORT"


@dataclass(frozen=True)
class UnreadSheet:
    sheet_name: str
    unclassified_rows: int
    imported_rows: int
    preview: str


def unread_sheets(sheets_imported) -> list[UnreadSheet]:
    """Sheet OPTIONAL_IMPORT còn dòng có số mà contract chưa phân loại được.

    Đây là con số duy nhất trả lời được câu "chủ dự án còn phải cấp thêm gì".
    Nó đến từ chính lần nhập, không phải từ một phỏng đoán.
    """
    entries = sheets_imported or []
    return [
        UnreadSheet(
            sheet_name=entry.get("sheet_name", "—"),
            unclassified_rows=int(entry.get("unclassified_rows") or 0),
            imported_rows=int(entry.get("imported_rows") or 0),
            preview=entry.get("unclassified_preview", ""),
        )
        for entry in entries
        if isinstance(entry, dict) and int(entry.get("unclassified_rows") or 0) > 0
    ]



# --------------------------------------------------------------------------
# THẨM QUYỀN NGUỒN (`DEC-178`).
#
# Hai nguồn cùng nói về một năm lịch sử. Quyết định của chủ dự án đã freeze:
# workbook MỘT NĂM độc lập là nguồn chuẩn; bản sao Summary nhúng trong
# workbook năm hiện hành là bằng chứng thứ cấp. Khi lệch nhau, bản độc lập
# thắng — không trộn, không trung bình, không "ai ghi sau thì thắng".
# --------------------------------------------------------------------------

SOURCE_AUTHORITY_YEAR = "AUTHORITATIVE_YEAR"
SOURCE_AUTHORITY_SNAPSHOT = "WORKBOOK_SNAPSHOT"

SOURCE_AUTHORITY_LABELS = {
    SOURCE_AUTHORITY_YEAR: "Nguồn chuẩn của năm",
    SOURCE_AUTHORITY_SNAPSHOT: "Bản sao trong workbook năm khác",
}

SOURCE_AUTHORITY_NOTE = (
    "Số của năm này lấy từ workbook lịch sử riêng của năm đó — nguồn chuẩn. "
    "Bản sao nằm trong workbook năm hiện hành chỉ là bằng chứng đối chiếu và "
    "KHÔNG bao giờ ghi đè lên nguồn chuẩn."
)


def source_authority_label(value: Optional[str]) -> str:
    # NULL = bản nhập có trước `DEC-178` ⟹ đọc như bản sao thứ cấp.
    return SOURCE_AUTHORITY_LABELS.get(
        value or SOURCE_AUTHORITY_SNAPSHOT,
        SOURCE_AUTHORITY_LABELS[SOURCE_AUTHORITY_SNAPSHOT],
    )


# Sheet chi tiết của workbook một năm: được GHI TÊN nhưng cố ý KHÔNG nhập ô
# nào (`LEGACY_LINE_DETAIL_2025 = DEFERRED`). Chúng mang tên, số điện thoại
# và địa chỉ khách hàng, nên đưa vào history store là một quyết định quản trị
# dữ liệu cá nhân — không phải một chi tiết triển khai của PHB-04.
SHEET_SCOPE_DETAIL_NOT_INGESTED = "DETAIL_NOT_INGESTED"


def deferred_detail_sheets(sheets_imported) -> int:
    return sum(
        1 for entry in (sheets_imported or [])
        if isinstance(entry, dict)
        and entry.get("scope") == SHEET_SCOPE_DETAIL_NOT_INGESTED
    )
