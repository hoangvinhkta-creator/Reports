"""Điểm điều phối mỏng cho luồng Owner: workbook → Demo V1 → báo cáo mới.

Module này chỉ chọn capture bất biến đã COMPLETE và gọi ``app.demo.run_demo``.
Nó không đọc dữ liệu bán hàng để tính lại, không dựng price composition và
không thay đổi capture hay workbook nguồn.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, TypeVar

from app import demo
from app.modules.pricing.daily_min.capture_file import load_daily_min_capture
from app.modules.pricing.daily_min.planning import (
    UnreadableSalesWorkbookError, plan_daily_min_request_for_workbook,
)
from app.modules.pricing.resolution.sources import (
    IDENTITY_STORE_LOG_PATH, load_tracking_catalog_capture,
    load_tracking_inv_map_capture,
)
from app.modules.product.identity.store import JsonlProductIdentityStore
from app.modules.pricing.tracking_history.capture_file import (
    load_tracking_price_history_capture,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
HISTORY_CAPTURE_DIRECTORIES = (
    Path("data/captures"),
    Path("data/tracking_price_history"),
)
CATALOG_CAPTURE_DIRECTORIES = (Path("data/tracking_catalog"),)
INV_MAP_CAPTURE_DIRECTORIES = (Path("data/tracking_inv_map"),)
DAILY_MIN_CAPTURE_DIRECTORIES = (Path("data/tracking_daily_min"),)


class OwnerUsabilityError(RuntimeError):
    """Lỗi có thể trình bày trực tiếp cho Owner, không kèm payload capture."""


@dataclass(frozen=True)
class SelectedCaptures:
    tracking_capture: Path
    tracking_catalog: Path
    tracking_inv_map: Path | None = None
    #: R1 — ảnh chụp MIN theo ngày bán. TUỲ CHỌN cùng khuôn `tracking_inv_map`:
    #: vắng mặt = "chưa nối", và mọi dòng Tracking Pending với đúng lý do ấy.
    #: KHÔNG bắt buộc vì nó phụ thuộc kỳ báo cáo (danh sách mã + khoảng ngày),
    #: nên nó không phải một capture "chụp một lần dùng mãi" như hai cái kia.
    tracking_daily_min: Path | None = None


@dataclass(frozen=True)
class OwnerRun:
    demo_run: demo.DemoRun
    captures: SelectedCaptures

    @property
    def output_path(self) -> Path:
        return self.demo_run.output_path


Snapshot = TypeVar("Snapshot")


def _capture_paths(directories: Iterable[Path]) -> tuple[Path, ...]:
    """Chỉ quét các kho capture cục bộ đã biết, không suy đoán từ tên file."""
    paths: set[Path] = set()
    for directory in directories:
        if directory.is_dir():
            paths.update(path for path in directory.rglob("*.json") if path.is_file())
    return tuple(sorted(paths))


def _latest_complete_capture(
    *,
    directories: Iterable[Path],
    loader: Callable[[Path], Snapshot | None],
    label: str,
    required: bool = True,
    accepts: Callable[[Snapshot], bool] | None = None,
) -> Path | None:
    """Trả về capture COMPLETE mới nhất theo ``captured_at`` đã được loader kiểm.

    Các file FAILED, hỏng hoặc không phải capture đúng loại đều bị loại. Không
    fallback sang file mới nhất theo tên hay mtime, vì hai thuộc tính đó không
    chứng minh được trạng thái capture.

    ``accepts`` lọc thêm theo NỘI DUNG trước khi so "mới nhất". Nó có mặt vì
    một loại capture không phải lúc nào cũng trả lời được mọi câu hỏi: ảnh chụp
    MIN theo ngày bán chỉ chứa những cặp (mã, ngày) mà lần chụp ấy đã hỏi, nên
    "mới nhất" là tiêu chí SAI cho nó — một ảnh chụp tháng 9 mới hơn ảnh chụp
    tháng 8, và hoàn toàn vô dụng khi mở lại sổ tháng 8.
    """
    candidates: list[tuple[datetime, Path]] = []
    for path in _capture_paths(directories):
        try:
            snapshot = loader(path)
            if snapshot is None:
                continue
            snapshot.require_complete()
            if accepts is not None and not accepts(snapshot):
                continue
            captured_at = snapshot.captured_at
            if captured_at.tzinfo is None or captured_at.utcoffset() is None:
                # Catalog loader cũ chỉ yêu cầu ISO-8601. Không dùng một giờ
                # không có múi giờ để tự nhận đây là "mới nhất".
                continue
            candidates.append((captured_at.astimezone(timezone.utc), path))
        except Exception:
            # Loader đã phân biệt đầy đủ hỏng/FAILED. UI chỉ cần thông báo
            # hành động, không được lộ failure_reason hay payload nguồn.
            continue
    if not candidates:
        if not required:
            return None
        locations = ", ".join(str(path) for path in directories)
        raise OwnerUsabilityError(
            f"Không có capture {label} COMPLETE hợp lệ trong {locations}. "
            "Hãy tạo capture COMPLETE mới rồi chạy lại."
        )
    return max(candidates, key=lambda candidate: (candidate[0], str(candidate[1])))[1]


def select_latest_valid_captures(
    *, repo_root: Path = REPO_ROOT, sales: Path | None = None
) -> SelectedCaptures:
    """Chọn các đầu vào Tracking hoàn chỉnh từ các kho capture cục bộ chuẩn.

    ``sales`` (R1) là workbook sắp chạy. Nó cần cho MỘT quyết định duy nhất:
    ảnh chụp MIN theo ngày bán nào trả lời được kỳ này. Ba capture kia là ảnh
    chụp của cả một nhánh dữ liệu nên "mới nhất" là tiêu chí đúng cho chúng;
    ảnh chụp MIN thì chỉ chứa những cặp (mã, ngày) mà lần chụp ấy đã hỏi, nên
    "mới nhất" là tiêu chí SAI — mở lại sổ tháng 8 sẽ vớ phải ảnh chụp tháng 9
    và mọi dòng ra ngoài cửa sổ, tức Pending hàng loạt với một lý do trỏ nhầm
    hướng.

    Không có ``sales`` thì KHÔNG chọn ảnh chụp MIN nào: không có kỳ thì không
    có tiêu chí, và chọn bừa một cái là đúng lỗi vừa mô tả.
    """
    root = Path(repo_root).expanduser().resolve()
    history = _latest_complete_capture(
        directories=tuple(root / path for path in HISTORY_CAPTURE_DIRECTORIES),
        loader=load_tracking_price_history_capture,
        label="lịch sử giá Tracking",
    )
    catalog = _latest_complete_capture(
        directories=tuple(root / path for path in CATALOG_CAPTURE_DIRECTORIES),
        loader=load_tracking_catalog_capture,
        label="danh mục Tracking",
    )
    # inv.map là authority TUỲ CHỌN (S068 follow-up): vắng mặt = chưa nối,
    # demo.run_demo vẫn chạy đúng đường alias.map/board cũ — không chặn Owner.
    inv_map = _latest_complete_capture(
        directories=tuple(root / path for path in INV_MAP_CAPTURE_DIRECTORIES),
        loader=load_tracking_inv_map_capture,
        label="inv.map Tracking",
        required=False,
    )
    # MIN theo ngày bán — TUỲ CHỌN, cùng lý do đã ghi ở `SelectedCaptures`,
    # nhưng chọn theo KỲ chứ không theo "mới nhất".
    daily_min = _select_daily_min_capture(root=root, sales=sales, catalog=catalog,
                                          inv_map=inv_map)
    return SelectedCaptures(
        tracking_capture=history, tracking_catalog=catalog, tracking_inv_map=inv_map,
        tracking_daily_min=daily_min,
    )


def _select_daily_min_capture(
    *, root: Path, sales: Path | None, catalog: Path, inv_map: Path | None
) -> Path | None:
    """Ảnh chụp MIN phủ ĐÚNG kỳ của workbook này, hoặc ``None``.

    ``None`` nghĩa là "chưa có ảnh chụp nào trả lời được kỳ này" — và nó dẫn
    tới Pending kèm lý do nguồn chưa nối, một câu đúng. Cái KHÔNG được làm là
    đưa ra một ảnh chụp của kỳ khác: khi ấy mọi dòng vẫn Pending, nhưng với lý
    do `SALE_DATE_OUTSIDE_CAPTURE`, và người đọc sẽ đi sửa nhầm chỗ.
    """
    if sales is None:
        return None
    try:
        plan = plan_daily_min_request_for_workbook(
            Path(sales),
            tracking_catalog=load_tracking_catalog_capture(catalog),
            identity_store_view=_identity_store_view(root),
            tracking_inv_map=(
                load_tracking_inv_map_capture(inv_map) if inv_map is not None else None
            ),
            tracking_identity_authority=True,
        )
    except UnreadableSalesWorkbookError:
        # Không nuốt lỗi: đường nhập sổ ngay sau đây đọc lại ĐÚNG file này và
        # sẽ báo lỗi ở nơi người dùng hiểu được. Ở đây chỉ có nghĩa là không
        # lập được kế hoạch, nên không chọn ảnh chụp nào.
        return None
    if plan is None:
        # Lần chạy này không có dòng nào mang identity Tracking, nên không có
        # câu hỏi nào để một ảnh chụp trả lời.
        return None
    return _latest_complete_capture(
        directories=tuple(root / path for path in DAILY_MIN_CAPTURE_DIRECTORIES),
        loader=load_daily_min_capture,
        label="MIN theo ngày bán của Tracking",
        required=False,
        accepts=plan.covered_by,
    )


def _identity_store_view(root: Path):
    store = JsonlProductIdentityStore(log_path=root / IDENTITY_STORE_LOG_PATH)
    return store.read_at_revision(store.current_revision())


def default_output_path(*, repo_root: Path = REPO_ROOT,
                        now: datetime | None = None) -> Path:
    """Tạo tên output mới, xác định được và không ghi đè báo cáo cũ."""
    root = Path(repo_root).expanduser().resolve()
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    output_dir = root / "outputs" / "reports"
    stem = f"report-{moment:%Y%m%dT%H%M%SZ}"
    candidate = output_dir / f"{stem}.xlsx"
    suffix = 1
    while candidate.exists():
        candidate = output_dir / f"{stem}-{suffix:02d}.xlsx"
        suffix += 1
    return candidate


def run_owner_report(*, sales: Path, repo_root: Path = REPO_ROOT,
                     now: datetime | None = None,
                     captures: SelectedCaptures | None = None) -> OwnerRun:
    """Gọi đúng Demo V1 sau khi chọn đầu vào Owner cần thấy.

    ``run_demo`` vẫn là đường production duy nhất; lớp này không truyền bất
    kỳ quyết định nghiệp vụ nào ngoài hai capture COMPLETE đã chọn.

    ``captures`` (S071): khi bên gọi đã tự chọn captures — ví dụ Reports Web
    Shared Beta pull-on-run LIVE từ Tracking thay vì đọc capture cục bộ trên
    máy Owner (``tools.tracking.live_pull``) — truyền thẳng vào đây, bỏ qua
    ``select_latest_valid_captures()``. Mặc định ``None`` giữ nguyên hành vi
    local Owner đã accepted (S068–S070): tự quét kho capture cục bộ.
    """
    sales = Path(sales).expanduser().resolve()
    if not sales.is_file() or sales.suffix.lower() != ".xlsx":
        raise OwnerUsabilityError("Hãy chọn một workbook kế toán có đuôi .xlsx.")
    if captures is None:
        captures = select_latest_valid_captures(repo_root=repo_root, sales=sales)
    output = default_output_path(repo_root=repo_root, now=now)
    output.parent.mkdir(parents=True, exist_ok=True)
    run = demo.run_demo(
        sales=sales,
        tracking_capture=captures.tracking_capture,
        tracking_catalog=captures.tracking_catalog,
        tracking_inv_map=captures.tracking_inv_map,
        tracking_daily_min=captures.tracking_daily_min,
        output=output,
    )
    if run.summary.input_orders != run.summary.accounted_orders:
        raise OwnerUsabilityError(
            "Báo cáo không đối chiếu đủ đơn hàng; không xem đây là kết quả hoàn tất."
        )
    return OwnerRun(demo_run=run, captures=captures)


def open_report_file(path: Path) -> None:
    """Mở đúng artifact vừa tạo bằng ứng dụng mặc định của macOS (S069)."""
    subprocess.run(["open", str(path)], check=False)
