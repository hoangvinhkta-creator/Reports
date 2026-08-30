"""Public Purchase Authority Correction — Tracking là nguồn sự thật duy nhất.

## Giả định CŨ đã bị thay

`DEC-156 D-01/OR-01` coi Public Purchase là một nguồn giá ĐỘC LẬP do chủ dự án
cấp bằng YAML (`data/public_purchase/source_version.yaml`). Quyết định nghiệp
vụ của Owner đã thay giả định ấy (`ADR-107`, `DEC-165`):

  · `inv.gia`  = giá vốn tồn THỰC TẾ (Y) — máy tính bình quân gia quyền,
                 KHÔNG BAO GIỜ rời tab Tồn kho của Tracking;
  · `inv.cong` = Public Purchase — Owner tự đặt, `congTay` khoá không cho Y
                 ghi đè, chiếu sang `board/<mã>/tp/ton`, và mỗi lần đổi sinh
                 một sự kiện `purchase_price_history` có dấu thời gian máy chủ.

Nên `purchase_price_baseline` + `purchase_price_history` — hai nhánh Reports
ĐÃ đọc qua Data Contract — chính là lịch sử effective-dated của Public
Purchase. Không cần nguồn thứ hai, và không được dựng nguồn thứ hai.

## Vì sao file test này tồn tại

Sửa kiến trúc lần này chỉ gỡ MỘT cổng AND, nên rất dễ hồi quy trở lại: chỉ cần
ai đó thêm `pp_version` vào lại điều kiện là mọi mã Tracking quay về Pending vì
một file không liên quan. Các test dưới đây khoá đúng ranh giới ấy, và khoá
luôn hai điều KHÔNG được phép đi kèm: giá vốn thật Y không được lọt vào đường
KPI, và thiếu Public Purchase không được biến thành một con số đoán.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from app.modules.domain.models import (
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_TRACKING_PRICE_HISTORY,
)
from app.modules.pricing.resolution.composition import PriceResolutionReason
from app.modules.product.identity.identity import Namespace
from app.modules.product.identity.resolver import (
    ProductIdentityResolver,
    SalesRowRef,
    distinct_identities,
)
from app.modules.validation.models import CATEGORY_MISSING_PURCHASE_PRICE
from tests.support import identity_fixtures as fx
from tests.test_105e_price_composition import (
    build_sources,
    composition,
    lines_by_order,
    post_cutover_raw_path,  # noqa: F401  (fixture pytest)
    run,
)

# ======================================================================
# 1 — Mã Tracking KHÔNG còn bị chặn bởi Public Purchase YAML legacy
# ======================================================================


def test_tracking_identity_resolves_without_the_legacy_public_purchase_yaml(
    post_cutover_raw_path, config_dir, tmp_path  # noqa: F811
):
    """Đây là finding gốc của phiên này: thiếu YAML chặn CẢ identity.

    `BH9001` có đủ bằng chứng Tracking (catalog + baseline). Không có một lý
    do nghiệp vụ nào để nó phải chờ một bảng giá công khai của một hệ thống
    khác — và sau `DEC-165` nó không chờ nữa.
    """
    comp = composition(tmp_path, with_public_purchase=False)
    result = run(post_cutover_raw_path, config_dir, comp)
    line = lines_by_order(result)["BH9001"][0]

    assert line.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    assert line.accounting_purchase_price == Decimal("9000000")
    # Public Purchase tại thời điểm bán LÀ giá KPI (Owner business decision).
    assert line.kpi_purchase_price == Decimal("9000000")
    assert line.eligible_kpi_profit == Decimal("3000000")


def test_the_identity_gate_no_longer_names_public_purchase(tmp_path):
    """Cổng AND chỉ còn hai nguồn identity THẬT SỰ cần cho một mã Tracking."""
    sources = build_sources(tmp_path, with_public_purchase=False)
    assert sources.public_purchase is None
    assert sources.tracking_catalog is not None
    assert sources.identity_store_view is not None


def test_absent_catalog_is_still_a_hard_gate(
    post_cutover_raw_path, config_dir, tmp_path  # noqa: F811
):
    """Gỡ Public Purchase khỏi cổng KHÔNG được nới lỏng phần còn lại.

    Thiếu catalog Tracking vẫn là NGUỒN CHƯA CÓ cho mọi dòng — không mã nào
    được đoán, không giá nào được dựng.
    """
    comp = composition(tmp_path, with_catalog=False, with_public_purchase=False)
    run(post_cutover_raw_path, config_dir, comp)

    assert comp.records
    for record in comp.records:
        assert record.price_vnd is None
        assert record.price_source == PRICE_SOURCE_PENDING
        assert record.reason is PriceResolutionReason.IDENTITY_SOURCES_UNAVAILABLE


# ======================================================================
# 2 — Thiếu Public Purchase vẫn là Pending TRUNG THỰC, không phải một con số
# ======================================================================


def test_a_public_purchase_identity_pends_truthfully_when_its_source_is_absent(
    post_cutover_raw_path, config_dir, tmp_path  # noqa: F811
):
    """`BH9003` là một mã `PUBLIC_PURCHASE:` legacy.

    Không có catalog PP thì nó không resolve được thành mã PP nào — và đó
    phải là Pending, KHÔNG phải một giá mượn từ nhánh Tracking.
    """
    comp = composition(tmp_path, with_public_purchase=False)
    result = run(post_cutover_raw_path, config_dir, comp)
    line = lines_by_order(result)["BH9003"][0]

    assert line.accounting_purchase_price is None
    assert line.kpi_purchase_price is None
    assert line.price_source == PRICE_SOURCE_PENDING

    record = next(r for r in comp.records if r.order_id == "BH9003")
    # Không có identity PP nào được dựng ra từ hư không.
    assert record.identity is None or (
        record.identity.namespace is not Namespace.PUBLIC_PURCHASE
    )
    # Và reader lịch sử Tracking KHÔNG được gọi thay cho nguồn vắng mặt.
    assert record.tracking_reconstruction is None


def test_every_pending_still_reaches_the_canonical_review_queue(
    post_cutover_raw_path, config_dir, tmp_path  # noqa: F811
):
    """`TASK-110` — Pending là một việc phải xử, không phải một dòng bị nuốt."""
    comp = composition(tmp_path, with_public_purchase=False)
    result = run(post_cutover_raw_path, config_dir, comp)

    pending_rows = {
        line.raw.source_row
        for order in result.orders
        for line in order.lines
        if line.price_source == PRICE_SOURCE_PENDING
    }
    assert pending_rows
    queued_rows = {
        row.source_row
        for item in result.review_queue.items
        if item.category == CATEGORY_MISSING_PURCHASE_PRICE
        for row in item.provenance.rows
    }
    assert pending_rows <= queued_rows


# ======================================================================
# 3 — Giá vốn tồn THỰC TẾ (Y) không có đường nào chảy vào KPI
# ======================================================================


def test_no_actual_inventory_cost_reaches_reports_at_all(tmp_path):
    """`inv.gia` (Y) KHÔNG tồn tại trong bất kỳ nguồn nào Reports đọc.

    Đây là khẳng định mạnh nhất có thể đưa ra ở phía Reports, và nó đúng vì
    hợp đồng dữ liệu chỉ chiếu `board` xuống `{name, alt}`: nhánh `inv` chưa
    bao giờ nằm trong allowlist. Không có fallback nào sang Y để chặn, vì
    không có Y nào đi tới đây.
    """
    sources = build_sources(tmp_path, with_public_purchase=False)
    snapshot = sources.tracking_catalog
    assert snapshot is not None
    for row in snapshot.rows:
        fields = set(vars(row))
        assert "gia" not in fields
        assert "inventory_cost" not in fields
        assert "actual_cost" not in fields


def test_a_pending_price_is_never_replaced_by_any_other_number(
    post_cutover_raw_path, config_dir, tmp_path  # noqa: F811
):
    """`BH9002` có giá Public Purchase đã bị XOÁ (`next=null`) tại ngày bán.

    Giá cũ trước khi xoá KHÔNG được tái sử dụng, và không có nguồn thứ hai
    nào được hỏi thay. Pending là câu trả lời đúng.
    """
    comp = composition(tmp_path, with_public_purchase=False)
    result = run(post_cutover_raw_path, config_dir, comp)
    line = lines_by_order(result)["BH9002"][0]

    assert line.accounting_purchase_price is None
    assert line.kpi_purchase_price is None
    assert line.price_source == PRICE_SOURCE_PENDING


# ======================================================================
# 4 — Resolver: `pp_version=None` nói "chưa nối", không nói "rỗng"
# ======================================================================


def _resolver_without_pp(a_store):
    """Resolver dựng ĐÚNG như production sau `DEC-165`: không truyền `pp_version`."""
    return ProductIdentityResolver(
        tracking_snapshot=fx.tracking_snapshot(
            rows=[("T2109NT1G", "Máy Giặt LG T2109NT1G", (), True)]
        ),
        store_view=a_store.read_at_revision(a_store.current_revision()),
        now=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def _one_identity(raw: str):
    return distinct_identities(
        [SalesRowRef(order_id="BH0001", sale_date=date(2026, 9, 15),
                     raw_product_identity=raw)]
    )[0]


def test_resolver_accepts_an_absent_public_purchase_catalog(tmp_path):
    resolver = _resolver_without_pp(fx.store(tmp_path))
    assert resolver.pp_version is None
    assert resolver._pp_identity_rows == ()
    assert resolver._pp_exact_hits(raw_key="bất kỳ", aid="batky") == ()


def test_provenance_records_the_absence_instead_of_faking_a_version(tmp_path):
    """`pp_version_id=None` là bằng chứng đọc lại được rằng không có catalog PP.

    Nếu chỗ này lỡ điền một chuỗi rỗng hay một id giả, một bản audit sau này
    sẽ đọc ra "đã dùng catalog PP" cho một lần resolve chưa từng có catalog.
    """
    resolver = _resolver_without_pp(fx.store(tmp_path))
    resolution = resolver.resolve(_one_identity("T2109NT1G"))

    provenance = resolution.outcome.provenance
    assert provenance.pp_version_id is None
    assert provenance.tracking_capture_id == fx.CAPTURE_A


def test_a_tracking_code_resolves_with_no_public_purchase_catalog_attached(
    tmp_path,
):
    """`TRACKING:<mã>` chỉ cần catalog Tracking + alias + xác nhận đã lưu.

    Đây chính là hình dạng của `T2109NT1G` trong `BH73804`: một mã CÓ trên
    board Tracking. Không có catalog Public Purchase nào tham gia, và không
    cần có.
    """
    resolver = _resolver_without_pp(fx.store(tmp_path))
    resolution = resolver.resolve(_one_identity("T2109NT1G"))

    target = resolution.outcome.identity
    assert target.namespace is Namespace.TRACKING
    assert target.source_product_code == "T2109NT1G"


def test_an_unknown_name_is_still_pending_and_is_never_forced(tmp_path):
    """`XVI` — thiếu Public Purchase KHÔNG được nới lỏng ngưỡng khớp.

    Một tên không khớp exact vẫn là Pending. Gỡ cổng AND là gỡ một điều kiện
    KHÔNG liên quan, không phải hạ tiêu chuẩn bằng chứng của identity.
    """
    resolver = _resolver_without_pp(fx.store(tmp_path))
    resolution = resolver.resolve(_one_identity("Hàng hoàn toàn vô danh XYZ"))

    assert not hasattr(resolution.outcome, "identity") or isinstance(
        getattr(resolution.outcome, "identity", None), type(None)
    )
