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

Một THÁNG đã có dòng pipeline thì lịch sử KHÔNG được chen vào đó — cùng thứ
tự thẩm quyền mà `_legacy_previous_month` đã dùng. Lịch sử chỉ điền vào
những tháng mà số mới hoàn toàn KHÔNG có dòng nào.

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
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Optional, Sequence

#: Origin của một điểm. Cùng từ vựng `DEC-166 E`, không phải một cặp nhãn mới.
ORIGIN_CURRENT = "PIPELINE_GENERATED"
ORIGIN_LEGACY = "LEGACY_REFERENCE"

#: Mốc THÔ (quý/năm, hoặc một tuần vắt qua hai tháng) gồm các tháng đã giải
#: về HAI origin khác nhau. Chỉ xuất hiện từ mức gộp lớn hơn tháng trở lên —
#: một mốc THÁNG không bao giờ mang giá trị này, vì thẩm quyền được giải đúng
#: ở mức đó (`§ Thẩm quyền được giải ở mức THÁNG`).
ORIGIN_MIXED = "MIXED_AUTHORITY"

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
                  "months": set(), "origin": ORIGIN_CURRENT})
        slot["revenue"] += Decimal(revenue)
        slot["months"].add((sale_date.year, sale_date.month))
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
                  "months": set(), "origin": ORIGIN_LEGACY})
        slot["revenue"] += Decimal(revenue)
        slot["months"].add((year, month))
    return buckets


def _legacy_day_points(
    legacy_days: Iterable[dict], granularity: str, taken: set[tuple[int, int]],
) -> dict[str, dict]:
    """Điểm mức Ngày/Tuần dựng từ bằng chứng TỪNG NGÀY của sổ cũ.

    Cùng luật "một kỳ một nguồn" ở độ mịn THÁNG: nếu tháng đó đã có dòng số
    mới thì cả tháng đó thuộc về số mới, không trộn từng ngày một. Trộn ở mức
    ngày sẽ tạo ra những tháng nửa nguồn này nửa nguồn kia mà không nhãn nào
    đọc được.
    """
    buckets: dict[str, dict] = {}
    for entry in legacy_days:
        year, month = int(entry["year"]), int(entry["month"])
        if (year, month) in taken:
            continue
        revenue = entry.get("sales_vnd")
        if revenue is None:
            continue
        try:
            when = date(year, month, int(entry["day"]))
        except ValueError:
            # Một ô ngày không hợp lệ trong sổ cũ là một khiếm khuyết đã biết
            # của nguồn (`DEC-166 E`: known defects ghi metadata, không sửa).
            # Bỏ qua đúng ô đó, không bịa một ngày thay thế.
            continue
        key, label = bucket_of(when, granularity)
        slot = buckets.setdefault(
            key, {"label": label, "revenue": Decimal(0),
                  "months": set(), "origin": ORIGIN_LEGACY})
        slot["revenue"] += Decimal(revenue)
        slot["months"].add((year, month))
    return buckets


def _merge_resolved(buckets: dict[str, dict], key: str, slot: dict) -> None:
    """Gộp một mốc lịch sử vào chuỗi — CỘNG, không loại bỏ. Sửa `F-C`.

    Phép cộng ở đây an toàn vì thẩm quyền ĐÃ được giải xong ở mức tháng
    trước khi hàm này chạy: `taken` đã loại khỏi `slot` mọi tháng mà sổ nạp
    có dòng, nên hai vế của phép cộng không bao giờ là hai nguồn của CÙNG
    một tháng — chúng là những tháng khác nhau của cùng một quý/năm/tuần.

    Bản cũ dùng `setdefault` ở đây và vì thế im lặng VỨT BỎ cả một mốc lịch
    sử mỗi khi nó rơi trúng khoá thô mà sổ nạp đã chiếm: một tháng 9 có sổ
    nạp làm bốc hơi tháng 7 và tháng 8 chỉ có sổ cũ (`§ Thẩm quyền được giải
    ở mức THÁNG`).
    """
    existing = buckets.get(key)
    if existing is None:
        buckets[key] = slot
        return
    overlap = existing["months"] & slot["months"]
    if overlap:
        # Không `assert`: một bất biến sổ sách không được biến mất khi ai đó
        # chạy Python với `-O`. Nếu điều này xảy ra, thứ tự thẩm quyền ở trên
        # đã hỏng và câu trả lời đúng là DỪNG, không phải một con số gấp đôi.
        raise ValueError(
            f"tháng {sorted(overlap)} nhận giá trị từ hai origin trong cùng "
            f"mốc {key!r} — thẩm quyền phải đã giải xong trước khi gộp "
            "(DEC-180 §9)")
    existing["revenue"] += slot["revenue"]
    existing["months"] |= slot["months"]
    if existing["origin"] != slot["origin"]:
        existing["origin"] = ORIGIN_MIXED


def series(
    details: Iterable[dict], *, granularity: str,
    legacy_months: Optional[Iterable[dict]] = None,
    legacy_days: Optional[Iterable[dict]] = None,
) -> list[Point]:
    """Chuỗi điểm đã sắp theo thời gian — bề mặt DUY NHẤT của biểu đồ.

    `legacy_months` là các bản ghi `{"year", "month", "sales_vnd"}` đã được
    tầng gọi giải về VND bằng thẩm quyền của `legacy_reference`; `legacy_days`
    là các dòng `legacy_daily_sales` (`{"year", "month", "day", "sales_vnd"}`,
    vốn đã là VND nguyên). Module này KHÔNG tự đổi đơn vị: quên hệ số 1.000
    một lần ở đây sẽ cho ra một đường cong trông như thật.
    """
    details = list(details)
    buckets = current_points(details, granularity)
    taken = {month for slot in buckets.values() for month in slot["months"]}

    if granularity in _DAY_LEVEL:
        legacy = _legacy_day_points(legacy_days or [], granularity, taken)
    else:
        legacy = _legacy_month_points(legacy_months or [], granularity, taken)
    for key, slot in legacy.items():
        _merge_resolved(buckets, key, slot)

    span = _MONTHS_IN_BUCKET.get(granularity)
    points = []
    for key in sorted(buckets):
        slot = buckets[key]
        points.append(Point(
            key=key, label=slot["label"], revenue=slot["revenue"],
            origin=slot["origin"],
            covered_months=None if span is None else len(slot["months"]),
            span_months=span,
        ))
    return points


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
COMPARISON_WINDOW_SIZES: dict[str, int] = {
    DAY: 30, WEEK: 12, MONTH: 12, QUARTER: 8,
}

#: Mức gộp có cửa sổ so sánh. Năm KHÔNG có: Owner không yêu cầu, và "8 năm so
#: với 8 năm trước" là một câu hỏi mà sổ này chưa có bằng chứng để trả lời.
COMPARISON_LEVELS: frozenset = frozenset(COMPARISON_WINDOW_SIZES)

CURRENT_WINDOW_LABEL = "Cửa sổ hiện tại"
COMPARISON_WINDOW_LABEL = "Cửa sổ so sánh (liền trước)"

COMPARISON_NOTE = (
    "Hai đường so HAI CỬA SỔ LIỀN KỀ có CÙNG độ dài: đường đậm là cửa sổ hiện "
    "tại, đường mờ là cửa sổ ngay trước nó. Chúng dùng CHUNG một trục và một "
    "thước đo, nên hai điểm cùng vị trí là hai mốc tương ứng của hai cửa sổ."
)

#: `F-E` ở chế độ hai cửa sổ — câu phải nói ĐÚNG phạm vi thật của biểu đồ.
#: `F-E` sinh ra để không cho hai con số cạnh nhau nói hai điều mâu thuẫn mà
#: không ai giải thích; cách giữ đúng tinh thần đó khi phạm vi đổi là ĐỔI CÂU
#: theo phạm vi mới, không phải xoá câu đi.
COMPARISON_SCOPE_TEXT = (
    "Biểu đồ so hai cửa sổ liền kề cùng độ dài: {current} so với "
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
    raise ValueError(f"Mức gộp không có cửa sổ so sánh: {granularity!r}")


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


def comparison_anchor(granularity: str, anchor: date, size: int) -> date:
    """Ngày neo của cửa sổ SO SÁNH — mốc ngay trước mốc đầu cửa sổ hiện tại."""
    return _step_back(granularity, anchor, size)


def anchor_date(
    period: Optional[tuple[int, int]], details: Iterable[dict],
) -> Optional[date]:
    """Mốc kết thúc của cửa sổ hiện tại.

    Đang xem một THÁNG ⟹ ngày cuối tháng đó: cửa sổ 30 ngày khi ấy phủ đúng
    tháng đang xem (với tháng 30 ngày), và người đọc thấy cái họ vừa chọn.

    Đang xem "Toàn bộ dữ liệu" ⟹ ngày bán MUỘN NHẤT thực sự có. Neo vào hôm
    nay thay vào đó sẽ vẽ ra một cửa sổ trống trơn mỗi khi sổ chưa được nạp
    vài ngày, và một biểu đồ trống đọc như "không bán được gì".

    `None` khi không có kỳ và cũng không có dòng nào — không có gì để neo.
    """
    if period is not None:
        year, month = period
        return date(year, month, monthrange(year, month)[1])
    dates = [detail["sale_date"] for detail in details
             if detail.get("sale_date") is not None]
    return max(dates) if dates else None


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

    @property
    def is_gap(self) -> bool:
        return self.revenue is None


@dataclass(frozen=True)
class PairedSeries:
    """Hai chuỗi cùng độ dài trên cùng một trục, và nhãn của chúng."""

    current: tuple[Slot, ...]
    comparison: tuple[Slot, ...]
    current_label: str
    comparison_label: str

    @property
    def size(self) -> int:
        return len(self.current)


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
    size = COMPARISON_WINDOW_SIZES.get(granularity)
    if size is None or anchor is None:
        return None
    current = window_slots(granularity, anchor, size)
    previous = window_slots(
        granularity, comparison_anchor(granularity, anchor, size), size)
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
    size = COMPARISON_WINDOW_SIZES.get(granularity)
    if size is None or anchor is None:
        return None
    by_key = {point.key: point for point in points}

    def slots_of(window_anchor: date) -> tuple[Slot, ...]:
        built = []
        for index, (key, label) in enumerate(
                window_slots(granularity, window_anchor, size)):
            point = by_key.get(key)
            if point is not None:
                built.append(Slot(index=index, key=key, label=label,
                                  revenue=point.revenue, origin=point.origin,
                                  partial=point.partial))
                continue
            # Không có điểm: số 0 CHỈ khi phạm vi đã được xác nhận đầy đủ,
            # tức hệ thống thật sự biết không có đơn nào. Mọi trường hợp còn
            # lại là một khoảng trống, và khoảng trống phải nhìn ra được.
            zero = _covered_by_confirmed(key, granularity, confirmed_ranges)
            built.append(Slot(index=index, key=key, label=label,
                              revenue=Decimal(0) if zero else None,
                              origin=ORIGIN_CURRENT if zero else None))
        return tuple(built)

    return PairedSeries(
        current=slots_of(anchor),
        comparison=slots_of(comparison_anchor(granularity, anchor, size)),
        current_label=CURRENT_WINDOW_LABEL,
        comparison_label=COMPARISON_WINDOW_LABEL,
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
    "COMPARISON_WINDOW_SIZES", "CURRENT_WINDOW_LABEL", "GAP_NOTE",
    "PairedSeries", "Slot", "anchor_date", "comparison_anchor",
    "paired_series", "paired_window_span", "window_slots",
    "CHART_NOTE", "CHART_SCOPE_NOTE", "DAY", "DEFAULT_GRANULARITY",
    "GRANULARITIES", "GRANULARITY_KEYS", "LEGACY_POINT_NOTE",
    "MIXED_POINT_NOTE", "MONTH", "NO_DAILY_LEGACY_NOTE", "ORIGIN_CURRENT",
    "ORIGIN_LEGACY", "ORIGIN_MIXED", "Point", "QUARTER", "WEEK", "YEAR",
    "bucket_of", "current_points", "parse_granularity", "series", "totals_of",
    "undated_count", "window_bounds", "window_label", "window_points",
]
