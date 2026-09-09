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

    ok("mọi trường hợp §7 + REPAIR-1 + DEC-206 đều có mặt", sorted(board),
       ["55Q6FA", "BAN-01", "BAN-02", "BAN-03", "LA-01", "MGS-01", "ML-01",
        "RT38", "TV-01", "VS-01", "XUNG-01"])
    ok("Tivi Samsung ⟹ category_label Tivi",
       board["55Q6FA"]["category_label"], "Tivi")
    ok("Tủ lạnh Samsung ⟹ category_label Tủ lạnh",
       board["RT38"]["category_label"], "Tủ lạnh")
    ok("mã chưa xếp ngành hàng ⟹ null",
       board["LA-01"]["category_label"], None)

    # --- REPAIR-1: `cat` bẩn NGỮ NGHĨA không còn đi qua ranh giới ---------
    #
    # Ba dòng này là chính các chuỗi `AR-R5.1-05` tái hiện được trên HEAD cũ.
    # Chúng là lý do repair cycle này tồn tại, nên chúng được đo ở đây, trên
    # payload do CHÍNH mã Tracking sinh — không phải trên một dict gõ tay.
    ok('"Tivi kho anh Ba" ⟹ null', board["BAN-01"]["category_label"], None)
    ok('"Tivi Đất Việt" (NCC) ⟹ null', board["BAN-02"]["category_label"], None)
    ok('"Tủ lạnh Hòa Phát" (hãng ngoài HANG) ⟹ null',
       board["BAN-03"]["category_label"], None)

    ok("hãng đã thêm vào HANG ⟹ nhãn ra bình thường",
       [board["VS-01"]["brand"], board["VS-01"]["category_label"]],
       ["Vsmart", "Tivi"])
    ok('đồng nghĩa gộp: "Máy lạnh" ⟹ "Điều hoà"',
       board["ML-01"]["category_label"], "Điều hoà")
    ok("cat hai hãng: nhóm hàng CHẮC CHẮN, hãng thì không",
       [board["XUNG-01"]["brand"], board["XUNG-01"]["category_label"]],
       [None, "Tivi"])

    # --- DEC-206: ba alias Owner chốt sau Independent Review vòng 2 -------
    ok('DEC-206: "TV" ⟹ category_label "Tivi"',
       board["TV-01"]["category_label"], "Tivi")
    ok('DEC-206: "Máy giặt sấy LG" ⟹ category "Máy giặt", brand "LG"',
       [board["MGS-01"]["category_label"], board["MGS-01"]["brand"]],
       ["Máy giặt", "LG"])

    # Mệnh đề trung tâm của REPAIR-1, đo trên payload thật: mọi nhãn đi qua
    # ranh giới đều thuộc từ điển đóng. Từ điển đọc NGƯỢC từ `src/index.js`
    # chứ không gõ lại ở đây — gõ lại là hai danh sách trôi khỏi nhau.
    tu_dien = set(re.findall(r"^  \['([^']+)',",
                             (tracking / "src/index.js").read_text(encoding="utf-8"),
                             re.M))
    ok("từ điển đọc được từ src/index.js", len(tu_dien) > 0, True)
    nhan = [v["category_label"] for v in board.values()
            if v["category_label"] is not None]
    ok("MỌI nhãn đi qua ranh giới đều thuộc từ điển đóng",
       sorted(set(nhan) - tu_dien), [])

    ok("alias.map mang stale target, Tracking KHÔNG gộp sẵn (INV-16)",
       alias["map"], {"CU-01": "55Q6FA"})

    # Rò dữ liệu — soi chuỗi ĐÃ serialize, không soi dict.
    chu = json.dumps(payload, ensure_ascii=False)
    # Mỗi marker dưới đây CHỈ xuất hiện trong `cat`/nhánh riêng tư của BOARD,
    # không xuất hiện trong `name` của bất kỳ dòng nào — `name` là trường ĐƯỢC
    # PHÉP đi ra, nên một marker trùng `name` sẽ báo rò một thứ không rò.
    for khoa, vi in [('"cat"', "khoá ngành hàng"),
                     ("kho anh Ba", "ghi chú trong cat"),
                     ("Hòa Phát", "hãng lạ trong cat"),
                     ("Đất Việt", "tên NCC"), ('"p"', "giá vốn"),
                     ('"tp"', "giá chốt"), ('"_c"', "số Engine"),
                     ('"q"', "tồn kho"), ('"bb"', "giá bán buôn"),
                     ("tinphat.vn", "link nội bộ")]:
        ok("không lộ " + vi, khoa in chu, False)

    # ĐỐI CHỨNG: các marker ấy CÓ trong dữ liệu thô mà producer đọc vào, nên
    # phép thử trên đo được thật chứ không xanh vì marker không tồn tại.
    tho = (tracking / "kiem/smoke/sinh-catalog-reports.mjs").read_text(
        encoding="utf-8")
    ok("đối chứng: marker có thật trong BOARD thô của producer",
       [x for x in ("kho anh Ba", "Hòa Phát", "Đất Việt", "tinphat.vn")
        if x not in tho], [])

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
    ok("XUNG-01: hãng None, nhóm hàng Tivi",
       ba_truong("XUNG-01"), (None, None, "Tivi"))
    ok("BAN-01: `cat` bẩn ⟹ nhóm hàng None qua tới snapshot",
       ba_truong("BAN-01")[2], None)
    ok("ML-01: nhãn canonical qua tới snapshot",
       ba_truong("ML-01")[2], "Điều hoà")
    ok("DEC-206: TV-01 ⟹ Tivi qua tới snapshot", ba_truong("TV-01")[2], "Tivi")
    # model_label ở đây là "FV1412" — modelCua() rút nó từ chính `name`
    # ("Máy giặt sấy LG FV1412"), độc lập với category_label. Bài này chỉ
    # canh CATEGORY và BRAND, đúng phạm vi của DEC-206.
    ok("DEC-206: MGS-01 ⟹ category Máy giặt + brand LG qua tới snapshot",
       (ba_truong("MGS-01")[1], ba_truong("MGS-01")[2]), ("LG", "Máy giặt"))
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
    chieu = json.loads(display_path.read_text(encoding="utf-8"))
    ok("bản chiếu giữ mọi dòng CÓ ít nhất một trường",
       sorted(chieu),
       ["55Q6FA", "BAN-01", "BAN-02", "MGS-01", "ML-01", "RT38", "TV-01",
        "VS-01", "XUNG-01"])
    ok("DEC-206: TV-01/MGS-01 hiện đúng nhãn trong bản chiếu",
       [chieu["TV-01"]["category_label"], chieu["MGS-01"]["category_label"]],
       ["Tivi", "Máy giặt"])
    ok("...và BAN-01/BAN-02 có mặt vì HÃNG, nhóm hàng của chúng vẫn None",
       [chieu["BAN-01"]["category_label"], chieu["BAN-02"]["category_label"]],
       [None, None])
    ok("BAN-03 không có gì để nói nên không chiếm chỗ", "BAN-03" in chieu, False)

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

    # === 5. REPAIR-2: LUỒNG UPLOAD/RUN, KHÔNG mở bảng chọn ===============
    #
    # Bốn mục §4 ở trên đi qua route POST `phan-loai`, tức đúng cái luồng mà
    # bản chiếu hiển thị VỐN ĐÃ được ghi. Lỗi production nằm ở luồng CÒN LẠI:
    # Owner upload sổ rồi bấm chạy, KHÔNG mở bảng chọn của dòng nào — và trước
    # `R5.1 REPAIR-2` thì bản chiếu không bao giờ được ghi trên đường đó.
    #
    # Mục này dựng lại đúng luồng ấy trên một app HOÀN TOÀN MỚI, với bản chiếu
    # bị XOÁ trước khi chạy (mô phỏng đĩa ephemeral sau một lần deploy).
    print("\n5) REPAIR-2: upload/run THẬT, KHÔNG mở bảng chọn phân loại")
    import io as _io

    from app import beta_telemetry, owner_usability
    from tests.fixtures.synthetic_workbook import build_synthetic_workbook

    run_tmp = tmp / "repair2"
    run_tmp.mkdir(parents=True, exist_ok=True)
    workbook = run_tmp / "so_ke_toan.xlsx"
    build_synthetic_workbook(workbook)

    # Cùng capture danh mục THẬT do producer Tracking sinh ở §1–§2, chỉ thêm
    # một mã khớp đúng tên hàng của workbook tổng hợp để có gì mà hiển thị.
    board_run = {**board, "MGS-01": {**board["MGS-01"],
                                     "alt": ["Máy giặt Test-1"]}}
    envelope_run = capture.build_capture(
        lambda node: {"board": board_run, "alias": alias}[node],
        capture_id="TRK-REPAIR2", captured_by="r51-repair2-smoke",
        source_system_ref="tracking/api/xuat")
    cap_run = run_tmp / "catalog.json"
    cap_run.write_text(json.dumps(envelope_run, ensure_ascii=False),
                       encoding="utf-8")
    snapshot_run = load_tracking_catalog_capture(cap_run)

    # §4 ở trên đã thay `_select_captures_for_run` bằng một lambda không nhận
    # tham số; `run_report` gọi nó VỚI `sales=`/`identity_store_view=`, nên §5
    # phải đặt lại nó cho đúng chữ ký. Nó trả về ĐÚNG capture danh mục mà
    # producer Tracking vừa sinh — tức đúng thứ mà một lần chạy production có
    # trong tay.
    web_server._select_captures_for_run = (
        lambda sales=None, identity_store_view=None: (
            SelectedCaptures(
                tracking_capture=None, tracking_catalog=cap_run,
                tracking_inv_map=None, tracking_daily_min=None),
            {"catalog_capture_id": "TRK-REPAIR2"}, None))
    live_pull.is_configured = lambda env=None: True
    web_server.load_tracking_catalog_capture = lambda path: snapshot_run
    web_server.UPLOAD_DIR = run_tmp / "uploads"
    web_server.ARTIFACT_DIR = (run_tmp / "outputs" / "reports").resolve()
    web_server.TRACKING_TEMP_DIR = run_tmp / "tracking_live_tmp"
    beta_telemetry.record_run = lambda record, **kw: None
    _real_owner_run = owner_usability.run_owner_report
    web_server.run_owner_report = (
        lambda *, sales, captures=None, identity_store_view=None:
        _real_owner_run(sales=sales, captures=captures, repo_root=run_tmp,
                        identity_store_view=identity_store_view))

    engine2 = create_engine("sqlite://")
    history_db.create_all_for_test(engine2)
    repo2 = history_store.SnapshotRepository(engine2)
    store2 = fx.store(run_tmp)
    identity_gateway.build_store = lambda: store2

    app2 = web_server.create_app(
        db_path=run_tmp / "runs.db",
        history=history_store.LegacyRepository(engine2), snapshots=repo2)
    app2.testing = True
    client2 = app2.test_client()

    # Xác nhận mapping qua ĐÚNG cổng identity_gateway, trên store mà app dùng.
    identity_gateway.confirm_identity(
        app2.config["IDENTITY_STORE"], product_raw="Máy giặt Test-1",
        tracking_code="MGS-01", snapshot=snapshot_run,
        actor_id="r51-repair2-smoke", affected_orders=("BH0001",),
        affected_lines=1)

    # Đĩa ephemeral: bản chiếu KHÔNG tồn tại trước khi chạy.
    display_path.unlink(missing_ok=True)
    ok("trước khi chạy: bản chiếu KHÔNG tồn tại", display_path.exists(), False)

    resp = client2.post("/run", data={
        "workbook": (_io.BytesIO(workbook.read_bytes()), workbook.name)},
        content_type="multipart/form-data")
    ok("upload/run thành công (302)", resp.status_code, 302)
    ok("run THÀNH CÔNG đã ghi bản chiếu", display_path.exists(), True)

    record = app2.config["RUN_REGISTRY"].list_runs(limit=1)[0]
    ok("bằng chứng của run ghi trạng thái bản chiếu",
       (record.tracking_evidence or {}).get("catalog_display", {}).get("written"),
       True)

    def rows_of_sheet(employee):
        r = client2.get(f"/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien={employee}")
        assert r.status_code == 200, r.status_code
        html = r.get_data(as_text=True)
        import html as _H
        def text(cell):
            return " ".join(_H.unescape(re.sub(r"<[^>]+>", " ", cell)).split())
        return {name: [text(v) for v in re.findall(
            rf'data-metric="{name}"[^>]*>(.*?)</td>', html, re.S)]
            for name in ("line-product", "line-brand", "line-category")}, html

    seen, html_ly = rows_of_sheet("Ly")
    ok("KHÔNG mở bảng chọn: cột Mặt hàng hiện MODEL NGẮN từ Tracking",
       "FV1412" in seen["line-product"], True)
    ok("...và tên dài trên sổ kế toán đã biến khỏi dòng đã xác nhận",
       "Máy giặt Test-1" in seen["line-product"], False)
    ok("cột Hãng hiện brand từ Tracking", "LG" in seen["line-brand"], True)
    ok("cột Nhóm hàng hiện category_label", "Máy giặt" in seen["line-category"], True)
    ok("dòng CHƯA xác nhận vẫn giữ tên gốc và dấu gạch",
       ("Bình nóng lạnh Test-5" in seen["line-product"]
        and "—" in seen["line-brand"]), True)
    ok("bản chiếu lành ⟹ KHÔNG có cảnh báo",
       'data-metric="catalog-projection-warning"' in html_ly, False)

    # Mất bản chiếu ⟹ CẢNH BÁO, không im lặng.
    display_path.unlink()
    _seen2, html_missing = rows_of_sheet("Ly")
    ok("mất bản chiếu ⟹ tab Nhân viên CẢNH BÁO",
       'data-metric="catalog-projection-warning"' in html_missing, True)

    print(f"\nKẾT QUẢ SMOKE: {DAT} PASS, {HONG} FAIL")
    return 1 if HONG else 0


if __name__ == "__main__":
    sys.exit(main())
