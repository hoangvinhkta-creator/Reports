"""DEC-PAN-001 — PRICE_AUTHORITY_NORMALIZATION + ACCOUNTING_REASON_NORMALIZATION.

Owner Decision: trong Reports chỉ có MỘT authority cho giá mua phục vụ phân
tích bán hàng — **Tracking PP có hiệu lực tại ngày bán**, gọi ở nghiệp vụ là
"Giá mua tham chiếu". Sổ bán hàng chỉ cung cấp `sản phẩm + ngày bán`; nó KHÔNG
phải nguồn giá nhập, và không tồn tại một "Accounting Purchase Price
Authority" chạy song song.

Hai trường `accounting_*` vì thế được phân loại lại, KHÔNG bị xoá:

    accounting_purchase_price = LEGACY_INTERNAL_PP_CARRIER
    accounting_profit         = LEGACY_DERIVED_FIELD

Tên trường legacy KHÔNG tự nó tạo ra business authority. Hệ quả DUY NHẤT ở
tầng hành vi: hai mã `Pending.accounting_*` không còn là management reason của
kết quả MỚI. Công thức, storage, schema, PP resolution, KPI, identity: không
đổi một dòng.

Nhóm test này canh đúng chín điều đó (brief §17 A–K) — trong đó điều quan
trọng nhất là những thứ PHẢI KHÔNG đổi.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.beta_presentation import REASON_DISPLAY_LABELS, RETIRED_PENDING_REASONS
from app.composition import build_price_composition
from app.modules.adjustment.confirmed_adjustment_source import (
    ConfirmedAdjustmentSource,
)
from app.modules.domain.models import (
    PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT,
    PRICE_SOURCE_PENDING,
)
from app.modules.exporting.excel_exporter import present_lines
from app.modules.importing.raw_reader import read_raw_rows
from app.modules.kpi.kpi_profit_engine import (
    AUTHORITY_UNAVAILABLE,
    PROVENANCE_ELIGIBLE_COSTS_EMPTY_SET,
    EligibleCostsAuthority,
)
from app.modules.product.identity.commands import ConfirmHistoricalEntry
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.registry import (
    ConfirmationAuthority,
    HistoricalConfirmedRegistry,
    HistoricalConfirmedRegistryEntry,
    SourceReportRef,
)
from app.modules.profit.profit_engine import compute_accounting_profit
from app.pipeline import run_import

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"

ACCOUNTING_REASONS = (
    "Pending.accounting_purchase_price",
    "Pending.accounting_profit",
)
VALID_COSTS_AUTHORITY = EligibleCostsAuthority(
    is_valid=True, categories=(), provenance=PROVENANCE_ELIGIBLE_COSTS_EMPTY_SET
)
CONFIRMED_PP = Decimal("500000")


# --- Dàn dựng: một lần chạy production THẬT trên workbook tổng hợp ---------

def _registry_for(rows) -> HistoricalConfirmedRegistry:
    """Xác nhận PP lịch sử cho MỌI dòng có đủ (ngày bán, sản phẩm).

    Dùng cổng DI thật (`identity_registry`) chứ không mock: mục tiêu là chứng
    minh hành vi của đường production, và một dòng có PP đã resolve là điều
    kiện cần để tách "thiếu KPI vì thiếu PP" khỏi "thiếu KPI vì hỏng authority".
    """
    registry = HistoricalConfirmedRegistry()
    for index, row in enumerate(rows):
        if row.date is None or row.product_raw is None:
            continue
        entry = HistoricalConfirmedRegistryEntry(
            entry_id=f"HCR-{index}",
            sale_date=row.date,
            order_id=row.order_id,
            raw_product_identity=row.product_raw,
            raw_identity_key=raw_identity_key(row.product_raw),
            confirmed_purchase_price=CONFIRMED_PP,
            source_report_ref=SourceReportRef(
                report_id="RPT-PAN", file_name="pan.xlsx", content_hash="0" * 64
            ),
            confirmed_by="test",
            confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            confirmation_authority=ConfirmationAuthority.OWNER,
        )
        registry.append(ConfirmHistoricalEntry(
            actor_id="test", client_request_id=f"req-{index}",
            expected_version=0, entry_id=entry.entry_id, entry=entry,
        ))
    return registry


def _run(raw_path, *, resolve_pp=True, costs_authority=VALID_COSTS_AUTHORITY,
         adjustment_source=None):
    """Chạy `run_import` thật rồi trình bày qua `present_lines` thật.

    `resolve_pp=False` KHÔNG chỉ là "bỏ registry": exporter đòi một
    `PriceResolutionRecord` cho mỗi dòng chưa confirmed, nên nhánh ấy phải đi
    qua composition thật (đúng đường production) — nó cũng chính là thứ sinh
    ra mã identity/PP mà nhóm test này quan sát.
    """
    rows = read_raw_rows(raw_path)
    composition = None if resolve_pp else build_price_composition(CONFIG_DIR)
    result = run_import(
        raw_path,
        config_dir=CONFIG_DIR,
        identity_registry=_registry_for(rows) if resolve_pp
        else HistoricalConfirmedRegistry(),
        price_composition=composition,
        confirmed_adjustment_source=(
            ConfirmedAdjustmentSource({}) if adjustment_source is None
            else adjustment_source
        ),
        eligible_costs_authority=costs_authority,
    )
    records = () if composition is None else composition.records
    return present_lines(result, records, rows)


def _view(views, order_id):
    return next(v for v in views if v.line.order_id == order_id)


@pytest.fixture
def resolved(synthetic_raw_path):
    """Mọi dòng: identity đã xác nhận, PP đã resolve, authority KPI hợp lệ."""
    return _run(synthetic_raw_path)


@pytest.fixture
def unresolved(synthetic_raw_path):
    """Không có registry -> PP Pending trên mọi dòng."""
    return _run(synthetic_raw_path, resolve_pp=False)


# --- A. Tracking PP vẫn nạp vào đúng carrier nội bộ ------------------------

def test_a_resolved_purchase_price_still_lands_in_the_legacy_internal_carrier(
    resolved,
):
    """`accounting_purchase_price` vẫn là carrier của PP đã resolve.

    Đây chính là lý do KHÔNG đổi tên trường: nó đang chở đúng thứ Owner gọi là
    "Giá mua tham chiếu", và đổi tên bây giờ tạo blast radius ngang mà không
    đổi được một con số nào cho người dùng.
    """
    line = _view(resolved, "BH0001").line
    assert line.accounting_purchase_price == CONFIRMED_PP
    assert line.price_source == PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT


# --- B. Không có nguồn giá kế toán độc lập nào được thêm vào ---------------

def test_b_no_independent_accounting_purchase_price_source_exists(resolved,
                                                                  unresolved):
    """PP resolve được thì carrier có giá; PP Pending thì carrier là None.

    Nếu tồn tại một nguồn giá nhập kế toán ĐỘC LẬP, dòng ở `unresolved` đã phải
    có giá từ nguồn ấy. Nó không có — carrier theo Tracking PP và chỉ theo
    Tracking PP.
    """
    assert _view(resolved, "BH0001").line.accounting_purchase_price == CONFIRMED_PP
    pending = _view(unresolved, "BH0001").line
    assert pending.accounting_purchase_price is None
    assert pending.price_source == PRICE_SOURCE_PENDING


# --- C. Thiếu PP vẫn cho ra lý do actionable đúng --------------------------

def test_c_missing_purchase_price_still_yields_the_actionable_reason(unresolved):
    """"Thiếu giá mua tham chiếu" là mã actionable được GIỮ, không đụng tới."""
    view = _view(unresolved, "BH0001")
    assert "Missing.PurchasePrice" in view.reasons
    assert REASON_DISPLAY_LABELS["Missing.PurchasePrice"] == "Thiếu giá mua tham chiếu"
    assert view.status == "PENDING"


# --- D. Kết quả MỚI không còn sinh hai mã kế toán --------------------------

def test_d_new_results_never_generate_the_two_accounting_reasons(resolved,
                                                                unresolved):
    """Yêu cầu trung tâm của brief §6, kiểm trên CẢ HAI phía của nhánh PP."""
    for views in (resolved, unresolved):
        for view in views:
            for reason in ACCOUNTING_REASONS:
                assert reason not in view.reasons


def test_d_the_pending_line_now_states_one_root_cause_not_a_chain(unresolved):
    """Brief §5 — MỘT nguyên nhân gốc, MỘT lý do quản trị actionable.

    Trước DEC-PAN-001 dòng này mang 5 mã cho đúng một chuỗi hỏng. Ba mã còn
    lại đều trỏ tới một việc người thật phải làm: nhận diện sản phẩm, lấy giá
    mua tham chiếu, và (độc lập) authority KPI.
    """
    view = _view(unresolved, "BH0001")
    assert set(view.reasons) == {
        "IDENTITY_SOURCES_UNAVAILABLE", "Missing.PurchasePrice",
        "Pending.eligible_kpi_profit",
    }


# --- E. Trường + công thức kế toán vẫn còn nguyên bên trong ----------------

def test_e_accounting_fields_and_formula_remain_available_internally(resolved):
    """Gỡ mã reason KHÔNG được phép gỡ dữ liệu: `accounting_profit` vẫn tính
    đúng `(sell_price - accounting_purchase_price) * quantity`."""
    line = _view(resolved, "BH0001").line
    expected = (line.sell_price - CONFIRMED_PP) * line.quantity
    assert line.accounting_profit == expected
    assert compute_accounting_profit(line) == expected


def test_e_the_legacy_fields_are_still_persisted_shaped_fields(resolved):
    """Không schema migration, không xoá field — carrier vẫn là thuộc tính
    thật của `WorkingLine`, không phải một thứ đã bị gỡ khỏi model."""
    line = _view(resolved, "BH0001").line
    assert hasattr(line, "accounting_purchase_price")
    assert hasattr(line, "accounting_profit")


# --- F. NULL != 0 ---------------------------------------------------------

def test_f_a_missing_price_stays_none_and_never_becomes_zero(unresolved):
    """DEC-103. Ô trống và ô bằng 0 là hai sự thật khác nhau; gỡ reason không
    được phép làm None trượt thành 0."""
    line = _view(unresolved, "BH0001").line
    assert line.accounting_purchase_price is None
    assert line.accounting_profit is None
    assert line.accounting_purchase_price != Decimal("0")
    assert line.accounting_profit != Decimal("0")


# --- G/H. KPI không đổi cho dòng đã resolve --------------------------------

def test_g_kpi_values_are_unchanged_for_resolved_lines(resolved):
    """Không đổi công thức KPI, không đổi PP adjustment, không đổi coverage."""
    line = _view(resolved, "BH0001").line
    assert line.kpi_purchase_price == CONFIRMED_PP
    assert line.eligible_kpi_profit == (
        (line.sell_price - CONFIRMED_PP) * line.quantity - line.discount
    )


def test_h_a_fully_resolved_line_is_auto_with_no_reason_at_all(resolved):
    """Coverage KPI không đổi: dòng đủ dữ liệu vẫn AUTO và vẫn có KPI."""
    view = _view(resolved, "BH0001")
    assert view.reasons == ()
    assert view.status == "AUTO"
    assert view.line.eligible_kpi_profit is not None


# --- §7. `Pending.eligible_kpi_profit` là lý do ĐỘC LẬP, có bằng chứng -----

def test_kpi_reason_is_independent_when_the_eligible_costs_authority_breaks(
    synthetic_raw_path,
):
    """Bằng chứng cho quyết định GIỮ mã KPI (brief §7, nhánh "reachable case").

    Identity đã nhận diện, PP đã resolve, `kpi_purchase_price` đã có — mọi
    input actionable phía trên đều hợp lệ — nhưng `config/eligible_costs.yaml`
    hỏng khiến KPI fail-closed. Đây là mã DUY NHẤT nói cho người vận hành biết
    có một authority cần sửa; gỡ nó đi là giấu một lỗi thật.
    """
    views = _run(synthetic_raw_path, costs_authority=AUTHORITY_UNAVAILABLE)
    view = _view(views, "BH0001")
    assert view.line.accounting_purchase_price == CONFIRMED_PP
    assert view.line.accounting_profit is not None
    assert view.line.kpi_purchase_price == CONFIRMED_PP  # upstream KPI vẫn tốt
    assert view.line.eligible_kpi_profit is None
    assert view.reasons == ("Pending.eligible_kpi_profit",)


def test_kpi_reason_is_independent_when_the_confirmed_adjustment_source_is_gone(
    synthetic_raw_path,
):
    """Đường độc lập thứ hai (DEC-144 §3): nguồn confirmed adjustment
    UNAVAILABLE. PP vẫn resolve, nhưng KPI fail-closed — và không mã nào khác
    báo điều đó."""
    views = _run(synthetic_raw_path,
                 adjustment_source=ConfirmedAdjustmentSource(None))
    view = _view(views, "BH0001")
    assert view.line.accounting_purchase_price == CONFIRMED_PP
    assert view.line.kpi_purchase_price is None
    assert view.line.eligible_kpi_profit is None
    assert view.reasons == ("Pending.eligible_kpi_profit",)


# --- I. Ngữ nghĩa Product Identity không đổi -------------------------------

def test_i_product_identity_reasons_are_untouched(unresolved):
    """Tracking vẫn là Product Identity Authority; mã identity không bị đụng."""
    view = _view(unresolved, "BH0001")
    assert "IDENTITY_SOURCES_UNAVAILABLE" in view.reasons
    assert REASON_DISPLAY_LABELS["IDENTITY_SOURCES_UNAVAILABLE"] == (
        "Chưa có dữ liệu để nhận diện sản phẩm"
    )


# --- J. Lịch sử đã persist KHÔNG bị viết lại -------------------------------

def test_j_retired_codes_are_still_rendered_for_persisted_history():
    """Brief §9 — KHÔNG backfill, KHÔNG migration.

    Một result version đã lưu trước quyết định này vẫn chứa hai mã kế toán, và
    UI phải đọc lại chúng TRUNG THỰC. Bảng nhãn vì thế giữ nguyên hai nhãn —
    chúng chỉ thôi là mã được SINH RA, chứ không bị xoá khỏi lịch sử.
    """
    from app.web import sales_presentation as sp

    persisted = ["IDENTITY_SOURCES_UNAVAILABLE", "Missing.PurchasePrice",
                 "Pending.accounting_purchase_price", "Pending.accounting_profit",
                 "Pending.eligible_kpi_profit"]
    assert sp.reason_labels(persisted) == [
        "Chưa có dữ liệu để nhận diện sản phẩm", "Thiếu giá mua tham chiếu",
        "Thiếu giá nhập kế toán", "Thiếu lợi nhuận kế toán", "Thiếu lợi nhuận KPI",
    ]


def test_j_the_retired_set_is_exactly_the_two_accounting_codes():
    assert RETIRED_PENDING_REASONS == set(ACCOUNTING_REASONS)


# --- K. Status delta được ĐO, không phải được khẳng định -------------------

def test_k_removing_the_two_codes_changes_no_line_status(unresolved):
    """Brief §16 — số AUTO/PENDING không đổi, và đây là lý do tại sao.

    Mọi dòng từng mang mã kế toán ĐỀU còn ít nhất một mã actionable khác
    (`Missing.PurchasePrice`), nên không dòng nào có thể lật PENDING -> AUTO
    chỉ vì hai mã kia biến mất. Test này canh chính điều kiện ấy thay vì canh
    một con số đếm — nó vẫn đúng khi fixture đổi kích thước.
    """
    accounting_only = [
        view for view in unresolved
        if view.reasons and set(view.reasons) <= set(ACCOUNTING_REASONS)
    ]
    assert accounting_only == []
    for view in unresolved:
        if view.line.accounting_purchase_price is None:
            assert "Missing.PurchasePrice" in view.reasons
            assert view.status == "PENDING"
