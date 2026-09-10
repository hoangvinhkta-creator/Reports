"""`STAB-03` + `API-01`/`API-02` — chống lặp, revision, và payload gọn.

File này canh những mệnh đề mà brief đặt làm điều kiện hoàn thành nhiệm vụ
đầu, và mỗi mệnh đề được kiểm bằng một tình huống THẬT chứ bằng một lời
gọi hàm:

    ghi trùng       server ghi xong rồi response thất lạc; gửi lại cùng
                    `request_id` KHÔNG tạo bản ghi thứ hai
    xung đột        hai người sửa cùng một bản; người thứ hai nhận
                    `REVISION_CONFLICT` kèm bản hiện tại
    draft           validation lỗi ⟹ không ghi gì, và câu lỗi nói ra
                    trường nào
    payload         chi tiết một đơn dưới 50 KB, kể cả trên fixture
                    5.000 dòng
    nghiệp vụ       tổng công ty và tiền của các đơn KHÁC không đổi vì
                    một lần sửa đơn này

Mệnh đề cuối là mệnh đề quan trọng nhất của cả file: một API mới có thể
nhanh, gọn, chống lặp đúng, và vẫn làm sai sổ sách. Nên mỗi test ghi dữ
liệu đều so lại tổng.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.web import history_store, mutation_guard, order_revision
from tests.fixtures import workspace_scale as ws
from tests.support import web_client

#: Fixture nhỏ cho phần lớn test: 200 dòng đủ để có đơn 1/2/3 dòng, giá 0,
#: giá null và dòng thiếu nguồn giá. Ngân sách payload được kiểm riêng
#: trên 5.000 dòng, ở test cuối file.
SMALL = 200


@pytest.fixture
def engine():
    return web_client.make_engine()


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def pairs(repository):
    return ws.install(repository, SMALL)


@pytest.fixture
def client(engine, pairs, monkeypatch, tmp_path):
    return web_client.make_client(engine, monkeypatch, tmp_path)


@pytest.fixture
def service(engine, pairs):
    return web_client.make_service(engine)


def multi_line_order(pairs) -> str:
    """Mã của một đơn có NHIỀU dòng — hình dạng đắt nhất của mọi test ghi."""
    counts: dict[str, int] = {}
    for source, _ in pairs:
        counts[source.key.order_key] = counts.get(source.key.order_key, 0) + 1
    for key, count in counts.items():
        if count >= 3:
            return key
    raise AssertionError("fixture không có đơn nào từ 3 dòng")


def detail(client, order_key: str):
    response = client.get(
        f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}")
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()


def patch(client, order_key: str, body: dict):
    return client.patch(f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
                        json=body)


def company_total(service) -> Decimal:
    """Tổng doanh thu của CẢ kỳ — bất biến của mọi test ghi ở file này."""
    data = service.period(**ws.PERIOD, period=(ws.YEAR, ws.MONTH))
    return data.totals.sales_revenue


def price_change(line, value: str) -> dict:
    return {"product_key": line["product_key"],
            "occurrence_index": line["occurrence_index"], "value": value}


# --- API-01: đọc ----------------------------------------------------------

def test_order_detail_returns_only_that_order(client, pairs):
    order_key = multi_line_order(pairs)
    payload = detail(client, order_key)
    assert payload["order_key"] == order_key
    assert payload["lines"], "đơn không có dòng nào"
    assert {line["order_key"] for line in payload["lines"]} == {order_key}, (
        "payload chứa dòng của đơn khác")


def test_order_detail_carries_both_revisions(client, pairs):
    payload = detail(client, multi_line_order(pairs))
    assert payload["order_revision"], "thiếu order_revision"
    assert payload["period_revision"], "thiếu period_revision"
    # Hai bản KHÁC nhau: chúng nói về hai phạm vi, và dùng lẫn sẽ làm một
    # thao tác trên đơn khác báo xung đột cho đơn đang mở.
    assert payload["order_revision"] != payload["period_revision"]


def test_order_detail_never_leaks_imei(client, pairs):
    """`DEC-R5-03` — mã máy chỉ tồn tại ở đúng một route, không ở đây."""
    payload = detail(client, multi_line_order(pairs))
    assert "imei" not in payload
    for line in payload["lines"]:
        assert "imei" not in line, line


def test_money_is_exact_strings_never_json_numbers(client, pairs):
    """Tiền đi qua dây bằng CHUỖI thập phân, không bằng `double`.

    Đây là ranh giới `§3` của brief ("giữ Python Decimal; không chuyển phép
    tính tiền sang JavaScript Number"). Một JSON number đi qua `double` của
    JavaScript và mất chính xác ở đúng những con số lớn nhất.
    """
    payload = detail(client, multi_line_order(pairs))
    for line in payload["lines"]:
        for field in ("sell_price", "discount", "total_sales",
                      "purchase_price", "auto_purchase_price", "kpi_profit",
                      "converted_sales"):
            cell = line[field]
            assert set(cell) == {"value", "text"}, (field, cell)
            assert cell["value"] is None or isinstance(cell["value"], str), (
                f"{field}.value phải là chuỗi hoặc null, được {cell['value']!r}")
            assert isinstance(cell["text"], str), field


def test_null_price_is_null_not_zero(client, engine, pairs):
    """`null` ≠ `0` — brief §8, kiểm trên đúng dòng fixture cài sẵn.

    Fixture đặt `kpi_purchase_price = None` ở mỗi đơn thứ 23. Một payload
    biến nó thành `0` sẽ làm panel hiện một giá vốn hợp lệ cho một dòng
    chưa có giá vốn, và lợi nhuận của dòng đó trông như bằng cả doanh thu.
    """
    nulls = []
    for order_key in ws.order_keys(pairs):
        payload = detail(client, order_key)
        for line in payload["lines"]:
            if line["purchase_price"]["value"] is None:
                nulls.append((order_key, line))
    assert nulls, "fixture không có dòng nào thiếu giá nhập"
    for _, line in nulls:
        assert line["purchase_price"]["value"] is None
        assert line["purchase_price"]["text"] == "—", line["purchase_price"]
        # Và lợi nhuận KPI của nó cũng phải là CHƯA BIẾT, không phải 0.
        assert line["kpi_profit"]["value"] is None, line["kpi_profit"]


def test_order_detail_404_for_an_order_outside_the_period(client):
    response = client.get(
        f"/api/v1/orders/BH00000?period={ws.PERIOD_TEXT}")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == mutation_guard.NOT_FOUND


def test_api_errors_are_json_not_html(client):
    """Đường `/api/` trả JSON kể cả cho lỗi — không trả một TRANG.

    Một client nhận HTML ở chỗ nó chờ mã lỗi sẽ báo "lỗi phân tích JSON",
    và câu đó không nói gì về nguyên nhân thật.
    """
    response = client.get("/api/v1/orders/BH00000?period=khong-phai-ky")
    assert response.status_code == 404
    assert response.mimetype == "application/json", response.mimetype
    assert "code" in response.get_json()["error"]


# --- API-02: ghi ----------------------------------------------------------

def test_patch_requires_a_request_id(client, pairs):
    order_key = multi_line_order(pairs)
    payload = detail(client, order_key)
    response = patch(client, order_key, {
        "base_revision": payload["order_revision"], "changes": {}})
    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == mutation_guard.VALIDATION_ERROR
    assert error["field"] == "request_id"


def test_patch_writes_the_price_and_returns_a_new_revision(
        client, service, pairs):
    order_key = multi_line_order(pairs)
    before = detail(client, order_key)
    line = before["lines"][0]
    response = patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": before["order_revision"],
        "changes": {"prices": [price_change(line, "777000")]},
        "reason": "Đối chiếu lại hoá đơn nhập của nhà cung cấp.",
    })
    assert response.status_code == 200, response.get_data(as_text=True)
    body = response.get_json()
    assert body["order_revision"] != before["order_revision"], (
        "ghi xong mà revision không đổi — panel sẽ gửi lần sau với một "
        "base_revision đã lỗi thời ngay từ lúc nó nhận được")
    assert body["applied"]["price_writes"] == 1
    assert body["audit_id"], "thiếu audit id"
    assert body["applied_by"], "thiếu người ghi"
    # Giá mới đọc lại được, và nó là con số vừa gửi — không phải một con
    # số đã đi qua `double`.
    saved = [item for item in body["lines"]
             if item["product_key"] == line["product_key"]
             and item["occurrence_index"] == line["occurrence_index"]]
    assert saved and saved[0]["purchase_price"]["value"] == "777000"


def test_patch_returns_period_totals_computed_on_the_whole_period(
        client, service, pairs):
    """KPI trả về tính trên TOÀN KỲ, không chỉ các dòng của đơn vừa sửa.

    Brief §6: "KPI/tổng luôn tính trên toàn bộ kỳ, không chỉ các dòng đã
    tải". Một tổng chỉ cộng đơn vừa sửa là một con số nhỏ hơn hàng trăm
    lần và trông hoàn toàn hợp lý.
    """
    order_key = multi_line_order(pairs)
    before = detail(client, order_key)
    response = patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": before["order_revision"],
        "changes": {"prices": [price_change(before["lines"][0], "555000")]},
        "reason": "Cập nhật theo hoá đơn nhập.",
    })
    totals = response.get_json()["totals"]["period"]
    assert Decimal(totals["sales_revenue"]) == company_total(service)
    assert totals["lines"] == SMALL


def test_patch_does_not_move_company_sales_revenue(client, service, pairs):
    """BẤT BIẾN: sửa giá NHẬP không đổi DOANH THU của công ty.

    Đây là bất biến mà `tests/test_employee_workspace_ux.py` lặp lại ở
    nhiều chỗ, và nó được lặp lại ở đây vì cùng lý do: nó là thứ duy nhất
    phân biệt một API mới với một API mới làm hỏng sổ sách.
    """
    order_key = multi_line_order(pairs)
    total_before = company_total(service)
    before = detail(client, order_key)
    patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": before["order_revision"],
        "changes": {"prices": [price_change(before["lines"][0], "999000")]},
        "reason": "Đối chiếu hoá đơn.",
    })
    assert company_total(service) == total_before


def test_patch_leaves_other_orders_untouched(client, service, pairs):
    """Một lần sửa đơn A không đổi một đồng nào của đơn B."""
    order_key = multi_line_order(pairs)
    others = [key for key in ws.order_keys(pairs) if key != order_key][:5]
    snapshot = {key: detail(client, key)["order_revision"] for key in others}
    before = detail(client, order_key)
    patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": before["order_revision"],
        "changes": {"prices": [price_change(before["lines"][0], "123000")]},
        "reason": "Đối chiếu hoá đơn.",
    })
    for key, revision in snapshot.items():
        assert detail(client, key)["order_revision"] == revision, (
            f"đơn {key} đổi bản vì một lần sửa đơn {order_key}")


def test_patch_without_a_reason_is_refused_when_it_overrides_auto(
        client, service, pairs):
    """`R2 §4.4` — thay một giá AUTO mà không có lý do thì KHÔNG ô nào được ghi.

    Và quan trọng hơn câu lỗi: KHÔNG có bản ghi nào vào database. Đây là
    "không có thành công một phần" của R5 §4, kiểm qua đường API.
    """
    order_key = multi_line_order(pairs)
    before = detail(client, order_key)
    assert before["reason_required"], (
        "fixture không có dòng nào mang giá AUTO — test này không nói gì")
    response = patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": before["order_revision"],
        "changes": {"prices": [price_change(before["lines"][0], "111000")]},
    })
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == \
        mutation_guard.VALIDATION_ERROR
    # Không ghi gì ⟹ bản của đơn KHÔNG đổi.
    assert detail(client, order_key)["order_revision"] == \
        before["order_revision"]


def test_patch_rejects_a_numeric_price_value(client, pairs):
    """`value` phải là CHUỖI: rỗng = gỡ giá tay, `"0"` = giá bằng không.

    Nhận một JSON number ở đây sẽ trộn hai ý nghĩa đó ngay tại tầng vận
    chuyển, trước khi tầng nghiệp vụ có cơ hội phân biệt.
    """
    order_key = multi_line_order(pairs)
    before = detail(client, order_key)
    line = before["lines"][0]
    response = patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": before["order_revision"],
        "changes": {"prices": [{"product_key": line["product_key"],
                                "occurrence_index": line["occurrence_index"],
                                "value": 111000}]},
        "reason": "x",
    })
    assert response.status_code == 400
    assert response.get_json()["error"]["field"] == "changes.prices"


def test_patch_rejects_a_line_key_missing_its_occurrence(client, pairs):
    order_key = multi_line_order(pairs)
    before = detail(client, order_key)
    response = patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": before["order_revision"],
        "changes": {"prices": [
            {"product_key": before["lines"][0]["product_key"],
             "value": "111000"}]},
        "reason": "x",
    })
    assert response.status_code == 400
    assert "occurrence_index" in response.get_json()["error"]["message"]


# --- STAB-03: chống lặp ---------------------------------------------------

def test_replaying_the_same_request_id_does_not_write_twice(
        client, service, engine, pairs):
    """MÔ PHỎNG response thất lạc: gửi lại cùng `request_id`.

    Đây là nghiệm thu của brief §STAB-03 — "mô phỏng server commit thành
    công rồi ngắt response không làm ghi trùng". Server ĐÃ ghi (lần gửi
    thứ nhất trả 200); browser coi như không nhận được và gửi lại đúng mã
    đó.

    Ba điều phải đúng cùng lúc, và test kiểm cả ba: lần hai KHÔNG ghi
    (revision không đổi), lần hai TRẢ LẠI kết quả cũ (người dùng biết
    được đã lưu gì), và số bản ghi override trong database vẫn là một.
    """
    from app.web import business_store

    order_key = multi_line_order(pairs)
    before = detail(client, order_key)
    request_id = str(uuid.uuid4())
    body = {
        "request_id": request_id,
        "base_revision": before["order_revision"],
        "changes": {"prices": [price_change(before["lines"][0], "888000")]},
        "reason": "Đối chiếu hoá đơn nhập.",
    }

    first = patch(client, order_key, body)
    assert first.status_code == 200, first.get_data(as_text=True)
    after_first = detail(client, order_key)["order_revision"]

    store = business_store.BusinessDecisionStore(engine)
    overrides_after_first = len(store.purchase_price_overrides())

    # Lần gửi THỨ HAI, cùng mã, cùng body — kể cả `base_revision` giờ đã
    # CŨ (chính lần ghi thứ nhất làm nó cũ). Nó vẫn phải đi qua, vì một
    # lần thử lại không được biến thành một xung đột.
    second = patch(client, order_key, body)
    assert second.status_code == 200, second.get_data(as_text=True)
    replay = second.get_json()
    assert replay["already_applied"] is True, (
        "lần gửi thứ hai không được nhận ra là một lần thử lại")
    assert replay["order_revision"] == first.get_json()["order_revision"]
    assert replay["applied_at"], "thiếu mốc thời gian của lần ghi gốc"

    assert detail(client, order_key)["order_revision"] == after_first, (
        "lần gửi thứ hai đã ghi thêm — đúng lỗi mà STAB-03 đóng")
    assert len(store.purchase_price_overrides()) == overrides_after_first, (
        "database có thêm một bản ghi override từ lần gửi thứ hai")


def test_a_different_request_id_is_a_new_decision(client, pairs):
    """Mã KHÁC ⟹ quyết định MỚI, và nó được ghi.

    Mặt còn lại của test trên. Nếu cơ chế chống lặp chặn cả mã mới thì nó
    không phải chống lặp — nó là chống ghi.
    """
    order_key = multi_line_order(pairs)
    first = detail(client, order_key)
    patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": first["order_revision"],
        "changes": {"prices": [price_change(first["lines"][0], "222000")]},
        "reason": "Lần một.",
    })
    second = detail(client, order_key)
    response = patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "base_revision": second["order_revision"],
        "changes": {"prices": [price_change(second["lines"][0], "333000")]},
        "reason": "Lần hai.",
    })
    assert response.status_code == 200
    saved = detail(client, order_key)["lines"]
    values = {item["purchase_price"]["value"] for item in saved}
    assert "333000" in values, values


def test_a_no_op_patch_is_not_remembered_as_a_write(client, pairs):
    """Gửi một PATCH không đổi gì KHÔNG chiếm `request_id` cho một lần ghi.

    Nếu nó chiếm, thì lần gửi tiếp theo của cùng mã — lần mà người dùng
    thật sự sửa gì đó — sẽ bị trả về kết quả "không có gì thay đổi" và
    thay đổi của họ mất đi im lặng.
    """
    order_key = multi_line_order(pairs)
    before = detail(client, order_key)
    request_id = str(uuid.uuid4())
    empty = patch(client, order_key, {
        "request_id": request_id,
        "base_revision": before["order_revision"], "changes": {}})
    assert empty.status_code == 200
    assert empty.get_json()["changed_nothing"] is True

    real = patch(client, order_key, {
        "request_id": request_id,
        "base_revision": before["order_revision"],
        "changes": {"prices": [price_change(before["lines"][0], "444000")]},
        "reason": "Đối chiếu hoá đơn.",
    })
    assert real.status_code == 200
    assert real.get_json().get("already_applied") is not True
    values = {item["purchase_price"]["value"]
              for item in detail(client, order_key)["lines"]}
    assert "444000" in values, values


# --- UI-03: xung đột hai người dùng --------------------------------------

def test_a_stale_base_revision_is_a_conflict_not_a_silent_overwrite(
        client, pairs):
    """Hai người mở cùng một đơn; người thứ hai KHÔNG được ghi đè im lặng.

    Brief §UI-03: "khi revision cũ, trả bản hiện tại và trường đã thay
    đổi… không âm thầm last-write-wins".
    """
    order_key = multi_line_order(pairs)
    # Cả hai "người" đọc cùng một bản.
    seen_by_both = detail(client, order_key)
    stale = seen_by_both["order_revision"]

    # Người thứ nhất ghi.
    first = patch(client, order_key, {
        "request_id": str(uuid.uuid4()), "base_revision": stale,
        "changes": {"prices": [price_change(seen_by_both["lines"][0],
                                            "101000")]},
        "reason": "Người thứ nhất.",
    })
    assert first.status_code == 200

    # Người thứ hai ghi, vẫn dựa trên bản CŨ.
    second = patch(client, order_key, {
        "request_id": str(uuid.uuid4()), "base_revision": stale,
        "changes": {"prices": [price_change(seen_by_both["lines"][0],
                                            "202000")]},
        "reason": "Người thứ hai.",
    })
    assert second.status_code == 409
    error = second.get_json()["error"]
    assert error["code"] == mutation_guard.REVISION_CONFLICT
    # Bản hiện tại đi kèm, để panel so được mà không phải gọi thêm GET.
    assert error["order_revision"] != stale
    assert error["current"]["lines"], "xung đột không kèm bản hiện tại"

    # Và giá trị của người thứ nhất còn nguyên — không bị ghi đè.
    values = {item["purchase_price"]["value"]
              for item in detail(client, order_key)["lines"]}
    assert "101000" in values and "202000" not in values, values


def test_a_missing_base_revision_still_writes(client, pairs):
    """Form CŨ (chưa khai `base_revision`) vẫn phải ghi được.

    Quyết định này được nói ra ở `mutation_guard.revision_conflict`: đợt
    này không viết lại mọi form của hệ, và chặn chúng lại sẽ là một hồi
    quy chức năng. Chúng mất lớp bảo vệ xung đột — đó là hiện trạng của
    chúng từ trước, không phải một sự nới lỏng mới.
    """
    order_key = multi_line_order(pairs)
    before = detail(client, order_key)
    response = patch(client, order_key, {
        "request_id": str(uuid.uuid4()),
        "changes": {"prices": [price_change(before["lines"][0], "606000")]},
        "reason": "Không có base_revision.",
    })
    assert response.status_code == 200, response.get_data(as_text=True)


def test_revision_changes_only_when_the_order_changes(client, service, pairs):
    """Đọc hai lần không đổi bản; ghi một lần thì đổi.

    Đây là mệnh đề làm cho revision dùng được: nếu nó đổi ở mỗi lần đọc
    (vì một mốc thời gian đi vào vân tay), mọi lần lưu sẽ báo xung đột.
    """
    order_key = multi_line_order(pairs)
    assert detail(client, order_key)["order_revision"] == \
        detail(client, order_key)["order_revision"]


def test_period_revision_moves_when_any_order_changes(client, pairs):
    """Bản của KỲ đổi khi bất kỳ đơn nào đổi — kể cả đơn khác.

    Đó là lý do nó KHÔNG được dùng làm `base_revision` của một lần sửa
    đơn, và test này ghim đúng tính chất ấy thay vì để nó là một giả định.
    """
    keys = ws.order_keys(pairs)
    target, other = multi_line_order(pairs), None
    for key in keys:
        if key != target:
            other = key
            break
    before = detail(client, other)["period_revision"]
    source = detail(client, target)
    patch(client, target, {
        "request_id": str(uuid.uuid4()),
        "base_revision": source["order_revision"],
        "changes": {"prices": [price_change(source["lines"][0], "707000")]},
        "reason": "Đổi một đơn khác.",
    })
    assert detail(client, other)["period_revision"] != before


# --- Ngân sách payload ----------------------------------------------------

def test_order_detail_stays_under_the_payload_budget_at_5000_lines(
        engine, monkeypatch, tmp_path):
    """Chi tiết một đơn dưới 50 KB trên fixture 5.000 dòng (brief §6).

    Test này là lý do cả `API-01` tồn tại. Trên cùng fixture, route HTML
    `?sua=` trả ~14,5 MB (xem `scripts/stab01_baseline.py`), nên nó cũng
    là chỗ ghi lại rằng con số ấy KHÔNG quay lại được mà không ai thấy.

    Ngưỡng đặt ở 50 KB đúng như brief, không đặt ở con số vừa đo được:
    một ngưỡng bám sát số hiện tại sẽ đỏ vì một trường mới hợp lệ, và khi
    đó người ta nâng ngưỡng thay vì nghĩ.
    """
    pairs = ws.install(history_store.SnapshotRepository(engine), 5000)
    client = web_client.make_client(engine, monkeypatch, tmp_path)
    order_key = multi_line_order(pairs)
    response = client.get(
        f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}")
    assert response.status_code == 200
    size = len(response.get_data())
    assert size < 50 * 1024, f"{size} byte, ngân sách 50 KB"
    # Và nó chứa ĐÚNG các dòng của đơn đó, không phải cả bảng.
    assert len(response.get_json()["lines"]) <= 4


# --- Ranh giới của chính cơ chế ------------------------------------------

def test_request_id_must_be_non_empty(engine):
    guard = mutation_guard.MutationGuard(engine)
    for bad in (None, "", "   "):
        with pytest.raises(mutation_guard.MissingRequestIdError):
            guard.clean_request_id(bad)


def test_request_id_length_is_bounded(engine):
    guard = mutation_guard.MutationGuard(engine)
    with pytest.raises(mutation_guard.MissingRequestIdError):
        guard.clean_request_id("x" * (mutation_guard.MAX_REQUEST_ID + 1))


def test_remember_twice_returns_the_first_result(engine):
    """Va khoá chính KHÔNG phải lỗi — nó là cơ chế đang hoạt động.

    Hai worker cùng nhận một mã trong đúng cửa sổ giữa `replay_of()` và
    `remember()`. Người thứ hai phải ĐỌC LẠI hàng của người thứ nhất và
    trả nó về; ném lỗi ở đó sẽ biến một lần chống lặp THÀNH CÔNG thành
    một trang lỗi.
    """
    guard = mutation_guard.MutationGuard(engine)
    first = guard.remember(request_id="r1", route="test",
                           response={"n": 1}, entered_by="a")
    second = guard.remember(request_id="r1", route="test",
                            response={"n": 2}, entered_by="b")
    assert second.response == {"n": 1}, "kết quả lần ghi thứ hai đã thắng"
    assert second.entered_at == first.entered_at


def test_order_revision_is_none_for_an_unknown_order(service):
    """`None` ≠ một chuỗi rỗng, và khoảng cách đó là một cửa bảo vệ.

    "Đơn không tồn tại trong kỳ này" là một câu trả lời khác hẳn "đơn tồn
    tại và đang ở bản X". Gộp chúng lại (trả `""` cho cả hai) sẽ làm một
    PATCH lên một đơn không tồn tại vượt được cửa kiểm revision.
    """
    data = service.period(**ws.PERIOD, period=(ws.YEAR, ws.MONTH))
    assert order_revision.of_order(data, "BH00000") is None
    existing = data.details[0]["order_key"]
    assert order_revision.of_order(data, existing) is not None


def test_order_lines_does_not_mutate_shared_period_data(service):
    """`order_lines` gắn `_scope` vào BẢN SAO, không vào dict gốc.

    Những dict ấy thuộc về `PeriodData` và được cả bảng kê HTML lẫn các
    phép gộp đọc. Thêm một khoá vào chúng là sửa trạng thái dùng chung từ
    một hàm mà không ai gọi để làm việc đó.
    """
    data = service.period(**ws.PERIOD, period=(ws.YEAR, ws.MONTH))
    order_key = data.details[0]["order_key"]
    scoped = order_revision.order_lines(data, order_key)
    assert scoped and all("_scope" in line for line in scoped)
    assert all("_scope" not in detail for detail in data.details), (
        "order_lines đã ghi vào dict gốc của PeriodData")
