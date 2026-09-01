"""`TASK-105E` — composition `P00–P11` tại BIÊN PRODUCTION THẬT.

Test đơn vị của từng provider không trả lời được câu hỏi của phiên này:
**pipeline production có thật sự gọi đúng nguồn, đúng thứ tự, và có giữ
nguyên fail-safe khi nó làm vậy không.** Mỗi test dưới đây là một câu khẳng
định về hành vi của `run_import()`/`run_import_production()` khi composition
đã được nối, không phải về một hàm cô lập.

Ba trục được kiểm liên tục vì chúng là chỗ một lỗi trở nên vô hình:

1. Định tuyến namespace — `TRACKING` và `PUBLIC_PURCHASE` không bao giờ
   tráo chỗ, kể cả khi mã trùng chuỗi.
2. Nguồn CHƯA CÓ khác GIÁ KHÔNG TỒN TẠI — không nhánh nào biến cái thứ nhất
   thành cái thứ hai, và không nhánh nào biến cái nào thành `0`.
3. Không dòng nào biến mất — mọi Pending đều có một mục Review Queue canonical
   của `TASK-110` phủ nó.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest
import yaml

from app.composition import build_price_composition, run_import_production
from app.modules.domain.models import (
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING,
    PRICE_SOURCE_PUBLIC_PURCHASE_NO_VENDOR_PRICE,
    PRICE_SOURCE_TRACKING_PRICE_HISTORY,
)
from app.modules.pricing.resolution.composition import (
    PRICE_SOURCE_BY_RULE,
    CompositionRule,
    PostCutoverPriceComposition,
    PriceResolutionReason,
)
from app.modules.pricing.resolution.sources import (
    BusinessTimezone,
    PriceResolutionSources,
    load_business_timezone,
    load_tracking_catalog_capture,
    InvalidTrackingCatalogCaptureFileError,
)
from app.modules.pricing.tracking_history.capture_file import (
    InvalidTrackingPriceCaptureFileError,
    load_tracking_price_history_capture,
)
from app.modules.pricing.tracking_history.reader import UnresolvedReason
from app.modules.pricing.tracking_history.snapshot import (
    CaptureStatus,
    TrackingCaptureFailedError,
    TrackingPriceHistorySnapshot,
)
from app.modules.product.identity.cli import confirm_cross_system
from app.modules.product.identity.identity import Namespace
from app.modules.product.identity.public_purchase import PublicPurchaseSourceLoader
from app.modules.product.identity.registry import CUTOVER_DATE
from app.modules.validation.models import CATEGORY_MISSING_PURCHASE_PRICE
from app.pipeline import run_import
from tests.fixtures.synthetic_workbook import HEADER
from tests.support import identity_fixtures as fx
from tests.test_tracking_history_reader import (
    CUTOVER,
    VN,
    build_export,
    event,
)

SALE_DAY = date(2026, 9, 5)
"""Sau CẢ HAI mốc: sau cutover dữ liệu Tracking (29/08) và sau cutover Product
Identity (01/09). Chỉ ở đây nhánh post-cutover mới hợp lệ."""


# ======================================================================
# Dựng nguồn — mọi thứ đi qua đúng loader production, không dựng tắt
# ======================================================================


def write_history_capture(
    tmp_path: Path,
    export: dict,
    *,
    capture_id: str = "PPH-20260929T120000Z-aaaa",
    captured_at: datetime | None = None,
    capture_status: str = "COMPLETE",
    failure_reason: str | None = None,
) -> Path:
    path = tmp_path / "tracking_price_history.json"
    payload = {
        "capture_id": capture_id,
        "captured_at": (captured_at or CUTOVER + timedelta(days=30)).isoformat(),
        "captured_by": "reports-capture-tool",
        "source_system_ref": "tracking/rtdb",
        "capture_status": capture_status,
        "data": export,
    }
    if failure_reason is not None:
        payload["failure_reason"] = failure_reason
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_catalog_capture(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "tracking_catalog.json"
    path.write_text(
        json.dumps(
            {
                "capture_id": fx.CAPTURE_A,
                "captured_at": datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
                "captured_by": "reports-capture-tool",
                "source_system_ref": "tracking/rtdb",
                "content_hash": "hash-cat-1",
                "capture_status": "COMPLETE",
                "rows": rows,
            }
        ),
        encoding="utf-8",
    )
    return path


def write_public_purchase(tmp_path: Path, products: list[dict], prices: list[dict]):
    path = tmp_path / "public_purchase.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "source_id": "PUBLIC_PURCHASE",
                "version_id": fx.PP_V1,
                "status": "PUBLISHED",
                "products": products,
                "prices": prices,
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return path


CATALOG_ROWS = [
    {"tracking_code": "A1", "name": "Máy giặt Tracking A1", "alt": [],
     "present_in_board": True},
    {"tracking_code": "B1", "name": "Tủ lạnh Tracking B1", "alt": [],
     "present_in_board": True},
    {"tracking_code": "D1", "name": "Máy sấy Tracking D1", "alt": [],
     "present_in_board": True},
]

PP_PRODUCTS = [
    # `PublicPurchaseSourceVersion.exact_match_codes` khớp EXACT trên
    # `product_code` và `aliases` — `product_name` KHÔNG phải khoá khớp.
    {"product_code": "C1", "product_name": "Bếp từ Công Khai C1",
     "aliases": ["Bếp từ Công Khai C1"]},
    {"product_code": "A1", "product_name": "Hàng công khai trùng mã A1"},
]

PP_PRICES = [
    {"product_key": "C1", "effective_from": date(2026, 9, 1),
     "effective_to": date(2026, 12, 31), "purchase_price": "5500000"},
    {"product_key": "A1", "effective_from": date(2026, 9, 1),
     "effective_to": date(2026, 12, 31), "purchase_price": "111000"},
]

DEFAULT_EXPORT = build_export(
    prices={"A1": 9000, "B1": 8000, "D1": 4200},
    n_absent=1,
    events={
        # B1: giá bị XOÁ trước ngày bán -> CASE D -> Pending, không lấy giá cũ.
        "B1": {
            "E1": event(prev=8000, nxt=None,
                        at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc))
        }
    },
)


def build_sources(
    tmp_path: Path,
    *,
    export: dict | None = None,
    catalog_rows: list[dict] | None = None,
    pp_products: list[dict] | None = None,
    pp_prices: list[dict] | None = None,
    history_captured_at: datetime | None = None,
    with_history: bool = True,
    with_catalog: bool = True,
    with_public_purchase: bool = True,
    timezone_config: Path | None = None,
    store=None,
) -> PriceResolutionSources:
    """Dựng `PriceResolutionSources` QUA ĐÚNG các loader production."""
    history = None
    if with_history:
        history = load_tracking_price_history_capture(
            write_history_capture(
                tmp_path,
                DEFAULT_EXPORT if export is None else export,
                captured_at=history_captured_at,
            )
        )
    catalog = None
    if with_catalog:
        catalog = load_tracking_catalog_capture(
            write_catalog_capture(
                tmp_path, CATALOG_ROWS if catalog_rows is None else catalog_rows
            )
        )
    pp = None
    if with_public_purchase:
        pp = PublicPurchaseSourceLoader.load(
            yaml.safe_load(
                write_public_purchase(
                    tmp_path,
                    PP_PRODUCTS if pp_products is None else pp_products,
                    PP_PRICES if pp_prices is None else pp_prices,
                ).read_text(encoding="utf-8")
            )
        )
    a_store = store if store is not None else fx.store()
    tz = (
        load_business_timezone(timezone_config)
        if timezone_config is not None
        else BusinessTimezone(
            is_valid=True, tzinfo=VN, label="UTC+07:00", provenance="test"
        )
    )
    return PriceResolutionSources(
        business_timezone=tz,
        tracking_price_history=history,
        tracking_catalog=catalog,
        public_purchase=pp,
        identity_store_view=a_store.read_at_revision(a_store.current_revision()),
    )


def composition(tmp_path: Path, **kwargs) -> PostCutoverPriceComposition:
    return PostCutoverPriceComposition(build_sources(tmp_path, **kwargs))


# ---------------------------------------------------------------- workbook

ROWS_POST_CUTOVER = [
    # BH9001 — TRACKING A1, có giá baseline -> RESOLVED (9.000 nghìn -> 9.000.000).
    (SALE_DAY, "BH9001", "Bán hàng Khách Lẻ A", "Máy giặt Tracking A1",
     "KH9001", "Khách A", "1 Đường Test", "0900000001", 1, 12_000_000,
     12_000_000, 0, "Vũ Hạnh Ly 0868345633", "Shipper A", 50_000, None, 3_000_000),
    # BH9002 — TRACKING B1, giá đã bị xoá -> Pending.
    (SALE_DAY, "BH9002", "Bán hàng Khách Lẻ B", "Tủ lạnh Tracking B1",
     "KH9002", "Khách B", "2 Đường Test", "0900000002", 1, 8_000_000,
     8_000_000, 0, "Lê Mạnh Hoàng 0865111533", "Shipper B", 50_000, None, 800_000),
    # BH9003 — PUBLIC_PURCHASE C1 -> giá công khai theo sale_date.
    (SALE_DAY, "BH9003", "Bán hàng Khách Lẻ C", "Bếp từ Công Khai C1",
     "KH9003", "Khách C", "3 Đường Test", "0900000003", 1, 7_000_000,
     7_000_000, 0, "Tín Phát 0869931931", "Shipper C", 50_000, None, 700_000),
    # BH9004 — hai dòng: một resolve được, một Pending. Cùng một đơn.
    (SALE_DAY, "BH9004", "Bán hàng Khách Lẻ D", "Máy sấy Tracking D1",
     "KH9004", "Khách D", "4 Đường Test", "0900000004", 2, 6_000_000,
     12_000_000, 100_000, "Vũ Hạnh Ly 0868345633", "Shipper D", 50_000, None, 900_000),
    (SALE_DAY, "BH9004", "Bán hàng Khách Lẻ D", "Hàng hoàn toàn vô danh XYZ",
     "KH9004", "Khách D", "4 Đường Test", "0900000004", 1, 1_000_000,
     1_000_000, 0, "Vũ Hạnh Ly 0868345633", "Shipper D", 0, None, 100_000),
]


def write_workbook(path: Path, rows) -> Path:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "SỔ CHI TIẾT BÁN HÀNG"
    sheet.append(["SỔ CHI TIẾT BÁN HÀNG"])
    sheet.append(["Từ ngày 01/09/2026 đến ngày 30/09/2026"])
    sheet.append([])
    sheet.append(HEADER)
    sheet.append(["", "", "Diễn giải chung"])
    for row in rows:
        sheet.append(list(row))
    workbook.save(path)
    return path


@pytest.fixture
def post_cutover_raw_path(tmp_path: Path) -> Path:
    return write_workbook(tmp_path / "post_cutover.xlsx", ROWS_POST_CUTOVER)


def lines_by_order(result) -> dict:
    out: dict = {}
    for order in result.orders:
        for line in order.lines:
            out.setdefault(order.order_id, []).append(line)
    return out


def run(raw_path, config_dir, comp):
    """Chạy `run_import()` với ĐỦ các nguồn mà `run_import_production()` nạp.

    Cố ý không gọi thẳng `run_import_production()`: các test dưới đây cần thay
    NGUỒN GIÁ bằng fixture (repo chưa có capture production nào), còn ba nguồn
    kia phải là nguồn canonical thật để đường `KpiPurchasePrice`/`TASK-108B`
    được đi qua đúng như production, không phải một nhánh test riêng.
    """
    from app.modules.adjustment.confirmed_adjustment_source import (
        load_confirmed_adjustments_from_jsonl,
    )
    from app.modules.kpi.kpi_profit_engine import load_eligible_costs_authority
    from app.modules.product.identity.registry_store import load_registry_from_jsonl
    from app.composition import (
        CONFIRMED_ADJUSTMENTS_PATH,
        ELIGIBLE_COSTS_PATH,
        HISTORICAL_REGISTRY_PATH,
    )

    return run_import(
        raw_path,
        config_dir,
        identity_registry=load_registry_from_jsonl(HISTORICAL_REGISTRY_PATH),
        confirmed_adjustment_source=load_confirmed_adjustments_from_jsonl(
            CONFIRMED_ADJUSTMENTS_PATH
        ),
        eligible_costs_authority=load_eligible_costs_authority(ELIGIBLE_COSTS_PATH),
        price_composition=comp,
    )


# ======================================================================
# 1/5 — TRACKING resolved đi đúng đường KpiPurchasePrice, reader THẬT được gọi
# ======================================================================


def test_tracking_resolved_reaches_the_kpi_purchase_price_path(
    post_cutover_raw_path, config_dir, tmp_path
):
    comp = composition(tmp_path)
    result = run(post_cutover_raw_path, config_dir, comp)
    line = lines_by_order(result)["BH9001"][0]

    assert line.accounting_purchase_price == Decimal("9000000")
    assert line.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    # `AccountingProfit` và `KpiPurchasePrice` phải đi tiếp từ chính con số đó.
    assert line.accounting_profit == Decimal("3000000")
    assert line.kpi_purchase_price == Decimal("9000000")
    assert line.eligible_kpi_profit == Decimal("3000000")


def test_the_tracking_history_reader_is_actually_invoked_post_cutover(
    post_cutover_raw_path, config_dir, tmp_path
):
    """`TASK-105E` §25.5 — reader không còn là mã đứng riêng.

    Bằng chứng phải là dấu vết CỦA CHÍNH reader, không phải một con số trùng
    hợp: mọi bản ghi TRACKING mang một `PriceReconstruction` có
    `snapshot_capture_id` của đúng ảnh chụp đã nạp.
    """
    comp = composition(tmp_path)
    run(post_cutover_raw_path, config_dir, comp)

    tracking = [r for r in comp.records if r.identity is not None
                and r.identity.namespace is Namespace.TRACKING]
    assert len(tracking) == 3  # A1, B1, D1
    for record in tracking:
        assert record.tracking_reconstruction is not None
        assert (
            record.tracking_reconstruction.provenance.snapshot_capture_id
            == "PPH-20260929T120000Z-aaaa"
        )


# ======================================================================
# 2 — TRACKING unresolved -> Missing.PurchasePrice -> Review Queue TASK-110
# ======================================================================


def test_unresolved_tracking_reaches_the_canonical_task110_review_queue(
    post_cutover_raw_path, config_dir, tmp_path
):
    comp = composition(tmp_path)
    result = run(post_cutover_raw_path, config_dir, comp)

    pending_line = lines_by_order(result)["BH9002"][0]
    assert pending_line.accounting_purchase_price is None
    assert pending_line.price_source == PRICE_SOURCE_PENDING

    categories = {item.category for item in result.review_queue.items}
    assert CATEGORY_MISSING_PURCHASE_PRICE in categories
    assert len(categories) >= 1


def test_stale_tracking_capture_cannot_emit_kpi_price_or_profit(tmp_path, config_dir):
    """The normal production composition turns a terminal authority gap into TASK-110."""
    comp = composition(
        tmp_path,
        history_captured_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )
    raw = write_workbook(tmp_path / "stale_capture.xlsx", [ROWS_POST_CUTOVER[0]])
    result = run(raw, config_dir, comp)

    line = lines_by_order(result)["BH9001"][0]
    assert line.accounting_purchase_price is None
    assert line.kpi_purchase_price is None
    assert line.eligible_kpi_profit is None
    assert line.price_source == PRICE_SOURCE_PENDING
    assert comp.records[0].tracking_reconstruction.reason is (
        UnresolvedReason.SNAPSHOT_DOES_NOT_COVER_SALE_INTERVAL
    )
    assert any(
        item.category == CATEGORY_MISSING_PURCHASE_PRICE
        and line.raw.source_row in {row.source_row for row in item.provenance.rows}
        for item in result.review_queue.items
    )


def test_every_pending_line_is_covered_by_the_queue_no_gap(
    post_cutover_raw_path, config_dir, tmp_path
):
    comp = composition(tmp_path)
    result = run(post_cutover_raw_path, config_dir, comp)

    pending_rows = {
        line.raw.source_row
        for order in result.orders
        for line in order.lines
        if line.price_source == PRICE_SOURCE_PENDING
    }
    queued_rows = {
        row.source_row
        for item in result.review_queue.items
        if item.category == CATEGORY_MISSING_PURCHASE_PRICE
        for row in item.provenance.rows
    }
    assert pending_rows, "fixture phải chứa ít nhất một dòng Pending"
    assert pending_rows <= queued_rows, "PENDING_NOT_QUEUED phải bằng 0"


def test_no_order_is_silently_dropped(
    post_cutover_raw_path, config_dir, tmp_path
):
    comp = composition(tmp_path)
    result = run(post_cutover_raw_path, config_dir, comp)
    assert {o.order_id for o in result.orders} == {
        "BH9001", "BH9002", "BH9003", "BH9004"
    }
    assert sum(len(o.lines) for o in result.orders) == len(ROWS_POST_CUTOVER)


# ======================================================================
# 3 — PUBLIC_PURCHASE không bị Tracking reader hijack
# ======================================================================


def test_public_purchase_identity_is_priced_by_the_public_purchase_source(
    post_cutover_raw_path, config_dir, tmp_path
):
    comp = composition(tmp_path)
    result = run(post_cutover_raw_path, config_dir, comp)
    line = lines_by_order(result)["BH9003"][0]

    assert line.accounting_purchase_price == Decimal("5500000")
    assert line.price_source == PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING


def test_the_reader_never_sees_a_public_purchase_line(
    post_cutover_raw_path, config_dir, tmp_path
):
    """Hijack sẽ để lại dấu vết: một `PriceReconstruction` cho dòng ấy."""
    comp = composition(tmp_path)
    run(post_cutover_raw_path, config_dir, comp)

    pp_records = [
        r for r in comp.records
        if r.identity is not None
        and r.identity.namespace is Namespace.PUBLIC_PURCHASE
    ]
    assert pp_records
    for record in pp_records:
        assert record.tracking_reconstruction is None
        assert record.rule is CompositionRule.PUBLIC_PURCHASE_DIRECT


def test_a_code_present_in_both_namespaces_does_not_collapse(tmp_path, config_dir):
    """`INV-18` — `TRACKING:A1` và `PUBLIC_PURCHASE:A1` là hai identity khác nhau.

    Bảng giá công khai có `A1` với giá 111.000. Nếu namespace bị collapse,
    dòng TRACKING A1 sẽ nhận con số đó thay vì 9.000.000 của Tracking.
    """
    comp = composition(tmp_path)
    raw = write_workbook(tmp_path / "collide.xlsx", [ROWS_POST_CUTOVER[0]])
    result = run(raw, config_dir, comp)
    line = lines_by_order(result)["BH9001"][0]

    assert line.accounting_purchase_price == Decimal("9000000")
    assert line.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY


# ======================================================================
# 4 — pre-cutover chỉ được resolve khi baseline/history thực sự phủ ngày bán
# ======================================================================


def test_pre_cutover_line_uses_authoritative_baseline_when_it_covers_sale_date(
    tmp_path, config_dir
):
    """01/09 là cutover kỹ thuật, không chặn evidence phủ 31/08."""
    pre_row = (
        date(2026, 8, 31), "BH0001", "Bán hàng Khách Lẻ A", "Máy giặt Tracking A1",
        "KH0001", "Khách A", "1 Đường Test", "0900000001", 1, 12_000_000,
        12_000_000, 0, "Vũ Hạnh Ly 0868345633", "Shipper A", 50_000, None, 1_000_000,
    )
    comp = composition(tmp_path)
    raw = write_workbook(tmp_path / "pre.xlsx", [pre_row])
    result = run(raw, config_dir, comp)

    line = lines_by_order(result)["BH0001"][0]
    assert line.date < CUTOVER_DATE
    assert line.accounting_purchase_price == Decimal("9000000")
    assert line.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    assert len(comp.records) == 1


def test_pre_cutover_line_before_baseline_remains_pending(tmp_path, config_dir):
    """Không được kéo baseline hiện có ngược về ngày chưa được nó chứng minh."""
    pre_row = (
        date(2026, 8, 20), "BH0001", "Bán hàng Khách Lẻ A", "Máy giặt Tracking A1",
        "KH0001", "Khách A", "1 Đường Test", "0900000001", 1, 12_000_000,
        12_000_000, 0, "Vũ Hạnh Ly 0868345633", "Shipper A", 50_000, None, 1_000_000,
    )
    comp = composition(tmp_path)
    result = run(write_workbook(tmp_path / "pre-baseline.xlsx", [pre_row]), config_dir, comp)
    line = lines_by_order(result)["BH0001"][0]
    assert line.accounting_purchase_price is None
    assert line.price_source == PRICE_SOURCE_PENDING
    assert comp.records[0].reason is PriceResolutionReason.TRACKING_HISTORY_PENDING
    assert comp.records[0].tracking_reconstruction.reason is UnresolvedReason.SALE_BEFORE_CUTOVER


def test_golden_1_and_3_keep_confirmed_registry_price_with_composition(
    tmp_path, config_dir
):
    """Registry CONFIRMED vẫn thắng composition, kể cả khi nó đã được nối."""
    from tests.test_golden_bh62063_kpi import GOLDEN_FIXTURE as G1

    result = run(G1, config_dir, composition(tmp_path))
    line = next(
        line
        for order in result.orders
        if order.order_id == "BH62063"
        for line in order.lines
    )
    assert line.accounting_purchase_price == Decimal("7000000")
    assert line.eligible_kpi_profit == Decimal("500000")


# ======================================================================
# 6/7/8/9/19/20 — fail-safe của reader được giữ nguyên qua composition
# ======================================================================


def test_sale_interval_uncertainty_is_preserved(tmp_path, config_dir):
    """Một thay đổi giá RƠI VÀO GIỮA ngày bán -> Pending, không đoán giờ bán."""
    export = build_export(
        prices={"A1": 9000},
        events={
            "A1": {
                "E1": event(
                    prev=9000, nxt=9500,
                    # 12:00 giờ VN ngày 05/09 = 05:00Z, nằm GIỮA [00:00, 24:00) VN.
                    at=datetime(2026, 9, 5, 5, tzinfo=timezone.utc),
                )
            }
        },
    )
    comp = composition(tmp_path, export=export)
    raw = write_workbook(tmp_path / "mid.xlsx", [ROWS_POST_CUTOVER[0]])
    result = run(raw, config_dir, comp)

    line = lines_by_order(result)["BH9001"][0]
    assert line.accounting_purchase_price is None
    assert line.price_source == PRICE_SOURCE_PENDING
    record = comp.records[0]
    assert record.reason is PriceResolutionReason.TRACKING_HISTORY_PENDING
    assert (
        record.tracking_reconstruction.reason
        is UnresolvedReason.PRICE_CHANGED_WITHIN_SALE_INTERVAL
    )


def test_old_unverified_history_stays_pending(tmp_path, config_dir):
    """Sự kiện thiếu `ta='SERVER'` -> không được nâng thẩm quyền ngược."""
    export = build_export(
        prices={"A1": 9000},
        events={
            "A1": {
                "E1": event(
                    prev=9000, nxt=9500,
                    at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc),
                    authority=None,
                )
            }
        },
    )
    comp = composition(tmp_path, export=export)
    raw = write_workbook(tmp_path / "old.xlsx", [ROWS_POST_CUTOVER[0]])
    result = run(raw, config_dir, comp)

    assert lines_by_order(result)["BH9001"][0].accounting_purchase_price is None
    assert (
        comp.records[0].tracking_reconstruction.reason
        is UnresolvedReason.HISTORY_PROVENANCE_NOT_AUTHORITATIVE
    )


def test_cleared_price_next_null_stays_pending_and_never_reuses_the_old_price(
    post_cutover_raw_path, config_dir, tmp_path
):
    comp = composition(tmp_path)
    result = run(post_cutover_raw_path, config_dir, comp)

    line = lines_by_order(result)["BH9002"][0]
    assert line.accounting_purchase_price is None
    assert line.price_source == PRICE_SOURCE_PENDING
    record = next(r for r in comp.records if r.order_id == "BH9002")
    assert record.tracking_reconstruction.reason is UnresolvedReason.PRICE_CLEARED


def test_absent_baseline_is_not_a_zero_and_not_the_current_price(
    tmp_path, config_dir
):
    """Mã vắng mặt trong baseline và không có sự kiện nào -> Pending, không 0."""
    export = build_export(prices={"D1": 4200}, n_absent=1)
    comp = composition(tmp_path, export=export)
    raw = write_workbook(tmp_path / "absent.xlsx", [ROWS_POST_CUTOVER[0]])
    result = run(raw, config_dir, comp)

    line = lines_by_order(result)["BH9001"][0]
    assert line.accounting_purchase_price is None
    assert line.accounting_purchase_price != Decimal("0")
    assert line.price_source == PRICE_SOURCE_PENDING
    assert (
        comp.records[0].tracking_reconstruction.reason
        is UnresolvedReason.NO_BASELINE_PRICE_AT_CUTOVER
    )


def test_malformed_temporal_evidence_never_produces_a_resolved_price(tmp_path):
    """Timestamp theo SECONDS bị từ chối ngay lúc nạp — không thành năm 1970."""
    export = build_export(
        prices={"A1": 9000},
        events={"A1": {"E1": {"prev": 9000, "next": 9500,
                              "t": 1_760_000_000, "ta": "SERVER",
                              "by": "u", "src": "sync"}}},
    )
    with pytest.raises(Exception) as excinfo:
        composition(tmp_path, export=export)
    assert "invalid_timestamp_unit" in getattr(excinfo.value, "reason", "")


def test_no_silent_fallback_to_the_current_tracking_price(tmp_path, config_dir):
    """Reader Pending KHÔNG được thay bằng giá baseline "hiện tại" của mã khác
    và KHÔNG được thay bằng chính giá baseline khi chuỗi đã gãy."""
    export = build_export(
        prices={"A1": 9000},
        events={
            "A1": {
                # prev không khớp trạng thái dựng được -> chuỗi gãy.
                "E1": event(prev=1234, nxt=9500,
                            at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc))
            }
        },
    )
    comp = composition(tmp_path, export=export)
    raw = write_workbook(tmp_path / "broken.xlsx", [ROWS_POST_CUTOVER[0]])
    result = run(raw, config_dir, comp)

    line = lines_by_order(result)["BH9001"][0]
    assert line.accounting_purchase_price is None
    assert (
        comp.records[0].tracking_reconstruction.reason
        is UnresolvedReason.HISTORY_CHAIN_INCONSISTENT
    )


# ======================================================================
# 10 — quy đổi đơn vị đúng MỘT lần
# ======================================================================


def test_thousand_vnd_is_converted_exactly_once(tmp_path, config_dir):
    comp = composition(tmp_path)
    raw = write_workbook(tmp_path / "unit.xlsx", [ROWS_POST_CUTOVER[0]])
    result = run(raw, config_dir, comp)

    line = lines_by_order(result)["BH9001"][0]
    record = comp.records[0]
    prov = record.tracking_reconstruction.provenance
    assert prov.raw_value_thousand_vnd == Decimal("9000")
    assert prov.resolved_price_vnd == Decimal("9000000")
    assert line.accounting_purchase_price == Decimal("9000000")
    # Không có phép nhân thứ hai: 9.000 × 1000 × 1000 sẽ là 9 tỉ.
    assert line.accounting_purchase_price < Decimal("1000000000")


def test_public_purchase_prices_are_already_vnd_and_are_not_multiplied(
    post_cutover_raw_path, config_dir, tmp_path
):
    comp = composition(tmp_path)
    result = run(post_cutover_raw_path, config_dir, comp)
    assert (
        lines_by_order(result)["BH9003"][0].accounting_purchase_price
        == Decimal("5500000")
    )


# ======================================================================
# 11/12/13/14 — kế toán đơn nhiều dòng, DEC-143/144 không đổi
# ======================================================================


def test_multi_line_order_accounting_and_no_sibling_price_leak(
    post_cutover_raw_path, config_dir, tmp_path
):
    """BH9004: dòng 1 resolve được, dòng 2 Pending. Không dòng nào mượn giá của
    dòng kia, và cả hai vẫn nằm trong đơn."""
    comp = composition(tmp_path)
    result = run(post_cutover_raw_path, config_dir, comp)
    lines = lines_by_order(result)["BH9004"]
    assert len(lines) == 2

    resolved = next(l for l in lines if l.product_raw.startswith("Máy sấy"))
    sibling = next(l for l in lines if l.product_raw.startswith("Hàng hoàn toàn"))

    assert resolved.accounting_purchase_price == Decimal("4200000")
    assert sibling.accounting_purchase_price is None
    assert sibling.price_source == PRICE_SOURCE_PENDING
    assert sibling.accounting_profit is None
    assert sibling.eligible_kpi_profit is None

    # DEC-143 rút gọn: (SellPrice − KpiPurchasePrice) × Qty − Discount
    assert resolved.kpi_purchase_price == Decimal("4200000")
    assert resolved.eligible_kpi_profit == (
        (Decimal("6000000") - Decimal("4200000")) * 2 - Decimal("100000")
    )


def test_dec144_no_confirmed_adjustment_semantics_are_unchanged(
    post_cutover_raw_path, config_dir, tmp_path
):
    """Nguồn adjustment nạp được nhưng 0 record khớp -> KpiPurchasePrice =
    AccountingPurchasePrice, provenance `Config:NoConfirmedAdjustment`."""
    from app.modules.adjustment.confirmed_adjustment_source import (
        load_confirmed_adjustments_from_jsonl,
    )
    from app.modules.domain.models import KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT
    from app.modules.kpi.kpi_profit_engine import load_eligible_costs_authority

    comp = composition(tmp_path)
    result = run_import(
        post_cutover_raw_path,
        config_dir,
        confirmed_adjustment_source=load_confirmed_adjustments_from_jsonl(
            Path("data/confirmed_adjustments/confirmed_adjustments.jsonl")
        ),
        eligible_costs_authority=load_eligible_costs_authority(
            Path("config/eligible_costs.yaml")
        ),
        price_composition=comp,
    )
    line = lines_by_order(result)["BH9001"][0]
    assert line.kpi_purchase_price == Decimal("9000000")
    assert line.kpi_purchase_price_provenance == KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT


# ======================================================================
# 15/16 — snapshot đông lạnh, kết quả tái lập được
# ======================================================================


def test_one_import_uses_exactly_one_frozen_evidence_snapshot(
    post_cutover_raw_path, config_dir, tmp_path
):
    comp = composition(tmp_path)
    run(post_cutover_raw_path, config_dir, comp)
    assert comp.records
    for record in comp.records:
        assert record.evidence is comp.evidence
    assert comp.evidence.tracking_price_history_capture_id == (
        "PPH-20260929T120000Z-aaaa"
    )
    assert comp.evidence.public_purchase_version_id == fx.PP_V1
    assert comp.evidence.tracking_catalog_capture_id == fx.CAPTURE_A


def test_the_same_snapshot_and_input_give_the_same_output_every_time(
    post_cutover_raw_path, config_dir, tmp_path
):
    def prices_of(comp):
        result = run(post_cutover_raw_path, config_dir, comp)
        return [
            (order.order_id, line.product_raw, line.accounting_purchase_price,
             line.price_source)
            for order in result.orders
            for line in order.lines
        ]

    assert prices_of(composition(tmp_path)) == prices_of(composition(tmp_path))


# ======================================================================
# 17/18 — HAI cutover, không gộp
# ======================================================================


def test_the_product_identity_cutover_is_still_2026_09_01():
    assert CUTOVER_DATE == date(2026, 9, 1)


def test_the_two_cutovers_are_different_kinds_and_cannot_be_compared():
    assert isinstance(CUTOVER_DATE, date) and not isinstance(CUTOVER_DATE, datetime)
    assert isinstance(CUTOVER, datetime)
    with pytest.raises(TypeError):
        _ = CUTOVER_DATE < CUTOVER


def test_a_sale_between_the_two_cutovers_can_use_authoritative_evidence(
    tmp_path, config_dir
):
    """30/08 được resolver hỏi, nhưng reader vẫn là cổng temporal quyết định."""
    row = list(ROWS_POST_CUTOVER[0])
    row[0] = date(2026, 8, 30)
    comp = composition(tmp_path)
    raw = write_workbook(tmp_path / "between.xlsx", [tuple(row)])
    result = run(raw, config_dir, comp)

    assert len(comp.records) == 1
    assert (
        lines_by_order(result)["BH9001"][0].price_source
        == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )


# ======================================================================
# P01/P03/P09 — fallback Public Purchase cho identity TRACKING bị CHẶN
# ======================================================================


def test_a_tracking_identity_never_borrows_a_public_purchase_price(
    tmp_path, config_dir
):
    """Kể cả khi có `CrossSystemProductMapping` CONFIRMED và bảng giá công khai
    có đúng mã ấy: `P03` đòi một absence ĐÃ XÁC ĐỊNH từ nguồn vendor, mà nguồn
    ấy (`TASK-105C`) chưa được cấp phép — nên điều kiện không thoả."""
    a_store = fx.store()
    confirm_cross_system(
        a_store,
        tracking_code="B1",
        public_purchase_code="C1",
        actor_id=fx.ACTOR,
        client_request_id="req-105e-1",
        expected_version=0,
        pp_version_id=fx.PP_V1,
        tracking_capture_id=fx.CAPTURE_A,
    )
    comp = composition(tmp_path, store=a_store)
    raw = write_workbook(tmp_path / "fallback.xlsx", [ROWS_POST_CUTOVER[1]])
    result = run(raw, config_dir, comp)

    line = lines_by_order(result)["BH9002"][0]
    assert line.accounting_purchase_price is None
    assert line.price_source == PRICE_SOURCE_PENDING
    record = comp.records[0]
    assert (
        record.fallback_blocked_by
        is PriceResolutionReason.VENDOR_SOURCE_NOT_AUTHORIZED
    )
    assert "TASK-105C" in record.fallback_blocked_detail


def test_the_two_public_purchase_provenances_are_not_collapsed():
    """`DEC-154` §10 — `P08` và `P09` là hai nhãn KHÁC nhau, kể cả khi `P09`
    chưa có đường tới."""
    assert (
        PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING
        != PRICE_SOURCE_PUBLIC_PURCHASE_NO_VENDOR_PRICE
    )
    assert len(set(PRICE_SOURCE_BY_RULE.values())) == len(PRICE_SOURCE_BY_RULE)
    assert (
        PRICE_SOURCE_BY_RULE[CompositionRule.PUBLIC_PURCHASE_VENDOR_FALLBACK]
        == PRICE_SOURCE_PUBLIC_PURCHASE_NO_VENDOR_PRICE
    )


def test_the_identity_namespace_is_unchanged_by_the_price_source(
    post_cutover_raw_path, config_dir, tmp_path
):
    """`P10` — nguồn giá đổi không đổi namespace của identity."""
    comp = composition(tmp_path)
    run(post_cutover_raw_path, config_dir, comp)
    by_raw = {r.raw_product_identity: r for r in comp.records}
    assert by_raw["Máy giặt Tracking A1"].identity.namespace is Namespace.TRACKING
    assert (
        by_raw["Bếp từ Công Khai C1"].identity.namespace is Namespace.PUBLIC_PURCHASE
    )


# ======================================================================
# Nguồn CHƯA CÓ khác GIÁ KHÔNG TỒN TẠI khác NGUỒN HỎNG
# ======================================================================


def test_absent_sources_are_pending_not_a_crash_and_not_a_zero(
    post_cutover_raw_path, config_dir, tmp_path
):
    """Trạng thái production HÔM NAY: chưa capture nguồn nào."""
    comp = composition(
        tmp_path, with_history=False, with_catalog=False,
        with_public_purchase=False,
    )
    result = run(post_cutover_raw_path, config_dir, comp)

    assert len(result.orders) == 4
    for record in comp.records:
        assert record.price_vnd is None
        assert record.price_source == PRICE_SOURCE_PENDING
        assert (
            record.reason is PriceResolutionReason.IDENTITY_SOURCES_UNAVAILABLE
        )


def test_a_failed_capture_is_a_hard_error_never_a_pending(tmp_path):
    """`INV-12` — capture hỏng KHÔNG được đọc thành 'không có dữ liệu'."""
    path = write_history_capture(
        tmp_path, {}, capture_status="FAILED", failure_reason="mất mạng giữa chừng"
    )
    snapshot = load_tracking_price_history_capture(path)
    assert snapshot.capture_status is CaptureStatus.FAILED
    sources = build_sources(tmp_path, with_history=False)
    with pytest.raises(TrackingCaptureFailedError):
        PostCutoverPriceComposition(
            PriceResolutionSources(
                business_timezone=sources.business_timezone,
                tracking_price_history=snapshot,
                tracking_catalog=sources.tracking_catalog,
                public_purchase=sources.public_purchase,
                identity_store_view=sources.identity_store_view,
            )
        )


def test_a_corrupt_capture_file_is_a_load_error_not_an_empty_source(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    with pytest.raises(InvalidTrackingPriceCaptureFileError):
        load_tracking_price_history_capture(bad)

    bad_catalog = tmp_path / "bad_catalog.json"
    bad_catalog.write_text(json.dumps({"capture_id": "x"}), encoding="utf-8")
    with pytest.raises(InvalidTrackingCatalogCaptureFileError):
        load_tracking_catalog_capture(bad_catalog)


def test_a_missing_capture_file_is_absence_not_an_error(tmp_path):
    assert load_tracking_price_history_capture(tmp_path / "nope.json") is None
    assert load_tracking_catalog_capture(tmp_path / "nope.json") is None


def test_public_purchase_price_absent_at_sale_date_is_pending_not_backfilled(
    tmp_path, config_dir
):
    """`P05`/`P06`/`P07` — giá công khai bắt đầu hiệu lực SAU ngày bán không
    được kéo ngược về đơn cũ."""
    comp = composition(
        tmp_path,
        pp_prices=[
            {"product_key": "C1", "effective_from": date(2026, 10, 1),
             "effective_to": None, "purchase_price": "5500000"},
        ],
    )
    raw = write_workbook(tmp_path / "pp_late.xlsx", [ROWS_POST_CUTOVER[2]])
    result = run(raw, config_dir, comp)

    line = lines_by_order(result)["BH9003"][0]
    assert line.accounting_purchase_price is None
    assert (
        comp.records[0].reason
        is PriceResolutionReason.PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE
    )


def test_an_invalid_business_timezone_fails_closed(tmp_path, config_dir):
    """Không có múi giờ hợp lệ -> không dựng khoảng bán -> Pending, KHÔNG có
    một mặc định UTC+7 thầm lặng."""
    empty_config = tmp_path / "cfg"
    empty_config.mkdir()
    sources = build_sources(tmp_path, timezone_config=empty_config)
    assert sources.business_timezone.is_valid is False

    comp = PostCutoverPriceComposition(sources)
    raw = write_workbook(tmp_path / "tz.xlsx", [ROWS_POST_CUTOVER[0]])
    result = run(raw, config_dir, comp)

    assert lines_by_order(result)["BH9001"][0].accounting_purchase_price is None
    assert (
        comp.records[0].reason
        is PriceResolutionReason.TRACKING_HISTORY_SOURCE_UNAVAILABLE
    )


# ======================================================================
# Biên composition — hai nguồn giá loại trừ lẫn nhau
# ======================================================================


def test_price_provider_and_price_composition_are_mutually_exclusive(
    post_cutover_raw_path, config_dir, tmp_path
):
    from app.modules.pricing.provider import PendingPriceProvider

    with pytest.raises(ValueError, match="loại trừ lẫn nhau"):
        run_import(
            post_cutover_raw_path,
            config_dir,
            price_provider=PendingPriceProvider(),
            price_composition=composition(tmp_path),
        )


def test_the_pipeline_default_is_still_pending_price_provider(
    post_cutover_raw_path, config_dir
):
    """`CHECK-105-04` — không nối gì thì hành vi mặc định KHÔNG ĐỔI."""
    result = run_import(post_cutover_raw_path, config_dir)
    for order in result.orders:
        for line in order.lines:
            assert line.accounting_purchase_price is None
            assert line.price_source == PRICE_SOURCE_PENDING


def test_production_sources_keep_temporal_and_vendor_provenance_explicit():
    """Nguồn local có thể được recapture; provenance contract thì không đổi."""
    comp = build_price_composition(Path("config"))
    assert comp.evidence.tracking_price_history_capture_id is None
    assert comp.evidence.public_purchase_version_id is None
    assert comp.evidence.business_timezone_label.startswith("Asia/Ho_Chi_Minh")
    assert comp.evidence.vendor_price_source == "NOT_AUTHORIZED:TASK-105C"


# ======================================================================
# Cơ chế thu thập nguồn — công cụ capture (tools/, ngoài app/modules/)
# ======================================================================


def test_the_capture_tool_round_trips_into_a_readable_snapshot(tmp_path):
    """Công cụ capture → file → loader → reader: một vòng khép kín, không mạng.

    `fetch` được tiêm vào nên vòng này kiểm ĐÚNG hợp đồng dữ liệu giữa hai
    phía của ranh giới `ADR-101`, thứ duy nhất mà mạng thật không dạy thêm gì.
    """
    from tools.tracking.capture_purchase_price_history import (
        BASELINE_NODE,
        HISTORY_NODE,
        build_capture,
        write_capture,
    )

    export = build_export(prices={"A1": 9000})

    def fetch(node):
        return export.get(node)

    envelope = build_capture(
        fetch,
        capture_id="PPH-TEST-0001",
        captured_by="test",
        source_system_ref="tracking/rtdb",
    )
    assert envelope["capture_status"] == "COMPLETE"
    assert set(envelope["data"]) == {BASELINE_NODE, HISTORY_NODE}

    path = write_capture(envelope, tmp_path / "cap" / "capture.json")
    snapshot = load_tracking_price_history_capture(path)
    assert isinstance(snapshot, TrackingPriceHistorySnapshot)
    assert snapshot.capture_id == "PPH-TEST-0001"
    assert snapshot.baseline.prices["A1"] == Decimal("9000")


def test_a_failed_fetch_writes_a_failed_capture_not_an_empty_one(tmp_path):
    """`INV-12` — mất mạng KHÔNG được biến thành 'lịch sử rỗng'."""
    from tools.tracking.capture_purchase_price_history import (
        CaptureError,
        build_capture,
        write_capture,
    )

    def fetch(node):
        raise CaptureError("mất mạng")

    envelope = build_capture(
        fetch, capture_id="PPH-TEST-0002", captured_by="test",
        source_system_ref="tracking/rtdb",
    )
    assert envelope["capture_status"] == "FAILED"
    assert "data" not in envelope

    path = write_capture(envelope, tmp_path / "failed.json")
    snapshot = load_tracking_price_history_capture(path)
    assert snapshot.capture_status is CaptureStatus.FAILED
    with pytest.raises(TrackingCaptureFailedError):
        snapshot.require_complete()


def test_a_capture_file_is_never_overwritten(tmp_path):
    from tools.tracking.capture_purchase_price_history import (
        CaptureError,
        write_capture,
    )

    envelope = {"capture_id": "x", "capture_status": "COMPLETE"}
    path = write_capture(envelope, tmp_path / "once.json")
    with pytest.raises(CaptureError, match="BẤT BIẾN"):
        write_capture(envelope, path)


def test_the_capture_tool_has_no_write_surface_to_tracking():
    """Read-only là một tính chất của MÃ, không phải một lời hứa trong doc."""
    source = Path(
        "tools/tracking/capture_purchase_price_history.py"
    ).read_text(encoding="utf-8")
    for verb in ('method="PUT"', 'method="POST"', 'method="PATCH"',
                 'method="DELETE"'):
        assert verb not in source
    assert source.count('method="GET"') == 1


def test_no_module_under_app_reaches_the_network():
    """`CHECK-105D-17` mở rộng cho các module mới của TASK-105E."""
    import re

    forbidden = re.compile(
        r"^\s*(?:import|from)\s+"
        r"(requests|urllib|http|httpx|socket|firebase\w*|google\.cloud"
        r"|boto3|aiohttp|websocket\w*|pyrebase)\b",
        re.MULTILINE,
    )
    for path in Path("app").rglob("*.py"):
        assert not forbidden.search(path.read_text(encoding="utf-8")), path


# ======================================================================
# Biên PRODUCTION THẬT — `run_import_production()` với dòng post-cutover
# ======================================================================


def test_the_real_production_entry_point_handles_post_cutover_lines_safely(
    post_cutover_raw_path, tmp_path,
):
    """Trước `TASK-105E`, `run_import_production()` chưa từng chạy một dòng
    `sale_date >= CUTOVER_DATE` nào (dữ liệu thật hiện có toàn pre-cutover).
    Test này chạy chính seam production ấy trên dữ liệu post-cutover, với
    nguồn giá đúng như trên đĩa hôm nay (chưa capture lần nào).

    Kỳ vọng KHÔNG phải là tự động hoá — mà là: không nổ, không đơn nào biến
    mất, không giá nào bị bịa, và mọi dòng chưa có giá đều nằm trong Review
    Queue canonical.
    """
    comp = composition(tmp_path)
    result = run_import_production(
        post_cutover_raw_path, config_dir=Path("config"), price_composition=comp
    )

    assert {o.order_id for o in result.orders} == {
        "BH9001", "BH9002", "BH9003", "BH9004"
    }
    assert sum(len(o.lines) for o in result.orders) == len(ROWS_POST_CUTOVER)

    lines = [line for order in result.orders for line in order.lines]
    assert any(line.accounting_purchase_price is not None for line in lines)
    assert any(line.accounting_purchase_price is None for line in lines)

    # Mọi dòng Pending đều được Review Queue phủ — PENDING_NOT_QUEUED = 0.
    pending_rows = {line.raw.source_row for line in lines if line.accounting_purchase_price is None}
    queued_rows = {
        row.source_row
        for item in result.review_queue.items
        if item.category == CATEGORY_MISSING_PURCHASE_PRICE
        for row in item.provenance.rows
    }
    assert pending_rows <= queued_rows

    # Mỗi Pending phải giữ lý do có kiểu; không có giá trị số giả.
    assert comp.records
    assert all(
        record.price_vnd is None
        for record in comp.records
        if record.reason is not None
    )
    assert any(
        record.reason is PriceResolutionReason.TRACKING_HISTORY_PENDING
        for record in comp.records
    )
