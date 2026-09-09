"""R6 §3 — cửa metadata: ĐỌC, không suy luận, và năm lý do tách rời."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pytest

from app.modules.product.identity.keys import raw_identity_key
from app.modules.reporting import product_metrics as pmx
from app.web import line_identity, product_taxonomy as pt
from tests.test_r6_dashboard_metrics import detail, line


@dataclass(frozen=True)
class FakeIdentity:
    """Đúng hình dạng mà `identity_gateway.confirmed_identities` trả về ở chỗ
    R6 đọc nó: một object có `source_product_code`."""
    source_product_code: Optional[str]


def make(product_raw="Tivi Samsung 55Q6FA", *, reasons=(), **kwargs):
    business_line = line(**kwargs)
    business_line = type(business_line)(
        **{**business_line.__dict__, "pending_reasons": tuple(reasons)})
    return detail(business_line, product_raw=product_raw,
                  product_key="pk-" + product_raw[:4])


def resolve(product_raw="Tivi Samsung 55Q6FA", *, reasons=(),
            confirmed=(), out_of_catalog=(), code="TV-01",
            display=None, conflict_resolved=None):
    item = make(product_raw, reasons=reasons)
    key = raw_identity_key(product_raw)
    decisions = line_identity.Decisions.of(
        confirmed=[key] if confirmed else [],
        out_of_catalog=[key] if out_of_catalog else [],
        conflict_resolved=conflict_resolved)
    identities = {key: FakeIdentity(code)} if code else {}
    return item, pt.metadata_of(
        item, decisions=decisions, identities=identities,
        display=display if display is not None
        else {"TV-01": {"model_label": "55Q6FA", "brand": "Samsung",
                        "category_label": "Tivi"}})


# --- Năm lý do, tách rời ------------------------------------------------------

def test_a_matched_line_reads_all_three_metadata_fields():
    _item, meta = resolve(confirmed=True)
    assert meta.state == pt.STATE_MATCHED
    assert (meta.tracking_code, meta.model_label, meta.brand,
            meta.category_label) == ("TV-01", "55Q6FA", "Samsung", "Tivi")


def test_an_unresolved_line_gets_the_unresolved_reason():
    _item, meta = resolve(reasons=("IDENTITY_UNRESOLVED",))
    assert meta.state == pt.STATE_UNRESOLVED
    assert meta.brand is None and meta.category_label is None


def test_a_conflicted_line_gets_the_conflict_reason_not_the_unresolved_one():
    """"Chưa ai xem" và "hai bên đã xem và không khớp" cần hai câu khác nhau,
    vì chúng cần hai hành động khác nhau."""
    _item, meta = resolve(reasons=("IDENTITY_CONFLICT",), confirmed=True)
    assert meta.state == pt.STATE_CONFLICT


def test_an_out_of_catalog_line_gets_its_own_reason():
    _item, meta = resolve(out_of_catalog=True)
    assert meta.state == pt.STATE_OUT_OF_CATALOG


def test_a_stale_target_is_told_apart_from_missing_metadata():
    """`line_identity` xếp một dòng stale là `MATCHED_TRACKING`, và đúng như
    vậy — dòng ĐÃ từng được khớp. Nhưng ở R6 nó phải nhìn ra được: xếp ngành
    hàng bên Tracking cho một mã không còn tồn tại sẽ không có tác dụng gì.
    """
    _item, meta = resolve(reasons=("MAPPING_STALE_TARGET_ABSENT",),
                          confirmed=True)
    assert meta.state == pt.STATE_STALE_TARGET
    assert meta.state != pt.STATE_METADATA_ABSENT


def test_a_matched_line_with_no_catalog_row_is_metadata_absent():
    _item, meta = resolve(confirmed=True, display={})
    assert meta.state == pt.STATE_METADATA_ABSENT
    assert meta.tracking_code == "TV-01"


def test_a_matched_mapping_without_a_tracking_code_is_metadata_absent():
    _item, meta = resolve(confirmed=True, code=None)
    assert meta.state == pt.STATE_METADATA_ABSENT


def test_every_undecided_state_has_a_label_and_a_reason_and_a_fixed_rank():
    for state in pt.UNDECIDED_ORDER:
        assert pt.UNDECIDED_LABELS[state]
        assert pt.UNDECIDED_REASONS[state]
    assert len(set(pt.UNDECIDED_ORDER)) == len(pt.UNDECIDED_ORDER) == 5


# --- Không suy metadata từ tên thô -------------------------------------------

def test_a_brand_name_inside_the_raw_product_text_never_becomes_a_brand():
    """Tên hàng trên sổ nói rõ "Samsung", nhưng dòng chưa khớp mã ⟹ hãng vẫn
    `None`. Đây là ranh giới `PHB-06 §3`/`BR-02`/`BR-10`, và nó là lý do
    `bucket_for` không nhận `product_raw` như một đầu vào phân loại."""
    _item, meta = resolve("Tivi Samsung 55Q6FA cực đẹp",
                          reasons=("IDENTITY_UNRESOLVED",))
    assert meta.brand is None
    assert pt.brand_bucket(meta).kind == pmx.KIND_UNDECIDED


def test_the_category_label_arrives_verbatim_from_tracking():
    """Reports KHÔNG chuẩn hoá lại chuỗi Tracking gửi sang — nếu Tracking nói
    "Điều hoà" thì bảng hiện đúng "Điều hoà"."""
    _item, meta = resolve(
        confirmed=True,
        display={"TV-01": {"model_label": None, "brand": None,
                           "category_label": "Điều hoà"}})
    assert pt.category_bucket(meta).key == "Điều hoà"


def test_reports_holds_no_category_vocabulary_of_its_own():
    """Canh bằng chính MÃ NGUỒN: không tên nhóm hàng canonical nào của Tracking
    được phép xuất hiện như DỮ LIỆU trong module taxonomy của R6. Cùng kỷ luật
    mà `tests/test_r51_category_label.py` đã dựng cho R5.1."""
    import inspect
    source = inspect.getsource(pt)
    # Bỏ docstring/comment: các nhãn ấy ĐƯỢC PHÉP xuất hiện trong văn xuôi
    # giải thích (và `CATEGORY_TAXONOMY_NOTE` cố ý trích dẫn `DEC-206`).
    code_only = "\n".join(
        stripped for stripped in
        (row.split("#")[0] for row in source.splitlines())
        if not stripped.strip().startswith(("\"", "'")))
    for name in ("Tủ lạnh", "Máy giặt", "Bếp từ"):
        assert name not in code_only, f"{name!r} nằm trong mã taxonomy của R6"


# --- Nhãn mặt hàng: ba bậc fallback -------------------------------------------

def test_a_matched_product_label_prefers_the_model_then_the_tracking_code():
    item, meta = resolve(confirmed=True)
    assert pt.product_bucket(item, meta).label == "55Q6FA"
    item, meta = resolve(
        confirmed=True,
        display={"TV-01": {"model_label": None, "brand": "Samsung",
                           "category_label": None}})
    assert pt.product_bucket(item, meta).label == "TV-01"


def test_the_product_key_is_the_bucket_key_whatever_the_metadata_says():
    """`product_key` là khoá phân tích DUY NHẤT — không bao giờ bị thay bằng
    mã Tracking, và không bao giờ dồn nhiều mặt hàng vào một ô "chưa xác
    định"."""
    item, meta = resolve(reasons=("IDENTITY_UNRESOLVED",))
    assert pt.product_bucket(item, meta).key == item["product_key"]
    item2, meta2 = resolve(confirmed=True)
    assert pt.product_bucket(item2, meta2).key == item2["product_key"]


def test_an_unmatched_product_row_declares_itself_undecided_with_its_reason():
    item, meta = resolve(reasons=("IDENTITY_UNRESOLVED",))
    bucket = pt.product_bucket(item, meta)
    assert bucket.kind == pmx.KIND_UNDECIDED
    assert bucket.reason == pt.UNDECIDED_REASONS[pt.STATE_UNRESOLVED]


# --- Chiều gộp ----------------------------------------------------------------

def test_an_unknown_dimension_falls_back_to_product_without_raising():
    assert pt.parse_dimension("khong-co") == pt.DIMENSION_PRODUCT
    assert pt.parse_dimension(None) == pt.DIMENSION_PRODUCT
    assert pt.parse_dimension("nhom-hang") == pt.DIMENSION_CATEGORY


def test_buckets_for_refuses_an_unknown_dimension():
    item, meta = resolve(confirmed=True)
    with pytest.raises(ValueError, match="chiều gộp"):
        pt.buckets_for([item], [meta], dimension="mau-sac")


def test_buckets_for_refuses_mismatched_lengths():
    item, meta = resolve(confirmed=True)
    with pytest.raises(ValueError, match="cùng độ dài"):
        pt.buckets_for([item, item], [meta], dimension=pt.DIMENSION_BRAND)


# --- Coverage ------------------------------------------------------------------

def test_coverage_counts_each_reason_separately_and_keeps_a_fixed_order():
    metadata = [
        resolve(confirmed=True)[1],
        resolve("Máy giặt A", reasons=("IDENTITY_UNRESOLVED",))[1],
        resolve("Máy giặt B", reasons=("IDENTITY_CONFLICT",), confirmed=True)[1],
        resolve("Máy giặt C", out_of_catalog=True)[1],
    ]
    result = pt.coverage(metadata)
    assert result.matched_lines == 1
    assert result.total_lines == 4
    assert [state for state, _ in result.by_state] == [
        pt.STATE_UNRESOLVED, pt.STATE_CONFLICT, pt.STATE_OUT_OF_CATALOG]
    assert not result.is_complete


def test_an_empty_slice_is_never_complete():
    """Kỳ rỗng ⟹ `False`: không có dòng nào thì cũng không có bằng chứng nào
    cho một lời khẳng định "đã đủ" (fail-closed, `DEC-143` §1)."""
    assert not pt.coverage([]).is_complete
