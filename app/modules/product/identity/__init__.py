"""TASK-105D — Product Identity Resolver.

Bề mặt công khai của module. Hợp đồng canonical:

- `docs/tasks/TASK-105D-product-identity-resolver.md` (Completion Gate FROZEN)
- `docs/spec/TASK-105D-DATA-CONTRACT.md` (`INV-01`…`INV-87`)

Module này resolve **danh tính** sản phẩm và không tính giá
(`CHECK-105D-16`): nó không import price provider nào, và outcome post-cutover
của nó không mang giá dưới bất kỳ tên nào.
"""

from app.modules.product.identity.identity import (
    AttemptedSource,
    CanonicalProductIdentity,
    HistoricalConfirmed,
    Namespace,
    PendingProduct,
    PendingReason,
    Provenance,
    RequiresConfirmation,
    Resolved,
    ResolutionOutcome,
)
from app.modules.product.identity.keys import (
    normalized_matching_aid,
    raw_identity_key,
)
from app.modules.product.identity.registry import CUTOVER_DATE
from app.modules.product.identity.resolver import (
    DistinctIdentity,
    IdentityResolution,
    ProductIdentityResolver,
    SalesRowRef,
    distinct_identities,
)
from app.modules.product.identity.service import (
    BatchResolution,
    lookup_public_purchase_code,
    resolve_batch,
)
from app.modules.product.identity.store import (
    JsonlProductIdentityStore,
    ProductIdentityStore,
)

__all__ = [
    "AttemptedSource",
    "BatchResolution",
    "CUTOVER_DATE",
    "CanonicalProductIdentity",
    "DistinctIdentity",
    "HistoricalConfirmed",
    "IdentityResolution",
    "JsonlProductIdentityStore",
    "Namespace",
    "PendingProduct",
    "PendingReason",
    "ProductIdentityResolver",
    "ProductIdentityStore",
    "Provenance",
    "RequiresConfirmation",
    "Resolved",
    "ResolutionOutcome",
    "SalesRowRef",
    "distinct_identities",
    "lookup_public_purchase_code",
    "normalized_matching_aid",
    "raw_identity_key",
    "resolve_batch",
]
