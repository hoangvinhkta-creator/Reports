"""TASK-PRA-003 — trình bày SỐ MỚI: định dạng và GẮN NHÃN, không tính toán.

Cùng hai kỷ luật với ``legacy_presentation`` (TASK-PRA-001 §8), thêm một điều
riêng của PRA-003:

1. Không phép tính nghiệp vụ nào ở đây. Mọi con số đã do
   ``analytics_queries`` tổng hợp; tầng này chỉ đổi cách VIẾT nó ra. Ngoại lệ
   DUY NHẤT là Δ so kỳ trước — một phép trừ và một tỉ lệ giữa HAI con số đã
   tổng hợp sẵn, được frozen contract mục 5.1 yêu cầu tường minh.
2. Không con số nào hiển thị mà thiếu nhãn nguồn. SỐ MỚI = ``PIPELINE_GENERATED``.
3. **``None`` LUÔN thành ``—``, không bao giờ thành ``0``.** Đây là lý do tầng
   này tồn tại tách khỏi template: một ``{{ value or 0 }}`` lỡ tay trong Jinja
   sẽ biến "chưa biết" thành "bằng không" mà không test nào của tầng truy vấn
   bắt được.

``format_number`` được TÁI DỤNG từ ``legacy_presentation`` thay vì nhân bản:
nó thuần định dạng vi-VN (dấu chấm phân cách nghìn) và trung lập với nguồn dữ
liệu — quy ước viết số của Owner không đổi theo việc số đến từ đâu. Tái dụng
ở đây KHÔNG kéo theo ngữ nghĩa legacy nào: nhãn, đơn vị và badge của SỐ MỚI
đều định nghĩa riêng bên dưới.
"""

from __future__ import annotations

import functools
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional

import yaml

from app.modules.config.loader import load_yaml
from app.web.analytics_queries import previous_month
from app.web.legacy_presentation import format_number, format_ratio

# TASK-UIUX-001 — tên NGƯỜI ĐỌC ĐƯỢC của nhóm nhân viên. Nguồn là chính master
# `config/employees.yaml` (`employee_groups[].name`) — cùng file mà
# `business_service` đọc để biết ai là nhân viên — nên không có bảng tên thứ
# hai nào để lệch. Mã lạ hoặc file không đọc được ⟹ trả NGUYÊN mã: một nhãn
# không bao giờ được làm trang sập, và cũng không bao giờ được bịa tên.
_EMPLOYEES_PATH = Path(__file__).resolve().parents[2] / "config" / "employees.yaml"


@functools.lru_cache(maxsize=1)
def _group_names() -> dict[str, str]:
    try:
        data = load_yaml(_EMPLOYEES_PATH)
    except (OSError, yaml.YAMLError):
        return {}
    names: dict[str, str] = {}
    for item in data.get("employee_groups", []) or []:
        if not isinstance(item, dict):
            continue
        code, name = item.get("code"), item.get("name")
        if isinstance(code, str) and isinstance(name, str) and name.strip():
            names[code] = name.strip()
    return names


def group_label(code: Optional[str]) -> str:
    """Tên hiển thị của một nhóm nhân viên; trống ⟹ `—`, mã lạ ⟹ nguyên mã."""
    if not code:
        return "—"
    return _group_names().get(code, code)


# TASK-OWNER-UIUX-002 — THỨ TỰ ĐỌC của các nhân viên, lấy từ chính thứ tự khai
# báo trong master `config/employees.yaml`. Đây KHÔNG phải một quy tắc nghiệp
# vụ mới: nó không đổi một con số nào, không đổi ai thuộc nhóm nào, và không
# quyết định dòng nào cộng vào đâu — nó chỉ trả lời "ai đọc trước" bằng một
# thứ tự mà chủ dự án đã tự viết ra và sửa được. Người không có trong master
# (ví dụ một cái tên vừa được gán lại) xếp SAU, theo alphabet.
@functools.lru_cache(maxsize=1)
def _master_order() -> dict[str, int]:
    try:
        data = load_yaml(_EMPLOYEES_PATH)
    except (OSError, yaml.YAMLError):
        return {}
    order: dict[str, int] = {}
    for item in data.get("employees", []) or []:
        if not isinstance(item, dict):
            continue
        name = item.get("normalized")
        if isinstance(name, str) and name.strip():
            order.setdefault(name.strip(), len(order))
    return order


def employee_master_rank(name: Optional[str]) -> int:
    """Hạng đọc của một nhân viên. Không có trong master ⟹ xếp sau tất cả."""
    if not name:
        return len(_master_order()) + 1
    return _master_order().get(name, len(_master_order()) + 1)


ORIGIN_BADGE = "SỐ MỚI"
ORIGIN_TITLE = "Số do Reports tính từ sổ kế toán đã nạp"
ORIGIN_NOTE = "Số do Reports tính từ sổ kế toán đã nạp."
BOTH_SOURCES_NOTE = (
    "SỐ CŨ = số cũ trong Excel. SỐ MỚI = số Reports tính từ sổ kế toán đã nạp. "
    "Hai loại số không bao giờ được cộng chung."
)
# `DEC-185` §F-03 — RANH GIỚI "SỐ CHÍNH THỨC" vs "SỔ THÔ".
#
# Quyết định của Owner nói rõ nghĩa của việc loại một dòng: dòng đó KHÔNG còn
# nằm trong BÁO CÁO NGHIỆP VỤ CHÍNH THỨC. Nhưng bản ghi kế toán gốc vẫn nguyên
# vẹn (`§31`), nên các trang đọc thẳng sổ đã nạp vẫn thấy dòng đó — và vẫn
# PHẢI thấy, vì đó là bằng chứng.
#
# Hệ quả: hai loại màn hình cùng hiện chữ "doanh thu" nhưng trả lời hai câu
# hỏi khác nhau, và điều nguy hiểm không phải là chúng khác số — mà là người
# đọc không biết mình đang xem cái nào. `F03-06` vì thế không đòi xoá các
# trang thô; nó đòi chúng NÓI RA rằng chúng là bằng chứng, không phải chỉ tiêu.
#
# Chỗ để nói ra điều đó là tầng trình bày, một lần, và mọi trang thô dùng lại
# — chứ không phải một câu chữ chép tay trên từng template.
RAW_SURFACE_BADGE = "SỔ THÔ"
RAW_SURFACE_TITLE = (
    "Đọc thẳng sổ kế toán đã nạp — chưa trừ các dòng Owner đã loại khỏi báo cáo"
)
RAW_SURFACE_NOTE = (
    "Trang này là BẰNG CHỨNG SỔ SÁCH, không phải chỉ tiêu chính thức: nó đếm "
    "cả những dòng Owner đã loại khỏi báo cáo. Số chính thức của công ty nằm ở "
    "Báo cáo và Nhân viên."
)

NO_PREVIOUS_PERIOD = "chưa có dữ liệu kỳ trước"
ALL_DATA_LABEL = "Toàn bộ dữ liệu"

# D3: nhãn ô số lượng là "Tổng số lượng" và KHÔNG được gọi là "Số lượng sản
# phẩm"/"Tổng số SP" — chưa có quy tắc phân loại product-line có thẩm quyền
# (N.7). Con số đếm MỌI dòng, kể cả phí vận chuyển / công lắp đặt / chiết khấu.
QUANTITY_LABEL = "Tổng số lượng"
QUANTITY_NOTE = (
    "Tổng số lượng đếm MỌI dòng của sổ, kể cả phí vận chuyển, công lắp đặt, "
    "chiết khấu và voucher — nên KHÔNG khớp cột \"Tổng số SP\" của báo cáo cũ."
)
ORDER_COLUMN_NOTE = (
    "Một đơn có nhiều nhân viên được đếm ở TỪNG dòng nhân viên liên quan, nên "
    "cột Đơn cộng lại có thể lớn hơn tổng đơn của kỳ. Dòng TỔNG đếm mỗi đơn "
    "đúng một lần."
)
UNKNOWN_EMPLOYEE = "Chưa xác định nhân viên"

# 7 cột SỐ MỚI của trang Nhân viên — OWNER_PRESENTATION_DECISION (KPI-first
# simplification): "LN kế toán" bị bỏ khỏi management UI mặc định (vẫn tính
# và lưu ở backend). Không thêm cột nào khác: top-nhân-viên và
# so-kỳ-trước-theo-nhân-viên là USEFUL_BUT_DEFER.
EMPLOYEE_COLUMNS: tuple[str, ...] = (
    "Nhân viên", "Nhóm", "Đơn", "Dòng hàng", QUANTITY_LABEL, "Doanh thu",
    "LN KPI",
)


def money(value: Optional[Decimal]) -> str:
    """SỐ ĐẾM (số lượng) và mọi con số KHÔNG phải tiền. ``None`` ⟹ ``—``.

    Tên giữ nguyên vì nhiều nơi gọi, nhưng từ `DEC-212` nó KHÔNG còn là hàm
    viết tiền: tiền đi qua `price`/`price_full`. Xem chú thích ở đó.
    """
    return format_number(value)


# `DEC-212` — Owner chốt: mọi con số TIỀN trên màn hình viết theo NGHÌN ĐỒNG.
# Các trang "sổ thô" (Tổng quan · Bán hàng · Sản phẩm · Nhân viên số cũ) nằm
# trong phạm vi đó y như các trang chỉ tiêu: chúng là những tab người dùng mở
# được, và một tab viết `13.550.000` cạnh một tab viết `13.550` cho cùng một
# con số là chỗ hai màn hình đọc như hai sự thật.
#
# `money` ở trên KHÔNG bị đổi hành vi: nó vẫn là hàm viết SỐ ĐẾM, và số lượng
# thì không có đơn vị nghìn để rút. Tách hai hàm chứ không thêm một tham số cờ
# vào một hàm: một cờ ở nơi gọi đọc như một tuỳ chọn trình bày, còn "cái này
# là tiền hay không" là một mệnh đề về chính con số.
def price(value: Optional[Decimal]) -> str:
    """Tiền, viết theo NGHÌN ĐỒNG — chỉ để hiển thị."""
    if value is None:
        return format_number(None)
    return format_number(
        (Decimal(value) / Decimal(1000)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP))


def price_full(value: Optional[Decimal]) -> str:
    """Cùng con số, VND đầy đủ — bản đối chiếu đi kèm mỗi ô rút gọn."""
    return format_number(value)


def count(value: Optional[int]) -> str:
    return "—" if value is None else format_number(Decimal(value))


def coverage(covered: int, total: int) -> str:
    """Coverage viết dạng ``N / M dòng``, cố ý KHÔNG viết dạng phần trăm.

    Hai lý do: (a) ``0 / 351 dòng`` nói thẳng "chưa dòng nào chắc chắn" trong
    khi ``0%`` dễ bị đọc nhầm thành "lãi bằng không"; (b) hai coverage của D1
    có TỬ SỐ khác nhau, và viết ra cả tử lẫn mẫu buộc người đọc thấy điều đó
    thay vì so hai phần trăm như thể chúng cùng nghĩa.
    """
    return f"{count(covered)} / {count(total)} dòng"


def profit(value: Optional[Decimal], covered: int, total: int) -> dict:
    """Một ô lợi nhuận LUÔN đi kèm coverage (quy tắc P4) — không có đường nào
    render con số lợi nhuận mà thiếu mẫu số của nó."""
    return {"text": price(value), "text_full": price_full(value),
            "coverage": coverage(covered, total),
            "missing": value is None}


def delta(current: Optional[Decimal], previous: Optional[Decimal]) -> dict:
    """Δ tuyệt đối + Δ % so kỳ trước.

    Thiếu một trong hai vế ⟹ cả hai ô là ``—``. TUYỆT ĐỐI KHÔNG quy kỳ trước
    vắng mặt về ``0`` rồi in ``-100%``: đó là câu "sụt 100%" cho một kỳ chưa
    bao giờ có dữ liệu, và là nhánh sai kinh điển của mọi dashboard.
    """
    if current is None or previous is None:
        return {"delta": "—", "ratio": "—", "missing": True}
    difference = Decimal(current) - Decimal(previous)
    sign = "+" if difference > 0 else ""
    # Kỳ trước bằng 0 mà kỳ này khác 0: tỉ lệ không xác định. Viết ``—`` chứ
    # không viết một phần trăm vô nghĩa hay chia cho không.
    ratio = "—" if previous == 0 else f"{sign}{format_ratio(difference / Decimal(previous))}"
    return {"delta": f"{sign}{format_number(difference)}", "ratio": ratio,
            "missing": False}


def period_label(period: Optional[tuple[int, int]]) -> str:
    return ALL_DATA_LABEL if period is None else f"Tháng {period[1]:02d}/{period[0]}"


def period_value(period: Optional[tuple[int, int]]) -> str:
    """Giá trị của tham số ``ky`` — ``tat-ca`` cho "Toàn bộ dữ liệu"."""
    return "tat-ca" if period is None else f"{period[0]}-{period[1]:02d}"


def period_options(periods: list[tuple[int, int]]) -> list[dict]:
    """Bộ chọn kỳ: MỌI tuỳ chọn dẫn xuất từ ``sale_date`` đã lưu. Không quý,
    không năm, không khoảng ngày tự do — chúng đã DEFER khỏi slice này."""
    return [{"value": period_value(period), "label": period_label(period)}
            for period in [None, *periods]]


def overview(totals: dict, previous: Optional[dict], *, period, undated: int) -> dict:
    """Mô hình hiển thị của Tổng quan — đúng 10 ô đã qua Minimum-Value Filter.

    ``previous is None`` mang HAI nghĩa và cả hai đều dẫn tới ô so sánh trống:
    đang xem "Toàn bộ dữ liệu" (không bịa kỳ trước cho một khoảng tuỳ ý), hoặc
    tháng liền trước không có dòng pipeline nào.
    """
    lines = totals["lines"]
    return {
        "period_label": period_label(period),
        "orders": count(totals["orders"]),
        "lines": count(lines),
        "quantity": money(totals["quantity"]),
        "total_sales": price(totals["total_sales"]),
        "total_sales_full": price_full(totals["total_sales"]),
        "kpi_profit": profit(totals["kpi_profit"], totals["kpi_lines"], lines),
        "accounting_profit": profit(
            totals["accounting_profit"], totals["accounting_lines"], lines),
        "auto_orders": count(totals["auto_orders"]),
        "review_orders": count(totals["review_orders"]),
        "comparison": None if previous is None else _comparison(totals, previous, period),
        "undated_lines": undated,
    }


def _comparison(totals: dict, previous: dict, period) -> dict:
    """Kỳ trước không có DÒNG NÀO ⟹ MỌI ô so sánh để trống.

    Không được đọc ``previous["orders"] == 0`` như thể đó là "kỳ trước bán
    được 0 đơn": một kỳ CHƯA CÓ DỮ LIỆU và một kỳ bán được không đồng nào là
    hai điều khác nhau, và chỉ một trong hai cho phép nói "tăng 40 đơn".
    """
    empty = previous["lines"] == 0
    prior = {"orders": None, "total_sales": None} if empty else previous
    return {
        "label": period_label(previous_period(period)),
        "orders": delta(totals["orders"], prior["orders"]),
        "total_sales": delta(totals["total_sales"], prior["total_sales"]),
        "empty": empty,
    }


def previous_period(period: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    return None if period is None else previous_month(*period)


def employee_rows(rows: list[dict], totals: dict) -> list[dict]:
    """Bảng nhân viên + dòng ``TỔNG``.

    Dòng TỔNG lấy thẳng từ ``period_totals`` chứ KHÔNG cộng các dòng phía
    trên: với cột Đơn hai cách cho kết quả KHÁC nhau một cách hợp lệ (một đơn
    có thể liên quan nhiều nhân viên) và dòng TỔNG phải đếm mỗi đơn đúng MỘT
    lần.
    """
    return [*(_employee_row(row) for row in rows),
            {**_employee_row({**totals, "employee": "TỔNG", "employee_group": ""}),
             "total_row": True}]


def _employee_row(row: dict) -> dict:
    lines = row["lines"]
    return {
        "employee": row["employee"] or UNKNOWN_EMPLOYEE,
        "employee_group": group_label(row["employee_group"]),
        "orders": count(row["orders"]),
        "lines": count(lines),
        "quantity": money(row["quantity"]),
        "total_sales": price(row["total_sales"]),
        "total_sales_full": price_full(row["total_sales"]),
        "kpi_profit": profit(row["kpi_profit"], row["kpi_lines"], lines),
        "accounting_profit": profit(
            row["accounting_profit"], row["accounting_lines"], lines),
        "total_row": False,
    }


__all__ = [
    "ALL_DATA_LABEL", "BOTH_SOURCES_NOTE", "EMPLOYEE_COLUMNS", "NO_PREVIOUS_PERIOD",
    "ORDER_COLUMN_NOTE", "ORIGIN_BADGE", "ORIGIN_NOTE", "ORIGIN_TITLE",
    "employee_master_rank", "group_label",
    "QUANTITY_LABEL", "QUANTITY_NOTE", "UNKNOWN_EMPLOYEE", "count", "coverage",
    "delta", "employee_rows", "money", "overview", "period_label", "period_options",
    "period_value", "previous_period", "profit",
]
