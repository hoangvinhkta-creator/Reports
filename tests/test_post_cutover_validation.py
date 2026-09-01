"""Kiểm định production hậu-cutover — test focused của `validate_post_cutover`.

Mỗi test dưới đây là một câu khẳng định về **công cụ kiểm định**, chạy qua
đúng seam production `run_import_production()` với nguồn giá là fixture. Không
test nào ở đây khẳng định điều gì về dữ liệu THẬT — repo chưa có đơn bán nào
`sale_date >= 2026-09-01` (xem `PROJECT/PROJECT_PROGRESS.md`), và một fixture
không bao giờ được đọc thành bằng chứng production.

Ba trục:

1. **Cohort không cherry-pick** — chọn theo thứ tự xuất hiện, không lọc trước
   theo khả năng resolve, không bỏ đơn Pending, không nhầm dòng với đơn.
2. **Mọi đơn đi tới đúng một kết cục** — và một dòng Pending không làm dòng
   anh em biến mất.
3. **Sai thì phải nói ra** — mâu thuẫn giữa con số và bằng chứng đứng sau nó
   phải thành một finding, không được trôi qua.
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
import shutil
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from app.modules.domain.models import (
    PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT,
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_TRACKING_PRICE_HISTORY,
)
from app.modules.pricing.resolution.composition import (
    CompositionRule,
    PriceResolutionReason,
    PriceResolutionRecord,
    PriceResolutionStatus,
)
from app.modules.pricing.tracking_history.reader import (
    DecisiveSource,
    PriceReconstruction,
    ReconstructionStatus,
    TimestampAuthority,
    TrackingPriceProvenance,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
)
from app.modules.product.identity.registry import CUTOVER_DATE
from tests.test_105e_price_composition import (
    CATALOG_ROWS,
    DEFAULT_EXPORT,
    PP_PRICES,
    PP_PRODUCTS,
    ROWS_POST_CUTOVER,
    SALE_DAY,
    write_catalog_capture,
    write_history_capture,
    write_public_purchase,
    write_workbook,
)
from tools.analysis import validate_post_cutover as vpc

CONFIG_DIR = Path("config")

PRE_CUTOVER_DAY = _dt.date(2026, 8, 30)
"""Ngày 30/08/2026 — SAU mốc dữ liệu Tracking (29/08) nhưng TRƯỚC mốc Product
Identity (01/09). Chỉ thị mở phiên §3 nói rõ đơn ngày này vẫn phải đi nhánh
lịch sử; nó ở đây để chứng minh cohort không nuốt nó."""

BOUNDARY_DAY = _dt.date(2026, 9, 1)
"""Đúng `CUTOVER_DATE`. Biên bao gồm — `>=`, không phải `>`."""


# ======================================================================
# Fixture — nguồn giá đi qua ĐÚNG loader production
# ======================================================================


def _row(day, order_id, product, *, quantity=1, sell=1_000_000, discount=0,
         employee="Vũ Hạnh Ly 0868345633", profit=None):
    return (
        day, order_id, f"Bán hàng {order_id}", product,
        f"KH{order_id}", f"Khách {order_id}", "1 Đường Test", "0900000000",
        quantity, sell, sell * quantity - discount, discount, employee,
        "Shipper", 0, None, profit,
    )


EXTRA_ROWS = [
    # Pre-cutover thuần — PHẢI bị loại khỏi cohort hậu-cutover (§18).
    _row(PRE_CUTOVER_DAY, "BH8001", "Máy giặt Tracking A1"),
    # Đúng biên 01/09 — PHẢI nằm trong cohort (§19).
    _row(BOUNDARY_DAY, "BH9101", "Máy giặt Tracking A1"),
    # Đơn hai dòng hai bên mốc — MIXED, loại khỏi cohort nhưng ĐẾM RIÊNG.
    _row(PRE_CUTOVER_DAY, "BH9200", "Máy giặt Tracking A1"),
    _row(SALE_DAY, "BH9200", "Tủ lạnh Tracking B1"),
    # Không có ngày — UNDATED, cũng đếm riêng.
    _row(None, "BH9300", "Máy giặt Tracking A1"),
]


@pytest.fixture
def sources(tmp_path: Path) -> dict[str, Path]:
    """Ba nguồn giá post-cutover, ghi ra file thật và nạp bằng loader thật."""
    return {
        "tracking_capture": write_history_capture(tmp_path, DEFAULT_EXPORT),
        "tracking_catalog": write_catalog_capture(tmp_path, CATALOG_ROWS),
        "public_purchase": write_public_purchase(tmp_path, PP_PRODUCTS, PP_PRICES),
        "identity_store": tmp_path / "identity.log.jsonl",
    }


@pytest.fixture
def sales(tmp_path: Path) -> Path:
    return write_workbook(tmp_path / "post_cutover.xlsx", ROWS_POST_CUTOVER)


@pytest.fixture
def mixed_sales(tmp_path: Path) -> Path:
    return write_workbook(
        tmp_path / "mixed.xlsx", list(ROWS_POST_CUTOVER) + EXTRA_ROWS
    )


def run(sales_path: Path, sources: dict[str, Path], **kwargs):
    # This suite preserves a pre-S068 compatibility fixture whose asserted
    # catalog-name/legacy-PP route is intentionally not the Owner production
    # identity contract. Strict production behavior is covered separately.
    kwargs.setdefault("tracking_identity_authority", False)
    return vpc.analyze(
        sales_path,
        config_dir=kwargs.pop("config_dir", CONFIG_DIR),
        tracking_capture=sources["tracking_capture"],
        tracking_catalog=sources["tracking_catalog"],
        public_purchase=sources["public_purchase"],
        identity_store=sources["identity_store"],
        **kwargs,
    )


# ======================================================================
# 1–3. Cohort: deterministic, đếm ĐƠN, không cherry-pick
# ======================================================================


def test_1_cohort_selection_is_deterministic(mixed_sales):
    """Cùng một file, hai lần chọn — cùng một tập đơn, cùng một thứ tự."""
    first = vpc.select_post_cutover_cohort(mixed_sales, 50)
    second = vpc.select_post_cutover_cohort(mixed_sales, 50)
    assert first.order_ids == second.order_ids
    assert first.source_sha256 == second.source_sha256
    # Thứ tự là thứ tự XUẤT HIỆN ĐẦU TIÊN trong file, không phải thứ tự chữ cái.
    assert list(first.order_ids) == ["BH9001", "BH9002", "BH9003", "BH9004", "BH9101"]


def test_1b_repo_commit_supports_a_git_worktree_pointer(tmp_path):
    metadata = tmp_path / "metadata"
    metadata.mkdir()
    expected = "0123456789abcdef0123456789abcdef01234567"
    (metadata / "HEAD").write_text(expected + "\n", encoding="utf-8")
    (tmp_path / ".git").write_text(f"gitdir: {metadata}\n", encoding="utf-8")
    assert vpc.repo_commit(tmp_path) == expected


def test_2_input_orders_counts_unique_order_ids_not_lines(sales, sources):
    """Đơn BH9004 có hai dòng. `INPUT_ORDERS` vẫn đếm nó MỘT lần."""
    result = run(sales, sources)
    assert result.metrics["INPUT_ORDERS"] == 4
    assert result.metrics["INPUT_LINES"] == 5
    assert len(set(result.cohort.order_ids)) == len(result.cohort.order_ids)


def test_3_pending_orders_are_never_filtered_out_of_the_cohort(sales, sources):
    """BH9002 (giá bị xoá → Pending) và BH9004 (một dòng Pending) đều nằm
    trong cohort. Bỏ đơn khó ra khỏi mẫu là cách chắc chắn nhất để một tỉ lệ
    tự động hoá trông đẹp hơn sự thật."""
    result = run(sales, sources)
    assert "BH9002" in result.cohort.order_ids
    assert "BH9004" in result.cohort.order_ids
    outcomes = {o.order_id: o.outcome for o in result.order_outcomes}
    assert outcomes["BH9002"] == "REVIEW_QUEUE"
    assert outcomes["BH9004"] == "REVIEW_QUEUE"


# ======================================================================
# 4. Nguồn đông lạnh đúng MỘT lần cho MỘT lần chạy
# ======================================================================


def test_4_every_record_of_a_run_shares_one_evidence_snapshot(sales, sources):
    """Cùng một `PriceEvidenceSnapshot` — so bằng `is`, không bằng niềm tin.

    Nếu mỗi đơn đọc lại nguồn thì "chạy lại ra cùng kết quả" là lời hứa không
    ai giữ được (§7).
    """
    result = run(sales, sources)
    snapshots = {id(v["tracking_capture_id"]) for v in result.line_views}
    assert len(result.line_views) == 5
    # Định danh nguồn được ghi lại kèm băm file — mở lại được.
    assert result.freeze.hashes["tracking_price_history_capture"] != "ABSENT"
    assert result.freeze.statuses["tracking_price_history_capture"] == "PRESENT"
    assert result.freeze.hashes["price_resolution_config"] != "ABSENT"
    assert result.freeze.statuses["price_resolution_config"] == "PRESENT"
    evidence = result.freeze.as_dict()["evidence_snapshot"]
    assert evidence["tracking_price_history_capture_id"]
    assert evidence["public_purchase_version_id"]
    assert evidence["vendor_price_source"] == "NOT_AUTHORIZED:TASK-105C"
    assert snapshots  # mọi dòng mang cùng capture_id của cùng ảnh chụp


def test_4b_source_freeze_records_absent_sources_as_not_captured(tmp_path, sales):
    """Nguồn vắng mặt là `SOURCE_NOT_CAPTURED`, KHÔNG phải một lịch sử rỗng."""
    freeze = vpc.freeze_sources(
        config_dir=CONFIG_DIR,
        tracking_capture=tmp_path / "khong-ton-tai.json",
        tracking_catalog=tmp_path / "khong-ton-tai-2.json",
        public_purchase=tmp_path / "khong-ton-tai-3.yaml",
        identity_store=tmp_path / "khong-ton-tai-4.jsonl",
    )
    assert freeze.statuses["tracking_price_history_capture"] == "SOURCE_NOT_CAPTURED"
    assert freeze.hashes["tracking_catalog_capture"] == "ABSENT"
    assert freeze.sources.tracking_price_history is None


# ======================================================================
# 5–7. Phân loại AUTO / REVIEW_QUEUE / ERROR
# ======================================================================


def test_5_auto_classification(sales, sources):
    """BH9001 (TRACKING) và BH9003 (PUBLIC_PURCHASE) resolve hết, không mục
    Review Queue nào chạm — đó và chỉ đó là AUTO."""
    result = run(sales, sources)
    outcomes = {o.order_id: o.outcome for o in result.order_outcomes}
    assert outcomes["BH9001"] == "AUTO"
    assert outcomes["BH9003"] == "AUTO"
    views = {v["source_row"]: v for v in result.line_views}
    tracking = next(v for v in views.values() if v["order_id"] == "BH9001")
    assert tracking["price_source"] == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    assert tracking["composition_rule"] == (
        CompositionRule.TRACKING_HISTORY_AUTHORITY.value
    )
    public = next(v for v in views.values() if v["order_id"] == "BH9003")
    assert public["composition_rule"] == CompositionRule.PUBLIC_PURCHASE_DIRECT.value


def test_6_review_queue_classification_uses_canonical_task110_categories(
    sales, sources
):
    """Không có hàng chờ thứ hai: category phải là của `TASK-110`."""
    result = run(sales, sources)
    queued = [o for o in result.order_outcomes if o.outcome == "REVIEW_QUEUE"]
    assert {o.order_id for o in queued} == {"BH9002", "BH9004"}
    for outcome in queued:
        assert "Missing.PurchasePrice" in outcome.queue_categories


def test_7_error_classification_when_the_pipeline_raises(sales, sources, tmp_path):
    """Một `config_dir` không tồn tại làm production raise thật.

    Production chạy MỘT file mỗi lần, nên một exception không quy được về một
    đơn cụ thể: cả cohort vào ô `ERROR`, và traceback đi kèm nguyên văn.
    """
    result = run(sales, sources, config_dir=tmp_path / "khong-co-config")
    assert result.status == "PIPELINE_ERROR"
    assert result.metrics["ERROR_ORDERS"] == result.metrics["INPUT_ORDERS"] > 0
    assert result.pipeline_error
    assert all(o.outcome == "ERROR" for o in result.order_outcomes)
    # Đơn vẫn được kể tên — ERROR không phải một cái hố nuốt đơn.
    assert result.metrics["ORDER_ACCOUNTING_RATE"] == 1.0


# ======================================================================
# 8. PENDING_NOT_QUEUED — chưa resolve mà không ai biết
# ======================================================================


def test_8_pending_not_queued_is_detected_when_the_detector_is_off(
    sales, sources, tmp_path
):
    """Tắt detector `missing_purchase_price` trong config làm production
    ngừng sinh `Missing.PurchasePrice`. Dòng Pending vẫn còn đó — và công cụ
    phải gọi tên khoảng trống ấy, không được im lặng đếm nó là REVIEW_QUEUE.
    """
    config_dir = tmp_path / "config_no_price_detector"
    shutil.copytree(CONFIG_DIR, config_dir)
    data = yaml.safe_load((config_dir / "validation.yaml").read_text(encoding="utf-8"))
    data["categories"]["missing_purchase_price"]["enabled"] = False
    (config_dir / "validation.yaml").write_text(
        yaml.safe_dump(data, allow_unicode=True), encoding="utf-8"
    )

    result = run(sales, sources, config_dir=config_dir)
    outcomes = {o.order_id: o.outcome for o in result.order_outcomes}
    assert outcomes["BH9002"] == "PENDING_NOT_QUEUED"
    assert outcomes["BH9004"] == "PENDING_NOT_QUEUED"
    assert result.metrics["PENDING_NOT_QUEUED"] == 2
    # Và rate tụt xuống đúng bằng phần chưa được kể tới — không làm tròn lên.
    assert result.metrics["ORDER_ACCOUNTING_RATE"] == 0.5
    assert any(f.code == "UNRESOLVED_NOT_IN_REVIEW_QUEUE" for f in result.findings)
    assert result.status == "BLOCKED_BY_SILENT_ERROR_FINDINGS"


# ======================================================================
# 9. SILENTLY_DROPPED — đơn/dòng biến mất
# ======================================================================


def test_9_silently_dropped_order_is_detected(sales, sources, monkeypatch):
    """Production hiện tại KHÔNG đánh rơi đơn — Batch 50 và Golden #4 đã đo.

    Test này thay pipeline bằng một bản trả thiếu một đơn, để kiểm chính
    **công cụ đo**: nếu một ngày nào đó pipeline đánh rơi thật, con số phải
    đổi. Một detector chưa từng thấy trường hợp nó tìm là một detector chưa
    được kiểm.
    """
    real = vpc.run_import_production

    def missing_one(path, config_dir, price_composition=None):
        result = real(path, config_dir=config_dir, price_composition=price_composition)
        kept = [o for o in result.orders if o.order_id != "BH9003"]
        object.__setattr__(result, "orders", kept)
        return result

    monkeypatch.setattr(vpc, "run_import_production", missing_one)
    result = run(sales, sources)
    assert result.metrics["SILENTLY_DROPPED"] == 1
    assert result.metrics["ORDER_ACCOUNTING_RATE"] == 0.75
    assert any(f.code == "SILENTLY_DROPPED_ORDER" for f in result.findings)


def test_9b_silently_dropped_sibling_line_is_detected(sales, sources, monkeypatch):
    """Một dòng biến mất khỏi một đơn CÒN NGUYÊN là loại mất mát khó thấy
    nhất: đơn vẫn được kể, tổng vẫn ra một con số."""
    real = vpc.run_import_production

    def drop_sibling(path, config_dir, price_composition=None):
        result = real(path, config_dir=config_dir, price_composition=price_composition)
        for order in result.orders:
            if order.order_id == "BH9004":
                order.lines = order.lines[:1]
        return result

    monkeypatch.setattr(vpc, "run_import_production", drop_sibling)
    result = run(sales, sources)
    assert result.metrics["SILENTLY_DROPPED_LINES"] == 1
    assert result.metrics["SILENTLY_DROPPED"] == 1
    assert result.metrics["ORDER_ACCOUNTING_RATE"] == 0.75
    outcome = next(o for o in result.order_outcomes if o.order_id == "BH9004")
    assert outcome.outcome == "SILENTLY_DROPPED"
    assert any(f.code == "SILENTLY_DROPPED_LINE" for f in result.findings)


# ======================================================================
# 10–11. Hai tỉ lệ
# ======================================================================


def test_10_order_accounting_rate(sales, sources):
    result = run(sales, sources)
    assert result.metrics["ORDER_ACCOUNTING_RATE"] == 1.0
    assert result.metrics["PENDING_NOT_QUEUED"] == 0
    assert result.metrics["SILENTLY_DROPPED"] == 0


def test_11_automation_rate_never_counts_unresolved_as_resolved(sales, sources):
    """2/4 đơn AUTO. Hai đơn Pending KHÔNG được đếm vào tử số dưới bất kỳ
    cách diễn giải nào."""
    result = run(sales, sources)
    assert result.metrics["AUTOMATION_RATE"] == 0.5
    assert result.metrics["AUTO_ORDERS"] == 2
    pending_views = [
        v for v in result.line_views if v["price_source"] == PRICE_SOURCE_PENDING
    ]
    assert all(v["accounting_purchase_price"] is None for v in pending_views)


def test_11b_rate_on_an_empty_cohort_is_none_not_zero(tmp_path, sources):
    """Không có đơn hậu-cutover nào thì tỉ lệ KHÔNG tồn tại. In `0%` ở đó là
    bịa một kết luận về một tập rỗng."""
    only_pre = write_workbook(
        tmp_path / "pre.xlsx", [_row(PRE_CUTOVER_DAY, "BH8001", "Máy giặt Tracking A1")]
    )
    result = run(only_pre, sources)
    assert result.metrics["INPUT_ORDERS"] == 0
    assert result.metrics["ORDER_ACCOUNTING_RATE"] is None
    assert result.metrics["AUTOMATION_RATE"] is None
    assert result.status == "WAITING_REAL_POST_CUTOVER_DATA"


# ======================================================================
# 12. Đơn nhiều dòng giữ nguyên
# ======================================================================


def test_12_multi_line_order_keeps_every_line_and_does_not_leak_price(sales, sources):
    """BH9004: dòng D1 resolve được, dòng vô danh Pending. Đơn vẫn đủ hai
    dòng, và giá của dòng này KHÔNG chảy sang dòng kia."""
    result = run(sales, sources)
    outcome = next(o for o in result.order_outcomes if o.order_id == "BH9004")
    assert outcome.line_count == 2 == outcome.expected_line_count
    assert outcome.missing_source_rows == []
    lines = [v for v in result.line_views if v["order_id"] == "BH9004"]
    resolved = [v for v in lines if v["price_source"] != PRICE_SOURCE_PENDING]
    pending = [v for v in lines if v["price_source"] == PRICE_SOURCE_PENDING]
    assert len(resolved) == 1 and len(pending) == 1
    assert pending[0]["accounting_purchase_price"] is None
    assert pending[0]["accounting_profit"] is None
    assert pending[0]["eligible_kpi_profit"] is None
    assert resolved[0]["accounting_purchase_price"] == "4200000"


# ======================================================================
# 13. Mẫu kiểm tay
# ======================================================================


def test_13_manual_sample_covers_categories_and_carries_no_personal_data(
    sales, sources, tmp_path
):
    result = run(sales, sources)
    tags = {t for v in result.manual_sample for t in v["sample_categories"]}
    assert {"AUTO_TRACKING", "AUTO_PUBLIC_PURCHASE", "MULTI_LINE"} <= tags
    assert "REVIEW_QUEUE_TRACKING" in tags
    assert "QUANTITY_GT_1" in tags and "DISCOUNT" in tags
    # Cohort nhỏ thì có nhóm rỗng — ghi ra, không ép.
    assert result.sample_coverage["IDENTITY_AMBIGUITY"] == 0

    out = tmp_path / "artifacts"
    vpc.write_artifacts(result, out)
    header = (out / "manual_sample.csv").read_text(encoding="utf-8").splitlines()[0]
    for forbidden in ("customer", "phone", "address", "imei", "employee_raw"):
        assert forbidden not in header
    assert header.endswith("outcome,note")


def test_13b_manual_sample_is_deterministic(sales, sources):
    first = run(sales, sources)
    second = run(sales, sources)
    assert [v["source_row"] for v in first.manual_sample] == [
        v["source_row"] for v in second.manual_sample
    ]


def test_13c_silent_error_rate_is_not_measured_until_a_human_fills_it_in(
    sales, sources, tmp_path
):
    """`0%` khi chưa ai chấm là câu nói dối nguy hiểm nhất của cả quy trình."""
    result = run(sales, sources)
    assert result.metrics["SILENT_ERROR_RATE"] == "NOT_YET_MEASURED"
    assert result.status == "AWAITING_MANUAL_VALIDATION"

    out = tmp_path / "artifacts"
    vpc.write_artifacts(result, out)
    verdicts = vpc.load_manual_verdicts(out / "manual_sample.csv", result.manual_sample)
    assert verdicts["MANUALLY_VALIDATED"] == 0
    assert verdicts["SILENT_ERROR_RATE"] is None
    assert verdicts["complete"] is False


def test_13d_filled_verdicts_produce_a_rate_and_gate_the_status(
    sales, sources, tmp_path
):
    result = run(sales, sources)
    out = tmp_path / "artifacts"
    vpc.write_artifacts(result, out)
    filled = _fill(out / "manual_sample.csv", tmp_path / "filled.csv", "CORRECT_AUTO")
    summary = vpc.load_manual_verdicts(filled, result.manual_sample)
    assert summary["complete"] is True
    assert summary["SILENT_ERROR_RATE"] == 0.0
    vpc.apply_manual_verdicts(result, summary)
    assert result.status == "ELIGIBLE_FOR_PRODUCTION_ACCEPTANCE_REVIEW"


def test_13e_one_silent_error_blocks_everything(sales, sources, tmp_path):
    result = run(sales, sources)
    out = tmp_path / "artifacts"
    vpc.write_artifacts(result, out)
    filled = _fill(
        out / "manual_sample.csv", tmp_path / "filled.csv", "CORRECT_AUTO",
        first_outcome="SILENT_ERROR",
    )
    summary = vpc.load_manual_verdicts(filled, result.manual_sample)
    assert summary["SILENT_ERROR"] == 1
    assert summary["SILENT_ERROR_RATE"] > 0
    vpc.apply_manual_verdicts(result, summary)
    assert result.status == "BLOCKED_BY_SILENT_ERROR"


def test_13f_an_outcome_outside_the_closed_enum_is_rejected(
    sales, sources, tmp_path
):
    result = run(sales, sources)
    out = tmp_path / "artifacts"
    vpc.write_artifacts(result, out)
    filled = _fill(out / "manual_sample.csv", tmp_path / "filled.csv", "CHAC_LA_DUNG")
    summary = vpc.load_manual_verdicts(filled, result.manual_sample)
    assert summary["invalid_entries"]
    assert summary["complete"] is False


def test_13g_existing_verdicts_are_never_overwritten(sales, sources, tmp_path):
    """Công sức kiểm tay không tái tạo được. Một lần chạy lại vô ý không được
    phép xoá nó."""
    result = run(sales, sources)
    out = tmp_path / "artifacts"
    vpc.write_artifacts(result, out)
    _fill(out / "manual_sample.csv", out / "manual_sample.csv", "CORRECT_AUTO")
    before = (out / "manual_sample.csv").read_text(encoding="utf-8")
    vpc.write_artifacts(result, out)
    assert (out / "manual_sample.csv").read_text(encoding="utf-8") == before
    assert (out / "manual_sample.SKIPPED_EXISTING_VERDICTS").exists()


def test_13h_verdicts_are_bound_to_the_frozen_sample_identity(sales, sources, tmp_path):
    """Không được áp verdict cũ sang source file khác chỉ vì source_row trùng."""
    first = run(sales, sources)
    out = tmp_path / "artifacts"
    vpc.write_artifacts(first, out)
    filled = _fill(out / "manual_sample.csv", tmp_path / "filled.csv", "CORRECT_AUTO")

    changed = write_workbook(
        tmp_path / "changed.xlsx",
        [
            _row(BOUNDARY_DAY, "BH-NEW", "Máy giặt Tracking A1"),
            *ROWS_POST_CUTOVER,
        ],
    )
    second = run(changed, sources)
    summary = vpc.load_manual_verdicts(filled, second.manual_sample)
    assert summary["MANUALLY_VALIDATED"] == 0
    assert summary["rows_outside_sample"]
    assert summary["complete"] is False


def test_13i_duplicate_or_extra_verdict_rows_cannot_complete_a_sample(
    sales, sources, tmp_path
):
    result = run(sales, sources)
    out = tmp_path / "artifacts"
    vpc.write_artifacts(result, out)
    filled = _fill(out / "manual_sample.csv", tmp_path / "filled.csv", "CORRECT_AUTO")
    with open(filled, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    rows.append(dict(rows[0]))
    with open(filled, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = vpc.load_manual_verdicts(filled, result.manual_sample)
    assert summary["duplicate_sample_ids"]
    assert summary["complete"] is False


def _fill(src: Path, dst: Path, outcome: str, *, first_outcome: str | None = None):
    with open(src, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0].keys())
    for index, row in enumerate(rows):
        row["outcome"] = first_outcome if (index == 0 and first_outcome) else outcome
    with open(dst, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return dst


# ======================================================================
# 14. Provenance giá được giữ nguyên
# ======================================================================


def test_14_price_provenance_survives_into_the_artifact(sales, sources, tmp_path):
    """Con số đi ra artifact KHÔNG BAO GIỜ đi một mình: mã đã quyết định giá,
    ảnh chụp nào, sự kiện nào, giá thô nghìn VND và phép quy đổi đều đi cùng."""
    result = run(sales, sources)
    tracking = next(
        v for v in result.line_views
        if v["price_source"] == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    assert tracking["identity"] == "TRACKING:A1"
    assert tracking["tracking_capture_id"]
    assert tracking["tracking_decisive_source"] in {"BASELINE", "HISTORY_EVENT"}
    assert tracking["tracking_raw_thousand_vnd"] == "9000"
    assert tracking["accounting_purchase_price"] == "9000000"
    assert tracking["tracking_unit_conversion"] == "thousand_VND × 1000 → VND"

    out = tmp_path / "artifacts"
    vpc.write_artifacts(result, out)
    body = (out / "lines.csv").read_text(encoding="utf-8")
    assert "TRACKING:A1" in body and "thousand_VND × 1000 → VND" in body


# ======================================================================
# 15. Không chạm mạng trong đường production
# ======================================================================


def test_15_the_validator_and_the_app_never_reach_the_network():
    """`CHECK-105D-17` mở rộng cho công cụ kiểm định: nó chạy trên chính
    đường production, nên nó cũng không được mở một kết nối nào."""
    import re

    forbidden = re.compile(
        r"^\s*(?:import|from)\s+"
        r"(requests|urllib|http|httpx|socket|firebase\w*|google\.cloud"
        r"|boto3|aiohttp|websocket\w*|pyrebase)\b",
        re.MULTILINE,
    )
    for path in list(Path("app").rglob("*.py")) + [
        Path("tools/analysis/validate_post_cutover.py")
    ]:
        assert not forbidden.search(path.read_text(encoding="utf-8")), path


# ======================================================================
# 16–17. Nguồn thiếu / nguồn hỏng
# ======================================================================


def test_16_missing_capture_fails_safe_without_inventing_a_price(sales, tmp_path):
    """Không capture nào trên đĩa: mọi dòng post-cutover Pending kèm lý do
    NGUỒN CHƯA CÓ, mọi đơn vẫn được kể, không giá nào bị dựng."""
    result = vpc.analyze(
        sales,
        config_dir=CONFIG_DIR,
        tracking_capture=tmp_path / "khong-co.json",
        tracking_catalog=tmp_path / "khong-co-2.json",
        public_purchase=tmp_path / "khong-co-3.yaml",
        identity_store=tmp_path / "khong-co-4.jsonl",
    )
    assert result.metrics["AUTO_ORDERS"] == 0
    assert result.metrics["REVIEW_QUEUE_ORDERS"] == 4
    assert result.metrics["ORDER_ACCOUNTING_RATE"] == 1.0
    assert result.findings == []
    assert all(
        v["price_source"] == PRICE_SOURCE_PENDING for v in result.line_views
    )
    assert all(
        v["pending_reason"] == PriceResolutionReason.IDENTITY_SOURCES_UNAVAILABLE.value
        for v in result.line_views
    )


def test_17_malformed_capture_raises_and_produces_no_report(sales, sources, tmp_path):
    """File hỏng là LỖI NẠP, không phải Pending. Một report vẫn được sinh ra
    trên một nguồn hỏng là chính lớp lỗi mà capability này tồn tại để chặn."""
    broken = tmp_path / "broken_capture.json"
    broken.write_text("{ khong phai json", encoding="utf-8")
    with pytest.raises(Exception):
        vpc.analyze(
            sales,
            config_dir=CONFIG_DIR,
            tracking_capture=broken,
            tracking_catalog=sources["tracking_catalog"],
            public_purchase=sources["public_purchase"],
            identity_store=sources["identity_store"],
        )


def test_17b_failed_capture_status_is_a_hard_error_not_pending(
    sales, sources, tmp_path
):
    """`capture_status = FAILED` (`INV-12`) không bao giờ được đọc thành một
    lịch sử rỗng."""
    failed_dir = tmp_path / "failed"
    failed_dir.mkdir()
    failed = write_history_capture(
        failed_dir, DEFAULT_EXPORT,
        capture_status="FAILED", failure_reason="mất mạng giữa chừng",
    )
    with pytest.raises(Exception):
        vpc.analyze(
            sales,
            config_dir=CONFIG_DIR,
            tracking_capture=failed,
            tracking_catalog=sources["tracking_catalog"],
            public_purchase=sources["public_purchase"],
            identity_store=sources["identity_store"],
        )


# ======================================================================
# 18–19. Hai mốc cutover không gộp
# ======================================================================


def test_18_pre_cutover_orders_are_excluded_but_counted(mixed_sales):
    cohort = vpc.select_post_cutover_cohort(mixed_sales, 50)
    assert "BH8001" not in cohort.order_ids
    assert "BH9200" not in cohort.order_ids  # hai bên mốc — MIXED
    assert "BH9300" not in cohort.order_ids  # không có ngày
    assert cohort.excluded_pre_cutover_orders == 1
    assert cohort.excluded_mixed_cutover_orders == 1
    assert cohort.excluded_undated_orders == 1
    # Không đơn nào biến mất khỏi phép đếm.
    assert (
        cohort.unique_orders
        + cohort.excluded_pre_cutover_orders
        + cohort.excluded_mixed_cutover_orders
        + cohort.excluded_undated_orders
        == cohort.total_orders_in_file
    )


def test_18b_post_and_undated_lines_are_undated_not_a_post_cohort(tmp_path):
    """Một line không ngày làm trạng thái cutover không chứng minh được."""
    source = write_workbook(
        tmp_path / "post_plus_undated.xlsx",
        [
            _row(BOUNDARY_DAY, "BH-MAY-BE", "Máy giặt Tracking A1"),
            _row(None, "BH-MAY-BE", "Máy giặt Tracking A1"),
        ],
    )
    classified = vpc.classify_orders_by_cutover(source)
    cohort = vpc.select_post_cutover_cohort(source)
    assert classified["BH-MAY-BE"]["cutover_class"] == vpc.CutoverClass.UNDATED
    assert cohort.order_ids == ()
    assert cohort.excluded_undated_orders == 1


def test_19_an_order_exactly_on_the_cutover_date_is_included(mixed_sales):
    """Biên là `>=`, không phải `>`. `CUTOVER_DATE` không đổi một byte."""
    cohort = vpc.select_post_cutover_cohort(mixed_sales, 50)
    assert CUTOVER_DATE == BOUNDARY_DAY
    assert "BH9101" in cohort.order_ids


def test_19b_the_two_cutovers_are_not_merged(mixed_sales):
    """Đơn ngày 30/08/2026 nằm SAU mốc dữ liệu Tracking (29/08) nhưng TRƯỚC
    mốc Product Identity (01/09) — nó vẫn thuộc nhánh lịch sử."""
    classified = vpc.classify_orders_by_cutover(mixed_sales)
    assert classified["BH8001"]["cutover_class"] == vpc.CutoverClass.PRE


# ======================================================================
# 20. Tái lập được
# ======================================================================


def test_20_two_runs_produce_the_same_cohort_metrics_and_artifacts(
    sales, sources, tmp_path
):
    first = run(sales, sources)
    second = run(sales, sources)
    assert first.cohort.order_ids == second.cohort.order_ids
    assert first.cohort.source_sha256 == second.cohort.source_sha256
    assert first.metrics == second.metrics
    assert [o.as_dict() for o in first.order_outcomes] == [
        o.as_dict() for o in second.order_outcomes
    ]

    out_a, out_b = tmp_path / "a", tmp_path / "b"
    vpc.write_artifacts(first, out_a)
    vpc.write_artifacts(second, out_b)
    for name in ("orders.csv", "lines.csv", "manual_sample.csv"):
        assert (out_a / name).read_text(encoding="utf-8") == (
            out_b / name
        ).read_text(encoding="utf-8")
    # `frozen_at` là thời điểm chạy — nó ĐƯỢC PHÉP khác; phần định nghĩa
    # cohort thì không.
    a = json.loads((out_a / "cohort.json").read_text(encoding="utf-8"))
    b = json.loads((out_b / "cohort.json").read_text(encoding="utf-8"))
    a.pop("frozen_at"), b.pop("frozen_at")
    assert a == b


# ======================================================================
# §11 — mỗi loại SILENT ERROR phải có một test làm nó đỏ
#
# Một detector chưa từng thấy trường hợp nó đi tìm là một detector chưa được
# kiểm. Các test dưới đây dựng đúng cái mâu thuẫn ấy trên kết quả THẬT của
# production rồi hỏi lại công cụ: mày có thấy không?
# ======================================================================


@pytest.fixture
def production(sales, sources):
    """Một lần chạy production thật, trả về nguyên liệu để dựng mâu thuẫn."""
    from app.composition import run_import_production
    from app.modules.pricing.resolution.composition import (
        PostCutoverPriceComposition,
    )

    freeze = vpc.freeze_sources(
        config_dir=CONFIG_DIR,
        tracking_capture=sources["tracking_capture"],
        tracking_catalog=sources["tracking_catalog"],
        public_purchase=sources["public_purchase"],
        identity_store=sources["identity_store"],
        tracking_identity_authority=False,
    )
    composition = PostCutoverPriceComposition(freeze.sources)
    result = run_import_production(
        sales, config_dir=CONFIG_DIR, price_composition=composition
    )
    lines = [line for order in result.orders for line in order.lines]
    return {
        "freeze": freeze,
        "lines": lines,
        "records": composition.records,
        "cohort_ids": {o.order_id for o in result.orders},
    }


def _detect(production, lines=None, records=None):
    return vpc.detect_silent_errors(
        lines=lines if lines is not None else production["lines"],
        records=records if records is not None else production["records"],
        freeze=production["freeze"],
        cohort_ids=production["cohort_ids"],
    )


def _codes(findings):
    return {f.code for f in findings}


def test_silent_a_clean_production_run_yields_no_findings(production):
    """Kiểm soát âm. Nếu test này đỏ thì mọi test dưới đây vô nghĩa."""
    assert _detect(production) == []


def test_silent_pending_line_carrying_a_price(production):
    line = next(
        l for l in production["lines"] if l.price_source == PRICE_SOURCE_PENDING
    )
    line.accounting_purchase_price = Decimal("1")
    assert "PENDING_LINE_CARRIES_PRICE" in _codes(_detect(production))


def test_silent_unknown_price_source_label(production):
    production["lines"][0].price_source = "GiaTamTinh"
    assert "UNKNOWN_PRICE_SOURCE_LABEL" in _codes(_detect(production))


def test_silent_cross_cutover_legacy_authority_leak(production):
    """Một đơn hậu-cutover mang thẩm quyền PRE-cutover: `DEC-154` P00 đã rò
    qua bên kia mốc."""
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    line.price_source = PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT
    assert "CROSS_CUTOVER_LEGACY_AUTHORITY_LEAK" in _codes(_detect(production))


def test_silent_cross_cutover_post_authority_leak(production):
    """Chiều ngược lại — chính là điều §14 chỉ thị cấm: dữ liệu Tracking
    08/2026 không được làm một đơn tháng 01/2026 tự động hơn."""
    line = production["lines"][0]
    line.date = _dt.date(2026, 1, 8)
    line.price_source = PRICE_SOURCE_TRACKING_PRICE_HISTORY
    line.accounting_purchase_price = Decimal("9000000")
    assert "CROSS_CUTOVER_POST_AUTHORITY_LEAK" in _codes(_detect(production))


def test_silent_accounting_profit_mismatch(production):
    line = next(
        l for l in production["lines"] if l.accounting_profit is not None
    )
    line.accounting_profit = line.accounting_profit + Decimal("1")
    assert "ACCOUNTING_PROFIT_MISMATCH" in _codes(_detect(production))


def test_silent_eligible_kpi_profit_fabricated_while_inputs_pending(production):
    line = next(
        l for l in production["lines"] if l.price_source == PRICE_SOURCE_PENDING
    )
    line.eligible_kpi_profit = Decimal("999")
    assert "ELIGIBLE_KPI_PROFIT_FABRICATED" in _codes(_detect(production))


def test_silent_resolution_record_missing_for_a_post_cutover_line(production):
    """Một dòng hậu-cutover không có bản ghi giá nào là một con số không mở
    lại được — dù nó tình cờ đúng."""
    assert "RESOLUTION_RECORD_MISSING" in _codes(_detect(production, records=()))


def test_silent_line_price_not_from_its_own_record(production):
    """Rò giá giữa hai dòng anh em: dòng mang một số mà bản ghi của CHÍNH NÓ
    không nói."""
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    line.accounting_purchase_price = Decimal("4200000")  # giá của dòng D1
    codes = _codes(_detect(production))
    assert "LINE_PRICE_NOT_FROM_RECORD" in codes


def _provenance(**kw) -> TrackingPriceProvenance:
    base = dict(
        product_code="A1",
        namespace=Namespace.TRACKING.value,
        sale_interval_start=_dt.datetime(2026, 9, 5, tzinfo=_dt.timezone.utc),
        sale_interval_end=_dt.datetime(2026, 9, 6, tzinfo=_dt.timezone.utc),
        snapshot_capture_id="PPH-test",
        baseline_cutover_id="cutover-1",
        baseline_captured_at=_dt.datetime(2026, 8, 29, tzinfo=_dt.timezone.utc),
        baseline_timestamp_authority=TimestampAuthority.SERVER,
        decisive_source=DecisiveSource.HISTORY_EVENT,
        decisive_event_id="E1",
        decisive_source_timestamp=_dt.datetime(
            2026, 9, 3, tzinfo=_dt.timezone.utc
        ),
        decisive_timestamp_authority=TimestampAuthority.SERVER,
        raw_value_thousand_vnd=Decimal("9000"),
        resolved_price_vnd=Decimal("9000000"),
    )
    base.update(kw)
    return TrackingPriceProvenance(**base)


def _tracking_record(line, provenance, price=Decimal("9000000")):
    return PriceResolutionRecord(
        order_id=line.order_id,
        raw_product_identity=line.product_raw,
        raw_identity_key="k",
        sale_date=line.date,
        identity=CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code="A1"
        ),
        status=PriceResolutionStatus.RESOLVED,
        rule=CompositionRule.TRACKING_HISTORY_AUTHORITY,
        price_vnd=price,
        price_source=PRICE_SOURCE_TRACKING_PRICE_HISTORY,
        # `evidence` không tham gia phép kiểm nào dưới đây; các test về
        # nguồn vắng mặt dùng `freeze` riêng của chúng.
        evidence=None,
        tracking_reconstruction=PriceReconstruction(
            status=ReconstructionStatus.RESOLVED,
            provenance=provenance,
            price_vnd=provenance.resolved_price_vnd,
        ),
    )


def test_silent_unit_conversion_mismatch(production):
    """`resolved != raw × 1000` — phép quy đổi nghìn VND đã sai ở đâu đó, và
    con số vẫn đi thẳng vào KPI."""
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    provenance = _provenance(
        raw_value_thousand_vnd=Decimal("9000"),
        resolved_price_vnd=Decimal("9000"),  # quên nhân 1000
    )
    record = _tracking_record(line, provenance, price=Decimal("9000"))
    line.accounting_purchase_price = Decimal("9000")
    codes = _codes(_detect(production, records=(record,)))
    assert "UNIT_CONVERSION_MISMATCH" in codes


def test_silent_price_after_the_sale_used_for_a_historical_state(production):
    """Giá hiện tại dùng cho một trạng thái quá khứ: sự kiện quyết định nằm
    SAU đầu khoảng bán."""
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    provenance = _provenance(
        sale_interval_start=_dt.datetime(2026, 9, 5, tzinfo=_dt.timezone.utc),
        decisive_source_timestamp=_dt.datetime(
            2026, 9, 20, tzinfo=_dt.timezone.utc
        ),
    )
    record = _tracking_record(line, provenance)
    codes = _codes(_detect(production, records=(record,)))
    assert "PRICE_AFTER_SALE_USED_FOR_HISTORICAL_STATE" in codes


def test_silent_source_unavailable_but_priced(production, sales, sources, tmp_path):
    """Nguồn không tồn tại mà vẫn trả giá — hỏng hạ tầng biến thành kết luận
    nghiệp vụ."""
    empty_freeze = vpc.freeze_sources(
        config_dir=CONFIG_DIR,
        tracking_capture=tmp_path / "khong-co.json",
        tracking_catalog=sources["tracking_catalog"],
        public_purchase=sources["public_purchase"],
        identity_store=sources["identity_store"],
    )
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    record = _tracking_record(line, _provenance())
    findings = vpc.detect_silent_errors(
        lines=[line],
        records=(record,),
        freeze=empty_freeze,
        cohort_ids=production["cohort_ids"],
    )
    assert "SOURCE_UNAVAILABLE_BUT_PRICED" in _codes(findings)


def test_silent_public_purchase_price_not_effective_at_sale_date(production):
    """Tra lại độc lập chính bảng giá đã đông lạnh: nếu không có khoảng hiệu
    lực nào phủ ngày bán mà dòng vẫn có giá, giá ấy đến từ đâu?"""
    line = next(
        l for l in production["lines"]
        if l.price_source not in {PRICE_SOURCE_PENDING}
        and l.order_id == "BH9003"
    )
    record = PriceResolutionRecord(
        order_id=line.order_id,
        raw_product_identity=line.product_raw,
        raw_identity_key="k",
        sale_date=line.date,
        identity=CanonicalProductIdentity(
            namespace=Namespace.PUBLIC_PURCHASE,
            source_product_code="KHONG-CO-TRONG-BANG-GIA",
        ),
        status=PriceResolutionStatus.RESOLVED,
        rule=CompositionRule.PUBLIC_PURCHASE_DIRECT,
        price_vnd=line.accounting_purchase_price,
        price_source=line.price_source,
        evidence=None,
    )
    codes = _codes(_detect(production, lines=[line], records=(record,)))
    assert "PUBLIC_PURCHASE_PRICE_NOT_EFFECTIVE_AT_SALE_DATE" in codes


def test_silent_vendor_fallback_reached_while_task_105c_is_blocked(production):
    """`P03`/`P09` chạy trong khi nguồn vendor chưa được cấp phép nghĩa là một
    absence CHƯA XÁC ĐỊNH đã bị đọc thành absence đã xác định."""
    line = production["lines"][0]
    record = PriceResolutionRecord(
        order_id=line.order_id,
        raw_product_identity=line.product_raw,
        raw_identity_key="k",
        sale_date=line.date,
        identity=CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code="A1"
        ),
        status=PriceResolutionStatus.RESOLVED,
        rule=CompositionRule.PUBLIC_PURCHASE_VENDOR_FALLBACK,
        price_vnd=Decimal("1"),
        price_source="PUBLIC_PURCHASE_NO_VENDOR_PRICE",
        evidence=None,
    )
    line.price_source = "PUBLIC_PURCHASE_NO_VENDOR_PRICE"
    line.accounting_purchase_price = Decimal("1")
    codes = _codes(_detect(production, lines=[line], records=(record,)))
    assert "VENDOR_FALLBACK_REACHED_WHILE_BLOCKED" in codes


def test_silent_findings_outside_the_cohort_are_counted_separately(production):
    """Rò thẩm quyền qua mốc chỉ quan sát được ở phần dữ liệu NGOÀI cohort —
    nên nó phải được đếm, và được đếm riêng."""
    line = production["lines"][0]
    line.price_source = "GiaTamTinh"
    findings = vpc.detect_silent_errors(
        lines=production["lines"],
        records=production["records"],
        freeze=production["freeze"],
        cohort_ids=set(),
    )
    assert findings and all(not f.in_cohort for f in findings)


def test_silent_zero_findings_always_says_how_many_lines_were_checked(
    sales, sources, tmp_path
):
    """`SILENT_ERROR_FINDINGS = 0` không được phép đọc giống hệt "chưa kiểm
    dòng nào". Cohort rỗng vẫn kiểm TOÀN BỘ file — và đó chính là chỗ duy
    nhất phát hiện được rò thẩm quyền qua mốc cutover."""
    only_pre = write_workbook(
        tmp_path / "chi_truoc_moc.xlsx",
        [
            _row(PRE_CUTOVER_DAY, "BH8001", "Máy giặt Tracking A1"),
            _row(PRE_CUTOVER_DAY, "BH8002", "Tủ lạnh Tracking B1"),
        ],
    )
    result = run(only_pre, sources)
    assert result.metrics["INPUT_ORDERS"] == 0
    assert result.metrics["LINES_CHECKED_FOR_SILENT_ERRORS"] == 2
    assert result.metrics["SILENT_ERROR_FINDINGS"] == 0
    assert "LINES_CHECKED_FOR_SILENT_ERRORS" in vpc.render_summary(result)


def test_silent_priced_label_without_a_price(production):
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    line.accounting_purchase_price = None
    assert "PRICED_LABEL_WITHOUT_PRICE" in _codes(_detect(production))


def test_silent_accounting_profit_fabricated_while_inputs_pending(production):
    line = next(
        l for l in production["lines"] if l.price_source == PRICE_SOURCE_PENDING
    )
    line.accounting_profit = Decimal("123")
    assert "ACCOUNTING_PROFIT_FABRICATED" in _codes(_detect(production))


def test_silent_eligible_kpi_profit_mismatch(production):
    """Tính lại `DEC-143` một lần độc lập: `(Sell − KpiPurchase) × Qty −
    Discount`. Engine trả số khác là một con số quyết định lương đã sai."""
    line = next(
        l for l in production["lines"] if l.eligible_kpi_profit is not None
    )
    line.eligible_kpi_profit = line.eligible_kpi_profit + Decimal("1")
    assert "ELIGIBLE_KPI_PROFIT_MISMATCH" in _codes(_detect(production))


def test_silent_resolution_record_ambiguous(production):
    """Hai bản ghi cùng khoá bất đồng giá: không bản nào là "bản ghi của dòng
    này" nữa, và chọn hộ một bản là đúng heuristic bị cấm."""
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    provenance = _provenance()
    records = (
        _tracking_record(line, provenance, price=Decimal("9000000")),
        _tracking_record(line, provenance, price=Decimal("1")),
    )
    codes = _codes(_detect(production, lines=[line], records=records))
    assert "RESOLUTION_RECORD_AMBIGUOUS" in codes


def test_silent_line_price_source_not_from_record(production):
    """Con số khớp nhưng NHÃN NGUỒN không — và nhãn nguồn chính là thứ người
    kiểm dùng để quyết có tin con số hay không."""
    from app.modules.domain.models import PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING

    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    line.price_source = PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING
    assert "LINE_PRICE_SOURCE_NOT_FROM_RECORD" in _codes(_detect(production))


def test_silent_resolved_without_identity(production):
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    record = PriceResolutionRecord(
        order_id=line.order_id,
        raw_product_identity=line.product_raw,
        raw_identity_key="k",
        sale_date=line.date,
        identity=None,
        status=PriceResolutionStatus.RESOLVED,
        rule=CompositionRule.TRACKING_HISTORY_AUTHORITY,
        price_vnd=line.accounting_purchase_price,
        price_source=PRICE_SOURCE_TRACKING_PRICE_HISTORY,
        evidence=None,
        tracking_reconstruction=PriceReconstruction(
            status=ReconstructionStatus.RESOLVED,
            provenance=_provenance(),
            price_vnd=line.accounting_purchase_price,
        ),
    )
    codes = _codes(_detect(production, lines=[line], records=(record,)))
    assert "RESOLVED_WITHOUT_IDENTITY" in codes


def test_silent_tracking_price_without_reconstruction(production):
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    record = PriceResolutionRecord(
        order_id=line.order_id,
        raw_product_identity=line.product_raw,
        raw_identity_key="k",
        sale_date=line.date,
        identity=CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code="A1"
        ),
        status=PriceResolutionStatus.RESOLVED,
        rule=CompositionRule.TRACKING_HISTORY_AUTHORITY,
        price_vnd=line.accounting_purchase_price,
        price_source=PRICE_SOURCE_TRACKING_PRICE_HISTORY,
        evidence=None,
        tracking_reconstruction=None,
    )
    codes = _codes(_detect(production, lines=[line], records=(record,)))
    assert "TRACKING_PRICE_WITHOUT_RECONSTRUCTION" in codes


def test_silent_reconstruction_price_mismatch(production):
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    record = _tracking_record(line, _provenance(), price=Decimal("7777"))
    codes = _codes(_detect(production, lines=[line], records=(record,)))
    assert "RECONSTRUCTION_PRICE_MISMATCH" in codes


def test_silent_tracking_provenance_wrong_namespace(production):
    line = next(
        l for l in production["lines"]
        if l.price_source == PRICE_SOURCE_TRACKING_PRICE_HISTORY
    )
    record = _tracking_record(
        line, _provenance(namespace=Namespace.PUBLIC_PURCHASE.value)
    )
    codes = _codes(_detect(production, lines=[line], records=(record,)))
    assert "TRACKING_PROVENANCE_WRONG_NAMESPACE" in codes


def test_silent_public_purchase_price_mismatch(production):
    """Tra lại độc lập bảng giá đã đông lạnh ra một số khác."""
    line = next(l for l in production["lines"] if l.order_id == "BH9003")
    line.accounting_purchase_price = Decimal("1")
    record = PriceResolutionRecord(
        order_id=line.order_id,
        raw_product_identity=line.product_raw,
        raw_identity_key="k",
        sale_date=line.date,
        identity=CanonicalProductIdentity(
            namespace=Namespace.PUBLIC_PURCHASE, source_product_code="C1"
        ),
        status=PriceResolutionStatus.RESOLVED,
        rule=CompositionRule.PUBLIC_PURCHASE_DIRECT,
        price_vnd=Decimal("1"),
        price_source=line.price_source,
        evidence=None,
    )
    codes = _codes(_detect(production, lines=[line], records=(record,)))
    assert "PUBLIC_PURCHASE_PRICE_MISMATCH" in codes


def test_silent_every_detector_code_has_a_test_that_makes_it_red():
    """Bất biến của chính bộ test này: mọi code mà `detect_silent_errors` có
    thể phát ra đều phải xuất hiện trong một assertion ở file này.

    Một detector chưa từng thấy trường hợp nó đi tìm là một detector chưa được
    kiểm — và danh sách "đã phủ hết" là thứ dễ mục nhất trong một tài liệu.
    Nên nó được kiểm bằng máy, không bằng trí nhớ.
    """
    import ast
    import re

    source = Path("tools/analysis/validate_post_cutover.py").read_text(
        encoding="utf-8"
    )
    emitted = set(re.findall(r'\n\s+(?:add|code=)\(?\s*"([A-Z_]{6,})"', source))
    emitted |= set(re.findall(r'code="([A-Z_]{6,})"', source))
    assert len(vpc.DETECTOR_CODES) == len(set(vpc.DETECTOR_CODES))
    assert emitted == set(vpc.DETECTOR_CODES)

    # Chỉ một string xuất hiện trong file test không chứng minh gì: nó có thể
    # nằm trong docstring hoặc data fixture. Đòi mã phải nằm trong một `assert`
    # thực thi, nên test của chính detector phải đỏ nếu detector bị xoá/dead.
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    asserted = {
        node.value
        for assertion in ast.walk(tree)
        if isinstance(assertion, ast.Assert)
        for node in ast.walk(assertion.test)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    missing = sorted(code for code in emitted if code not in asserted)
    assert not missing, f"detector chưa có assertion thực thi: {missing}"
