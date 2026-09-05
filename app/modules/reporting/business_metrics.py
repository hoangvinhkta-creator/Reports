"""PHB-03 — ngữ nghĩa nghiệp vụ đã freeze của Summary + Employee V1.

Module này THUẦN: không SQL, không Flask, không I/O. Nó nhận các dòng hàng đã
được tầng truy vấn đọc ra và trả về đúng những chỉ tiêu mà
`docs/tasks/PHB-02-business-parity-contract.md` mục 10 đã freeze. Tách ra như
vậy vì mọi vector nghiệm thu của PHB-03 (`1.000.000 / 7,5 % ≈ 13.333.333,33`
…) là mệnh đề về NGỮ NGHĨA, không phải về HTML — chúng phải kiểm được mà
không dựng database hay browser.

Sáu chỉ tiêu, mỗi cái chỉ tới đúng một quyết định Owner:

    Doanh thu bán hàng      DEC-114 — `Σ(sell_price × quantity − discount)`,
                            đọc thẳng `total_sales` mà pipeline đã ghi
    Số đơn                  M1 — `COUNT DISTINCT order_key`
    Tổng số SP              DEC-PHB02-03 — `SUM(quantity)` khi ĐƠN GIÁ BÁN
                            > 1.000.000 VND
    Lợi nhuận KPI           DEC-143 + gate 100 % của DEC-PHB02-02
    DS quy đổi              DEC-PHB02-04 (CHIA) + DEC-PHB02-05 (ma trận tỉ lệ)
    So tháng trước          DEC-PHB02-07 — % thay đổi DOANH THU BÁN HÀNG

## PROFIT_COVERAGE — vì sao tử số đúng bằng tập được cộng

`DEC-PHB02-02` §4 chỉ chấp nhận một mốc: **100 %**, và cấm phát minh ngưỡng
khác. Nhưng "100 % của cái gì" phải nói ra, nếu không con số "chính thức" vẫn
có thể bỏ sót dòng trong im lặng. Ở đây coverage được định nghĩa để KHÔNG thể
nói dối:

    PROFIT_COVERAGE = (số dòng THỰC SỰ góp một giá trị lợi nhuận KPI)
                    / (tổng số dòng hiện hành của kỳ)

Tử số đúng bằng tập dòng nằm trong tổng lợi nhuận. Vì vậy `coverage = 100 %`
tương đương "mọi dòng của kỳ đều đã có mặt trong con số này" — đó chính là
điều kiện để gọi nó là CHÍNH THỨC, không phải một cách viết khác của nó.

Một dòng góp giá trị khi `profit_gate.profit_blockers()` trả về tập RỖNG —
nghĩa là có giá bán, có số lượng dương, có giá nhập hiệu lực, và thẩm quyền
KPI đọc được. **Không vế nào đọc `status`** (`OD-6`): `status` chỉ là kết quả
cộng dồn 19 mã lý do rất khác nhau, và bản audit đã chứng minh không mã nào
trong đó là lý do kinh tế một khi các đầu vào trên đã đủ.

Coverage KHÔNG còn là một con số gộp. Nó tách ra đúng những nhóm dẫn tới
những hành động KHÁC NHAU của Owner (B02/B03):

    missing_price_lines     dòng chưa có giá nhập — gõ một con số là xong
    owner_fixable_lines     dòng mà giá nhập là cửa chặn DUY NHẤT còn lại
    blocked_lines           mã chặn → số dòng, để Owner biết sửa ở đâu
    unresolved_employee_lines   dòng tính được lãi nhưng chưa biết của ai

Gộp chúng lại là quay về đúng cái đã sai: một con số nói "còn thiếu" mà không
nói thiếu cái gì, và một ô đếm `missing_price_lines` luôn bằng 0 theo cấu tạo
vì nó hỏi `status == "AUTO"` — điều kiện mà một dòng thiếu giá không bao giờ
thoả.

## Lợi nhuận công ty và KPI nhân viên là HAI câu hỏi (OD-5)

    A. Dòng này lãi bao nhiêu?          → `kpi_profit`
    B. Khoản lãi đó của ai?             → `employee_attributed_profit`

Trước bản sửa này, không trả lời được câu B thì câu A cũng mất luôn con số.
Nay một dòng chưa biết ai bán VẪN vào tổng lợi nhuận của kỳ, và hiện riêng
dưới nhóm "Chưa xác định nhân viên" — hai con số cộng lại luôn đúng bằng
tổng, nên không đồng nào biến mất không dấu vết.

## DS quy đổi — chia theo TỪNG DÒNG, không bao giờ một tỉ lệ pha trộn

`R-E6`: `CONVERTED_SALES = EligibleKpiProfit ÷ rate`. Tỉ lệ thay đổi ngay
BÊN TRONG một nhân viên (một dòng Gia dụng của Vinh là 8 %, dòng Điện máy kế
bên là 2 %), nên phép chia phải xảy ra ở cấp dòng rồi mới cộng. Chia tổng lợi
nhuận cho một tỉ lệ trung bình là đúng cái sai mà `R-E6` gọi tên.

`profit × rate` là công thức SAI và không tồn tại ở bất kỳ đâu trong file này.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.modules.reporting import profit_gate

# `DEC-PHB02-03` — ngưỡng GIÁ, cố ý không phải một taxonomy sản phẩm. Hệ quả
# đã được Owner chấp nhận tường minh (`FIND-PHB02-N08`): vài sản phẩm thật giá
# thấp cũng bị loại. Đó là đánh đổi có chủ đích, không phải defect.
QUALIFYING_SALE_PRICE_THRESHOLD = Decimal("1000000")

# Provenance của giá nhập KPI dùng cho báo cáo (`DEC-PHB02-02` §3).
PROVENANCE_AUTO = "AUTO"
PROVENANCE_MANUAL = "MANUAL"
PROVENANCE_MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
PROVENANCE_PENDING = "PENDING"

# Khoá của nhóm "chưa xác định nhân viên" trong mọi phân hoạch theo người.
# `None`, không phải chuỗi rỗng: một chuỗi rỗng ngồi cạnh các tên thật trong
# cùng một cột trông như một nhân viên tên là "" (`R-E4`).
UNRESOLVED_EMPLOYEE = None

# `R-S7`/`R-E8`: hai trạng thái, không có trạng thái thứ ba "gần đủ".
STATE_OFFICIAL = "OFFICIAL"
STATE_INCOMPLETE = "INCOMPLETE"

# Đơn vị tiền nhỏ nhất mà DS quy đổi được viết ra. `1.000.000 / 7,5 %` là một
# số thập phân vô hạn tuần hoàn; vector nghiệm thu của `DEC-PHB02-05` viết nó
# là `13.333.333,33`, nên hai chữ số thập phân là hợp đồng, không phải sở thích.
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class BusinessLine:
    """Một dòng hàng hiện hành, đã hợp nhất quyết định của Owner.

    Đây là RANH GIỚI giữa tầng truy vấn và ngữ nghĩa nghiệp vụ: mọi trường ở
    đây là giá trị thuần, nên toàn bộ mục 8 của PHB-03 kiểm được bằng cách
    dựng dataclass này bằng tay.
    """

    order_key: str
    employee: Optional[str]
    employee_group: Optional[str]
    status: str
    sell_price: Optional[Decimal]
    quantity: Optional[Decimal]
    discount: Decimal
    total_sales: Optional[Decimal]
    # Giá nhập KPI do pipeline phân giải (`None` = chưa phân giải được).
    auto_purchase_price: Optional[Decimal]
    # Lợi nhuận KPI do pipeline tính, dùng NGUYÊN VẸN khi không có override.
    auto_kpi_profit: Optional[Decimal]
    # `DEC-143` §1 — thẩm quyền `config/eligible_costs.yaml` có đọc được không.
    # KHÔNG có giá trị mặc định: mặc định `True` là fail-OPEN, và cái van này
    # tồn tại chính để fail-CLOSED. Mọi nơi dựng một dòng phải nói ra nó.
    kpi_authority_valid: bool
    # Giá nhập do Owner nhập/ghi đè, `None` = Owner chưa động vào dòng này.
    manual_purchase_price: Optional[Decimal] = None
    manual_provenance: Optional[str] = None
    # Tỉ lệ quy đổi hiệu lực của dòng (đã tính cả tick Gia dụng nếu có).
    conversion_rate: Optional[Decimal] = None
    # Mã lý do pipeline đã lưu (`pending_reasons_json`). Dùng để CẢNH BÁO và
    # để hiển thị; KHÔNG có vế nào của cửa chặn lợi nhuận đọc trường này.
    pending_reasons: tuple[str, ...] = ()
    # Tên nhân viên NGUYÊN BẢN của pipeline, giữ lại kể cả sau khi Owner sửa —
    # bằng chứng kế toán gốc không bị ghi đè (`OD-5`).
    source_employee: Optional[str] = None
    # `SOURCE` = do pipeline gán · `MANUAL` = do Owner phân loại lại.
    employee_provenance: str = "SOURCE"

    @property
    def purchase_price(self) -> Optional[Decimal]:
        """Giá nhập KPI HIỆU LỰC: quyết định của người thắng giá trị tự động."""
        if self.manual_purchase_price is not None:
            return self.manual_purchase_price
        return self.auto_purchase_price

    @property
    def purchase_provenance(self) -> str:
        """`AUTO` | `MANUAL` | `MANUAL_OVERRIDE` | `PENDING`.

        `DEC-PHB02-02` §3 cấm âm thầm coi một override là AUTO, nên provenance
        do người nhập luôn thắng — kể cả khi giá trị nhập bằng đúng giá AUTO.
        """
        if self.manual_purchase_price is not None:
            return self.manual_provenance or PROVENANCE_MANUAL
        if self.auto_purchase_price is not None:
            return PROVENANCE_AUTO
        return PROVENANCE_PENDING

    @property
    def profit_blockers(self) -> tuple[str, ...]:
        """Lý do THẬT khiến dòng chưa chốt được lợi nhuận (rỗng = tính được).

        Đây là cửa chặn duy nhất. Nó hỏi về giá bán, số lượng, giá nhập và
        thẩm quyền KPI — bốn đại lượng của công thức đã freeze — chứ KHÔNG hỏi
        `status`. `OD-6`: một trạng thái "cần kiểm tra" chung chung tự nó
        không phải lý do đủ để từ chối tính lợi nhuận.
        """
        return profit_gate.profit_blockers(
            sell_price=self.sell_price,
            quantity=self.quantity,
            purchase_price=self.purchase_price,
            kpi_authority_valid=self.kpi_authority_valid,
        )

    @property
    def kpi_profit(self) -> Optional[Decimal]:
        """`EligibleKpiProfit` hiệu lực của dòng — `None` = chưa xác định.

        Bất biến của hàm này, và là thứ giữ cho coverage không nói dối:

            `profit_blockers` rỗng  ⟺  `kpi_profit` KHÁC `None`

        Có cửa chặn ⟹ `None`, và cửa chặn đó có tên để Owner đọc.

        Không cửa chặn nào, và Owner chưa động vào dòng, và pipeline đã ghi
        một con số ⟹ dùng NGUYÊN con số đó. Đây là mặc định tôn trọng engine.

        Còn lại ⟹ áp đúng công thức đã freeze của `DEC-143`/`OD-108B-01` lên
        các đầu vào HIỆN TẠI (`FIND-PHB02-N06`):

            (SellPrice − KpiPurchasePrice) × Quantity − Discount

        Nhánh cuối này phủ hai tình huống, và cả hai đều bắt buộc:

        1. Owner đã nhập/sửa giá nhập — giá mới phải có hiệu lực kinh tế thật,
           đó là toàn bộ lý do luồng nhập giá tồn tại (`B01`).
        2. Pipeline trả `None` trong khi hôm nay mọi đầu vào đã đủ (ví dụ hôm
           chạy máy thẩm quyền KPI đang hỏng, nay đã sửa). Không tính ở đây
           thì dòng đó vĩnh viễn không có số MÀ KHÔNG có cửa chặn nào mang
           tên — đúng kiểu "thiếu trong im lặng" mà bất biến trên cấm.

        `EligibleCosts = {}` (tập rỗng có thẩm quyền) và
        `OtherKpiAdjustment = 0` nên hai số hạng đó vắng mặt — không phải bị
        bỏ quên. Van fail-closed của `DEC-143` §1 nằm ở `profit_blockers`:
        thẩm quyền hỏng thì không nhánh nào dưới đây chạy tới.
        """
        if self.profit_blockers:
            return None
        if self.manual_purchase_price is None and self.auto_kpi_profit is not None:
            return self.auto_kpi_profit
        return ((self.sell_price - self.purchase_price) * self.quantity
                - self.discount)

    @property
    def warnings(self) -> tuple[str, ...]:
        """Điều Owner NÊN BIẾT về dòng này. Không điều nào làm mất con số."""
        codes = list(profit_gate.profit_warnings(
            sell_price=self.sell_price,
            purchase_price=self.purchase_price,
            profit=self.kpi_profit,
            pending_reasons=self.pending_reasons,
        ))
        if not self.employee_resolved:
            codes.append(profit_gate.BLOCK_EMPLOYEE_UNRESOLVED)
        return tuple(codes)

    @property
    def employee_resolved(self) -> bool:
        """Đã biết chắc dòng này của ai chưa? (`OD-5`)

        Chuỗi rỗng và `None` là CÙNG một tình trạng nghiệp vụ. Một tên đã có
        mặt ở đây nghĩa là pipeline map được, hoặc Owner đã đích thân gán —
        cả hai đều là một khẳng định về quyền sở hữu, đủ để cộng KPI.
        """
        return bool(self.employee)

    @property
    def employee_kpi_profit(self) -> Optional[Decimal]:
        """Lợi nhuận được cộng vào KPI CỦA MỘT NGƯỜI — `None` khi chưa rõ ai.

        Tách khỏi `kpi_profit` là toàn bộ nội dung `OD-5`: dòng chưa biết ai
        bán vẫn vào tổng công ty, nhưng chưa vào bảng lương của ai.
        """
        return self.kpi_profit if self.employee_resolved else None

    @property
    def qualifying_quantity(self) -> Decimal:
        """`DEC-PHB02-03` — số lượng của dòng, chỉ khi ĐƠN GIÁ > 1.000.000.

        So sánh trên `sell_price` (đơn giá), đúng cách đọc canonical đã đo ở
        mục 4.6 của hợp đồng. Ngưỡng là `>` chứ không phải `>=`: Owner viết
        "giá bán sản phẩm > 1.000.000 VND", và một dòng đúng 1.000.000 nằm ở
        phía BỊ LOẠI.
        """
        if self.sell_price is None or self.quantity is None:
            return Decimal(0)
        if self.sell_price <= QUALIFYING_SALE_PRICE_THRESHOLD:
            return Decimal(0)
        return self.quantity

    @property
    def converted_sales(self) -> Optional[Decimal]:
        """`R-E6` — lợi nhuận KPI của dòng CHIA cho tỉ lệ của chính dòng đó."""
        return converted_sales(self.kpi_profit, self.conversion_rate)

    @property
    def contributes_profit(self) -> bool:
        return self.kpi_profit is not None

    @property
    def blocked_by_missing_price(self) -> bool:
        """Dòng chưa có giá nhập hiệu lực — bất kể pipeline dán nhãn gì.

        `B02` — định nghĩa cũ hỏi thêm `status == "AUTO"`, mà một dòng thiếu
        giá nhập thì luôn mang `Missing.PurchasePrice` nên `status` của nó
        luôn là `PENDING`. Ô đếm đó vì vậy LUÔN bằng 0 theo cấu tạo, và toàn
        bộ số dòng thiếu bị dồn sang ô "nhập giá không cứu được" — màn hình
        nói với Owner điều ngược lại sự thật.
        """
        return self.purchase_price is None

    @property
    def owner_fixable(self) -> bool:
        """Gõ một con số giá nhập vào là dòng này có lợi nhuận ngay.

        Đây là con số Owner hành động được. Một dòng vừa thiếu giá nhập vừa
        có số lượng 0 KHÔNG nằm ở đây — hứa rằng nhập giá là xong với dòng đó
        chính là lời hứa sai mà `B03` gọi tên.
        """
        return set(self.profit_blockers) == set(
            profit_gate.OWNER_FIXABLE_BLOCKERS)


# --------------------------------------------------------------------------
# S121 — PHÂN RÃ HIỂN THỊ CHIẾT KHẤU (`DEC-180`).
#
# Sổ tay cũ ghi chiết khấu bằng MỘT DÒNG ÂM đứng ngay sau dòng hàng:
#
#     Tủ lạnh   SL 1   giá bán 5.000.000   Tổng bán  5.000.000
#     Chiết khấu SL 1  giá bán 0           Tổng bán   -100.000
#     ------------------------------------------------------
#                                          còn lại  4.900.000
#
# Sổ kế toán hiện hành ghi cùng nghiệp vụ đó bằng MỘT CỘT `discount`, và
# pipeline đã trừ nó rồi: `total_sales` và `eligible_kpi_profit` là số NET
# (`DEC-114`, `DEC-143`). Hai cách GHI, một nghiệp vụ.
#
# Vì vậy phần dưới đây KHÔNG trừ thêm lần nào. Nó CHIA con số canonical đã có
# thành hai phần cộng lại đúng bằng chính nó:
#
#     canonical  =  (canonical + discount)  +  (− discount)
#                    └── dòng sản phẩm ──┘     └─ dòng "Chiết khấu" ─┘
#
# Đó là toàn bộ khác biệt giữa bản sửa này và một lỗi trừ-hai-lần: một bên
# tách một con số làm hai, một bên cộng thêm một số hạng mới. Bất biến
# `Σ(hiển thị) == canonical` được `totals()` giữ nguyên vì `totals()` KHÔNG
# đọc phần này — nó vẫn cộng trên `BusinessLine`, một dòng một lần.
#
# DS quy đổi là chỗ DUY NHẤT có làm tròn, nên nó cần một quy ước để bất biến
# đúng TUYỆT ĐỐI chứ không "xấp xỉ": phần chiết khấu tính bằng ĐÚNG công thức
# và ĐÚNG tỉ lệ của dòng cha (`converted_sales(−discount, rate)`), còn dòng
# sản phẩm nhận phần CÒN LẠI. Chênh lệch làm tròn (tối đa 0,01 VND) vì thế
# nằm ở dòng cha thay vì rơi ra ngoài tổng.
# --------------------------------------------------------------------------

# Dòng hiển thị này KHÔNG phải một mặt hàng: nó không có `product_key`, không
# vào Product Identity, không tra giá nhập, không đếm vào số đơn hay số SP.
DISCOUNT_DISPLAY_LABEL = "Chiết khấu"
DISCOUNT_DISPLAY_QUANTITY = Decimal(1)
DISCOUNT_DISPLAY_SELL_PRICE = Decimal(0)

CONTRIBUTION_PRODUCT = "PRODUCT"
CONTRIBUTION_DISCOUNT = "DISCOUNT"


@dataclass(frozen=True)
class LineContribution:
    """Một DÒNG BẢNG của bảng kê — không phải một dòng hàng của sổ.

    Một `BusinessLine` sinh ra một `LineContribution` khi không có chiết khấu,
    và HAI khi có. Không cấu trúc nào ở đây được lưu xuống database: đây là
    mô hình đọc, dựng lại từ đầu mỗi lần tải trang.
    """

    kind: str
    quantity: Optional[Decimal]
    sell_price: Optional[Decimal]
    purchase_price: Optional[Decimal]
    total_sales: Optional[Decimal]
    kpi_profit: Optional[Decimal]
    converted_sales: Optional[Decimal]


def _plus(value: Optional[Decimal], addend: Decimal) -> Optional[Decimal]:
    """`None + x = None` — "chưa xác định" cộng gì cũng vẫn chưa xác định."""
    return None if value is None else Decimal(value) + addend


def display_contributions(line: BusinessLine) -> tuple[LineContribution, ...]:
    """Các dòng bảng của MỘT dòng hàng, theo cách trình bày của sổ tay cũ.

    Bất biến, đúng với mọi `line` (kể cả dòng chưa tính được lợi nhuận):

        Σ total_sales     == line.total_sales
        Σ kpi_profit      == line.kpi_profit
        Σ converted_sales == line.converted_sales

    với quy ước `None` là "chưa xác định" và không tham gia phép cộng. Khi
    dòng cha chưa có một chỉ tiêu nào đó, dòng "Chiết khấu" cũng KHÔNG có —
    nếu không, một dòng bị chặn lợi nhuận sẽ đẻ ra `−discount` từ hư không và
    tổng hiển thị vượt khỏi tổng canonical.
    """
    canonical_profit = line.kpi_profit
    canonical_converted = line.converted_sales

    def _product(total_sales, kpi_profit, converted) -> LineContribution:
        """Dòng sản phẩm — cùng nhận diện hàng hoá, khác nhau ở ba ô tiền."""
        return LineContribution(
            kind=CONTRIBUTION_PRODUCT,
            quantity=line.quantity,
            sell_price=line.sell_price,
            purchase_price=line.purchase_price,
            total_sales=total_sales,
            kpi_profit=kpi_profit,
            converted_sales=converted,
        )

    # `discount <= 0` gộp cả hai ca "không có gì để tách": không chiết khấu,
    # và một giá trị âm bất thường trong dữ liệu (nó sẽ sinh ra một dòng
    # "Chiết khấu" mang số DƯƠNG — vô nghĩa, nên không sinh dòng nào).
    discount = Decimal(line.discount or 0)
    if discount <= 0:
        return (_product(line.total_sales, canonical_profit, canonical_converted),)

    if canonical_converted is None:
        discount_converted = None
        product_converted = None
    else:
        # Cùng tỉ lệ, cùng phép chia, cùng cách làm tròn với dòng cha; dòng
        # cha nhận phần CÒN LẠI nên tổng khớp tuyệt đối, không "xấp xỉ".
        discount_converted = converted_sales(-discount, line.conversion_rate)
        product_converted = Decimal(canonical_converted) - discount_converted

    return (
        _product(_plus(line.total_sales, discount),
                 _plus(canonical_profit, discount),
                 product_converted),
        LineContribution(
            kind=CONTRIBUTION_DISCOUNT,
            quantity=DISCOUNT_DISPLAY_QUANTITY,
            sell_price=DISCOUNT_DISPLAY_SELL_PRICE,
            # Cột "Giá nhập KPI" của dòng chiết khấu mang CHÍNH số tiền chiết
            # khấu, đúng cách sổ tay cũ ghi. Nó KHÔNG phải một giá nhập tra
            # được, nên không dòng nào ở đây là "chưa có giá nhập".
            purchase_price=discount,
            total_sales=None if line.total_sales is None else -discount,
            kpi_profit=None if canonical_profit is None else -discount,
            converted_sales=discount_converted,
        ),
    )


def converted_sales(
    profit: Optional[Decimal], rate: Optional[Decimal]
) -> Optional[Decimal]:
    """`CONVERTED_SALES = profit / rate`, làm tròn tới 0,01 VND.

    `DEC-PHB02-04` viết hoa dòng "TUYỆT ĐỐI KHÔNG implement profit * rate".
    Phép chia ở đây là toàn bộ lý do hàm này tồn tại riêng thay vì nằm inline.

    `rate = 0` trả `None` chứ không raise: một tỉ lệ 0 trong cấu hình là lỗi
    cấu hình, và một trang báo cáo không được sập vì nó — nhưng cũng không
    được in ra một con số vô nghĩa.
    """
    if profit is None or rate is None or rate == 0:
        return None
    return (Decimal(profit) / Decimal(rate)).quantize(_CENT, rounding=ROUND_HALF_UP)


# `PHB-05` — ba lý do KHÁC NHAU khiến "So target" không có số. Chúng không
# được gộp: mỗi lý do dẫn tới một câu khác nhau và một việc khác nhau cho
# Owner (đặt target · sửa target · hoàn thiện giá nhập).
TARGET_UNSET = "TARGET_UNSET"      # Owner CHƯA đặt target cho người này/kỳ này
TARGET_ZERO = "TARGET_ZERO"        # Owner ĐÃ đặt target, và đặt bằng 0
TARGET_NO_ACTUAL = "TARGET_NO_ACTUAL"  # chưa có DS quy đổi nào để so


def vs_target_percent(
    converted: Optional[Decimal], target: Optional[Decimal]
) -> Optional[Decimal]:
    """`So target % = DS quy đổi / Target × 100`, hoặc `None`.

    ## Vì sao là DS QUY ĐỔI, không phải Doanh thu bán hàng

    Đây là công thức của chính sổ cũ, đọc từ ô chứ không đoán từ tên cột:
    `Summary 2026!N4 = IFERROR(F4/M4,"")`, trong đó `F` là **Doanh thu quy
    đổi** (`F4 = G4/5.5%`) và `M` là Target
    (`docs/analysis/02_FORMULA_MAPPING.md` §3, `03_RULE_CLASSIFICATION.md`:
    `PercentTarget = TotalConvertedRevenue / Target` ⟷ `N = F/M`). Thay `F`
    bằng Tổng bán (`E`) sẽ cho ra một tỉ lệ lớn hơn nhiều lần và không còn là
    chỉ tiêu mà Owner đã dùng để đánh giá nhân viên.

    ## Ba nhánh `None`, và không nhánh nào in ra một con số

    `IFERROR(...,"")` của sổ cũ để TRỐNG khi `M` rỗng hoặc bằng 0 — nó không
    viết `0 %`, và không cap ở `100 %`. Ở đây giữ đúng như vậy:

        target is None ⟹ chưa thiết lập     ⟹ `None`
        target == 0    ⟹ không chia được    ⟹ `None`
        converted is None ⟹ chưa có số để so ⟹ `None`

    Vượt target thì trả về đúng số vượt (`120 %`): cap ở `100 %` là bịa một
    trần không có trong sổ và làm mất chính thông tin Owner cần.

    Hàm này KHÔNG đọc trạng thái CHÍNH THỨC/CHƯA HOÀN CHỈNH và không quyết
    định gì về nó: nó nhận vào một con số DS quy đổi, và con số đó mang trạng
    thái nào thì "So target" thừa hưởng đúng trạng thái ấy (PHB-05 §9). Việc
    dán nhãn là của tầng trình bày, nơi nhãn đó đã tồn tại — PHB-05 không
    dựng hệ trạng thái thứ hai.
    """
    if converted is None or target is None or target == 0:
        return None
    return (Decimal(converted) / Decimal(target)
            * Decimal(100)).quantize(_CENT, rounding=ROUND_HALF_UP)


def vs_target_reason(
    converted: Optional[Decimal], target: Optional[Decimal]
) -> Optional[str]:
    """Mã lý do khi `vs_target_percent` không có số; `None` khi có số.

    Thứ tự kiểm CÓ Ý NGHĨA: "chưa đặt target" được nói trước "chưa có DS quy
    đổi", vì đặt target là việc Owner làm được ngay, còn DS quy đổi phụ thuộc
    việc hoàn thiện giá nhập.
    """
    if target is None:
        return TARGET_UNSET
    if target == 0:
        return TARGET_ZERO
    if converted is None:
        return TARGET_NO_ACTUAL
    return None


def month_over_month_percent(
    current: Optional[Decimal], previous: Optional[Decimal]
) -> Optional[Decimal]:
    """`DEC-PHB02-07` — % thay đổi DOANH THU BÁN HÀNG so tháng liền trước.

    Trả `None` cho cả hai tình huống mà Owner yêu cầu xử lý tường minh: thiếu
    dữ liệu kỳ trước, và kỳ trước bằng 0. `None` ở đây nghĩa là "không có phần
    trăm nào đúng để nói" — tầng trình bày viết nó thành một trạng thái chữ,
    KHÔNG BAO GIỜ thành vô cực, `-100 %`, hay `0 %`.
    """
    if current is None or previous is None or previous == 0:
        return None
    return ((Decimal(current) - Decimal(previous)) / Decimal(previous)
            * Decimal(100)).quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Coverage:
    """Coverage lợi nhuận của một tập dòng + gate 100 % của nó.

    Ba con số ở đây trả lời ba câu HỎI KHÁC NHAU, và cố ý không gộp (`B02`,
    `B03`, chỉ thị `COVERAGE`):

        missing_price_lines  "Còn bao nhiêu dòng chưa có giá nhập?"
        owner_fixable_lines  "Trong đó bao nhiêu dòng chỉ cần gõ giá là xong?"
        blocked_lines        "Những dòng còn lại vướng cái gì, sửa ở đâu?"
        unresolved_employee_lines
                             "Bao nhiêu dòng đã có lãi nhưng chưa biết của ai?"

    `missing_price_lines >= owner_fixable_lines` luôn đúng: nhóm thứ hai là
    tập con của nhóm thứ nhất. Chênh lệch giữa hai con số chính là số dòng mà
    nhập giá KHÔNG đủ để cứu — và Owner đọc được ngay, thay vì bị hứa hẹn.
    """

    covered_lines: int
    total_lines: int
    missing_price_lines: int
    owner_fixable_lines: int
    blocked_lines: tuple[tuple[str, int], ...]
    unresolved_employee_lines: int

    def blocked(self, code: str) -> int:
        """Số dòng bị chặn bởi MỘT mã cụ thể (0 nếu không dòng nào)."""
        return dict(self.blocked_lines).get(code, 0)

    @property
    def is_complete(self) -> bool:
        """`DEC-PHB02-02` §4 — gate, KHÔNG phải ngưỡng.

        Một kỳ không có dòng nào KHÔNG được coi là "đủ 100 %": `0/0` là chưa
        có gì để công nhận, không phải một lời khẳng định đã đầy đủ.
        """
        return self.total_lines > 0 and self.covered_lines == self.total_lines

    @property
    def percent(self) -> Optional[Decimal]:
        """Chỉ để HIỂN THỊ. Gate luôn đọc `is_complete`, không đọc số này —
        `350/351` làm tròn ra `99,72 %`, và không phần trăm nào được phép
        đứng ra thay cho phép so bằng."""
        if self.total_lines == 0:
            return None
        return (Decimal(self.covered_lines) / Decimal(self.total_lines)
                * Decimal(100)).quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class BusinessTotals:
    """Bộ chỉ tiêu nghiệp vụ của MỘT phạm vi (cả kỳ, hoặc một nhân viên).

    `kpi_profit` là lợi nhuận của TOÀN phạm vi. Hai trường dưới nó tách chính
    con số đó làm hai theo `OD-5`, và chúng luôn cộng lại đúng bằng nó:

        kpi_profit = employee_attributed_profit + unattributed_profit

    (với quy ước `NULL + x = x`, vì "chưa có dòng nào" không phải "0 đồng").
    """

    lines: int
    orders: int
    sales_revenue: Optional[Decimal]
    qualifying_quantity: Decimal
    kpi_profit: Optional[Decimal]
    converted_sales: Optional[Decimal]
    coverage: Coverage
    # Phần lợi nhuận đã biết chắc của ai — con số dùng cho KPI/bảng lương.
    employee_attributed_profit: Optional[Decimal] = None
    # Phần lợi nhuận có thật nhưng chưa gán được cho ai ("Chưa xác định
    # nhân viên"). KHÔNG bị bỏ đi, KHÔNG bị cộng nhầm cho ai.
    unattributed_profit: Optional[Decimal] = None

    @property
    def state(self) -> str:
        return STATE_OFFICIAL if self.coverage.is_complete else STATE_INCOMPLETE

    @property
    def official_kpi_profit(self) -> Optional[Decimal]:
        """`R-S7` — lợi nhuận KPI CHÍNH THỨC, hoặc `None`.

        Dưới 100 % coverage hàm này trả `None` để không có đường nào trình bày
        một kết quả một phần như số chính thức. Con số một phần vẫn tồn tại ở
        `kpi_profit` và tầng trình bày dán nhãn CHƯA HOÀN CHỈNH lên nó.
        """
        return self.kpi_profit if self.coverage.is_complete else None

    @property
    def official_converted_sales(self) -> Optional[Decimal]:
        """`R-E8` — DS quy đổi chỉ chính thức khi lợi nhuận nền đã đủ."""
        return self.converted_sales if self.coverage.is_complete else None


def _sum(values) -> Optional[Decimal]:
    """Tổng của các giá trị KHÔNG `None`; tập rỗng ⟹ `None`, không phải `0`.

    Đây là cùng kỷ luật `NULL ≠ 0` mà `analytics_queries` đã freeze: "chưa có
    giá trị nào" và "bằng không" là hai câu khác nhau, và chỉ một trong hai
    cho phép Owner ra quyết định.
    """
    present = [Decimal(value) for value in values if value is not None]
    return sum(present, Decimal(0)) if present else None


def totals(lines: list[BusinessLine]) -> BusinessTotals:
    """Gộp một tập dòng thành bộ chỉ tiêu nghiệp vụ.

    `orders` đếm `COUNT DISTINCT order_key` TRONG tập được truyền vào (M1).
    Khi tập là các dòng của một nhân viên, một đơn có hai nhân viên vì thế
    được đếm ở cả hai — đúng sự thật nghiệp vụ `R-E5`, và trang phải nói ra
    điều đó thay vì giấu đi.
    """
    blocked: dict[str, int] = {}
    for line in lines:
        for code in line.profit_blockers:
            blocked[code] = blocked.get(code, 0) + 1
    return BusinessTotals(
        lines=len(lines),
        orders=len({line.order_key for line in lines}),
        sales_revenue=_sum(line.total_sales for line in lines),
        qualifying_quantity=sum(
            (line.qualifying_quantity for line in lines), Decimal(0)),
        kpi_profit=_sum(line.kpi_profit for line in lines),
        converted_sales=_sum(line.converted_sales for line in lines),
        coverage=Coverage(
            covered_lines=sum(1 for line in lines if line.contributes_profit),
            total_lines=len(lines),
            missing_price_lines=sum(
                1 for line in lines if line.blocked_by_missing_price),
            owner_fixable_lines=sum(1 for line in lines if line.owner_fixable),
            # Thứ tự cố định theo `PROFIT_BLOCKERS` để màn hình không đổi thứ
            # tự dòng giữa hai lần tải trang chỉ vì dict đổi thứ tự chèn.
            blocked_lines=tuple(
                (code, blocked[code]) for code in profit_gate.PROFIT_BLOCKERS
                if code in blocked),
            unresolved_employee_lines=sum(
                1 for line in lines
                if line.contributes_profit and not line.employee_resolved),
        ),
        employee_attributed_profit=_sum(
            line.employee_kpi_profit for line in lines),
        unattributed_profit=_sum(
            line.kpi_profit for line in lines if not line.employee_resolved),
    )




def group_by_employee(
    lines: list[BusinessLine],
) -> list[tuple[Optional[str], Optional[str], BusinessTotals]]:
    """Phân hoạch theo `(nhân viên, nhóm)`, sắp theo doanh thu giảm dần.

    Đây là một PHÂN HOẠCH của cùng tập dòng, nên mọi chỉ tiêu cộng được (doanh
    thu, số lượng đủ điều kiện, lợi nhuận, DS quy đổi, coverage) cộng lại đúng
    bằng tổng kỳ. Cột `orders` thì KHÔNG — một đơn có hai nhân viên được đếm ở
    cả hai dòng. Đó là sự thật nghiệp vụ `R-E5`, và trang phải nói ra nó thay
    vì che đi bằng một phép đếm sai.

    Nhân viên chưa map (`employee is None`) KHÔNG bị bỏ im lặng (`R-E4`) — họ
    là một dòng như mọi người khác, và luôn nằm CUỐI bảng.
    """
    buckets: dict[tuple[Optional[str], Optional[str]], list[BusinessLine]] = {}
    for line in lines:
        buckets.setdefault((line.employee, line.employee_group), []).append(line)
    grouped = [(name, group, totals(bucket))
               for (name, group), bucket in buckets.items()]
    grouped.sort(key=lambda item: (
        item[0] is None,
        -(item[2].sales_revenue or Decimal(0)),
        item[0] or "",
    ))
    return grouped


def for_employee(
    lines: list[BusinessLine], employee: Optional[str]
) -> list[BusinessLine]:
    """Các dòng của MỘT nhân viên. `None` = nhóm "chưa xác định nhân viên"."""
    return [line for line in lines if line.employee == employee]


__all__ = [
    "BusinessLine", "BusinessTotals", "Coverage", "LineContribution",
    "CONTRIBUTION_DISCOUNT", "CONTRIBUTION_PRODUCT",
    "DISCOUNT_DISPLAY_LABEL", "DISCOUNT_DISPLAY_QUANTITY",
    "DISCOUNT_DISPLAY_SELL_PRICE", "display_contributions",
    "UNRESOLVED_EMPLOYEE",
    "PROVENANCE_AUTO", "PROVENANCE_MANUAL", "PROVENANCE_MANUAL_OVERRIDE",
    "PROVENANCE_PENDING", "QUALIFYING_SALE_PRICE_THRESHOLD",
    "STATE_INCOMPLETE", "STATE_OFFICIAL",
    "TARGET_NO_ACTUAL", "TARGET_UNSET", "TARGET_ZERO",
    "converted_sales", "for_employee", "group_by_employee",
    "month_over_month_percent", "totals", "vs_target_percent",
    "vs_target_reason",
]
