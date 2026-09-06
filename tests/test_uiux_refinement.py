"""TASK-UIUX-001 — tinh chỉnh trình bày cho NGƯỜI ĐỌC QUẢN TRỊ, kiểm trên HTML thật.

Mỗi test dưới đây canh một điều mà bản audit UI/UX phát hiện là làm người
đọc quản trị hiểu sai hoặc phải cố gắng không cần thiết:

    thẻ KPI không nhãn · mã enum nội bộ lộ ra màn hình · chênh lệch so tháng
    trước đứng xa con số nó so · số âm không phân biệt được · thẻ "không có
    vấn đề" to bằng thẻ có vấn đề · bảng sổ thô kéo cả trang sang ngang ·
    khoảng trống nguồn thương hiệu đọc như một lỗi hệ thống · hai màn hình
    viết ngày theo hai quy ước

Không test nào ở đây hỏi về một con số nghiệp vụ: chúng chỉ hỏi con số đó
ĐƯỢC TRÌNH BÀY như thế nào. Bộ test nghiệp vụ hiện có vẫn là thẩm quyền về
giá trị của các con số.

`test_the_bh_head_count_is_plain_text_not_a_pill_cell` (từng canh ô đếm
"N dòng") đã bị GỠ, không chỉ sửa lại: `TASK-OWNER-UIUX-003` §7 bỏ hẳn ô đó
theo yêu cầu trực tiếp của chủ dự án — số dòng của một BH giờ tự hiện ra
bằng chính số hàng của khối (Ngày/Mã đơn/Khách hàng gộp bằng `rowspan` qua
các hàng đó), nên không còn "viên pill dài" nào để kiểm hình dạng của nó.
Bộ test `tests/test_employee_workspace_ux.py` giữ vai trò kiểm cấu trúc
bảng kê sau khi gộp hàng.
"""

from __future__ import annotations

import re

from app.web import analytics_presentation as ap
from tests.test_employee_workspace_ux import (  # noqa: F401 — fixture qua import
    body, client, engine, line, metric, persist, repository, service, store,
    three_line_order,
)

ENGINEERING_CODES = {"NOI_THANH", "STANDARD_SALES", "GIA_DUNG"}


def test_the_qualifying_quantity_card_carries_its_label(repository, client):
    """Trước bản sửa, thẻ "Tổng số SP" trên Báo cáo hiện một con số KHÔNG TÊN:
    nhãn chưa từng được đăng ký với Jinja nên render thành chuỗi rỗng."""
    persist(repository, three_line_order())
    html = body(client, "/kinh-doanh?ky=2026-09")
    # `TASK-OWNER-UIUX-002` dời bốn thẻ vào MỘT hàng và thêm biểu tượng (?)
    # rê-chuột giữa nhãn và con số (KHÔNG còn `<details>` — xem R2); câu hỏi
    # của test này KHÔNG đổi: thẻ đó có tên chưa.
    card_html = re.search(
        r'<div class="kpi-card">.*?data-metric="qualifying_quantity".*?</div>',
        html, re.S).group(0)
    label = re.search(r'<span class="tp-label">([^<]*)', card_html)
    assert label is not None
    assert label.group(1).strip() == "Tổng số SP"


def test_the_group_column_never_shows_an_engineering_code(repository, client):
    persist(repository, [
        line("BH1", "Tủ lạnh", employee="Vinh", group="NOI_THANH"),
        line("BH2", "Tivi", employee="Ly", group="STANDARD_SALES", row=7),
    ])
    html = body(client, "/kinh-doanh?ky=2026-09")
    # `TASK-OWNER-UIUX-002` R5 bỏ hẳn cột Nhóm khỏi bảng NÀY (chủ dự án yêu
    # cầu trực tiếp) — hàng của Vinh đọc thành hàng NHÓM "Nội thành" và
    # không còn cột nào để mang mã nhóm nữa. Điều quan trọng nhất của test
    # này giữ nguyên: KHÔNG mã máy nào lọt ra chữ người đọc, trên TRANG này.
    table = re.search(r"<h2>Theo nhân viên.*?</table>", html, re.S).group(0)
    assert "Nhóm" not in table and 'data-group="' not in table
    for code in ENGINEERING_CODES:
        assert not re.search(rf">[^<]*\b{code}\b[^<]*<", html), code
    # Bảng Target vẫn liệt kê TỪNG NGƯỜI, và tên nhóm ở đó vẫn viết bằng chữ.
    target = body(client, "/kinh-doanh/target?ky=2026-09")
    assert "Kênh Nội thành" in target
    for code in ENGINEERING_CODES:
        assert not re.search(rf">[^<]*\b{code}\b[^<]*<", target), code


def test_group_label_reads_the_master_and_never_invents_a_name():
    assert ap.group_label("NOI_THANH") == "Kênh Nội thành"
    assert ap.group_label("STANDARD_SALES") == "Kinh doanh tiêu chuẩn"
    assert ap.group_label("KHONG_TON_TAI") == "KHONG_TON_TAI"
    assert ap.group_label(None) == "—"
    assert ap.group_label("") == "—"


def test_month_over_month_sits_beside_the_revenue_not_in_a_trailing_module(
    repository, client
):
    """`TASK-OWNER-UIUX-002` dời ô chủ đạo vào hàng bốn chỉ tiêu; chênh lệch
    so tháng trước vẫn phải đứng trong CÙNG một thẻ với con số nó so."""
    persist(repository, [
        line("BH1", "Tủ lạnh", month=8, sell="1000000"),
        line("BH2", "Tủ lạnh", month=9, sell="1200000", row=7),
    ])
    html = body(client, "/kinh-doanh?ky=2026-09")
    card = re.search(
        r'<div class="kpi-card kpi-strong[^"]*">(.*?)</div>\s*\n\s*<div class="kpi-card',
        html, re.S).group(1)
    assert 'data-metric="sales_revenue"' in card
    assert 'data-metric="mom"' in card
    assert metric(html, "mom") == "+20%"
    assert "kpi-delta up" in card
    assert html.index('data-metric="mom"') < html.index('data-metric="chart"')
    assert "<h2>So với" not in html


def test_a_negative_profit_is_marked_in_the_employee_table(repository, client):
    persist(repository, [line("BH1", "Bếp từ", sell="3200000",
                              kpi_purchase="3500000", kpi_profit="-300000")])
    html = body(client, "/kinh-doanh?ky=2026-09")
    assert re.search(r'class="num neg"\s+data-metric="kpi_profit"', html)


def test_the_undated_footnote_is_not_a_module_when_there_is_nothing_to_warn(
    repository, client
):
    persist(repository, three_line_order())
    html = body(client, "/kinh-doanh?ky=2026-09")
    assert 'class="footnote" data-metric="undated-lines"' in html
    assert "<h2>Dòng chưa có ngày bán</h2>" not in html


def test_every_table_scrolls_inside_its_card(repository, client):
    """Bảng rộng cuộn TRONG thẻ; thân trang không bao giờ kéo sang ngang."""
    persist(repository, three_line_order())
    for path in ("/ban-hang", "/san-pham", "/kinh-doanh?ky=2026-09",
                 "/kinh-doanh/thuong-hieu?ky=2026-09",
                 "/kinh-doanh/co-cau?ky=2026-09", "/du-lieu"):
        html = body(client, path)
        for match in re.finditer(r"<table", html):
            before = html[max(0, match.start() - 160):match.start()]
            assert 'class="tp-scroll"' in before, path


def test_the_brand_gap_reads_as_a_notice_not_an_error(repository, client):
    persist(repository, three_line_order())
    html = body(client, "/kinh-doanh/thuong-hieu?ky=2026-09")
    assert re.search(r'<p class="notice" data-metric="brand-unavailable">', html)
    assert "<details" in html and "Cách đọc bảng này" in html
    # Kết quả đối soát vẫn đọc được KHÔNG cần bấm: nó đứng ngoài <details>.
    assert html.index('data-metric="brand-reconciliation"') < html.index("<details")


def test_the_workspace_still_has_no_collapsible_step(repository, client):
    """`DEC-184` §14 giữ nguyên: không gian làm việc không có <details>."""
    persist(repository, three_line_order())
    assert "<details" not in body(client, "/kinh-doanh/nhan-vien")


def test_the_detail_ledger_writes_dates_like_the_workspace(repository, client):
    persist(repository, three_line_order(day=7))
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-09&loc=tat-ca")
    assert "07/09/2026" in html
    assert "2026-09-07" not in html


def test_snapshot_coverage_is_written_in_words_on_the_data_tab(
    repository, client
):
    persist(repository, three_line_order())
    html = body(client, "/du-lieu")
    assert "Chưa xác nhận đủ" in html
    assert re.search(r"<td[^>]*>\s*DETECTED_ONLY\s*</td>", html) is None
