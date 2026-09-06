"""`TASK-OWNER-UIUX-002` — trang Báo cáo đọc theo thứ tự của người quản lý.

Bản tinh chỉnh này KHÔNG đổi một con số nào. Nó đổi bốn thứ:

    kỳ mở đầu      mở tab Báo cáo là thấy THÁNG NÀY, không phải chọn kỳ trước
    hàng chỉ tiêu  bốn chỉ tiêu trên MỘT hàng, định nghĩa lùi sau dấu (?)
    biểu đồ        ĐƯỜNG, mở ở mức NGÀY
    cần kiểm tra   một khối gọn ở CUỐI trang thay cho hai thẻ lớn chen giữa

và một thứ về CÁCH ĐỌC bảng "Theo nhân viên": Vinh · Quý · Hiệp đọc thành
MỘT hàng "Nội thành", Gia dụng là hàng cuối, mọi người còn lại giữ tên riêng.

Bất biến quan trọng nhất của cả file, và là thứ duy nhất phân biệt một bản
sửa giao diện với một bản sửa làm hỏng sổ sách:

    Σ(các hàng hiện ra)  ==  tổng chính thức của kỳ

Nó đúng theo CẤU TẠO chứ không theo lời hứa, vì bảng đọc chính phân hoạch
`reporting_sheets.sheet_key_of` mà không gian làm việc đã dùng từ
`DEC-PHB02-08` — một hàm toàn phần, nên không dòng nào rơi ra ngoài và không
dòng nào được đếm hai lần.
"""

from __future__ import annotations

import re
from decimal import Decimal

from app.modules.reporting import business_metrics as bm
from app.web import revenue_timeline
from tests.test_employee_workspace_ux import (  # noqa: F401 — fixture qua import
    TODAY, body, client, engine, line, metric, persist, repository, service,
    store, three_line_order,
)

#: Ba người thuộc nhóm `NOI_THANH` trong master — và CHỈ ba người này gộp lại.
NOI_THANH_PEOPLE = ("Vinh", "Quý", "Hiệp")


def mixed_month():
    """Một tháng có đủ bốn hình dạng mà bảng phải phân biệt được.

    Cố ý dùng ĐÚNG tên trong `config/employees.yaml`: bài test này nói về
    thứ tự đọc lấy từ master, nên một cái tên bịa sẽ không chứng minh gì.
    """
    return [
        # Ba nhân viên `STANDARD_SALES` — mỗi người một hàng riêng.
        line("BH01", "Tủ lạnh", employee="Tín Phát", group="STANDARD_SALES",
             day=4, row=6, sell="9000000"),
        line("BH02", "Tivi", employee="Ly", group="STANDARD_SALES",
             day=5, row=7, sell="8000000"),
        line("BH03", "Máy giặt", employee="Kiên", group="STANDARD_SALES",
             day=6, row=8, sell="7000000"),
        # Ba người Nội thành — KHÔNG được có hàng riêng.
        line("BH04", "Điều hoà", employee="Vinh", group="NOI_THANH",
             day=7, row=9, sell="6000000"),
        line("BH05", "Bếp từ", employee="Quý", group="NOI_THANH",
             day=8, row=10, sell="5000000"),
        line("BH06", "Lò vi sóng", employee="Hiệp", group="NOI_THANH",
             day=9, row=11, sell="4000000"),
    ]


def month_with_work_left():
    """Cùng tháng đó nhưng CÒN một dòng chưa có giá nhập — tức là coverage
    chưa đủ, tức là danh sách "cần kiểm tra" có đúng một mục."""
    return [*mixed_month(),
            line("BH08", "Máy lọc nước", employee="Ly", group="STANDARD_SALES",
                 day=10, row=12, sell="3000000",
                 kpi_purchase=None, kpi_profit=None)]


def report(client, path="/kinh-doanh?ky=2026-09"):
    return body(client, path)


def code_cells(html: str) -> list[str]:
    """Nhãn của cột đầu tiên trong bảng "Theo nhân viên", theo đúng thứ tự."""
    table = re.search(r"<h2>Theo nhân viên.*?</table>", html, re.S).group(0)
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", cell)).strip()
            for cell in re.findall(r'<td class="code">(.*?)</td>', table, re.S)]


# ==========================================================================
# R1 — KỲ MỞ ĐẦU LÀ THÁNG HIỆN TẠI
# ==========================================================================

def test_r1_opening_the_report_tab_lands_on_the_current_month(
    repository, client
):
    """Mở `/kinh-doanh` không kèm tham số ⟹ tháng dương lịch hiện tại."""
    persist(repository, mixed_month())
    html = report(client, "/kinh-doanh")
    assert f"Tháng {TODAY.month:02d}/{TODAY.year}" in html
    assert re.search(
        r'<option value="2026-09"[^>]*selected', html), "kỳ hiện tại phải được chọn sẵn"
    # …và có SỐ ngay, không phải một trang chờ người dùng bấm.
    assert metric(html, "lines") == "6"


def test_r1_an_explicit_all_data_choice_is_never_overridden(repository, client):
    """`ky=` rỗng là Owner CHỦ ĐỘNG chọn "Toàn bộ dữ liệu" — mặc định lùi."""
    persist(repository, mixed_month())
    html = report(client, "/kinh-doanh?ky=")
    assert "Toàn bộ dữ liệu" in html
    assert f"Tháng {TODAY.month:02d}/{TODAY.year}" not in re.search(
        r"<h2>(.*?)</h2>", html, re.S).group(1)


def test_r1_the_user_can_still_move_to_another_month(repository, client):
    persist(repository, [*mixed_month(),
                         line("BH99", "Quạt", month=8, day=3, row=30)])
    html = report(client, "/kinh-doanh?ky=2026-08")
    assert "Tháng 08/2026" in html


def test_r1_a_month_with_no_data_does_not_open_on_an_empty_page(
    repository, client
):
    """Tháng hiện tại chưa có dòng nào ⟹ giữ hành vi cũ, vẫn có số để đọc."""
    persist(repository, [line("BH1", "Quạt", month=3, day=3)])
    html = report(client, "/kinh-doanh")
    assert "Toàn bộ dữ liệu" in html
    assert metric(html, "lines") == "1"


# ==========================================================================
# R2 · R4 — HÀNG CHỈ TIÊU
# ==========================================================================

def test_r2_the_four_headline_metrics_sit_in_one_row(repository, client):
    persist(repository, mixed_month())
    html = report(client)
    row = re.search(r'<div class="kpi-row">(.*?)\n  </div>', html, re.S).group(1)
    for name in ("sales_revenue", "qualifying_quantity", "kpi_profit",
                 "converted_sales"):
        assert f'data-metric="{name}"' in row, name
    assert row.count('class="kpi-card') == 4
    # Doanh thu vẫn đọc trước, nhưng KHÔNG còn là một dải riêng phía trên.
    assert "kpi-strong" in row
    assert 'class="kpi-hero"' not in html


def test_r4_every_headline_metric_explains_itself_behind_a_question_mark(
    repository, client
):
    """Định nghĩa KHÔNG bị xoá khỏi hệ thống — nó hiện khi rê chuột/lia bàn
    phím tới biểu tượng (?), không cần bấm vào đâu (`TASK-OWNER-UIUX-002` R2)."""
    persist(repository, mixed_month())
    html = report(client)
    row = re.search(r'<div class="kpi-row">(.*?)\n  </div>', html, re.S).group(1)
    assert row.count('class="kpi-help"') == 4
    helps = re.findall(r'class="kpi-help-tip" data-metric="kpi-help">(.*?)</span>',
                       html, re.S)
    assert len(helps) >= 4
    assert any("ĐƠN GIÁ BÁN" in text for text in helps)        # Tổng số SP
    assert any("tỉ lệ quy đổi" in text for text in helps)      # DS quy đổi
    # Không `<details>`, không bấm: `tabindex` lo phần lia bàn phím, và
    # không một dòng JavaScript nào cần cho việc này.
    assert "<script" not in html
    assert 'class="kpi-help" tabindex="0"' in html


# ==========================================================================
# R5 · R6 — BIỂU ĐỒ
# ==========================================================================

def test_r5_the_revenue_chart_is_a_line(repository, client):
    persist(repository, mixed_month())
    html = report(client)
    assert "<polyline" in html and 'class="rev-line-path"' in html
    assert 'class="rev-bar' not in html
    # Mỗi mốc vẫn đọc được bằng máy y như thời biểu đồ cột.
    assert html.count('data-metric="chart-bar"') >= 2
    assert re.search(r'data-metric="chart-bar"[^>]*data-revenue="\d', html)


def test_r6_the_chart_opens_on_the_day_grain(repository, client):
    persist(repository, mixed_month())
    html = report(client)
    assert re.search(r'data-metric="chart"[^>]*data-gran="ngay"', html)
    assert re.search(r'class="ghost btn-mini on"\s+data-gran="ngay"', html)


def test_r6_the_other_grains_still_work(repository, client):
    persist(repository, mixed_month())
    html = report(client, "/kinh-doanh?ky=2026-09&muc=thang")
    assert re.search(r'data-metric="chart"[^>]*data-gran="thang"', html)


def test_r6_the_day_default_is_a_page_choice_not_a_module_change():
    """Mặc định của module KHÔNG đổi — chỉ trang Báo cáo tự chọn NGÀY."""
    assert revenue_timeline.DEFAULT_GRANULARITY == revenue_timeline.MONTH
    assert revenue_timeline.parse_granularity(None) == revenue_timeline.MONTH
    assert revenue_timeline.parse_granularity(
        None, default=revenue_timeline.DAY) == revenue_timeline.DAY
    assert revenue_timeline.parse_granularity(
        "khong-co-that", default="cung-khong-co-that"
    ) == revenue_timeline.MONTH


# ==========================================================================
# R7 · R8 — CẦN KIỂM TRA
# ==========================================================================

def test_r7_the_pending_block_sits_at_the_bottom(repository, client):
    persist(repository, month_with_work_left())
    html = report(client)
    assert html.index('data-metric="pending"') > html.index("Theo nhân viên")
    assert html.index('data-metric="pending"') > html.index("Xu hướng doanh thu")
    # Hai thẻ lớn cũ không còn chen giữa các chỉ tiêu.
    assert "<h2>Cần soi trước khi tin vào tổng" not in html
    assert "Đã tính được lợi nhuận cho bao nhiêu dòng?" not in html


def test_r8_the_coverage_advisory_keeps_its_own_numbers_and_action(
    repository, client
):
    """Logic coverage KHÔNG đổi: cùng con số, cùng đường dẫn, chỉ khác chỗ."""
    persist(repository, month_with_work_left())
    html = report(client)
    item = re.search(r'data-code="coverage".*?</details>', html, re.S).group(0)
    assert 'data-severity="warn"' in item
    # Con số coverage trong mục này là ĐÚNG con số của khối cũ: 6 / 7 dòng.
    assert "6 / 7 dòng" in item
    assert "/kinh-doanh/gia-nhap" in item and "thieu-gia" in item


def test_r8_a_clean_period_reports_nothing_to_inspect(repository, client):
    persist(repository, mixed_month())
    html = report(client)
    assert 'data-metric="pending-empty"' in html
    assert 'data-metric="pending-item"' not in html


def test_r8_a_true_error_state_is_not_hidden_inside_pending(
    repository, client
):
    """Dòng thiếu ngày bán là một tình trạng SAI — nó giữ khối đỏ riêng."""
    persist(repository, [*mixed_month(),
                         line("BH07", "Nồi cơm", day=1, row=20)])
    html = report(client, "/kinh-doanh?ky=2026-09")
    assert 'data-metric="undated-lines"' in html
    undated = re.search(r'data-metric="undated-lines"[^>]*>(.*?)</p>', html, re.S)
    assert undated is not None


# ==========================================================================
# R9 … R16 — BẢNG "THEO NHÂN VIÊN"
# ==========================================================================

def test_r9_the_section_is_still_called_theo_nhan_vien(repository, client):
    persist(repository, mixed_month())
    html = report(client)
    assert "<h2>Theo nhân viên" in html
    for renamed in ("Theo đơn vị báo cáo", "Reporting unit", "Business unit"):
        assert renamed not in html


def test_r10_tin_phat_reads_first(repository, client):
    persist(repository, mixed_month())
    assert code_cells(report(client))[0] == "Tín Phát"


def test_r11_every_other_employee_keeps_their_own_name(repository, client):
    persist(repository, mixed_month())
    cells = code_cells(report(client))
    assert "Ly" in cells and "Kiên" in cells


def test_r12_and_r13_noi_thanh_is_one_row_and_its_members_have_none(
    repository, client
):
    persist(repository, mixed_month())
    cells = code_cells(report(client))
    for person in NOI_THANH_PEOPLE:
        assert person not in cells, person
    assert cells.count("Nội thành") == 1


def test_r14_gia_dung_is_the_last_row_before_the_total(repository, client):
    persist(repository, mixed_month())
    cells = code_cells(report(client))
    assert cells[-1] == "TỔNG"
    assert cells[-2] == "Gia dụng"


def test_the_group_rows_are_present_even_when_they_have_no_lines(
    repository, client
):
    """R13/R14 đúng KHÔNG điều kiện — kể cả tháng chưa có dòng Nội thành nào."""
    persist(repository, [line("BH1", "Tủ lạnh", employee="Ly",
                              group="STANDARD_SALES")])
    cells = code_cells(report(client))
    assert cells.count("Nội thành") == 1
    assert cells[-2] == "Gia dụng"


def test_a_noi_thanh_line_reaches_the_noi_thanh_row_not_an_employee_row(
    repository, client
):
    persist(repository, mixed_month())
    html = report(client)
    table = re.search(r"<h2>Theo nhân viên.*?</table>", html, re.S).group(0)
    row = re.search(r"<tr[^>]*>(?:(?!</tr>).)*?Nội thành.*?</tr>", table, re.S).group(0)
    revenue = re.search(r'data-metric="sales_revenue"[^>]*>([^<]+)<', row).group(1)
    # 6.000.000 + 5.000.000 + 4.000.000 = 15.000.000 đồng ⟹ 15.000 nghìn đồng
    assert revenue.strip() == "15.000"


def test_the_noi_thanh_row_opens_the_noi_thanh_sheet(repository, client):
    """Bấm vào hàng nhóm phải mở ĐÚNG sheet nhóm, không phải sheet một người."""
    persist(repository, mixed_month())
    html = report(client)
    assert re.search(r'href="[^"]*sheet=noi-thanh"[^>]*data-metric="unit-row"', html)


def test_the_employee_identity_of_a_noi_thanh_line_is_never_lost(
    repository, client
):
    """`DEC-127` §1 — gộp để ĐỌC, không phải để xoá tên ba con người."""
    persist(repository, mixed_month())
    workspace = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    for person in NOI_THANH_PEOPLE:
        assert person in workspace, person


# ==========================================================================
# R15 · R16 · R17 — ĐỐI SOÁT: KHÔNG THIẾU, KHÔNG ĐẾM HAI LẦN
# ==========================================================================

def _kvnd(text: str) -> Decimal:
    return Decimal(text.replace(".", "").replace("—", "0") or "0")


def test_r15_r16_r17_the_displayed_rows_sum_to_the_official_total(
    repository, client, service
):
    """Bất biến `§42` đọc trên chính HTML mà Owner nhìn thấy."""
    persist(repository, mixed_month())
    html = report(client)
    table = re.search(r"<h2>Theo nhân viên.*?</table>", html, re.S).group(0)
    rows = re.findall(r"<tr[^>]*>.*?</tr>", table, re.S)[1:]  # bỏ hàng tiêu đề

    displayed, total_row = Decimal(0), None
    for row in rows:
        value = _kvnd(re.search(
            r'data-metric="sales_revenue"[^>]*>([^<]+)<', row).group(1).strip())
        if "row-total" in row:
            total_row = value
        else:
            displayed += value

    assert total_row is not None
    assert displayed == total_row, "các hàng cộng lại phải đúng bằng hàng TỔNG"

    # …và hàng TỔNG đúng bằng tổng CHÍNH THỨC của kỳ, đọc từ tầng nghiệp vụ.
    data = service.period(date_from=None, date_to=None)
    official = bm.totals(data.lines).sales_revenue / Decimal(1000)
    assert total_row == official.quantize(Decimal("1"))


def test_the_partition_holds_for_every_additive_metric(repository, client, service):
    """Không chỉ doanh thu: mọi chỉ tiêu CỘNG ĐƯỢC đều khép kín theo sheet."""
    from app.modules.reporting import reporting_sheets

    persist(repository, mixed_month())
    data = service.period(date_from=None, date_to=None)
    sheets = reporting_sheets.sheets_for(data.sheet_assignments())
    parts = [data.for_sheet(sheet).totals for sheet in sheets]

    # Sheet RỖNG trả `None` chứ không phải 0 — "chưa tính được" khác "bằng
    # không", và bảng hiện `—` đúng như vậy. Phép cộng bỏ qua các ô đó.
    def added(field):
        return sum((value for value in (getattr(part, field) for part in parts)
                    if value is not None), Decimal(0))

    assert sum(part.lines for part in parts) == data.totals.lines
    assert added("sales_revenue") == data.totals.sales_revenue
    assert added("qualifying_quantity") == data.totals.qualifying_quantity


def test_no_line_is_counted_twice_across_the_displayed_rows(
    repository, client, service
):
    """Đếm DÒNG, chỗ mà một phép gộp trùng sẽ lộ ra ngay lập tức."""
    persist(repository, mixed_month())
    html = report(client)
    table = re.search(r"<h2>Theo nhân viên.*?</table>", html, re.S).group(0)
    rows = re.findall(r"<tr[^>]*>.*?</tr>", table, re.S)[1:]
    coverage = [re.search(r'data-metric="coverage"[^>]*>([^<]+)<', row).group(1)
                for row in rows]
    per_row = [int(text.split("/")[1].split("dòng")[0].strip())
               for text in coverage[:-1]]
    whole = int(coverage[-1].split("/")[1].split("dòng")[0].strip())
    assert sum(per_row) == whole == 6
