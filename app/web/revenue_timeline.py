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
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Optional

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
    "báo cáo. Mỗi mốc chỉ lấy từ MỘT nguồn: mốc nào đã có sổ nạp thì dùng sổ "
    "nạp, mốc chỉ còn bản ghi lịch sử thì dùng bản ghi lịch sử. Không mốc nào "
    "là hai nguồn cộng lại."
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


def parse_granularity(raw: Optional[str]) -> str:
    """Mức gộp đang chọn. Giá trị lạ rơi về mặc định, không báo lỗi.

    Một tham số URL gõ sai không đáng làm hỏng cả trang báo cáo; nhưng nó
    cũng không được âm thầm thành một mức gộp KHÁC cái người dùng gõ và trông
    như đã hiểu — nên mặc định là Tháng, và nút Tháng sẽ sáng lên đúng như
    trạng thái thật.
    """
    value = (raw or "").strip().lower()
    return value if value in GRANULARITY_KEYS else DEFAULT_GRANULARITY


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


def totals_of(points: Iterable[Point]) -> Decimal:
    """Tổng của một chuỗi — dùng để khẳng định bất biến gộp trong test."""
    return sum((point.revenue for point in points), Decimal(0))


__all__ = [
    "CHART_NOTE", "CHART_SCOPE_NOTE", "DAY", "DEFAULT_GRANULARITY",
    "GRANULARITIES", "GRANULARITY_KEYS", "LEGACY_POINT_NOTE",
    "MIXED_POINT_NOTE", "MONTH", "NO_DAILY_LEGACY_NOTE", "ORIGIN_CURRENT",
    "ORIGIN_LEGACY", "ORIGIN_MIXED", "Point", "QUARTER", "WEEK", "YEAR",
    "bucket_of", "current_points", "parse_granularity", "series", "totals_of",
    "undated_count",
]
