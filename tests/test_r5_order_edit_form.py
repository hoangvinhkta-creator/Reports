"""R5 §4 — sửa cả BH bằng MỘT lần bấm.

Trước R5, sửa một BH ba dòng cần tới bốn lần bấm và bốn lần tải lại trang:
`LƯU` một lần cho mỗi ô giá nhập, `GÁN CẢ ĐƠN` cho nhân viên, rồi `XONG`
— vốn chỉ ĐÓNG chế độ sửa chứ không lưu gì. Ba lớp lỗi đi kèm:

1. Bấm `XONG` sau khi gõ giá mà quên `LƯU` là mất trắng phần vừa gõ, và
   màn hình không nói gì — nút tên là "XONG".
2. Mỗi lần `LƯU` là một lần ghi độc lập: ô thứ hai hỏng thì ô thứ nhất đã
   nằm trong database rồi. Người dùng thấy một câu lỗi và không biết phần
   nào đã vào.
3. Nhân viên của cả đơn nằm ở một HÀNG RIÊNG bên dưới các dòng hàng, xa
   chỗ mắt đang nhìn.

R5 gộp về MỘT form cấp BH: chọn nhân viên nằm ngay hàng đầu, giá vẫn ở
đúng dòng của nó, và `XONG` là nút gửi DUY NHẤT — validate toàn bộ trước
khi ghi, rồi ghi CHỈ những ô thật sự đổi.

Ràng buộc R2 §4.4 không được nới một ly: thay một giá AUTO đang có vẫn
phải có lý do. Chỗ gõ lý do gộp về MỘT ô cho cả BH, và nó chỉ bắt buộc
khi trong lần gửi này thật sự có một override.
"""

from __future__ import annotations

import re
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, history_store

from tests.test_employee_workspace_ux import (
    SEPTEMBER, body, line, metrics, persist, three_line_order,
)
from tests.test_r3_web_workflow import client  # noqa: F401

PERIOD_QS = "ky=2026-09&sheet=noi-thanh"


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


def open_edit(client, order="BH72707") -> str:
    return body(client, f"/kinh-doanh/nhan-vien?{PERIOD_QS}&sua={order}")


def price_fields(html: str) -> list[str]:
    """Tên các ô nhập giá của form BH, đọc từ chính HTML."""
    return re.findall(r'name="(gia_nhap__[^"]+)"', html)


def keys_of(service, order_key, product):
    for detail in service.period(**SEPTEMBER).details:
        if detail["order_key"] == order_key and detail["product_raw"] == product:
            return detail
    raise AssertionError(f"không tìm thấy {order_key}/{product}")


def prices_of(service, order_key) -> dict:
    return {detail["product_raw"]: detail["line"].purchase_price
            for detail in service.period(**SEPTEMBER).details
            if detail["order_key"] == order_key}


def employees_of(service, order_key) -> set:
    return {detail["line"].employee
            for detail in service.period(**SEPTEMBER).details
            if detail["order_key"] == order_key}


# --- 1. Hình dạng: một form, một nút gửi ---------------------------------

def test_the_edit_mode_has_exactly_one_submit_button(repository, client):
    persist(repository, three_line_order())
    html = open_edit(client)

    assert 'data-metric="bh-save"' in html, "`XONG` phải là nút gửi"
    assert ">LƯU<" not in html, "không còn nút LƯU từng giá"
    assert "GÁN CẢ ĐƠN" not in html, "không còn nút gán riêng cho nhân viên"


def test_the_employee_selector_sits_on_the_first_row_of_the_order(
    repository, client,
):
    """Không còn một HÀNG RIÊNG bên dưới các dòng hàng (`§27`)."""
    persist(repository, three_line_order())
    html = open_edit(client)
    assert 'class="bh-edit-row' not in html
    first_row = html.split('data-metric="bh-order"', 1)[1].split("</tr>", 1)[0]
    assert 'data-metric="bh-employee-select"' in first_row


def test_every_line_of_the_order_still_has_its_own_price_field(
    repository, client,
):
    persist(repository, three_line_order())
    fields = price_fields(open_edit(client))
    assert len(fields) == 3, "giá vẫn sửa tại TỪNG dòng, không gộp về một ô"
    assert len(set(fields)) == 3


def test_the_form_is_not_nested_inside_another_form(repository, client):
    """HTML sai (`<form>` lồng `<form>`) im lặng nuốt mất phần bên trong."""
    html = open_edit(client) if persist(repository, three_line_order()) else ""
    table = html.split('class="sheet-table"', 1)[1].split("</table>", 1)[0]
    assert "<form" not in table, (
        "ô nhập nằm trong bảng phải trỏ tới form ngoài bằng thuộc tính `form=`")
    assert 'form="bh-edit-BH72707"' in table


# --- 2. Một lần bấm lưu tất cả ------------------------------------------

def test_one_submit_saves_both_the_prices_and_the_employee(
    repository, service, client,
):
    persist(repository, three_line_order())
    html = open_edit(client)
    response = client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Quý",
        price_fields(html)[0]: "4.400.000",
        price_fields(html)[1]: "2.000.000",
        price_fields(html)[2]: "300.000",
        "ly_do": "đối chiếu lại hoá đơn NCC",
    }, follow_redirects=True)
    assert response.status_code == 200

    assert employees_of(service, "BH72707") == {"Quý"}
    assert prices_of(service, "BH72707")["43F6000"] == Decimal("4400000")


def test_the_saved_values_survive_a_reload_and_a_new_service(
    repository, engine, client,
):
    """Không có "lưu giả": đọc lại bằng một service MỚI trên cùng database."""
    persist(repository, three_line_order())
    html = open_edit(client)
    client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Quý",
        price_fields(html)[0]: "4.400.000",
        "ly_do": "đối chiếu lại hoá đơn NCC",
    }, follow_redirects=True)

    fresh = business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))
    assert employees_of(fresh, "BH72707") == {"Quý"}
    assert prices_of(fresh, "BH72707")["43F6000"] == Decimal("4400000")


def test_submitting_without_changing_anything_writes_nothing(
    repository, engine, service, client,
):
    """Ô không đổi KHÔNG được sinh một quyết định — kể cả một quyết định
    trùng giá trị. Một `MANUAL_OVERRIDE` dựng ra chỉ vì Owner bấm `XONG`
    là một lời khẳng định "giá tự động sai" mà không ai từng nói."""
    from tools.db import schema
    from tests.test_snapshot_repository import count

    persist(repository, three_line_order())
    html = open_edit(client)
    before = (count(engine, schema.kpi_purchase_price_override),
              count(engine, schema.employee_attribution_override))

    fields = price_fields(html)
    values = dict(re.findall(
        r'name="(gia_nhap__[^"]+)"\s+value="([^"]*)"', html))
    client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Vinh",
        **{name: values[name] for name in fields},
    }, follow_redirects=True)

    assert (count(engine, schema.kpi_purchase_price_override),
            count(engine, schema.employee_attribution_override)) == before


# --- 3. Validate TOÀN BỘ trước khi ghi ----------------------------------

def test_one_bad_cell_stops_the_whole_write(repository, engine, service, client):
    """Không có thành công MỘT PHẦN: ô hỏng ⟹ không ô nào được ghi."""
    from tools.db import schema
    from tests.test_snapshot_repository import count

    persist(repository, three_line_order())
    html = open_edit(client)
    before = count(engine, schema.kpi_purchase_price_override)
    fields = price_fields(html)

    response = client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Vinh",
        fields[0]: "4.400.000",
        fields[1]: "không phải số",
        "ly_do": "đối chiếu lại hoá đơn NCC",
    }, follow_redirects=True)

    assert count(engine, schema.kpi_purchase_price_override) == before, (
        "ô hợp lệ KHÔNG được ghi khi ô khác của cùng lần gửi hỏng")
    assert prices_of(service, "BH72707")["43F6000"] == Decimal("5000000")
    assert "không phải số" in response.get_data(as_text=True) or \
        "số tiền" in response.get_data(as_text=True).lower()


def test_an_unknown_employee_stops_the_whole_write(
    repository, engine, client, service,
):
    from tools.db import schema
    from tests.test_snapshot_repository import count

    persist(repository, three_line_order())
    html = open_edit(client)
    before = count(engine, schema.kpi_purchase_price_override)
    client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Người Không Có Thật",
        price_fields(html)[0]: "4.400.000",
        "ly_do": "đối chiếu lại hoá đơn NCC",
    }, follow_redirects=True)
    assert count(engine, schema.kpi_purchase_price_override) == before


# --- 4. Lý do override của R2 vẫn còn nguyên ---------------------------

def test_changing_an_auto_price_without_a_reason_is_refused(
    repository, engine, client,
):
    from tools.db import schema
    from tests.test_snapshot_repository import count

    persist(repository, three_line_order())
    html = open_edit(client)
    before = count(engine, schema.kpi_purchase_price_override)
    response = client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Vinh",
        price_fields(html)[0]: "4.400.000",
    }, follow_redirects=True)
    assert count(engine, schema.kpi_purchase_price_override) == before
    assert "lý do" in response.get_data(as_text=True).lower()


def test_the_shared_reason_is_only_required_when_there_is_a_real_override(
    repository, service, client,
):
    """Đổi mỗi nhân viên KHÔNG cần lý do — không có override nào cả."""
    persist(repository, three_line_order())
    client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Quý",
    }, follow_redirects=True)
    assert employees_of(service, "BH72707") == {"Quý"}


def test_the_reason_reaches_the_audit_record_of_every_overridden_line(
    repository, engine, client,
):
    persist(repository, three_line_order())
    html = open_edit(client)
    fields = price_fields(html)
    client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Vinh",
        fields[0]: "4.400.000", fields[1]: "1.900.000",
        "ly_do": "đối chiếu lại hoá đơn NCC",
    }, follow_redirects=True)

    from tools.db import schema
    from tests.test_snapshot_repository import rows
    saved = rows(engine, schema.kpi_purchase_price_override)
    assert len(saved) == 2
    assert all(row["reason"] == "đối chiếu lại hoá đơn NCC" for row in saved)
    assert all(row["provenance"] == "MANUAL_OVERRIDE" for row in saved)


# --- 5. Xoá một giá tay: để trống ô rồi bấm XONG -----------------------

def test_clearing_a_field_removes_the_manual_price(
    repository, service, client,
):
    persist(repository, three_line_order())
    html = open_edit(client)
    client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Vinh",
        price_fields(html)[0]: "4.400.000",
        "ly_do": "đối chiếu lại hoá đơn NCC",
    }, follow_redirects=True)
    assert prices_of(service, "BH72707")["43F6000"] == Decimal("4400000")

    html = open_edit(client)
    client.post("/kinh-doanh/nhan-vien/sua-bh", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Vinh",
        price_fields(html)[0]: "",
    }, follow_redirects=True)
    assert prices_of(service, "BH72707")["43F6000"] == Decimal("5000000"), (
        "để trống ô là gỡ giá tay — dòng trở lại giá tự động")
