"""R1-A1 — FROZEN ATTACK CORPUS. Bằng chứng chấp nhận của hợp đồng đóng.

    PYTHONPATH=<repo-root> python tools/analysis/r1a1_annotation_probes.py

Artefact bằng chứng của R1-A1 sau khi Owner **freeze** hợp đồng
(`docs/tasks/TASK-110-R1-A1-FROZEN-CONTRACT.md`).

## Vì sao file này khác hẳn bản trước

Bản trước là một *ma trận thăm dò* 128 ô với bảy outcome (`SUPPORTED`,
`BYPASSED`, `REJECTED`, `UNDECLARED`, `BROKEN`, `NO_WITNESS`, `RAW_ERROR`).
Nó hỏi "framework làm gì với dạng này?" — một câu hỏi mở, trên một không gian
mở. Ba vòng repair cho thấy câu hỏi mở đó không kết thúc được: mỗi vòng đóng
thêm vài ô, mỗi vòng review sau lại dựng được một object Python mới.

File này hỏi một câu hỏi ĐÓNG: **corpus đã freeze có đúng như đã freeze
không?** Mỗi case mang một expected outcome bất biến, và kết quả chỉ có
`PASS`/`FAIL`. Corpus không được bổ sung trong cùng một vòng repair — attack
mới đi vào HARDENING BACKLOG, không đi vào đây.

## Đây cũng là NGUỒN SỰ THẬT DUY NHẤT của corpus

`tests/test_r1a1_annotation_contract.py` import chính `FROZEN_CORPUS` dưới
đây, nên "105/105" trong pytest và "105/105" trong file này là cùng 105 case.
Hai bản sao song song sẽ là một nguồn drift thứ hai — đúng thứ Review R1 đã
chỉ ra ở inventory viết tay.

File này KHÔNG phụ thuộc pytest: nó chạy được độc lập trên bất kỳ commit nào.
"""

from __future__ import annotations

import abc as _abc
import dataclasses
import enum as _enum
import io
import re as _re
import types as _types
import os as _os
import sys
import traceback as _traceback
import typing
from dataclasses import InitVar, dataclass
from datetime import date
from typing import Any, ClassVar, Literal, Optional, Union

import app.modules.domain.canonical as _cm
from app.modules.domain.canonical import (
    CanonicalContractViolation,
    CanonicalFieldError,
    FrozenCounter,
    FrozenMapping,
    canonical,
    canonical_types,
)
import app.modules.mapping.employee_mapper as _em
import app.modules.validation.models as _vm

# Nạp nốt module còn lại để registry đầy đủ dù file này chạy độc lập.
import app.modules.validation.employee_mapping  # noqa: F401

# Từ vựng lỗi HỢP LỆ của framework lúc CHẠY. Bất cứ ngoại lệ nào khác thoát ra
# đều là lỗi rò.
_FRAMEWORK_RUNTIME_ERRORS = (CanonicalContractViolation, CanonicalFieldError, TypeError)

MISSING = object()

# ── §6 GHIM INTERPRETER (HD-POST-A1-02).
#
# Ba case `K03`/`L03`/`M02` được phân loại `OUTSIDE_FRAMEWORK_BOUNDARY`, và
# phân loại đó phụ thuộc hành vi NỘI BỘ của CPython: `dataclasses` /
# `inspect` / `typing` đọc thuộc tính của annotation TRƯỚC khi `@canonical`
# bắt đầu chạy. Phân loại chỉ được carry trên interpreter đã verify.
#
# Số dòng trong `dataclasses.py` là EVIDENCE của interpreter hiện tại, KHÔNG
# phải invariant lâu dài — assertion ở dưới dựa vào biên NGỮ NGHĨA (canonical
# chưa chạy / registry không đổi / class không nhiễm state / traceback không
# có canonical), chứ không dựa vào `filename == dataclasses.py:946`.
VERIFIED_IMPLEMENTATION = "cpython"
VERIFIED_PYTHON_VERSION = "3.11.15 (main, Mar  3 2026, 09:26:23) [GCC 13.3.0]"
VERIFIED_VERSION_INFO = (3, 11, 15, "final", 0)

_CANONICAL_FILE = _os.path.abspath(_cm.__file__)
_CANONICAL_PARTIAL_MARKERS = (
    "__canonical_contract__", "__canonical__", "__canonical_sealed__",
)


def interpreter_matches_verified() -> bool:
    """Phân loại ngoài biên KHÔNG auto-carry sang minor version khác."""
    return (sys.implementation.name == VERIFIED_IMPLEMENTATION
            and sys.version_info[:2] == VERIFIED_VERSION_INFO[:2])


def observe_outside_boundary(annotation: Any, name: str) -> dict:
    """Chứng minh ĐẦY ĐỦ rằng exception xảy ra TRƯỚC biên framework.

    `xfail` chỉ chứng minh test fail; nó không chứng minh fail ĐÚNG VÌ biên.
    Bốn mệnh đề dưới đây mới là bằng chứng, và cả bốn đều phát biểu trên biên
    NGỮ NGHĨA:

      A. `@canonical` chưa hề bắt đầu xử lý class mục tiêu;
      B. registry canonical không đổi;
      C. class mục tiêu không nhận một mẩu state canonical nào;
      D. traceback KHÔNG chứa `canonical.py`, và frame chịu trách nhiệm nằm
         trong stdlib (`dataclasses`/`inspect`/`typing`/interpreter).

    Nếu một ngày CPython đổi và `canonical` bắt đầu xuất hiện trong đường xử
    lý trước exception, `A` và `D` sẽ sai và oracle FAIL — đúng như yêu cầu.
    """
    target = type(name, (), {
        "__annotations__": {"value": annotation},
        "__post_init__": lambda self: None,
        "__module__": __name__,
    })
    entered: list = []

    def spy(**kwargs):
        inner = canonical(**kwargs)

        def decorate(cls):
            entered.append(cls)
            return inner(cls)
        return decorate

    before = len(canonical_types())
    exc = None
    try:
        spy()(dataclass(frozen=True)(target))
    except BaseException as caught:  # noqa: BLE001 — đây chính là thứ đang đo
        exc = caught
    after = len(canonical_types())

    frames = _traceback.extract_tb(exc.__traceback__) if exc is not None else []
    canonical_in_traceback = any(
        _os.path.abspath(f.filename) == _CANONICAL_FILE for f in frames)
    stdlib = [f for f in frames if "/lib/python" in f.filename or
              "\\lib\\python" in f.filename.lower()]
    culprit = stdlib[-1] if stdlib else None

    return {
        "raised": exc is not None,
        "exception_type": type(exc).__name__ if exc is not None else None,
        "A_canonical_never_entered": not entered,
        "B_registry_unchanged": before == after,
        "B_registry": (before, after),
        "C_no_partial_state": not any(
            hasattr(target, m) for m in _CANONICAL_PARTIAL_MARKERS),
        "D_canonical_absent_from_traceback": not canonical_in_traceback,
        "foreign_component": _os.path.basename(culprit.filename) if culprit else None,
        "foreign_call_site": (f"{_os.path.basename(culprit.filename)}:{culprit.lineno}"
                              f" in {culprit.name}") if culprit else None,
        "module_chain": [_os.path.basename(f.filename) for f in frames],
    }


def observe_outside_boundary_at_construction(build_annotation, name: str) -> dict:
    """Biến thể của `observe_outside_boundary` cho case mà chính việc DỰNG
    annotation đã nổ (`T03`).

    Bốn mệnh đề y hệt, nhưng mệnh đề **C** được thoả ở dạng MẠNH HƠN chứ không
    yếu hơn: với `K03`/`L03`/`M02` có một class mục tiêu tồn tại và ta khẳng
    định nó SẠCH; với `T03` **class mục tiêu chưa từng được tạo ra**, nên
    không có chỗ nào để nhiễm state. Hàm này khẳng định đúng điều đó
    (`target_created is None`) chứ không hạ tiêu chuẩn.
    """
    entered: list = []

    def spy(**kwargs):
        inner = canonical(**kwargs)

        def decorate(cls):
            entered.append(cls)
            return inner(cls)
        return decorate

    before = len(canonical_types())
    target = None
    exc = None
    try:
        annotation = build_annotation()          # T03 nổ NGAY Ở ĐÂY
        target = type(name, (), {
            "__annotations__": {"value": annotation},
            "__post_init__": lambda self: None,
            "__module__": __name__,
        })
        spy()(dataclass(frozen=True)(target))
    except BaseException as caught:  # noqa: BLE001 — đây chính là thứ đang đo
        exc = caught
    after = len(canonical_types())

    frames = _traceback.extract_tb(exc.__traceback__) if exc is not None else []
    canonical_in_traceback = any(
        _os.path.abspath(f.filename) == _CANONICAL_FILE for f in frames)
    stdlib = [f for f in frames if "/lib/python" in f.filename]
    culprit = stdlib[-1] if stdlib else None

    return {
        "raised": exc is not None,
        "exception_type": type(exc).__name__ if exc is not None else None,
        "A_canonical_never_entered": not entered,
        "B_registry_unchanged": before == after,
        "B_registry": (before, after),
        # C ở dạng MẠNH: không có class mục tiêu nào được tạo ra.
        "C_no_target_class_created": target is None,
        "C_no_partial_state": target is None or not any(
            hasattr(target, m) for m in _CANONICAL_PARTIAL_MARKERS),
        "D_canonical_absent_from_traceback": not canonical_in_traceback,
        "foreign_component": _os.path.basename(culprit.filename) if culprit else None,
        "foreign_call_site": (f"{_os.path.basename(culprit.filename)}:{culprit.lineno}"
                              f" in {culprit.name}") if culprit else None,
        "module_chain": [_os.path.basename(f.filename) for f in frames],
    }


def _observe_outside_boundary_case(annotation: Any, name: str) -> str:
    ev = observe_outside_boundary(annotation, name)
    if not ev["raised"]:
        return "NO_EXCEPTION"
    for key, token in (
        ("A_canonical_never_entered", "CANONICAL_DID_ENTER"),
        ("B_registry_unchanged", "REGISTRY_MUTATED"),
        ("C_no_partial_state", "CLASS_LEFT_PARTIAL_STATE"),
        ("D_canonical_absent_from_traceback", "CANONICAL_IN_TRACEBACK"),
    ):
        if not ev[key]:
            return token
    if ev["foreign_component"] is None:
        return "NO_FOREIGN_COMPONENT_EVIDENCE"
    return OUTSIDE_FRAMEWORK_BOUNDARY

# ── Expected outcome đã FREEZE. Không thêm giá trị thứ sáu.
UNSUPPORTED_AT_DECORATION = "UNSUPPORTED_AT_DECORATION"
SUPPORTED_VALID = "SUPPORTED_VALID"
SUPPORTED_INVALID_REJECT = "SUPPORTED_INVALID_REJECT"
OUTSIDE_FRAMEWORK_BOUNDARY = "OUTSIDE_FRAMEWORK_BOUNDARY"
INVARIANT = "INVARIANT"

_SUPPORTED_EXPECTATIONS = (SUPPORTED_VALID, SUPPORTED_INVALID_REJECT)

# `SIDE_EFFECTS` ghi lại MỌI lần một hook của object thù địch được gọi. Bất
# biến Z03 đọc danh sách này: "không nổ" chưa phải "không chạy".
SIDE_EFFECTS: list = []


# ═══════════════════════════════════════════════ vật liệu thù địch


class _CondMeta(type):
    """`__instancecheck__` đổi hành vi THEO GIÁ TRỊ — không phép thử hữu hạn
    nào phát hiện được, nên phải bị loại bằng cấu trúc chứ không bằng probe."""

    def __instancecheck__(cls, obj):
        SIDE_EFFECTS.append("instancecheck")
        if obj is None or isinstance(obj, type):
            return False
        raise RuntimeError("__instancecheck__ nổ với dữ liệu thật")


class CondInstanceCheck(metaclass=_CondMeta):
    pass


class _ReprRaiseMeta(type):
    def __repr__(cls):
        SIDE_EFFECTS.append("repr")
        raise RuntimeError("__repr__ nổ")

    def __getattribute__(cls, name):
        if name == "__name__":
            SIDE_EFFECTS.append(name)
            raise RuntimeError("__name__ nổ")
        return type.__getattribute__(cls, name)


class ReprAndNameRaise(metaclass=_ReprRaiseMeta):
    pass


class _HugeReprMeta(type):
    def __repr__(cls):
        SIDE_EFFECTS.append("repr")
        return "X" * 100_000


class HugeRepr(metaclass=_HugeReprMeta):
    pass


class _GetattrRaiseMeta(type):
    def __getattribute__(cls, name):
        SIDE_EFFECTS.append("getattr")
        raise RuntimeError("mọi thuộc tính đều nổ")


class EverythingRaises(metaclass=_GetattrRaiseMeta):
    pass


class _NoHashMeta(type):
    __hash__ = None


class Unhashable(metaclass=_NoHashMeta):
    pass


class _HashRaiseMeta(type):
    def __hash__(cls):
        SIDE_EFFECTS.append("hash")
        raise RuntimeError("__hash__ nổ")


class HashRaises(metaclass=_HashRaiseMeta):
    pass


class _HashDriftMeta(type):
    _n = 0

    def __hash__(cls):
        SIDE_EFFECTS.append("hash")
        _HashDriftMeta._n += 1
        return _HashDriftMeta._n


class HashDrifts(metaclass=_HashDriftMeta):
    pass


class _EqSideMeta(type):
    def __eq__(cls, other):
        SIDE_EFFECTS.append("eq")
        return True

    def __hash__(cls):
        SIDE_EFFECTS.append("hash")
        return 1


class EqHasSideEffect(metaclass=_EqSideMeta):
    pass


class _EqRaiseMeta(type):
    def __eq__(cls, other):
        SIDE_EFFECTS.append("eq")
        raise RuntimeError("__eq__ nổ")

    __hash__ = type.__hash__


class EqRaises(metaclass=_EqRaiseMeta):
    pass


class _EqAlwaysTrueMeta(type):
    def __eq__(cls, other):
        SIDE_EFFECTS.append("eq")
        return True

    __hash__ = type.__hash__


class EqAlwaysTrue(metaclass=_EqAlwaysTrueMeta):
    pass


class _HostileStrError(Exception):
    """Exception mà chính việc RENDER nó là chạy code lạ."""

    def __str__(self):
        SIDE_EFFECTS.append("exception-str")
        raise RuntimeError("__str__ của exception lạ nổ")


class OriginRaises(_types.GenericAlias):
    """`get_origin` PHẢI thật sự nổ ở đây.

    Một object thường mang `__origin__` KHÔNG đủ: `typing.get_origin()` kiểm
    `isinstance(tp, (_BaseGenericAlias, GenericAlias, …))` trước, nên nó trả
    `None` mà không hề chạm `__origin__`. Case này chỉ đo đúng thứ nó tuyên bố
    khi annotation thật sự là một generic alias — khi đó biên B2 mới tới được.
    """

    def __getattribute__(self, name):
        if name == "__origin__":
            raise _HostileStrError("boom")
        return _types.GenericAlias.__getattribute__(self, name)


class ArgsRaises(typing._GenericAlias, _root=True):
    """`get_origin` chạy bình thường rồi `get_args` NỔ — biên B3.

    `_GenericAlias` lưu `__args__` trong `__dict__` nên `__getattr__` không bao
    giờ được gọi; phải dùng `__getattribute__`. Đo được: `get_args()` nổ thật.
    """

    def __getattribute__(self, name):
        if name == "__args__":
            raise _HostileStrError("boom")
        return typing._GenericAlias.__getattribute__(self, name)


class WideArgs:
    """`__args__` rộng 100 000 phần tử."""

    __origin__ = typing.Union
    __args__ = tuple(range(100_000))


class HostileReprInstance:
    def __repr__(self):
        SIDE_EFFECTS.append("repr")
        return "Y" * 100_000


class NameNotAString:
    __name__ = 12345


class ModuleRaises:
    @property
    def __module__(self):
        raise RuntimeError("__module__ nổ")


class ClassAttrRaises:
    """Giá trị runtime có `__class__` NỔ — `isinstance` sẽ để lỗi thô thoát."""

    @property
    def __class__(self):
        SIDE_EFFECTS.append("__class__")
        raise RuntimeError("__class__ nổ")


class _LyingClassAttr:
    _target: Any = tuple

    @property
    def __class__(self):
        SIDE_EFFECTS.append("__class__")
        return type(self)._target


class LiesAboutTuple(_LyingClassAttr):
    _target = tuple


class LiesAboutRecordRef(_LyingClassAttr):
    _target = _em.RecordRef


class MutableSubclass(list):
    """Lớp CON của `list` — phép so định danh bỏ sót, mutable guard phải bắt."""


class PlainUserClass:
    pass


class Shade(_enum.Enum):
    RED = 1


class PlainABC(_abc.ABC):
    pass


class Payload(typing.TypedDict):
    a: int


@typing.runtime_checkable
class RuntimeProto(typing.Protocol):
    def f(self) -> None: ...


_T = typing.TypeVar("_T")
_TC = typing.TypeVar("_TC", int, str)


def _nested_tuple(depth: int) -> Any:
    node: Any = int
    for _ in range(depth):
        node = typing.Tuple[node, ...]
    return node


# ═══════════════════════════════════════════════ máy chạy corpus


def _raw_dataclass(annotation: Any, name: str) -> type:
    """Giai đoạn CPython. `@dataclass` chạy TRƯỚC `@canonical` trong mọi khai
    báo canonical thật, và nó ĐỌC THUỘC TÍNH của annotation
    (`dataclasses._process_class` tra `isinstance(t, str)` và `__module__`).
    Một annotation thù địch có thể vì thế làm CPython nổ trước khi framework
    tồn tại trên call stack — đó là biên NGOÀI framework, không phải một lỗ
    hổng của hợp đồng: không canonical type nào được tạo ra."""
    cls = type(name, (), {
        "__annotations__": {"value": annotation},
        "__post_init__": lambda self: None,
        "__module__": __name__,
    })
    return dataclass(frozen=True)(cls)


def probe_class(annotation: Any, name: str = "Probe") -> type:
    """Khai một canonical type một-field mang `annotation`."""
    return canonical()(_raw_dataclass(annotation, name))


def _observe_annotation(annotation: Any, witness: Any, bad: Any) -> str:
    try:
        raw = _raw_dataclass(annotation, "Probe")
    except BaseException:  # noqa: BLE001 — CPython từ chối TRƯỚC biên framework
        return OUTSIDE_FRAMEWORK_BOUNDARY
    try:
        cls = canonical()(raw)
    except CanonicalContractViolation:
        return UNSUPPORTED_AT_DECORATION
    except BaseException as exc:  # noqa: BLE001 — đây chính là thứ đang đo
        return f"RAW_ERROR_AT_DECORATION({type(exc).__name__})"

    if witness is not MISSING:
        try:
            cls(value=witness)
        except _FRAMEWORK_RUNTIME_ERRORS:
            return "WITNESS_REJECTED"
        except BaseException as exc:  # noqa: BLE001
            return f"RAW_ERROR_AT_RUNTIME({type(exc).__name__})"
    if bad is not MISSING:
        try:
            cls(value=bad)
            return "BAD_VALUE_ACCEPTED"
        except _FRAMEWORK_RUNTIME_ERRORS:
            pass
        except BaseException as exc:  # noqa: BLE001
            return f"RAW_ERROR_AT_RUNTIME({type(exc).__name__})"
    return "SUPPORTED_OK"


def _satisfies(expected: str, observed: str) -> bool:
    if expected in _SUPPORTED_EXPECTATIONS:
        return observed == "SUPPORTED_OK"
    return observed == expected


@dataclasses.dataclass(frozen=True)
class Case:
    """Một case ĐÃ FREEZE. `expected` là bất biến, không phải kỳ vọng tạm."""

    id: str
    group: str
    description: str
    expected: str
    clause: str
    annotation: Any = MISSING
    witness: Any = MISSING
    bad: Any = MISSING
    observe: Any = None          # callable() -> str, cho case tầng decoration

    def run(self) -> str:
        if self.observe is not None:
            return self.observe()
        return _observe_annotation(self.annotation, self.witness, self.bad)

    def passed(self) -> bool:
        return _satisfies(self.expected, self.run())


# ═══════════════════════════════════════════════ case tầng decoration


def _observe_decoration(build) -> str:
    """`build()` phải nổ ĐÚNG `CanonicalContractViolation`, không gì khác."""
    try:
        build()
    except CanonicalContractViolation:
        return UNSUPPORTED_AT_DECORATION
    except BaseException as exc:  # noqa: BLE001
        return f"RAW_ERROR_AT_DECORATION({type(exc).__name__})"
    return "DECORATED"


def _initvar_single():
    @dataclass(frozen=True)
    class R:
        x: int
        seed: InitVar[int]

        def __post_init__(self, seed):
            pass
    return canonical()(R)


def _initvar_many():
    @dataclass(frozen=True)
    class R:
        x: int
        a: InitVar[int]
        b: InitVar[str]

        def __post_init__(self, a, b):
            pass
    return canonical()(R)


def _initvar_only():
    @dataclass(frozen=True)
    class R:
        a: InitVar[int]

        def __post_init__(self, a):
            pass
    return canonical()(R)


def _initvar_kwonly():
    @dataclass(frozen=True, kw_only=True)
    class R:
        x: int
        a: InitVar[int]

        def __post_init__(self, a):
            pass
    return canonical()(R)


def _observe_initvar_names() -> str:
    """R02 — thông báo phải nêu ĐỦ tên, không chỉ tên đầu tiên."""
    try:
        _initvar_many()
    except CanonicalContractViolation as exc:
        text = str(exc)
        if "`a`" in text and "`b`" in text:
            return UNSUPPORTED_AT_DECORATION
        return "UNSUPPORTED_BUT_NAMES_INCOMPLETE"
    except BaseException as exc:  # noqa: BLE001
        return f"RAW_ERROR_AT_DECORATION({type(exc).__name__})"
    return "DECORATED"


def _observe_classvar_alone() -> str:
    @dataclass(frozen=True)
    class S:
        K: ClassVar[int] = 1
        x: int

        def __post_init__(self):
            pass
    try:
        cls = canonical()(S)
        cls(x=1)
    except BaseException as exc:  # noqa: BLE001
        return f"REJECTED({type(exc).__name__})"
    if "K" in dict(cls.__canonical_contract__):
        return "CLASSVAR_LEAKED_INTO_CONTRACT"
    return "SUPPORTED_OK"


def _observe_classvar_with_fields() -> str:
    @dataclass(frozen=True)
    class S2:
        A: ClassVar[str] = "x"
        B: ClassVar[tuple] = ()
        x: int
        y: Optional[str]

        def __post_init__(self):
            pass
    try:
        cls = canonical()(S2)
        cls(x=1, y=None)
    except BaseException as exc:  # noqa: BLE001
        return f"REJECTED({type(exc).__name__})"
    names = {n for n, _ in cls.__canonical_contract__}
    return "SUPPORTED_OK" if names == {"x", "y"} else "CLASSVAR_LEAKED_INTO_CONTRACT"


def _observe_forward_ref() -> str:
    return _observe_decoration(lambda: probe_class("KhongTonTaiODau", "ProbeU1"))


def _observe_self_forward_ref() -> str:
    def build():
        cls = type("ProbeU2", (), {
            "__annotations__": {"value": "ProbeU2"},
            "__post_init__": lambda self: None,
            "__module__": __name__,
        })
        return canonical()(dataclass(frozen=True)(cls))
    return _observe_decoration(build)


class _LateGuardMeta(type):
    """Metaclass cho `setattr` của `@dataclass` đi qua, rồi NỔ với `setattr`
    của `@canonical`. Không có cổng C9, nó để lại một class nửa vời."""

    armed = False

    def __setattr__(cls, key, value):
        if _LateGuardMeta.armed:
            SIDE_EFFECTS.append("setattr")
            raise RuntimeError("__setattr__ nổ giữa decoration")
        type.__setattr__(cls, key, value)


def _observe_hostile_metaclass_atomicity() -> str:
    _LateGuardMeta.armed = False
    cls = _LateGuardMeta("ProbeV1", (), {
        "__annotations__": {"value": int},
        "__post_init__": lambda self: None,
        "__module__": __name__,
    })
    cls = dataclass(frozen=True)(cls)
    before = len(canonical_types())
    _LateGuardMeta.armed = True
    try:
        outcome = _observe_decoration(lambda: canonical()(cls))
    finally:
        _LateGuardMeta.armed = False
    if outcome != UNSUPPORTED_AT_DECORATION:
        return outcome
    if len(canonical_types()) != before:
        return "REGISTRY_MUTATED"
    if hasattr(cls, "__canonical_contract__") or hasattr(cls, "__canonical__"):
        return "CLASS_LEFT_HALF_WRITTEN"
    return UNSUPPORTED_AT_DECORATION


def _observe_registry_unchanged_on_b1_failure() -> str:
    before = len(canonical_types())
    outcome = _observe_decoration(lambda: probe_class("KhongTonTaiODau", "ProbeV2"))
    if outcome != UNSUPPORTED_AT_DECORATION:
        return outcome
    return (UNSUPPORTED_AT_DECORATION if len(canonical_types()) == before
            else "REGISTRY_MUTATED")


def _observe_class_untouched_on_second_field_failure() -> str:
    """Field đầu hợp lệ, field thứ hai ngoài ngữ pháp: class phải NGUYÊN VẸN."""
    cls = type("ProbeV3", (), {
        "__annotations__": {"ok": int, "bad": list},
        "__post_init__": lambda self: None,
        "__module__": __name__,
    })
    cls = dataclass(frozen=True)(cls)
    before = len(canonical_types())
    outcome = _observe_decoration(lambda: canonical()(cls))
    if outcome != UNSUPPORTED_AT_DECORATION:
        return outcome
    if len(canonical_types()) != before:
        return "REGISTRY_MUTATED"
    if hasattr(cls, "__canonical_contract__") or hasattr(cls, "__canonical__"):
        return "CLASS_LEFT_HALF_WRITTEN"
    if getattr(cls.__post_init__, "__canonical_wrapper__", False):
        return "CLASS_LEFT_HALF_WRITTEN"
    return UNSUPPORTED_AT_DECORATION


def _observe_wide_shapes() -> str:
    """T01 — bề rộng, hai hình dạng.

    (a) `__args__` giả rộng 100 000 phần tử: `get_origin` trả `None` nên nó bị
        loại ở C2 (ngoài ngữ pháp) trước khi tới ngân sách.
    (b) `Union` THẬT 600 nhánh: `get_args()` dài 600, chạm ngân sách C12.

    Cả hai phải cho cùng một outcome đã freeze.
    """
    a = _observe_annotation(WideArgs(), MISSING, MISSING)
    if a != UNSUPPORTED_AT_DECORATION:
        return f"fake-args:{a}"
    wide = Union[tuple(Literal[i] for i in range(600))]
    b = _observe_annotation(wide, MISSING, MISSING)
    if b != UNSUPPORTED_AT_DECORATION:
        return f"wide-union:{b}"
    return UNSUPPORTED_AT_DECORATION


def _observe_typing_refuses_first() -> str:
    """T03 — biên NGOÀI framework: `typing` tự nổ khi DỰNG annotation.

    Bản tại `c183123` chỉ kiểm HAI thứ — có `RecursionError` không, và registry
    có đổi không. Nó KHÔNG chứng minh canonical chưa entered, không chứng minh
    không có partial state, không chứng minh `canonical.py` vắng mặt trong
    traceback. Nói cách khác nó PASS đúng KẾT QUẢ nhưng chưa chứng minh CƠ CHẾ,
    và vì thế yếu hơn oracle của `K03`/`L03`/`M02`.

    Bản này dùng ĐÚNG cùng bốn mệnh đề (HD-POST-A1-04).
    """
    ev = observe_outside_boundary_at_construction(
        lambda: _nested_tuple(5000), "BndT03")
    if not ev["raised"]:
        return "TYPING_ACCEPTED_IT"
    if ev["exception_type"] != "RecursionError":
        return f"UNEXPECTED({ev['exception_type']})"
    for key, token in (
        ("A_canonical_never_entered", "CANONICAL_DID_ENTER"),
        ("B_registry_unchanged", "REGISTRY_MUTATED"),
        ("C_no_target_class_created", "TARGET_CLASS_WAS_CREATED"),
        ("C_no_partial_state", "CLASS_LEFT_PARTIAL_STATE"),
        ("D_canonical_absent_from_traceback", "CANONICAL_IN_TRACEBACK"),
    ):
        if not ev[key]:
            return token
    if ev["foreign_component"] is None:
        return "NO_FOREIGN_COMPONENT_EVIDENCE"
    return OUTSIDE_FRAMEWORK_BOUNDARY


def _witness_row_provenance() -> Any:
    """Witness của một type SEALED phải đến từ factory của chính nó — đó là
    toàn bộ ý nghĩa của Lớp 2, và §6 hợp đồng nói rõ witness là ORACLE
    CONTRACT chứ không phải định lý về inhabitation."""
    return _vm.RowProvenance.of()


# ═══════════════════════════════════════════════ CORPUS ĐÃ FREEZE

_C = Case

# Annotation của ba case ngoài biên, dựng MỘT LẦN để corpus và oracle dùng
# đúng cùng một object.
_MODULE_RAISES = ModuleRaises()
_ARGS_RAISES = ArgsRaises(typing.Union, (int, str))
# Bucket "OUTSIDE_FRAMEWORK_BOUNDARY" của số học chính thức. Sau HD-POST-A1-04
# nó gồm BỐN ID: ba ID do HD-POST-A1-02 phân loại lại, cộng `T03` do
# HD-POST-A1-04 ratify. Phân hoạch ngữ nghĩa duy nhất từ đây:
#
#     105 = 101 IN-FRAMEWORK FROZEN IDs + 4 OUTSIDE_FRAMEWORK_BOUNDARY IDs
#
# Không dùng `102 + 3` làm acceptance equation nữa.
OUTSIDE_BOUNDARY_CASE_IDS = ("K03", "L03", "M02", "T03")

# `T03` mang outcome ngoài biên từ bản PLAN (văn xuôi "ngoài biên framework —
# không canonical type nào được tạo"), nhưng oracle của nó tại `c183123` YẾU
# HƠN ba case kia: nó chỉ kiểm `RecursionError` + registry, không chứng minh
# A/C/D. HD-POST-A1-04 vừa ratify nhãn vừa nâng oracle lên cùng chuẩn.
HD_POST_A1_02_RECLASSIFIED_IDS = ("K03", "L03", "M02")
HD_POST_A1_04_RATIFIED_IDS = ("T03",)

FROZEN_CORPUS: tuple = (
    # ── A — Union / Optional / PEP604
    _C("A01", "A", "Union[int, str] (không phải Optional)", UNSUPPORTED_AT_DECORATION, "C2,C6", Union[int, str]),
    _C("A02", "A", "Union[int, str, None] — 3 nhánh", UNSUPPORTED_AT_DECORATION, "C6", Union[int, str, None]),
    _C("A03", "A", "PEP604 int | str", UNSUPPORTED_AT_DECORATION, "C6", int | str),
    _C("A04", "A", "PEP604 str | None", SUPPORTED_VALID, "C6", str | None, "x", 1),
    _C("A05", "A", "Optional[str]", SUPPORTED_VALID, "C6", Optional[str], None, 1),
    _C("A06", "A", "Union[None, str] — None đứng trước", SUPPORTED_VALID, "C6", Union[None, str], "x", 1),
    _C("A07", "A", "Optional[Optional[str]] (typing làm phẳng)", SUPPORTED_VALID, "C6", Optional[Optional[str]], "x", 1),
    _C("A08", "A", "Union[str] (typing thu về str)", SUPPORTED_VALID, "C2", Union[str], "x", 1),
    # ── B — Literal
    _C("B01", "B", "Literal['a','b']", UNSUPPORTED_AT_DECORATION, "C2", Literal["a", "b"]),
    _C("B02", "B", "Literal[1] (bẫy True == 1)", UNSUPPORTED_AT_DECORATION, "C2", Literal[1]),
    _C("B03", "B", "Optional[Literal['a','b']]", UNSUPPORTED_AT_DECORATION, "C6", Optional[Literal["a", "b"]]),
    _C("B04", "B", "Literal[1.5]", UNSUPPORTED_AT_DECORATION, "C2", Literal[1.5]),
    # ── C — special form
    _C("C01", "C", "TypeVar trần", UNSUPPORTED_AT_DECORATION, "C2", _T),
    _C("C02", "C", "TypeVar có ràng buộc", UNSUPPORTED_AT_DECORATION, "C2", _TC),
    _C("C03", "C", "Final[int]", UNSUPPORTED_AT_DECORATION, "C2", typing.Final[int]),
    _C("C04", "C", "NoReturn", UNSUPPORTED_AT_DECORATION, "C2", typing.NoReturn),
    _C("C05", "C", "Never", UNSUPPORTED_AT_DECORATION, "C2", typing.Never),
    _C("C06", "C", "Self", UNSUPPORTED_AT_DECORATION, "C2", typing.Self),
    _C("C07", "C", "LiteralString", UNSUPPORTED_AT_DECORATION, "C2", typing.LiteralString),
    # ── D — hậu duệ trong generic
    _C("D01", "D", "tuple[TypeVar] — hậu duệ không hỗ trợ", UNSUPPORTED_AT_DECORATION, "C2", tuple[_T]),
    _C("D02", "D", "tuple[int, ...]", UNSUPPORTED_AT_DECORATION, "C2", tuple[int, ...]),
    _C("D03", "D", "tuple[list[int], ...]", UNSUPPORTED_AT_DECORATION, "C2,C3", tuple[list[int], ...]),
    _C("D04", "D", "frozenset[int]", UNSUPPORTED_AT_DECORATION, "C2", frozenset[int]),
    _C("D05", "D", "tuple[()]", UNSUPPORTED_AT_DECORATION, "C2", tuple[()]),
    _C("D06", "D", "Optional[tuple[int, ...]]", UNSUPPORTED_AT_DECORATION, "C6", Optional[tuple[int, ...]]),
    # ── E — Callable
    _C("E01", "E", "Callable trần", UNSUPPORTED_AT_DECORATION, "C2,C3", typing.Callable),
    _C("E02", "E", "Callable[[int], str]", UNSUPPORTED_AT_DECORATION, "C2", typing.Callable[[int], str]),
    _C("E03", "E", "Callable[..., str]", UNSUPPORTED_AT_DECORATION, "C2", typing.Callable[..., str]),
    # ── F — TypedDict
    _C("F01", "F", "TypedDict class", UNSUPPORTED_AT_DECORATION, "C3", Payload),
    # ── G — Protocol
    _C("G01", "G", "Protocol runtime_checkable", UNSUPPORTED_AT_DECORATION, "C3", RuntimeProto),
    _C("G02", "G", "typing.Protocol", UNSUPPORTED_AT_DECORATION, "C3", typing.Protocol),
    _C("G03", "G", "typing.SupportsInt", UNSUPPORTED_AT_DECORATION, "C3", typing.SupportsInt),
    # ── H — họ typing.IO
    _C("H01", "H", "typing.IO", UNSUPPORTED_AT_DECORATION, "C3", typing.IO),
    _C("H02", "H", "typing.TextIO", UNSUPPORTED_AT_DECORATION, "C3", typing.TextIO),
    _C("H03", "H", "io.TextIOBase (class thật)", UNSUPPORTED_AT_DECORATION, "C3", io.TextIOBase),
    # ── I — __instancecheck__ có điều kiện
    _C("I01", "I", "metaclass __instancecheck__ đổi theo GIÁ TRỊ", UNSUPPORTED_AT_DECORATION, "C3,C4", CondInstanceCheck),
    _C("I02", "I", "Optional[<I01>]", UNSUPPORTED_AT_DECORATION, "C6", Optional[CondInstanceCheck]),
    # ── J — __class__ thù địch của GIÁ TRỊ runtime
    _C("J01", "J", "giá trị runtime có __class__ NỔ, field tuple", SUPPORTED_INVALID_REJECT, "C4", tuple, (), ClassAttrRaises()),
    _C("J02", "J", "giá trị runtime có __class__ NÓI DỐI là tuple", SUPPORTED_INVALID_REJECT, "C4", tuple, (), LiesAboutTuple()),
    _C("J03", "J", "__class__ nói dối, field Optional[RecordRef]", SUPPORTED_INVALID_REJECT, "C4,C6", Optional[_em.RecordRef], None, LiesAboutRecordRef()),
    # ── K — __repr__ thù địch trên class target
    _C("K01", "K", "metaclass __repr__ NỔ và __name__ NỔ", UNSUPPORTED_AT_DECORATION, "C3,C11", ReprAndNameRaise),
    _C("K02", "K", "metaclass __repr__ trả 100 000 ký tự", UNSUPPORTED_AT_DECORATION, "C11", HugeRepr),
    _C("K03", "K", "metaclass __getattr__ NỔ trên mọi thuộc tính", OUTSIDE_FRAMEWORK_BOUNDARY, "C10", EverythingRaises,
       observe=lambda: _observe_outside_boundary_case(EverythingRaises, "BndK03")),
    # ── L — tên/repr của annotation thù địch
    _C("L01", "L", "instance làm annotation, __repr__ có side effect", UNSUPPORTED_AT_DECORATION, "C2,C11", HostileReprInstance()),
    _C("L02", "L", "annotation có __name__ KHÔNG phải str", UNSUPPORTED_AT_DECORATION, "C11", NameNotAString()),
    _C("L03", "L", "annotation có __module__ NỔ", OUTSIDE_FRAMEWORK_BOUNDARY, "C10", _MODULE_RAISES,
       observe=lambda: _observe_outside_boundary_case(_MODULE_RAISES, "BndL03")),
    # ── M — exception lạ có __str__ thù địch
    _C("M01", "M", "get_origin NỔ với exception có __str__ thù địch", UNSUPPORTED_AT_DECORATION, "C10,C11", OriginRaises(tuple, (int,))),
    _C("M02", "M", "get_args NỔ với exception có __str__ thù địch", OUTSIDE_FRAMEWORK_BOUNDARY, "C10", _ARGS_RAISES,
       observe=lambda: _observe_outside_boundary_case(_ARGS_RAISES, "BndM02")),
    # ── N — không hash được
    _C("N01", "N", "class target không hash được (__hash__ = None)", UNSUPPORTED_AT_DECORATION, "C3,C5", Unhashable),
    _C("N02", "N", "Optional[<N01>]", UNSUPPORTED_AT_DECORATION, "C6", Optional[Unhashable]),
    # ── O — __hash__ thù địch
    _C("O01", "O", "class target có __hash__ NỔ", UNSUPPORTED_AT_DECORATION, "C3", HashRaises),
    _C("O02", "O", "class target có __hash__ trả giá trị khác nhau mỗi lần", UNSUPPORTED_AT_DECORATION, "C3", HashDrifts),
    # ── P — __eq__ có tác dụng phụ
    _C("P01", "P", "class target có __eq__/__hash__ đếm side effect", UNSUPPORTED_AT_DECORATION, "C3", EqHasSideEffect),
    _C("P02", "P", "class target có __eq__ NỔ", UNSUPPORTED_AT_DECORATION, "C3", EqRaises),
    _C("P03", "P", "class target có __eq__ luôn trả True", UNSUPPORTED_AT_DECORATION, "C3", EqAlwaysTrue),
    # ── Q — origin mutable / mutable guard
    _C("Q01", "Q", "list trần", UNSUPPORTED_AT_DECORATION, "C3", list),
    _C("Q02", "Q", "dict[str, int]", UNSUPPORTED_AT_DECORATION, "C2,C3", dict[str, int]),
    _C("Q03", "Q", "set[int]", UNSUPPORTED_AT_DECORATION, "C2,C3", set[int]),
    _C("Q04", "Q", "bytearray", UNSUPPORTED_AT_DECORATION, "C3", bytearray),
    _C("Q05", "Q", "Optional[list[int]]", UNSUPPORTED_AT_DECORATION, "C6", Optional[list[int]]),
    _C("Q06", "Q", "Union[list, dict]", UNSUPPORTED_AT_DECORATION, "C6", Union[list, dict]),
    _C("Q07", "Q", "field Any nhận một list", SUPPORTED_INVALID_REJECT, "C5,C7", Any, "ok", [1, 2]),
    _C("Q08", "Q", "field Any nhận một LỚP CON của list", SUPPORTED_INVALID_REJECT, "C5", Any, "ok", MutableSubclass()),
    # ── R — InitVar (tầng decoration)
    _C("R01", "R", "một InitVar[int]", UNSUPPORTED_AT_DECORATION, "C8", observe=lambda: _observe_decoration(_initvar_single)),
    _C("R02", "R", "nhiều InitVar — phải nêu ĐỦ tên", UNSUPPORTED_AT_DECORATION, "C8", observe=_observe_initvar_names),
    _C("R03", "R", "dataclass CHỈ có InitVar", UNSUPPORTED_AT_DECORATION, "C8", observe=lambda: _observe_decoration(_initvar_only)),
    _C("R04", "R", "InitVar dạng kw_only", UNSUPPORTED_AT_DECORATION, "C8", observe=lambda: _observe_decoration(_initvar_kwonly)),
    # ── S — ClassVar (tầng decoration)
    _C("S01", "S", "ClassVar[int] — phải VẪN hợp lệ", SUPPORTED_VALID, "C8", observe=_observe_classvar_alone),
    _C("S02", "S", "ClassVar cùng field thường — không vào contract", SUPPORTED_VALID, "C8", observe=_observe_classvar_with_fields),
    # ── T — độ phức tạp
    _C("T01", "T", "bề rộng: __args__ giả 100 000 + Union thật 600 nhánh", UNSUPPORTED_AT_DECORATION, "C12", observe=_observe_wide_shapes),
    _C("T02", "T", "tuple lồng 30 tầng", UNSUPPORTED_AT_DECORATION, "C2", _nested_tuple(30)),
    _C("T03", "T", "typing tự NỔ khi DỰNG annotation", OUTSIDE_FRAMEWORK_BOUNDARY, "C12", observe=_observe_typing_refuses_first),
    # ── U — forward ref
    _C("U01", "U", "forward ref không phân giải được", UNSUPPORTED_AT_DECORATION, "C10", observe=_observe_forward_ref),
    _C("U02", "U", "forward ref trỏ vòng về chính class", UNSUPPORTED_AT_DECORATION, "C10", observe=_observe_self_forward_ref),
    # ── V — nguyên tử của decoration
    _C("V01", "V", "metaclass __setattr__ NỔ giữa decoration", UNSUPPORTED_AT_DECORATION, "C9,C13", observe=_observe_hostile_metaclass_atomicity),
    _C("V02", "V", "hỏng ở biên B1 — registry KHÔNG ĐỔI", UNSUPPORTED_AT_DECORATION, "C13", observe=_observe_registry_unchanged_on_b1_failure),
    _C("V03", "V", "hỏng ở field thứ hai — class NGUYÊN VẸN", UNSUPPORTED_AT_DECORATION, "C13", observe=_observe_class_untouched_on_second_field_failure),
    # ── W — annotation lạ
    _C("W01", "W", "module object làm annotation", UNSUPPORTED_AT_DECORATION, "C2", sys),
    _C("W02", "W", "lambda làm annotation", UNSUPPORTED_AT_DECORATION, "C2", (lambda: None)),
    _C("W03", "W", "Enum class", UNSUPPORTED_AT_DECORATION, "C3", Shade),
    _C("W04", "W", "abc.ABC subclass", UNSUPPORTED_AT_DECORATION, "C3", PlainABC),
    _C("W05", "W", "class người dùng thường (metaclass type)", UNSUPPORTED_AT_DECORATION, "C3", PlainUserClass),
    _C("W06", "W", "re.Pattern", UNSUPPORTED_AT_DECORATION, "C3", _re.Pattern),
    _C("W07", "W", "type", UNSUPPORTED_AT_DECORATION, "C3", type),
    # ── X — witness của TỪNG thành viên allowlist
    _C("X01", "X", "field str", SUPPORTED_VALID, "C4,C14", str, "x", 1),
    _C("X02", "X", "field int — True bị loại", SUPPORTED_VALID, "C4,C14", int, 1, True),
    _C("X03", "X", "field bool — 1 bị loại", SUPPORTED_VALID, "C4,C14", bool, True, 1),
    _C("X04", "X", "field date", SUPPORTED_VALID, "C4,C14", date, date(2026, 1, 1), "2026-01-01"),
    _C("X05", "X", "field tuple — list bị loại", SUPPORTED_VALID, "C4,C5,C14", tuple, (1, 2), [1, 2]),
    _C("X06", "X", "field frozenset — set bị loại", SUPPORTED_VALID, "C4,C14", frozenset, frozenset([1]), {1}),
    _C("X07", "X", "field FrozenMapping", SUPPORTED_VALID, "C3,C14", FrozenMapping, FrozenMapping({}), {}),
    _C("X08", "X", "field FrozenCounter", SUPPORTED_VALID, "C3,C14", FrozenCounter, FrozenCounter({}), {}),
    _C("X09", "X", "field Any", SUPPORTED_VALID, "C7,C14", Any, object(), MISSING),
    _C("X10", "X", "field NoneType", SUPPORTED_VALID, "C2,C14", type(None), None, 1),
    _C("X11", "X", "field DateWindow", SUPPORTED_VALID, "C3,C14", _em.DateWindow, _em.DateWindow(date(2026, 1, 1), date(2026, 1, 2)), "x"),
    _C("X12", "X", "field RecordRef", SUPPORTED_VALID, "C3,C14", _em.RecordRef, _em.RecordRef("snap", 0, "Ly"), "x"),
    _C("X13", "X", "field RowProvenance (SEALED, witness từ factory)", SUPPORTED_VALID, "C3,C14", _vm.RowProvenance, _witness_row_provenance(), "x"),
    # ── Y — hành vi từng nhánh của union
    _C("Y01", "Y", "Optional[str] — nhánh None", SUPPORTED_VALID, "C6", Optional[str], None, 1),
    _C("Y02", "Y", "Optional[str] — nhánh str, loại 1.5", SUPPORTED_VALID, "C6", Optional[str], "x", 1.5),
    _C("Y03", "Y", "Optional[int] — loại True trong nhánh int", SUPPORTED_INVALID_REJECT, "C4,C6", Optional[int], 3, True),
    _C("Y04", "Y", "Optional[RecordRef] — loại 'x'", SUPPORTED_INVALID_REJECT, "C4,C6", Optional[_em.RecordRef], None, "x"),
)


# ═══════════════════════════════════════════════ Z — bất biến quét toàn corpus


def z01_only_contract_violations_escape_decoration() -> tuple:
    """Mọi ngoại lệ thoát ra khỏi decoration CỦA FRAMEWORK đúng là
    `CanonicalContractViolation`.

    Phạm vi là giai đoạn `@canonical`. Case mà CPython `@dataclass` từ chối
    trước đó không thuộc phạm vi này — framework chưa có trên call stack — và
    chúng được LIỆT KÊ RA thay vì bị giấu đi, để biên luôn nhìn thấy được.
    """
    leaks = []
    for case in FROZEN_CORPUS:
        observed = case.run()
        if "RAW_ERROR" in observed:
            leaks.append(f"{case.id}:{observed}")
    return (not leaks, leaks)


def cpython_boundary_cases() -> tuple:
    """Case mà CPython từ chối TRƯỚC khi `@canonical` chạy — biên đã phân loại."""
    return tuple(c.id for c in FROZEN_CORPUS
                 if c.annotation is not MISSING
                 and c.run() == OUTSIDE_FRAMEWORK_BOUNDARY)


def z02_no_foreign_text_in_messages() -> tuple:
    """Không thông báo nào chứa ký tự do object lạ sinh ra."""
    needles = ("X" * 50, "Y" * 50, "12345", "ProbeRepr")
    dirty = []
    for case in FROZEN_CORPUS:
        if case.annotation is MISSING or case.expected != UNSUPPORTED_AT_DECORATION:
            continue
        try:
            probe_class(case.annotation)
        except CanonicalContractViolation as exc:
            text = str(exc)
            if any(n in text for n in needles):
                dirty.append(case.id)
        except BaseException:  # noqa: BLE001 — Z01 lo chuyện này
            pass
    return (not dirty, dirty)


def z03_no_hostile_hook_ever_runs() -> tuple:
    """Không hook nào của object lạ được gọi trên đường phân loại.

    "Không nổ" chưa phải "không chạy": bản `1b0da151` gọi `__repr__` của
    annotation lạ hai lần trong `try/except` và vẫn coi là an toàn.
    """
    ran = set()
    for case in FROZEN_CORPUS:
        if case.group == "J":
            continue  # nhóm J CỐ Ý đưa giá trị thù địch vào đường runtime
        if case.annotation is MISSING:
            continue
        try:
            raw = _raw_dataclass(case.annotation, "ProbeZ3")
        except BaseException:  # noqa: BLE001 — giai đoạn CPython, ngoài phạm vi
            continue
        SIDE_EFFECTS.clear()          # bỏ qua hook do CPython gọi ở trên
        try:
            canonical()(raw)
        except BaseException:  # noqa: BLE001
            pass
        ran.update(SIDE_EFFECTS)
    SIDE_EFFECTS.clear()
    return (not ran, sorted(ran))


def z04_framework_bugs_are_not_swallowed() -> tuple:
    """Lỗi lập trình BÊN TRONG framework KHÔNG bị nuốt thành
    CanonicalContractViolation.

    Tiêm một lỗi vào chính `_build_spec` rồi khẳng định nó nổi lên nguyên hình.
    """
    import app.modules.domain.canonical as cm

    marker = ZeroDivisionError
    original = cm._in_allowlist

    def exploding(_target):
        raise marker("bug giả lập bên trong framework")

    cm._in_allowlist = exploding
    try:
        probe_class(str, "ProbeZ4")
    except marker:
        return (True, [])
    except BaseException as exc:  # noqa: BLE001
        return (False, [f"bị nuốt thành {type(exc).__name__}"])
    finally:
        cm._in_allowlist = original
    return (False, ["không nổ gì cả"])


Z_INVARIANTS = (
    ("Z01", "mọi exception thoát khỏi decoration ĐÚNG là CanonicalContractViolation",
     "C10", z01_only_contract_violations_escape_decoration),
    ("Z02", "không thông báo nào chứa ký tự do object lạ sinh ra",
     "C11", z02_no_foreign_text_in_messages),
    ("Z03", "không hook nào của object lạ được gọi trên đường phân loại",
     "C1,C4", z03_no_hostile_hook_ever_runs),
    ("Z04", "lỗi lập trình BÊN TRONG framework KHÔNG bị nuốt",
     "C10", z04_framework_bugs_are_not_swallowed),
)

TOTAL_CASES = len(FROZEN_CORPUS) + len(Z_INVARIANTS)


def corpus_accounting() -> dict:
    """Số học chính thức của corpus (§8 Owner Decision).

    KHÔNG báo "102/105 PASS" (đọc như 3 case hỏng) và KHÔNG báo "105/105 PASS"
    (đọc như 3 case ngoài biên cũng là in-scope). Corpus được PHÂN LOẠI đủ 105;
    trong đó 102 in-scope và 3 nằm ngoài biên framework.
    """
    in_scope, outside, unclassified, blocking = [], [], [], []
    for case in FROZEN_CORPUS:
        observed = case.run()
        ok = _satisfies(case.expected, observed)
        bucket = outside if case.id in OUTSIDE_BOUNDARY_CASE_IDS else in_scope
        bucket.append((case.id, ok, observed))
        if not ok:
            blocking.append((case.id, case.expected, observed))
    for cid, desc, clause, fn in Z_INVARIANTS:
        ok, detail = fn()
        in_scope.append((cid, ok, INVARIANT if ok else str(detail)))
        if not ok:
            blocking.append((cid, INVARIANT, str(detail)))
    return {
        "classified": len(in_scope) + len(outside),
        "in_scope_total": len(in_scope),
        "in_scope_pass": sum(1 for _, ok, _ in in_scope if ok),
        "outside_total": len(outside),
        "outside_ok": sum(1 for _, ok, _ in outside if ok),
        "outside_ids": [cid for cid, _, _ in outside],
        "unclassified": len(unclassified),
        "blocking": blocking,
    }


def main() -> int:
    acc = corpus_accounting()
    print("R1-A1 — FROZEN ATTACK CORPUS")
    print(f"interpreter đã verify: {VERIFIED_IMPLEMENTATION} {VERIFIED_PYTHON_VERSION}")
    print(f"interpreter đang chạy khớp: {interpreter_matches_verified()}\n")
    print(f"{'ID':5s} {'GRP':4s} {'CLAUSE':10s} {'MÔ TẢ':54s} {'EXPECTED':28s} KẾT QUẢ")
    print("-" * 130)
    for case in FROZEN_CORPUS:
        observed = case.run()
        ok = _satisfies(case.expected, observed)
        mark = "PASS" if ok else f"FAIL (đo được: {observed})"
        print(f"{case.id:5s} {case.group:4s} {case.clause:10s} "
              f"{case.description[:54]:54s} {case.expected:28s} {mark}")
    for cid, desc, clause, fn in Z_INVARIANTS:
        ok, detail = fn()
        mark = "PASS" if ok else f"FAIL ({detail})"
        print(f"{cid:5s} {'Z':4s} {clause:10s} {desc[:54]:54s} {INVARIANT:28s} {mark}")
    print("-" * 130)
    print("FROZEN CORPUS:")
    print(f"    {acc['classified']}/{TOTAL_CASES} CLASSIFIED")
    print(f"IN-FRAMEWORK FROZEN IDs:")
    print(f"    {acc['in_scope_pass']}/{acc['in_scope_total']} PASS")
    print(f"OUTSIDE_FRAMEWORK_BOUNDARY:")
    print(f"    {acc['outside_ok']}/{acc['outside_total']} correctly classified"
          f"  ({', '.join(acc['outside_ids'])})")
    print(f"    HD-POST-A1-02: {', '.join(HD_POST_A1_02_RECLASSIFIED_IDS)}"
          f"  ·  HD-POST-A1-04: {', '.join(HD_POST_A1_04_RATIFIED_IDS)}")
    print(f"UNCLASSIFIED:")
    print(f"    {acc['unclassified']}")
    print(f"BLOCKING FAIL:")
    print(f"    {len(acc['blocking'])}")
    print(f"\nSỐ HỌC: {TOTAL_CASES} = {acc['in_scope_total']} + {acc['outside_total']}"
          f"  ->  {acc['in_scope_total'] + acc['outside_total'] == TOTAL_CASES}")
    if acc["blocking"]:
        print("\nBLOCKING:")
        for cid, expected, observed in acc["blocking"]:
            print(f"  {cid}: chờ {expected}, đo được {observed}")
    return 1 if acc["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
