"""CLI mỏng: workbook kế toán → production composition → một báo cáo Excel."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Cho phép `python3 /đường/dẫn/Reports/app/demo.py` từ bất kỳ thư mục nào.
REPO_ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(REPO_ROOT))

from app.composition import run_import_production
from app.modules.exporting.excel_exporter import ReportSummary, export_report
from app.modules.importing.raw_reader import read_raw_rows
from app.modules.pricing.resolution.composition import (
    PostCutoverPriceComposition, PriceResolutionRecord,
)
from app.modules.pricing.resolution.sources import (
    IDENTITY_STORE_LOG_PATH, PriceResolutionSources,
    load_business_timezone, load_tracking_catalog_capture,
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


def run_demo(*, sales: Path, tracking_capture: Path, tracking_catalog: Path,
             output: Path) -> DemoRun:
    """Giữ nguyên kết quả và audit trail của đúng lần chạy production này.

    Production dùng đường dẫn canonical tương đối với repo. CLI đơn luồng
    chuyển thư mục trong lượt chạy và luôn khôi phục thư mục của caller.
    """
    sales, tracking_capture, tracking_catalog, output = (
        Path(path).expanduser().resolve()
        for path in (sales, tracking_capture, tracking_catalog, output)
    )
    for path in (sales, tracking_capture, tracking_catalog):
        if not path.is_file():
            raise FileNotFoundError("Không tìm thấy một tệp đầu vào đã chỉ định.")
    if sales.suffix.lower() != ".xlsx" or output.suffix.lower() != ".xlsx":
        raise ValueError("Tệp kế toán và báo cáo phải có đuôi .xlsx.")
    if output.exists() or output in (sales, tracking_capture, tracking_catalog):
        raise FileExistsError("Tệp output đã tồn tại; hãy chọn tên mới.")
    original_directory = Path.cwd()
    try:
        os.chdir(REPO_ROOT)
        store = JsonlProductIdentityStore(log_path=IDENTITY_STORE_LOG_PATH)
        sources = PriceResolutionSources(
            business_timezone=load_business_timezone(REPO_ROOT / "config"),
            tracking_price_history=load_tracking_price_history_capture(tracking_capture),
            tracking_catalog=load_tracking_catalog_capture(tracking_catalog),
            # Tắt tường minh, không đọc đường dẫn legacy rồi mới xóa dữ liệu.
            public_purchase=None,
            identity_store_view=store.read_at_revision(store.current_revision()),
        )
        composition = PostCutoverPriceComposition(sources)
        raw_rows = read_raw_rows(sales)
        result = run_import_production(sales, price_composition=composition)
        summary = export_report(
            result, composition.records, raw_rows, sales_path=sales,
            tracking_capture=tracking_capture, tracking_catalog=tracking_catalog,
            output_path=output, processed_at=datetime.now().astimezone(),
        )
        return DemoRun(result, composition.records, summary, output)
    finally:
        os.chdir(original_directory)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tạo Reports Demo V1 từ dữ liệu kế toán và capture Tracking.")
    parser.add_argument("--sales", required=True, type=Path, help="Workbook kế toán .xlsx")
    parser.add_argument("--tracking-capture", required=True, type=Path, help="Capture lịch sử giá JSON")
    parser.add_argument("--tracking-catalog", required=True, type=Path, help="Capture danh mục JSON")
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
