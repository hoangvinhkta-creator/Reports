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

import collections.abc as _cabc
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
from typing import Any, Callable, Literal, Optional, TypeVar


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


# ────────────────────── Lớp 1b: hợp đồng field DẪN XUẤT TỪ ANNOTATION (R1-A)
#
# Independent Review R1 falsify được rằng `@canonical` chỉ ĐÁNH DẤU chứ không
# BẢO ĐẢM: `RecordRef` và `MappingResult` mang decorator mà không có một phép
# kiểm nào, nên `RecordRef(snapshot_id, -1, "forged")` dựng được và
# `master.record(ref)` im lặng chọn employee CUỐI (Python negative index).
#
# Cách đóng không phải là viết thêm `__post_init__` cho hai type đó rồi coi là
# xong — lần sau sẽ có type thứ ba. Cách đóng là để **framework tự sinh phép
# kiểm field từ annotation mà type đã khai**. Annotation vốn đã có, đã được
# đọc khi review, và không ai quên viết nó — nên nó là nguồn duy nhất đáng tin
# để dẫn xuất hợp đồng.
#
# Ngữ nghĩa kiểm:
#   Any               không kiểm kiểu (nhưng vẫn cấm container mutable)
#   Optional[X]       None hoặc X
#   builtin vô hướng  KIỂU CHÍNH XÁC (`type(v) is X`) — một lớp con của `str`
#                     với `__str__` đổi theo lần gọi qua được mọi `isinstance`,
#                     và `True` qua được mọi phép kiểm `int`
#   class khác        `isinstance` — kế thừa ngoài module chủ đã bị Lớp 3 cấm,
#                     nên subclass hợp lệ (AmbiguousRow) vẫn dùng được
#   MỌI field         không được là container mutable (list/dict/set/bytearray)
#
# Bất biến NGỮ NGHĨA (`start <= end`, `status` thuộc enum nào, phần tử bên
# trong một tuple) framework
# không suy ra được, nên chúng vẫn ở `__post_init__` — và `@canonical` BẮT
# BUỘC mọi type phải khai `__post_init__`, để "quên nghĩ về invariant" nổ lúc
# import chứ không nằm im.

# Kiểu vô hướng dựng sẵn: đây là bề mặt tấn công bằng lớp con, nên kiểm CHÍNH
# XÁC. `bool` là lớp con của `int`, nên `type(v) is int` cũng loại luôn `True`.
_EXACT_TYPES = (str, int, bool, float, bytes, complex, date)

# Tên tiếng Việt của kiểu, dùng trong thông báo. Giữ đúng từ mà các thông báo
# master data đã dùng từ trước ("chuỗi thuần", "boolean") để chúng vẫn là cùng
# một câu chuyện với người đọc, và để bằng chứng cũ còn khớp.
_TYPE_NAMES = {
    str: "chuỗi thuần",
    bool: "boolean",
    int: "số nguyên thuần",
    float: "số thực thuần",
    bytes: "bytes thuần",
    date: "ngày (`datetime.date`) thuần",
}

# Container mutable: cấm ở MỌI field, bất kể annotation. `frozen=True` chỉ cấm
# gán lại thuộc tính, không cấm sửa đối tượng nó trỏ tới.
_MUTABLE_CONTAINERS = (list, dict, set, bytearray)

# Dạng CẶP của `_TYPE_NAMES`, để tra bằng `is` thay vì `dict.get()` (vốn gọi
# `hash()` của metaclass lạ).
_TYPE_NAME_PAIRS = tuple(_TYPE_NAMES.items())


# ── NGỮ PHÁP ANNOTATION ĐÓNG (R1-A1)
#
# Independent Review R1-A Finding #1: `_field_checker()` chỉ hiểu một tập con
# rất hẹp của `typing`, và mọi thứ ngoài tập đó ÂM THẦM rơi xuống đường không
# kiểm. Đo được tại `dead82e`: `Union[int, str]` nhận `1.5`; `Literal["a","b"]`
# nhận `"c"`; TypeVar có ràng buộc nhận mọi thứ; còn `str | None` (PEP 604) thì
# LOẠI cả giá trị hợp lệ vì nó bị đem đi `isinstance(value, types.UnionType)`.
#
# Root cause không phải thiếu năm nhánh `if`. Root cause là **nhánh cuối cùng
# của phép phân tích annotation là "bỏ qua"**. Một trình phân tích mà trường
# hợp mặc định là im lặng thì mọi annotation nó chưa gặp đều là một lỗ hổng
# chưa được phát hiện — và danh sách annotation Python sẽ còn dài ra.
#
# Cách đóng: phân tích annotation bằng **đệ quy xuống một ngữ pháp ĐÓNG**, và
# nhánh cuối cùng là `raise`, không phải `return`. Bất biến:
#
#     UNKNOWN ≠ ANY.
#
# Một annotation hoặc nằm trong ngữ pháp và được validate ĐỦ ngữ nghĩa, hoặc
# nổ `CanonicalContractViolation` NGAY LÚC IMPORT. Không có ô thứ ba.
#
# Ngữ pháp (cố ý nhỏ — production chỉ dùng ba hình thái đầu):
#
#     spec    := Any | none | atom | union | literal
#     none    := None | NoneType                (chỉ `None` hợp lệ)
#     atom    := <lớp cụ thể>                   builtin vô hướng -> kiểu CHÍNH XÁC
#                                               lớp khác        -> `isinstance`
#                <generic có tham số>           kiểm theo `origin`, phần tử KHÔNG
#                                               kiểm (đó là R1-D)
#     union   := Union[s1..sn] | s1 | .. | sn   khớp ÍT NHẤT MỘT nhánh
#     literal := Literal[v1..vn]                bằng VÀ đúng kiểu chính xác
#
# Ngoài ngữ pháp -> UNSUPPORTED, nổ lúc decorate. Hiện gồm: `TypeVar` (canonical
# dataclass không generic; đỡ `TypeVar` đúng nghĩa là phải mô hình hoá binding
# và variance — một trình kiểm kiểu thu nhỏ mà production không cần),
# `Final[...]`, và mọi special form khác chưa được mô hình hoá.


_NONE_TYPE = type(None)
_UNION_TYPE = getattr(_types, "UnionType", None)

# ─────────────────────────── R1-A1 #3: PHÂN LOẠI KHÔNG HỎI OBJECT LẠ
#
# Independent Review R1-A1 #2 chỉ ra rằng "chứng minh bằng hai phép thử
# `isinstance`" không phải một phép chứng minh: một metaclass đổi hành vi theo
# GIÁ TRỊ sẽ qua được hai phép thử rồi nổ với dữ liệu thật. Tệ hơn, chính việc
# tra chính sách (`target in frozenset(...)`) đã gọi `__hash__` của metaclass
# lạ TRƯỚC khi target được coi là an toàn — nên một `__hash__` nổ làm lỗi thô
# thoát ra ngay lúc decorate.
#
# Nguyên tắc thay thế: **phân loại bằng CẤU TRÚC framework tự biết, không bằng
# cách chạy code của người khác.** Cụ thể, trong toàn bộ đường phân loại:
#
#   * không `hash(target)`      -> mọi phép tra tập hợp dùng `is`, không `in`;
#   * không `target == x`       -> như trên;
#   * không `isinstance(v, target)` để "chứng minh" -> thay bằng luật metaclass.
#
# `isinstance(target, type)` và `type(target)` vẫn dùng được: cả hai đi qua
# `type.__instancecheck__` ở tầng C, không chạm code người dùng.

# Metaclass là `type` -> `isinstance()` là phép duyệt MRO ở tầng C, tất định và
# không chạy code nào của người dùng. Đây là điều kiện đủ mà framework tin được
# mà không phải chạy thử gì.
#
# Metaclass khác (`ABCMeta`, `EnumMeta`, `_ProtocolMeta`, metaclass tự viết)
# đều có thể chạy hook do người dùng định nghĩa (`__subclasshook__`,
# `__instancecheck__`). Chúng bị TỪ CHỐI, trừ đúng những class mà framework tự
# sở hữu và tự biết ngữ nghĩa — danh sách dưới đây, so bằng ĐỊNH DANH.
_TRUSTED_NON_TYPE_METACLASS_CLASSES: list = []  # điền sau khi định nghĩa xong

# Giới hạn độ phức tạp: parser đệ quy KHÔNG được để `RecursionError` của CPython
# làm chính sách. Production sâu nhất 2 tầng; 24 là dư thừa gấp hơn mười lần.
_MAX_ANNOTATION_DEPTH = 24
_MAX_ANNOTATION_NODES = 512

# ── CHÍNH SÁCH R1-A1 #2: họ `Callable` bị từ chối TOÀN BỘ.
#
# `get_args(Callable[[A, B], R])` trả `([A, B], R)` — phần tử đầu là một
# **list**, không phải một kiểu; `Callable[..., R]` trả `(Ellipsis, R)`. Hình
# dạng đó không giống bất kỳ generic nào khác, nên mô hình hoá nó tử tế là một
# nhánh ngữ pháp riêng mà production không dùng tới. Từ chối cả họ (trần lẫn có
# tham số) là kết quả HỢP LỆ và tốt hơn hỗ trợ nửa vời (Review R1-A1 #2, §4).
_UNSUPPORTED_ORIGINS = (_cabc.Callable,)

# ── CHÍNH SÁCH R1-A1 #2: class CHỈ DÙNG ĐỂ CHÚ THÍCH.
#
# Những class này qua được `isinstance(target, type)` VÀ qua được cả phép thử
# `isinstance()` (không nổ) — nhưng chúng trả `False` cho MỌI object thật, nên
# một field khai kiểu đó sẽ loại sạch giá trị hợp lệ. Không phép thử runtime
# nào phát hiện được điều đó, nên đây là một chính sách được TUYÊN BỐ, có test
# canh, chứ không phải một suy đoán.
_ANNOTATION_ONLY_CLASSES = (
    typing.IO, typing.TextIO, typing.BinaryIO, typing.Generic, typing.Protocol,
)

# `_INSTANCECHECK_PROBES` đã bị XOÁ ở R1-A1 #3: chạy `isinstance()` với vài giá
# trị mẫu không chứng minh được gì về một `__instancecheck__` đổi hành vi theo
# giá trị. Xem `_classify_class_target()`.

# Giá trị được phép xuất hiện trong `Literal[...]` (PEP 586 giới hạn tương tự).
_LITERAL_VALUE_TYPES = (str, int, bool, bytes, _NONE_TYPE)


class _Spec:
    """Một NÚT của cây annotation đã parse.

    `source` là annotation gốc sinh ra nút này, `children()` là các nút con.
    Hai thứ đó biến cây parse thành một **biểu diễn kiểm chứng được**: một test
    ở tầng trừu tượng đi hết cây và so số con với số tham số kiểu của
    `source`, nên "thêm một generic mới rồi hậu duệ của nó biến mất" là điều
    KHÔNG lặng lẽ xảy ra được nữa (Review R1-A1 #2, §9).

    `matches` trả bool; `label` để render thông báo.
    """

    __slots__ = ("label", "source")

    def matches(self, value: Any) -> bool:  # pragma: no cover - giao diện
        raise NotImplementedError

    def children(self) -> tuple:
        """Các nút con đã parse. Rỗng với nút lá."""
        return ()

    def accepts_none(self) -> bool:
        return self.matches(None)

    def has_exact_scalar(self) -> bool:
        """Có nhánh nào kiểm KIỂU CHÍNH XÁC không — quyết định thông báo có kèm
        câu giải thích về `str` subclass / `True` là `int` hay không."""
        return False

    def uninhabited_label(self) -> Optional[str]:
        """Nhãn của vị trí ĐẦU TIÊN không bao giờ khớp được giá trị nào.

        Dùng cho thông báo: với union, thủ phạm là một NHÁNH, và chỉ đúng
        nhánh đó mới nên bị nêu tên.
        """
        return None if self.is_inhabited() else self.label

    def is_inhabited(self) -> bool:
        """Hợp đồng này có ÍT NHẤT MỘT giá trị hợp lệ không?

        `list[int]` từng được gọi SUPPORTED trong khi chính sách bất biến loại
        MỌI instance của nó — "hỗ trợ" một hợp đồng rỗng là tự mâu thuẫn
        (R1-A1 #3, finding #3). Mặc định True; chỉ `_ClassSpec` và `_UnionSpec`
        có gì để nói.
        """
        return True


class _AnySpec(_Spec):
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
    """Một lớp cụ thể. Builtin vô hướng kiểm CHÍNH XÁC, còn lại `isinstance`.

    `args` là các nút con ĐÃ PARSE của một generic có tham số
    (`tuple[int, ...]` -> một con `int`). Chúng **không** được kiểm lúc chạy:
    `matches()` chỉ khẳng định container ngoài cùng. Đó là ranh giới cố ý giữa
    hai việc khác nhau —

        PARSE ANNOTATION   (R1-A1): mọi nút trong cây phải được phân loại;
        RUNTIME VALIDATION (R1-D) : có kiểm từng phần tử hay không.

    R1-A1 chỉ đòi cái thứ nhất. Trước bản này `get_args()` bị VỨT BỎ hẳn, nên
    `tuple[<TypeVar>]` decorate lọt — hậu duệ không hỗ trợ biến mất.
    """

    __slots__ = ("_target", "_exact", "_args")

    def __init__(self, target: type, args: tuple = ()) -> None:
        self._target = target
        # Tra bằng ĐỊNH DANH, không `in`/`get`: cả hai đều gọi `__hash__`/
        # `__eq__` của metaclass. Ở đây target đã qua `_classify_class_target()`
        # nên vốn đã an toàn, nhưng giữ một luật duy nhất cho cả đường class thì
        # dễ phát biểu và dễ canh hơn (R1-A1 #3, §4).
        self._exact = _is_one_of(target, _EXACT_TYPES)
        self._args = args
        label = None
        for candidate, name in _TYPE_NAME_PAIRS:
            if target is candidate:
                label = name
                break
        self.label = label if label is not None else f"`{_safe_name(target)}`"

    def children(self) -> tuple:
        return self._args

    def is_inhabited(self) -> bool:
        # Mọi instance của một container mutable đều bị chính sách bất biến
        # loại, nên field khai kiểu đó không có giá trị hợp lệ nào. `issubclass`
        # ở đây an toàn: nó điều phối theo metaclass của VẾ PHẢI (`list`/`dict`/
        # `set`/`bytearray` — đều `type`), không theo metaclass của target.
        return not issubclass(self._target, _MUTABLE_CONTAINERS)

    def matches(self, value: Any) -> bool:
        if self._exact:
            return type(value) is self._target
        return isinstance(value, self._target)

    def has_exact_scalar(self) -> bool:
        return self._exact


class _LiteralSpec(_Spec):
    """`Literal[...]`: bằng giá trị VÀ đúng kiểu chính xác.

    Kiểm kiểu chính xác là bắt buộc, không phải tinh chỉnh: `True == 1` trong
    Python, nên nếu chỉ so bằng thì `Literal[1]` sẽ nhận `True`.
    """

    __slots__ = ("_values",)

    def __init__(self, values: tuple) -> None:
        self._values = values
        self.label = "một trong " + ", ".join(repr(v) for v in values)

    def matches(self, value: Any) -> bool:
        return any(
            type(value) is type(allowed) and value == allowed
            for allowed in self._values
        )


class _UnionSpec(_Spec):
    """Khớp ít nhất một nhánh. `Optional[X]` chính là `Union[X, None]`."""

    __slots__ = ("_branches",)

    def __init__(self, branches: tuple) -> None:
        self._branches = branches
        self.label = " hoặc ".join(b.label for b in branches)

    def children(self) -> tuple:
        return self._branches

    def is_inhabited(self) -> bool:
        # MỌI nhánh, không phải "có một nhánh". Đây là luật NGHIÊM HƠN mức tối
        # thiểu mà bất biến đòi, và cố ý: một nhánh union không bao giờ khớp
        # được giá trị nào là một lời khai SAI LỆCH — `Optional[list[int]]` nói
        # "None hoặc một list" trong khi mọi list đều bị chính sách bất biến
        # loại. Luật phát biểu gọn: KHÔNG vị trí nào mà checker thực sự đánh giá
        # được phép trỏ tới một class chính sách đã cấm.
        #
        # Tham số của generic KHÔNG thuộc diện này: chúng chỉ được PARSE, không
        # được kiểm lúc chạy — đó là ranh giới R1-D.
        return all(branch.is_inhabited() for branch in self._branches)

    def uninhabited_label(self) -> Optional[str]:
        for branch in self._branches:
            dead = branch.uninhabited_label()
            if dead is not None:
                return dead
        return None

    def matches(self, value: Any) -> bool:
        return any(branch.matches(value) for branch in self._branches)

    def has_exact_scalar(self) -> bool:
        return any(branch.has_exact_scalar() for branch in self._branches)


def _safe_name(obj: Any) -> str:
    """Tên để render, KHÔNG bao giờ nổ.

    `__name__` và `__repr__` của một annotation lạ là code của người khác. Đọc
    chúng để dựng thông báo lỗi mà lại nổ thì thông báo lỗi trở thành một
    đường rò mới.
    """
    try:
        name = getattr(obj, "__name__", None)
        if type(name) is str:
            return name
    except Exception:  # noqa: BLE001
        pass
    try:
        return repr(obj)[:80]
    except Exception:  # noqa: BLE001
        return f"<annotation {type(obj).__name__} không repr được>"


def _foreign(call: Callable[[], Any], where: str, what: str) -> Any:
    """Gọi MỘT thao tác chạm vào object lạ, và biến mọi lỗi của nó thành
    `CanonicalContractViolation`.

    Cố ý HẸP: nó bọc đúng một lời gọi, không bọc cả parser. Nhờ vậy lỗi lập
    trình BÊN TRONG framework vẫn nổ nguyên hình, còn tương tác với annotation
    của người khác thì luôn ra một lỗi domain (R1-A1 #3, §8).
    """
    try:
        return call()
    except CanonicalContractViolation:
        raise
    except Exception as exc:  # noqa: BLE001
        raise CanonicalContractViolation(
            f"{where}: không đọc được {what} của annotation "
            f"({type(exc).__name__}: {str(exc)[:60]}). Một annotation mà "
            "framework không khảo sát nổi thì không thể được coi là hỗ trợ."
        ) from exc


def _is_one_of(target: Any, candidates) -> bool:
    """So bằng ĐỊNH DANH, không bằng `==` và không qua `hash()`.

    `target in <frozenset>` gọi `__hash__` của metaclass lạ TRƯỚC khi target
    được chứng minh an toàn — đúng finding #2 của Independent Review. `is`
    không chạm vào code nào.
    """
    return any(target is candidate for candidate in candidates)


def _classify_class_target(target: type, where: str) -> None:
    """Chứng minh CẤU TRÚC rằng `isinstance()` với `target` là an toàn.

    Không chạy `isinstance()` thử. Luật:

    * metaclass là ĐÚNG `type` -> `isinstance()` là phép duyệt MRO ở tầng C,
      tất định, không chạy code người dùng. Đủ để tin.
    * ngược lại -> chỉ chấp nhận nếu class nằm trong danh sách framework TỰ SỞ
      HỮU (so bằng định danh). `ABCMeta`, `EnumMeta`, `_ProtocolMeta` và mọi
      metaclass tự viết đều có thể chạy hook do người dùng định nghĩa
      (`__subclasshook__`, `__instancecheck__`), nên không chứng minh được.

    Mặc định là TỪ CHỐI.
    """
    if _is_one_of(target, _UNSUPPORTED_ORIGINS):
        raise CanonicalContractViolation(
            f"{where}: họ `{_safe_name(target)}` chưa được hỗ trợ, kể cả dạng "
            "trần. Hình dạng tham số của nó (`([A, B], R)` — phần tử đầu là "
            "một list, hoặc `Ellipsis`) không giống bất kỳ generic nào khác, "
            "nên hỗ trợ nửa vời sẽ tệ hơn từ chối rõ ràng."
        )
    if _is_one_of(target, _ANNOTATION_ONLY_CLASSES):
        raise CanonicalContractViolation(
            f"{where}: `{_safe_name(target)}` là class CHỈ DÙNG ĐỂ CHÚ THÍCH. "
            "Nó trả `False` cho mọi object thật, nên một field khai kiểu này "
            "sẽ loại sạch giá trị hợp lệ. Hãy khai lớp cụ thể mà giá trị thật "
            "sự thuộc về (ví dụ `io.TextIOBase` thay cho `typing.TextIO`)."
        )
    if type(target) is type:
        return
    if _is_one_of(target, _TRUSTED_NON_TYPE_METACLASS_CLASSES):
        return
    raise CanonicalContractViolation(
        f"{where}: `{_safe_name(target)}` có metaclass "
        f"`{_safe_name(type(target))}`, không phải `type`. Chiến lược kiểm "
        "runtime của canonical là `isinstance()`, mà với metaclass tuỳ biến "
        "`isinstance()` chạy hook do người dùng định nghĩa "
        "(`__instancecheck__`, `__subclasshook__`) — framework không chứng "
        "minh được nó tất định, và CHẠY THỬ vài giá trị không phải một phép "
        "chứng minh: một hook đổi hành vi theo giá trị sẽ qua được phép thử "
        "rồi nổ với dữ liệu thật (R1-A1 #3, finding #1). Hãy khai một class "
        "thường."
    )


class _Budget:
    """Ngân sách độ phức tạp của MỘT lần parse annotation.

    Parser đệ quy không được để `RecursionError` của CPython làm chính sách:
    nó phụ thuộc stack còn lại, nên cùng một annotation có thể lúc parse được
    lúc không. Ngân sách này tất định (R1-A1 #3, §7).
    """

    __slots__ = ("nodes",)

    def __init__(self) -> None:
        self.nodes = 0

    def spend(self, where: str, depth: int) -> None:
        if depth > _MAX_ANNOTATION_DEPTH:
            raise CanonicalContractViolation(
                f"{where}: annotation lồng sâu quá {_MAX_ANNOTATION_DEPTH} "
                "tầng. Đây là một giới hạn TẤT ĐỊNH của framework, không phải "
                "`RecursionError` của CPython — cùng một annotation phải luôn "
                "cho cùng một kết quả. Canonical type của dự án này sâu nhất "
                "hai tầng."
            )
        self.nodes += 1
        if self.nodes > _MAX_ANNOTATION_NODES:
            raise CanonicalContractViolation(
                f"{where}: annotation có hơn {_MAX_ANNOTATION_NODES} nút. "
                "Một canonical field không cần tới mức đó; giới hạn này chặn "
                "cả trục BỀ RỘNG (union khổng lồ), thứ không nổ "
                "`RecursionError` nhưng vẫn là độ phức tạp không kiểm soát."
            )


def _parse_generic_args(target: Any, args: tuple, where: str,
                        budget: "_Budget", depth: int) -> tuple:
    """Parse MỌI tham số kiểu của một generic thành nút con.

    Không tham số nào được bỏ qua im lặng. Một phần tử không parse được — một
    `list` (hình dạng tham số của `Callable`), một `Ellipsis` đứng sai chỗ, một
    `ParamSpec`, một `Unpack` — rơi vào nhánh `raise` cuối của `_build_spec()`.

    Ngoại lệ ngữ pháp DUY NHẤT: `tuple[X, ...]`. Ở đó `Ellipsis` là cú pháp của
    chính Python cho "tuple đồng nhất, độ dài bất kỳ", không phải một kiểu.
    """
    if target is tuple and len(args) == 2 and args[1] is Ellipsis:
        return (_build_spec(args[0], f"{where}[0]", budget, depth),)
    return tuple(
        _build_spec(arg, f"{where}[{i}]", budget, depth)
        for i, arg in enumerate(args)
    )


def _build_spec(hint: Any, where: str, budget: "_Budget" = None,
                depth: int = 0) -> _Spec:
    """Đệ quy xuống ngữ pháp đóng. Nhánh cuối là `raise`, KHÔNG phải `return`.

    "Đóng" ở đây là đóng THEO CẢ CHIỀU SÂU: mọi nút con của mọi nút đều phải
    được phân loại. Bản trước đóng đúng ở tầng ngoài cùng rồi quy generic có
    tham số về `_ClassSpec(origin)` và vứt `get_args()` — nên lớp lỗi cũ chỉ
    lùi xuống một tầng (Review R1-A1 #2, P1).
    """
    if budget is None:
        budget = _Budget()
    budget.spend(where, depth)
    spec = _build_spec_node(hint, where, budget, depth)
    # Chỉ gắn `source` cho nút VỪA dựng. Nhánh union một phần tử trả thẳng nút
    # con ra ngoài; ghi đè `source` của nó sẽ làm cây parse tự mâu thuẫn với
    # chính phép đếm tham số kiểu mà meta-invariant dùng để kiểm.
    if not hasattr(spec, "source"):
        spec.source = hint
    return spec


def _build_spec_node(hint: Any, where: str, budget: "_Budget",
                     depth: int) -> _Spec:
    if hint is Any:
        return _AnySpec()
    if hint is None or hint is _NONE_TYPE:
        return _NoneSpec()

    origin = _foreign(lambda: typing.get_origin(hint), where, "`get_origin`")

    if origin is Literal:
        values = _foreign(lambda: typing.get_args(hint), where, "`get_args`")
        for value in values:
            if not _is_one_of(type(value), _LITERAL_VALUE_TYPES):
                raise CanonicalContractViolation(
                    f"{where}: `Literal` chỉ nhận giá trị kiểu "
                    f"{', '.join(t.__name__ for t in _LITERAL_VALUE_TYPES)}; gặp "
                    f"{value!r} ({type(value).__name__})."
                )
        return _LiteralSpec(values)

    if origin is typing.Union or (_UNION_TYPE is not None and origin is _UNION_TYPE):
        # `typing` đã làm phẳng union lồng nhau, kể cả `Optional[Union[...]]`.
        branches = tuple(
            _build_spec(arg, f"{where}|{i}", budget, depth + 1)
            for i, arg in enumerate(
                _foreign(lambda: typing.get_args(hint), where, "`get_args`"))
        )
        if not branches:
            raise CanonicalContractViolation(f"{where}: union rỗng.")
        return branches[0] if len(branches) == 1 else _UnionSpec(branches)

    if isinstance(hint, TypeVar):
        raise CanonicalContractViolation(
            f"{where}: `TypeVar` ({hint!r}) chưa được hỗ trợ. Canonical dataclass "
            "trong dự án này không generic; đỡ `TypeVar` cho đúng nghĩa là phải "
            "mô hình hoá binding và variance — một trình kiểm kiểu thu nhỏ mà "
            "production không cần. Hãy khai kiểu cụ thể, hoặc `Union[...]` nếu "
            "thật sự có nhiều kiểu."
        )

    target = origin if origin is not None else hint

    # `isinstance(target, type)` PHẢI đứng trước mọi phép tra tập hợp: một
    # `target` không hash được (tham số dạng `[A, B]` của `Callable`) sẽ làm
    # `x in frozenset(...)` nổ `TypeError: unhashable type` — đúng lớp lỗi rò
    # mà P2 nói tới. Không hash được thì rơi thẳng xuống nhánh `raise` cuối.
    if isinstance(target, type):
        _classify_class_target(target, where)
        args = (_foreign(lambda: typing.get_args(hint), where, "`get_args`")
                if origin is not None else ())
        return _ClassSpec(
            target, _parse_generic_args(target, args, where, budget, depth + 1)
        )

    raise CanonicalContractViolation(
        f"{where}: annotation {_safe_name(hint)} nằm NGOÀI ngữ pháp canonical, nên framework "
        "không bảo đảm được gì cho field này. Ngữ pháp hỗ trợ: `Any`, `None`, một "
        "lớp cụ thể (kể cả generic có tham số — MỌI tham số đều được parse), "
        "`Optional[...]`, `Union[...]` (gồm cả dạng `a | b`), `Literal[...]`. "
        "Một annotation không hiểu được PHẢI nổ ở đây chứ không được âm thầm "
        "thành `Any` — đó là Finding #1 của Independent Review R1-A, và việc nó "
        "phải đúng ở MỌI ĐỘ SÂU là Finding #2 của Independent Review R1-A1."
    )


def _field_checker(name: str, hint: Any, error: type) -> Callable[[Any, str], None]:
    """Dựng phép kiểm cho một field, MỘT LẦN, lúc decorate.

    `error` là lớp ngoại lệ mà type khai — xem `canonical(field_error=...)`.
    Master data hỏng phải nổ thành `InvalidEmployeeConfig`, không phải một
    `TypeError` chung chung: lằn ranh "công cụ hỏng" ≠ "dữ liệu xấu" là một
    quyết định nghiệp vụ (HD-110-09), không phải chi tiết cài đặt.
    """
    spec = _build_spec(hint, f"`{name}`")
    if not spec.is_inhabited():
        dead = spec.uninhabited_label() or spec.label
        raise CanonicalContractViolation(
            f"`{name}`: {dead} không bao giờ khớp được giá trị nào "
            f"(trong annotation {spec.label}). "
            "Chính sách bất biến của canonical loại MỌI container mutable "
            "(`list`/`dict`/`set`/`bytearray`), nên một field khai kiểu đó sẽ "
            "decorate thành công rồi từ chối mọi giá trị — một hợp đồng rỗng. "
            "SUPPORTED phải nghĩa là 'có ít nhất một giá trị hợp lệ', không "
            "phải 'parser đọc được' (R1-A1 #3, finding #3). Dùng `tuple`, "
            "`frozenset`, `bytes` hoặc `FrozenMapping`."
        )
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
                f"`{name}` phải là {label}, gặp {type(value).__name__} "
                f"({value!r}).{strictness}"
            )
        if isinstance(value, _MUTABLE_CONTAINERS):
            raise error(
                f"`{name}` giữ một container mutable ({type(value).__name__}). "
                "Một canonical object bất biến không được giữ alias mà người "
                "gọi còn sửa được sau khi dựng."
            )

    # Phơi cây parse ra để một test ở TẦNG TRỪU TƯỢNG đi hết được nó và chứng
    # minh không nút nào bị bỏ rơi (R1-A1 #2, §9).
    check.__canonical_spec__ = spec  # type: ignore[attr-defined]
    return check


def _build_field_contract(cls: type, error: type) -> tuple:
    """Đọc annotation của class MỘT LẦN và dựng danh sách phép kiểm."""
    try:
        hints = typing.get_type_hints(cls)
    except Exception as exc:  # noqa: BLE001
        raise CanonicalContractViolation(
            f"{cls.__name__}: không phân giải được annotation nên không dẫn "
            f"xuất được hợp đồng field ({exc}). Một canonical type mà framework "
            "không đọc nổi kiểu thì không thể tự bảo đảm gì."
        ) from exc

    # ── PSEUDO-FIELD (R1-A1 #3, finding #4).
    #
    # `dataclasses.fields()` BỎ QUA `InitVar`, nhưng `@dataclass` vẫn truyền nó
    # vào `__post_init__`. Nên hợp đồng field không thấy nó, còn wrapper
    # `__post_init__(self)` của framework thì sai chữ ký — đo được tại
    # `d4a8797`: `TypeError: __post_init__() takes 1 positional argument but 2
    # were given`. Decorate lọt rồi constructor vỡ.
    #
    # `ClassVar` cũng nằm trong `__dataclass_fields__` nhưng KHÔNG phải field và
    # KHÔNG được truyền vào `__post_init__`, nên nó vô hại.
    declared = getattr(cls, "__dataclass_fields__", {})
    real = {fld.name for fld in _dataclass_fields(cls)}
    pseudo = [name for name in declared if name not in real]
    if pseudo:
        offenders = []
        for name in pseudo:
            resolved = hints.get(name)
            origin = _foreign(lambda: typing.get_origin(resolved),
                              f"{cls.__name__}.`{name}`", "`get_origin`")
            kind = ("ClassVar" if origin is typing.ClassVar
                    else "InitVar" if isinstance(resolved, _dataclasses.InitVar)
                    else _safe_name(resolved))
            if kind != "ClassVar":
                offenders.append(f"`{name}` ({kind})")
        if offenders:
            raise CanonicalContractViolation(
                f"{cls.__name__}: {', '.join(offenders)} — `@canonical` chưa hỗ "
                "trợ pseudo-field kiểu này. `dataclasses.fields()` bỏ qua "
                "chúng nên hợp đồng field không phủ được, trong khi "
                "`@dataclass` vẫn truyền chúng vào `__post_init__` — chữ ký "
                "wrapper của framework sẽ sai và constructor vỡ lúc chạy. Hãy "
                "khai thành field thường, hoặc nhận dữ liệu khởi tạo qua "
                "factory của chính type."
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

        # ── Hợp đồng R1-A #2: phép kiểm field dẫn xuất từ annotation, cài tự
        # động, chạy ĐÚNG GIỮA hai pha (xem `_canonical_post_init`).
        #
        # DỰNG TRƯỚC, GẮN SAU (R1-A1 #2, §6). Toàn bộ phép chứng minh — parse
        # hết cây annotation, chứng minh `isinstance()` dùng được với từng
        # target — chạy vào một biến CỤC BỘ. Chỉ khi mọi thứ đã chứng minh xong
        # mới chạm vào class và mới ghi registry. Nhờ vậy một decoration thất
        # bại để lại class NGUYÊN VẸN và registry KHÔNG ĐỔI: không có canonical
        # type nào tồn tại ở trạng thái nửa vời.
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

        # ── TỪ ĐÂY TRỞ XUỐNG mới là ghi: mọi phép chứng minh đã xong ở trên.
        cls.__canonical_contract__ = contract  # type: ignore[attr-defined]
        cls.__post_init__ = _canonical_post_init  # type: ignore[assignment]

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

        cls.__init_subclass__ = classmethod(_reject_subclass)  # type: ignore[assignment]

        if sealed:
            # ── Lớp 2: constructor công khai LUÔN từ chối.
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

            cls.__new__ = staticmethod(_sealed_new)  # type: ignore[assignment]

            def _no_pickle(self: Any) -> Any:
                raise SealedConstruction(
                    f"{type(self).__name__} không pickle được: tính hợp lệ của "
                    "nó bao gồm nguồn gốc, mà nguồn gốc thì không hồi sinh "
                    "được từ byte."
                )

            cls.__reduce__ = _no_pickle  # type: ignore[assignment]
        else:
            def _reduce(self: Any) -> Any:
                return (
                    _rebuild_canonical,
                    (
                        type(self),
                        {f.name: getattr(self, f.name) for f in _dataclass_fields(self)},
                    ),
                )

            cls.__reduce__ = _reduce  # type: ignore[assignment]

        # Value object bất biến: bản sao của nó chính là nó. Điều này cũng đóng
        # đường "deepcopy rồi sửa bản sao".
        cls.__copy__ = lambda self: self  # type: ignore[assignment]
        cls.__deepcopy__ = lambda self, memo: self  # type: ignore[assignment]
        cls.__canonical__ = True  # type: ignore[attr-defined]
        cls.__canonical_sealed__ = sealed  # type: ignore[attr-defined]
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


# `FrozenMapping`/`FrozenCounter` kế thừa `collections.abc.Mapping` nên
# metaclass của chúng là `ABCMeta`, không phải `type`. Đây là HAI class duy
# nhất framework tự sở hữu và tự biết ngữ nghĩa `isinstance` của chúng (không
# class nào trong cây MRO khai `__instancecheck__`/`__subclasshook__` riêng),
# nên chúng được tin bằng ĐỊNH DANH. Mọi class metaclass-lạ khác đều bị từ
# chối — xem `_classify_class_target()`.
_TRUSTED_NON_TYPE_METACLASS_CLASSES.extend((FrozenMapping, FrozenCounter))


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
    "frozen_tuple_map",
    "sealed_canonical_types",
]
