"""R7 §A — Tên KH · SĐT · Địa chỉ của dòng ``SAME`` được làm mới từ sổ đang nạp.

## Lỗi production

Owner báo (ảnh chụp tab Nhân viên, 2026-09-11): một số đơn đầu tháng 9 hiện
`—` ở Khách hàng và Liên hệ, trong khi chính sổ kế toán tháng 9 đang nạp CÓ đủ
tên và số điện thoại ở đúng những dòng ấy (đối chiếu trực tiếp trên file).

Ba trường liên hệ không thuộc ``FINGERPRINT_FIELDS``, nên một dòng đã có
version từ lần nạp trước — dù version ấy được ghi lúc liên hệ còn trống — được
reconcile thành ``SAME`` và giữ nguyên version cũ mãi mãi. Sổ nạp sau có đủ
liên hệ cũng không đưa được nó lên màn hình.

## Điều được canh ở đây

    làm mới      SAME + sổ mới có liên hệ khác ⟹ màn hình theo sổ mới
    không xoá    SAME + sổ mới để trống ⟹ giữ liên hệ đã có
    không đổi    version_no, fingerprint, n_same, tiền — KHÔNG đổi
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select

import tools.db as history_db
from app.web import business_service, business_store, history_store
from tools.db.schema import order_line_source_version

from tests.test_employee_workspace_ux import (  # noqa: F401 — fixtures
    SEPTEMBER, body, line, metrics, persist,
)
from tests.test_r3_web_workflow import client  # noqa: F401


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


def _versions(engine):
    with engine.begin() as connection:
        return connection.execute(
            select(order_line_source_version.c.order_key,
                   order_line_source_version.c.version_no,
                   order_line_source_version.c.line_fingerprint,
                   order_line_source_version.c.customer_name,
                   order_line_source_version.c.customer_phone)
            .order_by(order_line_source_version.c.id)).fetchall()


def test_a_same_line_takes_the_contact_the_new_book_carries(
    repository, engine, service, client,
):
    # Lần nạp 1: sổ xuất sớm, liên hệ còn trống — đúng cảnh production.
    first = persist(repository, [
        line("BH73884", "AS65GDBY0", day=1, customer="", phone="", address="")],
        run_id="run-1", at="2026-09-02T00:00:00", fingerprint="fp-a")
    assert first.contact_refreshed == 0
    assert metrics(body(client, "/kinh-doanh/nhan-vien"), "customer-name") == ["—"]

    # Lần nạp 2: CÙNG dòng (fingerprint không đổi), nay có tên + SĐT.
    second = persist(repository, [
        line("BH73884", "AS65GDBY0", day=1, customer="Chị Lê Dung 0967240203",
             phone="0967240203", address="")],
        run_id="run-2", at="2026-09-11T00:00:00", fingerprint="fp-b")
    assert second.counts["SAME"] == 1 and second.contact_refreshed == 1

    html = body(client, "/kinh-doanh/nhan-vien")
    assert metrics(html, "customer-name") == ["Chị Lê Dung 0967240203"]
    assert "0967240203" in html

    # KHÔNG version mới, KHÔNG đổi fingerprint, KHÔNG đổi tiền.
    rows = _versions(engine)
    assert [(r.version_no, r.customer_name) for r in rows] == [
        (1, "Chị Lê Dung 0967240203")]
    assert service.period(**SEPTEMBER).totals.sales_revenue == Decimal("8000000")


def test_an_empty_contact_in_a_later_book_never_erases_what_is_known(
    repository, engine, client,
):
    persist(repository, [
        line("BH1", "43F6000", day=5, customer="Anh Đức", phone="0865001086")],
        run_id="run-1", at="2026-09-06T00:00:00", fingerprint="fp-a")
    result = persist(repository, [
        line("BH1", "43F6000", day=5, customer="", phone="", address="")],
        run_id="run-2", at="2026-09-11T00:00:00", fingerprint="fp-b")
    assert result.counts["SAME"] == 1 and result.contact_refreshed == 0
    assert metrics(body(client, "/kinh-doanh/nhan-vien"), "customer-name") == ["Anh Đức"]


def test_an_identical_contact_writes_nothing(repository):
    pairs = [line("BH1", "43F6000", day=5, customer="Anh Đức", phone="0865001086")]
    persist(repository, pairs, run_id="run-1", at="2026-09-06T00:00:00",
            fingerprint="fp-a")
    result = persist(repository, pairs, run_id="run-2",
                     at="2026-09-11T00:00:00", fingerprint="fp-b")
    assert result.counts["SAME"] == 1 and result.contact_refreshed == 0


def test_a_changed_line_still_gets_a_new_version_with_its_own_contact(
    repository, engine,
):
    """Đường ``SOURCE_CHANGED`` không đi qua làm mới tại chỗ: version mới đã
    mang liên hệ của chính nó — hai cơ chế không giẫm lên nhau."""
    persist(repository, [line("BH1", "43F6000", day=5, customer="", phone="")],
            run_id="run-1", at="2026-09-06T00:00:00", fingerprint="fp-a")
    result = persist(repository, [
        line("BH1", "43F6000", day=5, sell="9000000", customer="Chị Hằng",
             phone="0869055099")],
        run_id="run-2", at="2026-09-11T00:00:00", fingerprint="fp-b")
    assert result.counts["SOURCE_CHANGED"] == 1 and result.contact_refreshed == 0
    rows = _versions(engine)
    assert [(r.version_no, r.customer_name) for r in rows] == [
        (1, ""), (2, "Chị Hằng")]
