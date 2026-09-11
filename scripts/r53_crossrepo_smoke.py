"""Smoke XUYÊN HAI REPO cho R5.3 — nhãn Tracking phải SỐNG QUA restart.

Vì sao script này tồn tại, và vì sao nó KHÔNG phải một test trong `tests/`:
nó cần repo Tracking nằm cạnh và cần `node` chạy được. Một test đòi hai điều
đó sẽ tự bỏ qua ở nơi chỉ có một repo — và một bài kiểm bị bỏ qua trông y hệt
một bài đã đạt. Nên nó là một script chạy tay, in ra PASS/FAIL đếm được, và
kết quả của nó được chép vào bàn giao làm bằng chứng.

Điều nó chứng minh mà `tests/test_r53_durable_tracking_labels.py` KHÔNG chứng
minh được: payload đi vào Reports là do CHÍNH mã Tracking sinh ra. File test
kia gõ tay các dict `{"brand": ..., "category_label": ...}` — chúng chứng minh
Reports đọc đúng thứ NÓ TƯỞNG Tracking gửi. Khoảng cách giữa "tưởng" và
"thật" là chỗ đắt nhất giữa hai hệ thống.

Chuỗi được tái hiện, đúng thứ tự production:

```text
Tracking chieuBoard() THẬT → capture Reports → POST /run THẬT
→ tab Nhân viên → XOÁ ĐĨA EPHEMERAL (đúng việc Render làm) → tab Nhân viên
```

Chạy (từ gốc repo Reports):

    .venv/bin/python scripts/r53_crossrepo_smoke.py

Tuỳ chọn `--tracking <đường dẫn>` nếu repo Tracking không ở `/home/user/Tracking`.
"""

from __future__ import annotations

import argparse
import html as html_module
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DAT = 0
HONG = 0


def ok(ten: str, that, mong) -> None:
    global DAT, HONG
    if that == mong:
        DAT += 1
        print(f"  ok   {ten}")
    else:
        HONG += 1
        print(f"  LỖI  {ten}\n         được  {that!r}\n         mong   {mong!r}")


def _text(cell: str) -> str:
    return " ".join(html_module.unescape(re.sub(r"<[^>]+>", " ", cell)).split())


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

    tmp = Path(tempfile.mkdtemp(prefix="r53-smoke-"))

    # === 1. Tracking sinh board/alias bằng CHÍNH `chieuBoard()` thật =====
    print("\n1) Tracking sinh board/alias bằng chính `chieuBoard()` thật")
    payload_path = tmp / "board.json"
    run = subprocess.run([ "node", str(producer), str(payload_path)],
                         cwd=args.tracking, capture_output=True, text=True)
    if run.returncode != 0:
        print(run.stdout + run.stderr, file=sys.stderr)
        print("producer của Tracking chạy hỏng — dừng.", file=sys.stderr)
        return 2
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    board, alias = payload["board"], payload["alias"]
    ok("hợp đồng R5.2 còn nguyên: đủ ba trường trên một mã đã phân loại",
       [board["55Q6FA"]["model_label"], board["55Q6FA"]["brand"],
        board["55Q6FA"]["category_label"]],
       ["QLED 55Q6FA", "Samsung", "Tivi"])
    ok("mã Tracking KHÔNG khẳng định hãng vẫn gửi nhóm hàng",
       [board["XUNG-01"]["brand"], board["XUNG-01"]["category_label"]],
       [None, "Tivi"])

    # === 2. Capture của Reports, dựng từ payload THẬT ====================
    print("\n2) Reports chụp capture từ payload THẬT của Tracking")
    from tools.tracking import capture_tracking_catalog as capture
    from app.modules.pricing.resolution.sources import (
        load_tracking_catalog_capture)

    # Một mã khớp đúng tên hàng của workbook tổng hợp, để có gì mà hiển thị.
    board_run = {**board, "MGS-01": {**board["MGS-01"],
                                     "alt": ["Máy giặt Test-1"]}}
    envelope = capture.build_capture(
        lambda node: {"board": board_run, "alias": alias}[node],
        capture_id="TRK-R53", captured_by="r53-smoke",
        source_system_ref="tracking/api/xuat")
    cap_path = tmp / "catalog.json"
    cap_path.write_text(json.dumps(envelope, ensure_ascii=False),
                        encoding="utf-8")
    snapshot = load_tracking_catalog_capture(cap_path)
    row = snapshot.row_for("MGS-01")
    ok("capture chở đủ ba trường của mã sẽ được xác nhận",
       [row.model_label, row.brand, row.category_label],
       ["FV1412", "LG", "Máy giặt"])

    # === 3. `POST /run` THẬT, KHÔNG mở bảng chọn phân loại ===============
    print("\n3) upload/run THẬT → tab Nhân viên")
    from sqlalchemy import create_engine, text as sql_text

    import tools.db as history_db
    from app import beta_telemetry, owner_usability
    from app.owner_usability import SelectedCaptures
    from app.web import catalog_display, history_store, identity_gateway
    from app.web import server as web_server
    from tools.tracking import live_pull
    from tests.fixtures.synthetic_workbook import build_synthetic_workbook
    from tests.support import identity_fixtures as fx

    workbook = tmp / "so_ke_toan.xlsx"
    build_synthetic_workbook(workbook)

    display_path = tmp / "tracking_display.json"
    catalog_display.DEFAULT_DISPLAY_PATH = display_path

    web_server._select_captures_for_run = (
        lambda sales=None, identity_store_view=None: (
            SelectedCaptures(
                tracking_capture=None, tracking_catalog=cap_path,
                tracking_inv_map=None, tracking_daily_min=None),
            {"catalog_capture_id": "TRK-R53"}, None))
    live_pull.is_configured = lambda env=None: True
    web_server.load_tracking_catalog_capture = lambda path: snapshot
    web_server.UPLOAD_DIR = tmp / "uploads"
    web_server.ARTIFACT_DIR = (tmp / "outputs" / "reports").resolve()
    web_server.TRACKING_TEMP_DIR = tmp / "tracking_live_tmp"
    beta_telemetry.record_run = lambda record, **kw: None
    _real_owner_run = owner_usability.run_owner_report
    web_server.run_owner_report = (
        lambda *, sales, captures=None, identity_store_view=None:
        _real_owner_run(sales=sales, captures=captures, repo_root=tmp,
                        identity_store_view=identity_store_view))

    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    identity_store = fx.store(tmp)
    identity_gateway.build_store = lambda: identity_store

    app = web_server.create_app(
        db_path=tmp / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    app.testing = True
    client = app.test_client()

    identity_gateway.confirm_identity(
        app.config["IDENTITY_STORE"], product_raw="Máy giặt Test-1",
        tracking_code="MGS-01", snapshot=snapshot, actor_id="r53-smoke",
        affected_orders=("BH0001",), affected_lines=1)

    # Đĩa ephemeral: bản chiếu KHÔNG tồn tại trước khi chạy.
    display_path.unlink(missing_ok=True)
    ok("trước khi chạy: cache đĩa KHÔNG tồn tại", display_path.exists(), False)

    resp = client.post("/run", data={
        "workbook": (io.BytesIO(workbook.read_bytes()), workbook.name)},
        content_type="multipart/form-data")
    ok("upload/run thành công (302)", resp.status_code, 302)

    def sheet(employee="Ly"):
        r = client.get(f"/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien={employee}")
        assert r.status_code == 200, r.status_code
        html = r.get_data(as_text=True)
        return {name: [_text(v) for v in re.findall(
            rf'data-metric="{name}"[^>]*>(.*?)</td>', html, re.S)]
            for name in ("line-product", "line-brand", "line-category",
                         "totals-purchase", "totals-sell", "totals-profit",
                         "totals-converted")}, html

    truoc, html_truoc = sheet()
    ok("KHÔNG mở bảng chọn: Mặt hàng hiện MODEL NGẮN từ Tracking",
       "FV1412" in truoc["line-product"], True)
    ok("cột Hãng hiện brand từ Tracking", "LG" in truoc["line-brand"], True)
    ok("cột Nhóm hàng hiện category_label từ Tracking",
       "Máy giặt" in truoc["line-category"], True)
    ok("tên dài trên sổ đã biến khỏi Ô Mặt hàng",
       "Máy giặt Test-1" in truoc["line-product"], False)
    ok("...nhưng vẫn đọc đủ được qua tooltip (R5.3 §UI)",
       'title="Máy giặt Test-1"' in html_truoc, True)
    ok("bản chiếu lành ⟹ KHÔNG có cảnh báo",
       'data-metric="catalog-projection-warning"' in html_truoc, False)

    # === 4. RESTART: xoá ĐÚNG những gì Render xoá ========================
    print("\n4) RESTART container: xoá đĩa ephemeral, KHÔNG đụng database")
    stored = history_store.SnapshotRepository(engine).latest_tracking_display()
    ok("lần chạy đã lưu BỀN bản chiếu, kèm capture đã dùng",
       stored is not None and stored["capture_id"], "TRK-R53")
    ok("bản bền mang NGUYÊN VĂN nhãn của capture Tracking thật",
       stored["rows"]["MGS-01"],
       {"model_label": "FV1412", "brand": "LG", "category_label": "Máy giặt"})

    for path in display_path.parent.glob("tracking_display*"):
        path.unlink()
    ok("sau restart: cache đĩa đã biến mất", display_path.exists(), False)

    sau, html_sau = sheet()
    ok("R5.3: Mặt hàng vẫn hiện MODEL NGẮN sau restart",
       "FV1412" in sau["line-product"], True)
    ok("R5.3: Hãng vẫn hiện sau restart", "LG" in sau["line-brand"], True)
    ok("R5.3: Nhóm hàng vẫn hiện sau restart",
       "Máy giặt" in sau["line-category"], True)
    ok("...và cache đĩa được ghi lại", display_path.exists(), True)
    ok("...và KHÔNG có cảnh báo nào, vì không có gì hỏng",
       'data-metric="catalog-projection-warning"' in html_sau, False)

    tien = ("totals-purchase", "totals-sell", "totals-profit",
            "totals-converted")
    ok("restart KHÔNG đổi một đồng nào của bảng kê",
       [sau[k] for k in tien], [truoc[k] for k in tien])
    ok("...và không thêm/bớt một dòng nào",
       len(sau["line-product"]), len(truoc["line-product"]))

    # === 5. Dòng CHƯA xác nhận: `—` dù tên nhìn giống hãng/nhóm hàng =====
    print("\n5) Dòng chưa xác nhận: dấu gạch, không suy từ tên kế toán")
    vinh, _ = sheet("Vinh")
    ok("`Tivi Test-7` chưa xác nhận ⟹ giữ TÊN THÔ",
       "Tivi Test-7" in vinh["line-product"], True)
    ok("...và Hãng/Nhóm hàng là dấu gạch, dù tên chứa chữ 'Tivi'",
       [set(vinh["line-brand"]), set(vinh["line-category"])],
       [{"—"}, {"—"}])

    # === 6. Mất CẢ HAI nơi lưu ⟹ vẫn CẢNH BÁO, không im lặng ===========
    print("\n6) Mất cả hai nơi lưu ⟹ cảnh báo, không im lặng")
    for path in display_path.parent.glob("tracking_display*"):
        path.unlink()
    with engine.begin() as connection:
        connection.execute(sql_text("DELETE FROM tracking_display_snapshot"))
    mat, html_mat = sheet()
    ok("mất cả hai ⟹ tab Nhân viên CẢNH BÁO",
       'data-metric="catalog-projection-warning"' in html_mat, True)
    ok("...và vẫn KHÔNG đổi một đồng nào",
       [mat[k] for k in tien], [truoc[k] for k in tien])

    print(f"\nKẾT QUẢ SMOKE: {DAT} PASS, {HONG} FAIL")
    return 1 if HONG else 0


if __name__ == "__main__":
    raise SystemExit(main())
