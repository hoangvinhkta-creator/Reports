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
from datetime import date, datetime, timedelta, timezone
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


def _before_now(days: int = 1) -> str:
    """Mốc ISO8601 chắc chắn Ở QUÁ KHỨ so với đồng hồ hệ thống thật.

    Dùng khi `persist()` cần đại diện một BH "đã tồn tại từ trước" một quyết
    định sẽ được ghi bằng đồng hồ thật ngay trong bài kiểm (`confirm_identity`
    qua route) — xem docstring `TestConflictThroughTheWeb`.
    """
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


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
        # `TASK-OWNER-UIUX-009` §1 — "Ngoài bảng giá" không còn chữ riêng
        # (chủ dự án yêu cầu trực tiếp): quyết định này đã xong, không còn gì
        # để hiện cạnh mã đơn.
        assert line_identity.LABEL_OUT_OF_CATALOG not in labels
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

    def test_an_out_of_catalog_line_no_longer_shows_a_tag_but_the_relink_route_still_works(
        self, repository, service, client
    ):
        """`TASK-OWNER-UIUX-009` §1 — đảo lại `§4.3` cũ theo yêu cầu trực tiếp
        của chủ dự án: "Không có trên bảng giá" LÀ đã phân loại xong, nên
        không còn tag cạnh mã đơn mời bấm lại nữa (bài cũ từng canh ngược lại,
        coi việc KHÔNG bấm được là finding chặn — chủ dự án chấp nhận đánh
        đổi này: mất lối vào từ bảng kê).

        Route "nối lại Tracking" (`?phan-loai=1&order_key=...`) vẫn còn sống
        trong code — chỉ không còn cách bấm tới nó từ tag nữa. Bài này canh
        cả hai vế: tag biến mất, route vẫn mở đúng khi gọi thẳng URL.
        """
        persist(repository, unpriced_order())
        keys = keys_of(service, "BH72707", RAW)
        client.post("/kinh-doanh/nhan-vien/ngoai-bang", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys})

        html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert 'data-metric="identity-label"' not in html, (
            "Ngoài bảng giá không còn tag nào cạnh mã đơn")

        # Route vẫn mở đúng chế độ "nối lại" khi gọi thẳng URL.
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

    `persist(..., at=...)` cho các BH "đã có từ trước khi Owner giải mâu
    thuẫn" LUÔN phải truyền tường minh một mốc chắc chắn Ở QUÁ KHỨ so với
    đồng hồ hệ thống thật (`_before_now`) — mặc định của `persist()`
    (`"2026-10-01T00:00:00"`, xem `test_employee_workspace_ux.py`) là một
    ngày nghiệp vụ hư cấu, không phải giờ tường thuật, và có thể rơi SAU
    đồng hồ thật tại thời điểm chạy CI (`FIND-R2-IR-03`: route
    `confirm_identity` ghi `confirmed_at` bằng `datetime.now(timezone.utc)`
    thật — nếu bằng chứng "cũ" lại mang mốc SAU quyết định, `state_of` sẽ
    đúng đắn coi bằng chứng đó mới hơn và không chịu miễn trừ, khiến bài
    kiểm sai một cách giả tạo, không phải vì code sai).
    """

    RAW_CONFLICT = "43F6000"

    @pytest.fixture
    def identity_store(self, tmp_path):
        from app.modules.product.identity.store import JsonlProductIdentityStore

        return JsonlProductIdentityStore(
            log_path=tmp_path / "identity" / "mappings.jsonl",
            index_path=tmp_path / "identity" / "index.json")

    def _snapshot_with_authority(self, code: str):
        """Một ảnh chụp catalog với `alias.map` trỏ THẲNG về `code`.

        Tách khỏi fixture `catalog` để bài `FIND-R2-IR-03` đổi authority
        THẬT giữa chừng (A100 → C300) qua đúng cửa mà `confirm_identity` đọc
        (`tracking_authority_code()`), không chỉ fabricate mã lý do — nếu
        không, `recorded_conflict_opposing_code` sau khi Owner chọn lại sẽ
        vẫn ghi mã authority CŨ (catalog tĩnh), làm bài kiểm "pass" sai.
        """
        aid = distinct_identities(
            [fx.row(self.RAW_CONFLICT)])[0].normalized_matching_aid.upper()
        return fx.tracking_snapshot(
            (
                ("TRK-A100", "Tủ lạnh Panasonic NR-BX", (), True),
                ("TRK-B200", "Tivi Sony KD-55", (), True),
                ("TRK-C300", "Máy giặt LG FV1450", (), True),
            ),
            alias_map_rows=((aid, code),),
        )

    @pytest.fixture
    def catalog(self):
        """`alias.map` cố ý trỏ THẲNG về `TRK-A100` — đây là điểm khiến kịch
        bản THẬT SỰ là một mâu thuẫn: authority của Tracking đang nói A100,
        trong khi bài kiểm sẽ để Owner chọn B200. Không có `alias_map_rows`
        này, `tracking_authority_code()` không tìm ra authority nào cho tên
        hàng thô, và không có mã đối lập nào được ghi lại — bài kiểm sẽ
        "pass" mà không thật sự canh được `FIND-R2-IR-02`.

        Trả về MỘT hộp chứa thay đổi được (`SimpleNamespace`), không phải
        thẳng object ảnh chụp: `client` (dưới) đóng nó vào một `lambda`
        được monkeypatch MỘT lần cho cả bài kiểm, còn bài `FIND-R2-IR-03`
        cần đổi authority THẬT (A100 → C300) giữa chừng, sau khi `client`
        đã dựng xong — sửa `catalog.snapshot` thì `lambda` đọc lại ngay,
        không cần monkeypatch lần hai giữa bài kiểm.
        """
        from types import SimpleNamespace

        return SimpleNamespace(snapshot=self._snapshot_with_authority("TRK-A100"))

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
            web_server, "load_tracking_catalog_capture",
            lambda path: catalog.snapshot)
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
        persist(repository, self._conflicted_order(), at=_before_now())

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
        persist(repository, self._conflicted_order(), at=_before_now())
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

    def test_authority_changing_again_reopens_as_a_new_conflict(
        self, engine, tmp_path, repository, service, client, identity_store,
        catalog,
    ):
        """`FIND-R2-IR-03`, xuyên route Flask thật, toàn bộ chuỗi yêu cầu.

        Owner giải A-vs-B (chọn B200 — xem `_seed_old_mapping`/luồng ở bài
        trên) → trang hết CONFLICT ngay. Sau đó Tracking đổi authority sang
        C300: một lần chạy sổ MỚI (mô phỏng bằng `persist` lần hai, CÙNG
        order/product key, `run_id`/`fingerprint` khác — đúng khuôn "nạp lại
        sổ" của `test_the_customer_fields_survive_a_new_snapshot`) ghi lại
        `IDENTITY_CONFLICT`. Đây là một mâu thuẫn HOÀN TOÀN KHÁC (A-vs-C,
        không phải A-vs-B đã giải) — trang phải hiện CONFLICT trở lại, có
        nút chọn lại, và dòng phải vào hàng đợi xung đột — chứ không được để
        quyết định A-vs-B cũ (`conflict_resolved` chỉ theo khoá) che mất nó.

        Owner chọn lại A100 cho ĐÚNG mâu thuẫn A-vs-C này; quyết định đó phải
        đứng vững qua một `create_app()` mới (mô phỏng restart).
        """
        self._seed_old_mapping(identity_store)
        persist(repository, self._conflicted_order(), at=_before_now(days=2))
        keys = keys_of(service, "BH-CONFLICT", self.RAW_CONFLICT)

        # Nửa đầu: giải A-vs-B, giữ B200 — trang phải hết CONFLICT ngay.
        response = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "ma_tracking": "TRK-B200", "ly_do": "Kiểm tra tem máy lại"})
        assert response.status_code == 302
        workspace = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert 'data-classification="CONFLICT"' not in workspace

        # Yêu cầu 3: chạy lại sổ với authority KHÔNG đổi (vẫn B200) — không
        # được hỏi lại. `_human_decision_resolution` (repair `FIND-R2-IR-02`)
        # tự miễn trừ ở tầng resolver nên lần chạy lại không còn lý do
        # `IDENTITY_CONFLICT` nào để fabricate — persist một bản KHÔNG xung
        # đột, đúng những gì resolver production sẽ thật sự tạo ra.
        persist(repository, [
            line("BH-CONFLICT", self.RAW_CONFLICT, day=5, sell="9000000",
                 kpi_purchase="6000000", kpi_profit="3000000", reasons=())
        ], run_id="run-2", at=_before_now(), fingerprint="fp-b")
        workspace = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert 'data-classification="CONFLICT"' not in workspace, (
            "authority không đổi — không được hỏi lại")

        # Tracking đổi authority sang C300 — THẬT, qua đúng cửa mà
        # `confirm_identity` đọc (`tracking_authority_code()`), không chỉ
        # fabricate mã lý do: nếu không, `recorded_conflict_opposing_code`
        # ở bước chọn lại phía dưới vẫn sẽ ghi A100 (authority CŨ của catalog
        # tĩnh), và bài kiểm sẽ không thật sự canh được yêu cầu 1.
        catalog.snapshot = self._snapshot_with_authority("TRK-C300")

        # Lần chạy sổ MỚI, SAU quyết định A-vs-B, lại ghi IDENTITY_CONFLICT —
        # một mâu thuẫn A-vs-C mới.
        #
        # `at` lấy ĐÚNG đồng hồ thật NGAY LÚC NÀY (không lệch ngày hư cấu):
        # bài kiểm còn một bước giải mâu thuẫn NỮA phía dưới (Owner chọn lại
        # A cho A-vs-C), và bước đó cũng ghi `confirmed_at` bằng đồng hồ
        # thật — nó chỉ có thể diễn ra SAU câu lệnh này theo đúng thứ tự thực
        # thi thật, nên không cần và không nên gán một mốc tương lai hư cấu.
        persist(repository, self._conflicted_order(), run_id="run-3",
                at=datetime.now(timezone.utc).isoformat(), fingerprint="fp-c")

        workspace = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert 'data-classification="CONFLICT"' in workspace, (
            "authority đổi sang C — quyết định A-vs-B cũ không được che mất "
            "mâu thuẫn A-vs-C mới")
        assert line_identity.LABEL_CONFLICT in metrics(workspace, "identity-label")

        # Yêu cầu 6: giá/lợi nhuận còn None trong lúc mâu thuẫn MỚI chưa xử lý.
        data = service.period(**SEPTEMBER)
        line_detail = next(
            d for d in data.details
            if d["order_key"] == "BH-CONFLICT" and d["product_raw"] == self.RAW_CONFLICT)
        assert line_detail["line"].purchase_price is None
        assert line_detail["line"].kpi_profit is None

        # Yêu cầu 4: dòng phải vào hàng đợi xung đột, có đường chọn lại.
        queue = body(client, "/kinh-doanh/gia-nhap?ky=2026-09&loc=xung-dot")
        assert 'data-metric="no-rows"' not in queue
        assert any(self.RAW_CONFLICT in text for text in _products(queue))

        # Owner chọn lại A100 cho ĐÚNG mâu thuẫn A-vs-C hiện hành.
        keys = keys_of(service, "BH-CONFLICT", self.RAW_CONFLICT)
        response = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
            "ky": "2026-09", "sheet": "noi-thanh", **keys,
            "ma_tracking": "TRK-A100", "ly_do": "C300 sai — vẫn là A100"})
        assert response.status_code == 302

        workspace = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert 'data-classification="CONFLICT"' not in workspace

        # Yêu cầu 5: quyết định phải persist qua reload/restart.
        view = identity_store.read_at_revision(identity_store.refresh())
        mapping = view.active_mapping(
            "REPORTS_SALES", raw_identity_key(self.RAW_CONFLICT))
        assert mapping.mapping_source is MappingSource.HUMAN_CONFLICT_RESOLUTION
        assert mapping.source_product_code == "TRK-A100"
        assert recorded_conflict_opposing_code(mapping) == "TRK-C300"

        # "Restart" thật: một `create_app()` MỚI, không phải chỉ đọc lại file
        # qua object `identity_store` đang mở sẵn — instance Flask cũ đã bị
        # bỏ hẳn, instance mới tự mở lại `mappings.jsonl`/`index.json` từ đĩa
        # (đường dẫn đã monkeypatch ở fixture `client` vẫn còn hiệu lực vì
        # nó vá module-level, không gắn với một app cụ thể).
        restarted = web_server.create_app(
            db_path=tmp_path / "runs.db",
            history=history_store.LegacyRepository(engine),
            snapshots=history_store.SnapshotRepository(engine))
        restarted.testing = True
        restarted_client = restarted.test_client()

        workspace_again = body(
            restarted_client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
        assert 'data-classification="CONFLICT"' not in workspace_again, (
            "quyết định A-vs-C phải đứng vững qua một app mới sau restart")


def _empty_xlsx():
    import io

    from openpyxl import Workbook

    buffer = io.BytesIO()
    Workbook().save(buffer)
    buffer.seek(0)
    return buffer


def _products(html: str) -> list[str]:
    return re.findall(r'<td[^>]*data-identity="[^"]*"[^>]*>(.*?)</td>', html, re.S)
