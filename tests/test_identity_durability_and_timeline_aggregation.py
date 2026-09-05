"""Bản sửa chặn: nhận diện sản phẩm BỀN + dòng thời gian gộp đúng.

Năm khiếm khuyết được nghiệm thu ở đây, và mỗi phần dưới đây trả lời đúng
một câu hỏi nghiệp vụ chứ không phải một câu hỏi kỹ thuật:

    F-A  hai worker gunicorn cùng đọc một log — worker B có thấy ngay quyết
         định mà worker A vừa ghi không?
    F-B  container bị dựng lại (deploy) — quyết định đã xác nhận còn không?
    F-C  Quý 3 gồm hai tháng sổ cũ và một tháng sổ nạp — nó bằng bao nhiêu?
    F-D  các bất biến gộp liên-origin ở mức QUÝ/NĂM có được kiểm không?
    F-E  ô chỉ tiêu nói về KỲ ĐANG CHỌN còn biểu đồ nói về toàn bộ dòng thời
         gian — màn hình có nói ra sự khác nhau đó không?

Và một ranh giới KHÔNG được nới ra khi sửa cả năm: `PHB-01` — Tracking vẫn
là thẩm quyền Product Identity; Reports không có thẩm quyền thứ hai.

## Vì sao "hai worker" ở đây là hai `app`/`store` thật, không phải hai luồng

Khiếm khuyết `F-A` không phải một cuộc đua giữa hai luồng: nó là chuyện hai
TIẾN TRÌNH mỗi bên giữ một ảnh chụp riêng của cùng một log. Mô phỏng đúng
hình dạng đó cần hai instance độc lập trên CÙNG một nơi lưu — nên mỗi worker
ở đây có `JsonlProductIdentityStore` riêng, `Flask app` riêng, và cả hai trỏ
vào một `FakeR2Client` duy nhất đóng vai bucket dùng chung.

Bucket là fake, và điều đó KHÔNG làm loãng bằng chứng: cái đang được chứng
minh là "quyết định nằm ở nơi lưu dùng chung chứ không nằm trong RAM của một
tiến trình", và một backing store in-memory dùng chung chứng minh đúng mệnh
đề đó. Độ bền vật lý của chính R2 là chuyện của Cloudflare, không phải của
bộ test này.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.product.identity.journal import JournalWriteConflict
from app.modules.product.identity.mapping import (
    MappingSource, MappingStatus, SOURCE_SYSTEM_REPORTS_SALES,
)
from app.modules.product.identity.store import JsonlProductIdentityStore
from app.web import (
    business_presentation, history_store, identity_gateway, identity_journal,
    line_identity, revenue_timeline as rt,
)
from app.web import server as web_server
from tests.fixtures.fake_r2_client import FakeR2Client
from tools.storage import r2_store
from tests.support import identity_fixtures as fx
from tests.test_dec185_nav_chart_identity import (
    UNRESOLVED, chart_bars, seed_legacy, seed_legacy_month_total_only,
)
from tests.test_employee_workspace_ux import TODAY, body, line, metric, metrics, persist
from tools.tracking import live_pull

SEPTEMBER = {"date_from": date(2026, 9, 1), "date_to": date(2026, 9, 30)}

#: Đủ bốn biến để `r2_store.is_configured()` trả `True`. Không credential
#: thật nào ở đây — client luôn được tiêm qua `client=`.
R2_ENV = {
    "R2_ACCOUNT_ID": "acc-test", "R2_BUCKET": "bucket-test",
    "R2_ACCESS_KEY_ID": "key-test", "R2_SECRET_ACCESS_KEY": "secret-test",
}


# ==========================================================================
# Dựng "hai worker" trên MỘT bucket dùng chung
# ==========================================================================

@pytest.fixture
def bucket():
    """Nơi lưu BỀN dùng chung — đóng vai R2 của production."""
    return FakeR2Client()


def worker_store(bucket) -> JsonlProductIdentityStore:
    """Store của MỘT worker: bộ nhớ riêng, nơi lưu chung."""
    return JsonlProductIdentityStore(
        journal=identity_journal.ObjectStoreIdentityJournal(
            client=bucket, env=R2_ENV))


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def service(engine):
    from app.web import business_service, business_store
    return business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))


@pytest.fixture
def snapshot():
    return fx.tracking_snapshot((
        ("EWF1143R7SC", "Máy giặt Electrolux EWF1143R7SC", (), True),
        ("43F6000", "Tivi TCL 43F6000", (), True),
    ))


@pytest.fixture
def worker(engine, monkeypatch, tmp_path, bucket, snapshot):
    """Nhà máy dựng một worker độc lập trên cùng engine + cùng bucket.

    Trả về `(client, store)` để test vừa hỏi được qua HTML (thứ Owner thật
    sự nhìn thấy) vừa hỏi được thẳng store khi cần một khẳng định về state.
    """
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
    monkeypatch.setattr(
        web_server, "load_tracking_catalog_capture", lambda path: snapshot)

    from app.owner_usability import SelectedCaptures
    captures = SelectedCaptures(
        tracking_capture=tmp_path / "history.json",
        tracking_catalog=tmp_path / "catalog.json",
        tracking_inv_map=tmp_path / "inv_map.json")
    monkeypatch.setattr(
        web_server, "_select_captures_for_run", lambda: (captures, None, None))

    created = []

    def build(name: str):
        store = worker_store(bucket)
        monkeypatch.setattr(identity_gateway, "build_store", lambda: store)
        application = web_server.create_app(
            db_path=tmp_path / f"runs-{name}.db",
            history=history_store.LegacyRepository(engine),
            snapshots=history_store.SnapshotRepository(engine))
        application.testing = True
        created.append(store)
        return application.test_client(), store

    return build


def unresolved_line(order="BH73877", product="Máy giặt Electrolux EWF1143R7SC"):
    return line(order, product, day=5, kpi_purchase=None, kpi_profit=None,
                status="PENDING", reasons=UNRESOLVED)


def confirm_through(client, service, *, code="EWF1143R7SC", order="BH73877"):
    """Owner phân loại một dòng, đi qua ĐÚNG route production."""
    detail = next(item for item in service.period(**SEPTEMBER).details
                  if item["order_key"] == order)
    response = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
        "ky": "2026-09", "order_key": order,
        "product_key": detail["product_key"],
        "occurrence_index": str(detail["occurrence_index"]),
        "ma_tracking": code})
    assert response.status_code == 302, response.status_code
    return response


def labels_of(client) -> list[str]:
    return metrics(body(client, "/kinh-doanh/nhan-vien?ky=2026-09"),
                   "identity-label")


# ==========================================================================
# F-A — hai worker, một sự thật
# ==========================================================================

def test_f_a_worker_b_sees_the_mapping_worker_a_just_confirmed(
    repository, service, worker
):
    """Vector nghiệm thu `§5`, chạy qua HTML thật của cả hai worker.

    Trước bản sửa, worker B chiếu một ảnh chụp trong bộ nhớ của CHÍNH nó và
    vì thế vẫn nói "Chưa phân loại" cho tới lần khởi động lại kế tiếp — một
    câu sai đắt tiền: nó đẩy Owner đi phân loại lại một thứ đã phân loại rồi.
    """
    persist(repository, [unresolved_line()])
    client_a, store_a = worker("a")
    client_b, store_b = worker("b")

    # Ban đầu: CẢ HAI worker cùng nói chưa phân loại.
    assert labels_of(client_a) == [line_identity.LABEL_UNRESOLVED]
    assert labels_of(client_b) == [line_identity.LABEL_UNRESOLVED]

    confirm_through(client_a, service)

    # Worker B, NGAY request kế tiếp, không khởi động lại, không refresh tay.
    labels = labels_of(client_b)
    assert line_identity.LABEL_UNRESOLVED not in labels, (
        "worker B vẫn nói 'Chưa phân loại' cho một mặt hàng worker A đã xác "
        "nhận — F-A chưa được sửa")
    assert labels == [line_identity.LABEL_MISSING_PRICE], (
        "đã nhận diện nhưng chưa có giá nhập ⟹ 'Thiếu giá' (ECONOMIC_ISOLATION)")

    # Và state của chính store worker B đọc lại được từ nơi lưu chung.
    view = store_b.read_at_revision(store_b.refresh())
    mappings = list(view.alias_index().values())
    assert len(mappings) == 1
    assert mappings[0].status is MappingStatus.CONFIRMED
    assert mappings[0].source_product_code == "EWF1143R7SC"


def test_f_a_worker_b_can_still_write_without_a_phantom_version_conflict(
    repository, service, worker
):
    """`§5` — worker B KHÔNG được nhận 'expected_version=0 / hiện tại=1'.

    Đây là mặt kia của cùng khiếm khuyết: một `expected_version` tính từ ảnh
    chụp cũ va vào `INV-59` và từ chối một thao tác hoàn toàn hợp lệ. Xung
    đột do bộ nhớ cục bộ bịa ra không phải xung đột.
    """
    persist(repository, [unresolved_line("BH1"),
                         unresolved_line("BH2", "Tivi TCL 43F6000")])
    client_a, _ = worker("a")
    client_b, store_b = worker("b")
    body(client_b, "/kinh-doanh/nhan-vien?ky=2026-09")  # B nạp ảnh chụp version 0

    confirm_through(client_a, service, order="BH1")
    response = confirm_through(client_b, service, code="43F6000", order="BH2")

    assert "loi=" not in response.headers["Location"], response.headers["Location"]
    html = body(client_b, "/kinh-doanh/nhan-vien?ky=2026-09")
    for forbidden in ("expected_version", "version hiện tại"):
        assert forbidden not in html, (
            f"{forbidden!r} lọt ra màn hình cho một thao tác hợp lệ")
    assert store_b.refresh() == 2, "cả hai xác nhận đều nằm trong log dùng chung"
    assert labels_of(client_b) == [line_identity.LABEL_MISSING_PRICE] * 2


def test_f_a_no_worker_keeps_a_permanently_stale_projection(bucket):
    """`§4` — không worker nào được giữ mãi một ảnh chiếu cũ.

    Kiểm ở mức store, không qua HTML: `refresh()` phải là thứ trả lời, và nó
    phải trả lời ĐÚNG sau mỗi lần bên kia ghi, không chỉ lần đầu.
    """
    a, b = worker_store(bucket), worker_store(bucket)
    assert a.refresh() == 0 and b.refresh() == 0

    a.append(_confirm(a, "TRK-1", "Máy sấy tổng hợp A", "req-1"))
    assert b.refresh() == 1

    b.append(_confirm(b, "TRK-2", "Máy sấy tổng hợp B", "req-2"))
    assert a.refresh() == 2

    a.append(_confirm(a, "TRK-3", "Máy sấy tổng hợp C", "req-3"))
    assert b.refresh() == 3, "worker B đóng băng ở một revision cũ"


def _confirm(store, code: str, product_raw: str, request_id: str):
    """`ConfirmMapping` dựng qua đúng cổng production của tầng web."""
    from app.modules.product.identity.audit import AffectedScope
    from app.modules.product.identity.commands import ConfirmMapping
    from app.modules.product.identity.evidence import (
        Evidence, MatchedOn, ResolutionMethod)
    from app.modules.product.identity.identity import (
        CanonicalProductIdentity, Namespace)
    from app.modules.product.identity.keys import raw_identity_key

    revision = store.refresh()
    current = store.read_at_revision(revision).active_mapping(
        SOURCE_SYSTEM_REPORTS_SALES, raw_identity_key(product_raw))
    return ConfirmMapping(
        actor_id="owner-web", client_request_id=request_id,
        expected_version=current.version if current is not None else 0,
        tracking_capture_id=fx.CAPTURE_A,
        affected_scope=AffectedScope(
            distinct_identity_count=1, affected_order_ids=(),
            affected_line_count=1, computed_at_revision=revision),
        raw_identity_key=raw_identity_key(product_raw),
        raw_product_identity=product_raw,
        source_system=SOURCE_SYSTEM_REPORTS_SALES,
        target=CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code=code),
        evidence=Evidence(
            matched_on=MatchedOn.MANUAL_SEARCH, matched_value=code,
            candidate_set_ids=(f"TRACKING:{code}",)),
        resolution_method=ResolutionMethod.SIMILARITY_RANKED)


def test_two_writers_racing_for_one_slot_do_not_both_win(bucket):
    """Loại trừ giữa hai người viết KHÔNG có khoá file chung.

    Cả hai tính vị trí kế tiếp là 1; đúng một người ghi được. Người thua
    nhận `JournalWriteConflict` — cùng ngữ nghĩa `INV-59`/`INV-60` — và
    quan trọng nhất: state trong bộ nhớ của họ KHÔNG được nhích lên một bậc
    mà log dùng chung không biết.
    """
    a, b = worker_store(bucket), worker_store(bucket)
    command_a = _confirm(a, "TRK-1", "Máy sấy tổng hợp A", "req-a")
    command_b = _confirm(b, "TRK-2", "Máy sấy tổng hợp B", "req-b")

    a.append(command_a)
    with pytest.raises(JournalWriteConflict):
        b._journal.append({"probe": True})  # B vẫn tin vị trí 1 còn trống

    # Sau khi hoàn lại, B nạp lại và ghi được ở vị trí kế tiếp thật.
    assert b.refresh() == 1
    b.append(_confirm(b, "TRK-2", "Máy sấy tổng hợp B", "req-b2"))
    assert a.refresh() == 2


def test_a_failed_write_leaves_no_event_visible_only_in_memory(bucket):
    """Ghi hỏng ⟹ store KHÔNG được tự nâng version của mình.

    Một event chỉ có trong RAM làm mọi phép kiểm `INV-59` sau đó của chính
    worker này tính trên một sự thật không tồn tại ở đâu cả.
    """
    a = worker_store(bucket)
    command = _confirm(a, "TRK-1", "Máy sấy tổng hợp A", "req-a")
    bucket.fail["put_object"] = RuntimeError("R2 sập")

    with pytest.raises(Exception):
        a.append(command)
    assert a.current_revision() == 0
    assert a.refresh() == 0

    bucket.fail.clear()
    a.append(_confirm(a, "TRK-1", "Máy sấy tổng hợp A", "req-a2"))
    assert a.refresh() == 1


# ==========================================================================
# F-B — sống qua restart / redeploy
# ==========================================================================

def test_f_b_a_confirmation_survives_the_store_being_destroyed_and_rebuilt(bucket):
    """`§6` — huỷ instance, dựng instance mới, mapping vẫn còn."""
    first = worker_store(bucket)
    first.append(_confirm(first, "TRK-1", "Máy sấy tổng hợp A", "req-1"))
    key = first.read_at_revision(1).alias_index()
    assert len(key) == 1

    del first  # container cũ biến mất

    second = worker_store(bucket)
    view = second.read_at_revision(second.refresh())
    mappings = list(view.alias_index().values())
    assert len(mappings) == 1, "mapping biến mất khi dựng lại instance — F-B"
    assert mappings[0].status is MappingStatus.CONFIRMED
    assert mappings[0].mapping_source is MappingSource.HUMAN_CONFIRMATION


def test_f_b_the_whole_app_survives_a_redeploy(repository, service, worker):
    """`§6` qua HTML: phân loại → container mới → vẫn 'Thiếu giá'."""
    persist(repository, [unresolved_line()])
    client_before, _ = worker("truoc-deploy")
    confirm_through(client_before, service)
    assert labels_of(client_before) == [line_identity.LABEL_MISSING_PRICE]

    # Deploy: tiến trình mới, bộ nhớ mới, filesystem container mới.
    client_after, _ = worker("sau-deploy")
    assert labels_of(client_after) == [line_identity.LABEL_MISSING_PRICE], (
        "quyết định phân loại biến mất sau redeploy — F-B chưa được sửa")


def test_f_b_nothing_is_written_to_the_ephemeral_jsonl_when_r2_is_configured(
    bucket, tmp_path, monkeypatch
):
    """Nơi lưu bền phải THAY nơi lưu ephemeral, không chạy song song.

    Hai nơi lưu cho một store là đúng thứ `D-06` cấm — và trong thực tế nó
    còn tệ hơn một chỗ lưu sai: hai nửa sự thật, mỗi nửa đúng một lúc.
    """
    monkeypatch.chdir(tmp_path)
    # Tiêm ở ĐÚNG một chỗ: nơi `r2_store` dựng client boto3. Nhờ vậy
    # `build_store()` chạy nguyên vẹn đường sản xuất — kể cả phép chọn nhánh
    # mà test này đang nghiệm thu — thay vì bị thay bằng một store dựng sẵn.
    monkeypatch.setattr(r2_store, "_client", lambda env=None: bucket)
    store = identity_gateway.build_store(env=R2_ENV)
    store.append(_confirm(store, "TRK-1", "Máy sấy tổng hợp A", "req-1"))

    assert store.log_path is None and store.index_path is None
    assert not (tmp_path / "data").exists(), (
        "quyết định vẫn rơi xuống đĩa container dù đã có nơi lưu bền")
    assert any(key.startswith(identity_journal.EVENT_KEY_PREFIX)
               for key in bucket.objects)


def test_the_local_file_store_is_unchanged_when_r2_is_not_configured(tmp_path):
    """Máy Owner: đĩa thật, một tiến trình — nhánh cũ không đổi hành vi."""
    store = identity_gateway.build_store(
        log_path=tmp_path / "log.jsonl", index_path=tmp_path / "index.json",
        env={})
    store.append(_confirm(store, "TRK-1", "Máy sấy tổng hợp A", "req-1"))
    assert (tmp_path / "log.jsonl").exists()
    assert JsonlProductIdentityStore(
        log_path=tmp_path / "log.jsonl").current_revision() == 1


def test_production_refuses_to_fall_back_to_an_ephemeral_log(tmp_path, monkeypatch):
    """Fail closed: `REPORTS_REQUIRE_R2` bật mà R2 thiếu ⟹ LỖI, không im lặng.

    Rơi về file cục bộ ở đây là rơi về đúng `F-B`, chỉ lặng lẽ hơn: màn hình
    sẽ nhận xác nhận, và mọi xác nhận biến mất ở lần deploy kế tiếp.
    """
    monkeypatch.chdir(tmp_path)
    with pytest.raises(identity_gateway.DurableStoreUnavailableError):
        identity_gateway.build_store(env={"REPORTS_REQUIRE_R2": "1"})
    assert not (tmp_path / "data").exists()


# ==========================================================================
# Ranh giới `PHB-01` — Tracking vẫn là thẩm quyền Product Identity
# ==========================================================================

def test_the_durable_store_is_the_same_authority_not_a_second_one(bucket):
    """Đổi NƠI LƯU không được đổi bản chất bản ghi.

    Cùng `source_system`, cùng `mapping_source`, cùng một `store.append()`,
    cùng cổng `INV-01`. Nếu một trong bốn thứ đó đổi, Reports vừa mọc ra một
    thẩm quyền identity thứ hai — đúng thứ `PHB-01` cấm.
    """
    store = worker_store(bucket)
    store.append(_confirm(store, "TRK-1", "Máy sấy tổng hợp A", "req-1"))
    mapping = next(iter(store.read_at_revision(1).alias_index().values()))
    assert mapping.source_system == SOURCE_SYSTEM_REPORTS_SALES
    assert mapping.mapping_source is MappingSource.HUMAN_CONFIRMATION
    assert mapping.namespace.value == "TRACKING"


def test_the_durable_path_writes_nothing_but_the_decision_log(bucket):
    """Bucket dùng chung chỉ được mọc thêm event, không mọc thêm bảng.

    Một "bảng ánh xạ sản phẩm" do Reports tự dựng cạnh log — kể cả dưới
    dạng một object index — CHÍNH LÀ thẩm quyền thứ hai.
    """
    store = worker_store(bucket)
    store.append(_confirm(store, "TRK-1", "Máy sấy tổng hợp A", "req-1"))
    store.append(_confirm(store, "TRK-2", "Máy sấy tổng hợp B", "req-2"))
    assert sorted(bucket.objects) == [
        identity_journal.event_key(1), identity_journal.event_key(2)]


def test_no_inv_map_write_path_appeared_in_the_new_modules():
    """`PI-06` mở rộng cho nơi lưu mới — phủ định trên chính mã nguồn."""
    import pathlib
    forbidden = re.compile(
        r"inv_map\w*\s*\[|write_inv_map|put_inv_map|set_inv_map", re.IGNORECASE)
    for name in ("app/web/identity_journal.py",
                 "app/modules/product/identity/journal.py"):
        text = pathlib.Path(name).read_text(encoding="utf-8")
        assert not forbidden.search(text), name


def test_the_missing_price_state_is_never_confused_with_unresolved_identity(
    repository, service, worker
):
    """`§8` — hai trạng thái vẫn KHÁC nhau sau khi đổi nơi lưu.

    Cám dỗ cũ không mất đi khi nơi lưu đổi: cả hai trạng thái đều để trống ô
    giá nhập. Gộp chúng lại sẽ đẩy Owner đi phân loại lại một thứ đã phân
    loại rồi, và việc đó không bao giờ làm giá nhập xuất hiện.
    """
    persist(repository, [unresolved_line()])
    client, _ = worker("a")
    assert labels_of(client) == [line_identity.LABEL_UNRESOLVED]
    confirm_through(client, service)
    assert labels_of(client) == [line_identity.LABEL_MISSING_PRICE]


# ==========================================================================
# F-C · F-D — QUÝ/NĂM gộp các THÁNG đã giải thẩm quyền
#
# Ví dụ của Owner, nguyên văn:
#     2026-07 Legacy = 50tr · 2026-08 Legacy = 60tr · 2026-09 Current = 1tr
#     ⟹ Q3/2026 = 111tr
# ==========================================================================

def revenue_line(month: int, day: int, vnd: str, order: str):
    return line(order, "43F6000", day=day, month=month, sell=vnd,
                kpi_purchase="0", kpi_profit="0")


@pytest.fixture
def owner_case(engine, repository):
    """Đúng ba tháng của ví dụ, dựng qua đường persist/legacy thật."""
    persist(repository, [revenue_line(9, 5, "1000000", "BH-T9")])
    seed_legacy(engine, [(7, 10, 50000000), (8, 10, 60000000)],
                import_id="imp-2026", year=2026)


def test_t01_the_quarter_is_the_sum_of_its_resolved_months(owner_case, worker):
    """`T-01` — Q3 = 50 + 60 + 1 = 111tr. Sửa `F-C`.

    Trước bản sửa, Q3 = 1tr: tháng 9 có sổ nạp nên nó chiếm CẢ khoá quý, và
    110 triệu của hai tháng chỉ có sổ cũ biến mất không dấu vết.
    """
    client, _ = worker("a")
    months = chart_bars(body(client, "/kinh-doanh?muc=thang"))
    assert months["2026-07"] == Decimal("50000000")
    assert months["2026-08"] == Decimal("60000000")
    assert months["2026-09"] == Decimal("1000000")

    quarters = chart_bars(body(client, "/kinh-doanh?muc=quy"))
    assert quarters["2026-Q3"] == Decimal("111000000")


def test_t01_the_year_aggregates_the_same_resolved_months(owner_case, worker):
    """`T-01` — năm gộp đúng các tháng đã giải, không chọn lại nguồn."""
    client, _ = worker("a")
    months = chart_bars(body(client, "/kinh-doanh?muc=thang"))
    years = chart_bars(body(client, "/kinh-doanh?muc=nam"))
    assert years["2026"] == sum(months.values())
    assert years["2026"] >= Decimal("111000000")


def test_t02_the_same_month_never_adds_two_origins(engine, repository, worker):
    """`T-02` — cùng một tháng có cả hai nguồn ⟹ CHỈ số mới, không phải tổng.

    Đây là phép cộng liên-origin THẬT SỰ bị cấm, và nó vẫn bị cấm sau `F-C`.
    """
    persist(repository, [revenue_line(7, 5, "1000000", "BH-T7")])
    seed_legacy(engine, [(7, 10, 50000000)], import_id="imp-2026", year=2026)

    client, _ = worker("a")
    months = chart_bars(body(client, "/kinh-doanh?muc=thang"))
    assert months["2026-07"] == Decimal("1000000"), "không được thành 51tr"
    quarters = chart_bars(body(client, "/kinh-doanh?muc=quy"))
    assert quarters["2026-Q3"] == Decimal("1000000")


def test_t03_a_quarter_mixing_legacy_only_current_only_and_overlap_months(
    engine, repository, worker
):
    """`T-03` — quý gồm một tháng sổ cũ, một tháng sổ nạp, một tháng chồng.

    Kết quả đúng là tổng các GIÁ TRỊ ĐÃ GIẢI: 50 (chỉ sổ cũ) + 2 (tháng
    chồng, số mới thắng) + 1 (chỉ sổ nạp).
    """
    persist(repository, [revenue_line(8, 5, "2000000", "BH-T8"),
                         revenue_line(9, 5, "1000000", "BH-T9")])
    seed_legacy(engine, [(7, 10, 50000000), (8, 10, 60000000)],
                import_id="imp-2026", year=2026)

    client, _ = worker("a")
    months = chart_bars(body(client, "/kinh-doanh?muc=thang"))
    assert months["2026-07"] == Decimal("50000000")
    assert months["2026-08"] == Decimal("2000000")
    assert months["2026-09"] == Decimal("1000000")
    quarters = chart_bars(body(client, "/kinh-doanh?muc=quy"))
    assert quarters["2026-Q3"] == Decimal("53000000")


def test_t04_legacy_never_wins_a_month_that_current_has(engine, repository, worker):
    """`T-04` — sổ cũ KHÔNG thắng, kể cả khi con số của nó lớn hơn nhiều."""
    persist(repository, [revenue_line(9, 5, "1000000", "BH-T9")])
    seed_legacy(engine, [(9, 10, 999000000)], import_id="imp-2026", year=2026)

    client, _ = worker("a")
    for gran, key in (("thang", "2026-09"), ("quy", "2026-Q3"), ("nam", "2026")):
        bars = chart_bars(body(client, f"/kinh-doanh?muc={gran}"))
        assert bars[key] == Decimal("1000000"), gran


def test_t05_adding_both_origins_into_one_month_is_refused_at_the_seam():
    """`T-05` — nếu thứ tự thẩm quyền hỏng, phép gộp DỪNG chứ không nhân đôi.

    Kiểm thẳng trên hàm gộp: nó là chỗ duy nhất hai origin có thể gặp nhau,
    nên nó phải là chỗ mệnh đề "một tháng một nguồn" được thi hành, không
    phải một quy ước mà người gọi tự nhớ.
    """
    buckets = {"2026-Q3": {"label": "Quý 3/2026", "revenue": Decimal("1000000"),
                           "months": {(2026, 7)}, "origin": rt.ORIGIN_CURRENT}}
    intruder = {"label": "Quý 3/2026", "revenue": Decimal("50000000"),
                "months": {(2026, 7)}, "origin": rt.ORIGIN_LEGACY}
    with pytest.raises(ValueError, match="hai origin"):
        rt._merge_resolved(buckets, "2026-Q3", intruder)


def test_t06_a_coarse_bar_never_resolves_authority_for_the_whole_quarter(
    owner_case, worker
):
    """`T-06` — chọn MỘT nguồn cho cả quý là chính khiếm khuyết `F-C`.

    Test này bắt đúng mutation đó: nếu quý lại giải thẩm quyền cho cả cột,
    Q3 rơi về 1tr (chỉ Current) hoặc 110tr (chỉ Legacy) — cả hai đều đỏ ở
    đây, và tổng năm cũng đỏ theo.
    """
    client, _ = worker("a")
    quarters = chart_bars(body(client, "/kinh-doanh?muc=quy"))
    assert quarters["2026-Q3"] not in (Decimal("1000000"), Decimal("110000000"))
    assert quarters["2026-Q3"] == Decimal("111000000")
    assert sum(quarters.values()) == sum(
        chart_bars(body(client, "/kinh-doanh?muc=thang")).values()), (
        "gộp thô hơn KHÔNG được làm đổi tổng")


def test_every_granularity_still_sums_to_the_same_total_with_legacy_months(
    owner_case, worker
):
    """Bất biến `CHART-05`…`CHART-08` mở rộng sang dòng thời gian có sổ cũ.

    Trước bản sửa, bất biến này chỉ đúng khi KHÔNG có sổ cũ — và im lặng sai
    đúng ở tình huống mà Owner thật sự đang dùng.
    """
    client, _ = worker("a")
    totals = {gran: sum(chart_bars(body(client, f"/kinh-doanh?muc={gran}")).values())
              for gran in ("thang", "quy", "nam")}
    assert len(set(totals.values())) == 1, totals
    assert totals["thang"] == Decimal("111000000")


# ==========================================================================
# §11 — provenance của mốc trộn: nói ra, KHÔNG thêm điều khiển
# ==========================================================================

def test_a_mixed_quarter_declares_its_provenance_without_a_source_control(
    owner_case, worker
):
    """`§11` — `MIXED_AUTHORITY` chỉ để đọc, và giá trị KHÔNG bị tách đôi."""
    client, _ = worker("a")
    html = body(client, "/kinh-doanh?muc=quy")
    origins = dict(re.findall(
        r'data-metric="chart-bar" data-key="([^"]+)"[^>]*data-origin="([^"]+)"',
        html))
    assert origins["2026-Q3"] == rt.ORIGIN_MIXED

    chart = re.search(r'id="bieu-do-doanh-thu".*?(?=<div class="module")',
                      html, re.S).group(0)
    for forbidden in ("Số cũ", "Số mới", "SỐ CŨ", "SỐ MỚI", "<select"):
        assert forbidden not in chart, f"{forbidden!r} là một điều khiển nguồn"
    # ĐÚNG MỘT cột cho quý đó — không có chuỗi thứ hai chạy song song.
    assert len(re.findall(r'data-key="2026-Q3"', chart)) == 1


def test_a_month_bucket_is_never_mixed(owner_case, worker):
    """Thẩm quyền giải ở mức tháng ⟹ mốc THÁNG luôn thuần một nguồn."""
    client, _ = worker("a")
    html = body(client, "/kinh-doanh?muc=thang")
    origins = dict(re.findall(
        r'data-metric="chart-bar" data-key="([^"]+)"[^>]*data-origin="([^"]+)"',
        html))
    assert rt.ORIGIN_MIXED not in origins.values()
    assert origins["2026-07"] == rt.ORIGIN_LEGACY
    assert origins["2026-09"] == rt.ORIGIN_CURRENT


def test_the_mixed_bar_explains_itself_in_its_own_tooltip(owner_case, worker):
    """Chiều origin của `DEC-166 E` đọc được — trong lời của đúng cột đó."""
    client, _ = worker("a")
    html = body(client, "/kinh-doanh?muc=quy")
    title = re.search(r'title="([^"]*)"[^>]*data-key="2026-Q3"', html)
    assert title is not None, "cột quý phải có lời giải thích"
    assert "MỘT nguồn" in title.group(1)


# ==========================================================================
# §13 — độ mịn Ngày/Tuần: không bịa dữ liệu không có
# ==========================================================================

def test_a_monthly_only_legacy_total_still_invents_no_days_or_weeks(
    engine, repository, worker
):
    """`§13` — bằng chứng dừng ở mức THÁNG thì Ngày/Tuần không có điểm nào."""
    persist(repository, [revenue_line(9, 5, "1000000", "BH-T9")])
    seed_legacy_month_total_only(engine, year=2026, month=7, vnd=50000000)

    client, _ = worker("a")
    for gran in ("ngay", "tuan"):
        bars = chart_bars(body(client, f"/kinh-doanh?muc={gran}"))
        assert not any(key.startswith("2026-07") for key in bars), gran
    # Nhưng ở mức tháng trở lên nó vẫn góp đúng phần của mình.
    assert chart_bars(body(client, "/kinh-doanh?muc=quy"))["2026-Q3"] == \
        Decimal("51000000")


def test_daily_legacy_evidence_joins_the_same_week_without_touching_its_month():
    """Tuần vắt qua hai tháng đã giải về hai nguồn vẫn là MỘT tuần.

    Kiểm trên giá trị thuần: tháng 8 chỉ có sổ cũ, tháng 9 chỉ có sổ nạp,
    và tuần 31/08–06/09 gồm cả hai. Cộng ở đây không phải cộng liên-origin
    trong một tháng — nó là hai ngày khác nhau của hai tháng khác nhau.
    """
    class L:
        total_sales = Decimal("1000000")
        pending_reasons = ()
        purchase_price = Decimal("1")

    points = rt.series(
        [{"sale_date": date(2026, 9, 1), "line": L()}],
        granularity=rt.WEEK,
        legacy_days=[{"year": 2026, "month": 8, "day": 31,
                      "sales_vnd": Decimal("2000000")}])
    assert len(points) == 1
    assert points[0].revenue == Decimal("3000000")
    assert points[0].origin == rt.ORIGIN_MIXED


# ==========================================================================
# F-E — phạm vi của biểu đồ nói thành lời
# ==========================================================================

def test_f_e_the_chart_says_it_is_not_limited_to_the_selected_period(
    engine, repository, worker
):
    """`§14` — ô chỉ tiêu là KỲ ĐANG CHỌN, biểu đồ là toàn bộ dữ liệu.

    Không sửa phạm vi (đó là một quyết định đã có), chỉ sửa chỗ mập mờ: hai
    con số khác nhau đứng cạnh nhau mà không ai nói ra sẽ đọc thành hai con
    số mâu thuẫn.
    """
    persist(repository, [revenue_line(9, 5, "1000000", "BH-T9")])
    seed_legacy(engine, [(7, 10, 50000000)], import_id="imp-2026", year=2026)

    client, _ = worker("a")
    html = body(client, "/kinh-doanh?ky=2026-09&muc=thang")

    scope = metric(html, "chart-scope")
    assert "TOÀN BỘ" in scope and "Kỳ dữ liệu" in scope

    # Và sự khác nhau là THẬT trên chính trang này: ô chỉ tiêu chỉ có tháng 9,
    # biểu đồ có cả tháng 7 — nên câu giải thích không phải một câu thừa.
    bars = chart_bars(html)
    assert set(bars) == {"2026-07", "2026-09"}
    assert Decimal(metric(html, "sales_revenue").replace(".", "")) < \
        Decimal("50000000") / 1000 + 1


def test_the_chart_scope_note_sits_inside_the_chart_module(repository, worker):
    """Câu giải thích phải ở CẠNH biểu đồ, không ở một trang khác."""
    persist(repository, [revenue_line(9, 5, "1000000", "BH-T9")])
    client, _ = worker("a")
    html = body(client, "/kinh-doanh")
    chart = re.search(r'id="bieu-do-doanh-thu".*?(?=<div class="module")',
                      html, re.S).group(0)
    assert 'data-metric="chart-scope"' in chart
    assert business_presentation.revenue_chart(
        [], granularity=rt.MONTH)["scope_note"] == rt.CHART_SCOPE_NOTE


def test_the_chart_stays_one_chart_with_no_new_page_or_filter(repository, worker):
    """`§14` — chỉ sửa chỗ mập mờ, KHÔNG thêm trang hay hệ thống lọc mới."""
    persist(repository, [revenue_line(9, 5, "1000000", "BH-T9")])
    client, _ = worker("a")
    html = body(client, "/kinh-doanh")
    assert html.count('data-metric="chart"') == 1
    nav = re.search(r'<nav class="ncc-tabs">(.*?)</nav>', html, re.S).group(1)
    assert len(re.findall(r"<a\b", nav)) == 3, "thanh tab chính vẫn ba mục"
