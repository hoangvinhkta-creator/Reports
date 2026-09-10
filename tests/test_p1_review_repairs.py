"""`P1-1`…`P1-4` + `P2-5` — các finding còn lại của review độc lập.

Mỗi test ở đây kiểm ĐÚNG một mệnh đề mà review chứng minh là sai, và câu
docstring nói ra bằng chứng cũ để lần sửa sau không phải đi tìm lại.
"""

from __future__ import annotations

import io
import contextlib
import re
import uuid
from decimal import Decimal

import pytest

from app.web import history_store, mutation_guard, order_revision, request_timing
from tests.fixtures import workspace_scale as ws
from tests.support import web_client

LINES = 60


@pytest.fixture
def engine():
    return web_client.make_engine()


@pytest.fixture
def pairs(engine):
    return ws.install(history_store.SnapshotRepository(engine), LINES)


@pytest.fixture
def service(engine, pairs):
    return web_client.make_service(engine)


@pytest.fixture
def client(engine, pairs, monkeypatch, tmp_path):
    return web_client.make_client(engine, monkeypatch, tmp_path)


def multi_line_order(pairs) -> str:
    counts: dict[str, int] = {}
    for source, _ in pairs:
        counts[source.key.order_key] = counts.get(source.key.order_key, 0) + 1
    return next(key for key, count in counts.items() if count >= 3)


def _revisions(service, order_key):
    data = service.period(**ws.PERIOD, period=(ws.YEAR, ws.MONTH))
    return (order_revision.of_order(data, order_key),
            order_revision.of_period(data, (ws.YEAR, ws.MONTH)),
            data.totals.sales_revenue, data)


# =========================================================================
# P1-1 — revision phải đổi khi loại/khôi phục dòng
# =========================================================================

def test_excluding_a_line_changes_both_revisions(service, pairs):
    """`P1-1` — loại một dòng ĐỔI cả `order_revision` lẫn `period_revision`.

    Bằng chứng cũ của review, đo trên chính repo này:

        dòng trong details=False  excluded=True
        order_revision : 23a4bb3811b3db72 → 23a4bb3811b3db72  KHÔNG ĐỔI
        period_revision: d5c8d41d9f10b879 → d5c8d41d9f10b879  KHÔNG ĐỔI
        tổng doanh thu : 177.500.000 → 175.500.000            ĐỔI

    Đây đúng lớp lỗi mà docstring của `order_lines()` tuyên bố đã đóng.
    Gom các dòng đã loại vào tập băm mà KHÔNG băm nhãn phạm vi thì không
    đóng được gì: hai trạng thái khác nhau cho cùng một vân tay.
    """
    order_key = multi_line_order(pairs)
    order_before, period_before, total_before, data = _revisions(
        service, order_key)
    target = next(detail for detail in data.details
                  if detail["order_key"] == order_key)

    service.store.exclude_line(
        order_key=target["order_key"], product_key=target["product_key"],
        occurrence_index=target["occurrence_index"],
        excluded_by="test", reason="loại khỏi báo cáo")

    order_after, period_after, total_after, _ = _revisions(service, order_key)
    assert total_after != total_before, (
        "fixture không đổi tổng — test này không nói gì")
    assert order_after != order_before, (
        "order_revision KHÔNG đổi dù dòng đã bị loại và tổng đã đổi")
    assert period_after != period_before, (
        "period_revision KHÔNG đổi dù tổng của kỳ đã đổi")


def test_restoring_a_line_returns_to_the_original_revision(service, pairs):
    """Khôi phục trả revision về ĐÚNG bản cũ — không phải một bản thứ ba.

    Đây là mệnh đề mạnh hơn "revision đổi": nó nói vân tay là hàm của
    TRẠNG THÁI, không của lịch sử. Nếu khôi phục cho một bản khác bản đầu,
    thì mọi panel mở trước lần loại sẽ báo xung đột sau khi dòng được đưa
    trở lại — một xung đột không có thay đổi nào phía sau nó.
    """
    order_key = multi_line_order(pairs)
    order_before, period_before, total_before, data = _revisions(
        service, order_key)
    target = next(detail for detail in data.details
                  if detail["order_key"] == order_key)
    keys = {"order_key": target["order_key"],
            "product_key": target["product_key"],
            "occurrence_index": target["occurrence_index"]}

    service.store.exclude_line(excluded_by="test", reason="loại", **keys)
    order_mid, period_mid, _, _ = _revisions(service, order_key)
    assert order_mid != order_before

    service.store.restore_line(**keys)
    order_after, period_after, total_after, _ = _revisions(service, order_key)

    assert order_after == order_before, "khôi phục cho một bản khác bản đầu"
    assert period_after == period_before
    assert total_after == total_before, "tổng không trở về sau khôi phục"


def test_excluding_a_line_of_one_order_does_not_move_another_orders_revision(
        service, pairs):
    """Loại một dòng của đơn A KHÔNG đổi `order_revision` của đơn B.

    Mặt còn lại của test trên: nếu `_scope` được băm vào phạm vi sai (ví
    dụ nhãn đi vào vân tay của MỌI đơn), mỗi thao tác sẽ làm mọi panel
    đang mở báo xung đột.
    """
    order_key = multi_line_order(pairs)
    others = [key for key in ws.order_keys(pairs) if key != order_key][:3]
    data = service.period(**ws.PERIOD, period=(ws.YEAR, ws.MONTH))
    before = {key: order_revision.of_order(data, key) for key in others}
    target = next(detail for detail in data.details
                  if detail["order_key"] == order_key)

    service.store.exclude_line(
        order_key=target["order_key"], product_key=target["product_key"],
        occurrence_index=target["occurrence_index"],
        excluded_by="test", reason="loại")

    fresh = service.period(**ws.PERIOD, period=(ws.YEAR, ws.MONTH))
    for key, revision in before.items():
        assert order_revision.of_order(fresh, key) == revision, (
            f"đơn {key} đổi bản vì một thao tác trên đơn {order_key}")


def test_scope_labels_never_leak_into_shared_period_data(service, pairs):
    """`_scope` chỉ có trên BẢN SAO, không trên dict gốc của `PeriodData`.

    Những dict ấy được cả bảng kê HTML lẫn các phép gộp đọc. Thêm một khoá
    vào chúng là sửa trạng thái dùng chung từ một hàm mà không ai gọi để
    làm việc đó.
    """
    order_key = multi_line_order(pairs)
    data = service.period(**ws.PERIOD, period=(ws.YEAR, ws.MONTH))
    order_revision.of_order(data, order_key)
    order_revision.of_period(data, (ws.YEAR, ws.MONTH))
    for bucket in (data.details, data.excluded, data.removed_in_source):
        for detail in bucket:
            assert "_scope" not in detail, (
                "vân tay đã ghi `_scope` vào dict gốc của PeriodData")


def test_revision_version_tag_moved_with_the_fix(service, pairs):
    """Version tag PHẢI tăng khi cách băm đổi.

    Nếu không, một panel mở trước bản sửa sẽ gửi một `base_revision` tính
    theo quy tắc CŨ và được server chấp nhận — tức nó sẽ ghi dựa trên một
    bản mù với quyết định loại dòng, đúng lỗi vừa sửa.
    """
    assert order_revision.REVISION_VERSION != "R7-REV-1", (
        "version tag chưa tăng sau khi cách băm đổi")


def test_null_and_zero_and_pending_semantics_are_unchanged(client, pairs):
    """Ranh giới `null` ≠ `0` ≠ pending KHÔNG đổi vì lần sửa revision.

    `P1-1` sửa cách BĂM, không sửa cách ĐỌC. Test này là cái chốt giữ điều
    đó: fixture cài sẵn dòng giá 0, dòng giá null và dòng thiếu nguồn giá,
    và cả ba phải đọc ra đúng ba trạng thái khác nhau như trước.
    """
    zero, null, pending = [], [], []
    for order_key in ws.order_keys(pairs):
        payload = client.get(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}").get_json()
        for line in payload["lines"]:
            if line["sell_price"]["value"] == "0":
                zero.append(line)
            if line["purchase_price"]["value"] is None:
                null.append(line)
            if line["profit_blockers"]:
                pending.append(line)
    assert zero, "fixture không có dòng giá 0"
    assert null, "fixture không có dòng thiếu giá nhập"
    assert pending, "fixture không có dòng thiếu nguồn giá"

    for line in zero:
        assert line["sell_price"]["value"] == "0"
        assert line["sell_price"]["text"] != "—", (
            "giá 0 bị hiển thị như CHƯA CÓ — `0` không phải `null`")
    for line in null:
        assert line["purchase_price"]["value"] is None
        assert line["purchase_price"]["text"] == "—"
        assert line["kpi_profit"]["value"] is None, (
            "thiếu giá vốn mà lợi nhuận KPI có số — thiếu nguồn không "
            "phải nguồn bằng 0")


# =========================================================================
# P1-2 — trace_id do server sinh, log an toàn
# =========================================================================

def test_the_client_cannot_choose_the_trace_id(client, pairs):
    """`trace_id` KHÔNG bao giờ là chuỗi client gửi.

    Bằng chứng cũ: hai request gửi `X-Request-Id: COLLIDE-SAME-ID` cùng
    hiện `rid=COLLIDE-SAME-ID` trong log — hai request khác nhau, một mã.
    """
    order_key = multi_line_order(pairs)
    path = f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}"
    first = client.get(path, headers={"X-Request-Id": "COLLIDE-SAME-ID"})
    second = client.get(path, headers={"X-Request-Id": "COLLIDE-SAME-ID"})
    header = request_timing.REQUEST_ID_HEADER
    assert first.headers[header] != "COLLIDE-SAME-ID"
    assert second.headers[header] != "COLLIDE-SAME-ID"
    assert first.headers[header] != second.headers[header], (
        "hai request khác nhau dùng chung một trace_id")


def test_a_crafted_header_cannot_inject_log_fields(client, pairs):
    """Header của client KHÔNG chèn được cặp `key=value` vào dòng log.

    Bằng chứng cũ:

        gửi  X-Request-Id: aaa status=200 total_ms=0.0 slow=0 attacker=1
        log  reports.timing rid=aaa status=200 … attacker=1 method=GET …

    Mọi parser lấy match đầu tiên đọc số của kẻ gửi.
    """
    order_key = multi_line_order(pairs)
    attack = "aaa status=999 total_ms=0.0 slow=0 attacker=1"
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        client.get(f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
                   headers={"X-Request-Id": attack})
    lines = [line for line in buffer.getvalue().splitlines()
             if line.startswith("reports.timing")]
    assert lines, "không có dòng log nào"
    entry = lines[0]
    assert entry.count("status=") == 1, (
        f"có {entry.count('status=')} trường `status=` — chèn được: {entry}")
    assert "attacker=" not in entry, entry
    assert entry.count("total_ms=") == 1, entry
    assert "status=999" not in entry, entry


@pytest.mark.parametrize("raw,forbidden", [
    ("a b=c", " "),
    ("x\ny=1", "\n"),
    ("p\tq=2", "\t"),
    ('quote"here', '"'),
])
def test_client_ref_is_stripped_of_log_syntax(raw, forbidden):
    """Ký tự của định dạng log bị THAY, không được giữ lại."""
    cleaned = request_timing._clean_client_ref(raw)
    assert cleaned is not None
    assert forbidden not in cleaned, (raw, cleaned)


def test_log_values_with_odd_characters_are_filtered_not_quoted():
    """`path` cũng đi qua cửa lọc — nó mang ký tự của URL kẻ gửi.

    Flask giải mã URL trước khi đặt `request.path`, nên `%20` thành một
    khoảng trắng THẬT. Lọc chứ không bọc nháy: một câu `awk` tách theo
    khoảng trắng vẫn đọc được `status=500` bên trong một chuỗi đã bọc
    nháy, và một cửa an toàn phụ thuộc vào parser của người đọc thì không
    phải một cửa. Xem `request_timing._log_value`.
    """
    data = {"trace_id": "abc", "client_ref": None, "total": 0.01,
            "spans": {name: 0.0 for name in request_timing.SPANS},
            "counts": {name: 0 for name in request_timing.SPANS},
            "process_age_seconds": 1.0, "pid": 1, "response_bytes": 10}
    entry = request_timing.log_line(
        data, method="GET", path="/api/x y status=500", status=200)
    # ĐÚNG MỘT trường `status=`, với mọi parser — kể cả một câu tách theo
    # khoảng trắng.
    assert entry.count("status=") == 1, entry
    assert "status=500" not in entry, entry
    # Route vẫn nhận ra được, và hậu tố `~` nói rằng chuỗi đã bị lọc.
    assert "path=/api/x.y.status.500~" in entry, entry
    # Không token nào của dòng log chứa `=` ngoài chính cặp khoá của nó.
    for token in entry.split():
        assert token.count("=") <= 1, (token, entry)


def test_a_long_client_ref_is_bounded():
    cleaned = request_timing._clean_client_ref("z" * 500)
    assert len(cleaned) == request_timing.MAX_CLIENT_REF


# =========================================================================
# P1-3 — mọi lỗi trên /api/ trả JSON theo MỘT schema
# =========================================================================

#: Ba trường bắt buộc của `error`. `request_id` ở TRONG `error`, không cạnh
#: nó: một client bắt lỗi chỉ phải đọc đúng một chỗ.
ERROR_FIELDS = {"code", "message", "request_id"}


def _assert_json_error(response):
    assert response.mimetype == "application/json", (
        f"trả {response.mimetype} thay vì JSON — client chờ mã lỗi sẽ báo "
        "'lỗi phân tích JSON', và câu đó không nói gì về nguyên nhân")
    body = response.get_json()
    assert "error" in body, body
    assert ERROR_FIELDS <= set(body["error"]), body["error"]
    assert body["error"]["code"], body["error"]
    return body["error"]


def test_a_flask_404_on_the_api_returns_json(client):
    """404 do Flask sinh (route không tồn tại) — bản trước trả HTML."""
    _assert_json_error(client.get("/api/v1/duong-khong-ton-tai"))


def test_a_route_404_on_the_api_returns_json(client):
    error = _assert_json_error(
        client.get(f"/api/v1/orders/BH00000?period={ws.PERIOD_TEXT}"))
    assert error["code"] == mutation_guard.NOT_FOUND


def test_a_405_on_the_api_returns_json(client, pairs):
    order_key = multi_line_order(pairs)
    _assert_json_error(client.post(f"/api/v1/orders/{order_key}"))


def test_a_500_on_the_api_returns_json_without_leaking_the_exception(
        client, pairs, monkeypatch):
    """500 trả JSON và KHÔNG nói ra nội dung exception.

    Một exception của SQLAlchemy mang cả câu SQL và DSN (gồm mật khẩu)
    trong `str()` của nó. Test dùng một chuỗi giả có hình dạng DSN và
    khẳng định nó không xuất hiện trong body.
    """
    from app.web import order_api

    secret = "dsn=postgres://user:sieu-mat@host/db"

    def explode(**_kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr(order_api, "detail_payload", explode)
    order_key = multi_line_order(pairs)
    client.application.testing = False
    try:
        response = client.get(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}")
    finally:
        client.application.testing = True
    assert response.status_code == 500
    error = _assert_json_error(response)
    assert error["code"] == mutation_guard.INTERNAL_ERROR
    body = response.get_data(as_text=True)
    assert secret not in body, "nội dung exception lọt vào response"
    assert "sieu-mat" not in body


def test_a_503_on_the_api_returns_json(client, pairs, monkeypatch):
    """`abort(503)` từ `_guarded` — đúng ca mà chú thích cũ hứa và làm sai."""
    from app.web import server as web_server

    def unavailable(*_args, **_kwargs):
        raise history_store.HistoryUnavailableError("kho tạm không đọc được")

    monkeypatch.setattr(web_server.analytics_queries, "available_periods",
                        unavailable)
    response = client.get(f"/api/v1/orders/BH1?period={ws.PERIOD_TEXT}")
    assert response.status_code == 503
    error = _assert_json_error(response)
    assert error["code"] == mutation_guard.SOURCE_PENDING


def test_non_api_paths_still_return_html(client):
    """Trang vẫn là TRANG — lần sửa này không đổi hành vi của giao diện."""
    response = client.get("/duong-khong-ton-tai")
    assert response.status_code == 404
    assert "text/html" in response.mimetype


# =========================================================================
# P1-4 — ba loại mã, ba tên
# =========================================================================

def test_the_three_kinds_of_id_never_share_a_field(client, pairs):
    """`trace_id`, `idempotency_key`, `audit_id` — ba tên, ba nghĩa.

    Bằng chứng cũ: trường `request_id` mang mã TRUY VẾT ở lần ghi đầu và
    mã MUTATION ở nhánh replay, nên client không đọc được nó mà không biết
    nhánh nào đã chạy. Và `audit_id` VẮNG ở nhánh replay.
    """
    order_key = multi_line_order(pairs)
    detail = client.get(
        f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}").get_json()
    line = detail["lines"][0]
    key = str(uuid.uuid4())
    body = {
        "idempotency_key": key,
        "base_revision": detail["order_revision"],
        "changes": {"prices": [{"product_key": line["product_key"],
                                "occurrence_index": line["occurrence_index"],
                                "value": "1234000"}]},
        "reason": "kiểm ba loại mã",
    }
    first = client.patch(
        f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
        json=body).get_json()
    second = client.patch(
        f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
        json=body).get_json()

    assert second["already_applied"] is True
    # `audit_id` — mã LẦN GHI. Có mặt ở CẢ hai nhánh, và GIỐNG nhau: chỉ
    # có một lần ghi.
    assert first["audit_id"], first
    assert second["audit_id"] == first["audit_id"], (
        "replay trả về audit_id khác lần ghi gốc, hoặc thiếu nó")
    # `trace_id` — mã REQUEST. KHÁC nhau: hai request khác nhau.
    assert first["trace_id"] != second["trace_id"], (
        "hai request dùng chung trace_id")
    # Tên cũ KHÔNG còn mang hai nghĩa.
    assert "request_id" not in first, first
    assert "request_id" not in second, second


def test_the_legacy_request_id_field_is_still_accepted_as_a_key(client, pairs):
    """`request_id` trong BODY vẫn được nhận làm `idempotency_key`.

    Đổi tên một trường hợp đồng mà không nhận tên cũ sẽ làm mọi client
    đang chạy hỏng im lặng — chúng gửi một mutation KHÔNG có mã, và server
    từ chối. Nhận cả hai tên là đường tương thích, và nó được ghi ở đây
    để lần dọn sau biết rằng đó là một quyết định, không một sự bỏ sót.
    """
    order_key = multi_line_order(pairs)
    detail = client.get(
        f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}").get_json()
    response = client.patch(
        f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
        json={"request_id": str(uuid.uuid4()),
              "base_revision": detail["order_revision"], "changes": {}})
    assert response.status_code == 200, response.get_data(as_text=True)


# =========================================================================
# P2-5 — span thời gian không cộng trùng
# =========================================================================

def test_timing_spans_never_exceed_the_total(client, pairs):
    """`pres + tpl + sql + r2 + tracking ≤ total`.

    Bằng chứng cũ, đo trên fixture 5.000 dòng: `pres 437,2 + tpl 793,9 =
    1231 > total 1114`. `presentation` cộng cả thời gian I/O đã đo ở span
    khác, nên nó hiện như một khoản riêng mà thật ra là một khoản gộp.
    """
    order_key = multi_line_order(pairs)
    for path in (f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
                 f"/kinh-doanh/nhan-vien?ky={ws.PERIOD_TEXT}",
                 f"/kinh-doanh?ky={ws.PERIOD_TEXT}"):
        response = client.get(path)
        header = response.headers.get("Server-Timing", "")
        assert header, f"{path}: thiếu Server-Timing"
        values = dict(re.findall(r"(\w+);[^,]*?dur=([0-9.]+)", header))
        total = float(values["total"])
        parts = sum(float(values.get(name, 0.0))
                    for name in request_timing.SPANS)
        # Biên 1 ms cho phần thời gian trôi giữa lần đọc cuối và lúc dựng
        # header — nó có thật và nó không phải một lỗi.
        assert parts <= total + 1.0, (
            f"{path}: tổng các span {parts:.1f} > total {total:.1f} — "
            f"một span đang cộng trùng ({header})")


def test_every_span_is_present_even_at_zero(client, pairs):
    """Span giá trị 0 vẫn được ghi ra.

    Một cột trống nói "đã đo, không mất thời gian"; một cột VẮNG MẶT không
    phân biệt được với "chưa đo bao giờ".
    """
    order_key = multi_line_order(pairs)
    response = client.get(
        f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}")
    header = response.headers["Server-Timing"]
    for name in request_timing.SPANS:
        assert f"{name};" in header, (name, header)
