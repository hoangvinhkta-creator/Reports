"""TASK-105D — thứ tự phân giải, ambiguity, candidate và ngân sách thao tác.

Gate: `CHECK-105D-02`…`-08`, `-11`, `-13`, `-23`, `-24`, `-26`, `-27`.
Adversarial: `A` (DISTINCT), `B` (known mapping), `C` (catalog exact unique),
`D` (alias aid unique), `E` (fuzzy only), `F` (ambiguous), `G` (no match),
`H` (PP direct product).
"""

from __future__ import annotations

import pytest

from app.modules.product.identity.audit import CONFIRMATION_ACTION_TYPES
from app.modules.product.identity.cli import confirm, render_candidates
from app.modules.product.identity.evidence import (
    AUTO_RESOLVE_METHODS,
    RANKING_METHOD_ID,
    ResolutionMethod,
    is_auto_resolvable,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    HistoricalConfirmed,
    Namespace,
    PendingProduct,
    PendingReason,
    POST_CUTOVER_VARIANTS,
    RequiresConfirmation,
    Resolved,
    ResolutionOutcome,
)
from app.modules.product.identity.keys import (
    normalized_matching_aid,
    raw_identity_key,
)
from app.modules.product.identity.resolver import distinct_identities
from app.modules.product.identity.service import resolve_batch
from app.modules.product.identity.store import AppendOutcome
from tests.support import identity_fixtures as fx

TRACKING_ROWS = (
    ("TRK-A100", "Nồi chiên TRK-A100", (), True),
    ("TRK-B200", "Máy lọc TRK-B200", ("TRK-B200-CU",), True),
)
PP_PRODUCTS = [
    {"product_code": "PPC-9000", "product_name": "Sản phẩm công khai 9000"},
]


def _resolve_one(a_store, product_raw, *, snapshot=None, version=None):
    resolver = fx.resolver(a_store, snapshot, version)
    identity, = distinct_identities([fx.row(product_raw)])
    return resolver.resolve(identity)


class TestG02ClosedUnion:
    """`CHECK-105D-02` — outcome đúng union type ĐÓNG."""

    def test_union_is_sealed_at_type_level(self):
        with pytest.raises(TypeError, match="union ĐÓNG"):
            class BiếnThểThứNăm(ResolutionOutcome):
                pass

    def test_exactly_four_variants_exist(self):
        assert set(ResolutionOutcome._variants) == {
            Resolved,
            RequiresConfirmation,
            PendingProduct,
            HistoricalConfirmed,
        }

    def test_resolved_always_carries_the_full_tuple(self):
        result = _resolve_one(
            fx.store(),
            "TRK-A100",
            snapshot=fx.tracking_snapshot(TRACKING_ROWS),
        )
        assert isinstance(result.outcome, Resolved)
        assert result.outcome.identity.namespace is Namespace.TRACKING
        assert result.outcome.identity.source_product_code == "TRK-A100"

    def test_resolved_refuses_an_empty_code(self):
        with pytest.raises(ValueError, match="source_product_code"):
            CanonicalProductIdentity(
                namespace=Namespace.TRACKING, source_product_code="  "
            )

    def test_historical_confirmed_never_leaks_into_post_cutover(self):
        a_store = fx.store()
        result = resolve_batch(
            [fx.row("TRK-A100"), fx.row("hoàn toàn không khớp gì")],
            registry=__import__(
                "app.modules.product.identity.registry",
                fromlist=["HistoricalConfirmedRegistry"],
            ).HistoricalConfirmedRegistry(),
            resolver_factory=lambda: fx.resolver(
                a_store, fx.tracking_snapshot(TRACKING_ROWS)
            ),
        )
        for resolution in result.resolutions:
            assert isinstance(resolution.outcome, POST_CUTOVER_VARIANTS)
            assert not isinstance(resolution.outcome, HistoricalConfirmed)


class TestG03DistinctBeforeMapping:
    """`CHECK-105D-03` — 10.000 dòng / 50 identity ⇒ `|D| == 50`."""

    def test_ten_thousand_rows_fifty_identities(self):
        rows = []
        for index in range(10_000):
            model = index % 50
            rows.append(
                fx.row(
                    f"Sản phẩm tổng hợp mã M{model:03d}",
                    order_id=f"ORD-{index % 700}",
                )
            )

        distinct = distinct_identities(rows)

        assert len(distinct) == 50
        assert sum(d.line_count for d in distinct) == 10_000
        # Một identity xuất hiện ở nhiều order khác nhau — fixture bắt buộc.
        assert any(len(d.order_ids) > 1 for d in distinct)

    def test_confirmation_budget_is_capped_by_distinct_not_rows(self):
        a_store = fx.store()
        rows = [
            fx.row("TRK-A100", order_id=f"ORD-{i}") for i in range(200)
        ]
        result = resolve_batch(
            rows,
            registry=__import__(
                "app.modules.product.identity.registry",
                fromlist=["HistoricalConfirmedRegistry"],
            ).HistoricalConfirmedRegistry(),
            resolver_factory=lambda: fx.resolver(
                a_store, fx.tracking_snapshot(TRACKING_ROWS)
            ),
        )
        assert result.distinct_count == 1
        assert a_store.confirmation_action_count() == 0
        assert a_store.confirmation_action_count() <= result.distinct_count

    def test_two_models_differing_by_one_token_stay_distinct(self):
        """`INV-27` — hai khoá khác nhau VÀ hai aid khác nhau."""
        a = "Nồi chiên không dầu XL-500"
        b = "Nồi chiên không dầu XL-700"

        assert raw_identity_key(a) != raw_identity_key(b)
        assert normalized_matching_aid(a) != normalized_matching_aid(b)
        assert len(distinct_identities([fx.row(a), fx.row(b)])) == 2


class TestG04AliasExactReadPath:
    """`CHECK-105D-04` — read path: 0 `confirmation_action`, 0 ghi."""

    def test_confirmed_alias_resolves_without_touching_the_store(self, tmp_path):
        a_store = fx.store(tmp_path)
        product = "TRK-A100"
        _seed_confirmed(a_store, product, Namespace.TRACKING, "TRK-A100")

        revision_before = a_store.current_revision()
        events_before = len(a_store.events())

        result = _resolve_one(
            a_store, product, snapshot=fx.tracking_snapshot(TRACKING_ROWS)
        )

        assert result.resolution_method is ResolutionMethod.ALIAS_EXACT
        assert a_store.current_revision() == revision_before
        assert len(a_store.events()) == events_before
        assert (
            a_store.confirmation_action_count(since_revision=revision_before) == 0
        )


class TestG05CatalogExactUniqueBothDirections:
    """`CHECK-105D-05` — assertion HAI CHIỀU."""

    def test_positive_unique_in_tracking(self):
        a_store = fx.store()
        result = _resolve_one(
            a_store, "TRK-A100", snapshot=fx.tracking_snapshot(TRACKING_ROWS)
        )

        assert result.resolution_method is ResolutionMethod.CATALOG_EXACT_UNIQUE
        assert isinstance(result.outcome, Resolved)
        assert result.outcome.identity.namespace is Namespace.TRACKING
        assert (
            result.outcome.provenance.mapping_source == "DETERMINISTIC_CATALOG_MATCH"
        )
        assert a_store.confirmation_action_count() == 0

    def test_positive_unique_in_public_purchase(self):
        a_store = fx.store()
        result = _resolve_one(
            a_store,
            "PPC-9000",
            snapshot=fx.tracking_snapshot(TRACKING_ROWS),
            version=fx.pp_version(PP_PRODUCTS),
        )

        assert result.resolution_method is ResolutionMethod.CATALOG_EXACT_UNIQUE
        assert result.outcome.identity.namespace is Namespace.PUBLIC_PURCHASE
        assert a_store.confirmation_action_count() == 0

    def test_negative_cross_namespace_tie_is_never_auto_resolved(self):
        """`INV-29` — khớp exact ở CẢ HAI namespace ⇒ KHÔNG auto-resolve."""
        shared = "SHARED-CODE-1"
        result = _resolve_one(
            fx.store(),
            shared,
            snapshot=fx.tracking_snapshot(((shared, "Tên Tracking", (), True),)),
            version=fx.pp_version(
                [{"product_code": shared, "product_name": "Tên Public Purchase"}]
            ),
        )

        assert result.resolution_method is ResolutionMethod.CROSS_NAMESPACE_TIE
        assert not is_auto_resolvable(result.resolution_method)
        assert isinstance(result.outcome, (RequiresConfirmation, PendingProduct))


class TestG06AmbiguousNeverAutoResolves:
    """`CHECK-105D-06` — BỐN fixture, mỗi nguồn ambiguity một fixture."""

    def test_a_multiple_exact(self):
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-X1", "Trùng tên", (), True),
                ("TRK-X2", "Trùng tên", (), True),
            )
        )
        result = _resolve_one(fx.store(), "Trùng tên", snapshot=snapshot)

        assert result.resolution_method is ResolutionMethod.MULTIPLE_EXACT
        assert not is_auto_resolvable(result.resolution_method)

    def test_b_cross_namespace_tie(self):
        shared = "SHARED-CODE-2"
        result = _resolve_one(
            fx.store(),
            shared,
            snapshot=fx.tracking_snapshot(((shared, "T", (), True),)),
            version=fx.pp_version([{"product_code": shared, "product_name": "P"}]),
        )
        assert result.resolution_method is ResolutionMethod.CROSS_NAMESPACE_TIE
        assert not is_auto_resolvable(result.resolution_method)

    def test_c_only_similarity(self):
        snapshot = fx.tracking_snapshot(
            (("TRK-A100", "Nồi chiên không dầu XL-500", (), True),)
        )
        result = _resolve_one(
            fx.store(), "Nồi chiên không dầu XL-900", snapshot=snapshot
        )

        assert result.resolution_method is ResolutionMethod.SIMILARITY_RANKED
        assert not is_auto_resolvable(result.resolution_method)
        assert isinstance(result.outcome, PendingProduct)
        assert result.outcome.reason_code is PendingReason.ONLY_SIMILARITY_EVIDENCE

    def test_d_alias_aid_unique_is_candidate_only(self):
        """`INV-28b` / `DEC-156` `OR-02` — KHÔNG BAO GIỜ tự sinh CONFIRMED."""
        a_store = fx.store()
        _seed_confirmed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")

        result = _resolve_one(
            a_store, "trk-a100", snapshot=fx.tracking_snapshot(())
        )

        assert result.resolution_method is ResolutionMethod.ALIAS_AID_UNIQUE
        assert not is_auto_resolvable(result.resolution_method)
        assert isinstance(result.outcome, RequiresConfirmation)
        assert a_store.confirmation_action_count() == 1  # chỉ lần seed

    def test_the_central_case_two_entries_one_token_apart(self):
        """Catalog có hai entry khác nhau ĐÚNG MỘT model token; raw mang token
        thứ ba ⇒ không có "im lặng chọn cái gần nhất"."""
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-M1", "Máy lọc không khí AP-100", (), True),
                ("TRK-M2", "Máy lọc không khí AP-200", (), True),
            )
        )
        result = _resolve_one(
            fx.store(), "Máy lọc không khí AP-300", snapshot=snapshot
        )

        assert not is_auto_resolvable(result.resolution_method)
        assert isinstance(result.outcome, (RequiresConfirmation, PendingProduct))


class TestG07FuzzyHasNoProductionAuthority:
    """`CHECK-105D-07` — phủ định TOÀN CỤC, không phải hành vi một case."""

    def test_similarity_only_creates_no_confirmed_mapping(self):
        a_store = fx.store()
        snapshot = fx.tracking_snapshot(
            (("TRK-A100", "Nồi chiên không dầu XL-500", (), True),)
        )
        _resolve_one(a_store, "Nồi chiên không dầu XL-900", snapshot=snapshot)

        view = a_store.read_at_revision(a_store.current_revision())
        assert view.alias_index() == {}

    def test_bootstrap_cannot_launder_similarity_into_confirmed(self):
        """Fixture (2): nạp qua bootstrap/migration một mapping
        `SIMILARITY_RANKED` ⇒ bị TỪ CHỐI."""
        from app.modules.product.identity.commands import BootstrapMapping
        from app.modules.product.identity.evidence import Evidence, MatchedOn
        from app.modules.product.identity.store import SimilarityAuthorityError

        a_store = fx.store()
        command = BootstrapMapping(
            actor_id=fx.ACTOR,
            client_request_id="req-bootstrap-bad",
            expected_version=0,
            raw_identity_key="một sản phẩm nào đó",
            raw_product_identity="một sản phẩm nào đó",
            target=CanonicalProductIdentity(
                namespace=Namespace.TRACKING, source_product_code="TRK-A100"
            ),
            evidence=Evidence(
                matched_on=MatchedOn.AID,
                matched_value="một sản phẩm nào đó",
                candidate_set_ids=("TRACKING:TRK-A100",),
            ),
            resolution_method=ResolutionMethod.SIMILARITY_RANKED,
        )

        with pytest.raises(SimilarityAuthorityError):
            a_store.append(command)
        assert a_store.current_revision() == 0

    def test_the_auto_resolve_set_contains_only_owner_authorized_methods(self):
        assert AUTO_RESOLVE_METHODS == {
            ResolutionMethod.ALIAS_EXACT,
            ResolutionMethod.CATALOG_EXACT_UNIQUE,
            ResolutionMethod.TRACKING_CONFIRMED_ALIAS,
            ResolutionMethod.TRACKING_CANONICAL_EXACT,
            ResolutionMethod.TRACKING_INV_MAP_CONFIRMED,
        }
        assert not is_auto_resolvable(ResolutionMethod.SIMILARITY_RANKED)
        assert not is_auto_resolvable(ResolutionMethod.ALIAS_AID_UNIQUE)
        assert not is_auto_resolvable(ResolutionMethod.TRACKING_ALIAS_MAP)


class TestG08CandidateRankingIsStableAndEvidenced:
    """`CHECK-105D-08` — thứ tự ổn định, evidence đủ ba trường REQUIRED."""

    def test_same_input_gives_the_same_order_across_runs(self):
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-M1", "Máy lọc không khí AP-100", (), True),
                ("TRK-M2", "Máy lọc không khí AP-200", (), True),
                ("TRK-M3", "Máy lọc không khí AP-400", (), True),
            )
        )
        orders = []
        for _ in range(2):
            result = _resolve_one(
                fx.store(), "Máy lọc không khí AP-300", snapshot=snapshot
            )
            orders.append(tuple(c.candidate_id for c in result.candidates))

        assert orders[0] == orders[1]
        assert len(orders[0]) >= 2

    def test_ranking_does_not_depend_on_the_python_hash_seed(self):
        """Thứ tự dựng từ giá trị dữ liệu, không từ `hash()`/thứ tự dict.

        Chạy lại trong một process con với `PYTHONHASHSEED` khác: cùng thứ tự.
        """
        import json
        import subprocess
        import sys

        script = (
            "import sys; sys.path.insert(0, '.');\n"
            "from tests.support import identity_fixtures as fx;\n"
            "from app.modules.product.identity.resolver import distinct_identities;\n"
            "snap = fx.tracking_snapshot(((\"TRK-M1\", \"Máy lọc AP-100\", (), True),"
            "(\"TRK-M2\", \"Máy lọc AP-200\", (), True),"
            "(\"TRK-M3\", \"Máy lọc AP-400\", (), True)));\n"
            "r = fx.resolver(fx.store(), snap);\n"
            "i, = distinct_identities([fx.row('Máy lọc AP-300')]);\n"
            "import json; print(json.dumps([c.candidate_id for c in r.resolve(i).candidates]))"
        )
        seen = set()
        for seed in ("0", "1", "12345"):
            out = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin:/usr/local/bin"},
            )
            assert out.returncode == 0, out.stderr
            seen.add(out.stdout.strip())

        assert len(seen) == 1, f"thứ tự candidate đổi theo hash seed: {seen}"

    def test_every_candidate_carries_the_three_required_evidence_fields(self):
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-M1", "Máy lọc không khí AP-100", (), True),
                ("TRK-M2", "Máy lọc không khí AP-200", (), True),
            )
        )
        result = _resolve_one(
            fx.store(), "Máy lọc không khí AP-300", snapshot=snapshot
        )

        assert result.candidates
        for candidate in result.candidates:
            assert candidate.evidence.matched_on is not None
            assert candidate.evidence.matched_value
            assert candidate.evidence.candidate_set_ids
            # `H-05` — resolver LUÔN gắn ranking_method_id, dù §6.7 để OPTIONAL.
            assert candidate.evidence.ranking_method_id == RANKING_METHOD_ID


class TestG13PendingIsItsOwnType:
    """`CHECK-105D-13` — bốn assertion `G13-a`…`G13-d`."""

    def test_g13a_pending_is_a_distinct_type_not_none(self):
        result = _resolve_one(fx.store(), "không khớp gì hết trơn")
        assert isinstance(result.outcome, PendingProduct)
        assert result.outcome is not None

    def test_g13b_reason_code_is_in_the_closed_enum_and_sources_not_empty(self):
        result = _resolve_one(fx.store(), "không khớp gì hết trơn")
        assert isinstance(result.outcome.reason_code, PendingReason)
        assert result.outcome.attempted_sources

    def test_g13c_pending_carries_no_namespace_or_code(self):
        result = _resolve_one(fx.store(), "không khớp gì hết trơn")
        assert result.outcome.provenance.namespace is None
        assert result.outcome.provenance.source_product_code is None

        from app.modules.product.identity.identity import IdentityValueError, Provenance
        from datetime import datetime, timezone

        with pytest.raises(IdentityValueError, match="INV-24"):
            PendingProduct(
                reason_code=PendingReason.NO_CANDIDATE_IN_ANY_CATALOG,
                provenance=Provenance(
                    raw_product_identity="x",
                    resolution_method="X",
                    resolved_at=datetime.now(timezone.utc),
                    namespace=Namespace.TRACKING,
                ),
            )

    def test_g13d_a_pending_identity_does_not_block_the_batch(self):
        a_store = fx.store()
        _seed_confirmed(a_store, "TRK-B200", Namespace.TRACKING, "TRK-B200")
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-A100", "Nồi chiên TRK-A100", (), True),
                ("TRK-M1", "Máy lọc không khí AP-100", (), True),
                ("TRK-M2", "Máy lọc không khí AP-200", (), True),
            )
        )
        rows = [
            fx.row("TRK-A100"),
            fx.row("Máy lọc không khí AP-100 hay AP-200"),
            fx.row("hoàn toàn vô danh"),
        ]
        from app.modules.product.identity.registry import HistoricalConfirmedRegistry

        result = resolve_batch(
            rows,
            registry=HistoricalConfirmedRegistry(),
            resolver_factory=lambda: fx.resolver(a_store, snapshot),
        )

        kinds = {type(r.outcome).__name__ for r in result.resolutions}
        assert len(result.resolutions) == 3
        assert "Resolved" in kinds
        assert "PendingProduct" in kinds


class TestG23AmbiguousCostsExactlyOneAction:
    """`CHECK-105D-23` — đúng 1 action lần đầu, 0 lần sau qua `ALIAS_EXACT`."""

    def test_alias_aid_unique_costs_one_then_zero(self):
        a_store = fx.store()
        _seed_confirmed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        variant = "  trk-a100  "
        baseline = a_store.current_revision()

        first = _resolve_one(a_store, variant, snapshot=fx.tracking_snapshot(()))
        assert first.resolution_method is ResolutionMethod.ALIAS_AID_UNIQUE
        assert first.candidates[0].rank == 1
        assert first.candidates[0].source_product_code == "TRK-A100"

        result = confirm(
            a_store,
            first,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="req-aid-1",
            expected_version=0,
        )

        assert result.outcome is AppendOutcome.APPLIED
        assert a_store.confirmation_action_count(since_revision=baseline) == 1
        mapping = result.mapping
        assert mapping.mapping_source.value == "HUMAN_CONFIRMATION"
        assert mapping.evidence.parent_mapping_id is not None

        after = a_store.current_revision()
        second = _resolve_one(a_store, variant, snapshot=fx.tracking_snapshot(()))
        assert second.resolution_method is ResolutionMethod.ALIAS_EXACT
        assert a_store.confirmation_action_count(since_revision=after) == 0

    @pytest.mark.parametrize(
        "product_raw, snapshot_rows, pp_products",
        [
            ("Trùng tên", (("TRK-X1", "Trùng tên", (), True), ("TRK-X2", "Trùng tên", (), True)), None),
            ("SHARED-C3", (("SHARED-C3", "T", (), True),), [{"product_code": "SHARED-C3", "product_name": "P"}]),
            ("Máy lọc không khí AP-300", (("TRK-M1", "Máy lọc không khí AP-100", (), True),), None),
        ],
        ids=["MULTIPLE_EXACT", "CROSS_NAMESPACE_TIE", "ONLY_SIMILARITY"],
    )
    def test_each_ambiguity_source_costs_exactly_one_then_zero(
        self, product_raw, snapshot_rows, pp_products
    ):
        a_store = fx.store()
        snapshot = fx.tracking_snapshot(snapshot_rows)
        version = fx.pp_version(pp_products) if pp_products else fx.pp_version()

        first = _resolve_one(
            a_store, product_raw, snapshot=snapshot, version=version
        )
        assert not is_auto_resolvable(first.resolution_method)
        assert first.candidates, "một identity AMBIGUOUS phải có candidate để chọn"

        confirm(
            a_store,
            first,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id=f"req-{product_raw}",
            expected_version=0,
        )
        assert a_store.confirmation_action_count() == 1

        after = a_store.current_revision()
        second = _resolve_one(
            a_store, product_raw, snapshot=snapshot, version=version
        )
        assert second.resolution_method is ResolutionMethod.ALIAS_EXACT
        assert a_store.confirmation_action_count(since_revision=after) == 0


class TestG24KnownMappingInBatch:
    """`CHECK-105D-24` — batch `N >= 2`: 0 action, revision KHÔNG đổi."""

    def test_batch_of_five_known_lines_plus_one_unknown(self, tmp_path):
        a_store = fx.store(tmp_path)
        _seed_confirmed(a_store, "TRK-A100", Namespace.TRACKING, "TRK-A100")
        revision_before = a_store.current_revision()

        from app.modules.product.identity.registry import HistoricalConfirmedRegistry

        rows = [fx.row("TRK-A100", order_id=f"ORD-{i}") for i in range(5)]
        rows.append(fx.row("một sản phẩm chưa từng biết"))

        result = resolve_batch(
            rows,
            registry=HistoricalConfirmedRegistry(),
            resolver_factory=lambda: fx.resolver(
                a_store, fx.tracking_snapshot(TRACKING_ROWS)
            ),
        )

        known = result.resolution_for(raw_identity_key("TRK-A100"))
        assert known.resolution_method is ResolutionMethod.ALIAS_EXACT
        assert a_store.confirmation_action_count(since_revision=revision_before) == 0
        assert a_store.current_revision() == revision_before
        assert result.distinct_count == 2
        unknown = result.resolution_for(
            raw_identity_key("một sản phẩm chưa từng biết")
        )
        assert isinstance(unknown.outcome, PendingProduct)


class TestG11OneActionResolvesEveryAffectedLine:
    """`CHECK-105D-11` — `M >= 3` order, `N >= 5` dòng, đúng một action."""

    def test_single_confirmation_covers_all_rows_and_orders(self):
        a_store = fx.store()
        product = "Sản phẩm dùng chung nhiều đơn"
        rows = [
            fx.row(product, order_id="ORD-A"),
            fx.row(product, order_id="ORD-A"),
            fx.row(product, order_id="ORD-B"),
            fx.row(product, order_id="ORD-C"),
            fx.row(product, order_id="ORD-C"),
        ]
        snapshot = fx.tracking_snapshot(
            (("TRK-A100", "Sản phẩm dùng chung nhiều", (), True),)
        )
        from app.modules.product.identity.registry import HistoricalConfirmedRegistry

        before = resolve_batch(
            rows,
            registry=HistoricalConfirmedRegistry(),
            resolver_factory=lambda: fx.resolver(a_store, snapshot),
        )
        resolution = before.resolutions[0]
        assert resolution.identity.line_count == 5
        assert len(resolution.identity.order_ids) == 3

        result = confirm(
            a_store,
            resolution,
            candidate_rank=1,
            actor_id=fx.ACTOR,
            client_request_id="req-shared-1",
            expected_version=0,
        )

        scope = result.event.affected_scope
        assert scope.affected_line_count == 5
        assert len(scope.affected_order_ids) == 3
        assert a_store.confirmation_action_count() == 1

        after = resolve_batch(
            rows,
            registry=HistoricalConfirmedRegistry(),
            resolver_factory=lambda: fx.resolver(a_store, snapshot),
        )
        assert isinstance(after.resolutions[0].outcome, Resolved)


class TestG26G27TrackingMissContinuesToPublicPurchase:
    """`CHECK-105D-26` chiều khẳng định, `CHECK-105D-27` chiều phủ định."""

    def test_g26_tracking_miss_plus_pp_unique_resolves_public_purchase(self):
        result = _resolve_one(
            fx.store(),
            "PPC-9000",
            snapshot=fx.tracking_snapshot(TRACKING_ROWS),
            version=fx.pp_version(PP_PRODUCTS),
        )

        assert isinstance(result.outcome, Resolved)
        assert result.outcome.identity.namespace is Namespace.PUBLIC_PURCHASE
        assert result.outcome.identity.source_product_code == "PPC-9000"
        assert result.resolution_method is ResolutionMethod.CATALOG_EXACT_UNIQUE

    def test_g27_tracking_miss_alone_is_not_enough_for_pending(self):
        result = _resolve_one(
            fx.store(),
            "hoàn toàn vô danh ở cả hai nơi",
            snapshot=fx.tracking_snapshot(TRACKING_ROWS),
            version=fx.pp_version(PP_PRODUCTS),
        )

        assert isinstance(result.outcome, PendingProduct)
        sources = {s.value for s in result.outcome.attempted_sources}
        assert "TRACKING_CATALOG" in sources
        assert "PUBLIC_PURCHASE_CATALOG" in sources


class TestConfirmationActionDefinition:
    """§17.1 — đếm COMMAND, không đếm phím/click (`D-14`)."""

    def test_exactly_four_command_types_are_counted(self):
        assert {t.value for t in CONFIRMATION_ACTION_TYPES} == {
            "CONFIRM_MAPPING",
            "REJECT_CANDIDATE",
            "CONFIRM_CROSS_SYSTEM",
            "SET_PENDING",
        }

    def test_viewing_candidates_is_not_a_confirmation_action(self):
        a_store = fx.store()
        snapshot = fx.tracking_snapshot(
            (
                ("TRK-M1", "Máy lọc không khí AP-100", (), True),
                ("TRK-M2", "Máy lọc không khí AP-200", (), True),
            )
        )
        result = _resolve_one(
            a_store, "Máy lọc không khí AP-300", snapshot=snapshot
        )

        for _ in range(20):
            rendered = render_candidates(result)

        assert "outcome:" in rendered
        assert a_store.confirmation_action_count() == 0
        assert a_store.current_revision() == 0


def _seed_confirmed(a_store, product_raw, namespace, code):
    """Gieo một mapping CONFIRMED qua đúng đường command, không ghi tắt."""
    from app.modules.product.identity.commands import ConfirmMapping
    from app.modules.product.identity.evidence import Evidence, MatchedOn

    return a_store.append(
        ConfirmMapping(
            actor_id=fx.ACTOR,
            client_request_id=f"seed-{product_raw}-{code}",
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
