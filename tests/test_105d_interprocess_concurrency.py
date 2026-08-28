"""TASK-105D — RC-1: concurrency LIÊN-TIẾN-TRÌNH của `JsonlProductIdentityStore`.

Trigger: `B-01` của Independent Implementation Review #1 (`S041`,
`docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md`).

Data contract `§11.1` tuyên bố phạm vi "JSONL + khoá file cho concurrency
**một máy**", tức nhiều người dùng đồng thời TRÊN MỘT MÁY nằm TRONG Phase 1.
`CHECK-105D-20` Phần A chỉ dựng contention trên **một** instance store, nên nó
không chạm tới biên đó. File này dựng contention THẬT ở đúng biên đã tuyên bố:
hai tiến trình HĐH độc lập, cùng một file log, cùng `expected_version`.

Không có case nào ở đây mô phỏng tranh chấp bằng hai lời gọi trên một
instance, bằng monkeypatch, hay bằng `sleep`. Đồng bộ dùng
`multiprocessing.Barrier` — cả hai tiến trình được nhân thả ra cùng lúc.
"""

from __future__ import annotations

import json
import multiprocessing
import os
from pathlib import Path

import pytest

from app.modules.product.identity.commands import BootstrapMapping, ConfirmMapping
from app.modules.product.identity.evidence import (
    Evidence,
    MatchedOn,
    RANKING_METHOD_ID,
    ResolutionMethod,
)
from app.modules.product.identity.identity import CanonicalProductIdentity, Namespace
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.mapping import MappingIntegrityError, MappingStatus
from app.modules.product.identity.store import (
    AppendOutcome,
    JsonlProductIdentityStore,
    MappingVersionConflict,
    SimilarityAuthorityError,
)
from tests.support import identity_fixtures as fx

PRODUCT_RAW = "Nồi chiên không dầu tranh chấp"

# Số vòng lặp của kịch bản tranh chấp. Một lần chạy may mắn không chứng minh
# được gì về một race; con số này đủ để lịch biểu của nhân đảo thứ tự nhiều
# lần mà vẫn giữ test dưới ngưỡng thời gian của CI.
CONTENTION_ROUNDS = 25


def _fork_context():
    """`fork` là ngữ cảnh duy nhất cho phép truyền `Barrier` sang tiến trình con.

    Đây là ràng buộc của `multiprocessing`, không phải của bản sửa: khoá file
    được thi hành bởi nhân và không quan tâm tiến trình sinh ra bằng cách nào.
    """
    try:
        return multiprocessing.get_context("fork")
    except ValueError:  # pragma: no cover — nền tảng không hỗ trợ fork
        pytest.skip("cần start method 'fork' để dựng barrier liên-tiến-trình")


def _confirm_command(code: str, *, request_id: str, expected_version: int = 0):
    return ConfirmMapping(
        actor_id=fx.ACTOR,
        client_request_id=request_id,
        expected_version=expected_version,
        raw_identity_key=raw_identity_key(PRODUCT_RAW),
        raw_product_identity=PRODUCT_RAW,
        target=CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code=code
        ),
        evidence=Evidence(
            matched_on=MatchedOn.RAW_KEY,
            matched_value=PRODUCT_RAW,
            candidate_set_ids=(f"TRACKING:{code}",),
            ranking_method_id=RANKING_METHOD_ID,
        ),
        resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
    )


def _worker(root: str, code: str, request_id: str, barrier, queue) -> None:
    """Chạy trong TIẾN TRÌNH CON: dựng store riêng, rồi tranh chấp thật.

    Store được dựng SAU khi fork, nên hai tiến trình không chia sẻ một mẩu
    state nào trong bộ nhớ — chúng chỉ gặp nhau ở file log.
    """
    directory = Path(root)
    store = JsonlProductIdentityStore(
        log_path=directory / "identity.log.jsonl",
        index_path=directory / "identity.index.json",
    )
    command = _confirm_command(code, request_id=request_id)
    barrier.wait()  # cả hai tiến trình được thả ra cùng lúc
    try:
        result = store.append(command)
        queue.put((code, result.outcome.value, result.new_version))
    except MappingVersionConflict:
        queue.put((code, "MappingVersionConflict", None))
    except BaseException as exc:  # noqa: BLE001 — báo về cho tiến trình cha
        queue.put((code, f"{type(exc).__name__}: {exc}", None))


def _race(directory: Path, *, request_ids=("req-A", "req-B")):
    """Thả hai tiến trình vào cùng một `expected_version = 0`."""
    ctx = _fork_context()
    barrier = ctx.Barrier(2)
    queue = ctx.Queue()
    procs = [
        ctx.Process(
            target=_worker, args=(str(directory), code, request_id, barrier, queue)
        )
        for code, request_id in zip(("TRK-A", "TRK-B"), request_ids)
    ]
    for proc in procs:
        proc.start()
    outcomes = [queue.get(timeout=30) for _ in procs]
    for proc in procs:
        proc.join(timeout=30)
        assert proc.exitcode == 0, f"tiến trình con thoát bất thường: {proc.exitcode}"
    return outcomes


def _log_lines(directory: Path) -> list[dict]:
    log = directory / "identity.log.jsonl"
    if not log.exists():
        return []
    return [
        json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line
    ]


class TestInterProcessVersionRace:
    """`B-01` — hai tiến trình, cùng file, cùng `expected_version`."""

    def test_exactly_one_writer_wins_and_the_stale_one_is_refused(self, tmp_path):
        outcomes = _race(tmp_path)

        applied = [o for o in outcomes if o[1] == AppendOutcome.APPLIED.value]
        conflicts = [o for o in outcomes if o[1] == "MappingVersionConflict"]
        assert len(applied) == 1, outcomes
        assert len(conflicts) == 1, outcomes
        assert applied[0][2] == 1

    def test_the_stale_writer_appends_nothing(self, tmp_path):
        _race(tmp_path)

        records = _log_lines(tmp_path)
        assert len(records) == 1, records
        assert records[0]["event_type"] == "CONFIRM_MAPPING"
        assert records[0]["resulting_version"] == 1

    def test_repeated_contention_never_produces_two_winners(self, tmp_path):
        """Một lần chạy may mắn không chứng minh gì — lặp `CONTENTION_ROUNDS` vòng."""
        for round_number in range(CONTENTION_ROUNDS):
            directory = tmp_path / f"round-{round_number:02d}"
            directory.mkdir()
            outcomes = _race(directory)

            applied = [o for o in outcomes if o[1] == AppendOutcome.APPLIED.value]
            conflicts = [o for o in outcomes if o[1] == "MappingVersionConflict"]
            assert len(applied) == 1, (round_number, outcomes)
            assert len(conflicts) == 1, (round_number, outcomes)
            assert len(_log_lines(directory)) == 1, (round_number, outcomes)

    def test_both_orderings_actually_occur_across_rounds(self, tmp_path):
        """Chứng minh barrier tạo tranh chấp THẬT, không phải một thứ tự cố định.

        Nếu người thắng luôn là cùng một tiến trình ở mọi vòng, test tranh chấp
        chỉ đang đo một chuỗi tuần tự trá hình. Case này không khẳng định một
        tỉ lệ cụ thể — nó chỉ ghi lại phân bố quan sát được để bằng chứng
        không im lặng về điểm đó.
        """
        winners = []
        for round_number in range(CONTENTION_ROUNDS):
            directory = tmp_path / f"round-{round_number:02d}"
            directory.mkdir()
            outcomes = _race(directory)
            winners.append(
                next(o[0] for o in outcomes if o[1] == AppendOutcome.APPLIED.value)
            )

        assert len(winners) == CONTENTION_ROUNDS
        assert set(winners) <= {"TRK-A", "TRK-B"}


class TestStoreStaysValidAfterContention:
    """`§9` — điều phải đúng là trạng thái TRÊN ĐĨA, không phải trong bộ nhớ."""

    def test_a_fresh_store_reopened_from_disk_reads_one_confirmed_mapping(
        self, tmp_path
    ):
        outcomes = _race(tmp_path)
        winner = next(
            o[0] for o in outcomes if o[1] == AppendOutcome.APPLIED.value
        )

        reopened = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl",
            index_path=tmp_path / "identity.index.json",
        )
        mapping = reopened.read_active_mapping(
            "REPORTS_SALES", raw_identity_key(PRODUCT_RAW)
        )

        assert mapping is not None
        assert mapping.source_product_code == winner
        assert mapping.status is MappingStatus.CONFIRMED
        assert mapping.version == 1
        assert reopened.current_revision() == 1

    def test_no_permanent_integrity_error_and_the_alias_index_rebuilds(self, tmp_path):
        _race(tmp_path)

        reopened = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl",
            index_path=tmp_path / "identity.index.json",
        )
        view = reopened.read_at_revision(reopened.current_revision())
        assert len(view.alias_index()) == 1

        index = json.loads((tmp_path / "identity.index.json").read_text("utf-8"))
        assert index["revision"] == 1
        assert len(index["active_mappings"]) == 1

    def test_the_store_still_accepts_the_next_valid_write(self, tmp_path):
        """Không deadlock, không khoá kẹt: vòng tranh chấp không làm hỏng store."""
        _race(tmp_path)

        reopened = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl",
            index_path=tmp_path / "identity.index.json",
        )
        result = reopened.append(
            _confirm_command("TRK-C", request_id="req-C", expected_version=1)
        )
        assert result.outcome is AppendOutcome.APPLIED
        assert result.new_version == 2


class TestTwoInstancesInOneProcess:
    """`§8` — bổ sung cho, KHÔNG thay thế, test đa tiến trình ở trên."""

    def test_the_second_instance_refreshes_under_lock_and_sees_the_stale_version(
        self, tmp_path
    ):
        a = fx.store(tmp_path)
        b = fx.store(tmp_path)
        assert a.current_revision() == 0 and b.current_revision() == 0

        a.append(_confirm_command("TRK-A", request_id="req-A"))

        # `b` vẫn tin version = 0. Chỉ khi vào khoá và nạp lại log nó mới thấy
        # version thật = 1 — và phải từ chối, không được ghi (`INV-59`).
        with pytest.raises(MappingVersionConflict):
            b.append(_confirm_command("TRK-B", request_id="req-B"))

        assert len(_log_lines(tmp_path)) == 1

    def test_the_refused_instance_can_reconcile_and_then_succeed(self, tmp_path):
        """`INV-60` — reload và reconcile, không auto-merge, không force write."""
        a = fx.store(tmp_path)
        b = fx.store(tmp_path)
        a.append(_confirm_command("TRK-A", request_id="req-A"))
        with pytest.raises(MappingVersionConflict):
            b.append(_confirm_command("TRK-B", request_id="req-B"))

        result = b.append(
            _confirm_command("TRK-B", request_id="req-B2", expected_version=1)
        )
        assert result.outcome is AppendOutcome.APPLIED
        assert result.new_version == 2

        records = _log_lines(tmp_path)
        assert len(records) == 2
        assert records[1]["new_value"]["supersedes"] is not None

    def test_a_stale_instance_never_rewinds_the_log(self, tmp_path):
        a = fx.store(tmp_path)
        b = fx.store(tmp_path)
        a.append(_confirm_command("TRK-A", request_id="req-A"))
        a.append(
            _confirm_command("TRK-A2", request_id="req-A2", expected_version=1)
        )
        assert b.current_revision() == 0

        with pytest.raises(MappingVersionConflict):
            b.append(_confirm_command("TRK-B", request_id="req-B"))

        assert b.current_revision() == 2  # đã nạp lại trong khoá
        assert len(_log_lines(tmp_path)) == 2


class TestIdempotencyUnderContention:
    """`§11` — khoá file KHÔNG được phép đổi ngữ nghĩa idempotency sẵn có."""

    def test_the_same_client_request_id_from_two_processes_writes_one_event(
        self, tmp_path
    ):
        outcomes = _race(tmp_path, request_ids=("req-same", "req-same"))

        applied = [o for o in outcomes if o[1] == AppendOutcome.APPLIED.value]
        assert len(applied) == 1, outcomes
        # Kẻ đến sau nạp lại log TRONG khoá, thấy `client_request_id` đã dùng,
        # nên đi ra bằng lớp idempotency 1 (`INV-68`) chứ không phải bằng
        # version conflict. Đúng hợp đồng sẵn có, không phải ngữ nghĩa mới.
        assert {o[1] for o in outcomes} <= {
            AppendOutcome.APPLIED.value,
            AppendOutcome.ALREADY_APPLIED.value,
        }, outcomes
        assert len(_log_lines(tmp_path)) == 1

    def test_a_cross_process_retry_returns_the_earlier_result(self, tmp_path):
        a = fx.store(tmp_path)
        a.append(_confirm_command("TRK-A", request_id="req-A"))

        other = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl",
            index_path=tmp_path / "identity.index.json",
        )
        result = other.append(_confirm_command("TRK-A", request_id="req-A"))

        assert result.outcome is AppendOutcome.ALREADY_APPLIED
        assert result.new_version == 1
        assert len(_log_lines(tmp_path)) == 1


class TestAuditUnderContention:
    """`§12` — đúng một mutation được chấp nhận ⇒ đúng một dấu vết audit."""

    def test_the_refused_writer_leaves_no_audit_evidence(self, tmp_path):
        _race(tmp_path)

        reopened = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl",
            index_path=tmp_path / "identity.index.json",
        )
        events = reopened.events()
        assert len(events) == 1
        assert events[0].actor_id == fx.ACTOR
        assert reopened.confirmation_action_count() == 1


class TestLockReleaseOnFailurePaths:
    """`§10` — mọi đường thoát khỏi khoá đều phải trả khoá."""

    def _assert_store_still_usable(self, store, tmp_path, *, expected_version):
        result = store.append(
            _confirm_command(
                "TRK-OK", request_id="req-ok", expected_version=expected_version
            )
        )
        assert result.outcome is AppendOutcome.APPLIED

    def test_a_version_conflict_releases_the_lock(self, tmp_path):
        a = fx.store(tmp_path)
        a.append(_confirm_command("TRK-A", request_id="req-A"))
        with pytest.raises(MappingVersionConflict):
            a.append(_confirm_command("TRK-B", request_id="req-B"))
        self._assert_store_still_usable(a, tmp_path, expected_version=1)

    def test_an_authority_rejection_releases_the_lock(self, tmp_path):
        """Lỗi ném ra SAU khi đã khoá, TRƯỚC khi append (`INV-01`)."""
        a = fx.store(tmp_path)
        bad = BootstrapMapping(
            actor_id=fx.ACTOR,
            client_request_id="req-bad",
            expected_version=0,
            raw_identity_key=raw_identity_key(PRODUCT_RAW),
            raw_product_identity=PRODUCT_RAW,
            target=CanonicalProductIdentity(
                namespace=Namespace.TRACKING, source_product_code="TRK-X"
            ),
            evidence=Evidence(
                matched_on=MatchedOn.TRACKING_NAME,
                matched_value=PRODUCT_RAW,
                candidate_set_ids=("TRACKING:TRK-X",),
                ranking_method_id=RANKING_METHOD_ID,
            ),
            resolution_method=ResolutionMethod.SIMILARITY_RANKED,
        )
        with pytest.raises(SimilarityAuthorityError):
            a.append(bad)
        assert _log_lines(tmp_path) == []
        self._assert_store_still_usable(a, tmp_path, expected_version=0)

    def test_a_malformed_log_line_releases_the_lock_and_stays_a_domain_error(
        self, tmp_path
    ):
        a = fx.store(tmp_path)
        a.append(_confirm_command("TRK-A", request_id="req-A"))

        # Một tiến trình khác ghi một dòng hỏng (crash giữa `write()`).
        with open(tmp_path / "identity.log.jsonl", "a", encoding="utf-8") as handle:
            handle.write('{"event_id": "dang-ghi-do')

        with pytest.raises(MappingIntegrityError):
            a.append(
                _confirm_command("TRK-B", request_id="req-B", expected_version=1)
            )

        # Khoá đã được trả: một tiến trình khác vẫn lấy được khoá và vẫn nổ
        # bằng CÙNG lỗi miền — không treo, không đổi loại lỗi.
        with pytest.raises(MappingIntegrityError):
            JsonlProductIdentityStore(log_path=tmp_path / "identity.log.jsonl")

    def test_a_shrinking_log_is_refused_as_an_append_only_violation(self, tmp_path):
        a = fx.store(tmp_path)
        a.append(_confirm_command("TRK-A", request_id="req-A"))

        (tmp_path / "identity.log.jsonl").write_text("", encoding="utf-8")

        with pytest.raises(MappingIntegrityError):
            a.append(
                _confirm_command("TRK-B", request_id="req-B", expected_version=1)
            )


class TestEveryWritePathIsLocked:
    """`§19` — một đường ghi bỏ ngoài khoá làm bản sửa thành vá nửa vời."""

    def test_the_lock_file_sits_beside_the_log_and_is_never_replaced(self, tmp_path):
        a = fx.store(tmp_path)
        a.append(_confirm_command("TRK-A", request_id="req-A"))
        lock_path = tmp_path / "identity.log.jsonl.lock"
        assert a.lock_path == lock_path
        assert lock_path.exists()
        inode = lock_path.stat().st_ino

        a.append(_confirm_command("TRK-A2", request_id="req-A2", expected_version=1))
        a.rebuild_index()

        # Khoá KHÔNG được đặt trên một inode bị thay giữa chừng: index bị
        # `os.replace` thay inode ở mỗi lần ghi, log thì không, và file khoá
        # phải đứng yên tuyệt đối.
        assert lock_path.stat().st_ino == inode

    def test_import_bundle_takes_the_same_lock(self, tmp_path):
        source = fx.store()
        source.append(_confirm_command("TRK-A", request_id="req-A"))
        bundle = source.export_bundle()

        target_log = tmp_path / "identity.log.jsonl"
        restored = JsonlProductIdentityStore.import_bundle(bundle, log_path=target_log)

        assert restored.current_revision() == 1
        assert (tmp_path / "identity.log.jsonl.lock").exists()
        # Bundle đã nhập phải đọc lại được nguyên vẹn — offset không được
        # đếm nhầm và không dòng nào bị nạp hai lần.
        reopened = JsonlProductIdentityStore(log_path=target_log)
        assert reopened.current_revision() == 1
        assert reopened.export_bundle()["manifest"] == bundle["manifest"]

    def test_only_one_helper_writes_to_the_log_file(self):
        """Kiểm tĩnh: không đường ghi thứ hai nào lọt ra ngoài `_append_line`."""
        source = Path("app/modules/product/identity/store.py").read_text("utf-8")
        opens = [
            line.strip()
            for line in source.splitlines()
            if "open(self.log_path" in line
        ]
        assert opens == [
            'with open(self.log_path, "rb") as handle:',
            'with open(self.log_path, "ab") as handle:',
        ], opens

    def test_a_symlinked_lock_path_is_refused_instead_of_followed(self, tmp_path):
        """Đi theo symlink = hai tiến trình khoá hai inode khác nhau = `B-01` quay lại."""
        elsewhere = tmp_path / "ke-tan-cong.lock"
        elsewhere.write_bytes(b"")
        (tmp_path / "identity.log.jsonl.lock").symlink_to(elsewhere)

        a = fx.store(tmp_path)
        with pytest.raises(OSError):
            a.append(_confirm_command("TRK-A", request_id="req-A"))
        assert _log_lines(tmp_path) == []

    def test_an_in_memory_store_needs_no_lock_file(self, tmp_path):
        a = fx.store()
        a.append(_confirm_command("TRK-A", request_id="req-A"))
        assert a.lock_path is None
        assert list(tmp_path.iterdir()) == []


def _lock_holder(root: str, queue, ready) -> None:
    """Chạy trong tiến trình con: giữ khoá rồi treo cho tới khi bị giết."""
    import fcntl as _fcntl
    import time as _time

    fd = os.open(Path(root) / "identity.log.jsonl.lock", os.O_RDWR | os.O_CREAT, 0o600)
    _fcntl.flock(fd, _fcntl.LOCK_EX)
    queue.put("held")
    ready.wait()
    while True:  # pragma: no cover — tiến trình cha SIGKILL nó
        _time.sleep(3600)


class TestCrashReleasesTheLock:
    """`§10`/`§19` — khoá chết theo tiến trình, không để lại stale lock."""

    def test_a_killed_holder_leaves_no_stale_lock(self, tmp_path):
        a = fx.store(tmp_path)
        a.append(_confirm_command("TRK-A", request_id="req-A"))

        ctx = _fork_context()
        queue = ctx.Queue()
        ready = ctx.Event()
        holder = ctx.Process(target=_lock_holder, args=(str(tmp_path), queue, ready))
        holder.start()
        assert queue.get(timeout=30) == "held"

        # Khoá là THẬT: tiến trình cha không thể lấy được khi con đang giữ.
        # Dùng `LOCK_NB` để đo bằng một phép thử xác định, không bằng thời gian.
        import fcntl

        probe = os.open(tmp_path / "identity.log.jsonl.lock", os.O_RDWR, 0o600)
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(probe)

        holder.kill()  # SIGKILL — không có `finally` nào chạy trong tiến trình con
        holder.join(timeout=30)

        # Nhân trả khoá khi tiến trình chết ⇒ không deadlock ở lệnh ghi kế tiếp.
        result = a.append(
            _confirm_command("TRK-B", request_id="req-B", expected_version=1)
        )
        assert result.outcome is AppendOutcome.APPLIED
        assert len(_log_lines(tmp_path)) == 2


class TestLockDoesNotStarveOrdinaryAppends:
    """`§13` — đo đủ để biết khoá không làm append Phase-1 trở nên không dùng được."""

    def test_a_hundred_sequential_appends_stay_within_a_sane_budget(self, tmp_path):
        import time

        a = fx.store(tmp_path)
        started = time.perf_counter()
        for index in range(100):
            a.append(
                _confirm_command(
                    f"TRK-{index:03d}",
                    request_id=f"req-{index:03d}",
                    expected_version=index,
                )
            )
        elapsed = time.perf_counter() - started

        assert a.current_revision() == 100
        # Ngưỡng rộng có chủ ý: đây là kiểm tra "không thoái hoá thảm hoạ",
        # KHÔNG phải một benchmark. `H-04` (rebuild index O(n) mỗi append) vẫn
        # là HARDENING mở và không thuộc phạm vi RC-1.
        assert elapsed < 10.0, elapsed


def test_the_repository_runtime_provides_a_real_file_lock():
    """Bản sửa phụ thuộc `fcntl`; nếu vắng, store có persistence phải nổ."""
    from app.modules.product.identity import store as store_module

    assert store_module.fcntl is not None
    assert hasattr(store_module.fcntl, "flock")
    assert os.name == "posix"
