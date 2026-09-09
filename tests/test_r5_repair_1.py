"""R5 REPAIR-1 — hai finding `REPAIR_REQUIRED` của Independent Review.

Cả hai có CÙNG hình dạng, và đó là điều đáng ghi lại: R5 lấy một cơ chế đã
đúng ở ngữ cảnh cũ và đặt nó vào một ngữ cảnh nơi cái giá của sai lầm khác
hẳn — nhưng không tính lại chiều an toàn của nó.

`FIND-R5-IR-01`  ô chọn nhân viên cố ý KHÔNG có mục trống. Đúng khi nó còn
                 nút gửi RIÊNG (`GÁN CẢ ĐƠN`): mở form đó ra nghĩa là bạn
                 muốn gán. Sai khi R5 §4 cho nó đi cùng MỌI lần lưu — khi ấy
                 một BH không có nhân viên hiệu lực duy nhất làm trình duyệt
                 tự gửi option ĐẦU TIÊN, và cả đơn đổi chủ vì một cú bấm
                 `XONG` mà người dùng nghĩ là để lưu giá.

`FIND-R5-IR-02`  nhãn "còn hiệu lực" so mốc snapshot NGẶT (`>`), và mốc ấy
                 ghi ở độ phân giải GIÂY. Chú thích ngay tại chỗ đã nói rõ vì
                 sao ngặt là an toàn: *"Không con số nghiệp vụ nào phụ thuộc
                 vào nhãn này"*. R5 §1 làm nhãn ấy quyết định tổng tiền, và
                 câu đó thôi đúng — nhưng chiều an toàn không được tính lại.
                 Hai lần nạp trong cùng một giây (độ phân giải THẬT của
                 production) làm dòng bị tạm loại VĨNH VIỄN.

Cả hai bài dưới đây đi qua đúng đường production, không qua một hàm phụ:
bài 1 đọc HTML thật rồi gửi đúng cái form ấy; bài 2 dùng đúng mốc thời gian
mà đường ghi thật sinh ra, không truyền tay ba mốc cách nhau một ngày.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, history_store

from tests.test_employee_workspace_ux import (
    SEPTEMBER, body, line, persist, three_line_order,
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


def employees_of(service, order_key="BH72707") -> list:
    return sorted({detail["line"].employee
                   for detail in service.period(**SEPTEMBER).details
                   if detail["order_key"] == order_key},
                  key=lambda name: (name is None, name))


def open_edit(client, order="BH72707", sheet="noi-thanh") -> str:
    """Mở chế độ sửa của một BH trên ĐÚNG sheet chứa nó.

    Dòng chưa xác định nhân viên rơi vào sheet `chua-xac-dinh`, không phải
    `noi-thanh` — `reporting_sheets.sheet_key_of` là hàm toàn phần và nó
    phân hoạch theo nhân viên/nhóm, nên một BH vô chủ có sheet riêng.
    """
    return body(client,
                f"/kinh-doanh/nhan-vien?ky=2026-09&sheet={sheet}&sua={order}")


def price_fields(html: str) -> list:
    return re.findall(r'name="(gia_nhap__[^"]+)"', html)


def submit_as_browser_would(client, html: str, order="BH72707",
                            sheet="noi-thanh"):
    """Gửi form ĐÚNG như trình duyệt gửi nó.

    Đây là toàn bộ điểm của bài kiểm này. Một bài gửi `nhan_vien_moi=""` hay
    bỏ hẳn trường ấy sẽ XANH trên chính bản mã có lỗi: lỗi không nằm ở server,
    nó nằm ở chỗ HTML bảo trình duyệt gửi cái gì khi người dùng không đụng vào
    ô chọn. Trình duyệt gửi giá trị của option ĐANG ĐƯỢC CHỌN; không option
    nào mang `selected` thì nó gửi option ĐẦU TIÊN.
    """
    select = re.search(
        r'<select name="nhan_vien_moi".*?</select>', html, re.S)
    assert select is not None, "phải có ô chọn nhân viên trong chế độ sửa"
    options = re.findall(r'<option value="([^"]*)"([^>]*)>', select.group(0))
    chosen = next((value for value, attrs in options if "selected" in attrs),
                  options[0][0] if options else "")
    data = {"ky": "2026-09", "sheet": sheet, "order_key": order,
            "nhan_vien_moi": chosen}
    for name in price_fields(html):
        value = re.search(rf'name="{re.escape(name)}"\s+value="([^"]*)"', html)
        data[name] = value.group(1) if value else ""
    return client.post("/kinh-doanh/nhan-vien/sua-bh", data=data,
                       follow_redirects=True)


# --- FIND-R5-IR-01 -------------------------------------------------------

def test_saving_an_order_split_between_two_employees_reassigns_nobody(
    repository, service, client,
):
    """BH có HAI nhân viên hiệu lực: bấm `XONG` không được đổi chủ ai cả."""
    pairs = three_line_order()
    pairs[1] = line("BH72707", "XP352AE-DS", occurrence=1, day=5,
                    employee="Quý", row=7, sell="4000000",
                    kpi_purchase="2000000", kpi_profit="2000000")
    persist(repository, pairs)
    before = employees_of(service)
    assert before == ["Quý", "Vinh"], "fixture phải dựng đúng một BH chia đôi"

    submit_as_browser_would(client, open_edit(client))

    assert employees_of(service) == before, (
        "một cú bấm XONG để lưu giá KHÔNG được gán lại cả đơn cho ai")


def test_saving_an_order_with_no_employee_assigns_nobody(
    repository, service, client,
):
    """BH CHƯA có nhân viên: bấm `XONG` không được tự gán một cái tên."""
    persist(repository, [
        line("BH72707", "43F6000", day=5, employee=None, group=None),
    ])
    assert employees_of(service) == [None]

    submit_as_browser_would(
        client, open_edit(client, sheet="chua-xac-dinh"),
        sheet="chua-xac-dinh")

    assert employees_of(service) == [None], (
        "chưa xác định được ai bán thì XONG không được chọn hộ")


def test_every_employee_select_always_has_exactly_one_option_selected(
    repository, client,
):
    """Bất biến CẤU TRÚC, và là bất biến thật sự đóng cả lớp lỗi này.

    Một ô chọn đi cùng MỌI lần lưu phải LUÔN có đúng một option được chọn.
    Không option nào ⟹ trình duyệt tự chọn hộ, và nó chọn cái đầu tiên. Kiểm
    theo từng trường hợp dữ liệu sẽ bỏ sót trường hợp thứ ba ai đó thêm sau.
    """
    pairs = three_line_order()
    pairs[1] = line("BH72707", "XP352AE-DS", occurrence=1, day=5,
                    employee="Quý", row=7, sell="4000000")
    persist(repository, [
        *pairs,
        line("BH80000", "43F6000", day=6, employee=None, group=None),
        line("BH90000", "43F6000", day=7, employee="Vinh"),
    ])
    for order, sheet in (("BH72707", "noi-thanh"),
                         ("BH80000", "chua-xac-dinh"),
                         ("BH90000", "noi-thanh")):
        html = open_edit(client, order, sheet)
        select = re.search(r'<select name="nhan_vien_moi".*?</select>',
                           html, re.S)
        assert select is not None, order
        selected = re.findall(r'<option[^>]*\sselected', select.group(0))
        assert len(selected) == 1, (
            f"{order}: phải có ĐÚNG MỘT option được chọn, đang có "
            f"{len(selected)}")


def test_choosing_a_real_name_still_assigns_the_whole_order(
    repository, service, client,
):
    """Cửa vẫn mở: chọn một tên THẬT vẫn gán cả đơn như `§27` đã nghiệm thu."""
    pairs = three_line_order()
    pairs[1] = line("BH72707", "XP352AE-DS", occurrence=1, day=5,
                    employee="Quý", row=7, sell="4000000")
    persist(repository, pairs)
    html = open_edit(client)
    data = {"ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
            "nhan_vien_moi": "Hiệp"}
    for name in price_fields(html):
        data[name] = ""
    client.post("/kinh-doanh/nhan-vien/sua-bh", data=data,
                follow_redirects=True)
    assert employees_of(service) == ["Hiệp"]


# --- FIND-R5-IR-02 -------------------------------------------------------

def two_orders():
    return [
        line("BH1", "43F6000", day=5, sell="8000000"),
        line("BH2", "XP352AE-DS", day=6, sell="4000000"),
    ]


def test_a_line_that_comes_back_within_the_same_second_is_restored(
    repository, service,
):
    """Kịch bản production của `FIND-R5-IR-02`, dựng bằng đúng mốc thật.

    Ba lần ghi dùng `history_writer._now_iso()` — CHÍNH hàm mà đường nạp sổ
    production gọi — và chúng chạy liên tiếp nên rơi vào CÙNG MỘT GIÂY đồng
    hồ treo tường. Đó là điều kiện mà bài `test_a_line_that_comes_back_…_by_
    itself` hiện có không bao giờ chạm tới: nó truyền tay ba mốc cách nhau
    một ngày.

    Vòng đầy đủ phải chạy được: đủ → thiếu+xác nhận → đủ lại.
    """
    from app.web import history_writer

    pairs = two_orders()
    persist(repository, pairs, run_id="run-1", at=history_writer._now_iso(),
            fingerprint="fp-a")
    assert service.period(**SEPTEMBER).totals.sales_revenue == Decimal("12000000")

    second = persist(repository, pairs[:1], run_id="run-2",
                     at=history_writer._now_iso(), fingerprint="fp-b")
    repository.confirm_coverage(
        second.snapshot_id, start=date(2026, 9, 1), end=date(2026, 9, 30),
        confirmed=True, confirmed_at=history_writer._now_iso())
    dropped = service.period(**SEPTEMBER)
    assert dropped.totals.sales_revenue == Decimal("8000000"), (
        "sổ đã xác nhận đầy đủ vẫn phải tạm loại được dòng vắng")
    assert [row["order_key"] for row in dropped.removed_in_source] == ["BH2"]

    # Kế toán xuất lại sổ đủ — VẪN trong cùng một giây đồng hồ.
    persist(repository, pairs, run_id="run-3", at=history_writer._now_iso(),
            fingerprint="fp-c")

    restored = service.period(**SEPTEMBER)
    assert restored.totals.sales_revenue == Decimal("12000000"), (
        "dòng quay lại phải được khôi phục, kể cả khi ba lần nạp cùng giây")
    assert restored.removed_in_source == []


def test_the_three_ingests_of_that_scenario_really_share_one_wall_clock_second():
    """Đối chứng: không có nó, bài trên có thể xanh vì ba lần ghi tình cờ
    rơi vào ba giây khác nhau, và khi ấy nó không chứng minh gì."""
    from app.web import history_writer

    stamps = [history_writer._now_iso() for _ in range(3)]
    assert len({stamp[:19] for stamp in stamps}) == 1, (
        "ba lần đọc mốc liên tiếp phải nằm trong cùng một giây")
    assert len(set(stamps)) == 3, "…nhưng vẫn phân biệt được với nhau"


def test_the_write_path_records_a_timestamp_finer_than_one_second(repository):
    """Mốc quyết định tiền phải phân giải hơn một giây.

    Kiểm HÀNH VI của đường ghi thật, không grep mã nguồn: hai lần ghi liên
    tiếp phải cho ra hai mốc KHÁC NHAU. Ở `timespec="seconds"` chúng bằng
    nhau, và `_with_absence_state` khi ấy không phân giải nổi thứ tự của
    chính hai lần nạp mà người dùng vừa thực hiện.
    """
    from app.web import history_writer

    stamps = {history_writer._now_iso() for _ in range(50)}
    assert len(stamps) > 1, (
        "năm mươi lần đọc mốc liên tiếp ra cùng một giá trị — độ phân giải "
        "không đủ để xếp thứ tự hai lần nạp sổ")
    assert all("." in stamp for stamp in stamps), (
        "mốc phải mang phần thập phân của giây")


def test_an_older_snapshot_tied_on_the_same_second_keeps_the_money(
    repository, service,
):
    """Bản ghi CŨ (độ phân giải giây) không phân giải được thứ tự.

    Khi ấy hai cách sai không ngang giá: giữ cờ là TRỪ TIỀN của một dòng có
    thật, im lặng và vĩnh viễn; bỏ cờ là giữ tiền đúng như TRƯỚC R5, và
    người dùng thấy ngay vì câu xác nhận nói "đã tạm loại N dòng" trong khi
    tổng không đổi. Bài này khoá chiều đã chọn.
    """
    stamp = "2026-10-01T09:15:30+00:00"
    pairs = two_orders()
    persist(repository, pairs, run_id="run-1", at=stamp, fingerprint="fp-a")
    second = persist(repository, pairs[:1], run_id="run-2", at=stamp,
                     fingerprint="fp-b")
    repository.confirm_coverage(
        second.snapshot_id, start=date(2026, 9, 1), end=date(2026, 9, 30),
        confirmed=True, confirmed_at=stamp)

    assert service.period(**SEPTEMBER).totals.sales_revenue == Decimal("12000000")


def test_a_genuinely_older_snapshot_still_leaves_the_flag_active(
    repository, service,
):
    """Cửa KHÔNG bị mở toang: mốc CŨ HƠN HẲN vẫn là "chưa quay lại".

    Không có bài này thì `>=` không phân biệt được với "bỏ hẳn phép so", và
    R5 §1 sẽ mất luôn khả năng loại dòng.
    """
    pairs = two_orders()
    persist(repository, pairs, run_id="run-1", at="2026-10-01T09:00:00.000000+00:00",
            fingerprint="fp-a")
    second = persist(repository, pairs[:1], run_id="run-2",
                     at="2026-10-02T09:00:00.000000+00:00", fingerprint="fp-b")
    repository.confirm_coverage(
        second.snapshot_id, start=date(2026, 9, 1), end=date(2026, 9, 30),
        confirmed=True, confirmed_at="2026-10-02T09:00:01.000000+00:00")

    data = service.period(**SEPTEMBER)
    assert data.totals.sales_revenue == Decimal("8000000")
    assert [row["order_key"] for row in data.removed_in_source] == ["BH2"]
