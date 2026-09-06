"""PHB-07 — CƠ CẤU của kết quả nghiệp vụ chính thức theo ĐƠN VỊ BÁO CÁO.

Module này THUẦN: không SQL, không Flask, không đọc file. Nó nhận các dòng
hàng ĐANG ĐƯỢC BÁO CÁO cùng đơn vị báo cáo của từng dòng, rồi làm đúng hai
việc: phân hoạch rồi cộng, và chia một con số đã có cho một con số đã có.

## Câu hỏi nghiệp vụ mà nó trả lời

    "Doanh thu của kỳ này đến từ những đơn vị báo cáo nào, và mỗi đơn vị
     chiếm bao nhiêu phần trăm?"

Đây là hình dạng của khối tháng trong sổ cũ — `docs/tasks/TASK-PRA-000-
persistent-reporting-analytics-plan.md` §C.1 đo được: mỗi khối tháng của
`Summary 2026` gồm *"5–7 dòng người bán/kênh + 1 dòng tổng tháng"*. Reports
hôm nay có đủ số cho từng đơn vị, nhưng chỉ xem được MỖI LẦN MỘT đơn vị qua
hàng tab của không gian làm việc Nhân viên. Cùng §C.4 ghi nhận chính khiếm
khuyết đó ở sổ cũ (*"Ẩn/hiện sheet là cơ chế điều hướng duy nhất"*).

## Vì sao ĐƠN VỊ BÁO CÁO chứ không phải từng nhân viên

`DEC-PHB02-08` đã freeze rằng đơn vị báo cáo KHÁC con người:

    EMPLOYEE   Vinh · Quý · Hiệp        ai bán dòng này
    SHEET      Nội thành · Gia dụng     báo cáo cộng dòng này vào đâu

Nội thành có Target của RIÊNG nó (`group_target`), và sổ cũ cũng để Nội thành
làm MỘT dòng. Một bảng cơ cấu tách Nội thành thành ba người sẽ nói về một cơ
cấu mà Owner không điều hành theo. Quan trọng hơn: đặt cả dòng "Nội thành"
LẪN ba dòng "Vinh/Quý/Hiệp" vào cùng một bảng là ĐẾM HAI LẦN cùng một số
tiền. Module này chỉ biết MỘT phân hoạch, nên lỗi đó không có chỗ để xảy ra.

Phân hoạch được lấy nguyên vẹn từ `reporting_sheets.sheet_key_of` — hàm TOÀN
PHẦN đã nghiệm thu của không gian làm việc. Không có phép phân loại thứ hai ở
đây: một dòng thuộc đơn vị nào là câu hỏi đã có người trả lời, và câu trả lời
đó chỉ có một chỗ.

## Tỉ trọng KHÔNG phải một công thức nghiệp vụ mới

`share_percent` chia DOANH THU của một đơn vị cho DOANH THU của cả kỳ — hai
con số đã do `business_metrics.totals` tính xong. Nó không đọc giá bán, số
lượng, chiết khấu, giá nhập hay tỉ lệ quy đổi, nên nó không thể ra một con số
doanh thu/lợi nhuận nào khác với con số chính thức. Chỉ tiêu này đã được phân
loại sẵn trong kế hoạch phân tích đã freeze — `TASK-PRA-000` §L, dòng
*"Employee contribution (share) | **NOW** | doanh thu NV / tổng"*.

Tỉ trọng CHỈ tính trên doanh thu bán hàng. KHÔNG có tỉ trọng lợi nhuận: mẫu
số của một tỉ suất lợi nhuận là câu hỏi `D1`/`N.7` mà `PHB-02` mục 11 vẫn
đang DEFER, và không phiên nào được tự chọn giúp Owner.

## Phân hoạch, không phải bộ lọc

`group_by_unit` là một PHÂN HOẠCH của đúng tập dòng được truyền vào: mỗi dòng
thuộc đúng MỘT đơn vị, không dòng nào rơi ra ngoài, không dòng nào có mặt hai
chỗ. Đó là lý do mọi chỉ tiêu cộng được cộng lại đúng bằng tổng kỳ — và phép
đối soát dưới đây biến tính chất ấy thành một phép so CHẠY THẬT.

Phép đối soát KHÔNG được viết lại ở đây: nó dùng nguyên
`brand_metrics.reconciliation`, vốn chỉ đọc `item[1]` của từng cặp nên đúng
cho MỌI phân hoạch của cùng một `BusinessTotals`. Viết một bản thứ hai sẽ là
hai định nghĩa "đối soát" cho cùng một mệnh đề, và ngày chúng lệch nhau sẽ
không ai biết bản nào đúng.

Cột `Đơn` là ngoại lệ đã biết và phải NÓI RA: một BH có một dòng Gia dụng và
một dòng không phải Gia dụng được đếm ở cả hai đơn vị. Đây cùng sự thật
`R-E5` mà bảng nhân viên và bảng thương hiệu đã phải nói ra, chỉ đổi chiều
gộp — không phải một lỗi.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Sequence

from app.modules.reporting import reporting_sheets
from app.modules.reporting.brand_metrics import reconciliation
from app.modules.reporting.business_metrics import (
    BusinessLine, BusinessTotals, totals,
)

# --- Ba loại đơn vị báo cáo ----------------------------------------------

KIND_GROUP = "GROUP"
"""Đơn vị NHÓM — Nội thành hoặc Gia dụng. Chủ thể là một kênh, không một người."""

KIND_EMPLOYEE = "EMPLOYEE"
"""Đơn vị của MỘT nhân viên bán lẻ (người có sheet riêng)."""

KIND_UNRESOLVED = "UNRESOLVED"
"""Các dòng chưa biết của ai (`R-E4`). Không bao giờ bị bỏ khỏi bảng."""

#: Hai chữ số thập phân, cùng quy ước làm tròn của mọi phần trăm đã có trong
#: `business_metrics` (coverage, So tháng trước, So Target).
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class ReportingUnit:
    """Một DÒNG của bảng cơ cấu.

    `key` là khoá phân hoạch (đúng khoá sheet của `reporting_sheets`), `label`
    là chữ hiện trên bảng, `kind` là loại đơn vị. Ba trường đi cùng nhau trong
    một value object để không có đường nào render một dòng "chưa xác định" mà
    rơi mất chiều "vì sao chưa xác định".
    """

    key: str
    label: str
    kind: str

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("ReportingUnit.key REQUIRED, không được rỗng")
        if not self.label:
            raise ValueError("ReportingUnit.label REQUIRED, không được rỗng")
        if self.kind not in (KIND_GROUP, KIND_EMPLOYEE, KIND_UNRESOLVED):
            raise ValueError(f"kind ngoài tập đóng: {self.kind!r}")

    @property
    def resolved(self) -> bool:
        """Đã biết dòng tiền này thuộc đơn vị báo cáo nào chưa?"""
        return self.kind != KIND_UNRESOLVED


def unit_for(sheet_key: str, employee: Optional[str]) -> ReportingUnit:
    """Đơn vị báo cáo ứng với `(khoá sheet, tên nhân viên)` của MỘT dòng.

    Đầu vào là đúng cặp mà `business_service.PeriodData.sheet_assignments()`
    đã dựng cho hàng tab của không gian làm việc, nên bảng cơ cấu và hàng tab
    KHÔNG THỂ nói hai câu khác nhau về việc một dòng thuộc về đâu.

    Nhãn của đơn vị nhân viên là chính tên đã chuẩn hoá — cùng cái tên mà
    `reporting_sheets.sheets_for` đặt lên tab của người đó. Không có phép
    "làm đẹp" tên nào ở đây: hai chỗ hiển thị cùng một người phải hiện cùng
    một chuỗi, nếu không Owner sẽ đọc thành hai người.
    """
    if sheet_key in reporting_sheets.GROUP_SHEETS:
        return ReportingUnit(key=sheet_key,
                             label=reporting_sheets.SHEET_LABELS[sheet_key],
                             kind=KIND_GROUP)
    if sheet_key == reporting_sheets.UNRESOLVED_SHEET:
        return ReportingUnit(key=sheet_key,
                             label=reporting_sheets.SHEET_LABELS[sheet_key],
                             kind=KIND_UNRESOLVED)
    if not employee:
        raise ValueError(
            f"khoá sheet nhân viên {sheet_key!r} mà không có tên — dòng chưa "
            "biết của ai phải mang khoá "
            f"{reporting_sheets.UNRESOLVED_SHEET!r}")
    return ReportingUnit(key=sheet_key, label=employee, kind=KIND_EMPLOYEE)


# --- Phân hoạch -----------------------------------------------------------

def group_by_unit(
    lines: Sequence[BusinessLine], units: Sequence[ReportingUnit],
) -> list[tuple[ReportingUnit, BusinessTotals]]:
    """Phân hoạch `lines` theo `units` (hai dãy ĐI SONG SONG).

    Sắp doanh thu giảm dần; đơn vị "chưa xác định nhân viên" LUÔN ở cuối. Sắp
    theo doanh thu chỉ là TRÌNH BÀY: không dòng nào được dán nhãn `top`,
    `best` hay `kém` — mọi nhãn kiểu đó cần một công thức và một quyết định
    Owner chưa tồn tại (`TASK-PRA-005` §17).

    Độ dài lệch nhau là LỖI CỨNG, không phải một lần `zip` cắt ngắn im lặng:
    cắt ngắn nghĩa là một số dòng biến mất khỏi mọi đơn vị trong khi bảng vẫn
    trông hợp lệ — đúng lớp lỗi mà phép đối soát được dựng để bắt, nên nó
    không được phép xảy ra ở tầng dưới nó.
    """
    if len(lines) != len(units):
        raise ValueError(
            f"lines ({len(lines)}) và units ({len(units)}) phải cùng độ dài — "
            "mỗi dòng đúng một đơn vị, không dòng nào rơi ra ngoài")
    grouped: dict[str, tuple[ReportingUnit, list[BusinessLine]]] = {}
    for line, unit in zip(lines, units):
        _, members = grouped.setdefault(unit.key, (unit, []))
        members.append(line)
    rows = [(unit, totals(members)) for unit, members in grouped.values()]
    rows.sort(key=lambda item: (
        0 if item[0].resolved else 1,
        -(item[1].sales_revenue or Decimal(0)),
        item[0].key,
    ))
    return rows


# --- Tỉ trọng -------------------------------------------------------------

def share_percent(
    part: Optional[Decimal], whole: Optional[Decimal],
) -> Optional[Decimal]:
    """Phần trăm mà `part` chiếm trong `whole` — `None` khi không nói được.

    Ba nhánh trả `None`, và cả ba đều là "chưa có câu trả lời" chứ không phải
    "bằng không": chưa có doanh thu nào ở tử số, chưa có doanh thu nào ở mẫu
    số, và mẫu số bằng 0 (chia cho 0 không có nghĩa, và một `0 %` in ra ở đó
    sẽ đọc thành "đơn vị này không đóng góp gì").

    Giá trị ÂM được giữ nguyên, không bị kẹp về 0: một kỳ mà chiết khấu lớn
    hơn doanh số của một đơn vị là một sự thật kế toán, và giấu nó đi là nói
    dối về chính con số đang nằm trong tổng.
    """
    if part is None or whole is None or whole == 0:
        return None
    return (Decimal(part) / Decimal(whole) * Decimal(100)).quantize(
        _CENT, rounding=ROUND_HALF_UP)


__all__ = [
    "KIND_EMPLOYEE", "KIND_GROUP", "KIND_UNRESOLVED", "ReportingUnit",
    "group_by_unit", "reconciliation", "share_percent", "unit_for",
]
