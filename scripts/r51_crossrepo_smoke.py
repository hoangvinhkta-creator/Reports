"""Smoke XUYÊN HAI REPO cho R5.1 — `category_label` từ Tracking tới màn hình.

Vì sao script này tồn tại, và vì sao nó KHÔNG phải một test trong `tests/`:
nó cần repo Tracking nằm cạnh và cần `node` chạy được. Một test đòi hai điều
đó sẽ tự bỏ qua ở nơi chỉ có một repo — và một bài kiểm bị bỏ qua trông y hệt
một bài đã đạt. Nên nó là một script chạy tay, in ra PASS/FAIL đếm được, và
kết quả của nó được chép vào bàn giao làm bằng chứng.

Điều nó chứng minh mà không test nào trong `tests/` chứng minh được:

    payload đi vào Reports là do CHÍNH mã Tracking sinh ra.

`tests/test_r51_category_label.py` gõ tay các dict `{"category_label": ...}`.
Chúng chứng minh Reports đọc đúng thứ NÓ TƯỞNG Tracking gửi. Khoảng cách
giữa "tưởng" và "thật" là chỗ đắt nhất giữa hai hệ thống, và với R5.1 nó còn
rộng hơn R5: `category_label` là trường DUY NHẤT trong hợp đồng được dẫn xuất
từ một chuỗi người dùng gõ tay (`board/<mã>/cat`), nên một fixture tự viết sẽ
tự cho mình một `cat` sạch sẽ mà đời thật không có.

Chạy (từ gốc repo Reports):

    .venv/bin/python scripts/r51_crossrepo_smoke.py

Tuỳ chọn `--tracking <đường dẫn>` nếu repo Tracking không ở `../Tracking`.
"""

from __future__ import annotations

import argparse
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracking", type=Path,
                        default=Path("/home/user/Tracking"))
    args = parser.parse_args(argv)

    tracking = args.tracking
    producer = tracking / "kiem/smoke/sinh-catalog-reports.mjs"
    if not producer.exists():
        print(f"KHÔNG CHẠY ĐƯỢC: không thấy {producer}", file=sys.stderr)
        print("Smoke này BẮT BUỘC cần repo Tracking — không có nó thì nó "
              "không chứng minh được gì, nên nó DỪNG thay vì báo đạt.",
              file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="r51-smoke-"))

    # === 1. Tracking sinh catalog bằng CHÍNH mã thật của nó ==============
    print("\n1) Tracking sinh board/alias bằng chính `chieuBoard()` thật")
    payload_path = tmp / "board.json"
    run = subprocess.run(
        ["node", str(producer), str(payload_path)],
        cwd=tracking, capture_output=True, text=True)
    if run.returncode != 0:
        print(run.stdout + run.stderr, file=sys.stderr)
        print("producer của Tracking chạy hỏng — dừng.", file=sys.stderr)
        return 2
    print("    " + "\n    ".join(run.stdout.strip().splitlines()))
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    board, alias = payload["board"], payload["alias"]

    ok("bốn trường hợp §7 đều có mặt", sorted(board),
       ["55Q6FA", "LA-01", "RT38", "XUNG-01"])
    ok("Tivi Samsung ⟹ category_label Tivi",
       board["55Q6FA"]["category_label"], "Tivi")
    ok("Tủ lạnh Samsung ⟹ category_label Tủ lạnh",
       board["RT38"]["category_label"], "Tủ lạnh")
    ok("mã chưa xếp ngành hàng ⟹ null",
       board["LA-01"]["category_label"], None)
    ok("mã cat hai hãng ⟹ null", board["XUNG-01"]["category_label"], None)
    ok("alias.map mang stale target, Tracking KHÔNG gộp sẵn (INV-16)",
       alias["map"], {"CU-01": "55Q6FA"})

    # Rò dữ liệu — soi chuỗi ĐÃ serialize, không soi dict.
    chu = json.dumps(payload, ensure_ascii=False)
    for khoa, vi in [('"cat"', "khoá ngành hàng"), ("Tivi Samsung", "cat ghép hãng"),
                     ("Đất Việt", "tên NCC"), ('"p"', "giá vốn"),
                     ('"tp"', "giá chốt"), ('"_c"', "số Engine"),
                     ('"q"', "tồn kho"), ('"bb"', "giá bán buôn"),
                     ("tinphat.vn", "link nội bộ")]:
        # `name` được phép đi ra, nên chỉ soi những chuỗi KHÔNG nằm trong name.
        if khoa == "Tivi Samsung":
            ok("không lộ " + vi,
               any(khoa in json.dumps(v, ensure_ascii=False)
                   for k, v in board.items() if k != "55Q6FA"), False)
            continue
        ok("không lộ " + vi, khoa in chu, False)

    # === 2. Reports capture đọc ĐÚNG payload đó bằng mã capture thật =====
    print("\n2) Reports capture (mã thật) đọc payload do Tracking sinh")
    from tools.tracking import capture_tracking_catalog as capture
    from app.modules.pricing.resolution.sources import (
        load_tracking_catalog_capture,
    )

    def fetch(node):
        return {"board": board, "alias": alias}[node]

    envelope = capture.build_capture(
        fetch, capture_id="TRK-R51-SMOKE", captured_by="r51-crossrepo-smoke",
        source_system_ref="tracking/api/xuat")
    ok("capture COMPLETE", envelope["capture_status"], "COMPLETE")

    cap_path = tmp / "catalog.json"
    cap_path.write_text(json.dumps(envelope, ensure_ascii=False),
                        encoding="utf-8")
    snapshot = load_tracking_catalog_capture(cap_path)

    def ba_truong(code):
        row = snapshot.row_for(code)
        return (row.model_label, row.brand, row.category_label)

    ok("55Q6FA: model + hãng + nhóm hàng đúng",
       ba_truong("55Q6FA"), ("QLED 55Q6FA", "Samsung", "Tivi"))
    ok("RT38: model + hãng + nhóm hàng đúng",
       ba_truong("RT38"), ("RT38", "Samsung", "Tủ lạnh"))
    ok("LA-01: cả ba đều None", ba_truong("LA-01"), (None, None, None))
    ok("XUNG-01: cả ba đều None", ba_truong("XUNG-01"), (None, None, None))
    ok("alias_map qua được nguyên vẹn",
       snapshot.alias_map(), {"CU-01": "55Q6FA"})

    # Nhóm hàng KHÔNG tham gia nhận diện, đo trên chính snapshot thật này.
    ok("ghép EXACT không đọc nhóm hàng",
       snapshot.exact_match_codes(raw_key="Tivi", aid="tivi"), ())

    # Envelope đã serialize không được mang một trường riêng tư nào.
    than = json.dumps(envelope, ensure_ascii=False)
    for khoa, vi in [('"cat"', "ngành hàng thô"), ('"p"', "giá vốn"),
                     ('"tp"', "giá chốt"), ('"q"', "tồn kho"),
                     ("tinphat.vn", "link nội bộ")]:
        ok("envelope không lộ " + vi, khoa in than, False)

    # === 3. Artifact R5 CŨ vẫn đọc được =================================
    print("\n3) Artifact R5 cũ (không có category_label) vẫn đọc được")
    # Dựng artifact cũ cho ĐÚNG: chụp lại từ một `board` KHÔNG có trường mới
    # — tức từ một Tracking đời R5 — chứ không phải bằng cách xoá trường khỏi
    # envelope mới. Cách xoá ấy tạo ra một file mà `content_hash` không còn
    # khớp `rows`, và loader ĐÚNG khi từ chối nó (bất biến `INV-11`): đó là
    # một file bị sửa sau khi ghi, không phải một artifact R5 hợp lệ.
    board_r5 = {code: {k: v for k, v in row.items() if k != "category_label"}
                for code, row in board.items()}
    envelope_cu = capture.build_capture(
        lambda node: {"board": board_r5, "alias": alias}[node],
        capture_id="TRK-R5-CU", captured_by="r51-crossrepo-smoke",
        source_system_ref="tracking/api/xuat")
    cu_path = tmp / "catalog-cu.json"
    cu_path.write_text(json.dumps(envelope_cu, ensure_ascii=False),
                       encoding="utf-8")
    snapshot_cu = load_tracking_catalog_capture(cu_path)
    ok("artifact cũ vẫn load được", snapshot_cu.capture_status.value, "COMPLETE")

    # §4.7 đo trực tiếp: cùng một danh mục, khác đúng nhóm hàng ⟹ khác hash.
    # Đây là thứ làm Reports BIẾT phải nhận bản chiếu mới.
    ok("content_hash ĐỔI khi nhóm hàng đổi",
       envelope_cu["content_hash"] == envelope["content_hash"], False)
    # ...nhưng một dòng vốn KHÔNG có nhóm hàng thì băm y hệt ở cả hai đời
    # hợp đồng — nâng cấp hợp đồng không tự khai là một lần đổi danh mục.
    ok("dòng không có nhóm hàng băm y hệt ở cả hai đời hợp đồng",
       [r for r in envelope["rows"] if r["tracking_code"] == "LA-01"],
       [r for r in envelope_cu["rows"] if r["tracking_code"] == "LA-01"])
    ok("artifact cũ: model/hãng giữ nguyên",
       (snapshot_cu.row_for("55Q6FA").model_label,
        snapshot_cu.row_for("55Q6FA").brand), ("QLED 55Q6FA", "Samsung"))
    ok("artifact cũ: nhóm hàng là None, không phải lỗi",
       snapshot_cu.row_for("55Q6FA").category_label, None)

    # === 4. Đi qua ĐÚNG route web thật ===================================
    print("\n4) Route web thật: capture → bản chiếu → bảng kê nhân viên")
    from sqlalchemy import create_engine

    import tools.db as history_db
    from app.web import catalog_display, history_store, identity_gateway
    from app.web import server as web_server
    from tools.tracking import live_pull
    from tests.test_employee_workspace_ux import line, persist
    from tests.support import identity_fixtures as fx

    display_path = tmp / "tracking_display.json"
    catalog_display.DEFAULT_DISPLAY_PATH = display_path
    # Bản chiếu được ghi từ CHÍNH snapshot do Tracking sinh — không gõ tay.
    catalog_display.write(snapshot)
    ok("bản chiếu chỉ giữ dòng CÓ điều để nói",
       sorted(json.loads(display_path.read_text(encoding="utf-8"))),
       ["55Q6FA", "RT38"])

    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    repository = history_store.SnapshotRepository(engine)
    identity_store = fx.store(tmp)

    web_server.select_latest_valid_captures = lambda: None
    live_pull.is_configured = lambda env=None: False
    identity_gateway.build_store = lambda: identity_store
    from app.owner_usability import SelectedCaptures
    captures = SelectedCaptures(
        tracking_capture=tmp / "history.json", tracking_catalog=cap_path,
        tracking_inv_map=tmp / "inv_map.json")
    web_server._select_captures_for_run = lambda: (captures, None, None)
    web_server.load_tracking_catalog_capture = lambda path: snapshot

    app = web_server.create_app(
        db_path=tmp / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    app.testing = True
    client = app.test_client()

    persist(repository, [
        line("BH1", "Tivi Samsung QLED 55Q6FA", day=5, kpi_purchase=None,
             kpi_profit=None, status="PENDING", reasons=("IDENTITY_UNRESOLVED",)),
        line("BH2", "Tủ lạnh Samsung RT38", day=6, kpi_purchase=None,
             kpi_profit=None, status="PENDING", reasons=("IDENTITY_UNRESOLVED",)),
        line("BH3", "Tivi cũ trưng bày", day=7, kpi_purchase=None,
             kpi_profit=None, status="PENDING", reasons=("IDENTITY_UNRESOLVED",)),
        line("BH4", "Tivi Sony thay thế Samsung", day=8, kpi_purchase=None,
             kpi_profit=None, status="PENDING", reasons=("IDENTITY_CONFLICT",)),
    ])

    def html_of():
        resp = client.get("/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert resp.status_code == 200, resp.status_code
        return resp.get_data(as_text=True)

    def cells(html, name):
        return [v.strip() for v in re.findall(
            rf'data-metric="{name}"[^>]*>(.*?)<', html, re.S)]

    def money(html):
        return {n: re.search(rf'data-metric="{n}"[^>]*>(.*?)<', html, re.S)
                .group(1).strip()
                for n in ("totals-purchase", "totals-sell", "totals-profit",
                          "totals-converted")}

    truoc = html_of()
    tien_truoc = money(truoc)
    ok("trước khi phân loại: KHÔNG dòng nào có nhóm hàng",
       set(cells(truoc, "line-category")), {"—"})

    # Phân loại từng dòng qua ĐÚNG route POST thật.
    def classify(product_name, code):
        html = html_of()
        for block in re.findall(
                r'data-metric="identity-open"[^>]*href="([^"]+)"', html):
            m = re.search(r"order_key=([^&\"]+).*?product_key=([0-9a-f]+)"
                          r".*?occurrence_index=(\d+)", block)
            if m is None:
                continue
            order, product_key, occ = m.groups()
            if order != product_name:
                continue
            resp = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
                "ky": "2026-09", "sheet": "noi-thanh", "order_key": order,
                "product_key": product_key, "occurrence_index": occ,
                "ma_tracking": code})
            return resp.status_code
        return None

    ok("phân loại BH1 → 55Q6FA", classify("BH1", "55Q6FA"), 302)
    ok("phân loại BH2 → RT38", classify("BH2", "RT38"), 302)
    ok("phân loại BH3 → LA-01 (mã CÓ thật, chưa xếp ngành hàng)",
       classify("BH3", "LA-01"), 302)

    sau = html_of()
    ok("BH1/BH2 hiện đúng nhóm hàng; BH3 và BH4 để trống",
       cells(sau, "line-category"), ["Tivi", "Tủ lạnh", "—", "—"])
    ok("hãng đi kèm đúng dòng",
       cells(sau, "line-brand"), ["Samsung", "Samsung", "—", "—"])
    ok("model canonical đi kèm đúng dòng",
       cells(sau, "line-product")[:2], ["QLED 55Q6FA", "RT38"])
    ok("dòng conflict giữ TÊN THÔ",
       "Tivi Sony thay thế Samsung" in sau, True)
    ok("tổng tiền KHÔNG đổi sau khi nhóm hàng xuất hiện",
       money(sau), tien_truoc)

    # Đổi nhóm hàng bên Tracking ⟹ chỉ nhãn đổi, tiền không.
    duoc = json.loads(display_path.read_text(encoding="utf-8"))
    duoc["55Q6FA"]["category_label"] = "Màn hình"
    display_path.write_text(json.dumps(duoc, ensure_ascii=False),
                            encoding="utf-8")
    doi = html_of()
    ok("đổi nhóm hàng bên Tracking hiện ra ngay ở lần đọc sau",
       cells(doi, "line-category")[0], "Màn hình")
    ok("...và KHÔNG đổi một đồng nào", money(doi), tien_truoc)

    # Restart: một `create_app()` mới đọc ra đúng câu đó.
    lai = web_server.create_app(
        db_path=tmp / "runs-2.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    lai.testing = True
    resp = lai.test_client().get(
        "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
    ok("sau create_app() mới vẫn đọc đúng",
       cells(resp.get_data(as_text=True), "line-category"),
       ["Màn hình", "Tủ lạnh", "—", "—"])

    print(f"\nKẾT QUẢ SMOKE: {DAT} PASS, {HONG} FAIL")
    return 1 if HONG else 0


if __name__ == "__main__":
    sys.exit(main())
