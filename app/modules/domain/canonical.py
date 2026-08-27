"""Biên canonical — GIỮ ĐƯỢC OBJECT CHÍNH LÀ BẰNG CHỨNG OBJECT HỢP LỆ (R1).

## Vì sao file này tồn tại

Trước Repair R1, "sealed construction" được cài bằng một *field* sentinel::

    @dataclass(frozen=True)
    class X:
        ...
        _seal: Any = None
        def __post_init__(self):
            if self._seal is not _SEAL:
                raise SealedConstruction(...)

Independent Review #8 falsify được cấu trúc đó. Root cause không phải thiếu
một vài phép kiểm, mà là **ba tính chất cấu trúc** của chính cơ chế:

1. **Seal là một FIELD**, nên nó là dữ liệu công khai của object. Vì thế nó
   *đọc lại được* (``obj._seal``), *sao chép được* bởi
   ``dataclasses.replace()``, và *truyền vào được* qua ``__init__``. Một
   capability token mà chính object trao lại cho mọi caller thì không phải
   capability token. Đo được: ``replace(master, records=("rác",))`` mang seal
   hợp lệ sang một object rác.

2. **``__post_init__`` là một method thường, ghi đè được.** Một subclass ghi đè
   nó là xoá sạch phép kiểm, trong khi ``isinstance()`` vẫn trả ``True``. Phép
   validate cài bằng một method mở thì chỉ có tính khuyến nghị.

3. **Phép kiểm là ``_seal is _SEAL``, không phải kiểm lại bất biến.** Phần
   parse thật nằm NGOÀI kiểu (``parse_employee_record()``,
   ``AffectedRow.from_line()``). Nên khi vào lại constructor với một seal hợp
   lệ và dữ liệu khác, ta được một object chưa từng được parse.

Nói gọn: **biên canonical là một token truyền vào constructor công khai, chứ
không phải chính constructor.**

## Bất biến R1

    Với mọi canonical type ``C``: một object thoả ``isinstance(x, C)`` chỉ tồn
    tại nếu nó do factory của chính ``C`` dựng ra VÀ mọi bất biến của ``C``
    đúng tại thời điểm dựng; vì ``C`` bất biến sâu, chúng còn đúng mãi về sau.
    Không public/reasonable API nào — kể cả ``C(...)``, ``dataclasses.replace``,
    ``copy``/``deepcopy``, ``pickle``, hay kế thừa — tạo được ngoại lệ.

## Bốn lớp đóng, mỗi lớp đóng một mệnh đề khác nhau

**Lớp 1 — kiểu tự validate.** Mọi bất biến của ``C`` được kiểm trong
``__post_init__`` của chính ``C``, và mọi container được SAO CHÉP sang dạng
bất biến. Vì thế bất kỳ đường nào quay lại ``__init__`` — ``replace()`` trước
hết — cũng không dựng nổi dữ liệu invalid. Đây là phần "làm invalid state
không biểu diễn được", và nó khiến seal thôi gánh trách nhiệm an toàn.

**Lớp 2 — construction đóng kín.** Với những kiểu mà tính hợp lệ bao gồm cả
"đã đi qua một phép parse có thật" (provenance), constructor công khai bị chặn
bằng một **permit theo class, KHÔNG phải field**: nó chỉ sống trong thân một
factory đã đăng ký, không có field nào để đọc, không có tham số nào để truyền,
và ``replace()`` (gọi ngoài factory) raise ``SealedConstruction``. Không còn
sentinel nào để sao chép, nên bypass (1) chết theo cơ chế chứ không theo danh
sách.

**Lớp 3 — final.** Canonical type từ chối subclass khai báo ngoài module định
nghĩa nó. Vì thế ``__post_init__`` không ghi đè được từ bên ngoài, và
``isinstance(x, C)`` lại trở thành bằng chứng.

**Lớp 4 — mọi đường tái tạo quay về constructor.** ``copy``/``deepcopy`` trả
về chính object (đúng ngữ nghĩa cho value object bất biến); ``pickle`` của
kiểu sealed bị từ chối, của kiểu còn lại đi qua constructor nên vẫn validate.

## Điều file này CỐ TÌNH không hứa

Python không có kiểu thật sự đóng. ``object.__setattr__`` trên một instance
frozen, ``ctypes``, ``gc.get_objects()``, hay việc gán ``fn.__module__`` để
giả mạo module chủ vẫn phá được. Bất biến trên phát biểu với **public/
reasonable API**; những đường còn lại đều đòi hỏi cố ý thò tay vào nội bộ
private của module khác, và được ghi nhận là residual risk của R1.
"""

from __future__ import annotations

import dataclasses as _dataclasses
import functools
import threading
import types as _types
import typing
from datetime import date, datetime as _datetime
from collections.abc import Mapping
from dataclasses import fields as _dataclass_fields
from operator import itemgetter
from types import MappingProxyType
from typing import Any, Callable, Optional


class SealedConstruction(TypeError):
    """Một canonical object bị dựng ngoài factory đã parse của chính nó.

    Đây là lỗi lập trình, không phải lỗi dữ liệu, nên nó nổ to thay vì trả về
    một object "gần đúng".
    """


class CanonicalContractViolation(TypeError):
    """Một type được decorate ``@canonical`` nhưng không thoả hợp đồng canonical.

    Nổ ở **thời điểm import**, không phải trong một test nào đó. Đây là điểm
    mà Independent Review R1 (FAIL tại ``2be5bfe``) chỉ ra là còn thiếu:
    ``@canonical`` khi đó là một *lời tuyên bố*, không phải một *hợp đồng* —
    nó nhận ``RecordRef`` và ``MappingResult`` mà không đòi hỏi bằng chứng nào
    rằng hai type đó có validate gì.
    """


class CanonicalFieldError(TypeError):
    """Một field của canonical object không đúng kiểu đã khai, hoặc là một
    container mutable.

    Kế thừa ``TypeError`` để mọi consumer sẵn có bắt ``TypeError`` vẫn đúng.
    """


class CanonicalSubclassRejected(SealedConstruction):
    """Một canonical type bị kế thừa từ ngoài module định nghĩa nó.

    Kế thừa là đường ghi đè ``__post_init__``, tức là đường xoá phép validate
    trong khi ``isinstance()`` vẫn nói "hợp lệ". Đóng nó là điều kiện để
    ``isinstance`` còn là bằng chứng.
    """


# ─────────────────────────────────────────────────────────── Lớp 2: permit
#
# Permit là trạng thái AMBIENT theo thread, đếm theo class. Nó KHÔNG nằm trên
# object, nên không đọc lại được, không sao chép được bởi `replace()`, và
# không truyền vào được qua `__init__`. Đó chính là điểm khác biệt so với
# field `_seal` mà Review #8 đã falsify.

_PERMITS = threading.local()


def _permit_counts() -> dict:
    counts = getattr(_PERMITS, "counts", None)
    if counts is None:
        counts = {}
        _PERMITS.counts = counts
    return counts


def _is_permitted(cls: type) -> bool:
    return _permit_counts().get(cls, 0) > 0


class _ConstructionPermit:
    """Quyền dựng ĐÚNG MỘT class, sống đúng trong thân một materialiser.

    Đếm chồng (re-entrant) vì một factory có thể gọi factory khác của cùng
    class (``RowProvenance.batch()`` gọi ``RowProvenance.of()``).
    """

    __slots__ = ("_cls",)

    def __init__(self, cls: type) -> None:
        self._cls = cls

    def __enter__(self) -> "_ConstructionPermit":
        counts = _permit_counts()
        counts[self._cls] = counts.get(self._cls, 0) + 1
        return self

    def __exit__(self, *exc_info: Any) -> bool:
        counts = _permit_counts()
        remaining = counts.get(self._cls, 0) - 1
        if remaining > 0:
            counts[self._cls] = remaining
        else:
            counts.pop(self._cls, None)
        return False


def factory_for(cls: type) -> Callable[[Callable], Callable]:
    """Đánh dấu một hàm là **materialiser** được phép dựng ``cls``.

    Hai ràng buộc cấu trúc, không phải quy ước:

    1. Hàm PHẢI nằm trong chính module định nghĩa ``cls``. Chỉ module chủ của
       một canonical type mới được vật chất hoá nó — cùng ranh giới với luật
       final ở Lớp 3, nên không có cách nào "đăng ký thêm một factory" từ
       ngoài.
    2. Permit chỉ mở trong thân hàm được đánh dấu. Nên materialiser phải là
       một hàm bé, thân chỉ có đúng lời gọi ``cls(...)``: mọi việc đọc dữ liệu
       của caller xảy ra TRƯỚC khi permit mở.
    """

    def decorate(fn: Callable) -> Callable:
        home = getattr(fn, "__module__", None)
        if home != cls.__module__:
            raise SealedConstruction(
                f"Materialiser của {cls.__name__} phải nằm trong module định "
                f"nghĩa nó ({cls.__module__!r}), không phải {home!r}. Cho phép "
                "đăng ký factory từ module khác chính là mở lại đường mà seal "
                "dạng field đã bị falsify."
            )

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with _ConstructionPermit(cls):
                return fn(*args, **kwargs)

        wrapper.__canonical_factory_for__ = cls  # type: ignore[attr-defined]
        return wrapper

    return decorate


# ──────────── R1-A1: HỢP ĐỒNG ANNOTATION HỮU HẠN (FROZEN CONTRACT, DEC-135)
#
# Independent Review R1-A Finding #1 (tại `dead82e`) mở ra một vòng lặp ba lần
# repair: mỗi vòng đóng thêm vài lớp annotation, và mỗi vòng review sau lại
# dựng được một object Python mới mà lớp vừa đóng chưa nghĩ tới — metaclass
# mới, `__instancecheck__` đổi hành vi theo giá trị, `__hash__` nổ, `__repr__`
# có side effect, `__class__` nói dối.
#
# Root cause KHÔNG phải thiếu thêm vài nhánh. Root cause là **tiêu chí chấp
# nhận được phát biểu trên một không gian vô hạn**: "mọi annotation hợp lý đều
# phải an toàn". Không gian đó không đếm được, nên không vòng repair nào kết
# thúc được.
#
# Bản này thay tiêu chí đó bằng một HỢP ĐỒNG ĐÓNG, hữu hạn, do Owner freeze
# (`docs/tasks/TASK-110-R1-A1-FROZEN-CONTRACT.md`):
#
#     spec := any | none | class | optional
#
# Bốn dạng. Không có dạng thứ năm. Nhánh cuối của parser là `raise`.
#
# ## Vì sao đóng được tới mức này: production chỉ cần tới mức này
#
# Audit 11 canonical type / 72 field tại `1b0da151` cho ra đúng 17 hình thái
# annotation, và cả 17 quy về ba dạng: `class` (37 field), `optional` (34),
# `any` (1). Production KHÔNG dùng một generic có tham số nào, KHÔNG dùng
# `Literal`, KHÔNG dùng union nhiều nhánh. Ngữ pháp dưới đây vì thế phủ 72/72
# field mà không phải mở thêm gì — và mọi thứ ngoài nó là UNSUPPORTED theo
# **mặc định TỪ CHỐI**.
#
# ## Hai thay đổi cấu trúc, không phải hai phép kiểm thêm
#
# **1. Phân loại bằng ĐỊNH DANH, không bằng cách hỏi object lạ.** Một class chỉ
# được nhận nếu nó `is` một phần tử của allowlist đóng. Không `hash(target)`,
# không `target == x`, không `target in <set>`, không `isinstance(v, target)`,
# không `repr`/`str`/`__name__`/`__module__`. Với annotation HỢP LỆ, framework
# không thực hiện một lời gọi lạ nào.
#
# **2. Kiểm runtime bằng `type(value) is T`, không `isinstance`.** Đo trên toàn
# bộ 702 test tại `1b0da151`: 0 lần `isinstance` và `type(v) is T` cho kết quả
# khác nhau. Dung sai lớp con mà `isinstance` mua thêm, production không dùng;
# còn cái nó bán đi là hai lỗ hổng đo được — `isinstance` tra `value.__class__`,
# nên một property `__class__` nổ làm lỗi thô thoát ra, và một `__class__` nói
# dối đưa object giả qua được field khai class thật.
#
# ## Điều hợp đồng này CỐ TÌNH không hứa
#
# Nó không hứa "không ai nghĩ ra được attack Python mới". Nó hứa một điều đếm
# được: mọi annotation hoặc nằm trong bốn dạng trên và được kiểm đủ, hoặc nổ
# `CanonicalContractViolation` ngay lúc decorate.

_NONE_TYPE = type(None)
_UNION_TYPE = getattr(_types, "UnionType", None)

# ── C3 — FROZEN_CLASS_ALLOWLIST: bốn category hữu hạn, so bằng ĐỊNH DANH.
#
# Vô hướng bất biến. Kiểm bằng `type(v) is T` nên `True` KHÔNG lọt qua `int`
# (bool là lớp con của int), và một lớp con của `str` đổi giá trị giữa hai lần
# đọc cũng không lọt qua `str`.
_FROZEN_SCALARS = (str, int, bool, date)

# Container bất biến. Dạng TRẦN, không tham số — production chỉ dùng dạng này,
# và mọi generic có tham số là UNSUPPORTED (HD-A1-16).
_FROZEN_CONTAINERS = (tuple, frozenset)

# Class do chính framework sở hữu. Điền sau khi định nghĩa xong ở cuối file.
_FROZEN_FRAMEWORK: list = []

# Container mutable: cấm ở MỌI field, bất kể annotation. `frozen=True` chỉ cấm
# gán lại thuộc tính, không cấm sửa đối tượng nó trỏ tới. Chính sách này thuộc
# R1-D và KHÔNG đổi ở R1-A1.
_MUTABLE_CONTAINERS = (list, dict, set, bytearray)

# ── C12 — ngân sách độ phức tạp.
#
# Dưới ngữ pháp đóng, một annotation HỢP LỆ có tối đa 3 nút (đo trên cả 72
# field production: max = 3), nên ngân sách này không bao giờ chặn oan. Nó là
# hàng rào cho trục BỀ RỘNG: một `Union` 600 nhánh có `get_args()` dài 600 và
# bị chặn ở đây TRƯỚC khi tới phép kiểm arity. Không còn giới hạn ĐỘ SÂU riêng:
# ngữ pháp tự chặn ở 2 tầng, nên parser không đệ quy và `RecursionError` của
# CPython không còn cơ hội làm chính sách.
_MAX_ANNOTATION_NODES = 512


# ── C11 — AN TOÀN THÔNG BÁO.
#
# Thông báo lúc decorate KHÔNG chứa một ký tự nào do object lạ sinh ra. Bản
# trước có `_safe_name()` gọi `repr(obj)` trong `try/except`: nó không để lọt
# exception, nhưng nó VẪN chạy code của người khác — đo được hai lần gọi
# `__repr__` có side effect. Không nổ ≠ không chạy. Nên toàn bộ lý do từ chối
# là HẰNG SỐ, và thứ duy nhất thay đổi theo ngữ cảnh là tên field, vốn do
# `dataclasses.fields()` cấp.

_REASON_NOT_IN_GRAMMAR = (
    "annotation nằm NGOÀI ngữ pháp canonical đã đóng băng. Ngữ pháp chỉ gồm "
    "bốn dạng: `Any`; `None`; một class thuộc allowlist đóng "
    "(`str`/`int`/`bool`/`date`/`tuple`/`frozenset`/`FrozenMapping`/"
    "`FrozenCounter`/một canonical type đã đăng ký TRƯỚC đó); và `Optional[X]` "
    "với `X` thuộc chính allowlist ấy. Mọi thứ khác — generic có tham số, "
    "`Literal`, union tổng quát, `TypeVar`, `Callable`, `Protocol`, "
    "`TypedDict`, `Enum`, class ngoài allowlist — là UNSUPPORTED theo mặc "
    "định TỪ CHỐI. Framework không đoán một annotation 'có vẻ dùng được'."
)

_REASON_UNION_ARITY = (
    "union phải có ĐÚNG hai nhánh và một trong hai phải là `None`. Union "
    "nhiều nhánh không nằm trong ngữ pháp đóng: production chỉ dùng "
    "`Optional[X]`."
)

_REASON_UNION_SHAPE = (
    "union có hai nhánh nhưng không phải dạng `Optional[X]` hợp lệ: cần đúng "
    "một nhánh `None` và một nhánh là class thuộc allowlist đóng."
)

_REASON_ARGS_NOT_TUPLE = (
    "tham số của union không phải một tuple, nên annotation này không phải "
    "một union thật."
)

_REASON_NODE_BUDGET = (
    f"annotation có hơn {_MAX_ANNOTATION_NODES} nút. Giới hạn này chặn trục "
    "BỀ RỘNG (union khổng lồ) — thứ không nổ `RecursionError` nhưng vẫn là độ "
    "phức tạp không kiểm soát. Đây là hằng số TẤT ĐỊNH của framework, không "
    "phải stack còn lại của CPython."
)

_REASON_B2 = (
    "không khảo sát được `get_origin` của annotation (biên lạ B2). Một "
    "annotation mà framework không khảo sát nổi thì không thể được coi là hỗ "
    "trợ. Lý do gốc CỐ Ý không được render: đọc `__str__` của một exception lạ "
    "chính là chạy code lạ."
)

_REASON_B3 = (
    "không khảo sát được `get_args` của annotation (biên lạ B3). Xem giải "
    "thích ở B2."
)

# Tên hiển thị của KIỂU GIÁ TRỊ trong thông báo runtime. Tra bằng ĐỊNH DANH.
# Ngoài bảng -> hằng số, không bao giờ `type(v).__name__` (một metaclass có
# `__getattribute__` riêng biến việc dựng thông báo thành đường chạy code lạ).
_VALUE_TYPE_NAME_PAIRS: list = [
    (str, "str"), (int, "int"), (bool, "bool"), (float, "float"),
    (bytes, "bytes"), (complex, "complex"), (date, "date"),
    (_datetime, "datetime"), (tuple, "tuple"), (frozenset, "frozenset"),
    (list, "list"), (dict, "dict"), (set, "set"), (bytearray, "bytearray"),
    (_NONE_TYPE, "NoneType"), (MappingProxyType, "mappingproxy"),
]
_UNKNOWN_TYPE_NAME = "<kiểu không xác định>"
_UNRENDERABLE_VALUE = "<giá trị không hiển thị được>"
_MAX_VALUE_REPR = 200

# Chỉ những kiểu có `__repr__` là hàm C, không đệ quy xuống phần tử con, mới
# được render. `tuple`/`frozenset` KHÔNG nằm đây: `repr((hostile,))` gọi
# `__repr__` của phần tử.
_REPR_SAFE_TYPES = (str, int, bool, float, bytes, complex, date, _NONE_TYPE)

# Nhãn tiếng Việt của kiểu trong thông báo hợp đồng. Giữ đúng từ mà các thông
# báo master data đã dùng từ trước ("chuỗi thuần", "boolean") để bằng chứng cũ
# còn khớp. Class được `@canonical` nhận sẽ tự thêm nhãn của nó lúc commit.
_CLASS_LABEL_PAIRS: list = [
    (str, "chuỗi thuần"),
    (bool, "boolean"),
    (int, "số nguyên thuần"),
    (date, "ngày (`datetime.date`) thuần"),
    (tuple, "`tuple`"),
    (frozenset, "`frozenset`"),
]


def _is_one_of(target: Any, candidates) -> bool:
    """So bằng ĐỊNH DANH, không bằng `==` và không qua `hash()`.

    `target in <frozenset>` gọi `__hash__` của metaclass lạ TRƯỚC khi target
    được chứng minh an toàn; `dict.get()` cũng vậy. `is` không chạm code nào.
    """
    return any(target is candidate for candidate in candidates)


def _pair_lookup(key: Any, pairs, default: str) -> str:
    """Tra bảng bằng ĐỊNH DANH. Thay cho `dict[...]`, vốn gọi `__hash__`."""
    for candidate, value in pairs:
        if key is candidate:
            return value
    return default


def _in_allowlist(target: Any) -> bool:
    """C3 — target có thuộc FROZEN_CLASS_ALLOWLIST không.

    Bốn category, tất cả so bằng định danh. `_REGISTRY` là metadata do chính
    decorator ghi, nên nó là trusted source theo đúng nghĩa §4 của hợp đồng:
    framework không hỏi object lạ, nó tra sổ của chính nó.
    """
    return (_is_one_of(target, _FROZEN_SCALARS)
            or _is_one_of(target, _FROZEN_CONTAINERS)
            or _is_one_of(target, _FROZEN_FRAMEWORK)
            or _is_one_of(target, _REGISTRY))


def frozen_class_allowlist() -> tuple:
    """Toàn bộ allowlist tại thời điểm gọi — để oracle đi hết được nó."""
    return (tuple(_FROZEN_SCALARS) + tuple(_FROZEN_CONTAINERS)
            + tuple(_FROZEN_FRAMEWORK) + tuple(_REGISTRY))


def _value_type_name(value: Any) -> str:
    return _pair_lookup(type(value), _VALUE_TYPE_NAME_PAIRS, _UNKNOWN_TYPE_NAME)


def _render_value(value: Any) -> str:
    """Render giá trị bị từ chối, KHÔNG bao giờ chạy code của người khác."""
    if not _is_one_of(type(value), _REPR_SAFE_TYPES):
        return _UNRENDERABLE_VALUE
    text = repr(value)
    if len(text) > _MAX_VALUE_REPR:
        return text[:_MAX_VALUE_REPR] + "…"
    return text


def _violation(where: str, reason: str) -> "CanonicalContractViolation":
    return CanonicalContractViolation(f"{where}: {reason}")


# ── C10 — BIÊN LẠ. Đúng ba điểm chạm object lạ trong toàn bộ hợp đồng, và
# không điểm nào ở đường runtime. Mỗi `try` bọc ĐÚNG MỘT lời gọi stdlib, nên
# lỗi lập trình BÊN TRONG framework vẫn nổ nguyên hình thay vì bị nuốt thành
# `CanonicalContractViolation`.
#
# `from None` chứ không `from exc`: giữ `exc` trong chain nghĩa là bất kỳ ai in
# traceback về sau đều chạy `__str__` của nó — đúng lỗ hổng đang đóng, chỉ bị
# dời chỗ. Mã lý do đã chỉ đủ rõ biên nào hỏng.


def _boundary_get_origin(hint: Any, where: str) -> Any:
    try:
        return typing.get_origin(hint)
    except Exception:  # noqa: BLE001 — biên lạ B2, bọc đúng một lời gọi
        raise _violation(where, _REASON_B2) from None


def _boundary_get_args(hint: Any, where: str) -> Any:
    try:
        return typing.get_args(hint)
    except Exception:  # noqa: BLE001 — biên lạ B3, bọc đúng một lời gọi
        raise _violation(where, _REASON_B3) from None


# ── Cây spec. Bốn nút, đúng bằng bốn production của ngữ pháp.


class _Spec:
    """Một NÚT của cây annotation đã parse.

    `children()` phơi cấu trúc ra cho một test ở tầng trừu tượng đi hết được
    cây, nên "thêm một dạng mới rồi hậu duệ của nó biến mất" không lặng lẽ xảy
    ra được.
    """

    __slots__ = ("label", "source")

    def matches(self, value: Any) -> bool:  # pragma: no cover - giao diện
        raise NotImplementedError

    def children(self) -> tuple:
        return ()

    def accepts_none(self) -> bool:
        return self.matches(None)

    def has_exact_scalar(self) -> bool:
        """Có kiểm một vô hướng dựng sẵn không — quyết định thông báo có kèm
        câu giải thích về `str` subclass / `True` là `int` hay không."""
        return False


class _AnySpec(_Spec):
    """C7 — `Any`: không kiểm kiểu, nhưng VẪN chịu mutable guard."""

    __slots__ = ()

    def __init__(self) -> None:
        self.label = "`Any`"

    def matches(self, value: Any) -> bool:
        return True


class _NoneSpec(_Spec):
    __slots__ = ()

    def __init__(self) -> None:
        self.label = "`None`"

    def matches(self, value: Any) -> bool:
        return value is None


class _ClassSpec(_Spec):
    """C4 — một class thuộc allowlist, kiểm bằng ĐỊNH DANH KIỂU CHÍNH XÁC.

    `type(value) is target` đọc thẳng slot `ob_type` trong header object, nên
    nó miễn nhiễm với `__class__` giả mạo, không gọi `__instancecheck__`,
    không gọi `__subclasshook__`, và không phụ thuộc metaclass của target.
    """

    __slots__ = ("_target", "_scalar")

    def __init__(self, target: type) -> None:
        self._target = target
        self._scalar = _is_one_of(target, _FROZEN_SCALARS)
        self.label = _pair_lookup(target, _CLASS_LABEL_PAIRS, _UNKNOWN_TYPE_NAME)

    def matches(self, value: Any) -> bool:
        return type(value) is self._target

    def has_exact_scalar(self) -> bool:
        return self._scalar


class _OptionalSpec(_Spec):
    """C6 — `Optional[X]`: `None`, hoặc đúng kiểu `X`."""

    __slots__ = ("_inner",)

    def __init__(self, inner: _ClassSpec) -> None:
        self._inner = inner
        self.label = f"{inner.label} hoặc `None`"

    def children(self) -> tuple:
        return (self._inner,)

    def matches(self, value: Any) -> bool:
        return value is None or self._inner.matches(value)

    def has_exact_scalar(self) -> bool:
        return self._inner.has_exact_scalar()


def _build_spec(hint: Any, where: str) -> _Spec:
    """C1/C2 — phân loại một annotation, hoặc `raise`. Không có ô thứ ba.

    Không đệ quy: ngữ pháp sâu tối đa hai tầng nên đây là mã thẳng. Ba phép
    kiểm định danh đứng TRƯỚC mọi lời gọi lạ, nên với một annotation hợp lệ
    framework không chạm vào code của ai.
    """
    nodes = 1
    if hint is Any:
        return _AnySpec()
    if hint is None or hint is _NONE_TYPE:
        return _NoneSpec()
    if _in_allowlist(hint):
        return _ClassSpec(hint)

    origin = _boundary_get_origin(hint, where)
    if not (origin is typing.Union
            or (_UNION_TYPE is not None and origin is _UNION_TYPE)):
        raise _violation(where, _REASON_NOT_IN_GRAMMAR)

    args = _boundary_get_args(hint, where)
    if type(args) is not tuple:
        raise _violation(where, _REASON_ARGS_NOT_TUPLE)
    nodes += len(args)
    if nodes > _MAX_ANNOTATION_NODES:
        raise _violation(where, _REASON_NODE_BUDGET)
    if len(args) != 2:
        raise _violation(where, _REASON_UNION_ARITY)

    first, second = args
    # `None` được chấp nhận ở CẢ HAI vị trí: `Union[None, str]` cho
    # `get_args() == (NoneType, str)` — chỉ nhận một vị trí là một bẫy im lặng.
    if first is _NONE_TYPE and second is not _NONE_TYPE and _in_allowlist(second):
        return _OptionalSpec(_ClassSpec(second))
    if second is _NONE_TYPE and first is not _NONE_TYPE and _in_allowlist(first):
        return _OptionalSpec(_ClassSpec(first))
    raise _violation(where, _REASON_UNION_SHAPE)


def _field_checker(name: str, hint: Any, error: type) -> Callable[[Any, str], None]:
    """Dựng phép kiểm cho một field, MỘT LẦN, lúc decorate.

    `error` là lớp ngoại lệ mà type khai — xem `canonical(field_error=...)`.
    Master data hỏng phải nổ thành `InvalidEmployeeConfig`, không phải một
    `TypeError` chung chung: lằn ranh "công cụ hỏng" ≠ "dữ liệu xấu" là một
    quyết định nghiệp vụ (HD-110-09), không phải chi tiết cài đặt.
    """
    spec = _build_spec(hint, f"`{name}`")
    spec.source = hint
    label = spec.label
    nullable = spec.accepts_none()
    strictness = (
        " Kiểm CHÍNH XÁC chứ không `isinstance`: một lớp con của `str` đổi giá "
        "trị giữa hai lần đọc, và `True` là một `int` hợp lệ."
        if spec.has_exact_scalar() else ""
    )

    def check(value: Any, owner: str) -> None:
        # KIỂU trước, MUTABLE sau: với một field khai `str` mà nhận `list`,
        # "phải là chuỗi thuần" nói đúng vấn đề hơn "giữ container mutable".
        if not spec.matches(value):
            if value is None and not nullable:
                raise error(f"`{name}` không được là None (khai {label}).")
            raise error(
                f"`{name}` phải là {label}, gặp {_value_type_name(value)} "
                f"({_render_value(value)}).{strictness}"
            )
        # C5 — MUTABLE GUARD. `issubclass(type(v), ...)` chứ không
        # `isinstance(v, ...)`: phép sau tra `v.__class__`, nên một property
        # `__class__` nổ làm lỗi thô thoát ra và một `__class__` nói dối giấu
        # được một `list` thật. Phép trước điều phối theo metaclass của VẾ PHẢI
        # (`list`/`dict`/`set`/`bytearray` — đều `type`), rơi vào
        # `PyType_IsSubtype`, vốn đọc trường C `tp_mro`; nó cũng bắt được LỚP
        # CON của container mutable, thứ phép so định danh bỏ sót.
        if issubclass(type(value), _MUTABLE_CONTAINERS):
            raise error(
                f"`{name}` giữ một container mutable ({_value_type_name(value)}). "
                "Một canonical object bất biến không được giữ alias mà người "
                "gọi còn sửa được sau khi dựng."
            )

    # Phơi cây parse ra để một test ở TẦNG TRỪU TƯỢNG đi hết được nó.
    check.__canonical_spec__ = spec  # type: ignore[attr-defined]
    return check


def _build_field_contract(cls: type, error: type) -> tuple:
    """Đọc annotation của class MỘT LẦN và dựng danh sách phép kiểm.

    KHÔNG ghi gì lên `cls`: toàn bộ phép chứng minh chạy vào giá trị trả về,
    và caller mới quyết định commit (C13).
    """
    # ── Biên lạ B1. `get_type_hints` chạy `eval` trên annotation dạng chuỗi và
    # duyệt MRO, nên nó là điểm chạm lạ đầu tiên. Bọc ĐÚNG một lời gọi.
    try:
        hints = typing.get_type_hints(cls)
    except Exception:  # noqa: BLE001 — biên lạ B1, bọc đúng một lời gọi
        raise CanonicalContractViolation(
            f"{cls.__name__}: không phân giải được annotation nên không dẫn "
            "xuất được hợp đồng field. Một canonical type mà framework không "
            "đọc nổi kiểu thì không thể tự bảo đảm gì. Lý do gốc CỐ Ý không "
            "được render: đọc `__str__` của một exception lạ chính là chạy "
            "code lạ."
        ) from None

    # ── C8 — PSEUDO-FIELD.
    #
    # `dataclasses.fields()` BỎ QUA cả `InitVar` lẫn `ClassVar`, nhưng
    # `@dataclass` vẫn TRUYỀN `InitVar` vào `__post_init__`. Nên hợp đồng field
    # không phủ được nó, còn wrapper `__post_init__(self)` của framework thì
    # sai chữ ký — đo được tại `d4a8797`: `TypeError: __post_init__() takes 1
    # positional argument but 2 were given`. `ClassVar` thì không được truyền
    # vào nên vô hại.
    declared = getattr(cls, "__dataclass_fields__", {})
    real = {fld.name for fld in _dataclass_fields(cls)}
    offenders = []
    for name in declared:
        if name in real:
            continue
        resolved = hints.get(name)
        origin = _boundary_get_origin(resolved, f"{cls.__name__}.`{name}`")
        if origin is typing.ClassVar:
            continue
        kind = ("InitVar" if type(resolved) is _dataclasses.InitVar
                else "pseudo-field không xác định")
        offenders.append(f"`{name}` ({kind})")
    if offenders:
        raise CanonicalContractViolation(
            f"{cls.__name__}: {', '.join(offenders)} — `@canonical` không hỗ "
            "trợ pseudo-field kiểu này. `dataclasses.fields()` bỏ qua chúng "
            "nên hợp đồng field không phủ được, trong khi `@dataclass` vẫn "
            "truyền chúng vào `__post_init__` — chữ ký wrapper của framework "
            "sẽ sai và constructor vỡ lúc chạy. Hãy khai thành field thường, "
            "hoặc nhận dữ liệu khởi tạo qua factory của chính type."
        )

    checks = []
    for fld in _dataclass_fields(cls):
        if fld.name not in hints:
            raise CanonicalContractViolation(
                f"{cls.__name__}.{fld.name}: thiếu annotation, nên không dẫn "
                "xuất được phép kiểm."
            )
        checks.append((fld.name, _field_checker(fld.name, hints[fld.name], error)))
    return tuple(checks)


# ─────────────────────────────────────────── Registry TỰ ĐỘNG (R1-A)
#
# Inventory viết tay là nguồn drift thứ hai mà Review R1 chỉ ra: oracle liệt kê
# 9 type trong khi 11 type mang `@canonical`, và hai type bị bỏ sót đúng là hai
# type không validate gì. Registry này do chính decorator ghi, nên không có
# danh sách nào để quên cập nhật.

_REGISTRY: list = []


def canonical_types() -> tuple:
    """Mọi type đã được `@canonical` nhận, theo thứ tự khai báo."""
    return tuple(_REGISTRY)


def sealed_canonical_types() -> tuple:
    return tuple(c for c in _REGISTRY if getattr(c, "__canonical_sealed__", False))


# ───────────────────────────────────────────────── Lớp 4: copy / deepcopy / pickle


def _rebuild_canonical(cls: type, values: dict) -> Any:
    """Tái tạo QUA constructor, nên pickle không đi vòng qua Lớp 1."""
    return cls(**values)


# ────────────────────────────────────────────────────────── decorator chính


def canonical(
    *, sealed: bool = False, field_error: type = CanonicalFieldError
) -> Callable[[type], type]:
    """Đóng một frozen dataclass thành canonical type.

    ``sealed=False`` — kiểu tự validate và FINAL, nhưng constructor vẫn công
    khai. Dùng cho những kiểu mà tính hợp lệ là **thuần cấu trúc**: đọc đủ
    field là kết luận được, không cần biết object đến từ đâu.

    ``sealed=True`` — thêm Lớp 2. Dùng cho những kiểu mà tính hợp lệ bao gồm
    **nguồn gốc**: một ``AffectedRow`` "đúng cấu trúc" nhưng trỏ vào dòng
    99999 của một file không tồn tại vẫn là provenance bịa, và không field nào
    diễn đạt được điều đó.

    **Hợp đồng bắt buộc (R1-A).** Decorator từ chối class nếu:

    * không phải ``@dataclass(frozen=True)``;
    * không khai ``__post_init__`` (của chính nó hoặc thừa kế từ một canonical
      base) — bất biến ngữ nghĩa framework không suy ra được, nên "quên nghĩ
      về invariant" phải nổ lúc import chứ không nằm im;
    * có field không phân giải được annotation.

    Và nó **tự cài** phép kiểm field dẫn xuất từ annotation cho MỌI canonical
    type. Nhờ vậy một canonical type mới được bảo vệ đầy đủ mà tác giả không
    phải nhớ gì; ``__post_init__`` chỉ còn lo phần ngữ nghĩa.

    ``field_error`` — lớp ngoại lệ cho vi phạm field. Mặc định
    ``CanonicalFieldError``. Master data khai ``InvalidEmployeeConfig``: lằn
    ranh "công cụ hỏng" ≠ "dữ liệu giao dịch xấu" (HD-110-09) là một quyết
    định nghiệp vụ, nên nó phải giữ được từ vựng lỗi của chính nó.
    """

    def decorate(cls: type) -> type:
        # ── C9 — CỔNG METACLASS, câu lệnh ĐẦU TIÊN, trước mọi phép đọc và mọi
        # phép ghi lên class.
        #
        # Với `type(cls) is type`, mọi `getattr`/`setattr` lên class đi qua
        # `type.__getattribute__`/`type.__setattr__` ở tầng C và không chạy
        # code của người dùng. Không có cổng này, một metaclass khai
        # `__setattr__` raise giữa chừng làm lỗi thô thoát ra VÀ để lại class
        # nửa vời — đo được tại `1b0da151`: `__canonical_contract__` đã ghi
        # trong khi `__post_init__` chưa bọc. Rollback không cứu được (bản thân
        # rollback cũng gọi `setattr`), nên đường đóng là TỪ CHỐI TỪ ĐẦU.
        # Production: cả 11 canonical type đều có `type(cls) is type`.
        if type(cls) is not type:
            raise CanonicalContractViolation(
                "@canonical: class có metaclass tuỳ biến, không phải `type` — "
                "UNSUPPORTED. Framework phải ghi thuộc tính lên class để cài "
                "hợp đồng, và với metaclass tuỳ biến thao tác ghi ấy chạy code "
                "do người dùng định nghĩa: một `__setattr__` nổ giữa chừng để "
                "lại một canonical type nửa vời. Hãy khai một dataclass thường."
            )

        params = getattr(cls, "__dataclass_params__", None)
        if params is None or not params.frozen:
            raise TypeError(
                f"@canonical yêu cầu @dataclass(frozen=True): {cls.__name__} "
                "không phải frozen dataclass."
            )

        home = cls.__module__
        label = cls.__name__

        # ── Hợp đồng R1-A #1: phải có validator ngữ nghĩa được khai tường minh.
        if not hasattr(cls, "__post_init__"):
            raise CanonicalContractViolation(
                f"{label} mang @canonical nhưng không khai `__post_init__`. "
                "Framework tự kiểm được KIỂU của từng field (dẫn từ annotation) "
                "nhưng KHÔNG suy ra được bất biến ngữ nghĩa — `start <= end`, "
                "`status` thuộc enum nào, `record` phải nhất quán với `status`. "
                "Nếu type này thật sự không có bất biến ngữ nghĩa nào, hãy khai "
                "`def __post_init__(self) -> None:` với thân rỗng và một câu giải "
                "thích: một dòng nhìn thấy được trong code review, thay cho một "
                "khoảng lặng. Đây là finding R1-A của Independent Review R1."
            )

        # ══════════════════════ C13, PHA 1 — TÍNH. Không ghi gì lên `cls`.
        #
        # Toàn bộ phép chứng minh — phân giải annotation, phân loại từng field
        # theo ngữ pháp đóng, dựng mọi closure — chạy vào biến CỤC BỘ. Một
        # decoration thất bại vì thế để lại class NGUYÊN VẸN và registry KHÔNG
        # ĐỔI: không có canonical type nào tồn tại ở trạng thái nửa vời.
        contract = _build_field_contract(cls, field_error)

        user_post_init = cls.__post_init__
        # Một canonical subclass KHÔNG khai `__post_init__` riêng sẽ thừa kế
        # bản ĐÃ BỌC của lớp cha. Bọc chồng lên nó là chạy hai lần pha ép kiểu
        # và hai lần hợp đồng. Gỡ về hàm gốc của tác giả: phần ngữ nghĩa của
        # lớp cha vẫn chạy, còn hợp đồng của lớp con đã phủ mọi field (kể cả
        # field thừa kế).
        while getattr(user_post_init, "__canonical_wrapper__", False):
            user_post_init = user_post_init.__wrapped__

        @functools.wraps(user_post_init)
        def _canonical_post_init(self: Any) -> None:
            """Ba pha, đúng thứ tự này và framework giữ thứ tự đó:

            1. **ép kiểu** (`__canonical_coerce__`, nếu type khai) — biên nhận
               dữ liệu dòng giao dịch phải ÉP chứ không nổ (§18 đặc tả: một
               dòng thô méo mó không được làm gãy cả lượt import);
            2. **hợp đồng field** — khẳng định kiểu và tính bất biến của trạng
               thái SAU khi ép;
            3. **bất biến ngữ nghĩa** (`__post_init__` của chính type).

            Thứ tự này là điều khiến pha 3 được phép GIẢ ĐỊNH kiểu đã đúng.
            Trước R1-A, `RecordRef.__post_init__` chạy trên dữ liệu chưa kiểm
            nên `RecordRef(sid, "0", "x")` nổ `TypeError: '<' not supported
            between instances of 'str' and 'int'` — một lỗi của trình thông
            dịch rò ra từ bên trong validator, không phải một lỗi domain.
            """
            coerce = getattr(type(self), "__canonical_coerce__", None)
            if coerce is not None:
                coerce(self)
            owner = type(self).__name__
            for name, check in type(self).__canonical_contract__:
                check(getattr(self, name), owner)
            user_post_init(self)

        _canonical_post_init.__canonical_wrapper__ = True  # type: ignore[attr-defined]

        # ── Lớp 3: final ngoài module chủ.
        def _reject_subclass(subcls: type, **kwargs: Any) -> None:
            if subcls.__module__ != home:
                raise CanonicalSubclassRejected(
                    f"{label} là canonical type và không kế thừa được từ "
                    f"{subcls.__module__!r}. Một subclass ghi đè "
                    "`__post_init__` là xoá toàn bộ phép validate trong khi "
                    "`isinstance()` vẫn trả True — đúng bypass mà Independent "
                    "Review #8 đã đo được."
                )
            if "__new__" in subcls.__dict__:
                raise CanonicalSubclassRejected(
                    f"{subcls.__name__} không được tự định nghĩa `__new__`: đó "
                    f"là cổng dựng của {label}."
                )

        # ── Lớp 2: constructor công khai LUÔN từ chối (chỉ với sealed).
        def _sealed_new(newcls: type, *args: Any, **kwargs: Any) -> Any:
            if not _is_permitted(newcls):
                raise SealedConstruction(
                    f"{newcls.__name__} chỉ dựng được qua factory của chính "
                    "nó. Không có tham số nào bật được đường này: seal "
                    "không còn là field, nên không đọc lại, không sao chép "
                    "và không truyền vào được (R1). `dataclasses.replace()` "
                    "cũng đi qua đây."
                )
            return object.__new__(newcls)

        def _no_pickle(self: Any) -> Any:
            raise SealedConstruction(
                f"{type(self).__name__} không pickle được: tính hợp lệ của "
                "nó bao gồm nguồn gốc, mà nguồn gốc thì không hồi sinh "
                "được từ byte."
            )

        def _reduce(self: Any) -> Any:
            return (
                _rebuild_canonical,
                (
                    type(self),
                    {f.name: getattr(self, f.name) for f in _dataclass_fields(self)},
                ),
            )

        # ══════════════════════ C13, PHA 2 — GHI. Mọi phép chứng minh đã xong.
        cls.__canonical_contract__ = contract  # type: ignore[attr-defined]
        cls.__post_init__ = _canonical_post_init  # type: ignore[assignment]
        cls.__init_subclass__ = classmethod(_reject_subclass)  # type: ignore[assignment]
        if sealed:
            cls.__new__ = staticmethod(_sealed_new)  # type: ignore[assignment]
            cls.__reduce__ = _no_pickle  # type: ignore[assignment]
        else:
            cls.__reduce__ = _reduce  # type: ignore[assignment]
        # Value object bất biến: bản sao của nó chính là nó. Điều này cũng đóng
        # đường "deepcopy rồi sửa bản sao".
        cls.__copy__ = lambda self: self  # type: ignore[assignment]
        cls.__deepcopy__ = lambda self, memo: self  # type: ignore[assignment]
        cls.__canonical__ = True  # type: ignore[attr-defined]
        cls.__canonical_sealed__ = sealed  # type: ignore[attr-defined]

        # Tên hiển thị được chốt Ở ĐÂY, từ một class mà cổng C9 đã chứng minh
        # có metaclass `type` — nên `label` là metadata do framework tự đọc từ
        # trusted source, không phải một chuỗi do object lạ cấp lúc dựng thông
        # báo lỗi. Nhờ vậy `_ClassSpec.label` không bao giờ phải gọi
        # `__name__` của một target chưa được bless.
        _CLASS_LABEL_PAIRS.append((cls, f"`{label}`"))
        _VALUE_TYPE_NAME_PAIRS.append((cls, label))
        _REGISTRY.append(cls)
        return cls

    return decorate


# ────────────────────────────────────── Lớp 1: container bất biến THẬT SỰ


class FrozenMapping(Mapping):
    """Mapping chỉ-đọc cho field của canonical object.

    ``frozen=True`` chỉ cấm gán lại thuộc tính; nó KHÔNG cấm sửa đối tượng mà
    thuộc tính đó trỏ tới. Một sealed dataclass giữ ``dict``/``Counter`` vì thế
    vẫn sửa được từ bên ngoài — Review #8 gọi đúng tên: *sealed dataclass có
    thể giữ mutable alias*.

    Dữ liệu được SAO CHÉP vào một ``MappingProxyType``, nên ngay cả khi thò tay
    vào ``._data`` cũng không ghi được, và alias của caller không còn đường
    chạm tới nội dung.
    """

    __slots__ = ("_data",)

    def __init__(self, data: Any = ()) -> None:
        object.__setattr__(self, "_data", MappingProxyType(dict(data)))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} là bất biến")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"{type(self).__name__} là bất biến")

    def __getitem__(self, key: Any) -> Any:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: Any) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return f"{type(self).__name__}({dict(self._data)!r})"


class FrozenCounter(FrozenMapping):
    """``FrozenMapping`` mang đúng ngữ nghĩa đọc của ``collections.Counter``.

    Giữ nguyên hai hành vi mà consumer đang dựa vào — khoá vắng mặt trả ``0``,
    và ``most_common()`` sắp đúng thứ tự ``Counter`` cho (kể cả cách xử lý
    hoà). ``tools/analysis/reconcile_conversion.py`` in ra từ chính hai hàm
    này và output của nó là bằng chứng đã ký của CHECK-108A1-15
    (CHECK-110-14), nên thứ tự phải khớp từng dòng.
    """

    __slots__ = ()

    def __getitem__(self, key: Any) -> Any:
        return self._data.get(key, 0)

    def most_common(self, n: Optional[int] = None) -> list:
        ordered = sorted(self._data.items(), key=itemgetter(1), reverse=True)
        return ordered if n is None else ordered[:n]


# ── C3, category thứ ba: class do chính framework sở hữu.
#
# Hai class này là toàn bộ `_FROZEN_FRAMEWORK`. Chúng vào allowlist bằng ĐỊNH
# DANH, và phép kiểm runtime của chúng là `type(v) is FrozenMapping` /
# `type(v) is FrozenCounter` — nên metaclass `ABCMeta` mà chúng thừa hưởng từ
# `collections.abc.Mapping` KHÔNG tham gia phép kiểm nào. Đo tại `1b0da151`:
# field khai `FrozenMapping` chưa bao giờ nhận một `FrozenCounter` (593 lần
# gặp, không lần nào), nên phép kiểm chính xác không siết oan chỗ nào.
_FROZEN_FRAMEWORK.extend((FrozenMapping, FrozenCounter))
_CLASS_LABEL_PAIRS.extend((
    (FrozenMapping, "`FrozenMapping`"),
    (FrozenCounter, "`FrozenCounter`"),
))
_VALUE_TYPE_NAME_PAIRS.extend((
    (FrozenMapping, "FrozenMapping"),
    (FrozenCounter, "FrozenCounter"),
))


def frozen_tuple_map(data: Any) -> FrozenMapping:
    """``FrozenMapping`` mà mọi value cũng đã đóng băng thành tuple."""
    return FrozenMapping({key: tuple(value) for key, value in dict(data).items()})


def as_exact_str(value: Any) -> str:
    """Ép về ``str`` THUẦN, không raise.

    Một lớp con của ``str`` với ``__str__`` đổi theo lần gọi qua được mọi
    ``isinstance`` và làm cùng một field trả hai giá trị khác nhau giữa hai lần
    đọc (Audit P4). Nên phép kiểm là ``type(...) is str``, không phải
    ``isinstance``.

    **Ép chứ không raise, có chủ đích.** Những field dùng hàm này mang dữ liệu
    của một DÒNG GIAO DỊCH. §18 đặc tả cấm một dòng thô méo mó làm gãy cả lượt
    import — nó phải vào Review Queue. Đây là cùng quy tắc mà ``Diagnostics``
    đã áp dụng từ DEC-133; hàm này chỉ đặt cho nó một cái tên.
    """
    return value if type(value) is str else str(value)


def as_exact_date(value: Any, where: str):
    """Ép về ``datetime.date`` thuần; ``datetime`` bị hạ xuống ``date``.

    Cùng lý do như trên: đây là dữ liệu dòng giao dịch. ``raw_reader._to_date``
    đã chuẩn hoá ở biên đọc, nên hàm này chỉ raise khi gặp thứ không phải ngày
    — tức là một lỗi lập trình, không phải một dòng xấu.
    """
    if isinstance(value, _datetime):
        return value.date()
    if type(value) is date:
        return value
    if isinstance(value, date):
        return date(value.year, value.month, value.day)
    raise TypeError(
        f"{where} phải là `datetime.date` hoặc None, gặp "
        f"{type(value).__name__} ({value!r})."
    )


__all__ = [
    "CanonicalContractViolation",
    "CanonicalFieldError",
    "CanonicalSubclassRejected",
    "FrozenCounter",
    "FrozenMapping",
    "SealedConstruction",
    "as_exact_date",
    "as_exact_str",
    "canonical",
    "canonical_types",
    "factory_for",
    "frozen_class_allowlist",
    "frozen_tuple_map",
    "sealed_canonical_types",
]
