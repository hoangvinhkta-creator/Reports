"""R5 §2 — danh sách thay đổi gọn và tra cứu được.

Hai lớp lỗi khác nhau, và cả hai đều làm trang snapshot mất tác dụng theo
cùng một cách: người dùng thôi đọc nó.

1. **Nhiễu.** `delivery_cost` và `imei` NẰM TRONG fingerprint, và phải nằm
   trong đó: chúng là dữ liệu nghiệp vụ thật, và một dòng vừa được bổ sung
   IMEI phải sinh source version mới để giá trị ấy được lưu. Nhưng chúng
   KHÔNG phải thứ người dùng cần soi — một lần xuất sổ bổ sung phí giao cho
   ba trăm dòng làm ba trăm mục "Nguồn đã sửa" xuất hiện, và mục thứ ba
   trăm lẻ một — cái đổi doanh thu thật — chìm nghỉm giữa chúng.

   Vì vậy R5 lọc ở TẦNG TRÌNH BÀY và chỉ ở đó: fingerprint không đổi, source
   version không mất, `detail_json` trong database vẫn đủ cả hai trường.

2. **Không tra cứu được.** Bảng cờ chỉ có Số BH dạng chữ. Người đọc thấy
   "BH72707 đã đổi" rồi phải tự đi tìm nó ở tab nào, tháng nào, sheet nào.

Cả hai bài kiểm dưới đây đi qua trang thật, vì cả hai là mệnh đề về cái
người dùng NHÌN THẤY — kiểm ở tầng dưới sẽ xanh trong khi trang vẫn hỏng.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.history import keys as history_keys
from app.web import business_service, business_store, history_store

from tests.test_employee_workspace_ux import body, line, metrics, persist
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


def pair(**overrides):
    return line("BH72707", "43F6000", day=5, sell="8000000",
                kpi_purchase="5000000", kpi_profit="3000000", **overrides)


def with_source(pairs, **source_overrides):
    """Cùng các dòng, nhưng đổi vài trường NGUỒN — sinh source version mới."""
    out = []
    for source, result in pairs:
        values = {name: getattr(source, name)
                  for name in history_keys.FINGERPRINT_FIELDS}
        values.update(source_overrides)
        ordered = tuple(values[name] for name in history_keys.FINGERPRINT_FIELDS)
        changed = type(source)(**{
            **{f: getattr(source, f) for f in source.__dataclass_fields__},
            **values,
            "fingerprint": history_keys.line_fingerprint(ordered),
        })
        out.append((changed, result))
    return out


def snapshot_page(client, snapshot_id: str) -> str:
    return body(client, f"/du-lieu/snapshot/{snapshot_id}")


# --- 1. Lọc nhiễu — chỉ ở tầng trình bày ---------------------------------

def test_a_change_that_is_only_delivery_cost_and_imei_is_not_worth_reviewing(
    repository, client,
):
    first = [pair()]
    persist(repository, first, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(
        repository,
        with_source(first, delivery_cost=Decimal("50000"), imei="356938035643809"),
        run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")

    html = snapshot_page(client, second.snapshot_id)
    assert metrics(html, "review-source-changed") == ["0"], (
        "thay đổi chỉ gồm phí giao/IMEI không phải việc cần người dùng soi")
    assert "delivery_cost" not in html
    assert "imei" not in html
    assert "356938035643809" not in html, "IMEI không có đường ra trang này"


def test_the_source_version_and_the_fingerprint_still_carry_both_fields(
    repository, engine,
):
    """Lọc là chuyện TRÌNH BÀY. Bằng chứng dưới database phải còn nguyên."""
    from tools.db import schema
    from tests.test_snapshot_repository import count, rows

    first = [pair()]
    persist(repository, first, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    before = count(engine, schema.order_line_source_version)
    persist(repository,
            with_source(first, delivery_cost=Decimal("50000"), imei="356938035643809"),
            run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")

    assert count(engine, schema.order_line_source_version) == before + 1, (
        "vẫn phải tạo source version mới — nếu không, IMEI vừa nhập sẽ mất")
    stored = [row for row in rows(engine, schema.order_line_source_version)
              if row["imei"]]
    assert stored and stored[0]["delivery_cost"] is not None
    # Cờ SOURCE_CHANGED và diff đầy đủ vẫn nằm trong bảng cờ.
    flag = [f for f in repository.list_flags() if f["kind"] == "SOURCE_CHANGED"][0]
    assert set(flag["detail_json"]) == {"delivery_cost", "imei"}


def test_a_mixed_change_shows_only_the_fields_that_are_not_noise(
    repository, client,
):
    first = [pair()]
    persist(repository, first, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(
        repository,
        with_source(first, delivery_cost=Decimal("50000"),
                    sell_price=Decimal("9000000"),
                    total_sales_raw=Decimal("9000000")),
        run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")

    html = snapshot_page(client, second.snapshot_id)
    assert metrics(html, "review-source-changed") == ["1"]
    assert "sell_price" in html
    assert "delivery_cost" not in html, "trường nhiễu bị ẩn kể cả trong thay đổi hỗn hợp"


def test_a_real_change_is_still_listed(repository, client):
    first = [pair()]
    persist(repository, first, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(
        repository,
        with_source(first, sell_price=Decimal("9000000"),
                    total_sales_raw=Decimal("9000000")),
        run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")

    html = snapshot_page(client, second.snapshot_id)
    assert metrics(html, "review-source-changed") == ["1"]
    assert "9000000" in html


# --- 2. Cột "Phiên bản" biến khỏi UI, không khỏi audit -------------------

def test_the_version_column_is_gone_from_the_screen(repository, client):
    first = [pair()]
    persist(repository, first, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(
        repository, with_source(first, sell_price=Decimal("9000000"),
                                total_sales_raw=Decimal("9000000")),
        run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")

    html = snapshot_page(client, second.snapshot_id)
    assert "<th>Phiên bản</th>" not in html


def test_the_two_version_ids_are_still_in_the_audit_record(repository):
    first = [pair()]
    persist(repository, first, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    persist(repository, with_source(first, sell_price=Decimal("9000000"),
                                    total_sales_raw=Decimal("9000000")),
            run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")

    flag = [f for f in repository.list_flags() if f["kind"] == "SOURCE_CHANGED"][0]
    assert flag["from_version_id"] is not None
    assert flag["to_version_id"] is not None


# --- 3. Nhân viên hiệu lực + deep link ----------------------------------

def test_each_changed_order_shows_its_effective_employee_and_a_deep_link(
    repository, client,
):
    first = [pair()]
    persist(repository, first, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(
        repository, with_source(first, sell_price=Decimal("9000000"),
                                total_sales_raw=Decimal("9000000")),
        run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")

    html = snapshot_page(client, second.snapshot_id)
    assert metrics(html, "flag-employee") == ["Vinh"]
    link = re.search(r'data-metric="flag-link"[^>]*href="([^"]+)"', html)
    assert link is not None, "Số BH phải là đường dẫn về đúng dòng"
    href = link.group(1)
    assert "ky=2026-09" in href
    assert "sheet=noi-thanh" in href, "sheet của nhóm Nội thành, đúng khoá sheet thật"
    assert href.endswith("#bh-BH72707")


def test_a_flag_whose_line_is_no_longer_current_says_so_instead_of_guessing(
    repository, client, service, store,
):
    """Không đoán nhân viên cho một dòng đã rời khỏi kỳ hiện tại."""
    first = [pair()]
    persist(repository, first, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(
        repository, with_source(first, sell_price=Decimal("9000000"),
                                total_sales_raw=Decimal("9000000")),
        run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")
    # Owner loại dòng khỏi báo cáo — nó không còn là một dòng của kỳ nữa.
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
    detail = data.details[0]
    store.exclude_line(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], excluded_by="test",
        reason="kiểm")

    html = snapshot_page(client, second.snapshot_id)
    assert metrics(html, "flag-employee") == ["Không còn trong kỳ hiện tại"]
    assert 'data-metric="flag-link"' not in html
