"""`DEC-185` — MỘT dải doanh thu theo thời gian cho trang Báo cáo.

Module này THUẦN: không SQL, không Flask, không đọc file. Nó nhận các dòng đã
hợp nhất quyết định của Owner (`PeriodData.details`) cùng bằng chứng lịch sử
đã đọc sẵn, rồi trả về một chuỗi điểm để vẽ. Mọi mệnh đề nghiệp vụ dưới đây
kiểm được bằng một test đơn vị trên giá trị thuần.

## Một biểu đồ, năm độ mịn — không phải năm biểu đồ

Owner yêu cầu ĐÚNG MỘT biểu đồ đổi mức gộp, không phải một biểu đồ cho mỗi
mức. Vì thế ở đây chỉ có MỘT hàm dựng chuỗi (`series`) và mức gộp là một
THAM SỐ của nó. Nếu mai này ai đó thêm "biểu đồ theo tuần" riêng, họ sẽ phải
thêm một hàm thứ hai — và điều đó nhìn thấy được trong diff.

## Doanh thu ở đây là DOANH THU CHÍNH THỨC, không phải tổng sổ thô

`§CHART-04`/`§CHART-09`. Chuỗi hiện tại cộng `line.total_sales` trên đúng tập
dòng mà `BusinessReportService.period` đã giữ lại — tức là ĐÃ trừ những dòng
Owner loại khỏi báo cáo (`DEC-PHB02-08` §30). Đây không phải một định nghĩa
doanh thu mới: nó là cùng phép cộng mà `business_metrics.totals` dùng cho ô
"Doanh thu bán hàng", chỉ tách theo mốc thời gian. Hệ quả kiểm được:

    Σ(mọi điểm của kỳ)  ==  totals.sales_revenue của chính kỳ đó

và nó đúng ở CẢ NĂM mức gộp, vì cả năm mức đều phân hoạch cùng một tập dòng.
Khi dòng thời gian có thêm các tháng chỉ còn bản ghi lịch sử, bất biến đó nói
về đúng phần SỔ NẠP; phần lịch sử cộng thêm vào tổng của biểu đồ, và điều đó
vẫn đúng ở cả năm mức gộp — xem `§ Thẩm quyền được giải ở mức THÁNG`.

Dòng KHÔNG có ngày bán không rơi vào bất kỳ điểm nào — đúng như chúng đã
không rơi vào bất kỳ kỳ nào (`R-S5`). Chúng được đếm riêng ở `undated`, chứ
không bị nhét vào một ngày nào đó cho đủ.

## Lịch sử và hiện tại là MỘT dòng thời gian, nhưng KHÔNG BAO GIỜ là một phép cộng

Đây là chỗ hai luật gặp nhau, nên nó được nói ra hết:

- Owner: *"Legacy History + Current should appear as one continuous business
  timeline"*, và KHÔNG được có bộ chọn nguồn hay nhãn Số cũ/Số mới — người
  đọc đang hỏi một câu về THỜI GIAN kinh doanh, không phải về hệ thống nào
  sinh ra con số.
- `DEC-166 E`: `LEGACY_REFERENCE` LUÔN phải phân biệt được với
  `PIPELINE_GENERATED`; `DEC-180` §9: MỘT kỳ ⟹ MỘT nguồn ⟹ MỘT giá trị.

Cách thoả cả hai, và là cách DUY NHẤT thoả được cả hai:

    một TRỤC thời gian · một chuỗi · KHÔNG bộ chọn nguồn
    nhưng MỖI THÁNG chỉ đến từ MỘT origin, không bao giờ từ hai cộng lại

Thẩm quyền được giải ở ĐÚNG độ mịn mà biểu đồ đang vẽ, không thô hơn:

    Tháng · Quý · Năm   một THÁNG đã có dòng pipeline thì lịch sử không chen
                        vào tháng đó — cùng thứ tự thẩm quyền mà
                        `_legacy_previous_month` đã dùng.
    Ngày · Tuần         một NGÀY đã có dòng pipeline thì lịch sử không chen
                        vào ngày đó; ngày không có thì lịch sử điền vào
                        (`DEC-211`, xem `_legacy_day_points`).

Giải ở độ mịn thô hơn mốc đang vẽ là đúng lớp lỗi mà `§ Thẩm quyền được giải
ở mức THÁNG` mô tả, chỉ đổi độ mịn: loại cả tháng 9 khỏi sổ cũ vì sổ nạp bắt
đầu từ 04/09 sẽ làm ba ngày đầu tháng — vốn CÓ bằng chứng — thành một lỗ trên
đường vẽ. Trong cả hai trường hợp, "MỘT kỳ ⟹ MỘT nguồn ⟹ MỘT giá trị" vẫn
đúng nguyên: không đơn vị thời gian nào nhận giá trị từ hai nguồn.

## Thẩm quyền được giải ở mức THÁNG, rồi mới gộp lên — không giải lại ở mức thô

Đây là bản sửa `F-C`, và nó cần nói rõ vì cái sai trước đó rất dễ đọc thành
đúng. Trước bản sửa, mốc Quý/Năm được dựng bằng cách để chuỗi hiện tại và
chuỗi lịch sử tự rơi vào cùng một khoá thô rồi cho chuỗi hiện tại thắng CẢ
KHOÁ đó. Với dữ liệu thật của Owner:

    2026-07 chỉ có sổ cũ   = 50tr
    2026-08 chỉ có sổ cũ   = 60tr
    2026-09 đã có sổ nạp   =  1tr

    Quý 3 = 1tr        ← Tháng 7 và Tháng 8 BỐC HƠI

Một quý mất 110 triệu vì hệ thống hỏi sai câu hỏi: nó hỏi "quý này thuộc
nguồn nào" trong khi thẩm quyền chỉ có nghĩa ở mức THÁNG. Trình tự đúng, và
là trình tự mà file này thi hành:

    1. giải thẩm quyền cho TỪNG THÁNG   (có sổ nạp ⟹ sổ nạp, ngược lại ⟹ sổ cũ)
    2. gộp các tháng ĐÃ GIẢI lên trên   (quý = tổng các tháng của nó, năm = tổng
                                         các tháng của nó)

    Quý 3 = 50 + 60 + 1 = 111tr

Phép cộng ở bước 2 KHÔNG phải phép cộng liên-origin bị cấm. Cái bị cấm là
cộng hai nguồn vào CÙNG MỘT THÁNG (Tháng 7 sổ cũ + Tháng 7 sổ nạp); cộng
Tháng 7 với Tháng 9 là điều mà mọi phép tính quý đều làm, và hai tháng đó
đến từ đâu không đổi được việc chúng là hai tháng khác nhau.

## Một quý gồm nhiều origin: nói ra, nhưng KHÔNG tách đôi giá trị

Hệ quả của bước 2 là một mốc thô có thể gồm cả tháng sổ cũ lẫn tháng sổ nạp.
Chiều `DEC-166 E` vẫn phải đọc được, nên có `ORIGIN_MIXED` — một giá trị
TRÌNH BÀY, dùng cho lời giải thích của đúng cột đó. Nó KHÔNG kéo theo một bộ
chọn nguồn, một chuỗi thứ hai, hay một nhãn Số cũ/Số mới: giá trị kinh doanh
vẫn là MỘT con số, vì quý đó thật sự chỉ có một con số.

## Không bịa điểm cho một độ mịn mà bằng chứng không đỡ nổi

`§CHART-10`. Sổ cũ lưu hai độ mịn khác nhau: `legacy_daily_sales` có TỪNG
NGÀY, còn nguồn chuẩn của một kỳ (`authoritative_period_sales`) chỉ có TỔNG
THÁNG. Nên:

    Ngày · Tuần    cần bằng chứng NGÀY. Tháng lịch sử chỉ có tổng tháng thì
                   KHÔNG góp điểm nào — không chia đều cho 30.
    Tháng          dùng tổng tháng.
    Quý · Năm      cộng các THÁNG có bằng chứng bên trong nó.

Chia một tổng tháng thành 30 ngày bằng nhau sẽ vẽ ra một đường phẳng trông
như một sự thật về hoạt động kinh doanh từng ngày — một sự thật chưa ai từng
đo. `covered_months` nói ra một quý/năm được dựng từ bao nhiêu tháng có bằng
chứng, để trang không im lặng về chỗ nó không biết.
"""

from __future__ import annotations

from dataclasses import dataclass
from calendar import isleap, monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional, Sequence

from app.modules.reporting import dashboard_metrics

#: Origin của một điểm. Cùng từ vựng `DEC-166 E`, không phải một cặp nhãn mới.
ORIGIN_CURRENT = "PIPELINE_GENERATED"
ORIGIN_LEGACY = "LEGACY_REFERENCE"

#: Mốc THÔ (quý/năm, hoặc một tuần vắt qua hai tháng) gồm các tháng đã giải
#: về HAI origin khác nhau. Chỉ xuất hiện từ mức gộp lớn hơn tháng trở lên —
#: một mốc THÁNG không bao giờ mang giá trị này, vì thẩm quyền được giải đúng
#: ở mức đó (`§ Thẩm quyền được giải ở mức THÁNG`).
ORIGIN_MIXED = "MIXED_AUTHORITY"

#: `DEC-216` — bằng chứng TỪNG NGÀY dựng riêng để lấp lỗ hổng của biểu đồ ở
#: mức Ngày/Tuần, KHÔNG phải một nguồn legacy (xem `app/web/chart_gapfill.py`).
#: Nó có nhãn riêng chứ không mượn `ORIGIN_LEGACY`: mượn nhãn sẽ nói với người
#: đọc rằng con số ấy đến từ sổ cũ đã chốt, trong khi sổ cũ không hề có ngày
#: nào — và làm hỏng đúng chiều mà `DEC-166 E` bắt phải luôn đọc được.
ORIGIN_GAPFILL = "CHART_GAPFILL"

DAY = "ngay"
WEEK = "tuan"
MONTH = "thang"
QUARTER = "quy"
YEAR = "nam"

#: Thứ tự cố định từ mịn tới thô. Đây là thứ tự các nút hiện trên màn hình,
#: và nó KHÔNG đổi theo dữ liệu — một hàng nút đổi chỗ giữa hai lần tải trang
#: buộc người đọc phải tìm lại chỗ mình vừa bấm.
GRANULARITIES: tuple[tuple[str, str], ...] = (
    (DAY, "Ngày"), (WEEK, "Tuần"), (MONTH, "Tháng"),
    (QUARTER, "Quý"), (YEAR, "Năm"),
)

GRANULARITY_KEYS: tuple[str, ...] = tuple(key for key, _ in GRANULARITIES)

DEFAULT_GRANULARITY = MONTH

#: Các mức gộp cần bằng chứng TỪNG NGÀY. Xem `§ Không bịa điểm` ở trên.
_DAY_LEVEL = frozenset({DAY, WEEK})

#: Số tháng trong một bucket, dùng để nói ra độ đầy đủ của quý/năm.
_MONTHS_IN_BUCKET = {MONTH: 1, QUARTER: 3, YEAR: 12}

CHART_NOTE = (
    "Doanh thu chính thức theo thời gian — đã trừ các dòng Owner loại khỏi "
    "báo cáo. Mỗi tháng chỉ lấy từ một nguồn có thẩm quyền; quý và năm có "
    "thể tổng hợp các tháng từ nhiều nguồn lịch sử/hiện tại."
)

LEGACY_POINT_NOTE = "Mốc này lấy từ bản ghi lịch sử — chưa có sổ nạp cho kỳ đó."

#: Câu cho một mốc thô gồm cả tháng sổ nạp lẫn tháng sổ cũ. Nó nói ra nguồn
#: gốc mà KHÔNG mời người đọc tách con số ra làm hai: quý đó có đúng một giá
#: trị kinh doanh, và các tháng bên trong nó không chồng lên nhau.
MIXED_POINT_NOTE = (
    "Mốc này gồm cả tháng đã có sổ nạp lẫn tháng chỉ còn bản ghi lịch sử. Mỗi "
    "tháng chỉ lấy từ MỘT nguồn, nên không tháng nào bị cộng hai lần."
)

#: `DEC-216` — bản của `MIXED_POINT_NOTE` cho mốc hỗn hợp CÓ phần lấp lỗ
#: hổng. Dùng chung một câu cho cả hai kiểu hỗn hợp sẽ nói rằng phần không
#: phải sổ nạp là "bản ghi lịch sử" — sai, và sai đúng ở chiều `DEC-166 E`
#: bắt phải đọc được.
MIXED_GAPFILL_POINT_NOTE = (
    "Mốc này gồm cả ngày đã có sổ nạp lẫn ngày chỉ vẽ được từ bảng kê ngày "
    "của sổ kế toán. Mỗi ngày chỉ lấy từ MỘT nguồn, nên không ngày nào bị "
    "cộng hai lần."
)

#: `F-E` — phạm vi thời gian của biểu đồ, nói thành lời ngay cạnh biểu đồ.
#:
#: Ô chỉ tiêu ở trên trả lời "kỳ đang chọn ra sao"; biểu đồ trả lời "xu hướng
#: đi thế nào" và cố ý nhìn TOÀN BỘ dữ liệu khả dụng (`server._revenue_chart`
#: § Biểu đồ nhìn toàn bộ dòng thời gian). Hai phạm vi khác nhau đứng cạnh
#: nhau mà không ai nói ra là cách chắc chắn nhất để một người đọc kết luận
#: rằng hai con số đang mâu thuẫn.
CHART_SCOPE_NOTE = (
    "Biểu đồ xu hướng theo TOÀN BỘ dữ liệu khả dụng, không giới hạn trong "
    "Kỳ dữ liệu đang chọn ở trên."
)

#: `DEC-216` — câu của MỘT mốc lấp lỗ hổng. Nó phải nói ra hai điều trong
#: cùng một hơi: con số này có thật (đọc từ bảng kê ngày của sổ kế toán), và
#: nó KHÔNG phải sổ nạp cũng không phải bản ghi lịch sử đã chốt — nên đừng
#: dùng nó để đối soát với ô chỉ tiêu ở trên.
GAPFILL_POINT_NOTE = (
    "Mốc này lấy từ bảng kê ngày của sổ kế toán, chỉ dùng để vẽ xu hướng — "
    "không phải sổ nạp, cũng không phải bản ghi lịch sử dùng để đối soát."
)

#: `DEC-216` — câu nói cạnh biểu đồ khi có mốc lấy từ nguồn lấp lỗ hổng.
#: Nó thay `NO_DAILY_LEGACY_NOTE` chứ không đứng cùng: câu kia giải thích một
#: khoảng TRỐNG, và giữ nó lại bên cạnh một đường đã liền là nói với người đọc
#: rằng chỗ họ đang nhìn thấy số vẫn đang trống.
GAPFILL_CHART_NOTE = (
    "Các mốc trước khi sổ nạp bắt đầu được vẽ từ bảng kê ngày của sổ kế toán, "
    "chỉ để nhìn xu hướng. Con số ĐỐI SOÁT của các kỳ cũ vẫn là tổng tháng "
    "của bản ghi lịch sử, không phải các mốc ngày này."
)

#: `R7 §D` — bản của `GAPFILL_CHART_NOTE` cho biểu đồ SỐ ĐƠN: nguồn lấp lỗ
#: hổng số đơn (`data/chart_gapfill/daily_orders.jsonl`) được trích từ chính
#: sổ chi tiết bán hàng, chỉ giữ ngày + số chứng từ. Không có "tổng tháng của
#: bản ghi lịch sử" nào cho số đơn, nên câu này không được mượn câu kia.
GAPFILL_COUNT_CHART_NOTE = (
    "Các mốc chưa có sổ nạp được đếm từ bảng kê ngày của sổ kế toán (chỉ ngày "
    "và số chứng từ), chỉ để nhìn xu hướng số đơn. Chúng KHÔNG đi vào tổng số "
    "đơn của kỳ ở phía trên."
)

NO_DAILY_LEGACY_NOTE = (
    "Bản ghi lịch sử của các kỳ cũ chỉ lưu TỔNG THÁNG, nên ở mức Ngày và Tuần "
    "chúng không có điểm nào. Hệ thống không chia đều tổng tháng ra từng ngày."
)

#: `TASK-OWNER-UIUX-003` §2 — chỉ Ngày/Tuần/Tháng bị "khoanh cửa sổ"; Quý và
#: Năm giữ nguyên hành vi TOÀN BỘ dòng thời gian của `F-E` (đã đủ thô, không
#: "dàn trải" như Ngày/Tuần/Tháng nhìn cả lịch sử làm một hàng chấm).
_WINDOWED_LEVELS = frozenset({DAY, WEEK, MONTH})


def parse_granularity(raw: Optional[str], *,
                      default: Optional[str] = None) -> str:
    """Mức gộp đang chọn. Giá trị lạ rơi về mặc định, không báo lỗi.

    Một tham số URL gõ sai không đáng làm hỏng cả trang báo cáo; nhưng nó
    cũng không được âm thầm thành một mức gộp KHÁC cái người dùng gõ và trông
    như đã hiểu — nên nó rơi về mức MẶC ĐỊNH, và đúng cái nút đó sẽ sáng lên
    như trạng thái thật.

    `default` cho phép mỗi trang tự chọn mức mở đầu của mình
    (`TASK-OWNER-UIUX-002`: trang Báo cáo mở ở NGÀY). Một `default` lạ cũng
    rơi về `DEFAULT_GRANULARITY`, nên không trang nào đặt được một mức không
    tồn tại.
    """
    fallback = default if default in GRANULARITY_KEYS else DEFAULT_GRANULARITY
    value = (raw or "").strip().lower()
    return value if value in GRANULARITY_KEYS else fallback


@dataclass(frozen=True)
class Point:
    """Một cột của biểu đồ.

    `key` là khoá SẮP XẾP và cũng là khoá gộp — nó phải so sánh được theo thứ
    tự thời gian bằng phép so chuỗi thông thường, nên mọi thành phần số đều
    được đệm 0. `label` là thứ người đọc thấy và KHÔNG được dùng để sắp xếp.
    """

    key: str
    label: str
    revenue: Decimal
    origin: str
    #: Số tháng CÓ BẰNG CHỨNG bên trong mốc này (`None` với mức Ngày/Tuần,
    #: nơi khái niệm "tháng đầy đủ" không nói lên điều gì).
    covered_months: Optional[int] = None
    #: Tổng số tháng mà mốc này bao trùm theo lịch (`None` như trên).
    span_months: Optional[int] = None
    #: Tập origin đã góp giá trị vào mốc này (`DEC-216`). Một phần tử với
    #: mốc thuần; nhiều phần tử thì `origin` là `ORIGIN_MIXED` và tập này nói
    #: hỗn hợp giữa NHỮNG GÌ. Mặc định rỗng để mọi `Point` dựng tay trong test
    #: cũ giữ nguyên chữ ký.
    origins: frozenset = frozenset()

    @property
    def is_legacy(self) -> bool:
        """Mốc này lấy TOÀN BỘ từ bản ghi lịch sử.

        `ORIGIN_MIXED` cố ý trả `False`: một quý gồm hai tháng sổ cũ và một
        tháng sổ nạp không phải "một mốc lịch sử", và dán nhãn lịch sử lên nó
        sẽ nói sai về phần số mới bên trong. Câu đúng cho nó nằm ở
        `MIXED_POINT_NOTE`.
        """
        return self.origin == ORIGIN_LEGACY

    @property
    def is_mixed(self) -> bool:
        return self.origin == ORIGIN_MIXED

    @property
    def is_gapfill(self) -> bool:
        """Mốc này lấy TOÀN BỘ từ nguồn lấp lỗ hổng (`DEC-216`)."""
        return self.origin == ORIGIN_GAPFILL

    @property
    def has_gapfill(self) -> bool:
        """Mốc này CÓ PHẦN lấy từ nguồn lấp lỗ hổng — kể cả khi hỗn hợp.

        Một tuần vắt qua ngày sổ nạp bắt đầu chạy gồm cả ngày lấp lỗ hổng lẫn
        ngày sổ nạp, nên nó mang `ORIGIN_MIXED` và `is_gapfill` trả `False`.
        Nhưng người đọc vẫn cần biết một phần con số ấy không dùng để đối
        soát được, nên câu hỏi "có phần lấp lỗ hổng không" phải trả lời được
        RIÊNG với câu hỏi "có thuần lấp lỗ hổng không".
        """
        return ORIGIN_GAPFILL in self.origins

    @property
    def partial(self) -> bool:
        """Mốc được dựng từ ÍT tháng hơn số tháng nó bao trùm.

        Chỉ có nghĩa với Quý/Năm. Một quý chỉ có bằng chứng của hai tháng vẫn
        được vẽ — giấu nó đi là mất một sự thật — nhưng nó phải tự khai rằng
        nó chưa đủ, nếu không người đọc sẽ so nó với một quý đủ ba tháng.
        """
        if self.covered_months is None or self.span_months is None:
            return False
        return self.covered_months < self.span_months


def _iso_week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def bucket_of(value: date, granularity: str) -> tuple[str, str]:
    """`(khoá sắp xếp, nhãn)` của mốc chứa ngày `value`.

    Tuần dùng chuẩn ISO (thứ Hai mở đầu) và được ghi bằng NGÀY BẮT ĐẦU chứ
    không bằng số tuần ISO: "Tuần 01/2027" của ISO có thể nằm trong tháng
    12/2026, và một nhãn như thế đặt cạnh nhãn tháng sẽ đọc như một lỗi. Ngày
    bắt đầu thì không mơ hồ với bất kỳ ai.
    """
    if granularity == DAY:
        return value.isoformat(), f"{value.day:02d}/{value.month:02d}/{value.year}"
    if granularity == WEEK:
        start = _iso_week_start(value)
        return (f"{start.isoformat()}",
                f"Tuần {start.day:02d}/{start.month:02d}/{start.year}")
    if granularity == MONTH:
        return f"{value.year:04d}-{value.month:02d}", f"{value.month:02d}/{value.year}"
    if granularity == QUARTER:
        quarter = (value.month - 1) // 3 + 1
        return f"{value.year:04d}-Q{quarter}", f"Quý {quarter}/{value.year}"
    if granularity == YEAR:
        return f"{value.year:04d}", f"Năm {value.year}"
    raise ValueError(f"Mức gộp không có trong từ vựng: {granularity!r}")


def _month_bucket(year: int, month: int, granularity: str) -> tuple[str, str]:
    """Mốc chứa THÁNG (year, month) — dùng cho bằng chứng chỉ có tổng tháng."""
    return bucket_of(date(year, month, 1), granularity)


def current_points(details: Iterable[dict], granularity: str) -> dict[str, dict]:
    """Gộp doanh thu CHÍNH THỨC của các dòng đã giữ lại, theo mốc.

    `details` là `PeriodData.details` — đã trừ dòng bị loại (`§CHART-09`) và
    đã hợp nhất mọi quyết định của Owner. Hàm này KHÔNG lọc thêm gì: lọc lần
    thứ hai ở đây sẽ dựng ra một định nghĩa doanh thu thứ hai.

    Dòng thiếu `sale_date` bị bỏ qua, và người gọi đếm chúng riêng.
    """
    buckets: dict[str, dict] = {}
    for detail in details:
        sale_date = detail.get("sale_date")
        if sale_date is None:
            continue
        revenue = detail["line"].total_sales
        if revenue is None:
            # `None` không phải `0`: một dòng chưa biết doanh thu không được
            # cộng vào mốc như thể nó bằng không. Nó vẫn nằm trong tập dòng —
            # `totals.sales_revenue` xử lý `None` bằng cùng kỷ luật.
            continue
        key, label = bucket_of(sale_date, granularity)
        slot = buckets.setdefault(
            key, {"label": label, "revenue": Decimal(0),
                  "months": set(), "days": set(), "origin": ORIGIN_CURRENT,
                  "origins": {ORIGIN_CURRENT}})
        slot["revenue"] += Decimal(revenue)
        slot["months"].add((sale_date.year, sale_date.month))
        # `DEC-211` — độ mịn NGÀY của cùng thẩm quyền. Ở mức Ngày/Tuần, thứ
        # quyết định "mốc này thuộc nguồn nào" là NGÀY chứ không phải tháng
        # chứa nó; xem `_legacy_day_points`.
        slot["days"].add(sale_date)
    return buckets


def undated_count(details: Iterable[dict]) -> int:
    """Số dòng của tập không rơi vào mốc nào vì thiếu ngày bán."""
    return sum(1 for detail in details if detail.get("sale_date") is None)


def _legacy_month_points(
    legacy_months: Iterable[dict], granularity: str, taken: set[tuple[int, int]],
) -> dict[str, dict]:
    """Điểm dựng từ TỔNG THÁNG lịch sử, bỏ những tháng số mới đã có dòng.

    `taken` là tập `(năm, tháng)` mà chuỗi hiện tại đã chiếm. Đây là chỗ thi
    hành "MỘT kỳ ⟹ MỘT nguồn": lịch sử không bao giờ được cộng thêm vào một
    mốc mà sổ nạp đã nói, kể cả khi con số của nó lớn hơn.
    """
    buckets: dict[str, dict] = {}
    for entry in legacy_months:
        year, month = int(entry["year"]), int(entry["month"])
        if (year, month) in taken:
            continue
        revenue = entry.get("sales_vnd")
        if revenue is None:
            continue
        key, label = _month_bucket(year, month, granularity)
        slot = buckets.setdefault(
            key, {"label": label, "revenue": Decimal(0),
                  "months": set(), "days": set(), "origin": ORIGIN_LEGACY,
                  "origins": {ORIGIN_LEGACY}})
        slot["revenue"] += Decimal(revenue)
        slot["months"].add((year, month))
    return buckets


def _legacy_day_points(
    legacy_days: Iterable[dict], granularity: str, taken_days: set,
) -> dict[str, dict]:
    """Điểm mức Ngày/Tuần dựng từ bằng chứng TỪNG NGÀY của sổ cũ.

    ## Thẩm quyền ở mức Ngày/Tuần được giải theo NGÀY, không theo tháng

    `DEC-211`, và đây là bản sửa một lỗ hổng Owner nhìn thấy trên màn hình
    thật. Bản cũ loại cả tháng: một ngày sổ cũ bị vứt đi chỉ vì THÁNG chứa nó
    đã có dòng sổ nạp. Với dữ liệu thật của Owner — sổ kế toán mới nạp từ
    04/09, sổ cũ có tới hết 03/09 — hệ quả là:

    ```text
    01/09 → 03/09   có bằng chứng sổ cũ, nhưng THÁNG 9 đã "thuộc" sổ nạp
                    ⟹ bị loại ⟹ ba mốc trống
    04/09 → …       sổ nạp
    ```

    Đường vẽ bắt đầu ở 04/09 và ba ngày đầu tháng là một lỗ. Không phải vì
    hệ thống không biết ba ngày đó — nó biết — mà vì nó hỏi câu hỏi thẩm
    quyền ở sai độ mịn. Cùng hình lỗi đã sửa cho Quý/Năm ở `§ Thẩm quyền được
    giải ở mức THÁNG`, chỉ khác độ mịn.

    Ở mức Ngày/Tuần, mốc được vẽ là NGÀY, nên câu hỏi đúng là "ngày này thuộc
    nguồn nào", và `taken_days` trả lời nó: một ngày đã có dòng sổ nạp thì
    thuộc sổ nạp, ngày không có thì sổ cũ được điền vào. Bất biến `DEC-180`
    §9 ("MỘT kỳ ⟹ MỘT nguồn ⟹ MỘT giá trị") KHÔNG bị nới: nó vẫn đúng, chỉ
    được thi hành ở đúng độ mịn mà biểu đồ đang nói — không ngày nào nhận giá
    trị từ hai nguồn, và `_merge_resolved` vẫn dừng hẳn nếu điều đó xảy ra.

    Hệ quả nhìn thấy được: một mốc TUẦN vắt qua ranh giới ấy gồm cả ngày sổ
    cũ lẫn ngày sổ nạp, nên nó mang `ORIGIN_MIXED` và nói ra điều đó trong
    lời của chính nó — cùng từ vựng `DEC-166 E` đã có, không phải một nhãn
    mới.
    """
    return _day_points(legacy_days, granularity, taken_days,
                       origin=ORIGIN_LEGACY)


def _day_points(rows: Iterable[dict], granularity: str, claimed_days: set,
                *, origin: str, value_field: str = "sales_vnd") -> dict[str, dict]:
    """Cơ chế dùng chung của mọi nguồn có bằng chứng TỪNG NGÀY.

    Tách ra khỏi `_legacy_day_points` khi `DEC-216` thêm nguồn lấp lỗ hổng:
    hai nguồn ấy khác nhau ở NHÃN và ở CHỖ ĐỨNG trong thứ tự thẩm quyền, chứ
    không khác nhau ở phép gộp. Viết phép gộp lần thứ hai là mở cửa cho hai
    đường vẽ cùng một biểu đồ bằng hai luật khác nhau — và sai lệch kiểu đó
    chỉ lộ ra ở đúng những ngày hiếm mà hai nguồn cùng nói.

    `claimed_days` là tập ngày đã có nguồn thẩm quyền CAO HƠN; ngày nằm trong
    đó bị loại tại đây, để `_merge_resolved` không bao giờ phải cộng hai
    nguồn cho cùng một ngày (`DEC-180` §9).
    """
    buckets: dict[str, dict] = {}
    for entry in rows:
        year, month = int(entry["year"]), int(entry["month"])
        # `R7 §D` — `value_field` là "sales_vnd" (doanh số) hay "orders" (số
        # đơn). Cùng MỘT phép gộp cho cả hai: khác nhau ở tên trường, không ở
        # luật, đúng như chú thích ở trên đòi hỏi.
        revenue = entry.get(value_field)
        if revenue is None:
            continue
        try:
            when = date(year, month, int(entry["day"]))
        except ValueError:
            # Một ô ngày không hợp lệ trong sổ cũ là một khiếm khuyết đã biết
            # của nguồn (`DEC-166 E`: known defects ghi metadata, không sửa).
            # Bỏ qua đúng ô đó, không bịa một ngày thay thế.
            continue
        if when in claimed_days:
            continue
        key, label = bucket_of(when, granularity)
        slot = buckets.setdefault(
            key, {"label": label, "revenue": Decimal(0),
                  "months": set(), "days": set(), "origin": origin,
                  "origins": {origin}})
        slot["revenue"] += Decimal(revenue)
        slot["months"].add((year, month))
        slot["days"].add(when)
    return buckets


def _gapfill_day_points(
    gapfill_days: Iterable[dict], granularity: str, claimed_days: set,
) -> dict[str, dict]:
    """`DEC-216` — điểm mức Ngày/Tuần dựng từ nguồn LẤP LỖ HỔNG.

    Nguồn này đứng CUỐI trong thứ tự thẩm quyền, sau cả sổ nạp lẫn sổ cũ:

        sổ nạp  →  sổ cũ  →  lấp lỗ hổng

    Một ngày mà sổ nạp hay sổ cũ đã nói tới thì nguồn này im lặng, kể cả khi
    nó có con số cho ngày đó. Đây không phải một quy ước tuỳ ý mà là điều
    kiện để `DEC-180` §9 còn đúng: MỘT ngày ⟹ MỘT nguồn ⟹ MỘT giá trị. Đặt
    nó lên trước bất kỳ nguồn nào khác sẽ khiến một con số dựng để VẼ ghi đè
    một con số dùng để ĐỐI SOÁT — và không màn hình nào cho thấy điều đó đã
    xảy ra.
    """
    return _day_points(gapfill_days, granularity, claimed_days,
                       origin=ORIGIN_GAPFILL)


def _merge_resolved(buckets: dict[str, dict], key: str, slot: dict,
                    *, unit: str = "months") -> None:
    """Gộp một mốc lịch sử vào chuỗi — CỘNG, không loại bỏ. Sửa `F-C`.

    Phép cộng ở đây an toàn vì thẩm quyền ĐÃ được giải xong trước khi hàm này
    chạy: tập đã bị sổ nạp chiếm đã được loại khỏi `slot`, nên hai vế của
    phép cộng không bao giờ là hai nguồn của CÙNG một đơn vị thời gian —
    chúng là những đơn vị khác nhau của cùng một mốc thô.

    `unit` nói ĐỘ MỊN mà thẩm quyền vừa được giải ở đó, và vì thế cũng là độ
    mịn phải kiểm chồng lấn: `"months"` cho Tháng/Quý/Năm, `"days"` cho
    Ngày/Tuần (`DEC-211`, xem `_legacy_day_points`). Kiểm sai độ mịn thì
    van này hoặc chặn nhầm một phép gộp đúng, hoặc — tệ hơn — bỏ lọt đúng
    trường hợp nó sinh ra để chặn.

    Bản cũ dùng `setdefault` ở đây và vì thế im lặng VỨT BỎ cả một mốc lịch
    sử mỗi khi nó rơi trúng khoá thô mà sổ nạp đã chiếm: một tháng 9 có sổ
    nạp làm bốc hơi tháng 7 và tháng 8 chỉ có sổ cũ (`§ Thẩm quyền được giải
    ở mức THÁNG`).
    """
    existing = buckets.get(key)
    if existing is None:
        buckets[key] = slot
        return
    overlap = existing[unit] & slot[unit]
    if overlap:
        # Không `assert`: một bất biến sổ sách không được biến mất khi ai đó
        # chạy Python với `-O`. Nếu điều này xảy ra, thứ tự thẩm quyền ở trên
        # đã hỏng và câu trả lời đúng là DỪNG, không phải một con số gấp đôi.
        raise ValueError(
            f"{unit} {sorted(overlap)} nhận giá trị từ hai origin trong cùng "
            f"mốc {key!r} — thẩm quyền phải đã giải xong trước khi gộp "
            "(DEC-180 §9)")
    existing["revenue"] += slot["revenue"]
    existing["months"] |= slot["months"]
    existing["days"] |= slot["days"]
    # `DEC-216` — giữ TẬP origin đã góp vào mốc này, không chỉ kết luận
    # "hỗn hợp". Với hai nguồn thì một cờ boolean là đủ, nhưng với ba thì
    # "hỗn hợp" không còn nói được nó hỗn hợp giữa những gì — và câu giải
    # thích cạnh mốc sẽ phải đoán, tức là sẽ có lúc nói sai.
    existing["origins"] |= slot["origins"]
    if existing["origin"] != slot["origin"]:
        existing["origin"] = ORIGIN_MIXED


def series(
    details: Iterable[dict], *, granularity: str,
    legacy_months: Optional[Iterable[dict]] = None,
    legacy_days: Optional[Iterable[dict]] = None,
    gapfill_days: Optional[Iterable[dict]] = None,
) -> list[Point]:
    """Chuỗi điểm đã sắp theo thời gian — bề mặt DUY NHẤT của biểu đồ.

    `legacy_months` là các bản ghi `{"year", "month", "sales_vnd"}` đã được
    tầng gọi giải về VND bằng thẩm quyền của `legacy_reference`; `legacy_days`
    là các dòng `legacy_daily_sales` (`{"year", "month", "day", "sales_vnd"}`,
    vốn đã là VND nguyên). Module này KHÔNG tự đổi đơn vị: quên hệ số 1.000
    một lần ở đây sẽ cho ra một đường cong trông như thật.

    `gapfill_days` (`DEC-216`) cùng hình dạng với `legacy_days` nhưng đứng
    CUỐI thứ tự thẩm quyền và CHỈ có tác dụng ở mức Ngày/Tuần. Ở mức Tháng
    trở lên nó bị bỏ qua hoàn toàn — không phải vì tiết kiệm, mà vì ở đó tổng
    tháng chính thức đã có mặt và cộng thêm một nguồn thứ hai cho cùng một
    tháng là đúng thứ `_merge_resolved` sinh ra để chặn.
    """
    details = list(details)
    buckets = current_points(details, granularity)
    taken = {month for slot in buckets.values() for month in slot["months"]}

    if granularity in _DAY_LEVEL:
        # `DEC-211` — ở mức Ngày/Tuần thẩm quyền giải theo NGÀY, nên cả
        # phép lọc lẫn van chống-cộng-hai-nguồn đều đọc tập NGÀY.
        taken_days = {day for slot in buckets.values() for day in slot["days"]}
        legacy = _legacy_day_points(legacy_days or [], granularity, taken_days)
        # `DEC-216` — nguồn lấp lỗ hổng chỉ nhận những ngày mà CẢ HAI nguồn
        # trên đều không nói tới. Tập bị loại phải cộng cả ngày của sổ cũ vừa
        # dựng ở trên, không chỉ ngày của sổ nạp: một ngày sổ cũ mà nguồn lấp
        # cũng có sẽ thành hai giá trị trong cùng một mốc.
        claimed = set(taken_days)
        for slot in legacy.values():
            claimed |= slot["days"]
        resolved = [legacy,
                    _gapfill_day_points(gapfill_days or [], granularity, claimed)]
        unit = "days"
    else:
        resolved = [_legacy_month_points(legacy_months or [], granularity, taken)]
        unit = "months"
    for group in resolved:
        for key, slot in group.items():
            _merge_resolved(buckets, key, slot, unit=unit)

    span = _MONTHS_IN_BUCKET.get(granularity)
    points = []
    for key in sorted(buckets):
        slot = buckets[key]
        points.append(Point(
            key=key, label=slot["label"], revenue=slot["revenue"],
            origin=slot["origin"], origins=frozenset(slot["origins"]),
            covered_months=None if span is None else len(slot["months"]),
            span_months=span,
        ))
    return points


def count_series(
    details: Iterable[dict], *, granularity: str,
    gapfill_days: Optional[Iterable[dict]] = None,
) -> list[Point]:
    """`R7 §D` — chuỗi SỐ ĐƠN theo thời gian, có lấp lỗ hổng, MỌI mức gộp.

    Số đơn của sổ nạp đếm bằng đúng `dashboard_metrics.order_facts` (một số
    chứng từ = một đơn, xếp vào NGÀY NHỎ NHẤT của đơn) — không có định nghĩa
    số đơn thứ hai ở đây. Nguồn lấp lỗ hổng (`chart_gapfill.daily_order_rows`)
    chỉ nhận những NGÀY mà sổ nạp không nói tới, đúng luật `_gapfill_day_
    points` của doanh số.

    Khác `series()` ở một điểm, và điểm ấy có lý do: nguồn lấp được nối ở CẢ
    Tháng/Quý/Năm. Với doanh số, ở các mức thô tổng tháng chính thức của bản
    ghi lịch sử đã có mặt nên nối thêm là cộng hai nguồn cho cùng một tháng;
    với SỐ ĐƠN không tồn tại bản ghi lịch sử nào (`_orders_chart_summary`:
    "legacy chỉ lưu DOANH THU, không lưu SỐ ĐƠN"), nên ở mức Tháng một tháng
    chưa nạp sổ chỉ có đúng một nguồn để hỏi. Thẩm quyền vẫn giải ở mức NGÀY
    và gộp lên: một tháng nửa sổ nạp nửa lấp lỗ hổng là `ORIGIN_MIXED` với
    `origins` nói rõ hai nửa — không ngày nào bị đếm hai lần.
    """
    buckets: dict[str, dict] = {}
    claimed: set = set()
    for fact in dashboard_metrics.order_facts(details).values():
        when = fact.bucket_date
        if when is None:
            continue
        claimed.add(when)
        key, label = bucket_of(when, granularity)
        slot = buckets.setdefault(
            key, {"label": label, "revenue": Decimal(0), "months": set(),
                  "days": set(), "origin": ORIGIN_CURRENT,
                  "origins": {ORIGIN_CURRENT}})
        slot["revenue"] += 1
        slot["months"].add((when.year, when.month))
        slot["days"].add(when)
    filled = _day_points(gapfill_days or [], granularity, claimed,
                         origin=ORIGIN_GAPFILL, value_field="orders")
    for key, slot in filled.items():
        _merge_resolved(buckets, key, slot, unit="days")
    return [
        Point(key=key, label=slot["label"], revenue=slot["revenue"],
              origin=slot["origin"], origins=frozenset(slot["origins"]))
        for key, slot in sorted(buckets.items())
    ]


# --- R5 §3: hai cửa sổ liền kề, cùng độ dài -------------------------------
#
# Quyết định Owner 08/09/2026 (`DEC-R5-02`): biểu đồ so HAI cửa sổ liền kề có
# CÙNG độ dài — 30 ngày, 12 tuần, 12 tháng, 8 quý. Đây là một sửa đổi có chủ
# đích với `window_bounds` của `TASK-OWNER-UIUX-003` §2 (cửa sổ theo CONTAINER
# lịch: Ngày trong một tháng, Tuần trong một quý, Tháng trong một năm), và lý
# do đổi nằm ở chính phép so sánh: hai container lịch liền nhau KHÔNG cùng độ
# dài (tháng 2 có 28 ngày, tháng 3 có 31), nên đặt chúng cạnh nhau là mời
# người đọc so hai con số không so được.
#
# `window_bounds`/`window_points` KHÔNG bị xoá: mức Năm vẫn dùng đường một
# chuỗi cũ, và hai hàm ấy vẫn là bề mặt kiểm được của phép cắt cửa sổ.
#: `R7 §C` (Owner 11/09/2026) — cửa sổ là CONTAINER LỊCH của mốc neo, KHÔNG
#: còn là một dải cố định N mốc kết thúc ở mép phải (`DEC-211`). Owner nói
#: thẳng về mức Ngày: *"dải 30 ngày sửa lại từ 1 đến cuối tháng"*, và "áp
#: dụng cho cả tuần - tháng - quý - năm":
#:
#:     Ngày   → mọi ngày của THÁNG chứa mốc neo (01 → cuối tháng)
#:     Tuần   → mọi tuần ISO chạm vào QUÝ chứa mốc neo
#:     Tháng  → 12 tháng của NĂM chứa mốc neo
#:     Quý    → 4 quý của NĂM chứa mốc neo
#:     Năm    → 5 năm kết thúc ở năm chứa mốc neo (không có "container" nào
#:              trên năm; giữ nguyên cửa sổ 5 mốc của `DEC-211`)
#:
#: Cửa sổ so sánh vẫn là CÙNG KỲ NĂM TRƯỚC (`DEC-211` không đổi ở điểm này):
#: container ấy của năm trước. Hai container có thể lệch nhau một mốc (tháng
#: 2 nhuận, quý 13/14 tuần) — cửa sổ ngắn hơn được đệm một mốc TRỐNG ở cuối
#: để hai đường vẫn dùng chung một trục, và mốc đệm không bao giờ mang số.
#:
#: Phần bên phải mốc neo (những ngày CHƯA tới) là khoảng trống của đường
#: hiện tại: đó chính là chỗ người đọc nhìn thấy "đến hiện tại" kết thúc ở
#: đâu so với đường năm trước chạy hết container.
CONTAINER_OF: dict[str, str] = {DAY: MONTH, WEEK: QUARTER, MONTH: YEAR,
                                QUARTER: YEAR}

#: Số mốc của cửa sổ mức NĂM — mức duy nhất không có container lịch phía trên.
YEAR_WINDOW_SIZE = 5

#: Mức gộp có cửa sổ so sánh — TẤT CẢ, kể cả Năm (`DEC-211`).
COMPARISON_LEVELS: frozenset = frozenset((DAY, WEEK, MONTH, QUARTER, YEAR))

#: Khoá của một mốc ĐỆM (xem `CONTAINER_OF`). Không phải khoá lịch nào có
#: thể sinh ra chuỗi này, nên `_bucket_span` trả `None` cho nó và không nhánh
#: nào biến nó thành một số 0 "đã xác nhận".
PAD_KEY_PREFIX = "__pad__"

CURRENT_WINDOW_LABEL = "Kỳ này"
COMPARISON_WINDOW_LABEL = "Cùng kỳ năm trước"

COMPARISON_NOTE = (
    "Hai đường so KỲ NÀY với CÙNG KỲ NĂM TRƯỚC: đường đậm là kỳ hiện tại, "
    "đường mờ là đúng khoảng thời gian ấy của năm trước. Chúng dùng CHUNG một "
    "trục và một thước đo, nên hai điểm cùng vị trí là cùng một mốc lịch của "
    "hai năm — ngày 05/09 năm nay nằm đúng trên ngày 05/09 năm ngoái."
)

#: `F-E` ở chế độ hai cửa sổ — câu phải nói ĐÚNG phạm vi thật của biểu đồ.
#: `F-E` sinh ra để không cho hai con số cạnh nhau nói hai điều mâu thuẫn mà
#: không ai giải thích; cách giữ đúng tinh thần đó khi phạm vi đổi là ĐỔI CÂU
#: theo phạm vi mới, không phải xoá câu đi.
COMPARISON_SCOPE_TEXT = (
    "Biểu đồ so kỳ này với cùng kỳ năm trước: {current} so với "
    "{comparison} — chưa phải toàn bộ dữ liệu."
)

GAP_NOTE = (
    "Chỗ đường bị ĐỨT là chỗ chưa có bằng chứng cho mốc đó — không phải doanh "
    "thu bằng 0. Số 0 chỉ được vẽ khi khoảng ngày ấy nằm trong một sổ đã được "
    "xác nhận đầy đủ, tức là hệ thống thật sự biết không có đơn nào."
)


def _shift_months(year: int, month: int, delta: int) -> tuple[int, int]:
    """`(năm, tháng)` sau khi dịch `delta` tháng. `delta` âm là lùi."""
    index = (year * 12 + month - 1) + delta
    return index // 12, index % 12 + 1


def _step_back(granularity: str, value: date, steps: int) -> date:
    """Ngày ĐẠI DIỆN của mốc lùi `steps` bước từ mốc chứa `value`.

    Trả về một ngày nằm TRONG mốc đích, không nhất thiết là ngày đầu mốc —
    `bucket_of` sẽ chuẩn hoá lại. Với tháng/quý, ngày 1 luôn tồn tại ở mọi
    tháng nên không có nhánh nào rơi vào một ngày không có thật (31/02).
    """
    if granularity == DAY:
        return value - timedelta(days=steps)
    if granularity == WEEK:
        return _iso_week_start(value) - timedelta(days=7 * steps)
    if granularity == MONTH:
        year, month = _shift_months(value.year, value.month, -steps)
        return date(year, month, 1)
    if granularity == QUARTER:
        start_month = (value.month - 1) // 3 * 3 + 1
        year, month = _shift_months(value.year, start_month, -3 * steps)
        return date(year, month, 1)
    if granularity == YEAR:
        return date(value.year - steps, 1, 1)
    raise ValueError(f"Mức gộp không có cửa sổ so sánh: {granularity!r}")


def _same_day_last_year(value: date) -> date:
    """Cùng ngày dương lịch của năm trước. 29/02 lùi về 28/02.

    Không có ngày 29/02 ở một năm không nhuận, và bịa ra 01/03 thay vào đó sẽ
    đặt một ngày của tháng 3 lên đúng vị trí trục của một ngày tháng 2.
    """
    try:
        return value.replace(year=value.year - 1)
    except ValueError:
        return date(value.year - 1, 2, 28)


def _same_week_last_year(value: date) -> date:
    """Ngày đầu của cùng TUẦN ISO ở năm ISO trước.

    Đi qua số tuần ISO chứ không qua "lùi 52 tuần": một năm ISO có 52 hoặc 53
    tuần, nên phép lùi cố định sẽ trôi dần khỏi cùng kỳ sau vài năm. Năm đích
    chỉ có 52 tuần mà đang đứng ở tuần 53 thì rơi về tuần 52 — mốc gần nhất
    thật sự tồn tại, không phải một tuần bịa ra.
    """
    iso_year, iso_week, _ = value.isocalendar()
    target = iso_year - 1
    try:
        return date.fromisocalendar(target, iso_week, 1)
    except ValueError:
        return date.fromisocalendar(target, 52, 1)


def _same_period_last_year(granularity: str, value: date) -> date:
    """Ngày ĐẠI DIỆN của cùng mốc ấy ở năm trước.

    `DEC-211` — Owner chốt: MỌI mức gộp so với cùng kỳ NĂM TRƯỚC, không phải
    với cửa sổ liền kề như `DEC-R5-02`. Ngày so với ngày ấy năm ngoái, tuần
    với tuần ISO ấy năm ngoái, tháng/quý/năm tương tự.

    Trả về một ngày nằm TRONG mốc đích; `bucket_of` chuẩn hoá lại.
    """
    if granularity == DAY:
        return _same_day_last_year(value)
    if granularity == WEEK:
        return _same_week_last_year(value)
    if granularity in (MONTH, QUARTER, YEAR):
        return _step_back(granularity, value, 1 if granularity == YEAR else
                          (12 if granularity == MONTH else 4))
    raise ValueError(f"Mức gộp không có cửa sổ so sánh: {granularity!r}")


def container_bounds(granularity: str, anchor: date) -> tuple[date, date]:
    """`(ngày đầu, ngày cuối)` — cận trên BAO GỒM — của CONTAINER chứa `anchor`
    ở mức `granularity` (`R7 §C`, xem `CONTAINER_OF`).

    Dựng từ LỊCH, không từ dữ liệu: cùng lý do `window_slots` đã ghi — một cửa
    sổ co theo những ngày có số sẽ làm hai cửa sổ "cùng khung" trải trên hai
    khoảng thời gian khác nhau.
    """
    if granularity == DAY:
        return (date(anchor.year, anchor.month, 1),
                date(anchor.year, anchor.month,
                     monthrange(anchor.year, anchor.month)[1]))
    if granularity == WEEK:
        start, next_start = _quarter_bounds(anchor.year, anchor.month)
        return start, next_start - timedelta(days=1)
    if granularity in (MONTH, QUARTER):
        return date(anchor.year, 1, 1), date(anchor.year, 12, 31)
    return date(anchor.year - YEAR_WINDOW_SIZE + 1, 1, 1), date(anchor.year, 12, 31)


def container_slots(granularity: str, anchor: date) -> list[tuple[str, str]]:
    """Mọi mốc của CONTAINER chứa `anchor`, từ cũ tới mới (`R7 §C`).

    Mức Tuần liệt kê mọi tuần ISO CHẠM vào quý — tuần đầu có thể bắt đầu ở
    quý trước và tuần cuối kết thúc ở quý sau; đó là hình dạng thật của một
    quý trên lịch tuần, và cắt bớt là làm mất vài ngày bán ở hai mép.
    """
    start, end = container_bounds(granularity, anchor)
    if granularity == DAY:
        return [bucket_of(start + timedelta(days=offset), DAY)
                for offset in range((end - start).days + 1)]
    if granularity == WEEK:
        slots, cursor = [], _iso_week_start(start)
        while cursor <= end:
            slots.append(bucket_of(cursor, WEEK))
            cursor += timedelta(days=7)
        return slots
    if granularity == MONTH:
        return [bucket_of(date(anchor.year, month, 1), MONTH)
                for month in range(1, 13)]
    if granularity == QUARTER:
        return [bucket_of(date(anchor.year, month, 1), QUARTER)
                for month in (1, 4, 7, 10)]
    return window_slots(YEAR, anchor, YEAR_WINDOW_SIZE)


def window_slots(granularity: str, anchor: date, size: int) -> list[tuple[str, str]]:
    """`size` mốc LIÊN TIẾP kết thúc tại mốc chứa `anchor`, từ cũ tới mới.

    Dựng từ LỊCH, không từ dữ liệu. Đó là toàn bộ điểm của hàm này: một cửa
    sổ dựng từ các mốc CÓ dữ liệu sẽ tự co lại quanh những ngày bán được, và
    hai cửa sổ "cùng độ dài" khi ấy sẽ trải trên hai khoảng thời gian khác
    nhau — đúng phép so sánh sai mà `DEC-R5-02` sinh ra để tránh.
    """
    slots = [bucket_of(_step_back(granularity, anchor, step), granularity)
             for step in range(size - 1, -1, -1)]
    return slots


def comparison_anchor(granularity: str, anchor: date,
                      size: Optional[int] = None) -> date:
    """Ngày neo của cửa sổ SO SÁNH — cùng mốc ấy của NĂM TRƯỚC.

    `DEC-211` thay `DEC-R5-02`: cửa sổ so sánh không còn là cửa sổ liền kề
    lùi `size` mốc, mà là ĐÚNG khoảng thời gian ấy của năm trước. `size` giữ
    lại trong chữ ký để mọi nơi gọi cũ không phải sửa, và cố ý KHÔNG được
    dùng tới — cùng kỳ năm trước không phụ thuộc độ dài cửa sổ.

    Hệ quả cần biết: ở mức Tháng (12 mốc) và Quý (4 mốc), một năm ĐÚNG BẰNG
    một cửa sổ, nên hai cửa sổ vẫn liền kề và không chồng nhau như trước. Ở
    mức Năm (5 mốc) chúng chồng nhau 4 năm — đó là đúng nghĩa "năm nay so với
    năm ngoái" tại từng vị trí trục, không phải một lỗi.
    """
    return _same_period_last_year(granularity, anchor)


def anchor_date(
    period: Optional[tuple[int, int]], details: Iterable[dict],
) -> Optional[date]:
    """Mốc kết thúc của cửa sổ hiện tại — MÉP PHẢI của biểu đồ.

    `DEC-211` — Owner chốt: mép phải luôn là NGÀY CÓ DỮ LIỆU MỚI NHẤT, kể
    cả khi đang chọn một kỳ. Trước đó, chọn một tháng sẽ neo vào ngày CUỐI
    THÁNG, nên nửa cuối biểu đồ là một khoảng trắng của những ngày chưa tới —
    Owner đọc khoảng trắng ấy như "biểu đồ bị cụt". Neo vào ngày cuối cùng có
    số thì mọi pixel của trục đều là thời gian đã có sổ.

    Neo vào HÔM NAY theo lịch cũng bị loại vì lý do cũ: sổ chưa nạp vài ngày
    sẽ vẽ ra một dải trống ở mép phải, và một biểu đồ trống đọc như "không
    bán được gì".

    `period` chỉ còn là đường lui khi lát dữ liệu không có dòng nào mang ngày
    bán — khi ấy vẫn phải có một mép phải để dựng trục.

    `None` khi không có kỳ và cũng không có dòng nào — không có gì để neo.
    """
    dates = [detail["sale_date"] for detail in details
             if detail.get("sale_date") is not None]
    if dates:
        return max(dates)
    if period is not None:
        year, month = period
        return date(year, month, monthrange(year, month)[1])
    return None


@dataclass(frozen=True)
class Slot:
    """Một VỊ TRÍ trên trục X — nơi hai cửa sổ gặp nhau.

    `index` là toạ độ tương đối dùng chung: điểm `index` của cửa sổ hiện tại
    và điểm `index` của cửa sổ so sánh là hai mốc TƯƠNG ỨNG (ngày thứ n của
    mỗi cửa sổ), và đó là toàn bộ ý nghĩa của việc vẽ chúng chồng lên nhau.

    `revenue is None` là một KHOẢNG TRỐNG, không phải số 0 — xem `GAP_NOTE`.
    """

    index: int
    key: str
    label: str
    revenue: Optional[Decimal]
    origin: Optional[str] = None
    #: `Point.partial` của mốc gốc — một quý dựng từ ít tháng hơn số tháng nó
    #: bao trùm. Chở theo chứ không tính lại: nó là một sự thật về BẰNG CHỨNG
    #: của mốc, và bỏ nó đi ở đây sẽ khiến một quý hai tháng trông ngang hàng
    #: với một quý đủ ba tháng trên cùng một đường.
    partial: bool = False
    #: `Point.origins` của mốc gốc (`DEC-216`) — chở theo vì lời giải thích
    #: cạnh chấm phải nói đúng mốc ấy hỗn hợp giữa những gì.
    origins: frozenset = frozenset()

    @property
    def is_gap(self) -> bool:
        return self.revenue is None

    @property
    def has_gapfill(self) -> bool:
        return ORIGIN_GAPFILL in self.origins


@dataclass(frozen=True)
class PairedSeries:
    """Hai chuỗi cùng độ dài trên cùng một trục, và nhãn của chúng."""

    current: tuple[Slot, ...]
    comparison: tuple[Slot, ...]
    current_label: str
    comparison_label: str
    #: `R7 §C` — mốc neo và mức gộp đã dựng nên hai cửa sổ, để `project()`
    #: biết kỳ đã đi được bao xa. Mặc định để mọi `PairedSeries` dựng tay
    #: trong test cũ giữ nguyên chữ ký.
    anchor: Optional[date] = None
    granularity: str = ""

    @property
    def size(self) -> int:
        return len(self.current)


@dataclass(frozen=True)
class Projection:
    """`R7 §C` — "với tốc độ này thì hết kỳ đạt bao nhiêu % so với cùng kỳ".

    Một phép chia ba số, và cả ba đều đọc được trên màn hình để người đọc
    kiểm lại: `current_to_date` là tổng ĐÃ có của kỳ này tới mốc neo,
    `elapsed_fraction` là phần lịch của container đã trôi qua tới mốc neo,
    `comparison_total` là tổng TRỌN container của cùng kỳ năm trước. Dự phóng
    = tổng đã có ÷ phần đã trôi qua — tức giữ đúng nhịp hiện tại tới hết kỳ.
    Đây là một phép ngoại suy TRÌNH BÀY, không phải một chỉ tiêu: nó không
    đi vào KPI, không vào bảng kê, không vào chốt kỳ.
    """

    current_to_date: Decimal
    elapsed_units: int
    total_units: int
    comparison_total: Decimal
    #: Tổng cùng kỳ năm trước tính ĐẾN CÙNG VỊ TRÍ mốc neo — để so "đến giờ
    #: này năm ngoái được bao nhiêu" mà không cần đợi hết kỳ.
    comparison_to_date: Decimal
    #: Số mốc của cửa sổ so sánh KHÔNG có bằng chứng: khác 0 thì các phần
    #: trăm dưới đây so với một con số chưa đủ, và trang phải nói ra.
    comparison_gaps: int

    @property
    def elapsed_fraction(self) -> Decimal:
        if self.total_units <= 0:
            return Decimal(0)
        return Decimal(self.elapsed_units) / Decimal(self.total_units)

    @property
    def projected_total(self) -> Decimal:
        fraction = self.elapsed_fraction
        if fraction <= 0:
            return Decimal(0)
        return (self.current_to_date / fraction).quantize(
            Decimal(1), rounding=ROUND_HALF_UP)

    def _percent(self, value: Decimal) -> Optional[Decimal]:
        if self.comparison_total <= 0:
            return None
        return (value / self.comparison_total * 100).quantize(
            Decimal(1), rounding=ROUND_HALF_UP)

    @property
    def projected_percent(self) -> Optional[Decimal]:
        """Dự phóng hết kỳ ÷ trọn cùng kỳ năm trước, %. `None` khi năm trước
        không có số để chia."""
        return self._percent(self.projected_total)

    @property
    def to_date_percent(self) -> Optional[Decimal]:
        """Đã có tới mốc neo ÷ cùng kỳ năm trước TỚI CÙNG MỐC, %."""
        if self.comparison_to_date <= 0:
            return None
        return (self.current_to_date / self.comparison_to_date * 100).quantize(
            Decimal(1), rounding=ROUND_HALF_UP)


def _covered_by_confirmed(key: str, granularity: str,
                          confirmed_ranges: Sequence[tuple[date, date]]) -> bool:
    """Mốc `key` có nằm TRỌN trong một khoảng đã xác nhận đầy đủ không?

    "Trọn" chứ không "chạm": một sổ đã xác nhận đầy đủ cho 01–10/09 KHÔNG nói
    được gì về phần còn lại của tháng 9, nên mốc THÁNG 09/2026 vẫn là một
    khoảng trống chứ không phải số 0. Cùng ranh giới thẩm quyền mà
    `reconciler.absent_keys` đã thi hành ở tầng dòng.
    """
    span = _bucket_span(key, granularity)
    if span is None:
        return False
    start, end = span
    return any(low <= start and end <= high for low, high in confirmed_ranges)


def _bucket_span(key: str, granularity: str) -> Optional[tuple[date, date]]:
    """`(ngày đầu, ngày cuối)` của mốc — cận trên BAO GỒM."""
    try:
        if granularity == DAY:
            day = date.fromisoformat(key)
            return day, day
        if granularity == WEEK:
            start = date.fromisoformat(key)
            return start, start + timedelta(days=6)
        if granularity == MONTH:
            year, month = int(key[:4]), int(key[5:7])
            return date(year, month, 1), date(year, month, monthrange(year, month)[1])
        if granularity == QUARTER:
            year, quarter = int(key[:4]), int(key[6:])
            start_month = (quarter - 1) * 3 + 1
            start = date(year, start_month, 1)
            end_year, end_month = _shift_months(year, start_month, 2)
            return start, date(end_year, end_month,
                               monthrange(end_year, end_month)[1])
        if granularity == YEAR:
            # `DEC-211` cho mức Năm một cửa sổ so sánh, nên mốc NĂM nay đi
            # qua đây thật (trước đó không nhánh nào chạm tới). Thiếu nhánh
            # này, mọi năm sẽ là "không nằm trọn trong khoảng đã xác nhận" và
            # `paired_window_span` không đọc nổi cận ngày của cửa sổ.
            year = int(key[:4])
            return date(year, 1, 1), date(year, 12, 31)
    except (ValueError, IndexError):
        return None
    return None


def paired_window_span(
    granularity: str, anchor: Optional[date],
) -> Optional[tuple[date, date]]:
    """`(ngày đầu cửa sổ SO SÁNH, ngày cuối cửa sổ HIỆN TẠI)`, hoặc `None`.

    Repair `FIND-R6-IR-01`. Hàm này trả lời một câu mà `paired_series()` KHÔNG
    trả lời được, và chính khoảng trống giữa hai câu ấy là chỗ lỗi đã sống:

    ```text
    paired_series()      "hai cửa sổ này gồm những MỐC nào, giá trị bao nhiêu"
    paired_window_span() "muốn trả lời câu trên, phải ĐỌC dữ liệu từ ngày nào
                          tới ngày nào"
    ```

    Tầng gọi trước đây tự trả lời câu thứ hai bằng cách đưa vào lát dữ liệu ĐÃ
    LỌC theo phạm vi đang xem. Nhưng cửa sổ so sánh — theo định nghĩa — nằm
    NGOÀI phạm vi ấy, và với các mức gộp thô hơn NGÀY thì ngay cả cửa sổ HIỆN
    TẠI cũng lùi ra ngoài (12 tuần tính từ cuối tháng 9 chạm tới tháng 7). Mọi
    mốc thiếu dữ liệu khi ấy hoặc thành khoảng trống, hoặc — tệ hơn — thành số
    `0` mang cờ `ORIGIN_CURRENT` nếu ngày đó nằm trọn trong một sổ đã xác nhận
    đầy đủ (`_covered_by_confirmed`). Một khoảng thời gian có tiền thật bị vẽ
    thành "đã đo, bằng 0".

    Khoảng trả về được dựng từ LỊCH, đúng cùng phép tính mà `window_slots` và
    `comparison_anchor` đã dùng — nên nó phủ đúng `2 x size` mốc mà
    `paired_series()` sẽ hỏi tới, không thừa một ngày, không thiếu một ngày.
    Cận trên là ngày CUỐI của mốc chứa `anchor` (không phải chính `anchor`): mốc
    cuối phải được phủ TRỌN, nếu không giá trị của nó sẽ nhỏ hơn giá trị mà
    trang Báo cáo `R5` — vốn đọc toàn bộ dòng thời gian — hiện cho cùng mốc.

    `None` khi mức gộp không có cửa sổ so sánh (Năm) hoặc không có gì để neo.
    Ở hai trường hợp đó tầng gọi giữ nguyên lát của phạm vi đang xem: không có
    cửa sổ thứ hai nào để phủ.

    Đây KHÔNG phải một engine thời gian thứ hai. Nó không chia mốc, không tính
    giá trị, không sắp xếp — nó chỉ cộng lại hai phép lùi mốc đã có và đọc cận
    ngày của mốc đầu/cuối bằng `_bucket_span`, cùng hàm mà `paired_series()`
    dùng để quyết định một mốc có nằm trọn trong khoảng đã xác nhận hay không.
    """
    if granularity not in COMPARISON_LEVELS or anchor is None:
        return None
    current = container_slots(granularity, anchor)
    previous = container_slots(granularity, comparison_anchor(granularity, anchor))
    if not current or not previous:
        return None
    low = _bucket_span(previous[0][0], granularity)
    high = _bucket_span(current[-1][0], granularity)
    if low is None or high is None:
        return None
    return low[0], high[1]


def paired_series(
    points: Sequence[Point], *, granularity: str, anchor: Optional[date],
    confirmed_ranges: Sequence[tuple[date, date]] = (),
) -> Optional[PairedSeries]:
    """Hai cửa sổ liền kề cùng độ dài, dựng từ MỘT chuỗi điểm đã tính.

    `points` là kết quả của `series()` — KHÔNG tính lại doanh thu ở đây, và
    đó là điều kiện để `DEC-R5-02` không dựng ra một công thức doanh thu thứ
    hai. Hàm này chỉ CHỌN và XẾP: nó lấy các mốc lịch của hai cửa sổ, tra
    giá trị đã có, và để trống chỗ không có.

    `None` khi mức gộp không có cửa sổ so sánh (Năm) hoặc không có gì để neo.
    """
    if granularity not in COMPARISON_LEVELS or anchor is None:
        return None
    by_key = {point.key: point for point in points}
    anchor_key = bucket_of(anchor, granularity)[0]

    def slots_of(window_anchor: date, *, cutoff: Optional[str]) -> list[Slot]:
        built = []
        for index, (key, label) in enumerate(
                container_slots(granularity, window_anchor)):
            # `R7 §C` — đường HIỆN TẠI dừng ở mốc neo: phần bên phải của
            # container là những mốc CHƯA tới (hoặc nằm ngoài phạm vi người
            # dùng chọn), và chúng là khoảng trống — không phải số 0, cũng
            # không phải một con số đã có trong sổ nhưng ngoài "đến hiện
            # tại". Cửa sổ so sánh không có mốc neo: nó chạy trọn container.
            if cutoff is not None and key > cutoff:
                built.append(Slot(index=index, key=key, label=label,
                                  revenue=None, origin=None))
                continue
            point = by_key.get(key)
            if point is not None:
                built.append(Slot(index=index, key=key, label=label,
                                  revenue=point.revenue, origin=point.origin,
                                  partial=point.partial,
                                  origins=point.origins))
                continue
            # Không có điểm: số 0 CHỈ khi phạm vi đã được xác nhận đầy đủ,
            # tức hệ thống thật sự biết không có đơn nào. Mọi trường hợp còn
            # lại là một khoảng trống, và khoảng trống phải nhìn ra được.
            zero = _covered_by_confirmed(key, granularity, confirmed_ranges)
            built.append(Slot(index=index, key=key, label=label,
                              revenue=Decimal(0) if zero else None,
                              origin=ORIGIN_CURRENT if zero else None))
        return built

    current = slots_of(anchor, cutoff=anchor_key)
    comparison = slots_of(comparison_anchor(granularity, anchor), cutoff=None)
    # `R7 §C` — hai container có thể lệch nhau một mốc (tháng 2 nhuận, quý
    # 13/14 tuần). Đệm cửa sổ ngắn hơn bằng mốc TRỐNG ở cuối: không số, không
    # nhãn, không khoá lịch — để hai đường vẫn chung một trục mà không mốc
    # nào bị vẽ thành một con số chưa ai đo.
    size = max(len(current), len(comparison))
    for window in (current, comparison):
        while len(window) < size:
            window.append(Slot(index=len(window),
                               key=f"{PAD_KEY_PREFIX}{len(window)}", label="",
                               revenue=None, origin=None))
    return PairedSeries(
        current=tuple(current), comparison=tuple(comparison),
        current_label=CURRENT_WINDOW_LABEL,
        comparison_label=COMPARISON_WINDOW_LABEL,
        anchor=anchor, granularity=granularity,
    )


def _elapsed_units(granularity: str, anchor: date) -> tuple[int, int]:
    """`(số ngày đã trôi qua, tổng số ngày)` của container chứa `anchor`.

    Đo bằng NGÀY ở mọi mức, kể cả Tháng/Quý: "tốc độ này" là tốc độ tính tới
    hôm nay, và một tháng mới đi được 3 ngày không thể được tính là đã trôi
    qua trọn 1/12 năm. Mức Năm đo trong chính năm chứa mốc neo (container
    của nó là năm đó, cửa sổ 5 năm chỉ là bề rộng trục).
    """
    if granularity == YEAR:
        start, end = date(anchor.year, 1, 1), date(anchor.year, 12, 31)
    else:
        start, end = container_bounds(granularity, anchor)
    return (anchor - start).days + 1, (end - start).days + 1


def project(paired: Optional[PairedSeries]) -> Optional[Projection]:
    """Dự phóng hết kỳ của `paired`, hoặc `None` khi không có gì để dự phóng.

    Chỉ CHỌN và CỘNG các mốc đã có — không đọc dữ liệu, không tính lại doanh
    thu. Mức Năm chỉ so NĂM chứa mốc neo với NĂM TRƯỚC NÓ (mốc cuối của hai
    cửa sổ), vì "5 năm so với 5 năm trước" không phải câu Owner hỏi.
    """
    if paired is None or paired.anchor is None or not paired.granularity:
        return None
    granularity, anchor = paired.granularity, paired.anchor
    anchor_key = bucket_of(anchor, granularity)[0]

    def real(slots):
        return [slot for slot in slots
                if not slot.key.startswith(PAD_KEY_PREFIX)]

    if granularity == YEAR:
        current = [slot for slot in real(paired.current) if slot.key == anchor_key]
        comparison = [slot for slot in real(paired.comparison)
                      if slot.key == bucket_of(
                          comparison_anchor(YEAR, anchor), YEAR)[0]]
        comparison_to_date = comparison
    else:
        current = [slot for slot in real(paired.current) if slot.key <= anchor_key]
        comparison = real(paired.comparison)
        cutoff = max((slot.index for slot in current), default=-1)
        comparison_to_date = [slot for slot in comparison if slot.index <= cutoff]
    if not current:
        return None
    total = lambda slots: sum((slot.revenue for slot in slots  # noqa: E731
                               if not slot.is_gap), Decimal(0))
    elapsed, units = _elapsed_units(granularity, anchor)
    return Projection(
        current_to_date=total(current),
        elapsed_units=elapsed, total_units=units,
        comparison_total=total(comparison),
        comparison_to_date=total(comparison_to_date),
        comparison_gaps=sum(1 for slot in comparison if slot.is_gap),
    )


def _quarter_bounds(year: int, month: int) -> tuple[date, date]:
    """`(ngày đầu quý, ngày đầu quý KẾ TIẾP)` chứa `(year, month)` — cận trên
    KHÔNG bao gồm, cùng quy ước với mọi cận trên khác trong module này."""
    start_month = (month - 1) // 3 * 3 + 1
    start = date(year, start_month, 1)
    end_month, end_year = start_month + 3, year
    if end_month > 12:
        end_month, end_year = end_month - 12, year + 1
    return start, date(end_year, end_month, 1)


def window_bounds(
    granularity: str, period: Optional[tuple[int, int]],
) -> Optional[tuple[str, str]]:
    """`(khoá thấp nhất, khoá cao nhất KHÔNG bao gồm)` của cửa sổ hiện tại,
    hoặc `None` nếu không khoanh.

    `TASK-OWNER-UIUX-003` §2 — Owner: biểu đồ Ngày dàn trải hết lịch sử "nhìn
    kinh khủng"; muốn Ngày chỉ hiện các ngày trong THÁNG đang chọn, Tuần chỉ
    hiện các tuần trong QUÝ chứa kỳ đang chọn, Tháng chỉ hiện các tháng trong
    NĂM chứa kỳ đang chọn.

    Đây LÀ một sửa đổi có chủ đích với `F-E` (`CHART_SCOPE_NOTE` cũ: biểu đồ
    luôn nhìn TOÀN BỘ dữ liệu, không giới hạn theo kỳ đang chọn) — không phải
    một vi phạm âm thầm. `F-E` sinh ra để không cho hai con số cạnh nhau nói
    hai điều mâu thuẫn mà không ai giải thích; cách giữ đúng tinh thần đó khi
    phạm vi biểu đồ đổi là ĐỔI CÂU CHỮ theo đúng phạm vi mới (xem
    `business_presentation.revenue_chart` → `scope_note`), không phải xoá
    câu chữ đi. Quý/Năm KHÔNG bị khoanh — hai mức đó đã đủ thô, và không có
    "quý chứa quý" hay "năm chứa năm" để khoanh vào.

    `period=None` ("Toàn bộ dữ liệu" đang chọn) ⟹ không có kỳ nào để neo cửa
    sổ, nên KHÔNG khoanh — giữ hành vi TOÀN BỘ dòng thời gian cũ cho trường
    hợp đó, ở mọi mức gộp.
    """
    if period is None or granularity not in _WINDOWED_LEVELS:
        return None
    year, month = period
    if granularity == DAY:
        prefix = f"{year:04d}-{month:02d}"
        return prefix, prefix + "~"
    if granularity == WEEK:
        start, next_start = _quarter_bounds(year, month)
        return start.isoformat(), next_start.isoformat()
    return f"{year:04d}", f"{year:04d}~"


#: Mức gộp CHỨA cửa sổ hiển thị của mỗi mức mịn: Ngày khoanh trong một
#: THÁNG, Tuần khoanh trong một QUÝ, Tháng khoanh trong một NĂM.
_WINDOW_CONTAINER = {DAY: MONTH, WEEK: QUARTER, MONTH: YEAR}


def window_label(granularity: str, period: Optional[tuple[int, int]]) -> str:
    """Nhãn NGƯỜI ĐỌC của cửa sổ đang áp dụng ("09/2026", "Quý 3/2026",
    "Năm 2026"), hoặc chuỗi rỗng khi mức gộp này không bị khoanh."""
    if period is None or granularity not in _WINDOWED_LEVELS:
        return ""
    year, month = period
    return bucket_of(date(year, month, 1), _WINDOW_CONTAINER[granularity])[1]


def window_points(
    points: list[Point], *, granularity: str, period: Optional[tuple[int, int]],
) -> list[Point]:
    """Cắt `points` (đã tính ĐẦY ĐỦ, không đổi) về đúng cửa sổ hiển thị.

    Hàm THUẦN, tách khỏi `series()` một cách cố ý: `series()` vẫn luôn trả về
    TOÀN BỘ điểm của cả dòng thời gian — bất biến `Σ(mọi điểm của kỳ) ==
    totals.sales_revenue` và mọi kiểm chứng `DEC-166 E`/`F-N03` vẫn đúng trên
    chính danh sách đầy đủ đó, không phụ thuộc việc trang có vẽ hết hay không.
    `window_points` chỉ CHỌN một dải con liên tục của danh sách đã sắp sẵn để
    VẼ — không tính lại, không đổi origin, không đổi giá trị điểm nào.
    """
    bounds = window_bounds(granularity, period)
    if bounds is None:
        return points
    low, high = bounds
    return [point for point in points if low <= point.key < high]


def totals_of(points: Iterable[Point]) -> Decimal:
    """Tổng của một chuỗi — dùng để khẳng định bất biến gộp trong test."""
    return sum((point.revenue for point in points), Decimal(0))


__all__ = [
    "COMPARISON_LEVELS", "COMPARISON_NOTE", "COMPARISON_WINDOW_LABEL",
    "CONTAINER_OF", "CURRENT_WINDOW_LABEL", "GAP_NOTE",
    "GAPFILL_COUNT_CHART_NOTE", "PAD_KEY_PREFIX", "PairedSeries",
    "Projection", "Slot", "YEAR_WINDOW_SIZE", "anchor_date",
    "comparison_anchor", "container_bounds", "container_slots",
    "count_series", "paired_series", "paired_window_span", "project",
    "window_slots",
    "CHART_NOTE", "CHART_SCOPE_NOTE", "DAY", "DEFAULT_GRANULARITY",
    "GRANULARITIES", "GRANULARITY_KEYS", "LEGACY_POINT_NOTE",
    "GAPFILL_CHART_NOTE", "GAPFILL_POINT_NOTE", "MIXED_GAPFILL_POINT_NOTE",
    "MIXED_POINT_NOTE", "MONTH",
    "NO_DAILY_LEGACY_NOTE", "ORIGIN_CURRENT", "ORIGIN_GAPFILL",
    "ORIGIN_LEGACY", "ORIGIN_MIXED", "Point", "QUARTER", "WEEK", "YEAR",
    "bucket_of", "current_points", "parse_granularity", "series", "totals_of",
    "undated_count", "window_bounds", "window_label", "window_points",
]
