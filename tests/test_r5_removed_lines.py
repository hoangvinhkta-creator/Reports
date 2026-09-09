"""R5 §1 — sổ đã xác nhận đầy đủ và dòng biến mất khỏi nó.

Câu hỏi trung tâm, và là toàn bộ lý do file này tồn tại:

    sau khi NGƯỜI DÙNG đã xác nhận "sổ này đầy đủ cho khoảng ngày X", một
    dòng cũ nằm trong X mà sổ đó KHÔNG có thì còn được cộng vào tổng nữa
    không?

Trước R5 câu trả lời là CÓ: `REMOVED_IN_SOURCE_CANDIDATE` chỉ là một dòng
trong bảng cờ, và mọi con số đi qua `BusinessReportService.period` không hề
biết cờ đó tồn tại. Đó an toàn khi file mới là file MỘT PHẦN — nhưng người
dùng vừa nói nó KHÔNG phải file một phần.

Quyết định Owner 08/09/2026 (`DEC-R5-01`) đổi đúng một mệnh đề: cờ phát sinh
từ một snapshot `CONFIRMED_COMPLETE` và CÒN HIỆU LỰC thì tạm loại dòng khỏi
dữ liệu hiệu lực. Ba biên vẫn không đổi và được canh ở đây:

    file CHƯA xác nhận   → không đổi một đồng nào (chỉ cảnh báo)
    lịch sử              → không hard-delete: version/snapshot/flag còn nguyên
    dòng quay lại        → cảnh báo tự mất, số tự khôi phục

Test đi qua tầng ráp thật (`BusinessReportService.period`) chứ không qua một
hàm phụ, vì "loại khỏi TOÀN BỘ số liệu" chỉ đúng theo cấu tạo khi tập bị loại
không bao giờ đi vào tập được cộng.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, history_store
from app.web import revenue_timeline
from app.web.period_lock import content_fingerprint
from tools.db import schema

from tests.test_employee_workspace_ux import (
    SEPTEMBER, TODAY, body, line, metrics, persist,
)
from tests.test_r3_web_workflow import PERIOD_QS, client  # noqa: F401
from tests.test_snapshot_repository import count, rows

CONFIRMED_RANGE = {"start": date(2026, 9, 1), "end": date(2026, 9, 30)}


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


def two_orders():
    """Hai BH một dòng, cùng tháng 9 — một cái sẽ biến mất ở lần nạp sau."""
    return [
        line("BH1", "43F6000", day=5, sell="8000000",
             kpi_purchase="5000000", kpi_profit="3000000"),
        line("BH2", "XP352AE-DS", day=6, sell="4000000",
             kpi_purchase="2000000", kpi_profit="2000000"),
    ]


def confirm(repository, snapshot_id, at="2026-10-02T00:00:00"):
    return repository.confirm_coverage(
        snapshot_id, confirmed=True, confirmed_at=at, **CONFIRMED_RANGE)


def load_both_then_drop_bh2(repository):
    """Nạp hai đơn, rồi nạp lại một sổ chỉ còn BH1."""
    pairs = two_orders()
    persist(repository, pairs, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    return persist(repository, pairs[:1], run_id="run-2",
                   at="2026-10-02T00:00:00", fingerprint="fp-b")


def order_keys(data) -> set:
    return {detail["order_key"] for detail in data.details}


# --- 1. File CHƯA xác nhận: không một đồng nào đổi ------------------------

def test_an_unconfirmed_snapshot_never_removes_a_line_from_the_totals(
    repository, service,
):
    """`NOT_SEEN_IN_LATEST_SNAPSHOT` vẫn CHỈ là cảnh báo — biên không đổi."""
    load_both_then_drop_bh2(repository)

    data = service.period(**SEPTEMBER)
    assert order_keys(data) == {"BH1", "BH2"}
    assert data.totals.orders == 2
    assert data.totals.sales_revenue == Decimal("12000000")
    assert data.removed_in_source == []


# --- 2. File ĐÃ xác nhận: dòng vắng bị tạm loại khỏi MỌI số ---------------

def test_a_confirmed_complete_snapshot_drops_the_missing_line_from_every_figure(
    repository, service,
):
    second = load_both_then_drop_bh2(repository)
    before = service.period(**SEPTEMBER)
    assert before.totals.sales_revenue == Decimal("12000000")

    confirm(repository, second.snapshot_id)
    after = service.period(**SEPTEMBER)

    assert order_keys(after) == {"BH1"}, "BH2 phải rời khỏi dữ liệu hiệu lực"
    assert after.totals.orders == 1, "BH mất trọn dòng không được tính vào số đơn"
    assert after.totals.lines == 1
    assert after.totals.sales_revenue == Decimal("8000000")
    assert after.totals.kpi_profit == Decimal("3000000")
    assert after.totals.converted_sales != before.totals.converted_sales


def test_the_dropped_line_lands_in_its_own_warning_list_with_no_money(
    repository, service,
):
    """Danh sách cảnh báo chỉ để TRA CỨU: Số BH, ngày cũ, sản phẩm, nhân viên."""
    second = load_both_then_drop_bh2(repository)
    confirm(repository, second.snapshot_id)

    data = service.period(**SEPTEMBER)
    assert len(data.removed_in_source) == 1
    dropped = data.removed_in_source[0]
    assert dropped["order_key"] == "BH2"
    assert dropped["sale_date"] == date(2026, 9, 6)
    assert dropped["product_raw"] == "XP352AE-DS"
    assert dropped["line"].employee == "Vinh"
    # Số tiền của dòng KHÔNG được cộng vào bất kỳ tổng nào — kể cả một tổng
    # "của riêng danh sách cảnh báo".
    assert data.totals.sales_revenue == Decimal("8000000")


def test_the_chart_the_sheets_and_the_export_all_read_the_reduced_set(
    repository, service,
):
    """Một effective data ⟹ biểu đồ, sheet nhân viên và Excel cùng rơi theo."""
    second = load_both_then_drop_bh2(repository)
    confirm(repository, second.snapshot_id)
    data = service.period(**SEPTEMBER)

    points = revenue_timeline.series(data.details, granularity=revenue_timeline.DAY)
    assert revenue_timeline.totals_of(points) == Decimal("8000000")
    assert all(point.key != "2026-09-06" for point in points)

    assert {employee for _, employee in data.sheet_assignments()} == {"Vinh"}
    assert data.for_employee("Vinh").totals.sales_revenue == Decimal("8000000")

    workbook = service.export_workbook(data=data, period_label="09/2026")
    text = "\n".join(
        str(cell.value)
        for sheet in workbook.worksheets
        for row in sheet.iter_rows()
        for cell in row
        if cell.value is not None)
    assert "BH1" in text
    assert "BH2" not in text, "dòng đã tạm loại không được xuất ra Excel"


def test_the_period_fingerprint_moves_when_a_line_is_dropped(
    repository, service,
):
    """Vân tay chốt kỳ đọc cùng tập — nếu không, một kỳ đã chốt sẽ im lặng."""
    second = load_both_then_drop_bh2(repository)
    before = service.period(**SEPTEMBER, period=(2026, 9))
    fingerprint_before = content_fingerprint(
        details=before.details, totals=business_service.snapshot_of(before.totals))

    confirm(repository, second.snapshot_id)
    after = service.period(**SEPTEMBER, period=(2026, 9))
    assert content_fingerprint(
        details=after.details,
        totals=business_service.snapshot_of(after.totals)) != fingerprint_before


# --- 3. Lịch sử KHÔNG bị xoá ---------------------------------------------

def test_nothing_is_hard_deleted_when_a_line_is_dropped(
    repository, engine, service,
):
    second = load_both_then_drop_bh2(repository)
    before = {
        "current": count(engine, schema.order_line_current),
        "source_versions": count(engine, schema.order_line_source_version),
        "flags": count(engine, schema.reconciliation_flag),
    }
    confirm(repository, second.snapshot_id)
    service.period(**SEPTEMBER)

    assert count(engine, schema.order_line_current) == before["current"]
    assert (count(engine, schema.order_line_source_version)
            == before["source_versions"])
    assert count(engine, schema.reconciliation_flag) > before["flags"]
    assert {row["order_key"] for row
            in rows(engine, schema.order_line_current)} == {"BH1", "BH2"}


# --- 4. Dòng quay lại: cảnh báo tự mất, số tự khôi phục -------------------

def test_a_line_that_comes_back_is_restored_to_the_totals_by_itself(
    repository, service,
):
    pairs = two_orders()
    persist(repository, pairs, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(repository, pairs[:1], run_id="run-2",
                     at="2026-10-02T00:00:00", fingerprint="fp-b")
    confirm(repository, second.snapshot_id)
    assert service.period(**SEPTEMBER).totals.sales_revenue == Decimal("8000000")

    # Kế toán xuất lại sổ, lần này có đủ cả hai đơn.
    persist(repository, pairs, run_id="run-3", at="2026-10-03T00:00:00",
            fingerprint="fp-c")

    restored = service.period(**SEPTEMBER)
    assert order_keys(restored) == {"BH1", "BH2"}
    assert restored.totals.sales_revenue == Decimal("12000000")
    assert restored.removed_in_source == [], "cảnh báo phải TỰ mất"


# --- 5. Biên phạm vi: ngoài khoảng đã xác nhận thì không đụng tới ---------

def test_a_line_outside_the_confirmed_range_is_never_dropped(
    repository, service,
):
    pairs = [
        line("BH1", "43F6000", day=5, sell="8000000"),
        line("BH2", "XP352AE-DS", month=10, day=6, sell="4000000"),
    ]
    persist(repository, pairs, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(repository, pairs[:1], run_id="run-2",
                     at="2026-10-02T00:00:00", fingerprint="fp-b")
    confirm(repository, second.snapshot_id)

    october = service.period(date_from=date(2026, 10, 1), date_to=date(2026, 10, 31))
    assert order_keys(october) == {"BH2"}
    assert october.removed_in_source == []


# --- 6. Màn hình: câu chữ và danh sách cảnh báo ---------------------------

def test_the_workspace_shows_the_dropped_line_in_its_own_warning_block(
    repository, service, client,
):
    """Danh sách "Không còn trong file đầy đủ" — tra cứu được, không có tiền."""
    second = load_both_then_drop_bh2(repository)
    confirm(repository, second.snapshot_id)

    html = body(client, f"/kinh-doanh/nhan-vien?{PERIOD_QS}&sheet=Vinh")
    assert "Không còn trong file đầy đủ" in html
    assert metrics(html, "removed-order") == ["BH2"]
    assert metrics(html, "removed-product") == ["XP352AE-DS"]
    assert metrics(html, "removed-employee") == ["Vinh"]
    assert metrics(html, "removed-date") == ["06/09/2026"]
    # Không một ô tiền nào của dòng bị loại lọt vào khối cảnh báo.
    block = html.split("Không còn trong file đầy đủ", 1)[1].split("</div>", 3)[0]
    assert "4.000.000" not in block
    # Và các con số của sheet đã trừ đúng dòng đó ra.
    assert "8.000.000" in html


def test_the_workspace_has_no_warning_block_before_the_snapshot_is_confirmed(
    repository, service, client,
):
    load_both_then_drop_bh2(repository)
    html = body(client, f"/kinh-doanh/nhan-vien?{PERIOD_QS}&sheet=Vinh")
    assert "Không còn trong file đầy đủ" not in html


def test_the_confirmation_message_says_the_lines_were_dropped(
    repository, client,
):
    """Câu sau khi bấm xác nhận phải nói HỆ QUẢ THẬT, không phải hệ quả cũ."""
    second = load_both_then_drop_bh2(repository)
    response = client.post(
        f"/du-lieu/snapshot/{second.snapshot_id}/xac-nhan-du",
        data={"tu_ngay": "2026-09-01", "den_ngay": "2026-09-30", "xac_nhan": "1"},
        follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "TẠM LOẠI" in html
    assert "VẪN tính" not in html, "câu cũ mô tả hành vi trước R5 — phải biến mất"
