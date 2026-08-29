"""Golden #4 — SAFE PENDING, BH62439 dòng 53 (`source_row=53`), real production
trace: PURCHASE_PRICE_UNRESOLVED phải dừng ở `Pending` một cách trung thực,
không bao giờ tự suy đoán, không rơi rớt khỏi kết quả, và phải tới được Review
Queue hiện có (TASK-110).

Golden #4 KHÔNG chứng minh case này resolve được — mục tiêu NGƯỢC LẠI: chứng
minh "khi hệ thống không biết, nó không giả vờ biết". Không đăng ký thêm entry
nào vào `data/historical_confirmed/registry.jsonl`, không thêm confirmed
adjustment, không sửa `app/**`/`config/**` — 0 dòng production code.

BH62439 CÙNG đơn hàng thật đã dùng ở Golden #3 (`test_golden_bh62439_kpi.py`,
4 dòng, `source_row` 50-53), nhưng NHẮM VÀO một dòng KHÁC — dòng 53 (`Máy lạnh
Daikin Inverter 2 HP FTKB50ZVMV`) — chưa từng có oracle/pre-code trace/Review
Queue verification riêng. Dòng 52 (Điều hòa Daikin FTHF25XVMV) của CHÍNH đơn
này ĐÃ resolve (Golden #3, entry `HCR-BH62439-20260108-1`) — đây chính là bằng
chứng cross-line-leakage MẠNH NHẤT có sẵn trong dữ liệu thật: nếu giá vốn của
dòng 52 rò rỉ sang dòng 53 cùng đơn, test này bắt được ngay.

Oracle (ghi TRƯỚC khi verify, session S058):

    OrderID              : BH62439
    SaleDate             : 2026-01-08
    SourceRow            : 53
    RawProductName       : "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV"
    Quantity              : 1
    SellPrice             : 16.300.000 VND
    Discount              : 50.000 VND

    Identity              : "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV"
                            (product_raw — KHÔNG bị xoá/thay bằng giá trị nào
                            khác; TASK-105D identity resolver KHÔNG được wiring
                            vào `app.pipeline` — xem `_post_cutover_resolver_not_wired`
                            — nên "Identity" ở tầng production hiện tại CHÍNH LÀ
                            `product_raw`, không phải một namespace TRACKING/
                            PUBLIC_PURCHASE nào được resolve thêm)
    AccountingPurchasePrice : None — PURCHASE_PRICE_UNRESOLVED (không có entry
                            `(BH62439, "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV",
                            2026-01-08)` trong `data/historical_confirmed/registry.jsonl`
                            — registry chỉ có 2 entry, BH62063 và BH62439/dòng 52)
    AccountingProfit       : None
    KpiPurchasePrice       : None
    EligibleKpiProfit      : None

Đây là PURCHASE_PRICE_UNRESOLVED, KHÔNG PHẢI IDENTITY_UNRESOLVED: `product_raw`
là một chuỗi sản phẩm rõ ràng, không rỗng, không mơ hồ — cái duy nhất còn thiếu
là bằng chứng giá vốn đã confirm.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.composition import run_import_production
from app.modules.domain.models import (
    KPI_PURCHASE_PENDING,
    PRICE_SOURCE_PENDING,
)
from app.modules.validation.models import CATEGORY_MISSING_PURCHASE_PRICE

GOLDEN_FIXTURE = Path("tests/fixtures/golden/period_2026_01.xlsx")
CONFIG_DIR = Path("config")

TARGET_ORDER = "BH62439"
TARGET_PRODUCT = "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV"
TARGET_SOURCE_ROW = 53

SIBLING_RESOLVED_PRODUCT = "Điều hòa Daikin FTHF25XVMV"


def _order(result, order_id):
    return next(o for o in result.orders if o.order_id == order_id)


def _line(order, product_raw):
    return next(l for l in order.lines if l.product_raw == product_raw)


def test_bh62439_row53_reaches_production_composition_and_is_present():
    """F/J — dòng KHÔNG rơi rớt: nó có mặt trong `result.orders`, đúng
    `source_row`, đúng đơn, cùng 4 dòng như Golden #3 đã khoá."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    order = _order(result, TARGET_ORDER)
    assert order.line_count == 4

    line = _line(order, TARGET_PRODUCT)
    assert line.raw.source_row == TARGET_SOURCE_ROW
    assert line.order_id == TARGET_ORDER


def test_bh62439_row53_known_raw_fields_are_preserved_not_erased():
    """G — các trường raw/accounting đã biết KHÔNG bị xoá chỉ vì giá vốn
    unresolved: `product_raw`/`quantity`/`sell_price`/`discount`/`date` phải
    khớp NGUYÊN VĂN oracle (không bị None hoá, không bị thay bằng giá trị của
    dòng khác trong cùng đơn)."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, TARGET_ORDER), TARGET_PRODUCT)

    assert line.product_raw == TARGET_PRODUCT
    assert line.quantity == Decimal("1")
    assert line.sell_price == Decimal("16300000")
    assert line.discount == Decimal("50000")
    assert line.date is not None and line.date.isoformat() == "2026-01-08"


def test_bh62439_row53_purchase_price_stays_pending_no_zero_substitution():
    """A/B/C/D/E — PURCHASE_PRICE_UNRESOLVED: không giá vốn, không lợi nhuận
    bịa, không KPI purchase price bịa, không None bị âm thầm thay bằng 0
    (DEC-103 — None và 0 là hai sự thật khác nhau)."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, TARGET_ORDER), TARGET_PRODUCT)

    assert line.price_source == PRICE_SOURCE_PENDING
    assert line.accounting_purchase_price is None
    assert line.accounting_purchase_price != Decimal("0")
    assert line.accounting_profit is None
    assert line.accounting_profit != Decimal("0")

    assert line.kpi_purchase_price is None
    assert line.kpi_purchase_price_provenance == KPI_PURCHASE_PENDING
    assert line.eligible_kpi_profit is None
    assert line.eligible_kpi_profit != Decimal("0")


def test_bh62439_row53_does_not_borrow_confirmed_sibling_price_same_order():
    """I — cross-line leakage: dòng 52 (`Điều hòa Daikin FTHF25XVMV`) CÙNG đơn
    BH62439 ĐÃ resolve (Golden #3). Dòng 53 KHÔNG được mượn giá đó — hai dòng
    phải cho hai kết quả khác nhau dù chia sẻ `OrderID`."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    order = _order(result, TARGET_ORDER)

    resolved_line = _line(order, SIBLING_RESOLVED_PRODUCT)
    assert resolved_line.accounting_purchase_price == Decimal("10250000")
    assert resolved_line.price_source == "OWNER_MANUAL_LEGACY_CONFIRMATION"

    target_line = _line(order, TARGET_PRODUCT)
    assert target_line.accounting_purchase_price is None
    assert target_line.accounting_purchase_price != resolved_line.accounting_purchase_price
    assert target_line.price_source == PRICE_SOURCE_PENDING
    assert target_line.price_source != resolved_line.price_source


def test_bh62439_row53_reaches_existing_review_queue_missing_purchase_price():
    """§8/§17 session brief — TASK-110's Review Queue (đã wiring, KHÔNG phải
    queue mới) THỰC SỰ chứa dòng 53: `detect_missing_purchase_price`
    (`app/modules/validation/rules.py`, `config/validation.yaml`
    `missing_purchase_price.aggregate: true`) nén mọi dòng Pending thành MỘT
    `ReviewItem` cấp batch — dòng 53 phải nằm trong `source_rows` của chính
    item đó, và message/severity phải trung thực (không claim lỗi dữ liệu,
    không giấu diếm là 'Pending' hệ thống)."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    items = [
        item
        for item in result.review_queue.items
        if item.category == CATEGORY_MISSING_PURCHASE_PRICE
    ]
    assert len(items) == 1
    item = items[0]

    assert TARGET_SOURCE_ROW in item.provenance.source_rows
    assert item.severity == "INFO"
    assert "Pending" in item.message
    assert "giá nhập" in item.message  # trung thực: nói rõ THIẾU GIÁ NHẬP


def test_bh62439_row53_default_run_import_without_wiring_is_still_pending():
    """0 blast radius (Golden #3 pattern): `run_import()` PURE, không DI, vẫn
    giữ nguyên Pending cho dòng 53 — hành vi mặc định không đổi."""
    from app.pipeline import run_import

    result = run_import(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, TARGET_ORDER), TARGET_PRODUCT)
    assert line.accounting_purchase_price is None
    assert line.kpi_purchase_price is None
    assert line.eligible_kpi_profit is None
