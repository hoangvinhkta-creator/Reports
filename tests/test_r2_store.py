"""S071B — ``tools.storage.r2_store``: put/get/list JSON + bytes trên R2,
qua ``FakeR2Client`` (không cần credential/mạng R2 thật).
"""

from __future__ import annotations

import threading

import pytest

from tests.fixtures.fake_r2_client import FakeClientError, FakeR2Client
from tools.storage import r2_store
from tools.storage.errors import (
    CorruptRunRecordError, RunAlreadyExistsError, StorageUnavailableError,
)

ENV = {
    r2_store.ACCOUNT_ID_ENV_VAR: "acct",
    r2_store.BUCKET_ENV_VAR: "bucket",
    r2_store.ACCESS_KEY_ID_ENV_VAR: "key",
    r2_store.SECRET_ACCESS_KEY_ENV_VAR: "secret",
}


def _client() -> FakeR2Client:
    return FakeR2Client()


# --- is_configured / is_valid_run_id ---------------------------------------


def test_is_configured_true_when_all_four_vars_present():
    assert r2_store.is_configured(ENV) is True


@pytest.mark.parametrize("missing", list(ENV))
def test_is_configured_false_when_any_var_missing(missing):
    env = dict(ENV)
    del env[missing]
    assert r2_store.is_configured(env) is False


def test_is_valid_run_id_rejects_path_traversal():
    assert r2_store.is_valid_run_id("report-20260901T080000Z") is True
    assert r2_store.is_valid_run_id("../../etc/passwd") is False
    assert r2_store.is_valid_run_id("runs/other.json") is False
    assert r2_store.is_valid_run_id("") is False


# --- put_json_if_absent / get_json ------------------------------------------


def test_put_then_get_json_round_trips():
    client = _client()
    r2_store.put_json_if_absent("runs/a.json", {"run_id": "a"}, client=client, env=ENV)
    assert r2_store.get_json("runs/a.json", client=client, env=ENV) == {"run_id": "a"}


def test_get_json_unknown_key_returns_none():
    client = _client()
    assert r2_store.get_json("runs/missing.json", client=client, env=ENV) is None


def test_put_json_duplicate_key_raises_run_already_exists():
    client = _client()
    r2_store.put_json_if_absent("runs/dup.json", {"n": 1}, client=client, env=ENV)
    with pytest.raises(RunAlreadyExistsError):
        r2_store.put_json_if_absent("runs/dup.json", {"n": 2}, client=client, env=ENV)


def test_get_json_corrupt_body_raises_corrupt_not_none():
    client = _client()
    client.put_raw("runs/bad.json", b"{not valid json")
    with pytest.raises(CorruptRunRecordError):
        r2_store.get_json("runs/bad.json", client=client, env=ENV)


@pytest.mark.parametrize("method", ["get_object", "put_object"])
def test_r2_unavailable_raises_storage_unavailable_not_swallowed(method):
    client = _client()
    client.fail[method] = FakeClientError("500", "network unreachable")
    with pytest.raises(StorageUnavailableError):
        if method == "get_object":
            r2_store.get_json("runs/x.json", client=client, env=ENV)
        else:
            r2_store.put_json_if_absent("runs/x.json", {}, client=client, env=ENV)


def test_r2_head_object_unavailable_raises_storage_unavailable_via_put_bytes():
    """`put_json_if_absent` không còn gọi `head_object` (PUT có điều kiện,
    một request) — chỗ duy nhất còn dùng `head_object` là verify-sau-upload
    của `put_bytes`, nên kiểm lỗi mạng/hạ tầng ở đúng chỗ đó."""
    client = _client()
    client.fail["head_object"] = FakeClientError("500", "network unreachable")
    with pytest.raises(StorageUnavailableError):
        r2_store.put_bytes(
            "artifacts/x.xlsx", b"data", content_type="x", client=client, env=ENV,
        )


def test_r2_auth_failure_raises_storage_unavailable():
    client = _client()
    client.fail["put_object"] = FakeClientError("AccessDenied", "bad credentials")
    with pytest.raises(StorageUnavailableError):
        r2_store.put_json_if_absent("runs/x.json", {}, client=client, env=ENV)


def test_r2_timeout_raises_storage_unavailable():
    client = _client()
    client.fail["get_object"] = TimeoutError("read timed out")
    with pytest.raises(StorageUnavailableError):
        r2_store.get_json("runs/x.json", client=client, env=ENV)


# --- N-01: PUT có điều kiện thay HEAD-rồi-PUT --------------------------------


def test_put_json_if_absent_sends_if_none_match_star_not_head_then_put():
    """Hợp đồng: `put_json_if_absent` phải là ĐÚNG một request `put_object`
    mang `IfNoneMatch="*"` — không còn một `head_object` đứng trước nó."""
    client = _client()
    r2_store.put_json_if_absent("runs/a.json", {"n": 1}, client=client, env=ENV)
    assert client.calls == [("put_object", "runs/a.json")]


def test_two_threads_racing_the_same_key_exactly_one_wins(monkeypatch):
    """`N-01` — hai luồng cùng tính key còn trống rồi cùng ghi ĐỒNG THỜI.

    `before_check["put_object"]` gắn một `threading.Barrier(2)`: cả hai
    luồng phải cùng tới đúng điểm quyết định của `put_object` trước khi bên
    nào được đi tiếp — ép ra đúng hình dạng cuộc đua, không phó mặc cho may
    rủi lịch chạy luồng. Với PUT có điều kiện thật (khoá bên trong
    `FakeR2Client.put_object`), đúng một luồng phải thắng dù cả hai cùng
    xuất phát từ "key còn trống".
    """
    client = _client()
    barrier = threading.Barrier(2)
    client.before_check["put_object"] = barrier.wait

    outcomes: list[str] = []
    lock = threading.Lock()

    def _writer(n: int) -> None:
        try:
            r2_store.put_json_if_absent(
                "runs/race.json", {"n": n}, client=client, env=ENV)
            result = "success"
        except RunAlreadyExistsError:
            result = "conflict"
        with lock:
            outcomes.append(result)

    threads = [threading.Thread(target=_writer, args=(n,)) for n in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert sorted(outcomes) == ["conflict", "success"], outcomes
    assert client.objects["runs/race.json"] is not None


# --- list_run_keys_desc ------------------------------------------------------


def test_list_run_keys_desc_newest_first_and_respects_limit():
    client = _client()
    for run_id in ["report-A", "report-B", "report-C"]:
        r2_store.put_json_if_absent(
            r2_store.run_key(run_id), {"run_id": run_id}, client=client, env=ENV,
        )
    keys = r2_store.list_run_keys_desc(limit=2, client=client, env=ENV)
    assert keys == [r2_store.run_key("report-C"), r2_store.run_key("report-B")]


def test_list_run_keys_desc_empty_history_returns_empty_list_not_error():
    client = _client()
    assert r2_store.list_run_keys_desc(limit=50, client=client, env=ENV) == []


def test_list_failure_raises_storage_unavailable_not_empty_history():
    client = _client()
    client.fail["list_objects_v2"] = FakeClientError("500")
    with pytest.raises(StorageUnavailableError):
        r2_store.list_run_keys_desc(limit=50, client=client, env=ENV)


# --- F-N02: list_all_keys không giới hạn số lượng ----------------------------


def test_list_all_keys_returns_every_key_beyond_a_single_page():
    """Bucket có nhiều hơn một trang (`MaxKeys=1000` mỗi lần) — `list_all_keys`
    phải liệt kê hết, không dừng ở trang đầu."""
    client = _client()
    for index in range(1, 2501):
        client.put_raw(f"prefix/{index:06d}.json", b"{}")
    keys = r2_store.list_all_keys("prefix/", client=client, env=ENV)
    assert len(keys) == 2500
    assert keys == sorted(keys)


def test_list_all_keys_empty_prefix_returns_empty_list():
    client = _client()
    assert r2_store.list_all_keys("prefix/", client=client, env=ENV) == []


def test_list_all_keys_failure_raises_storage_unavailable():
    client = _client()
    client.fail["list_objects_v2"] = FakeClientError("500")
    with pytest.raises(StorageUnavailableError):
        r2_store.list_all_keys("prefix/", client=client, env=ENV)


# --- put_bytes / get_bytes (artifact) ---------------------------------------


def test_put_then_get_bytes_round_trips():
    client = _client()
    r2_store.put_bytes(
        "artifacts/a.xlsx", b"xlsx-bytes", content_type="x", client=client, env=ENV,
    )
    assert r2_store.get_bytes("artifacts/a.xlsx", client=client, env=ENV) == b"xlsx-bytes"


def test_get_bytes_missing_artifact_returns_none():
    client = _client()
    assert r2_store.get_bytes("artifacts/missing.xlsx", client=client, env=ENV) is None


def test_put_bytes_verify_mismatch_raises_storage_unavailable(monkeypatch):
    client = _client()
    # head_object trả ContentLength khác thật — mô phỏng verify-sau-upload
    # phát hiện upload không toàn vẹn (S071B: fail closed).
    original_head = client.head_object

    def _lying_head(**kwargs):
        result = original_head(**kwargs)
        return {**result, "ContentLength": result["ContentLength"] + 1}

    monkeypatch.setattr(client, "head_object", _lying_head)
    with pytest.raises(StorageUnavailableError):
        r2_store.put_bytes(
            "artifacts/bad.xlsx", b"data", content_type="x", client=client, env=ENV,
        )


def test_artifact_upload_failure_raises_storage_unavailable():
    client = _client()
    client.fail["put_object"] = FakeClientError("503")
    with pytest.raises(StorageUnavailableError):
        r2_store.put_bytes(
            "artifacts/a.xlsx", b"data", content_type="x", client=client, env=ENV,
        )
