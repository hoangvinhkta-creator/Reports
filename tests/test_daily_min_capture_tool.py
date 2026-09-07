"""Công cụ chụp `daily-min-v1`: đọc HẾT các trang, hoặc FAILED (R1).

Bộ này canh một chỗ mà lỗi không hiện ra thành ngoại lệ mà hiện ra thành một
ảnh chụp trông đầy đủ: **hai trang của hai trạng thái database khác nhau được
nối lại thành một**.

Con trỏ phân trang phía Tracking chỉ là vị trí trong danh sách mã đã sắp xếp —
nó KHÔNG đóng băng dữ liệu, và Firebase RTDB không có ảnh chụp đọc nhất quán
giữa nhiều lệnh đọc. Giữa trang 1 và trang 2 có thể xảy ra: một lượt cron chụp
thêm, một ngày chuyển `PROVISIONAL → FINAL`, hoặc một lệnh sửa ghi đè một bản
ghi cũ mà những ngày sau nó đang mang qua.

Năm trường phong bì cũ (`schema_version`, `currency_unit`, `business_timezone`,
`date_from`, `date_to`) KHÔNG bắt được cảnh ấy: chúng chỉ lặp lại yêu cầu vừa
gửi đi, nên chúng khớp nhau kể cả khi dữ liệu bên dưới đã đổi hoàn toàn.
`query_revision` là trường duy nhất nói về TRẠNG THÁI, và Tracking đổi nó sau
mọi lượt ghi vào các nhánh MIN theo ngày.
"""

from __future__ import annotations

import pytest

from tools.tracking.capture_daily_min import (
    SCHEMA_VERSION,
    TRAN_TRANG,
    TRUONG_CHUNG_KHOANG,
    TRUONG_PHONG_BI,
    build_capture,
    gop_khoang,
    gop_trang,
)
from tools.tracking.capture_purchase_price_history import CaptureError

REV = "rev-0001"


def page(*, records=(), errors=(), cursor=None, revision=REV, **overrides):
    """Một trang đúng hình dạng `xuatMinNgay()` trả về."""
    body = {
        "schema_version": SCHEMA_VERSION,
        "business_timezone": "Asia/Ho_Chi_Minh",
        "currency_unit": "VND_THOUSAND",
        "date_from": "2026-09-03",
        "date_to": "2026-09-03",
        "generated_at": "2026-09-30T12:00:00+00:00",
        "query_revision": revision,
        "records": list(records),
        "errors": list(errors),
        "next_cursor": cursor,
    }
    body.update(overrides)
    return body


def rec(code):
    return {"product_code": code, "effective_date": "2026-09-03"}


def capture(poster):
    return build_capture(
        poster,
        product_codes=["A", "B"],
        date_from="2026-09-03",
        date_to="2026-09-03",
        capture_id="DMIN-TEST",
        captured_by="kiem",
        source_system_ref="tracking/api/min-ngay",
    )


# ======================================================================
# 1. Gộp trang — chỉ khi các trang thật sự là một
# ======================================================================


def test_pages_of_one_state_merge_into_one_envelope():
    merged = gop_trang([
        page(records=[rec("A")], cursor="1"),
        page(records=[rec("B")]),
    ])
    assert [r["product_code"] for r in merged["records"]] == ["A", "B"]
    assert merged["pages"] == 2
    assert merged["query_revision"] == REV


def test_a_revision_that_changed_between_pages_refuses_the_merge():
    """Ca trung tâm của bộ này: mọi trường cũ khớp, chỉ trạng thái đã đổi."""
    with pytest.raises(CaptureError) as exc:
        gop_trang([
            page(records=[rec("A")], cursor="1"),
            page(records=[rec("B")], revision="rev-0002"),
        ])
    assert "query_revision" in str(exc.value)


def test_a_first_page_without_a_revision_refuses_the_merge():
    """Không có gì để so thì không chứng minh được gì — từ chối, chứ không
    coi 'thiếu' là 'khớp'."""
    with pytest.raises(CaptureError) as exc:
        gop_trang([page(records=[rec("A")], query_revision=None)])
    assert "query_revision" in str(exc.value)


@pytest.mark.parametrize("value", ["", "   "])
def test_a_blank_revision_is_not_a_revision(value):
    with pytest.raises(CaptureError):
        gop_trang([page(revision=value)])


def test_the_revision_is_part_of_the_envelope_contract():
    assert "query_revision" in TRUONG_PHONG_BI


@pytest.mark.parametrize("field", [f for f in TRUONG_PHONG_BI])
def test_every_envelope_field_must_match_across_pages(field):
    with pytest.raises(CaptureError) as exc:
        gop_trang([page(cursor="1"), page(**{field: "khac"})])
    assert field in str(exc.value)


# ======================================================================
# 2. Đường chụp thật — lỗi thành FAILED đọc lại được, không phải traceback
# ======================================================================


def test_a_mid_capture_revision_change_produces_a_failed_capture():
    """Đây là hình dạng lỗi mà người vận hành THẬT SỰ gặp: một lượt cron chạy
    đúng lúc công cụ đang đọc trang 2. Kết quả phải là một artifact FAILED đọc
    lại được (`INV-12`), không phải một file capture trông đầy đủ."""
    pages = iter([
        page(records=[rec("A")], cursor="1"),
        page(records=[rec("B")], revision="rev-0002"),
    ])

    envelope = capture(lambda body: next(pages))
    assert envelope["capture_status"] == "FAILED"
    assert "query_revision" in envelope["failure_reason"]
    assert "data" not in envelope


def test_a_clean_two_page_capture_is_complete():
    pages = iter([page(records=[rec("A")], cursor="1"), page(records=[rec("B")])])
    envelope = capture(lambda body: next(pages))
    assert envelope["capture_status"] == "COMPLETE"
    assert envelope["data"]["pages"] == 2
    assert envelope["data"]["query_revision"] == REV


def test_the_cursor_is_sent_back_verbatim():
    seen: list[object] = []

    def post(body):
        seen.append(body.get("cursor"))
        return page(cursor="7") if len(seen) == 1 else page()

    capture(post)
    assert seen == [None, "7"]


def test_an_endless_cursor_stops_as_a_named_failure():
    envelope = capture(lambda body: page(cursor="9"))
    assert envelope["capture_status"] == "FAILED"
    assert str(TRAN_TRANG) in envelope["failure_reason"]


def test_a_contract_refusal_is_not_read_as_an_empty_period():
    envelope = capture(lambda body: {"ok": False, "ly": "khoang-ngay-qua-dai"})
    assert envelope["capture_status"] == "FAILED"
    assert "khoang-ngay-qua-dai" in envelope["failure_reason"]


# ======================================================================
# 3. Gộp nhiều ĐOẠN NGÀY — chỉ khi cùng một trạng thái
# ======================================================================
#
# Hợp đồng có trần 62 ngày mỗi lượt, nên một kỳ rộng hơn phải hỏi làm nhiều
# lượt. Bỏ qua lượt hỏi giá vì kỳ quá rộng thì lần chạy vẫn ra một báo cáo —
# đầy đủ hình thức, không một giá vốn nào, và trông y hệt một báo cáo bình
# thường. Nên phải chia và gộp; nhưng gộp CHỈ hợp lệ khi database không đổi
# giữa các lượt.


def part(*, date_from, date_to, records=(), errors=(), revision=REV, **overrides):
    body = {
        "schema_version": SCHEMA_VERSION,
        "business_timezone": "Asia/Ho_Chi_Minh",
        "currency_unit": "VND_THOUSAND",
        "date_from": date_from,
        "date_to": date_to,
        "generated_at": "2026-09-30T12:00:00+00:00",
        "query_revision": revision,
        "pages": 1,
        "records": list(records),
        "errors": list(errors),
    }
    body.update(overrides)
    return body


def test_windows_of_one_state_merge_into_the_whole_period():
    merged = gop_khoang([
        part(date_from="2026-01-01", date_to="2026-03-03",
             records=[{"product_code": "A", "effective_date": "2026-01-05"}]),
        part(date_from="2026-03-04", date_to="2026-05-04",
             records=[{"product_code": "A", "effective_date": "2026-04-01"}]),
    ])
    assert (merged["date_from"], merged["date_to"]) == ("2026-01-01", "2026-05-04")
    assert len(merged["records"]) == 2
    assert merged["windows"] == 2
    assert merged["query_revision"] == REV


def test_windows_of_two_states_are_refused():
    """Ca trung tâm: mỗi đoạn tự nó hợp lệ, chỉ trạng thái đã đổi giữa chúng."""
    with pytest.raises(CaptureError) as exc:
        gop_khoang([
            part(date_from="2026-01-01", date_to="2026-03-03"),
            part(date_from="2026-03-04", date_to="2026-05-04", revision="rev-0002"),
        ])
    assert "query_revision" in str(exc.value)


@pytest.mark.parametrize("field", ["schema_version", "currency_unit",
                                   "business_timezone", "query_revision"])
def test_every_shared_field_must_match_across_windows(field):
    with pytest.raises(CaptureError) as exc:
        gop_khoang([
            part(date_from="2026-01-01", date_to="2026-03-03"),
            part(date_from="2026-03-04", date_to="2026-05-04", **{field: "khac"}),
        ])
    assert field in str(exc.value)


def test_the_date_range_is_never_part_of_the_shared_fields():
    """Khác `gop_trang`: các đoạn CỐ Ý khác khoảng ngày — đó là lý do có nhiều
    đoạn. Nhầm hai danh sách này thì hoặc không gộp được gì, hoặc gộp cả những
    thứ không nên gộp."""
    assert "date_from" not in TRUONG_CHUNG_KHOANG
    assert "date_to" not in TRUONG_CHUNG_KHOANG
    assert "date_from" in TRUONG_PHONG_BI


@pytest.mark.parametrize("value", [None, "", "   "])
def test_a_window_without_a_revision_is_refused(value):
    with pytest.raises(CaptureError):
        gop_khoang([part(date_from="2026-01-01", date_to="2026-03-03",
                         query_revision=value)])


def test_merging_nothing_is_an_error_not_an_empty_period():
    with pytest.raises(CaptureError):
        gop_khoang([])
