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
from app.modules.domain.canonical import _Spec, _build_spec  # noqa: F401
import app.modules.domain.canonical as canonical_module  # noqa: E402
from app.modules.domain.models import MAPPING_STATUS_UNMAPPED
from app.modules.mapping.employee_mapper import MappingResult, RecordRef

# Nạp module còn lại để registry đầy đủ khi file này chạy độc lập.
import app.modules.validation.employee_mapping  # noqa: E402,F401

T_CONSTRAINED = TypeVar("T_CONSTRAINED", int, str)
T_BOUND = TypeVar("T_BOUND", bound=int)
SENTINEL = object()


class Marker:
    """Lớp thường, đóng vai 'class reference' trong các case union."""


# ── vật liệu cho P1 (hậu duệ generic) và P2 (class-like runtime)
import abc as _abc  # noqa: E402
import enum as _enum  # noqa: E402
import re as _re  # noqa: E402

TS = typing.TypeVarTuple("TS")
PS = typing.ParamSpec("PS")
REPattern = _re.Pattern


class TD(typing.TypedDict):
    a: int


class TDPartial(typing.TypedDict, total=False):
    a: int


class ProtoPlain(typing.Protocol):
    def f(self) -> None: ...


@typing.runtime_checkable
class ProtoRuntime(typing.Protocol):
    def f(self) -> None: ...


@typing.runtime_checkable
class ProtoData(typing.Protocol):
    x: int


class Impl:
    """Thoả cả `ProtoRuntime` lẫn `ProtoData`."""

    x = 1

    def f(self) -> None:
        return None


class _EvilMeta(type):
    def __instancecheck__(cls, obj):
        raise RuntimeError("__instancecheck__ nổ")


class EvilInstanceCheck(metaclass=_EvilMeta):
    pass


class NTuple(typing.NamedTuple):
    a: int


class Shade(_enum.Enum):
    RED = 1


BoxT = typing.TypeVar("BoxT")


class Box(typing.Generic[BoxT]):
    pass


class PlainABC(_abc.ABC):
    pass


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


def test_the_mutable_policy_still_wins_at_runtime_where_it_applies():
    """Chính sách bất biến KHÔNG đổi ở R1-A1 #3; chỉ ngữ pháp annotation được
    làm nhất quán với nó.

    `Union[list, int]` nay bị từ chối ngay lúc decorate (nhánh `list` chết —
    xem `test_every_runtime_checked_branch_of_a_union_must_be_inhabited`), nên
    chỗ chính sách bất biến còn thể hiện lúc CHẠY là field khai `Any`."""
    assert accepts(Any, 1)
    assert not accepts(Any, [])
    assert not accepts(Any, {})


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


# ══════════════════════ P1 — HẬU DUỆ GENERIC (Review R1-A1 #2)
#
# Ngữ pháp đóng ở tầng ngoài cùng là chưa đủ: bản trước quy mọi generic có tham
# số về `_ClassSpec(origin)` và VỨT BỎ `get_args()`, nên lớp lỗi cũ chỉ lùi
# xuống một tầng. `tuple[<TypeVar>]` decorate lọt.
#
# PHẠM VI: các test này khẳng định parser HIỂU và PHÂN LOẠI mọi nút. Việc có
# kiểm từng phần tử lúc chạy hay không là R1-D — xem
# `test_p1_boundary_parsing_is_not_element_validation`.

_UNSUPPORTED_DESCENDANTS = [
    ("tuple[TypeVar]", tuple[T_CONSTRAINED]),
    ("tuple[Final[int]]", tuple[typing.Final[int]]),
    ("tuple[Literal[1.5]]", tuple[Literal[1.5]]),
    ("tuple[NoReturn]", tuple[typing.NoReturn]),
    ("Callable[[TypeVar], int]", typing.Callable[[T_CONSTRAINED], int]),
    ("list[TypeVar]", list[T_CONSTRAINED]),
    ("dict[str, TypeVar]", dict[str, T_CONSTRAINED]),
    ("tuple[Union[int, TypeVar], ...]", tuple[Union[int, T_CONSTRAINED], ...]),
    ("tuple[Annotated[TypeVar, 'x']]", tuple[typing.Annotated[T_CONSTRAINED, "x"]]),
    ("Optional[tuple[TypeVar]]", Optional[tuple[T_CONSTRAINED]]),
    ("Union[int, tuple[TypeVar]]", Union[int, tuple[T_CONSTRAINED]]),
    ("Callable[[int], TypeVar]", typing.Callable[[int], T_CONSTRAINED]),
    ("Callable[..., TypeVar]", typing.Callable[..., T_CONSTRAINED]),
    # Sâu hơn — do chính lượt repair này tìm thêm.
    ("dict[str, tuple[Final[int]]]", dict[str, tuple[typing.Final[int]]]),
    ("tuple[tuple[tuple[NoReturn]]]", tuple[tuple[tuple[typing.NoReturn]]]),
    ("frozenset[TypeVar]", frozenset[T_CONSTRAINED]),
    ("tuple[Callable[[TypeVar], int], ...]",
     tuple[typing.Callable[[T_CONSTRAINED], int], ...]),
    ("Optional[dict[str, Literal[1.5]]]", Optional[dict[str, Literal[1.5]]]),
    ("tuple[Unpack[TypeVarTuple]]", tuple[typing.Unpack[TS]]),
    ("Callable[ParamSpec, int]", typing.Callable[PS, int]),
    # Target KHÔNG HASH ĐƯỢC. Tìm ra khi tự soát lại bản sửa của chính lượt
    # này: phép tra `target in <frozenset chính sách>` nổ `TypeError:
    # unhashable type` với một tham số dạng list — đúng lớp lỗi rò mà P2 nói
    # tới, do chính bản vá tạo ra. Nay `isinstance(target, type)` đứng trước
    # mọi phép tra tập hợp.
    ("tuple[[int]]", tuple[[int]]),
    ("dict[str, [int]]", dict[str, [int]]),
    ("tuple[[int], str]", tuple[[int], str]),
]


@pytest.mark.parametrize("label, annotation", _UNSUPPORTED_DESCENDANTS,
                         ids=[label for label, _ in _UNSUPPORTED_DESCENDANTS])
def test_p1_an_unsupported_descendant_is_refused_at_decoration(label, annotation):
    """Không tham số kiểu nào được bỏ qua im lặng, ở BẤT KỲ độ sâu nào."""
    with pytest.raises(CanonicalContractViolation):
        build(annotation)


@pytest.mark.parametrize("annotation, good, bad", [
    (tuple[int, ...], [(), (1, 2)], [[], 5, None]),
    (tuple[()], [(), (1,)], [[], 5, None]),
    (tuple[int], [(), (1,), ("a",)], [[], 5, None]),
    (frozenset[int], [frozenset(), frozenset({1})], [set(), 5, None]),
])
def test_p1_supported_generics_keep_working(annotation, good, bad):
    """Đóng hậu duệ không được làm hỏng generic hợp lệ."""
    for value in good:
        assert accepts(annotation, value), f"{annotation}: {value!r} phải được nhận"
    for value in bad:
        assert not accepts(annotation, value), f"{annotation}: {value!r} phải bị loại"


def test_p1_boundary_parsing_is_not_element_validation():
    """RANH GIỚI R1-A1 / R1-D, đóng đinh tường minh.

    `tuple[int]` phải PARSE được — nút con `int` được phân loại — nhưng R1-A1
    **không** kiểm từng phần tử lúc chạy. Nếu ai đó sửa điều này, họ đang làm
    R1-D, không phải R1-A1."""
    spec = _build_spec(tuple[int], "`value`")
    assert len(spec.children()) == 1
    assert accepts(tuple[int], ("không phải int",))


def test_p1_the_ellipsis_in_a_variadic_tuple_is_grammar_not_a_type():
    """`tuple[X, ...]` hợp lệ; `Ellipsis` ở chỗ khác thì không."""
    assert len(_build_spec(tuple[int, ...], "`value`").children()) == 1
    with pytest.raises(CanonicalContractViolation):
        build(typing.Callable[..., int])


@pytest.mark.parametrize("annotation", [
    typing.Callable, typing.Callable[[], None], typing.Callable[..., int],
    typing.Callable[[int, str], None],
])
def test_p1_the_callable_family_is_refused_entirely(annotation):
    """Hình dạng tham số của `Callable` (`([A, B], R)` — phần tử đầu là một
    list) không giống generic nào khác. Từ chối CẢ HỌ, kể cả dạng trần, là kết
    quả hợp lệ và tốt hơn hỗ trợ nửa vời."""
    with pytest.raises(CanonicalContractViolation, match="Callable"):
        build(annotation)


# ══════════════════ P2 — CLASS-LIKE KHÔNG AN TOÀN CHO `isinstance`

@pytest.mark.parametrize("label, target", [
    ("TypedDict", TD),
    ("TypedDict(total=False)", TDPartial),
    ("Protocol không runtime_checkable", ProtoPlain),
    ("typing.Protocol trần", typing.Protocol),
    ("metaclass __instancecheck__ nổ", EvilInstanceCheck),
], ids=lambda v: v if isinstance(v, str) else "")
def test_p2_isinstance_unsafe_targets_are_refused_with_a_contract_violation(label, target):
    """Đo tại `44018e3`: những target này làm `isinstance()` NỔ, và lỗi đó rò
    ra dưới dạng `TypeError`/`RuntimeError` THÔ ngay lúc decorate — framework
    tự vỡ chứ không đưa ra tuyên bố. Nay là một `CanonicalContractViolation`.

    Từ R1-A1 #3 chúng bị chặn bằng LUẬT CẤU TRÚC (metaclass), không phải bằng
    phép chạy thử `isinstance()` — xem
    `test_p2_a_conditional_instancecheck_cannot_pass_a_finite_probe`."""
    with pytest.raises(CanonicalContractViolation):
        build(target)


@pytest.mark.parametrize("label, annotation", [
    ("typing.IO[str]", typing.IO[str]),
    ("typing.IO", typing.IO),
    ("typing.TextIO", typing.TextIO),
    ("typing.BinaryIO", typing.BinaryIO),
    ("typing.Generic", typing.Generic),
], ids=lambda v: v if isinstance(v, str) else "")
def test_p2_annotation_only_classes_are_refused(label, annotation):
    """Nhóm này KHÔNG làm `isinstance()` nổ — nó trả `False` cho mọi object
    thật. Không phép thử runtime nào phát hiện được, nên đây là một chính sách
    được TUYÊN BỐ và test này là thứ canh nó."""
    with pytest.raises(CanonicalContractViolation, match="CHỈ DÙNG ĐỂ CHÚ THÍCH"):
        build(annotation)


@pytest.mark.parametrize("label, annotation, good, bad", [
    ("NamedTuple", NTuple, [NTuple(a=1)], [5]),
    ("re.Pattern", REPattern, [_re.compile("x")], ["x", 5]),
    ("generic người dùng (trần)", Box, [Box()], [5]),
    ("generic người dùng có tham số", Box[int], [Box()], [5]),
    ("FrozenMapping (framework tự sở hữu)", FrozenMapping,
     [FrozenMapping({"a": 1})], [{}, MappingProxyType({}), 5]),
    ("class thường", Marker, [Marker()], [5, None]),
], ids=lambda v: v if isinstance(v, str) else "")
def test_p2_runtime_safe_classes_stay_supported(label, annotation, good, bad):
    """Mặt còn lại: siết chặt mà chặn luôn class hợp lệ thì không phải sửa.

    Mỗi dòng ở đây BẮT BUỘC có ít nhất một witness được CHẤP NHẬN — không dùng
    danh sách valid rỗng để tuyên bố SUPPORTED (§10)."""
    assert good, f"{label}: một case SUPPORTED phải có ít nhất một witness"
    for value in good:
        assert accepts(annotation, value), f"{label}: {value!r} phải được nhận"
    for value in bad:
        assert not accepts(annotation, value), f"{label}: {value!r} phải bị loại"


@pytest.mark.parametrize("label, target", [
    ("Enum", Shade),
    ("abc.ABC subclass", PlainABC),
    ("Protocol runtime_checkable", ProtoRuntime),
    ("Protocol runtime_checkable có data", ProtoData),
    ("typing.SupportsInt", typing.SupportsInt),
    ("collections.abc.Mapping", Mapping[str, int]),
    ("collections.abc.Sequence", Sequence[int]),
], ids=lambda v: v if isinstance(v, str) else "")
def test_p2_custom_metaclass_targets_are_refused_structurally(label, target):
    """R1-A1 #3, finding #1. Chính sách nay là CẤU TRÚC, không phải chạy thử:

        metaclass là ĐÚNG `type`  ->  `isinstance()` là phép duyệt MRO ở tầng C
        metaclass khác            ->  có thể chạy hook người dùng -> TỪ CHỐI

    `ABCMeta`, `EnumMeta`, `_ProtocolMeta` đều chạy `__subclasshook__` /
    `__instancecheck__` do người dùng định nghĩa được. Siết chặt CÓ TUYÊN BỐ:
    không class nào trong production dùng chúng (đã audit), và ngoại lệ duy
    nhất — `FrozenMapping`/`FrozenCounter` của chính framework — được tin bằng
    ĐỊNH DANH."""
    with pytest.raises(CanonicalContractViolation, match="metaclass"):
        build(target)


def test_p2_a_conditional_instancecheck_cannot_pass_a_finite_probe():
    """Vì sao luật phải là CẤU TRÚC chứ không phải chạy thử.

    Metaclass dưới đây an toàn với đúng hai giá trị mà bản `d4a8797` dùng để
    "chứng minh" (`object()` và `None`) rồi nổ với dữ liệu thật. Một phép thử
    hữu hạn không bao giờ chứng minh được điều gì về một hàm tuỳ ý."""
    class CondMeta(type):
        def __instancecheck__(cls, obj):
            if obj is None or type(obj) is object:
                return False
            raise RuntimeError("nổ với giá trị thật")

    class Conditional(metaclass=CondMeta):
        pass

    # Bằng chứng phép thử hữu hạn KHÔNG phát hiện được:
    assert isinstance(object(), Conditional) is False
    assert isinstance(None, Conditional) is False
    with pytest.raises(RuntimeError):
        isinstance("giá trị thật", Conditional)
    # Nhưng luật cấu trúc thì chặn được:
    with pytest.raises(CanonicalContractViolation, match="metaclass"):
        build(Conditional)


@pytest.mark.parametrize("label, meta_body", [
    ("__hash__ nổ", {"__hash__": lambda cls: (_ for _ in ()).throw(RuntimeError("hash nổ"))}),
    ("__hash__ = None", {"__hash__": None}),
    ("__eq__ nổ", {"__eq__": lambda cls, o: (_ for _ in ()).throw(RuntimeError("eq nổ"))}),
    ("__instancecheck__ nổ", {"__instancecheck__": lambda cls, o: (_ for _ in ()).throw(RuntimeError("ic nổ"))}),
    ("__subclasscheck__ nổ", {"__subclasscheck__": lambda cls, o: (_ for _ in ()).throw(RuntimeError("sc nổ"))}),
], ids=lambda v: v if isinstance(v, str) else "")
def test_p2_classification_never_runs_hash_eq_or_instancecheck_of_the_target(label, meta_body):
    """R1-A1 #3, finding #2. Bản `d4a8797` tra chính sách bằng
    `target in frozenset(...)`, tức là gọi `__hash__` của metaclass lạ TRƯỚC
    khi target được coi là an toàn — nên một `__hash__` nổ làm lỗi thô thoát ra
    ngay lúc decorate. Nay mọi phép tra dùng `is`."""
    Meta = type("Meta", (type,), dict(meta_body))
    Hostile = Meta("Hostile", (), {})
    with pytest.raises(CanonicalContractViolation):
        build(Hostile)


# ═══════════════ SUPPORTED PHẢI CÓ MIỀN GIÁ TRỊ (§5, finding #3)

@pytest.mark.parametrize("label, annotation", [
    ("list", list), ("list[int]", list[int]),
    ("dict", dict), ("dict[str, int]", dict[str, int]),
    ("set", set), ("set[int]", set[int]),
    ("bytearray", bytearray),
    ("Optional[list[int]]", Optional[list[int]]),
    ("Union[list, dict]", Union[list, dict]),
], ids=lambda v: v if isinstance(v, str) else "")
def test_an_uninhabitable_annotation_is_refused_at_decoration(label, annotation):
    """Chính sách bất biến của canonical loại MỌI container mutable, nên một
    field khai kiểu đó decorate thành công rồi từ chối mọi giá trị — hợp đồng
    rỗng. SUPPORTED phải nghĩa là "có ít nhất một giá trị hợp lệ"."""
    with pytest.raises(CanonicalContractViolation, match="không bao giờ khớp được giá trị nào"):
        build(annotation)


def test_every_runtime_checked_branch_of_a_union_must_be_inhabited():
    """Luật NGHIÊM HƠN mức tối thiểu, cố ý: một nhánh union không khớp được giá
    trị nào là một lời khai SAI LỆCH. `Union[list, int]` nói "list hoặc int"
    trong khi mọi list đều bị loại."""
    with pytest.raises(CanonicalContractViolation, match="không bao giờ khớp được giá trị nào"):
        build(Union[list, int])
    # Nhánh hợp lệ thì vẫn hợp lệ.
    assert accepts(Union[str, int], 1)
    assert accepts(Optional[str], None)


def test_a_generic_argument_is_exempt_because_it_is_not_runtime_checked():
    """RANH GIỚI R1-A1 / R1-D: tham số của generic chỉ được PARSE, không được
    kiểm lúc chạy, nên luật "phải sống được" không áp cho chúng."""
    assert accepts(tuple[list[int], ...], ())
    assert accepts(tuple[list[int], ...], ([1],))


def test_the_mutable_policy_itself_is_unchanged():
    """R1-A1 #3 KHÔNG đụng vào chính sách container mutable (đó là R1-A3/R1-D);
    nó chỉ làm ngữ pháp annotation nhất quán với chính sách đang có."""
    from app.modules.domain.canonical import _MUTABLE_CONTAINERS

    assert _MUTABLE_CONTAINERS == (list, dict, set, bytearray)
    for value in ([], {}, set(), bytearray()):
        assert not accepts(Any, value)


# ═══════════════════════════ INITVAR (§6, finding #4)

def test_initvar_is_refused_at_decoration():
    """`dataclasses.fields()` bỏ qua `InitVar` nhưng `@dataclass` vẫn truyền nó
    vào `__post_init__`, nên hợp đồng field không phủ được và chữ ký wrapper
    của framework sai. Đo tại `d4a8797`: decorate lọt rồi constructor nổ
    `TypeError: __post_init__() takes 1 positional argument but 2 were given`."""
    @dataclass(frozen=True)
    class WithInitVar:
        kept: int
        seed: dataclasses.InitVar[int]

        def __post_init__(self, seed) -> None:
            pass

    with pytest.raises(CanonicalContractViolation, match="InitVar"):
        canonical()(WithInitVar)


def test_multiple_initvars_are_all_named():
    @dataclass(frozen=True)
    class TwoSeeds:
        kept: int
        a: dataclasses.InitVar[int]
        b: dataclasses.InitVar[str]

        def __post_init__(self, a, b) -> None:
            pass

    with pytest.raises(CanonicalContractViolation) as exc:
        canonical()(TwoSeeds)
    assert "`a`" in str(exc.value) and "`b`" in str(exc.value)


def test_an_initvar_only_dataclass_is_refused():
    @dataclass(frozen=True)
    class OnlySeed:
        seed: dataclasses.InitVar[int]

        def __post_init__(self, seed) -> None:
            pass

    with pytest.raises(CanonicalContractViolation, match="InitVar"):
        canonical()(OnlySeed)


def test_a_kw_only_initvar_is_refused():
    @dataclass(frozen=True, kw_only=True)
    class KwSeed:
        kept: int
        seed: dataclasses.InitVar[int]

        def __post_init__(self, seed) -> None:
            pass

    with pytest.raises(CanonicalContractViolation, match="InitVar"):
        canonical()(KwSeed)


def test_classvar_is_not_an_initvar_and_stays_legal():
    """`ClassVar` cũng nằm trong `__dataclass_fields__` nhưng KHÔNG phải field
    và KHÔNG được truyền vào `__post_init__` — nó vô hại, không được bắt nhầm."""
    @canonical()
    @dataclass(frozen=True)
    class WithClassVar:
        kept: int
        shared: typing.ClassVar[int] = 7

        def __post_init__(self) -> None:
            pass

    assert WithClassVar(kept=1).kept == 1
    assert WithClassVar.shared == 7
    assert {n for n, _ in WithClassVar.__canonical_contract__} == {"kept"}


# ═══════════════════════════ ĐỘ SÂU / ĐỘ PHỨC TẠP (§7, finding #5)

def _nest(depth):
    annotation = int
    for _ in range(depth):
        annotation = tuple[annotation, ...]
    return annotation


@pytest.mark.parametrize("depth", [1, 2, 10, 23, 24])
def test_depth_just_below_and_at_the_limit_is_accepted(depth):
    assert build(_nest(depth)) is not None


@pytest.mark.parametrize("depth", [25, 26, 40])
def test_depth_over_the_limit_is_a_contract_violation_not_a_recursionerror(depth):
    """Không bao giờ được dựa vào `RecursionError` của CPython làm chính sách:
    nó phụ thuộc stack còn lại, nên cùng một annotation có thể lúc parse được
    lúc không."""
    with pytest.raises(CanonicalContractViolation, match="lồng sâu quá"):
        build(_nest(depth))


@pytest.mark.parametrize("depth", [100, 300, 500])
def test_very_deep_annotations_still_end_in_a_contract_violation(depth):
    """Sâu hơn nữa, `typing.get_type_hints()` mới là chỗ hết stack trước. Điều
    được khẳng định ở đây là BIÊN LỖI: dù hết stack ở đâu trong đường xử lý của
    framework, kết quả vẫn là `CanonicalContractViolation`, không phải
    `RecursionError` thô."""
    with pytest.raises(CanonicalContractViolation):
        build(_nest(depth))


def test_beyond_a_point_python_itself_refuses_before_canonical_runs():
    """Ghi nhận RANH GIỚI: với annotation cực sâu, `@dataclass` của CPython nổ
    `RecursionError` TRƯỚC khi `@canonical` chạy. Đó nằm ngoài biên framework —
    không có canonical type nào được tạo ra, nên không có trạng thái nửa vời."""
    deep = _nest(5000)
    with pytest.raises(RecursionError):
        dataclass(frozen=True)(type("TooDeep", (), {
            "__annotations__": {"value": deep},
            "__post_init__": lambda self: None,
            "__module__": __name__,
        }))


def test_mixed_union_and_generic_nesting_counts_toward_the_same_limit():
    annotation = int
    for _ in range(13):
        annotation = Optional[tuple[annotation, ...]]
    with pytest.raises(CanonicalContractViolation, match="lồng sâu quá"):
        build(annotation)


def test_a_very_wide_union_is_bounded_too():
    """Trục BỀ RỘNG không nổ `RecursionError` nhưng vẫn là độ phức tạp không
    kiểm soát, nên nó cũng có ngân sách."""
    wide = Union[tuple(Literal[i] for i in range(600))]
    with pytest.raises(CanonicalContractViolation, match="nút"):
        build(wide)


# ═══════════════ BIÊN LỖI (§8) — annotation thù địch không rò lỗi thô

def test_a_hostile_annotation_object_cannot_leak_a_raw_error():
    """`get_origin`/`get_args`/`__name__`/`__repr__` của một annotation lạ đều
    là code của người khác. Đọc chúng để phân loại — hoặc chỉ để dựng thông báo
    lỗi — mà lại nổ thì chính đường xử lý lỗi trở thành đường rò.

    Gọi thẳng `_build_spec()` vì đây là biên của FRAMEWORK: với một annotation
    thù địch tới mức `__repr__` cũng nổ, `@dataclass` của CPython đã hỏng từ
    trước (`inspect.signature` gọi `repr`), tức là ngoài phạm vi R1-A1."""
    class Hostile:
        @property
        def __origin__(self):
            raise RuntimeError("__origin__ nổ")

        def __repr__(self):
            raise RuntimeError("__repr__ nổ")

    with pytest.raises(CanonicalContractViolation):
        _build_spec(Hostile(), "`value`")


def test_a_hostile_get_args_cannot_leak_a_raw_error():
    class HostileArgs:
        __origin__ = tuple

        @property
        def __args__(self):
            raise RuntimeError("__args__ nổ")

    with pytest.raises(CanonicalContractViolation):
        _build_spec(HostileArgs(), "`value`")


def test_an_annotation_whose_name_raises_still_produces_a_readable_error():
    class NameRaisesMeta(type):
        @property
        def __name__(cls):
            raise RuntimeError("__name__ nổ")

    Hostile = NameRaisesMeta("H", (), {})
    with pytest.raises(CanonicalContractViolation) as exc:
        build(Hostile)
    assert str(exc.value)


# ══════════════════════════ META-INVARIANT (§9)

def _walk(spec):
    yield spec
    for child in spec.children():
        yield from _walk(child)


def _type_position_args(hint):
    """TÍNH LẠI ĐỘC LẬP số tham số ở vị trí kiểu của một annotation.

    Không gọi hàm nào của parser — nếu không thì phép kiểm sẽ vòng tròn."""
    origin = typing.get_origin(hint)
    if origin is None:
        return []
    if origin is Literal:
        return []          # tham số của Literal là GIÁ TRỊ, không phải kiểu
    args = list(typing.get_args(hint))
    if origin is tuple and len(args) == 2 and args[1] is Ellipsis:
        return args[:1]    # `tuple[X, ...]`: Ellipsis là cú pháp
    return args


@pytest.mark.parametrize("cls", [c for c in canonical_types()
                                 if c.__module__.startswith("app.")],
                         ids=lambda c: c.__name__)
def test_meta_every_node_of_every_production_spec_tree_is_classified(cls):
    """Bất biến ở TẦNG TRỪU TƯỢNG, không phải một inventory typing thủ công:

        mọi nút trong cây annotation đã parse đều là một `_Spec`,
        và số nút con bằng số tham số ở vị trí kiểu của `source`.

    Vế thứ hai được tính lại từ `typing.get_args()` một cách độc lập, nên nó
    bắt được đúng lớp lỗi "thêm một generic mới → hậu duệ tự biến mất"."""
    for _, check in cls.__canonical_contract__:
        spec = check.__canonical_spec__
        for node in _walk(spec):
            assert isinstance(node, _Spec), f"{cls.__name__}: nút {node!r} không phải _Spec"
            assert hasattr(node, "source"), f"{cls.__name__}: nút {node!r} thiếu `source`"
            expected = _type_position_args(node.source)
            assert len(node.children()) == len(expected), (
                f"{cls.__name__}: {node.source!r} có {len(expected)} tham số kiểu "
                f"nhưng cây parse chỉ giữ {len(node.children())} nút con"
            )


@pytest.mark.parametrize("depth", [1, 2, 3, 4])
def test_meta_an_unsupported_descendant_is_caught_at_any_depth(depth):
    """Bằng chứng cho "annotation thêm sau này": bất biến không phụ thuộc việc
    liệt kê đủ construct hôm nay, mà phụ thuộc nhánh `raise` cuối của parser."""
    annotation = T_CONSTRAINED
    for _ in range(depth):
        annotation = tuple[annotation]
    with pytest.raises(CanonicalContractViolation, match="TypeVar"):
        build(annotation)


def test_meta_only_contract_violations_escape_decoration():
    """Không construct thù địch nào được làm framework nổ bằng lỗi NGOÀI từ
    vựng của nó. Đây là phát biểu tổng quát của P2."""
    hostile = [a for _, a in _UNSUPPORTED_DESCENDANTS] + [
        TD, TDPartial, ProtoPlain, typing.Protocol, EvilInstanceCheck,
        typing.IO, typing.IO[str], typing.TextIO, typing.BinaryIO, typing.Generic,
        typing.Callable, typing.Final[int], typing.NoReturn, typing.Self,
        typing.Optional, T_CONSTRAINED, T_BOUND, Literal[1.5], 42, "KhongTonTai",
    ]
    for annotation in hostile:
        try:
            build(annotation)
        except CanonicalContractViolation:
            continue
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"{annotation!r} nổ bằng {type(exc).__name__} thô: {exc}")
        else:
            pytest.fail(f"{annotation!r} decorate lọt — UNKNOWN đã thành ANY")


# ══════════════════════════ ATOMICITY (§6)

def test_a_failed_decoration_leaves_registry_and_class_untouched():
    """Decoration thất bại không được để lại một canonical type nửa vời."""
    before_registry = len(canonical_types())

    @dataclass(frozen=True)
    class Half:
        value: tuple[T_CONSTRAINED]

        def __post_init__(self) -> None:
            pass

    before_attrs = set(vars(Half))
    with pytest.raises(CanonicalContractViolation):
        canonical()(Half)

    assert len(canonical_types()) == before_registry
    assert set(vars(Half)) == before_attrs
    assert not hasattr(Half, "__canonical_contract__")
    assert not getattr(Half, "__canonical__", False)


# ═══════════ ORACLE PHẢI CHỨNG MINH ĐƯỢC CHÍNH NÓ CÓ THỂ FAIL (§9)
#
# Một bộ test luôn xanh không nói lên điều gì. Ba test dưới đây TẮT từng lớp
# bảo vệ của framework rồi khẳng định lỗ hổng tương ứng QUAY LẠI — nếu ai đó gỡ
# lớp bảo vệ đó, test tương ứng ở trên sẽ đỏ.

def test_oracle_proof_removing_the_metaclass_rule_reopens_the_hole(monkeypatch):
    class CondMeta(type):
        def __instancecheck__(cls, obj):
            if obj is None or type(obj) is object:
                return False
            raise RuntimeError("nổ với giá trị thật")

    class Conditional(metaclass=CondMeta):
        pass

    monkeypatch.setattr(canonical_module, "_classify_class_target",
                        lambda target, where: None)
    cls = build(Conditional)                     # nay decorate LỌT
    with pytest.raises(RuntimeError):            # và lỗi thô quay lại
        cls(value="giá trị thật")


def test_oracle_proof_removing_the_inhabited_rule_reopens_the_hole(monkeypatch):
    monkeypatch.setattr(canonical_module._ClassSpec, "is_inhabited",
                        lambda self: True)
    cls = build(list[int])                       # nay decorate LỌT
    with pytest.raises(CanonicalFieldError):     # nhưng witness vẫn bị loại
        cls(value=[1])                           # -> đúng "hợp đồng rỗng"


def test_oracle_proof_removing_the_depth_budget_loses_determinism(monkeypatch):
    """Ngân sách độ sâu là thứ mang lại TÍNH TẤT ĐỊNH, không phải thứ duy nhất
    chặn lỗi.

    Còn ngân sách -> lỗi nói "lồng sâu quá <N> tầng": một hằng số của framework,
    cùng annotation luôn cho cùng kết quả.
    Bỏ ngân sách -> parser đệ quy tới khi hết stack; biên lỗi vẫn biến nó thành
    `CanonicalContractViolation` (phòng thủ lớp hai), nhưng ngưỡng nay phụ
    thuộc stack CÒN LẠI — cùng một annotation có thể lúc parse được lúc không.
    """
    deep = _nest(4000)

    with pytest.raises(CanonicalContractViolation) as bounded:
        _build_spec(deep, "`value`")
    assert "lồng sâu quá" in str(bounded.value)

    monkeypatch.setattr(canonical_module, "_MAX_ANNOTATION_DEPTH", 10 ** 6)
    monkeypatch.setattr(canonical_module, "_MAX_ANNOTATION_NODES", 10 ** 6)
    with pytest.raises(CanonicalContractViolation) as unbounded:
        _build_spec(deep, "`value`")
    assert "lồng sâu quá" not in str(unbounded.value)
    assert "recursion" in str(unbounded.value).lower()


# ═══════════════ META — MỌI CASE SUPPORTED PHẢI CÓ WITNESS (§10)

_SUPPORTED_WITNESSES = [
    (int, 0), (str, "x"), (bool, True), (date, date(2026, 1, 1)),
    (Optional[str], None), (Optional[int], 3), (tuple, ()), (frozenset, frozenset()),
    (bytes, b"x"), (tuple[int, ...], (1,)), (tuple[()], ()), (tuple[int], (1,)),
    (frozenset[int], frozenset({1})), (FrozenMapping, FrozenMapping({"a": 1})),
    (Any, 1), (None, None), (type, int), (Literal["a"], "a"),
    (Union[int, str], 1), (Optional[Literal["a", "b"]], "b"),
    (Marker, Marker()), (NTuple, NTuple(a=1)), (Box, Box()), (Box[int], Box()),
    (REPattern, _re.compile("x")), (tuple[list[int], ...], ()),
    (typing.Annotated[int, "meta"], 1), (typing.Required[int], 1),
]


@pytest.mark.parametrize("annotation, witness", _SUPPORTED_WITNESSES,
                         ids=[str(a)[:38] for a, _ in _SUPPORTED_WITNESSES])
def test_meta_every_supported_annotation_has_an_accepted_witness(annotation, witness):
    """Kỷ luật oracle: không được tuyên bố SUPPORTED bằng một danh sách giá trị
    hợp lệ RỖNG. Mỗi dòng ở đây phải dựng được một object thật."""
    assert accepts(annotation, witness), (
        f"{annotation!r} được coi là SUPPORTED nhưng witness {witness!r} bị loại "
        "— đó là một hợp đồng rỗng, không phải hỗ trợ"
    )


def test_meta_the_witness_table_covers_every_supported_shape_of_the_grammar():
    """Bảng witness phải phủ mọi hình thái ngữ pháp, không chỉ vài dòng dễ.

    Đi qua ĐƯỜNG DECORATION THẬT (`build`), không gọi `_build_spec` trực tiếp:
    `typing.get_type_hints()` bóc `Annotated`/`Required` trước khi framework
    nhìn thấy, nên hai đường cho hai kết quả khác nhau và chỉ đường thật mới
    phản ánh production."""
    kinds = set()
    for annotation, _ in _SUPPORTED_WITNESSES:
        cls = build(annotation)
        (_, check), = cls.__canonical_contract__
        kinds.add(type(check.__canonical_spec__).__name__)
    assert kinds >= {"_AnySpec", "_NoneSpec", "_ClassSpec", "_LiteralSpec", "_UnionSpec"}
