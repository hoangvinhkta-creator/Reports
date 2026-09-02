"""TASK-PRA-002 slice B — vắng mặt: NOT_SEEN vs REMOVED_CANDIDATE trên DB thật.

Bất biến an toàn quan trọng nhất của cả slice, và mọi test ở đây tồn tại để
bảo vệ đúng nó:

    "không thấy" KHÔNG BAO GIỜ tự động trở thành "đã xoá".

Kể cả ``REMOVED_IN_SOURCE_CANDIDATE`` — mức mạnh nhất mà PRA-002 dựng được —
cũng chỉ là một dòng trong bảng cờ: con trỏ hiện hành, các bảng version và
mọi con số analytics phải KHÔNG đổi. Vì vậy gần như mọi test dưới đây kết
thúc bằng cùng một câu hỏi hỏi thẳng database: tổng tiền, số dòng hiện hành
và số bản ghi lịch sử có y hệt trước khi cờ được dựng không.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.exc import OperationalError

from app.web import history_store
from tools.db import schema

from tests.test_snapshot_repository import count, repository, rows, source_line, write

CONFIRMED_AT = "2026-02-10T00:00:00"
UNKNOWN_HEADER = "Sổ chi tiết bán hàng quý 3"


def flags(repo, kind=None) -> list[dict]:
    return [flag for flag in repo.list_flags()
            if kind is None or flag["kind"] == kind]


def business_state(repo, engine) -> dict:
    """Những gì một cờ vắng mặt KHÔNG BAO GIỜ được đổi, ở bất kỳ đường nào.

    Cố ý KHÔNG gồm ``order_line_result_version`` và ``snapshot_line``: mỗi lần
    chạy pipeline hợp lệ đều ghi thêm bản ghi quan sát vào hai bảng đó (slice
    A, mục 6) — số audit tăng, số nghiệp vụ thì không.
    """
    return {
        "totals": repo.current_totals(),
        "fingerprints": repo.current_fingerprints(),
        "source_versions": count(engine, schema.order_line_source_version),
        "current": count(engine, schema.order_line_current),
    }


def state(repo, engine) -> dict:
    """Thêm hai bảng quan sát — dùng cho đường XÁC NHẬN, nơi KHÔNG có run mới
    nào chạy nên tuyệt đối không bảng nào được phép nhúc nhích."""
    return dict(
        business_state(repo, engine),
        result_versions=count(engine, schema.order_line_result_version),
        membership=count(engine, schema.snapshot_line),
    )


def confirm(repo, snapshot_id, *, start, end, confirmed=True):
    return repo.confirm_coverage(
        snapshot_id, start=start, end=end, confirmed=confirmed,
        confirmed_at=CONFIRMED_AT,
    )


# --- bước 4: NOT_SEEN, ở cả hai mức coverage chưa xác nhận -----------------

@pytest.mark.parametrize("header_text,expected_state", [
    (UNKNOWN_HEADER, "DETECTED_ONLY"),
    ("Nhân viên: Tín Phát, Tháng 1 năm 2026", "HEADER_CONSISTENT"),
])
def test_a_missing_line_is_only_not_seen_while_coverage_is_unconfirmed(
    repository, history_engine, header_text, expected_state,
):
    """CHECK-PRA002-07: chưa xác nhận đủ → chỉ thông tin, KHÔNG ứng viên xoá."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00",
          header_text=header_text)
    before = business_state(repository, history_engine)

    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00", header_text=header_text)

    snapshot = repository.get_snapshot(second.snapshot_id)
    assert snapshot["coverage_state"] == expected_state
    assert snapshot["n_not_seen"] == 1
    assert snapshot["n_removed_candidate"] == 0
    flag, = flags(repository, "NOT_SEEN_IN_LATEST_SNAPSHOT")
    assert flag["order_key"] == "BH2"
    assert flag["raised_by_snapshot_id"] == second.snapshot_id
    assert flag["detail_json"]["scope"] == "DETECTED"
    assert flags(repository, "REMOVED_IN_SOURCE_CANDIDATE") == []
    assert business_state(repository, history_engine) == before, (
        "cờ KHÔNG đổi hiện trạng"
    )


def test_the_not_seen_flag_carries_the_provenance_needed_to_explain_it(
    repository, history_engine,
):
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    first = write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    current_version = {
        (row["order_key"], row["current_source_version_id"])
        for row in rows(history_engine, schema.order_line_current)
    }

    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")

    flag, = flags(repository, "NOT_SEEN_IN_LATEST_SNAPSHOT")
    assert flag["raised_by_snapshot_id"] == second.snapshot_id
    assert flag["run_id"] == "run-2"
    assert ("BH2", flag["from_version_id"]) in current_version, (
        "cờ phải trỏ tới version nguồn ĐANG hiện hành của khoá vắng mặt"
    )
    assert flag["to_version_id"] is None, "không có version mới nào được tạo"
    assert first.snapshot_id != second.snapshot_id



# --- bước R: REMOVED_CANDIDATE, chỉ sau xác nhận tường minh ---------------

def test_confirming_the_snapshot_turns_the_absence_into_a_review_candidate(
    repository, history_engine,
):
    """CHECK-PRA002-07: xác nhận đủ → ứng viên xoá, nhưng KHÔNG xoá gì cả."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")
    before = state(repository, history_engine)

    result = confirm(repository, second.snapshot_id,
                     start=date(2026, 1, 1), end=date(2026, 1, 31))

    assert result.removed_candidates == 1
    snapshot = repository.get_snapshot(second.snapshot_id)
    assert snapshot["coverage_state"] == "CONFIRMED_COMPLETE"
    assert snapshot["confirmed_range_start"] == date(2026, 1, 1)
    assert snapshot["confirmed_range_end"] == date(2026, 1, 31)
    assert snapshot["confirmed_at"] == CONFIRMED_AT
    assert snapshot["confirmed_by"] is None, "PRA-002 không có danh tính người dùng"
    assert snapshot["n_removed_candidate"] == 1
    removed, = flags(repository, "REMOVED_IN_SOURCE_CANDIDATE")
    assert removed["order_key"] == "BH2"
    assert removed["detail_json"]["scope"] == "CONFIRMED"
    assert state(repository, history_engine) == before, (
        "REMOVED_CANDIDATE là trạng thái Review — không xoá, không đổi tổng"
    )


def test_the_removed_candidate_line_is_still_current_and_still_counted(
    repository, history_engine,
):
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")
    confirm(repository, second.snapshot_id,
            start=date(2026, 1, 1), end=date(2026, 1, 31))

    current = {row["order_key"] for row in rows(history_engine, schema.order_line_current)}
    assert current == {"BH1", "BH2"}, "dòng bị đánh cờ VẪN là dòng hiện hành"
    assert repository.current_totals()["lines"] == 2
    assert repository.current_totals()["orders"] == 2
    assert repository.current_totals()["total_sales"] == sum(
        line.total_sales_raw for line in both
    ), "doanh thu KHÔNG giảm vì một cờ Review"


def test_the_earlier_not_seen_flag_is_kept_as_history_next_to_the_removed_one(
    repository,
):
    """Cờ cũ KHÔNG bị sửa hay xoá khi cờ mạnh hơn xuất hiện — append-only."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")
    confirm(repository, second.snapshot_id,
            start=date(2026, 1, 1), end=date(2026, 1, 31))

    kinds = [flag["kind"] for flag in repository.list_flags()]
    assert kinds == ["NOT_SEEN_IN_LATEST_SNAPSHOT", "REMOVED_IN_SOURCE_CANDIDATE"]
    assert all(flag["acknowledged_at"] is None for flag in repository.list_flags())


def test_historical_source_versions_are_untouched_by_any_absence_flag(
    repository, history_engine,
):
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    before = rows(history_engine, schema.order_line_source_version,
                  schema.order_line_source_version.c.id)

    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")
    confirm(repository, second.snapshot_id,
            start=date(2026, 1, 1), end=date(2026, 1, 31))

    after = rows(history_engine, schema.order_line_source_version,
                 schema.order_line_source_version.c.id)
    assert after == before, "lịch sử nguồn là bằng chứng — không được đụng vào"


# --- ranh giới phạm vi ----------------------------------------------------

def test_a_line_outside_the_confirmed_range_is_never_a_removal_candidate(
    repository, history_engine,
):
    """Chỉ thị mục 12/13: xác nhận 01–10 KHÔNG có thẩm quyền lên 11–30."""
    wide = [
        source_line("BH-EARLY", row=6, sale_date=date(2026, 1, 5)),
        source_line("BH-LATE", row=7, sale_date=date(2026, 1, 20)),
    ]
    write(repository, wide, run_id="run-b", created_at="2026-02-01T00:00:00")
    narrow = write(repository, [wide[0]], run_id="run-a", fingerprint="fp-a2",
                   created_at="2026-02-02T00:00:00")
    before = state(repository, history_engine)

    result = confirm(repository, narrow.snapshot_id,
                     start=date(2026, 1, 1), end=date(2026, 1, 10))

    assert result.removed_candidates == 0
    assert flags(repository, "REMOVED_IN_SOURCE_CANDIDATE") == []
    assert repository.get_snapshot(narrow.snapshot_id)["n_removed_candidate"] == 0
    assert state(repository, history_engine) == before


def test_the_narrow_snapshot_does_not_even_flag_the_later_period_as_not_seen(
    repository,
):
    """Bước 4 cũng bị giới hạn bởi khoảng ĐO ĐƯỢC của chính snapshot.

    Đây là điều frozen contract (mục 8 bước 4) quy định: phạm vi của một cờ
    vắng mặt là phạm vi snapshot thực sự đại diện. Một sổ 01–05/01 không phát
    biểu gì về đơn ngày 20/01, nên nó không được dựng cờ ở đó — im lặng đúng
    còn hơn một cảnh báo sai.
    """
    wide = [
        source_line("BH-EARLY", row=6, sale_date=date(2026, 1, 5)),
        source_line("BH-LATE", row=7, sale_date=date(2026, 1, 20)),
    ]
    write(repository, wide, run_id="run-b", created_at="2026-02-01T00:00:00")
    write(repository, [wide[0]], run_id="run-a", fingerprint="fp-a2",
          created_at="2026-02-02T00:00:00")

    assert flags(repository, "NOT_SEEN_IN_LATEST_SNAPSHOT") == []


def test_a_wider_confirmed_range_than_the_data_does_reach_the_later_lines(
    repository,
):
    """Nếu Owner khai rộng hơn, thẩm quyền theo đúng lời khai của họ — không hơn."""
    wide = [
        source_line("BH-EARLY", row=6, sale_date=date(2026, 1, 5)),
        source_line("BH-LATE", row=7, sale_date=date(2026, 1, 20)),
    ]
    write(repository, wide, run_id="run-b", created_at="2026-02-01T00:00:00")
    narrow = write(repository, [wide[0]], run_id="run-a", fingerprint="fp-a2",
                   created_at="2026-02-02T00:00:00")

    result = confirm(repository, narrow.snapshot_id,
                     start=date(2026, 1, 1), end=date(2026, 1, 31))

    assert result.removed_candidates == 1
    removed, = flags(repository, "REMOVED_IN_SOURCE_CANDIDATE")
    assert removed["order_key"] == "BH-LATE"
    assert repository.current_totals()["lines"] == 2, "vẫn không xoá gì"


# --- chồng kỳ: A ⊂ B ------------------------------------------------------

def test_a_snapshot_that_contains_the_previous_one_raises_no_absence_at_all(
    repository, history_engine,
):
    """A(01–10) rồi B(01–30): B chứa A → SAME + INSERT, KHÔNG cờ vắng mặt."""
    early = source_line("BH-A", row=6, sale_date=date(2026, 1, 5))
    late = source_line("BH-B", row=7, sale_date=date(2026, 1, 20))
    write(repository, [early], run_id="run-a", created_at="2026-02-01T00:00:00")
    second = write(repository, [early, late], run_id="run-b", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")

    snapshot = repository.get_snapshot(second.snapshot_id)
    assert (snapshot["n_same"], snapshot["n_insert"]) == (1, 1)
    assert snapshot["n_not_seen"] == 0
    assert repository.list_flags() == []
    assert repository.current_totals()["lines"] == 2, "không double-count"


def test_confirming_the_containing_snapshot_still_raises_nothing(repository):
    early = source_line("BH-A", row=6, sale_date=date(2026, 1, 5))
    late = source_line("BH-B", row=7, sale_date=date(2026, 1, 20))
    write(repository, [early], run_id="run-a", created_at="2026-02-01T00:00:00")
    second = write(repository, [early, late], run_id="run-b", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")

    result = confirm(repository, second.snapshot_id,
                     start=date(2026, 1, 1), end=date(2026, 1, 31))

    assert result.removed_candidates == 0
    assert repository.list_flags() == []


# --- xuất hiện trở lại ----------------------------------------------------

def test_a_line_that_comes_back_leaves_the_old_flag_standing_but_not_active(
    repository, history_engine,
):
    """Cờ vắng mặt là BẤT BIẾN; "còn hiệu lực" được DẪN XUẤT lúc đọc."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")
    confirm(repository, second.snapshot_id,
            start=date(2026, 1, 1), end=date(2026, 1, 31))
    assert all(flag["is_active"] for flag in repository.list_flags())
    flags_before = count(history_engine, schema.reconciliation_flag)

    third = write(repository, both, run_id="run-3", fingerprint="fp-c",
                  created_at="2026-02-03T00:00:00")

    assert count(history_engine, schema.reconciliation_flag) == flags_before, (
        "không cờ nào bị xoá và không cờ nào bị sửa"
    )
    for flag in repository.list_flags():
        assert flag["is_active"] is False
        assert flag["seen_again_in_snapshot_id"] == third.snapshot_id
    assert repository.current_totals()["lines"] == 2
    assert repository.get_snapshot(third.snapshot_id)["n_same"] == 2, (
        "quay lại với nội dung cũ là SAME — không version mới, không double-count"
    )


def test_a_flag_stays_active_while_the_line_is_still_missing(repository):
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
          created_at="2026-02-02T00:00:00")
    write(repository, [both[0]], run_id="run-3", fingerprint="fp-c",
          created_at="2026-02-03T00:00:00")

    absence = flags(repository, "NOT_SEEN_IN_LATEST_SNAPSHOT")
    assert len(absence) == 2
    assert all(flag["is_active"] for flag in absence)


def test_flags_that_are_not_about_absence_carry_no_active_state(repository):
    """SOURCE_CHANGED không phải phát biểu về sự vắng mặt — không gắn nhãn giả."""
    first = source_line("BH1", row=6)
    write(repository, [first], run_id="run-1", created_at="2026-02-01T00:00:00")
    write(repository, [source_line("BH1", row=6, sell_price="9000000")],
          run_id="run-2", fingerprint="fp-b", created_at="2026-02-02T00:00:00")

    changed, = flags(repository, "SOURCE_CHANGED")
    assert changed["is_active"] is None
    assert changed["seen_again_in_snapshot_id"] is None


# --- xác nhận: fail-closed và bất biến ------------------------------------

def test_confirmation_without_the_explicit_flag_writes_nothing(
    repository, history_engine,
):
    """Không có hành động tường minh → KHÔNG có CONFIRMED_COMPLETE. Fail-closed."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")
    before = state(repository, history_engine)

    with pytest.raises(history_store.CoverageRangeError):
        confirm(repository, second.snapshot_id, start=date(2026, 1, 1),
                end=date(2026, 1, 31), confirmed=False)

    assert repository.get_snapshot(second.snapshot_id)["coverage_state"] != (
        "CONFIRMED_COMPLETE"
    )
    assert flags(repository, "REMOVED_IN_SOURCE_CANDIDATE") == []
    assert state(repository, history_engine) == before


def test_a_range_that_does_not_cover_the_data_is_refused_and_changes_nothing(
    repository,
):
    written = write(repository, [source_line("BH1", sale_date=date(2026, 1, 20))],
                    run_id="run-1", created_at="2026-02-01T00:00:00")

    with pytest.raises(history_store.CoverageRangeError):
        confirm(repository, written.snapshot_id,
                start=date(2026, 1, 1), end=date(2026, 1, 10))

    snapshot = repository.get_snapshot(written.snapshot_id)
    assert snapshot["coverage_state"] != "CONFIRMED_COMPLETE"
    assert snapshot["confirmed_range_start"] is None
    assert snapshot["confirmed_at"] is None


def test_confirming_twice_is_refused_and_leaves_the_first_confirmation_intact(
    repository, history_engine,
):
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    second = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")
    confirm(repository, second.snapshot_id,
            start=date(2026, 1, 1), end=date(2026, 1, 31))
    after_first = state(repository, history_engine)
    flags_after_first = count(history_engine, schema.reconciliation_flag)

    with pytest.raises(history_store.CoverageAlreadyConfirmedError):
        confirm(repository, second.snapshot_id,
                start=date(2026, 1, 1), end=date(2026, 1, 31))

    snapshot = repository.get_snapshot(second.snapshot_id)
    assert snapshot["confirmed_range_end"] == date(2026, 1, 31)
    assert snapshot["n_removed_candidate"] == 1
    assert count(history_engine, schema.reconciliation_flag) == flags_after_first, (
        "xác nhận lần hai KHÔNG được nhân đôi cờ"
    )
    assert state(repository, history_engine) == after_first


def test_confirming_a_snapshot_that_does_not_exist_is_a_key_error(repository):
    with pytest.raises(KeyError):
        confirm(repository, "SNAP-khong-ton-tai",
                start=date(2026, 1, 1), end=date(2026, 1, 31))


def _explode_on(monkeypatch, name, table):
    """Ép đúng MỘT câu lệnh SQL trên ``table`` hỏng, các câu khác chạy bình thường."""
    real = getattr(history_store, name)

    def broken(target, *args, **kwargs):
        if target is table:
            raise OperationalError("mô phỏng mất kết nối", {}, Exception(name))
        return real(target, *args, **kwargs)

    monkeypatch.setattr(history_store, name, broken)


@pytest.mark.parametrize("statement,table", [
    ("update", schema.source_snapshot),
    ("insert", schema.reconciliation_flag),
])
def test_a_database_failure_midway_leaves_neither_half_of_the_confirmation(
    repository, history_engine, monkeypatch, statement, table,
):
    """Nâng coverage và bước R là MỘT đơn vị công việc (mục 7.3) — chứng minh
    bằng cách làm hỏng từng nửa.

    Hai trạng thái nửa vời bị cấm, và mỗi tham số ở đây ép đúng một nửa hỏng:

    * ``CONFIRMED_COMPLETE`` mà thiếu cờ → hệ thống đã tuyên bố "sổ này đầy
      đủ" rồi im lặng nuốt các dòng vắng mặt — đúng thứ BR-2 nói là mất doanh
      thu không ai thấy.
    * cờ ``REMOVED_IN_SOURCE_CANDIDATE`` mà coverage chưa xác nhận → database
      mang những "ứng viên đã bị xoá" mà không hành động tường minh nào của
      con người đứng sau, phá vỡ chính bất biến của slice B.

    Sau lỗi, database phải trở về trạng thái TRƯỚC lệnh xác nhận, không phải
    một trạng thái "gần đúng".
    """
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    narrow = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")
    before = state(repository, history_engine)
    flags_before = count(history_engine, schema.reconciliation_flag)

    _explode_on(monkeypatch, statement, table)
    with pytest.raises(history_store.HistoryUnavailableError):
        confirm(repository, narrow.snapshot_id,
                start=date(2026, 1, 1), end=date(2026, 1, 31))
    monkeypatch.undo()

    snapshot = repository.get_snapshot(narrow.snapshot_id)
    assert snapshot["coverage_state"] != "CONFIRMED_COMPLETE"
    assert snapshot["confirmed_range_start"] is None
    assert snapshot["confirmed_at"] is None
    assert snapshot["n_removed_candidate"] == 0
    assert count(history_engine, schema.reconciliation_flag) == flags_before
    assert flags(repository, "REMOVED_IN_SOURCE_CANDIDATE") == []
    assert state(repository, history_engine) == before


def test_the_confirmation_can_still_be_made_after_a_failed_attempt(
    repository, history_engine, monkeypatch,
):
    """Rollback không được để lại một snapshot "kẹt": lần thử sau phải chạy đủ."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    narrow = write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
                   created_at="2026-02-02T00:00:00")

    _explode_on(monkeypatch, "update", schema.source_snapshot)
    with pytest.raises(history_store.HistoryUnavailableError):
        confirm(repository, narrow.snapshot_id,
                start=date(2026, 1, 1), end=date(2026, 1, 31))
    monkeypatch.undo()

    result = confirm(repository, narrow.snapshot_id,
                     start=date(2026, 1, 1), end=date(2026, 1, 31))

    assert result.removed_candidates == 1
    snapshot = repository.get_snapshot(narrow.snapshot_id)
    assert snapshot["coverage_state"] == "CONFIRMED_COMPLETE"
    assert snapshot["n_removed_candidate"] == 1
    removed, = flags(repository, "REMOVED_IN_SOURCE_CANDIDATE")
    assert removed["order_key"] == "BH2"
    assert count(history_engine, schema.reconciliation_flag) == 2, (
        "đúng một NOT_SEEN (bước 4) + một REMOVED (bước R) — lần hỏng không để lại gì"
    )


def test_confirmation_uses_this_snapshots_membership_not_the_latest_state(
    repository,
):
    """DEC-171 #6: bước R hỏi "dòng này có trong SỔ ĐÓ không", không hỏi last_seen.

    Kịch bản bẫy: xác nhận sổ hẹp SAU khi một sổ rộng hơn đã ghi đè
    ``last_seen`` của mọi khoá. Nếu bước R đọc ``last_seen`` thay vì
    membership, nó sẽ không thấy khoá nào vắng mặt và bỏ sót ứng viên thật.
    """
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    narrow = write(repository, [both[0]], run_id="run-1",
                   created_at="2026-02-01T00:00:00")
    write(repository, both, run_id="run-2", fingerprint="fp-b",
          created_at="2026-02-02T00:00:00")

    result = confirm(repository, narrow.snapshot_id,
                     start=date(2026, 1, 1), end=date(2026, 1, 31))

    assert result.removed_candidates == 1
    removed, = flags(repository, "REMOVED_IN_SOURCE_CANDIDATE")
    assert removed["order_key"] == "BH2"
    assert removed["raised_by_snapshot_id"] == narrow.snapshot_id


def test_a_line_under_identity_dispute_is_never_flagged_absent(
    repository, history_engine,
):
    """Khoá đang tranh chấp: hệ thống chưa biết nó là đơn nào — không kết luận."""
    from datetime import timedelta

    original = source_line("BH1", row=6, sale_date=date(2026, 1, 5))
    write(repository, [original], run_id="run-1", created_at="2026-02-01T00:00:00")
    far = source_line("BH1", row=6, sale_date=date(2026, 1, 5) + timedelta(days=91))
    write(repository, [far], run_id="run-2", fingerprint="fp-b",
          created_at="2026-02-02T00:00:00")

    third = write(repository, [source_line("BH2", row=7)], run_id="run-3",
                  fingerprint="fp-c", created_at="2026-02-03T00:00:00")
    confirm(repository, third.snapshot_id,
            start=date(2026, 1, 1), end=date(2026, 1, 31))

    assert flags(repository, "NOT_SEEN_IN_LATEST_SNAPSHOT") == []
    assert flags(repository, "REMOVED_IN_SOURCE_CANDIDATE") == []
