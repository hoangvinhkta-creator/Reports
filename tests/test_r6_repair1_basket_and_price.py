"""R6 REPAIR-1 · `FIND-R6-IR-02` + `AR-R6-IR-03`.

`FIND-R6-IR-02` (§7.2): bucket "Chưa xác định" đứng làm MỘT NHÓM HÀNG HOÁ trong
Basket. Hệ quả đo được: một đơn có `Tivi` + một dòng chưa khớp mã bị đếm là
"đơn nhiều nhóm hàng hoá", và bảng cặp sinh ra hàng gợi ý bán chéo giữa HAI lý
do chưa xác định (`[xung đột mã] × [chưa khớp mã]`, support 2, 100 %/100 %).

`AR-R6-IR-03` (§7.3): `PriceStats.average` chia một tử số ĐÃ LOẠI dòng thiếu
doanh thu cho một mẫu số VẪN CÒN số lượng của chính dòng ấy — giá bình quân bị
hạ đúng một nửa so với giá duy nhất quan sát được.

Hai finding nằm cùng file vì cùng một ranh giới: chúng đều là *một tập dòng
được dùng ở một nửa phép tính và không được dùng ở nửa kia*.
"""

from __future__ import annotations

import re
from datetime import date
from dataclasses import replace
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.reporting import basket_metrics as bkm
from app.modules.reporting import dashboard_metrics as dmx
from app.modules.reporting import line_type as lt
from app.modules.reporting import product_metrics as pmx
from app.web import catalog_display, history_store
from app.web import product_taxonomy as pt
from app.web import server as web_server
from tools.tracking import live_pull

from tests.test_employee_workspace_ux import TODAY, line, persist
from tests.test_r6_dashboard_metrics import detail
from tests.test_r6_dashboard_metrics import line as plain_line


# --- Dựng bucket bằng ĐÚNG tầng taxonomy thật, không gõ tay -----------------

def known(label):
    return pt.GroupBucket(key=label, label=label)


def undecided(state):
    """Bucket "chưa xác định" dựng qua ĐÚNG `product_taxonomy`, nên nếu ranh
    giới `known` đổi ở đó thì bài kiểm ở đây đổi theo — không có bản sao thứ
    hai của quy tắc."""
    return pt.category_bucket(pt.LineMetadata(
        state=state, tracking_code=None, model_label=None, brand=None,
        category_label=None))


def revenue_unknown(sell="10000000", qty="1", **kwargs):
    """Một dòng hàng hoá CÓ đơn giá và CÓ số lượng nhưng CHƯA có doanh thu.

    `tests/test_r6_dashboard_metrics.line` không dựng được ca này: nó TỰ TÍNH
    `total` từ `sell x qty` khi `total is None`, nên `total=None` ở đó cho ra
    một doanh thu đã biết. Ca "chưa biết doanh thu" là chính ca mà
    `AR-R6-IR-03` nói về, nên nó phải được dựng tường minh — nếu không, bài
    kiểm xanh mà không đo gì.
    """
    return replace(plain_line(sell=sell, qty=qty, **kwargs), total_sales=None)


def index_of(rows):
    """`rows` = `[(BusinessLine, product bucket, category bucket)]`."""
    details = [detail(item[0], product_key=f"pk{index}")
               for index, item in enumerate(rows)]
    return bkm.build_index(details,
                           product_buckets=[item[1] for item in rows],
                           category_buckets=[item[2] for item in rows])


# --- IR-02 · tầng domain ----------------------------------------------------

def test_a_known_category_plus_an_unresolved_line_is_not_a_multi_category_order():
    """`Tivi + Chưa xác định` KHÔNG phải một đơn nhiều nhóm hàng hoá.

    Một trạng thái QUY TRÌNH (chưa khớp mã) không phải một nhóm hàng hoá, và
    đếm nó như một nhóm biến mọi đơn có một dòng chưa phân loại thành một lần
    bán chéo.
    """
    index = index_of([
        (plain_line("BH1"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH1"), known("pk-la"), undecided(pt.STATE_UNRESOLVED)),
    ])
    assert bkm.counts(index).multi_merchandise_category_orders == 0


def test_a_known_category_plus_an_unresolved_line_creates_no_category_pair():
    index = index_of([
        (plain_line("BH1"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH1"), known("pk-la"), undecided(pt.STATE_UNRESOLVED)),
        (plain_line("BH2"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH2"), known("pk-la"), undecided(pt.STATE_UNRESOLVED)),
    ])
    assert bkm.category_pairs(index, min_support=1) == []


def test_two_different_unknown_reasons_never_pair_with_each_other():
    """Bằng chứng §4.2: `[xung đột mã] × [chưa khớp mã]` support 2,
    attachment 100 %/100 % — một gợi ý bán chéo giữa hai trạng thái quy trình.
    """
    index = index_of([
        (plain_line("BH1"), known("pk-a"), undecided(pt.STATE_CONFLICT)),
        (plain_line("BH1"), known("pk-b"), undecided(pt.STATE_UNRESOLVED)),
        (plain_line("BH2"), known("pk-a"), undecided(pt.STATE_CONFLICT)),
        (plain_line("BH2"), known("pk-b"), undecided(pt.STATE_UNRESOLVED)),
    ])
    counts = bkm.counts(index)
    assert counts.multi_merchandise_category_orders == 0
    assert bkm.category_pairs(index, min_support=1) == []


@pytest.mark.parametrize("state", list(pt.UNDECIDED_ORDER))
def test_no_undecided_state_whatsoever_enters_the_category_basket(state):
    """Cả NĂM lý do, không riêng hai lý do review đo được."""
    index = index_of([
        (plain_line("BH1"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH1"), known("pk-x"), undecided(state)),
    ])
    basket = index["BH1"]
    assert basket.categories == frozenset({"Tivi"})
    assert bkm.counts(index).multi_merchandise_category_orders == 0


def test_two_genuine_categories_are_still_a_multi_category_order():
    """Sửa KHÔNG được làm mất phép đếm thật — nếu không, bài kiểm trên xanh
    chỉ vì engine thôi đếm gì cả."""
    index = index_of([
        (plain_line("BH1"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH1"), known("pk-tl"), known("Tủ lạnh")),
    ])
    counts = bkm.counts(index)
    assert counts.multi_merchandise_category_orders == 1
    pairs = bkm.category_pairs(index, min_support=1)
    assert [(pair.left, pair.right) for pair in pairs] == [("Tivi", "Tủ lạnh")]


def test_product_pair_semantics_are_untouched_by_the_category_repair():
    """Phạm vi repair là CATEGORY basket. Cặp SẢN PHẨM giữ nguyên ngữ nghĩa:
    `product_key` là khoá phân tích duy nhất và tồn tại cho mọi dòng, nên một
    dòng chưa khớp mã vẫn là một mặt hàng thật trong giỏ."""
    index = index_of([
        (plain_line("BH1"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH1"), known("pk-la"), undecided(pt.STATE_UNRESOLVED)),
    ])
    assert index["BH1"].products == frozenset({"pk-tivi", "pk-la"})
    assert bkm.counts(index).multi_product_orders == 1
    pairs = bkm.product_pairs(index, min_support=1)
    assert [(pair.left, pair.right) for pair in pairs] == [("pk-la", "pk-tivi")]


# --- IR-02 · tín hiệu data-quality ------------------------------------------

def test_the_index_records_how_much_was_left_out_of_the_category_basket():
    """Loại dòng chưa xác định khỏi phân tích cặp là ĐÚNG, nhưng im lặng về nó
    thì không: người đọc phải biết phần cross-sell chưa phủ hết."""
    index = index_of([
        (plain_line("BH1"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH1"), known("pk-la"), undecided(pt.STATE_UNRESOLVED)),
        (plain_line("BH2"), known("pk-tl"), known("Tủ lạnh")),
    ])
    counts = bkm.counts(index)
    assert counts.orders_with_unknown_category == 1
    assert counts.unknown_category_lines == 1
    assert counts.orders == 2


def test_a_fee_line_is_not_counted_as_an_unknown_category():
    """Dòng phí KHÔNG phải hàng hoá, nên nó không nằm trong chiều nhóm hàng và
    cũng KHÔNG được đếm vào tín hiệu "chưa xác định nhóm hàng" — trộn hai thứ
    ấy làm tín hiệu data-quality nói về một vấn đề không tồn tại."""
    index = index_of([
        (plain_line("BH1"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH1", line_type=lt.TYPE_FEE), known("pk-phi"),
         undecided(pt.STATE_UNRESOLVED)),
    ])
    counts = bkm.counts(index)
    assert counts.unknown_category_lines == 0
    assert counts.orders_with_unknown_category == 0


def test_money_is_never_lost_by_the_category_repair():
    """Tiền của dòng chưa xác định vẫn nằm đủ trong giỏ và trong tổng — repair
    chỉ đổi CHIỀU PHÂN TÍCH, không đổi một đồng nào."""
    rows = [
        (plain_line("BH1", sell="1000000"), known("pk-tivi"), known("Tivi")),
        (plain_line("BH1", sell="2000000"), known("pk-la"),
         undecided(pt.STATE_UNRESOLVED)),
    ]
    index = index_of(rows)
    details = [detail(item[0], product_key=f"pk{i}")
               for i, item in enumerate(rows)]
    assert index["BH1"].revenue == Decimal("3000000")
    assert dmx.totals(details).sales_revenue == Decimal("3000000")


def test_group_reconciliation_still_keeps_every_undecided_line():
    """Bảng gộp theo nhóm hàng vẫn phải giữ TOÀN BỘ dòng và tiền, kể cả dòng
    chưa xác định — đó là điều kiện để đối soát không mất dữ liệu. Repair chỉ
    chạm Basket."""
    rows = [
        (plain_line("BH1", sell="1000000"), known("Tivi")),
        (plain_line("BH2", sell="2000000"), undecided(pt.STATE_UNRESOLVED)),
        (plain_line("BH3", sell="3000000"), undecided(pt.STATE_CONFLICT)),
    ]
    lines = [item[0] for item in rows]
    details = [detail(item[0], product_key=f"pk{i}")
               for i, item in enumerate(rows)]
    grouped = pmx.group_rows(lines, details, [item[1] for item in rows])
    company = dmx.totals(details)
    assert pmx.reconciliation(grouped, company).is_exact
    assert len(grouped) == 3, "ba bucket riêng, không bucket nào bị bỏ"
    assert company.sales_revenue == Decimal("6000000")


# --- AR-R6-IR-03 · tử số và mẫu số phải cùng một tập dòng -------------------

def test_a_line_missing_revenue_leaves_both_sides_of_the_average():
    """Bằng chứng §7.3: hai dòng, mỗi dòng 1 chiếc giá 10.000.000, một dòng
    chưa có `total_sales`. Giá bình quân phải là 10.000.000, KHÔNG phải
    5.000.000."""
    stats = pmx.price_stats([
        plain_line("BH1", sell="10000000", qty="1"),
        revenue_unknown(sell="10000000", qty="1"),
    ])
    assert stats.average == Decimal("10000000.00")


def test_a_line_missing_quantity_leaves_both_sides_of_the_average():
    """Chiều đối xứng: dòng có doanh thu nhưng KHÔNG có số lượng cũng phải rời
    khỏi cả tử số. Giữ nó ở tử số mà không có mẫu số sẽ ĐẨY giá bình quân lên."""
    stats = pmx.price_stats([
        plain_line("BH1", sell="10000000", qty="1"),
        plain_line("BH2", sell="10000000", qty=None, total="10000000"),
    ])
    assert stats.average == Decimal("10000000.00")


def test_a_line_with_zero_quantity_leaves_both_sides_of_the_average():
    stats = pmx.price_stats([
        plain_line("BH1", sell="10000000", qty="1"),
        plain_line("BH2", sell="10000000", qty="0", total="10000000"),
    ])
    assert stats.average == Decimal("10000000.00")


def test_the_ordinary_case_is_unchanged():
    """Ca bình thường phải cho ra ĐÚNG con số cũ — repair không được đổi giá
    bình quân của dữ liệu lành."""
    stats = pmx.price_stats([
        plain_line("BH1", sell="30000000", qty="1"),
        plain_line("BH2", sell="200000", qty="100"),
    ])
    assert stats.average == Decimal("495049.50")


def test_a_gift_priced_zero_still_takes_part_in_the_average_and_the_minimum():
    """`OD-4` — giá 0 của hàng tặng là giá bán THẬT. Nó có đủ doanh thu (0) và
    đủ số lượng, nên nó thuộc tập tính giá bình quân, và vẫn giữ min = 0."""
    stats = pmx.price_stats([
        plain_line("BH1", sell="5000000", qty="1"),
        plain_line("BH2", sell="0", qty="1", total="0",
                   line_type=lt.TYPE_ACCESSORY_GIFT),
    ])
    assert stats.minimum == Decimal("0")
    assert stats.average == Decimal("2500000.00")


def test_no_line_with_enough_data_gives_none_and_a_reason_not_zero():
    stats = pmx.price_stats([
        revenue_unknown(sell="10000000", qty="1"),
    ])
    assert stats.average is None
    assert stats.average_reason is not None


def test_a_fee_only_bucket_gives_none_and_a_reason():
    stats = pmx.price_stats([
        plain_line("BH1", sell="500000", qty="1", line_type=lt.TYPE_FEE),
    ])
    assert stats.average is None
    assert stats.minimum is None
    assert stats.average_reason is not None


def test_the_minimum_and_maximum_read_every_merchandise_line_with_a_price():
    """Min/max KHÔNG bị thu hẹp theo tập tính giá bình quân: một dòng chưa có
    `total_sales` vẫn có một ĐƠN GIÁ quan sát được, và giá thấp nhất/cao nhất
    của nhóm là một sự thật về đơn giá, không về doanh thu."""
    stats = pmx.price_stats([
        plain_line("BH1", sell="10000000", qty="1"),
        revenue_unknown(sell="1000", qty="1"),
    ])
    assert stats.minimum == Decimal("1000")
    assert stats.maximum == Decimal("10000000")
    assert stats.average == Decimal("10000000.00")


def test_the_total_business_quantity_is_not_narrowed_by_the_average_repair():
    """`dashboard_metrics.total_quantity` là chỉ tiêu NGHIỆP VỤ và phải giữ
    nguyên: nó đếm số lượng của MỌI dòng có số lượng, kể cả dòng chưa có doanh
    thu."""
    details = [detail(plain_line("BH1", sell="10000000", qty="1")),
               detail(revenue_unknown(sell="10000000", qty="2"),
                      product_key="pk2")]
    assert dmx.totals(details).total_quantity == Decimal("3")


# --- IR-02 · route THẬT -----------------------------------------------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
    monkeypatch.setattr(catalog_display, "DEFAULT_DISPLAY_PATH",
                        tmp_path / "tracking_display.json")
    monkeypatch.setattr(web_server.identity_gateway, "DEFAULT_LOG_PATH",
                        tmp_path / "identity" / "mappings.jsonl")
    monkeypatch.setattr(web_server.identity_gateway, "DEFAULT_INDEX_PATH",
                        tmp_path / "identity" / "index.json")
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application.test_client()


def body(client, path):
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def metric(html, name):
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)
    assert match is not None, f"không tìm thấy data-metric={name}"
    return match.group(1).strip()


def two_line_order():
    """Một BH hai dòng, KHÔNG dòng nào khớp mã Tracking (không có capture nào),
    nên cả hai rơi vào bucket "chưa xác định" ở chiều nhóm hàng."""
    return [
        line("BH1", "Tivi Samsung QLED 55Q6FA", day=5, sell="9000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_UNRESOLVED",)),
        line("BH1", "Tủ lạnh Samsung RT38", day=5, row=7, sell="7000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("IDENTITY_CONFLICT",)),
    ]


def test_the_basket_route_excludes_unknown_categories(client, engine):
    repository = history_store.SnapshotRepository(engine)
    persist(repository, two_line_order())
    html = body(client, "/kinh-doanh/phan-tich/gio-hang?ky=2026-09&chieu=nhom-hang")
    assert int(metric(html, "multi_merchandise_category_orders")) == 0
    assert "Chưa xác định" not in html.split("Cặp thường đi cùng nhau", 1)[1]


def test_the_basket_route_shows_the_data_quality_signal(client, engine):
    """Người đọc phải thấy phần cross-sell chưa phủ hết, bằng con số cụ thể."""
    repository = history_store.SnapshotRepository(engine)
    persist(repository, two_line_order())
    html = body(client, "/kinh-doanh/phan-tich/gio-hang?ky=2026-09")
    assert int(metric(html, "unknown-category-orders")) == 1
    assert int(metric(html, "unknown-category-lines")) == 2


def test_the_data_quality_signal_leaks_no_customer_field(client, engine):
    repository = history_store.SnapshotRepository(engine)
    persist(repository, two_line_order())
    html = body(client, "/kinh-doanh/phan-tich/gio-hang?ky=2026-09")
    for leaked in ("Nguyễn Thị Hoa", "0912000111", "12 Lê Lợi, Q1"):
        assert leaked not in html


def test_the_basket_route_still_reports_money_and_multi_line(client, engine):
    """Đơn vẫn là một đơn nhiều DÒNG, và tiền không đổi."""
    repository = history_store.SnapshotRepository(engine)
    persist(repository, two_line_order())
    html = body(client, "/kinh-doanh/phan-tich/gio-hang?ky=2026-09")
    assert int(metric(html, "multi_line_orders")) == 1
    overview = body(client, "/kinh-doanh/phan-tich?ky=2026-09")
    assert re.search(r'data-metric="sales_revenue"[^>]*title="([^"]+)"',
                     overview).group(1) == "16.000.000 đồng"
