"""R1-A1 — ANNOTATION CONTRACT. Falsification suite của sub-repair R1-A1.

Nguồn: Independent Review R1-A **Finding #1** tại `dead82e`.
Bằng chứng BEFORE/AFTER: `docs/tasks/TASK-110_REPAIR_PROGRESS.md` → R1-A1.

Finding #1: `_field_checker()` chỉ hiểu một tập con rất hẹp của `typing`, và
mọi annotation ngoài tập đó ÂM THẦM rơi xuống đường không kiểm. Đo được tại
`dead82e` trên 51 dạng annotation: 10 BYPASSED, 4 REJECTED, 9 UNDECLARED.

Bất biến mà file này canh giữ:

    UNKNOWN ≠ ANY.

Mỗi annotation hoặc nằm trong ngữ pháp canonical và được validate ĐỦ ngữ nghĩa,
hoặc nổ `CanonicalContractViolation` NGAY LÚC IMPORT. Không có ô thứ ba, và
đặc biệt không có ô "framework không hiểu nên thôi bỏ qua".

Phần lớn test ở đây khai canonical type ĐỘNG. Chúng đăng ký vào registry của
`canonical.py` như mọi canonical type khác — đó là lý do các assertion về
inventory (`test_r1a_canonical_type_coverage.py`) lọc theo module `app.`.
"""

from __future__ import annotations

import dataclasses
import pickle
import typing
from dataclasses import dataclass, replace
from datetime import date
from types import MappingProxyType
from typing import Any, Literal, Mapping, Optional, Sequence, TypeVar, Union

import pytest

from app.modules.domain.canonical import (
    CanonicalContractViolation,
    CanonicalFieldError,
    FrozenMapping,
    canonical,
    canonical_types,
)
from app.modules.domain.models import MAPPING_STATUS_UNMAPPED
from app.modules.mapping.employee_mapper import MappingResult, RecordRef

# Nạp module còn lại để registry đầy đủ khi file này chạy độc lập.
import app.modules.validation.employee_mapping  # noqa: E402,F401

T_CONSTRAINED = TypeVar("T_CONSTRAINED", int, str)
T_BOUND = TypeVar("T_BOUND", bound=int)
SENTINEL = object()


class Marker:
    """Lớp thường, đóng vai 'class reference' trong các case union."""


def build(annotation):
    """Khai một canonical type một-field mang `annotation`."""
    cls = type("Probe", (), {
        "__annotations__": {"value": annotation},
        "__post_init__": lambda self: None,
        "__module__": __name__,
    })
    return canonical()(dataclass(frozen=True)(cls))


def accepts(annotation, value) -> bool:
    cls = build(annotation)
    try:
        cls(value=value)
        return True
    except (TypeError, ValueError):
        return False


# ═══════════════════════ FINDING #1 — năm case reviewer đã falsify

@pytest.mark.parametrize("value", [1, "a"])
def test_f1_union_accepts_every_declared_branch(value):
    assert accepts(Union[int, str], value)


@pytest.mark.parametrize("value", [1.5, SENTINEL, None, b"x", [], True])
def test_f1_union_rejects_everything_outside_its_branches(value):
    """`Union[int, str]` từng nhận `1.5`. `True` cũng phải bị loại: nó là một
    `int` với `isinstance` nhưng kiểu chính xác của nó là `bool`."""
    assert not accepts(Union[int, str], value)


@pytest.mark.parametrize("value", [1, "a", None])
def test_f2_optional_union_accepts_branches_and_none(value):
    assert accepts(Optional[Union[int, str]], value)


@pytest.mark.parametrize("value", [1.5, SENTINEL, b"x"])
def test_f2_optional_union_rejects_outsiders(value):
    """`Optional[Union[int, str]]` từng nhận `object()`."""
    assert not accepts(Optional[Union[int, str]], value)


@pytest.mark.parametrize("annotation, good, bad", [
    (eval("str | None"), ["x", None], [1, 1.5, []]),
    (eval("int | str"), [1, "a"], [1.5, None, SENTINEL]),
    (eval("int | str | None"), [1, "a", None], [1.5, True, SENTINEL]),
])
def test_f3_f4_pep604_unions_are_handled(annotation, good, bad):
    """`str | None` từng LOẠI CẢ giá trị hợp lệ: `get_origin` trả
    `types.UnionType` chứ không phải `typing.Union`, nên nó bị đem đi
    `isinstance(value, types.UnionType)` và không giá trị nào qua nổi."""
    for value in good:
        assert accepts(annotation, value), f"{value!r} phải được nhận"
    for value in bad:
        assert not accepts(annotation, value), f"{value!r} phải bị loại"


@pytest.mark.parametrize("value", ["a", "b"])
def test_f5_literal_accepts_its_own_values(value):
    assert accepts(Literal["a", "b"], value)


@pytest.mark.parametrize("value", ["c", "", 1, None, SENTINEL])
def test_f5_literal_rejects_everything_else(value):
    """`Literal['a','b']` từng nhận `'c'`."""
    assert not accepts(Literal["a", "b"], value)


def test_f5b_literal_compares_exact_type_not_just_equality():
    """`True == 1` trong Python. Chỉ so bằng thì `Literal[1]` sẽ nhận `True`."""
    assert accepts(Literal[1], 1)
    assert not accepts(Literal[1], True)
    assert accepts(Literal[True], True)
    assert not accepts(Literal[True], 1)


@pytest.mark.parametrize("annotation", [T_CONSTRAINED, T_BOUND])
def test_f6_f7_typevar_is_refused_at_decoration(annotation):
    """`TypeVar` có ràng buộc từng nhận MỌI giá trị. Chính sách của R1-A1 là
    TỪ CHỐI, không phải hỗ trợ nửa vời: canonical dataclass trong dự án này
    không generic, và đỡ `TypeVar` cho đúng nghĩa là phải mô hình hoá binding
    và variance."""
    with pytest.raises(CanonicalContractViolation, match="TypeVar"):
        build(annotation)


# ══════════════════ NGỮ PHÁP ĐÓNG — UNKNOWN phải nổ, không được thành ANY

@pytest.mark.parametrize("annotation, label", [
    (typing.Final[int], "Final"),
    (typing.NoReturn, "NoReturn"),
    (typing.Self, "Self"),
    (typing.Optional, "Optional chưa subscript"),
    ("KhongTonTaiODau", "forward reference không giải được"),
])
def test_unknown_annotation_fails_at_decoration_not_silently(annotation, label):
    with pytest.raises(CanonicalContractViolation):
        build(annotation)


def test_the_grammar_is_closed_by_recursion_not_by_a_top_level_switch():
    """Đây là điểm khác biệt giữa "thêm năm nhánh `if`" và "đóng ngữ pháp": một
    construct KHÔNG hỗ trợ nằm SÂU bên trong một construct ĐƯỢC hỗ trợ vẫn phải
    nổ."""
    with pytest.raises(CanonicalContractViolation, match="TypeVar"):
        build(Union[int, T_CONSTRAINED])
    with pytest.raises(CanonicalContractViolation, match="TypeVar"):
        build(Optional[T_BOUND])
    with pytest.raises(CanonicalContractViolation, match="TypeVar"):
        build(typing.Annotated[T_CONSTRAINED, "meta"])


def test_literal_values_outside_the_allowed_types_fail_at_decoration():
    with pytest.raises(CanonicalContractViolation, match="Literal"):
        build(Literal[1.5])


def test_a_nonsense_annotation_object_fails_at_decoration():
    """Bất biến phải đúng cả với construct chưa tồn tại lúc viết code này: nhánh
    cuối của phép phân tích là `raise`, nên bất cứ thứ gì không khớp ngữ pháp
    đều rơi vào đó."""
    class NotAType:
        def __repr__(self):
            return "<annotation lạ>"

    with pytest.raises(CanonicalContractViolation, match="NGOÀI ngữ pháp"):
        build(NotAType())


# ═══════════════════════════ NGỮ PHÁP ĐƯỢC HỖ TRỢ — validate ĐỦ ngữ nghĩa

@pytest.mark.parametrize("annotation, good, bad", [
    (int, [0, -3], [True, "1", 1.0, None]),
    (str, ["", "x"], [1, None, []]),
    (bool, [True, False], [1, 0, "yes", None]),
    (date, [date(2026, 1, 1)], ["2026-01-01", 1, None]),
    (Optional[str], ["x", None], [1, 1.5, []]),
    (Optional[int], [3, None], [True, "3"]),
    (tuple, [(), (1, "a")], [[], "abc", 5, None]),
    (frozenset, [frozenset()], [set(), [], None]),
    (FrozenMapping, [FrozenMapping({"a": 1})], [{}, MappingProxyType({}), None]),
    (typing.Tuple[int, ...], [(), (1, 2)], [[], 5, None]),
    (Mapping[str, int], [FrozenMapping({"a": 1}), MappingProxyType({"a": 1})], [5, None]),
    (Sequence[int], [(1, 2)], [5, None]),
    (typing.Annotated[int, "meta"], [1], ["a", True, None]),
    (Union[Marker, int], [Marker(), 1], ["x", 1.5, None]),
    (Union[str, bytes, None], ["x", b"x", None], [1, 1.5, SENTINEL]),
    (Optional[Literal["a", "b"]], ["a", "b", None], ["c", 1]),
    (Union[Literal[1], Literal["a"]], [1, "a"], [2, "b", True, None]),
    (None, [None], [1, "x", SENTINEL]),
    (type, [int, Marker], [5, None]),
])
def test_supported_grammar_validates_full_semantics(annotation, good, bad):
    for value in good:
        assert accepts(annotation, value), f"{annotation}: {value!r} phải được nhận"
    for value in bad:
        assert not accepts(annotation, value), f"{annotation}: {value!r} phải bị loại"


def test_any_is_unchecked_only_when_the_annotation_really_is_any():
    """`Any` được bỏ qua phép kiểm kiểu — nhưng CHỈ khi tác giả thực sự viết
    `Any`. Đó là khác biệt cốt lõi với bản trước, nơi `Any` là nơi mọi thứ
    không hiểu được rơi vào."""
    for value in (1, "x", None, SENTINEL, ()):
        assert accepts(Any, value)
    # Chính sách bất biến vẫn đứng trên `Any`.
    for value in ([], {}, set()):
        assert not accepts(Any, value)


def test_scalar_strictness_survives_inside_a_union():
    """Lớp con của `str` phải bị loại kể cả khi `str` chỉ là một nhánh."""
    class Shifty(str):
        n = 0

        def __str__(self):
            Shifty.n += 1
            return f"đọc lần {Shifty.n}"

    assert accepts(Optional[str], "x")
    assert not accepts(Optional[str], Shifty("x"))
    assert not accepts(Union[int, str], Shifty("x"))


def test_the_mutable_policy_still_wins_over_a_matching_branch():
    """`Union[list, int]`: giá trị `[]` KHỚP nhánh `list`, nhưng chính sách bất
    biến vẫn loại nó. R1-A1 không đụng vào chính sách đó."""
    assert accepts(Union[list, int], 1)
    assert not accepts(Union[list, int], [])


# ═══════════════════════════ TÁI DỰNG — replace / pickle phải đi qua hợp đồng

def test_replace_revalidates_a_union_field():
    cls = build(Union[int, str])
    ok = cls(value=1)
    assert replace(ok, value="a").value == "a"
    with pytest.raises(CanonicalFieldError):
        replace(ok, value=1.5)


def test_pickle_round_trip_of_a_production_union_field_goes_through_the_contract():
    ok = MappingResult(normalized=None, status=MAPPING_STATUS_UNMAPPED,
                       default_lead_source=None, include_in_kpi=None)
    assert pickle.loads(pickle.dumps(ok)) == ok


# ═════════════════════════════════ NON-REGRESSION trên production

def test_every_production_canonical_type_still_builds_its_contract():
    prod = [c for c in canonical_types() if c.__module__.startswith("app.")]
    assert len(prod) == 11
    for cls in prod:
        contract = getattr(cls, "__canonical_contract__", None)
        assert contract, cls.__name__
        assert {n for n, _ in contract} == {f.name for f in dataclasses.fields(cls)}


def test_production_error_messages_are_unchanged():
    """Thông báo là bằng chứng đã trích dẫn ở nhiều nơi; ngữ pháp mới không
    được làm chúng đổi giọng."""
    with pytest.raises((TypeError, ValueError), match="chuỗi thuần"):
        MappingResult(normalized=1, status="mapped", default_lead_source=None,
                      include_in_kpi=None, group="SALES")
    with pytest.raises((TypeError, ValueError), match="không được là None"):
        RecordRef(snapshot_id=None, index=0, label="x")


def test_optional_recordref_label_still_names_the_type():
    with pytest.raises(CanonicalFieldError, match="RecordRef"):
        MappingResult(normalized="Ly", status="mapped", default_lead_source=None,
                      include_in_kpi=None, group="SALES", record="not-a-RecordRef")
