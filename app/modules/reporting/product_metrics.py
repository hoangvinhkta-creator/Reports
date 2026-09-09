"""R6 §3 — GỘP theo mặt hàng, nhóm hàng và hãng, cùng MỘT engine.

Module này THUẦN và cố ý KHÔNG biết ba chiều gộp ấy khác nhau ở đâu: nó nhận
một dãy `GroupBucket` ĐI SONG SONG với dãy dòng, rồi phân hoạch. Ai quyết định
một dòng thuộc bucket nào là việc của tầng trên (`app/web/product_taxonomy.py`),
và tách như vậy là điều kiện để ba chiều gộp không bao giờ cho ra ba phép cộng
tiền khác nhau.

Hình dạng này KHÔNG mới: `brand_metrics.group_by_brand` đã dựng đúng nó cho
`PHB-06` (hai dãy song song, lệch độ dài là LỖI CỨNG, hai bucket "chưa xác
định" xuống cuối, rồi một phép đối soát về tổng kỳ). R6 dùng lại đúng khuôn ấy
và thêm ĐÚNG những cột mà `BusinessTotals` không mang: số lượng, chiết khấu,
số đơn, tỉ trọng, giá bán bình quân gia quyền và min/max giá bán.

## Vì sao không nhồi các cột này vào `BusinessTotals`

`BusinessTotals` là bộ chỉ tiêu đã được nghiệm thu của `PHB-03`, và mọi trang
cũ đọc nó. Thêm sáu trường vào đó buộc mọi test nghiệp vụ cũ phải dựng dữ liệu
chúng không quan tâm, và — nặng hơn — nó đặt "giá bán bình quân" vào cùng một
value object với `official_kpi_profit`, tức mời một trang tương lai coi giá
bình quân là một con số CHÍNH THỨC chịu gate coverage 100 %. Nó không phải:
giá bình quân là một phép chia trên hai cột đã có, không phải một kết luận về
lợi nhuận.

## Giá bán bình quân — GIA QUYỀN, trên MỘT tập dòng duy nhất

```text
average_sell_price = Σ total_sales / Σ quantity   trên CÙNG tập dòng "đủ dữ liệu"
```

Repair `AR-R6-IR-03`. Trước repair, tử số loại các dòng thiếu `total_sales`
trong khi mẫu số vẫn cộng số lượng của chính những dòng ấy — hai vế của một
phép chia đọc hai tập dòng khác nhau:

```text
hai dòng, mỗi dòng 1 chiếc giá 10.000.000, MỘT dòng chưa có total_sales
  tử số  = 10.000.000     (một dòng)
  mẫu số = 2              (hai dòng)
  giá BQ = 5.000.000      ← thấp đúng một nửa giá duy nhất quan sát được
```

Nặng hơn con số: `dashboard_presentation.data_quality` in ra cho người đọc rằng
dòng chưa có doanh thu *"không được cộng như số 0 vào bất kỳ ô nào"* — và với
đúng ô này mệnh đề ấy đã SAI. Trang khẳng định một bất biến mà mã không giữ.

Tập "đủ dữ liệu" (`priced_lines`) là dòng HÀNG HOÁ có ĐỦ ba điều: `total_sales`
không `None`, `quantity` không `None`, và `quantity > 0`. Điều kiện thứ ba
không phải để làm đẹp: một dòng số lượng 0 mà có doanh thu sẽ góp vào tử số mà
không góp gì vào mẫu số, tức đẩy giá bình quân LÊN — cùng lớp lỗi, chiều ngược
lại.

`min`/`max` KHÔNG bị thu hẹp theo tập ấy: chúng đọc `sell_price` của mọi dòng
hàng hoá CÓ đơn giá. Một dòng chưa chốt doanh thu vẫn có một đơn giá quan sát
được, và "giá bán thấp nhất của nhóm" là một sự thật về ĐƠN GIÁ, không về doanh
thu. Hai câu hỏi khác nhau, hai tập dòng khác nhau — và đó là hợp đồng, không
phải một chỗ bỏ quên: `PriceStats` nói ra cả hai bằng hai nhóm trường riêng.

Chia tổng cho tổng, KHÔNG lấy trung bình của các đơn giá. Một bucket có một
dòng 1 chiếc giá 30 triệu và một dòng 100 chiếc giá 200 nghìn thì trung bình
đơn giá là 15,1 triệu — một con số không mô tả bất cứ thứ gì đã xảy ra. Phép
chia gia quyền cho ra 494 nghìn, tức số tiền trung bình thật trên mỗi chiếc.

Mẫu số bằng 0 ⟹ `None`, không phải `0`: chia cho 0 không có nghĩa, và một
`0 đồng/chiếc` in ra sẽ đọc thành "hàng này bán không lấy tiền". `average_reason`
đi kèm để trang nói ra VÌ SAO ô ấy trống, thay vì để người đọc tự đoán.

`FEE`/`DISCOUNT`/`RETURN_CANCEL`/`UNDECIDED_DOCUMENT` KHÔNG tham gia phép chia
(`dashboard_metrics.MERCHANDISE_TYPES` là tập duy nhất định nghĩa "hàng hoá").
Một bucket không có dòng hàng hoá nào vì thế có `average is None` và trang hiện
`—`. Doanh thu của nó KHÔNG bị bỏ đi — nó vẫn nằm trong `revenue` và vẫn phải
khớp khi đối soát, vì một khoản phí là tiền thật.

`dashboard_metrics.total_quantity` — tổng số lượng NGHIỆP VỤ của một bucket —
KHÔNG bị repair này chạm tới: nó vẫn đếm số lượng của MỌI dòng có số lượng, kể
cả dòng chưa chốt doanh thu. Thu hẹp nó theo tập tính giá sẽ làm tổng số lượng
của bảng thôi khớp với tổng của phạm vi, tức đánh đổi một phép đối soát để sửa
một phép chia.

## Giá 0 của hàng tặng là giá THẬT

`OD-4`. Một dòng `ACCESSORY_GIFT` giá 0 vẫn tham gia `min_sell_price`, nên
min của một bucket có hàng tặng là `0`. Đó là câu trả lời ĐÚNG cho "giá bán
thấp nhất của nhóm này": nó thật sự đã có một chiếc ra khỏi kho với giá 0. Lọc
nó ra để min "trông hợp lý" là sửa dữ liệu cho khớp trực giác.

Dòng KHÔNG có đơn giá (`sell_price is None`) thì không tham gia min/max — vắng
mặt khác 0, và một `None` kéo min xuống 0 sẽ bịa ra một lần bán giá 0 chưa hề
xảy ra.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Sequence

from app.modules.reporting import dashboard_metrics as dmx
from app.modules.reporting.business_metrics import BusinessLine, BusinessTotals
from app.modules.reporting.business_metrics import totals as business_totals
from app.modules.reporting.contribution import (
    share_percent as _contribution_share,
)

_CENT = Decimal("0.01")

#: Bucket CHÍNH DANH — nhãn đến từ hợp đồng metadata của Tracking.
KIND_KNOWN = "KNOWN"
#: Bucket "chưa xác định" — nhãn do Reports đặt, kèm LÝ DO riêng. Không bao giờ
#: gộp mọi lý do vào một ô: hai lý do khác nhau cần hai hành động khác nhau và
#: chỉ một trong hai sửa được từ trong Reports (`PHB-06 §10`).
KIND_UNDECIDED = "UNDECIDED"

KINDS: tuple[str, ...] = (KIND_KNOWN, KIND_UNDECIDED)


@dataclass(frozen=True)
class GroupBucket:
    """Ô mà MỘT dòng rơi vào trên một bảng gộp của R6.

    `key` là khoá phân hoạch, `label` là chữ hiện trên bảng, `kind` nói ô ấy
    có chính danh hay không, và `reason` nói VÌ SAO khi nó không chính danh.
    Bốn trường đi cùng nhau trong một value object vì tách chúng ra là cách
    một đường render mất chiều "chưa xác định vì sao".

    `sort_hint` là thứ tự CỐ ĐỊNH của các bucket "chưa xác định" ở cuối bảng —
    viết ra thay vì phụ thuộc thứ tự chèn của dict, cùng lý do mà
    `brand_metrics.UNKNOWN_ORDER` đã ghi: một bảng đổi thứ tự dòng giữa hai lần
    tải trang mà số không đổi làm người đọc mất niềm tin vào cả trang.
    """

    key: str
    label: str
    kind: str = KIND_KNOWN
    reason: Optional[str] = None
    sort_hint: int = 0

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("GroupBucket.key REQUIRED, không được rỗng")
        if self.kind not in KINDS:
            raise ValueError(f"kind ngoài tập đóng: {self.kind!r}")
        if self.kind == KIND_UNDECIDED and not self.reason:
            raise ValueError(
                "bucket UNDECIDED phải nói ra LÝ DO — một ô \"chưa xác định\" "
                "không kèm lý do là một ô người đọc không sửa được")

    @property
    def known(self) -> bool:
        return self.kind == KIND_KNOWN


#: Lý do một ô giá bình quân trống. Tập ĐÓNG, và mỗi giá trị là một câu người
#: đọc hành động được — không phải một mã lỗi.
NO_AVERAGE_NO_MERCHANDISE = "NO_MERCHANDISE"
NO_AVERAGE_NO_PRICED_LINE = "NO_PRICED_LINE"

AVERAGE_REASONS = {
    NO_AVERAGE_NO_MERCHANDISE: (
        "Nhóm này không có dòng hàng hoá nào (chỉ phí, chiết khấu, hoàn/hủy "
        "hoặc chứng từ chưa định nghĩa), nên không có giá bán hàng hoá để "
        "tính. Doanh thu của nhóm vẫn nằm đủ trong cột doanh thu."
    ),
    NO_AVERAGE_NO_PRICED_LINE: (
        "Nhóm này có dòng hàng hoá, nhưng chưa dòng nào có ĐỦ cả doanh thu và "
        "số lượng để tham gia phép chia. Ô trống ở đây nghĩa là CHƯA TÍNH "
        "ĐƯỢC, không phải bằng 0."
    ),
}


@dataclass(frozen=True)
class PriceStats:
    """Các con số về GIÁ BÁN của một bucket, trên dòng hàng hoá.

    Hai NHÓM trường, hai câu hỏi khác nhau, và chúng cố ý không dùng chung một
    tập dòng (xem đầu file):

    ```text
    priced_*            tập "đủ dữ liệu" — tử số VÀ mẫu số của giá bình quân
    minimum / maximum   mọi dòng hàng hoá CÓ đơn giá
    merchandise_lines   mọi dòng hàng hoá, để biết bucket có hàng hoá hay không
    ```

    `merchandise_lines == 0` ⟹ mọi con số là `None`, và trang hiện `—`. Đó là
    câu trả lời đúng cho một bucket chỉ gồm phí: nó không có giá bán hàng hoá
    nào, và in ra một con số ở đó là bịa.
    """

    merchandise_lines: int
    #: Số dòng hàng hoá CÓ ĐỦ doanh thu và số lượng hợp lệ — tập dùng cho CẢ
    #: tử số và mẫu số của `average` (repair `AR-R6-IR-03`).
    priced_lines: int
    priced_quantity: Decimal
    priced_revenue: Optional[Decimal]
    minimum: Optional[Decimal]
    maximum: Optional[Decimal]

    @property
    def average(self) -> Optional[Decimal]:
        """`Σ total_sales / Σ quantity` trên CÙNG tập dòng, hoặc `None`."""
        if self.priced_revenue is None or self.priced_quantity <= 0:
            return None
        return (Decimal(self.priced_revenue)
                / Decimal(self.priced_quantity)).quantize(
                    _CENT, rounding=ROUND_HALF_UP)

    @property
    def average_reason(self) -> Optional[str]:
        """VÌ SAO `average` là `None`, hoặc `None` khi nó có giá trị.

        `None`-vì-không-có-hàng-hoá và `None`-vì-chưa-đủ-dữ-liệu cần hai câu
        khác nhau: cái đầu là trạng thái ĐÚNG của một nhóm phí và không phải
        việc phải sửa, cái sau là một khoảng trống dữ liệu có chỗ sửa thật.
        """
        if self.average is not None:
            return None
        if self.merchandise_lines == 0:
            return AVERAGE_REASONS[NO_AVERAGE_NO_MERCHANDISE]
        return AVERAGE_REASONS[NO_AVERAGE_NO_PRICED_LINE]

    @property
    def has_merchandise(self) -> bool:
        return self.merchandise_lines > 0


def _priced(line: BusinessLine) -> bool:
    """Dòng này có ĐỦ dữ liệu để tham gia phép chia giá bình quân?

    Ba điều kiện, và cả ba đều cần (repair `AR-R6-IR-03`):

    ```text
    total_sales is not None   có tử số
    quantity is not None      có mẫu số
    quantity > 0              mẫu số dùng được — số lượng 0 góp tiền mà không
                              góp chiếc, tức đẩy giá bình quân LÊN
    ```
    """
    return (line.total_sales is not None and line.quantity is not None
            and Decimal(line.quantity) > 0)


def price_stats(lines: Sequence[BusinessLine]) -> PriceStats:
    """`PriceStats` của một tập dòng — CHỈ đọc dòng hàng hoá.

    Tử số và mẫu số của giá bình quân đọc CÙNG một danh sách `priced`, nên
    chúng không thể trôi khỏi nhau: thêm hay bớt một điều kiện ở `_priced` đổi
    cả hai vế cùng lúc.
    """
    merchandise = [line for line in lines
                   if line.line_type in dmx.MERCHANDISE_TYPES]
    prices = [Decimal(line.sell_price) for line in merchandise
              if line.sell_price is not None]
    priced = [line for line in merchandise if _priced(line)]
    revenues = [Decimal(line.total_sales) for line in priced]
    return PriceStats(
        merchandise_lines=len(merchandise),
        priced_lines=len(priced),
        priced_quantity=sum((Decimal(line.quantity) for line in priced),
                            Decimal(0)),
        priced_revenue=sum(revenues, Decimal(0)) if revenues else None,
        minimum=min(prices) if prices else None,
        maximum=max(prices) if prices else None,
    )


@dataclass(frozen=True)
class GroupRow:
    """Một hàng của bảng gộp — bucket + mọi chỉ tiêu của nó.

    `business` là `BusinessTotals` của ĐÚNG tập dòng trong bucket, tính bằng
    chính `business_metrics.totals`. Không cột tiền nào ở đây được tính bằng
    một công thức thứ hai: `revenue` đọc `business.sales_revenue`, và
    `dashboard` đọc `dashboard_metrics.totals` trên cùng tập dòng ấy.
    """

    bucket: GroupBucket
    business: BusinessTotals
    dashboard: dmx.DashboardTotals
    prices: PriceStats

    @property
    def revenue(self) -> Optional[Decimal]:
        return self.business.sales_revenue

    @property
    def quantity(self) -> Decimal:
        return self.dashboard.total_quantity

    @property
    def discount(self) -> Decimal:
        return self.dashboard.discount_total

    @property
    def orders(self) -> int:
        """Số đơn KHÁC NHAU có mặt trong bucket.

        Một đơn chứa hàng của hai bucket được đếm ở CẢ HAI — đúng sự thật
        nghiệp vụ, và đúng lý do `brand_metrics.BrandReconciliation` cố ý
        KHÔNG đối soát cột này (`R-E5`). Bảng phải nói ra điều đó thay vì để
        người đọc cộng cột số đơn và thấy nó vượt tổng kỳ.
        """
        return self.dashboard.orders

    @property
    def lines(self) -> int:
        return self.business.lines


def group_rows(
    lines: Sequence[BusinessLine], details: Sequence[dict],
    buckets: Sequence[GroupBucket],
) -> list[GroupRow]:
    """Phân hoạch theo `buckets`, sắp doanh thu giảm dần, "chưa xác định" CUỐI.

    Ba dãy ĐI SONG SONG. Độ dài lệch nhau là LỖI CỨNG, không phải một lần
    `zip` cắt ngắn im lặng: cắt ngắn ở đây nghĩa là một số dòng biến mất khỏi
    mọi bucket trong khi hàng tổng vẫn trông hợp lệ — đúng lớp lỗi mà
    `reconciliation()` được dựng để bắt, nên nó không được phép xảy ra ở tầng
    dưới nó.

    `details` cần có mặt vì `dashboard_metrics` đếm đơn theo `order_key` và
    `sale_date`, hai thứ nằm trên `details` chứ không trên `BusinessLine` (xem
    `business_queries.line_details`).
    """
    if not (len(lines) == len(details) == len(buckets)):
        raise ValueError(
            f"lines ({len(lines)}), details ({len(details)}) và buckets "
            f"({len(buckets)}) phải cùng độ dài — mỗi dòng đúng một bucket, "
            "không dòng nào rơi ra ngoài")
    grouped: dict[str, tuple[GroupBucket, list[BusinessLine], list[dict]]] = {}
    for line, detail, bucket in zip(lines, details, buckets):
        _, members, member_details = grouped.setdefault(
            bucket.key, (bucket, [], []))
        members.append(line)
        member_details.append(detail)
    rows = [
        GroupRow(bucket=bucket, business=business_totals(members),
                 dashboard=dmx.totals(member_details),
                 prices=price_stats(members))
        for bucket, members, member_details in grouped.values()
    ]
    rows.sort(key=lambda row: (
        0 if row.bucket.known else 1,
        row.bucket.sort_hint if not row.bucket.known else 0,
        -(row.revenue or Decimal(0)),
        row.bucket.key,
    ))
    return rows


def share_percent(part: Optional[Decimal],
                  whole: Optional[Decimal]) -> Optional[Decimal]:
    """Tỉ trọng doanh thu của một bucket.

    Uỷ quyền cho `contribution.share_percent` chứ không viết lại phép chia:
    một bản sao thứ hai sẽ làm tròn khác đi ở đúng những chỗ khó nhất, và hai
    trang cùng dự án sẽ hiện hai tỉ trọng cho cùng một bucket.
    """
    return _contribution_share(part, whole)


@dataclass(frozen=True)
class GroupReconciliation:
    """Đối soát bảng gộp về tổng của CHÍNH lát dữ liệu.

    Phép so là BẰNG ĐÚNG trên `Decimal`, không phải "gần bằng" — cùng lý do mà
    `brand_metrics.reconciliation` đã ghi: một ngưỡng dung sai ở đây sẽ giấu
    đúng loại lỗi mà hàm này tồn tại để bắt, tức một dòng bị bỏ rơi hoặc bị
    đếm hai lần.

    `orders` cố ý VẮNG MẶT — xem `GroupRow.orders`.
    """

    lines: bool
    sales_revenue: bool
    quantity: bool
    discount: bool

    @property
    def is_exact(self) -> bool:
        return all((self.lines, self.sales_revenue, self.quantity,
                    self.discount))


def reconciliation(rows: Sequence[GroupRow],
                   company: dmx.DashboardTotals) -> GroupReconciliation:
    """So từng chỉ tiêu CỘNG ĐƯỢC của bảng với tổng của cả lát dữ liệu.

    `company` phải là `dashboard_metrics.totals` của CHÍNH lát đã sinh ra
    `rows` — truy trực tiếp từ lát dữ liệu, không cộng lại từ các hàng đang
    hiển thị (`R6 §1`). Đó là toàn bộ giá trị của phép đối soát này: hai đường
    tính độc lập gặp nhau ở cùng một con số.
    """
    return GroupReconciliation(
        lines=sum(row.lines for row in rows) == company.lines,
        sales_revenue=dmx.sum_optional(row.revenue for row in rows)
        == company.sales_revenue,
        quantity=sum((row.quantity for row in rows), Decimal(0))
        == company.total_quantity,
        discount=sum((row.discount for row in rows), Decimal(0))
        == company.discount_total,
    )


__all__ = [
    "AVERAGE_REASONS", "GroupBucket", "GroupReconciliation", "GroupRow",
    "KINDS", "KIND_KNOWN", "KIND_UNDECIDED", "NO_AVERAGE_NO_MERCHANDISE",
    "NO_AVERAGE_NO_PRICED_LINE", "PriceStats", "group_rows", "price_stats",
    "reconciliation", "share_percent",
]
