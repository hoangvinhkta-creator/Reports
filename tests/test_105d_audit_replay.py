"""TASK-105D — correction audit, provenance, actor semantics, replay và bề mặt
vận hành Phase 1.

Gate: `CHECK-105D-14`, `-18`, `-21`, `-22`.
Adversarial: `L` (correction), `S` (declared actor).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.modules.product.identity import cli
from app.modules.product.identity.audit import (
    ACTOR_DISCLOSURE,
    EventType,
    FORBIDDEN_ACTOR_PHRASES,
    MappingAuditEvent,
    MissingActorError,
    MissingReasonError,
    REASON_REQUIRED_TYPES,
)
from app.modules.product.identity.binding import (
    IncompleteBindingError,
    ReportReplay,
    ResolutionBinding,
    replay_signature,
    require_binding,
)
from app.modules.product.identity.commands import ConfirmMapping, CorrectMapping
from app.modules.product.identity.evidence import (
    Evidence,
    MatchedOn,
    RANKING_METHOD_ID,
    ResolutionMethod,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
    PendingProduct,
    Resolved,
)
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.mapping import MappingStatus
from app.modules.product.identity.public_purchase import (
    PublicPurchaseSourceRepository,
)
from app.modules.product.identity.registry import HistoricalConfirmedRegistry
from app.modules.product.identity.resolver import distinct_identities
from app.modules.product.identity.tracking_catalog import TrackingSnapshotRepository
from tests.support import identity_fixtures as fx

ROWS = (("TRK-A100", "Nồi chiên TRK-A100", (), True),)


def _seed(a_store, product_raw, code, *, request_id="seed-1", namespace=None):
    return a_store.append(
        ConfirmMapping(
            actor_id=fx.ACTOR,
            client_request_id=request_id,
            expected_version=0,
            raw_identity_key=raw_identity_key(product_raw),
            raw_product_identity=product_raw,
            target=CanonicalProductIdentity(
                namespace=namespace or Namespace.TRACKING, source_product_code=code
            ),
            evidence=Evidence(
                matched_on=MatchedOn.RAW_KEY,
                matched_value=product_raw,
                candidate_set_ids=(f"TRACKING:{code}",),
                ranking_method_id=RANKING_METHOD_ID,
            ),
            resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
        )
    )


def _correct(a_store, product_raw, new_code, *, reason="đối chiếu lại chứng từ"):
    return a_store.append(
        CorrectMapping(
            actor_id="quan.tri.01",
            client_request_id=f"req-correct-{new_code}",
            expected_version=1,
            reason=reason,
            raw_identity_key=raw_identity_key(product_raw),
            raw_product_identity=product_raw,
            target=CanonicalProductIdentity(
                namespace=Namespace.TRACKING, source_product_code=new_code
            ),
            evidence=Evidence(
                matched_on=MatchedOn.MANUAL_SEARCH,
                matched_value=product_raw,
                candidate_set_ids=(f"TRACKING:{new_code}",),
            ),
            resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
        )
    )


class TestG14RawNameIsImmutable:
    """`CHECK-105D-14` — `product_raw` giống hệt byte-wise qua ba bước."""

    def test_confirm_then_correct_then_reimport_never_rewrites_the_raw_name(self):
        raw = "  Nồi  chiên   không dầu XL-500 (bản đặc biệt)  "
        a_store = fx.store()

        first = _seed(a_store, raw, "TRK-A100")
        assert first.mapping.raw_product_identity == raw

        second = _correct(a_store, raw, "TRK-B200")
        assert second.mapping.raw_product_identity == raw

        stored = a_store.read_active_mapping(
            "REPORTS_SALES", raw_identity_key(raw)
        )
        assert stored.raw_product_identity == raw
        assert stored.raw_product_identity.encode("utf-8") == raw.encode("utf-8")

    def test_the_derived_keys_never_write_back_into_the_raw_name(self):
        raw = "Máy   lọc  KHÔNG khí AP-100"
        a_store = fx.store()
        mapping = _seed(a_store, raw, "TRK-A100").mapping

        assert mapping.raw_product_identity == raw
        assert mapping.raw_identity_key == "Máy lọc KHÔNG khí AP-100"
        assert mapping.normalized_matching_aid == "máy lọc không khí ap-100"
        assert mapping.raw_identity_key != mapping.raw_product_identity

    def test_diacritics_survive_the_identity_key(self):
        """`INV-26` — cấm bỏ dấu tiếng Việt."""
        raw = "Bếp từ đôi ĐẶC BIỆT"
        assert raw_identity_key(raw) == raw
        assert "đ" in raw_identity_key(raw).lower()


class TestG18CorrectionAuditKeepsHistory:
    """`CHECK-105D-18` — bốn fixture."""

    def test_fixture_1_correction_supersedes_and_keeps_both_records(self):
        raw = "Sản phẩm cần sửa"
        a_store = fx.store()
        first = _seed(a_store, raw, "TRK-A100")
        second = _correct(a_store, raw, "TRK-B200")

        assert second.mapping.supersedes == first.mapping.mapping_id
        records = [
            event.new_value
            for event in a_store.events()
            if event.new_value and "mapping_id" in event.new_value
        ]
        assert len(records) == 2
        assert {r["source_product_code"] for r in records} == {
            "TRK-A100",
            "TRK-B200",
        }
        correct_events = [
            e for e in a_store.events() if e.event_type is EventType.CORRECT_MAPPING
        ]
        assert len(correct_events) == 1
        assert correct_events[0].old_value["source_product_code"] == "TRK-A100"
        assert correct_events[0].new_value["source_product_code"] == "TRK-B200"

    def test_fixture_2_a_correction_without_a_reason_is_refused(self):
        raw = "Sản phẩm cần sửa"
        a_store = fx.store()
        _seed(a_store, raw, "TRK-A100")
        revision = a_store.current_revision()

        with pytest.raises(MissingReasonError):
            _correct(a_store, raw, "TRK-B200", reason="   ")
        assert a_store.current_revision() == revision

    def test_fixture_3_a_pinned_report_does_not_change_after_a_correction(
        self, tmp_path
    ):
        """`INV-77` — correction tác động TƯƠNG LAI, không viết lại quá khứ."""
        raw = "TRK-A100"
        a_store = fx.store(tmp_path)
        _seed(a_store, raw, "TRK-A100")
        replay, binding, rows = _replay_setup(a_store, raw)
        before = replay_signature(replay.replay(rows, binding))

        _correct(a_store, raw, "TRK-B200")

        assert replay_signature(replay.replay(rows, binding)) == before
        # Nhưng một lần chạy MỚI (không ghim) thấy correction.
        fresh = ResolutionBinding(
            binding_id="BND-2",
            report_run_id="RUN-2",
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
            mapping_store_revision=a_store.current_revision(),
            registry_revision=0,
            bound_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
            bound_by=fx.ACTOR,
        )
        assert replay_signature(replay.replay(rows, fresh)) != before

    def test_fixture_4_an_explicit_repin_is_audited_and_needs_a_reason(self):
        assert EventType.REPIN_REPORT in REASON_REQUIRED_TYPES
        scope = _scope()
        with pytest.raises(MissingReasonError):
            MappingAuditEvent(
                event_id="E1",
                revision=1,
                event_type=EventType.REPIN_REPORT,
                aggregate_type=__import__(
                    "app.modules.product.identity.audit",
                    fromlist=["AggregateType"],
                ).AggregateType.PRODUCT_IDENTITY_MAPPING,
                aggregate_id="A",
                actor_id=fx.ACTOR,
                occurred_at=datetime.now(timezone.utc),
                old_value=None,
                new_value={},
                affected_scope=scope,
                client_request_id="req",
                resulting_version=1,
            )

    def test_audit_answers_who_when_from_what_to_what_why_and_scope(self):
        """`INV-75` — trả lời được CHỈ TỪ LOG."""
        raw = "Sản phẩm cần sửa"
        a_store = fx.store()
        _seed(a_store, raw, "TRK-A100")
        _correct(a_store, raw, "TRK-B200", reason="hoá đơn gốc ghi mã khác")

        event = a_store.events()[-1]
        record = event.to_record()

        assert record["actor_id"] == "quan.tri.01"
        assert record["occurred_at"]
        assert record["old_value"]["source_product_code"] == "TRK-A100"
        assert record["new_value"]["source_product_code"] == "TRK-B200"
        assert record["reason"] == "hoá đơn gốc ghi mã khác"
        assert "affected_scope" in record
        assert record["affected_scope"]["computed_at_revision"] >= 0


class TestG21ProvenanceActorAndReplay:
    """`CHECK-105D-21` — Phần A provenance, B actor, C binding/replay."""

    def test_part_a_every_outcome_variant_carries_full_provenance(self):
        a_store = fx.store()
        snapshot = fx.tracking_snapshot(ROWS)

        resolver = fx.resolver(a_store, snapshot)
        resolved, = distinct_identities([fx.row("TRK-A100")])
        resolved_result = resolver.resolve(resolved)
        assert isinstance(resolved_result.outcome, Resolved)
        provenance = resolved_result.outcome.provenance
        for field in (
            "raw_product_identity",
            "resolution_method",
            "resolved_at",
            "mapping_source",
            "namespace",
            "source_product_code",
            "pp_version_id",
            "tracking_capture_id",
        ):
            assert getattr(provenance, field) is not None, field

        pending, = distinct_identities([fx.row("vô danh hoàn toàn")])
        pending_result = resolver.resolve(pending)
        assert isinstance(pending_result.outcome, PendingProduct)
        assert pending_result.outcome.reason_code is not None
        assert pending_result.outcome.attempted_sources
        assert pending_result.outcome.provenance.namespace is None

    def test_part_b_an_audit_event_without_an_actor_cannot_exist(self):
        with pytest.raises(MissingActorError):
            MappingAuditEvent(
                event_id="E1",
                revision=1,
                event_type=EventType.CONFIRM_MAPPING,
                aggregate_type=__import__(
                    "app.modules.product.identity.audit",
                    fromlist=["AggregateType"],
                ).AggregateType.PRODUCT_IDENTITY_MAPPING,
                aggregate_id="A",
                actor_id="   ",
                occurred_at=datetime.now(timezone.utc),
                old_value=None,
                new_value={},
                affected_scope=_scope(),
                client_request_id="req",
                resulting_version=1,
            )

    def test_part_b_no_artifact_calls_the_phase_1_actor_authenticated(self):
        """`INV-73` — quét văn bản trên artifact/chuỗi hiển thị do task sinh ra."""
        a_store = fx.store()
        _seed(a_store, "TRK-A100", "TRK-A100")
        resolver = fx.resolver(a_store, fx.tracking_snapshot(ROWS))
        identity, = distinct_identities([fx.row("TRK-A100")])

        surfaces = [
            ACTOR_DISCLOSURE,
            cli.render_candidates(resolver.resolve(identity)),
            cli.build_parser().format_help(),
            str(a_store.events()[-1].to_record()),
            str(a_store.export_bundle()["manifest"]),
        ]
        for surface in surfaces:
            lowered = surface.casefold()
            for phrase in FORBIDDEN_ACTOR_PHRASES:
                assert phrase.casefold() not in lowered, (
                    f"INV-73: bề mặt hiển thị chứa cụm bị cấm {phrase!r}"
                )

    def test_part_b_the_disclosure_states_the_real_capability_boundary(self):
        assert "khai báo" in ACTOR_DISCLOSURE
        assert "chưa có xác thực" in ACTOR_DISCLOSURE
        assert "actor_disclosure" in _any_event_record()

    def test_part_c_a_binding_missing_any_component_is_a_hard_error(self):
        base = dict(
            binding_id="B",
            report_run_id="R",
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
            mapping_store_revision=1,
            registry_revision=1,
            bound_at=datetime.now(timezone.utc),
            bound_by=fx.ACTOR,
        )
        for missing in (
            "pp_version_id",
            "tracking_capture_id",
            "mapping_store_revision",
            "registry_revision",
        ):
            kwargs = dict(base)
            kwargs[missing] = None
            with pytest.raises(IncompleteBindingError, match="INV-55"):
                ResolutionBinding(**kwargs)

    def test_part_c_no_binding_means_refuse_not_fallback_to_latest(self):
        with pytest.raises(IncompleteBindingError, match="INV-57"):
            require_binding(None)

    def test_part_c_replay_is_identical_after_store_catalog_and_price_change(
        self, tmp_path
    ):
        """Fixture (5) — so khớp output ĐẦY ĐỦ, không chỉ một trường."""
        raw = "TRK-A100"
        a_store = fx.store(tmp_path)
        _seed(a_store, raw, "TRK-A100")
        replay, binding, rows = _replay_setup(a_store, raw)
        before = replay_signature(replay.replay(rows, binding))

        # Đổi cả ba: store, catalog, và nguồn giá.
        _correct(a_store, raw, "TRK-B200")
        replay.tracking_repository.register(
            fx.tracking_snapshot(
                (("TRK-A100", "Tên đã đổi hẳn", (), False),), capture_id=fx.CAPTURE_B
            )
        )
        replay.pp_repository.publish(
            fx.pp_version(
                [{"product_code": "PPC-MOI", "product_name": "Hàng mới"}],
                prices=[
                    {
                        "product_key": "PPC-MOI",
                        "effective_from": "2026-10-01",
                        "effective_to": "2026-12-31",
                        "purchase_price": "9999999",
                    }
                ],
                version_id=fx.PP_V2,
            )
        )

        assert replay_signature(replay.replay(rows, binding)) == before

    def test_part_c_a_missing_pinned_version_is_a_hard_error(self, tmp_path):
        from app.modules.product.identity.public_purchase import (
            SourceVersionNotFoundError,
        )
        from app.modules.product.identity.tracking_catalog import (
            TrackingCaptureNotFoundError,
        )

        a_store = fx.store(tmp_path)
        _seed(a_store, "TRK-A100", "TRK-A100")
        replay, _, rows = _replay_setup(a_store, "TRK-A100")

        missing_pp = ResolutionBinding(
            binding_id="B",
            report_run_id="R",
            pp_version_id="PP-KHONG-TON-TAI",
            tracking_capture_id=fx.CAPTURE_A,
            mapping_store_revision=1,
            registry_revision=0,
            bound_at=datetime.now(timezone.utc),
            bound_by=fx.ACTOR,
        )
        with pytest.raises(SourceVersionNotFoundError, match="KHÔNG fallback"):
            replay.replay(rows, missing_pp)

        missing_capture = ResolutionBinding(
            binding_id="B",
            report_run_id="R",
            pp_version_id=fx.PP_V1,
            tracking_capture_id="TRK-KHONG-TON-TAI",
            mapping_store_revision=1,
            registry_revision=0,
            bound_at=datetime.now(timezone.utc),
            bound_by=fx.ACTOR,
        )
        with pytest.raises(TrackingCaptureNotFoundError, match="KHÔNG fallback"):
            replay.replay(rows, missing_capture)


class TestG22KeyboardFirstOnPhase1Surface:
    """`CHECK-105D-22` — ba fixture trên bề mặt CLI THẬT của Phase 1."""

    def test_fixture_1_a_whole_batch_runs_headless(self, monkeypatch, tmp_path):
        """Chạy trọn batch, cả bốn loại command, không display, không con trỏ."""
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

        a_store = fx.store(tmp_path)
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-M1", "Máy lọc không khí AP-100", (), True),
                ("TRK-M2", "Máy lọc không khí AP-200", (), True),
                ("TRK-A100", "Nồi chiên TRK-A100", (), True),
            )
        )
        resolver = fx.resolver(a_store, snapshot)
        ambiguous, = distinct_identities([fx.row("Máy lọc không khí AP-300")])
        resolution = resolver.resolve(ambiguous)

        assert cli.render_candidates(resolution)
        cli.reject(
            a_store,
            resolution,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="cli-reject",
            expected_version=0,
        )
        cli.confirm(
            a_store,
            resolution,
            candidate_rank=2,
            actor_id=fx.ACTOR,
            client_request_id="cli-confirm",
            expected_version=0,
        )
        cli.confirm_cross_system(
            a_store,
            tracking_code="TRK-A100",
            public_purchase_code="PPC-1000",
            actor_id=fx.ACTOR,
            client_request_id="cli-cross",
            expected_version=0,
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )
        other, = distinct_identities([fx.row("một thứ vô danh")])
        cli.set_pending(
            a_store,
            resolver.resolve(other),
            actor_id=fx.ACTOR,
            client_request_id="cli-pending",
            expected_version=0,
        )

        kinds = {e.event_type for e in a_store.events()}
        assert {
            EventType.CONFIRM_MAPPING,
            EventType.REJECT_CANDIDATE,
            EventType.CONFIRM_CROSS_SYSTEM,
            EventType.SET_PENDING,
        } <= kinds

    def test_fixture_2_the_module_imports_no_gui_library(self):
        import pathlib
        import re

        forbidden = re.compile(
            r"^\s*(?:import|from)\s+"
            r"(tkinter|PyQt\w*|PySide\w*|wx|kivy|pygame|flask|django|fastapi"
            r"|streamlit|gradio|selenium|playwright|pynput|mouse|pyautogui)\b",
            re.MULTILINE,
        )
        root = pathlib.Path("app/modules/product")
        for path in root.rglob("*.py"):
            assert not forbidden.search(path.read_text(encoding="utf-8")), path

    def test_fixture_3_every_confirmation_action_has_a_non_pointer_surface(self):
        from app.modules.product.identity.audit import CONFIRMATION_ACTION_TYPES

        surfaces = cli.callable_surfaces()
        assert set(surfaces) == set(CONFIRMATION_ACTION_TYPES)
        assert set(cli.ACTION_COMMANDS) == set(CONFIRMATION_ACTION_TYPES)
        for action in surfaces.values():
            assert callable(action)

        parser_help = cli.build_parser().format_help()
        for name in cli.ACTION_COMMANDS.values():
            assert name in parser_help


def _scope():
    from app.modules.product.identity.audit import AffectedScope

    return AffectedScope(
        distinct_identity_count=1,
        affected_order_ids=(),
        affected_line_count=0,
        computed_at_revision=0,
    )


def _any_event_record() -> str:
    a_store = fx.store()
    _seed(a_store, "TRK-A100", "TRK-A100")
    return str(a_store.events()[-1].to_record())


def _replay_setup(a_store, raw):
    tracking_repo = TrackingSnapshotRepository()
    tracking_repo.register(fx.tracking_snapshot(ROWS, capture_id=fx.CAPTURE_A))
    pp_repo = PublicPurchaseSourceRepository()
    pp_repo.publish(fx.pp_version())
    registry = HistoricalConfirmedRegistry()

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
    return replay, binding, [fx.row(raw)]
