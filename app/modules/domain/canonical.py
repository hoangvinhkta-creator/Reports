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

import functools
import threading
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


# ───────────────────────────────────────────────── Lớp 4: copy / deepcopy / pickle


def _rebuild_canonical(cls: type, values: dict) -> Any:
    """Tái tạo QUA constructor, nên pickle không đi vòng qua Lớp 1."""
    return cls(**values)


# ────────────────────────────────────────────────────────── decorator chính


def canonical(*, sealed: bool = False) -> Callable[[type], type]:
    """Đóng một frozen dataclass thành canonical type.

    ``sealed=False`` — kiểu tự validate và FINAL, nhưng constructor vẫn công
    khai. Dùng cho những kiểu mà tính hợp lệ là **thuần cấu trúc**: đọc đủ
    field là kết luận được, không cần biết object đến từ đâu.

    ``sealed=True`` — thêm Lớp 2. Dùng cho những kiểu mà tính hợp lệ bao gồm
    **nguồn gốc**: một ``AffectedRow`` "đúng cấu trúc" nhưng trỏ vào dòng
    99999 của một file không tồn tại vẫn là provenance bịa, và không field nào
    diễn đạt được điều đó.
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
    "CanonicalSubclassRejected",
    "FrozenCounter",
    "FrozenMapping",
    "SealedConstruction",
    "as_exact_date",
    "as_exact_str",
    "canonical",
    "factory_for",
    "frozen_tuple_map",
]
