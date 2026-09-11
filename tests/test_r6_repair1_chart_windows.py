"""R6 REPAIR-1 · `FIND-R6-IR-01` — cửa sổ so sánh phải nạp ĐỦ dữ liệu.

Finding gốc (`docs/reviews/R6-INDEPENDENT-REVIEW-RECORD.md` §7.1): cả hai biểu
đồ của trang phân tích truyền `view["data"].details` — lát ĐÃ LỌC theo phạm vi
— vào `revenue_timeline.paired_series()`. Cửa sổ so sánh theo định nghĩa nằm
NGOÀI lát ấy, nên nó không có điểm nào; và `_covered_by_confirmed` biến mỗi mốc
không có điểm thành `Decimal(0)` mang cờ `ORIGIN_CURRENT` khi ngày đó nằm trọn
trong một sổ đã xác nhận đầy đủ. Kết quả: một khoảng thời gian CÓ doanh thu và
số đơn THẬT được vẽ thành số 0 "đã đo".

File này đi qua **HTTP THẬT** (một `werkzeug` server nghe trên cổng thật, không
phải test client) vì đúng bề mặt ấy là nơi review đo được sai số, và vì oracle
để so là trang Báo cáo `R5` trên CÙNG server, CÙNG sổ, CÙNG kỳ, CÙNG mức gộp.

Bất biến trung tâm mà file này canh:

    R5 `/kinh-doanh` và R6 `/kinh-doanh/phan-tich` phải nói CÙNG một con số
    cho CÙNG một mốc của cửa sổ so sánh — và con số đó phải là con số THẬT
    trên sổ, không phải 0.
"""

from __future__ import annotations

import http.client
import re
import threading
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from werkzeug.serving import make_server

import tools.db as history_db
from app.web import business_store, catalog_display, history_store
from app.web import revenue_timeline
from app.web import server as web_server
from tools.tracking import live_pull

from tests.test_employee_workspace_ux import line, persist

#: Kỳ đang xem trên cả hai trang. Tháng 9/2026 là kỳ "hiện tại"; `DEC-211`
#: đổi cửa sổ so sánh từ "liền trước" sang CÙNG KỲ NĂM TRƯỚC, nên mốc phải
#: hiện số THẬT nay nằm ở tháng 8/2025 — vẫn NGOÀI lát dữ liệu của kỳ đang
#: chọn, tức vẫn đúng hình dạng lỗi mà `FIND-R6-IR-01` mô tả.
CURRENT_PERIOD = "2026-09"
TODAY = date(2026, 9, 30)

#: Mép phải THẬT của hai biểu đồ khi đang xem `CURRENT_PERIOD`. `DEC-211`
#: neo vào ngày có dữ liệu MỚI NHẤT, không vào ngày cuối kỳ — sổ này ghi tới
#: 25/09/2026, nên cửa sổ kết thúc ở đó chứ không ở 30/09. Mọi kỳ vọng dưới
#: đây tính lại từ hằng số này, không hard-code cửa sổ.
ANCHOR = date(2026, 9, 25)

#: Mốc "có tiền thật trong cửa sổ so sánh" của mức NGÀY, sau `DEC-211`.
#: Cửa sổ hiện tại 31 mốc kết thúc ở `ANCHOR` (25/09/2026) nên bắt đầu từ
#: 26/08/2026; cửa sổ so sánh là đúng khoảng ấy của 2025. 10/09/2025 nằm giữa
#: nó, và `book_2025` đặt một dòng có tiền thật đúng vào ngày đó.
PREV_DAY_KEY = "2025-09-10"
PREV_DAY_REVENUE = "7000000"

#: Khoảng xác nhận đầy đủ phải BAO TRỌN dữ liệu của snapshot
#: (`history_store.confirm_coverage` từ chối khoảng hẹp hơn) — nên nó phủ cả
#: hai cửa sổ, và đó chính là điều kiện KHUẾCH ĐẠI mà §7.1 mô tả: mốc không có
#: điểm sẽ thành số 0 "đã đo" thay vì một khoảng trống nhìn ra được.
#:
#: `DEC-211` kéo cửa sổ so sánh lùi một năm, nên phải có HAI khoảng: một cho
#: cửa sổ hiện tại (2026), một cho cửa sổ so sánh (2025). Không gộp được thành
#: một khoảng: `history_coverage.MAX_CONFIRMED_RANGE_DAYS` chặn ở 366 ngày, và
#: cái chặn đó là một van thật (nó bắt lỗi gõ nhầm năm), không phải một chi
#: tiết của fixture để đi vòng. Vì thế sổ được nạp thành HAI snapshot, mỗi
#: snapshot xác nhận trên đúng khoảng của năm mình — và `confirmed_ranges`
#: gom cả hai, đúng như nó vẫn làm với sổ thật của Owner.
CONFIRMED_RANGES = (
    {"start": date(2025, 7, 1), "end": date(2025, 9, 30)},
    {"start": date(2026, 7, 1), "end": date(2026, 9, 30)},
)


def book():
    """Sổ trải ba tháng, mỗi mốc có tiền THẬT khác nhau để không mốc nào trùng.

    Ngày được chọn để mỗi mức gộp đều có ít nhất một mốc CÓ tiền trong cửa sổ
    so sánh của nó:

    ```text
    mức    cửa sổ hiện tại (neo 30/09/2026)  cửa sổ so sánh    mốc có tiền
    ngay   31/08/2026–30/09/2026             31/08–30/09/2025  10/08? không —
                                                               xem dưới
    tuan   13 tuần tới 30/09/2026            13 tuần ấy /2025  tuần 07/07/2025
    thang  10/2025–09/2026                   10/2024–09/2025   08/2025
    quy    Q4/2025–Q3/2026                   Q4/2024–Q3/2025   Q3/2025
    ```

    `DEC-211` — cửa sổ so sánh nay là CÙNG KỲ NĂM TRƯỚC, nên sổ phải có
    tiền thật ở năm 2025 thì bài kiểm mới đo được điều nó định đo. Các dòng
    2025 là bản sao đúng NGÀY–THÁNG của các dòng 2026, chỉ lùi một năm: nhờ
    thế mỗi mốc của cửa sổ so sánh nằm đúng dưới mốc tương ứng của cửa sổ hiện
    tại, và một sai lệch cửa sổ sẽ hiện ra thành một cặp lệch chỗ chứ không
    thành một con số ngẫu nhiên.

    Riêng mức NGÀY: cửa sổ hiện tại 31 mốc kết thúc 30/09/2026 bắt đầu từ
    31/08/2026, nên mốc 10/08 KHÔNG còn nằm trong cửa sổ nào. Mốc mang tiền
    thật của cửa sổ so sánh ở mức Ngày là `PREV_DAY_KEY` = 10/09/2025 — cùng
    ngày-năm-trước của 10/09/2026.
    """
    return [*book_2025(), *book_2026()]


def book_2025():
    """Phần sổ của cửa sổ SO SÁNH — nạp thành một snapshot riêng."""
    return [
        line("BH2507", "43F6000", year=2025, month=7, day=8, sell="5000000"),
        line("BH2508", "XP352AE-DS", year=2025, month=8, day=10, sell="7000000",
             kpi_purchase="4000000", kpi_profit="3000000"),
        # Mốc NGÀY có tiền thật của cửa sổ so sánh (`PREV_DAY_KEY`).
        line("BH2509", "RT38", year=2025, month=9, day=10, sell="7000000",
             kpi_purchase="4000000", kpi_profit="3000000"),
    ]


def book_2026():
    """Phần sổ của cửa sổ HIỆN TẠI — snapshot thứ hai."""
    return [
        # Tháng 7 — nằm trong cửa sổ hiện tại của mức TUẦN/THÁNG/QUÝ.
        line("BH0701", "43F6000", month=7, day=8, sell="5000000"),
        # Tháng 8.
        line("BH0810", "XP352AE-DS", month=8, day=10, sell="7000000",
             kpi_purchase="4000000", kpi_profit="3000000"),
        line("BH0820", "RT38", month=8, day=20, sell="9000000",
             kpi_purchase="5000000", kpi_profit="4000000"),
        # Tháng 9 — kỳ đang xem.
        line("BH0905", "55Q6FA", month=9, day=5, sell="11000000",
             kpi_purchase="6000000", kpi_profit="5000000"),
        line("BH0925", "Giá treo", month=9, day=25, sell="600000",
             kpi_purchase="300000", kpi_profit="300000"),
    ]


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    """Một server HTTP THẬT nghe trên cổng thật, dựng đúng một lần cho cả file.

    Không dùng `app.test_client()`: review đo sai số qua HTTP, và một bài kiểm
    hồi quy chạy ở một bề mặt khác bề mặt phát hiện lỗi thì không đóng được
    finding.
    """
    tmp = tmp_path_factory.mktemp("r6-repair1-live")
    engine = create_engine(f"sqlite:///{tmp / 'history.db'}")
    history_db.create_all_for_test(engine)
    repository = history_store.SnapshotRepository(engine)

    # Hai snapshot, mỗi cái xác nhận trên khoảng của năm mình — xem
    # `CONFIRMED_RANGES`. Nạp 2025 TRƯỚC để bước R của lần xác nhận sau không
    # đọc các dòng 2025 như vừa biến mất khỏi sổ.
    for index, (pairs, span) in enumerate(
            zip((book_2025(), book_2026()), CONFIRMED_RANGES), start=1):
        outcome = persist(repository, pairs, run_id=f"run-{index}",
                          at=f"2026-10-0{index}T00:00:00.000000",
                          fingerprint=f"fp-{index}")
        repository.confirm_coverage(
            outcome.snapshot_id, confirmed=True,
            confirmed_at=f"2026-10-0{index + 2}T00:00:00", **span)

    # `monkeypatch` là fixture theo HÀM, còn server ở đây dựng một lần cho cả
    # module — nên phải dùng `MonkeyPatch` tường minh và HOÀN NGUYÊN ở `finally`.
    #
    # Gán thẳng vào module (`live_pull.is_configured = ...`) là điều KHÔNG được
    # làm trong pytest: nó rò ra mọi test chạy sau trong cùng tiến trình, và
    # nó đã thật sự làm đỏ `tests/test_tracking_live_pull.py::
    # test_is_configured_requires_both_source_url_and_api_key` ở lần chạy full
    # đầu tiên của repair này. Các script `scripts/r6_*_smoke.py` gán thẳng
    # được vì chúng là tiến trình riêng; một file test thì không.
    patch = pytest.MonkeyPatch()
    patch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    patch.setattr(live_pull, "is_configured", lambda env=None: False)
    patch.setattr(web_server, "_today", lambda: TODAY)
    patch.setattr(catalog_display, "DEFAULT_DISPLAY_PATH",
                  tmp / "tracking_display.json")
    patch.setattr(web_server.identity_gateway, "DEFAULT_LOG_PATH",
                  tmp / "identity" / "mappings.jsonl")
    patch.setattr(web_server.identity_gateway, "DEFAULT_INDEX_PATH",
                  tmp / "identity" / "index.json")

    app = web_server.create_app(
        db_path=tmp / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port, engine, repository
    finally:
        server.shutdown()
        thread.join(timeout=5)
        patch.undo()


def get(port: int, path: str) -> str:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        payload = response.read().decode("utf-8")
        assert response.status == 200, f"{path} → {response.status}"
        return payload
    finally:
        connection.close()


#: Tiền tố `id` của MỌI khối biểu đồ trên trang phân tích. Dùng để CẮT ĐUÔI
#: một khối, không chỉ để tìm đầu nó.
_CHART_ID_PREFIX = 'id="bieu-do-'


def chart_block(html: str, dom_id: str) -> str:
    """Đúng khối HTML của MỘT biểu đồ, CÓ cắt đuôi.

    Trang phân tích có HAI biểu đồ dùng chung một macro. Cắt từ `id` tới HẾT
    trang là không đủ: các chấm của biểu đồ SAU vẫn nằm trong chuỗi, và vì
    `re.findall` gom mọi khớp rồi `dict()` lấy khớp SAU CÙNG cho mỗi khoá, giá
    trị của biểu đồ này sẽ bị giá trị của biểu đồ kia ghi đè. Trước repair cả
    hai đều là `0` nên lỗi đọc ấy vô hình; sau repair nó biến `7.000.000`
    thành `1`.

    Đây đúng cái bẫy mà `S143` §4 đã gặp một lần, ở một hình dạng khác — nên
    lần này việc cắt đuôi được viết vào chính helper, không để mỗi bài kiểm tự
    nhớ.
    """
    assert f'id="{dom_id}"' in html, f"không thấy khối {dom_id}"
    tail = html.split(f'id="{dom_id}"', 1)[1]
    nxt = tail.find(_CHART_ID_PREFIX)
    return tail if nxt < 0 else tail[:nxt]


def comparison_points(block: str) -> dict[str, str]:
    """`{khoá mốc: giá trị thô}` của các chấm thuộc CỬA SỔ SO SÁNH."""
    return {key: value for key, value in re.findall(
        r'data-metric="chart-bar-prev"[^>]*data-key="([^"]+)"'
        r'[^>]*data-revenue="([^"]+)"', block)}


def current_points(block: str) -> dict[str, str]:
    return {key: value for key, value in re.findall(
        r'data-metric="chart-bar"[^>]*data-key="([^"]+)"'
        r'[^>]*data-revenue="([^"]+)"', block)}


def window_spans(granularity: str, anchor: date):
    """`[(đầu, cuối)]` của CỬA SỔ HIỆN TẠI và CỬA SỔ SO SÁNH, riêng từng cái.

    `paired_window_span` trả về khoảng HỢP của hai cửa sổ — đúng câu hỏi "phải
    đọc dữ liệu từ ngày nào tới ngày nào", nhưng sai câu hỏi "hai cửa sổ phủ
    những ngày nào". Trước `DEC-211` hai câu ấy có cùng đáp án vì hai cửa sổ
    liền kề nhau; nay chúng cách nhau đúng một năm, nên khoảng hợp còn chứa cả
    quãng ở giữa mà biểu đồ KHÔNG vẽ.

    Dựng từ chính `window_slots` + `_bucket_span` của engine, nên nó không mở
    ra một phép tính cửa sổ thứ hai để trôi khỏi cái đang chạy thật.
    """
    # `R7 §C` — cửa sổ là CONTAINER LỊCH; đường hiện tại dừng ở mốc neo nên
    # cận trên của cửa sổ hiện tại là cuối MỐC chứa `anchor`, không phải cuối
    # container.
    slots = revenue_timeline.container_slots(granularity, anchor)
    low = revenue_timeline._bucket_span(slots[0][0], granularity)[0]
    high = revenue_timeline._bucket_span(
        revenue_timeline.bucket_of(anchor, granularity)[0], granularity)[1]
    previous = revenue_timeline.container_slots(
        granularity, revenue_timeline.comparison_anchor(granularity, anchor))
    prev_low = revenue_timeline._bucket_span(previous[0][0], granularity)[0]
    prev_high = revenue_timeline._bucket_span(previous[-1][0], granularity)[1]
    return [(low, high), (prev_low, prev_high)]


def comparison_range(block: str) -> str:
    match = re.search(r'data-metric="chart-legend-comparison"[^>]*>(.*?)</span>',
                      block, re.S)
    assert match is not None
    return " ".join(match.group(1).split())


# --- Oracle: trang Báo cáo R5 trên CÙNG server, CÙNG sổ ---------------------

def test_the_r5_report_page_shows_the_real_previous_window_value(live):
    """Neo oracle TRƯỚC khi so. Nếu bài này đỏ thì oracle sai, không phải R6 —
    và cả file mất ý nghĩa. Nên nó chạy đầu tiên và đo riêng."""
    port, _engine, _repository = live
    block = chart_block(get(port, f"/kinh-doanh?ky={CURRENT_PERIOD}&muc=ngay"),
                        "bieu-do-doanh-thu")
    assert comparison_points(block).get(PREV_DAY_KEY) == PREV_DAY_REVENUE


# --- IR-01: doanh thu -------------------------------------------------------

def test_the_revenue_chart_shows_the_real_previous_window_value(live):
    """`FIND-R6-IR-01`, vế doanh thu — ĐỎ trước repair (giá trị là `0`)."""
    port, _engine, _repository = live
    block = chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=ngay"),
        "bieu-do-doanh-thu-r6")
    assert comparison_points(block).get(PREV_DAY_KEY) == PREV_DAY_REVENUE


def test_r5_and_r6_agree_on_every_comparison_bucket_of_the_revenue_chart(live):
    """Hai trang cùng sản phẩm, cùng sổ, cùng kỳ, cùng mức gộp: KHÔNG được cho
    hai con số. Đây là mệnh đề mà `dashboard_metrics` mở đầu bằng việc cấm."""
    port, _engine, _repository = live
    r5 = comparison_points(chart_block(
        get(port, f"/kinh-doanh?ky={CURRENT_PERIOD}&muc=ngay"),
        "bieu-do-doanh-thu"))
    r6 = comparison_points(chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=ngay"),
        "bieu-do-doanh-thu-r6"))
    assert r6 == r5


def test_the_revenue_chart_previous_window_is_not_all_zero(live):
    """Bài canh đúng hình dạng lỗi mà review đo được: `{'0': 31}`."""
    port, _engine, _repository = live
    block = chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=ngay"),
        "bieu-do-doanh-thu-r6")
    values = set(comparison_points(block).values())
    assert values != {"0"}, "cả cửa sổ so sánh bị vẽ thành 0"


# --- IR-01: số đơn ----------------------------------------------------------

def test_the_orders_chart_shows_the_real_previous_window_value(live):
    """`FIND-R6-IR-01`, vế số đơn. 10/08 có ĐÚNG một đơn trên sổ."""
    port, _engine, _repository = live
    block = chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=ngay"),
        "bieu-do-so-don")
    assert comparison_points(block).get(PREV_DAY_KEY) == "1"


def test_the_orders_chart_previous_window_is_not_all_zero(live):
    port, _engine, _repository = live
    block = chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=ngay"),
        "bieu-do-so-don")
    assert set(comparison_points(block).values()) != {"0"}


def test_the_two_charts_cut_the_same_comparison_window(live):
    """Hai biểu đồ phải cắt CÙNG một cửa sổ — nếu không, hai chấm cùng vị trí
    trên hai biểu đồ là hai mốc thời gian khác nhau."""
    port, _engine, _repository = live
    html = get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=ngay")
    revenue = chart_block(html, "bieu-do-doanh-thu-r6")
    orders = chart_block(html, "bieu-do-so-don")
    # Cùng TẬP MỐC trên cả hai cửa sổ: nếu hai biểu đồ cắt hai cửa sổ khác
    # nhau, hai chấm cùng vị trí là hai mốc thời gian khác nhau.
    assert set(comparison_points(revenue)) == set(comparison_points(orders))
    assert set(current_points(revenue)) == set(current_points(orders))


# --- Bao phủ NGÀY · TUẦN · THÁNG · QUÝ --------------------------------------

@pytest.mark.parametrize("granularity",
                         ["ngay", "tuan", "thang", "quy", "nam"])
def test_every_granularity_with_a_comparison_window_loads_real_data(
    live, granularity,
):
    """Ở mọi mức gộp CÓ cửa sổ so sánh, tổng của hai cửa sổ cộng lại phải bằng
    tổng doanh thu THẬT của sổ trong khoảng hai cửa sổ ấy phủ — nói cách khác,
    không đồng nào của sổ bị vẽ thành 0 chỉ vì nó nằm ngoài phạm vi đang chọn.

    Bài này KHÔNG hard-code con số của từng mức: nó tính lại kỳ vọng từ chính
    engine cửa sổ và từ sổ, nên nó đúng ở cả bốn mức mà không cần bốn bảng
    hằng số song song.
    """
    port, _engine, repository = live
    block = chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc={granularity}"),
        "bieu-do-doanh-thu-r6")
    charted = sum(Decimal(value) for value in
                  (*current_points(block).values(),
                   *comparison_points(block).values()))
    spans = window_spans(granularity, ANCHOR)
    # Tính TỪNG cửa sổ rồi cộng, không tính trên khoảng hợp: hai cửa sổ nay
    # cách nhau một năm (`DEC-211`), và ở mức NĂM chúng còn CHỒNG nhau bốn
    # năm — một mốc nằm trong cả hai cửa sổ được vẽ hai lần, đúng như "năm nay
    # so với năm ngoái" đòi hỏi. Cộng từng cửa sổ phản ánh đúng cả hai điều đó.
    real = sum(
        (Decimal(pair[0].total_sales_raw) for low, high in spans
         for pair in book() if low <= pair[0].sale_date <= high), Decimal(0))
    assert charted == real, (
        f"{granularity}: biểu đồ vẽ {charted}, sổ có {real} trong {spans}")


@pytest.mark.parametrize("granularity",
                         ["ngay", "tuan", "thang", "quy", "nam"])
def test_every_granularity_charts_the_real_order_count(live, granularity):
    port, _engine, _repository = live
    block = chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc={granularity}"),
        "bieu-do-so-don")
    charted = sum(int(Decimal(value)) for value in
                  (*current_points(block).values(),
                   *comparison_points(block).values()))
    real = sum(
        len({pair[0].key.order_key for pair in book()
             if low <= pair[0].sale_date <= high})
        for low, high in window_spans(granularity, ANCHOR))
    assert charted == real


# --- Custom range: anchor rõ ràng, không mượn period lock -------------------

def test_a_custom_range_anchors_the_window_on_its_own_end_date(live):
    """Phạm vi tự chọn phải neo cửa sổ vào ĐÚNG `Đến ngày` của nó.

    Neo vào ngày bán muộn nhất CÓ dữ liệu (hành vi của `anchor_date` khi
    `period is None`) sẽ làm cửa sổ trôi theo dữ liệu: hai lần nạp sổ khác
    nhau cho ra hai cửa sổ khác nhau cho cùng một khoảng ngày người dùng gõ.
    """
    port, _engine, _repository = live
    block = chart_block(
        get(port, "/kinh-doanh/phan-tich"
                  "?tu-ngay=2026-09-01&den-ngay=2026-09-20&muc=ngay"),
        "bieu-do-doanh-thu-r6")
    current = current_points(block)
    # Neo = 20/09 ⟹ đường hiện tại DỪNG ở 20/09 (`R7 §C`) ⟹ mốc 25/09 KHÔNG
    # được có mặt dù nó nằm trong container tháng 9.
    assert "2026-09-25" not in current
    assert current.get("2026-09-05") == "11000000"
    # …và cửa sổ so sánh (21/08/2025–20/09/2025) vẫn nạp đủ dữ liệu thật của
    # nó — `DEC-211`: cùng kỳ NĂM TRƯỚC, không phải cửa sổ liền trước.
    assert comparison_points(block).get(PREV_DAY_KEY) == PREV_DAY_REVENUE


def test_a_custom_range_never_borrows_a_period_lock(live):
    """Phạm vi `CUSTOM` mang `period = None`, nên lát dữ liệu của nó — kể cả
    lát MỞ RỘNG cho biểu đồ — không được mang một `ClosedPeriod` nào."""
    port, engine, _repository = live
    service = web_server.business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))
    assert service.period(date_from=date(2026, 7, 23),
                          date_to=date(2026, 9, 20)).closed is None


# --- Số 0 CHỈ khi kỳ trước thật sự rỗng VÀ coverage xác nhận ----------------

def test_a_genuinely_empty_confirmed_bucket_is_still_drawn_as_zero(live):
    """Luật của `R5` không bị nới: một mốc nằm TRỌN trong khoảng đã xác nhận
    đầy đủ mà sổ thật sự không có đơn nào vẫn được vẽ `0`.

    11/09/2025 nằm trong khoảng xác nhận của năm 2025, thuộc cửa sổ so sánh,
    và sổ không có dòng nào ngày đó.
    """
    port, _engine, _repository = live
    block = chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=ngay"),
        "bieu-do-doanh-thu-r6")
    assert comparison_points(block).get("2025-09-11") == "0"


def test_a_bucket_outside_any_confirmed_range_stays_a_gap_not_a_zero(live):
    """Ngoài khoảng đã xác nhận, một mốc không có dữ liệu phải là KHOẢNG TRỐNG
    — không có chấm nào — chứ không phải số 0.

    Khoảng xác nhận sớm nhất bắt đầu 01/07/2025. Mức TUẦN neo 30/09/2026 có
    cửa sổ so sánh 13 tuần kết thúc đầu tháng 9/2025, nên nó lùi tới tháng 6 —
    NGOÀI khoảng xác nhận; những mốc ấy phải vắng mặt.
    """
    port, _engine, _repository = live
    block = chart_block(
        get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=tuan"),
        "bieu-do-doanh-thu-r6")
    span = revenue_timeline.paired_window_span("tuan", ANCHOR)
    charted = {*current_points(block), *comparison_points(block)}
    earliest = min(span["start"] for span in CONFIRMED_RANGES)
    before_confirmed = [
        key for key, _label in revenue_timeline.container_slots(
            "tuan", revenue_timeline.comparison_anchor("tuan", ANCHOR))
        if date.fromisoformat(key) < earliest]
    assert before_confirmed, "fixture phải có mốc ngoài khoảng xác nhận"
    assert not (set(before_confirmed) & charted), (
        f"mốc ngoài khoảng xác nhận bị vẽ thành 0: "
        f"{sorted(set(before_confirmed) & charted)} (span {span})")


# --- Cards/KPI/bảng/basket KHÔNG bị mở rộng ---------------------------------

def test_the_cards_and_tables_still_use_only_the_selected_scope(live):
    """Chỉ DỮ LIỆU CẤP CHO BIỂU ĐỒ được mở rộng. Ô chỉ tiêu, bảng gộp và giỏ
    hàng vẫn phải đọc đúng phạm vi đang xem — nếu không, con số trên đầu trang
    sẽ nói về một khoảng thời gian khác cái người dùng vừa chọn."""
    port, _engine, _repository = live
    html = get(port, f"/kinh-doanh/phan-tich?ky={CURRENT_PERIOD}&muc=ngay")
    revenue = re.search(r'data-metric="sales_revenue"[^>]*title="([^"]+)"', html)
    assert revenue is not None
    # Tháng 9: 11.000.000 + 600.000 = 11.600.000. KHÔNG gồm tháng 7/8.
    assert revenue.group(1) == "11.600.000 đồng"
    orders = re.search(r'data-metric="orders"[^>]*>(.*?)<', html, re.S)
    assert orders.group(1).strip() == "2"


def test_the_group_table_still_reconciles_on_the_selected_scope(live):
    port, _engine, _repository = live
    html = get(port, f"/kinh-doanh/phan-tich/co-cau?ky={CURRENT_PERIOD}")
    match = re.search(r'data-metric="reconciliation"[^>]*data-reconciled="(\w+)"',
                      html)
    assert match is not None and match.group(1) == "yes"
