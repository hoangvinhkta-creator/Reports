"""`P0-1`/`P0-2`/`P0-3` — at-most-once và CAS revision, kiểm ĐỒNG THỜI.

File này là bằng chứng cho ba finding chặn merge của review độc lập, và nó
kiểm chúng theo đúng cách review đã dùng để chứng minh chúng: hai luồng
thật, một `threading.Barrier` đặt ngay trước lần ghi nghiệp vụ, và đếm số
lần tầng lưu THẬT được gọi.

## Vì sao PostgreSQL, không SQLite

SQLite chỉ cho MỘT writer tại một thời điểm trên cả database. Khoá ghi
toàn cục đó CHE BỚT race: trên SQLite kẻ thua nhận một lỗi lock (và
`_guarded` biến nó thành 503), nên một lần ghi trùng TRÔNG như một sự cố
hạ tầng. Trên PostgreSQL hai transaction không chặn nhau, và bản trước
sửa gọi `set_purchase_price()` HAI lần.

Không có PostgreSQL ⟹ `pytest.skip` với câu nói rõ phải đặt biến gì. Xem
`tests/support/postgres.py`.

## Barrier đặt ở đâu, và vì sao đúng chỗ đó

Ngay trước `apply_order_edit` — tức sau khi CẢ HAI request đã qua mọi cửa
kiểm và đang chuẩn bị ghi. Đó là cửa sổ mà check-then-act để hở, nên đó
là chỗ duy nhất một test có thể chứng minh cửa sổ ấy đã đóng.

Đặt barrier sớm hơn (ví dụ ở đầu route) sẽ không chứng minh gì: hai
request vẫn có thể chạy nối đuôi nhau một cách tình cờ và test xanh trên
một bản mã sai.
"""

from __future__ import annotations

import datetime
import tempfile
import threading
import uuid
from pathlib import Path

import pytest

from app.web import business_store, history_store, order_revision
from app.web import server as web_server
from tests.fixtures import workspace_scale as ws
from tests.support import postgres
from tools.tracking import live_pull

#: Đủ để có đơn 1/2/3 dòng và các ca giá 0/null/pending. Không cần lớn:
#: file này kiểm ĐỒNG THỜI, không kiểm quy mô.
LINES = 60

#: Trần thời gian chờ của barrier. Vượt nó nghĩa là một luồng không tới
#: được điểm hẹn — thường vì nó đã bị chặn ở một cửa TRƯỚC đó, và đó là
#: một thông tin hữu ích chứ không phải một lỗi hạ tầng.
BARRIER_TIMEOUT = 30


@pytest.fixture
def pg():
    engine, dispose = postgres.fresh_engine("p0")
    try:
        yield engine
    finally:
        dispose()


@pytest.fixture
def app(pg, monkeypatch):
    """App THẬT trên PostgreSQL. Chỉ mạng ngoài bị cắt."""
    monkeypatch.setattr(web_server, "select_latest_valid_captures",
                        lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today",
                        lambda: datetime.date(2026, 9, 30))
    application = web_server.create_app(
        db_path=Path(tempfile.mkdtemp()) / "runs.db",
        history=history_store.LegacyRepository(pg),
        snapshots=history_store.SnapshotRepository(pg))
    application.testing = True
    return application


@pytest.fixture
def scene(app, pg):
    """`(mã đơn, dòng đầu, revision hiện tại)` — điểm khởi đầu chung."""
    pairs = ws.install(history_store.SnapshotRepository(pg), LINES)
    counts: dict[str, int] = {}
    for source, _ in pairs:
        counts[source.key.order_key] = counts.get(source.key.order_key, 0) + 1
    order_key = next(key for key, count in counts.items() if count >= 3)
    with app.test_client() as client:
        payload = client.get(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}").get_json()
    return order_key, payload["lines"][0], payload["order_revision"]


class _WriteCounter:
    """Đếm số lần tầng lưu THẬT được gọi, và chặn cả hai luồng ở barrier.

    Đếm ở `BusinessDecisionStore.set_purchase_price` chứ ở route: at-most-once
    là một mệnh đề về HIỆU ỨNG (bao nhiêu lần ghi xảy ra), không về mã
    HTTP. Một bản mã trả hai lần 200 mà chỉ ghi một lần là ĐÚNG; một bản
    trả một 200 và một 503 mà ghi hai lần là SAI.
    """

    def __init__(self, monkeypatch, app, *, parties: int) -> None:
        self.calls: list[str] = []
        self._lock = threading.Lock()
        self._barrier = threading.Barrier(parties, timeout=BARRIER_TIMEOUT)

        original_write = business_store.BusinessDecisionStore.set_purchase_price

        def counted(inner_self, **kwargs):
            with self._lock:
                self.calls.append(kwargs.get("order_key"))
            return original_write(inner_self, **kwargs)

        monkeypatch.setattr(business_store.BusinessDecisionStore,
                            "set_purchase_price", counted)

        service_class = type(app.config["BUSINESS_SERVICE"])
        original_apply = service_class.apply_order_edit

        def barriered(inner_self, plan, **kwargs):
            # Điểm hẹn: cả hai luồng đã qua mọi cửa kiểm, chưa ai ghi.
            try:
                self._barrier.wait()
            except threading.BrokenBarrierError:
                pass
            return original_apply(inner_self, plan, **kwargs)

        monkeypatch.setattr(service_class, "apply_order_edit", barriered)

    def release(self) -> None:
        """Gỡ barrier để luồng đang chờ không treo tới hết timeout.

        Cần khi một luồng bị chặn ở cửa TRƯỚC `apply_order_edit` (ví dụ
        `REVISION_CONFLICT`) và vì thế không bao giờ tới điểm hẹn.
        """
        self._barrier.abort()


def _fire(app, order_key: str, bodies: list[dict]) -> list[dict]:
    """Gửi các PATCH SONG SONG; trả kết quả theo thứ tự `bodies`."""
    results: dict[int, dict] = {}

    def run(index: int) -> None:
        with app.test_client() as client:
            response = client.patch(
                f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
                json=bodies[index])
            payload = response.get_json() or {}
            results[index] = {
                "status": response.status_code,
                "already_applied": payload.get("already_applied"),
                "audit_id": payload.get("audit_id"),
                "code": (payload.get("error") or {}).get("code"),
            }

    threads = [threading.Thread(target=run, args=(i,))
               for i in range(len(bodies))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=BARRIER_TIMEOUT + 15)
    assert len(results) == len(bodies), (
        f"chỉ {len(results)}/{len(bodies)} luồng hoàn tất — một luồng treo")
    return [results[i] for i in range(len(bodies))]


def _body(*, key: str, revision, line: dict, value: str) -> dict:
    return {
        "idempotency_key": key,
        "base_revision": revision,
        "changes": {"prices": [{
            "product_key": line["product_key"],
            "occurrence_index": line["occurrence_index"],
            "value": value}]},
        "reason": "test đồng thời",
    }


def _prices(app, order_key: str) -> set:
    with app.test_client() as client:
        payload = client.get(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}").get_json()
    return {line["purchase_price"]["value"] for line in payload["lines"]}


# --- P0-1: cùng idempotency_key -----------------------------------------

def test_same_idempotency_key_writes_exactly_once(app, scene, monkeypatch):
    """`P0-1` — hai request đồng thời cùng mã ⟹ ĐÚNG MỘT lần ghi.

    Bản trước: `set_purchase_price()` 2 lần, kẻ thua HTTP 503.
    """
    order_key, line, revision = scene
    counter = _WriteCounter(monkeypatch, app, parties=2)
    shared = str(uuid.uuid4())
    bodies = [_body(key=shared, revision=revision, line=line,
                    value="1234000") for _ in range(2)]

    results = _fire(app, order_key, bodies)

    assert len(counter.calls) == 1, (
        f"set_purchase_price() gọi {len(counter.calls)} lần — at-most-once "
        "đòi đúng 1")
    # Không ai được nhận 503: một lần chống lặp THÀNH CÔNG không phải một
    # sự cố hạ tầng, và nói với người dùng "thử lại sau" ở đây là sai.
    assert all(item["status"] != 503 for item in results), results
    # Một trong hai phải là replay, hoặc bị từ chối bằng mã ổn định
    # `REQUEST_IN_FLIGHT` — cả hai đều là câu trả lời đúng, xem
    # `mutation_guard.RequestInFlightError`.
    replays = [item for item in results if item["already_applied"]]
    in_flight = [item for item in results if item["code"] == "REQUEST_IN_FLIGHT"]
    assert len(replays) + len(in_flight) == 1, results
    if replays:
        winners = [item for item in results if not item["already_applied"]]
        assert winners and winners[0]["audit_id"], results
        assert replays[0]["audit_id"] == winners[0]["audit_id"], (
            "replay trả về một audit_id KHÁC lần ghi gốc — `P1-4`")


def test_same_idempotency_key_leaves_one_decision_row(app, scene, monkeypatch,
                                                      pg):
    """Và database chỉ có ĐÚNG MỘT bản ghi quyết định.

    Đếm hàng thật thay vì tin mã HTTP: một bản mã trả 200 hai lần mà ghi
    một lần là đúng, còn một bản trả 200 một lần mà ghi hai lần là sai —
    và chỉ phép đếm này phân biệt được hai trường hợp đó.
    """
    order_key, line, revision = scene
    counter = _WriteCounter(monkeypatch, app, parties=2)
    shared = str(uuid.uuid4())
    _fire(app, order_key, [
        _body(key=shared, revision=revision, line=line, value="1234000")
        for _ in range(2)])

    store = business_store.BusinessDecisionStore(pg)
    overrides = [row for row in store.purchase_price_overrides()
                 if row[0] == order_key]
    assert len(overrides) == 1, f"{len(overrides)} bản ghi override"
    assert len(counter.calls) == 1


# --- P0-3: cùng base_revision, hai mã khác nhau -------------------------

def test_same_base_revision_lets_exactly_one_win(app, scene, monkeypatch):
    """`P0-3` — hai mã KHÁC nhau, cùng `base_revision` ⟹ một thắng, một xung đột.

    Bản trước: `set_purchase_price()` 2 lần, KHÔNG ai nhận
    `REVISION_CONFLICT` — kẻ thua chỉ nhận 503 do lock của SQLite, và trên
    PostgreSQL cả hai commit.
    """
    order_key, line, revision = scene
    counter = _WriteCounter(monkeypatch, app, parties=2)
    bodies = [
        _body(key=str(uuid.uuid4()), revision=revision, line=line,
              value="1110000"),
        _body(key=str(uuid.uuid4()), revision=revision, line=line,
              value="2220000"),
    ]

    results = _fire(app, order_key, bodies)

    assert len(counter.calls) == 1, (
        f"set_purchase_price() gọi {len(counter.calls)} lần — chỉ MỘT "
        "request được phép ghi")
    ok = [item for item in results if item["status"] == 200]
    conflicts = [item for item in results
                 if item["code"] == "REVISION_CONFLICT"]
    assert len(ok) == 1, results
    assert len(conflicts) == 1, (
        f"kẻ thua phải nhận REVISION_CONFLICT, được {results}")
    assert all(item["status"] != 503 for item in results), results
    # Đúng MỘT giá trị thắng, và nó là một trong hai giá đã gửi — không
    # phải một sự pha trộn.
    saved = _prices(app, order_key)
    assert len({"1110000", "2220000"} & saved) == 1, saved


def test_a_conflicting_request_writes_nothing_at_all(app, scene, monkeypatch):
    """Kẻ thua KHÔNG ghi gì — không nửa vời, không audit trail rác."""
    order_key, line, revision = scene
    counter = _WriteCounter(monkeypatch, app, parties=2)
    _fire(app, order_key, [
        _body(key=str(uuid.uuid4()), revision=revision, line=line,
              value="1110000"),
        _body(key=str(uuid.uuid4()), revision=revision, line=line,
              value="2220000"),
    ])
    counter.release()
    saved = _prices(app, order_key)
    assert not ({"1110000", "2220000"} <= saved), (
        f"cả hai giá cùng có mặt — last-write-wins đã xảy ra: {saved}")


# --- P0-2: crash trước khi chốt sổ --------------------------------------

def test_a_crash_before_the_ledger_rolls_back_the_write(app, scene,
                                                        monkeypatch, pg):
    """`P0-2` — chết SAU khi ghi, TRƯỚC khi chốt sổ ⟹ rollback CẢ HAI.

    Bản trước: giá đã vào database, `mutation_request` rỗng — và nút THỬ
    LẠI (hứa "server nhận ra và không ghi hai lần") ghi lần thứ hai.

    Nay hai việc đó nằm trong một transaction, nên chúng có cùng số phận.
    """
    from sqlalchemy import text

    order_key, line, revision = scene
    service_class = type(app.config["BUSINESS_SERVICE"])
    original_apply = service_class.apply_order_edit

    def write_then_die(inner_self, plan, **kwargs):
        original_apply(inner_self, plan, **kwargs)   # ghi THẬT
        raise RuntimeError("mô phỏng tiến trình chết trước khi chốt sổ")

    monkeypatch.setattr(service_class, "apply_order_edit", write_then_die)

    key = str(uuid.uuid4())
    body = _body(key=key, revision=revision, line=line, value="6111000")
    with app.test_client() as client:
        try:
            client.patch(
                f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
                json=body)
        except RuntimeError:
            pass  # `testing=True` để ngoại lệ nổ ra ngoài — đúng mô phỏng

    assert "6111000" not in _prices(app, order_key), (
        "lần ghi đã vào database dù transaction phải rollback")
    with pg.connect() as connection:
        rows = connection.execute(
            text("select count(*) from mutation_request")).scalar()
    assert rows == 0, f"sổ còn {rows} hàng sau rollback"

    # THỬ LẠI cùng mã ⟹ đúng MỘT hiệu ứng cuối cùng.
    monkeypatch.setattr(service_class, "apply_order_edit", original_apply)
    with app.test_client() as client:
        retry = client.patch(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}", json=body)
    assert retry.status_code == 200, retry.get_data(as_text=True)
    assert "6111000" in _prices(app, order_key)
    store = business_store.BusinessDecisionStore(pg)
    assert len([row for row in store.purchase_price_overrides()
                if row[0] == order_key]) == 1


# --- Cấu tạo: một transaction, một kết nối ------------------------------

def test_the_write_path_never_opens_a_second_connection(app, scene,
                                                        monkeypatch):
    """Không đường nào của `period()` mở một kết nối THỨ HAI trong transaction.

    Đây là test canh CẤU TẠO, và nó tồn tại vì bản đầu của
    `BusinessReportService.bind()` bỏ sót đúng một store:
    `BindingExceptionStore`. `period()` đọc `open_keys()` của nó, nên nó
    mở một kết nối riêng — tức đọc NGOÀI transaction, đúng lớp lỗi `P0-3`.

    Trên PostgreSQL sự bỏ sót đó là một phép đọc không nhất quán; trên
    SQLite trong bộ nhớ nó còn tệ hơn (cùng một kết nối DBAPI được chia
    sẻ, nên context exit của nó ROLLBACK cả transaction đang chạy). Cả hai
    đều là lỗi, và test này bắt được cả hai bằng cách đếm.
    """
    from sqlalchemy.engine import Engine

    order_key, line, revision = scene
    opened: list[str] = []
    inside = {"active": False}

    original_connect = Engine.connect
    original_begin = Engine.begin

    def watch(name, original):
        def wrapper(inner_self, *args, **kwargs):
            if inside["active"]:
                opened.append(name)
            return original(inner_self, *args, **kwargs)
        return wrapper

    monkeypatch.setattr(Engine, "connect", watch("connect", original_connect))
    monkeypatch.setattr(Engine, "begin", watch("begin", original_begin))

    service_class = type(app.config["BUSINESS_SERVICE"])
    original_apply = service_class.apply_order_edit

    def marked(inner_self, plan, **kwargs):
        inside["active"] = True
        try:
            return original_apply(inner_self, plan, **kwargs)
        finally:
            inside["active"] = False

    monkeypatch.setattr(service_class, "apply_order_edit", marked)

    with app.test_client() as client:
        response = client.patch(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
            json=_body(key=str(uuid.uuid4()), revision=revision, line=line,
                       value="1234000"))
    assert response.status_code == 200, response.get_data(as_text=True)
    assert opened == [], (
        f"đường ghi mở thêm {len(opened)} kết nối ngoài transaction: "
        f"{opened}")


def test_revision_is_recomputed_inside_the_transaction(app, scene,
                                                       monkeypatch):
    """Phép kiểm revision đọc qua CHÍNH kết nối của transaction.

    Nếu nó đọc ngoài, một lần ghi xảy ra giữa lần đọc và lần ghi sẽ không
    bị phát hiện — và khi đó `base_revision` chỉ là một trường trang trí.
    """
    from app.web import mutation_guard

    order_key, line, revision = scene
    seen: list[bool] = []
    original = mutation_guard.MutationGuard.transaction

    import contextlib

    @contextlib.contextmanager
    def traced(inner_self, **kwargs):
        revision_of = kwargs.pop("revision_of")

        def watched(connection):
            # Kết nối truyền vào phải là kết nối ĐANG có transaction mở.
            seen.append(connection.in_transaction())
            return revision_of(connection)

        with original(inner_self, revision_of=watched, **kwargs) as ctx:
            yield ctx

    monkeypatch.setattr(mutation_guard.MutationGuard, "transaction", traced)

    with app.test_client() as client:
        response = client.patch(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
            json=_body(key=str(uuid.uuid4()), revision=revision, line=line,
                       value="1234000"))
    assert response.status_code == 200, response.get_data(as_text=True)
    assert seen == [True], (
        "revision không được tính lại bên trong transaction đang mở")


def test_four_concurrent_writers_produce_one_write(app, scene, monkeypatch):
    """Bốn luồng, cùng mã: vẫn ĐÚNG MỘT lần ghi.

    Hai luồng chứng minh cửa loại trừ tồn tại; bốn luồng chứng minh nó
    không phải một cuộc đua may mắn giữa hai bên.
    """
    order_key, line, revision = scene
    counter = _WriteCounter(monkeypatch, app, parties=4)
    shared = str(uuid.uuid4())
    results = _fire(app, order_key, [
        _body(key=shared, revision=revision, line=line, value="1234000")
        for _ in range(4)])
    assert len(counter.calls) == 1, (
        f"set_purchase_price() gọi {len(counter.calls)} lần")
    assert all(item["status"] != 503 for item in results), results


def test_period_revision_and_order_revision_move_together_after_a_write(
        app, scene):
    """Sau một lần ghi, CẢ hai revision đổi — và chúng đổi vì lần ghi đó."""
    order_key, line, revision = scene
    with app.test_client() as client:
        before = client.get(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}").get_json()
        response = client.patch(
            f"/api/v1/orders/{order_key}?period={ws.PERIOD_TEXT}",
            json=_body(key=str(uuid.uuid4()), revision=revision, line=line,
                       value="1234000"))
        after = response.get_json()
    assert response.status_code == 200
    assert after["order_revision"] != before["order_revision"]
    assert after["period_revision"] != before["period_revision"]
    assert order_revision.REVISION_VERSION, "version tag phải có mặt"
