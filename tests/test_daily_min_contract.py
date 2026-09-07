"""Hợp đồng `daily-min-v1` ở tầng ĐỌC: ảnh chụp, biên file, provider (R1).

Bộ này canh những chỗ mà một lỗi KHÔNG hiện ra thành ngoại lệ mà hiện ra thành
một con số tiền trông hoàn toàn bình thường:

1. `min_price = null` không bao giờ trở thành `0`.
2. Nghìn VND → VND quy đổi ĐÚNG MỘT LẦN.
3. Ngày bán quyết định giá; không có nhánh nào lấy giá của ngày khác.
4. Một hợp đồng ở phiên bản lạ bị TỪ CHỐI, không đọc một phần rồi bỏ phần còn
   lại.
5. "Chưa hỏi" / "đã hỏi và không có" / "hôm ấy không quan sát được" là ba câu
   khác nhau và không bao giờ được gộp.

Bộ vertical (`tests/test_daily_min_vertical.py`) canh cùng những tính chất ấy
trên đường production thật, với dữ liệu do CHÍNH mã Tracking sinh ra.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.modules.domain.models import PRICE_SOURCE_TRACKING_DAILY_MIN
from app.modules.pricing.daily_min import (
    DailyMinCaptureFailedError,
    DailyMinStatus,
    DailyMinUnresolvedReason,
    DayStatus,
    InvalidDailyMinCaptureFileError,
    InvalidDailyMinSnapshotError,
    MissingReason,
    PriceStatus,
    SUPPORTED_CURRENCY_UNIT,
    SUPPORTED_SCHEMA_VERSION,
    SourceType,
    THOUSAND_VND_TO_VND,
    TrackingDailyMinProvider,
    UnsupportedDailyMinSchemaError,
    load_daily_min_capture,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
)
from app.modules.product.identity.keys import raw_identity_key
from tests.support import daily_min_fixtures as dmin

SALE_DAY = date(2026, 9, 3)
NEXT_DAY = date(2026, 9, 4)
RAW_NAME = "Máy giặt TRK-A"


def snapshot(tmp_path: Path, data=None, **kwargs):
    """Luôn đi qua ĐÚNG loader production, không dựng thẳng dataclass."""
    return load_daily_min_capture(dmin.write_capture(tmp_path, data, **kwargs))


def provider(tmp_path: Path, data=None, *, code="TRK-A", namespace=Namespace.TRACKING,
             raw=RAW_NAME, **kwargs):
    identity = CanonicalProductIdentity(namespace=namespace, source_product_code=code)
    return TrackingDailyMinProvider(
        snapshot(tmp_path, data, **kwargs),
        identity_index={raw_identity_key(raw): identity},
    )


# ======================================================================
# 1. Ngày bán quyết định giá — ngày chạy báo cáo không tham gia
# ======================================================================


def test_sale_date_picks_its_own_day_not_a_later_one(tmp_path):
    """Bán 03/09, giá đổi 04/09, chạy báo cáo sau đó: vẫn phải là giá 03/09.

    Đây là toàn bộ lý do capability này tồn tại. Một phép "lấy bản mới nhất"
    ở đây vẫn trả về một số tiền hợp lệ, vẫn xuất ra một báo cáo đẹp, và vẫn
    sai — sai đúng ở phần không ai nhìn thấy.
    """
    p = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-05",
        records=[
            dmin.record("TRK-A", "2026-09-03", min_price=6800),
            dmin.record("TRK-A", "2026-09-04", min_price=6000),
            dmin.record("TRK-A", "2026-09-05", min_price=6000,
                        observed_on="2026-09-04", carried_from="2026-09-04"),
        ],
    ))
    assert p.resolve(RAW_NAME, SALE_DAY).price_vnd == Decimal("6800000")
    assert p.resolve(RAW_NAME, NEXT_DAY).price_vnd == Decimal("6000000")


def test_a_carried_mark_says_so_instead_of_pretending_to_be_its_own_day(tmp_path):
    """Mốc mang qua vẫn dùng được, nhưng phải NÓI RA là mang qua.

    Gộp `observed_on` vào `effective_date` sẽ giấu mất phép suy: người kiểm mở
    ngày 05/09 sẽ tưởng Tracking đã quan sát một thay đổi hôm ấy.
    """
    p = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-05",
        records=[dmin.record("TRK-A", "2026-09-05", min_price=6000,
                             observed_on="2026-09-04", carried_from="2026-09-04")],
    ))
    prov = p.resolve(RAW_NAME, date(2026, 9, 5)).provenance
    assert prov.observed_on == date(2026, 9, 4)
    assert prov.carried_from == date(2026, 9, 4)


def test_a_day_outside_the_captured_window_is_not_a_conclusion_about_price(tmp_path):
    """Ngoài khoảng đã chụp ≠ "mặt hàng không có giá".

    Hai câu ấy dẫn tới hai việc khác nhau: chụp lại rộng hơn, hay đi tìm hiểu
    dữ liệu. Một mã lý do chung sẽ bảo người ta làm sai việc.
    """
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record("TRK-A", "2026-09-03", min_price=6800)],
    )).resolve(RAW_NAME, date(2026, 9, 10))
    assert r.reason is DailyMinUnresolvedReason.SALE_DATE_OUTSIDE_CAPTURE
    assert r.price_vnd is None


def test_a_pair_missing_from_both_blocks_is_an_unbalanced_capture(tmp_path):
    """Hợp đồng cam kết mỗi cặp đã hỏi nằm ở `records` HOẶC `errors`.

    Không ở đâu cả nghĩa là mã ấy chưa được hỏi trong lần chụp — và đọc nó
    thành "không có giá" là để một lỗi phạm vi capture phát biểu thay cho dữ
    liệu.
    """
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03", records=[],
    )).resolve(RAW_NAME, SALE_DAY)
    assert r.reason is DailyMinUnresolvedReason.NOT_IN_CAPTURE


# ======================================================================
# 2. Không có giá — và không cảnh nào thành 0
# ======================================================================


@pytest.mark.parametrize(
    "price_status, expected",
    [
        ("OUT_OF_STOCK", DailyMinUnresolvedReason.OUT_OF_STOCK),
        ("NO_DATA", DailyMinUnresolvedReason.NO_DATA),
    ],
)
def test_a_priceless_day_is_pending_with_its_own_reason(tmp_path, price_status, expected):
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record("TRK-A", "2026-09-03", price_status=price_status)],
    )).resolve(RAW_NAME, SALE_DAY)
    assert r.status is DailyMinStatus.PENDING
    assert r.reason is expected
    assert r.price_vnd is None


@pytest.mark.parametrize(
    "reason, expected",
    [
        ("NO_DATA", DailyMinUnresolvedReason.TRACKING_NO_DATA),
        ("SOURCE_UNAVAILABLE", DailyMinUnresolvedReason.TRACKING_SOURCE_UNAVAILABLE),
        ("INVALID_PRODUCT_CODE",
         DailyMinUnresolvedReason.TRACKING_INVALID_PRODUCT_CODE),
    ],
)
def test_every_contract_error_reason_maps_to_exactly_one_reports_reason(
    tmp_path, reason, expected
):
    """Bảng ánh xạ TOÀN PHẦN — không lý do nào của Tracking rơi vào hư không."""
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        errors=[dmin.error("TRK-A", "2026-09-03", reason)],
    )).resolve(RAW_NAME, SALE_DAY)
    assert r.reason is expected


def test_the_reason_map_covers_the_whole_closed_contract_enum():
    """Một mã hợp đồng mới mà quên ánh xạ sẽ nổ `KeyError` giữa lúc định giá.

    Bài này bắt nó ở đây, nơi sửa mất một dòng, thay vì ở đó.
    """
    from app.modules.pricing.daily_min.provider import _LY_DO_THEO_HOP_DONG

    assert set(_LY_DO_THEO_HOP_DONG) == set(MissingReason)


def test_a_zero_price_is_refused_at_load_time(tmp_path):
    """`AVAILABLE` với giá 0 không phải một giá — nó là một mâu thuẫn.

    Chặn ngay lúc nạp: để nó đi tiếp thì lợi nhuận của dòng ấy bằng đúng doanh
    thu, và con số đó cộng vào KPI mà không có gì đỏ lên.
    """
    with pytest.raises(InvalidDailyMinSnapshotError) as exc:
        snapshot(tmp_path, dmin.contract(
            records=[dmin.record("TRK-A", "2026-09-03", min_price=0)],
        ))
    assert exc.value.reason == "available_without_price"


def test_a_priced_out_of_stock_record_is_refused_at_load_time(tmp_path):
    with pytest.raises(InvalidDailyMinSnapshotError) as exc:
        snapshot(tmp_path, dmin.contract(
            records=[dmin.record("TRK-A", "2026-09-03", min_price=6800,
                                 price_status="OUT_OF_STOCK")],
        ))
    assert exc.value.reason == "missing_status_with_price"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True])
def test_a_non_price_never_becomes_a_price(tmp_path, bad):
    """`NaN`/vô cực lọt qua mọi phép so sánh rồi đi thẳng vào một phép nhân;
    `True` là `int` trong Python nên nó sẽ lặng lẽ thành giá 1 nghìn đồng.
    Tiền lệ `TASK-105B-RC-1` đã vá đúng lớp lỗi này một lần rồi."""
    payload = dmin.contract(records=[dmin.record("TRK-A", "2026-09-03", min_price=1)])
    payload["records"][0]["min_price"] = bad
    path = Path(tmp_path) / "bad.json"
    # `json.dumps` phát ra literal `NaN`/`Infinity` và `json.loads` nhận lại
    # chúng — nên file này là ĐÚNG thứ một hợp đồng lỗi có thể gửi tới, không
    # phải một tình huống chỉ dựng được trong bộ nhớ.
    path.write_text(
        json.dumps(
            {
                "capture_id": dmin.CAPTURE_ID,
                "captured_at": "2026-09-30T12:00:00+00:00",
                "captured_by": dmin.CAPTURED_BY,
                "source_system_ref": dmin.SOURCE_SYSTEM_REF,
                "capture_status": "COMPLETE",
                "data": payload,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with pytest.raises(InvalidDailyMinSnapshotError):
        load_daily_min_capture(path)


# ======================================================================
# 3. Đơn vị tiền — quy đổi đúng một lần
# ======================================================================


def test_the_thousand_to_vnd_conversion_happens_exactly_once(tmp_path):
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record("TRK-A", "2026-09-03", min_price=6800)],
    )).resolve(RAW_NAME, SALE_DAY)
    assert r.price_vnd == Decimal("6800") * THOUSAND_VND_TO_VND
    # Cả hai con số cùng có mặt trong provenance: người đọc THẤY phép quy đổi
    # đã xảy ra, không phải tin rằng nó đã xảy ra.
    assert r.provenance.raw_value_thousand_vnd == Decimal("6800")
    assert r.provenance.resolved_price_vnd == Decimal("6800000")
    assert "1000" in r.provenance.unit_conversion


def test_the_conversion_constant_appears_exactly_once_in_the_package():
    """Hai chỗ nhân 1000 là hai chỗ để quên một chỗ — và quên một chỗ là sai
    đúng 1.000 lần, sai đều nên nhìn bảng không phát hiện ra."""
    package = Path("app/modules/pricing/daily_min")
    uses = [
        (path.name, line.strip())
        for path in package.glob("*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
        if "THOUSAND_VND_TO_VND" in line
        and "import" not in line
        and not line.strip().startswith(('"', "#", "*"))
        and '"' not in line.split("THOUSAND_VND_TO_VND")[0]
    ]
    multiplications = [u for u in uses if "*" in u[1]]
    assert len(multiplications) == 1, multiplications


def test_an_unknown_currency_unit_is_refused(tmp_path):
    """Đơn vị tiền là thứ KHÔNG được đoán."""
    with pytest.raises(InvalidDailyMinSnapshotError) as exc:
        snapshot(tmp_path, dmin.contract(currency_unit="VND"))
    assert exc.value.reason == "unsupported_currency_unit"


def test_a_record_may_not_carry_a_currency_unit_of_its_own(tmp_path):
    payload = dmin.contract(records=[dmin.record("TRK-A", "2026-09-03", min_price=1)])
    payload["records"][0]["currency_unit"] = "VND"
    with pytest.raises(InvalidDailyMinSnapshotError) as exc:
        snapshot(tmp_path, payload)
    assert exc.value.reason == "unsupported_currency_unit"


# ======================================================================
# 4. Phiên bản hợp đồng — từ chối, không đọc bừa
# ======================================================================


def test_an_unsupported_schema_is_refused_not_partially_read(tmp_path):
    with pytest.raises(UnsupportedDailyMinSchemaError):
        snapshot(tmp_path, dmin.contract(schema_version="daily-min-v2"))


def test_a_record_may_not_carry_a_schema_of_its_own(tmp_path):
    payload = dmin.contract(records=[dmin.record("TRK-A", "2026-09-03", min_price=1)])
    payload["records"][0]["schema_version"] = "daily-min-v9"
    with pytest.raises(UnsupportedDailyMinSchemaError):
        snapshot(tmp_path, payload)


@pytest.mark.parametrize(
    "field, value",
    [("price_status", "MAYBE"), ("day_status", "DRAFT"),
     ("min_sources", [{"source_type": "MAGIC", "source_id": "x"}])],
)
def test_every_enum_is_closed_at_load_time(tmp_path, field, value):
    """Một giá trị lạ đến từ một phiên bản Reports chưa hiểu. "Bỏ qua thứ không
    hiểu" trong một luồng định giá nghĩa là im lặng đánh rơi đúng những dòng
    mới nhất."""
    payload = dmin.contract(records=[dmin.record("TRK-A", "2026-09-03", min_price=1)])
    payload["records"][0][field] = value
    with pytest.raises(InvalidDailyMinSnapshotError):
        snapshot(tmp_path, payload)


def test_two_answers_for_one_question_are_refused(tmp_path):
    """Trùng (mã, ngày), hoặc vừa có bản ghi vừa có lỗi — chọn hộ một cái là
    đoán."""
    with pytest.raises(InvalidDailyMinSnapshotError) as exc:
        snapshot(tmp_path, dmin.contract(records=[
            dmin.record("TRK-A", "2026-09-03", min_price=1),
            dmin.record("TRK-A", "2026-09-03", min_price=2),
        ]))
    assert exc.value.reason == "duplicate_record"

    with pytest.raises(InvalidDailyMinSnapshotError) as exc:
        snapshot(tmp_path, dmin.contract(
            records=[dmin.record("TRK-A", "2026-09-03", min_price=1)],
            errors=[dmin.error("TRK-A", "2026-09-03", "NO_DATA")],
        ))
    assert exc.value.reason == "record_and_error_conflict"


# ======================================================================
# 5. Ba trạng thái nguồn — vắng mặt / hỏng / FAILED, không được gộp
# ======================================================================


def test_a_missing_file_is_absence_not_an_error(tmp_path):
    assert load_daily_min_capture(tmp_path / "chua-chup-lan-nao.json") is None


def test_a_corrupt_file_is_a_load_error_not_an_empty_source(tmp_path):
    bad = tmp_path / "hong.json"
    bad.write_text("{ khong phai json", encoding="utf-8")
    with pytest.raises(InvalidDailyMinCaptureFileError):
        load_daily_min_capture(bad)


def test_a_failed_capture_explodes_when_someone_builds_a_provider(tmp_path):
    """`INV-12` — một lần capture hỏng và một khoảng thời gian thật sự không có
    giá là hai sự kiện khác nhau."""
    snap = snapshot(tmp_path, capture_status="FAILED", failure_reason="mat-mang")
    with pytest.raises(DailyMinCaptureFailedError):
        TrackingDailyMinProvider(snap, identity_index={})


# ======================================================================
# 6. Identity — provider ĐƯỢC TRAO, không tự suy ra
# ======================================================================


def test_an_unresolved_name_never_guesses_a_code(tmp_path):
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record("TRK-A", "2026-09-03", min_price=6800)],
    )).resolve("Một tên hàng chưa ai phân loại", SALE_DAY)
    assert r.reason is DailyMinUnresolvedReason.IDENTITY_UNRESOLVED
    assert r.provenance.product_code is None


def test_a_public_purchase_identity_never_borrows_a_tracking_price(tmp_path):
    """`INV-18` — một mã trùng chuỗi ở hai namespace là hai identity khác nhau.

    Ảnh chụp CÓ đúng chuỗi `TRK-A`, nhưng identity thuộc `PUBLIC_PURCHASE`;
    trả giá ở đây là để một mã của hệ khác mượn giá vốn của Tracking.
    """
    r = provider(
        tmp_path,
        dmin.contract(
            date_from="2026-09-03", date_to="2026-09-03",
            records=[dmin.record("TRK-A", "2026-09-03", min_price=6800)],
        ),
        namespace=Namespace.PUBLIC_PURCHASE,
    ).resolve(RAW_NAME, SALE_DAY)
    assert r.reason is DailyMinUnresolvedReason.IDENTITY_NOT_TRACKING
    assert r.price_vnd is None


def test_a_line_without_a_sale_date_has_no_day_to_ask_about(tmp_path):
    r = provider(tmp_path).resolve(RAW_NAME, None)
    assert r.reason is DailyMinUnresolvedReason.SALE_DATE_MISSING


# ======================================================================
# 7. Provenance — đủ để mở lại, kể cả trên dòng Pending
# ======================================================================


def test_provenance_carries_sources_revision_and_rule_version(tmp_path):
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record(
            "TRK-A", "2026-09-03", min_price=6800,
            min_sources=[dmin.supplier("Tuấn Ngoan"), dmin.inventory()],
            revision="R-2026-09-03-abc", source_fingerprint="abc",
        )],
    )).resolve(RAW_NAME, SALE_DAY)
    prov = r.provenance
    assert prov.min_sources == ("SUPPLIER:Tuấn Ngoan", "INVENTORY:TON_KHO")
    assert prov.revision == "R-2026-09-03-abc"
    assert prov.rule_version == "min-1"
    assert prov.source_fingerprint == "abc"
    assert prov.capture_id == dmin.CAPTURE_ID
    assert prov.recorded_at == datetime(2026, 9, 5, 4, tzinfo=timezone.utc)


def test_a_pending_line_still_says_which_record_tracking_answered_with(tmp_path):
    """Câu hỏi người kiểm hỏi về một dòng KHÔNG có giá là "Tracking đã nói gì,
    ở bản ghi nào" — và không có mấy trường này thì không trả lời được."""
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record("TRK-A", "2026-09-03", price_status="OUT_OF_STOCK",
                             revision="R-het-hang")],
    )).resolve(RAW_NAME, SALE_DAY)
    assert not r.is_resolved
    assert r.provenance.revision == "R-het-hang"
    assert r.provenance.price_status is PriceStatus.OUT_OF_STOCK


def test_the_audit_trail_keeps_every_lookup_including_the_pending_ones(tmp_path):
    p = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record("TRK-A", "2026-09-03", min_price=6800)],
    ))
    p.resolve(RAW_NAME, SALE_DAY)
    p.resolve("tên lạ", SALE_DAY)
    assert len(p.audit_trail) == 2
    assert [r.is_resolved for r in p.audit_trail] == [True, False]


def test_the_provider_labels_its_own_source_and_not_the_history_one(tmp_path):
    """Nhãn nguồn là thứ người kiểm dùng để quyết có tin con số hay không."""
    assert TrackingDailyMinProvider.price_source == PRICE_SOURCE_TRACKING_DAILY_MIN
    assert TrackingDailyMinProvider.price_source != "TRACKING_PRICE_HISTORY"


# ======================================================================
# 8. PROVISIONAL — dùng được, nhưng trạng thái đi cùng con số
# ======================================================================


def test_a_provisional_day_still_gives_a_price_but_keeps_saying_it_is_provisional(
    tmp_path,
):
    """Bắt người ta chờ hết ngày mới xem được báo cáo là vô ích; giấu mất việc
    con số còn có thể đổi thì tệ hơn nhiều."""
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record("TRK-A", "2026-09-03", min_price=6800,
                             day_status="PROVISIONAL")],
    )).resolve(RAW_NAME, SALE_DAY)
    assert r.price_vnd == Decimal("6800000")
    assert r.is_provisional
    assert r.provenance.day_status is DayStatus.PROVISIONAL


def test_a_final_day_is_not_provisional(tmp_path):
    r = provider(tmp_path, dmin.contract(
        date_from="2026-09-03", date_to="2026-09-03",
        records=[dmin.record("TRK-A", "2026-09-03", min_price=6800,
                             day_status="FINAL")],
    )).resolve(RAW_NAME, SALE_DAY)
    assert not r.is_provisional
    assert r.provenance.day_status is DayStatus.FINAL


# ======================================================================
# 9. Ranh giới đóng của các enum hợp đồng
# ======================================================================


def test_the_contract_constants_are_the_ones_tracking_publishes():
    assert SUPPORTED_SCHEMA_VERSION == "daily-min-v1"
    assert SUPPORTED_CURRENCY_UNIT == "VND_THOUSAND"
    assert {s.value for s in SourceType} == {"SUPPLIER", "INVENTORY"}
    assert {s.value for s in PriceStatus} == {"AVAILABLE", "OUT_OF_STOCK", "NO_DATA"}
    assert {s.value for s in DayStatus} == {"PROVISIONAL", "FINAL"}
