"""R1 XUYÊN SUỐT: Tracking tính MIN → hợp đồng → Reports → giá nhập → lợi nhuận.

## Fixture này KHÔNG được viết tay

`tests/fixtures/daily_min/tracking_contract_export.json` được sinh ra bằng
CHÍNH mã Tracking: `price-engine/src/nghiepvu.js` (luật MIN thật, kể cả lọc
NCC giá bất thường và sentinel hết-hàng) chạy qua `src/min-ngay.js`
(`chupMinNgay` → `chotNgay` → `xuatMinNgay`), rồi đóng gói đúng hình dạng mà
`tools/tracking/capture_daily_min.py` ghi ra.

Vì sao điều đó quan trọng: một payload gõ tay chỉ chứng minh Reports đọc được
thứ MÌNH TƯỞNG Tracking gửi. Cả lớp lỗi tốn kém nhất giữa hai hệ thống nằm
đúng ở khoảng cách giữa "tưởng" và "thật" — tên trường, đơn vị tiền, hình
dạng `null`, thứ tự nguồn. Fixture này đóng khoảng cách ấy.

Kịch bản dựng sẵn trong fixture (số nghìn VND, đúng đơn vị Tracking lưu):

```text
TRK-A  03/09 = 6800 (NCC Tuấn Ngoan)   04/09 = 6000   05/09 = mang mốc 04 qua
TRK-B  Tồn kho 5000 rẻ hơn mọi NCC     → nguồn INVENTORY:TON_KHO
TRK-C  hết hàng hoàn toàn              → OUT_OF_STOCK, KHÔNG phải giá 0
TRK-D  chưa NCC nào báo giá            → NO_DATA
TRK-E  một NCC báo 150 (đọc nhầm)      → bị luật lọc, MIN = 9500, có dấu vết
03/09 và 04/09 đã CHỐT; 05/09 còn PROVISIONAL.
```

Bốn câu hỏi bộ này trả lời, và chỉ đường xuyên suốt mới trả lời được:

1. Một đơn bán 03/09, nạp sổ ngày 30/09, có ra đúng giá của 03/09 không?
2. Con số ấy có đi hết tới `AccountingProfit`/`KpiPurchasePrice` không?
3. Provenance có trỏ ngược về ĐÚNG bản ghi Tracking đã quyết định không?
4. Lịch sử `tp/ton` cũ có bị chọn làm MIN ở đâu không?
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest

from app.modules.domain.models import (
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_TRACKING_DAILY_MIN,
    PRICE_SOURCE_TRACKING_PRICE_HISTORY,
)
from app.modules.pricing.daily_min import (
    DailyMinUnresolvedReason,
    DayStatus,
    SourceType,
    load_daily_min_capture,
)
from app.modules.pricing.resolution.composition import (
    CompositionRule,
    PostCutoverPriceComposition,
    PriceResolutionReason,
)
from app.modules.pricing.resolution.sources import PriceResolutionSources
from app.modules.product.identity.store import JsonlProductIdentityStore
from app.modules.validation.models import CATEGORY_MISSING_PURCHASE_PRICE
from app.pipeline import run_import
from tests.fixtures.synthetic_workbook import HEADER
from tests.test_105e_price_composition import write_catalog_capture, write_history_capture
from tests.test_tracking_history_reader import build_export

CONTRACT_FIXTURE = (
    Path(__file__).parent / "fixtures" / "daily_min" / "tracking_contract_export.json"
)

SALE_DAY = date(2026, 9, 3)
"""Ngày bán. Fixture cố ý có một giá KHÁC ở 04/09 để một phép "lấy bản mới
nhất" lộ ra ngay thành một con số khác."""

CATALOG = [
    {"tracking_code": code, "name": code, "alt": [], "present_in_board": True}
    for code in ("TRK-A", "TRK-B", "TRK-C", "TRK-D", "TRK-E")
]

ROWS = [
    # (mã đơn, tên hàng trên chứng từ, SL, giá bán) — tên hàng chuẩn hoá về
    # đúng khoá `board`, tức đúng đường identity production (S068).
    ("BH7001", "TRK-A", 1, 9_000_000),
    ("BH7002", "TRK-B", 2, 7_000_000),
    ("BH7003", "TRK-C", 1, 8_000_000),
    ("BH7004", "TRK-D", 1, 8_000_000),
    ("BH7005", "TRK-E", 1, 12_000_000),
]


def write_sales(path: Path, rows, day: date = SALE_DAY) -> Path:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "SỔ CHI TIẾT BÁN HÀNG"
    sheet.append(["SỔ CHI TIẾT BÁN HÀNG"])
    sheet.append(["Từ ngày 01/09/2026 đến ngày 30/09/2026"])
    sheet.append([])
    sheet.append(HEADER)
    sheet.append(["", "", "Diễn giải chung"])
    for order_id, product, quantity, sell in rows:
        sheet.append([
            day, order_id, f"Bán hàng {order_id}", product, f"KH{order_id}",
            f"Khách {order_id}", "1 Đường Test", "0900000000", quantity, sell,
            sell * quantity, 0, "Vũ Hạnh Ly 0868345633", "Shipper", 0, None, None,
        ])
        sheet.cell(sheet.max_row, 4).data_type = "s"
    workbook.save(path)
    workbook.close()
    return path


@pytest.fixture
def daily_min_capture() -> Path:
    return CONTRACT_FIXTURE


@pytest.fixture
def sales_path(tmp_path: Path) -> Path:
    return write_sales(tmp_path / "sales.xlsx", ROWS)


def build(tmp_path: Path, *, daily_min: Path | None, with_history: bool = True,
          legacy: bool = False) -> PostCutoverPriceComposition:
    """Dựng composition QUA ĐÚNG các loader production."""
    store = JsonlProductIdentityStore(log_path=tmp_path / "identity.jsonl")
    from app.modules.pricing.resolution.sources import load_business_timezone
    from app.modules.pricing.tracking_history.capture_file import (
        load_tracking_price_history_capture,
    )
    from app.modules.pricing.resolution.sources import load_tracking_catalog_capture

    history = None
    if with_history:
        # Lịch sử `tp/ton` CÓ MẶT và CÓ GIÁ cho cùng những mã ấy — cố ý. Nếu
        # một nhánh nào đó lỡ rơi về nó, con số sẽ khác hẳn MIN và bài kiểm
        # thấy ngay. Một fixture để nguồn cũ trống rỗng sẽ không phân biệt
        # được "không dùng nó" với "không có gì để dùng".
        history = load_tracking_price_history_capture(write_history_capture(
            tmp_path, build_export(prices={code["tracking_code"]: 4_444 for code in CATALOG}),
        ))
    return PostCutoverPriceComposition(PriceResolutionSources(
        business_timezone=load_business_timezone(Path("config")),
        tracking_price_history=history,
        tracking_catalog=load_tracking_catalog_capture(
            write_catalog_capture(tmp_path, CATALOG)
        ),
        tracking_inv_map=None,
        public_purchase=None,
        identity_store_view=store.read_at_revision(store.current_revision()),
        tracking_identity_authority=True,
        tracking_daily_min=(
            load_daily_min_capture(daily_min) if daily_min is not None else None
        ),
        legacy_tracking_history_authority=legacy,
    ))


def run(sales_path: Path, composition: PostCutoverPriceComposition):
    return run_import(sales_path, config_dir=Path("config"),
                      price_composition=composition)


def lines_by_order(result) -> dict:
    return {
        order.order_id: list(order.lines) for order in result.orders
    }


def record_for(composition, order_id: str):
    return next(r for r in composition.records if r.order_id == order_id)


# ======================================================================
# 0. Fixture đúng là thứ Tracking sinh ra
# ======================================================================


def test_the_fixture_is_a_real_tracking_contract_envelope():
    """Nếu ai đó sửa tay fixture cho một bài xanh lại, bài này đỏ trước."""
    payload = json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))
    assert payload["capture_status"] == "COMPLETE"
    assert payload["source_system_ref"] == "tracking/api/min-ngay"
    data = payload["data"]
    assert data["schema_version"] == "daily-min-v1"
    assert data["currency_unit"] == "VND_THOUSAND"
    assert data["business_timezone"] == "Asia/Ho_Chi_Minh"
    assert (data["date_from"], data["date_to"]) == ("2026-09-03", "2026-09-05")
    # Giá của TRK-A ĐỔI giữa hai ngày — điều kiện để câu hỏi "ngày nào" có
    # nghĩa. Một fixture cùng giá mọi ngày sẽ xanh với cả một triển khai sai.
    by_day = {
        r["effective_date"]: r["min_price"]
        for r in data["records"] if r["product_code"] == "TRK-A"
    }
    assert by_day == {"2026-09-03": 6800, "2026-09-04": 6000, "2026-09-05": 6000}


def test_the_fixture_loads_through_the_production_loader(daily_min_capture):
    snap = load_daily_min_capture(daily_min_capture)
    assert snap.capture_status.value == "COMPLETE"
    assert snap.covers(SALE_DAY)
    a = snap.record_for("TRK-A", SALE_DAY)
    assert a.min_price_thousand_vnd == Decimal("6800")
    assert a.min_sources[0].source_type is SourceType.SUPPLIER
    assert a.day_status is DayStatus.FINAL


# ======================================================================
# 1. Câu hỏi trung tâm: ngày bán, không phải ngày chạy
# ======================================================================


def test_a_sale_on_03_09_is_priced_with_the_03_09_mark(tmp_path, sales_path,
                                                        daily_min_capture):
    """Nạp sổ lúc nào không quan trọng — 6.800 nghìn là giá của ngày bán.

    Fixture có 6.000 ở 04/09; nếu đường mã lấy "bản mới nhất" thì con số ở đây
    là 6.000.000 chứ không phải 6.800.000, và cả bài này lẫn lợi nhuận bên
    dưới cùng đỏ.
    """
    comp = build(tmp_path, daily_min=daily_min_capture)
    result = run(sales_path, comp)
    line = lines_by_order(result)["BH7001"][0]
    assert line.accounting_purchase_price == Decimal("6800000")
    assert line.price_source == PRICE_SOURCE_TRACKING_DAILY_MIN


def test_the_price_reaches_profit_and_the_kpi_purchase_price(tmp_path, sales_path,
                                                             daily_min_capture):
    """Giá nhập không dừng ở một ô — nó đi vào lợi nhuận, rồi vào KPI.

    `AccountingProfit = (giá bán − giá nhập) × SL`. Ở đây: (9.000.000 −
    6.800.000) × 1 = 2.200.000.
    """
    comp = build(tmp_path, daily_min=daily_min_capture)
    result = run(sales_path, comp)
    line = lines_by_order(result)["BH7001"][0]
    assert line.accounting_profit == Decimal("2200000")
    # `KpiPurchasePrice` chở đúng giá ấy khi không có điều chỉnh đã xác nhận;
    # nguồn điều chỉnh chưa được nối trong lần chạy này nên nó Pending — và
    # ĐÓ là hành vi đúng (`DEC-144` §3), không phải một khiếm khuyết.
    assert line.kpi_purchase_price is None
    assert line.kpi_purchase_price_provenance == "Pending"


def test_a_price_from_a_different_day_is_never_used(tmp_path, daily_min_capture):
    """Cùng mã, cùng ảnh chụp, đổi MỖI ngày bán ⇒ phải ra con số khác."""
    for day, expected in ((date(2026, 9, 3), "6800000"), (date(2026, 9, 4), "6000000")):
        tmp = tmp_path / day.isoformat()
        tmp.mkdir()
        comp = build(tmp, daily_min=daily_min_capture)
        result = run(write_sales(tmp / "s.xlsx", ROWS[:1], day=day), comp)
        line = lines_by_order(result)["BH7001"][0]
        assert line.accounting_purchase_price == Decimal(expected), day


# ======================================================================
# 2. Nguồn thắng, luật lọc, và dấu vết đi hết đường
# ======================================================================


def test_the_inventory_source_wins_and_says_so(tmp_path, sales_path, daily_min_capture):
    """TRK-B: ô Tồn rẻ hơn mọi NCC. Con số ĐÚNG và nguồn NÓI ĐÚNG nó từ đâu."""
    comp = build(tmp_path, daily_min=daily_min_capture)
    result = run(sales_path, comp)
    assert lines_by_order(result)["BH7002"][0].accounting_purchase_price == Decimal(
        "5000000"
    )
    prov = record_for(comp, "BH7002").daily_min_resolution.provenance
    assert prov.min_sources == ("INVENTORY:TON_KHO",)


def test_an_abnormally_low_vendor_price_never_becomes_the_cost(tmp_path, sales_path,
                                                               daily_min_capture):
    """TRK-E: một NCC báo 150 nghìn cho một mặt hàng 9.500 nghìn — đọc nhầm số
    trong ngoặc, đúng sự cố đã xảy ra thật bên Tracking. Luật lọc của Tracking
    loại nó, và Reports nhận đúng con số đã lọc chứ không tự lọc lại."""
    comp = build(tmp_path, daily_min=daily_min_capture)
    result = run(sales_path, comp)
    assert lines_by_order(result)["BH7005"][0].accounting_purchase_price == Decimal(
        "9500000"
    )


def test_the_provenance_points_back_at_the_exact_tracking_record(
    tmp_path, sales_path, daily_min_capture
):
    """Mở lại một dòng phải ra đúng bản ghi Tracking đã quyết định nó."""
    comp = build(tmp_path, daily_min=daily_min_capture)
    run(sales_path, comp)
    record = record_for(comp, "BH7001")
    assert record.rule is CompositionRule.TRACKING_DAILY_MIN

    payload = json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))
    source = next(
        r for r in payload["data"]["records"]
        if r["product_code"] == "TRK-A" and r["effective_date"] == "2026-09-03"
    )
    prov = record.daily_min_resolution.provenance
    assert prov.revision == source["revision"]
    assert prov.source_fingerprint == source["source_fingerprint"]
    assert prov.rule_version == source["rule_version"]
    assert prov.raw_value_thousand_vnd == Decimal(str(source["min_price"]))
    assert prov.resolved_price_vnd == Decimal("6800000")
    assert record.evidence.tracking_daily_min_capture_id == payload["capture_id"]


# ======================================================================
# 3. Thiếu bằng chứng ⇒ Pending có lý do, không có con số nào bị bịa
# ======================================================================


@pytest.mark.parametrize(
    "order_id, expected",
    [
        ("BH7003", DailyMinUnresolvedReason.OUT_OF_STOCK),
        ("BH7004", DailyMinUnresolvedReason.NO_DATA),
    ],
)
def test_a_priceless_day_never_becomes_a_zero_cost(
    tmp_path, sales_path, daily_min_capture, order_id, expected
):
    """Hết hàng hoàn toàn và chưa có dữ liệu là HAI chuyện, và không chuyện nào
    là "mua được với giá 0 đồng" — con số ấy sẽ làm lợi nhuận bằng đúng doanh
    thu trên mọi dòng của mã đó."""
    comp = build(tmp_path, daily_min=daily_min_capture)
    result = run(sales_path, comp)
    line = lines_by_order(result)[order_id][0]
    assert line.accounting_purchase_price is None
    assert line.accounting_profit is None
    assert line.price_source == PRICE_SOURCE_PENDING
    record = record_for(comp, order_id)
    assert record.reason is PriceResolutionReason.TRACKING_DAILY_MIN_PENDING
    assert record.daily_min_resolution.reason is expected


def test_every_pending_line_is_covered_by_the_canonical_review_queue(
    tmp_path, sales_path, daily_min_capture
):
    """Không dòng nào biến mất: mọi dòng chưa có giá đều có một mục Review
    Queue canonical (`TASK-110`) phủ nó."""
    comp = build(tmp_path, daily_min=daily_min_capture)
    result = run(sales_path, comp)
    pending_rows = {
        line.raw.source_row
        for order in result.orders for line in order.lines
        if line.accounting_purchase_price is None
    }
    queued_rows = {
        row.source_row
        for item in result.review_queue.items
        if item.category == CATEGORY_MISSING_PURCHASE_PRICE
        for row in item.provenance.rows
    }
    assert pending_rows
    assert pending_rows <= queued_rows


def test_an_unwired_source_is_not_a_conclusion_about_price(tmp_path, sales_path):
    """Chưa chạy công cụ chụp KHÁC "mặt hàng không có giá".

    Hai câu ấy dẫn tới hai việc khác nhau, nên chúng có hai mã lý do khác nhau.
    """
    comp = build(tmp_path, daily_min=None)
    result = run(sales_path, comp)
    assert all(
        line.accounting_purchase_price is None
        for order in result.orders for line in order.lines
    )
    record = record_for(comp, "BH7001")
    assert record.reason is (
        PriceResolutionReason.TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE
    )
    # Thông điệp chỉ đúng việc phải làm, không bắt người đọc đi tìm.
    assert "capture_daily_min.py" in record.detail


def test_a_sale_outside_the_captured_window_stays_pending(tmp_path, daily_min_capture):
    """Ảnh chụp phủ 03–05/09; một đơn ngày 20/09 KHÔNG được lấy mốc cuối cùng."""
    sales = write_sales(tmp_path / "muon.xlsx", ROWS[:1], day=date(2026, 9, 20))
    comp = build(tmp_path, daily_min=daily_min_capture)
    result = run(sales, comp)
    assert lines_by_order(result)["BH7001"][0].accounting_purchase_price is None
    assert record_for(comp, "BH7001").daily_min_resolution.reason is (
        DailyMinUnresolvedReason.SALE_DATE_OUTSIDE_CAPTURE
    )


# ======================================================================
# 4. Nhánh cũ `tp/ton` KHÔNG được chọn làm MIN
# ======================================================================


def test_the_legacy_tp_ton_history_is_never_the_default_price_source(
    tmp_path, sales_path, daily_min_capture
):
    """Lịch sử `tp/ton` có mặt, có giá (4.444 nghìn), và KHÔNG được dùng.

    Đây là bài canh thẳng vào thay đổi thẩm quyền của R1. Hai đại lượng đều là
    số tiền hợp lệ, nên nếu nhánh cũ lỡ chạy thì không có gì đỏ lên ngoài bài
    này.
    """
    comp = build(tmp_path, daily_min=daily_min_capture, with_history=True)
    result = run(sales_path, comp)
    prices = {
        order_id: lines[0].accounting_purchase_price
        for order_id, lines in lines_by_order(result).items()
    }
    assert Decimal("4444000") not in prices.values()
    assert prices["BH7001"] == Decimal("6800000")
    sources = {
        line.price_source
        for order in result.orders for line in order.lines
    }
    assert PRICE_SOURCE_TRACKING_PRICE_HISTORY not in sources


def test_without_a_daily_min_source_nothing_falls_back_to_the_old_history(
    tmp_path, sales_path
):
    """Nguồn mới chưa nối cũng KHÔNG mở đường cho nguồn cũ.

    Đây là chỗ một "fallback cho đỡ trống" trông hợp lý nhất, và cũng là chỗ
    nó nguy hiểm nhất: báo cáo sẽ đầy số, không dòng nào Pending, và mọi con
    số là của một đại lượng khác.
    """
    comp = build(tmp_path, daily_min=None, with_history=True)
    result = run(sales_path, comp)
    assert all(
        line.price_source == PRICE_SOURCE_PENDING
        for order in result.orders for line in order.lines
    )


def test_the_legacy_path_still_works_when_a_caller_asks_for_it_by_name(
    tmp_path, sales_path
):
    """Nhánh cũ KHÔNG bị xoá — nó vẫn đúng và vẫn cần để mở lại kết quả cũ.

    Nó chỉ không còn là mặc định, và bật nó phải là một câu lệnh tường minh.
    """
    comp = build(tmp_path, daily_min=None, with_history=True, legacy=True)
    result = run(sales_path, comp)
    line = lines_by_order(result)["BH7001"][0]
    assert line.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    assert line.accounting_purchase_price == Decimal("4444000")


# ======================================================================
# 5. PROVISIONAL — kỳ còn dùng bản tạm thì chưa chốt được
# ======================================================================


def test_an_empty_report_is_not_a_finished_period(tmp_path, daily_min_capture):
    """Kỳ RỖNG không phải kỳ đã xong — nó là một kỳ chưa có gì.

    `resolved_prices_are_final` trả `True` ở đây và đúng theo nghĩa hẹp của
    nó ("không giá nào đến từ ngày chưa chốt", vì không có giá nào). Chính vì
    câu ấy đúng mà nó KHÔNG dùng làm cổng chốt kỳ được: hai tình huống dẫn tới
    hai việc khác nhau — trình bày kết quả, hay đi tìm xem sổ bán hàng đâu.
    """
    comp = build(tmp_path, daily_min=daily_min_capture)
    run(write_sales(tmp_path / "rong.xlsx", [], day=SALE_DAY), comp)
    report = comp.report
    assert report.records == ()
    assert report.resolved_prices_are_final     # đúng, và vô nghĩa ở đây
    assert not report.has_priceable_lines
    assert not report.period_is_final


def test_a_report_where_every_line_is_pending_is_not_a_finished_period(tmp_path):
    """Chưa nối nguồn giá ⇒ mọi dòng Pending. Cổng cấp kỳ phải nói KHÔNG.

    Đây là hình dạng nguy hiểm nhất của bản trước: một kỳ chưa có LẤY MỘT giá
    vốn nào vẫn trả `True` cho cờ mang tên `prices_are_final`, và bất kỳ cổng
    "kỳ đã chốt" nào xây trên đó sẽ mở ra cho đúng kỳ tệ nhất.
    """
    comp = build(tmp_path, daily_min=None)
    run(write_sales(tmp_path / "pending.xlsx", ROWS, day=SALE_DAY), comp)
    report = comp.report
    assert report.resolved_count == 0
    assert report.pending_count == len(ROWS)
    assert report.resolved_prices_are_final     # đúng, và vô nghĩa ở đây
    assert report.has_priceable_lines
    assert not report.period_is_final


def test_a_period_with_every_line_priced_from_a_final_day_is_finished(tmp_path,
                                                                      daily_min_capture):
    """Ca DUY NHẤT được gọi là đã chốt: có dữ liệu, không Pending, không tạm."""
    comp = build(tmp_path, daily_min=daily_min_capture)
    run(write_sales(tmp_path / "du.xlsx", ROWS[:2], day=SALE_DAY), comp)
    report = comp.report
    assert (report.resolved_count, report.pending_count, report.provisional_count) == (
        2, 0, 0)
    assert report.period_is_final


def test_one_provisional_line_keeps_the_whole_period_open(tmp_path, daily_min_capture):
    """Một dòng lấy giá của ngày chưa chốt là đủ để cả kỳ chưa chốt được."""
    comp = build(tmp_path, daily_min=daily_min_capture)
    run(write_sales(tmp_path / "tam2.xlsx", ROWS[:2], day=date(2026, 9, 5)), comp)
    report = comp.report
    assert report.pending_count == 0
    assert report.provisional_count == 2
    assert not report.period_is_final


def test_a_period_priced_from_a_provisional_day_is_not_final(tmp_path, daily_min_capture):
    """05/09 trong fixture còn PROVISIONAL. Giá vẫn ra, nhưng báo cáo phải
    tiếp tục nói rằng con số ấy chưa cuối cùng."""
    sales = write_sales(tmp_path / "tam.xlsx", ROWS[:1], day=date(2026, 9, 5))
    comp = build(tmp_path, daily_min=daily_min_capture)
    result = run(sales, comp)
    line = lines_by_order(result)["BH7001"][0]
    assert line.accounting_purchase_price == Decimal("6000000")

    report = comp.report
    assert report.evidence.tracking_daily_min_capture_id
    assert report.provisional_count == 1
    assert not report.resolved_prices_are_final
    assert report.provisional_records[0].daily_min_resolution.is_provisional


def test_a_period_priced_only_from_final_days_is_final(tmp_path, daily_min_capture):
    comp = build(tmp_path, daily_min=daily_min_capture)
    run(write_sales(tmp_path / "chot.xlsx", ROWS[:1], day=SALE_DAY), comp)
    report = comp.report
    assert report.resolved_count == 1
    assert report.provisional_count == 0
    assert report.resolved_prices_are_final
    assert all(
        r.daily_min_resolution.provenance.day_status is DayStatus.FINAL
        for r in report.records if r.is_resolved
    )
