"""Kiểm định production hậu-cutover — Post-Cutover Production Validation V1.

Công cụ này KHÔNG phải một pipeline thứ hai. Nó chạy **đúng** seam production
`app.composition.run_import_production()` trên một cohort đơn bán thật, rồi
ĐỌC kết quả để trả lời một câu hỏi duy nhất:

    Production composition `TASK-105E` có xử lý đúng dữ liệu thật hậu
    cutover Product Identity (01/09/2026) không, và nếu sai thì cái sai đó
    có tự nói ra không?

Không có business rule nào được định nghĩa lại ở đây. Không có giá nào được
tính. Không có identity nào được resolve. Mọi con số đến từ pipeline thật;
công cụ chỉ so chúng với chính bằng chứng mà pipeline đã ghi bên cạnh.

## Ba lớp câu trả lời, không gộp

```text
1. ORDER ACCOUNTING   mọi đơn đầu vào có đi tới đúng một kết cục nào không
2. SILENT ERROR       có con số sai nào đi qua mà không bật tín hiệu không
3. MANUAL VALIDATION  con người xác nhận một mẫu — máy không tự chấm hộ
```

Lớp 3 không máy nào làm được. Công cụ sinh ra một **bảng mẫu** để người kiểm
điền, và chỉ tính `SILENT_ERROR_RATE` khi bảng ấy đã được điền thật
(`--manual-verdicts`). Không có bảng thì tỉ lệ đó là `NOT_YET_MEASURED`,
KHÔNG phải `0%` — "pipeline không crash" chưa bao giờ là "kết quả đúng".

## Đơn vị kiểm định là ĐƠN, không phải DÒNG

`INPUT_ORDERS` đếm `OrderID` DUY NHẤT. Một đơn 4 dòng mà 1 dòng Pending vẫn
là MỘT đơn, và ba dòng còn lại không được phép biến mất theo. Số dòng được đo
song song (`INPUT_LINES`, `SILENTLY_DROPPED_LINES`) chứ không thay thế số đơn.

## Vì sao công cụ này KHÔNG BAO GIỜ tự tuyên Production Acceptance

Nó không phân biệt được một file bán hàng thật với một fixture cùng hình
dạng. Trạng thái cao nhất nó được phép in ra là
`ELIGIBLE_FOR_PRODUCTION_ACCEPTANCE_REVIEW`. Quyết định
`PRODUCTION_POST_CUTOVER_ACCEPTED` là một quyết định governance, ghi ở
`PROJECT/PROJECT_PROGRESS.md`, và đòi bằng chứng về tính THẬT của dữ liệu mà
chỉ con người mới cấp được.

## Múi giờ

Không có tham số `--timezone`. Múi giờ nghiệp vụ là một authority nạp từ
`config/price_resolution.yaml` (`load_business_timezone`), và thêm một cờ CLI
ghi đè nó chỉ là chuyển chỗ giấu một hằng số — đúng thứ mà
`app/modules/pricing/resolution/sources.py` đã từ chối làm.

## Cách chạy

```text
python3 tools/analysis/validate_post_cutover.py \
    --sales <so_chi_tiet_ban_hang.xlsx> \
    --output <thư_mục_kết_quả>

# khi nguồn thật nằm ngoài đường dẫn canonical trong repo:
python3 tools/analysis/validate_post_cutover.py \
    --sales <file.xlsx> \
    --tracking-capture <capture.json> \
    --tracking-catalog <catalog.json> \
    --public-purchase <source_version.yaml> \
    --identity-store <mappings.jsonl> \
    --output <dir>

# sau khi người kiểm điền cột outcome của manual_sample.csv:
python3 tools/analysis/validate_post_cutover.py \
    --sales <file.xlsx> --output <dir> \
    --manual-verdicts <dir>/manual_sample.csv
```

Operator KHÔNG phải sửa code để chạy trên dữ liệu mới.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import sys
import traceback
from dataclasses import dataclass, field, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.composition import run_import_production  # noqa: E402
from app.modules.domain.models import (  # noqa: E402
    CONVERSION_UNRESOLVED,
    MAPPING_STATUS_MAPPED,
    PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT,
    PRICE_SOURCE_MANUAL,
    PRICE_SOURCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_PRICE_MASTER,
    PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING,
    PRICE_SOURCE_PUBLIC_PURCHASE_NO_VENDOR_PRICE,
    PRICE_SOURCE_TRACKING_PRICE_HISTORY,
    WorkingLine,
)
from app.modules.importing.raw_reader import read_raw_rows  # noqa: E402
from app.modules.pricing.file_price_provider import FilePriceProvider  # noqa: E402
from app.modules.pricing.resolution.composition import (  # noqa: E402
    CompositionRule,
    PostCutoverPriceComposition,
    PriceResolutionRecord,
)
from app.modules.pricing.resolution.sources import (  # noqa: E402
    IDENTITY_STORE_LOG_PATH,
    PUBLIC_PURCHASE_SOURCE_PATH,
    TRACKING_CATALOG_CAPTURE_PATH,
    TRACKING_PRICE_HISTORY_CAPTURE_PATH,
    PriceResolutionSources,
    load_price_resolution_sources,
)
from app.modules.pricing.tracking_history.reader import (  # noqa: E402
    THOUSAND_VND_TO_VND,
    DecisiveSource,
    UnresolvedReason,
)
from app.modules.product.identity.identity import Namespace  # noqa: E402
from app.modules.product.identity.registry import CUTOVER_DATE  # noqa: E402
from app.modules.validation.models import (  # noqa: E402
    CATEGORY_EMPLOYEE_MAPPING,
    CATEGORY_MISSING,
    CATEGORY_MISSING_PURCHASE_PRICE,
    ReviewItem,
)

__all__ = [
    "CohortDefinition",
    "CutoverClass",
    "DETECTOR_CODES",
    "MANUAL_OUTCOMES",
    "OrderOutcome",
    "SilentErrorFinding",
    "ValidationRun",
    "analyze",
    "classify_orders_by_cutover",
    "load_manual_verdicts",
    "main",
    "select_post_cutover_cohort",
    "write_artifacts",
]

DEFAULT_COHORT_SIZE = 50
DEFAULT_SAMPLE_SIZE = 12

# Tập nhãn `price_source` ĐÓNG mà production hiện tại được phép sinh ra. Một
# nhãn ngoài tập này là một nhánh chưa ai review — nó phải nổi lên như một
# finding, không được trôi qua thành "chắc là ổn".
KNOWN_PRICE_SOURCES = frozenset(
    {
        PRICE_SOURCE_PENDING,
        PRICE_SOURCE_PRICE_MASTER,
        PRICE_SOURCE_MANUAL,
        PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT,
        PRICE_SOURCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
        PRICE_SOURCE_TRACKING_PRICE_HISTORY,
        PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING,
        PRICE_SOURCE_PUBLIC_PURCHASE_NO_VENDOR_PRICE,
    }
)

# Thẩm quyền giá của nhánh PRE-cutover (`DEC-154` P00). Một dòng
# `sale_date >= CUTOVER_DATE` mang một trong hai nhãn này nghĩa là thẩm quyền
# lịch sử đã rò sang bên kia mốc.
LEGACY_PRICE_SOURCES = frozenset(
    {
        PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT,
        PRICE_SOURCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
    }
)

# Thẩm quyền giá của nhánh POST-cutover (`TASK-105E`, `P01–P11`). Một dòng
# `sale_date < CUTOVER_DATE` mang một trong ba nhãn này nghĩa là Batch 50
# (tháng 01/2026) đang được "tự động hoá" bằng dữ liệu Tracking tháng 08/2026
# — chính điều mục §14 của chỉ thị cấm.
POST_CUTOVER_PRICE_SOURCES = frozenset(
    {
        PRICE_SOURCE_TRACKING_PRICE_HISTORY,
        PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING,
        PRICE_SOURCE_PUBLIC_PURCHASE_NO_VENDOR_PRICE,
    }
)

MANUAL_OUTCOMES = ("CORRECT_AUTO", "CORRECT_PENDING", "SILENT_ERROR", "UNVERIFIABLE")
"""Bốn kết cục của một dòng đã kiểm tay (§10). Enum ĐÓNG: một giá trị lạ
trong bảng verdict là lỗi nhập liệu, không phải một loại kết cục mới."""

# Danh mục đóng của các mâu thuẫn cấu trúc mà V1 biết phát hiện. Registry này
# được test như một hợp đồng: detector mới phải khai báo ở đây, và mọi mã phải
# có assertion thực thi làm nó đỏ.
DETECTOR_CODES = (
    "ACCOUNTING_PROFIT_FABRICATED",
    "ACCOUNTING_PROFIT_MISMATCH",
    "CROSS_CUTOVER_LEGACY_AUTHORITY_LEAK",
    "CROSS_CUTOVER_POST_AUTHORITY_LEAK",
    "ELIGIBLE_KPI_PROFIT_FABRICATED",
    "ELIGIBLE_KPI_PROFIT_MISMATCH",
    "LINE_PRICE_NOT_FROM_RECORD",
    "LINE_PRICE_SOURCE_NOT_FROM_RECORD",
    "PENDING_LINE_CARRIES_PRICE",
    "PRICED_LABEL_WITHOUT_PRICE",
    "PRICE_AFTER_SALE_USED_FOR_HISTORICAL_STATE",
    "PUBLIC_PURCHASE_PRICE_MISMATCH",
    "PUBLIC_PURCHASE_PRICE_NOT_EFFECTIVE_AT_SALE_DATE",
    "RECONSTRUCTION_PRICE_MISMATCH",
    "RESOLUTION_RECORD_AMBIGUOUS",
    "RESOLUTION_RECORD_MISSING",
    "RESOLVED_WITHOUT_IDENTITY",
    "SILENTLY_DROPPED_LINE",
    "SILENTLY_DROPPED_ORDER",
    "SOURCE_UNAVAILABLE_BUT_PRICED",
    "TRACKING_PRICE_WITHOUT_RECONSTRUCTION",
    "TRACKING_PROVENANCE_WRONG_NAMESPACE",
    "UNIT_CONVERSION_MISMATCH",
    "UNKNOWN_PRICE_SOURCE_LABEL",
    "UNRESOLVED_NOT_IN_REVIEW_QUEUE",
    "VENDOR_FALLBACK_REACHED_WHILE_BLOCKED",
)


# ======================================================================
# 1. Phân loại cutover + đông lạnh cohort
# ======================================================================


class CutoverClass:
    """Một đơn nằm ở phía nào của mốc Product Identity 01/09/2026.

    `MIXED` tồn tại vì một `OrderID` có thể mang nhiều ngày (chính là thứ
    `OrderInconsistency` của `TASK-110` phát hiện). Một đơn như vậy KHÔNG
    được lặng lẽ đưa vào cohort hậu-cutover, cũng không được lặng lẽ bỏ đi —
    nó được đếm riêng và in ra.
    """

    POST = "POST_CUTOVER"
    PRE = "PRE_CUTOVER"
    MIXED = "MIXED_CUTOVER"
    UNDATED = "UNDATED"


def classify_orders_by_cutover(raw_path: Path) -> dict[str, dict[str, Any]]:
    """Đọc file thô MỘT LẦN và trả về, theo thứ tự xuất hiện đầu tiên,
    `order_id -> {cutover_class, source_rows, dates, first_seen_row}`.

    Đây là phép đọc DUY NHẤT quyết định cohort. Nó không gọi pipeline, không
    hỏi giá, không biết đơn nào "dễ" — nên nó không thể cherry-pick.
    """
    orders: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(read_raw_rows(raw_path)):
        entry = orders.get(row.order_id)
        if entry is None:
            entry = {
                "order_id": row.order_id,
                "first_seen_row": row.source_row,
                "first_seen_index": index,
                "source_rows": [],
                "dates": [],
                "undated_source_rows": [],
            }
            orders[row.order_id] = entry
        entry["source_rows"].append(row.source_row)
        if row.date is not None:
            entry["dates"].append(row.date)
        else:
            entry["undated_source_rows"].append(row.source_row)

    for entry in orders.values():
        dates = entry["dates"]
        # Một dòng không ngày không thể chứng minh đơn "hoàn toàn hậu
        # cutover". Ưu tiên UNDATED cả khi các dòng khác sau mốc để một đơn
        # vừa post vừa undated chỉ có đúng một lớp và không lọt cohort bằng
        # suy đoán thuận lợi.
        if entry["undated_source_rows"]:
            entry["cutover_class"] = CutoverClass.UNDATED
        elif all(d >= CUTOVER_DATE for d in dates):
            entry["cutover_class"] = CutoverClass.POST
        elif all(d < CUTOVER_DATE for d in dates):
            entry["cutover_class"] = CutoverClass.PRE
        else:
            entry["cutover_class"] = CutoverClass.MIXED
    return orders


@dataclass(frozen=True)
class CohortDefinition:
    """Định nghĩa cohort đông lạnh — đủ để chạy lại và ra đúng tập đơn ấy."""

    source_file: str
    source_sha256: str
    requested_size: int
    order_ids: tuple[str, ...]
    raw_line_count: int
    sale_date_min: Optional[_dt.date]
    sale_date_max: Optional[_dt.date]
    frozen_at: str
    reports_commit: Optional[str]
    excluded_pre_cutover_orders: int
    excluded_mixed_cutover_orders: int
    excluded_undated_orders: int
    total_orders_in_file: int

    @property
    def unique_orders(self) -> int:
        return len(self.order_ids)

    @property
    def first_order_id(self) -> Optional[str]:
        return self.order_ids[0] if self.order_ids else None

    @property
    def last_order_id(self) -> Optional[str]:
        return self.order_ids[-1] if self.order_ids else None

    @property
    def sample_not_yet_50(self) -> bool:
        """`SAMPLE_NOT_YET_50` (§6) — cohort nhỏ hơn mức V1 yêu cầu.

        Không phải một lỗi. Là một sự thật phải in ra cạnh mọi con số, để
        không ai đọc `AUTOMATION_RATE` của 3 đơn như của 50 đơn.
        """
        return len(self.order_ids) < DEFAULT_COHORT_SIZE

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "source_sha256": self.source_sha256,
            "requested_size": self.requested_size,
            "unique_orders": self.unique_orders,
            "raw_line_count": self.raw_line_count,
            "first_order_id": self.first_order_id,
            "last_order_id": self.last_order_id,
            "order_ids": list(self.order_ids),
            "sale_date_min": _iso(self.sale_date_min),
            "sale_date_max": _iso(self.sale_date_max),
            "frozen_at": self.frozen_at,
            "reports_commit": self.reports_commit,
            "cutover_date": CUTOVER_DATE.isoformat(),
            "total_orders_in_file": self.total_orders_in_file,
            "excluded_pre_cutover_orders": self.excluded_pre_cutover_orders,
            "excluded_mixed_cutover_orders": self.excluded_mixed_cutover_orders,
            "excluded_undated_orders": self.excluded_undated_orders,
            "SAMPLE_NOT_YET_50": self.sample_not_yet_50,
        }


def select_post_cutover_cohort(
    raw_path: Path, size: int = DEFAULT_COHORT_SIZE
) -> CohortDefinition:
    """N `OrderID` DUY NHẤT ĐẦU TIÊN theo thứ tự xuất hiện, trong số các đơn
    hoàn toàn hậu-cutover.

    Không lọc trước theo khả năng resolve, không bỏ đơn Pending, không sắp xếp
    lại theo bất kỳ tiêu chí "dễ" nào — thứ tự duy nhất được dùng là thứ tự
    dòng trong chính file nguồn.
    """
    classified = classify_orders_by_cutover(raw_path)
    post = [e for e in classified.values() if e["cutover_class"] == CutoverClass.POST]
    post.sort(key=lambda e: e["first_seen_index"])
    chosen = post[:size]

    dates = [d for e in chosen for d in e["dates"]]
    counts = {
        CutoverClass.PRE: 0,
        CutoverClass.MIXED: 0,
        CutoverClass.UNDATED: 0,
    }
    for entry in classified.values():
        if entry["cutover_class"] in counts:
            counts[entry["cutover_class"]] += 1

    return CohortDefinition(
        source_file=str(raw_path),
        source_sha256=sha256_of(raw_path),
        requested_size=size,
        order_ids=tuple(e["order_id"] for e in chosen),
        raw_line_count=sum(len(e["source_rows"]) for e in chosen),
        sale_date_min=min(dates) if dates else None,
        sale_date_max=max(dates) if dates else None,
        frozen_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        reports_commit=repo_commit(),
        excluded_pre_cutover_orders=counts[CutoverClass.PRE],
        excluded_mixed_cutover_orders=counts[CutoverClass.MIXED],
        excluded_undated_orders=counts[CutoverClass.UNDATED],
        total_orders_in_file=len(classified),
    )


# ======================================================================
# 2. Tiện ích provenance — băm nguồn, commit repo
# ======================================================================


def sha256_of(path: Path) -> str:
    """Băm nội dung file nguồn. Đây là thứ khiến "chạy lại trên cùng đầu vào"
    là một câu kiểm được, không phải một lời hứa."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 16), b""):
                digest.update(chunk)
    except OSError:
        return "UNREADABLE"
    return digest.hexdigest()


def repo_commit(repo_root: Path = REPO_ROOT) -> Optional[str]:
    """Commit Reports đang chạy, đọc thẳng từ metadata Git, không subprocess.

    Git worktree dùng file `.git` chứa `gitdir: ...`, còn checkout thường dùng
    thư mục `.git/`. Cả hai phải trả cùng SHA; `None` khi không xác định được
    tốt hơn bịa version evidence.
    """
    git_dir = repo_root / ".git"
    if git_dir.is_file():
        try:
            pointer = git_dir.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        if not pointer.startswith("gitdir:"):
            return None
        location = pointer[len("gitdir:"):].strip()
        if not location:
            return None
        candidate = Path(location)
        git_dir = candidate if candidate.is_absolute() else repo_root / candidate
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not head.startswith("ref:"):
        return head or None
    ref = head[4:].strip()
    try:
        return (git_dir / ref).read_text(encoding="utf-8").strip() or None
    except OSError:
        pass
    try:
        for line in (git_dir / "packed-refs").read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) == 2 and parts[1] == ref:
                return parts[0]
    except OSError:
        return None
    return None


def _iso(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    return str(value)


def _num(value: Optional[Decimal]) -> Optional[str]:
    """Số tiền ra artifact dưới dạng CHUỖI thập phân chính xác. `float` làm
    tròn được một con số quyết định lương người thật — không dùng."""
    return None if value is None else str(value)


def _rate(numerator: int, denominator: int) -> Optional[float]:
    """`None` khi mẫu số bằng 0. Một tỉ lệ trên tập rỗng không phải `0%` —
    nó không tồn tại, và in `0%` ở đó là bịa một kết luận."""
    if denominator == 0:
        return None
    return numerator / denominator


def _pct(rate: Optional[float]) -> str:
    return "N/A" if rate is None else f"{rate:.1%}"


# ======================================================================
# 3. Đông lạnh nguồn — đúng một lần cho một lần chạy
# ======================================================================


@dataclass(frozen=True)
class SourceFreeze:
    """Bộ nguồn đã đông lạnh của MỘT lần chạy, kèm định danh để mở lại.

    `PriceResolutionSources` đã tự bảo đảm "đọc đúng một lần" (`TASK-105E`
    §15); lớp này chỉ ghi lại ĐƯỜNG DẪN + BĂM của từng file, thứ mà bản thân
    snapshot không mang, để một lần chạy sau chứng minh được nó dùng đúng bộ
    bằng chứng ấy.
    """

    sources: PriceResolutionSources
    paths: dict[str, str]
    hashes: dict[str, str]
    statuses: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        evidence = self.sources.evidence_snapshot
        return {
            "paths": self.paths,
            "sha256": self.hashes,
            "status": self.statuses,
            "evidence_snapshot": {
                "tracking_price_history_capture_id": (
                    evidence.tracking_price_history_capture_id
                ),
                "tracking_price_history_captured_at": _iso(
                    evidence.tracking_price_history_captured_at
                ),
                "tracking_catalog_capture_id": evidence.tracking_catalog_capture_id,
                "public_purchase_version_id": evidence.public_purchase_version_id,
                "public_purchase_content_hash": evidence.public_purchase_content_hash,
                "identity_store_revision": evidence.identity_store_revision,
                "business_timezone_label": evidence.business_timezone_label,
                "business_timezone_provenance": (
                    evidence.business_timezone_provenance
                ),
                "vendor_price_source": evidence.vendor_price_source,
            },
        }


def freeze_sources(
    *,
    config_dir: Path,
    tracking_capture: Path,
    tracking_catalog: Path,
    public_purchase: Path,
    identity_store: Path,
    tracking_identity_authority: bool = True,
) -> SourceFreeze:
    """Nạp mọi nguồn giá QUA ĐÚNG loader production, đúng một lần.

    `SOURCE_NOT_CAPTURED` là một trạng thái ĐƯỢC GHI RA, không phải một
    lịch sử rỗng (§8). File hỏng thì loader production raise và lần chạy
    dừng — công cụ này KHÔNG bắt lấy để sinh một report giả.
    """
    paths = {
        "config_dir": str(config_dir),
        "price_resolution_config": str(config_dir / "price_resolution.yaml"),
        "tracking_price_history_capture": str(tracking_capture),
        "tracking_catalog_capture": str(tracking_catalog),
        "public_purchase_source": str(public_purchase),
        "identity_store_log": str(identity_store),
    }
    statuses = {
        key: ("PRESENT" if Path(value).exists() else "SOURCE_NOT_CAPTURED")
        for key, value in paths.items()
        if key != "config_dir"
    }
    statuses["config_dir"] = "PRESENT" if config_dir.is_dir() else "SOURCE_NOT_CAPTURED"
    hashes = {
        key: (sha256_of(Path(value)) if Path(value).is_file() else "ABSENT")
        for key, value in paths.items()
        if key != "config_dir"
    }
    sources = load_price_resolution_sources(
        config_dir=config_dir,
        tracking_price_history_path=tracking_capture,
        tracking_catalog_path=tracking_catalog,
        public_purchase_path=public_purchase,
        identity_store_log_path=identity_store,
    )
    if not tracking_identity_authority:
        # Chỉ dành cho regression fixture dựng trước S068. Owner workflow và
        # production loader giữ strict Tracking alias.map + board authority.
        sources = replace(sources, tracking_identity_authority=False)
    return SourceFreeze(
        sources=sources, paths=paths, hashes=hashes, statuses=statuses
    )


# ======================================================================
# 4. Order accounting — Review Queue phủ tới đâu, thiếu ở đâu
# ======================================================================

# Chiều "chưa resolve" của một dòng, và category Review Queue canonical
# (`TASK-110`) PHẢI phủ nó. Bảng này là chỗ DUY NHẤT khai báo quan hệ ấy —
# một chiều không có category tương ứng là `None`, nghĩa là hôm nay chưa có
# detector nào, và điều đó phải hiện ra chứ không được coi như đã phủ.
UNRESOLVED_DIMENSIONS: tuple[tuple[str, Optional[str]], ...] = (
    ("Missing.PurchasePrice", CATEGORY_MISSING_PURCHASE_PRICE),
    ("Missing.date", CATEGORY_MISSING),
    ("Missing.quantity", CATEGORY_MISSING),
    ("Missing.total_sales", CATEGORY_MISSING),
    ("Missing.employee", CATEGORY_EMPLOYEE_MAPPING),
    ("ConversionScheme.Unresolved", None),
)


def line_unresolved_dimensions(line: WorkingLine) -> list[str]:
    """Những chiều dòng này còn chưa resolve, gọi tên theo đúng hằng số của
    `app/modules/domain/models.py` — không dựng một taxonomy song song."""
    dims: list[str] = []
    if line.price_source == PRICE_SOURCE_PENDING:
        dims.append("Missing.PurchasePrice")
    if line.date is None:
        dims.append("Missing.date")
    if line.quantity is None:
        dims.append("Missing.quantity")
    if line.total_sales is None:
        dims.append("Missing.total_sales")
    if line.employee_mapping_status != MAPPING_STATUS_MAPPED:
        dims.append("Missing.employee")
    if line.conversion_scheme_final == CONVERSION_UNRESOLVED:
        dims.append("ConversionScheme.Unresolved")
    return dims


@dataclass(frozen=True)
class QueueCoverage:
    """Review Queue phủ những dòng nào, theo từng category.

    `by_category_rows` là tập `source_row` mà một category thực sự trỏ tới;
    `by_category_orders` là các `OrderID` mà một item cấp đơn gọi tên. Hai
    kênh tách biệt vì `DEC-128` §1 nén `Missing.PurchasePrice` thành một item
    cấp lô — nó phủ theo DÒNG, không theo tên đơn.
    """

    by_category_rows: dict[str, set[int]]
    by_category_orders: dict[str, set[str]]
    rows_touched: set[int]
    orders_touched: set[str]

    def covers(self, category: Optional[str], source_row: int, order_id: str) -> bool:
        if category is None:
            return False
        if source_row in self.by_category_rows.get(category, set()):
            return True
        return order_id in self.by_category_orders.get(category, set())


def build_queue_coverage(items: Iterable[ReviewItem]) -> QueueCoverage:
    by_rows: dict[str, set[int]] = {}
    by_orders: dict[str, set[str]] = {}
    rows_touched: set[int] = set()
    orders_touched: set[str] = set()
    for item in items:
        rows = set(item.provenance.source_rows)
        by_rows.setdefault(item.category, set()).update(rows)
        rows_touched.update(rows)
        if item.order_id:
            by_orders.setdefault(item.category, set()).add(item.order_id)
            orders_touched.add(item.order_id)
    return QueueCoverage(
        by_category_rows=by_rows,
        by_category_orders=by_orders,
        rows_touched=rows_touched,
        orders_touched=orders_touched,
    )


@dataclass
class OrderOutcome:
    """Kết cục của MỘT đơn trong cohort — đúng một nhãn, không chồng lấn."""

    order_id: str
    outcome: str
    line_count: int
    expected_line_count: int
    source_rows: list[int]
    missing_source_rows: list[int]
    queue_categories: list[str]
    unresolved_dimensions: list[str]
    uncovered_dimensions: list[str]
    sale_dates: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "outcome": self.outcome,
            "line_count": self.line_count,
            "expected_line_count": self.expected_line_count,
            "source_rows": self.source_rows,
            "missing_source_rows": self.missing_source_rows,
            "queue_categories": self.queue_categories,
            "unresolved_dimensions": self.unresolved_dimensions,
            "uncovered_dimensions": self.uncovered_dimensions,
            "sale_dates": self.sale_dates,
        }


# ======================================================================
# 5. Phát hiện SILENT ERROR bằng cấu trúc
# ======================================================================


@dataclass(frozen=True)
class SilentErrorFinding:
    """Một MÂU THUẪN kiểm được giữa con số đã đi ra và bằng chứng đứng sau nó.

    Đây không phải "nghi ngờ": mỗi finding dưới đây là hai phát biểu của
    chính hệ thống không đứng cùng nhau được. Một finding = một blocker. Danh
    sách rỗng KHÔNG chứng minh không có silent error — nó chỉ nói không có
    loại nào MÁY phát hiện được; đó là lý do §10 vẫn đòi kiểm tay một mẫu.
    """

    code: str
    order_id: str
    source_row: Optional[int]
    in_cohort: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "order_id": self.order_id,
            "source_row": self.source_row,
            "in_cohort": self.in_cohort,
            "detail": self.detail,
        }


def _record_key(order_id: str, product_raw: Optional[str], sale_date) -> tuple:
    return (order_id, (product_raw or "").strip(), sale_date)


def _index_records(
    records: Iterable[PriceResolutionRecord],
) -> dict[tuple, list[PriceResolutionRecord]]:
    index: dict[tuple, list[PriceResolutionRecord]] = {}
    for record in records:
        key = _record_key(record.order_id, record.raw_product_identity, record.sale_date)
        index.setdefault(key, []).append(record)
    return index


def detect_silent_errors(
    *,
    lines: list[WorkingLine],
    records: tuple[PriceResolutionRecord, ...],
    freeze: SourceFreeze,
    cohort_ids: set[str],
) -> list[SilentErrorFinding]:
    """Chạy trên MỌI dòng của file, không chỉ cohort.

    Cố ý: hai trong số các mâu thuẫn nguy hiểm nhất là **rò thẩm quyền qua
    mốc cutover** (§14 — Batch 50 tháng 01/2026 không được tự động hoá bằng
    dữ liệu Tracking tháng 08/2026), và chúng chỉ quan sát được ở phần dữ
    liệu NGOÀI cohort. Mỗi finding mang cờ `in_cohort` để hai câu hỏi không
    bị trộn.
    """
    findings: list[SilentErrorFinding] = []
    evidence = freeze.sources.evidence_snapshot
    index = _index_records(records)
    pp_version = freeze.sources.public_purchase
    pp_prices = (
        FilePriceProvider(pp_version.validated_price_rows())
        if pp_version is not None
        else None
    )

    def add(code: str, line: WorkingLine, detail: str) -> None:
        findings.append(
            SilentErrorFinding(
                code=code,
                order_id=line.order_id,
                source_row=line.raw.source_row,
                in_cohort=line.order_id in cohort_ids,
                detail=detail,
            )
        )

    for line in lines:
        source = line.price_source
        price = line.accounting_purchase_price
        post_cutover = line.date is not None and line.date >= CUTOVER_DATE

        # --- Nhãn nguồn nằm ngoài tập đóng ------------------------------
        if source not in KNOWN_PRICE_SOURCES:
            add(
                "UNKNOWN_PRICE_SOURCE_LABEL",
                line,
                f"price_source={source!r} không thuộc tập nhãn đã review.",
            )

        # --- Pending mà vẫn mang số ------------------------------------
        if source == PRICE_SOURCE_PENDING and price is not None:
            add(
                "PENDING_LINE_CARRIES_PRICE",
                line,
                f"price_source='Pending' nhưng accounting_purchase_price={price} "
                "(INV-25: Pending không phải 0, không phải giá cũ).",
            )
        if source != PRICE_SOURCE_PENDING and price is None:
            add(
                "PRICED_LABEL_WITHOUT_PRICE",
                line,
                f"price_source={source!r} nhưng accounting_purchase_price=None.",
            )

        # --- Rò thẩm quyền qua mốc cutover ------------------------------
        if post_cutover and source in LEGACY_PRICE_SOURCES:
            add(
                "CROSS_CUTOVER_LEGACY_AUTHORITY_LEAK",
                line,
                f"sale_date={line.date} >= {CUTOVER_DATE} nhưng dùng thẩm quyền "
                f"PRE-cutover {source!r} (DEC-154 P00 chỉ áp cho nhánh lịch sử).",
            )
        if (
            line.date is not None
            and line.date < CUTOVER_DATE
            and source in POST_CUTOVER_PRICE_SOURCES
        ):
            add(
                "CROSS_CUTOVER_POST_AUTHORITY_LEAK",
                line,
                f"sale_date={line.date} < {CUTOVER_DATE} nhưng dùng thẩm quyền "
                f"POST-cutover {source!r}; dữ liệu Tracking 08/2026 không được "
                "phép quyết định giá của một đơn trước mốc.",
            )

        # --- Kiểm tra số học độc lập (DEC-126 §1, DEC-143) --------------
        if (
            line.sell_price is not None
            and price is not None
            and line.quantity is not None
        ):
            expected = (line.sell_price - price) * line.quantity
            if line.accounting_profit != expected:
                add(
                    "ACCOUNTING_PROFIT_MISMATCH",
                    line,
                    f"(SellPrice {line.sell_price} - Purchase {price}) × "
                    f"Quantity {line.quantity} = {expected}, engine trả "
                    f"{line.accounting_profit}.",
                )
        elif line.accounting_profit is not None:
            add(
                "ACCOUNTING_PROFIT_FABRICATED",
                line,
                "Có accounting_profit trong khi một input còn thiếu "
                f"(sell_price={line.sell_price}, purchase={price}, "
                f"quantity={line.quantity}).",
            )

        if (
            line.sell_price is not None
            and line.kpi_purchase_price is not None
            and line.quantity is not None
            and line.eligible_kpi_profit is not None
        ):
            expected_kpi = (
                line.sell_price - line.kpi_purchase_price
            ) * line.quantity - line.discount
            if line.eligible_kpi_profit != expected_kpi:
                add(
                    "ELIGIBLE_KPI_PROFIT_MISMATCH",
                    line,
                    f"(SellPrice {line.sell_price} - KpiPurchase "
                    f"{line.kpi_purchase_price}) × Quantity {line.quantity} - "
                    f"Discount {line.discount} = {expected_kpi}, engine trả "
                    f"{line.eligible_kpi_profit}.",
                )
        elif line.eligible_kpi_profit is not None:
            add(
                "ELIGIBLE_KPI_PROFIT_FABRICATED",
                line,
                "Có eligible_kpi_profit trong khi một input còn Pending "
                f"(sell_price={line.sell_price}, kpi_purchase="
                f"{line.kpi_purchase_price}, quantity={line.quantity}).",
            )

        if not post_cutover:
            continue

        # --- Từ đây chỉ còn nhánh POST-cutover: đối chiếu với audit trail --
        matched = index.get(
            _record_key(line.order_id, line.product_raw, line.date), []
        )
        if not matched:
            add(
                "RESOLUTION_RECORD_MISSING",
                line,
                "Dòng post-cutover không có PriceResolutionRecord nào — giá "
                "(hoặc Pending) của nó không mở lại được.",
            )
            continue

        statuses = {r.status for r in matched}
        prices = {r.price_vnd for r in matched}
        if len(statuses) > 1 or len(prices) > 1:
            add(
                "RESOLUTION_RECORD_AMBIGUOUS",
                line,
                f"{len(matched)} bản ghi cùng khoá (order/hàng/ngày) bất đồng: "
                f"statuses={sorted(s.value for s in statuses)}, "
                f"prices={sorted(str(p) for p in prices)}.",
            )
            continue

        record = matched[0]
        if record.price_vnd != price:
            add(
                "LINE_PRICE_NOT_FROM_RECORD",
                line,
                f"Dòng mang {price} nhưng bản ghi giá của chính nó nói "
                f"{record.price_vnd} — giá đã đến từ chỗ khác (rò dòng anh em).",
            )
        if record.price_source != source:
            add(
                "LINE_PRICE_SOURCE_NOT_FROM_RECORD",
                line,
                f"Dòng mang price_source={source!r}, bản ghi nói "
                f"{record.price_source!r}.",
            )
        if record.is_resolved and record.identity is None:
            add(
                "RESOLVED_WITHOUT_IDENTITY",
                line,
                "Bản ghi RESOLVED nhưng không mang identity nào — không biết "
                "giá này thuộc về sản phẩm nào.",
            )

        if not record.is_resolved:
            continue

        # --- Nhánh TRACKING: kiểm lại chính bằng chứng tái dựng ----------
        if record.rule is CompositionRule.TRACKING_HISTORY_AUTHORITY:
            if evidence.tracking_price_history_capture_id is None:
                add(
                    "SOURCE_UNAVAILABLE_BUT_PRICED",
                    line,
                    "Giá đến từ TRACKING_PRICE_HISTORY nhưng ảnh chụp lịch sử "
                    "giá không có capture_id — nguồn không tồn tại mà vẫn trả giá.",
                )
            reconstruction = record.tracking_reconstruction
            if reconstruction is None or not reconstruction.is_resolved:
                add(
                    "TRACKING_PRICE_WITHOUT_RECONSTRUCTION",
                    line,
                    "Bản ghi RESOLVED theo nhánh Tracking nhưng không mang một "
                    "PriceReconstruction đã resolve nào.",
                )
            else:
                prov = reconstruction.provenance
                raw = prov.raw_value_thousand_vnd
                resolved = prov.resolved_price_vnd
                if raw is not None and resolved is not None:
                    if resolved != raw * THOUSAND_VND_TO_VND:
                        add(
                            "UNIT_CONVERSION_MISMATCH",
                            line,
                            f"raw={raw} nghìn VND × {THOUSAND_VND_TO_VND} ≠ "
                            f"resolved={resolved} VND.",
                        )
                if resolved is not None and resolved != record.price_vnd:
                    add(
                        "RECONSTRUCTION_PRICE_MISMATCH",
                        line,
                        f"provenance nói {resolved}, bản ghi composition nói "
                        f"{record.price_vnd}.",
                    )
                stamp = prov.decisive_source_timestamp
                if stamp is not None and stamp > prov.sale_interval_start:
                    add(
                        "PRICE_AFTER_SALE_USED_FOR_HISTORICAL_STATE",
                        line,
                        f"Sự kiện giá quyết định lúc {stamp.isoformat()} nằm SAU "
                        f"đầu khoảng bán {prov.sale_interval_start.isoformat()} "
                        "— trạng thái hiện tại đã bị dùng cho một thời điểm quá khứ.",
                    )
                if prov.namespace is not None and prov.namespace != Namespace.TRACKING.value:
                    add(
                        "TRACKING_PROVENANCE_WRONG_NAMESPACE",
                        line,
                        f"provenance.namespace={prov.namespace!r} trên nhánh TRACKING.",
                    )

        # --- Nhánh PUBLIC_PURCHASE: tra lại chính bảng giá đã đông lạnh ---
        elif record.rule is CompositionRule.PUBLIC_PURCHASE_DIRECT:
            if evidence.public_purchase_version_id is None:
                add(
                    "SOURCE_UNAVAILABLE_BUT_PRICED",
                    line,
                    "Giá đến từ bảng Public Purchase nhưng snapshot không có "
                    "version_id nào.",
                )
            if pp_prices is not None and record.identity is not None:
                again = pp_prices.find_record(
                    record.identity.source_product_code, line.date
                )
                if again is None:
                    add(
                        "PUBLIC_PURCHASE_PRICE_NOT_EFFECTIVE_AT_SALE_DATE",
                        line,
                        f"Tra lại độc lập {record.identity} tại {line.date}: "
                        "không có bản ghi giá nào hiệu lực, nhưng dòng vẫn có giá.",
                    )
                elif again.purchase_price != record.price_vnd:
                    add(
                        "PUBLIC_PURCHASE_PRICE_MISMATCH",
                        line,
                        f"Tra lại độc lập cho {record.price_vnd}, bảng giá nói "
                        f"{again.purchase_price}.",
                    )

        elif record.rule is CompositionRule.PUBLIC_PURCHASE_VENDOR_FALLBACK:
            add(
                "VENDOR_FALLBACK_REACHED_WHILE_BLOCKED",
                line,
                "Nhánh P03/P09 đã chạy trong khi TASK-105C vẫn NOT AUTHORIZED — "
                "một absence CHƯA XÁC ĐỊNH đã bị đọc thành absence đã xác định.",
            )

    return findings


# ======================================================================
# 6. Mẫu kiểm tay — ưu tiên bao phủ, không ép đủ khi cohort nhỏ
# ======================================================================

PRICE_CHANGE_PROXIMITY_DAYS = 30
"""Một sự kiện đổi giá trong vòng ngần này trước ngày bán làm dòng đó đáng
được người kiểm nhìn tận mắt (§10 — "price change gần ngày bán"). Con số này
KHÔNG tham gia vào bất kỳ phép quyết định giá nào; nó chỉ xếp thứ tự ưu tiên
của mẫu kiểm tay."""


def _sample_categories(view: dict[str, Any]) -> list[str]:
    """Những nhóm bao phủ mà dòng này đại diện được (§10)."""
    tags: list[str] = []
    outcome = view["order_outcome"]
    rule = view.get("composition_rule")
    reason = view.get("pending_reason")
    resolved = view["price_source"] != PRICE_SOURCE_PENDING

    if resolved and rule == CompositionRule.TRACKING_HISTORY_AUTHORITY.value:
        tags.append("AUTO_TRACKING")
    if resolved and rule == CompositionRule.PUBLIC_PURCHASE_DIRECT.value:
        tags.append("AUTO_PUBLIC_PURCHASE")
    if not resolved and outcome == "REVIEW_QUEUE":
        namespace = view.get("identity_namespace")
        if namespace == Namespace.TRACKING.value:
            tags.append("REVIEW_QUEUE_TRACKING")
        elif namespace == Namespace.PUBLIC_PURCHASE.value:
            tags.append("REVIEW_QUEUE_PUBLIC_PURCHASE")
        else:
            tags.append("REVIEW_QUEUE_NO_IDENTITY")
    if view["order_line_count"] > 1:
        tags.append("MULTI_LINE")
    if view["discount"] not in (None, "0"):
        tags.append("DISCOUNT")
    if view["quantity"] is not None and Decimal(view["quantity"]) > 1:
        tags.append("QUANTITY_GT_1")
    if view.get("price_change_near_sale"):
        tags.append("PRICE_CHANGE_NEAR_SALE")
    if reason == "IDENTITY_REQUIRES_CONFIRMATION":
        tags.append("IDENTITY_AMBIGUITY")
    return tags


SAMPLE_CATEGORY_ORDER = (
    "AUTO_TRACKING",
    "AUTO_PUBLIC_PURCHASE",
    "REVIEW_QUEUE_TRACKING",
    "REVIEW_QUEUE_PUBLIC_PURCHASE",
    "REVIEW_QUEUE_NO_IDENTITY",
    "MULTI_LINE",
    "DISCOUNT",
    "QUANTITY_GT_1",
    "PRICE_CHANGE_NEAR_SALE",
    "IDENTITY_AMBIGUITY",
)


def build_manual_sample(
    views: list[dict[str, Any]], sample_size: int
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Chọn mẫu THEO NHÓM BAO PHỦ, deterministic theo `source_row`.

    Duyệt từng nhóm theo thứ tự cố định và lấy dòng chưa được chọn có
    `source_row` nhỏ nhất. Cohort nhỏ thì một số nhóm rỗng — không ép, và
    nhóm rỗng được ghi ra để không ai đọc mẫu như thể nó đã phủ hết.
    """
    by_row = {v["source_row"]: v for v in views}
    chosen_rows: list[int] = []
    coverage: dict[str, int] = {}
    for category in SAMPLE_CATEGORY_ORDER:
        candidates = sorted(
            row for row, v in by_row.items() if category in v["sample_categories"]
        )
        coverage[category] = len(candidates)
        for row in candidates:
            if row not in chosen_rows:
                chosen_rows.append(row)
                break
    # Còn chỗ trống thì lấp bằng các dòng đầu tiên chưa chọn — vẫn deterministic.
    for row in sorted(by_row):
        if len(chosen_rows) >= sample_size:
            break
        if row not in chosen_rows:
            chosen_rows.append(row)
    sample = [by_row[row] for row in sorted(chosen_rows[:sample_size])]
    return sample, coverage


# ======================================================================
# 7. Chạy kiểm định
# ======================================================================


@dataclass
class ValidationRun:
    cohort: CohortDefinition
    freeze: SourceFreeze
    metrics: dict[str, Any]
    order_outcomes: list[OrderOutcome]
    line_views: list[dict[str, Any]]
    findings: list[SilentErrorFinding]
    manual_sample: list[dict[str, Any]]
    sample_coverage: dict[str, int]
    queue_rows: list[dict[str, Any]]
    status: str
    pipeline_error: Optional[str] = None
    manual_summary: Optional[dict[str, Any]] = None
    command: str = ""


def analyze(
    sales_path: Path,
    *,
    config_dir: Path = Path("config"),
    tracking_capture: Path = TRACKING_PRICE_HISTORY_CAPTURE_PATH,
    tracking_catalog: Path = TRACKING_CATALOG_CAPTURE_PATH,
    public_purchase: Path = PUBLIC_PURCHASE_SOURCE_PATH,
    identity_store: Path = IDENTITY_STORE_LOG_PATH,
    cohort_size: int = DEFAULT_COHORT_SIZE,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    tracking_identity_authority: bool = True,
) -> ValidationRun:
    """Một lần kiểm định đầy đủ: đông lạnh → chạy production → đọc kết quả."""
    cohort = select_post_cutover_cohort(sales_path, cohort_size)
    freeze = freeze_sources(
        config_dir=config_dir,
        tracking_capture=tracking_capture,
        tracking_catalog=tracking_catalog,
        public_purchase=public_purchase,
        identity_store=identity_store,
        tracking_identity_authority=tracking_identity_authority,
    )
    cohort_ids = set(cohort.order_ids)
    classified = classify_orders_by_cutover(sales_path)
    expected_rows = {
        oid: set(classified[oid]["source_rows"]) for oid in cohort.order_ids
    }

    composition = PostCutoverPriceComposition(freeze.sources)
    try:
        result = run_import_production(
            sales_path, config_dir=config_dir, price_composition=composition
        )
    except Exception:  # noqa: BLE001 — đây CHÍNH LÀ ô ERROR của §9
        metrics = _metrics(
            cohort=cohort,
            counts={"ERROR": len(cohort.order_ids)},
            dropped_lines=0,
        )
        return ValidationRun(
            cohort=cohort,
            freeze=freeze,
            metrics=metrics,
            order_outcomes=[
                OrderOutcome(
                    order_id=oid,
                    outcome="ERROR",
                    line_count=0,
                    expected_line_count=len(expected_rows[oid]),
                    source_rows=sorted(expected_rows[oid]),
                    missing_source_rows=sorted(expected_rows[oid]),
                    queue_categories=[],
                    unresolved_dimensions=[],
                    uncovered_dimensions=[],
                    sale_dates=[],
                )
                for oid in cohort.order_ids
            ],
            line_views=[],
            findings=[],
            manual_sample=[],
            sample_coverage={},
            queue_rows=[],
            status="PIPELINE_ERROR",
            pipeline_error=traceback.format_exc(),
        )

    coverage = build_queue_coverage(result.review_queue.items)
    orders_by_id = {o.order_id: o for o in result.orders}
    all_lines = [line for order in result.orders for line in order.lines]
    records = composition.records
    record_index = _index_records(records)

    findings = detect_silent_errors(
        lines=all_lines,
        records=records,
        freeze=freeze,
        cohort_ids=cohort_ids,
    )

    outcomes: list[OrderOutcome] = []
    views: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    dropped_lines = 0

    for oid in cohort.order_ids:
        order = orders_by_id.get(oid)
        expected = expected_rows[oid]
        if order is None:
            counts["SILENTLY_DROPPED"] = counts.get("SILENTLY_DROPPED", 0) + 1
            dropped_lines += len(expected)
            outcomes.append(
                OrderOutcome(
                    order_id=oid,
                    outcome="SILENTLY_DROPPED",
                    line_count=0,
                    expected_line_count=len(expected),
                    source_rows=sorted(expected),
                    missing_source_rows=sorted(expected),
                    queue_categories=[],
                    unresolved_dimensions=[],
                    uncovered_dimensions=[],
                    sale_dates=[],
                )
            )
            findings.append(
                SilentErrorFinding(
                    code="SILENTLY_DROPPED_ORDER",
                    order_id=oid,
                    source_row=min(expected) if expected else None,
                    in_cohort=True,
                    detail=(
                        f"Đơn có trong file nguồn ({len(expected)} dòng) nhưng "
                        "không xuất hiện trong ImportResult.orders."
                    ),
                )
            )
            continue

        present_rows = {line.raw.source_row for line in order.lines}
        missing = sorted(expected - present_rows)
        if missing:
            dropped_lines += len(missing)
            findings.append(
                SilentErrorFinding(
                    code="SILENTLY_DROPPED_LINE",
                    order_id=oid,
                    source_row=missing[0],
                    in_cohort=True,
                    detail=(
                        f"Dòng {missing} của đơn có trong file nguồn nhưng không "
                        "có trong kết quả — một dòng anh em đã biến mất."
                    ),
                )
            )

        queue_categories: set[str] = set()
        unresolved: set[str] = set()
        uncovered: set[str] = set()
        for line in order.lines:
            row = line.raw.source_row
            for category, rows in coverage.by_category_rows.items():
                if row in rows:
                    queue_categories.add(category)
            for category, order_ids in coverage.by_category_orders.items():
                if oid in order_ids:
                    queue_categories.add(category)
            dims = line_unresolved_dimensions(line)
            unresolved.update(dims)
            for dim in dims:
                required = dict(UNRESOLVED_DIMENSIONS).get(dim)
                if not coverage.covers(required, row, oid):
                    uncovered.add(dim)
                    findings.append(
                        SilentErrorFinding(
                            code="UNRESOLVED_NOT_IN_REVIEW_QUEUE",
                            order_id=oid,
                            source_row=row,
                            in_cohort=True,
                            detail=(
                                f"Chiều {dim!r} chưa resolve nhưng không có mục "
                                f"Review Queue {required!r} nào phủ dòng này."
                            ),
                        )
                    )
            views.append(
                _line_view(
                    line=line,
                    order_line_count=len(order.lines),
                    record=_single_record(record_index, line),
                )
            )

        # Một line provenance bị mất làm toàn order không còn là AUTO hay
        # REVIEW_QUEUE hợp lệ. Nếu vẫn đếm theo các dòng còn lại, accounting
        # rate có thể trông 100% dù một sibling đã biến mất.
        if missing:
            outcome = "SILENTLY_DROPPED"
        elif uncovered:
            outcome = "PENDING_NOT_QUEUED"
        elif queue_categories:
            outcome = "REVIEW_QUEUE"
        else:
            outcome = "AUTO"
        counts[outcome] = counts.get(outcome, 0) + 1

        outcomes.append(
            OrderOutcome(
                order_id=oid,
                outcome=outcome,
                line_count=len(order.lines),
                expected_line_count=len(expected),
                source_rows=sorted(present_rows),
                missing_source_rows=missing,
                queue_categories=sorted(queue_categories),
                unresolved_dimensions=sorted(unresolved),
                uncovered_dimensions=sorted(uncovered),
                sale_dates=sorted(
                    {l.date.isoformat() for l in order.lines if l.date is not None}
                ),
            )
        )

    outcome_by_order = {o.order_id: o.outcome for o in outcomes}
    for view in views:
        view["order_outcome"] = outcome_by_order.get(view["order_id"], "")
        view["sample_categories"] = _sample_categories(view)
        view["sales_input_sha256"] = cohort.source_sha256
        view["manual_sample_id"] = manual_sample_id(cohort.source_sha256, view)

    sample, sample_coverage = build_manual_sample(views, sample_size)
    metrics = _metrics(cohort=cohort, counts=counts, dropped_lines=dropped_lines)
    metrics["SILENT_ERROR_FINDINGS"] = len(
        [f for f in findings if f.in_cohort]
    )
    metrics["SILENT_ERROR_FINDINGS_OUTSIDE_COHORT"] = len(
        [f for f in findings if not f.in_cohort]
    )
    metrics["SILENT_ERROR_RATE"] = "NOT_YET_MEASURED"
    metrics["MANUAL_SAMPLE_SIZE"] = len(sample)
    # Bao nhiêu dòng đã thực sự đi qua bộ phát hiện. Không có con số này thì
    # `SILENT_ERROR_FINDINGS = 0` đọc giống hệt "chưa kiểm dòng nào" — và một
    # cohort rỗng vẫn kiểm toàn bộ file, đó chính là chỗ phát hiện được rò
    # thẩm quyền qua mốc cutover.
    metrics["LINES_CHECKED_FOR_SILENT_ERRORS"] = len(all_lines)

    queue_rows = [
        {
            "category": item.category,
            "severity": item.severity,
            "scope": item.scope,
            "order_id": item.order_id or "",
            "affected_count": item.affected_count,
            "cohort_rows": sorted(
                row
                for row in item.provenance.source_rows
                if row in {v["source_row"] for v in views}
            ),
            "message": item.message,
        }
        for item in result.review_queue.items
    ]

    return ValidationRun(
        cohort=cohort,
        freeze=freeze,
        metrics=metrics,
        order_outcomes=outcomes,
        line_views=views,
        findings=findings,
        manual_sample=sample,
        sample_coverage=sample_coverage,
        queue_rows=queue_rows,
        status=_status(cohort, metrics, findings),
    )


def _single_record(
    index: dict[tuple, list[PriceResolutionRecord]], line: WorkingLine
) -> Optional[PriceResolutionRecord]:
    matched = index.get(_record_key(line.order_id, line.product_raw, line.date), [])
    return matched[0] if len(matched) == 1 else None


def _line_view(
    *,
    line: WorkingLine,
    order_line_count: int,
    record: Optional[PriceResolutionRecord],
) -> dict[str, Any]:
    """Một dòng cohort, phẳng hoá đủ để người kiểm mở lại từng con số (§13)."""
    reconstruction = record.tracking_reconstruction if record else None
    prov = reconstruction.provenance if reconstruction else None
    near_change = False
    if (
        prov is not None
        and prov.decisive_source is DecisiveSource.HISTORY_EVENT
        and prov.decisive_source_timestamp is not None
    ):
        # Chỉ một SỰ KIỆN đổi giá mới đáng gọi là "giá đổi gần ngày bán". Mốc
        # cutover cũng có dấu thời gian, nhưng nó là điểm neo của cả trục —
        # gắn nhãn cho nó sẽ làm mọi dòng đều "gần một thay đổi" và nhãn mất
        # hết giá trị xếp ưu tiên.
        delta = prov.sale_interval_start - prov.decisive_source_timestamp
        near_change = _dt.timedelta(0) <= delta <= _dt.timedelta(
            days=PRICE_CHANGE_PROXIMITY_DAYS
        )
    if (
        prov is not None
        and prov.unresolved_reason is not None
        and prov.unresolved_reason is UnresolvedReason.PRICE_CHANGED_WITHIN_SALE_INTERVAL
    ):
        near_change = True
    return {
        "order_id": line.order_id,
        "source_row": line.raw.source_row,
        "source_file": line.raw.source_file,
        "sale_date": _iso(line.date),
        "product_raw": line.product_raw,
        "order_line_count": order_line_count,
        "quantity": _num(line.quantity),
        "sell_price": _num(line.sell_price),
        "discount": _num(line.discount),
        "total_sales": _num(line.total_sales),
        "accounting_purchase_price": _num(line.accounting_purchase_price),
        "price_source": line.price_source,
        "accounting_profit": _num(line.accounting_profit),
        "kpi_purchase_price": _num(line.kpi_purchase_price),
        "kpi_purchase_price_provenance": line.kpi_purchase_price_provenance,
        "eligible_kpi_profit": _num(line.eligible_kpi_profit),
        "employee_mapping_status": line.employee_mapping_status,
        "conversion_scheme_final": line.conversion_scheme_final,
        "composition_rule": record.rule.value if record else None,
        "pending_reason": (
            record.reason.value if record and record.reason is not None else None
        ),
        "pending_detail": record.detail if record else "",
        "identity": str(record.identity) if record and record.identity else None,
        "identity_namespace": (
            record.identity.namespace.value if record and record.identity else None
        ),
        "tracking_capture_id": (
            prov.snapshot_capture_id if prov is not None else None
        ),
        "tracking_decisive_source": (
            prov.decisive_source.value if prov is not None else None
        ),
        "tracking_decisive_event_id": (
            prov.decisive_event_id if prov is not None else None
        ),
        "tracking_decisive_timestamp": (
            _iso(prov.decisive_source_timestamp) if prov is not None else None
        ),
        "tracking_raw_thousand_vnd": (
            _num(prov.raw_value_thousand_vnd) if prov is not None else None
        ),
        "tracking_unit_conversion": prov.unit_conversion if prov is not None else None,
        "price_change_near_sale": near_change,
        "order_outcome": "",
        "sample_categories": [],
    }


def manual_sample_id(sales_input_sha256: str, view: dict[str, Any]) -> str:
    """Khoá bất biến của đúng một dòng được chọn để kiểm tay.

    `source_row` chỉ có ý nghĩa trong đúng một file. Gắn nó với hash nội dung
    đầu vào, OrderID, ngày và product ngăn một CSV của run A bị áp sang run B
    khi file đã đổi nhưng số dòng tình cờ giữ nguyên.
    """
    payload = {
        "sales_input_sha256": sales_input_sha256,
        "source_row": view["source_row"],
        "order_id": view["order_id"],
        "sale_date": view["sale_date"],
        "product_raw": view["product_raw"],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _metrics(
    *, cohort: CohortDefinition, counts: dict[str, int], dropped_lines: int
) -> dict[str, Any]:
    input_orders = cohort.unique_orders
    auto = counts.get("AUTO", 0)
    queued = counts.get("REVIEW_QUEUE", 0)
    errored = counts.get("ERROR", 0)
    pending_not_queued = counts.get("PENDING_NOT_QUEUED", 0)
    dropped = counts.get("SILENTLY_DROPPED", 0)
    accounted = auto + queued + errored
    return {
        "INPUT_ORDERS": input_orders,
        "INPUT_LINES": cohort.raw_line_count,
        "AUTO_ORDERS": auto,
        "REVIEW_QUEUE_ORDERS": queued,
        "ERROR_ORDERS": errored,
        "PENDING_NOT_QUEUED": pending_not_queued,
        "SILENTLY_DROPPED": dropped,
        "SILENTLY_DROPPED_LINES": dropped_lines,
        "ORDER_ACCOUNTING_RATE": _rate(accounted, input_orders),
        "AUTOMATION_RATE": _rate(auto, input_orders),
        "SAMPLE_NOT_YET_50": cohort.sample_not_yet_50,
    }


def _status(
    cohort: CohortDefinition,
    metrics: dict[str, Any],
    findings: list[SilentErrorFinding],
) -> str:
    """Trạng thái vận hành của lần chạy. KHÔNG BAO GIỜ là một tuyên bố
    Production Acceptance — xem docstring đầu file."""
    if cohort.unique_orders == 0:
        return "WAITING_REAL_POST_CUTOVER_DATA"
    if findings:
        return "BLOCKED_BY_SILENT_ERROR_FINDINGS"
    if metrics["ORDER_ACCOUNTING_RATE"] != 1.0:
        return "BLOCKED_BY_ORDER_ACCOUNTING"
    return "AWAITING_MANUAL_VALIDATION"


# ======================================================================
# 8. Nạp verdict kiểm tay — SILENT_ERROR_RATE chỉ tồn tại khi có người chấm
# ======================================================================


def load_manual_verdicts(
    path: Path, sample: list[dict[str, Any]]
) -> dict[str, Any]:
    """Đọc `manual_sample.csv` đã điền cột `outcome`.

    Máy KHÔNG tự chấm. Dòng để trống là `NOT_VALIDATED`, không phải
    `CORRECT_AUTO` — và chừng nào còn một dòng chưa chấm thì mẫu chưa hoàn
    tất, dù mọi dòng đã chấm đều đúng.
    """
    sample_by_id = {str(v["manual_sample_id"]): v for v in sample}
    verdicts: dict[str, str] = {}
    notes: dict[int, str] = {}
    invalid: list[str] = []
    unknown_rows: list[int] = []
    duplicate_ids: list[str] = []
    seen_ids: set[str] = set()

    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw_row = (row.get("source_row") or "").strip()
            if not raw_row:
                continue
            try:
                source_row = int(raw_row)
            except ValueError:
                invalid.append(f"source_row={raw_row!r} không phải số nguyên")
                continue
            outcome = (row.get("outcome") or "").strip().upper()
            if not outcome:
                continue
            if outcome not in MANUAL_OUTCOMES:
                invalid.append(
                    f"dòng {source_row}: outcome={outcome!r} ngoài enum "
                    f"{MANUAL_OUTCOMES}"
                )
                continue
            sample_id = (row.get("manual_sample_id") or "").strip()
            expected = sample_by_id.get(sample_id)
            if expected is None:
                unknown_rows.append(source_row)
                continue
            if sample_id in seen_ids:
                duplicate_ids.append(sample_id)
                continue
            # `source_row` không đủ để gắn verdict: nó chỉ có nghĩa trong
            # đúng file sales đã freeze. Hai cột lặp này bắt lỗi copy/paste
            # sai và làm mapping giữa hai run fail-closed.
            for key in ("order_id", "sales_input_sha256"):
                if (row.get(key) or "").strip() != str(expected[key]):
                    invalid.append(
                        f"dòng {source_row}: {key} không khớp mẫu đã freeze"
                    )
                    break
            else:
                seen_ids.add(sample_id)
                verdicts[sample_id] = outcome
                notes[source_row] = (row.get("note") or "").strip()

    counts = {outcome: 0 for outcome in MANUAL_OUTCOMES}
    for outcome in verdicts.values():
        counts[outcome] += 1
    validated = sum(counts.values())
    silent = counts["SILENT_ERROR"]
    return {
        "verdicts_file": str(path),
        "counts": counts,
        "MANUALLY_VALIDATED": validated,
        "SILENT_ERROR": silent,
        "SILENT_ERROR_RATE": _rate(silent, validated),
        "sample_size": len(sample_by_id),
        "not_validated_rows": sorted(
            int(v["source_row"])
            for sample_id, v in sample_by_id.items()
            if sample_id not in verdicts
        ),
        "rows_outside_sample": sorted(unknown_rows),
        "duplicate_sample_ids": sorted(duplicate_ids),
        "invalid_entries": invalid,
        "complete": (
            validated > 0
            and len(verdicts) == len(sample_by_id)
            and not invalid
            and not unknown_rows
            and not duplicate_ids
        ),
        "notes": {str(k): v for k, v in notes.items() if v},
    }


def apply_manual_verdicts(run: ValidationRun, summary: dict[str, Any]) -> None:
    """Gắn kết quả kiểm tay vào lần chạy và cập nhật trạng thái.

    `ELIGIBLE_FOR_PRODUCTION_ACCEPTANCE_REVIEW` là trần của công cụ này: nó
    nói "mọi điều kiện MÁY kiểm được đã thoả", không nói dữ liệu là thật.
    """
    run.manual_summary = summary
    run.metrics["MANUALLY_VALIDATED"] = summary["MANUALLY_VALIDATED"]
    run.metrics["SILENT_ERROR"] = summary["SILENT_ERROR"]
    run.metrics["SILENT_ERROR_RATE"] = (
        "NOT_YET_MEASURED"
        if summary["SILENT_ERROR_RATE"] is None
        else summary["SILENT_ERROR_RATE"]
    )
    if summary["SILENT_ERROR"] > 0:
        run.status = "BLOCKED_BY_SILENT_ERROR"
        return
    if run.status != "AWAITING_MANUAL_VALIDATION":
        return
    if summary["complete"]:
        run.status = "ELIGIBLE_FOR_PRODUCTION_ACCEPTANCE_REVIEW"


# ======================================================================
# 9. Artifact — CSV/JSON/Markdown, không Dashboard
# ======================================================================

_ORDER_CSV_FIELDS = (
    "order_id",
    "outcome",
    "line_count",
    "expected_line_count",
    "missing_source_rows",
    "queue_categories",
    "unresolved_dimensions",
    "uncovered_dimensions",
    "sale_dates",
    "source_rows",
)

_LINE_CSV_FIELDS = (
    "order_id",
    "source_row",
    "sale_date",
    "order_outcome",
    "product_raw",
    "identity",
    "identity_namespace",
    "quantity",
    "sell_price",
    "discount",
    "total_sales",
    "accounting_purchase_price",
    "price_source",
    "composition_rule",
    "pending_reason",
    "accounting_profit",
    "kpi_purchase_price",
    "kpi_purchase_price_provenance",
    "eligible_kpi_profit",
    "employee_mapping_status",
    "conversion_scheme_final",
    "tracking_capture_id",
    "tracking_decisive_source",
    "tracking_decisive_event_id",
    "tracking_decisive_timestamp",
    "tracking_raw_thousand_vnd",
    "tracking_unit_conversion",
    "price_change_near_sale",
    "order_line_count",
    "sample_categories",
    "pending_detail",
)

_SAMPLE_CSV_FIELDS = (
    "manual_sample_id",
    "sales_input_sha256",
    "source_row",
    "order_id",
    "sale_date",
    "sample_categories",
    "product_raw",
    "identity",
    "quantity",
    "sell_price",
    "discount",
    "accounting_purchase_price",
    "price_source",
    "composition_rule",
    "pending_reason",
    "accounting_profit",
    "kpi_purchase_price",
    "eligible_kpi_profit",
    "tracking_decisive_source",
    "tracking_decisive_timestamp",
    "tracking_raw_thousand_vnd",
    "outcome",
    "note",
)


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "|".join(str(v) for v in value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([_csv_value(row.get(field)) for field in fields])


def _manual_sample_has_verdicts(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            return any(
                (row.get("outcome") or "").strip() for row in csv.DictReader(handle)
            )
    except OSError:
        return True  # không đọc được thì coi như CÓ, và không ghi đè


def write_artifacts(run: ValidationRun, out_dir: Path) -> list[Path]:
    """Ghi toàn bộ artifact của một lần chạy. Trả về các file đã ghi.

    `manual_sample.csv` KHÔNG BAO GIỜ bị ghi đè khi nó đã mang verdict của
    người kiểm — công việc ấy không tái tạo được, và một lần chạy lại vô ý
    sẽ xoá đúng bằng chứng đắt nhất của cả quy trình.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def record(path: Path) -> Path:
        written.append(path)
        return path

    (out_dir / "cohort.json").write_text(
        json.dumps(run.cohort.as_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    record(out_dir / "cohort.json")

    (out_dir / "metrics.json").write_text(
        json.dumps(
            {
                "status": run.status,
                "command": run.command,
                "metrics": run.metrics,
                "sources": run.freeze.as_dict(),
                "manual_validation": run.manual_summary,
                "sample_coverage": run.sample_coverage,
                "pipeline_error": run.pipeline_error,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    record(out_dir / "metrics.json")

    (out_dir / "silent_error_findings.json").write_text(
        json.dumps(
            [f.as_dict() for f in run.findings], ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    record(out_dir / "silent_error_findings.json")

    _write_csv(
        out_dir / "orders.csv",
        _ORDER_CSV_FIELDS,
        [o.as_dict() for o in run.order_outcomes],
    )
    record(out_dir / "orders.csv")

    _write_csv(out_dir / "lines.csv", _LINE_CSV_FIELDS, run.line_views)
    record(out_dir / "lines.csv")

    _write_csv(
        out_dir / "review_queue.csv",
        ("category", "severity", "scope", "order_id", "affected_count",
         "cohort_rows", "message"),
        run.queue_rows,
    )
    record(out_dir / "review_queue.csv")

    sample_path = out_dir / "manual_sample.csv"
    if _manual_sample_has_verdicts(sample_path):
        record(out_dir / "manual_sample.SKIPPED_EXISTING_VERDICTS")
        (out_dir / "manual_sample.SKIPPED_EXISTING_VERDICTS").write_text(
            "manual_sample.csv đã có verdict của người kiểm — KHÔNG ghi đè.\n",
            encoding="utf-8",
        )
    else:
        rows = [dict(view, outcome="", note="") for view in run.manual_sample]
        _write_csv(sample_path, _SAMPLE_CSV_FIELDS, rows)
        record(sample_path)

    (out_dir / "summary.md").write_text(render_summary(run), encoding="utf-8")
    record(out_dir / "summary.md")
    return written


def render_summary(run: ValidationRun) -> str:
    m = run.metrics
    cohort = run.cohort
    lines: list[str] = []
    lines.append("# Kiểm định production hậu-cutover — V1")
    lines.append("")
    lines.append(f"**STATUS: {run.status}**")
    lines.append("")
    if run.status == "WAITING_REAL_POST_CUTOVER_DATA":
        lines.append(
            f"Không có đơn nào `sale_date >= {CUTOVER_DATE.isoformat()}` trong "
            f"`{cohort.source_file}`. Đây là trạng thái vận hành mong đợi khi "
            "thời gian chưa tới, KHÔNG phải một thất bại quy trình."
        )
        lines.append("")
    lines.append("## Cohort")
    lines.append("")
    lines.append("```text")
    for key, value in cohort.as_dict().items():
        if key == "order_ids":
            value = f"{len(cohort.order_ids)} mã (xem cohort.json)"
        lines.append(f"{key:32s}: {value}")
    lines.append("```")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append("```text")
    for key in (
        "INPUT_ORDERS",
        "INPUT_LINES",
        "AUTO_ORDERS",
        "REVIEW_QUEUE_ORDERS",
        "ERROR_ORDERS",
        "PENDING_NOT_QUEUED",
        "SILENTLY_DROPPED",
        "SILENTLY_DROPPED_LINES",
    ):
        lines.append(f"{key:32s}: {m.get(key)}")
    lines.append(
        f"{'ORDER_ACCOUNTING_RATE':32s}: {_pct(m.get('ORDER_ACCOUNTING_RATE'))}"
    )
    lines.append(f"{'AUTOMATION_RATE':32s}: {_pct(m.get('AUTOMATION_RATE'))}")
    rate = m.get("SILENT_ERROR_RATE")
    lines.append(
        f"{'SILENT_ERROR_RATE':32s}: "
        + (rate if isinstance(rate, str) else _pct(rate))
    )
    lines.append(
        f"{'LINES_CHECKED_FOR_SILENT_ERRORS':32s}: "
        f"{m.get('LINES_CHECKED_FOR_SILENT_ERRORS')}"
    )
    lines.append(f"{'SILENT_ERROR_FINDINGS':32s}: {m.get('SILENT_ERROR_FINDINGS')}")
    lines.append(
        f"{'SILENT_ERROR_FINDINGS_OUTSIDE_COHORT':32s}: "
        f"{m.get('SILENT_ERROR_FINDINGS_OUTSIDE_COHORT')}"
    )
    lines.append("```")
    lines.append("")
    if cohort.sample_not_yet_50:
        lines.append(
            f"`SAMPLE_NOT_YET_50` — cohort có {cohort.unique_orders} đơn, ít hơn "
            f"{DEFAULT_COHORT_SIZE}. Mọi tỉ lệ ở trên phải đọc kèm con số này."
        )
        lines.append("")
    lines.append("## Nguồn đã đông lạnh")
    lines.append("")
    lines.append("```text")
    for key, value in run.freeze.paths.items():
        status = run.freeze.statuses.get(key, "")
        digest = run.freeze.hashes.get(key, "")
        lines.append(f"{key:32s}: {value}  [{status}]  {digest[:16]}")
    for key, value in run.freeze.as_dict()["evidence_snapshot"].items():
        lines.append(f"{key:32s}: {value}")
    lines.append("```")
    lines.append("")
    lines.append("## Silent error — phát hiện bằng cấu trúc")
    lines.append("")
    if not run.findings:
        lines.append(
            "Không có mâu thuẫn cấu trúc nào. Điều này KHÔNG chứng minh không "
            "có silent error — nó chỉ nói không loại nào máy phát hiện được. "
            "`SILENT_ERROR_RATE` vẫn phải do người kiểm chấm trên "
            "`manual_sample.csv`."
        )
    else:
        by_code: dict[str, int] = {}
        for finding in run.findings:
            by_code[finding.code] = by_code.get(finding.code, 0) + 1
        lines.append("```text")
        for code, count in sorted(by_code.items(), key=lambda kv: -kv[1]):
            lines.append(f"{code:44s}: {count}")
        lines.append("```")
        lines.append("")
        lines.append("Chi tiết đầy đủ: `silent_error_findings.json`.")
    lines.append("")
    lines.append("## Mẫu kiểm tay")
    lines.append("")
    lines.append(
        f"`manual_sample.csv` — {len(run.manual_sample)} dòng. Điền cột "
        f"`outcome` bằng đúng một trong {MANUAL_OUTCOMES}, rồi chạy lại với "
        "`--manual-verdicts <đường dẫn file đã điền>`."
    )
    lines.append("")
    lines.append("```text")
    for category in SAMPLE_CATEGORY_ORDER:
        available = run.sample_coverage.get(category, 0)
        note = "" if available else "  (cohort chưa có dòng nào thuộc nhóm này)"
        lines.append(f"{category:32s}: {available} ứng viên{note}")
    lines.append("```")
    if run.manual_summary is not None:
        lines.append("")
        lines.append("### Kết quả kiểm tay đã nạp")
        lines.append("")
        lines.append("```text")
        for key in ("MANUALLY_VALIDATED", "SILENT_ERROR", "sample_size"):
            lines.append(f"{key:32s}: {run.manual_summary[key]}")
        lines.append(
            f"{'SILENT_ERROR_RATE':32s}: "
            f"{_pct(run.manual_summary['SILENT_ERROR_RATE'])}"
        )
        lines.append(
            f"{'not_validated_rows':32s}: {run.manual_summary['not_validated_rows']}"
        )
        lines.append(
            f"{'invalid_entries':32s}: {run.manual_summary['invalid_entries']}"
        )
        lines.append("```")
    lines.append("")
    lines.append("## Giới hạn thẩm quyền của công cụ này")
    lines.append("")
    lines.append(
        "Công cụ không phân biệt được một sổ bán hàng THẬT với một fixture "
        "cùng hình dạng, nên trạng thái cao nhất nó in ra là "
        "`ELIGIBLE_FOR_PRODUCTION_ACCEPTANCE_REVIEW`. "
        "`PRODUCTION_POST_CUTOVER_ACCEPTED` là một quyết định governance, ghi "
        "ở `PROJECT/PROJECT_PROGRESS.md`, và đòi bằng chứng về tính thật của "
        "dữ liệu mà chỉ con người mới cấp được."
    )
    lines.append("")
    if run.pipeline_error:
        lines.append("## Pipeline đã raise")
        lines.append("")
        lines.append("```text")
        lines.append(run.pipeline_error)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


# ======================================================================
# 10. CLI
# ======================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_post_cutover.py",
        description=(
            "Chạy cohort đơn bán hậu-cutover qua production pipeline thật và "
            "xuất bằng chứng đủ để quyết định Production Acceptance."
        ),
    )
    parser.add_argument("--sales", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--config-dir", type=Path, default=Path("config"))
    parser.add_argument(
        "--tracking-capture", type=Path, default=TRACKING_PRICE_HISTORY_CAPTURE_PATH
    )
    parser.add_argument(
        "--tracking-catalog", type=Path, default=TRACKING_CATALOG_CAPTURE_PATH
    )
    parser.add_argument(
        "--public-purchase", type=Path, default=PUBLIC_PURCHASE_SOURCE_PATH
    )
    parser.add_argument(
        "--identity-store", type=Path, default=IDENTITY_STORE_LOG_PATH
    )
    parser.add_argument("--cohort-size", type=int, default=DEFAULT_COHORT_SIZE)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument(
        "--manual-verdicts",
        type=Path,
        default=None,
        help="manual_sample.csv đã được người kiểm điền cột outcome.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    run = analyze(
        args.sales,
        config_dir=args.config_dir,
        tracking_capture=args.tracking_capture,
        tracking_catalog=args.tracking_catalog,
        public_purchase=args.public_purchase,
        identity_store=args.identity_store,
        cohort_size=args.cohort_size,
        sample_size=args.sample_size,
    )
    run.command = " ".join(
        ["python3", "tools/analysis/validate_post_cutover.py"]
        + (argv if argv is not None else sys.argv[1:])
    )
    if args.manual_verdicts is not None:
        apply_manual_verdicts(
            run, load_manual_verdicts(args.manual_verdicts, run.manual_sample)
        )
    written = write_artifacts(run, args.output)
    print(render_summary(run))
    print("Artifact đã ghi:")
    for path in written:
        print(f"  {path}")
    return 0 if run.status not in {
        "BLOCKED_BY_SILENT_ERROR_FINDINGS",
        "BLOCKED_BY_SILENT_ERROR",
        "BLOCKED_BY_ORDER_ACCOUNTING",
        "PIPELINE_ERROR",
    } else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
