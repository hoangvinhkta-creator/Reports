"""R1-A1 — ANNOTATION CONTRACT. Ma trận falsification cho `_field_checker()`.

    PYTHONPATH=<repo-root> python tools/analysis/r1a1_annotation_probes.py

Artefact bằng chứng của sub-repair **R1-A1**, mở sau Independent Review R1-A
Finding #1 tại `dead82e`. Chạy được trên cả commit TRƯỚC lẫn SAU R1-A1 nên hai
lần chạy so trực tiếp được với nhau.

Câu hỏi: với MỖI dạng annotation mà `@canonical` có thể gặp, framework làm gì?

    SUPPORTED   nhận mọi giá trị hợp lệ, từ chối mọi giá trị không hợp lệ
    BYPASSED    nhận cả giá trị KHÔNG hợp lệ  -> lỗ hổng
    REJECTED    từ chối cả giá trị HỢP LỆ     -> hỏng theo chiều ngược lại
    UNSUPPORTED nổ ngay lúc decorate           -> an toàn, có tuyên bố
    UNDECLARED  framework KHÔNG mô hình hoá được construct này nhưng vẫn
                decorate lọt -> đây chính là "UNKNOWN âm thầm thành ANY"
    BROKEN      vừa loại giá trị hợp lệ vừa nhận giá trị không hợp lệ
    NO_WITNESS  dòng probe tuyên bố SUPPORTED nhưng không đưa ra nổi một giá
                trị hợp lệ nào -> lỗi của chính oracle (§10)
    RAW_ERROR   decorate lọt rồi để lỗi NGOÀI từ vựng framework rò ra lúc chạy
                (`TypeError` thô từ `isinstance`, `RuntimeError` từ
                `__instancecheck__` tuỳ biến…)

Bất biến mà R1-A1 phải đạt: **UNKNOWN không bao giờ được thành ANY.** Mọi
annotation hoặc SUPPORTED (validate đủ ngữ nghĩa) hoặc UNSUPPORTED (nổ lúc
import). Không có ô nào rơi vào "framework không hiểu nên thôi bỏ qua".
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any, Literal, Mapping, Optional, Sequence, TypeVar, Union

from app.modules.domain.canonical import (
    CanonicalContractViolation,
    CanonicalFieldError,
    FrozenMapping,
    canonical,
)

# Từ vựng lỗi HỢP LỆ của framework. Bất cứ ngoại lệ nào khác thoát ra lúc dựng
# object đều là lỗi rò — xem outcome `RAW_ERROR`.
_FRAMEWORK_ERRORS = (CanonicalContractViolation, CanonicalFieldError)

# ── giá trị mẫu dùng chung
SENTINEL = object()
T_CONSTRAINED = TypeVar("T_CONSTRAINED", int, str)
T_BOUND = TypeVar("T_BOUND", bound=int)


class Marker:
    """Class thường, dùng làm 'canonical class reference' giả lập."""


# ── vật liệu cho nhóm G (hậu duệ generic) và nhóm R (class-like runtime)
import abc as _abc  # noqa: E402
import functools as _functools  # noqa: E402
import enum as _enum  # noqa: E402
import re as _re  # noqa: E402

TS = typing.TypeVarTuple("TS")
PS = typing.ParamSpec("PS")


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


class _FlagShade(_enum.Flag):
    A = 1


MARKER = Marker()

RESULTS = []


def declare(annotation):
    """Khai một canonical type một-field mang `annotation`. Trả class hoặc lỗi."""
    ns = {"__annotations__": {"value": annotation},
          "__post_init__": lambda self: None,
          "__module__": __name__}
    cls = type("Probe", (), ns)
    cls = dataclass(frozen=True)(cls)
    return canonical()(cls)


def matrix(annotation, valid, invalid, expect):
    try:
        cls = declare(annotation)
    except CanonicalContractViolation as exc:
        # Từ chối CÓ TUYÊN BỐ: đây là kết quả hợp lệ.
        if expect == "UNSUPPORTED":
            return "UNSUPPORTED", f"{type(exc).__name__}: {str(exc)[:84]}"
        return "UNSUPPORTED", f"loại lúc decorate dù chờ hỗ trợ — {str(exc)[:66]}"
    except Exception as exc:  # noqa: BLE001
        # Nổ lúc decorate bằng một lỗi NGOÀI từ vựng framework — không phải một
        # tuyên bố, mà là framework tự vỡ. Đây chính là P2.
        return "RAW_ERROR", (f"nổ lúc decorate bằng {type(exc).__name__} thô "
                             f"(không phải CanonicalContractViolation): "
                             f"{str(exc)[:60]}")

    leaked = []

    if expect == "SUPPORTED" and not valid:
        # §10 — kỷ luật oracle. Tuyên bố SUPPORTED mà không đưa ra nổi một giá
        # trị hợp lệ nào thì chính dòng probe đó vô nghĩa: nó không phân biệt
        # được "hỗ trợ" với "hợp đồng rỗng".
        return "NO_WITNESS", "case SUPPORTED nhưng không có witness nào"

    def accepts(v):
        try:
            cls(value=v)
            return True
        except _FRAMEWORK_ERRORS:
            return False
        except Exception as exc:  # noqa: BLE001
            # Lỗi NGOÀI từ vựng của framework: `TypeError` thô từ
            # `isinstance()`, `RuntimeError` từ `__instancecheck__` tuỳ biến…
            leaked.append(type(exc).__name__)
            return False

    # So theo VỊ TRÍ, không theo `repr`: một lớp con của `str` có cùng `repr`
    # với chuỗi thường, nên so bằng `repr` sẽ báo nhầm nó là "đã được nhận".
    valid_ok = [accepts(v) for v in valid]
    invalid_ok = [accepts(v) for v in invalid]

    if leaked:
        # Nặng hơn UNDECLARED: framework nhận type rồi để lỗi của trình thông
        # dịch rò ra ngoài lúc chạy, thay vì một lỗi domain.
        return "RAW_ERROR", (f"decorate lọt rồi rò lỗi ngoài từ vựng framework: "
                             f"{', '.join(sorted(set(leaked)))}")

    if expect == "UNSUPPORTED":
        # Với construct framework KHÔNG mô hình hoá được, việc decorate THÀNH
        # CÔNG đã là lỗi — bất kể sau đó nó nhận hay loại giá trị nào. Đó chính
        # là "UNKNOWN âm thầm thành ANY".
        total = len(valid) + len(invalid)
        taken = sum(valid_ok) + sum(invalid_ok)
        return "UNDECLARED", f"decorate lọt; nhận {taken}/{total} giá trị thử"

    wrongly_rejected = [f"{v!r} ({type(v).__name__})"
                        for v, ok in zip(valid, valid_ok) if not ok]
    wrongly_accepted = [f"{v!r} ({type(v).__name__})"
                        for v, ok in zip(invalid, invalid_ok) if ok]
    if wrongly_rejected and wrongly_accepted:
        return "BROKEN", f"loại hợp lệ {wrongly_rejected} VÀ nhận {wrongly_accepted}"
    if wrongly_accepted:
        return "BYPASSED", f"nhận giá trị KHÔNG hợp lệ: {', '.join(wrongly_accepted)}"
    if wrongly_rejected:
        return "REJECTED", f"loại giá trị HỢP LỆ: {', '.join(wrongly_rejected)}"
    return "SUPPORTED", f"{len(valid)} hợp lệ nhận, {len(invalid)} không hợp lệ loại"


def probe(pid, label, annotation, valid, invalid, expect="SUPPORTED"):
    outcome, detail = matrix(annotation, valid, invalid, expect)
    RESULTS.append((pid, outcome, label, detail))
    print(f"PROBE {pid:<5} | {outcome:<11} | {label}\n{'':>8}   -> {detail}")


# ═══════════════════════════════ nhóm 1 — dạng production ĐANG dùng thật

probe("P1", "builtin scalar `int`", int,
      valid=[0, 7, -3], invalid=[True, "1", 1.0, [], None])
probe("P2", "builtin scalar `str`", str,
      valid=["", "x"], invalid=[1, [], None, type("S", (str,), {})("x")])
probe("P3", "builtin scalar `bool`", bool,
      valid=[True, False], invalid=[1, 0, "yes", None])
probe("P4", "`datetime.date`", date,
      valid=[date(2026, 1, 1)], invalid=["2026-01-01", 1, None])
probe("P5", "`Optional[str]`", Optional[str],
      valid=["x", None], invalid=[1, [], 1.5])
probe("P6", "`Optional[int]`", Optional[int],
      valid=[3, None], invalid=[True, "3", 1.5])
probe("P7", "`Optional[date]`", Optional[date],
      valid=[date(2026, 1, 1), None], invalid=["x", 1])
probe("P8", "`tuple` (bare)", tuple,
      valid=[(), (1, "a")], invalid=[[], "abc", 5, None])
probe("P9", "`frozenset`", frozenset,
      valid=[frozenset(), frozenset({1})], invalid=[set(), [], 5, None])
probe("P10", "class reference (`FrozenMapping`)", FrozenMapping,
      valid=[FrozenMapping({"a": 1})], invalid=[{}, MappingProxyType({}), 5, None])
probe("P11", "`Any`", Any,
      valid=[1, "x", None, SENTINEL, ()], invalid=[[], {}, set()])

# ═══════════════════════════ nhóm 2 — Finding #1 của Independent Review

probe("F1", "`Union[int, str]`", Union[int, str],
      valid=[1, "a"], invalid=[1.5, SENTINEL, None, [], b"x"])
probe("F2", "`Optional[Union[int, str]]`", Optional[Union[int, str]],
      valid=[1, "a", None], invalid=[1.5, SENTINEL, []])
probe("F3", "`str | None` (PEP 604)", eval("str | None"),
      valid=["x", None], invalid=[1, [], 1.5])
probe("F4", "`int | str` (PEP 604)", eval("int | str"),
      valid=[1, "a"], invalid=[1.5, SENTINEL, None])
probe("F5", "`Literal['a', 'b']`", Literal["a", "b"],
      valid=["a", "b"], invalid=["c", 1, None, SENTINEL])
probe("F6", "constrained `TypeVar(int, str)`", T_CONSTRAINED,
      valid=[1, "a"], invalid=[1.5, SENTINEL, None], expect="UNSUPPORTED")
probe("F7", "bound `TypeVar(bound=int)`", T_BOUND,
      valid=[1], invalid=["a", 1.5, SENTINEL, None], expect="UNSUPPORTED")

# ═════════════════════════════ nhóm 3 — construct khác framework có thể gặp

probe("X1", "`tuple[int, ...]`", typing.Tuple[int, ...],
      valid=[(), (1, 2)], invalid=[[], 5, None])
probe("X2", "`Mapping[str, int]` — origin metaclass ABCMeta", Mapping[str, int],
      valid=[FrozenMapping({"a": 1})], invalid=[5, None, "x"],
      expect="UNSUPPORTED")
probe("X3", "`Sequence[int]` — origin metaclass ABCMeta", Sequence[int],
      valid=[(1, 2)], invalid=[5, None], expect="UNSUPPORTED")
probe("X4", "`list[int]` — hợp đồng RỖNG", typing.List[int],
      valid=[[1]], invalid=[5, None], expect="UNSUPPORTED")
probe("X5", "`dict[str, int]` — hợp đồng RỖNG", typing.Dict[str, int],
      valid=[{"a": 1}], invalid=[5, None], expect="UNSUPPORTED")
probe("X6", "`Final[int]`", typing.Final[int],
      valid=[1], invalid=["a", 1.5, None], expect="UNSUPPORTED")
probe("X7", "`Annotated[int, 'meta']`", typing.Annotated[int, "meta"],
      valid=[1], invalid=["a", True, None])
probe("X8", "`Callable[[], None]`", typing.Callable[[], None],
      valid=[lambda: None], invalid=[5, None, "x"])
probe("X9", "`None` (chỉ None hợp lệ)", None,
      valid=[None], invalid=[1, "x", SENTINEL])
probe("X10", "forward reference GIẢI ĐƯỢC (`'Marker'`)", "Marker",
      valid=[MARKER], invalid=[5, None, "Marker"])
probe("X11", "forward reference KHÔNG giải được", "KhongTonTaiODau",
      valid=[], invalid=[1, "x", SENTINEL], expect="UNSUPPORTED")
probe("X12", "`type` (class object)", type,
      valid=[int, Marker], invalid=[5, None])
probe("X13", "`Union[int, None]` (= Optional[int])", Union[int, None],
      valid=[1, None], invalid=["1", 1.5, True])
probe("X14", "`Union[str, bytes, None]` ba nhánh + None", Union[str, bytes, None],
      valid=["x", b"x", None], invalid=[1, 1.5, SENTINEL])
probe("X15", "`Union[Marker, int]` class + scalar", Union[Marker, int],
      valid=[MARKER, 1], invalid=["x", 1.5, None])


# ═══════════════ WAVE 2 — tấn công vào THIẾT KẾ, không phải implementation
#
# Năm case của Finding #1 đã đóng. Nhóm này hỏi câu khác: ngữ pháp đóng có
# THỰC SỰ đóng không, hay chỉ đóng ở tầng ngoài cùng? Trọng tâm là ĐỆ QUY —
# một construct không hỗ trợ nằm SÂU bên trong một construct được hỗ trợ.

probe("W1", "`Union[int, <TypeVar>]` — không hỗ trợ NẰM TRONG được hỗ trợ",
      Union[int, T_CONSTRAINED], valid=[1], invalid=[1.5, SENTINEL, None],
      expect="UNSUPPORTED")
probe("W2", "`Optional[Literal['a','b']]`", Optional[Literal["a", "b"]],
      valid=["a", "b", None], invalid=["c", 1, SENTINEL])
probe("W3", "`Union[Literal[1], Literal['a']]`", Union[Literal[1], Literal["a"]],
      valid=[1, "a"], invalid=[2, "b", True, None])
probe("W4", "`Literal[1]` không được nhận `True` (True == 1)", Literal[1],
      valid=[1], invalid=[True, "1", 1.0, None])
probe("W4b", "`Literal[True]` không được nhận `1`", Literal[True],
      valid=[True], invalid=[1, "True", None])
probe("W5", "`Literal[1.5]` — giá trị literal ngoài kiểu cho phép", Literal[1.5],
      valid=[1.5], invalid=[2.5, "1.5", None], expect="UNSUPPORTED")
probe("W6", "`int | str | None` (PEP 604 ba nhánh)", eval("int | str | None"),
      valid=[1, "a", None], invalid=[1.5, True, SENTINEL])
probe("W7", "`Annotated[Union[int, str], 'meta']`",
      typing.Annotated[Union[int, str], "meta"],
      valid=[1, "a"], invalid=[1.5, None])
probe("W8", "`Annotated[<TypeVar>, 'meta']` — bóc Annotated ra vẫn phải loại",
      typing.Annotated[T_CONSTRAINED, "meta"], valid=[1],
      invalid=[1.5, SENTINEL, None], expect="UNSUPPORTED")
probe("W9", "`typing.NoReturn`", typing.NoReturn, valid=[],
      invalid=[1, "x", SENTINEL, None], expect="UNSUPPORTED")
probe("W10", "`typing.Optional` (chưa subscript)", typing.Optional,
      valid=[], invalid=[1, None, SENTINEL], expect="UNSUPPORTED")
probe("W11", "`typing.Self`", typing.Self, valid=[],
      invalid=[1, "x", SENTINEL], expect="UNSUPPORTED")
probe("W12", "`Optional[str]` vẫn loại lớp con của `str` (nghiêm ngặt xuyên union)",
      Optional[str], valid=["x", None],
      invalid=[type("Sub", (str,), {})("x")])
probe("W13", "`Union[Any, None]` — Any khớp mọi thứ NHƯNG mutable vẫn bị loại",
      Optional[Any], valid=[1, None, (), SENTINEL], invalid=[[], {}, set()])
probe("W14", "`Union[list, int]` — nhánh `list` không bao giờ khớp",
      Union[list, int], valid=[1], invalid=[[], [1]], expect="UNSUPPORTED")


# ══════════ NHÓM G — P1: hậu duệ generic bị parser bỏ rơi (Review R1-A1 #2)
#
# `_build_spec()` tại `44018e3` quy mọi generic có tham số về `_ClassSpec(origin)`
# và VỨT BỎ `get_args()`. Nên `tuple[<TypeVar>]` decorate lọt: hậu duệ không
# được hỗ trợ biến mất, đúng lớp lỗi mà R1-A1 vòng một tuyên bố đã đóng — chỉ
# là nó lùi xuống một tầng.
#
# LƯU Ý PHẠM VI: R1-A1 chỉ đòi parser HIỂU và PHÂN LOẠI mọi node trong cây
# annotation. Việc có kiểm từng phần tử lúc chạy hay không là **R1-D**, cố ý
# không đụng ở đây.

probe("G1", "`tuple[<TypeVar>]`", tuple[T_CONSTRAINED],
      valid=[(1,)], invalid=[(1.5,), SENTINEL], expect="UNSUPPORTED")
probe("G2", "`tuple[Final[int]]`", tuple[typing.Final[int]],
      valid=[(1,)], invalid=[("a",), SENTINEL], expect="UNSUPPORTED")
probe("G3", "`tuple[Literal[1.5]]`", tuple[Literal[1.5]],
      valid=[(1.5,)], invalid=[(2.5,), SENTINEL], expect="UNSUPPORTED")
probe("G4", "`tuple[NoReturn]`", tuple[typing.NoReturn],
      valid=[()], invalid=[(1,), SENTINEL], expect="UNSUPPORTED")
probe("G5", "`Callable[[<TypeVar>], int]`", typing.Callable[[T_CONSTRAINED], int],
      valid=[lambda x: 1], invalid=[5, None], expect="UNSUPPORTED")
probe("G6", "`list[<TypeVar>]`", list[T_CONSTRAINED],
      valid=[], invalid=[[1], [1.5], 5], expect="UNSUPPORTED")
probe("G7", "`dict[str, <TypeVar>]`", dict[str, T_CONSTRAINED],
      valid=[], invalid=[{"a": 1}, {"a": 1.5}, 5], expect="UNSUPPORTED")
probe("G8", "`tuple[Union[int, <TypeVar>], ...]`",
      tuple[Union[int, T_CONSTRAINED], ...],
      valid=[(1,)], invalid=[(1.5,), SENTINEL], expect="UNSUPPORTED")
probe("G9", "`tuple[Annotated[<TypeVar>, 'x']]`",
      tuple[typing.Annotated[T_CONSTRAINED, "x"]],
      valid=[(1,)], invalid=[(1.5,), SENTINEL], expect="UNSUPPORTED")
probe("G10", "`Optional[tuple[<TypeVar>]]`", Optional[tuple[T_CONSTRAINED]],
      valid=[(1,), None], invalid=[(1.5,), SENTINEL], expect="UNSUPPORTED")
probe("G11", "`Union[int, tuple[<TypeVar>]]`",
      Union[int, tuple[T_CONSTRAINED]],
      valid=[1, (1,)], invalid=[1.5, SENTINEL], expect="UNSUPPORTED")
probe("G12", "`Callable[[int], <TypeVar>]`", typing.Callable[[int], T_CONSTRAINED],
      valid=[lambda x: 1], invalid=[5, None], expect="UNSUPPORTED")
probe("G13", "`Callable[..., <TypeVar>]`", typing.Callable[..., T_CONSTRAINED],
      valid=[lambda: 1], invalid=[5, None], expect="UNSUPPORTED")
probe("G14", "`Callable[..., int]` — Ellipsis ở vị trí tham số",
      typing.Callable[..., int], valid=[lambda: 1], invalid=[5, None],
      expect="UNSUPPORTED")
probe("G15", "`Callable[[int, str], None]` — họ Callable, từ chối toàn bộ",
      typing.Callable[[int, str], None], valid=[lambda a, b: None],
      invalid=[5, None], expect="UNSUPPORTED")
probe("G16", "`dict[str, tuple[Final[int]]]` — hai tầng",
      dict[str, tuple[typing.Final[int]]],
      valid=[], invalid=[{"a": (1,)}, 5], expect="UNSUPPORTED")
probe("G17", "`tuple[tuple[tuple[NoReturn]]]` — ba tầng",
      tuple[tuple[tuple[typing.NoReturn]]],
      valid=[((( ),),)], invalid=[SENTINEL], expect="UNSUPPORTED")
probe("G18", "`frozenset[<TypeVar>]`", frozenset[T_CONSTRAINED],
      valid=[frozenset({1})], invalid=[{1}, 5], expect="UNSUPPORTED")
probe("G19", "`tuple[Callable[[<TypeVar>], int], ...]` — họ bị từ chối lồng trong họ được hỗ trợ",
      tuple[typing.Callable[[T_CONSTRAINED], int], ...],
      valid=[()], invalid=[SENTINEL], expect="UNSUPPORTED")
probe("G20", "`Optional[dict[str, Literal[1.5]]]`",
      Optional[dict[str, Literal[1.5]]],
      valid=[None], invalid=[{"a": 1.5}, 5], expect="UNSUPPORTED")
probe("G21", "`tuple[int, ...]` — biến thể ĐỒNG NHẤT, phải VẪN hỗ trợ",
      tuple[int, ...], valid=[(), (1, 2)], invalid=[[], 5, None])
probe("G22", "`tuple[()]` — tuple rỗng, phải VẪN hỗ trợ",
      tuple[()], valid=[(), (1,)], invalid=[[], 5, None])
probe("G23", "`dict[str, int]` — parse được nhưng hợp đồng RỖNG",
      dict[str, int], valid=[{"a": 1}], invalid=[5, None], expect="UNSUPPORTED")
probe("G24", "`tuple[Unpack[TypeVarTuple]]`", tuple[typing.Unpack[TS]],
      valid=[(1,)], invalid=[SENTINEL], expect="UNSUPPORTED")
probe("G25", "`Callable[ParamSpec, int]`", typing.Callable[PS, int],
      valid=[lambda: 1], invalid=[5], expect="UNSUPPORTED")
probe("G26", "`tuple[[int]]` — tham số là list, KHÔNG hash được",
      tuple[[int]], valid=[], invalid=[(1,), SENTINEL], expect="UNSUPPORTED")
probe("G27", "`dict[str, [int]]` — list lồng ở vị trí value",
      dict[str, [int]], valid=[], invalid=[{"a": 1}, SENTINEL], expect="UNSUPPORTED")
probe("G28", "`tuple[[int], str]` — list ở vị trí đầu, không phải Callable",
      tuple[[int], str], valid=[], invalid=[(1, "a"), SENTINEL], expect="UNSUPPORTED")


# ══════════ NHÓM R — P2: class-like KHÔNG an toàn cho `isinstance` lúc chạy
#
# `isinstance(target, type)` là True cho cả `TypedDict`, `Protocol` không
# `runtime_checkable`, và họ `typing.IO`. Nhưng:
#   * TypedDict / Protocol thường -> `isinstance()` NỔ `TypeError` thô lúc dựng;
#   * `typing.IO` -> `isinstance()` trả False cho MỌI object thật, nên field
#     khai kiểu đó sẽ loại sạch giá trị hợp lệ.
# Cả hai đều là "decorate lọt rồi sai lúc chạy", không phải một tuyên bố.

probe("R1", "`TypedDict`", TD, valid=[{"a": 1}], invalid=[5, None],
      expect="UNSUPPORTED")
probe("R2", "`TypedDict(total=False)`", TDPartial, valid=[{}], invalid=[5],
      expect="UNSUPPORTED")
probe("R3", "`Protocol` KHÔNG runtime_checkable", ProtoPlain,
      valid=[Impl()], invalid=[5, None], expect="UNSUPPORTED")
probe("R4", "`Protocol` runtime_checkable (metaclass _ProtocolMeta)", ProtoRuntime,
      valid=[Impl()], invalid=[5, None], expect="UNSUPPORTED")
probe("R5", "`Protocol` runtime_checkable có data member", ProtoData,
      valid=[Impl()], invalid=[5, None], expect="UNSUPPORTED")
probe("R6", "`typing.IO[str]`", typing.IO[str], valid=[], invalid=[5, None, "x"],
      expect="UNSUPPORTED")
probe("R7", "`typing.IO` (trần)", typing.IO, valid=[], invalid=[5, None],
      expect="UNSUPPORTED")
probe("R8", "`typing.TextIO`", typing.TextIO, valid=[], invalid=[5, None],
      expect="UNSUPPORTED")
probe("R9", "`typing.BinaryIO`", typing.BinaryIO, valid=[], invalid=[5, None],
      expect="UNSUPPORTED")
probe("R10", "`typing.Generic`", typing.Generic, valid=[], invalid=[5, None],
      expect="UNSUPPORTED")
probe("R11", "`typing.Protocol` (trần)", typing.Protocol, valid=[], invalid=[5],
      expect="UNSUPPORTED")
probe("R12", "class có metaclass `__instancecheck__` NỔ", EvilInstanceCheck,
      valid=[], invalid=[5, None], expect="UNSUPPORTED")
probe("R13", "`typing.SupportsInt` (metaclass _ProtocolMeta)",
      typing.SupportsInt, valid=[5], invalid=[SENTINEL], expect="UNSUPPORTED")
probe("R14", "`NamedTuple` class", NTuple, valid=[NTuple(a=1)], invalid=[5, (1,)])
probe("R15", "`Enum` class (metaclass EnumMeta)", Shade, valid=[Shade.RED],
      invalid=[1, "RED"], expect="UNSUPPORTED")
probe("R16", "class generic của người dùng (trần)", Box, valid=[Box()], invalid=[5])
probe("R17", "`Box[int]` — generic người dùng có tham số", Box[int],
      valid=[Box()], invalid=[5])
probe("R18", "`abc.ABC` subclass (metaclass ABCMeta)", PlainABC,
      valid=[], invalid=[5, None], expect="UNSUPPORTED")
probe("R19", "`re.Pattern`", _re.Pattern, valid=[_re.compile("x")], invalid=["x", 5])


# ══════════ NHÓM H — metaclass/class-like thù địch (R1-A1 #3, §11-A)
#
# Phép "chứng minh" bằng vài lời gọi `isinstance()` ở bản `d4a8797` không phải
# chứng minh: một hook đổi hành vi theo GIÁ TRỊ qua được phép thử rồi nổ với dữ
# liệu thật. Nhóm này tấn công đúng giả định đó.

def _meta(name, body):
    return type(name, (type,), body)("Hostile" + name, (), {})


def _boom(msg):
    def raiser(*a, **kw):
        raise RuntimeError(msg)
    return raiser


probe("H1", "metaclass `__instancecheck__` đổi hành vi theo giá trị",
      _meta("Cond", {"__instancecheck__":
                     lambda cls, o: False if (o is None or type(o) is object)
                     else _boom("nổ với giá trị thật")()}),
      valid=[], invalid=["giá trị thật", 1], expect="UNSUPPORTED")
probe("H2", "metaclass `__instancecheck__` nổ vô điều kiện",
      _meta("IC", {"__instancecheck__": _boom("instancecheck nổ")}),
      valid=[], invalid=[1, None], expect="UNSUPPORTED")
probe("H3", "metaclass `__subclasscheck__` nổ",
      _meta("SC", {"__subclasscheck__": _boom("subclasscheck nổ")}),
      valid=[], invalid=[1, None], expect="UNSUPPORTED")
probe("H4", "metaclass `__getattr__` nổ (đọc `__name__` cũng gãy)",
      _meta("GA", {"__getattr__": _boom("getattr nổ")}),
      valid=[], invalid=[1, None], expect="UNSUPPORTED")
probe("H5", "metaclass `__instancecheck__` trả kết quả KHÔNG ổn định",
      _meta("Flip", {"__instancecheck__":
                     lambda cls, o, _c=[0]: (_c.append(1), len(_c) % 2 == 0)[1]}),
      valid=[], invalid=[1, None], expect="UNSUPPORTED")
probe("H6", "metaclass thường (không hook) vẫn bị từ chối — mặc định là REJECT",
      _meta("Plain", {}), valid=[], invalid=[1, None], expect="UNSUPPORTED")


# ══════════ NHÓM K — hash/eq có tác dụng phụ (R1-A1 #3, §11-B)
#
# Bản `d4a8797` tra chính sách bằng `target in frozenset(...)`, tức là gọi
# `__hash__` của metaclass lạ TRƯỚC khi target được coi là an toàn.

probe("K1", "`__hash__` nổ", _meta("HashBoom", {"__hash__": _boom("hash nổ")}),
      valid=[], invalid=[1], expect="UNSUPPORTED")
probe("K2", "`__hash__ = None` (không hash được)",
      _meta("NoHash", {"__hash__": None}), valid=[], invalid=[1],
      expect="UNSUPPORTED")
probe("K3", "`__eq__` nổ", _meta("EqBoom", {"__eq__": _boom("eq nổ")}),
      valid=[], invalid=[1], expect="UNSUPPORTED")
probe("K4", "`__eq__` có tác dụng phụ (đếm số lần bị so sánh)",
      _meta("EqCount", {"__eq__": lambda cls, o, _c=[0]: (_c.append(1), False)[1],
                        "__hash__": lambda cls: 0}),
      valid=[], invalid=[1], expect="UNSUPPORTED")
probe("K5", "`__hash__` trả về thứ không phải int",
      _meta("BadHash", {"__hash__": lambda cls: "không phải int"}),
      valid=[], invalid=[1], expect="UNSUPPORTED")
probe("K6", "`__hash__` trả giá trị KHÁC NHAU mỗi lần",
      _meta("DriftHash", {"__hash__": lambda cls, _c=[0]: (_c.append(1), len(_c))[1]}),
      valid=[], invalid=[1], expect="UNSUPPORTED")


# ══════════ NHÓM M — origin mutable: hợp đồng RỖNG (R1-A1 #3, §11-C)

probe("M1", "`list` trần", list, valid=[[1]], invalid=[5], expect="UNSUPPORTED")
probe("M2", "`set[int]`", set[int], valid=[{1}], invalid=[5], expect="UNSUPPORTED")
probe("M3", "`bytearray` trần", bytearray, valid=[bytearray(b"x")], invalid=[5],
      expect="UNSUPPORTED")
probe("M4", "`Optional[list[int]]` — chỉ `None` sống được, nhánh list chết",
      Optional[list[int]], valid=[None], invalid=[[1]], expect="UNSUPPORTED")
probe("M5", "`Union[list, dict]` — mọi nhánh đều chết",
      Union[list, dict], valid=[], invalid=[[], {}], expect="UNSUPPORTED")
probe("M6", "`Union[str, set]` — một nhánh sống, một nhánh chết",
      Union[str, set], valid=["x"], invalid=[{1}], expect="UNSUPPORTED")
probe("M7", "`tuple[list[int], ...]` — tham số generic KHÔNG bị luật này (R1-D)",
      tuple[list[int], ...], valid=[(), ([1],)], invalid=[5, None])
probe("M8", "`bytes` — bất biến, phải VẪN hỗ trợ", bytes, valid=[b"x"],
      invalid=[bytearray(b"x"), "x", 5])


# ══════════ NHÓM Z — shape hoàn toàn ngoài ma trận cũ (R1-A1 #3, §11-F)

probe("Z1", "`typing.Never`", typing.Never, valid=[], invalid=[1, None],
      expect="UNSUPPORTED")
probe("Z2", "`typing.LiteralString`", typing.LiteralString, valid=[], invalid=["x"],
      expect="UNSUPPORTED")
probe("Z3", "`typing.Concatenate[int, ParamSpec]`",
      typing.Concatenate[int, PS], valid=[], invalid=[1], expect="UNSUPPORTED")
# `typing.get_type_hints()` BÓC `Required[int]` thành `int` — chuẩn hoá của
# chính CPython, giống `Annotated`. Nên qua đường decoration thật, annotation
# framework nhìn thấy là `int`, hợp lệ. Gọi thẳng `_build_spec(Required[int])`
# thì nó bị từ chối; xem test cùng tên trong suite pytest.
probe("Z4", "`typing.Required[int]` — CPython tự bóc thành `int` lúc resolve",
      typing.Required[int], valid=[1], invalid=["x", None])
probe("Z5", "`typing.TypeAlias`", typing.TypeAlias, valid=[], invalid=[1],
      expect="UNSUPPORTED")
probe("Z6", "một `functools.partial` object làm annotation",
      _functools.partial(int), valid=[], invalid=[1], expect="UNSUPPORTED")
probe("Z7", "một lambda làm annotation", lambda: None, valid=[], invalid=[1],
      expect="UNSUPPORTED")
probe("Z8", "một module object làm annotation", typing, valid=[], invalid=[1],
      expect="UNSUPPORTED")
probe("Z9", "instance của một class thường làm annotation", Marker(),
      valid=[], invalid=[1], expect="UNSUPPORTED")
probe("Z10", "`enum.Flag` class", _FlagShade, valid=[_FlagShade.A], invalid=[1],
      expect="UNSUPPORTED")


def _extra_wave():
    """Hai đường không diễn đạt được bằng bảng: `replace()` và `pickle`.

    Dùng `MappingResult` THẬT của production — nó có sẵn field union
    (`Optional[str]`, `Optional[RecordRef]`). Class động của probe không pickle
    được (không tra ngược được bằng tên), nên đo trên nó sẽ đo nhầm hạn chế của
    chính bộ probe.
    """
    import dataclasses
    import pickle as _pickle

    from app.modules.domain.models import MAPPING_STATUS_UNMAPPED
    from app.modules.mapping.employee_mapper import MappingResult

    ok = MappingResult(normalized=None, status=MAPPING_STATUS_UNMAPPED,
                       default_lead_source=None, include_in_kpi=None)

    try:
        dataclasses.replace(ok, normalized=1.5)
        out = ("BYPASSED", "replace() dựng được giá trị ngoài union")
    except Exception as exc:  # noqa: BLE001
        out = ("SUPPORTED", f"replace() kiểm lại: {type(exc).__name__}")
    RESULTS.append(("W15", out[0], "replace() trên field union", out[1]))
    print(f"PROBE {'W15':<5} | {out[0]:<11} | replace() trên field union\n{'':>8}   -> {out[1]}")

    try:
        back = _pickle.loads(_pickle.dumps(ok))
        same = back == ok
        out = (("SUPPORTED", "round-trip qua constructor, giá trị giữ nguyên") if same
               else ("BYPASSED", f"round-trip đổi object: {back!r}"))
    except Exception as exc:  # noqa: BLE001
        out = ("REJECTED", f"{type(exc).__name__}: {str(exc)[:60]}")
    RESULTS.append(("W16", out[0], "pickle round-trip field union", out[1]))
    print(f"PROBE {'W16':<5} | {out[0]:<11} | pickle round-trip field union\n{'':>8}   -> {out[1]}")


_extra_wave()

# ═══════════ non-regression ngược: production annotation phải VẪN chạy

def _production_still_builds():
    """11 canonical type của production phải decorate được như cũ.

    Lọc theo module `app.` — registry còn chứa cả các class động mà chính bộ
    probe này vừa khai, và đó là chuyện của probe, không phải của production.
    """
    import app.modules.validation.employee_mapping  # noqa: F401
    import app.modules.mapping.employee_mapper  # noqa: F401  (nạp registry)
    from app.modules.domain.canonical import canonical_types

    prod = [c for c in canonical_types() if c.__module__.startswith("app.")]
    missing = [c.__name__ for c in prod if not getattr(c, "__canonical_contract__", None)]
    if missing:
        out = ("REJECTED", f"thiếu hợp đồng: {missing}")
    elif len(prod) != 11:
        out = ("REJECTED", f"đếm được {len(prod)} canonical type production, chờ 11")
    else:
        out = ("SUPPORTED", f"{len(prod)} canonical type production dựng hợp đồng bình thường")
    RESULTS.append(("N1", out[0], "production canonical types vẫn decorate được", out[1]))
    print(f"PROBE {'N1':<5} | {out[0]:<11} | production canonical types vẫn decorate được"
          f"\n{'':>8}   -> {out[1]}")


_production_still_builds()


if __name__ == "__main__":
    print("=" * 78)
    tally = {}
    for _, outcome, _, _ in RESULTS:
        tally[outcome] = tally.get(outcome, 0) + 1
    print(f"TỔNG: {len(RESULTS)} annotation | " +
          " | ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    for label in ("BYPASSED", "REJECTED", "BROKEN", "RAW_ERROR", "NO_WITNESS",
                  "UNDECLARED", "UNSUPPORTED"):
        ids = [r[0] for r in RESULTS if r[1] == label]
        if ids:
            print(f"{label}: {', '.join(ids)}")
    print()
    print("BẤT BIẾN R1-A1: không ô nào được BYPASSED / REJECTED / BROKEN / "
          "RAW_ERROR / NO_WITNESS / UNDECLARED.")
    print("UNSUPPORTED là kết quả CHẤP NHẬN ĐƯỢC — nó là một tuyên bố, không phải lỗ hổng.")
