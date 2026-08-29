"""Import pipeline entrypoint: the first 9 steps of spec §22.

    1. Read `.xlsx`                         -> raw_reader.read_raw_rows
    2. Metadata preview before normalizing   -> preview.build_preview
    3. Normalize columns, deduct Chiết khấu  -> normalizer.normalize_lines
    4. Employee mapping                      -> mapping.EmployeeMapper
    5. Group by OrderID                      -> orders.build_orders
    6. LeadSource rule at order level        -> lead_source.LeadSourceClassifier
    7. Propagate LeadSourceFinal to lines    -> (done inside step 6's apply())
    8. Price lookup (Pending if no Price Master) -> pricing.price_engine
    9. AccountingProfit (Universal formula, no KPI Adjustment) -> profit.profit_engine
   9b. KpiPurchasePrice + EligibleKpiProfit, minimum B7/B8 slice
       (DEC-143 + DEC-144, Golden #1 KPI vertical slice) -> kpi.kpi_profit_engine
  10. ProductGroup + ConversionScheme, PER LINE -> conversion.conversion_engine
  11. Validation + Review Queue (spec section 18) -> validation.Validator

Step 11 never blocks: it reports, it does not gate. An import whose every row
is defective still returns a full `ImportResult` (spec section 18, DEC-128).

Out of scope here (later tasks): product/transaction classification
(TASK-103), full Converted Revenue aggregation / PERSONAL-ADS bucketing /
summary engine (TASK-108B remainder + TASK-109 — DEFERRED_BY_MINIMAL_FIX,
see `PROJECT/PROJECT_PROGRESS.md`), Adjustment persistence/writer UI
(TASK-202/302/305), Review Queue persistence (TASK-201), audit trail and real
overrides (TASK-202), the review screen (TASK-305), export (TASK-111),
CLI (TASK-112).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.modules.adjustment.confirmed_adjustment_source import (
    ConfirmedAdjustmentSource,
)
from app.modules.conversion.conversion_engine import apply_conversion_schemes
from app.modules.conversion.scheme_resolver import ConversionSchemeResolver
from app.modules.domain.models import (
    MAPPING_STATUS_MAPPED,
    PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT,
    PRICE_SOURCE_PENDING,
    Order,
    WorkingLine,
)
from app.modules.importing.normalizer import normalize_lines
from app.modules.importing.preview import ImportPreview, build_preview
from app.modules.importing.raw_reader import read_raw_rows
from app.modules.kpi.kpi_profit_engine import apply_kpi_profit
from app.modules.lead_source.classifier import LeadSourceClassifier
from app.modules.mapping.employee_mapper import EmployeeMapper
from app.modules.orders.order_builder import build_orders
from app.modules.pricing.price_engine import apply_prices
from app.modules.pricing.provider import PendingPriceProvider, PriceProvider
from app.modules.product.identity.identity import HistoricalConfirmed, PendingProduct
from app.modules.product.identity.registry import (
    CUTOVER_DATE,
    HistoricalConfirmedRegistry,
)
from app.modules.product.identity.resolver import SalesRowRef
from app.modules.product.identity.service import ResolverFactory, resolve_batch
from app.modules.product.product_group import (
    DefaultProductGroupProvider,
    ProductGroupProvider,
)
from app.modules.profit.profit_engine import apply_accounting_profit
from app.modules.validation.models import ReviewQueue
from app.modules.validation.validator import Validator

DEFAULT_CONFIG_DIR = Path("config")


def _post_cutover_resolver_not_wired():
    """`TASK-105E` (chủ sở hữu composition P01–P11 post-cutover) chưa được
    authorize/implement (`DEC-154` §11, S050 §13). Không có
    `TrackingCatalogSnapshot`/`PublicPurchaseSourceVersion`/`StoreView` thật
    nào được wiring vào `app.pipeline`, nên factory này KHÔNG được phép giả
    lập khả năng đó — nó nổ rõ ràng nếu thực sự bị gọi. Theo `INV-47`, điều
    này chỉ xảy ra khi một batch chứa ít nhất một dòng post-cutover
    (`sale_date >= CUTOVER_DATE`); mọi dữ liệu production/test hiện có đều
    pre-cutover nên nhánh này chưa từng được kích hoạt (S051 §6, §17)."""
    raise NotImplementedError(
        "Post-cutover product identity resolution (TASK-105E composition) "
        "chưa được wiring vào app.pipeline — không có dependency thật nào "
        "khả dụng trong production config để dựng ProductIdentityResolver."
    )


def _apply_pre_cutover_identity(
    lines: list[WorkingLine],
    *,
    registry: HistoricalConfirmedRegistry,
    resolver_factory: ResolverFactory,
) -> None:
    """Nối `app.pipeline` với biên `product/identity` của `TASK-105D`
    (S051) cho nhánh pre-cutover (`DEC-154` §2/P00): giá của một dòng
    `sale_date < CUTOVER_DATE` đến TỪ `HistoricalConfirmedRegistry` khi có
    entry `CONFIRMED`, hoặc là Pending khi không có — không bao giờ qua
    `PriceProvider` (P01–P11 chỉ áp cho nhánh post-cutover). Dòng nào không
    thuộc nhánh này (post-cutover hoặc thiếu `date`) không bị đụng tới ở đây
    — `apply_prices` hiện hành vẫn xử lý chúng như trước (S051 §17: đổi tối
    thiểu, không redesign `TASK-105D`).
    """
    pre_cutover = [
        line for line in lines if line.date is not None and line.date < CUTOVER_DATE
    ]
    if not pre_cutover:
        return

    rows = [
        SalesRowRef(
            order_id=line.order_id,
            sale_date=line.date,
            raw_product_identity=line.product_raw or "",
        )
        for line in pre_cutover
    ]
    result = resolve_batch(rows, registry=registry, resolver_factory=resolver_factory)

    for line, (_, outcome) in zip(pre_cutover, result.historical):
        if isinstance(outcome, HistoricalConfirmed):
            line.accounting_purchase_price = outcome.price
            # `outcome.provenance.price_provenance` — không hardcode hằng số
            # `HISTORICAL_CONFIRMED_REPORT`: registry entry đứng sau outcome
            # này có thể là `OWNER_MANUAL_LEGACY_CONFIRMATION` (Golden #1
            # session brief §2, LEGACY DATA GAP) và `price_source` phải nói
            # đúng loại bằng chứng thật, không được gắn nhãn "report" cho một
            # xác nhận không có report.
            line.price_source = (
                outcome.provenance.price_provenance
                or PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT
            )
        elif isinstance(outcome, PendingProduct):
            line.accounting_purchase_price = None
            line.price_source = PRICE_SOURCE_PENDING


@dataclass(frozen=True)
class WorkingData:
    """Everything steps 1–10 produce, before validation ever runs.

    Extracted so a test can hold the state as it exists at the moment BEFORE
    the Review Queue is built (Independent Review #2, Finding 4). Snapshotting
    the output of `run_import()` proved nothing about mutation: validation had
    already run once inside it, so the "before" picture was really an "after"
    one, and any mutation would have been baked into both sides.
    """

    preview: ImportPreview
    lines: list[WorkingLine]
    orders: list[Order]
    # CHÍNH instance đã resolve các dòng trên. Validation nhận nó để hỏi lại
    # "record nào" thay vì đoán lại bằng giá trị (DEC-132). Đây là một trường
    # của `WorkingData`, KHÔNG phải của `WorkingLine`/`Order` — hai lớp đó
    # nằm ngoài phạm vi TASK-110 và không đổi.
    employee_mapper: EmployeeMapper


@dataclass(frozen=True)
class ImportResult:
    preview: ImportPreview
    orders: list[Order]
    unmapped_lines: list[WorkingLine]
    review_queue: ReviewQueue


def build_working_data(
    raw_path: Path,
    config_dir: Path = DEFAULT_CONFIG_DIR,
    price_provider: PriceProvider | None = None,
    product_group_provider: ProductGroupProvider | None = None,
    identity_registry: HistoricalConfirmedRegistry | None = None,
    identity_resolver_factory: ResolverFactory | None = None,
    confirmed_adjustment_source: ConfirmedAdjustmentSource | None = None,
) -> WorkingData:
    """Steps 1–10 of spec section 22 — everything except the Review Queue."""
    raw_rows = read_raw_rows(raw_path)
    preview = build_preview(raw_rows)

    lines = normalize_lines(raw_rows)

    employee_mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    employee_mapper.apply(lines)

    orders = build_orders(lines)

    classifier = LeadSourceClassifier.from_yaml(config_dir / "lead_source.yaml")
    classifier.apply(orders, employee_mapper)

    # Bước 8 §22 (TASK-105, nối `TASK-105D` — S051). Pre-cutover đi qua biên
    # product identity (DEC-154 P00) trước; phần còn lại (post-cutover /
    # `date` thiếu — không xảy ra trong dữ liệu hiện có) vẫn qua
    # `PriceProvider` như cũ.
    _apply_pre_cutover_identity(
        lines,
        registry=identity_registry or HistoricalConfirmedRegistry(),
        resolver_factory=identity_resolver_factory or _post_cutover_resolver_not_wired,
    )
    remaining_lines = [
        line for line in lines if line.date is None or line.date >= CUTOVER_DATE
    ]
    apply_prices(remaining_lines, price_provider or PendingPriceProvider())

    apply_accounting_profit(lines)

    # Bước 9b (TASK-108B minimum B7/B8 slice, DEC-143 + DEC-144). Chạy ngay
    # sau AccountingPurchasePrice/AccountingProfit vì cùng cần
    # accounting_purchase_price đã resolve — nhưng KHÔNG phụ thuộc kết quả
    # accounting_profit (capability khác, DEC-126 điểm 1). `confirmed_adjustment_source
    # is None` mặc định (không truyền) nghĩa là chưa có nguồn nào được wiring
    # cho lời gọi này -> SOURCE_UNAVAILABLE -> Pending, không phải 0 blast
    # radius giả — hành vi mặc định của mọi `run_import()` hiện có không đổi.
    apply_kpi_profit(lines, confirmed_adjustment_source)

    resolver = ConversionSchemeResolver.from_yaml(
        config_dir / "conversion_rates.yaml"
    )
    apply_conversion_schemes(
        orders, resolver, product_group_provider or DefaultProductGroupProvider()
    )

    return WorkingData(
        preview=preview,
        lines=lines,
        orders=orders,
        employee_mapper=employee_mapper,
    )


def run_import(
    raw_path: Path,
    config_dir: Path = DEFAULT_CONFIG_DIR,
    price_provider: PriceProvider | None = None,
    product_group_provider: ProductGroupProvider | None = None,
    identity_registry: HistoricalConfirmedRegistry | None = None,
    identity_resolver_factory: ResolverFactory | None = None,
    confirmed_adjustment_source: ConfirmedAdjustmentSource | None = None,
) -> ImportResult:
    working = build_working_data(
        raw_path,
        config_dir,
        price_provider,
        product_group_provider,
        identity_registry,
        identity_resolver_factory,
        confirmed_adjustment_source,
    )

    # Step 11. Runs exactly once, last, and only reads: the Review Queue is a
    # report that travels beside the data, never a stage that edits it.
    # `build_queue_for` nhận nguyên bundle: các dòng và chính mapper đã enrich
    # chúng đi cùng nhau, nên không có hình dạng lời gọi nào ghép sai (DEC-133).
    review_queue = Validator.from_config_dir(
        config_dir, employee_mapper=working.employee_mapper
    ).build_queue_for(working)

    unmapped_lines = [
        line
        for line in working.lines
        if line.employee_mapping_status != MAPPING_STATUS_MAPPED
    ]

    return ImportResult(
        preview=working.preview,
        orders=working.orders,
        unmapped_lines=unmapped_lines,
        review_queue=review_queue,
    )
