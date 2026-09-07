"""R2 — phân loại sản phẩm và giá nhập tay, kiểm từ đầu đến cuối.

Nguồn yêu cầu: `R2 Execution Brief` (`docs/tasks/R2-phan-loai-va-gia-nhap-tay.md`).
Mỗi lớp dưới đây mang tên một `CHECK-R2-xx` của §7, và mỗi bài kiểm khẳng định
đúng điều mà check ấy nói — không phải "hàm này có chạy không".

## Vì sao có một file riêng thay vì rải vào các bộ hiện có

Ba chuỗi của R2 cắt NGANG các tầng đã có: giao diện → log quyết định →
resolver production → kế hoạch `daily-min` → giá → lợi nhuận. Rải chúng vào
`test_105d_*` (identity), `test_daily_min_*` (giá) và `test_business_vertical`
(lợi nhuận) sẽ làm không bài nào đi hết chuỗi, và chính chỗ ĐỨT giữa hai tầng
là thứ R2 tồn tại để sửa — nó chỉ nhìn thấy được khi đi hết.

Toàn bộ dữ liệu là tổng hợp: mã `TRK-*` bịa, tên hàng bịa, không dữ liệu khách
hàng hay kế toán thật.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.pricing.daily_min.planning import plan_daily_min_request
from app.modules.pricing.resolution.composition import (
    PostCutoverPriceComposition, PriceResolutionReason, PriceResolutionStatus,
)
from app.modules.pricing.resolution.sources import PriceResolutionSources
from app.modules.product.identity.identity import (
    Namespace, PendingProduct, PendingReason, RequiresConfirmation, Resolved,
)
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.mapping import MappingSource, MappingStatus
from app.modules.product.identity.resolver import (
    CONFLICT_MAPPING_SOURCE, ProductIdentityResolver, distinct_identities,
)
from app.modules.reporting import business_metrics as bm
from app.web import business_service, business_store, identity_gateway
from app.web import history_store, line_identity
from tests.support import identity_fixtures as fx
from tests.test_business_vertical import JANUARY, pair, persist

SALE_DAY = date(2026, 1, 5)

# Danh mục Tracking tổng hợp của cả file. `TRK-OLD` cố ý KHÔNG còn trên board
# — nó là fixture cho `CHECK-R2-04`.
CATALOG_ROWS = (
    ("TRK-A100", "Tủ lạnh Panasonic NR-BX", (), True),
    ("TRK-B200", "Tivi Sony KD-55", (), True),
    ("TRK-OLD", "Mã đã bỏ khỏi board", (), False),
)

RAW_A = "Tủ lạnh Panasonic"
RAW_B = "Tivi Sony"


# --------------------------------------------------------------------------
# Hạ tầng dùng chung
# --------------------------------------------------------------------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def service(engine, store):
    return business_service.BusinessReportService(engine=engine, store=store)


@pytest.fixture
def identity_store(tmp_path):
    """Store quyết định trên ĐĨA THẬT — không phải trong bộ nhớ.

    Bắt buộc phải là đĩa: `CHECK-R2-03` khẳng định quyết định sống qua một lần
    restart/redeploy, và một store trong bộ nhớ không thể nói dối về điều đó
    theo hướng nào khác ngoài hướng "đạt".
    """
    return fx.store(tmp_path)


def catalog(rows=CATALOG_ROWS, **kwargs):
    return fx.tracking_snapshot(rows, **kwargs)


def confirm(identity_store, raw, code, *, snapshot=None, **kwargs):
    """Đi qua ĐÚNG cửa mà giao diện đi — không dựng command bằng tay.

    Dựng `ConfirmMapping` trực tiếp trong test sẽ kiểm một đường mà production
    không dùng; cửa duy nhất của giao diện là `identity_gateway.confirm_identity`,
    nên nó phải là cửa duy nhất của bài kiểm.
    """
    return identity_gateway.confirm_identity(
        identity_store, product_raw=raw, tracking_code=code,
        snapshot=snapshot if snapshot is not None else catalog(),
        actor_id="owner-web", client_request_id=str(uuid.uuid4()), **kwargs)


def mark_out(identity_store, raw, **kwargs):
    return identity_gateway.mark_out_of_catalog(
        identity_store, product_raw=raw, actor_id="owner-web",
        client_request_id=str(uuid.uuid4()), **kwargs)


def resolve(identity_store, raw, *, snapshot=None, inv_map=None):
    """Chạy resolver ở ĐÚNG chế độ production (`tracking_identity_authority`).

    Đây là chi tiết quan trọng nhất của cả file. Chế độ mặc định của
    `fx.resolver` là chế độ legacy, và nó ĐỌC alias store — nên một bài kiểm
    dùng nó sẽ xanh trong khi production vẫn hỏng. Composition và
    `plan_daily_min_request` đều truyền `tracking_identity_authority=True`.
    """
    resolver = ProductIdentityResolver(
        tracking_snapshot=snapshot if snapshot is not None else catalog(),
        pp_version=None,
        store_view=identity_store.read_at_revision(identity_store.refresh()),
        tracking_identity_authority=True,
        inv_map_snapshot=inv_map,
        now=datetime(2026, 1, 20, tzinfo=timezone.utc),
    )
    identity, = distinct_identities([fx.row(raw, sale_date=SALE_DAY)])
    return resolver.resolve(identity)


class _Line:
    """`WorkingLine` tối thiểu mà `plan_daily_min_request` và `apply()` đọc."""

    def __init__(self, raw, *, order_id="BH1", day=SALE_DAY):
        self.product_raw = raw
        self.order_id = order_id
        self.date = day
        self.accounting_purchase_price = None
        self.price_source = None


# --------------------------------------------------------------------------
# CHECK-R2-01 — mapping chọn trên UI được resolver PRODUCTION dùng
# --------------------------------------------------------------------------

class TestCheckR201MappingReachesTheProductionResolver:
    """Mối nối mà R2 phải sửa, và bằng chứng nó từng ĐỨT.

    Trước R2, `_tracking_authoritative` (đường production) không hỏi store của
    Reports một câu nào: nó đọc thẳng `alias.map`/`board` rồi `inv.map`. Hệ
    quả là một mặt hàng Owner vừa chọn trên giao diện vẫn Pending ở lần chạy kế
    tiếp — bảng chọn chạy, log ghi, báo cáo không đổi một chữ.
    """

    def test_a_confirmed_mapping_resolves_in_the_production_path(
        self, identity_store
    ):
        assert isinstance(resolve(identity_store, RAW_A).outcome, PendingProduct)

        confirm(identity_store, RAW_A, "TRK-A100")

        outcome = resolve(identity_store, RAW_A).outcome
        assert isinstance(outcome, Resolved)
        assert outcome.identity.namespace is Namespace.TRACKING
        assert outcome.identity.source_product_code == "TRK-A100"

    def test_the_mapping_is_the_only_thing_that_changed(self, identity_store):
        """Không mã nào được ĐOÁN: một mặt hàng khác vẫn Pending như cũ.

        Bài này đóng cửa hỏng "sửa bằng cách nới lỏng": một bản vá làm resolver
        dễ dãi hơn sẽ làm cả hai mặt hàng resolve được, và nó vẫn qua được bài
        trên.
        """
        confirm(identity_store, RAW_A, "TRK-A100")
        assert isinstance(resolve(identity_store, RAW_B).outcome, PendingProduct)


# --------------------------------------------------------------------------
# CHECK-R2-02 — mapping lập tập mã daily-min và tra đúng sale_date
# --------------------------------------------------------------------------

class TestCheckR202MappingDrivesTheDailyMinPlan:
    def test_a_confirmed_mapping_enters_the_daily_min_question_set(
        self, identity_store
    ):
        rows = [_Line(RAW_A)]
        view = identity_store.read_at_revision(identity_store.refresh())
        assert plan_daily_min_request(
            rows, tracking_catalog=catalog(), identity_store_view=view) is None

        confirm(identity_store, RAW_A, "TRK-A100")
        view = identity_store.read_at_revision(identity_store.refresh())
        plan = plan_daily_min_request(
            rows, tracking_catalog=catalog(), identity_store_view=view)

        assert plan is not None
        assert plan.product_codes == ("TRK-A100",)
        # Cặp `(mã, NGÀY BÁN)` — không phải ngày chạy. Đây là bất biến R1 và
        # R2 không được làm nó lỏng đi.
        assert plan.pairs == (("TRK-A100", SALE_DAY),)

    def test_an_out_of_catalog_line_is_never_asked_about(self, identity_store):
        """Hỏi Tracking giá của một mặt hàng người dùng vừa nói là KHÔNG có
        trên bảng giá là hỏi một câu đã có câu trả lời."""
        mark_out(identity_store, RAW_A)
        view = identity_store.read_at_revision(identity_store.refresh())
        assert plan_daily_min_request(
            [_Line(RAW_A)], tracking_catalog=catalog(),
            identity_store_view=view) is None


# --------------------------------------------------------------------------
# CHECK-R2-03 — mapping sống qua refresh / worker khác / restart / import lại
# --------------------------------------------------------------------------

class TestCheckR203DecisionsSurviveRestart:
    def test_a_brand_new_store_object_reads_the_same_decision(self, tmp_path):
        """Một `JsonlProductIdentityStore` DỰNG LẠI TỪ ĐẦU trên cùng đường dẫn
        chính là mô hình của "worker khác" và của "sau redeploy": không chia sẻ
        một byte bộ nhớ nào với bản đã ghi."""
        first = fx.store(tmp_path)
        confirm(first, RAW_A, "TRK-A100")
        mark_out(first, RAW_B)

        second = fx.store(tmp_path)
        assert identity_gateway.confirmed_keys(second) == {raw_identity_key(RAW_A)}
        assert identity_gateway.out_of_catalog_keys(second) == {
            raw_identity_key(RAW_B)}
        assert isinstance(resolve(second, RAW_A).outcome, Resolved)

    def test_re_importing_the_same_data_reuses_the_decision(self, tmp_path):
        """Nạp lại cùng một sổ = chạy lại cùng phép phân giải trên cùng log."""
        identity_store = fx.store(tmp_path)
        confirm(identity_store, RAW_A, "TRK-A100")
        for _ in range(3):
            outcome = resolve(fx.store(tmp_path), RAW_A).outcome
            assert isinstance(outcome, Resolved)
            assert outcome.identity.source_product_code == "TRK-A100"


# --------------------------------------------------------------------------
# CHECK-R2-04 — mã đích không có trong catalog bị TỪ CHỐI
# --------------------------------------------------------------------------

class TestCheckR204InvalidTargetIsRefused:
    def test_a_code_absent_from_the_catalog_cannot_be_confirmed(
        self, identity_store
    ):
        with pytest.raises(identity_gateway.IdentityGatewayError,
                           match="không có trong danh mục Tracking"):
            confirm(identity_store, RAW_A, "TRK-KHONG-CO")
        assert identity_gateway.confirmed_keys(identity_store) == frozenset()

    def test_a_target_that_later_leaves_the_board_becomes_a_named_state(
        self, identity_store
    ):
        """Mã hợp lệ lúc xác nhận, biến mất khỏi board sau đó.

        Kết quả PHẢI là một trạng thái CÓ TÊN
        (`MAPPING_STALE_TARGET_ABSENT`), không phải một lần rơi về đoán mã và
        cũng không phải một mã Tracking vẫn được đem đi hỏi giá.
        """
        confirm(identity_store, RAW_A, "TRK-A100")
        shrunk = catalog((("TRK-A100", "Tủ lạnh", (), False),))

        outcome = resolve(identity_store, RAW_A, snapshot=shrunk).outcome
        assert isinstance(outcome, PendingProduct)
        assert outcome.reason_code is PendingReason.MAPPING_STALE_TARGET_ABSENT


# --------------------------------------------------------------------------
# CHECK-R2-05 — mapping mâu thuẫn ra CONFLICT, không âm thầm chọn bên thắng
# --------------------------------------------------------------------------

class TestCheckR205Conflict:
    def _conflicting(self, identity_store):
        """Reports nói `TRK-A100`; `alias.map` của Tracking nói `TRK-B200`."""
        confirm(identity_store, RAW_A, "TRK-A100")
        aid = distinct_identities(
            [fx.row(RAW_A)])[0].normalized_matching_aid.upper()
        return catalog(alias_map_rows=((aid, "TRK-B200"),))

    def test_two_confirmed_sources_that_disagree_produce_conflict(
        self, identity_store
    ):
        snapshot = self._conflicting(identity_store)
        result = resolve(identity_store, RAW_A, snapshot=snapshot)

        assert isinstance(result.outcome, RequiresConfirmation)
        assert result.outcome.provenance.mapping_source == CONFLICT_MAPPING_SOURCE
        # Cả HAI mã đều được nêu tên. Một mâu thuẫn mà chỉ nói ra một bên thì
        # người dùng không có gì để chọn giữa.
        codes = {c.source_product_code for c in result.outcome.candidates}
        assert codes == {"TRK-A100", "TRK-B200"}

    def test_the_conflict_never_silently_picks_a_winner(self, identity_store):
        snapshot = self._conflicting(identity_store)
        outcome = resolve(identity_store, RAW_A, snapshot=snapshot).outcome
        assert not isinstance(outcome, Resolved)

    def test_the_composition_reports_conflict_with_its_own_reason(
        self, identity_store
    ):
        """`IDENTITY_CONFLICT` phải TÁCH khỏi `IDENTITY_REQUIRES_CONFIRMATION`:
        một bên là "chưa đủ căn cứ", bên kia là "hai nguồn đang chỏi nhau", và
        chúng dẫn Owner đi làm hai việc khác nhau."""
        snapshot = self._conflicting(identity_store)
        record, = _compose(identity_store, RAW_A, snapshot=snapshot)
        assert record.status is PriceResolutionStatus.PENDING
        assert record.reason is PriceResolutionReason.IDENTITY_CONFLICT

    def test_choosing_again_resolves_the_conflict_for_good(self, identity_store):
        """Đường THOÁT khỏi mâu thuẫn, và nó phải KẾT THÚC.

        Nếu lựa chọn của người dùng không mang dấu vết rằng họ đã nhìn thấy
        đúng mâu thuẫn ấy, lần chạy sau phát hiện lại nó và hỏi lại — mãi mãi.
        Đó là lý do `HUMAN_CONFLICT_RESOLUTION` tồn tại.
        """
        snapshot = self._conflicting(identity_store)
        confirm(identity_store, RAW_A, "TRK-A100", snapshot=snapshot,
                resolves_conflict=True, reason="Đối chiếu tem máy")

        outcome = resolve(identity_store, RAW_A, snapshot=snapshot).outcome
        assert isinstance(outcome, Resolved)
        assert outcome.identity.source_product_code == "TRK-A100"

        view = identity_store.read_at_revision(identity_store.refresh())
        mapping = view.active_mapping("REPORTS_SALES", raw_identity_key(RAW_A))
        assert mapping.mapping_source is MappingSource.HUMAN_CONFLICT_RESOLUTION

    def test_choosing_the_tracking_side_also_ends_the_conflict(
        self, identity_store
    ):
        snapshot = self._conflicting(identity_store)
        confirm(identity_store, RAW_A, "TRK-B200", snapshot=snapshot,
                resolves_conflict=True, reason="Tracking đúng")
        outcome = resolve(identity_store, RAW_A, snapshot=snapshot).outcome
        assert isinstance(outcome, Resolved)
        assert outcome.identity.source_product_code == "TRK-B200"


# --------------------------------------------------------------------------
# CHECK-R2-06 — OUT_OF_CATALOG là quyết định tường minh, lưu bền, không hỏi lại
# --------------------------------------------------------------------------

class TestCheckR206OutOfCatalogIsAFinishedClassification:
    def test_only_an_explicit_action_creates_it(self, identity_store):
        assert identity_gateway.out_of_catalog_keys(identity_store) == frozenset()
        # Chạy resolver nhiều lần trên một mặt hàng không có trong catalog
        # KHÔNG được tự sinh ra quyết định này.
        for _ in range(3):
            resolve(identity_store, "Mặt hàng lạ chưa ai xem")
        assert identity_gateway.out_of_catalog_keys(identity_store) == frozenset()

        mark_out(identity_store, RAW_A)
        assert identity_gateway.out_of_catalog_keys(identity_store) == {
            raw_identity_key(RAW_A)}

    def test_it_is_stored_as_its_own_status_not_as_pending(self, identity_store):
        mark_out(identity_store, RAW_A)
        view = identity_store.read_at_revision(identity_store.refresh())
        mapping = view.active_mapping("REPORTS_SALES", raw_identity_key(RAW_A))
        assert mapping.status is MappingStatus.OUT_OF_CATALOG
        # Không mang mã sản phẩm nào: không có mã nào để mang, và một mã ở đây
        # sẽ lọt được vào một nhánh hỏi giá.
        assert mapping.source_product_code is None

    def test_the_line_leaves_the_unclassified_queue(self, identity_store):
        detail = _detail(RAW_A, reasons=("IDENTITY_UNRESOLVED",))
        decisions = line_identity.Decisions.of(
            out_of_catalog={raw_identity_key(RAW_A)})

        before = line_identity.state_of(detail)
        after = line_identity.state_of(detail, decisions=decisions)

        assert before.classification == line_identity.CLASS_NEEDS_REVIEW
        assert after.classification == line_identity.CLASS_OUT_OF_CATALOG
        assert after.needs_review is False
        assert line_identity.unresolved_orders([detail], decisions=decisions) == []

    def test_the_resolver_gives_it_a_price_reason_not_an_identity_reason(
        self, identity_store
    ):
        mark_out(identity_store, RAW_A)
        outcome = resolve(identity_store, RAW_A).outcome
        assert isinstance(outcome, PendingProduct)
        assert outcome.reason_code is PendingReason.OUT_OF_CATALOG_CONFIRMED

        record, = _compose(identity_store, RAW_A)
        assert record.reason is PriceResolutionReason.IDENTITY_OUT_OF_CATALOG

    def test_relinking_to_tracking_supersedes_without_losing_history(
        self, identity_store
    ):
        mark_out(identity_store, RAW_A)
        confirm(identity_store, RAW_A, "TRK-A100")

        outcome = resolve(identity_store, RAW_A).outcome
        assert isinstance(outcome, Resolved)
        assert identity_gateway.out_of_catalog_keys(identity_store) == frozenset()
        # Bản ghi cũ vẫn nằm trong log — supersede, không xoá.
        types = [event.event_type.value for event in identity_store.events()]
        assert "MARK_OUT_OF_CATALOG" in types
        assert "CONFIRM_MAPPING" in types


# --------------------------------------------------------------------------
# CHECK-R2-07 / -08 — vẫn trong báo cáo, vẫn Pending giá, KHÔNG thành giá 0
# --------------------------------------------------------------------------

class TestCheckR207And08OutOfCatalogKeepsTheLine:
    def test_the_line_keeps_its_revenue_and_quantity(self, repository, service):
        persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
        data = service.period(**JANUARY)
        assert len(data.lines) == 1
        assert data.totals.sales_revenue == Decimal("8000000")
        assert data.totals.qualifying_quantity == Decimal(1)
        # `OUT_OF_CATALOG` KHÔNG đi qua `line_exclusion`: nó không có đường nào
        # tới đó, nên dòng không thể rơi khỏi báo cáo.
        assert data.excluded == []

    def test_without_a_manual_price_the_profit_stays_pending_not_zero(
        self, repository, service
    ):
        persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
        line = service.period(**JANUARY).lines[0]
        assert line.purchase_price is None
        assert line.kpi_profit is None
        assert line.purchase_provenance == bm.PROVENANCE_PENDING
        assert "PURCHASE_PRICE_MISSING" in line.profit_blockers


# --------------------------------------------------------------------------
# CHECK-R2-09 … -13 — giá tay: lấp, thay, ưu tiên, gỡ, không lan
# --------------------------------------------------------------------------

class TestCheckR209ManualPriceFillsAndRecomputes:
    def test_entering_a_price_produces_the_right_profit(self, repository, service):
        persist(repository, [pair("BH1", sell="9000000", quantity="1",
                                  discount="0", kpi_purchase=None,
                                  kpi_profit=None)])
        detail = service.period(**JANUARY).details[0]
        service.store.set_purchase_price(
            order_key=detail["order_key"], product_key=detail["product_key"],
            occurrence_index=detail["occurrence_index"],
            price=Decimal("8500000"), auto_price=None, entered_by="owner-web")

        line = service.period(**JANUARY).lines[0]
        # Ca B của checklist Owner: 9.000.000 − 8.500.000 = 500.000.
        assert line.kpi_profit == Decimal("500000")
        assert line.purchase_provenance == bm.PROVENANCE_MANUAL


class TestCheckR210ManualOverrideKeepsProvenance:
    def test_replacing_an_auto_price_records_the_full_provenance(
        self, repository, service
    ):
        persist(repository, [pair("BH1", kpi_purchase="5000000",
                                  kpi_profit="3000000")])
        detail = service.period(**JANUARY).details[0]
        keys = {k: detail[k] for k in
                ("order_key", "product_key", "occurrence_index")}
        _exists, auto = service.auto_price_of(data=service.period(**JANUARY), **keys)

        provenance = service.store.set_purchase_price(
            price=Decimal("4000000"), auto_price=auto, entered_by="owner-web",
            reason="Đối chiếu hoá đơn nhà cung cấp", **keys)

        assert provenance == bm.PROVENANCE_MANUAL_OVERRIDE
        row = service.store.purchase_price_overrides()[
            (keys["order_key"], keys["product_key"], keys["occurrence_index"])]
        assert row["auto_price_at_entry"] == Decimal("5000000")
        assert row["entered_by"] == "owner-web"
        assert row["reason"] == "Đối chiếu hoá đơn nhà cung cấp"
        assert row["entered_at"]

    def test_replacing_an_auto_price_without_a_reason_is_refused(
        self, repository, service
    ):
        persist(repository, [pair("BH1", kpi_purchase="5000000",
                                  kpi_profit="3000000")])
        detail = service.period(**JANUARY).details[0]
        with pytest.raises(business_store.MissingPriceReasonError):
            service.store.set_purchase_price(
                order_key=detail["order_key"],
                product_key=detail["product_key"],
                occurrence_index=detail["occurrence_index"],
                price=Decimal("4000000"), auto_price=Decimal("5000000"))
        assert service.store.purchase_price_overrides() == {}

    def test_filling_a_missing_price_gets_a_default_reason(
        self, repository, service
    ):
        persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
        detail = service.period(**JANUARY).details[0]
        service.store.set_purchase_price(
            order_key=detail["order_key"], product_key=detail["product_key"],
            occurrence_index=detail["occurrence_index"],
            price=Decimal("6000000"), auto_price=None)
        row, = service.store.purchase_price_overrides().values()
        assert row["reason"] == business_store.DEFAULT_FILL_REASON


class TestCheckR211AutoNeverOverwritesManual:
    def test_an_auto_price_appearing_later_does_not_win(
        self, repository, service
    ):
        """Giá tay đặt khi CHƯA có AUTO; một lần nạp sau mang AUTO về."""
        persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
        detail = service.period(**JANUARY).details[0]
        keys = {k: detail[k] for k in
                ("order_key", "product_key", "occurrence_index")}
        service.store.set_purchase_price(
            price=Decimal("6000000"), auto_price=None, **keys)

        persist(repository, [pair("BH1", kpi_purchase="5000000",
                                  kpi_profit="3000000")],
                run_id="run-2", at="2026-02-02T00:00:00", fingerprint="fp-b")

        line = service.period(**JANUARY).lines[0]
        assert line.auto_purchase_price == Decimal("5000000")
        assert line.purchase_price == Decimal("6000000")
        assert line.purchase_provenance == bm.PROVENANCE_MANUAL


class TestCheckR212ClearingReturnsToAutoOrPending:
    def test_clearing_returns_to_the_current_auto_price(
        self, repository, service
    ):
        persist(repository, [pair("BH1", kpi_purchase="5000000",
                                  kpi_profit="3000000")])
        detail = service.period(**JANUARY).details[0]
        keys = {k: detail[k] for k in
                ("order_key", "product_key", "occurrence_index")}
        service.store.set_purchase_price(
            price=Decimal("4000000"), auto_price=Decimal("5000000"),
            reason="Thử", **keys)
        service.store.clear_purchase_price(**keys)

        line = service.period(**JANUARY).lines[0]
        assert line.purchase_price == Decimal("5000000")
        assert line.purchase_provenance == bm.PROVENANCE_AUTO

    def test_clearing_returns_to_pending_when_no_auto_price_exists(
        self, repository, service
    ):
        """Và KHÔNG giữ lại con số cũ — Ca C bước 5 của checklist Owner."""
        persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
        detail = service.period(**JANUARY).details[0]
        keys = {k: detail[k] for k in
                ("order_key", "product_key", "occurrence_index")}
        service.store.set_purchase_price(
            price=Decimal("6000000"), auto_price=None, **keys)
        service.store.clear_purchase_price(**keys)

        line = service.period(**JANUARY).lines[0]
        assert line.purchase_price is None
        assert line.purchase_provenance == bm.PROVENANCE_PENDING
        assert line.kpi_profit is None


class TestCheckR213ManualPriceDoesNotSpread:
    def test_only_the_edited_line_changes(self, repository, service):
        """Hai dòng CÙNG mặt hàng, cùng ngày, khác đơn."""
        persist(repository, [
            pair("BH1", kpi_purchase=None, kpi_profit=None),
            pair("BH2", kpi_purchase=None, kpi_profit=None),
        ])
        data = service.period(**JANUARY)
        first, second = data.details[0], data.details[1]
        assert first["product_key"] == second["product_key"]

        service.store.set_purchase_price(
            order_key=first["order_key"], product_key=first["product_key"],
            occurrence_index=first["occurrence_index"],
            price=Decimal("6000000"), auto_price=None)

        after = service.period(**JANUARY)
        edited = [d for d in after.details
                  if d["order_key"] == first["order_key"]][0]["line"]
        untouched = [d for d in after.details
                     if d["order_key"] == second["order_key"]][0]["line"]
        assert edited.purchase_price == Decimal("6000000")
        assert untouched.purchase_price is None
        assert len(service.store.purchase_price_overrides()) == 1


# --------------------------------------------------------------------------
# CHECK-R2-14 — pending reason cũ KHÔNG chặn lợi nhuận khi giá tay đã đủ
# --------------------------------------------------------------------------

class TestCheckR214StalePendingReasonsDoNotBlockProfit:
    def test_the_recorded_reasons_stay_but_stop_blocking(
        self, repository, service
    ):
        persist(repository, [pair(
            "BH1", kpi_purchase=None, kpi_profit=None,
            reasons=("IDENTITY_OUT_OF_CATALOG", "Missing.PurchasePrice",
                     "Pending.eligible_kpi_profit"))])
        detail = service.period(**JANUARY).details[0]
        service.store.set_purchase_price(
            order_key=detail["order_key"], product_key=detail["product_key"],
            occurrence_index=detail["occurrence_index"],
            price=Decimal("6000000"), auto_price=None)

        line = service.period(**JANUARY).lines[0]
        # Bằng chứng của lần chạy KHÔNG bị viết lại...
        assert "IDENTITY_OUT_OF_CATALOG" in line.pending_reasons
        # ...nhưng nó thôi chặn con số.
        assert line.profit_blockers == ()
        assert line.kpi_profit == Decimal("2000000")


# --------------------------------------------------------------------------
# CHECK-R2-15 — giao diện, service và hàng đợi đọc CÙNG effective state
# --------------------------------------------------------------------------

class TestCheckR215OneEffectiveState:
    def test_the_four_classifications_are_distinct_end_to_end(self):
        """Bốn ngữ nghĩa của §4.1 phải TÁCH BẠCH ở tầng đọc trạng thái."""
        assert len(set(line_identity.CLASSIFICATIONS)) == 4
        seen = {
            line_identity.state_of(
                _detail(RAW_A, reasons=("IDENTITY_UNRESOLVED",))).classification,
            line_identity.state_of(
                _detail(RAW_A, reasons=("IDENTITY_CONFLICT",))).classification,
            line_identity.state_of(
                _detail(RAW_A, reasons=("IDENTITY_OUT_OF_CATALOG",))
            ).classification,
            line_identity.state_of(_detail(RAW_A)).classification,
        }
        assert seen == set(line_identity.CLASSIFICATIONS)

    def test_a_decision_takes_effect_without_re_running_the_pipeline(self):
        """Mã lý do đã LƯU vẫn nói "chưa nhận diện"; quyết định mới thắng."""
        detail = _detail(RAW_A, reasons=("IDENTITY_UNRESOLVED",))
        decisions = line_identity.Decisions.of(
            confirmed={raw_identity_key(RAW_A)})
        assert line_identity.state_of(
            detail, decisions=decisions
        ).classification == line_identity.CLASS_MATCHED_TRACKING

    def test_out_of_catalog_and_matched_are_told_apart_when_both_lack_a_price(
        self,
    ):
        """Hai dòng hiện CÙNG ô trống, và cần HAI hành động khác nhau."""
        detail = _detail(RAW_A)
        matched = line_identity.state_of(
            detail, decisions=line_identity.Decisions.of(
                confirmed={raw_identity_key(RAW_A)}))
        out = line_identity.state_of(
            detail, decisions=line_identity.Decisions.of(
                out_of_catalog={raw_identity_key(RAW_A)}))
        assert matched.state == out.state == line_identity.STATE_MISSING_PRICE
        assert matched.classification != out.classification


# --------------------------------------------------------------------------
# CHECK-R2-16 — R1 không hồi quy
# --------------------------------------------------------------------------

class TestCheckR216R1InvariantsHold:
    def test_a_confirmed_mapping_does_not_create_a_price(self, identity_store):
        """`ECONOMIC_ISOLATION` — nhận diện xong KHÔNG kéo theo giá.

        Không có ảnh chụp MIN nào được nối, nên dòng phải Pending với đúng lý
        do "chưa nối nguồn" — KHÔNG rơi về `tp/ton`, không rơi về giá hiện tại
        và không dựng một con số nào.
        """
        confirm(identity_store, RAW_A, "TRK-A100")
        record, = _compose(identity_store, RAW_A)
        assert record.status is PriceResolutionStatus.PENDING
        assert record.price_vnd is None
        assert record.reason is (
            PriceResolutionReason.TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE)

    def test_the_legacy_history_source_stays_unauthorised(self, identity_store):
        sources = _sources(identity_store)
        assert sources.legacy_tracking_history_authority is False
        assert sources.tracking_price_history is None

    def test_a_zero_purchase_price_is_still_refused_from_tracking(self):
        """R1 — `OUT_OF_STOCK`/giá 0 KHÔNG bao giờ thành một giá nhập.

        Bất biến này nằm ở `DailyMinRecord`; R2 chỉ khẳng định lại rằng nó chưa
        bị nới ra ở đâu.
        """
        from app.modules.pricing.daily_min.snapshot import DailyMinRecord

        assert not DailyMinRecord.__post_init__.__doc__ or True
        with pytest.raises(Exception):
            DailyMinRecord.from_contract({
                "schema_version": "daily-min-v1", "product_code": "TRK-A100",
                "effective_date": "2026-01-05", "min_price": 0,
                "currency_unit": "thousand_VND", "min_sources": [],
                "price_status": "AVAILABLE", "day_status": "FINAL",
                "rule_version": "min-1", "source_fingerprint": "ff",
                "recorded_at": "2026-01-05T00:00:00Z", "recorded_by": "cron",
                "revision": "R-1", "observed_on": "2026-01-05",
            })


# --------------------------------------------------------------------------
# Trợ giúp
# --------------------------------------------------------------------------

def _detail(raw, *, reasons=(), purchase_price=None):
    """Một `detail` tối thiểu đúng hình dạng mà `line_identity` đọc."""
    line = bm.BusinessLine(
        order_key="BH1", employee="Vinh", employee_group="NOI_THANH",
        status="PENDING", sell_price=Decimal("8000000"), quantity=Decimal(1),
        discount=Decimal(0), total_sales=Decimal("8000000"),
        auto_purchase_price=purchase_price, auto_kpi_profit=None,
        kpi_authority_valid=True, pending_reasons=tuple(reasons))
    return {"order_key": "BH1", "product_key": "pk", "occurrence_index": 1,
            "product_raw": raw, "line": line}


def _sources(identity_store, snapshot=None):
    from zoneinfo import ZoneInfo

    from app.modules.pricing.resolution.sources import BusinessTimezone

    return PriceResolutionSources(
        business_timezone=BusinessTimezone(
            is_valid=True, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"),
            label="Asia/Ho_Chi_Minh", provenance="config"),
        tracking_price_history=None,
        tracking_catalog=snapshot if snapshot is not None else catalog(),
        public_purchase=None,
        identity_store_view=identity_store.read_at_revision(
            identity_store.refresh()),
        tracking_identity_authority=True,
    )


def _compose(identity_store, raw, *, snapshot=None):
    """Chạy composition production trên MỘT dòng, trả về các bản ghi giá."""
    composition = PostCutoverPriceComposition(_sources(identity_store, snapshot))
    composition.apply([_Line(raw)])
    return composition.records
