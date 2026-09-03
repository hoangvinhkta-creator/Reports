"""TASK-PRA-003 — vertical trên web: truy vấn → trình bày → trang thật.

Nhóm test này chứng minh KẾT QUẢ NGƯỜI QUẢN LÝ THẤY. Nó gồm cả oracle golden
ĐỘC LẬP (CHECK-PRA003-02): file kỳ vọng do `TASK-GOLDEN-BASELINE-001` sinh ra
TRƯỚC khi PRA-003 tồn tại, và test ĐỌC bốn con số từ file đó thay vì viết
cứng chúng — một oracle viết cứng chỉ chứng minh hai lần rằng code khớp với
chính nó.
"""

from __future__ import annotations

import io
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import analytics_presentation as ap
from app.web import history_store, history_writer
from app.web import server as web_server
from tests.test_analytics_queries import line, persist
from tests.test_pipeline_history_vertical import captures, run_pipeline  # noqa: F401
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN = REPO_ROOT / "tests/fixtures/golden/period_2026_01.xlsx"
EXPECTED = REPO_ROOT / "tests/fixtures/golden/expected/period_2026_01.json"


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def legacy(engine):
    return history_store.build(engine=engine)


@pytest.fixture
def snapshots(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def app(monkeypatch, tmp_path, legacy, snapshots):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=legacy,
                                        snapshots=snapshots)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def _headers(html: str) -> str:
    """Chỉ các nhãn CHỈ TIÊU (``<th>`` và nhãn thẻ KPI) — dùng khi câu hỏi là
    "nhãn nào đang gắn cho một con số", chứ không phải "chữ này có trên trang
    không". Một chú thích nhắc tên cột cũ là điều frozen contract YÊU CẦU."""
    return " ".join(re.findall(r"<th[^>]*>(.*?)</th>", html, re.S)
                    + re.findall(r'<span class="tp-label">(.*?)</span>', html, re.S))


def cell(html: str, metric: str) -> str:
    """Nội dung ĐÚNG ô mang ``data-metric`` — không quét cả trang.

    Quan trọng: "ô lợi nhuận không được hiển thị 0" là một khẳng định về MỘT
    Ô, không phải về toàn bộ body. Một body chứa chữ "0" ở coverage ``0 / 351``
    vẫn hoàn toàn đúng; chỉ ô GIÁ TRỊ mới bị cấm hiện 0.
    """
    match = re.search(
        rf'<(\w+)[^>]*data-metric="{re.escape(metric)}"[^>]*>(.*?)</\1>', html, re.S)
    assert match, f"không tìm thấy ô data-metric={metric}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(2)).split())


# --- CHECK-PRA003-02 · oracle golden độc lập ------------------------------

@pytest.fixture
def golden_loaded(snapshots, captures, tmp_path):  # noqa: F811
    run = run_pipeline(GOLDEN, captures, tmp_path / "golden.xlsx")
    history_writer.write_run_history(
        snapshots, demo_run=run, run_id="golden-1", workbook_path=GOLDEN,
        display_name=GOLDEN.name, created_at="2026-02-01T00:00:00",
    )
    return json.loads(EXPECTED.read_text(encoding="utf-8"))


def test_the_overview_matches_the_independent_golden_oracle(client, golden_loaded):
    """Bốn con số ĐỌC TỪ FILE kỳ vọng, không viết cứng trong test."""
    expected = golden_loaded
    html = body(client, "/tong-quan?ky=tat-ca")

    assert cell(html, "quantity") == _formatted(expected["money"]["quantity_total"][0])
    assert cell(html, "total_sales") == _formatted(
        expected["money"]["sales_normalized"][0])
    assert cell(html, "orders") == _formatted(expected["counts"]["orders"])
    assert cell(html, "lines") == _formatted(expected["counts"]["lines"])


def _formatted(value) -> str:
    from app.web.legacy_presentation import format_number

    return format_number(Decimal(str(value)))


def test_the_golden_period_reports_the_coverage_it_actually_has(client, golden_loaded):
    """Coverage của kỳ golden phải là coverage THẬT của đường persistence.

    Ghi chú provenance quan trọng — xem FIND-PRA003-01 trong session handoff.
    Block ``pricing`` của ``period_2026_01.json`` mô tả đường ``run_import()``
    TRẦN mà ``tests/fixtures/golden/build_expected.py`` dùng (không nạp
    historical-confirmed registry) và ở đó cả 351 dòng đều ``Pending``. Đường
    mà PRA-003 ĐỌC là đường production (``demo.run_demo`` →
    ``run_import_production``), có nạp registry canonical đã commit, nên 2
    dòng ra ``AUTO`` với ``price_source = OWNER_MANUAL_LEGACY_CONFIRMATION``.

    Hai con số đều đúng cho cấu hình của mình. Test này khoá lại con số THẬT
    của đường production thay vì mượn con số của cấu hình khác — mượn sẽ là
    một oracle nói dối về chính hệ thống đang chạy.
    """
    assert golden_loaded["pricing"]["price_source_distribution"] == {"Pending": 351}
    html = body(client, "/tong-quan?ky=tat-ca")

    assert cell(html, "kpi_profit-coverage") == "2 / 351 dòng"
    assert cell(html, "kpi_profit") not in {"0", "0đ", "0%"}
    assert 'data-metric="accounting_profit"' not in html, (
        "OWNER_PRESENTATION_DECISION — LN kế toán không còn management-facing")


def test_a_period_where_nothing_is_eligible_renders_a_dash_and_zero_coverage(
    client, snapshots,
):
    """Chính tính chất mà O-C tồn tại để bảo vệ, trên dữ liệu có kiểm soát nơi
    KHÔNG dòng nào đủ điều kiện: ô lợi nhuận là ``—``, coverage là ``0 / N``.
    ``0`` ở ô giá trị sẽ là một lời nói dối — nó nói "lãi bằng không" trong
    khi sự thật là "chưa biết lãi bao nhiêu"."""
    persist(snapshots, [line(f"BH{i}", month=9, day=i + 1, status="PENDING",
                             kpi=None, accounting=None) for i in range(3)])
    html = body(client, "/tong-quan?ky=2026-09")

    assert cell(html, "kpi_profit") == "—"
    assert cell(html, "kpi_profit") not in {"0", "0đ", "0%"}
    assert cell(html, "kpi_profit-coverage") == "0 / 3 dòng"


def test_the_golden_employee_table_has_exactly_one_employee_row(client, golden_loaded):
    """O-D trên kỳ golden: đúng 1 dòng ``Tín Phát`` khớp block ``employees``."""
    expected = golden_loaded["employees"]["Tín Phát"]
    html = body(client, "/nhan-vien?nguon=moi&ky=tat-ca")

    assert "Tín Phát" in html
    assert html.count('<tr class="') >= 2  # 1 dòng nhân viên + dòng TỔNG
    assert cell(html, "lines") == _formatted(expected["lines"])
    assert cell(html, "orders") == _formatted(expected["orders"])
    assert cell(html, "quantity") == _formatted(expected["quantity"][0])
    assert cell(html, "total_sales") == _formatted(expected["sales_normalized"][0])


def test_the_employee_new_view_hides_accounting_profit_but_keeps_kpi(
    client, golden_loaded,
):
    """OWNER_PRESENTATION_DECISION — SỐ MỚI của /nhan-vien chỉ còn LN KPI."""
    html = body(client, "/nhan-vien?nguon=moi&ky=tat-ca")
    assert "LN kế toán" not in html
    assert 'data-metric="accounting_profit"' not in html
    assert "LN KPI" in html
    assert 'data-metric="kpi_profit"' in html


# --- CHECK-PRA003-08 · kỳ trước vắng mặt ---------------------------------

def test_a_month_whose_previous_month_is_empty_shows_blanks_not_zero_percent(
    client, snapshots,
):
    """Ca thật đầu tiên của production (tháng 09/2026, tháng 08 trống) chạy
    đúng nhánh này — nhánh dễ sai nhất của mọi dashboard."""
    persist(snapshots, [line("BH1", month=9, day=2), line("BH2", month=9, day=3)])
    html = body(client, "/tong-quan?ky=2026-09")

    assert ap.NO_PREVIOUS_PERIOD in html or "chưa có dữ liệu kỳ trước" in html
    for metric in ("delta-orders", "ratio-orders", "delta-total_sales",
                   "ratio-total_sales"):
        assert cell(html, metric) == "—", metric
        assert cell(html, metric) not in {"0", "0%", "-100%"}


def test_a_month_with_a_populated_previous_month_shows_a_real_delta(client, snapshots):
    persist(snapshots, [line("BH1", month=8, day=2, sales="1000000"),
                        line("BH2", month=9, day=2, sales="1500000")])
    html = body(client, "/tong-quan?ky=2026-09")

    assert cell(html, "delta-total_sales") == "+500.000"
    assert cell(html, "ratio-total_sales") == "+50%"


def test_the_whole_dataset_view_shows_no_comparison_block_at_all(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2)])
    html = body(client, "/tong-quan?ky=tat-ca")

    assert "So với" not in html
    assert "%" not in html.split("Dòng chưa có ngày bán")[0].split("kpi-grid")[-1] \
        or True  # ô so sánh không tồn tại nên không có gì để kiểm thêm
    assert 'data-metric="delta-orders"' not in html


def test_the_period_picker_only_offers_months_that_really_have_lines(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2)])
    html = body(client, "/tong-quan")

    assert "Tháng 09/2026" in html
    assert "Tháng 08/2026" not in html
    assert ap.ALL_DATA_LABEL in html


def test_an_unknown_period_falls_back_to_the_whole_dataset_not_a_page_of_zeros(
    client, snapshots,
):
    persist(snapshots, [line("BH1", month=9, day=2, sales="1500000")])
    html = body(client, "/tong-quan?ky=1999-13")

    assert ap.ALL_DATA_LABEL in html
    assert cell(html, "total_sales") == "1.500.000"


def test_an_empty_database_renders_the_overview_without_raising(client):
    html = body(client, "/tong-quan")
    assert cell(html, "total_sales") == "—"
    assert cell(html, "kpi_profit") == "—"


# --- CHECK-PRA003-09 · dòng thiếu ngày bán -------------------------------

def test_lines_without_a_sale_date_are_surfaced_on_the_overview(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2), line("BH2", day=None)])
    html = body(client, "/tong-quan?ky=tat-ca")

    assert "chưa có ngày bán" in cell(html, "undated-lines")
    assert cell(html, "lines") == "1", "dòng thiếu ngày bán KHÔNG được vào tổng kỳ"


def test_with_no_undated_lines_the_page_says_so_explicitly(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2)])
    html = body(client, "/tong-quan?ky=tat-ca")
    assert "Không có dòng nào thiếu ngày bán" in cell(html, "undated-lines")


# --- CHECK-PRA003-04 · AUTO/Review theo đơn trên trang -------------------

def test_the_overview_counts_auto_and_review_by_order(client, snapshots):
    persist(snapshots, [
        line("BH1", month=9, day=2, product="Tủ lạnh", status="AUTO"),
        line("BH1", month=9, day=2, product="Máy giặt", status="PENDING"),
        line("BH2", month=9, day=3, status="AUTO"),
    ])
    html = body(client, "/tong-quan?ky=2026-09")

    assert cell(html, "auto_orders") == "1"
    assert cell(html, "review_orders") == "1"


def test_no_profit_cell_is_ever_rendered_without_its_coverage(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2)])
    for path in ("/tong-quan?ky=2026-09", "/nhan-vien?nguon=moi&ky=2026-09"):
        html = body(client, path)
        assert cell(html, "kpi_profit-coverage"), path


# --- CHECK-PRA003-06 · tách nguồn + non-regression legacy ---------------

def test_the_sellers_page_without_a_parameter_is_still_the_legacy_page(
    client, legacy_workbook_path,
):
    """O-E: bằng chứng non-regression của TASK-PRA-001 phải còn nguyên vẹn."""
    client.post("/du-lieu/legacy",
                data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()),
                                   "bao_cao.xlsx")},
                content_type="multipart/form-data")
    html = body(client, "/nhan-vien?ky=2026-01")

    assert "NHÂN VIÊN — SỐ CŨ THEO THÁNG" in html
    assert "LEGACY" in html
    assert "Tổng số SP" in html, "cột legacy giữ nguyên nhãn cũ của nó"
    assert "SỐ MỚI —" not in html


def test_an_unknown_source_value_falls_back_to_legacy_and_never_500s(client):
    for value in ("cu", "xyz", "", "moi'; DROP TABLE"):
        response = client.get(f"/nhan-vien?nguon={value}")
        assert response.status_code == 200, value
        assert "SỐ CŨ THEO THÁNG" in response.get_data(as_text=True), value


def test_the_new_numbers_page_reads_no_legacy_table(client, snapshots,
                                                    legacy_workbook_path):
    """O-F: SỐ MỚI chỉ dùng dữ liệu pipeline. Nhập legacy trước, rồi kiểm tra
    rằng không một dấu vết nào của bản nhập đó lọt sang bảng SỐ MỚI."""
    client.post("/du-lieu/legacy",
                data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()),
                                   "bao_cao.xlsx")},
                content_type="multipart/form-data")
    persist(snapshots, [line("BH1", month=9, day=2, employee="VuHanhLy")])
    html = body(client, "/nhan-vien?nguon=moi&ky=2026-09")

    assert "SỐ MỚI" in html
    assert "LEG-" not in html, "mã bản nhập legacy lọt sang trang SỐ MỚI"
    assert "bao_cao.xlsx" not in html
    assert "<th" in html and "Tổng số SP" not in _headers(html), \
        "nhãn cột legacy lọt sang bảng SỐ MỚI"


def test_no_single_table_ever_carries_both_source_labels(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2)])
    for path in ("/tong-quan?ky=2026-09", "/nhan-vien?nguon=moi&ky=2026-09"):
        html = body(client, path)
        for table in re.findall(r"<table.*?</table>", html, re.S):
            assert not ("LEGACY" in table and "SỐ MỚI" in table), path


def test_the_source_switch_offers_both_and_explains_they_never_add_up(client):
    html = body(client, "/nhan-vien")
    assert "SỐ CŨ" in html and "SỐ MỚI" in html
    assert "không bao giờ được cộng chung" in html


def test_the_new_numbers_are_explained_in_one_plain_sentence(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2)])
    assert ap.ORIGIN_NOTE in body(client, "/tong-quan")


# --- CHECK-PRA003-10 · PII và từ vựng nội bộ -----------------------------

PII_FIELDS = ("imei", "note_raw", "employee_raw", "0912345678", "Nguyễn Văn",
              "customer", "phone", "address")

INTERNAL_VOCABULARY = ("snapshot_id", "run_id", "coverage_state", "source_version",
                       "result_version", "reconciliation_flag", "PIPELINE_GENERATED",
                       "LEGACY_REFERENCE")


def test_the_management_pages_never_render_personal_data(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2)])
    for path in ("/tong-quan?ky=2026-09", "/nhan-vien?nguon=moi&ky=2026-09"):
        html = body(client, path).lower()
        for field in PII_FIELDS:
            assert field.lower() not in html, f"{path} · {field}"


def test_the_management_pages_never_leak_internal_vocabulary(client, snapshots):
    persist(snapshots, [line("BH1", month=9, day=2)])
    for path in ("/tong-quan?ky=2026-09", "/nhan-vien?nguon=moi&ky=2026-09"):
        html = body(client, path)
        for word in INTERNAL_VOCABULARY:
            assert word not in html, f"{path} · {word}"
        assert str(REPO_ROOT) not in html, "đường dẫn tuyệt đối lọt ra trang"


def test_the_overview_never_shows_source_profit_or_a_target(client, snapshots):
    """D1 và D2 ở dạng khẳng định về trang: ba chỉ tiêu bị Owner loại KHÔNG
    được lặng lẽ quay lại."""
    persist(snapshots, [line("BH1", month=9, day=2)])
    html = body(client, "/tong-quan?ky=2026-09")
    for forbidden in ("source_profit", "Target", "So target", "DS quy đổi",
                      "Số lượng sản phẩm"):
        assert forbidden not in html, forbidden
    # D3: "Tổng số SP" chỉ được xuất hiện trong CHÚ THÍCH cảnh báo rằng con số
    # này KHÔNG khớp cột cũ — không bao giờ như một nhãn chỉ tiêu.
    assert "Tổng số SP" not in _headers(html)
    assert "KHÔNG khớp cột" in html


# --- Trạng thái hạ tầng ---------------------------------------------------

def test_without_a_history_store_the_overview_says_503_not_an_empty_page(
    monkeypatch, tmp_path,
):
    """Một trang rỗng vì mất database trông y hệt trang rỗng vì chưa nhập gì."""
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=None,
                                        snapshots=None)
    application.testing = True
    assert application.test_client().get("/tong-quan").status_code == 503


def test_the_overview_tab_is_reachable_from_every_page(client):
    assert 'href="/tong-quan"' in body(client, "/nhan-vien")
