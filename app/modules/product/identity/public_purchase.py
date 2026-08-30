"""E-A/E-B/E-C — MỘT nguồn Public Purchase versioned, HAI projection.

## ⚠ LEGACY SUPPORTED FORMAT — KHÔNG còn là production source authority

`ADR-107` / `DEC-165` (2026-08-30) thay giả định gốc của module này. Public
Purchase **không** phải một nguồn giá độc lập do chủ dự án cấp cho Reports:
nó là giá Owner tự quản trong Tracking (`inv.cong` → `board/<mã>/tp/ton`), có
lịch sử effective-dated dấu thời gian máy chủ
(`purchase_price_baseline`/`purchase_price_history`), và Reports đọc nó qua
Data Contract. Đường production của `KpiPurchasePrice` đi qua
`TrackingPriceHistoryReader`, KHÔNG qua file này.

Module này **ở lại nguyên vẹn** và vẫn được nạp khi có file, vì hai lý do
thật: namespace identity `PUBLIC_PURCHASE` còn phục vụ các mã ngoài danh mục
Tracking, và test/fixture/bằng chứng lịch sử đang dựa vào nó. Nhưng
`data/public_purchase/source_version.yaml` vắng mặt KHÔNG còn chặn được một
mã Tracking: `ProductIdentityResolver(pp_version=...)` nay là `Optional`.

Đọc nguyên văn quyết định tại
`docs/adr/ADR-107-public-purchase-authority-in-tracking.md`.

---

`D-01` + `OR-01` (`DEC-156` §1, APPROVED): identity catalog và price table
**không** phải hai nguồn dữ liệu độc lập. Chúng là hai projection của cùng một
`PublicPurchaseSourceVersion`, publish cùng lúc, mang cùng `version_id`, và
được kiểm ràng buộc chéo tại thời điểm publish/load.

## Vì sao loader này STRICT tới mức khó chịu

`INV-02`. `FilePriceProvider.from_yaml()` đọc `data.get("prices", [])` và bỏ
qua mọi khoá top-level khác. Nghĩa là một lỗi chính tả ở `products:` sẽ nạp 0
dòng identity **trong im lặng** — và một danh mục rỗng im lặng biến mọi sản
phẩm thành Pending, một sự cố trông y hệt "chưa ai nhập dữ liệu". Vì thế
loader của projection identity từ chối: thiếu khối, sai tên khối, khối rỗng,
hay có khoá top-level lạ đều là LỖI LOAD.

## Ranh giới với `FilePriceProvider` (FROZEN — `DEC-153`)

`INV-03` cho đúng MỘT đường đi hợp lệ: loader này validate CẢ HAI projection,
rồi khối `prices` **đã validate** được truyền vào `FilePriceProvider` qua
constructor `rows`. File này vì thế:

- KHÔNG sửa `app/modules/pricing/file_price_provider.py` (`CHECK-105D-28` B3
  assert diff của file đó là RỖNG);
- KHÔNG import nó (`CHECK-105D-16` assert module identity không import price
  provider nào). `price_rows` được **phơi ra** dưới dạng dict thuần; lớp
  composition (`TASK-105E`) là nơi dựng provider. Đó là lý do hai gate tưởng
  như mâu thuẫn thực ra không mâu thuẫn: validate ≠ construct.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from app.modules.validation.text import fold


class PublicPurchaseSourceError(ValueError):
    """Nguồn Public Purchase sai cấu trúc — LỖI LOAD, không phải danh mục rỗng.

    `reason` là mã máy đọc được để test khẳng định đúng luật nào đã nổ, không
    phải parse chuỗi thông báo (cùng khuôn với `InvalidPriceMasterError`).
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


class SourceVersionNotFoundError(LookupError):
    """`§3.3` câu 9 — thiếu version là hỏng hệ thống, KHÔNG phải Pending."""


class SourceStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ROLLED_BACK = "ROLLED_BACK"


_TOP_LEVEL_KEYS = frozenset(
    {
        "source_id",
        "version_id",
        "status",
        "published_at",
        "published_by",
        "supersedes",
        "rollback_of",
        "note",
        "products",
        "prices",
    }
)


@dataclass(frozen=True)
class PublicPurchaseIdentityRow:
    """E-B — identity projection."""

    product_code: str
    product_name: str
    aliases: tuple[str, ...] = ()
    active_from: Optional[date] = None
    active_to: Optional[date] = None


@dataclass(frozen=True)
class PublicPurchaseSourceVersion:
    """E-A — một version, hai projection, một `content_hash` trên cả hai."""

    source_id: str
    version_id: str
    status: SourceStatus
    content_hash: str
    identity_rows: tuple[PublicPurchaseIdentityRow, ...]
    price_rows: tuple[dict[str, Any], ...]
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    supersedes: Optional[str] = None
    rollback_of: Optional[str] = None
    note: Optional[str] = None

    def exact_match_codes(
        self, *, raw_key: str, aid: str
    ) -> tuple[tuple[str, str], ...]:
        """Mọi `product_code` khớp EXACT, kèm trường đã khớp (`PP_PRODUCT_CODE`
        hoặc `PP_ALIAS`).

        Thứ tự trả về theo thứ tự dòng trong version — ổn định, không phụ
        thuộc thứ tự dict (`INV-64`).
        """
        hits: list[tuple[str, str]] = []
        for row in self.identity_rows:
            if row.product_code == raw_key or fold(row.product_code) == aid:
                hits.append((row.product_code, "PP_PRODUCT_CODE"))
                continue
            for alias in row.aliases:
                if alias == raw_key or fold(alias) == aid:
                    hits.append((row.product_code, "PP_ALIAS"))
                    break
        return tuple(hits)

    def identity_row(self, product_code: str) -> Optional[PublicPurchaseIdentityRow]:
        for row in self.identity_rows:
            if row.product_code == product_code:
                return row
        return None

    def validated_price_rows(self) -> tuple[dict[str, Any], ...]:
        """Khối `prices` ĐÃ validate, để truyền vào `FilePriceProvider(rows=…)`.

        Trả dict thuần chứ không phải một provider: `INV-03` cho phép truyền
        rows, còn `CHECK-105D-16` cấm module này import price provider. Việc
        dựng provider thuộc lớp composition (`TASK-105E`).
        """
        return self.price_rows


def canonical_content_hash(
    identity_rows: list[dict[str, Any]], price_rows: list[dict[str, Any]]
) -> str:
    """`INV-10` — hash trên biểu diễn canonical của CẢ HAI projection."""
    payload = json.dumps(
        {"products": identity_rows, "prices": price_rows},
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class PublicPurchaseSourceLoader:
    """Đường nạp DUY NHẤT của Public Purchase (`INV-03`, `G28` B3/B6).

    Hai projection đi qua đây cùng nhau hoặc không đi. Không có phương thức
    "chỉ nạp identity" hay "chỉ nạp prices" — vì tồn tại một phương thức như
    thế là đã tạo ra nguồn vận hành thứ hai mà `OR-01` cấm.
    """

    @staticmethod
    def load(data: Any) -> PublicPurchaseSourceVersion:
        if not isinstance(data, dict):
            raise PublicPurchaseSourceError(
                "nguồn Public Purchase phải là một ánh xạ khoá-giá trị",
                reason="not_a_mapping",
            )

        unknown = sorted(set(data) - _TOP_LEVEL_KEYS)
        if unknown:
            raise PublicPurchaseSourceError(
                f"khoá top-level lạ: {unknown} — INV-02 cấm bỏ qua trong im lặng",
                reason="unknown_top_level_key",
            )

        for block in ("products", "prices"):
            if block not in data:
                raise PublicPurchaseSourceError(
                    f"thiếu khối {block!r} — LỖI LOAD, không phải danh mục rỗng",
                    reason=f"missing_{block}_block",
                )
            if not isinstance(data[block], list):
                raise PublicPurchaseSourceError(
                    f"khối {block!r} phải là một danh sách",
                    reason=f"malformed_{block}_block",
                )
            if not data[block]:
                raise PublicPurchaseSourceError(
                    f"khối {block!r} rỗng — LỖI LOAD (INV-02)",
                    reason=f"empty_{block}_block",
                )

        version_id = _require_text(data, "version_id")
        source_id = data.get("source_id") or "PUBLIC_PURCHASE"
        status = SourceStatus(data.get("status", SourceStatus.PUBLISHED.value))

        identity_rows = _parse_identity_rows(data["products"])
        price_rows = tuple(dict(row) for row in data["prices"])

        _validate_identity_uniqueness(identity_rows)
        _validate_referential_integrity(identity_rows, price_rows)

        return PublicPurchaseSourceVersion(
            source_id=source_id,
            version_id=version_id,
            status=status,
            content_hash=canonical_content_hash(
                list(data["products"]), list(data["prices"])
            ),
            identity_rows=identity_rows,
            price_rows=price_rows,
            published_at=data.get("published_at"),
            published_by=data.get("published_by"),
            supersedes=data.get("supersedes"),
            rollback_of=data.get("rollback_of"),
            note=data.get("note"),
        )


def _require_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PublicPurchaseSourceError(
            f"{key} REQUIRED và không được rỗng", reason=f"missing_{key}"
        )
    return value


def _parse_identity_rows(rows: list[Any]) -> tuple[PublicPurchaseIdentityRow, ...]:
    parsed: list[PublicPurchaseIdentityRow] = []
    for number, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise PublicPurchaseSourceError(
                f"dòng identity #{number} phải là một ánh xạ",
                reason="malformed_identity_row",
            )
        code = row.get("product_code")
        if not isinstance(code, str) or not code.strip():
            raise PublicPurchaseSourceError(
                f"dòng identity #{number} thiếu product_code",
                reason="missing_product_code",
            )
        aliases = row.get("aliases") or ()
        if isinstance(aliases, str) or not all(isinstance(a, str) for a in aliases):
            raise PublicPurchaseSourceError(
                f"dòng identity #{number}: aliases phải là danh sách chuỗi",
                reason="malformed_aliases",
            )
        parsed.append(
            PublicPurchaseIdentityRow(
                product_code=code,
                product_name=row.get("product_name") or "",
                aliases=tuple(aliases),
                active_from=row.get("active_from"),
                active_to=row.get("active_to"),
            )
        )
    return tuple(parsed)


def _validate_identity_uniqueness(
    rows: tuple[PublicPurchaseIdentityRow, ...]
) -> None:
    """`INV-04`, `INV-05`, `INV-09`.

    `INV-05` (unique sau `fold`) không phải sự cầu toàn: `DEC-147` §4 ghi nhận
    `normCode` của Tracking đã từng gộp nhầm hai mã chỉ khác một gạch nối.
    Hai mã chỉ khác hoa/thường/khoảng trắng là một LỖI dữ liệu, không phải hai
    sản phẩm.
    """
    seen_raw: set[str] = set()
    seen_folded: dict[str, str] = {}
    for row in rows:
        if row.product_code in seen_raw:
            raise PublicPurchaseSourceError(
                f"product_code trùng trong version: {row.product_code!r}",
                reason="duplicate_product_code",
            )
        seen_raw.add(row.product_code)

        folded = fold(row.product_code)
        if folded in seen_folded:
            raise PublicPurchaseSourceError(
                f"product_code {row.product_code!r} và {seen_folded[folded]!r} "
                "đụng độ sau fold() — INV-05",
                reason="folded_product_code_collision",
            )
        seen_folded[folded] = row.product_code

    for row in rows:
        for alias in row.aliases:
            folded_alias = fold(alias)
            owner = seen_folded.get(folded_alias)
            if owner is not None and owner != row.product_code:
                raise PublicPurchaseSourceError(
                    f"alias {alias!r} của {row.product_code!r} trùng product_code "
                    f"của sản phẩm khác ({owner!r}) — INV-09",
                    reason="alias_collides_with_other_product_code",
                )


def _validate_referential_integrity(
    identity_rows: tuple[PublicPurchaseIdentityRow, ...],
    price_rows: tuple[dict[str, Any], ...],
) -> None:
    """`INV-06` — mọi `price_rows[*].product_key` phải có trong `identity_rows`.

    Kiểm tại thời điểm LOAD, không phải lúc tính giá/KPI/lương. Một mã có giá
    mà vắng trong catalog là một identity không tra tới được; phát hiện nó lúc
    publish tốn một phút, phát hiện nó lúc trả lương thì đã muộn.
    """
    known = {row.product_code for row in identity_rows}
    known_folded = {fold(code) for code in known}
    for number, row in enumerate(price_rows, start=1):
        key = row.get("product_key")
        if not isinstance(key, str) or not key.strip():
            raise PublicPurchaseSourceError(
                f"dòng price #{number} thiếu product_key", reason="missing_product_key"
            )
        if key not in known and fold(key) not in known_folded:
            raise PublicPurchaseSourceError(
                f"dòng price #{number}: product_key {key!r} không tồn tại trong "
                "identity_rows của cùng version — INV-06",
                reason="price_key_absent_from_identity",
            )


class PublicPurchaseSourceRepository:
    """Kho version đã publish, tra theo `version_id`. Published = IMMUTABLE."""

    def __init__(self) -> None:
        self._by_id: dict[str, PublicPurchaseSourceVersion] = {}

    def publish(self, version: PublicPurchaseSourceVersion) -> None:
        if version.version_id in self._by_id:
            raise PublicPurchaseSourceError(
                f"version_id {version.version_id} đã publish — IMMUTABLE (§3.3 câu 13)",
                reason="version_already_published",
            )
        self._by_id[version.version_id] = version

    def get(self, version_id: str) -> PublicPurchaseSourceVersion:
        try:
            return self._by_id[version_id]
        except KeyError:
            raise SourceVersionNotFoundError(
                f"không có pp_version_id {version_id!r}; KHÔNG fallback sang "
                "version mới nhất, KHÔNG chuyển thành Pending (§3.3 câu 9)"
            ) from None
