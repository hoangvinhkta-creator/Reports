"""R5.1 REPAIR-2 — luồng UPLOAD/RUN phải làm mới bản chiếu hiển thị.

## Lỗi production mà file này đóng lại

Trên production, cột `Nhóm hàng` / `Hãng` / `IMEI` ĐÃ hiển thị (không bị ẩn),
nhưng `Hãng` là `—` và `Mặt hàng` vẫn là tên dài trên sổ kế toán — kể cả với
những dòng đã có mapping `CONFIRMED`.

Nguyên nhân nằm ở đúng một chỗ: `catalog_display` (bản chiếu
`mã Tracking → model_label · brand · category_label`) CHỈ được ghi trong
`server._tracking_snapshot()`, tức chỉ khi Owner **mở bảng chọn phân loại của
một dòng**. Luồng chạy báo cáo/upload thông thường — `POST /run` — không ghi và
không làm mới bản chiếu ấy. Trên đĩa ephemeral của Render, sau mỗi lần deploy
bản chiếu biến mất và không có gì dựng lại nó, nên cả bảng chỉ còn `—`.

Đây là lỗi LUỒNG CHÍNH, không phải accepted risk: `AR-R5.1-04` nói về việc
"chờ lần capture danh mục MỚI đầu tiên", và một lần chạy báo cáo THÀNH CÔNG
CHÍNH LÀ một lần capture danh mục mới — nó chỉ không được dùng.

## Vì sao test đi qua `POST /run` thật

Tầng trình bày đã ĐÚNG từ `R5` §5: `workspace_presentation._catalog_field`
tra bản chiếu và chặn đúng các trạng thái chưa xác nhận. Một bài kiểm ở tầng đó
sẽ XANH cả trước và sau bản sửa, nên nó không chứng minh gì. Lỗi chỉ nhìn thấy
được khi đi qua ĐÚNG luồng người dùng thật:

    upload workbook → POST /run → (KHÔNG mở popup phân loại) → mở tab Nhân viên
"""

from __future__ import annotations

import html as html_module
import io
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app import owner_usability
from app import beta_telemetry
from app.web import catalog_display, history_store, identity_gateway
from app.web import server as web_server
from tools.tracking import live_pull

from tests.fixtures.synthetic_workbook import build_synthetic_workbook
from tests.support import identity_fixtures as fx

#: Mã Tracking + ba trường hiển thị mà bản chiếu phải chở sang được.
TRACKING_CODE = "55Q6FA"
MODEL_LABEL = "55Q6FA"
BRAND = "Samsung"
CATEGORY = "Tivi"

#: Tên hàng THÔ trên sổ kế toán — dài, và là thứ production đang hiện thay cho
#: model ngắn. Nó phải trùng đúng một dòng của workbook tổng hợp.
RAW_PRODUCT = "Máy lạnh Test-2"


def catalog_rows(*, with_metadata: bool = True) -> list[dict]:
    """Dòng danh mục của capture Tracking cho lần chạy này.

    `with_metadata=False` dựng đúng hình dạng artifact ĐỜI CŨ (`R5` trước §5):
    chỉ `tracking_code`/`name`/`alt`, không có ba trường hiển thị. Nó phải
    fallback an toàn, không crash — yêu cầu tương thích capture cũ.
    """
    row = {"tracking_code": TRACKING_CODE, "name": "Tivi Samsung QLED 55Q6FA",
           "alt": [RAW_PRODUCT], "present_in_board": True}
    if with_metadata:
        row |= {"model_label": MODEL_LABEL, "brand": BRAND,
                "category_label": CATEGORY}
    return [row]


def write_catalog_capture(path: Path, rows: list[dict]) -> Path:
    path.write_text(json.dumps({
        "capture_id": "TRK-CAT-REPAIR2",
        "captured_at": datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
        "captured_by": "reports-live-pull",
        "source_system_ref": "tracking/api/xuat",
        "content_hash": "hash-repair2",
        "capture_status": "COMPLETE",
        "rows": rows,
    }, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def workbook(tmp_path) -> Path:
    # `build_synthetic_workbook` GHI file và trả `None`, nên đường dẫn phải do
    # bài kiểm tự giữ.
    path = tmp_path / "so_ke_toan.xlsx"
    build_synthetic_workbook(path)
    return path


@pytest.fixture
def projection_path(tmp_path, monkeypatch) -> Path:
    """Bản chiếu nằm ở tmp, và bắt đầu ở trạng thái KHÔNG TỒN TẠI.

    Đúng trạng thái production sau một lần deploy trên đĩa ephemeral — và đúng
    trạng thái mà bản sửa phải tự thoát ra khỏi.
    """
    path = tmp_path / "projection" / "tracking_display.json"
    monkeypatch.setattr(catalog_display, "DEFAULT_DISPLAY_PATH", path)
    return path


@pytest.fixture
def live_catalog(tmp_path, monkeypatch) -> Path:
    """Giả lập ĐÚNG nhánh production: `live_pull` đã cấu hình.

    Nó trả về capture danh mục THẬT trên đĩa (một file JSON đúng hợp đồng
    `load_tracking_catalog_capture`), nên `POST /run` đi qua cùng đường mà
    Render đi. Không mock `catalog_display` và không mock tầng trình bày —
    những chỗ ấy là chỗ đang được kiểm.
    """
    catalog = write_catalog_capture(tmp_path / "tracking_catalog.json",
                                    catalog_rows())
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)

    def fake_pull(*, out_dir, sales=None, identity_store_view=None, **kwargs):
        return live_pull.LiveSelectedCaptures(
            tracking_capture=None, tracking_catalog=catalog,
            tracking_inv_map=None, tracking_daily_min=None,
            evidence={"tracking_catalog_capture_id": "TRK-CAT-REPAIR2"},
            temp_paths=())

    monkeypatch.setattr(live_pull, "pull_live_captures", fake_pull)
    return catalog


@pytest.fixture
def identity_store(app):
    """CHÍNH store mà `create_app()` đã dựng cho ứng dụng này.

    KHÔNG dựng một store thứ hai rồi tiêm vào: `create_app` gọi
    `identity_gateway.build_store()` đúng MỘT LẦN và giữ kết quả ở
    `app.config["IDENTITY_STORE"]`, nên một store dựng ở fixture khác sẽ nằm ở
    một đường dẫn khác và mọi lần xác nhận trong bài kiểm sẽ vô hình với route.
    Đó chính là cái bẫy đã làm bài kiểm của file này đỏ vì sai lý do ở lần chạy
    đầu.
    """
    store = app.config["IDENTITY_STORE"]
    assert store is not None, "app phải có store Product Identity thật"
    return store


def confirm(store, *, product_raw=RAW_PRODUCT, code=TRACKING_CODE,
            rows=None):
    """Xác nhận mapping qua ĐÚNG cổng `identity_gateway.confirm_identity`.

    Không ghi tay vào log: cổng đó là nơi `INV-01` và các bất biến idempotency
    sống, và một mapping dựng tay sẽ bỏ qua chính những phép chặn mà bài kiểm
    dựa vào ở các ca "chưa xác nhận".
    """
    snapshot = fx.tracking_snapshot(
        rows or [(code, "Tivi Samsung QLED 55Q6FA", (product_raw,), True)])
    return identity_gateway.confirm_identity(
        store, product_raw=product_raw, tracking_code=code, snapshot=snapshot,
        actor_id="test-owner", affected_orders=("BH0002",), affected_lines=1)


@pytest.fixture
def app(engine, tmp_path, monkeypatch):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR",
                        (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "TRACKING_TEMP_DIR",
                        tmp_path / "tracking_live_tmp")
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    # `run_owner_report` THẬT, chỉ dời nơi ghi artifact sang thư mục tạm —
    # `repo_root` là default argument nên không monkeypatch được từ ngoài.
    # Cùng khuôn `tests/test_web_daily_min_integration.py` đã nghiệm thu.
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


def unwritable_projection(tmp_path: Path, monkeypatch) -> Path:
    """Trỏ bản chiếu vào một đường dẫn mà ghi THẬT SỰ thất bại.

    Cách làm: cha của nó là một FILE, nên `mkdir(parents=True)` ném
    `NotADirectoryError` (một `OSError`). Đây là một thất bại ghi THẬT của hệ
    thống tệp.

    KHÔNG monkeypatch `Path.mkdir`: `catalog_display.Path` CHÍNH LÀ
    `pathlib.Path`, nên vá phương thức đó là vá toàn cục cho mọi module trong
    cùng tiến trình — đúng lớp rò trạng thái đã làm đỏ một bài kiểm của vertical
    khác ở phiên `R6 REPAIR-1`.
    """
    blocker = tmp_path / "khong-phai-thu-muc"
    blocker.write_text("đây là file, không phải thư mục", encoding="utf-8")
    target = blocker / "display.json"
    monkeypatch.setattr(catalog_display, "DEFAULT_DISPLAY_PATH", target)
    return target


def latest_run(app):
    """Bản ghi run gần nhất, đọc qua ĐÚNG store mà app đang dùng."""
    store = app.config["RUN_REGISTRY"]
    runs = store.list_runs(limit=5)
    assert runs, "phải có ít nhất một run"
    return runs[0]


def upload(client, workbook: Path):
    """Đúng thao tác của Owner: chọn file rồi bấm chạy."""
    response = client.post("/run", data={
        "workbook": (io.BytesIO(workbook.read_bytes()), workbook.name)},
        content_type="multipart/form-data")
    assert response.status_code == 302, (
        f"run phải thành công, nhận {response.status_code}: "
        f"{response.get_data(as_text=True)[:400]}")
    return response


#: Sheet chứa `RAW_PRODUCT`. Không gian làm việc phân hoạch theo NHÂN VIÊN,
#: và `BH0002` của workbook tổng hợp thuộc "Lê Mạnh Hoàng" — nên bài kiểm phải
#: mở đúng sheet ấy. Dùng bí danh `nhan-vien=` (đường dẫn kế thừa mà
#: `_workspace_sheet_key` giải) thay vì tự dựng khoá sheet đã url-encode.
EMPLOYEE = "Hoàng"


def employee_page(client, *, employee: str = EMPLOYEE) -> str:
    response = client.get(
        f"/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien={employee}")
    assert response.status_code == 200, response.status_code
    html = response.get_data(as_text=True)
    # Bảng kê PHẢI có dòng — một bài kiểm chạy trên sheet rỗng sẽ xanh vì
    # không tìm thấy gì, chứ không vì hành vi đúng. Chính cái bẫy đó đã làm
    # một bài của file này xanh giả ở lần chạy đầu.
    assert cells(html, "line-product"), (
        f"sheet của {employee!r} không có dòng nào — bài kiểm sẽ xanh giả")
    return html


def _text(cell: str) -> str:
    """Chữ NGƯỜI ĐỌC THẤY trong một ô, sau khi bỏ thẻ.

    Ô `line-product` chứa một `<a>` khi dòng còn mở bảng chọn, nên một phép
    tìm tới dấu `<` đầu tiên trả về chuỗi rỗng — và mọi khẳng định dựa trên nó
    đều vô nghĩa.
    """
    return " ".join(html_module.unescape(re.sub(r"<[^>]+>", " ", cell)).split())


def cells(html: str, name: str) -> list[str]:
    return [_text(value) for value in re.findall(
        rf'data-metric="{re.escape(name)}"[^>]*>(.*?)</td>', html, re.S)]


def row_of(html: str, product: str) -> str:
    """Khối `<tr>` của dòng mang tên hàng/model này."""
    for block in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        if product in block:
            return block
    raise AssertionError(f"không thấy dòng cho {product!r}")


def brand_of(html: str, product: str) -> str:
    """Ô `Hãng` của ĐÚNG dòng mang tên hàng/model này."""
    block = row_of(html, product)
    match = re.search(r'data-metric="line-brand"[^>]*>(.*?)</td>', block, re.S)
    assert match is not None, f"dòng {product!r} không có ô Hãng"
    return _text(match.group(1))


# --- 1. Luồng chính: run thành công ⟹ Model ngắn + Hãng, KHÔNG mở popup ------

def test_a_successful_run_writes_the_display_projection(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """Bản chiếu phải TỒN TẠI sau một lần chạy thành công.

    ĐỎ trước bản sửa: `POST /run` không ghi bản chiếu, nên file không bao giờ
    xuất hiện và mọi nhãn hiển thị đều mất.
    """
    confirm(identity_store)
    assert not projection_path.exists()
    upload(client, workbook)
    assert projection_path.exists(), (
        "run thành công KHÔNG ghi bản chiếu — đúng lỗi production")
    written = json.loads(projection_path.read_text(encoding="utf-8"))
    assert written[TRACKING_CODE]["brand"] == BRAND
    assert written[TRACKING_CODE]["model_label"] == MODEL_LABEL
    assert written[TRACKING_CODE]["category_label"] == CATEGORY


def test_the_employee_tab_shows_model_and_brand_without_opening_the_popover(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """Mệnh đề TRUNG TÂM của repair, đo trên chính HTML tab Nhân viên.

    KHÔNG có lời gọi nào tới `?phan-loai=` trong bài này — nếu bảng chỉ đúng
    sau khi mở popover thì bản sửa chưa chạm luồng chính.
    """
    confirm(identity_store)
    upload(client, workbook)
    html = employee_page(client)

    assert MODEL_LABEL in cells(html, "line-product"), (
        f"cột Mặt hàng phải hiện model ngắn {MODEL_LABEL!r}, "
        f"đang hiện {cells(html, 'line-product')!r}")
    assert BRAND in cells(html, "line-brand"), (
        f"cột Hãng phải hiện {BRAND!r}, đang hiện {cells(html, 'line-brand')!r}")
    assert CATEGORY in cells(html, "line-category")

    # …và ĐÚNG dòng ấy, không phải một dòng khác tình cờ mang nhãn.
    block = row_of(html, MODEL_LABEL)
    assert BRAND in block and CATEGORY in block


def test_the_raw_accounting_name_is_replaced_for_the_confirmed_line(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """Tên dài trên sổ kế toán KHÔNG còn ở dòng đã xác nhận.

    Đây là nửa còn lại của bằng chứng production ("Mặt hàng còn tên dài"): chỉ
    kiểm "có model" là chưa đủ, vì cả hai có thể cùng xuất hiện.
    """
    confirm(identity_store)
    upload(client, workbook)
    assert RAW_PRODUCT not in cells(employee_page(client), "line-product")


def test_a_second_run_refreshes_the_projection_in_place(
    client, workbook, live_catalog, projection_path, identity_store, tmp_path,
):
    """Lần chạy SAU phải làm mới bản chiếu, không chỉ ghi lần đầu.

    Owner đổi ngành hàng bên Tracking ⟹ lần chạy kế tiếp phải chở giá trị mới
    sang. Nếu bản sửa chỉ ghi khi file chưa tồn tại, bài này đỏ.
    """
    confirm(identity_store)
    upload(client, workbook)
    assert json.loads(projection_path.read_text(
        encoding="utf-8"))[TRACKING_CODE]["category_label"] == CATEGORY

    moved = catalog_rows()
    moved[0]["category_label"] = "Màn hình"
    write_catalog_capture(live_catalog, moved)
    upload(client, workbook)
    assert json.loads(projection_path.read_text(
        encoding="utf-8"))[TRACKING_CODE]["category_label"] == "Màn hình"
    assert "Màn hình" in cells(employee_page(client), "line-category")


def test_the_run_does_not_pull_tracking_a_second_time_for_display(
    client, workbook, live_catalog, projection_path, identity_store, monkeypatch,
):
    """Bản chiếu phải dùng ĐÚNG capture của lần chạy đó.

    `pull_live_captures` được đếm: một lần chạy báo cáo gọi nó ĐÚNG MỘT LẦN.
    Gọi lần thứ hai chỉ để lấy nhãn hiển thị là giữ authority thô của Tracking
    trên đĩa lâu hơn cần thiết (`S071` §10) và thêm một lần gọi mạng cho mỗi
    lần chạy.
    """
    calls = []
    original = live_pull.pull_live_captures

    def counting(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(live_pull, "pull_live_captures", counting)
    confirm(identity_store)
    upload(client, workbook)
    assert len(calls) == 1, f"gọi Tracking {len(calls)} lần, phải đúng 1"


# --- 2. Tương thích capture cũ và metadata thiếu ----------------------------

def test_a_legacy_capture_without_the_three_fields_falls_back_safely(
    client, workbook, tmp_path, projection_path, identity_store, monkeypatch,
):
    """Capture ĐỜI CŨ (không có `model_label`/`brand`/`category_label`):
    run vẫn thành công, bảng rơi về mã Tracking + `—`, KHÔNG crash."""
    catalog = write_catalog_capture(tmp_path / "tracking_catalog.json",
                                    catalog_rows(with_metadata=False))
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)
    monkeypatch.setattr(live_pull, "pull_live_captures", lambda **kw:
                        live_pull.LiveSelectedCaptures(
                            tracking_capture=None, tracking_catalog=catalog,
                            tracking_inv_map=None, tracking_daily_min=None,
                            evidence={}, temp_paths=()))
    confirm(identity_store)
    upload(client, workbook)
    html = employee_page(client)
    # Đã xác nhận nhưng danh mục chưa nói model ⟹ fallback về MÃ Tracking
    # (`R5` §5), và hãng/nhóm hàng là `—`.
    assert TRACKING_CODE in cells(html, "line-product")
    assert cells(html, "line-brand") and set(cells(html, "line-brand")) == {"—"}
    assert set(cells(html, "line-category")) == {"—"}


def test_an_unconfirmed_mapping_never_leaks_metadata(
    client, workbook, live_catalog, projection_path,
):
    """KHÔNG xác nhận mapping nào ⟹ bảng giữ TÊN THÔ và `—`.

    Bản chiếu vẫn được ghi (danh mục có metadata), nên bài này đo đúng phép
    chặn ở tầng trình bày chứ không đo sự vắng mặt của dữ liệu: nhãn CÓ trên
    đĩa mà KHÔNG được phép lên màn hình.
    """
    upload(client, workbook)
    assert projection_path.exists(), "bản chiếu vẫn phải được ghi"
    html = employee_page(client)
    assert RAW_PRODUCT in cells(html, "line-product")
    assert MODEL_LABEL not in cells(html, "line-product")
    assert BRAND not in cells(html, "line-brand")
    assert set(cells(html, "line-brand")) == {"—"}


def test_money_is_identical_whether_or_not_the_projection_exists(
    client, workbook, live_catalog, projection_path, identity_store, engine,
):
    """Bản chiếu là NHÃN. Nó không được đổi một đồng nào.

    Đo bằng cách so tổng tiền của kỳ TRƯỚC và SAU khi bản chiếu tồn tại.
    """
    from app.web import business_service, business_store

    confirm(identity_store)
    upload(client, workbook)
    service = business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))
    bounds = (date(2026, 1, 1), date(2026, 1, 31))
    with_projection = service.period(date_from=bounds[0], date_to=bounds[1])

    projection_path.unlink()
    without = service.period(date_from=bounds[0], date_to=bounds[1])

    assert with_projection.totals.sales_revenue == without.totals.sales_revenue
    assert with_projection.totals.kpi_profit == without.totals.kpi_profit
    assert with_projection.totals.qualifying_quantity == without.totals.qualifying_quantity
    assert with_projection.totals.orders == without.totals.orders
    assert with_projection.totals.lines == without.totals.lines


# --- 3. Không im lặng khi bản chiếu không ghi được -------------------------

def test_an_unwritable_projection_is_reported_in_the_run_evidence(
    app, client, workbook, live_catalog, identity_store, tmp_path, monkeypatch,
):
    """Ghi bản chiếu THẤT BẠI ⟹ run evidence phải NÓI RA.

    Im lặng ở đây là đúng lớp lỗi mà production vừa gặp: cả bảng chỉ có `—` và
    không một dòng nào trên màn hình hay trong bằng chứng giải thích vì sao.
    """
    unwritable_projection(tmp_path, monkeypatch)
    confirm(identity_store)
    upload(client, workbook)

    record = latest_run(app)
    evidence = record.tracking_evidence or {}
    status = evidence.get("catalog_display")
    assert status is not None, (
        "run evidence phải mang trạng thái ghi bản chiếu, đang thiếu hẳn")
    assert status.get("written") is False
    assert status.get("reason") == catalog_display.REASON_WRITE_FAILED


def test_an_unwritable_projection_still_lets_the_run_succeed(
    client, workbook, live_catalog, identity_store, tmp_path, monkeypatch,
):
    """Bản chiếu là tính năng PHỤ: không ghi được thì mất vài cái nhãn, không
    được mất cả báo cáo."""
    unwritable_projection(tmp_path, monkeypatch)
    confirm(identity_store)
    upload(client, workbook)  # 302 = thành công


def test_the_employee_tab_warns_when_the_projection_is_missing(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """Bản chiếu vắng mặt trong khi CÓ mapping đã xác nhận ⟹ tab Nhân viên
    phải cảnh báo, không để cả cột `Hãng` là `—` mà không lời nào giải thích.
    """
    confirm(identity_store)
    upload(client, workbook)
    projection_path.unlink()
    html = employee_page(client)
    assert 'data-metric="catalog-projection-warning"' in html, (
        "mất bản chiếu mà bảng im lặng — đúng lỗi production")


def test_no_warning_when_the_projection_is_healthy(
    client, workbook, live_catalog, projection_path, identity_store,
):
    """Cảnh báo phải VẮNG khi mọi thứ bình thường — một cảnh báo luôn hiện là
    một cảnh báo không ai đọc."""
    confirm(identity_store)
    upload(client, workbook)
    assert 'data-metric="catalog-projection-warning"' not in employee_page(client)
