"""R6 §1 — HỢP ĐỒNG PHẠM VI của mọi màn hình phân tích kinh doanh.

Một màn hình phân tích chọn ĐÚNG MỘT phạm vi thời gian, và module này là chỗ
duy nhất quy tắc ấy được viết ra. Nó THUẦN: không Flask, không SQL, không đọc
file — đầu vào là hai chuỗi người dùng gõ, đầu ra là một value object.

## Vì sao phải có một hợp đồng thay vì hai tham số rời

Trước R6 mọi trang nghiệp vụ nhận phạm vi bằng đúng một tham số `ky`
(`server._workspace_period`). R6 thêm phạm vi `Từ ngày`–`Đến ngày`, và ngay
lúc có HAI cách nói về thời gian thì xuất hiện một lớp lỗi mới: một trang đọc
`ky` cho bảng tổng và đọc `tu-ngay`/`den-ngay` cho biểu đồ sẽ hiện hai con số
của hai khoảng thời gian KHÁC NHAU cạnh nhau, và không ô nào trên màn hình
nói ra điều đó.

Vì thế `resolve()` trả về MỘT `AnalysisRange` duy nhất, mang sẵn cả cận ngày
lẫn nhãn để hiển thị. Một trang gọi nó một lần rồi dùng đúng kết quả đó cho
mọi khối — không có đường nào để hai khối cùng trang chọn hai phạm vi.

## Không kết hợp hai phạm vi

`AnalysisRange.kind` là một trong hai giá trị, không bao giờ là cả hai và
không bao giờ là một phép GIAO của hai. Giao hai phạm vi (lấy phần chung của
tháng đang chọn và khoảng ngày vừa gõ) là cách im lặng nhất để một trang trả
về ít tiền hơn cả hai phạm vi mà người dùng nghĩ mình đã chọn.

Khi cả hai được gửi lên, khoảng ngày HỢP LỆ thắng — nó cụ thể hơn, và người
dùng vừa gõ nó. Một khoảng ngày KHÔNG hợp lệ (thiếu một đầu, sai định dạng,
`Từ ngày` sau `Đến ngày`) KHÔNG âm thầm trở thành một phạm vi khác: nó bị từ
chối kèm LÝ DO, và trang rơi về phạm vi kỳ. `note` mang lý do đó lên màn hình
thay vì để người dùng tưởng khoảng ngày của họ đã được áp dụng.

## Chốt kỳ chỉ có nghĩa với MỘT THÁNG

`AnalysisRange.period` chỉ có giá trị ở phạm vi `PERIOD`, và đó là trường duy
nhất được truyền vào `BusinessReportService.period(period=...)`. Ở phạm vi
`CUSTOM` nó là `None`, nên `PeriodData.closed` là `None` và không màn hình nào
tuyên bố một khoảng ngày tự chọn "đã chốt".

Đây KHÔNG phải một cơ chế chốt kỳ thứ hai và cũng không nới lỏng cơ chế cũ:
`period_lock` vẫn khoá theo `(năm, tháng)` như R3 đã freeze, và mọi đường GHI
quyết định vẫn đi qua `guard_period_open` với một tháng thật. R6 chỉ ĐỌC, nên
một phạm vi không phải tháng đơn giản là không có gì để hỏi về trạng thái
chốt — và nói `None` ở đó đúng hơn là mượn trạng thái chốt của tháng chứa
ngày đầu khoảng.
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from typing import Optional

#: Hai phạm vi, và chỉ hai. Tập ĐÓNG.
SCOPE_PERIOD = "PERIOD"
SCOPE_CUSTOM = "CUSTOM"
SCOPES: tuple[str, ...] = (SCOPE_PERIOD, SCOPE_CUSTOM)

#: Ranh giới năm có nghĩa — cùng khoảng mà `server._workspace_period` đã dùng,
#: viết lại ở tầng thuần để quy tắc kiểm được mà không cần dựng một request.
MIN_YEAR = 2000
MAX_YEAR = 2100

NOTE_INCOMPLETE = (
    "Khoảng ngày tự chọn cần ĐỦ hai đầu Từ ngày và Đến ngày. Chỉ một đầu thì "
    "hệ thống không biết đầu còn lại là ngày nào, nên phạm vi đang hiển thị "
    "vẫn là kỳ được chọn ở trên — không phải khoảng ngày vừa gõ."
)

NOTE_UNREADABLE = (
    "Khoảng ngày tự chọn không đọc được (định dạng phải là NĂM-THÁNG-NGÀY, ví "
    "dụ 2026-09-01). Phạm vi đang hiển thị vẫn là kỳ được chọn ở trên."
)

NOTE_REVERSED = (
    "Từ ngày nằm SAU Đến ngày. Hệ thống KHÔNG tự đảo hai đầu — một khoảng đảo "
    "ngược thường là gõ nhầm, và tự sửa nó sẽ cho ra một bộ số mà người gõ "
    "không yêu cầu. Phạm vi đang hiển thị vẫn là kỳ được chọn ở trên."
)

SCOPE_NOTE = (
    "Mỗi màn hình phân tích áp dụng ĐÚNG MỘT phạm vi thời gian cho mọi ô số, "
    "mọi bảng và mọi biểu đồ trên trang. Chọn một kỳ có sẵn HOẶC gõ một khoảng "
    "ngày — hai phạm vi không bao giờ được cộng gộp hay lấy phần chung."
)


def parse_iso_date(raw: Optional[str]) -> Optional[date]:
    """`YYYY-MM-DD` → `date`, hoặc `None` khi rỗng/không đọc được.

    KHÔNG chấp nhận một định dạng thứ hai. Nhận thêm `dd/mm/yyyy` ở đây sẽ
    làm `01/02/2026` mơ hồ giữa hai nền văn hoá ngày tháng, và một phạm vi
    lệch một tháng là một bộ số sai mà không ô nào trên trang cảnh báo.
    """
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """`(ngày đầu tháng, ngày cuối tháng)` — cận trên BAO GỒM.

    Cùng quy ước với `analytics_queries.month_bounds` và
    `business_service._month_bounds`. Viết ở đây để tầng thuần không phải
    import tầng truy vấn chỉ vì hai phép cộng ngày; giá trị trả về được
    `tests/test_r6_analysis_range.py` canh là khớp từng ngày với hai hàm kia.
    """
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def _valid_period(year: int, month: int) -> bool:
    return 1 <= month <= 12 and MIN_YEAR <= year <= MAX_YEAR


def parse_period(raw: Optional[str]) -> Optional[tuple[int, int]]:
    """`YYYY-MM` → `(năm, tháng)`, hoặc `None`.

    Cùng cách đọc mà `server._workspace_period` đã dùng cho tham số `ky`, nên
    mọi đường dẫn và bookmark cũ mở đúng phạm vi cũ.
    """
    year_text, _, month_text = (raw or "").partition("-")
    try:
        year, month = int(year_text), int(month_text)
    except ValueError:
        return None
    return (year, month) if _valid_period(year, month) else None


@dataclass(frozen=True)
class AnalysisRange:
    """Phạm vi thời gian HIỆU LỰC của MỘT màn hình phân tích.

    `kind` là một trong `SCOPES`. Mọi trường còn lại đọc theo nó:

    ```text
    PERIOD   period = (năm, tháng)   date_from/date_to = hai cận của tháng đó
    CUSTOM   period = None           date_from/date_to = hai cận người dùng gõ
    ```

    `period is None` ở phạm vi `CUSTOM` là một BẢO ĐẢM, không phải một chỗ
    trống chưa điền: nó là thứ giữ cho không màn hình nào truyền một tháng bịa
    vào `BusinessReportService.period(period=...)` và mượn trạng thái chốt kỳ
    của tháng đó cho một khoảng ngày tự chọn.
    """

    kind: str
    date_from: date
    date_to: date
    label: str
    period: Optional[tuple[int, int]] = None
    #: Lý do một khoảng ngày được gửi lên đã BỊ TỪ CHỐI. `None` = không có gì
    #: phải nói. Trang hiển thị nguyên văn — im lặng ở đây nghĩa là người dùng
    #: tưởng khoảng ngày của họ đang được áp dụng.
    note: Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind not in SCOPES:
            raise ValueError(f"kind ngoài tập đóng: {self.kind!r}")
        if self.date_from > self.date_to:
            raise ValueError(
                "AnalysisRange không được mang một khoảng đảo ngược — "
                "`resolve()` từ chối nó trước khi dựng object")
        if self.kind == SCOPE_CUSTOM and self.period is not None:
            raise ValueError(
                "phạm vi CUSTOM KHÔNG mang `period`: một khoảng ngày tự chọn "
                "không có trạng thái chốt kỳ để mượn")
        if self.kind == SCOPE_PERIOD and self.period is None:
            raise ValueError("phạm vi PERIOD phải nói ra `period` của nó")

    @property
    def is_custom(self) -> bool:
        return self.kind == SCOPE_CUSTOM

    @property
    def days(self) -> int:
        """Số ngày LỊCH mà phạm vi bao trùm, cận trên bao gồm."""
        return (self.date_to - self.date_from).days + 1

    @property
    def period_value(self) -> str:
        """Giá trị cho bộ chọn kỳ (`YYYY-MM`), hoặc chuỗi rỗng ở phạm vi
        `CUSTOM` — bộ chọn khi ấy KHÔNG được sáng lên ở một tháng nào, vì
        không tháng nào là phạm vi đang xem."""
        if self.period is None:
            return ""
        return f"{self.period[0]}-{self.period[1]:02d}"


def period_range(period: tuple[int, int]) -> AnalysisRange:
    """`AnalysisRange` của MỘT tháng."""
    year, month = period
    if not _valid_period(year, month):
        raise ValueError(f"kỳ không có nghĩa: {period!r}")
    low, high = month_bounds(year, month)
    return AnalysisRange(kind=SCOPE_PERIOD, date_from=low, date_to=high,
                         label=f"{month:02d}/{year}", period=(year, month))


def custom_range(date_from: date, date_to: date,
                 note: Optional[str] = None) -> AnalysisRange:
    """`AnalysisRange` của một khoảng ngày tự chọn."""
    return AnalysisRange(
        kind=SCOPE_CUSTOM, date_from=date_from, date_to=date_to,
        label=f"{date_from.day:02d}/{date_from.month:02d}/{date_from.year}"
              f" – {date_to.day:02d}/{date_to.month:02d}/{date_to.year}",
        period=None, note=note)


def resolve(
    *, period_raw: Optional[str], from_raw: Optional[str],
    to_raw: Optional[str], fallback_period: tuple[int, int],
) -> AnalysisRange:
    """Phạm vi HIỆU LỰC của một lần tải trang — ĐÚNG MỘT phạm vi.

    Thứ tự quyết định là hợp đồng:

    1. Hai đầu ngày ĐỀU đọc được và không đảo ngược ⟹ phạm vi `CUSTOM`.
    2. Có gõ ngày nhưng không dùng được ⟹ phạm vi `PERIOD`, kèm `note` nói rõ
       khoảng ngày đã bị từ chối vì sao.
    3. Không gõ ngày ⟹ phạm vi `PERIOD` của `ky`, hoặc `fallback_period` khi
       `ky` vắng/không hợp lệ.

    `fallback_period` KHÔNG có giá trị mặc định: nó là quyết định của tầng
    gọi (tháng dương lịch hiện tại ở các trang không gian làm việc), và một
    mặc định ẩn ở đây sẽ đặt quyết định đó vào sai chỗ.
    """
    typed_from = (from_raw or "").strip()
    typed_to = (to_raw or "").strip()
    low, high = parse_iso_date(from_raw), parse_iso_date(to_raw)

    note: Optional[str] = None
    if low is not None and high is not None:
        if low <= high:
            return custom_range(low, high)
        note = NOTE_REVERSED
    elif typed_from or typed_to:
        # Có gõ, nhưng không thành một khoảng. Hai lý do khác nhau và người
        # dùng sửa chúng bằng hai hành động khác nhau, nên chúng không dùng
        # chung một câu.
        both_typed = bool(typed_from) and bool(typed_to)
        note = NOTE_UNREADABLE if both_typed else NOTE_INCOMPLETE

    period = parse_period(period_raw) or fallback_period
    resolved = period_range(period)
    return resolved if note is None else AnalysisRange(
        kind=resolved.kind, date_from=resolved.date_from,
        date_to=resolved.date_to, label=resolved.label,
        period=resolved.period, note=note)


__all__ = [
    "AnalysisRange", "MAX_YEAR", "MIN_YEAR", "NOTE_INCOMPLETE",
    "NOTE_REVERSED", "NOTE_UNREADABLE", "SCOPES", "SCOPE_CUSTOM",
    "SCOPE_NOTE", "SCOPE_PERIOD", "custom_range", "month_bounds",
    "parse_iso_date", "parse_period", "period_range", "resolve",
]
