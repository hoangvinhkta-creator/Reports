"""Reports History Reader V1 — focused tests.

Mọi test ở đây trả lời đúng một câu: **khi nào reader được phép trả một con
số, và khi nào nó BẮT BUỘC phải từ chối**. Không test nào ở đây đo độ phủ —
độ phủ không phải mục tiêu của capability này, `SILENT_ERROR_RATE = 0` mới
là.

Mốc cutover dùng đúng thời điểm production đã đóng (`29/08/2026 19:35:37`
giờ Việt Nam = `12:35:37Z`), vì các bài kiểm biên chỉ có ý nghĩa khi biên là
biên thật.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.modules.pricing.tracking_history import (
    DecisiveSource,
    InvalidTrackingPriceSnapshotError,
    ReconstructionStatus,
    SaleInterval,
    TimestampAuthority,
    TrackingHistoryPriceProvider,
    TrackingPriceHistoryReader,
    TrackingPriceHistorySnapshot,
    UnresolvedReason,
)
from app.modules.pricing.tracking_history.snapshot import (
    CaptureStatus,
    TrackingCaptureFailedError,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
)

VN = timezone(timedelta(hours=7))
"""Múi giờ nghiệp vụ. Việt Nam UTC+7, không có DST — nên một ngày lịch là một
khoảng 24 giờ liền, không có ngày 23 hay 25 giờ."""

CUTOVER = datetime(2026, 8, 29, 12, 35, 37, tzinfo=timezone.utc)
"""Production: Firebase server time 29/08/2026 19:35:37 (UTC+7)."""

CUTOVER_MS = int(CUTOVER.timestamp() * 1000)


def _ms(moment: datetime) -> int:
    return int(moment.timestamp() * 1000)


def build_export(
    *,
    prices: dict[str, float] | None = None,
    events: dict[str, dict[str, dict]] | None = None,
    n_absent: int = 0,
    n_invalid: int = 0,
    baseline_t: int | None = None,
    with_baseline: bool = True,
) -> dict:
    """Dựng đúng hình dạng export RTDB mà công cụ capture sẽ ghi ra."""
    data: dict = {}
    if with_baseline:
        prices = prices or {}
        data["purchase_price_baseline"] = {
            "cutover": {
                "t": CUTOVER_MS if baseline_t is None else baseline_t,
                "by": "admin@tinphat",
                "src": "cutover_snapshot",
                "n": len(prices) + n_absent + n_invalid,
                "nCap": len(prices),
                "nAbsent": n_absent,
                "nInvalid": n_invalid,
                "prices": prices,
            }
        }
    if events:
        data["purchase_price_history"] = events
    return data


def event(
    *,
    prev: float | None,
    nxt: float | None,
    at: datetime,
    authority: str | None = "SERVER",
) -> dict:
    node = {"prev": prev, "next": nxt, "t": _ms(at), "by": "u@tinphat", "src": "sync"}
    if authority is not None:
        node["ta"] = authority
    return node


def build_reader(
    export: dict, *, captured_at: datetime = CUTOVER + timedelta(days=30)
) -> TrackingPriceHistoryReader:
    snapshot = TrackingPriceHistorySnapshot.from_export(
        export,
        capture_id="cap-001",
        captured_at=captured_at,
        captured_by="reports-capture-tool",
        source_system_ref="tracking/rtdb",
    )
    return TrackingPriceHistoryReader(snapshot)


def sale_on(day: date) -> SaleInterval:
    return SaleInterval.for_sale_date(day, VN)


# ===================================================================== §12.1
# "sale trước baseline → Pending"


def test_sale_before_cutover_is_pending_never_a_price():
    reader = build_reader(build_export(prices={"A1": 7000}))
    out = reader.price_at("A1", sale_on(date(2026, 8, 20)))
    assert out.status is ReconstructionStatus.PENDING
    assert out.reason is UnresolvedReason.SALE_BEFORE_CUTOVER
    assert out.price_vnd is None


def test_sale_day_straddling_the_cutover_instant_is_pending():
    """Ngày 29/08 chứa CẢ phần trước lẫn phần sau `19:35:37`.

    Reports chỉ biết ngày, không biết giờ. Nếu chọn "cả ngày là sau cutover"
    thì một đơn bán buổi sáng nhận giá của mốc chiều — đúng kiểu sai lặng lẽ
    mà capability này tồn tại để chặn.
    """
    reader = build_reader(build_export(prices={"A1": 7000}))
    out = reader.price_at("A1", sale_on(date(2026, 8, 29)))
    assert out.reason is UnresolvedReason.SALE_BEFORE_CUTOVER


# ===================================================================== §12.2
# "sale đúng baseline → deterministic" + §12.3 "baseline price được resolve"


def test_sale_exactly_at_cutover_instant_resolves_from_baseline():
    """Biên chính xác `sale_time == baseline.t`: mốc CÓ hiệu lực tại chính nó."""
    reader = build_reader(build_export(prices={"A1": 7000}))
    out = reader.price_at("A1", SaleInterval.at_instant(CUTOVER))
    assert out.status is ReconstructionStatus.RESOLVED
    assert out.price_vnd == Decimal("7000000")
    assert out.provenance.decisive_source is DecisiveSource.BASELINE
    assert out.provenance.decisive_source_timestamp == CUTOVER
    assert (
        out.provenance.baseline_timestamp_authority is TimestampAuthority.SERVER
    )


def test_one_microsecond_before_cutover_is_pending_not_a_price():
    """Cùng một mã, lệch một mili-giây, đổi hẳn kết luận — và phải như thế."""
    reader = build_reader(build_export(prices={"A1": 7000}))
    just_before = CUTOVER - timedelta(milliseconds=1)
    out = reader.price_at("A1", SaleInterval.at_instant(just_before))
    assert out.reason is UnresolvedReason.SALE_BEFORE_CUTOVER


def test_baseline_price_resolves_for_a_full_day_after_cutover():
    reader = build_reader(build_export(prices={"A1": 7000}))
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.is_resolved
    assert out.price_vnd == Decimal("7000000")
    assert out.provenance.decisive_source is DecisiveSource.BASELINE
    assert out.provenance.decisive_event_id is None


def test_capture_predating_the_sale_interval_is_pending_never_a_price():
    interval = sale_on(date(2026, 9, 5))
    reader = build_reader(
        build_export(prices={"A1": 7000}),
        captured_at=interval.lo - timedelta(microseconds=1),
    )

    out = reader.price_at("A1", interval)

    assert out.status is ReconstructionStatus.PENDING
    assert out.reason is UnresolvedReason.SNAPSHOT_DOES_NOT_COVER_SALE_INTERVAL
    assert out.price_vnd is None


def test_stale_baseline_is_not_extrapolated_through_sale_interval():
    interval = sale_on(date(2026, 9, 5))
    reader = build_reader(
        build_export(prices={"A1": 7000}), captured_at=interval.lo
    )

    out = reader.price_at("A1", interval)

    assert out.reason is UnresolvedReason.SNAPSHOT_DOES_NOT_COVER_SALE_INTERVAL
    assert out.price_vnd is None


def test_stale_terminal_history_event_is_not_extrapolated_through_sale_interval():
    interval = sale_on(date(2026, 9, 5))
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(
                        prev=7000,
                        nxt=6800,
                        at=interval.lo - timedelta(hours=1),
                    )
                }
            },
        ),
        captured_at=interval.lo,
    )

    out = reader.price_at("A1", interval)

    assert out.reason is UnresolvedReason.SNAPSHOT_DOES_NOT_COVER_SALE_INTERVAL
    assert out.price_vnd is None


def test_capture_at_sale_interval_end_preserves_valid_resolution():
    interval = sale_on(date(2026, 9, 5))
    reader = build_reader(
        build_export(prices={"A1": 7000}), captured_at=interval.hi
    )

    out = reader.price_at("A1", interval)

    assert out.is_resolved
    assert out.price_vnd == Decimal("7000000")


# ===================================================================== §12.4
# "history change trước sale → new price"


def test_event_before_the_sale_supersedes_the_baseline():
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(
                        prev=7000, nxt=6800, at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc)
                    )
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.is_resolved
    assert out.price_vnd == Decimal("6800000")
    assert out.provenance.decisive_source is DecisiveSource.HISTORY_EVENT
    assert out.provenance.decisive_event_id == "E1"


def test_events_apply_in_temporal_order_last_state_wins():
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    # Cố ý đưa vào theo thứ tự ĐẢO so với thời gian: kết quả
                    # phải do dấu thời gian quyết định, không do thứ tự dòng.
                    "E2": event(prev=6800, nxt=6500,
                                at=datetime(2026, 9, 3, 4, tzinfo=timezone.utc)),
                    "E1": event(prev=7000, nxt=6800,
                                at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc)),
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 10)))
    assert out.is_resolved
    assert out.price_vnd == Decimal("6500000")
    assert out.provenance.decisive_event_id == "E2"


# ===================================================================== §12.5
# "history change sau sale → không ảnh hưởng"


def test_event_after_the_sale_does_not_change_the_answer():
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=6800,
                                at=datetime(2026, 9, 20, 3, tzinfo=timezone.utc))
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.is_resolved
    assert out.price_vnd == Decimal("7000000")
    assert out.provenance.decisive_source is DecisiveSource.BASELINE


def test_a_later_event_confirms_the_state_held_through_the_sale():
    """`prev` của sự kiện SAU khoảng bán là bằng chứng xác nhận, không phải nhiễu."""
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    # prev = 9999 != 7000 -> đã có một lần đổi giá KHÔNG đi qua
                    # lịch sử, ở đâu đó trước sự kiện này — có thể ngay trong
                    # ngày bán.
                    "E1": event(prev=9999, nxt=6800,
                                at=datetime(2026, 9, 20, 3, tzinfo=timezone.utc))
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.HISTORY_CHAIN_INCONSISTENT


def test_a_chain_break_beyond_the_confirming_event_does_not_poison_an_earlier_sale():
    """Phạm vi khoá chuỗi cắt đúng bằng phạm vi ảnh hưởng.

    `E2` (20/09) xác nhận trạng thái đã giữ nguyên xuyên qua ngày bán 12/09,
    nên chuỗi cho đơn ấy đã đóng. `E3` gãy vào tháng 12 nói về một khoảng
    KHÁC — nó không được kéo một đơn tháng 9 đã có bằng chứng đầy đủ sang
    Pending.
    """
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=6800,
                                at=datetime(2026, 9, 10, 3, tzinfo=timezone.utc)),
                    "E2": event(prev=6800, nxt=6500,
                                at=datetime(2026, 9, 20, 3, tzinfo=timezone.utc)),
                    # Gãy chuỗi ở tháng 12, SAU sự kiện xác nhận.
                    "E3": event(prev=1234, nxt=6000,
                                at=datetime(2026, 12, 1, 3, tzinfo=timezone.utc)),
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 12)))
    assert out.is_resolved
    assert out.price_vnd == Decimal("6800000")


def test_a_chain_break_at_the_first_event_after_the_sale_does_poison_it():
    """Mặt kia của cùng một luật — và là mặt quan trọng hơn.

    Nếu sự kiện đầu tiên SAU ngày bán khai một `prev` khác trạng thái dựng
    được thì lần đổi giá ngoài sổ đã xảy ra ở đâu đó trong khoảng chứa CẢ
    ngày bán. Không có bằng chứng nào loại nó ra, nên đơn ấy phải Pending.
    """
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=6800,
                                at=datetime(2026, 9, 10, 3, tzinfo=timezone.utc)),
                    "E2": event(prev=1234, nxt=6000,
                                at=datetime(2026, 12, 1, 3, tzinfo=timezone.utc)),
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 12)))
    assert out.reason is UnresolvedReason.HISTORY_CHAIN_INCONSISTENT


# ===================================================================== §12.6
# "clear next=null → Pending"


def test_cleared_price_is_pending_never_the_old_price_and_never_zero():
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=None,
                                at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc))
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.PRICE_CLEARED
    assert out.price_vnd is None
    assert out.provenance.decisive_event_id == "E1"
    assert out.provenance.resolved_price_vnd is None


def test_price_restored_after_a_clear_resolves_again():
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=None,
                                at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc)),
                    "E2": event(prev=None, nxt=6600,
                                at=datetime(2026, 9, 4, 3, tzinfo=timezone.utc)),
                }
            },
        )
    )
    assert reader.price_at("A1", sale_on(date(2026, 9, 3))).reason is (
        UnresolvedReason.PRICE_CLEARED
    )
    later = reader.price_at("A1", sale_on(date(2026, 9, 6)))
    assert later.is_resolved
    assert later.price_vnd == Decimal("6600000")


# ===================================================================== §12.7
# "product absent baseline → không fake price"


def test_product_absent_from_baseline_never_gets_an_invented_price():
    reader = build_reader(build_export(prices={"A1": 7000}, n_absent=3100))
    out = reader.price_at("KHONG_CO", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.NO_BASELINE_PRICE_AT_CUTOVER
    assert out.price_vnd is None


def test_absent_product_becomes_resolvable_only_from_its_first_event(
):
    """CASE E — trước sự kiện đầu tiên KHÔNG suy diễn, sau đó thì được."""
    first = datetime(2026, 9, 10, 3, tzinfo=timezone.utc)
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            n_absent=1,
            events={"MOI": {"E1": event(prev=None, nxt=5500, at=first)}},
        )
    )
    before = reader.price_at("MOI", sale_on(date(2026, 9, 5)))
    assert before.reason is UnresolvedReason.NO_BASELINE_PRICE_AT_CUTOVER

    after = reader.price_at("MOI", sale_on(date(2026, 9, 15)))
    assert after.is_resolved
    assert after.price_vnd == Decimal("5500000")
    assert after.provenance.decisive_event_id == "E1"


def test_absent_product_is_ambiguous_when_the_baseline_skipped_invalid_prices():
    """`nInvalid > 0` làm "vắng mặt" không còn phân biệt được với "giá hỏng"."""
    reader = build_reader(
        build_export(prices={"A1": 7000}, n_absent=10, n_invalid=3)
    )
    out = reader.price_at("KHAC", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.BASELINE_ABSENCE_AMBIGUOUS


# ===================================================================== §12.8
# "history provenance không authoritative → Pending"


def test_client_timestamped_event_is_never_authoritative():
    """Sự kiện lịch sử V1 (`Date.now()` máy trạm) — thiếu nhãn `ta`."""
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=6800,
                                at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc),
                                authority=None)
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.HISTORY_PROVENANCE_NOT_AUTHORITATIVE
    assert out.price_vnd is None


@pytest.mark.parametrize("marker", ["CLIENT", "server", "", "SERVER_ISH", True, 1])
def test_only_the_exact_server_marker_grants_authority(marker):
    """Allow-list: mọi giá trị khác `"SERVER"` rơi về phía an toàn."""
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=6800,
                                at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc),
                                authority=marker)
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.HISTORY_PROVENANCE_NOT_AUTHORITATIVE


def test_one_unverified_event_poisons_the_whole_code_even_if_it_claims_a_past_date():
    """Dấu thời gian máy trạm không bị chặn — nó có thể ở BẤT KỲ đâu thật sự.

    Sự kiện dưới đây *khai* mình xảy ra trước cutover, nghĩa là nó trông như
    đã bị baseline thay thế và vô hại. Nhưng chính lời khai ấy là thứ không
    tin được, nên nó vẫn phải làm mã này Pending.
    """
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=6000, nxt=7000,
                                at=CUTOVER - timedelta(days=40), authority=None)
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.HISTORY_PROVENANCE_NOT_AUTHORITATIVE


def test_old_events_are_not_retro_upgraded_by_the_presence_of_new_ones():
    """Một mã có cả sự kiện cũ lẫn mới KHÔNG được "kéo" thẩm quyền sang."""
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "OLD": event(prev=7000, nxt=6900,
                                 at=datetime(2026, 9, 1, 3, tzinfo=timezone.utc),
                                 authority=None),
                    "NEW": event(prev=6900, nxt=6800,
                                 at=datetime(2026, 9, 3, 3, tzinfo=timezone.utc)),
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 10)))
    assert out.reason is UnresolvedReason.HISTORY_PROVENANCE_NOT_AUTHORITATIVE


def test_baseline_authority_is_read_from_the_snapshot_not_assumed():
    reader = build_reader(build_export(prices={"A1": 7000}))
    assert (
        reader.snapshot.baseline.timestamp_authority is TimestampAuthority.SERVER
    )


# ===================================================================== §12.9
# "Tracking thousand VND → Reports VND đúng"


@pytest.mark.parametrize(
    "thousand,expected_vnd",
    [(7000, "7000000"), (6800, "6800000"), (1, "1000"), (0, "0"), (12345, "12345000")],
)
def test_unit_conversion_is_exactly_times_one_thousand(thousand, expected_vnd):
    reader = build_reader(build_export(prices={"A1": thousand}))
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.is_resolved
    assert out.price_vnd == Decimal(expected_vnd)
    # Provenance phải CHỨA cả hai vế của phép quy đổi, không chỉ kết quả.
    assert out.provenance.raw_value_thousand_vnd == Decimal(str(thousand))
    assert out.provenance.unit_conversion == "thousand_VND × 1000 → VND"


def test_conversion_keeps_decimal_precision_no_float_anywhere():
    reader = build_reader(build_export(prices={"A1": 6250.5}))
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.price_vnd == Decimal("6250500")
    assert isinstance(out.price_vnd, Decimal)


# ==================================================================== BIÊN
# Ngữ nghĩa biên chính xác (brief §6)


def test_event_exactly_at_the_start_of_the_sale_interval_is_applied():
    """`event.t == interval.lo` — sự kiện có hiệu lực TẠI chính thời điểm nó."""
    start = datetime(2026, 9, 5, 0, 0, tzinfo=VN)
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={"A1": {"E1": event(prev=7000, nxt=6800, at=start)}},
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.is_resolved
    assert out.price_vnd == Decimal("6800000")


def test_event_exactly_at_the_open_end_of_the_interval_is_not_applied():
    """`hi` là đầu MỞ: một sự kiện lúc 00:00 hôm sau thuộc về hôm sau."""
    end = datetime(2026, 9, 6, 0, 0, tzinfo=VN)
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={"A1": {"E1": event(prev=7000, nxt=6800, at=end)}},
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.is_resolved
    assert out.price_vnd == Decimal("7000000")
    assert reader.price_at("A1", sale_on(date(2026, 9, 6))).price_vnd == Decimal(
        "6800000"
    )


def test_price_change_inside_the_sale_day_is_pending_not_a_guess():
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=6800,
                                at=datetime(2026, 9, 5, 14, 30, tzinfo=VN))
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.PRICE_CHANGED_WITHIN_SALE_INTERVAL
    assert out.price_vnd is None


def test_a_known_instant_inside_that_same_day_resolves_deterministically():
    """Nếu caller BIẾT giờ bán thì cùng dữ liệu ấy lại quyết định được.

    Chứng minh Pending ở test trên là do ĐỘ PHÂN GIẢI của Reports, không phải
    do dữ liệu Tracking thiếu.
    """
    change = datetime(2026, 9, 5, 14, 30, tzinfo=VN)
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={"A1": {"E1": event(prev=7000, nxt=6800, at=change)}},
        )
    )
    morning = reader.price_at(
        "A1", SaleInterval.at_instant(datetime(2026, 9, 5, 9, 0, tzinfo=VN))
    )
    evening = reader.price_at(
        "A1", SaleInterval.at_instant(datetime(2026, 9, 5, 18, 0, tzinfo=VN))
    )
    assert morning.price_vnd == Decimal("7000000")
    assert evening.price_vnd == Decimal("6800000")


def test_event_exactly_at_the_cutover_instant_is_pending():
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={"A1": {"E1": event(prev=6900, nxt=7000, at=CUTOVER)}},
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.EVENT_AT_CUTOVER_INSTANT


def test_two_events_sharing_a_timestamp_are_non_deterministic():
    same = datetime(2026, 9, 2, 3, tzinfo=timezone.utc)
    reader = build_reader(
        build_export(
            prices={"A1": 7000},
            events={
                "A1": {
                    "E1": event(prev=7000, nxt=6800, at=same),
                    "E2": event(prev=6800, nxt=6500, at=same),
                }
            },
        )
    )
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.NON_DETERMINISTIC_EVENT_ORDER


def test_same_timestamp_on_two_different_codes_is_fine():
    """Một lượt sync ghi nhiều mã cùng lúc — bình thường, không nhập nhằng."""
    same = datetime(2026, 9, 2, 3, tzinfo=timezone.utc)
    reader = build_reader(
        build_export(
            prices={"A1": 7000, "B1": 5000},
            events={
                "A1": {"E1": event(prev=7000, nxt=6800, at=same)},
                "B1": {"E2": event(prev=5000, nxt=4800, at=same)},
            },
        )
    )
    assert reader.price_at("A1", sale_on(date(2026, 9, 5))).price_vnd == Decimal(
        "6800000"
    )
    assert reader.price_at("B1", sale_on(date(2026, 9, 5))).price_vnd == Decimal(
        "4800000"
    )


def test_sale_interval_rejects_naive_datetimes():
    with pytest.raises(ValueError, match="AWARE"):
        SaleInterval.at_instant(datetime(2026, 9, 5, 9, 0))


def test_for_sale_date_requires_an_explicit_business_timezone():
    with pytest.raises(TypeError):
        SaleInterval.for_sale_date(date(2026, 9, 5))  # type: ignore[call-arg]


# ============================================================== ẢNH CHỤP


def test_failed_capture_is_a_hard_error_never_a_pending():
    """`INV-12` — một lần capture hỏng KHÔNG được đọc thành "không có dữ liệu"."""
    snapshot = TrackingPriceHistorySnapshot.from_export(
        {},
        capture_id="cap-bad",
        captured_at=CUTOVER,
        captured_by="tool",
        source_system_ref="tracking/rtdb",
        capture_status=CaptureStatus.FAILED,
        failure_reason="mất mạng giữa chừng",
    )
    with pytest.raises(TrackingCaptureFailedError):
        TrackingPriceHistoryReader(snapshot)


def test_snapshot_without_baseline_is_pending_not_a_crash():
    reader = build_reader(build_export(with_baseline=False))
    out = reader.price_at("A1", sale_on(date(2026, 9, 5)))
    assert out.reason is UnresolvedReason.SNAPSHOT_HAS_NO_BASELINE


def test_baseline_counters_must_agree_or_the_snapshot_refuses_to_load():
    export = build_export(prices={"A1": 7000})
    export["purchase_price_baseline"]["cutover"]["n"] = 99
    with pytest.raises(InvalidTrackingPriceSnapshotError) as exc:
        build_reader(export)
    assert exc.value.reason == "counter_mismatch"


def test_negative_price_in_the_snapshot_refuses_to_load():
    with pytest.raises(InvalidTrackingPriceSnapshotError) as exc:
        build_reader(build_export(prices={"A1": -1}))
    assert exc.value.reason == "negative_price"


@pytest.mark.parametrize("location", ["baseline", "event"])
def test_epoch_seconds_are_rejected_not_silently_interpreted_as_1970(location):
    """A seconds timestamp must not make a post-cutover change disappear.

    The source contract is Firebase epoch *milliseconds*. Parsing a plausible
    seconds value as milliseconds moves it into 1970; the reader would then
    discard the event as pre-cutover and incorrectly return the baseline.
    """
    export = build_export(
        prices={"A1": 7000},
        events={
            "A1": {
                "E1": event(
                    prev=7000,
                    nxt=6800,
                    at=datetime(2026, 9, 2, 3, tzinfo=timezone.utc),
                )
            }
        },
    )
    if location == "baseline":
        export["purchase_price_baseline"]["cutover"]["t"] = CUTOVER_MS // 1000
    else:
        export["purchase_price_history"]["A1"]["E1"]["t"] = _ms(
            datetime(2026, 9, 2, 3, tzinfo=timezone.utc)
        ) // 1000

    with pytest.raises(InvalidTrackingPriceSnapshotError) as exc:
        build_reader(export)
    assert exc.value.reason == "invalid_timestamp_unit"


def test_production_cutover_counters_load_exactly():
    """Đúng các con số production đã công bố: 3441 / 341 / 3100 / 0."""
    prices = {f"MA{i:04d}": 1000 + i for i in range(341)}
    reader = build_reader(build_export(prices=prices, n_absent=3100, n_invalid=0))
    baseline = reader.snapshot.baseline
    assert (baseline.codes_checked, baseline.n_captured) == (3441, 341)
    assert (baseline.n_absent, baseline.n_invalid) == (3100, 0)
    assert baseline.has_invalid_entries is False


# ==================================================================== §12.10
# "identity không phải TRACKING → reader không hijack"


def _provider(index):
    return TrackingHistoryPriceProvider(
        build_reader(build_export(prices={"A1": 7000})),
        identity_index=index,
        business_tz=VN,
    )


def test_public_purchase_identity_is_never_served_by_the_tracking_reader():
    provider = _provider(
        {"Máy giặt X": CanonicalProductIdentity(Namespace.PUBLIC_PURCHASE, "A1")}
    )
    out = provider.resolve("Máy giặt X", date(2026, 9, 5))
    assert out.reason is UnresolvedReason.IDENTITY_NOT_TRACKING
    assert out.price_vnd is None
    # Dù mã trùng chuỗi với một mã CÓ giá trong baseline.
    assert provider.lookup("Máy giặt X", date(2026, 9, 5)) is None


def test_tracking_identity_is_served():
    provider = _provider(
        {"Máy giặt X": CanonicalProductIdentity(Namespace.TRACKING, "A1")}
    )
    assert provider.lookup("Máy giặt X", date(2026, 9, 5)) == Decimal("7000000")


def test_provider_never_infers_a_tracking_code_from_the_raw_product_name():
    """Tên hàng trùng khít một mã Tracking vẫn KHÔNG được tự nhận."""
    provider = _provider({})
    out = provider.resolve("A1", date(2026, 9, 5))
    assert out.reason is UnresolvedReason.IDENTITY_UNRESOLVED
    assert out.provenance.product_code is None
    assert out.provenance.raw_product_identity == "A1"


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_provider_pending_when_the_line_has_no_product_name(raw):
    """Tên hàng rỗng KHÔNG sinh một khoá rỗng gộp mọi dòng thiếu tên (`INV-30`)."""
    provider = _provider(
        {"Máy giặt X": CanonicalProductIdentity(Namespace.TRACKING, "A1")}
    )
    out = provider.resolve(raw, date(2026, 9, 5))
    assert out.reason is UnresolvedReason.IDENTITY_UNRESOLVED
    assert out.price_vnd is None


def test_provider_pending_when_the_line_has_no_sale_date():
    provider = _provider(
        {"Máy giặt X": CanonicalProductIdentity(Namespace.TRACKING, "A1")}
    )
    out = provider.resolve("Máy giặt X", None)
    assert out.reason is UnresolvedReason.SALE_DATE_MISSING


def test_provider_records_provenance_for_every_lookup_including_pending():
    provider = _provider(
        {"Máy giặt X": CanonicalProductIdentity(Namespace.TRACKING, "A1")}
    )
    provider.lookup("Máy giặt X", date(2026, 9, 5))
    provider.lookup("Không rõ", date(2026, 9, 5))
    trail = provider.audit_trail
    assert len(trail) == 2
    assert trail[0].is_resolved and trail[0].provenance.product_code == "A1"
    assert trail[1].reason is UnresolvedReason.IDENTITY_UNRESOLVED
    # Không có kết quả nào là một con số trần: mọi phần tử đều mang provenance.
    assert all(r.provenance is not None for r in trail)


def test_resolved_result_never_carries_a_reason_and_pending_never_a_price():
    """Bất biến kiểu — kiểm ở `__post_init__`, không chỉ hứa trong tài liệu."""
    from app.modules.pricing.tracking_history.reader import (
        PriceReconstruction,
        TrackingPriceProvenance,
    )

    prov = TrackingPriceProvenance(
        product_code="A1",
        namespace="TRACKING",
        sale_interval_start=CUTOVER,
        sale_interval_end=CUTOVER,
        snapshot_capture_id="cap",
        baseline_cutover_id="cutover",
        baseline_captured_at=CUTOVER,
        baseline_timestamp_authority=TimestampAuthority.SERVER,
        decisive_source=DecisiveSource.BASELINE,
    )
    with pytest.raises(ValueError):
        PriceReconstruction(status=ReconstructionStatus.RESOLVED, provenance=prov)
    with pytest.raises(ValueError):
        PriceReconstruction(
            status=ReconstructionStatus.PENDING,
            provenance=prov,
            price_vnd=Decimal("1"),
            reason=UnresolvedReason.PRICE_CLEARED,
        )
