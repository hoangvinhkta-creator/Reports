"""TASK-105D — persistence, drift danh mục, bộ nhớ từ chối, idempotency,
concurrency và namespace.

Gate: `CHECK-105D-09`, `-10`, `-12`, `-19`, `-20`, `-29`, `-30`.
Adversarial: `K` (rejection memory), `M` (duplicate import), `N` (concurrency),
`O` (Tracking rename), `P` (Tracking disappears), `I` (same code, cross
namespace), `S` (declared actor).
"""

from __future__ import annotations

import json

import pytest

from app.modules.product.identity.audit import MissingActorError
from app.modules.product.identity.cli import confirm, reject, set_pending
from app.modules.product.identity.commands import (
    ConfirmMapping,
    MarkStale,
    RejectCandidate,
    SetPending,
)
from app.modules.product.identity import drift
from app.modules.product.identity.evidence import (
    Evidence,
    MatchedOn,
    RANKING_METHOD_ID,
    ResolutionMethod,
    evidence_fingerprint,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
    PendingProduct,
    PendingReason,
    RequiresConfirmation,
    Resolved,
)
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.mapping import (
    MappingIntegrityError,
    MappingStatus,
)
from app.modules.product.identity.registry import HistoricalConfirmedRegistry
from app.modules.product.identity.resolver import distinct_identities
from app.modules.product.identity.service import resolve_batch
from app.modules.product.identity.store import (
    AppendOutcome,
    JsonlProductIdentityStore,
    MappingVersionConflict,
)
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    ImmutableCaptureError,
    TrackingCaptureFailedError,
    TrackingSnapshotRepository,
)
from tests.support import identity_fixtures as fx

ROWS_V1 = (("TRK-A100", "Nồi chiên đời cũ", ("NCA-100",), True),)
ROWS_RENAMED = (("TRK-A100", "Nồi chiên đời MỚI", ("NCA-100-NEW",), True),)
ROWS_ABSENT = (("TRK-A100", "Nồi chiên đời cũ", (), False),)


def _confirm_seed(a_store, product_raw, namespace, code, *, request_id="seed-1"):
    return a_store.append(
        ConfirmMapping(
            actor_id=fx.ACTOR,
            client_request_id=request_id,
            expected_version=0,
            raw_identity_key=raw_identity_key(product_raw),
            raw_product_identity=product_raw,
            target=CanonicalProductIdentity(
                namespace=namespace, source_product_code=code
            ),
            evidence=Evidence(
                matched_on=MatchedOn.RAW_KEY,
                matched_value=product_raw,
                candidate_set_ids=(f"{namespace.value}:{code}",),
                ranking_method_id=RANKING_METHOD_ID,
            ),
            resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
        )
    )


def _resolve_one(a_store, product_raw, *, snapshot=None, version=None):
    resolver = fx.resolver(a_store, snapshot, version)
    identity, = distinct_identities([fx.row(product_raw)])
    return resolver.resolve(identity)


class TestG09PersistenceAndStoreIntegrity:
    """`CHECK-105D-09` — bền vững, index dẫn xuất, toàn vẹn store."""

    def test_fixture_1_confirm_then_restart_then_read_back(self, tmp_path):
        a_store = fx.store(tmp_path)
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        revision = a_store.current_revision()

        reopened = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl",
            index_path=tmp_path / "identity.index.json",
        )

        mapping = reopened.read_active_mapping("REPORTS_SALES", "TRK-A100")
        assert mapping is not None
        assert mapping.source_product_code == "TRK-A100"
        assert mapping.version == 1
        assert reopened.current_revision() == revision

    def test_fixture_2_deleting_the_index_loses_nothing(self, tmp_path):
        a_store = fx.store(tmp_path)
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        before = a_store.read_active_mapping("REPORTS_SALES", "TRK-A100")

        (tmp_path / "identity.index.json").unlink()
        rebuilt = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl",
            index_path=tmp_path / "identity.index.json",
        )

        after = rebuilt.read_active_mapping("REPORTS_SALES", "TRK-A100")
        assert after.mapping_id == before.mapping_id
        assert after.to_record() == before.to_record()

    def test_fixture_3_two_independent_confirmed_records_raise_not_pick_one(
        self, tmp_path
    ):
        """`INV-33` — TUYỆT ĐỐI không tự chọn một cái."""
        a_store = fx.store(tmp_path)
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")

        log = tmp_path / "identity.log.jsonl"
        lines = log.read_text(encoding="utf-8").splitlines()
        forged = json.loads(lines[0])
        forged["event_id"] = "forged-event"
        forged["revision"] = 2
        forged["new_value"] = dict(forged["new_value"])
        forged["new_value"]["mapping_id"] = "forged-mapping"
        forged["new_value"]["source_product_code"] = "TRK-KHAC"
        log.write_text(
            "\n".join(lines + [json.dumps(forged, ensure_ascii=False)]) + "\n",
            encoding="utf-8",
        )

        corrupted = JsonlProductIdentityStore(log_path=log)
        with pytest.raises(MappingIntegrityError, match="INV-33"):
            corrupted.read_active_mapping("REPORTS_SALES", "TRK-A100")

    def test_no_delete_operation_exists_on_the_interface(self):
        """`INV-67` — không có thao tác xoá ở bất kỳ đâu."""
        forbidden = {"delete", "remove", "drop", "truncate", "purge", "clear"}
        names = {name.lower() for name in dir(JsonlProductIdentityStore)}
        assert not (names & forbidden)

    def test_a_corrupt_log_line_refuses_to_load_half_a_state(self, tmp_path):
        log = tmp_path / "identity.log.jsonl"
        log.write_text('{"event_id": "a", broken\n', encoding="utf-8")
        with pytest.raises(MappingIntegrityError, match="không phải JSON"):
            JsonlProductIdentityStore(log_path=log)

    def test_export_then_import_is_bit_equivalent(self, tmp_path):
        """`INV-65` — HARDENING `HB-105D-F2-03`, không có gate riêng."""
        a_store = fx.store(tmp_path)
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        bundle = a_store.export_bundle()

        restored = JsonlProductIdentityStore.import_bundle(
            bundle, log_path=tmp_path / "restored.jsonl"
        )

        assert restored.export_bundle()["manifest"] == bundle["manifest"]
        assert restored.current_revision() == a_store.current_revision()


class TestG10ReuseAndCatalogDrift:
    """`CHECK-105D-10` — Phần A + `B1`…`B6`, bảy fixture."""

    def test_part_a_reuse_across_a_new_run(self, tmp_path):
        a_store = fx.store(tmp_path)
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")

        new_run = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl",
            index_path=tmp_path / "identity.index.json",
        )
        revision_before = new_run.current_revision()
        result = _resolve_one(
            new_run, "TRK-A100", snapshot=fx.tracking_snapshot(ROWS_V1)
        )

        assert result.resolution_method is ResolutionMethod.ALIAS_EXACT
        assert new_run.confirmation_action_count(since_revision=revision_before) == 0

    def test_b1_rename_keeps_the_confirmed_mapping_valid(self):
        """`INV-13`/`INV-21` — tên hiển thị KHÔNG phải identity."""
        a_store = fx.store()
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        revision = a_store.current_revision()

        result = _resolve_one(
            a_store, "TRK-A100", snapshot=fx.tracking_snapshot(ROWS_RENAMED)
        )

        assert result.resolution_method is ResolutionMethod.ALIAS_EXACT
        assert a_store.confirmation_action_count(since_revision=revision) == 0
        mapping = a_store.read_active_mapping("REPORTS_SALES", "TRK-A100")
        assert mapping.status is MappingStatus.CONFIRMED
        assert mapping.status is not MappingStatus.STALE

    def test_b2a_disappearance_does_not_invalidate_a_confirmed_mapping(self):
        a_store = fx.store()
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        revision = a_store.current_revision()
        absent = fx.tracking_snapshot(ROWS_ABSENT, capture_id=fx.CAPTURE_B)

        result = _resolve_one(a_store, "TRK-A100", snapshot=absent)

        assert result.resolution_method is ResolutionMethod.ALIAS_EXACT
        assert isinstance(result.outcome, Resolved)
        assert a_store.current_revision() == revision
        mapping = a_store.read_active_mapping("REPORTS_SALES", "TRK-A100")
        assert mapping.status is MappingStatus.CONFIRMED
        assert drift.mapping_still_valid(mapping, absent)

    def test_b2b_a_report_pinned_to_the_old_capture_replays_identically(
        self, tmp_path
    ):
        from app.modules.product.identity.binding import (
            ReportReplay,
            ResolutionBinding,
            replay_signature,
        )
        from datetime import datetime, timezone
        from app.modules.product.identity.public_purchase import (
            PublicPurchaseSourceRepository,
        )

        a_store = fx.store(tmp_path)
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        registry = HistoricalConfirmedRegistry()

        tracking_repo = TrackingSnapshotRepository()
        old_capture = fx.tracking_snapshot(ROWS_V1, capture_id=fx.CAPTURE_A)
        tracking_repo.register(old_capture)
        pp_repo = PublicPurchaseSourceRepository()
        pp_repo.publish(fx.pp_version())

        binding = ResolutionBinding(
            binding_id="BND-1",
            report_run_id="RUN-1",
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
            mapping_store_revision=a_store.current_revision(),
            registry_revision=registry.current_revision(),
            bound_at=datetime(2026, 9, 20, tzinfo=timezone.utc),
            bound_by=fx.ACTOR,
        )
        replay = ReportReplay(
            store=a_store,
            registry=registry,
            tracking_repository=tracking_repo,
            pp_repository=pp_repo,
        )
        rows = [fx.row("TRK-A100")]
        first = replay_signature(replay.replay(rows, binding))

        # Nạp capture MỚI, trong đó sản phẩm đã biến mất, và thêm mapping mới.
        tracking_repo.register(
            fx.tracking_snapshot(ROWS_ABSENT, capture_id=fx.CAPTURE_B)
        )
        _confirm_seed(
            a_store,
            "Một sản phẩm khác hẳn",
            Namespace.TRACKING,
            "TRK-B200",
            request_id="seed-2",
        )

        assert replay_signature(replay.replay(rows, binding)) == first

    def test_b3_a_new_identity_matching_only_an_absent_code_is_stale(self):
        """`INV-14c` — cần confirmation, KHÔNG auto-resolve."""
        a_store = fx.store()
        absent = fx.tracking_snapshot(ROWS_ABSENT, capture_id=fx.CAPTURE_B)

        result = _resolve_one(a_store, "TRK-A100", snapshot=absent)

        assert isinstance(result.outcome, PendingProduct)
        assert result.outcome.reason_code is PendingReason.MAPPING_STALE_TARGET_ABSENT
        assert a_store.confirmation_action_count() == 0

        # "cần confirmation": một SET_PENDING tường minh ghi status = STALE.
        applied = set_pending(
            a_store,
            result,
            actor_id=fx.ACTOR,
            client_request_id="req-stale-1",
            expected_version=0,
            stale=True,
        )
        assert applied.mapping.status is MappingStatus.STALE

    def test_b4_alias_map_merge_proposes_but_never_moves(self):
        """`INV-16` — resolver KHÔNG tự chuyển mapping đã confirm sang mã chính."""
        a_store = fx.store()
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        revision = a_store.current_revision()
        merged = fx.tracking_snapshot(
            (("TRK-PRIMARY", "Mã chính", (), True),),
            capture_id=fx.CAPTURE_B,
            alias_map_rows=(("TRK-A100", "TRK-PRIMARY"),),
        )

        result = _resolve_one(a_store, "TRK-A100", snapshot=merged)
        mapping = a_store.read_active_mapping("REPORTS_SALES", "TRK-A100")

        assert result.resolution_method is ResolutionMethod.ALIAS_EXACT
        assert mapping.source_product_code == "TRK-A100"
        assert a_store.current_revision() == revision

        view = a_store.read_at_revision(revision)
        proposals = drift.detect(view, merged)
        assert len(proposals) == 1
        assert proposals[0].candidate_1 == "TRK-PRIMARY"

        a_store.append(
            MarkStale(
                actor_id=fx.ACTOR,
                client_request_id="req-mark-stale-1",
                expected_version=mapping.version,
                raw_identity_key=mapping.raw_identity_key,
                raw_product_identity=mapping.raw_product_identity,
                proposed_primary_code="TRK-PRIMARY",
            )
        )
        assert (
            a_store.events()[-1].event_type.value == "MARK_STALE"
        )
        assert a_store.confirmation_action_count(since_revision=revision) == 0

    def test_b5_a_failed_capture_is_a_hard_error_not_pending(self):
        failed = fx.tracking_snapshot(
            (),
            capture_id="TRK-failed-1",
            status=CaptureStatus.FAILED,
            failure_reason="mất kết nối giữa chừng",
        )
        with pytest.raises(TrackingCaptureFailedError, match="INV-12"):
            fx.resolver(fx.store(), failed)

    def test_b6_the_current_catalog_never_rewrites_a_historical_identity(self):
        """`INV-15` — cấm retroactive remap."""
        a_store = fx.store()
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        revision = a_store.current_revision()
        moved = fx.tracking_snapshot(
            (("TRK-NEWCODE", "TRK-A100", (), True),), capture_id=fx.CAPTURE_B
        )

        _resolve_one(a_store, "TRK-A100", snapshot=moved)

        mapping = a_store.read_active_mapping("REPORTS_SALES", "TRK-A100")
        assert mapping.source_product_code == "TRK-A100"
        assert a_store.current_revision() == revision

    def test_no_drift_branch_writes_to_tracking(self):
        """Không nhánh nào ở Phần B ghi vào Tracking (bất biến của `G17`)."""
        repository = TrackingSnapshotRepository()
        snapshot = fx.tracking_snapshot(ROWS_V1)
        repository.register(snapshot)
        with pytest.raises(ImmutableCaptureError, match="INV-11"):
            repository.register(snapshot)


class TestG12RejectedCandidateMemory:
    """`CHECK-105D-12` — bốn fixture + chiều `ranking_method_id` (`H-05`)."""

    def _ambiguous(self, a_store, snapshot=None, version=None):
        snapshot = snapshot or fx.tracking_snapshot(
            (
                ("TRK-M1", "Máy lọc không khí AP-100", (), True),
                ("TRK-M2", "Máy lọc không khí AP-200", (), True),
            )
        )
        return _resolve_one(
            a_store, "Máy lọc không khí AP-300", snapshot=snapshot, version=version
        )

    def test_fixture_1_same_evidence_suppresses_the_rejected_candidate(self):
        a_store = fx.store()
        first = self._ambiguous(a_store)
        rejected_id = first.candidates[0].candidate_id

        reject(
            a_store,
            first,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="req-rej-1",
            expected_version=0,
        )

        again = self._ambiguous(a_store)
        assert rejected_id not in {c.candidate_id for c in again.candidates}

    def test_fixture_2_a_new_pp_version_brings_the_candidate_back(self):
        a_store = fx.store()
        first = self._ambiguous(a_store)
        rejected_id = first.candidates[0].candidate_id
        reject(
            a_store,
            first,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="req-rej-2",
            expected_version=0,
        )

        again = self._ambiguous(a_store, version=fx.pp_version(version_id=fx.PP_V2))

        returned = {c.candidate_id: c for c in again.candidates}
        assert rejected_id in returned
        assert "đã từ chối tại" in (returned[rejected_id].note or "")

    def test_fixture_2b_a_new_ranking_method_brings_the_candidate_back(self):
        """`H-05` — chiều `ranking_method_id`, KHÔNG có fixture nào ở `G12` gốc.

        Freeze Review #2 ghi rõ: bốn fixture bắt buộc của `CHECK-105D-12` chỉ
        diễn tập chiều `pp_version_id`. Đây là fixture còn thiếu, thêm ở tầng
        implementation mà KHÔNG sửa gate và KHÔNG sửa data contract.
        """
        base = dict(
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
            candidate_set_ids=("TRACKING:TRK-M1", "TRACKING:TRK-M2"),
        )
        v1 = evidence_fingerprint(**base, ranking_method_id="rank/v1")
        v2 = evidence_fingerprint(**base, ranking_method_id="rank/v2")
        absent = evidence_fingerprint(**base, ranking_method_id=None)

        assert v1 != v2, "đổi thuật toán xếp hạng phải đổi fingerprint (INV-35)"
        assert absent not in {v1, v2}, (
            "ranking_method_id vắng phải phân biệt được với có — nếu không, "
            "chiều 'thuật toán đã đổi' của INV-35 im lặng biến mất (H-05)"
        )

    def test_fixture_3_rejecting_candidate_1_never_auto_confirms_candidate_2(self):
        """`INV-36` — từ chối A KHÔNG BAO GIỜ trở thành mapping tới B."""
        a_store = fx.store()
        first = self._ambiguous(a_store)
        assert len(first.candidates) == 2

        reject(
            a_store,
            first,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="req-rej-3",
            expected_version=0,
        )

        again = self._ambiguous(a_store)
        assert isinstance(again.outcome, (RequiresConfirmation, PendingProduct))
        assert a_store.read_active_mapping(
            "REPORTS_SALES", raw_identity_key("Máy lọc không khí AP-300")
        ) is None

    def test_fixture_4_rejecting_everything_gives_pending_with_the_right_reason(
        self,
    ):
        """`INV-37` — không ép người dùng chọn một candidate sai để thoát."""
        a_store = fx.store()
        for index in range(2):
            current = self._ambiguous(a_store)
            if not current.candidates:
                break
            reject(
                a_store,
                current,
                candidate_rank=1,
                actor_id=fx.ACTOR,
                client_request_id=f"req-rej-all-{index}",
                expected_version=0,
            )

        final = self._ambiguous(a_store)
        assert isinstance(final.outcome, PendingProduct)
        assert (
            final.outcome.reason_code
            is PendingReason.CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED
        )

    def test_rejecting_the_same_candidate_twice_is_a_no_op(self):
        a_store = fx.store()
        first = self._ambiguous(a_store)
        reject(
            a_store,
            first,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="req-dup-a",
            expected_version=0,
        )
        revision = a_store.current_revision()
        result = a_store.append(
            RejectCandidate(
                actor_id=fx.ACTOR,
                client_request_id="req-dup-b",
                expected_version=0,
                raw_identity_key=first.identity.raw_identity_key,
                raw_product_identity=first.identity.raw_product_identity,
                candidate_namespace=first.candidates[0].namespace,
                candidate_code=first.candidates[0].source_product_code,
                evidence_fingerprint=first.evidence_fingerprint,
            )
        )
        assert result.outcome is AppendOutcome.NO_CHANGE
        assert a_store.current_revision() == revision


class TestG19Idempotency:
    """`CHECK-105D-19` — bốn fixture, hai lớp."""

    def test_fixture_1_reimporting_the_same_file_changes_nothing(self, tmp_path):
        a_store = fx.store(tmp_path)
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        revision_before = a_store.current_revision()
        events_before = len(a_store.events())

        rows = [fx.row("TRK-A100", order_id=f"ORD-{i}") for i in range(3)]
        signatures = []
        for _ in range(2):
            result = resolve_batch(
                rows,
                registry=HistoricalConfirmedRegistry(),
                resolver_factory=lambda: fx.resolver(
                    a_store, fx.tracking_snapshot(ROWS_V1)
                ),
            )
            signatures.append(
                tuple(
                    (r.identity.raw_identity_key, r.resolution_method)
                    for r in result.resolutions
                )
            )

        assert signatures[0] == signatures[1]
        assert signatures[0][0][1] is ResolutionMethod.ALIAS_EXACT
        assert a_store.current_revision() == revision_before
        assert len(a_store.events()) == events_before

    def test_fixture_2_the_same_client_request_id_returns_the_old_result(self):
        a_store = fx.store()
        first = _confirm_seed(
            a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100", request_id="req-x"
        )
        revision = a_store.current_revision()

        again = _confirm_seed(
            a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100", request_id="req-x"
        )

        assert again.outcome is AppendOutcome.ALREADY_APPLIED
        assert again.mapping.mapping_id == first.mapping.mapping_id
        assert a_store.current_revision() == revision

    def test_fixture_3_a_new_request_that_changes_nothing_is_a_no_op(self):
        a_store = fx.store()
        _confirm_seed(
            a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100", request_id="req-a"
        )
        revision = a_store.current_revision()

        result = a_store.append(
            ConfirmMapping(
                actor_id=fx.ACTOR,
                client_request_id="req-b",
                expected_version=1,
                raw_identity_key=raw_identity_key("TRK-A100"),
                raw_product_identity="TRK-A100",
                target=CanonicalProductIdentity(
                    namespace=Namespace.TRACKING, source_product_code="TRK-A100"
                ),
                evidence=Evidence(
                    matched_on=MatchedOn.RAW_KEY,
                    matched_value="TRK-A100",
                    candidate_set_ids=("TRACKING:TRK-A100",),
                ),
                resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
            )
        )

        assert result.outcome is AppendOutcome.NO_CHANGE
        assert a_store.current_revision() == revision

    def test_fixture_4_a_retry_after_failure_does_not_double_the_scope(self):
        """`INV-71` — `affected_count` tính lại, KHÔNG cộng dồn."""
        a_store = fx.store()
        product = "Sản phẩm nhiều dòng"
        rows = [fx.row(product, order_id=f"ORD-{i}") for i in range(4)]
        # Cố ý AMBIGUOUS (hai entry cùng khớp) để cần một confirmation thật —
        # một identity auto-resolve không có candidate nào để xác nhận.
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-A100", "Sản phẩm nhiều dòng", (), True),
                ("TRK-A101", "Sản phẩm nhiều dòng", (), True),
            )
        )
        batch = resolve_batch(
            rows,
            registry=HistoricalConfirmedRegistry(),
            resolver_factory=lambda: fx.resolver(a_store, snapshot),
        )
        resolution = batch.resolutions[0]

        first = confirm(
            a_store,
            resolution,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="req-retry",
            expected_version=0,
        )
        retry = confirm(
            a_store,
            resolution,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="req-retry",
            expected_version=0,
        )

        assert retry.outcome is AppendOutcome.ALREADY_APPLIED
        assert (
            retry.event.affected_scope.affected_line_count
            == first.event.affected_scope.affected_line_count
            == 4
        )


class TestG20ConcurrencyAndActor:
    """`CHECK-105D-20` — Phần A concurrency, Phần B actor REQUIRED."""

    def test_part_a_conflicting_confirmations_are_refused_not_merged(self):
        a_store = fx.store()
        _confirm_seed(
            a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100", request_id="user-a"
        )
        revision = a_store.current_revision()

        with pytest.raises(MappingVersionConflict) as excinfo:
            a_store.append(
                ConfirmMapping(
                    actor_id="nv.kho.02",
                    client_request_id="user-b",
                    expected_version=0,  # User B đọc trước khi A ghi.
                    raw_identity_key=raw_identity_key("TRK-A100"),
                    raw_product_identity="TRK-A100",
                    target=CanonicalProductIdentity(
                        namespace=Namespace.TRACKING,
                        source_product_code="TRK-B200",
                    ),
                    evidence=Evidence(
                        matched_on=MatchedOn.RAW_KEY,
                        matched_value="TRK-A100",
                        candidate_set_ids=("TRACKING:TRK-B200",),
                    ),
                    resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
                )
            )

        assert excinfo.value.current_state is not None
        assert a_store.current_revision() == revision
        assert (
            a_store.read_active_mapping(
                "REPORTS_SALES", "TRK-A100"
            ).source_product_code
            == "TRK-A100"
        )

    def test_part_a_aggregate_boundary_is_per_identity_not_whole_store(self):
        """`INV-61` — hai identity khác nhau không khoá lẫn nhau."""
        a_store = fx.store()
        _confirm_seed(
            a_store, "SP-1", Namespace.TRACKING, "TRK-A100", request_id="req-1"
        )
        result = _confirm_seed(
            a_store, "SP-2", Namespace.TRACKING, "TRK-B200", request_id="req-2"
        )
        assert result.outcome is AppendOutcome.APPLIED
        assert result.new_version == 1

    @pytest.mark.parametrize("actor", [None, "", "   ", "\t\n"])
    def test_part_b_every_state_changing_command_refuses_a_missing_actor(
        self, actor
    ):
        """`INV-72` — rỗng và chỉ-khoảng-trắng đều là THIẾU."""
        a_store = fx.store()
        revision = a_store.current_revision()

        with pytest.raises(MissingActorError):
            SetPending(
                actor_id=actor,
                client_request_id="req-no-actor",
                expected_version=0,
                raw_identity_key="k",
                raw_product_identity="k",
            )
        assert a_store.current_revision() == revision

    def test_part_b_no_command_type_can_default_its_actor(self):
        from app.modules.product.identity.commands import (
            BootstrapMapping,
            ConfirmCrossSystem,
            CorrectCrossSystem,
            CorrectMapping,
        )

        common = dict(client_request_id="req", expected_version=0)
        cases = [
            (SetPending, dict(raw_identity_key="k", raw_product_identity="k")),
            (MarkStale, dict(raw_identity_key="k", raw_product_identity="k")),
            (
                RejectCandidate,
                dict(
                    raw_identity_key="k",
                    raw_product_identity="k",
                    candidate_namespace=Namespace.TRACKING,
                    candidate_code="C",
                    evidence_fingerprint="f",
                ),
            ),
            (
                ConfirmMapping,
                dict(
                    raw_identity_key="k",
                    raw_product_identity="k",
                    target=CanonicalProductIdentity(
                        namespace=Namespace.TRACKING, source_product_code="C"
                    ),
                    evidence=Evidence(
                        matched_on=MatchedOn.RAW_KEY,
                        matched_value="k",
                        candidate_set_ids=(),
                    ),
                ),
            ),
        ]
        for command_type, kwargs in cases:
            with pytest.raises(MissingActorError):
                command_type(actor_id="", **common, **kwargs)

        with pytest.raises(MissingActorError):
            ConfirmCrossSystem(
                actor_id="  ",
                **common,
                tracking_code="T",
                public_purchase_code="P",
                evidence=Evidence(
                    matched_on=MatchedOn.MANUAL_SEARCH,
                    matched_value="T",
                    candidate_set_ids=(),
                ),
            )
        with pytest.raises(MissingActorError):
            CorrectCrossSystem(
                actor_id="",
                **common,
                tracking_code="T",
                public_purchase_code="P",
                reason="r",
                evidence=Evidence(
                    matched_on=MatchedOn.MANUAL_SEARCH,
                    matched_value="T",
                    candidate_set_ids=(),
                ),
            )
        with pytest.raises(MissingActorError):
            CorrectMapping(
                actor_id="",
                **common,
                raw_identity_key="k",
                raw_product_identity="k",
                reason="r",
                target=CanonicalProductIdentity(
                    namespace=Namespace.TRACKING, source_product_code="C"
                ),
                evidence=Evidence(
                    matched_on=MatchedOn.RAW_KEY,
                    matched_value="k",
                    candidate_set_ids=(),
                ),
            )
        with pytest.raises(MissingActorError):
            BootstrapMapping(
                actor_id="",
                **common,
                raw_identity_key="k",
                raw_product_identity="k",
                target=CanonicalProductIdentity(
                    namespace=Namespace.TRACKING, source_product_code="C"
                ),
                evidence=Evidence(
                    matched_on=MatchedOn.RAW_KEY,
                    matched_value="k",
                    candidate_set_ids=(),
                ),
            )


class TestG29G30Namespace:
    """`CHECK-105D-29` bất biến LƯU TRỮ, `CHECK-105D-30` bất biến SO SÁNH."""

    def test_g29_namespace_is_persisted_not_inferred_on_read(self, tmp_path):
        a_store = fx.store(tmp_path)
        _confirm_seed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")

        record = json.loads(
            (tmp_path / "identity.log.jsonl").read_text(encoding="utf-8").splitlines()[0]
        )
        assert record["new_value"]["namespace"] == "TRACKING"

        reopened = JsonlProductIdentityStore(log_path=tmp_path / "identity.log.jsonl")
        assert (
            reopened.read_active_mapping("REPORTS_SALES", "TRK-A100").namespace
            is Namespace.TRACKING
        )

    def test_g29_mapping_records_are_frozen_no_in_place_update(self):
        a_store = fx.store()
        mapping = _confirm_seed(
            a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100"
        ).mapping
        with pytest.raises(Exception):
            mapping.namespace = Namespace.PUBLIC_PURCHASE

    def test_g29_changing_the_namespace_creates_a_new_record_and_supersedes(self):
        a_store = fx.store()
        first = _confirm_seed(
            a_store, "SP-X", Namespace.TRACKING, "CODE-X", request_id="r1"
        )
        from app.modules.product.identity.commands import CorrectMapping

        second = a_store.append(
            CorrectMapping(
                actor_id=fx.ACTOR,
                client_request_id="r2",
                expected_version=1,
                reason="xác định lại là hàng mua ngoài",
                raw_identity_key=raw_identity_key("SP-X"),
                raw_product_identity="SP-X",
                target=CanonicalProductIdentity(
                    namespace=Namespace.PUBLIC_PURCHASE, source_product_code="CODE-X"
                ),
                evidence=Evidence(
                    matched_on=MatchedOn.MANUAL_SEARCH,
                    matched_value="SP-X",
                    candidate_set_ids=("PUBLIC_PURCHASE:CODE-X",),
                ),
                resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
            )
        )

        assert second.mapping.mapping_id != first.mapping.mapping_id
        assert second.mapping.supersedes == first.mapping.mapping_id
        assert second.mapping.namespace is Namespace.PUBLIC_PURCHASE

    def test_g30_same_code_different_namespace_do_not_collide(self):
        a_store = fx.store()
        _confirm_seed(a_store, "Hàng của Tracking", Namespace.TRACKING, "X", request_id="r1")
        _confirm_seed(
            a_store, "Hàng mua ngoài", Namespace.PUBLIC_PURCHASE, "X", request_id="r2"
        )

        tracking = a_store.read_active_mapping("REPORTS_SALES", "Hàng của Tracking")
        public = a_store.read_active_mapping("REPORTS_SALES", "Hàng mua ngoài")

        assert tracking.source_product_code == public.source_product_code == "X"
        assert tracking.namespace is not public.namespace
        assert tracking.identity_tuple != public.identity_tuple

    def test_g30_identity_equality_uses_the_full_tuple(self):
        a = CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code="X"
        )
        b = CanonicalProductIdentity(
            namespace=Namespace.PUBLIC_PURCHASE, source_product_code="X"
        )
        assert a != b
        assert hash(a) != hash(b)
        assert len({a, b}) == 2
