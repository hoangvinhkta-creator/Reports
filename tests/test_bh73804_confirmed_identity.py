"""Owner-confirmed identity seed for the BH73804 production rerun."""

from pathlib import Path

from app.modules.product.identity.audit import EventType
from app.modules.product.identity.identity import Namespace
from app.modules.product.identity.mapping import (
    MappingSource,
    SOURCE_SYSTEM_REPORTS_SALES,
)
from app.modules.product.identity.store import JsonlProductIdentityStore


REPO_ROOT = Path(__file__).resolve().parents[1]
IDENTITY_LOG = REPO_ROOT / "data/product_identity/mappings.jsonl"
RAW_LABEL = "Máy Giặt LG T2109NT1G"


def test_bh73804_owner_confirmation_is_persistent_and_auditable():
    """The sales label resolves by a stored human confirmation, never fuzzy auto-promotion."""
    store = JsonlProductIdentityStore(log_path=IDENTITY_LOG)

    mapping = store.read_active_mapping(SOURCE_SYSTEM_REPORTS_SALES, RAW_LABEL)
    assert mapping is not None
    assert mapping.namespace is Namespace.TRACKING
    assert mapping.source_product_code == "T2109NT1G"
    assert mapping.mapping_source is MappingSource.HUMAN_CONFIRMATION
    assert mapping.confirmed_by == "owner"
    assert mapping.evidence.matched_value == RAW_LABEL

    event, = (
        item
        for item in store.events()
        if item.client_request_id == "owner-confirmed-bh73804-t2109nt1g-20260831"
    )
    assert event.event_type is EventType.CONFIRM_MAPPING
    assert event.affected_scope.affected_order_ids == ("BH73804",)
    assert event.affected_scope.affected_line_count == 1
