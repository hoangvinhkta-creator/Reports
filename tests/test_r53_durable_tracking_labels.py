"""R5.3 — Hãng/Nhóm hàng phải SỐNG QUA restart, không chỉ qua một lần chạy.

## Lỗi production mà file này đóng lại

`R5.1 REPAIR-2` đã bắt `POST /run` ghi bản chiếu hiển thị (`mã Tracking →
model · hãng · nhóm hàng`) từ capture Tracking của CHÍNH lần chạy đó, và
`tests/test_r51_repair2_run_refreshes_projection.py` chứng minh nó chạy. Bản
sửa ấy đúng nhưng CHƯA đủ: nó ghi ra một FILE trên đĩa máy chủ.

Trên Render, đĩa ấy là EPHEMERAL. Mỗi lần deploy hay restart, file biến mất.
Con số của kỳ thì KHÔNG — chúng nằm trong database. Đo trực tiếp trên đường
thật, trước bản sửa `R5.3`:

```text
upload sổ → POST /run → tab Nhân viên   Mặt hàng "QLED 55Q6FA" · Hãng
                                        "Samsung" · Nhóm hàng "Tivi"
xoá đĩa ephemeral (đúng việc Render làm ở mỗi deploy)
mở LẠI tab Nhân viên, CÙNG lần chạy ấy  Hãng "—" · Nhóm hàng "—", VĨNH VIỄN
```

Không đường nào dựng lại được bản chiếu, nên trạng thái "chưa có nhãn" là
vĩnh viễn cho tới lần chạy báo cáo kế tiếp — và một Owner mở lại báo cáo của
tuần trước sau một lần deploy sẽ không bao giờ thấy nhãn nào.

`R5.3` thêm nửa BỀN của chính bản chiếu ấy (`tracking_display_snapshot`,
khoá theo `run_id`), và tầng trình bày dựng lại từ đó khi cache đĩa vắng —
KHÔNG gọi Tracking lần nào, KHÔNG suy một chữ nào từ tên trên sổ kế toán.

## Vì sao mọi bài ở đây đi qua `POST /run` thật

Cùng lý do `R5.1 REPAIR-2` đã ghi: tầng trình bày và tầng hợp đồng đều ĐÚNG
từ trước, nên một bài ở tầng đó sẽ xanh cả trước lẫn sau bản sửa. Lỗi chỉ
nhìn thấy được trên đường người dùng thật, và "restart" phải được mô phỏng
bằng cách dọn ĐÚNG những gì Render dọn: đĩa — không phải database.
"""

from __future__ import annotations

import html as html_module
import io
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text as sql_text

import tools.db as history_db
from app import beta_telemetry, owner_usability
from app.web import catalog_display, history_store, identity_gateway
from app.web import server as web_server
from tools.tracking import live_pull

from tests.fixtures.synthetic_workbook import build_synthetic_workbook
from tests.support import identity_fixtures as fx

# --- Danh mục Tracking của các bài dưới đây --------------------------------
#
# Bốn mã, mỗi mã dựng một ca mà `R5.3` phải trả lời khác nhau.

#: Đã CONFIRMED, đủ ba trường. Ca chính.
CODE_FULL = "55Q6FA"
MODEL_FULL = "QLED 55Q6FA"
BRAND_FULL = "Samsung"
CATEGORY_FULL = "Tivi"
RAW_FULL = "Máy lạnh Test-2"

#: Đã CONFIRMED nhưng Tracking KHÔNG khẳng định hãng (`brand=None`), có nhóm
#: hàng. Nhóm hàng phải hiện, Hãng phải là `—` — không mượn tên trên sổ.
CODE_NO_BRAND = "RT38"
MODEL_NO_BRAND = "RT38"
CATEGORY_NO_BRAND = "Tủ lạnh"
RAW_NO_BRAND = "Tủ lạnh Test-3"

#: KHÔNG xác nhận gì cả, và tên trên sổ NHÌN GIỐNG một cặp hãng/nhóm hàng
#: ("Tivi" + "Test-7"). Nó phải hiện `—` — đúng chỗ một phép suy từ tên kế
#: toán sẽ lộ ra nếu có ai lỡ viết một phép suy như thế.
RAW_LOOKS_LIKE_A_BRAND = "Tivi Test-7"

EMPLOYEE_FULL = "Hoàng"        # sheet chứa BH0002 (RAW_FULL, RAW_NO_BRAND)
EMPLOYEE_LOOKALIKE = "Vinh"    # sheet chứa BH0006 (RAW_LOOKS_LIKE_A_BRAND)


def catalog_rows(*, with_metadata: bool = True,
                 brand_for_no_brand: bool = False) -> list[dict]:
    """Dòng danh mục của capture Tracking cho lần chạy này.

    `with_metadata=False` dựng đúng hình dạng artifact ĐỜI CŨ (`R5` trước §5):
    chỉ `tracking_code`/`name`/`alt`. Nó phải đọc được y như cũ và fallback an
    toàn — đó là mệnh đề tương thích ngược, không phải một ca lỗi.
    """
    full = {"tracking_code": CODE_FULL, "name": "Tivi Samsung QLED 55Q6FA",
            "alt": [RAW_FULL], "present_in_board": True}
    no_brand = {"tracking_code": CODE_NO_BRAND, "name": "Tủ lạnh Samsung RT38",
                "alt": [RAW_NO_BRAND], "present_in_board": True}
    if with_metadata:
        full |= {"model_label": MODEL_FULL, "brand": BRAND_FULL,
                 "category_label": CATEGORY_FULL}
        # `brand` VẮNG MẶT hoàn toàn — đúng cách Tracking nói "không khẳng
        # định" (`chieuBoard()` chiếu `null`, và capture tool bỏ hẳn khoá).
        no_brand |= {"model_label": MODEL_NO_BRAND,
                     "category_label": CATEGORY_NO_BRAND}
        if brand_for_no_brand:
            no_brand |= {"brand": BRAND_FULL}
    return [full, no_brand]


def write_catalog_capture(path: Path, rows: list[dict], *,
                          capture_id: str = "TRK-CAT-R53") -> Path:
    path.write_text(json.dumps({
        "capture_id": capture_id,
        "captured_at": datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
        "captured_by": "reports-live-pull",
        "source_system_ref": "tracking/api/xuat",
        "content_hash": "hash-" + capture_id,
        "capture_status": "COMPLETE",
        "rows": rows,
    }, ensure_ascii=False), encoding="utf-8")
    return path


# --- Bộ khung: app THẬT, `/run` THẬT, đĩa THẬT ----------------------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def workbook(tmp_path) -> Path:
    path = tmp_path / "so_ke_toan.xlsx"
    build_synthetic_workbook(path)
    return path


@pytest.fixture
def projection_path(tmp_path, monkeypatch) -> Path:
    """Cache đĩa của bản chiếu, bắt đầu ở trạng thái KHÔNG TỒN TẠI — đúng
    trạng thái production sau một lần deploy."""
    path = tmp_path / "projection" / "tracking_display.json"
    monkeypatch.setattr(catalog_display, "DEFAULT_DISPLAY_PATH", path)
    return path


def set_live_catalog(monkeypatch, path: Path, rows: list[dict], *,
                     capture_id: str = "TRK-CAT-R53") -> Path:
    """`live_pull` đã cấu hình và trả về ĐÚNG capture này cho lần chạy sau."""
    catalog = write_catalog_capture(path, rows, capture_id=capture_id)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)

    def fake_pull(*, out_dir, sales=None, identity_store_view=None, **kwargs):
        return live_pull.LiveSelectedCaptures(
            tracking_capture=None, tracking_catalog=catalog,
            tracking_inv_map=None, tracking_daily_min=None,
            evidence={"tracking_catalog_capture_id": capture_id},
            temp_paths=())

    monkeypatch.setattr(live_pull, "pull_live_captures", fake_pull)
    return catalog


@pytest.fixture
def live_catalog(tmp_path, monkeypatch) -> Path:
    return set_live_catalog(monkeypatch, tmp_path / "tracking_catalog.json",
                            catalog_rows())


@pytest.fixture
def app(engine, tmp_path, monkeypatch):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR",
                        (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "TRACKING_TEMP_DIR",
                        tmp_path / "tracking_live_tmp")
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    real = owner_usability.run_owner_report
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales, captures=None, identity_store_view=None: real(
            sales=sales, captures=captures, repo_root=tmp_path,
            identity_store_view=identity_store_view))
    monkeypatch.setattr(web_server, "_today", lambda: date(2026, 1, 31))
    monkeypatch.setattr(web_server.identity_gateway, "DEFAULT_LOG_PATH",
                        tmp_path / "identity" / "mappings.jsonl")
    monkeypatch.setattr(web_server.identity_gateway, "DEFAULT_INDEX_PATH",
                        tmp_path / "identity" / "index.json")
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def identity_store(app):
    store = app.config["IDENTITY_STORE"]
    assert store is not None, "app phải có store Product Identity thật"
    return store


def confirm(store, *, product_raw: str, code: str, orders=("BH0002",)):
    """Xác nhận mapping qua ĐÚNG cổng `identity_gateway.confirm_identity`."""
    snapshot = fx.tracking_snapshot([(code, "Tên trên Tracking",
                                      (product_raw,), True)])
    return identity_gateway.confirm_identity(
        store, product_raw=product_raw, tracking_code=code, snapshot=snapshot,
        actor_id="test-owner", affected_orders=tuple(orders), affected_lines=1)


def upload(client, workbook: Path):
    response = client.post("/run", data={
        "workbook": (io.BytesIO(workbook.read_bytes()), workbook.name)},
        content_type="multipart/form-data")
    assert response.status_code == 302, (
        f"run phải thành công, nhận {response.status_code}: "
        f"{response.get_data(as_text=True)[:400]}")
    return response


def restart_the_container(projection_path: Path) -> None:
    """Mô phỏng ĐÚNG việc Render làm ở mỗi deploy/restart: đĩa ephemeral bị
    thay mới, database KHÔNG bị đụng.

    Dọn CẢ file trạng thái cạnh bản chiếu (`*.status.json`) — nó cũng nằm trên
    đúng cái đĩa ấy, và giữ lại nó sẽ dựng một trạng thái mà production không
    bao giờ có: "bản chiếu mất nhưng lịch sử ghi của nó còn".
    """
    folder = projection_path.parent
    if not folder.exists():
        return
    for path in folder.glob("*"):
        if path.is_file():
            path.unlink()


def wipe_durable_display(engine) -> None:
    """Dọn nửa BỀN — để dựng ca "chưa lần chạy nào ghi được nó"."""
    with engine.begin() as connection:
        connection.execute(sql_text("DELETE FROM tracking_display_snapshot"))


def _text(cell: str) -> str:
    return " ".join(html_module.unescape(re.sub(r"<[^>]+>", " ", cell)).split())


def cells(html: str, name: str) -> list[str]:
    return [_text(value) for value in re.findall(
        rf'data-metric="{re.escape(name)}"[^>]*>(.*?)</td>', html, re.S)]


def employee_page(client, *, employee: str = EMPLOYEE_FULL) -> str:
    response = client.get(
        f"/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien={employee}")
    assert response.status_code == 200, response.status_code
    html = response.get_data(as_text=True)
    assert cells(html, "line-product"), (
        f"sheet của {employee!r} không có dòng nào — bài kiểm sẽ xanh giả")
    return html


def row_of(html: str, product: str) -> str:
    for block in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        if product in block:
            return block
    raise AssertionError(f"không thấy dòng cho {product!r}")


def field_of(html: str, product: str, metric: str) -> str:
    block = row_of(html, product)
    match = re.search(rf'data-metric="{metric}"[^>]*>(.*?)</td>', block, re.S)
    assert match is not None, f"dòng {product!r} không có ô {metric}"
    return _text(match.group(1))


TOTAL_METRICS = ("totals-purchase", "totals-sell", "totals-profit",
                 "totals-converted")


def totals(client, *, employee: str = EMPLOYEE_FULL) -> dict:
    """Mọi con số của bảng kê mà một bản sửa NHÃN không được đụng.

    Bốn ô của dòng TỔNG (giá nhập · giá bán · lợi nhuận · DS quy đổi) CỘNG số
    dòng hàng: một bản sửa làm mất/thêm một dòng sẽ không đổi tổng nếu dòng ấy
    rỗng, nên chỉ so tổng thôi là chưa đủ.
    """
    html = employee_page(client, employee=employee)
    measured = {metric: cells(html, metric) for metric in TOTAL_METRICS}
    measured["so_dong"] = [str(len(cells(html, "line-product")))]
    return measured


def run_evidence(app) -> dict:
    store = app.config["RUN_REGISTRY"]
    runs = store.list_runs(limit=1)
    assert runs, "phải có ít nhất một run"
    return store.get_run(runs[0].run_id).tracking_evidence or {}


# --- 1. Luồng chính: một lần chạy ⟹ ba ô, KHÔNG mở bảng chọn -------------

def test_a_confirmed_line_shows_model_brand_and_category_after_one_run(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """Mệnh đề của `R5` §5 + `R5.1` §5, đo lại ở đây làm NỀN cho các bài dưới.

    KHÔNG có lời gọi `?phan-loai=` nào: nếu bảng chỉ đúng sau khi mở popover
    thì bản sửa chưa chạm luồng chính.
    """
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    html = employee_page(client)
    assert field_of(html, MODEL_FULL, "line-product") == MODEL_FULL
    assert field_of(html, MODEL_FULL, "line-brand") == BRAND_FULL
    assert field_of(html, MODEL_FULL, "line-category") == CATEGORY_FULL
    # Tên dài trên sổ biến khỏi Ô — nhưng vẫn đọc được qua tooltip (`R5.3`
    # §UI): nó là thứ Owner dùng để đối chiếu với đơn thật, nên nó không được
    # mất hẳn, chỉ không được chiếm chỗ của model canonical.
    assert RAW_FULL not in cells(html, "line-product")
    assert f'title="{RAW_FULL}"' in row_of(html, MODEL_FULL)


def test_the_run_stores_the_labels_durably_with_the_capture_it_used(
    app, client, workbook, live_catalog, projection_path, identity_store,
    engine,
):
    """Bản BỀN phải mang NGUYÊN VĂN nhãn của capture lần chạy đó, và nói ra
    capture nào — bằng chứng nhãn này đến từ ĐÂU, không phải một bảng danh mục
    Reports tự dựng."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)

    stored = history_store.SnapshotRepository(engine).latest_tracking_display()
    assert stored is not None, "lần chạy thành công KHÔNG lưu bền bản chiếu"
    assert stored["capture_id"] == "TRK-CAT-R53"
    assert stored["rows"][CODE_FULL] == {
        "model_label": MODEL_FULL, "brand": BRAND_FULL,
        "category_label": CATEGORY_FULL}
    # …và bằng chứng của run nói ra CẢ HAI nơi lưu, tách bạch.
    evidence = run_evidence(app)["catalog_display"]
    assert evidence["written"] is True
    assert evidence["durable"] == {"written": True, "rows": 2, "reason": None}


# --- 2. RESTART: đúng lỗi production mà `R5.3` sửa ------------------------

def test_the_labels_survive_a_container_restart(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """ĐỎ trước `R5.3`: xoá đĩa ephemeral ⟹ Hãng/Nhóm hàng `—` VĨNH VIỄN.

    Đây là bài trung tâm của `R5.3`. Nó KHÔNG chạy lại báo cáo sau khi
    "restart" — chạy lại là cách CŨ để dựng lại nhãn, và cách ấy đòi Owner
    phải nạp lại sổ mỗi lần Render deploy.
    """
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    assert field_of(employee_page(client), MODEL_FULL, "line-brand") == BRAND_FULL

    restart_the_container(projection_path)
    assert not projection_path.exists()

    html = employee_page(client)
    assert field_of(html, MODEL_FULL, "line-product") == MODEL_FULL
    assert field_of(html, MODEL_FULL, "line-brand") == BRAND_FULL
    assert field_of(html, MODEL_FULL, "line-category") == CATEGORY_FULL


def test_the_rebuild_writes_the_disk_cache_back(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """Dựng lại rồi ghi lại cache: lần tải trang SAU không phải hỏi database
    nữa. Một trang bảng kê được mở hàng chục lần một buổi."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    restart_the_container(projection_path)
    employee_page(client)
    assert projection_path.exists(), "bản chiếu dựng lại KHÔNG được ghi lại cache"
    assert json.loads(projection_path.read_text(encoding="utf-8"))[
        CODE_FULL]["brand"] == BRAND_FULL


def test_the_rebuild_never_pulls_tracking(
    client, workbook, live_catalog, projection_path, identity_store,
    monkeypatch,
):
    """Dựng lại đọc DATABASE, không đọc Tracking. Một lần pull cho mỗi lần mở
    bảng kê là đúng thứ `S071` §10 cấm."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    restart_the_container(projection_path)

    def forbidden(**kwargs):
        raise AssertionError("render bảng kê KHÔNG được gọi Tracking")

    monkeypatch.setattr(live_pull, "pull_live_captures", forbidden)
    assert field_of(employee_page(client), MODEL_FULL, "line-brand") == BRAND_FULL


def test_exactly_one_tracking_pull_per_run(
    client, workbook, live_catalog, projection_path, identity_store,
    monkeypatch, tmp_path,
):
    """`R5.3` §Thiết kế — một lượt `/run` chỉ pull Tracking ĐÚNG MỘT LẦN, và
    CÙNG capture ấy phục vụ cả giá lẫn nhãn (bền lẫn cache)."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    catalog = write_catalog_capture(tmp_path / "cat-count.json", catalog_rows())
    calls = []

    def counting(*, out_dir, sales=None, identity_store_view=None, **kwargs):
        calls.append(1)
        return live_pull.LiveSelectedCaptures(
            tracking_capture=None, tracking_catalog=catalog,
            tracking_inv_map=None, tracking_daily_min=None,
            evidence={"tracking_catalog_capture_id": "TRK-CAT-R53"},
            temp_paths=())

    monkeypatch.setattr(live_pull, "pull_live_captures", counting)
    upload(client, workbook)
    assert calls == [1], f"một lần chạy phải pull Tracking đúng 1 lần, đếm {len(calls)}"


# --- 3. Capture ĐỜI CŨ: tương thích ngược, không đoán --------------------

def test_a_legacy_capture_without_the_new_fields_never_crashes_or_guesses(
    app, client, workbook, projection_path, identity_store, tmp_path,
    monkeypatch,
):
    """Capture `R5` đời cũ (không `model_label`/`brand`/`category_label`) phải
    chạy được y như cũ: run thành công, ba ô hiện dấu gạch, và bằng chứng NÓI
    RA lý do (`NO_METADATA`) thay vì để người đọc đoán."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    set_live_catalog(monkeypatch, tmp_path / "legacy.json",
                     catalog_rows(with_metadata=False),
                     capture_id="TRK-CAT-LEGACY")
    upload(client, workbook)

    html = employee_page(client)
    # Đã CONFIRMED nên tên thô được thay bằng MÃ Tracking (`R5` §5), nhưng
    # KHÔNG có hãng và KHÔNG có nhóm hàng để nói.
    assert field_of(html, CODE_FULL, "line-brand") == "—"
    assert field_of(html, CODE_FULL, "line-category") == "—"

    evidence = run_evidence(app)["catalog_display"]
    assert evidence["reason"] == catalog_display.REASON_NO_METADATA
    # Nhánh BỀN theo ĐÚNG luật của cache đĩa: một capture không mang nhãn nào
    # thì KHÔNG ghi đè thứ đang có. Hai nơi lưu lệch luật ở đây sẽ cho hai màn
    # hình khác nhau cho cùng một lần chạy, tuỳ vào việc đĩa còn hay mất.
    assert evidence["durable"] == {"written": False, "rows": 0,
                                   "reason": catalog_display.REASON_NO_METADATA}


def test_a_legacy_capture_does_not_erase_labels_an_earlier_run_stored(
    client, workbook, live_catalog, projection_path, identity_store, tmp_path,
    monkeypatch,
):
    """Một capture đời cũ đến SAU không được xoá nhãn mà một lần chạy trước đã
    đọc được — kể cả sau restart. Làm màn hình nói ÍT hơn vì một artifact cũ
    là một hồi quy, không phải một phép thận trọng."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    set_live_catalog(monkeypatch, tmp_path / "legacy2.json",
                     catalog_rows(with_metadata=False),
                     capture_id="TRK-CAT-LEGACY-2")
    upload(client, workbook)
    restart_the_container(projection_path)

    html = employee_page(client)
    assert field_of(html, MODEL_FULL, "line-brand") == BRAND_FULL, (
        "một capture đời cũ đã xoá nhãn của lần chạy trước")


# --- 4. Trạng thái mapping quyết định, KHÔNG phải tên trên sổ -------------

def test_an_unclassified_line_stays_dashed_even_when_its_name_looks_like_a_brand(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """`Tivi Test-7` chưa ai xác nhận. Tên nó chứa đúng chữ mà cột Nhóm hàng
    đang hiện cho một dòng khác — và nó vẫn phải là `—`. Đây là bài duy nhất
    bắt được một phép suy từ tên kế toán nếu có ai lỡ viết một phép suy như
    thế (`ADR-111` §3)."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    html = employee_page(client, employee=EMPLOYEE_LOOKALIKE)
    assert field_of(html, RAW_LOOKS_LIKE_A_BRAND, "line-product") == \
        RAW_LOOKS_LIKE_A_BRAND
    assert field_of(html, RAW_LOOKS_LIKE_A_BRAND, "line-brand") == "—"
    assert field_of(html, RAW_LOOKS_LIKE_A_BRAND, "line-category") == "—"


def test_the_same_holds_after_a_restart(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """Phép chặn theo trạng thái mapping không được nới ra ở đường DỰNG LẠI.

    Đây là rủi ro thật của `R5.3`: một đường đọc thứ hai là một chỗ thứ hai để
    quên mất phép chặn `§5.4`.
    """
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    restart_the_container(projection_path)
    html = employee_page(client, employee=EMPLOYEE_LOOKALIKE)
    assert field_of(html, RAW_LOOKS_LIKE_A_BRAND, "line-brand") == "—"
    assert field_of(html, RAW_LOOKS_LIKE_A_BRAND, "line-category") == "—"


def test_an_out_of_catalog_line_gets_no_label_after_a_restart(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """`OUT_OF_CATALOG` là một quyết định "dòng này KHÔNG có mã", nên nó không
    có nhãn nào để nhận — trước hay sau restart."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    identity_gateway.mark_out_of_catalog(
        identity_store, product_raw=RAW_NO_BRAND,
        actor_id="test-owner", affected_orders=("BH0002",), affected_lines=1)
    upload(client, workbook)
    restart_the_container(projection_path)
    html = employee_page(client)
    assert field_of(html, RAW_NO_BRAND, "line-brand") == "—"
    assert field_of(html, RAW_NO_BRAND, "line-category") == "—"
    assert field_of(html, RAW_NO_BRAND, "line-product") == RAW_NO_BRAND


def test_a_min_price_without_a_confirmed_mapping_earns_no_label(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """`R5.3` §4 — giá MIN có hay không KHÔNG quyết định việc hiện nhãn.

    Lần chạy này KHÔNG xác nhận mapping nào, nhưng bản chiếu VẪN được ghi đầy
    đủ (nó mang mọi mã của capture, không chỉ mã đã xác nhận). Nếu điều kiện
    hiển thị có lúc nào đó trượt từ "đã CONFIRMED" sang "có mặt trong bản
    chiếu", bài này đỏ.
    """
    upload(client, workbook)
    html = employee_page(client)
    assert field_of(html, RAW_FULL, "line-brand") == "—"
    assert field_of(html, RAW_FULL, "line-category") == "—"
    assert field_of(html, RAW_FULL, "line-product") == RAW_FULL


def test_a_confirmed_code_with_no_brand_shows_the_category_and_dashes_the_brand(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """`R5.3` §6 — hai trường trả lời hai câu KHÁC NHAU, nên một trường vắng
    không được kéo trường kia xuống theo, và cũng không được lấp bằng gì."""
    confirm(identity_store, product_raw=RAW_NO_BRAND, code=CODE_NO_BRAND)
    upload(client, workbook)
    restart_the_container(projection_path)
    html = employee_page(client)
    assert field_of(html, MODEL_NO_BRAND, "line-category") == CATEGORY_NO_BRAND
    assert field_of(html, MODEL_NO_BRAND, "line-brand") == "—"


# --- 5. Bản chiếu chỉ mang NHÃN: không đồng nào đổi ----------------------

def test_wiping_or_corrupting_the_cache_moves_no_money(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """`R5.3` §7 — xoá hay làm hỏng cache KHÔNG đổi doanh thu, lợi nhuận, SL,
    số dòng. Bản chiếu mang NHÃN, không mang tiền, và đó là lý do nó được phép
    sống trên một cái đĩa có thể mất."""
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    baseline = totals(client)
    assert all(baseline[metric] for metric in TOTAL_METRICS), (
        f"bảng kê phải có dòng tổng — nếu không bài kiểm vô nghĩa: {baseline}")

    restart_the_container(projection_path)
    assert totals(client) == baseline

    # …và một cache HỎNG (không phải JSON) cũng vậy: nó đọc thành rỗng rồi
    # được dựng lại, không thành một trang lỗi.
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_text("{ đây không phải JSON", encoding="utf-8")
    html = employee_page(client)
    assert field_of(html, MODEL_FULL, "line-brand") == BRAND_FULL
    assert totals(client) == baseline


def test_a_broken_durable_row_degrades_to_dashes_not_to_an_error(
    client, workbook, live_catalog, projection_path, identity_store, engine,
):
    """Hàng bền hỏng ⟹ màn hình nói ÍT đi, không nói SAI và không đổ vỡ.

    Cùng kỷ luật fail-safe mà `catalog_display.read()` áp cho file trên đĩa.
    """
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    restart_the_container(projection_path)
    with engine.begin() as connection:
        connection.execute(sql_text(
            "UPDATE tracking_display_snapshot SET rows_json = 'không-phải-json'"))
    html = employee_page(client)
    assert field_of(html, CODE_FULL, "line-brand") == "—"


def test_losing_both_places_still_warns_instead_of_going_silent(
    client, workbook, live_catalog, projection_path, identity_store, engine,
):
    """Mất CẢ HAI nơi lưu ⟹ cảnh báo của `R5.1 REPAIR-2` vẫn phải nổi lên.

    `R5.3` thêm một nơi lưu, KHÔNG gỡ một phép cảnh báo nào: một bảng đầy dấu
    gạch mà không lời nào giải thích vẫn là lỗi.
    """
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_FULL)
    upload(client, workbook)
    restart_the_container(projection_path)
    wipe_durable_display(engine)
    assert 'data-metric="catalog-projection-warning"' in employee_page(client)


# --- 6. Tầng lưu bền, đo trực tiếp ---------------------------------------

def test_the_durable_store_keeps_one_row_per_run_and_returns_the_latest(engine):
    """Ghi đè theo `run_id`, và "gần nhất" theo `created_at` — một lần chạy có
    ĐÚNG một capture danh mục, nên hai hàng cho cùng `run_id` chỉ có thể là
    cùng một sự thật viết hai lần."""
    repo = history_store.SnapshotRepository(engine)
    repo.write_tracking_display(
        run_id="run-1", rows={CODE_FULL: {"brand": BRAND_FULL}},
        created_at="2026-09-01T00:00:00+00:00", capture_id="CAP-1")
    repo.write_tracking_display(
        run_id="run-1", rows={CODE_FULL: {"brand": "Sony"}},
        created_at="2026-09-01T01:00:00+00:00", capture_id="CAP-1B")
    repo.write_tracking_display(
        run_id="run-2", rows={CODE_NO_BRAND: {"category_label": "Tủ lạnh"}},
        created_at="2026-09-02T00:00:00+00:00", capture_id="CAP-2")

    latest = repo.latest_tracking_display()
    assert latest["run_id"] == "run-2"
    assert latest["capture_id"] == "CAP-2"
    assert latest["rows"] == {CODE_NO_BRAND: {"category_label": "Tủ lạnh"}}
    with engine.connect() as connection:
        rows = connection.execute(sql_text(
            "SELECT run_id FROM tracking_display_snapshot")).fetchall()
    assert sorted(row[0] for row in rows) == ["run-1", "run-2"]


def test_an_empty_durable_row_reads_back_as_empty_not_as_missing(engine):
    """Đường ĐỌC phải phân biệt "có hàng, hàng rỗng" khỏi "không có hàng nào".

    Đường ghi của production không tạo ra hàng rỗng (`_persist_tracking_
    display` không ghi đè khi capture không mang nhãn nào), nhưng đường đọc
    VẪN gặp trạng thái này: một hàng có `rows_json` hỏng được đọc thành `{}`
    theo đúng kỷ luật fail-safe. Hai câu ấy dẫn tới hai lời giải thích khác
    nhau cho người đọc, nên chúng không được gộp làm một ở tầng đọc.
    """
    repo = history_store.SnapshotRepository(engine)
    assert repo.latest_tracking_display() is None
    repo.write_tracking_display(run_id="run-1", rows={},
                                created_at="2026-09-01T00:00:00+00:00")
    stored = repo.latest_tracking_display()
    assert stored is not None and stored["rows"] == {} and stored["row_count"] == 0


def test_the_durable_store_holds_no_money_column():
    """Bảng nhãn KHÔNG được mang một trường tiền nào — nếu nó mang, một lần
    mất bảng này sẽ đổi một con số, và toàn bộ lý lẽ "được phép mất" sụp."""
    from tools.db.schema import tracking_display_snapshot
    assert set(tracking_display_snapshot.c.keys()) == {
        "run_id", "capture_id", "captured_at", "rows_json", "row_count",
        "created_at"}
