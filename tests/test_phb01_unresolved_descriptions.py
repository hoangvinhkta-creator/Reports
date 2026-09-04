"""PHB-01 — Product Identity Manual Resolution V1, phía Reports.

Ba câu hỏi mà bộ này trả lời, và không bộ nào khác trả lời:

A. **Gộp đúng đơn vị công việc.** "Còn bao nhiêu việc phải làm" phải đếm theo
   KHOÁ `inv.map` (một lần bấm của Owner bên Tracking), không theo dòng đơn
   hàng và không theo cách viết. Đếm sai đơn vị thì con số vô dụng.
B. **Bản xuất dùng được thật.** Một dòng cho mỗi khoá, thứ tự xác định, và
   CỘT ĐẦU là câu tên hàng nguyên văn để dán thẳng sang màn phân loại của
   Tracking.
F. **Vòng lặp khép kín.** Sau khi Owner phân loại bên Tracking, đúng hợp đồng
   authority ĐANG CÓ (`inv.map` → `/api/xuat/inv_map` → resolver) là đủ để
   Reports nhận diện được mặt hàng ấy ở lần chạy sau — không có kho mapping
   thứ hai bên Reports.

Bài G (authority rỗng hợp lệ ≠ authority hỏng) nằm ở
`tests/test_tracking_live_pull.py` và `tests/test_tracking_inv_map_capture.py`,
cạnh chính đoạn mã quyết định điều đó; ở đây chỉ kiểm phần bản xuất KHÔNG
được liệt kê một sự cố authority như một việc chờ phân loại.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import openpyxl
import pytest

from app import demo
from app.modules.pricing.resolution.composition import (
    CompositionRule,
    PRICE_SOURCE_PENDING,
    PriceResolutionReason,
    PriceResolutionRecord,
    PriceResolutionStatus,
)
from app.modules.pricing.resolution.sources import PriceEvidenceSnapshot
from app.modules.pricing.resolution.unresolved_descriptions import (
    aggregate_unresolved_descriptions,
    is_unresolved_identity_record,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
    PendingReason,
)
from app.modules.product.identity.tracking_inv_map import inv_map_key
from tests.test_105e_price_composition import (
    write_catalog_capture,
    write_history_capture,
    write_inv_map_capture,
)
from tests.test_demo import write_sales
from tests.test_tracking_history_reader import build_export, event

EVIDENCE = PriceEvidenceSnapshot(
    tracking_price_history_capture_id=None,
    tracking_price_history_captured_at=None,
    tracking_catalog_capture_id=None,
    tracking_inv_map_capture_id=None,
    public_purchase_version_id=None,
    public_purchase_content_hash=None,
    identity_store_revision=None,
    business_timezone_label="Asia/Ho_Chi_Minh",
    business_timezone_provenance="test",
    vendor_price_source="test",
)


def pending(
    description,
    *,
    order_id="BH0001",
    reason=PriceResolutionReason.IDENTITY_UNRESOLVED,
    identity_pending_reason=PendingReason.NO_CANDIDATE_IN_ANY_CATALOG,
):
    return PriceResolutionRecord(
        order_id=order_id,
        raw_product_identity=description,
        raw_identity_key=None,
        sale_date=date(2026, 9, 5),
        identity=None,
        status=PriceResolutionStatus.PENDING,
        rule=CompositionRule.NOT_RESOLVED,
        price_vnd=None,
        price_source=PRICE_SOURCE_PENDING,
        evidence=EVIDENCE,
        reason=reason,
        detail="",
        identity_pending_reason=identity_pending_reason,
    )


def resolved(description, *, order_id="BH0001"):
    return PriceResolutionRecord(
        order_id=order_id,
        raw_product_identity=description,
        raw_identity_key=None,
        sale_date=date(2026, 9, 5),
        identity=CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code="A1"
        ),
        status=PriceResolutionStatus.RESOLVED,
        rule=CompositionRule.TRACKING_HISTORY_AUTHORITY,
        price_vnd=Decimal("5000000"),
        price_source="Tracking PP",
        evidence=EVIDENCE,
    )


# ======================================================================
# A. Gộp theo KHOÁ inv.map — đơn vị công việc thật của Owner
# ======================================================================


def test_unresolved_descriptions_are_grouped_by_the_tracking_inv_map_key():
    """Hai cách viết cùng rơi vào một khoá `inv.map` là MỘT việc, không phải
    hai. Bên Tracking chúng ghi vào cùng một ô `/inv/map/<khoá>`, nên phân
    loại một cái là phân loại luôn cái kia."""
    groups = aggregate_unresolved_descriptions(
        [
            (pending("Tivi Samsung 75Q6FA", order_id="BH1"), Decimal("10")),
            (pending("TIVI SAMSUNG  75Q6FA!", order_id="BH2"), Decimal("20")),
            (pending("Tủ lạnh Funiki HR-T6185TDG", order_id="BH1"), Decimal("30")),
        ]
    )
    assert [group.inv_map_key for group in groups] == [
        inv_map_key("Tivi Samsung 75Q6FA"),
        inv_map_key("Tủ lạnh Funiki HR-T6185TDG"),
    ]
    tivi = groups[0]
    assert tivi.line_count == 2
    assert tivi.order_count == 2
    assert tivi.revenue_vnd == Decimal("30")
    assert tivi.description_variants == 2
    # Cách viết đại diện là một trong hai cách viết THẬT trong file nguồn,
    # không phải một chuỗi do máy dựng lại.
    assert tivi.raw_description in {"Tivi Samsung 75Q6FA", "TIVI SAMSUNG  75Q6FA!"}


def test_resolved_lines_never_appear_in_the_worklist():
    groups = aggregate_unresolved_descriptions(
        [
            (resolved("Tivi Samsung 75Q6FA"), Decimal("10")),
            (pending("Máy giặt LG FV1450S3B"), Decimal("20")),
        ]
    )
    assert [group.raw_description for group in groups] == ["Máy giặt LG FV1450S3B"]


def test_a_human_confirmed_ignore_is_not_asked_again():
    """`inv.map[khoá] == "-"` nghĩa là một người của Tracking ĐÃ xem và kết
    luận đây không phải sản phẩm cần map. Xuất lại là bắt Owner trả lời mãi
    một câu hỏi họ đã trả lời."""
    groups = aggregate_unresolved_descriptions(
        [
            (
                pending(
                    "Phí vận chuyển",
                    identity_pending_reason=(
                        PendingReason.TRACKING_INV_MAP_EXPLICIT_IGNORE
                    ),
                ),
                Decimal("10"),
            )
        ]
    )
    assert groups == ()


def test_an_authority_outage_is_never_listed_as_work_to_classify():
    """PHB-01/D1 ở đúng chỗ nó dễ tái phát nhất.

    Khi nguồn identity chưa nối/hỏng, mọi dòng Pending mang
    `IDENTITY_SOURCES_UNAVAILABLE`. Nếu bản xuất nhận cả nhánh ấy, một sự cố
    hạ tầng sẽ hiện ra dưới dạng "cả trăm mặt hàng chờ phân loại" và Owner sẽ
    đi phân loại lại những thứ đã phân loại xong."""
    record = pending(
        "Tivi Samsung 75Q6FA",
        reason=PriceResolutionReason.IDENTITY_SOURCES_UNAVAILABLE,
        identity_pending_reason=None,
    )
    assert is_unresolved_identity_record(record) is False
    assert aggregate_unresolved_descriptions([(record, Decimal("10"))]) == ()


def test_ordering_is_deterministic_and_independent_of_input_order():
    entries = [
        (pending("B sản phẩm", order_id="BH1"), None),
        (pending("A sản phẩm", order_id="BH1"), None),
        (pending("A sản phẩm", order_id="BH2"), None),
    ]
    forward = aggregate_unresolved_descriptions(entries)
    backward = aggregate_unresolved_descriptions(list(reversed(entries)))
    assert forward == backward
    # Nhiều dòng trước; "A sản phẩm" có 2 dòng nên đứng trên.
    assert [group.line_count for group in forward] == [2, 1]


def test_revenue_stays_unknown_instead_of_becoming_zero():
    """Ô trống là "chưa xác định", không phải `0` — cùng quy ước với báo cáo."""
    groups = aggregate_unresolved_descriptions([(pending("Hàng lạ"), None)])
    assert groups[0].revenue_vnd is None


# ======================================================================
# B + F. Bản xuất thật, rồi vòng lặp khép kín qua hợp đồng authority hiện có
# ======================================================================

UNKNOWN = "Điều hoà Casper GC-09IS35 chưa từng có trên bảng giá"


@pytest.fixture
def run_inputs(tmp_path):
    """Một lần chạy production thật với ĐÚNG MỘT mặt hàng chưa định danh."""
    history = write_history_capture(
        tmp_path,
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(
                        prev=7000,
                        nxt=7000,
                        at=datetime(2026, 9, 1, tzinfo=timezone.utc),
                    )
                }
            },
        ),
    )
    catalog = write_catalog_capture(
        tmp_path,
        [{"tracking_code": "A1", "name": "A1", "alt": [], "present_in_board": True}],
    )
    sales = write_sales(
        tmp_path / "sales.xlsx",
        [
            ("BH-KNOWN", "A1", date(2026, 9, 5), 1, 8_000_000),
            ("BH-NEW-1", UNKNOWN, date(2026, 9, 5), 1, 9_000_000),
            ("BH-NEW-2", UNKNOWN, date(2026, 9, 5), 2, 9_000_000),
        ],
    )
    return dict(
        sales=sales,
        tracking_capture=history,
        tracking_catalog=catalog,
        output=tmp_path / "report.xlsx",
        tmp_path=tmp_path,
    )


def sheet_rows(path):
    workbook = openpyxl.load_workbook(path, data_only=True)
    try:
        sheet = workbook["Chưa định danh"]
        return [
            row
            for row in sheet.iter_rows(min_row=2, values_only=True)
            if any(cell is not None for cell in row)
        ]
    finally:
        workbook.close()


def test_the_export_sheet_carries_one_row_per_unique_description(run_inputs):
    tmp_path = run_inputs.pop("tmp_path")
    run = demo.run_demo(**run_inputs)

    rows = sheet_rows(run.output_path)
    assert len(rows) == 1
    description, key, lines, orders, revenue, variants, reasons = rows[0]
    # Cột ĐẦU là câu tên hàng nguyên văn — đây là thứ Owner bôi đen và dán
    # sang màn "Phân loại theo tên hàng" bên Tracking.
    assert description == UNKNOWN
    # Khoá in ra phải là ĐÚNG khoá Tracking sẽ ghi, không phải một khoá riêng
    # của Reports: cùng hàm `inv_map_key()` mà resolver dùng để tra.
    assert key == inv_map_key(UNKNOWN)
    assert (lines, orders) == (2, 2)
    assert revenue == 27_000_000
    assert variants == 1
    assert "NO_CANDIDATE_IN_ANY_CATALOG" in reasons
    assert run.summary.unresolved_description_count == 1
    assert tmp_path.exists()


def test_the_export_is_byte_identical_across_two_runs_of_the_same_input(run_inputs):
    """Xác định được, nên dùng được làm bằng chứng: hai lần chạy cùng dữ liệu
    cho cùng một danh sách, cùng thứ tự."""
    tmp_path = run_inputs.pop("tmp_path")
    first = demo.run_demo(**run_inputs)
    second = demo.run_demo(**dict(run_inputs, output=tmp_path / "report-2.xlsx"))
    assert sheet_rows(first.output_path) == sheet_rows(second.output_path)


def test_a_mapping_written_to_inv_map_resolves_the_identity_on_the_next_run(
    run_inputs,
):
    """VÒNG LẶP KHÉP KÍN (PHB-01 §8, kiểm F).

    Owner phân loại câu tên hàng bên Tracking → `/inv/map/<khoá>` = mã bảng
    giá. Reports chạy lại và nhận diện được, KHÔNG cần một kho mapping nào
    bên Reports và KHÔNG cần đổi hợp đồng authority: đúng khoá cũ, đúng file
    capture cũ, đúng resolver cũ.

    Ba khẳng định đi liền nhau mới thành bằng chứng: mặt hàng biến khỏi danh
    sách chờ, nó được resolve THẬT (có mã, có giá), và khoá dùng để phân loại
    chính là khoá bản xuất đã in ra ở lần chạy trước.
    """
    tmp_path = run_inputs.pop("tmp_path")
    before = demo.run_demo(**run_inputs)
    exported_key = sheet_rows(before.output_path)[0][1]

    # Đúng thao tác Owner làm bên Tracking, không hơn: một cặp khoá → mã.
    inv_map = write_inv_map_capture(tmp_path, {exported_key: "A1"})

    after = demo.run_demo(
        **dict(run_inputs, output=tmp_path / "report-after.xlsx"),
        tracking_inv_map=inv_map,
    )
    assert sheet_rows(after.output_path) == []
    assert after.summary.unresolved_description_count == 0

    records = [
        record
        for record in after.price_records
        if record.raw_product_identity == UNKNOWN
    ]
    assert records, "phải còn đúng các dòng của mặt hàng vừa phân loại"
    assert all(
        record.identity is not None
        and record.identity.source_product_code == "A1"
        and record.identity.namespace is Namespace.TRACKING
        for record in records
    )
    assert all(record.is_resolved for record in records)


def test_an_explicit_ignore_written_to_inv_map_also_clears_the_worklist(run_inputs):
    """`"-"` là một quyết định hợp lệ của Owner ("không phải sản phẩm cần
    map"). Nó phải làm câu tên hàng biến khỏi danh sách chờ — nhưng KHÔNG
    được dựng ra một identity giả: dòng vẫn Pending, chỉ là Pending đã có
    người quyết định."""
    tmp_path = run_inputs.pop("tmp_path")
    inv_map = write_inv_map_capture(tmp_path, {inv_map_key(UNKNOWN): "-"})
    run = demo.run_demo(**run_inputs, tracking_inv_map=inv_map)

    assert sheet_rows(run.output_path) == []
    records = [
        record
        for record in run.price_records
        if record.raw_product_identity == UNKNOWN
    ]
    assert records
    assert all(record.identity is None for record in records)
    assert all(
        record.identity_pending_reason
        is PendingReason.TRACKING_INV_MAP_EXPLICIT_IGNORE
        for record in records
    )
