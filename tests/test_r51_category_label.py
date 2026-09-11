"""R5.1 — `category_label` đi từ Tracking tới màn hình nhân viên.

Ba mệnh đề, và cả ba nói về việc KHÔNG làm gì:

1. Reports không SINH RA nhóm hàng. Nó đọc một trường mà Tracking đã chuẩn
   hoá. `ADR-111 §3` đặt thẩm quyền thương hiệu ở Tracking vì bằng chứng
   (`board/<mã>/cat`) nằm ở đó; nhóm hàng đến từ ĐÚNG trường ấy, nên thẩm
   quyền của nó cũng ở đó. `PHB-06 §3`/`BR-02`/`BR-10` cấm bốn cách dựng một
   thẩm quyền thứ hai, và "suy nhóm hàng từ `product_raw`" là đúng cách thứ
   tư — `§5.9` của brief nhắc lại nó thành một điều cấm riêng.

2. Artifact CŨ (R5, không có trường này) vẫn đọc được, và đọc thành `None`.
   Một hợp đồng mở rộng mà làm hỏng những file đã ghi là một lần mất dữ liệu.

3. `category_label` KHÔNG đổi một đồng nào. Nó là metadata trình bày gắn vào
   `product_key` đang có — không phải một khoá sản phẩm mới, không tham gia
   nhận diện, và không có đường nào chạm vào doanh thu, giá nhập hay lợi
   nhuận. Mục 5 đo đúng điều đó bằng cách ĐỔI nhóm hàng rồi cộng lại tiền.

Ba câu mà ba trường trả lời, và lý do chúng phải tách bạch:

```text
brand            ai làm ra          "Samsung"
model_label      đúng dòng máy nào  "55Q6FA"
category_label   LOẠI hàng gì       "Tivi"     ⟸ không chứa hãng/model/NCC/giá
```

`None` nghĩa là CHƯA ĐỦ CĂN CỨ — Tracking chưa xếp ngành hàng cho mã đó,
hoặc ngành hàng đã xếp không khẳng định được. Đó là một câu trả lời hợp lệ,
không phải một chỗ trống để Reports điền vào.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.pricing.resolution.sources import (
    InvalidTrackingCatalogCaptureFileError, load_tracking_catalog_capture,
)
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus, TrackingCatalogRow, TrackingCatalogSnapshot,
    canonical_content_hash,
)
from app.modules.reporting import business_metrics as bm
from app.web import business_service, business_store, catalog_display
from app.web import history_store
from tools.tracking import capture_tracking_catalog as capture

from tests.test_employee_workspace_ux import (
    SEPTEMBER, body, line, line_keys, metrics, persist,
)
from tests.test_dec185_nav_chart_identity import (  # noqa: F401
    client, identity_store, snapshot, tracking_on, unresolved_line,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def write_capture(path: Path, rows: list[dict], alias: dict | None = None) -> Path:
    alias = alias or {}
    payload = {
        "capture_id": "cap-r51",
        "captured_at": "2026-09-09T00:00:00+00:00",
        "captured_by": "test",
        "source_system_ref": "tracking",
        "capture_status": "COMPLETE",
        "content_hash": canonical_content_hash(rows, alias),
        "rows": rows,
        "alias_map": alias,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


# --- 1. Capture đọc được hợp đồng MỚI ------------------------------------

def test_the_capture_carries_the_category_when_tracking_sends_it():
    rows = capture._rows_from_board({
        "55Q6FA": {"name": "Tivi Samsung QLED 55Q6FA", "alt": ["QN55Q6FA"],
                   "model_label": "QLED 55Q6FA", "brand": "Samsung",
                   "category_label": "Tivi"},
    })
    assert rows == [{
        "tracking_code": "55Q6FA", "present_in_board": True,
        "name": "Tivi Samsung QLED 55Q6FA", "alt": ["QN55Q6FA"],
        "model_label": "QLED 55Q6FA", "brand": "Samsung",
        "category_label": "Tivi",
    }]


def test_a_null_category_is_kept_out_of_the_row_entirely():
    """`null` nghĩa là Tracking KHÔNG khẳng định — không ghi một khoá rỗng.

    Cùng lý do với R5: một khoá mang `None` và một khoá vắng mặt đọc lên đều
    thành "chưa phân loại", nhưng khoá vắng mặt còn giữ được điều thứ hai —
    hash của một dòng Tracking chưa xếp ngành hàng bằng đúng hash của cùng
    dòng đó ở hợp đồng R5, nên nâng cấp hợp đồng không tự khai là một lần đổi
    danh mục.
    """
    rows = capture._rows_from_board({
        "LA-01": {"name": "Tivi cũ trưng bày", "model_label": None,
                  "brand": None, "category_label": None},
    })
    assert rows == [{"tracking_code": "LA-01", "present_in_board": True,
                     "name": "Tivi cũ trưng bày"}]


def test_upgrading_the_contract_alone_does_not_change_the_content_hash():
    """Mệnh đề backward-compatibility đo bằng HASH, không bằng lời hứa."""
    r5 = capture._rows_from_board({"X": {"name": "A", "brand": "Sony"}})
    r51 = capture._rows_from_board(
        {"X": {"name": "A", "brand": "Sony", "category_label": None}})
    assert canonical_content_hash(r5, {}) == canonical_content_hash(r51, {})


def test_a_wrong_type_category_is_a_malformed_source_not_a_guess():
    with pytest.raises(capture.MalformedSourceError):
        capture._rows_from_board({"X": {"name": "A", "category_label": 7}})
    with pytest.raises(capture.MalformedSourceError):
        capture._rows_from_board({"X": {"name": "A", "category_label": ["Tivi"]}})


def test_the_content_hash_covers_the_category(tmp_path):
    """`§4.7` — đổi nhóm hàng mà hash không đổi là một lần đổi danh mục KHÔNG
    dấu vết, và Reports sẽ tiếp tục dùng bản chiếu cũ."""
    tivi = capture._rows_from_board(
        {"X": {"name": "A", "category_label": "Tivi"}})
    tu_lanh = capture._rows_from_board(
        {"X": {"name": "A", "category_label": "Tủ lạnh"}})
    none = capture._rows_from_board({"X": {"name": "A"}})
    hashes = {canonical_content_hash(r, {}) for r in (tivi, tu_lanh, none)}
    assert len(hashes) == 3, "ba nội dung khác nhau phải cho ba hash khác nhau"


# --- 2. Loader đọc được CẢ hợp đồng cũ lẫn mới ---------------------------

def test_an_r5_artifact_without_the_category_still_loads(tmp_path):
    """`§5.2` — artifact R5 ghi TRƯỚC R5.1 vẫn đọc được, category là `None`."""
    path = write_capture(tmp_path / "cap.json", [
        {"tracking_code": "65S20M2", "present_in_board": True,
         "name": "Tivi Sony K-65S20M2", "model_label": "K-65S20M2",
         "brand": "Sony"},
    ])
    row = load_tracking_catalog_capture(path).row_for("65S20M2")
    assert (row.model_label, row.brand) == ("K-65S20M2", "Sony")
    assert row.category_label is None


def test_a_new_artifact_loads_all_three_fields(tmp_path):
    path = write_capture(tmp_path / "cap.json", [
        {"tracking_code": "55Q6FA", "present_in_board": True,
         "name": "Tivi Samsung QLED 55Q6FA", "model_label": "QLED 55Q6FA",
         "brand": "Samsung", "category_label": "Tivi"},
    ])
    row = load_tracking_catalog_capture(path).row_for("55Q6FA")
    assert (row.model_label, row.brand, row.category_label) == (
        "QLED 55Q6FA", "Samsung", "Tivi")


def test_a_wrong_type_category_in_the_artifact_is_refused_not_coerced(tmp_path):
    path = write_capture(tmp_path / "cap.json", [
        {"tracking_code": "X", "present_in_board": True, "category_label": 7},
    ])
    with pytest.raises(InvalidTrackingCatalogCaptureFileError):
        load_tracking_catalog_capture(path)


# --- 3. Nhóm hàng KHÔNG tham gia nhận diện -------------------------------

def test_identity_matching_never_reads_the_category():
    """`INV-13`/`INV-21` — chỉ mã, tên và alt được ghép EXACT.

    Ghép thêm bằng nhóm hàng còn tệ hơn ghép bằng hãng: mọi cái Tivi trên đời
    sẽ khớp với nhau, và một mapping đã confirm có thể trượt sang một mặt
    hàng khác cùng nhóm.
    """
    snap = TrackingCatalogSnapshot(
        capture_id="c", captured_at=datetime(2026, 9, 9),
        captured_by="t", source_system_ref="s", content_hash="h",
        capture_status=CaptureStatus.COMPLETE,
        rows=(TrackingCatalogRow(
            tracking_code="55Q6FA", present_in_board=True,
            name="Tivi Samsung QLED 55Q6FA", model_label="QLED 55Q6FA",
            brand="Samsung", category_label="Tivi"),))
    assert snap.exact_match_codes(raw_key="Tivi", aid="tivi") == ()
    assert snap.exact_match_codes(
        raw_key="Tivi Samsung QLED 55Q6FA",
        aid="tivi samsung qled 55q6fa") == (("55Q6FA", "TRACKING_NAME"),)


def test_no_branch_derives_the_category_from_product_raw():
    """`§5.9` — bằng chứng đọc được từ MÃ NGUỒN, không phải từ một lời hứa.

    Bài này canh cả hai chiều mà một lần "tiện tay" sẽ đi qua: một hàm đọc
    `product_raw` để đoán nhóm hàng, hoặc bản chiếu hiển thị mọc thêm một
    đường ghi từ tên trên sổ. Nó cố ý đọc mã nguồn thay vì chạy một trường
    hợp: một nhánh đoán chỉ cần đúng trên trường hợp test là xanh.
    """
    for path in ("app/web/catalog_display.py",
                 "app/web/workspace_presentation.py"):
        source = (REPO_ROOT / path).read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", source, flags=re.S)
        code = re.sub(r"^\s*#.*$", "", code, flags=re.M)
        for line_no, text in enumerate(code.splitlines(), start=1):
            if "product_raw" in text and "category" in text:
                raise AssertionError(
                    f"{path}:{line_no} đọc `product_raw` cạnh nhóm hàng — "
                    "đây đúng là cách dựng thẩm quyền thứ hai mà ADR-111 §3 "
                    "cấm")


# --- 3b. REPAIR-1: thẩm quyền ở MỘT phía, và Reports không phải phía đó ---

def test_reports_keeps_no_category_vocabulary_of_its_own():
    """`R5.1 REPAIR-1` — từ điển nhóm hàng sống ở Tracking, và CHỈ ở đó.

    Repair cycle này khoá `category_label` thành một từ điển đóng. Chỗ dễ sai
    tiếp theo là "tiện tay" chép từ điển ấy sang Reports để tự kiểm tra lại —
    và đó chính là cách dựng một thẩm quyền thứ hai mà `ADR-111` §3 và
    `PHB-06 §3` cấm. Hai bản danh sách sẽ trôi khỏi nhau, rồi một nhãn hợp lệ
    bên Tracking bị Reports loại mà không màn hình nào nói vì sao.

    Bài này canh cấu trúc, không canh một trường hợp: một tên nhóm hàng cụ thể
    KHÔNG được xuất hiện như dữ liệu trong mã sản phẩm của Reports.
    """
    NHOM_CUA_TRACKING = ("Tủ lạnh", "Máy giặt", "Điều hoà", "Nồi cơm điện",
                         "Bình nóng lạnh", "Lò vi sóng", "Máy lọc không khí")
    for path in ("app/web/catalog_display.py",
                 "app/web/workspace_presentation.py",
                 "app/web/server.py",
                 "app/modules/product/identity/tracking_catalog.py",
                 "app/modules/pricing/resolution/sources.py",
                 "tools/tracking/capture_tracking_catalog.py"):
        source = (REPO_ROOT / path).read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", source, flags=re.S)
        code = re.sub(r"^\s*#.*$", "", code, flags=re.M)
        for ten in NHOM_CUA_TRACKING:
            assert ten not in code, (
                f"{path} mang tên nhóm hàng {ten!r} trong MÃ — Reports đang "
                "dựng một từ điển nhóm hàng thứ hai; thẩm quyền thuộc về "
                "Tracking (ADR-111 §3)")


def test_dec206_owner_approved_labels_pass_through_unmodified(tmp_path):
    """`DEC-206` — ba nhãn Owner chốt (`"Điều hoà"`, `"Tivi"`, `"Máy giặt"`)
    đi qua Reports NGUYÊN VẸN, đúng như mọi nhãn khác từ từ điển Tracking.

    Reports không có logic ĐẶC BIỆT cho ba nhãn này — chúng chỉ là những giá
    trị chuỗi bình thường trong `category_label`. Bài này tồn tại để chứng
    minh đúng điều đó: không rẽ nhánh nào, không case đặc cách nào.
    """
    path = write_capture(tmp_path / "cap.json", [
        {"tracking_code": "TV-01", "present_in_board": True,
         "name": "TV Samsung 55 inch", "brand": "Samsung",
         "category_label": "Tivi"},
        {"tracking_code": "MGS-01", "present_in_board": True,
         "name": "Máy giặt sấy LG FV1412", "brand": "LG",
         "category_label": "Máy giặt"},
        {"tracking_code": "DH-01", "present_in_board": True,
         "name": "Máy lạnh Casper", "brand": "Casper",
         "category_label": "Điều hoà"},
    ])
    snapshot = load_tracking_catalog_capture(path)
    assert snapshot.row_for("TV-01").category_label == "Tivi"
    assert snapshot.row_for("MGS-01").category_label == "Máy giặt"
    assert snapshot.row_for("DH-01").category_label == "Điều hoà"


def test_reports_passes_the_label_through_without_sanitising_it(tmp_path):
    """Reports KHÔNG lọc lại nhãn — và đó là một quyết định, không phải sót.

    Sau `REPAIR-1`, bảo đảm "nhãn luôn thuộc từ điển đóng" nằm ở TRACKING, nơi
    có bằng chứng (`board/<mã>/cat`) và nơi từ điển sống. Dựng thêm một phép
    lọc ở đây sẽ cần một bản sao từ điển — xem bài ngay trên.

    Nên nếu một Tracking hỏng gửi rác, Reports chở nguyên rác đó ra màn hình.
    Bài này ghim hành vi ấy để nó là một lựa chọn ĐỌC ĐƯỢC, không phải một lỗ
    hổng người sau phát hiện rồi vá nhầm chỗ. Phép đo thật của bảo đảm nằm ở
    `scripts/r51_crossrepo_smoke.py`, chạy trên payload do chính mã Tracking
    sinh, và nó đọc từ điển NGƯỢC từ `src/index.js` chứ không gõ lại.
    """
    path = write_capture(tmp_path / "cap.json", [
        {"tracking_code": "X", "present_in_board": True,
         "category_label": "Tivi kho anh Ba"},
    ])
    row = load_tracking_catalog_capture(path).row_for("X")
    assert row.category_label == "Tivi kho anh Ba", (
        "Reports là bên TIÊU THỤ: nó không sửa, không lọc, không đoán lại")


# --- 4. Bản chiếu hiển thị -----------------------------------------------

@pytest.fixture
def display(tmp_path, monkeypatch):
    path = tmp_path / "tracking_display.json"
    monkeypatch.setattr(catalog_display, "DEFAULT_DISPLAY_PATH", path)
    return path


def _snapshot(rows):
    return TrackingCatalogSnapshot(
        capture_id="c", captured_at=datetime(2026, 9, 9), captured_by="t",
        source_system_ref="s", content_hash="h",
        capture_status=CaptureStatus.COMPLETE,
        rows=tuple(TrackingCatalogRow(
            tracking_code=code, present_in_board=True, name=code,
            model_label=model, brand=brand, category_label=category)
            for code, model, brand, category in rows))


def test_the_display_projection_round_trips_the_category(display):
    catalog_display.write(_snapshot([
        ("55Q6FA", "QLED 55Q6FA", "Samsung", "Tivi"),
        ("RT38", "RT38", "Samsung", "Tủ lạnh"),
        ("LA-01", None, None, None)]))
    assert catalog_display.read() == {
        "55Q6FA": {"model_label": "QLED 55Q6FA", "brand": "Samsung",
                   "category_label": "Tivi"},
        "RT38": {"model_label": "RT38", "brand": "Samsung",
                 "category_label": "Tủ lạnh"},
    }, "dòng không có gì để nói thì không chiếm chỗ"


def test_a_row_with_only_a_category_still_earns_its_place(display):
    """Một mã đã xếp ngành hàng nhưng chưa rõ hãng vẫn phải được ghi lại."""
    catalog_display.write(_snapshot([("X", None, None, "Tivi")]))
    assert catalog_display.read() == {
        "X": {"model_label": None, "brand": None, "category_label": "Tivi"}}


def test_a_broken_projection_reads_as_empty_not_as_an_error(display):
    display.write_text("{ hỏng", encoding="utf-8")
    assert catalog_display.read() == {}


def test_category_of_never_falls_back_to_the_tracking_code(display):
    """Khác `label_of`: một mã Tracking là một cái MÃ, không phải loại hàng."""
    projection = {"X": {"model_label": None, "brand": None,
                        "category_label": None}}
    assert catalog_display.category_of(projection, "X") is None
    assert catalog_display.category_of(projection, "KHONG-CO") is None
    assert catalog_display.category_of(projection, None) is None
    assert catalog_display.label_of(projection, "X") is None


# --- 5. Màn hình: đúng dòng, đúng trạng thái, KHÔNG đổi tiền -------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def service(engine, store):
    return business_service.BusinessReportService(engine=engine, store=store)


def seed_display(path, rows: dict):
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def workspace(client) -> str:
    return body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")


def _keys(client):
    match = re.search(
        r'data-metric="identity-open"[^>]*href="[^"]*order_key=(?P<order>[^&"]+)'
        r'[^"]*product_key=(?P<product>[0-9a-f]+)[^"]*'
        r'occurrence_index=(?P<occ>\d+)', workspace(client))
    assert match is not None, "phải có lối vào phân loại"
    return match.groupdict()


def _classify(client, keys, code):
    response = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": keys["order"],
        "product_key": keys["product"], "occurrence_index": keys["occ"],
        "ma_tracking": code})
    assert response.status_code == 302
    return response


ELECTROLUX = {"EWF1143R7SC": {"model_label": "EWF1143R7SC",
                              "brand": "Electrolux",
                              "category_label": "Máy giặt"}}


def test_a_confirmed_line_shows_the_category_of_its_tracking_code(
    repository, client, display, tracking_on,
):
    """`§5.4` nhánh CONFIRMED — nhóm hàng đi cùng ĐÚNG mã đã resolve."""
    seed_display(display, ELECTROLUX)
    persist(repository, [unresolved_line("BH1")])
    _classify(client, _keys(client), "EWF1143R7SC")

    html = workspace(client)
    assert metrics(html, "line-category") == ["Máy giặt"]
    assert metrics(html, "line-brand") == ["Electrolux"]


def test_an_unclassified_line_never_gets_a_category(
    repository, client, display,
):
    """`§5.4` nhánh CHƯA PHÂN LOẠI — kể cả khi tên hàng nói rõ là máy giặt."""
    seed_display(display, ELECTROLUX)
    persist(repository, [unresolved_line("BH1")])
    html = workspace(client)
    assert "Máy giặt Electrolux EWF1143R7SC" in html, "giữ TÊN THÔ"
    assert metrics(html, "line-category") == ["—"], (
        "chưa phân loại thì chưa có nhóm hàng — không đoán từ tên hàng")


def test_a_category_never_leaks_from_one_code_to_another(
    repository, client, display, tracking_on,
):
    """`§10` — gắn nhóm hàng của mã này sang mã khác là lỗi phải repair ngay.

    Dòng được xác nhận là `EWF1143R7SC`, và bản chiếu CÓ một mã khác mang
    nhóm hàng "Tivi". Một phép tra bằng tên, bằng hãng, hay bằng "mã đầu
    tiên của bản chiếu" đều sẽ cho ra "Tivi" ở đây.
    """
    seed_display(display, {**ELECTROLUX,
                           "43F6000": {"model_label": "43F6000",
                                       "brand": "TCL",
                                       "category_label": "Tivi"}})
    persist(repository, [unresolved_line("BH1")])
    _classify(client, _keys(client), "EWF1143R7SC")
    assert metrics(workspace(client), "line-category") == ["Máy giặt"]


def test_an_out_of_catalog_line_gets_no_category(
    repository, client, display, tracking_on,
):
    """`§5.4` nhánh OUT_OF_CATALOG — cố ý không có mã Tracking nào."""
    seed_display(display, ELECTROLUX)
    persist(repository, [unresolved_line("BH1")])
    keys = _keys(client)
    response = client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": keys["order"],
        "product_key": keys["product"], "occurrence_index": keys["occ"]})
    assert response.status_code == 302
    assert metrics(workspace(client), "line-category") == ["—"]


def test_a_conflicting_line_gets_no_category(repository, client, display):
    """`§5.4` nhánh CONFLICT — dòng đang tranh chấp có HAI mã ứng viên.

    Không mã nào trong hai được phép cho mượn nhóm hàng: chọn một cái là
    Reports tự giải mâu thuẫn thay người, trên một màn hình trông bình
    thường.
    """
    seed_display(display, ELECTROLUX)
    persist(repository, [line(
        "BH1", "Máy giặt Electrolux EWF1143R7SC", day=5, kpi_purchase=None,
        kpi_profit=None, status="PENDING", reasons=("IDENTITY_CONFLICT",))])
    html = workspace(client)
    assert metrics(html, "line-category") == ["—"]
    assert metrics(html, "line-brand") == ["—"], (
        "cùng một cổng chặn giữ cả hai trường — không phải hai phép chặn")


# --- 6. Đổi nhóm hàng KHÔNG đổi tiền ------------------------------------

def _money(html: str) -> dict:
    return {name: metric_value
            for name in ("totals-purchase", "totals-sell", "totals-profit",
                         "totals-converted")
            for metric_value in [re.search(
                rf'data-metric="{name}"[^>]*>(.*?)<', html, re.S).group(1).strip()]}


def test_changing_the_category_moves_no_money(
    repository, client, display, tracking_on,
):
    """`§6` — nhóm hàng đổi thì CHỈ bucket metadata đổi.

    Đây là bất biến đắt nhất của R5.1 và là mục §10 đầu tiên của tiêu chí
    repair. Nó đo bằng cách chụp lại tổng tiền, ĐỔI nhóm hàng bên Tracking
    (tức là ghi lại bản chiếu, đúng thứ một lần capture mới làm), rồi đọc lại
    cùng một trang.
    """
    seed_display(display, ELECTROLUX)
    persist(repository, [unresolved_line("BH1")])
    keys = _keys(client)
    _classify(client, keys, "EWF1143R7SC")

    truoc = workspace(client)
    tien_truoc = _money(truoc)
    product_key_truoc = line_keys(truoc, "EWF1143R7SC")["product"]
    assert metrics(truoc, "line-category") == ["Máy giặt"]

    # Tracking xếp lại ngành hàng. Không ai bên Reports phải phân loại lại mã
    # sản phẩm (`§3.9`) — chỉ bản chiếu đổi.
    seed_display(display, {"EWF1143R7SC": {"model_label": "EWF1143R7SC",
                                           "brand": "Electrolux",
                                           "category_label": "Đồ gia dụng"}})
    sau = workspace(client)

    assert metrics(sau, "line-category") == ["Đồ gia dụng"], "nhóm hàng ĐÃ đổi"
    assert _money(sau) == tien_truoc, (
        "doanh thu, giá nhập, lợi nhuận và DS quy đổi KHÔNG được đổi")
    assert line_keys(sau, "EWF1143R7SC")["product"] == product_key_truoc, (
        "`§5.8` — không tạo product key mới; nhóm hàng là thuộc tính của "
        "product_key hiện hành")
    assert metrics(sau, "line-product") == ["EWF1143R7SC"], (
        "mã/model hiển thị không đổi theo nhóm hàng")


def test_losing_the_projection_empties_the_category_without_touching_money(
    repository, client, display, tracking_on,
):
    """Mất file bản chiếu (deploy mới, đĩa ephemeral) ⟹ màn hình nói ÍT ĐI,
    không nói SAI, và tiền không đổi."""
    seed_display(display, ELECTROLUX)
    persist(repository, [unresolved_line("BH1")])
    _classify(client, _keys(client), "EWF1143R7SC")
    tien = _money(workspace(client))

    display.unlink()
    sau = workspace(client)
    assert metrics(sau, "line-category") == ["—"]
    assert _money(sau) == tien


# --- 7. Sống qua refresh và create_app() --------------------------------

def test_the_category_survives_a_refresh_and_a_restart(
    repository, engine, client, display, tracking_on, monkeypatch, tmp_path,
    identity_store,
):
    """`§5.5` — refresh là một GET nữa; restart là một `create_app()` nữa.

    Bản chiếu nằm trên đĩa và log quyết định nằm trong store, nên một tiến
    trình mới phải đọc ra đúng cùng một câu — nếu nhóm hàng chỉ sống trong
    bộ nhớ của một app object, bài này đỏ.
    """
    from app.web import identity_gateway
    from app.web import server as web_server
    from tools.tracking import live_pull

    seed_display(display, ELECTROLUX)
    persist(repository, [unresolved_line("BH1")])
    _classify(client, _keys(client), "EWF1143R7SC")
    assert metrics(workspace(client), "line-category") == ["Máy giặt"]
    # Refresh: đọc lại đúng trang đó.
    assert metrics(workspace(client), "line-category") == ["Máy giặt"]

    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(identity_gateway, "build_store", lambda: identity_store)
    lai = web_server.create_app(
        db_path=tmp_path / "runs-2.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    lai.testing = True
    assert metrics(workspace(lai.test_client()), "line-category") == ["Máy giặt"]


# --- 8. Cột trên bảng kê -------------------------------------------------

def test_the_category_column_shares_the_one_optional_toggle(
    repository, client, display,
):
    persist(repository, [line("BH1", "43F6000", day=5)])
    html = workspace(client)
    assert html.count('data-metric="toggle-optional"') == 1
    assert 'col-optional">Nhóm hàng</th>' in html
    assert 'data-optional-hidden="1"' in html, "ẩn ngay từ khung hình đầu"
    assert re.search(
        r'data-metric="line-category"[^>]*title="', html), "đọc đủ qua tooltip"


def test_the_discount_line_has_no_category(
    repository, client, display, tracking_on,
):
    """Dòng "Chiết khấu" là số suy ra từ sổ, không phải một mặt hàng.

    Nó không có trạng thái nhận diện nào (`DEC-185` §PI-01), nên nó cũng
    không có nhóm hàng — kể cả khi dòng hàng thật ngay trên nó đã được xác
    nhận và ĐANG hiện một nhóm hàng.
    """
    seed_display(display, ELECTROLUX)
    persist(repository, [line(
        "BH1", "Máy giặt Electrolux EWF1143R7SC", day=5, discount="100000",
        kpi_purchase=None, kpi_profit=None, status="PENDING",
        reasons=("IDENTITY_UNRESOLVED",))])
    _classify(client, _keys(client), "EWF1143R7SC")

    html = workspace(client)
    assert bm.DISCOUNT_DISPLAY_LABEL in html, "fixture phải sinh ra dòng suy ra"
    assert metrics(html, "line-category") == ["Máy giặt", "—"], (
        "dòng hàng thật có nhóm hàng; dòng chiết khấu ngay dưới thì không")
