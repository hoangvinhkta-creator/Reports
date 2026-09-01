"""TASK-105D — hai khoá identity, enum đóng và bất biến kiểu.

Data contract §6.3 (`INV-20`, `INV-26`, `INV-27`), §5 (`INV-17`…`INV-19`),
§6.4/§6.5/§6.6 (enum đóng).
"""

from __future__ import annotations

import unicodedata

import pytest

from app.modules.product.identity.evidence import (
    AUTO_RESOLVE_METHODS,
    Evidence,
    EvidenceError,
    MatchedOn,
    ResolutionMethod,
    is_ambiguous,
    is_auto_resolvable,
)
from app.modules.product.identity.identity import (
    AttemptedSource,
    CanonicalProductIdentity,
    IdentityValueError,
    Namespace,
    PendingReason,
)
from app.modules.product.identity.keys import (
    EmptyRawIdentityError,
    normalized_matching_aid,
    raw_identity_key,
)
from app.modules.product.identity.mapping import MappingSource, MappingStatus


class TestRawIdentityKey:
    """`INV-26` — khoá định danh chỉ mất thông tin ở hai mức an toàn."""

    def test_it_normalizes_unicode_form_and_whitespace_only(self):
        assert raw_identity_key("  Nồi   chiên  ") == "Nồi chiên"
        assert raw_identity_key("A\tB\nC") == "A B C"

    def test_it_preserves_case_diacritics_punctuation_and_model_tokens(self):
        raw = "Bếp TỪ đôi ĐẶC-BIỆT (2026) 50% mã XL-500/A"
        assert raw_identity_key(raw) == raw

    def test_nfc_and_nfd_spellings_collapse_to_the_same_key(self):
        precomposed = "phí"
        decomposed = unicodedata.normalize("NFD", precomposed)
        assert precomposed != decomposed
        assert raw_identity_key(precomposed) == raw_identity_key(decomposed)

    def test_case_alone_gives_a_different_identity_key(self):
        assert raw_identity_key("TRK-a100") != raw_identity_key("TRK-A100")

    def test_an_empty_raw_name_is_refused_not_turned_into_an_empty_key(self):
        """Một khoá rỗng sẽ gộp mọi dòng thiếu tên hàng thành MỘT identity."""
        for value in (None, "", "   ", "\t\n"):
            with pytest.raises(EmptyRawIdentityError):
                raw_identity_key(value)
            with pytest.raises(EmptyRawIdentityError):
                normalized_matching_aid(value)


class TestNormalizedMatchingAid:
    """`INV-20` — aid là aid tìm candidate, không phải canonical identity."""

    def test_it_folds_case_on_top_of_the_identity_key(self):
        assert normalized_matching_aid("TRK-A100") == "trk-a100"
        assert normalized_matching_aid("  TRK-a100 ") == "trk-a100"

    def test_case_variants_share_an_aid_but_not_an_identity_key(self):
        a, b = "TRK-A100", "trk-a100"
        assert normalized_matching_aid(a) == normalized_matching_aid(b)
        assert raw_identity_key(a) != raw_identity_key(b)

    def test_it_never_strips_diacritics(self):
        """Bỏ dấu sẽ gộp "mã" và "ma" — hai từ khác nghĩa hoàn toàn."""
        assert normalized_matching_aid("Bếp từ") != normalized_matching_aid("Bep tu")


class TestInv27ModelTokensStayDistinct:
    """`INV-27` — assertion bắt buộc của `CHECK-105D-06`."""

    @pytest.mark.parametrize(
        "a, b",
        [
            ("Nồi chiên XL-500", "Nồi chiên XL-700"),
            ("Máy lọc AP-100", "Máy lọc AP-1000"),
            ("SJ-X198V-DG", "SJ-X198V-SL"),
            ("Bếp từ 2 vùng", "Bếp từ 3 vùng"),
        ],
    )
    def test_one_token_apart_gives_two_keys_and_two_aids(self, a, b):
        assert raw_identity_key(a) != raw_identity_key(b)
        assert normalized_matching_aid(a) != normalized_matching_aid(b)


class TestClosedEnums:
    """Mọi enum của contract là enum ĐÓNG; thêm giá trị là quyết định Owner."""

    def test_namespace_has_exactly_two_values(self):
        assert {n.value for n in Namespace} == {"TRACKING", "PUBLIC_PURCHASE"}

    def test_an_unknown_namespace_is_refused_at_construction(self):
        with pytest.raises(IdentityValueError, match="namespace"):
            CanonicalProductIdentity(
                namespace="VENDOR", source_product_code="X"
            )

    def test_pending_reason_matches_the_contract_exactly(self):
        assert {r.value for r in PendingReason} == {
            "NO_CANDIDATE_IN_ANY_CATALOG",
            "AMBIGUOUS_MULTIPLE_DETERMINISTIC_CANDIDATES",
            "ONLY_SIMILARITY_EVIDENCE",
            "CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED",
            "MAPPING_STALE_TARGET_ABSENT",
            "AWAITING_HUMAN_CONFIRMATION",
            "PENDING_HISTORICAL_CONFIRMATION",
        }

    def test_mapping_status_matches_the_contract_exactly(self):
        assert {s.value for s in MappingStatus} == {
            "CONFIRMED",
            "PENDING",
            "SUPERSEDED",
            "CONFLICT",
            "STALE",
        }

    def test_mapping_source_matches_the_contract_exactly(self):
        assert {s.value for s in MappingSource} == {
            "HUMAN_CONFIRMATION",
            "DETERMINISTIC_CATALOG_MATCH",
            "OWNER_BOOTSTRAP",
            "HISTORICAL_CONFIRMED_REPORT",
        }

    def test_resolution_method_matches_the_contract_exactly(self):
        assert {m.value for m in ResolutionMethod} == {
            "ALIAS_EXACT",
            "CATALOG_EXACT_UNIQUE",
            "ALIAS_AID_UNIQUE",
            "TRACKING_ALIAS_MAP",
            "TRACKING_CONFIRMED_ALIAS",
            "TRACKING_CANONICAL_EXACT",
            "SIMILARITY_RANKED",
            "CROSS_NAMESPACE_TIE",
            "MULTIPLE_EXACT",
        }

    def test_matched_on_matches_the_contract_exactly(self):
        assert {m.value for m in MatchedOn} == {
            "RAW_KEY",
            "AID",
            "TRACKING_CODE",
            "TRACKING_NAME",
            "TRACKING_ALT",
            "TRACKING_ALIAS_MAP",
            "PP_PRODUCT_CODE",
            "PP_ALIAS",
            "MANUAL_SEARCH",
        }

    def test_ambiguous_is_exactly_the_complement_of_the_auto_resolve_set(self):
        """§17.2 — AMBIGUOUS = KHÔNG thuộc tập auto-resolve đóng."""
        for method in ResolutionMethod:
            assert is_ambiguous(method) is not is_auto_resolvable(method)
        assert len(AUTO_RESOLVE_METHODS) == 4

    def test_attempted_source_covers_both_catalogs(self):
        values = {s.value for s in AttemptedSource}
        assert "TRACKING_CATALOG" in values
        assert "PUBLIC_PURCHASE_CATALOG" in values


class TestEvidenceRequiredFields:
    """§6.7 — ba trường REQUIRED, hai trường OPTIONAL."""

    def test_the_three_required_fields_are_enforced(self):
        with pytest.raises(EvidenceError, match="matched_value"):
            Evidence(
                matched_on=MatchedOn.RAW_KEY, matched_value="", candidate_set_ids=()
            )
        with pytest.raises(EvidenceError, match="matched_on"):
            Evidence(
                matched_on="RAW_KEY", matched_value="x", candidate_set_ids=()
            )
        with pytest.raises(EvidenceError, match="candidate_set_ids"):
            Evidence(
                matched_on=MatchedOn.RAW_KEY,
                matched_value="x",
                candidate_set_ids=None,
            )

    def test_ranking_method_id_stays_optional_per_the_data_contract(self):
        """`H-05` vẫn OPEN ở tầng contract: trường này là `OPTIONAL` (§6.7).

        Phiên implementation KHÔNG có thẩm quyền đổi `OPTIONAL → REQUIRED`, nên
        nó không đổi. Rủi ro được xử lý ở hai chỗ khác, cả hai đều trong thẩm
        quyền implementation: resolver luôn gắn giá trị, và
        `evidence_fingerprint()` dùng một sentinel tường minh cho trường vắng.
        """
        evidence = Evidence(
            matched_on=MatchedOn.RAW_KEY,
            matched_value="x",
            candidate_set_ids=("TRACKING:A",),
        )
        assert evidence.ranking_method_id is None
        assert evidence.parent_mapping_id is None


class TestCanonicalIdentityValueObject:
    def test_it_is_frozen(self):
        identity = CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code="X"
        )
        with pytest.raises(Exception):
            identity.source_product_code = "Y"

    def test_str_renders_the_namespaced_form(self):
        identity = CanonicalProductIdentity(
            namespace=Namespace.PUBLIC_PURCHASE, source_product_code="ABC"
        )
        assert str(identity) == "PUBLIC_PURCHASE:ABC"

    def test_an_empty_code_is_refused(self):
        for code in ("", "   "):
            with pytest.raises(IdentityValueError):
                CanonicalProductIdentity(
                    namespace=Namespace.TRACKING, source_product_code=code
                )
