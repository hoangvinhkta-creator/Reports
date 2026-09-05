"""Bản sửa chặn N-01 / F-N02 cho journal quyết định Product Identity.

    N-01    hai worker cùng tính vị trí kế tiếp là N và cùng ghi ĐỒNG THỜI —
            trước bản sửa này `put_json_if_absent` dùng HEAD-rồi-PUT (hai
            request rời nhau), nên hai luồng cùng thấy N còn trống rồi cùng
            ghi đều có thể "thành công", và bản ghi của một bên biến mất.
            Sau bản sửa, PUT có điều kiện (`IfNoneMatch="*"`) làm việc
            kiểm-tra-rồi-ghi xảy ra trong ĐÚNG một request — đúng một bên
            thắng, bên kia nhận `JournalWriteConflict` để nạp lại và ghi
            tiếp ở N+1 (`INV-59`/`INV-60`).
    F-N02   liệt kê log qua `EVENT_KEY_PREFIX` từng dừng ở 5000 key — vượt
            ngưỡng đó, `pull()` đọc thiếu event và `append()` kế tiếp tưởng
            nhầm một vị trí đã có event là còn trống (ghi đè vĩnh viễn).

`FakeR2Client` đóng vai bucket R2 dùng chung — không cần credential thật.
`before_check["put_object"]` cho phép gắn một `threading.Barrier` để ép hai
luồng cùng đứng lại ở đúng điểm quyết định của một PUT có điều kiện, tạo ra
đúng hình dạng cuộc đua thay vì phó mặc lịch chạy luồng của hệ điều hành.
"""

from __future__ import annotations

import json
import threading

import pytest

from app.modules.product.identity.journal import JournalWriteConflict
from app.modules.product.identity.mapping import MappingIntegrityError
from app.web import identity_journal
from tests.fixtures.fake_r2_client import FakeR2Client

#: Đủ bốn biến để `r2_store.is_configured()` trả `True` — không credential
#: thật nào ở đây, client luôn được tiêm qua `client=`.
R2_ENV = {
    "R2_ACCOUNT_ID": "acc-test", "R2_BUCKET": "bucket-test",
    "R2_ACCESS_KEY_ID": "key-test", "R2_SECRET_ACCESS_KEY": "secret-test",
}


def _journal(bucket: FakeR2Client) -> identity_journal.ObjectStoreIdentityJournal:
    return identity_journal.ObjectStoreIdentityJournal(client=bucket, env=R2_ENV)


# ==========================================================================
# N-01 — hai worker cùng tính vị trí kế tiếp, ghi đồng thời
# ==========================================================================


def test_two_writers_at_the_same_next_sequence_exactly_one_wins_one_conflicts():
    """Cả hai worker cùng `pull()` thấy log rỗng ⟹ cả hai cùng tính vị trí kế
    tiếp là 1. Barrier ép cả hai đứng lại đúng ở bước quyết định của
    `put_object` trước khi cho cả hai ghi đồng thời — đúng hình dạng cuộc
    đua thật, không phải hai lệnh gọi nối tiếp nhau như test tuần tự có sẵn.

    Phải FAIL trên bản HEAD-rồi-PUT trước sửa: barrier ép cả hai `head_object`
    cùng trả "còn trống" trước khi bên nào kịp `put_object`, nên cả hai lần
    ghi không điều kiện phía sau đều "thành công" — mất một xác nhận Owner.
    """
    bucket = FakeR2Client()
    a, b = _journal(bucket), _journal(bucket)
    assert a.pull() == [] and b.pull() == []

    barrier = threading.Barrier(2)
    bucket.before_check["head_object"] = barrier.wait
    bucket.before_check["put_object"] = barrier.wait

    outcomes: dict[str, tuple[str, object]] = {}
    lock = threading.Lock()

    def _write(name, journal, payload):
        try:
            journal.append(payload)
            result = ("success", None)
        except JournalWriteConflict as exc:
            result = ("conflict", exc)
        with lock:
            outcomes[name] = result

    threads = [
        threading.Thread(target=_write, args=("a", a, {"writer": "A"})),
        threading.Thread(target=_write, args=("b", b, {"writer": "B"})),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not any(thread.is_alive() for thread in threads), "deadlock/timeout"
    # Gỡ barrier ngay sau cuộc đua — mọi lời gọi `put_object` một luồng sau
    # đó (retry của người thua) không còn ai để hẹn gặp ở checkpoint nữa.
    bucket.before_check.clear()
    results = sorted(outcome for outcome, _ in outcomes.values())
    assert results == ["conflict", "success"], outcomes

    # Log bền chỉ có ĐÚNG một event tại vị trí 1 — không phải hai lần "thành
    # công" đè lên nhau (mất một xác nhận Owner).
    assert sorted(bucket.objects) == [identity_journal.event_key(1)]

    loser_name = next(
        name for name, (outcome, _) in outcomes.items() if outcome == "conflict")
    loser = a if loser_name == "a" else b
    winner_payload = json.loads(bucket.objects[identity_journal.event_key(1)])

    # Người thua KHÔNG được tự nâng version của mình khi ghi hỏng (INV-59).
    assert loser.pull() == [winner_payload]

    # Nạp lại rồi thử lại ⟹ ghi được ở đúng vị trí kế tiếp thật (2).
    loser.append({"writer": f"{loser_name}-retry"})
    assert sorted(bucket.objects) == [
        identity_journal.event_key(1), identity_journal.event_key(2)]


def test_loser_retry_succeeds_and_restart_preserves_both_confirmations():
    """Sau cuộc đua: người thua nạp lại + ghi lại thành công, rồi "khởi động
    lại" (dựng journal MỚI trên cùng bucket, mô phỏng redeploy) — cả hai xác
    nhận đều còn, đúng thứ tự."""
    bucket = FakeR2Client()
    a, b = _journal(bucket), _journal(bucket)
    a.pull()
    b.pull()

    a.append({"writer": "A"})
    with pytest.raises(JournalWriteConflict):
        b.append({"writer": "B"})  # B vẫn tin vị trí 1 còn trống

    b.pull()
    b.append({"writer": "B"})

    restarted = _journal(bucket)
    records = restarted.pull()
    assert [record["writer"] for record in records] == ["A", "B"]


def test_conditional_write_contention_never_reports_two_successes_for_one_slot():
    """`M2` — nếu cả hai lần PUT có điều kiện đều báo thành công cho cùng
    một vị trí thì đây chính là mất-xác-nhận mà `N-01` phải đóng. Lặp lại
    vài lần để không phụ thuộc một lần trúng lịch chạy luồng may mắn."""
    for _ in range(5):
        bucket = FakeR2Client()
        a, b = _journal(bucket), _journal(bucket)
        a.pull()
        b.pull()
        barrier = threading.Barrier(2)
        bucket.before_check["put_object"] = barrier.wait

        successes = []
        lock = threading.Lock()

        def _write(journal, payload):
            try:
                journal.append(payload)
                with lock:
                    successes.append(payload)
            except JournalWriteConflict:
                pass

        threads = [
            threading.Thread(target=_write, args=(a, {"writer": "A"})),
            threading.Thread(target=_write, args=(b, {"writer": "B"})),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        assert len(successes) == 1, successes
        assert len(bucket.objects) == 1


# ==========================================================================
# F-N02 — phân trang khi log vượt quá một trang liệt kê
# ==========================================================================


def _seed_events(bucket: FakeR2Client, count: int) -> None:
    for sequence in range(1, count + 1):
        payload = json.dumps({"seq": sequence}, sort_keys=True).encode("utf-8")
        bucket.put_raw(identity_journal.event_key(sequence), payload)


def test_pull_sees_all_events_beyond_the_old_5000_cap_and_append_continues():
    """`> _SCAN_LIMIT` (5000) event — `pull()` không được dừng giữa chừng, và
    lần ghi kế tiếp phải rơi đúng vào 5004, không đè lên một vị trí đã có."""
    bucket = FakeR2Client()
    _seed_events(bucket, 5003)

    journal = _journal(bucket)
    records = journal.pull()
    assert len(records) == 5003
    assert [record["seq"] for record in records] == list(range(1, 5004))

    journal.append({"seq": 5004})
    assert identity_journal.event_key(5004) in bucket.objects
    assert sorted(bucket.objects) == [
        identity_journal.event_key(n) for n in range(1, 5005)]


def test_a_gap_straddling_a_page_boundary_raises_mapping_integrity_error():
    """1500 event nhưng thiếu đúng key 1001 — ngay sau ranh giới trang đầu
    của `list_objects_v2` (`MaxKeys=1000`). `pull()` phải nổ ngay, không
    được đọc tiếp thành một state một nửa (`INV-63`/`INV-67`)."""
    bucket = FakeR2Client()
    _seed_events(bucket, 1500)
    del bucket.objects[identity_journal.event_key(1001)]

    journal = _journal(bucket)
    with pytest.raises(MappingIntegrityError):
        journal.pull()


def test_a_gap_well_inside_a_single_page_still_raises():
    """Cùng bất biến khi lỗ hổng KHÔNG nằm ở ranh giới trang — phải nổ dù
    toàn bộ log nằm gọn trong một lần liệt kê."""
    bucket = FakeR2Client()
    _seed_events(bucket, 10)
    del bucket.objects[identity_journal.event_key(5)]

    journal = _journal(bucket)
    with pytest.raises(MappingIntegrityError):
        journal.pull()
