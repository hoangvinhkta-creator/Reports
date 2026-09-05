"""`F-01` — script kiểm tác động của `BUSINESS_ROUTING_FIX` trên dữ liệu thật.

Script `tools/db/f01_routing_impact.py` được chạy TRƯỚC một lần tích hợp, để
trả lời "trên database production, có bao nhiêu dòng đổi DS quy đổi vì bản
sửa định tuyến?". Một script chạy đúng một lần vẫn cần test, và cần đúng hai
loại test:

1. nó khớp ĐÚNG tập dòng nó tuyên bố — không rộng hơn, không hẹp hơn;
2. nó TỪ CHỐI trả lời khi database không phải sổ thật.

Loại thứ hai quan trọng hơn loại thứ nhất. Một script in ra
`F01_MATCH_COUNT = 0` khi chạy nhầm trên SQLite dev trống đưa ra một con số
ĐÚNG về database đang mở và HOÀN TOÀN SAI về câu hỏi được hỏi — và không ai
nhìn thấy sự khác biệt, vì cả hai trường hợp in ra cùng một dòng chữ.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select

import tools.db as history_db
from app.modules.reporting.rate_routing import ConversionRateRouter
from app.web import business_store, history_store
from app.web.business_service import CONVERSION_RATES_PATH
from tests.test_business_vertical import pair, persist
from tools.db import f01_routing_impact as f01
from tools.db.schema import order_line_current


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def router():
    return ConversionRateRouter.from_yaml(CONVERSION_RATES_PATH)


def keys_of(engine, order_key: str) -> tuple[str, int]:
    with engine.connect() as conn:
        row = conn.execute(
            select(order_line_current.c.product_key,
                   order_line_current.c.occurrence_index)
            .where(order_line_current.c.order_key == order_key)).one()
    return row[0], int(row[1])


def test_it_refuses_to_answer_on_a_database_that_has_no_ledger(engine):
    """Database đã migrate nhưng chưa nạp sổ ⟹ NOT_MEASURABLE, không phải 0."""
    with pytest.raises(f01.NotAProductionDatabaseError):
        f01.assert_has_ledger(engine)


def test_it_refuses_to_answer_when_the_schema_is_not_even_there():
    with pytest.raises(f01.NotAProductionDatabaseError):
        f01.assert_has_ledger(create_engine("sqlite://"))


def test_it_matches_only_lines_that_satisfy_all_three_conditions(
    engine, store, router
):
    """Ba điều kiện là một phép AND, và test dựng đủ ba phản ví dụ.

    Nếu ai đó nới một điều kiện thành OR, đúng một trong ba dòng "không khớp"
    dưới đây sẽ lọt vào kết quả và test đỏ — thay vì một bản báo cáo tác động
    phóng đại đi thẳng tới Owner.
    """
    repository = history_store.SnapshotRepository(engine)
    persist(repository, [
        # KHỚP: đã phân loại + đã gán lại + nhóm hiệu lực khác nhóm gốc.
        pair("BH1", product="Tủ lạnh", employee="Vinh", group="NOI_THANH",
             kpi_purchase="5000000", kpi_profit="3000000", rate="0.080"),
        # KHÔNG khớp: đã phân loại nhưng KHÔNG gán lại.
        pair("BH2", product="Tivi Sony", employee="Quy", group="NOI_THANH",
             kpi_purchase="5000000", kpi_profit="1000000", rate="0.080"),
        # KHÔNG khớp: đã gán lại nhưng CHƯA phân loại.
        pair("BH3", product="May giat LG", employee="Hiep", group="NOI_THANH",
             kpi_purchase="5000000", kpi_profit="2000000", rate="0.020"),
        # KHÔNG khớp: đã phân loại + đã gán lại nhưng nhóm KHÔNG đổi.
        pair("BH4", product="Noi chien", employee="Vinh", group="NOI_THANH",
             kpi_purchase="5000000", kpi_profit="1000000", rate="0.080"),
    ])
    for order in ("BH1", "BH2", "BH4"):
        product_key, _ = keys_of(engine, order)
        store.set_product_group(product_key=product_key,
                                product_group="GIA_DUNG", classified_by="owner")
    for order, employee, group in (("BH1", "Ly", "PERSONAL"),
                                   ("BH3", "Ly", "PERSONAL"),
                                   ("BH4", "Quy", "NOI_THANH")):
        product_key, occurrence = keys_of(engine, order)
        store.set_employee(order_key=order, product_key=product_key,
                           occurrence_index=occurrence, employee=employee,
                           employee_group=group, source_employee="Vinh")

    found = f01.matches(engine, store, router)
    assert [item["order_key"] for item in found] == ["BH1"]


def test_a_matched_line_reports_both_rates_and_the_exact_delta(
    engine, store, router
):
    """Bảng so sánh phải đủ để Owner tự kiểm lại bằng tay."""
    repository = history_store.SnapshotRepository(engine)
    persist(repository, [
        pair("BH1", product="Tủ lạnh", employee="Vinh", group="NOI_THANH",
             kpi_purchase="5000000", kpi_profit="3000000", rate="0.080"),
    ])
    product_key, occurrence = keys_of(engine, "BH1")
    store.set_product_group(product_key=product_key, product_group="GIA_DUNG",
                            classified_by="owner")
    store.set_employee(order_key="BH1", product_key=product_key,
                       occurrence_index=occurrence, employee="Ly",
                       employee_group="PERSONAL", source_employee="Vinh")

    item, = f01.matches(engine, store, router)
    assert item["old_group"] == "NOI_THANH" and item["new_group"] == "PERSONAL"
    assert item["old_rate"] == Decimal("0.080")
    # `DEC-PHB02-05` — nhân viên bán lẻ KHÔNG BAO GIỜ đi qua 8 %.
    assert item["new_rate"] == Decimal("0.055")
    assert item["new_converted"] - item["old_converted"] == item["delta"]
    assert "F01_MATCH_COUNT = 1" in f01.render([item])


def test_no_match_says_so_in_the_exact_words_the_gate_reads(engine, store, router):
    repository = history_store.SnapshotRepository(engine)
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    rendered = f01.render(f01.matches(engine, store, router))
    assert "F01_MATCH_COUNT = 0" in rendered
    assert "BUSINESS_TOTALS_UNEXPECTEDLY_CHANGED = NO_CONFIRMED" in rendered


def test_the_script_reads_and_never_writes(engine, store, router):
    """Chạy script KHÔNG được đổi một dòng nào của database."""
    repository = history_store.SnapshotRepository(engine)
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])

    def fingerprint():
        with engine.connect() as conn:
            return sorted(
                tuple(row) for row in conn.execute(select(order_line_current)))

    before = fingerprint()
    f01.matches(engine, store, router)
    assert fingerprint() == before
    assert not store.employee_overrides()
    assert not store.product_groups()
