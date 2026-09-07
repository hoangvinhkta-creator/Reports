"""R2 — ba luồng của Owner, kiểm qua ỨNG DỤNG WEB THẬT.

`tests/test_r2_product_classification.py` kiểm ngữ nghĩa ở tầng domain. File
này hỏi câu còn lại, và nó là câu Owner thật sự hỏi:

    tôi bấm nút trên trang → con số trên trang có đổi đúng không, và nó có
    còn nguyên sau khi tôi mở lại không?

Ba luồng phản chiếu đúng ba ca nghiệm thu của §12 trong `R2 Execution Brief`
(Ca A chọn mã Tracking · Ca B ngoài bảng giá + giá tay · Ca C ưu tiên và hoàn
tác giá tay), cộng một bài canh mối nối `/run` — mối nối mà R2 tồn tại để sửa.

Toàn bộ dữ liệu là tổng hợp.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.reporting import business_metrics as bm
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.mapping import MappingSource
from app.modules.product.identity.resolver import (
    distinct_identities, recorded_conflict_opposing_code,
)
from app.web import (
    business_service, business_store, history_store, identity_gateway,
    line_identity,
)
from app.web import server as web_server
from tests.support import identity_fixtures as fx
from tests.test_employee_workspace_ux import (
    SEPTEMBER, TODAY, body, line, metrics, persist,
)
from tools.tracking import live_pull

RAW = "43F6000"


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
    return business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    """Ứng dụng thật, với log quyết định trên ĐĨA THẬT dưới `tmp_path`.

    Đĩa thật chứ không phải bộ nhớ, vì bài "mở lại vẫn còn" chỉ có nghĩa khi
    nơi lưu có thể quên.
    """
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


def keys_of(service, order_key, product):
    for detail in service.period(**SEPTEMBER).details:
        if detail["order_key"] == order_key and detail["product_raw"] == product:
            return {"order_key": detail["order_key"],
                    "product_key": detail["product_key"],
                    "occurrence_index": detail["occurrence_index"]}
    raise AssertionError(f"không tìm thấy dòng {order_key}/{product}")


def unpriced_order(order="BH72707"):
    """Một BH một dòng, CHƯA phân loại và CHƯA có giá — điểm xuất phát của R2."""
    return [line(order, RAW, day=5, sell="9000000", kpi_purchase=None,
                 kpi_profit=None,
                 reasons=("IDENTITY_UNRESOLVED", "Missing.PurchasePrice"))]


# --------------------------------------------------------------------------
# Ca B — ngoài bảng giá, rồi nhập giá tay
# --------------------------------------------------------------------------

class TestOutOfCatalogThroughTheWeb:
    def test_the_line_starts_unclassified(self, repository, client):
        persist(repository, unpriced_order())
        html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert line_identity.LABEL_UNRESOLVED in metrics(html, "identity-label")

    def test_marking_out_of_catalog_takes_effect_after_the_redirect(
        self, repository, service, client
    ):
        """`§4.5` — sau redirect/refresh màn hình phải hiện NGAY trạng thái mới,
        không chờ một lần nạp sổ khác."""
        persist(repository, unpriced_order())
        keys = keys_of(service, "BH72707", RAW)

        response = client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys})
        assert response.status_code == 302

        html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        labels = metrics(html, "identity-label")
        assert line_identity.LABEL_OUT_OF_CATALOG in labels
        assert line_identity.LABEL_UNRESOLVED not in labels
        # `§4.3` — dòng thôi nằm trong danh sách chưa phân loại, nên cảnh báo
        # đầu sheet biến mất thay vì tiếp tục gọi Owner đi phân loại lại.
        assert 'data-metric="identity-warning"' not in html

    def test_the_line_keeps_its_revenue_after_the_decision(
        self, repository, service, client
    ):
        persist(repository, unpriced_order())
        before = service.period(**SEPTEMBER).totals.sales_revenue
        client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
            "ky": "2026-09", "sheet": "noi-thanh",
            **keys_of(service, "BH72707", RAW)})
        after = service.period(**SEPTEMBER)

        assert after.totals.sales_revenue == before == Decimal("9000000")
        assert len(after.lines) == 1
        assert after.excluded == []
        # Chưa có giá tay ⟹ vẫn Pending. KHÔNG có giá 0 nào được dựng ra.
        assert after.lines[0].purchase_price is None
        assert after.lines[0].kpi_profit is None

    def test_entering_the_manual_price_produces_the_owner_checklist_number(
        self, repository, service, client
    ):
        """Ca B bước 4–5: bán 9.000.000, nhập 8.500.000, SL 1 ⟹ lãi 500.000."""
        persist(repository, unpriced_order())
        keys = keys_of(service, "BH72707", RAW)
        client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys})

        response = client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "8.500.000"})
        assert response.status_code == 302

        line_after = service.period(**SEPTEMBER).lines[0]
        assert line_after.purchase_price == Decimal("8500000")
        assert line_after.kpi_profit == Decimal("500000")
        assert line_after.purchase_provenance == bm.PROVENANCE_MANUAL

    def test_an_out_of_catalog_line_keeps_a_door_back_to_tracking(
        self, repository, service, client
    ):
        """`§4.3` — "Nối lại Tracking" phải BẤM ĐƯỢC.

        Một quyết định không có đường đảo ngược là đúng thứ mà §8 của Brief
        gọi là finding chặn ("mất audit cần thiết để sửa quyết định"). Bài này
        đi đúng đường người dùng đi: mở lại bảng chọn từ chính nhãn trên bảng
        kê, rồi xác nhận một mã có thật.
        """
        persist(repository, unpriced_order())
        keys = keys_of(service, "BH72707", RAW)
        client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys})

        html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        # Nhãn "Ngoài bảng giá" là một LIÊN KẾT, không phải một chữ chết.
        assert re.search(
            r'<a[^>]*data-metric="identity-label"[^>]*>\s*'
            + re.escape(line_identity.LABEL_OUT_OF_CATALOG),
            html), "nhãn Ngoài bảng giá phải mở lại được bảng chọn"

        # Và bảng chọn mở ra ở đúng chế độ "nối lại".
        panel = body(
            client,
            "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh&phan-loai=1"
            f"&order_key={keys['order_key']}"
            f"&product_key={keys['product_key']}"
            f"&occurrence_index={keys['occurrence_index']}")
        assert 'data-metric="identify-out-of-catalog"' in panel
        assert f'data-classification="{line_identity.CLASS_OUT_OF_CATALOG}"' in panel

    def test_the_decision_and_the_price_survive_a_fresh_application(
        self, engine, repository, service, client, tmp_path, monkeypatch
    ):
        """"Mở lại" ở đây là một `create_app` HOÀN TOÀN MỚI trên cùng nơi lưu —
        mô hình của restart/redeploy, không phải một lần `GET` thứ hai."""
        persist(repository, unpriced_order())
        keys = keys_of(service, "BH72707", RAW)
        client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys})
        client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "8.500.000"})

        fresh = web_server.create_app(
            db_path=tmp_path / "runs.db",
            history=history_store.LegacyRepository(engine),
            snapshots=history_store.SnapshotRepository(engine))
        fresh.testing = True
        html = body(fresh.test_client(),
                    "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")

        labels = metrics(html, "identity-label")
        assert line_identity.LABEL_UNRESOLVED not in labels
        assert service.period(**SEPTEMBER).lines[0].kpi_profit == Decimal("500000")


# --------------------------------------------------------------------------
# Ca C — ưu tiên và hoàn tác giá tay
# --------------------------------------------------------------------------

class TestManualPricePriorityThroughTheWeb:
    def _two_lines(self):
        """Hai BH, CÙNG mặt hàng, cùng giá tự động — fixture của "không lan"."""
        return [line("BH1", RAW, day=5), line("BH2", RAW, day=5)]

    def test_a_manual_price_beats_the_auto_price_and_survives_reload(
        self, repository, service, client
    ):
        persist(repository, self._two_lines())
        keys = keys_of(service, "BH1", RAW)
        before = service.period(**SEPTEMBER).lines[0]
        assert before.purchase_price == Decimal("5000000")

        client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "4.000.000", "ly_do": "Đối chiếu hoá đơn"})

        edited = [d for d in service.period(**SEPTEMBER).details
                  if d["order_key"] == "BH1"][0]["line"]
        assert edited.purchase_price == Decimal("4000000")
        assert edited.purchase_provenance == bm.PROVENANCE_MANUAL_OVERRIDE
        # Giá AUTO VẪN CÒN ĐÓ và vẫn thua — đó là toàn bộ nội dung của `§4.4`.
        assert edited.auto_purchase_price == Decimal("5000000")

    def test_a_manual_price_without_a_reason_is_refused_with_a_message(
        self, repository, service, client
    ):
        persist(repository, self._two_lines())
        response = client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh",
            **keys_of(service, "BH1", RAW), "gia_nhap": "4.000.000"})

        assert response.status_code == 302
        assert "loi=" in response.headers["Location"]
        assert service.store.purchase_price_overrides() == {}

    def test_the_other_line_of_the_same_product_is_untouched(
        self, repository, service, client
    ):
        persist(repository, self._two_lines())
        client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh",
            **keys_of(service, "BH1", RAW),
            "gia_nhap": "4.000.000", "ly_do": "Đối chiếu hoá đơn"})

        untouched = [d for d in service.period(**SEPTEMBER).details
                     if d["order_key"] == "BH2"][0]["line"]
        assert untouched.purchase_price == Decimal("5000000")
        assert untouched.purchase_provenance == bm.PROVENANCE_AUTO

    def test_removing_the_manual_price_returns_the_line_to_auto(
        self, repository, service, client
    ):
        persist(repository, self._two_lines())
        keys = keys_of(service, "BH1", RAW)
        client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "4.000.000", "ly_do": "Đối chiếu hoá đơn"})
        client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys, "hanh-dong": "go"})

        restored = [d for d in service.period(**SEPTEMBER).details
                    if d["order_key"] == "BH1"][0]["line"]
        assert restored.purchase_price == Decimal("5000000")
        assert restored.purchase_provenance == bm.PROVENANCE_AUTO


# --------------------------------------------------------------------------
# Gói 4 — hàng đợi xử lý
# --------------------------------------------------------------------------

class TestTheProcessingQueue:
    def test_each_queue_narrows_to_its_own_situation(
        self, repository, service, client
    ):
        persist(repository, unpriced_order("BH-CHUA-PL") + [
            line("BH-DA-KHOP", "XP352AE-DS", day=5, kpi_purchase=None,
                 kpi_profit=None)])

        def rows(mode):
            html = body(
                client,
                f"/kinh-doanh/gia-nhap?ky=2026-09&loc={mode}")
            return metrics(html, "line-product") or _products(html)

        # Dòng chưa phân loại nằm trong hàng đợi phân loại...
        assert any("43F6000" in text for text in rows("chua-phan-loai"))
        # ...và KHÔNG nằm trong hàng đợi "đã khớp, thiếu MIN".
        assert not any("43F6000" in text for text in rows("thieu-min"))
        # Dòng đã khớp nhưng thiếu giá thì ngược lại.
        assert any("XP352AE-DS" in text for text in rows("thieu-min"))
        assert not any("XP352AE-DS" in text for text in rows("chua-phan-loai"))

    def test_the_out_of_catalog_queue_appears_only_after_the_decision(
        self, repository, service, client
    ):
        persist(repository, unpriced_order())
        html = body(client,
                    "/kinh-doanh/gia-nhap?ky=2026-09&loc=ngoai-bang-thieu-gia")
        assert 'data-metric="no-rows"' in html

        client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
            "ky": "2026-09", "sheet": "noi-thanh",
            **keys_of(service, "BH72707", RAW)})

        html = body(client,
                    "/kinh-doanh/gia-nhap?ky=2026-09&loc=ngoai-bang-thieu-gia")
        assert 'data-metric="no-rows"' not in html
        assert line_identity.CLASS_OUT_OF_CATALOG in html

    def test_the_queue_empties_once_the_price_is_entered(
        self, repository, service, client
    ):
        persist(repository, unpriced_order())
        keys = keys_of(service, "BH72707", RAW)
        client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys})
        client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "gia_nhap": "8.500.000"})

        html = body(client,
                    "/kinh-doanh/gia-nhap?ky=2026-09&loc=ngoai-bang-thieu-gia")
        assert 'data-metric="no-rows"' in html


# --------------------------------------------------------------------------
# Mối nối `/run` — R2 Gói 1
# --------------------------------------------------------------------------

class TestTheRunRouteUsesTheDurableStore:
    """Bằng chứng CẤU TRÚC cho mối nối mà R2 sửa.

    Trước R2, `/run` không truyền một ảnh chụp log nào xuống, và cả `live_pull`
    lẫn `demo.run_demo` tự mở một store trên `data/product_identity/` — đĩa
    ephemeral của container, trong khi log thật của bản Web nằm ở R2. Bài kiểm
    này canh đúng chỗ đó: nếu ai đó gỡ tham số ra, nó đỏ.
    """

    def test_run_passes_one_frozen_view_to_both_the_plan_and_the_pipeline(
        self, repository, client, monkeypatch, tmp_path
    ):
        seen = {}

        def fake_select(sales=None, identity_store_view=None):
            seen["plan"] = identity_store_view
            return None, None, None

        def fake_run(*, sales, captures=None, identity_store_view=None):
            seen["pipeline"] = identity_store_view
            raise web_server.OwnerUsabilityError("dừng ở đây, đã đủ bằng chứng")

        monkeypatch.setattr(web_server, "_select_captures_for_run", fake_select)
        monkeypatch.setattr(web_server, "run_owner_report", fake_run)

        client.post("/run", data={
            "workbook": (_empty_xlsx(), "so.xlsx")},
            content_type="multipart/form-data")

        assert "plan" in seen and "pipeline" in seen
        # MỘT ảnh chụp, không phải hai: kế hoạch hỏi giá và phép phân giải phải
        # nhìn cùng một trạng thái.
        assert seen["plan"] is seen["pipeline"]
        assert seen["plan"] is not None

    def test_the_view_comes_from_the_gateway_not_from_a_local_file(
        self, repository, client, monkeypatch
    ):
        sentinel = object()
        monkeypatch.setattr(
            web_server.identity_gateway, "store_view", lambda store: sentinel)
        captured = {}

        def fake_run(*, sales, captures=None, identity_store_view=None):
            captured["view"] = identity_store_view
            raise web_server.OwnerUsabilityError("đủ rồi")

        monkeypatch.setattr(
            web_server, "_select_captures_for_run",
            lambda sales=None, identity_store_view=None: (None, None, None))
        monkeypatch.setattr(web_server, "run_owner_report", fake_run)

        client.post("/run", data={"workbook": (_empty_xlsx(), "so.xlsx")},
                    content_type="multipart/form-data")
        assert captured["view"] is sentinel


# --------------------------------------------------------------------------
# Independent Review repair — FIND-R2-IR-01 / FIND-R2-IR-02, qua route THẬT
# --------------------------------------------------------------------------

class TestConflictThroughTheWeb:
    """PROBE-1 của Independent Review đi qua đúng route Flask; bài kiểm này
    tái hiện đường đó rồi khẳng định repair đứng vững.

    Cần một danh mục Tracking THẬT (không chỉ log quyết định) để `ma_tracking`
    xác nhận được, nên lớp này tự dựng `client`/`identity_store` riêng — cùng
    khuôn `test_dec185_nav_chart_identity.py::tracking_on` — thay vì dùng
    fixture `client` chung của file (vốn không nối Tracking).
    """

    RAW_CONFLICT = "43F6000"

    @pytest.fixture
    def identity_store(self, tmp_path):
        from app.modules.product.identity.store import JsonlProductIdentityStore

        return JsonlProductIdentityStore(
            log_path=tmp_path / "identity" / "mappings.jsonl",
            index_path=tmp_path / "identity" / "index.json")

    @pytest.fixture
    def catalog(self):
        """`alias.map` cố ý trỏ THẲNG về `TRK-A100` — đây là điểm khiến kịch
        bản THẬT SỰ là một mâu thuẫn: authority của Tracking đang nói A100,
        trong khi bài kiểm sẽ để Owner chọn B200. Không có `alias_map_rows`
        này, `tracking_authority_code()` không tìm ra authority nào cho tên
        hàng thô, và không có mã đối lập nào được ghi lại — bài kiểm sẽ
        "pass" mà không thật sự canh được `FIND-R2-IR-02`."""
        aid = distinct_identities(
            [fx.row(self.RAW_CONFLICT)])[0].normalized_matching_aid.upper()
        return fx.tracking_snapshot(
            (
                ("TRK-A100", "Tủ lạnh Panasonic NR-BX", (), True),
                ("TRK-B200", "Tivi Sony KD-55", (), True),
            ),
            alias_map_rows=((aid, "TRK-A100"),),
        )

    @pytest.fixture
    def client(self, engine, monkeypatch, tmp_path, identity_store, catalog):
        from app.owner_usability import SelectedCaptures

        monkeypatch.setattr(web_server, "select_latest_valid_captures",
                            lambda: None)
        monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
        monkeypatch.setattr(web_server, "_today", lambda: TODAY)
        # Log quyết định của app trỏ đúng file mà `identity_store` (ở trên)
        # cũng ghi vào — hai object, MỘT nguồn sự thật trên đĩa.
        monkeypatch.setattr(
            web_server.identity_gateway, "DEFAULT_LOG_PATH",
            tmp_path / "identity" / "mappings.jsonl")
        monkeypatch.setattr(
            web_server.identity_gateway, "DEFAULT_INDEX_PATH",
            tmp_path / "identity" / "index.json")
        # Danh mục Tracking: tiêm thẳng vào chỗ route đọc, để cửa kiểm mã của
        # `identity_gateway.confirm_identity` vẫn chạy thật trên dữ liệu này.
        captures = SelectedCaptures(
            tracking_capture=tmp_path / "history.json",
            tracking_catalog=tmp_path / "catalog.json")
        monkeypatch.setattr(
            web_server, "load_tracking_catalog_capture", lambda path: catalog)
        monkeypatch.setattr(
            web_server, "_select_captures_for_run",
            lambda sales=None, identity_store_view=None: (captures, None, None))

        application = web_server.create_app(
            db_path=tmp_path / "runs.db",
            history=history_store.LegacyRepository(engine),
            snapshots=history_store.SnapshotRepository(engine))
        application.testing = True
        return application.test_client()

    def _seed_old_mapping(self, identity_store, *, code="TRK-A100"):
        """Mapping CŨ: xác nhận THƯỜNG, đi qua ĐÚNG cửa mà giao diện đi, TỪ
        TRƯỚC khi mâu thuẫn (giả lập) xuất hiện."""
        return identity_gateway.confirm_identity(
            identity_store, product_raw=self.RAW_CONFLICT,
            tracking_code=code,
            snapshot=fx.tracking_snapshot((
                (code, "Mã ban đầu", (), True),)),
            actor_id="owner-web", client_request_id="seed-old-mapping")

    def _conflicted_order(self, order="BH-CONFLICT"):
        """BH mà pipeline đã ghi `IDENTITY_CONFLICT` ở lần chạy gần nhất —
        bằng chứng của lần chạy đó được fabricate trực tiếp, đúng khuôn
        `unpriced_order()` của các bài Ca B/C phía trên. Phần resolver/
        composition production tạo ra chính lý do này đã có bộ
        `test_r2_product_classification.py` kiểm riêng, đi hết từ đầu."""
        return [line(order, self.RAW_CONFLICT, day=5, sell="9000000",
                     kpi_purchase=None, kpi_profit=None,
                     reasons=("IDENTITY_CONFLICT", "Missing.PurchasePrice"))]

    def test_a_stale_mapping_does_not_hide_the_conflict_on_the_page(
        self, repository, service, client, identity_store
    ):
        """`FIND-R2-IR-01`, PROBE-1 tái hiện qua route thật.

        Trước bản sửa: `web_classification=MATCHED_TRACKING`,
        `conflict_queue_rows=0` — mapping cũ che mất conflict của lần chạy
        hiện hành. Bài này khẳng định cả hai con số đó nay đúng.
        """
        self._seed_old_mapping(identity_store)
        persist(repository, self._conflicted_order())

        workspace = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert 'data-classification="CONFLICT"' in workspace
        assert line_identity.LABEL_CONFLICT in metrics(workspace, "identity-label")

        queue = body(client, "/kinh-doanh/gia-nhap?ky=2026-09&loc=xung-dot")
        assert 'data-metric="no-rows"' not in queue, (
            "hàng đợi xung đột trống — đúng PROBE-1: conflict_queue_rows=0")
        assert any(self.RAW_CONFLICT in text for text in _products(queue))

    def test_choosing_again_clears_the_conflict_from_the_page(
        self, repository, service, client, identity_store
    ):
        """Nửa còn lại của luồng: sau khi CHỌN LẠI, trang phải hiện NGAY là
        đã khớp — không chờ chạy lại sổ (`§4.5`)."""
        self._seed_old_mapping(identity_store)
        persist(repository, self._conflicted_order())
        keys = keys_of(service, "BH-CONFLICT", self.RAW_CONFLICT)

        response = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "ma_tracking": "TRK-B200", "ly_do": "Kiểm tra tem máy lại"})
        assert response.status_code == 302
        assert "da-luu=" in response.headers["Location"]

        workspace = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert 'data-classification="CONFLICT"' not in workspace
        assert line_identity.LABEL_CONFLICT not in metrics(
            workspace, "identity-label")

        queue = body(client, "/kinh-doanh/gia-nhap?ky=2026-09&loc=xung-dot")
        assert 'data-metric="no-rows"' in queue

        # Mapping đang hiệu lực phải mang đúng nhãn "đã giải mâu thuẫn", và
        # mã đối lập ghi lại phải đúng mã đã bác bỏ (`TRK-A100`) — nếu không,
        # `FIND-R2-IR-02` mở lại: authority quay về A100 sẽ bị hỏi lại dù đó
        # chính là mã CŨ trước khi giải, không phải một mâu thuẫn mới.
        view = identity_store.read_at_revision(identity_store.refresh())
        mapping = view.active_mapping(
            "REPORTS_SALES", raw_identity_key(self.RAW_CONFLICT))
        assert mapping.mapping_source is MappingSource.HUMAN_CONFLICT_RESOLUTION
        assert recorded_conflict_opposing_code(mapping) == "TRK-A100"


def _empty_xlsx():
    import io

    from openpyxl import Workbook

    buffer = io.BytesIO()
    Workbook().save(buffer)
    buffer.seek(0)
    return buffer


def _products(html: str) -> list[str]:
    return re.findall(r'<td[^>]*data-identity="[^"]*"[^>]*>(.*?)</td>', html, re.S)
