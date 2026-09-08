"""R3 §2 — loại dòng và luật giá nhập đi kèm, đo trên NGỮ NGHĨA thuần.

Bốn mệnh đề mà cả file này canh, và mỗi cái tương ứng một câu đã ký:

    phí / chiết khấu   giá nhập `0` BY DEFINITION       `OD-105B-01` §3
    hàng bán           thiếu giá ⟹ PENDING, không `0`   `OD-105B-01` §3 câu 2
    quà tặng kèm       giá bán `0` là giá bán THẬT      `OD-4`
    hoàn / hủy         không phát minh ngữ nghĩa        `OD-2`
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.modules.reporting import business_metrics as bm
from app.modules.reporting import line_type as lt
from app.modules.reporting import line_type_config
from app.modules.reporting import profit_gate

from tests.test_business_vertical import (  # noqa: F401 — fixtures
    JANUARY, engine, pair, persist, repository, service, store,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Từ vựng PRODUCTION, không một bản dựng riêng cho test: các bài dưới đây
#: khẳng định điều gì đó về sổ THẬT, nên chúng phải hỏi đúng file mà production
#: đọc. Một từ vựng riêng cho test sẽ xanh mãi trong khi production đổi.
REAL_VOCABULARY = line_type_config.load_vocabulary(
    REPO_ROOT / "config" / "line_types.yaml")


def classify(product, *, order="BH62511", sell="8000000", quantity="1"):
    return lt.classify(
        vocabulary=REAL_VOCABULARY, order_key=order, product_raw=product,
        sell_price=None if sell is None else Decimal(sell),
        quantity=None if quantity is None else Decimal(quantity))


def line(**overrides) -> bm.BusinessLine:
    values = dict(
        order_key="BH1", employee="Vinh", employee_group="NOI_THANH",
        status="PENDING", sell_price=Decimal("8000000"), quantity=Decimal("1"),
        discount=Decimal("0"), total_sales=Decimal("8000000"),
        auto_purchase_price=None, auto_kpi_profit=None, kpi_authority_valid=True,
    )
    values.update(overrides)
    return bm.BusinessLine(**values)


# --- Phân loại trên đúng từ vựng production -------------------------------

class TestTheVocabularyClassifiesTheRealBook:
    """Nhãn thật đo được trên hai kỳ golden (`period_2026_01`, `_06`)."""

    @pytest.mark.parametrize("product", [
        "Chi phí vận chuyển", "Chi phí lắp đặt", "Chi phí lắp đặt sửa chữa",
        "Chênh VAT", "Phụ Phí", "Phụ Phí Đổi mới",
    ])
    def test_the_supplementary_labels_of_the_real_book_are_fees(self, product):
        assert classify(product, sell="0") == lt.TYPE_FEE

    def test_a_keyboard_is_not_a_fee(self):
        """Biên từ, không phải substring: `"phí"` KHÔNG khớp `"bàn phím"`.

        Đây là chính cái bẫy mà `app/modules/validation/text.py` đã ghi lại
        một lần; dùng lại đúng bộ khớp đó là cách không rơi vào nó lần hai.
        """
        assert classify("Bàn phím cơ Logitech") == lt.TYPE_SALE

    def test_a_zero_priced_product_line_is_an_accessory_or_gift(self):
        """`Giá treo Tivi`, đơn giá 0, SL 1 — dữ liệu thật của kỳ 01/2026."""
        assert classify("Giá treo Tivi", sell="0") == lt.TYPE_ACCESSORY_GIFT

    def test_a_zero_quantity_line_is_never_called_a_gift(self):
        """`OD-1` — SL `0` là dữ liệu chưa đủ tin, không phải một món quà."""
        assert classify("Giá treo Tivi", sell="0", quantity="0") == lt.TYPE_SALE

    def test_an_undeclared_document_prefix_stops_the_line(self):
        """`BTL` có thật trong sổ và KHÔNG có quyết định nào của Owner.

        Suy ra "bán trả lại" từ ba chữ cái rồi tự cộng một dấu âm vào KPI
        chính là điều `OD-2` cấm.
        """
        assert classify("Máy giặt Panasonic", order="BTL00300") == \
            lt.TYPE_UNDECIDED_DOCUMENT

    def test_the_document_type_beats_the_line_label(self):
        """Một dòng phí BÊN TRONG một chứng từ chưa rõ vẫn là chưa rõ."""
        assert classify("Chi phí vận chuyển", order="BTL00300", sell="0") == \
            lt.TYPE_UNDECIDED_DOCUMENT

    def test_an_empty_vocabulary_is_refused(self):
        """Bảng tiền tố rỗng ⟹ mọi dòng thành `UNDECIDED` — cấu hình HỎNG."""
        with pytest.raises(ValueError):
            lt.LineTypeVocabulary.of(document_prefixes={})

    def test_no_vocabulary_reproduces_the_behaviour_before_r3(self):
        assert lt.classify(
            vocabulary=None, order_key="BTL1", product_raw="Chi phí vận chuyển",
            sell_price=Decimal("0"), quantity=Decimal("1")) == lt.TYPE_SALE


# --- Giá nhập theo chính sách, và ranh giới của nó ------------------------

class TestPolicyZeroIsNotZeroInsteadOfMissing:
    def test_a_fee_line_gets_zero_by_definition_with_its_own_provenance(self):
        fee = line(line_type=lt.TYPE_FEE, sell_price=Decimal("0"),
                   total_sales=Decimal("0"))
        assert fee.purchase_price == Decimal(0)
        assert fee.purchase_provenance == bm.PROVENANCE_POLICY_ZERO
        assert fee.profit_blockers == ()
        assert fee.kpi_profit == Decimal(0)
        # Nó KHÔNG còn là một dòng "thiếu giá" — đó là toàn bộ điểm của §3.
        assert fee.blocked_by_missing_price is False

    def test_a_plain_product_line_without_a_price_stays_pending(self):
        """`OD-105B-01` §3 câu 2 — KHÔNG dùng `0` thay cho thiếu."""
        product = line(line_type=lt.TYPE_SALE)
        assert product.purchase_price is None
        assert product.purchase_provenance == bm.PROVENANCE_PENDING
        assert product.profit_blockers == (profit_gate.BLOCK_PURCHASE_PRICE_MISSING,)
        assert product.kpi_profit is None

    def test_a_gift_line_still_needs_a_real_purchase_price(self):
        """Một chiếc giá treo tivi tặng kèm VẪN tốn tiền mua.

        Cho nó giá nhập `0` sẽ biến một khoản lỗ có thật thành lãi 0 đồng.
        """
        gift = line(line_type=lt.TYPE_ACCESSORY_GIFT, sell_price=Decimal("0"),
                    total_sales=Decimal("0"))
        assert gift.purchase_price is None
        assert gift.profit_blockers == (profit_gate.BLOCK_PURCHASE_PRICE_MISSING,)
        # Có giá nhập rồi thì con số ÂM phải hiện ra (`OD-4`).
        priced = line(line_type=lt.TYPE_ACCESSORY_GIFT, sell_price=Decimal("0"),
                      total_sales=Decimal("0"),
                      manual_purchase_price=Decimal("500000"))
        assert priced.kpi_profit == Decimal("-500000")

    def test_a_real_price_still_beats_the_policy_zero(self):
        """Chính sách là chỗ dựa khi không ai trả lời, không phải lệnh ghi đè."""
        fee = line(line_type=lt.TYPE_FEE, auto_purchase_price=Decimal("120000"))
        assert fee.purchase_price == Decimal("120000")
        assert fee.purchase_provenance == bm.PROVENANCE_AUTO
        manual = line(line_type=lt.TYPE_FEE,
                      manual_purchase_price=Decimal("90000"),
                      manual_provenance=bm.PROVENANCE_MANUAL)
        assert manual.purchase_price == Decimal("90000")
        assert manual.purchase_provenance == bm.PROVENANCE_MANUAL

    def test_an_undecided_line_is_blocked_by_name_not_by_silence(self):
        undecided = line(line_type=lt.TYPE_UNDECIDED_DOCUMENT,
                         manual_purchase_price=Decimal("5000000"))
        assert profit_gate.BLOCK_LINE_TYPE_UNDECIDED in undecided.profit_blockers
        assert undecided.kpi_profit is None
        # Nhập giá KHÔNG cứu được dòng này ⟹ không được hứa là cứu được.
        assert undecided.owner_fixable is False


# --- Chiết khấu: một lần trừ, không hai ------------------------------------

class TestDiscountIsDeductedExactlyOnce:
    def test_a_discount_line_carries_its_own_negative_amount_only(self):
        """Dòng "Chiết khấu" riêng: giá nhập 0 theo chính sách, doanh thu âm.

        Nó KHÔNG trừ thêm lần nữa — cột `discount` của chính nó là `0`.
        """
        row = line(line_type=lt.TYPE_DISCOUNT, sell_price=Decimal("-100000"),
                   total_sales=Decimal("-100000"))
        assert row.purchase_price == Decimal(0)
        assert row.kpi_profit == Decimal("-100000")

    def test_the_column_form_deducts_once_and_the_line_form_is_not_added(self):
        """Sổ hiện hành: chiết khấu là một CỘT, `DEC-114` đã trừ nó."""
        row = line(discount=Decimal("100000"), total_sales=Decimal("7900000"),
                   manual_purchase_price=Decimal("5000000"))
        # (8.000.000 − 5.000.000) × 1 − 100.000
        assert row.kpi_profit == Decimal("2900000")

    def test_an_order_carrying_both_forms_is_named_not_silently_fixed(self):
        product = line(order_key="BH9", discount=Decimal("100000"))
        separate = line(order_key="BH9", line_type=lt.TYPE_DISCOUNT,
                        sell_price=Decimal("-100000"),
                        total_sales=Decimal("-100000"))
        assert bm.discount_double_count_orders([product, separate]) == ("BH9",)

    def test_a_discount_line_alone_is_not_a_warning(self):
        """Sổ tay CŨ ghi chiết khấu bằng một dòng riêng — cách ghi hợp lệ."""
        separate = line(order_key="BH9", line_type=lt.TYPE_DISCOUNT,
                        sell_price=Decimal("-100000"),
                        total_sales=Decimal("-100000"))
        assert bm.discount_double_count_orders([separate]) == ()


# --- Qua database THẬT: cả kỳ đọc cùng một effective data ------------------

class TestTheWholePeriodReadsOneEffectiveTruth:
    def test_a_fee_line_no_longer_blocks_the_period_from_being_official(
        self, repository, service
    ):
        """Chuỗi mà `TASK-105B-Q3` tồn tại để mở khoá.

        Trước R3: một dòng `Chi phí vận chuyển` không có giá nhập để tra và
        sẽ không bao giờ có, nên `PROFIT_COVERAGE` khoá dưới 100 % vĩnh viễn
        — tức cả kỳ vĩnh viễn không CHÍNH THỨC, vì một lý do không ai sửa
        được bằng bất kỳ thao tác nào.
        """
        persist(repository, [
            pair("BH1", product="Tủ lạnh Panasonic", kpi_purchase="5000000",
                 kpi_profit="3000000", status="AUTO", row=6),
            pair("BH1", product="Chi phí vận chuyển", occurrence=1, row=7,
                 sell="0", quantity="1", kpi_purchase=None, kpi_profit=None),
        ])
        data = service.period(**JANUARY)
        by_product = {d["product_raw"]: d["line"] for d in data.details}
        fee = by_product["Chi phí vận chuyển"]
        assert fee.line_type == lt.TYPE_FEE
        assert fee.purchase_price == Decimal(0)
        assert fee.purchase_provenance == bm.PROVENANCE_POLICY_ZERO
        assert data.totals.coverage.is_complete
        assert data.totals.state == bm.STATE_OFFICIAL

    def test_the_employee_table_and_the_period_totals_read_the_same_lines(
        self, repository, service
    ):
        """Bảng nhân viên là một PHÂN HOẠCH của cùng tập dòng, không phải một
        truy vấn thứ hai — nên nó phải cộng lại đúng bằng tổng kỳ."""
        persist(repository, [
            pair("BH1", product="Tủ lạnh Panasonic", kpi_purchase="5000000",
                 kpi_profit="3000000", status="AUTO", row=6),
            pair("BH2", product="Chi phí vận chuyển", sell="0", quantity="1",
                 employee="Quý", kpi_purchase=None, kpi_profit=None, row=7),
        ])
        data = service.period(**JANUARY)
        grouped = bm.group_by_employee(data.lines)
        assert sum(totals.lines for _n, _g, totals in grouped) == data.totals.lines
        assert sum((totals.kpi_profit or Decimal(0))
                   for _n, _g, totals in grouped) == data.totals.kpi_profit

    def test_the_exception_queue_reads_the_same_lines_as_the_totals(
        self, repository, service
    ):
        """Hàng đợi ngoại lệ lọc trên CHÍNH `data.details` — không đọc lại sổ."""
        persist(repository, [
            pair("BTL00300", product="Máy Giặt Panasonic", quantity="0",
                 sell="6200000", kpi_purchase=None, kpi_profit=None, row=6),
            pair("BH1", product="Tủ lạnh Panasonic", kpi_purchase="5000000",
                 kpi_profit="3000000", status="AUTO", row=7),
        ])
        data = service.period(**JANUARY)
        undecided = [d for d in data.details
                     if d["line"].line_type in lt.UNDECIDED_TYPES]
        assert len(undecided) == 1
        assert undecided[0]["order_key"] == "BTL00300"
        # Dòng đó KHÔNG biến mất khỏi kỳ và KHÔNG bị tính như một dòng bán.
        assert data.totals.lines == 2
        assert data.totals.coverage.blocked("LINE_TYPE_UNDECIDED") == 1
