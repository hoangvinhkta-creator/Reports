"""Điểm điều phối mỏng cho luồng Owner: workbook → Demo V1 → báo cáo mới.

Module này chỉ chọn capture bất biến đã COMPLETE và gọi ``app.demo.run_demo``.
Nó không đọc dữ liệu bán hàng để tính lại, không dựng price composition và
không thay đổi capture hay workbook nguồn.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, TypeVar

from app import demo
from app.modules.pricing.resolution.sources import load_tracking_catalog_capture
from app.modules.pricing.tracking_history.capture_file import (
    load_tracking_price_history_capture,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
HISTORY_CAPTURE_DIRECTORIES = (
    Path("data/captures"),
    Path("data/tracking_price_history"),
)
CATALOG_CAPTURE_DIRECTORIES = (Path("data/tracking_catalog"),)


class OwnerUsabilityError(RuntimeError):
    """Lỗi có thể trình bày trực tiếp cho Owner, không kèm payload capture."""


@dataclass(frozen=True)
class SelectedCaptures:
    tracking_capture: Path
    tracking_catalog: Path


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
) -> Path:
    """Trả về capture COMPLETE mới nhất theo ``captured_at`` đã được loader kiểm.

    Các file FAILED, hỏng hoặc không phải capture đúng loại đều bị loại. Không
    fallback sang file mới nhất theo tên hay mtime, vì hai thuộc tính đó không
    chứng minh được trạng thái capture.
    """
    candidates: list[tuple[datetime, Path]] = []
    for path in _capture_paths(directories):
        try:
            snapshot = loader(path)
            if snapshot is None:
                continue
            snapshot.require_complete()
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
        locations = ", ".join(str(path) for path in directories)
        raise OwnerUsabilityError(
            f"Không có capture {label} COMPLETE hợp lệ trong {locations}. "
            "Hãy tạo capture COMPLETE mới rồi chạy lại."
        )
    return max(candidates, key=lambda candidate: (candidate[0], str(candidate[1])))[1]


def select_latest_valid_captures(*, repo_root: Path = REPO_ROOT) -> SelectedCaptures:
    """Chọn hai đầu vào Tracking hoàn chỉnh mới nhất từ các kho cục bộ chuẩn."""
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
    return SelectedCaptures(tracking_capture=history, tracking_catalog=catalog)


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
                     now: datetime | None = None) -> OwnerRun:
    """Gọi đúng Demo V1 sau khi chọn đầu vào Owner cần thấy.

    ``run_demo`` vẫn là đường production duy nhất; lớp này không truyền bất
    kỳ quyết định nghiệp vụ nào ngoài hai capture COMPLETE đã chọn.
    """
    sales = Path(sales).expanduser().resolve()
    if not sales.is_file() or sales.suffix.lower() != ".xlsx":
        raise OwnerUsabilityError("Hãy chọn một workbook kế toán có đuôi .xlsx.")
    captures = select_latest_valid_captures(repo_root=repo_root)
    output = default_output_path(repo_root=repo_root, now=now)
    output.parent.mkdir(parents=True, exist_ok=True)
    run = demo.run_demo(
        sales=sales,
        tracking_capture=captures.tracking_capture,
        tracking_catalog=captures.tracking_catalog,
        output=output,
    )
    if run.summary.input_orders != run.summary.accounted_orders:
        raise OwnerUsabilityError(
            "Báo cáo không đối chiếu đủ đơn hàng; không xem đây là kết quả hoàn tất."
        )
    return OwnerRun(demo_run=run, captures=captures)
