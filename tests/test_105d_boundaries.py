"""TASK-105D — ranh giới kiến trúc, nguồn Public Purchase hợp nhất,
cross-system mapping, metrics, migration/rollback và Golden.

Gate: `CHECK-105D-15`, `-16`, `-17`, `-25`, `-28`, `-31`, `-32`.
Adversarial: `H`/`I` (namespace), `J` (cross-system boundary), `T` (unified PP
version/binding).
HARDENING `HB-105D-F2-03`: `INV-79`…`INV-82` (migration/rollback), `INV-84`/
`INV-85`/`INV-86` (metrics).
"""

from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

from app.modules.product.identity import metrics
from app.modules.product.identity.cli import confirm_cross_system
from app.modules.product.identity.commands import ConfirmCrossSystem, ConfirmMapping
from app.modules.product.identity.cross_system import CrossSystemConflictError
from app.modules.product.identity.evidence import (
    Evidence,
    MatchedOn,
    RANKING_METHOD_ID,
    ResolutionMethod,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    HistoricalConfirmed,
    Namespace,
    PendingProduct,
    RequiresConfirmation,
    Resolved,
    outcome_field_names,
)
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.mapping import (
    PRICE_LIKE_FIELD_NAMES,
    mapping_field_names,
)
from app.modules.product.identity.public_purchase import (
    PublicPurchaseSourceError,
    PublicPurchaseSourceLoader,
    PublicPurchaseSourceRepository,
)
from app.modules.product.identity.registry import HistoricalConfirmedRegistry
from app.modules.product.identity.service import (
    lookup_public_purchase_code,
    resolve_batch,
)
from app.modules.product.identity.store import AppendOutcome
from tests.support import identity_fixtures as fx

MODULE_ROOT = pathlib.Path("app/modules/product/identity")
FROZEN_PRICE_PROVIDER = "app/modules/pricing/file_price_provider.py"


def _cross_evidence(code: str) -> Evidence:
    return Evidence(
        matched_on=MatchedOn.MANUAL_SEARCH,
        matched_value=code,
        candidate_set_ids=(f"PUBLIC_PURCHASE:{code}",),
        ranking_method_id=RANKING_METHOD_ID,
    )


class TestG15MappingSchemaHasNoPrice:
    """`CHECK-105D-15` — assertion CẤU TRÚC, cả trên bản ghi đã persist."""

    def test_the_dataclass_has_no_price_field(self):
        assert not (mapping_field_names() & PRICE_LIKE_FIELD_NAMES)

    def test_the_persisted_record_has_no_price_key(self, tmp_path):
        import json

        a_store = fx.store(tmp_path)
        a_store.append(
            ConfirmMapping(
                actor_id=fx.ACTOR,
                client_request_id="req-1",
                expected_version=0,
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

        record = json.loads(
            (tmp_path / "identity.log.jsonl").read_text(encoding="utf-8").splitlines()[0]
        )
        keys = set(record["new_value"])
        assert not (keys & PRICE_LIKE_FIELD_NAMES)
        assert not any("price" in key.lower() for key in keys)


class TestG16PriceProviderBoundary:
    """`CHECK-105D-16` — import-graph sạch, outcome post-cutover không mang giá."""

    def test_the_module_imports_no_price_provider(self):
        forbidden = re.compile(
            r"^\s*(?:import|from)\s+.*"
            r"(file_price_provider|price_engine|PendingPriceProvider"
            r"|FilePriceProvider|app\.modules\.pricing)",
            re.MULTILINE,
        )
        for path in MODULE_ROOT.rglob("*.py"):
            assert not forbidden.search(path.read_text(encoding="utf-8")), path

    def test_post_cutover_outcomes_carry_no_price_field(self):
        for variant in (Resolved, RequiresConfirmation, PendingProduct):
            names = outcome_field_names(variant)
            assert "price" not in names
            assert not (names & PRICE_LIKE_FIELD_NAMES)

    def test_only_the_pre_cutover_variant_carries_a_price_and_it_comes_from_the_registry(
        self,
    ):
        assert "price" in outcome_field_names(HistoricalConfirmed)

        entry = fx.registry_entry(price="1234000")
        registry = HistoricalConfirmedRegistry()
        from app.modules.product.identity.commands import ConfirmHistoricalEntry

        registry.append(
            ConfirmHistoricalEntry(
                actor_id=fx.ACTOR,
                client_request_id="req-h",
                expected_version=0,
                entry_id=entry.entry_id,
                entry=entry,
            )
        )
        spy = fx.CallSpy()
        result = resolve_batch(
            [
                fx.row(
                    entry.raw_product_identity,
                    order_id=entry.order_id,
                    sale_date=fx.PRE_CUTOVER,
                )
            ],
            registry=registry,
            resolver_factory=spy,
        )

        outcome = result.historical[0][1]
        assert outcome.price == entry.confirmed_purchase_price
        assert outcome.provenance.price_provenance == "HISTORICAL_CONFIRMED_REPORT"
        assert spy.calls == 0


class TestG17TrackingIsNeverMutated:
    """`CHECK-105D-17` — 0 lệnh ghi, capture bất biến, không chạm mạng."""

    def test_app_modules_never_import_a_network_library(self):
        forbidden = re.compile(
            r"^\s*(?:import|from)\s+"
            r"(requests|urllib|http|httpx|socket|firebase\w*|google\.cloud"
            r"|boto3|aiohttp|websocket\w*|pyrebase)\b",
            re.MULTILINE,
        )
        for path in pathlib.Path("app/modules").rglob("*.py"):
            assert not forbidden.search(path.read_text(encoding="utf-8")), path

    def test_the_module_does_not_know_rtdb_exists(self):
        for path in MODULE_ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "firebaseio" not in text
            assert "https://" not in text.replace("https://code", "")

    def test_no_write_surface_to_tracking_exists(self):
        """Snapshot chỉ có `register`/`get`; không có `push`/`update`/`set`."""
        from app.modules.product.identity.tracking_catalog import (
            TrackingCatalogSnapshot,
            TrackingSnapshotRepository,
        )

        forbidden = {"push", "update", "set", "write", "put", "patch", "delete"}
        for cls in (TrackingSnapshotRepository, TrackingCatalogSnapshot):
            names = {n.lower() for n in dir(cls) if not n.startswith("_")}
            assert not (names & forbidden), cls

    def test_every_drift_fixture_runs_with_zero_writes_to_tracking(self):
        """Fixture (3) — Tracking fake ghi-nhận-mọi-lệnh-ghi, đếm == 0."""

        class RecordingTracking:
            def __init__(self, snapshot):
                self._snapshot = snapshot
                self.writes = 0

            def __getattr__(self, name):
                if name in {"push", "update", "set", "write", "delete"}:
                    self.writes += 1
                    raise AssertionError("INV-11: TASK-105D không ghi vào Tracking")
                return getattr(self._snapshot, name)

        a_store = fx.store()
        for rows in (
            (("TRK-A100", "Tên cũ", (), True),),
            (("TRK-A100", "Tên MỚI", (), True),),
            (("TRK-A100", "Tên cũ", (), False),),
        ):
            recorder = RecordingTracking(fx.tracking_snapshot(rows))
            resolver = fx.resolver(a_store, recorder)
            from app.modules.product.identity.resolver import distinct_identities

            identity, = distinct_identities([fx.row("TRK-A100")])
            resolver.resolve(identity)
            assert recorder.writes == 0


class TestG28UnifiedPublicPurchaseSource:
    """`CHECK-105D-28` — Phần A + `B1`…`B6`, bảy fixture."""

    def test_fixture_1_a_public_purchase_identity_is_valid_without_tracking(self):
        from app.modules.product.identity.resolver import distinct_identities

        a_store = fx.store()
        resolver = fx.resolver(
            a_store,
            fx.tracking_snapshot(()),
            fx.pp_version([{"product_code": "PPC-777", "product_name": "Hàng ngoài"}]),
        )
        identity, = distinct_identities([fx.row("PPC-777")])
        result = resolver.resolve(identity)

        assert isinstance(result.outcome, Resolved)
        assert result.outcome.identity.namespace is Namespace.PUBLIC_PURCHASE
        assert len(resolver.tracking.rows) == 0

    def test_fixture_2_a_price_key_absent_from_identity_rows_fails_to_load(self):
        """`INV-06` — lỗi lúc LOAD, không phải lúc tính giá/KPI/lương."""
        with pytest.raises(PublicPurchaseSourceError) as excinfo:
            fx.pp_version(
                [{"product_code": "PPC-1", "product_name": "A"}],
                prices=[
                    {
                        "product_key": "PPC-KHONG-CO",
                        "effective_from": "2026-09-01",
                        "effective_to": "2026-12-31",
                        "purchase_price": "1",
                    }
                ],
            )
        assert excinfo.value.reason == "price_key_absent_from_identity"

    @pytest.mark.parametrize(
        "payload, reason",
        [
            ({"version_id": "PP-1", "prices": [{"product_key": "A"}]}, "missing_products_block"),
            (
                {
                    "version_id": "PP-1",
                    "products": [{"product_code": "A", "product_name": "A"}],
                    "prices": [],
                },
                "empty_prices_block",
            ),
            (
                {
                    "version_id": "PP-1",
                    "products": [],
                    "prices": [{"product_key": "A"}],
                },
                "empty_products_block",
            ),
            (
                {
                    "version_id": "PP-1",
                    "product": [{"product_code": "A"}],
                    "products": [{"product_code": "A", "product_name": "A"}],
                    "prices": [{"product_key": "A"}],
                },
                "unknown_top_level_key",
            ),
        ],
        ids=["missing_block", "empty_prices", "empty_products", "typo_key"],
    )
    def test_fixture_3_a_shape_error_is_never_swallowed_as_an_empty_catalog(
        self, payload, reason
    ):
        """`INV-02` — lỗi chính tả ở `products:` KHÔNG được nạp 0 dòng im lặng."""
        with pytest.raises(PublicPurchaseSourceError) as excinfo:
            PublicPurchaseSourceLoader.load(payload)
        assert excinfo.value.reason == reason

    def test_fixture_4_two_codes_differing_only_in_case_fail_to_load(self):
        """`INV-05` — `DEC-147` §4: không lặp lại lỗi gộp mã của `normCode`."""
        with pytest.raises(PublicPurchaseSourceError) as excinfo:
            fx.pp_version(
                [
                    {"product_code": "PPC-abc", "product_name": "A"},
                    {"product_code": "PPC-ABC", "product_name": "B"},
                ],
                prices=[
                    {
                        "product_key": "PPC-abc",
                        "effective_from": "2026-09-01",
                        "effective_to": "2026-12-31",
                        "purchase_price": "1",
                    }
                ],
            )
        assert excinfo.value.reason == "folded_product_code_collision"

    def test_fixture_5_an_alias_colliding_with_another_product_code_fails(self):
        with pytest.raises(PublicPurchaseSourceError) as excinfo:
            fx.pp_version(
                [
                    {"product_code": "PPC-1", "product_name": "A"},
                    {"product_code": "PPC-2", "product_name": "B", "aliases": ["PPC-1"]},
                ],
                prices=[
                    {
                        "product_key": "PPC-1",
                        "effective_from": "2026-09-01",
                        "effective_to": "2026-12-31",
                        "purchase_price": "1",
                    }
                ],
            )
        assert excinfo.value.reason == "alias_collides_with_other_product_code"

    def test_fixture_6_renaming_does_not_change_a_report_pinned_to_the_version(self):
        """`INV-07` — published version IMMUTABLE."""
        repo = PublicPurchaseSourceRepository()
        original = fx.pp_version(
            [{"product_code": "PPC-1", "product_name": "Tên cũ", "aliases": ["cũ"]}],
            prices=[
                {
                    "product_key": "PPC-1",
                    "effective_from": "2026-09-01",
                    "effective_to": "2026-12-31",
                    "purchase_price": "1",
                }
            ],
        )
        repo.publish(original)

        with pytest.raises(PublicPurchaseSourceError) as excinfo:
            repo.publish(original)
        assert excinfo.value.reason == "version_already_published"

        pinned = repo.get(fx.PP_V1)
        assert pinned.identity_row("PPC-1").product_name == "Tên cũ"
        assert pinned.content_hash == original.content_hash

    def test_fixture_7_the_frozen_price_provider_is_untouched(self):
        """`INV-03`/`DEC-153` — diff trên `file_price_provider.py` phải RỖNG."""
        diff = subprocess.run(
            ["git", "diff", "HEAD", "--", FROZEN_PRICE_PROVIDER],
            capture_output=True,
            text=True,
        )
        assert diff.returncode == 0, diff.stderr
        assert diff.stdout == "", (
            "CHECK-105D-28 B3: file_price_provider.py là FROZEN (DEC-153)"
        )

    def test_b6_both_projections_come_from_one_version_id(self):
        """`OR-01` — MỘT canonical versioned source, HAI projection."""
        version = fx.pp_version(
            [{"product_code": "PPC-1", "product_name": "A"}],
            prices=[
                {
                    "product_key": "PPC-1",
                    "effective_from": "2026-09-01",
                    "effective_to": "2026-12-31",
                    "purchase_price": "1",
                }
            ],
        )
        assert version.identity_rows and version.validated_price_rows()
        assert version.version_id == fx.PP_V1
        # Không có đường nạp riêng cho từng projection: `load()` là API duy nhất.
        public_api = {
            name
            for name in dir(PublicPurchaseSourceLoader)
            if not name.startswith("_")
        }
        assert public_api == {"load"}


class TestG31G32CrossSystemMapping:
    """`CHECK-105D-31` tính ĐÚNG, `CHECK-105D-32` chi phí vận hành."""

    def test_g31_fixture_1_string_equality_is_not_a_mapping(self):
        """`INV-38` — kể cả khi hai mã bằng nhau tuyệt đối."""
        a_store = fx.store()
        view = a_store.read_at_revision(0)
        assert lookup_public_purchase_code(view, "SAME-CODE") is None

        # Có một PP product trùng chuỗi cũng không tạo ra mapping.
        fx.pp_version([{"product_code": "SAME-CODE", "product_name": "P"}])
        assert lookup_public_purchase_code(view, "SAME-CODE") is None

    def test_g31_fixture_2_a_second_mapping_for_the_same_pp_code_conflicts(self):
        """`INV-39`/`INV-40` — 1:1, không silent last-write-wins."""
        a_store = fx.store()
        confirm_cross_system(
            a_store,
            tracking_code="TRK-A100",
            public_purchase_code="PPC-1",
            actor_id=fx.ACTOR,
            client_request_id="req-cs-1",
            expected_version=0,
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )
        revision = a_store.current_revision()

        with pytest.raises(CrossSystemConflictError, match="INV-39"):
            confirm_cross_system(
                a_store,
                tracking_code="TRK-B200",
                public_purchase_code="PPC-1",
                actor_id=fx.ACTOR,
                client_request_id="req-cs-2",
                expected_version=0,
                pp_version_id=fx.PP_V1,
                tracking_capture_id=fx.CAPTURE_A,
            )
        assert a_store.current_revision() == revision

    def test_g31_fixture_3_correction_supersedes_and_keeps_the_old_record(self):
        a_store = fx.store()
        first = confirm_cross_system(
            a_store,
            tracking_code="TRK-A100",
            public_purchase_code="PPC-1",
            actor_id=fx.ACTOR,
            client_request_id="req-cs-3",
            expected_version=0,
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )
        from app.modules.product.identity.commands import CorrectCrossSystem

        second = a_store.append(
            CorrectCrossSystem(
                actor_id=fx.ACTOR,
                client_request_id="req-cs-4",
                expected_version=1,
                reason="mã công khai đã đổi theo bảng giá mới",
                tracking_code="TRK-A100",
                public_purchase_code="PPC-2",
                evidence=_cross_evidence("PPC-2"),
                pp_version_id=fx.PP_V1,
                tracking_capture_id=fx.CAPTURE_A,
            )
        )

        assert second.cross_system.supersedes == first.cross_system.mapping_id
        old = [
            e.old_value
            for e in a_store.events()
            if e.old_value and "public_purchase_code" in e.old_value
        ]
        assert any(record["public_purchase_code"] == "PPC-1" for record in old)

    def test_g31_fixture_4_lookup_returns_the_mapping_s_own_code(self):
        a_store = fx.store()
        confirm_cross_system(
            a_store,
            tracking_code="TRK-A100",
            public_purchase_code="PPC-KHAC-HAN",
            actor_id=fx.ACTOR,
            client_request_id="req-cs-5",
            expected_version=0,
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )

        view = a_store.read_at_revision(a_store.current_revision())
        assert lookup_public_purchase_code(view, "TRK-A100") == "PPC-KHAC-HAN"
        assert lookup_public_purchase_code(view, "TRK-B200") is None

    def test_g32_a_confirmed_cross_system_mapping_is_never_asked_again(self):
        """`INV-42`/`INV-45` — 0 action, revision không đổi, namespace giữ nguyên."""
        a_store = fx.store()
        confirm_cross_system(
            a_store,
            tracking_code="TRK-A100",
            public_purchase_code="PPC-1",
            actor_id=fx.ACTOR,
            client_request_id="req-cs-6",
            expected_version=0,
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )
        baseline = a_store.current_revision()

        for _ in range(2):
            view = a_store.read_at_revision(a_store.current_revision())
            assert lookup_public_purchase_code(view, "TRK-A100") == "PPC-1"

        assert a_store.current_revision() == baseline
        assert a_store.confirmation_action_count(since_revision=baseline) == 0

    def test_g32_the_identity_namespace_survives_a_price_fallback(self):
        """`INV-45`/`P10` — identity TRACKING vẫn là TRACKING sau fallback."""
        from app.modules.product.identity.resolver import distinct_identities

        a_store = fx.store()
        confirm_cross_system(
            a_store,
            tracking_code="TRK-A100",
            public_purchase_code="PPC-1000",
            actor_id=fx.ACTOR,
            client_request_id="req-cs-7",
            expected_version=0,
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )
        resolver = fx.resolver(
            a_store, fx.tracking_snapshot((("TRK-A100", "Nồi chiên", (), True),))
        )
        identity, = distinct_identities([fx.row("TRK-A100")])
        outcome = resolver.resolve(identity).outcome

        view = a_store.read_at_revision(a_store.current_revision())
        assert lookup_public_purchase_code(view, "TRK-A100") == "PPC-1000"
        assert outcome.identity.namespace is Namespace.TRACKING

    def test_g32_provenance_distinguishes_the_two_public_purchase_paths(self):
        """`DEC-154` §10 — `NO_VENDOR_PRICE` khác `NO_TRACKING`."""
        from app.modules.product.identity.resolver import distinct_identities

        a_store = fx.store()
        resolver = fx.resolver(
            a_store,
            fx.tracking_snapshot(()),
            fx.pp_version([{"product_code": "PPC-9", "product_name": "Hàng ngoài"}]),
        )
        direct, = distinct_identities([fx.row("PPC-9")])
        outcome = resolver.resolve(direct).outcome
        assert outcome.provenance.price_provenance == "PUBLIC_PURCHASE_NO_TRACKING"

        tracking_resolver = fx.resolver(
            a_store, fx.tracking_snapshot((("TRK-A100", "Nồi chiên", (), True),))
        )
        tracked, = distinct_identities([fx.row("TRK-A100")])
        tracked_outcome = tracking_resolver.resolve(tracked).outcome
        assert tracked_outcome.provenance.price_provenance is None

    def test_confirm_cross_system_is_idempotent_on_repeat(self):
        a_store = fx.store()
        kwargs = dict(
            tracking_code="TRK-A100",
            public_purchase_code="PPC-1",
            actor_id=fx.ACTOR,
            expected_version=0,
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )
        confirm_cross_system(a_store, client_request_id="req-a", **kwargs)
        revision = a_store.current_revision()
        again = a_store.append(
            ConfirmCrossSystem(
                actor_id=fx.ACTOR,
                client_request_id="req-b",
                expected_version=1,
                tracking_code="TRK-A100",
                public_purchase_code="PPC-1",
                evidence=_cross_evidence("PPC-1"),
            )
        )
        assert again.outcome is AppendOutcome.NO_CHANGE
        assert a_store.current_revision() == revision


class TestG25GoldenBaselineUnchanged:
    """`CHECK-105D-25` — Golden không đổi, default provider không đổi."""

    def test_no_golden_fixture_or_expected_file_was_modified(self):
        diff = subprocess.run(
            [
                "git",
                "diff",
                "HEAD",
                "--stat",
                "--",
                "tests/test_golden_baseline.py",
                "tests/fixtures/golden/",
                "tests/fixtures/baseline_snapshot.py",
            ],
            capture_output=True,
            text=True,
        )
        assert diff.returncode == 0, diff.stderr
        assert diff.stdout == "", f"Golden bị sửa:\n{diff.stdout}"

    def test_the_pipeline_default_is_still_pending_price_provider(self):
        source = pathlib.Path("app/pipeline.py").read_text(encoding="utf-8")
        assert "PendingPriceProvider" in source
        assert "FilePriceProvider" not in source

    def test_task_105d_does_not_touch_app_pipeline(self):
        diff = subprocess.run(
            ["git", "diff", "HEAD", "--", "app/pipeline.py"],
            capture_output=True,
            text=True,
        )
        assert diff.stdout == "", "app/pipeline.py nằm ngoài Scope Lock của TASK-105D"


class TestMetricsHardening:
    """`HB-105D-F2-03` — `INV-83`…`INV-86` không có gate riêng."""

    def _batch(self, a_store):
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-A100", "Nồi chiên TRK-A100", (), True),
                ("TRK-M1", "Máy lọc không khí AP-100", (), True),
                ("TRK-M2", "Máy lọc không khí AP-200", (), True),
            )
        )
        rows = [
            fx.row("TRK-A100", order_id="ORD-1"),
            fx.row("Máy lọc không khí AP-300", order_id="ORD-2"),
            fx.row("hoàn toàn vô danh", order_id="ORD-3"),
        ]
        return resolve_batch(
            rows,
            registry=HistoricalConfirmedRegistry(),
            resolver_factory=lambda: fx.resolver(a_store, snapshot),
        )

    def test_inv83_the_three_rates_sum_to_one(self):
        a_store = fx.store()
        result = metrics.compute(
            self._batch(a_store),
            mapping_store_revision=a_store.current_revision(),
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )
        assert result.distinct_count == 3
        assert result.sums_to_one()

    def test_inv84_every_metric_carries_its_version_identifiers(self):
        a_store = fx.store()
        result = metrics.compute(
            self._batch(a_store),
            mapping_store_revision=7,
            pp_version_id=fx.PP_V1,
            tracking_capture_id=fx.CAPTURE_A,
        )
        assert result.mapping_store_revision == 7
        assert result.pp_version_id == fx.PP_V1
        assert result.tracking_capture_id == fx.CAPTURE_A

    def test_inv85_the_resolver_never_imports_metrics(self):
        """Vòng phản hồi "hạ ngưỡng để tăng AUTO_RESOLUTION_RATE" không biểu
        diễn được nếu resolver không thấy metric."""
        for name in ("resolver.py", "store.py", "service.py", "evidence.py"):
            source = (MODULE_ROOT / name).read_text(encoding="utf-8")
            assert "metrics" not in source, name

    def test_inv86_metrics_carry_no_customer_data(self):
        a_store = fx.store()
        result = metrics.compute(
            self._batch(a_store), mapping_store_revision=0
        )
        rendered = repr(result)
        for leaked in ("ORD-1", "TRK-A100", "Máy lọc", "vô danh"):
            assert leaked not in rendered

    def test_an_empty_batch_does_not_divide_by_zero(self):
        result = metrics.compute(
            resolve_batch(
                [],
                registry=HistoricalConfirmedRegistry(),
                resolver_factory=fx.CallSpy(),
            ),
            mapping_store_revision=0,
        )
        assert result.distinct_count == 0

    def test_the_correction_rate_uses_its_own_denominator(self):
        from decimal import Decimal

        assert metrics.wrong_mapping_correction_rate(
            correction_events=3, active_confirmed_at_window_start=60
        ) == Decimal(3) / Decimal(60)
        assert metrics.wrong_mapping_correction_rate(
            correction_events=1, active_confirmed_at_window_start=0
        ) == Decimal(0)


class TestMigrationRollbackHardening:
    """`HB-105D-F2-03` — `INV-79`…`INV-82` không có gate riêng."""

    def test_inv79_m0_an_empty_store_is_a_correct_starting_state(self):
        """§14.3 — store rỗng KHÔNG phải lỗi cần vá bằng dữ liệu bịa."""
        from app.modules.product.identity.resolver import distinct_identities

        a_store = fx.store()
        assert a_store.current_revision() == 0
        resolver = fx.resolver(a_store)
        identity, = distinct_identities([fx.row("bất cứ thứ gì")])
        assert isinstance(resolver.resolve(identity).outcome, PendingProduct)

    def test_inv80_rollback_loses_no_confirmation(self, tmp_path):
        """Tắt flag = quay về hành vi cũ; KHÔNG xoá dữ liệu store."""
        a_store = fx.store(tmp_path)
        a_store.append(
            ConfirmMapping(
                actor_id=fx.ACTOR,
                client_request_id="req-1",
                expected_version=0,
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
        bundle_before = a_store.export_bundle()

        from app.modules.product.identity.store import JsonlProductIdentityStore

        reopened = JsonlProductIdentityStore(
            log_path=tmp_path / "identity.log.jsonl"
        )
        assert reopened.export_bundle()["events"] == bundle_before["events"]
        assert reopened.read_active_mapping("REPORTS_SALES", "TRK-A100") is not None

    def test_inv81_a_rolled_back_pp_version_is_a_new_version_not_an_edit(self):
        """`INV-81` qua đúng đường sản xuất thật: `rollback_of` đi qua
        `PublicPurchaseSourceLoader.load()` (khoá top-level được loader đọc
        trực tiếp, `public_purchase.py:219`), KHÔNG `object.__setattr__` bơm
        field vào fixture sau khi dựng (H-06, S041/S047)."""
        repo = PublicPurchaseSourceRepository()
        original = fx.pp_version()
        repo.publish(original)

        rollback = fx.pp_version(version_id=fx.PP_V2, rollback_of=fx.PP_V1)
        repo.publish(rollback)

        # Version cũ KHÔNG bị sửa/xoá — publish rollback không đổi một field
        # nào của nó (§3.3 câu 10).
        assert repo.get(fx.PP_V1) == original
        assert repo.get(fx.PP_V1).rollback_of is None
        # Rollback = một version MỚI, riêng biệt, mang rollback_of đúng.
        assert repo.get(fx.PP_V2).rollback_of == fx.PP_V1
        assert repo.get(fx.PP_V2) is not repo.get(fx.PP_V1)

    def test_inv82_a_report_pinned_to_the_old_binding_replays_unchanged(
        self, tmp_path
    ):
        """Đã chứng minh đầy đủ ở `TestG21…::test_part_c_replay_is_identical…`;
        ở đây kiểm đúng chiều rollback: version cũ vẫn đọc được sau khi publish
        một version rollback."""
        repo = PublicPurchaseSourceRepository()
        original = fx.pp_version()
        repo.publish(original)
        repo.publish(fx.pp_version(version_id=fx.PP_V2))

        assert repo.get(fx.PP_V1).content_hash == original.content_hash
