"""PHB-03 mục 8 — vector nghiệm thu NGHIỆP VỤ của Summary + Employee V1.

File này kiểm NGỮ NGHĨA, không kiểm HTML. Mọi mệnh đề ở đây là một câu của
`docs/tasks/PHB-02-business-parity-contract.md` mục 0 (`DEC-PHB02-01…07`), và
mỗi test chỉ tới đúng một quyết định — nên khi một test đỏ, cái đỏ là "một
quyết định Owner đã bị vi phạm", không phải "một hàm đổi chữ ký".

Bốn vector A–D lấy nguyên văn từ ví dụ nghiệm thu của `DEC-PHB02-05`, kể cả
con số làm tròn hai chữ số thập phân.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.modules.reporting import business_metrics as bm
from app.modules.reporting import profit_gate
from app.modules.reporting.rate_routing import (
    ConversionRateRouter, gia_dung_workflow_applies,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERSION_RATES = REPO_ROOT / "config" / "conversion_rates.yaml"


def line(**kwargs) -> bm.BusinessLine:
    """Một dòng hàng mặc định LÀNH: có đủ giá bán/số lượng/giá nhập.

    Mặc định lành có chủ đích — mỗi test chỉ hỏng đúng một thứ nó đang nói về,
    nên "vì sao dòng này không vào tổng" luôn có đúng một câu trả lời.

    `status="AUTO"` chỉ còn là NHÃN LỊCH SỬ của pipeline. Sau bản sửa PHB-03
    nó không tham gia vào bất kỳ phép quyết định nào — các test dưới đây chứng
    minh chính điều đó.
    """
    defaults = dict(
        order_key="BH1", employee="Ly", employee_group="STANDARD_SALES",
        status="AUTO", sell_price=Decimal("8000000"), quantity=Decimal("1"),
        discount=Decimal("0"), total_sales=Decimal("8000000"),
        auto_purchase_price=Decimal("7000000"),
        auto_kpi_profit=Decimal("1000000"),
        kpi_authority_valid=True,
        conversion_rate=Decimal("0.055"),
    )
    return bm.BusinessLine(**{**defaults, **kwargs})


def production_pending(**kwargs) -> bm.BusinessLine:
    """Trạng thái mà production THẬT SỰ tạo ra, và test cũ không dựng được.

    Pipeline không tra được giá nhập ⟹ nó ghi hai mã lý do và đóng dấu
    `PENDING`. Tổ hợp `status="AUTO"` + thiếu giá nhập — thứ mà bài test cũ
    `test_a_missing_price_becomes_manual_and_recalculates_the_profit` dựng lên
    — **không tồn tại trên dữ liệu thật**, nên bài test đó chạy xanh mà không
    chứng minh gì về production (bản audit mục 11).
    """
    defaults = dict(
        status="PENDING", auto_purchase_price=None, auto_kpi_profit=None,
        pending_reasons=("TRACKING_HISTORY_PENDING", "Missing.PurchasePrice",
                         "Pending.eligible_kpi_profit"),
    )
    return line(**{**defaults, **kwargs})


# --- A–D · DS quy đổi là phép CHIA, theo ma trận tỉ lệ của DEC-PHB02-05 ----

@pytest.mark.parametrize("rate,expected", [
    ("0.075", "13333333.33"),   # A · Tín Phát
    ("0.02", "50000000.00"),    # B · Vinh/Quý/Hiệp, hàng thường
    ("0.08", "12500000.00"),    # C · Vinh/Quý/Hiệp, Gia dụng
    ("0.055", "18181818.18"),   # D · bán lẻ khác
])
def test_converted_sales_divides_profit_by_the_rate(rate, expected):
    assert bm.converted_sales(Decimal("1000000"), Decimal(rate)) == Decimal(expected)


def test_converted_sales_is_never_a_multiplication():
    """`DEC-PHB02-04` viết hoa: "TUYỆT ĐỐI KHÔNG implement profit * rate".

    Phép nhân cho `75.000` ở đây; phép chia cho `13.333.333,33`. Hai con số
    cách nhau 178 lần, nên một lần cài sai sẽ không "hơi lệch" — nó sẽ khiến
    mọi bảng lương sai hoàn toàn. Test này tồn tại để cái sai đó không im lặng.
    """
    result = bm.converted_sales(Decimal("1000000"), Decimal("0.075"))
    assert result != Decimal("1000000") * Decimal("0.075")
    assert result > Decimal("1000000")


def test_a_line_divides_by_its_own_rate_not_by_a_blended_one():
    """`R-E6` — tỉ lệ đổi ngay BÊN TRONG một nhân viên (Gia dụng 8% cạnh Điện
    máy 2%), nên phép chia phải ở cấp dòng rồi mới cộng."""
    lines = [
        line(order_key="BH1", conversion_rate=Decimal("0.02"),
             auto_kpi_profit=Decimal("1000000")),
        line(order_key="BH2", conversion_rate=Decimal("0.08"),
             auto_kpi_profit=Decimal("1000000")),
    ]
    totals = bm.totals(lines)
    assert totals.converted_sales == Decimal("62500000.00")  # 50tr + 12,5tr
    # Cộng lợi nhuận trước rồi chia cho một tỉ lệ pha trộn cho ra con số khác.
    blended = bm.converted_sales(Decimal("2000000"), Decimal("0.05"))
    assert totals.converted_sales != blended


# --- E · Tổng số SP = SUM(quantity) khi ĐƠN GIÁ > 1.000.000 ---------------

def test_quantity_counts_only_lines_priced_above_one_million():
    """`DEC-PHB02-03` — ngưỡng GIÁ, cố ý không phải một taxonomy."""
    lines = [
        line(sell_price=Decimal("8000000"), quantity=Decimal("3")),   # đủ
        line(sell_price=Decimal("1500000"), quantity=Decimal("2")),   # đủ
        line(sell_price=Decimal("250000"), quantity=Decimal("12")),   # giá treo
        line(sell_price=Decimal("1000000"), quantity=Decimal("5")),   # đúng ngưỡng
    ]
    assert bm.totals(lines).qualifying_quantity == Decimal("5")


def test_the_threshold_is_strictly_greater_than_one_million():
    """Owner viết "> 1.000.000", nên một dòng ĐÚNG 1.000.000 bị LOẠI."""
    assert line(sell_price=Decimal("1000000")).qualifying_quantity == Decimal(0)
    assert line(sell_price=Decimal("1000001")).qualifying_quantity == Decimal("1")


def test_quantity_is_a_sum_of_quantities_not_a_count_of_skus_or_rows():
    """`DEC-PHB02-03`: "KHÔNG phải số SKU duy nhất, KHÔNG phải số dòng"."""
    lines = [line(quantity=Decimal("4")), line(quantity=Decimal("6"))]
    assert bm.totals(lines).qualifying_quantity == Decimal("10")


# --- F/G · gate coverage 100 %, không có ngưỡng nào khác ------------------

def test_coverage_below_one_hundred_percent_does_not_unlock_official_profit():
    """`DEC-PHB02-02` §4 — 99,x % vẫn là CHƯA CHÍNH THỨC.

    Dựng đúng 351 dòng để phần trăm hiển thị ra `99,72 %`: nếu ai đó thay phép
    so bằng bằng một ngưỡng phần trăm, test này là chỗ nó gãy.
    """
    lines = [line(order_key=f"BH{i}") for i in range(350)]
    lines.append(line(order_key="BH350", auto_purchase_price=None,
                      auto_kpi_profit=None))
    totals = bm.totals(lines)
    assert totals.coverage.covered_lines == 350
    assert totals.coverage.total_lines == 351
    assert totals.coverage.percent == Decimal("99.72")
    assert totals.coverage.is_complete is False
    assert totals.state == bm.STATE_INCOMPLETE
    assert totals.official_kpi_profit is None
    assert totals.official_converted_sales is None
    # Con số một phần VẪN tồn tại — nó chỉ không được gọi là chính thức.
    assert totals.kpi_profit == Decimal("350000000")


def test_full_coverage_unlocks_official_profit_and_converted_sales():
    totals = bm.totals([line(order_key=f"BH{i}") for i in range(3)])
    assert totals.coverage.is_complete is True
    assert totals.state == bm.STATE_OFFICIAL
    assert totals.official_kpi_profit == Decimal("3000000")
    assert totals.official_converted_sales == bm.converted_sales(
        Decimal("1000000"), Decimal("0.055")) * 3


def test_an_empty_period_is_not_one_hundred_percent_covered():
    """`0/0` là "chưa có gì để công nhận", không phải "đã đầy đủ"."""
    totals = bm.totals([])
    assert totals.coverage.is_complete is False
    assert totals.coverage.percent is None
    assert totals.official_kpi_profit is None
    assert totals.kpi_profit is None  # NULL, KHÔNG phải 0


def test_coverage_numerator_equals_the_set_that_is_actually_summed():
    """Bất biến giữ cho chữ CHÍNH THỨC không nói dối.

    Nếu tử số của coverage rộng hơn tập được cộng, `coverage = 100 %` sẽ công
    nhận một con số vẫn còn bỏ sót dòng. Bất biến này là toàn bộ lý do định
    nghĩa coverage của PHB-03 không phải là "số dòng có giá nhập".
    """
    lines = [
        line(order_key="BH1"),
        line(order_key="BH2", status="PENDING"),
        line(order_key="BH3", auto_purchase_price=None, auto_kpi_profit=None),
    ]
    totals = bm.totals(lines)
    contributing = [l for l in lines if l.kpi_profit is not None]
    assert totals.coverage.covered_lines == len(contributing)
    assert totals.kpi_profit == sum(l.kpi_profit for l in contributing)


def test_coverage_separates_what_the_owner_can_fix_from_what_they_cannot():
    """`B02`/`B03` — hai ô đếm cũ nói với Owner điều ngược lại sự thật.

    Ô `missing_price_lines` cũ được định nghĩa là `status == "AUTO" VÀ chưa có
    giá nhập`. Nhưng một dòng chưa có giá nhập LUÔN mang `Missing.PurchasePrice`
    nên `status` của nó luôn là `PENDING` — ô đó vì vậy **luôn bằng 0 theo cấu
    tạo**, và toàn bộ số dòng thiếu bị dồn sang ô "nhập giá không cứu được".

    Bốn dòng dưới đây dựng đúng bốn tình huống khác nhau. Trước bản sửa, ba
    trong bốn dòng cùng hiện dưới một câu duy nhất và câu đó sai.
    """
    totals = bm.totals([
        line(order_key="BH1"),                                   # đủ, có lãi
        production_pending(order_key="BH2"),                      # gõ giá là xong
        production_pending(order_key="BH3", quantity=Decimal(0)), # thiếu 2 thứ
        line(order_key="BH4", quantity=Decimal(0)),               # SL = 0 thôi
    ])
    coverage = totals.coverage
    assert coverage.covered_lines == 1
    # Hai dòng thiếu giá nhập — con số này KHÁC 0, khác hẳn ô đếm cũ.
    assert coverage.missing_price_lines == 2
    # Nhưng chỉ MỘT trong hai dòng đó gõ giá vào là xong.
    assert coverage.owner_fixable_lines == 1
    # Và mỗi cửa chặn tự nói tên mình, kèm số dòng.
    assert coverage.blocked(profit_gate.BLOCK_PURCHASE_PRICE_MISSING) == 2
    assert coverage.blocked(profit_gate.BLOCK_QUANTITY_ZERO) == 2


def test_a_generic_pending_label_alone_never_blocks_profit():
    """`OD-6` — "cần kiểm tra" chung chung KHÔNG phải một lý do kinh tế.

    Đây là bài test thay cho
    `test_a_pending_line_stays_out_of_the_profit_sum_even_with_a_manual_price`,
    bài vốn đang CỐ ĐỊNH HOÁ chính lỗi `B01` thành hành vi mong muốn. Owner đã
    quyết định ngược lại: phải có một cửa chặn kinh tế CỤ THỂ mới được từ chối
    tính lợi nhuận.
    """
    rescued = production_pending(manual_purchase_price=Decimal("6500000"),
                                 manual_provenance=bm.PROVENANCE_MANUAL_OVERRIDE)
    assert rescued.status == "PENDING"          # nhãn lịch sử vẫn còn nguyên
    assert rescued.profit_blockers == ()        # nhưng không cửa chặn nào thật
    assert rescued.kpi_profit == Decimal("1500000")
    assert bm.totals([rescued]).coverage.is_complete is True


# --- H/I · nhập tay và ghi đè, và việc tính lại theo sau ------------------

def test_a_missing_price_becomes_manual_and_recalculates_the_profit():
    """Vector H, dựng trên trạng thái production THẬT: PENDING → MANUAL.

    Bài cũ dựng `status="AUTO"` + thiếu giá nhập — một tổ hợp production không
    tạo ra được — nên nó chạy xanh mà không chứng minh gì. Bài này dùng
    `production_pending()`, tức là đúng cái mà pipeline ghi xuống database.
    """
    pending = production_pending()
    assert pending.purchase_provenance == bm.PROVENANCE_PENDING
    assert pending.kpi_profit is None
    assert pending.profit_blockers == (profit_gate.BLOCK_PURCHASE_PRICE_MISSING,)
    assert pending.owner_fixable is True
    assert bm.totals([pending]).coverage.is_complete is False

    completed = production_pending(manual_purchase_price=Decimal("6500000"),
                                   manual_provenance=bm.PROVENANCE_MANUAL)
    assert completed.purchase_provenance == bm.PROVENANCE_MANUAL
    # (8.000.000 − 6.500.000) × 1 − 0 = 1.500.000  (DEC-143, FIND-PHB02-N06)
    assert completed.kpi_profit == Decimal("1500000")
    totals = bm.totals([completed])
    assert totals.coverage.is_complete is True
    assert totals.official_kpi_profit == Decimal("1500000")


def test_editing_an_auto_price_becomes_manual_override_and_recalculates():
    """Vector I: AUTO → MANUAL_OVERRIDE → tính lại."""
    auto = line()
    assert auto.purchase_provenance == bm.PROVENANCE_AUTO
    assert auto.kpi_profit == Decimal("1000000")

    overridden = line(manual_purchase_price=Decimal("6000000"),
                      manual_provenance=bm.PROVENANCE_MANUAL_OVERRIDE)
    assert overridden.purchase_provenance == bm.PROVENANCE_MANUAL_OVERRIDE
    assert overridden.kpi_profit == Decimal("2000000")
    assert overridden.converted_sales == bm.converted_sales(
        Decimal("2000000"), Decimal("0.055"))


def test_an_override_is_never_silently_reported_as_auto():
    """`DEC-PHB02-02` §3 — kể cả khi giá nhập TRÙNG đúng giá tự động.

    Owner đã ra một quyết định; xoá dấu vết quyết định đó là nói dối về nguồn
    con số, và đó chính là điều khoản này cấm.
    """
    same_value = line(manual_purchase_price=Decimal("7000000"),
                      manual_provenance=bm.PROVENANCE_MANUAL_OVERRIDE)
    assert same_value.auto_purchase_price == same_value.manual_purchase_price
    assert same_value.purchase_provenance == bm.PROVENANCE_MANUAL_OVERRIDE


def test_the_frozen_profit_formula_keeps_quantity_and_discount():
    """`FIND-PHB02-N06` — `DEC-PHB02-04` KHÔNG bỏ `× Quantity` hay `− Discount`.

    Dòng minh hoạ `sale_price − purchase_price` của `DEC-PHB02-04` là theo MỘT
    đơn vị sản phẩm; công thức thi hành vẫn là `DEC-143`/`OD-108B-01`.
    """
    overridden = line(sell_price=Decimal("10000000"), quantity=Decimal("3"),
                      discount=Decimal("500000"),
                      manual_purchase_price=Decimal("8000000"),
                      manual_provenance=bm.PROVENANCE_MANUAL_OVERRIDE)
    # (10.000.000 − 8.000.000) × 3 − 500.000
    assert overridden.kpi_profit == Decimal("5500000")


def test_a_line_without_an_override_reuses_the_engine_number_verbatim():
    """Owner chưa động vào dòng và engine đã ra số ⟹ dùng NGUYÊN số đó."""
    untouched = line()
    assert untouched.manual_purchase_price is None
    assert untouched.kpi_profit is untouched.auto_kpi_profit


def test_a_broken_kpi_authority_fails_closed_even_with_a_manual_price():
    """`DEC-143` §1 — cái van an toàn phải sống sót qua bản sửa này.

    Bản audit cảnh báo đúng chỗ này: đường tính lại khi có giá tay trước đây
    áp thẳng công thức mà KHÔNG hỏi thẩm quyền có đọc được không, nên nới cửa
    chặn mà không xử lý điểm này sẽ khiến những dòng có giá tay **vẫn ra số**
    trong lúc file thẩm quyền hỏng — đi vòng qua đúng cái van dựng để chặn.

    Ở đây thẩm quyền là một cửa chặn TƯỜNG MINH, nên nó chặn cả hai đường.
    """
    broken = line(kpi_authority_valid=False,
                  manual_purchase_price=Decimal("6000000"),
                  manual_provenance=bm.PROVENANCE_MANUAL_OVERRIDE)
    assert broken.profit_blockers == (
        profit_gate.BLOCK_KPI_AUTHORITY_UNAVAILABLE,)
    assert broken.kpi_profit is None
    assert broken.converted_sales is None
    # Và nó KHÔNG bị đếm nhầm là "chỉ thiếu giá nhập": gõ giá không cứu được.
    assert broken.owner_fixable is False
    totals = bm.totals([broken])
    assert totals.kpi_profit is None
    assert totals.coverage.is_complete is False


def test_the_invariant_that_keeps_coverage_from_lying():
    """`cửa chặn rỗng` ⟺ `có lợi nhuận`. Không có khe hở giữa hai vế.

    Nếu một dòng không có cửa chặn nào MÀ vẫn không ra số, nó sẽ nằm ngoài
    tổng trong khi màn hình không có gì để nói về nó — đúng kiểu "thiếu trong
    im lặng" mà toàn bộ định nghĩa coverage của PHB-03 tồn tại để chặn.

    Trường hợp cụ thể: pipeline trả `None` (hôm chạy máy thẩm quyền KPI hỏng)
    nhưng hôm nay mọi đầu vào đã đủ. Dòng đó PHẢI ra số.
    """
    lines = [
        line(),
        line(auto_kpi_profit=None),
        production_pending(),
        production_pending(manual_purchase_price=Decimal("6500000")),
        line(quantity=Decimal(0)),
        line(quantity=Decimal(-1)),
        line(sell_price=None),
        line(quantity=None),
        line(kpi_authority_valid=False),
    ]
    for item in lines:
        assert (item.profit_blockers == ()) == (item.kpi_profit is not None), item
    # Và dòng mà engine bỏ trống nhưng đầu vào đã đủ thì được tính lại đúng.
    assert lines[1].kpi_profit == Decimal("1000000")


# --- OD-1…OD-5 · quyết định Owner đã đóng băng cho bản sửa PHB-03 ---------

def test_quantity_zero_warns_and_never_finalises_a_profit(): # OD-1
    """`OD-1` — số lượng 0 KHÔNG phải "lãi 0 đồng".

    Ví dụ thật từ golden: `BTL00300`, `Máy Giặt Panasonic`, số lượng 0, đơn giá
    6.200.000. Không ai biết được đó là "thật sự không giao cái nào" hay "quên
    gõ số lượng". Owner đã quyết: đây là dữ liệu chưa đủ tin, phải sửa trên sổ
    gốc — và một con số `0` bịa ra còn nguy hiểm hơn một ô trống, vì nó trông
    như đã tính xong.
    """
    zero = line(quantity=Decimal(0), auto_kpi_profit=None)
    assert zero.profit_blockers == (profit_gate.BLOCK_QUANTITY_ZERO,)
    assert zero.kpi_profit is None          # KHÔNG phải Decimal(0)
    assert zero.converted_sales is None
    totals = bm.totals([zero])
    assert totals.kpi_profit is None
    assert totals.coverage.blocked(profit_gate.BLOCK_QUANTITY_ZERO) == 1
    # Gõ giá nhập KHÔNG cứu được dòng này — màn hình không được hứa như vậy.
    assert zero.owner_fixable is False


def test_negative_quantity_needs_review_and_never_reaches_an_employee_kpi(): # OD-2
    """`OD-2` — số lượng âm cần xem lại; KHÔNG tự cộng vào KPI nhân viên.

    Cộng `−1 × biên lợi nhuận` vào một con số nào đó chính là khẳng định dấu
    âm nghĩa là hoàn hàng — tức là phát minh ngữ nghĩa trả hàng/hoàn tiền,
    đúng thứ `OD-2` cấm trong task này. Nên dòng dừng ở "cần xem lại".
    """
    negative = line(quantity=Decimal(-1), auto_kpi_profit=None)
    assert negative.profit_blockers == (profit_gate.BLOCK_QUANTITY_NEGATIVE,)
    assert negative.kpi_profit is None
    assert negative.employee_kpi_profit is None
    totals = bm.totals([negative])
    assert totals.employee_attributed_profit is None
    assert totals.coverage.blocked(profit_gate.BLOCK_QUANTITY_NEGATIVE) == 1


def test_a_possible_duplicate_only_warns_and_keeps_both_revenue_and_profit(): # OD-3
    """`OD-3` — mâu thuẫn cũ: doanh thu cộng cả hai dòng, lợi nhuận bỏ cả hai.

    Không có cách đọc nào khiến hành vi cũ là đúng: nếu đó thật sự là dòng
    trùng thì doanh thu ĐÃ bị đếm đúp mà không ai chặn; nếu không phải thì lợi
    nhuận đang bị loại oan. Owner đã chọn phương án nhất quán: cộng cả hai, và
    nói rõ có nghi ngờ trùng.
    """
    duplicate = line(pending_reasons=("Duplicate",), status="PENDING")
    assert duplicate.profit_blockers == ()
    assert duplicate.kpi_profit == Decimal("1000000")
    assert profit_gate.WARN_POSSIBLE_DUPLICATE in duplicate.warnings

    totals = bm.totals([line(order_key="BH1"), duplicate])
    assert totals.sales_revenue == Decimal("16000000")   # doanh thu: cả hai
    assert totals.kpi_profit == Decimal("2000000")       # lợi nhuận: cả hai
    assert totals.coverage.is_complete is True


def test_a_zero_sell_price_warns_and_still_produces_a_negative_profit(): # OD-4
    """`OD-4` — vector nguyên văn của Owner: SL 1, giá bán 0, giá nhập 500.000.

    `0` là một giá bán THẬT (hàng tặng kèm), không phải một ô trống. Khoản
    500.000 kia là chi phí doanh nghiệp thật sự chịu, nên nó phải hiện ra dưới
    dạng −500.000. Thay nó bằng `0` là làm báo cáo đẹp hơn sự thật.
    """
    giveaway = line(sell_price=Decimal(0), quantity=Decimal(1),
                    total_sales=Decimal(0), auto_purchase_price=None,
                    auto_kpi_profit=None,
                    manual_purchase_price=Decimal("500000"),
                    manual_provenance=bm.PROVENANCE_MANUAL)
    assert giveaway.profit_blockers == ()
    assert giveaway.kpi_profit == Decimal("-500000")
    assert profit_gate.WARN_SELL_PRICE_ZERO in giveaway.warnings
    assert profit_gate.WARN_PURCHASE_ABOVE_SELL in giveaway.warnings
    assert profit_gate.WARN_NEGATIVE_PROFIT in giveaway.warnings
    assert bm.totals([giveaway]).kpi_profit == Decimal("-500000")


def test_an_unknown_employee_keeps_company_profit_but_not_an_individual_kpi(): # OD-5
    """`OD-5` — "tính được lãi" và "biết lãi của ai" là HAI câu hỏi.

    Trước bản sửa, không trả lời được câu thứ hai thì câu thứ nhất cũng mất
    luôn con số: lợi nhuận của cả kỳ bị kéo xuống bởi một vấn đề vốn chỉ là
    chuyện gán tên người.
    """
    known = line(order_key="BH1", employee="Ly")
    unknown = line(order_key="BH2", employee=None, employee_group=None)
    assert unknown.kpi_profit == Decimal("1000000")   # vào tổng công ty
    assert unknown.employee_kpi_profit is None        # chưa vào KPI của ai
    assert profit_gate.BLOCK_EMPLOYEE_UNRESOLVED in unknown.warnings

    totals = bm.totals([known, unknown])
    assert totals.kpi_profit == Decimal("2000000")
    assert totals.employee_attributed_profit == Decimal("1000000")
    assert totals.unattributed_profit == Decimal("1000000")
    # Hai phần cộng lại đúng bằng tổng — không đồng nào biến mất.
    assert (totals.employee_attributed_profit + totals.unattributed_profit
            == totals.kpi_profit)
    # Và nhóm "chưa xác định" nhìn thấy được, không im lặng.
    assert totals.coverage.unresolved_employee_lines == 1
    # Nó KHÔNG làm coverage tụt: dòng đó ĐÃ có lợi nhuận.
    assert totals.coverage.is_complete is True


def test_assigning_the_employee_moves_the_line_without_changing_the_total(): # OD-5
    """Sau khi Owner gán, dòng rời nhóm "chưa xác định" và về đúng người.

    Tổng của cả kỳ KHÔNG đổi — đó là điều kiện để Owner tin thao tác này chỉ
    dời một khoản chứ không tạo ra hay làm mất tiền.
    """
    before = bm.totals([line(order_key="BH1", employee="Ly"),
                        line(order_key="BH2", employee=None)])
    after = bm.totals([
        line(order_key="BH1", employee="Ly"),
        line(order_key="BH2", employee="Vinh", employee_group="NOI_THANH",
             source_employee=None, employee_provenance="MANUAL"),
    ])
    assert after.kpi_profit == before.kpi_profit
    assert after.coverage.unresolved_employee_lines == 0
    assert after.unattributed_profit is None
    assert after.employee_attributed_profit == after.kpi_profit
    assert [name for name, _g, _t in bm.group_by_employee([
        line(order_key="BH2", employee="Vinh", employee_provenance="MANUAL")])
    ] == ["Vinh"]


def test_a_rescued_line_stops_shouting_about_the_gap_it_no_longer_has():
    """Cảnh báo xuất hiện ở khắp nơi thì không còn là cảnh báo.

    Trên dữ liệu thật `Missing.PurchasePrice` gắn vào **100 % số dòng** của cả
    hai kỳ golden. Nếu mọi mã pipeline đều sinh ra một cảnh báo, mọi dòng của
    mọi báo cáo sẽ mang câu "có ghi chú cần kiểm tra" — kể cả dòng Owner vừa
    nhập giá xong.

    Không có gì bị giấu: khi giá nhập còn thiếu, cửa chặn nói đúng điều đó
    bằng ngôn ngữ hành động được; và bảng kê vẫn liệt kê nguyên văn mọi mã.
    """
    rescued = production_pending(manual_purchase_price=Decimal("6500000"),
                                 manual_provenance=bm.PROVENANCE_MANUAL)
    assert rescued.pending_reasons                      # mã vẫn còn nguyên
    assert rescued.warnings == ()                       # nhưng không ồn ào

    # Một ghi chú KHÔNG thuộc nhóm "thiếu giá nhập" thì vẫn được nói ra.
    other = production_pending(
        manual_purchase_price=Decimal("6500000"),
        manual_provenance=bm.PROVENANCE_MANUAL,
        pending_reasons=("Missing.PurchasePrice", "OrderInconsistency"))
    assert profit_gate.WARN_PIPELINE_REVIEW in other.warnings


def test_the_raw_accounting_employee_survives_a_reassignment():
    """Bằng chứng gốc ĐI KÈM chứ không bị thay thế.

    Chỉ thị: *"Preserve raw accounting source evidence. Do NOT overwrite the
    raw source field destructively."* Sau khi gán, vẫn trả lời được câu "sổ
    ghi ai" mà không phải mở lại lịch sử chạy máy.
    """
    reassigned = line(employee="Vinh", source_employee="Vjnh",
                      employee_provenance="MANUAL")
    assert reassigned.employee == "Vinh"          # có hiệu lực cho KPI
    assert reassigned.source_employee == "Vjnh"   # sổ vẫn ghi nguyên như cũ


# --- J/K · So tháng trước, trên DOANH THU BÁN HÀNG ------------------------

def test_month_over_month_is_a_percentage_of_sales_revenue():
    """`DEC-PHB02-07` — chỉ tiêu được so là DOANH THU BÁN HÀNG."""
    assert bm.month_over_month_percent(
        Decimal("120000000"), Decimal("100000000")) == Decimal("20.00")
    assert bm.month_over_month_percent(
        Decimal("80000000"), Decimal("100000000")) == Decimal("-20.00")


def test_a_zero_previous_month_never_produces_infinity_or_a_misleading_number():
    """`DEC-PHB02-07`: "KHÔNG bịa vô cực hay một phần trăm gây hiểu nhầm"."""
    assert bm.month_over_month_percent(Decimal("50000000"), Decimal(0)) is None
    assert bm.month_over_month_percent(Decimal(0), Decimal(0)) is None
    assert bm.month_over_month_percent(Decimal("50000000"), None) is None
    assert bm.month_over_month_percent(None, Decimal("1")) is None


# --- L/M · Gia dụng chỉ định tuyến cho Vinh · Quý · Hiệp ------------------

@pytest.fixture(scope="module")
def router() -> ConversionRateRouter:
    return ConversionRateRouter.from_yaml(CONVERSION_RATES)


@pytest.mark.parametrize("group,employee,lead_source,product_group,expected", [
    ("STANDARD_SALES", "Tín Phát", "ADS", "DIEN_MAY", "0.075"),
    ("NOI_THANH", "Vinh", "PERSONAL", "DIEN_MAY", "0.020"),
    ("NOI_THANH", "Quý", "PERSONAL", "GIA_DUNG", "0.080"),
    ("NOI_THANH", "Hiệp", "PERSONAL", "GIA_DUNG", "0.080"),
    ("STANDARD_SALES", "Ly", "PERSONAL", "DIEN_MAY", "0.055"),
])
def test_the_conversion_rate_matrix_matches_the_frozen_decision(
    router, group, employee, lead_source, product_group, expected
):
    """`DEC-PHB02-05` đọc thẳng từ `config/conversion_rates.yaml` thật."""
    assert router.rate_for(
        stored_rate=None, classified_group=product_group, employee=employee,
        employee_group=group, lead_source=lead_source,
        sale_date=date(2026, 1, 15),
    ) == Decimal(expected)


def test_only_noi_thanh_can_ever_route_through_the_eight_percent_rate(router):
    """Vector L — và ranh giới này là CẤU TRÚC của bảng cấu hình, không phải
    một câu `if` trong mã: dòng `GIA_DUNG_8` khoá trên `employee_group:
    NOI_THANH`, nên một nhân viên bán lẻ khớp dòng phổ quát và ra 5,5 %."""
    retail = router.rate_for(
        stored_rate=None, classified_group="GIA_DUNG", employee="Ly",
        employee_group="STANDARD_SALES", lead_source="PERSONAL",
        sale_date=date(2026, 1, 15))
    assert retail == Decimal("0.055")
    assert retail != Decimal("0.080")


def test_ordinary_retail_employees_are_never_shown_the_gia_dung_workflow():
    """Vector M — `DEC-PHB02-05`: "KHÔNG hiện và KHÔNG bắt buộc luồng đó với
    nhân viên bán lẻ thường"."""
    assert gia_dung_workflow_applies("NOI_THANH") is True
    assert gia_dung_workflow_applies("STANDARD_SALES") is False
    assert gia_dung_workflow_applies(None) is False


def test_an_unticked_product_keeps_the_rate_the_pipeline_already_recorded(router):
    """Không tick ⟹ KHÔNG hỏi lại resolver.

    Tính lại mọi dòng lúc đọc sẽ âm thầm áp cấu hình HÔM NAY lên một báo cáo
    đã phát hành — đúng lớp lỗi mà `DEC-121` tồn tại để chặn.
    """
    assert router.rate_for(
        stored_rate=Decimal("0.075"), classified_group=None, employee="Ly",
        employee_group="STANDARD_SALES", lead_source="PERSONAL",
        sale_date=date(2026, 1, 15)) == Decimal("0.075")


# --- Ngữ nghĩa nền: NULL không phải 0, và phân hoạch cộng đúng ------------

def test_an_unknown_value_is_never_reported_as_zero():
    """`R-S2` — "chưa biết" và "bằng không" là hai câu khác nhau."""
    unknown = bm.totals([line(total_sales=None, auto_kpi_profit=None,
                              auto_purchase_price=None)])
    assert unknown.sales_revenue is None
    assert unknown.kpi_profit is None
    assert unknown.converted_sales is None


def test_grouping_by_employee_is_a_partition_of_the_same_lines():
    """Mọi chỉ tiêu CỘNG ĐƯỢC cộng lại đúng bằng tổng kỳ; cột Đơn thì KHÔNG
    (`R-E5`: một đơn hai nhân viên được đếm ở cả hai dòng)."""
    lines = [
        line(order_key="BH1", employee="Ly"),
        line(order_key="BH1", employee="Hoàng"),
        line(order_key="BH2", employee="Ly"),
    ]
    company = bm.totals(lines)
    grouped = bm.group_by_employee(lines)
    assert sum(totals.lines for _n, _g, totals in grouped) == company.lines
    assert sum(totals.sales_revenue for _n, _g, totals in grouped) == company.sales_revenue
    assert company.orders == 2
    assert sum(totals.orders for _n, _g, totals in grouped) == 3


def test_an_unmapped_employee_is_never_silently_dropped():
    """`R-E4` — họ là một dòng như mọi người khác, và nằm cuối bảng."""
    grouped = bm.group_by_employee([
        line(employee="Ly"), line(employee=None, employee_group=None)])
    assert [name for name, _g, _t in grouped] == ["Ly", None]
