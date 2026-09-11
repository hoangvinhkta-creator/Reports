"""`R7 §D` — trích SỐ ĐƠN THEO NGÀY từ sổ chi tiết bán hàng, CHỈ để vẽ.

Cùng đường vòng mà `DEC-216` đã mở cho doanh số: đọc file thô trong phiên,
xử lí trước, rồi ghi ra một nguồn KHÔNG PHẢI legacy, chỉ phục vụ việc lấp lỗ
hổng biểu đồ Số đơn (`data/chart_gapfill/daily_orders.jsonl`).

## Dữ liệu cá nhân

Công cụ đọc sổ bằng ĐÚNG `raw_reader.read_raw_rows` của pipeline (cùng cột,
cùng phép chuẩn hoá), nhưng chỉ GIỮ LẠI hai thứ của mỗi dòng: ngày bán và số
chứng từ. Tên, số điện thoại, địa chỉ khách hàng, tên hàng, tiền — đi qua bộ
nhớ tiến trình rồi bị bỏ, không được ghi ra file, không được in ra màn hình.
File kết quả chỉ có ngày và một con số đếm.

## Định nghĩa "một đơn" — MƯỢN của pipeline, không phát minh

`dashboard_metrics.order_facts` đếm một đơn theo `order_key` (số chứng từ,
nguyên văn) và xếp nó vào mốc thời gian bằng NGÀY NHỎ NHẤT trong các dòng
của đơn (`OrderFacts.bucket_date`). Công cụ này làm đúng như thế: một số
chứng từ = một đơn, dù nó có bao nhiêu dòng, và ngày của đơn là ngày sớm
nhất. Dòng không có số chứng từ đã bị `read_raw_rows` bỏ (như pipeline);
đơn không có ngày nào không rơi vào ngày nào và được báo riêng.

Cách dùng:

    python3 tools/chart_gapfill/extract_daily_orders.py \\
        --out data/chart_gapfill/daily_orders.jsonl <sổ 2025.xlsx> <sổ 2026.xlsx> ...

Nhiều sổ chồng nhau về ngày thì gộp theo TẬP số chứng từ, không cộng dồn —
một đơn có mặt ở hai file vẫn là một đơn.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.modules.importing.raw_reader import read_raw_rows  # noqa: E402


def orders_by_day(paths: list[Path]) -> tuple[dict[date, set[str]], int]:
    """`{ngày: {số chứng từ}}` gộp qua mọi sổ, và số đơn KHÔNG có ngày."""
    first_date: dict[str, date] = {}
    undated: set[str] = set()
    for path in paths:
        for row in read_raw_rows(path):
            if row.date is None:
                undated.add(row.order_id)
                continue
            seen = first_date.get(row.order_id)
            if seen is None or row.date < seen:
                first_date[row.order_id] = row.date
    by_day: dict[date, set[str]] = defaultdict(set)
    for order_id, when in first_date.items():
        by_day[when].add(order_id)
    return by_day, len(undated - set(first_date))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("workbooks", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    by_day, undated = orders_by_day(list(args.workbooks))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for when in sorted(by_day):
            handle.write(json.dumps(
                {"date": when.isoformat(), "orders": len(by_day[when])}) + "\n")
    total = sum(len(ids) for ids in by_day.values())
    print(f"{len(by_day)} ngày · {total} đơn · "
          f"{min(by_day).isoformat() if by_day else '-'} → "
          f"{max(by_day).isoformat() if by_day else '-'} · "
          f"{undated} đơn không có ngày (không ghi)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
