"""`STAB-01`/`UI-01`/`UI-02` — đo cold/warm và ghi số đo TRƯỚC/SAU của các
đường request, KỂ CẢ panel sửa đơn tại chỗ (`GET`/`PATCH` của
`/api/v1/orders/<order_key>`).

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
động", không phải "container Render vừa được đánh thức": phần sau gồm cả
thời gian Render kéo image và mở cổng, và không mã nào trong repo đo được
nó từ bên trong.

`tests/browser/` kiểm HÀNH VI của `app.js` trên một DOM thật (jsdom) —
response nào vào DOM, response cũ có ghi đè response mới không.
`tests/playwright/` (`UI-01`/`UI-02`) đo được thứ jsdom KHÔNG đo được —
`<dialog>.showModal()` có bẫy focus thật không, vị trí cuộn thật — nhưng nó
cũng KHÔNG in ra một con số p50/p95 nào để chép vào bàn giao; đó là việc
của CHÍNH FILE NÀY. Nên mọi con số ở đây vẫn là THỜI GIAN MÁY CHỦ và SỐ
BYTE, không phải tốc độ vẽ/parse của trình duyệt — kể cả các dòng
`panel-*`/`patch-*` bên dưới.

## `mo-panel` là gì, và vì sao nó CHÍNH LÀ `api-order-detail`

`UI-01` mở panel bằng CHÍNH MỘT lượt `GET /api/v1/orders/<order_key>` —
không có route server nào khác cho "mở panel". Không có một con số "mở
panel" tách biệt để đo ở tầng server: phần server của việc mở panel VÀ của
việc gọi API chi tiết đơn là CÙNG MỘT request. Bảng WARM bên dưới vì vậy
in hai tên (`api-order-detail`, và `panel-open` là bí danh của đúng route
đó) để đọc số không phải đi tra chú thích.

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
import uuid as uuid_module
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
#: `sua=` mở chế độ sửa một đơn kiểu CŨ (`?sua=`, fallback không-JS của
#: `UI-01` — có JS thì đường này không còn được gọi để mở panel nữa, panel
#: gọi `api-order-detail`/`panel-open` bên dưới thay vào đó). Giữ lại phép
#: đo này để thấy rõ CHÊNH LỆCH mà `UI-01` tạo ra: `mo-sua-don-fragment`
#: dựng lại CẢ bảng kê, còn `panel-open` chỉ trả JSON của một đơn.
def routes(order_key: str) -> list[tuple[str, str, bool]]:
    period = ws.PERIOD_TEXT
    return [
        ("tong-hop-full", f"/kinh-doanh?ky={period}", False),
        ("tong-hop-fragment", f"/kinh-doanh?ky={period}", True),
        ("nhan-vien-full", f"/kinh-doanh/nhan-vien?ky={period}", False),
        ("nhan-vien-fragment", f"/kinh-doanh/nhan-vien?ky={period}", True),
        ("mo-sua-don-fragment (CŨ, fallback không-JS)",
         f"/kinh-doanh/nhan-vien?ky={period}&sua={order_key}", True),
        ("api-order-detail (= panel-open, UI-01/UI-02)",
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


def measure_patch_sequence(client, *, order_key: str, period: str,
                           sheet: str, n: int) -> dict:
    """`n` lượt `PATCH` LIÊN TIẾP, THẬT — mỗi lượt một quyết định MỚI.

    Đây là "20 thao tác liên tiếp" của brief §7: một mã chống lặp MỚI mỗi
    lượt (`idempotency_key` khác nhau — nếu không, lượt thứ hai trở đi chỉ
    còn đo đường THỬ LẠI/replay của `mutation_guard`, không đo một lần ghi
    thật), và `base_revision` LẤY TỪ response của lượt TRƯỚC — đúng cách
    panel thật làm (`app.js`, `applySuccess()`): revision đọc lại sau mỗi
    lần ghi, không tính nhẩm.

    Giá được gõ LUÂN PHIÊN giữa hai giá trị, để mỗi lượt là một thay đổi
    THẬT (server bỏ qua ô không đổi — `plan_order_edit`) chứ không phải
    `n` lượt "ghi lại đúng giá cũ" mà `changes_nothing` sẽ làm số đo lạc
    quan giả tạo.
    """
    detail = client.get(
        f"/api/v1/orders/{order_key}?period={period}").get_json()
    line = detail["lines"][0]
    revision = detail["order_revision"]
    times: list[float] = []
    last = None
    base_value = int(line["purchase_price"]["value"] or 0) or 600_000
    for i in range(n):
        value = str(base_value + (i % 2) * 1_000)
        body = {
            "idempotency_key": str(uuid_module.uuid4()),
            "base_revision": revision,
            "changes": {
                "prices": [{
                    "product_key": line["product_key"],
                    "occurrence_index": line["occurrence_index"],
                    "value": value,
                }],
            },
            "reason": "stab01_baseline — đo tuần tự",
        }
        started = time.perf_counter()
        response = client.patch(
            f"/api/v1/orders/{order_key}?period={period}&sheet={sheet}",
            json=body)
        times.append((time.perf_counter() - started) * 1000)
        last = response
        payload = response.get_json() or {}
        revision = payload.get("order_revision", revision)
    body_bytes = last.get_data() if last is not None else b""
    return {
        "n": n,
        "status": last.status_code if last is not None else None,
        "p50_ms": round(statistics.median(times), 1) if times else 0.0,
        "p95_ms": round(_p95(times), 1) if times else 0.0,
        "min_ms": round(min(times), 1) if times else 0.0,
        "max_ms": round(max(times), 1) if times else 0.0,
        "bytes_last": len(body_bytes),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lines", type=int, default=5000,
                        help="số dòng của fixture (100 / 3000 / 5000)")
    parser.add_argument("--repeat", type=int, default=5,
                        help="số lần gọi mỗi đường (warm)")
    parser.add_argument("--json", type=Path, default=None,
                        help="ghi kết quả ra file JSON để so trước/sau")
    parser.add_argument("--patch-ops", type=int, default=20,
                        help="số lượt PATCH liên tiếp đo ở cuối (mặc định "
                        "20, đúng brief §7 'hai mươi thao tác liên tiếp')")
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

    # `UI-02` §7 — PATCH: một lượt LẺ (cold, gánh khởi tạo lười nếu route
    # này chưa được gọi lượt nào ở trên) rồi `--patch-ops` lượt LIÊN TIẾP
    # (mặc định 20, "hai mươi thao tác liên tiếp" của brief), mỗi lượt một
    # `idempotency_key`/`base_revision` MỚI — xem docstring
    # `measure_patch_sequence`. Sheet cố định `noi-thanh`: mọi đơn của
    # `workspace_scale` đều mang `employee_group=NOI_THANH`.
    sheet = "noi-thanh"
    print(f"\nPATCH (đơn {target_order}, sheet={sheet}) — MÁY LOCAL/TEST, "
          "KHÔNG PHẢI SỐ PRODUCTION (xem docstring đầu file)")
    single = measure_patch_sequence(
        client, order_key=target_order, period=ws.PERIOD_TEXT, sheet=sheet, n=1)
    results["patch_single"] = single
    print(f"  1 lượt (cold)      status={single['status']} "
          f"{single['p50_ms']:>8.1f} ms  {single['bytes_last']:>8} bytes")
    sequence = measure_patch_sequence(
        client, order_key=target_order, period=ws.PERIOD_TEXT, sheet=sheet,
        n=args.patch_ops)
    results["patch_sequence"] = sequence
    print(f"  {sequence['n']} lượt liên tiếp  status={sequence['status']} "
          f"p50={sequence['p50_ms']:>7.1f} ms  p95={sequence['p95_ms']:>7.1f} ms "
          f"min={sequence['min_ms']:>7.1f}  max={sequence['max_ms']:>7.1f} "
          f"bytes_lượt_cuối={sequence['bytes_last']}")
    print("  Đây là thời gian MÁY CHỦ mỗi lượt PATCH thật (ghi thật, không")
    print("  replay) — không phải thời gian người dùng chờ trên trình duyệt;")
    print("  phần đó cần Playwright + mạng thật, xem `tests/playwright/`.")

    if args.json:
        args.json.write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"\nĐã ghi {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
