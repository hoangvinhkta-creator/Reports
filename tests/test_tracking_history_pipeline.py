"""Reader V1 tại BIÊN pipeline — Review Queue, no silent drop, non-regression.

Ba câu hỏi mà test đơn vị của reader không trả lời được:

1. Nối reader vào `run_import()` có làm rơi mất đơn nào không? (không)
2. Kết quả không đủ thẩm quyền có thật sự vào Review Queue canonical của
   `TASK-110` không, hay chỉ biến mất? (có, qua `Missing.PurchasePrice`)
3. Bật reader lên có đổi hành vi MẶC ĐỊNH của pipeline không? (không —
   `PendingPriceProvider` vẫn là mặc định, `CHECK-105-04`)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest

from app.modules.domain.models import (
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_TRACKING_PRICE_HISTORY,
)
from app.modules.pricing.tracking_history import (
    TrackingHistoryPriceProvider,
    UnresolvedReason,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
)
from app.modules.product.identity.registry import CUTOVER_DATE
from app.modules.validation.models import CATEGORY_MISSING_PURCHASE_PRICE
from app.pipeline import run_import
from tests.fixtures.synthetic_workbook import HEADER
from tests.test_tracking_history_reader import (
    CUTOVER,
    VN,
    build_export,
    build_reader,
    event,
)

# Ba đơn sau cutover Tracking, cùng ngày bán, ba kết cục KHÁC nhau — để một
# batch duy nhất chứng minh cả ba nhánh cùng lúc.
POST_CUTOVER_ROWS = [
    # BH9001 — mã TRACKING có giá baseline -> resolve được.
    (date(2026, 9, 5), "BH9001", "Bán hàng Khách Lẻ A", "Máy giặt Tracking A1",
     "KH9001", "Khách A", "1 Đường Test", "0900000001", 1, 9_000_000,
     9_000_000, 0, "Vũ Hạnh Ly 0868345633", "Shipper A", 50_000, None, 900_000),
    # BH9002 — mã TRACKING nhưng giá đã bị XOÁ -> Pending.
    (date(2026, 9, 5), "BH9002", "Bán hàng Khách Lẻ B", "Tủ lạnh Tracking B1",
     "KH9002", "Khách B", "2 Đường Test", "0900000002", 1, 8_000_000,
     8_000_000, 0, "Lê Mạnh Hoàng 0865111533", "Shipper B", 50_000, None, 800_000),
    # BH9003 — identity PUBLIC_PURCHASE -> reader không đụng tới -> Pending.
    (date(2026, 9, 5), "BH9003", "Bán hàng Khách Lẻ C", "Bếp từ Công Khai C1",
     "KH9003", "Khách C", "3 Đường Test", "0900000003", 1, 7_000_000,
     7_000_000, 0, "Tín Phát 0869931931", "Shipper C", 50_000, None, 700_000),
]


@pytest.fixture
def post_cutover_raw_path(tmp_path: Path) -> Path:
    path = tmp_path / "post_cutover_sample.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "SỔ CHI TIẾT BÁN HÀNG"
    sheet.append(["SỔ CHI TIẾT BÁN HÀNG"])
    sheet.append(["Từ ngày 01/09/2026 đến ngày 30/09/2026"])
    sheet.append([])
    sheet.append(HEADER)
    sheet.append(["", "", "Diễn giải chung"])
    for row in POST_CUTOVER_ROWS:
        sheet.append(list(row))
    workbook.save(path)
    return path


@pytest.fixture
def tracking_provider() -> TrackingHistoryPriceProvider:
    reader = build_reader(
        build_export(
            prices={"A1": 9000, "B1": 8000},
            n_absent=1,
            events={
                # B1 bị xoá giá trước ngày bán -> CASE D.
                "B1": {
                    "E1": event(prev=8000, nxt=None,
                                at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc))
                }
            },
        )
    )
    return TrackingHistoryPriceProvider(
        reader,
        identity_index={
            "Máy giặt Tracking A1": CanonicalProductIdentity(Namespace.TRACKING, "A1"),
            "Tủ lạnh Tracking B1": CanonicalProductIdentity(Namespace.TRACKING, "B1"),
            "Bếp từ Công Khai C1": CanonicalProductIdentity(
                Namespace.PUBLIC_PURCHASE, "C1"
            ),
        },
        business_tz=VN,
    )


def _lines_by_order(result):
    return {
        line.order_id: line
        for order in result.orders
        for line in order.lines
    }


# ==================================================================== §12.13
# "Review Queue vẫn nhận unresolved result" + §12.14 "no silent drop"


def test_resolved_pending_and_not_tracking_land_in_one_batch(
    post_cutover_raw_path, config_dir, tracking_provider
):
    result = run_import(
        post_cutover_raw_path, config_dir, price_provider=tracking_provider
    )
    lines = _lines_by_order(result)

    resolved = lines["BH9001"]
    assert resolved.accounting_purchase_price == Decimal("9000000")
    assert resolved.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY

    cleared = lines["BH9002"]
    assert cleared.accounting_purchase_price is None
    assert cleared.price_source == PRICE_SOURCE_PENDING

    public = lines["BH9003"]
    assert public.accounting_purchase_price is None
    assert public.price_source == PRICE_SOURCE_PENDING


def test_no_order_is_silently_dropped(
    post_cutover_raw_path, config_dir, tracking_provider
):
    result = run_import(
        post_cutover_raw_path, config_dir, price_provider=tracking_provider
    )
    got = {order.order_id for order in result.orders}
    assert got == {row[1] for row in POST_CUTOVER_ROWS}


def test_unresolved_prices_reach_the_canonical_task110_review_queue(
    post_cutover_raw_path, config_dir, tracking_provider
):
    """KHÔNG tạo Review Queue mới — dùng đúng `Missing.PurchasePrice` sẵn có."""
    result = run_import(
        post_cutover_raw_path, config_dir, price_provider=tracking_provider
    )
    items = result.review_queue.by_category(CATEGORY_MISSING_PURCHASE_PRICE)
    assert items, "hai dòng Pending phải xuất hiện trong Review Queue canonical"

    covered = {
        row.source_row
        for item in items
        for row in item.provenance.rows
    }
    pending_rows = {
        line.raw.source_row
        for line in _lines_by_order(result).values()
        if line.price_source == PRICE_SOURCE_PENDING
    }
    assert pending_rows <= covered
    # Dòng đã resolve KHÔNG được lọt vào hàng chờ.
    resolved_row = _lines_by_order(result)["BH9001"].raw.source_row
    assert resolved_row not in covered


def test_every_pending_line_is_covered_by_the_queue_no_gap(
    post_cutover_raw_path, config_dir, tracking_provider
):
    """"Không silent drop" ở mức DÒNG, không chỉ mức đơn."""
    result = run_import(
        post_cutover_raw_path, config_dir, price_provider=tracking_provider
    )
    covered = {
        row.source_row
        for item in result.review_queue.by_category(CATEGORY_MISSING_PURCHASE_PRICE)
        for row in item.provenance.rows
    }
    for line in _lines_by_order(result).values():
        if line.price_source == PRICE_SOURCE_PENDING:
            assert line.raw.source_row in covered, (
                f"dòng {line.raw.source_row} Pending nhưng không có mục Review Queue "
                "nào phủ — đây chính là một silent drop"
            )


def test_provider_audit_trail_explains_every_pending_line(
    post_cutover_raw_path, config_dir, tracking_provider
):
    run_import(post_cutover_raw_path, config_dir, price_provider=tracking_provider)
    reasons = {r.reason for r in tracking_provider.audit_trail if not r.is_resolved}
    assert reasons == {
        UnresolvedReason.PRICE_CLEARED,
        UnresolvedReason.IDENTITY_NOT_TRACKING,
    }
    resolved = [r for r in tracking_provider.audit_trail if r.is_resolved]
    assert len(resolved) == 1
    prov = resolved[0].provenance
    assert prov.product_code == "A1"
    assert prov.raw_value_thousand_vnd == Decimal("9000")
    assert prov.resolved_price_vnd == Decimal("9000000")
    assert prov.baseline_captured_at == CUTOVER


# ==================================================================== §12.11
# Non-regression: mặc định pipeline KHÔNG đổi


def test_pipeline_default_is_still_pending_provider(
    post_cutover_raw_path, config_dir
):
    """`CHECK-105-04` — reader phải được truyền vào TƯỜNG MINH, không tự bật."""
    result = run_import(post_cutover_raw_path, config_dir)
    for line in _lines_by_order(result).values():
        assert line.accounting_purchase_price is None
        assert line.price_source == PRICE_SOURCE_PENDING


def test_synthetic_pre_cutover_batch_is_untouched_by_the_new_provider(
    synthetic_raw_path, config_dir, tracking_provider
):
    """Dòng pre-cutover đi nhánh `HistoricalConfirmedRegistry`, KHÔNG qua provider.

    Truyền reader vào cũng không được kéo được một dòng pre-cutover nào sang
    nhánh Tracking — đó đúng là "biến current price thành historical price".
    """
    result = run_import(
        synthetic_raw_path, config_dir, price_provider=tracking_provider
    )
    for line in _lines_by_order(result).values():
        assert line.price_source == PRICE_SOURCE_PENDING
    assert tracking_provider.audit_trail == ()


# ===================================================== §3 — HAI cutover riêng


def test_product_identity_cutover_is_unchanged_and_distinct():
    """`01/09/2026` (identity) và `29/08/2026 19:35:37` (giá) KHÔNG được gộp."""
    assert CUTOVER_DATE == date(2026, 9, 1)
    # Mốc giá là một THỜI ĐIỂM có múi giờ, không phải một ngày — hai khái niệm
    # khác kiểu, nên không có phép so sánh nào âm thầm hợp nhất chúng.
    assert isinstance(CUTOVER, datetime) and CUTOVER.tzinfo is not None
    assert CUTOVER.date() < CUTOVER_DATE
    with pytest.raises(TypeError):
        _ = CUTOVER < CUTOVER_DATE  # type: ignore[operator]


def test_the_gap_between_the_two_cutovers_resolves_nothing_by_itself(
    tracking_provider,
):
    """29/08 → 31/08: giá đã có mốc, nhưng identity vẫn ở nhánh lịch sử.

    Reader trả lời được cho khoảng này khi ĐƯỢC HỎI, nhưng pipeline không hỏi
    nó — `run_import` chỉ gửi dòng `sale_date >= CUTOVER_DATE` qua
    `PriceProvider`. Khoảng lệch ấy KHÔNG phải lý do để dời `01/09`.
    """
    from app.modules.pricing.tracking_history import SaleInterval

    reader = tracking_provider._reader
    out = reader.price_at("A1", SaleInterval.for_sale_date(date(2026, 8, 31), VN))
    assert out.is_resolved  # dữ liệu giá đủ thẩm quyền cho ngày này
    assert date(2026, 8, 31) < CUTOVER_DATE  # nhưng identity vẫn là nhánh lịch sử
