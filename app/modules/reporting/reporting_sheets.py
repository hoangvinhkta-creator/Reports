"""`DEC-PHB02-08` — các SHEET của không gian làm việc Nhân viên.

Module này THUẦN: không SQL, không Flask, không I/O, không đọc file cấu hình.
Nó trả lời đúng ba câu hỏi, và mỗi câu là một mệnh đề nghiệp vụ kiểm được
bằng một test đơn vị trên giá trị thuần:

    1. Có những sheet nào trong kỳ này?          `sheets_for`
    2. Dòng hàng này thuộc sheet nào?            `sheet_key_of`
    3. Tháng đang xem đã trôi qua bao nhiêu?     `month_progress_percent`

## Sheet là ĐƠN VỊ BÁO CÁO, không phải con người

Đây là điểm dễ hỏng nhất của toàn bộ thay đổi, nên nó được nói ra ở đây một
lần và được cấu trúc bảo vệ ở mọi nơi khác.

`config/employees.yaml` đã ghi rõ vì sao Vinh · Quý · Hiệp KHÔNG được gộp
thành một "Employee" tên "Nội thành": cách đó làm MẤT danh tính của ba con
người có thật (DEC-127 §1). Quyết định mới của Owner không đảo lại điều đó —
nó thêm một tầng KHÁC:

    EMPLOYEE   Vinh · Quý · Hiệp        ai bán dòng này (giữ nguyên, luôn hiện)
    SHEET      Nội thành · Gia dụng     báo cáo cộng dòng này vào đâu

Một dòng của Vinh nằm trên sheet "Nội thành" và cột Nhân viên của nó VẪN ghi
"Vinh". Không có chỗ nào trong module này ghi đè `line.employee`.

## Gia dụng là một BUCKET, không phải một nhân viên

`GIA_DUNG` đã là một `ProductGroup` từ ADR-106 — thuộc tính của DÒNG HÀNG.
Sheet Gia dụng vì thế không phát minh ra khái niệm mới: nó chỉ là "tập các
dòng có ProductGroup hiệu lực = GIA_DUNG", và tỉ lệ quy đổi 8 % của chúng vẫn
do `config/conversion_rates.yaml` quyết định, không do file này.

## Vì sao điều kiện nhóm `NOI_THANH` xuất hiện ở `sheet_key_of`

Cùng lý do mà `conversion_rates.yaml` khoá dòng `GIA_DUNG_8` trên
`employee_group: NOI_THANH`: một dòng hàng gia dụng do nhân viên bán lẻ bán
vẫn quy đổi 5,5 %, nên nó cũng không được rơi vào sheet Gia dụng — nếu không,
sheet đó sẽ trộn hai tỉ lệ và "DS quy đổi của Gia dụng" thành một con số
không tương ứng với chính sách nào.

Hệ quả thực tế: sau khi Owner gán lại một dòng Gia dụng từ Vinh sang Ly, dòng
đó rời sheet Gia dụng và về sheet của Ly — đúng như tỉ lệ của nó cũng đổi.
Bucket và tỉ lệ không bao giờ nói hai câu khác nhau.

## Phân hoạch, không phải bộ lọc

`sheet_key_of` là một HÀM TOÀN PHẦN: mọi dòng của kỳ đều nhận đúng MỘT khoá
sheet, kể cả dòng chưa biết ai bán (`UNRESOLVED_SHEET`). Đó là điều làm cho
bất biến `§42` đúng theo cấu tạo chứ theo lời hứa:

    Σ(chỉ tiêu cộng được của mọi sheet)  ==  chỉ tiêu của cả kỳ

và cũng là lý do một dòng KHÔNG BAO GIỜ nằm ở hai bucket (`§11.3`).
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.modules.reporting.rate_routing import GIA_DUNG, GIA_DUNG_ELIGIBLE_GROUP

#: Sheet NHÓM — chủ thể của nó là một ĐƠN VỊ BÁO CÁO, không phải một người.
NOI_THANH_SHEET = "noi-thanh"
GIA_DUNG_SHEET = "gia-dung"
GROUP_SHEETS = (NOI_THANH_SHEET, GIA_DUNG_SHEET)

#: Sheet của các dòng chưa biết của ai. Nó tồn tại để phân hoạch KHÉP KÍN —
#: một dòng vô chủ vẫn phải nhìn thấy được, đúng `R-E4`.
UNRESOLVED_SHEET = "chua-xac-dinh"

#: Khoá NHÓM dùng cho `group_target` (`§43`). Cố ý KHÁC khoá sheet ở trên:
#: khoá sheet là một đoạn URL, khoá nhóm là một giá trị nằm trong database và
#: phải đọc được bằng mắt khi ai đó mở bảng ra xem.
GROUP_TARGET_KEYS = {
    NOI_THANH_SHEET: "NOI_THANH",
    GIA_DUNG_SHEET: "GIA_DUNG",
}

SHEET_LABELS = {
    NOI_THANH_SHEET: "Nội thành",
    GIA_DUNG_SHEET: "Gia dụng",
    UNRESOLVED_SHEET: "Chưa xác định nhân viên",
}

#: Thứ tự cố định của hai sheet nhóm, đứng TRƯỚC các sheet nhân viên. Không
#: sắp theo doanh thu: một thanh tab đổi thứ tự giữa hai lần tải trang buộc
#: Owner phải đọc lại toàn bộ để tìm chỗ mình vừa bấm.
_GROUP_ORDER = {NOI_THANH_SHEET: 0, GIA_DUNG_SHEET: 1}


@dataclass(frozen=True)
class Sheet:
    """Một tab của không gian làm việc.

    `employee` chỉ có giá trị với sheet của MỘT nhân viên; hai sheet nhóm và
    sheet "chưa xác định" để `None`. Đó là chỗ duy nhất trong toàn bộ mã nguồn
    phân biệt "sheet này có một chủ thể là người" với "sheet này là một nhóm",
    và mọi câu hỏi khác về nó (Target đọc bảng nào, có nút Gia dụng không) đều
    dẫn xuất từ đây thay vì so chuỗi ở từng chỗ.
    """

    key: str
    label: str
    #: Tên nhân viên khi sheet là của một người. `None` với sheet nhóm.
    employee: Optional[str] = None
    #: `True` khi sheet là nhóm "chưa xác định nhân viên" (`employee is None`
    #: cũng đúng với sheet nhóm, nên hai thứ này không thay nhau được).
    unresolved: bool = False

    @property
    def is_group(self) -> bool:
        return self.key in GROUP_SHEETS

    @property
    def group_key(self) -> Optional[str]:
        """Khoá `group_target` của sheet, hoặc `None` nếu nó không phải nhóm."""
        return GROUP_TARGET_KEYS.get(self.key)

    @property
    def accepts_gia_dung_classification(self) -> bool:
        """`§9` — CHỈ sheet Nội thành nhận thao tác phân loại Gia dụng.

        Sheet Gia dụng không nhận nó (dòng đã ở đó rồi), và sheet của nhân
        viên bán lẻ không nhận nó vì `conversion_rates.yaml` không định tuyến
        họ qua 8 % — một nút bấm không có tác dụng kinh tế nào là một nút bấm
        nói dối.
        """
        return self.key == NOI_THANH_SHEET


def employee_sheet_key(employee: Optional[str]) -> str:
    """Khoá sheet của MỘT nhân viên — ổn định qua các lần tải trang.

    Dùng chính tên đã chuẩn hoá làm khoá thay vì một slug bỏ dấu: khoá này đi
    vào URL và đi ngược lại thành một tra cứu, nên một phép biến đổi mất thông
    tin (bỏ dấu) sẽ làm hai nhân viên khác nhau đụng nhau. Flask/Werkzeug tự
    lo phần mã hoá URL.
    """
    return UNRESOLVED_SHEET if not employee else f"nv:{employee}"


def sheet_key_of(
    *, employee: Optional[str], employee_group: Optional[str],
    product_group: Optional[str],
) -> str:
    """Sheet mà MỘT dòng hàng được cộng vào. Hàm TOÀN PHẦN.

    `product_group` là phân loại HIỆU LỰC của dòng (`business_queries.
    effective_product_group`) — tức là đã tính cả quyết định cấp dòng lẫn
    quyết định cấp mặt hàng của Owner.

    Thứ tự ba nhánh là thứ tự THẨM QUYỀN và nó không đảo được:

    1. Gia dụng + nhóm Nội thành ⟹ sheet Gia dụng. Đây là câu Owner vừa nói.
    2. Nhóm Nội thành (còn lại)  ⟹ sheet Nội thành.
    3. Còn lại ⟹ sheet của chính nhân viên đó, hoặc "chưa xác định".

    Nhánh 1 hỏi CẢ HAI điều kiện, không chỉ `product_group`: xem docstring của
    module — bucket và tỉ lệ quy đổi phải luôn nói cùng một câu.
    """
    if employee_group == GIA_DUNG_ELIGIBLE_GROUP:
        if product_group == GIA_DUNG:
            return GIA_DUNG_SHEET
        return NOI_THANH_SHEET
    return employee_sheet_key(employee)


def sheets_for(
    assignments: list[tuple[str, Optional[str]]],
) -> list[Sheet]:
    """Các sheet cần hiện, từ `(khoá sheet, tên nhân viên)` của từng dòng.

    Hai sheet nhóm LUÔN có mặt kể cả khi kỳ chưa có dòng nào của chúng
    (`§5`/`§46`): Owner cần mở sheet Nội thành của tháng hiện tại để đặt
    Target TRƯỚC khi bán được đồng nào, và một tab biến mất đúng lúc chưa có
    số là một tab không dùng được vào việc đó.

    Sheet của một nhân viên thì ngược lại — nó chỉ xuất hiện khi người đó có
    dòng trong kỳ. Dựng sẵn một tab cho mọi người trong master sẽ cho ra một
    thanh tab đầy những trang toàn số 0, tức là đúng thứ `R-E1` đã bác bỏ.

    Không sinh tab trùng: `assignments` có bao nhiêu dòng cũng chỉ cho ra một
    tab cho mỗi khoá (`§5`).
    """
    employees: dict[str, Optional[str]] = {}
    has_unresolved = False
    for key, employee in assignments:
        if key in GROUP_SHEETS:
            continue
        if key == UNRESOLVED_SHEET:
            has_unresolved = True
            continue
        employees.setdefault(key, employee)

    sheets = [
        Sheet(key=key, label=SHEET_LABELS[key])
        for key in sorted(GROUP_SHEETS, key=_GROUP_ORDER.__getitem__)
    ]
    sheets += [
        Sheet(key=key, label=employees[key] or "", employee=employees[key])
        for key in sorted(employees, key=lambda item: employees[item] or "")
    ]
    if has_unresolved:
        sheets.append(Sheet(key=UNRESOLVED_SHEET,
                            label=SHEET_LABELS[UNRESOLVED_SHEET],
                            unresolved=True))
    return sheets


def find_sheet(sheets: list[Sheet], key: Optional[str]) -> Optional[Sheet]:
    """Sheet mang đúng khoá này, hoặc `None`. Không đoán gần đúng."""
    for sheet in sheets:
        if sheet.key == key:
            return sheet
    return None


_CENT = Decimal("0.01")


def month_progress_percent(
    period: tuple[int, int], *, today: date
) -> Decimal:
    """`§15` — THÁNG đang xem đã trôi qua bao nhiêu phần trăm.

    Đây là một chỉ báo THỜI GIAN và không có đường nào từ nó tới một con số
    nghiệp vụ: nó không xuất hiện trong `business_metrics`, không tham gia
    Target, KPI hay DS quy đổi. Nó trả lời đúng một câu Owner hỏi khi nhìn một
    con số "So target 40 %": *40 % của tháng, hay 40 % ở ngày cuối tháng?*

    Quy tắc lịch, cố ý xác định và không phụ thuộc múi giờ hay giờ trong ngày:

        tháng đã qua      ⟹ 100
        tháng chưa tới    ⟹ 0
        tháng hiện tại    ⟹ số ngày ĐÃ TRÔI QUA / số ngày của tháng × 100

    "Đã trôi qua" TÍNH CẢ ngày hôm nay (`§15`: ngày 3 của tháng 30 ngày = 10
    %). Ngày hôm nay là một ngày bán hàng đang diễn ra, không phải một ngày
    chưa bắt đầu.
    """
    year, month = period
    current = (today.year, today.month)
    if (year, month) < current:
        return Decimal(100)
    if (year, month) > current:
        return Decimal(0)
    days_in_month = calendar.monthrange(year, month)[1]
    return (Decimal(today.day) / Decimal(days_in_month)
            * Decimal(100)).quantize(_CENT, rounding=ROUND_HALF_UP)


__all__ = [
    "GIA_DUNG_SHEET", "GROUP_SHEETS", "GROUP_TARGET_KEYS", "NOI_THANH_SHEET",
    "SHEET_LABELS", "Sheet", "UNRESOLVED_SHEET", "employee_sheet_key",
    "find_sheet", "month_progress_percent", "sheet_key_of", "sheets_for",
]
