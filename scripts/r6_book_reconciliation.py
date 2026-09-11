"""R6 — ĐỐI SOÁT sổ kế toán thật với kết quả import/aggregate của Reports.

    .venv/bin/python scripts/r6_book_reconciliation.py --so <đường dẫn .xlsx>

Script này KHÔNG phải một test đơn vị: nó cần một file sổ kế toán thật, và
`DEC-108` cấm commit file ấy vào repo (`tests/fixtures/synthetic_workbook.py`
ghi lại lý do). Vì thế nó sống ở `scripts/`, chạy tay, và in ra bằng chứng
nguyên văn để dán vào một bản ghi task.

## Hai tầng đo, và vì sao phải có cả hai

```text
TẦNG NGUỒN     đọc thẳng .xlsx bằng CHÍNH app.modules.importing.raw_reader
TẦNG AGGREGATE chạy CHÍNH app.demo.run_demo → history_writer → PeriodData
               → dashboard_metrics.totals
```

Tầng nguồn trả lời "sổ này thật sự có bao nhiêu tiền". Tầng aggregate trả lời
"Reports nói sổ này có bao nhiêu tiền". Chỉ một trong hai là không đủ:

- chỉ tầng nguồn ⟹ chứng minh được sổ, không chứng minh được hệ thống;
- chỉ tầng aggregate ⟹ nếu importer và aggregate cùng sai theo một hướng thì
  hai con số vẫn khớp nhau và cả hai vẫn sai.

Script vì thế so BA cạnh: nguồn ↔ aggregate ↔ vector kỳ vọng của Owner.

## Cột `Lợi nhuận` của Excel KHÔNG được dùng

`OD-2`/`DEC-108` và brief R6 nói thẳng: cột đó là số của sổ tay cũ, không phải
nguồn của R6. Script này không đọc nó, và `raw_reader` giữ nó ở
`RawRow.source_profit` chỉ như bằng chứng gốc.

## "Doanh số bán" là con số DẪN XUẤT

Sổ kế toán có cột `Doanh số bán` (trước chiết khấu) và cột `Chiết khấu`.
Reports lưu `total_sales` là doanh thu SAU chiết khấu (`DEC-114`), nên phía
Reports con số "Doanh số bán" chỉ tồn tại như một phép cộng để đối soát:
`doanh thu sau CK + chiết khấu`. Xem `dashboard_metrics.GROSS_DERIVED_NOTE`.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

#: Vector kỳ vọng của sổ Owner, nguyên văn theo brief R6 (mục "Đối soát dữ
#: liệu thật"). Nó nằm ở đây như một HẰNG SỐ ĐƯỢC TRÍCH DẪN, không phải một
#: con số script tự tính: nếu một lần chạy không khớp, cái sai có thể là sổ,
#: có thể là hệ thống, và script không được phép tự quyết bên nào đúng.
OWNER_BOOK_EXPECTED = {
    "source_rows": 466,
    "orders": 345,
    "positive_revenue_orders": 338,
    "total_quantity": "626",
    "gross_before_discount": "4500085001",
    "discount_total": "1550000",
    "sales_revenue": "4498535001",
    "multi_line_orders": 85,
}

#: Nhãn người đọc của từng chỉ tiêu, để bảng in ra tự giải thích.
LABELS = {
    "source_rows": "Dòng nguồn (có Số BH)",
    "orders": "Số BH khác nhau",
    "positive_revenue_orders": "BH có doanh thu sau CK dương",
    "total_quantity": "Tổng SL",
    "gross_before_discount": "Doanh số bán (dẫn xuất)",
    "discount_total": "Chiết khấu",
    "sales_revenue": "Doanh thu sau CK",
    "multi_line_orders": "BH có ít nhất hai dòng",
}

ORDER = tuple(LABELS)


def _decimal(value) -> Decimal:
    return Decimal(0) if value is None else Decimal(value)


def source_figures(workbook: Path) -> dict:
    """Tầng NGUỒN — đọc thẳng sổ bằng chính reader của production.

    `read_raw_rows` bỏ qua dòng không có Số BH (`raw_reader` docstring), đúng
    như production; nên `source_rows` ở đây là "dòng bán", không phải "dòng
    của sheet".
    """
    from app.modules.importing.raw_reader import read_raw_rows

    rows = read_raw_rows(workbook)
    per_order: dict[str, dict] = {}
    for row in rows:
        slot = per_order.setdefault(row.order_id, {
            "lines": 0, "gross": Decimal(0), "discount": Decimal(0)})
        slot["lines"] += 1
        slot["gross"] += _decimal(row.total_sales_raw)
        slot["discount"] += _decimal(row.discount)
    gross = sum((slot["gross"] for slot in per_order.values()), Decimal(0))
    discount = sum((slot["discount"] for slot in per_order.values()), Decimal(0))
    return {
        "source_rows": len(rows),
        "orders": len(per_order),
        "positive_revenue_orders": sum(
            1 for slot in per_order.values()
            if slot["gross"] - slot["discount"] > 0),
        "total_quantity": sum((_decimal(row.quantity) for row in rows),
                              Decimal(0)),
        "gross_before_discount": gross,
        "discount_total": discount,
        "sales_revenue": gross - discount,
        "multi_line_orders": sum(1 for slot in per_order.values()
                                 if slot["lines"] >= 2),
    }


def aggregate_figures(workbook: Path, workdir: Path) -> dict:
    """Tầng AGGREGATE — chạy ĐÚNG đường production, rồi đọc `dashboard_metrics`.

    Capture Tracking để RỖNG có chủ ý: không mã nào khớp danh mục nên mọi dòng
    ra `PENDING` và không có giá nhập nào. Điều đó KHÔNG ảnh hưởng một chỉ tiêu
    nào script này đo — doanh thu, chiết khấu, số lượng, số đơn không phụ thuộc
    giá nhập — và nó giữ cho lần đối soát không cần credential hay egress nào.
    Lợi nhuận và coverage vì thế KHÔNG được đối soát ở đây, và script không in
    ra chúng để không ai đọc nhầm một số Pending thành một kết luận.
    """
    from sqlalchemy import create_engine

    import tools.db as history_db
    from app import demo
    from app.modules.reporting import dashboard_metrics
    from app.web import business_service, business_store, history_store
    from app.web import history_writer
    from tests.test_105e_price_composition import (
        write_catalog_capture, write_history_capture,
    )
    from tests.test_tracking_history_reader import build_export

    workdir.mkdir(parents=True, exist_ok=True)
    history = write_history_capture(workdir, build_export(prices={}, events={}))
    catalog = write_catalog_capture(workdir, [])
    run = demo.run_demo(sales=workbook, tracking_capture=history,
                        tracking_catalog=catalog,
                        output=workdir / "bao_cao.xlsx")

    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    repository = history_store.SnapshotRepository(engine)
    history_writer.write_run_history(
        repository, demo_run=run, run_id="doi-soat-r6",
        workbook_path=workbook, display_name=workbook.name,
        created_at="2026-01-01T00:00:00.000000")

    service = business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine),
        snapshot_repo=repository)
    # KHÔNG khoanh ngày: phạm vi của một lần đối soát là TOÀN BỘ sổ, và một
    # cận ngày gõ nhầm ở đây sẽ làm mọi con số nhỏ đi mà bảng vẫn "khớp" với
    # chính nó.
    data = service.period()
    totals = dashboard_metrics.totals(data.details)
    return {
        "source_rows": totals.lines,
        "orders": totals.orders,
        "positive_revenue_orders": totals.positive_revenue_orders,
        "total_quantity": totals.total_quantity,
        "gross_before_discount": totals.gross_before_discount,
        "discount_total": totals.discount_total,
        "sales_revenue": totals.sales_revenue,
        "multi_line_orders": totals.multi_line_orders,
    }


def compare(source: dict, aggregate: dict, expected: dict) -> tuple[list, bool]:
    """Ba cạnh: nguồn ↔ aggregate ↔ vector kỳ vọng.

    Phép so là BẰNG ĐÚNG trên `Decimal`. Một ngưỡng dung sai ở đây sẽ giấu
    đúng loại lỗi mà cả script tồn tại để bắt.
    """
    rows, ok = [], True
    for key in ORDER:
        want = expected.get(key)
        got_source = source[key]
        got_aggregate = aggregate[key]
        if isinstance(got_source, Decimal) or isinstance(got_aggregate, Decimal):
            got_source = _decimal(got_source)
            got_aggregate = _decimal(got_aggregate)
            want_value = None if want is None else Decimal(str(want))
        else:
            want_value = None if want is None else int(want)
        same_pair = got_source == got_aggregate
        same_expected = want_value is None or got_aggregate == want_value
        ok = ok and same_pair and same_expected
        rows.append({
            "key": key, "label": LABELS[key],
            "source": got_source, "aggregate": got_aggregate,
            "expected": want_value,
            "source_vs_aggregate": same_pair,
            "aggregate_vs_expected": same_expected,
        })
    return rows, ok


def render(rows: list, *, workbook: Path, checked_expected: bool) -> None:
    print(f"\nSỔ: {workbook}")
    print(f"{'Chỉ tiêu':<34}{'Nguồn':>18}{'Aggregate':>18}"
          f"{'Kỳ vọng':>18}  Kết quả")
    print("-" * 100)
    for row in rows:
        expected = "—" if row["expected"] is None else f"{row['expected']:,}"
        verdict = "OK" if (row["source_vs_aggregate"]
                           and row["aggregate_vs_expected"]) else "LỆCH"
        print(f"{row['label']:<34}{row['source']:>18,}{row['aggregate']:>18,}"
              f"{expected:>18}  {verdict}")
    print("-" * 100)
    if not checked_expected:
        print("KHÔNG có vector kỳ vọng cho sổ này — chỉ đối soát NGUỒN ↔ "
              "AGGREGATE.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--so", required=True, type=Path,
                        help="đường dẫn file sổ kế toán .xlsx")
    parser.add_argument("--ky-vong", type=Path, default=None,
                        help="file JSON vector kỳ vọng; mặc định dùng vector "
                             "của sổ Owner khi --so-cua-owner được bật")
    parser.add_argument("--so-cua-owner", action="store_true",
                        help="đối soát với vector đã freeze của sổ Owner "
                             "(466 dòng / 345 BH / 4.498.535.001 …)")
    parser.add_argument("--tmp", type=Path, default=None,
                        help="thư mục tạm cho lần chạy pipeline")
    args = parser.parse_args(argv)

    workbook = args.so.expanduser().resolve()
    if not workbook.exists():
        print(f"KHÔNG TÌM THẤY SỔ: {workbook}")
        print("Đây KHÔNG phải một lỗi của R6 — file sổ kế toán không được "
              "commit vào repo (DEC-108) và không có mặt trong môi trường này.")
        return 2

    expected = {}
    if args.ky_vong is not None:
        expected = json.loads(args.ky_vong.read_text(encoding="utf-8"))
    elif args.so_cua_owner:
        expected = OWNER_BOOK_EXPECTED

    import tempfile
    with tempfile.TemporaryDirectory() as raw_tmp:
        workdir = args.tmp or Path(raw_tmp)
        source = source_figures(workbook)
        aggregate = aggregate_figures(workbook, workdir)
    rows, ok = compare(source, aggregate, expected)
    render(rows, workbook=workbook, checked_expected=bool(expected))
    print("KẾT QUẢ ĐỐI SOÁT:", "KHỚP TOÀN BỘ" if ok else "CÓ Ô LỆCH")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
