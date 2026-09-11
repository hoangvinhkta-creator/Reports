"""CLI mỏng: workbook kế toán → production composition → một báo cáo Excel."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Cho phép `python3 /đường/dẫn/Reports/app/demo.py` từ bất kỳ thư mục nào.
REPO_ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(REPO_ROOT))

from app.composition import run_import_production
from app.modules.exporting.excel_exporter import ReportSummary, export_report, present_lines
from app.modules.importing.raw_reader import read_raw_rows
from app.modules.pricing.daily_min.capture_file import load_daily_min_capture
from app.modules.pricing.resolution.composition import (
    PostCutoverPriceComposition, PriceResolutionRecord,
)
from app.modules.pricing.resolution.sources import (
    IDENTITY_STORE_LOG_PATH, PriceResolutionSources,
    load_business_timezone, load_tracking_catalog_capture,
    load_tracking_inv_map_capture,
)
from app.modules.pricing.tracking_history.capture_file import load_tracking_price_history_capture
from app.modules.product.identity.store import JsonlProductIdentityStore
from app.pipeline import ImportResult


@dataclass(frozen=True)
class DemoRun:
    result: ImportResult
    price_records: tuple[PriceResolutionRecord, ...]
    summary: ReportSummary
    output_path: Path
    # Đã tính trong lượt chạy này; trả ra để tầng lưu lịch sử khỏi tính lại.
    raw_rows: tuple = ()
    presented_lines: tuple = ()


def run_demo(*, sales: Path, tracking_catalog: Path, output: Path,
             tracking_capture: Optional[Path] = None,
             tracking_inv_map: Optional[Path] = None,
             tracking_daily_min: Optional[Path] = None,
             identity_store_view=None) -> DemoRun:
    """Giữ nguyên kết quả và audit trail của đúng lần chạy production này.

    Production dùng đường dẫn canonical tương đối với repo. CLI đơn luồng
    chuyển thư mục trong lượt chạy và luôn khôi phục thư mục của caller.

    `tracking_inv_map` TUỲ CHỌN (S068 follow-up): vắng mặt = "chưa nối",
    resolver vẫn chạy đúng đường `alias.map`/`board` cũ — cùng khuôn
    `public_purchase=None` tường minh ngay dưới đây.

    `tracking_daily_min` (R1) là ảnh chụp MIN theo NGÀY BÁN — nguồn giá nhập
    tự động hiện hành. Cũng TUỲ CHỌN, và vắng mặt cũng có nghĩa "chưa nối":
    mọi dòng Tracking sẽ Pending với `TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE`
    thay vì mượn một nguồn giá khác.

    `tracking_capture` (lịch sử `board/<mã>/tp/ton`) trở thành TUỲ CHỌN kể từ
    lượt review vòng 2. Từ R1 nó KHÔNG còn quyết định giá nào — nhánh của một
    mã Tracking đi qua `_daily_min_branch`, và đường lịch sử chỉ chạy khi
    caller nêu rõ `legacy_tracking_history_authority=True`. Nó vẫn được nạp và
    vẫn vào bằng chứng khi CÓ mặt (để đối chiếu kết quả sinh trước R1), nhưng
    bắt nó phải có mặt là bắt báo cáo hôm nay phụ thuộc vào một nguồn hôm nay
    không dùng. Xem `composition.py` và `ADR-110` §6.

    `identity_store_view` (R2) là ảnh chụp ĐÃ ĐÓNG BĂNG của log quyết định
    Product Identity. Bên gọi đọc nó MỘT lần rồi truyền vào cả đây lẫn bước
    lập kế hoạch hỏi giá, để kế hoạch và phép phân giải nhìn cùng một trạng
    thái — hai lần đọc ở hai thời điểm có thể lệch nhau đúng một xác nhận, và
    khi ấy mã được hỏi giá không trùng với mã được phân giải.

    `None` giữ nguyên hành vi cũ: đọc log cục bộ dưới `data/product_identity/`.
    Đó là nhánh ĐÚNG trên máy Owner và trong test. Trên bản Web nó SAI —
    filesystem của container là ephemeral và log thật nằm ở R2 — nên
    `app/web/server.py` luôn truyền view vào, và `identity_gateway.build_store`
    là chỗ duy nhất quyết định log thật nằm ở đâu.
    """
    paths_to_resolve = [sales, tracking_catalog, output]
    optional_paths = [tracking_capture, tracking_inv_map, tracking_daily_min]
    paths_to_resolve += [p for p in optional_paths if p is not None]
    resolved = [Path(p).expanduser().resolve() for p in paths_to_resolve]
    sales, tracking_catalog, output = resolved[:3]
    extra = iter(resolved[3:])
    tracking_capture = next(extra) if tracking_capture is not None else None
    tracking_inv_map = next(extra) if tracking_inv_map is not None else None
    tracking_daily_min = next(extra) if tracking_daily_min is not None else None

    required_inputs = [sales, tracking_catalog]
    if tracking_capture is not None:
        required_inputs.append(tracking_capture)
    if tracking_inv_map is not None:
        required_inputs.append(tracking_inv_map)
    if tracking_daily_min is not None:
        required_inputs.append(tracking_daily_min)
    for path in required_inputs:
        if not path.is_file():
            raise FileNotFoundError("Không tìm thấy một tệp đầu vào đã chỉ định.")
    if sales.suffix.lower() != ".xlsx" or output.suffix.lower() != ".xlsx":
        raise ValueError("Tệp kế toán và báo cáo phải có đuôi .xlsx.")
    if output.exists() or output in required_inputs:
        raise FileExistsError("Tệp output đã tồn tại; hãy chọn tên mới.")
    original_directory = Path.cwd()
    try:
        os.chdir(REPO_ROOT)
        view = identity_store_view
        if view is None:
            store = JsonlProductIdentityStore(log_path=IDENTITY_STORE_LOG_PATH)
            view = store.read_at_revision(store.current_revision())
        sources = PriceResolutionSources(
            business_timezone=load_business_timezone(REPO_ROOT / "config"),
            tracking_price_history=(
                load_tracking_price_history_capture(tracking_capture)
                if tracking_capture is not None
                else None
            ),
            tracking_catalog=load_tracking_catalog_capture(tracking_catalog),
            tracking_inv_map=(
                load_tracking_inv_map_capture(tracking_inv_map)
                if tracking_inv_map is not None
                else None
            ),
            tracking_daily_min=(
                load_daily_min_capture(tracking_daily_min)
                if tracking_daily_min is not None
                else None
            ),
            # Tắt tường minh, không đọc đường dẫn legacy rồi mới xóa dữ liệu.
            public_purchase=None,
            identity_store_view=view,
        )
        composition = PostCutoverPriceComposition(sources)
        raw_rows = read_raw_rows(sales)
        result = run_import_production(sales, price_composition=composition)
        summary = export_report(
            result, composition.records, raw_rows, sales_path=sales,
            tracking_capture=tracking_capture, tracking_catalog=tracking_catalog,
            output_path=output, processed_at=datetime.now().astimezone(),
        )
        return DemoRun(result, composition.records, summary, output,
                       tuple(raw_rows), tuple(present_lines(
                           result, composition.records, raw_rows)))
    finally:
        os.chdir(original_directory)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tạo Reports Demo V1 từ dữ liệu kế toán và capture Tracking.")
    parser.add_argument("--sales", required=True, type=Path, help="Workbook kế toán .xlsx")
    parser.add_argument("--tracking-capture", required=True, type=Path, help="Capture lịch sử giá JSON")
    parser.add_argument("--tracking-catalog", required=True, type=Path, help="Capture danh mục JSON")
    parser.add_argument(
        "--tracking-inv-map", required=False, default=None, type=Path,
        help="Capture inv.map JSON (TUỲ CHỌN — S068 follow-up; vắng mặt = chưa nối)",
    )
    parser.add_argument(
        "--tracking-daily-min", required=False, default=None, type=Path,
        help=(
            "Capture MIN theo ngày bán JSON, hợp đồng daily-min-v1 (R1). Đây là "
            "NGUỒN GIÁ NHẬP TỰ ĐỘNG; vắng mặt = chưa nối, và mọi dòng Tracking "
            "sẽ chờ giá thay vì mượn một nguồn giá khác. Tạo bằng "
            "tools/tracking/capture_daily_min.py"
        ),
    )
    parser.add_argument("--output", required=True, type=Path, help="Báo cáo .xlsx mới, không ghi đè")
    args = parser.parse_args(argv)
    try:
        run = run_demo(**vars(args))
    except Exception as exc:
        # Lỗi loader có thể chứa nguyên payload; không in payload/traceback.
        print(f"DEMO_FAILED\nERROR={type(exc).__name__}\n"
              "Kiểm tra tệp đầu vào, cấu trúc capture và chọn output chưa tồn tại. "
              "Không có báo cáo hoàn tất.", file=sys.stderr)
        return 1
    print("DEMO_COMPLETE")
    print(f"OUTPUT={run.output_path}")
    print(f"ORDERS={run.summary.input_orders}")
    print(f"AUTO={run.summary.auto_orders}")
    print(f"REVIEW_QUEUE={run.summary.review_orders}")
    print(f"ORDER_ACCOUNTING_RATE={run.summary.order_accounting_rate:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
