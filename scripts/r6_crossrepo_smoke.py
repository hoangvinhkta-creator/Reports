"""R6 — smoke XUYÊN HAI REPO: producer Tracking THẬT → capture THẬT → dashboard THẬT.

    .venv/bin/python scripts/r6_crossrepo_smoke.py [--tracking /home/user/Tracking]

Không phải một test đơn vị, và cố ý không nằm trong `tests/`: nó cần repo
Tracking nằm cạnh và cần `node` chạy được. Một test đòi hai điều đó sẽ hoặc đỏ
ở mọi môi trường không có chúng, hoặc lặng lẽ tự bỏ qua và báo xanh mà chẳng
chứng minh gì. Cùng lý do và cùng khuôn với `scripts/r51_crossrepo_smoke.py`.

## Bốn mệnh đề mà chỉ smoke này nói được

1. Nhóm hàng/hãng trên bảng R6 đến từ CHÍNH `chieuBoard()` của Tracking, qua
   capture thật, qua log quyết định thật — không phải từ một dict gõ tay.
2. Đổi nhóm hàng bên Tracking chỉ ĐỔI BUCKET: tổng doanh thu, tổng SL, tổng
   chiết khấu và số đơn của kỳ KHÔNG đổi một đồng, một cái, một BH nào.
3. Dòng R5 tạm loại không lọt vào một ô nào của R6 — đo trên đúng route thật.
4. Drill-down mở từ bảng cặp không rò một trường khách hàng nào.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DAT = 0
HONG = 0


def ok(ten: str, that, mong) -> None:
    global DAT, HONG
    if that == mong:
        DAT += 1
        print(f"  ok   {ten}")
    else:
        HONG += 1
        print(f"  HỎNG {ten}\n       thấy : {that!r}\n       mong : {mong!r}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracking", type=Path,
                        default=Path("/home/user/Tracking"))
    args = parser.parse_args(argv)

    producer = args.tracking / "kiem/smoke/sinh-catalog-reports.mjs"
    if not producer.exists():
        print(f"KHÔNG CHẠY ĐƯỢC: không thấy {producer}", file=sys.stderr)
        print("Smoke này BẮT BUỘC cần repo Tracking — không có nó thì nó "
              "không chứng minh được gì, nên nó DỪNG thay vì báo đạt.",
              file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="r6-smoke-"))

    # === 1. Tracking sinh danh mục bằng CHÍNH mã thật của nó =============
    print("\n1) Tracking sinh board/alias bằng chính `chieuBoard()` thật")
    payload_path = tmp / "board.json"
    run = subprocess.run(["node", str(producer), str(payload_path)],
                         cwd=args.tracking, capture_output=True, text=True)
    if run.returncode != 0:
        print(run.stdout + run.stderr, file=sys.stderr)
        return 2
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    board, alias = payload["board"], payload["alias"]
    ok("DEC-206 còn nguyên trên producer thật",
       [board["TV-01"]["category_label"], board["MGS-01"]["category_label"],
        board["ML-01"]["category_label"]],
       ["Tivi", "Máy giặt", "Điều hoà"])

    # === 2. Reports capture bằng mã capture thật =========================
    print("\n2) Reports capture (mã thật) đọc payload do Tracking sinh")
    from app.modules.pricing.resolution.sources import (
        load_tracking_catalog_capture,
    )
    from tools.tracking import capture_tracking_catalog as capture

    envelope = capture.build_capture(
        lambda node: {"board": board, "alias": alias}[node],
        capture_id="TRK-R6-SMOKE", captured_by="r6-crossrepo-smoke",
        source_system_ref="tracking/api/xuat")
    cap_path = tmp / "catalog.json"
    cap_path.write_text(json.dumps(envelope, ensure_ascii=False),
                        encoding="utf-8")
    snapshot = load_tracking_catalog_capture(cap_path)
    ok("capture COMPLETE", envelope["capture_status"], "COMPLETE")

    # === 3. Route R6 THẬT ================================================
    print("\n3) Route R6 thật: capture → bản chiếu → dashboard phân tích")
    from sqlalchemy import create_engine

    import tools.db as history_db
    from app.owner_usability import SelectedCaptures
    from app.web import catalog_display, history_store, identity_gateway
    from app.web import server as web_server
    from tests.support import identity_fixtures as fx
    from tests.test_employee_workspace_ux import line, persist
    from tools.tracking import live_pull

    display_path = tmp / "tracking_display.json"
    catalog_display.DEFAULT_DISPLAY_PATH = display_path
    catalog_display.write(snapshot)

    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    repository = history_store.SnapshotRepository(engine)
    identity_store = fx.store(tmp)

    web_server.select_latest_valid_captures = lambda: None
    live_pull.is_configured = lambda env=None: False
    identity_gateway.build_store = lambda: identity_store
    captures = SelectedCaptures(tracking_capture=tmp / "history.json",
                                tracking_catalog=cap_path,
                                tracking_inv_map=tmp / "inv_map.json")
    web_server._select_captures_for_run = lambda: (captures, None, None)
    web_server.load_tracking_catalog_capture = lambda path: snapshot

    app = web_server.create_app(
        db_path=tmp / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    app.testing = True
    client = app.test_client()

    # BH1 mua Tivi + Tủ lạnh (một cặp thật); BH2 mua Tivi + phí; BH3 chưa khớp.
    persist(repository, [
        line("BH1", "Tivi Samsung QLED 55Q6FA", day=5, sell="9000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
        line("BH1", "Tủ lạnh Samsung RT38", day=5, row=7, sell="7000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
        line("BH2", "Tivi Samsung QLED 55Q6FA", day=6, row=8, sell="9000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
        line("BH2", "Chi phí vận chuyển", day=6, row=9, sell="300000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
        line("BH3", "Tivi cũ trưng bày", day=7, row=10, sell="1000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
    ])

    def html_of(path):
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} → {resp.status_code}"
        return resp.get_data(as_text=True)

    def cells(html, name):
        return [v.strip() for v in re.findall(
            rf'data-metric="{name}"[^>]*>(.*?)<', html, re.S)]

    def one(html, name):
        return cells(html, name)[0]

    def totals(html):
        return {name: one(html, name) for name in
                ("sales_revenue", "discount_total", "orders", "total_quantity",
                 "gross_before_discount")}

    OVERVIEW = "/kinh-doanh/phan-tich?ky=2026-09"
    STRUCTURE = "/kinh-doanh/phan-tich/co-cau?ky=2026-09&chieu=nhom-hang"
    BASKET = "/kinh-doanh/phan-tich/gio-hang?ky=2026-09"

    before = html_of(OVERVIEW)
    money_before = totals(before)
    ok("đối soát với bộ chỉ tiêu nghiệp vụ đã nghiệm thu: KHỚP",
       re.search(r'data-metric="totals-reconciliation"[^>]*'
                 r'data-reconciled="(\w+)"', before).group(1), "yes")
    ok("trước khi phân loại: KHÔNG nhóm hàng nào chính danh",
       [label for label in cells(html_of(STRUCTURE), "bucket-label")
        if label not in ("TỔNG",) and "Chưa xác định" not in label], [])

    # Phân loại qua ĐÚNG route POST thật của R2/R5.
    def classify(order, code):
        html = html_of("/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        for href in re.findall(
                r'data-metric="identity-open"[^>]*href="([^"]+)"', html):
            match = re.search(r"order_key=([^&\"]+).*?product_key=([0-9a-f]+)"
                              r".*?occurrence_index=(\d+)", href)
            if match is None or match.group(1) != order:
                continue
            resp = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
                "ky": "2026-09", "sheet": "noi-thanh",
                "order_key": match.group(1), "product_key": match.group(2),
                "occurrence_index": match.group(3), "ma_tracking": code})
            if resp.status_code == 302:
                return True
        return False

    ok("phân loại BH1 → 55Q6FA", classify("BH1", "55Q6FA"), True)
    ok("phân loại BH2 → RT38", classify("BH2", "RT38"), True)

    after = html_of(STRUCTURE)
    ok("nhóm hàng canonical của Tracking lên đúng bảng R6",
       sorted({label for label in cells(after, "bucket-label")
               if "Chưa xác định" not in label and label != "TỔNG"}),
       ["Tivi", "Tủ lạnh"])
    ok("bảng nhóm hàng ĐỐI SOÁT khớp",
       re.search(r'data-metric="reconciliation"[^>]*data-reconciled="(\w+)"',
                 after).group(1), "yes")
    ok("tổng tiền/SL/đơn KHÔNG đổi sau khi nhóm hàng xuất hiện",
       totals(html_of(OVERVIEW)), money_before)

    # Đổi nhóm hàng bên Tracking ⟹ chỉ bucket đổi, tiền không.
    projection = json.loads(display_path.read_text(encoding="utf-8"))
    projection["55Q6FA"]["category_label"] = "Màn hình"
    display_path.write_text(json.dumps(projection, ensure_ascii=False),
                            encoding="utf-8")
    moved = html_of(STRUCTURE)
    ok("đổi nhóm hàng bên Tracking hiện ra ngay ở lần đọc sau",
       sorted({label for label in cells(moved, "bucket-label")
               if "Chưa xác định" not in label and label != "TỔNG"}),
       ["Màn hình", "Tủ lạnh"])
    ok("...và KHÔNG đổi một đồng, một cái, một BH nào",
       totals(html_of(OVERVIEW)), money_before)

    # === 4. Giỏ hàng và drill-down ======================================
    print("\n4) Giỏ hàng, cặp, attachment và drill-down")
    basket = html_of(BASKET)
    ok("BH1 là đơn nhiều mặt hàng; BH2 có dịch vụ kèm",
       [one(basket, "multi_product_orders"),
        one(basket, "service_attachment_orders")], ["1", "1"])
    # Phép đo ĐÚNG của mệnh đề "phí không làm tăng nhóm hàng hoá" là một phép
    # SO SÁNH, không phải một con số 0: BH1 (hai mặt hàng, hai nhóm) là một đơn
    # nhiều nhóm hàng THẬT và phải được đếm. Cái phải KHÔNG được đếm là BH2
    # (một tivi + một khoản phí). Vì thế:
    #
    #     đơn nhiều dòng                = 2   (BH1 và BH2)
    #     đơn nhiều nhóm hàng hoá       = 1   (chỉ BH1)
    #
    # và chênh lệch đúng bằng đơn có phí. Một khẳng định "= 0" sẽ xanh khi
    # engine hỏng theo hướng ngược lại (bỏ sót cả BH1) mà không ai thấy.
    ok("đơn nhiều dòng đếm cả BH1 lẫn BH2",
       one(basket, "multi_line_orders"), "2")
    ok("phí KHÔNG làm tăng ô nhiều nhóm hàng hoá: chỉ BH1 được đếm",
       one(basket, "multi_merchandise_category_orders"), "1")

    pairs = html_of(BASKET + "&chieu=nhom-hang")
    ok("cặp nhóm hàng dựng được từ dữ liệu đi qua database",
       len(cells(pairs, "pair-orders")) >= 1, True)
    ok("attachment có HAI cột riêng",
       len(cells(pairs, "attachment-left")) ==
       len(cells(pairs, "attachment-right")) >= 1, True)

    drill = html_of("/kinh-doanh/phan-tich/don-hang?ky=2026-09")
    ok("drill-down KHÔNG rò tên khách hàng",
       "Nguyễn Thị Hoa" in drill, False)
    ok("drill-down KHÔNG rò số điện thoại", "0912000111" in drill, False)
    ok("drill-down KHÔNG rò địa chỉ", "12 Lê Lợi, Q1" in drill, False)
    ok("drill-down vẫn hiện đủ bốn cột nghiệp vụ",
       [bool(cells(drill, name)) for name in
        ("order-key", "sale-date", "employee", "product")],
       [True, True, True, True])

    # === 5. Dòng R5 tạm loại không lọt vào R6 ============================
    print("\n5) Dòng R5 tạm loại KHÔNG lọt vào một ô nào của R6")
    second = persist(repository, [
        line("BH1", "Tivi Samsung QLED 55Q6FA", day=5, sell="9000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
        line("BH1", "Tủ lạnh Samsung RT38", day=5, row=7, sell="7000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
        line("BH2", "Tivi Samsung QLED 55Q6FA", day=6, row=8, sell="9000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
        line("BH2", "Chi phí vận chuyển", day=6, row=9, sell="300000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
    ], run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")
    from datetime import date as _date
    repository.confirm_coverage(second.snapshot_id, confirmed=True,
                                confirmed_at="2026-10-03T00:00:00",
                                start=_date(2026, 9, 1), end=_date(2026, 9, 30))
    dropped = html_of(OVERVIEW)
    ok("BH3 rời khỏi số đơn của R6",
       int(one(dropped, "orders")), int(money_before["orders"]) - 1)
    ok("doanh thu R6 giảm đúng phần của BH3",
       Decimal(one(dropped, "sales_revenue").replace(".", "")),
       Decimal(money_before["sales_revenue"].replace(".", ""))
       - Decimal("1000"))
    ok("...và trang vẫn ĐỐI SOÁT khớp",
       re.search(r'data-metric="totals-reconciliation"[^>]*'
                 r'data-reconciled="(\w+)"', dropped).group(1), "yes")
    ok("BH3 cũng biến khỏi bảng kê drill-down",
       "Tivi cũ trưng bày" in html_of(
           "/kinh-doanh/phan-tich/don-hang?ky=2026-09"), False)

    print(f"\nKẾT QUẢ SMOKE: {DAT} PASS, {HONG} FAIL")
    return 1 if HONG else 0


if __name__ == "__main__":
    sys.exit(main())
