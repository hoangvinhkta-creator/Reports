"""`P1-5` — HTML form KHÔNG được hứa một điều server không làm.

## Lỗi mà file này đóng

Bản trước gắn một `request_id` vào MỌI form POST của trang, và dòng chữ
cạnh nút LƯU nói với người dùng rằng "server nhận ra mã của lần gửi này
và không ghi hai lần". Review độc lập chỉ ra rằng KHÔNG route HTML nào
đọc mã đó: `business_save_order`, `business_save_line_purchase_price`,
target, chốt kỳ, upload — tất cả nhận thêm một trường rồi bỏ qua nó.

Hệ quả tệ hơn một trường thừa. Người dùng bấm THỬ LẠI *dựa trên* lời hứa
ấy, và mỗi lần bấm là một lần ghi nữa.

## Hướng đã chọn, và vì sao chỉ một hướng

Review cho hai hướng: gỡ lời hứa khỏi các form chưa được server đỡ, hoặc
mở rộng `mutation_guard` cho từng route HTML. Đợt này chọn hướng THỨ NHẤT,
và lý do là phạm vi: mở rộng guard cho một route HTML đòi route ấy phải
có `base_revision` của đối tượng nó sửa (không thì CAS không có gì để so),
tức phải đổi cả template render form đó. Đó là công việc của `UI-02`, và
làm nửa vời sẽ dựng một guard chạy nhưng không so gì — nguy hiểm hơn
không có guard, vì nó *trông như* đã đỡ.

Nên hôm nay: `idempotency_key` chỉ tồn tại trên đường `/api/`. Form HTML
không gửi mã, không mọc nút THỬ LẠI, và nói đúng sự thật rằng phải tải
lại trang để xem trạng thái thật.

## Ba mệnh đề, và ba cửa khác nhau

    1. server: một POST HTML gửi LẠI cùng `idempotency_key` VẪN ghi lần
       thứ hai — bằng chứng trực tiếp rằng lời hứa cũ là sai
    2. server: đường HTML không tạo bản ghi nào trong `mutation_request`
       (guard không hề chạy ở đó)
    3. drift: nếu MAI có template khai `data-idempotent`, route của nó
       PHẢI đọc `idempotency_key` — nếu không, test này đỏ

Mặt client (form nào gửi mã, form nào mọc nút THỬ LẠI, câu chữ nào được
hiện) nằm ở `tests/browser/stab0345_navigation.test.mjs`; nó là mệnh đề
về DOM và một test Python không kiểm được nó.
"""

from __future__ import annotations

import inspect
import re
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select

import tools.db as history_db
from app.web import business_service, business_store, history_store
from app.web import server as web_server
from tests.test_employee_workspace_ux import SEPTEMBER, TODAY, line, persist
from tools.db.schema import mutation_request
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = REPO_ROOT / "app" / "web" / "templates"
RAW = "43F6000"
ORDER = "BH72707"


# --------------------------------------------------------------------------
# Bộ khung: đúng ứng dụng web thật, đúng route thật
# --------------------------------------------------------------------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def snapshot_repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def service(engine):
    return business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
    monkeypatch.setattr(
        web_server.identity_gateway, "DEFAULT_LOG_PATH",
        tmp_path / "identity" / "mappings.jsonl")
    monkeypatch.setattr(
        web_server.identity_gateway, "DEFAULT_INDEX_PATH",
        tmp_path / "identity" / "index.json")
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application.test_client()


def _keys(service):
    for detail in service.period(**SEPTEMBER).details:
        if detail["order_key"] == ORDER and detail["product_raw"] == RAW:
            return {"order_key": detail["order_key"],
                    "product_key": detail["product_key"],
                    "occurrence_index": detail["occurrence_index"]}
    raise AssertionError(f"không tìm thấy dòng {ORDER}/{RAW}")


def _unpriced():
    return [line(ORDER, RAW, day=5, sell="9000000", kpi_purchase=None,
                 kpi_profit=None,
                 reasons=("IDENTITY_UNRESOLVED", "Missing.PurchasePrice"))]


def _price_of(service):
    return service.period(**SEPTEMBER).lines[0].purchase_price


# --------------------------------------------------------------------------
# (1) + (2) — hành vi THẬT của một form HTML thật
# --------------------------------------------------------------------------

class TestARealHtmlFormIsNotProtectedByAnyKey:
    """Route `/kinh-doanh/nhan-vien/gia-nhap` — form nhập giá nhập của một dòng.

    Chọn route này chứ không phải `api_patch_order` có chủ đích: review đòi
    "test cho form HTML thực tế, không chỉ API PATCH", và đây là một trong
    những form mà bản trước gắn `request_id` vào.
    """

    def test_resending_the_same_idempotency_key_writes_a_SECOND_time(
        self, snapshot_repository, service, client
    ):
        """Bằng chứng trực tiếp rằng lời hứa cũ là sai.

        Hai lần POST mang CÙNG `idempotency_key` nhưng GIÁ KHÁC NHAU. Nếu
        server đỡ mã ấy, lần thứ hai sẽ bị coi là bản sao của lần thứ nhất
        và giá phải đứng ở 8.500.000. Nó không: giá thành 7.000.000, tức
        lần gửi thứ hai đã được ghi như một quyết định mới.

        Giá KHÁC NHAU chứ không cùng giá, vì `set_purchase_price()` là một
        UPSERT: gửi lại cùng giá sẽ cho cùng kết quả và không phân biệt
        được "server chống lặp" với "server ghi lại y nguyên".
        """
        persist(snapshot_repository, _unpriced())
        keys = _keys(service)
        key = "0f7f7d3a-4a4e-4f2e-9c1b-2a3b4c5d6e7f"

        first = client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "8.500.000", "idempotency_key": key})
        assert first.status_code == 302
        assert _price_of(service) == Decimal("8500000")

        second = client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "7.000.000", "idempotency_key": key,
            "ly_do": "sửa lại sau khi đối chiếu hoá đơn"})
        assert second.status_code == 302

        assert _price_of(service) == Decimal("7000000"), (
            "lần gửi thứ hai bị bỏ qua — nếu route HTML này THẬT SỰ chống "
            "lặp được thì P1-5 phải đi hướng thứ hai (mở rộng guard) và "
            "docstring của file này đang nói sai về hệ thống")

    def test_the_html_path_never_touches_the_mutation_guard_table(
        self, snapshot_repository, service, client, engine
    ):
        """Mệnh đề (2): guard KHÔNG hề chạy trên đường HTML.

        Kiểm ở tầng bảng chứ không bằng cách đọc mã nguồn: một `import`
        chưa dùng hay một lần gọi trong nhánh chết đều không đổi được kết
        quả ở đây.
        """
        persist(snapshot_repository, _unpriced())
        keys = _keys(service)
        client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "8.500.000",
            "idempotency_key": "0f7f7d3a-4a4e-4f2e-9c1b-2a3b4c5d6e7f"})

        with engine.connect() as connection:
            rows = connection.execute(
                select(func.count()).select_from(mutation_request)).scalar()
        assert rows == 0, (
            "đường HTML đã ghi vào `mutation_request` — nếu guard đã chạy ở "
            "đây thì test trên phải đỏ, và một trong hai test đang nói sai")

    def test_the_route_still_works_with_NO_key_at_all(
        self, snapshot_repository, service, client
    ):
        """Và đây là hình dạng THẬT của lần gửi hôm nay: không có mã nào.

        `app.js` chỉ gắn `idempotency_key` cho form khai `data-idempotent`,
        và không template nào khai — nên mọi POST HTML thật đến đây không
        mang trường ấy. Route phải chạy bình thường; nếu nó bắt đầu ĐÒI mã,
        cả giao diện sẽ vỡ mà không test nào khác thấy.
        """
        persist(snapshot_repository, _unpriced())
        keys = _keys(service)
        response = client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "8.500.000"})
        assert response.status_code == 302
        assert _price_of(service) == Decimal("8500000")


# --------------------------------------------------------------------------
# (3) — cửa chặn DRIFT
# --------------------------------------------------------------------------

#: `<form …>` mở đầu, cùng toàn bộ thuộc tính của nó.
FORM_TAG = re.compile(r"<form\b[^>]*>", re.IGNORECASE | re.DOTALL)
ACTION = re.compile(r"""\baction\s*=\s*["']([^"']*)["']""", re.IGNORECASE)


def _forms_declaring_idempotent():
    """Mọi `<form data-idempotent …>` trong template, kèm nơi tìm thấy."""
    found = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        for tag in FORM_TAG.findall(path.read_text(encoding="utf-8")):
            if "data-idempotent" not in tag:
                continue
            action = ACTION.search(tag)
            found.append((path.relative_to(REPO_ROOT),
                          action.group(1) if action else ""))
    return found


#: Mọi method GHI. Không chỉ `POST`: route duy nhất đọc `idempotency_key`
#: hôm nay là `PATCH /api/v1/orders/<order_key>`, và một cửa chặn chỉ soi
#: `POST` sẽ báo "không route nào đọc mã" — sai, và sai theo hướng nguy
#: hiểm (nó sẽ coi MỌI form khai `data-idempotent` là vi phạm, kể cả form
#: trỏ đúng vào một route có đỡ).
WRITE_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})


def _mutating_view_sources(application):
    """`{đường dẫn rule: mã nguồn view}` cho mọi rule nhận một method GHI."""
    sources = {}
    for rule in application.url_map.iter_rules():
        if not (rule.methods or set()) & WRITE_METHODS:
            continue
        view = application.view_functions.get(rule.endpoint)
        if view is None:
            continue
        try:
            sources[str(rule.rule)] = inspect.getsource(view)
        except (OSError, TypeError):       # view dựng động: không đọc được
            sources[str(rule.rule)] = ""
    return sources


def _routes_reading_the_key(application):
    return {rule for rule, source in _mutating_view_sources(application).items()
            if "idempotency_key" in source}


def _violations(forms, honouring):
    """Form khai `data-idempotent` mà route của nó KHÔNG đọc mã."""
    bad = []
    for where, action in forms:
        # Template dùng `url_for(...)`: so bằng chuỗi không nói được gì, nên
        # nó được coi là VI PHẠM cho tới khi ai đó dạy hàm này giải nó. Một
        # cửa chặn mặc định "cho qua" là cửa không chặn gì.
        target = action.split("?")[0]
        if target not in honouring:
            bad.append((str(where), action))
    return bad


class TestNoTemplatePromisesWhatTheServerDoesNotDo:
    def test_today_no_html_route_honours_an_idempotency_key(self, client):
        """Trạng thái hôm nay, ghi thành một mệnh đề kiểm được.

        Nếu ai mở rộng `mutation_guard` cho một route HTML, test này đỏ —
        và đó đúng là lúc phải đọc lại docstring đầu file, vì hướng đã chọn
        của `P1-5` khi ấy không còn là hướng đúng.
        """
        application = client.application
        honouring = _routes_reading_the_key(application)
        assert honouring == {"/api/v1/orders/<order_key>"}, (
            "tập route đọc `idempotency_key` đã thay đổi: "
            f"{sorted(honouring)}. Nếu một route HTML nay thật sự chống lặp "
            "được (guard trong CÙNG transaction ghi, có `base_revision` để "
            "so), hãy cho template của nó khai `data-idempotent` và cập nhật "
            "docstring của file này.")

    def test_no_template_declares_data_idempotent_against_a_bare_route(
        self, client
    ):
        """CỬA CHẶN: một form hứa chống lặp phải có route đỡ nó."""
        forms = _forms_declaring_idempotent()
        bad = _violations(forms, _routes_reading_the_key(client.application))
        assert bad == [], (
            "form khai `data-idempotent` nhưng route KHÔNG đọc "
            "`idempotency_key`: " + "; ".join(f"{w} → {a!r}" for w, a in bad)
            + ". `app.js` sẽ gắn mã và mọc nút THỬ LẠI với câu 'server nhận "
            "ra mã của lần gửi này và không ghi hai lần' — một lời hứa "
            "không có gì đỡ. Đó đúng là lỗi P1-5.")

    def test_the_drift_gate_actually_catches_a_violation(self, client):
        """Cửa chặn trên hôm nay chạy trên một tập RỖNG (không template nào
        khai `data-idempotent`), nên nó xanh mà chưa chứng minh được gì.

        Bài này chạy CÙNG hàm kiểm trên một form giả lập vi phạm, và trên
        một form giả lập hợp lệ. Không có nó, `test_no_template_declares…`
        là một mệnh đề rỗng và sẽ ở lại rỗng kể cả khi hàm kiểm hỏng.
        """
        honouring = _routes_reading_the_key(client.application)

        vi_pham = [(Path("app/web/templates/gia_lap.html"),
                    "/kinh-doanh/nhan-vien/gia-nhap")]
        assert _violations(vi_pham, honouring), (
            "hàm kiểm KHÔNG bắt được một form khai `data-idempotent` trỏ "
            "vào một route không đọc mã — cửa chặn đang hỏng")

        hop_le = [(Path("app/web/templates/gia_lap.html"),
                   "/api/v1/orders/<order_key>")]
        assert _violations(hop_le, honouring) == [], (
            "hàm kiểm báo vi phạm cho một route CÓ đọc mã — cửa chặn sẽ "
            "chặn oan và người sau sẽ tắt nó")

    def test_the_form_scanner_actually_finds_forms(self):
        """Và hàm quét template cũng phải thật sự quét được.

        Nếu `FORM_TAG` hỏng, `_forms_declaring_idempotent()` trả rỗng mãi
        và cửa chặn trên xanh vĩnh viễn. Bài này kiểm hàm quét trên chính
        thư mục template thật: nó phải tìm ra CÁC form (số lượng > 0), và
        không form nào trong số đó khai `data-idempotent`.
        """
        every = [tag for path in TEMPLATES.rglob("*.html")
                 for tag in FORM_TAG.findall(path.read_text(encoding="utf-8"))]
        assert len(every) > 10, (
            f"chỉ tìm thấy {len(every)} thẻ <form> trong toàn bộ template — "
            "regex FORM_TAG đang hỏng, và cửa chặn drift là mệnh đề rỗng")
        assert _forms_declaring_idempotent() == [], (
            "có template khai `data-idempotent`: "
            f"{_forms_declaring_idempotent()}")
