"""F-R2 — token progression guard cho ``tools.storage.r2_store.list_all_keys``.

Trước bản sửa này, vòng lặp phân trang của ``list_all_keys`` chỉ dừng khi
``NextContinuationToken`` vắng mặt — một backend hỏng luôn trả lại ĐÚNG
token cũ (không tiến trang) sẽ khiến hàm lặp vô hạn, treo request mãi mãi
thay vì fail loud. Bản sửa thêm một bất biến: token của lần gọi kế tiếp
PHẢI khác token vừa dùng, nếu không ``StorageUnavailableError`` được raise
ngay ở lần lặp thứ hai — nhanh, xác định, không cần chờ timeout thật nào.

Bốn case theo đúng đặc tả F-R2:
    P-01    phân trang bình thường (token tiến đều) → danh sách đầy đủ.
    P-02    backend trả cùng continuation token mãi mãi → fail loud, không
            treo (phải hoàn tất nhanh và xác định).
    P-03    > 5000 key (vượt ``_SCAN_LIMIT`` cũ của ``list_keys``) vẫn hoạt
            động đúng qua ``list_all_keys``.
    P-04    lỗ hổng số thứ tự ngay ranh giới trang vẫn raise
            ``MappingIntegrityError`` ở tầng journal (không bị guard mới che
            lấp hay đổi hành vi).
"""

from __future__ import annotations

import json

import pytest

from app.modules.product.identity.mapping import MappingIntegrityError
from app.web import identity_journal
from tests.fixtures.fake_r2_client import FakeR2Client
from tools.storage import r2_store
from tools.storage.errors import StorageUnavailableError

ENV = {
    r2_store.ACCOUNT_ID_ENV_VAR: "acct",
    r2_store.BUCKET_ENV_VAR: "bucket",
    r2_store.ACCESS_KEY_ID_ENV_VAR: "key",
    r2_store.SECRET_ACCESS_KEY_ENV_VAR: "secret",
}

PREFIX = "guard-test/"


class _RepeatingTokenClient:
    """Backend giả lập đúng dạng bug đã thấy: mỗi trang có nội dung (không
    rỗng, để không bị nhầm là "hết trang" theo cách khác) nhưng
    ``NextContinuationToken`` không bao giờ đổi. Guard phải bắt được ngay ở
    lần lặp thứ hai — test này không bao giờ thật sự lặp vô hạn dù guard có
    lỗi, vì ``max_calls`` chặn cứng số lần gọi ``list_objects_v2``."""

    STUCK_TOKEN = "stuck-token-does-not-advance"

    def __init__(self, max_calls: int = 10_000) -> None:
        self.calls = 0
        self._max_calls = max_calls

    def list_objects_v2(self, *, Bucket, Prefix="", MaxKeys=1000, ContinuationToken=None):
        self.calls += 1
        if self.calls > self._max_calls:
            raise AssertionError(
                "guard không chặn — list_objects_v2 bị gọi vượt "
                f"{self._max_calls} lần, đúng dạng lặp vô hạn cần tránh."
            )
        return {
            "Contents": [{"Key": f"{Prefix}stuck-{self.calls}.json"}],
            "NextContinuationToken": self.STUCK_TOKEN,
        }


def _journal(bucket: FakeR2Client) -> identity_journal.ObjectStoreIdentityJournal:
    return identity_journal.ObjectStoreIdentityJournal(client=bucket, env=ENV)


def _seed_events(bucket: FakeR2Client, count: int) -> None:
    for sequence in range(1, count + 1):
        payload = json.dumps({"seq": sequence}, sort_keys=True).encode("utf-8")
        bucket.put_raw(identity_journal.event_key(sequence), payload)


# ==========================================================================
# P-01 — phân trang bình thường, token tiến đều
# ==========================================================================


def test_p01_normal_pagination_token_advances_and_full_list_returned():
    bucket = FakeR2Client()
    for i in range(2500):
        bucket.put_raw(f"{PREFIX}{i:05d}.json", b"{}")

    keys = r2_store.list_all_keys(PREFIX, client=bucket, env=ENV)

    assert len(keys) == 2500
    assert keys == sorted(keys)


# ==========================================================================
# P-02 — token lặp lại mãi mãi → fail loud, không treo
# ==========================================================================


def test_p02_repeated_continuation_token_fails_loudly_and_does_not_hang():
    client = _RepeatingTokenClient()

    with pytest.raises(StorageUnavailableError):
        r2_store.list_all_keys(PREFIX, client=client, env=ENV)

    # Bắt ngay ở lần lặp thứ hai (lần đầu chưa có gì để so sánh) — không
    # phải chạy hàng ngàn vòng lặp trước khi nổ.
    assert client.calls == 2


# ==========================================================================
# P-03 — > 5000 key vẫn hoạt động đúng qua list_all_keys
# ==========================================================================


def test_p03_more_than_5000_keys_still_returns_the_complete_list():
    bucket = FakeR2Client()
    for i in range(5003):
        bucket.put_raw(f"{PREFIX}{i:05d}.json", b"{}")

    keys = r2_store.list_all_keys(PREFIX, client=bucket, env=ENV)

    assert len(keys) == 5003
    assert keys == sorted(keys)


def test_p03_journal_pull_still_sees_all_events_beyond_5000_with_guard_in_place():
    bucket = FakeR2Client()
    _seed_events(bucket, 5003)

    journal = _journal(bucket)
    records = journal.pull()

    assert len(records) == 5003
    assert [record["seq"] for record in records] == list(range(1, 5004))


# ==========================================================================
# P-04 — lỗ hổng ở ranh giới trang vẫn raise MappingIntegrityError
# ==========================================================================


def test_p04_page_boundary_gap_still_raises_mapping_integrity_error():
    bucket = FakeR2Client()
    _seed_events(bucket, 1500)
    del bucket.objects[identity_journal.event_key(1001)]

    journal = _journal(bucket)
    with pytest.raises(MappingIntegrityError):
        journal.pull()
