"""`STAB-01` — đo cold/warm và ghi số đo TRƯỚC/SAU của các đường request.

Chạy (từ gốc repo):

    .venv/bin/python scripts/stab01_baseline.py --lines 5000

Vì sao là một script chứ không một test: nó là một PHÉP ĐO, không phải một
mệnh đề đúng/sai. Số nó in ra đổi theo máy, và một test khẳng định "dưới
300 ms" sẽ đỏ trên một máy CI chậm mà không có gì hỏng. Bộ số được chép
vào bàn giao làm bằng chứng, đúng cách `scripts/r51_crossrepo_smoke.py`
đang được dùng.

## Cái script này đo được, và cái nó KHÔNG đo được

ĐO ĐƯỢC — trên cùng một máy, cùng một fixture, so sánh trước/sau một thay
đổi mã: thời gian máy chủ theo thành phần (`Server-Timing`), số câu SQL,
số byte response, số hàng `<tr>` trong DOM.

KHÔNG ĐO ĐƯỢC — thời gian mạng thật, thời gian browser parse/render, và
cold open THẬT của Render. Cold open ở đây là "tiến trình Python vừa khởi
động" (`--cold`), không phải "container Render vừa được đánh thức": phần
sau gồm cả thời gian Render kéo image và mở cổng, và không mã nào trong
repo đo được nó từ bên trong. Số đo browser nằm ở `tests/browser/`.

## Vì sao SQLite chứ không PostgreSQL

Cùng lý do audit đã nói: đây là số để so TRƯỚC/SAU của một thay đổi ở tầng
UI/API, không phải một dự báo về production. Một câu SQL bớt đi là bớt đi ở
cả hai database; một megabyte HTML bớt đi là bớt đi ở cả hai. Ngưỡng p95
production phải đo trên production.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from sqlalchemy import create_engine  # noqa: E402

import tools.db as history_db  # noqa: E402
from app.web import history_store  # noqa: E402
from app.web import server as web_server  # noqa: E402
from tools.tracking import live_pull  # noqa: E402
from tests.fixtures import workspace_scale as ws  # noqa: E402

#: Các đường request được đo. `(tên, đường dẫn, có gửi header fragment)`.
#: `sua=` mở chế độ sửa một đơn — đúng thao tác mà brief gọi là "mở/sửa đơn".
def routes(order_key: str) -> list[tuple[str, str, bool]]:
    period = ws.PERIOD_TEXT
    return [
        ("tong-hop-full", f"/kinh-doanh?ky={period}", False),
        ("tong-hop-fragment", f"/kinh-doanh?ky={period}", True),
        ("nhan-vien-full", f"/kinh-doanh/nhan-vien?ky={period}", False),
        ("nhan-vien-fragment", f"/kinh-doanh/nhan-vien?ky={period}", True),
        ("mo-sua-don-fragment",
         f"/kinh-doanh/nhan-vien?ky={period}&sua={order_key}", True),
        ("api-order-detail",
         f"/api/v1/orders/{order_key}?period={period}", False),
    ]


def build_client(engine, *, today=None):
    """App THẬT, không mock tầng nghiệp vụ nào — chỉ cắt mạng ngoài.

    `select_latest_valid_captures`/`live_pull.is_configured` bị cắt vì
    chúng đi ra Tracking/đĩa Owner. Cắt chúng làm số đo BỚT đi phần mạng
    ngoài, và điều đó được nói ra ở đây thay vì để người đọc số tự đoán.
    """
    import datetime

    web_server.select_latest_valid_captures = lambda: None
    live_pull.is_configured = lambda env=None: False
    web_server._today = lambda: datetime.date(2026, 9, 30)
    app = web_server.create_app(
        db_path=Path("/tmp/stab01-runs.db"),
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    app.testing = True
    return app.test_client()


def parse_server_timing(header: str) -> dict:
    """`Server-Timing` → `{tên: (ms, n)}`."""
    out: dict[str, tuple[float, int]] = {}
    for part in (header or "").split(","):
        part = part.strip()
        if not part:
            continue
        name = part.split(";")[0].strip()
        dur = re.search(r"dur=([0-9.]+)", part)
        n = re.search(r'desc="n=(\d+)"', part)
        out[name] = (float(dur.group(1)) if dur else 0.0,
                     int(n.group(1)) if n else 0)
    return out


def measure(client, path: str, *, fragment: bool, repeat: int) -> dict:
    """`repeat` lần gọi cùng một đường; trả p50/p95 + số của lần cuối."""
    headers = {"X-Fragment": "1"} if fragment else {}
    times: list[float] = []
    last = None
    for _ in range(repeat):
        started = time.perf_counter()
        response = client.get(path, headers=headers)
        times.append((time.perf_counter() - started) * 1000)
        last = response
    body = last.get_data()
    timing = parse_server_timing(last.headers.get("Server-Timing", ""))
    return {
        "status": last.status_code,
        "p50_ms": round(statistics.median(times), 1),
        "p95_ms": round(_p95(times), 1),
        "bytes": len(body),
        "tr_rows": body.count(b"<tr"),
        "sql_n": timing.get("sql", (0.0, 0))[1],
        "sql_ms": round(timing.get("sql", (0.0, 0))[0], 1),
        "r2_ms": round(timing.get("r2", (0.0, 0))[0], 1),
        "tracking_ms": round(timing.get("tracking", (0.0, 0))[0], 1),
        "presentation_ms": round(timing.get("presentation", (0.0, 0))[0], 1),
        "template_ms": round(timing.get("template", (0.0, 0))[0], 1),
        "request_id": last.headers.get("X-Request-Id", "-"),
        "app_content_count": body.count(b'id="app-content"'),
    }


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lines", type=int, default=5000,
                        help="số dòng của fixture (100 / 3000 / 5000)")
    parser.add_argument("--repeat", type=int, default=5,
                        help="số lần gọi mỗi đường (warm)")
    parser.add_argument("--json", type=Path, default=None,
                        help="ghi kết quả ra file JSON để so trước/sau")
    args = parser.parse_args(argv)

    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    repo = history_store.SnapshotRepository(engine)
    print(f"Dựng fixture {args.lines} dòng…", flush=True)
    built = time.perf_counter()
    pairs = ws.install(repo, args.lines)
    orders = ws.order_keys(pairs)
    print(f"  {len(pairs)} dòng · {len(orders)} đơn · "
          f"{(time.perf_counter() - built):.1f}s")

    client = build_client(engine)
    target_order = orders[len(orders) // 2]

    results = {"lines": args.lines, "orders": len(orders),
               "order_key": target_order, "repeat": args.repeat, "routes": {}}

    # COLD = lần gọi ĐẦU TIÊN của tiến trình này trên đường đó. Nó gánh
    # phần khởi tạo lười (nạp YAML cấu hình, dựng router tỉ lệ, cache của
    # Jinja compile template) mà mọi lần sau không gánh lại.
    print("\nCOLD (lần gọi đầu tiên của tiến trình, repeat=1)")
    print(f"  {'đường':<26} {'ms':>8} {'bytes':>10} {'sql':>5} {'main':>5}")
    for name, path, fragment in routes(target_order):
        row = measure(client, path, fragment=fragment, repeat=1)
        results["routes"].setdefault(name, {})["cold"] = row
        print(f"  {name:<26} {row['p50_ms']:>8.1f} {row['bytes']:>10} "
              f"{row['sql_n']:>5} {row['app_content_count']:>5}")

    print(f"\nWARM (p50/p95 trên {args.repeat} lần)")
    print(f"  {'đường':<26} {'p50':>8} {'p95':>8} {'bytes':>10} {'<tr>':>7} "
          f"{'sql':>5} {'sql_ms':>7} {'pres':>7} {'tpl':>7} {'main':>5}")
    for name, path, fragment in routes(target_order):
        row = measure(client, path, fragment=fragment, repeat=args.repeat)
        results["routes"].setdefault(name, {})["warm"] = row
        print(f"  {name:<26} {row['p50_ms']:>8.1f} {row['p95_ms']:>8.1f} "
              f"{row['bytes']:>10} {row['tr_rows']:>7} {row['sql_n']:>5} "
              f"{row['sql_ms']:>7.1f} {row['presentation_ms']:>7.1f} "
              f"{row['template_ms']:>7.1f} {row['app_content_count']:>5}")

    print("\nGhi chú đọc số:")
    print("  main = số lần chuỗi id=\"app-content\" xuất hiện. Fragment phải")
    print("         là 0 (STAB-04); full page phải là 1.")
    print("  <tr> = số hàng bảng trong response. Đây là con số ngân sách")
    print("         \"không quá 200–300 row trong DOM\" nói về.")
    print("  status khác 200 ⟹ đường đó CHƯA tồn tại ở bản đang đo.")

    if args.json:
        args.json.write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"\nĐã ghi {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
