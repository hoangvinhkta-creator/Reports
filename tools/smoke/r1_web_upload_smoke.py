"""SMOKE R1 — ĐÚNG ĐƯỜNG NGƯỜI DÙNG: upload workbook lên web → báo cáo có giá.

## Vì sao cần smoke NÀY khi đã có `r1_daily_min_smoke.py`

Smoke kia NHẬN sẵn một ảnh chụp MIN rồi chạy composition. Nó chứng minh
provider và price resolution đúng — và nó xanh rực kể cả khi `app/web/server.py`
không hề gọi hợp đồng `daily-min-v1`, tức khi mọi dòng Tracking Pending và báo
cáo vẫn được tạo ra trông hoàn chỉnh. Đó chính là lỗi đã lọt qua R1 vòng đầu:
mọi bài kiểm xanh, đường thật thì đứt.

Smoke này đi qua đúng chỗ Owner bấm nút:

```text
POST /run (Flask thật)
  → _select_captures_for_run(sales=workbook)
  → live_pull.pull_live_captures  ── HTTP thật ──►  máy chủ cục bộ
  → kế hoạch hỏi giá (đọc sổ, resolve identity, gom mã + khoảng ngày)
  → tools/tracking/capture_daily_min (urllib thật, header X-Report-Key thật)
  → run_owner_report → run_demo → pipeline → xuất Excel
  → mở file .xlsx và ĐỌC con số
```

Máy chủ cục bộ trả lời `/api/min-ngay` bằng cách gọi **chính mã Tracking**
(`node kiem/smoke/tra-loi-min-ngay.mjs`), nên `query_revision`, vân tay, thứ tự
nguồn và mọi tên trường đều do hệ thống thật sinh ra. Bốn node GET còn lại
(`purchase_price_baseline`, `purchase_price_history`, `board`, `alias`,
`inv_map`) được phục vụ bằng payload tổng hợp: chúng không phải chủ đề của R1,
và mỗi node đã có bộ kiểm riêng.

Lịch sử `tp/ton` cũ CỐ Ý có giá 4.444 nghìn cho đúng những mã ấy: nhánh nào rơi
về nguồn cũ sẽ ra 4.444.000 thay vì 6.800.000. Và ảnh chụp CÓ giá ngày 30/09
(5.200) lẫn 04/09 (6.000), nên một nhánh lấy "bản mới nhất" cũng lộ ra ngay.

## Chạy

```bash
python tools/smoke/r1_web_upload_smoke.py [--tracking-repo /đường/dẫn/Tracking]
```

Thoát 0 nếu mọi khẳng định PASS, 1 nếu có mục FAIL. Cần `node` trên PATH.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tempfile
import threading
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import openpyxl  # noqa: E402

SALE_DAY = date(2026, 9, 3)
GIA_NGAY_BAN = 6_800_000        # MIN của 03/09, đơn vị VND sau quy đổi
GIA_NGAY_KHAC = 6_000_000       # MIN của 04/09 — KHÔNG được dùng
GIA_HIEN_TAI = 5_200_000        # MIN của 30/09 — KHÔNG được dùng
GIA_LICH_SU_CU = 4_444_000      # `tp/ton` — KHÔNG được dùng

MA = ["TRK-A", "TRK-B", "TRK-C", "TRK-D", "TRK-E"]
ROWS = [
    ("BH7001", "TRK-A", 1, 9_000_000),
    ("BH7002", "TRK-B", 2, 7_000_000),
    ("BH7003", "TRK-C", 1, 8_000_000),
]

_ok = True


def kiem(nhan: str, dieu_kien: bool) -> None:
    global _ok
    _ok = _ok and bool(dieu_kien)
    print(("  PASS  " if dieu_kien else "  FAIL  ") + nhan)


# ---------------------------------------------------------------------------
# Tracking cục bộ — GET tổng hợp, POST /api/min-ngay do mã Tracking thật trả
# ---------------------------------------------------------------------------


def get_payload(node: str) -> dict:
    """Bốn node GET của Data Contract V1, đủ để identity resolve được."""
    if node == "board":
        # `name` phải có: identity khớp tên hàng trên chứng từ với danh mục.
        return {ma: {"name": ma, "tp": {"ton": GIA_LICH_SU_CU // 1000}} for ma in MA}
    if node == "alias":
        # Hình dạng `{"map": {...}}` là hợp đồng đã audit (DEC-147 §4); trả
        # `{}` trần thì công cụ chụp DỪNG thay vì đoán một bảng alias rỗng.
        return {"map": {}}
    if node == "inv_map":
        return {}
    if node == "purchase_price_baseline":
        return {ma: {"gia": GIA_LICH_SU_CU // 1000, "t": 1756000000000} for ma in MA}
    if node == "purchase_price_history":
        return {
            ma: {f"h{i}": {"gia": GIA_LICH_SU_CU // 1000, "t": 1756000000000}}
            for i, ma in enumerate(MA)
        }
    raise KeyError(node)


def make_handler(tracking_repo: Path, calls: list):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # im lặng — smoke tự in bảng của nó
            pass

        def _json(self, payload, status=200):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _key_ok(self) -> bool:
            return self.headers.get("X-Report-Key") == "khoa-smoke"

        def do_GET(self):  # noqa: N802
            if not self._key_ok():
                return self._json({"ok": False, "ly": "thieu-khoa"}, 403)
            node = self.path.rsplit("/", 1)[-1]
            try:
                self._json(get_payload(node))
            except KeyError:
                self._json({"ok": False, "ly": "node-la"}, 404)

        def do_POST(self):  # noqa: N802
            if not self._key_ok():
                return self._json({"ok": False, "ly": "thieu-khoa"}, 403)
            raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            calls.append(json.loads(raw.decode("utf-8")))
            # ĐÂY là chỗ mã Tracking thật trả lời.
            out = subprocess.run(
                ["node", "kiem/smoke/tra-loi-min-ngay.mjs"],
                input=raw, cwd=str(tracking_repo),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            )
            body = out.stdout
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


# ---------------------------------------------------------------------------


def write_sales(path: Path, rows, day: date) -> Path:
    from tests.fixtures.synthetic_workbook import HEADER

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "SỔ CHI TIẾT BÁN HÀNG"
    sheet.append(["SỔ CHI TIẾT BÁN HÀNG"])
    sheet.append(["Từ ngày 01/09/2026 đến ngày 30/09/2026"])
    sheet.append([])
    sheet.append(HEADER)
    sheet.append(["", "", "Diễn giải chung"])
    for order_id, product, quantity, sell in rows:
        sheet.append([
            day, order_id, f"Bán hàng {order_id}", product, f"KH{order_id}",
            f"Khách {order_id}", "1 Đường Test", "0900000000", quantity, sell,
            sell * quantity, 0, "Vũ Hạnh Ly 0868345633", "Shipper", 0, None, None,
        ])
        sheet.cell(sheet.max_row, 4).data_type = "s"
    book.save(path)
    book.close()
    return path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracking-repo", type=Path,
                        default=REPO_ROOT.parent / "Tracking")
    args = parser.parse_args(argv[1:])
    if not (args.tracking_repo / "kiem/smoke/tra-loi-min-ngay.mjs").is_file():
        print(f"Không thấy repo Tracking ở {args.tracking_repo}", file=sys.stderr)
        return 2

    calls: list = []
    server = HTTPServer(("127.0.0.1", 0), make_handler(args.tracking_repo, calls))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"TRACKING giả: {base}  (POST /api/min-ngay ⇒ node kiem/smoke/tra-loi-min-ngay.mjs)")

    import os

    os.environ["TRACKING_REPORT_SOURCE_URL"] = base
    os.environ["TRACKING_REPORT_API_KEY"] = "khoa-smoke"

    from app import beta_telemetry, owner_usability
    from app.web import server as web_server

    tmp = Path(tempfile.mkdtemp(prefix="smoke-web-r1-"))
    web_server.UPLOAD_DIR = tmp / "uploads"
    web_server.ARTIFACT_DIR = (tmp / "outputs" / "reports").resolve()
    web_server.TRACKING_TEMP_DIR = tmp / "tracking_live_tmp"
    beta_telemetry.record_run = lambda record, **kw: None

    real_run = owner_usability.run_owner_report
    web_server.run_owner_report = (
        lambda *, sales, captures=None: real_run(
            sales=sales, captures=captures, repo_root=tmp)
    )

    app = web_server.create_app(db_path=tmp / "runs.db")
    app.testing = True
    client = app.test_client()

    sales = write_sales(tmp / "so-thang-9.xlsx", ROWS, day=SALE_DAY)
    print(f"SỔ BÁN   ngày bán = {SALE_DAY}, kỳ sổ 01/09–30/09 (nạp cuối tháng)\n")

    resp = client.post(
        "/run",
        data={"workbook": (io.BytesIO(sales.read_bytes()), "so-thang-9.xlsx")},
        content_type="multipart/form-data",
    )
    print(f"POST /run → HTTP {resp.status_code}")
    if resp.status_code != 302:
        print(resp.get_data(as_text=True)[:2000])
        return 1

    artifacts = sorted(web_server.ARTIFACT_DIR.glob("*.xlsx"))
    book = openpyxl.load_workbook(artifacts[-1], data_only=True)
    sheet = book["Order Lines"]
    header = [c.value for c in sheet[1]]
    rows = [tuple(c.value for c in row) for row in sheet.iter_rows(min_row=2)]
    book.close()

    cot_don = header.index("OrderID / Số BH")
    cot_gia = header.index("Giá nhập kế toán / công khai")
    cot_lai = header.index("Lợi nhuận kế toán")
    cot_nguon = header.index("Nguồn giá")
    theo_don = {r[cot_don]: r for r in rows}

    print(f"ARTIFACT {artifacts[-1].name}")
    for order_id, *_ in ROWS:
        r = theo_don[order_id]
        print(f"  [{order_id}] giá nhập = {r[cot_gia]!r}   lợi nhuận = {r[cot_lai]!r}   "
              f"nguồn = {r[cot_nguon]}")

    run_id = artifacts[-1].stem
    evidence = app.config["RUN_REGISTRY"].get_run(run_id).tracking_evidence
    print(f"  bằng chứng run: {json.dumps({k: v for k, v in evidence.items() if k.startswith('daily_min')}, ensure_ascii=False)}")

    print("\n=== KHẲNG ĐỊNH SMOKE ===")
    kiem("hợp đồng daily-min-v1 ĐƯỢC GỌI đúng một lượt", len(calls) == 1)
    kiem("  · và hỏi đúng tập mã suy từ sổ",
         calls and calls[0]["product_codes"] == ["TRK-A", "TRK-B", "TRK-C"])
    kiem("  · và đúng khoảng NGÀY BÁN, không phải ngày nạp sổ",
         calls and (calls[0]["date_from"], calls[0]["date_to"])
         == ("2026-09-03", "2026-09-03"))

    a = theo_don["BH7001"]
    kiem("A. đơn 03/09 nạp 30/09 → 6.800.000 (giá NGÀY BÁN)",
         a[cot_gia] == GIA_NGAY_BAN)
    kiem("A. KHÔNG lấy giá hiện tại 30/09", a[cot_gia] != GIA_HIEN_TAI)
    kiem("A. KHÔNG lấy giá ngày 04/09", a[cot_gia] != GIA_NGAY_KHAC)
    kiem("A. KHÔNG rơi về lịch sử tp/ton cũ", a[cot_gia] != GIA_LICH_SU_CU)
    kiem("A. nhãn nguồn = TRACKING_DAILY_MIN", a[cot_nguon] == "TRACKING_DAILY_MIN")

    b = theo_don["BH7002"]
    kiem("B. TON_KHO thắng → 5.000.000", b[cot_gia] == 5_000_000)

    c = theo_don["BH7003"]
    kiem("C. hết hàng → KHÔNG có giá (không phải 0)", c[cot_gia] is None)
    kiem("C. lợi nhuận KHÔNG bằng doanh thu", c[cot_lai] is None)

    kiem("bằng chứng run trỏ về đúng lần chụp đã định giá",
         str(evidence.get("daily_min_capture_id", "")).startswith("LIVE-DMIN-")
         and bool(evidence.get("daily_min_query_revision")))
    kiem("capture tạm KHÔNG ở lại trên đĩa sau lần chạy",
         list((tmp / "tracking_live_tmp").glob("*.json")) == [])

    server.shutdown()
    print("\nKẾT QUẢ SMOKE:", "TẤT CẢ PASS" if _ok else "CÓ MỤC FAIL")
    return 0 if _ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
