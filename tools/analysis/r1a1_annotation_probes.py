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

from app.modules.domain.canonical import FrozenMapping, canonical

# ── giá trị mẫu dùng chung
SENTINEL = object()
T_CONSTRAINED = TypeVar("T_CONSTRAINED", int, str)
T_BOUND = TypeVar("T_BOUND", bound=int)


class Marker:
    """Class thường, dùng làm 'canonical class reference' giả lập."""


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
    except Exception as exc:  # noqa: BLE001
        if expect == "UNSUPPORTED":
            return "UNSUPPORTED", f"{type(exc).__name__}: {str(exc)[:88]}"
        return "UNSUPPORTED", f"loại lúc decorate dù chờ hỗ trợ — {str(exc)[:70]}"

    def accepts(v):
        try:
            cls(value=v)
            return True
        except Exception:  # noqa: BLE001
            return False

    # So theo VỊ TRÍ, không theo `repr`: một lớp con của `str` có cùng `repr`
    # với chuỗi thường, nên so bằng `repr` sẽ báo nhầm nó là "đã được nhận".
    valid_ok = [accepts(v) for v in valid]
    invalid_ok = [accepts(v) for v in invalid]

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
probe("X2", "`Mapping[str, int]`", Mapping[str, int],
      valid=[FrozenMapping({"a": 1}), MappingProxyType({"a": 1})],
      invalid=[5, None, "x"])
probe("X3", "`Sequence[int]`", Sequence[int],
      valid=[(1, 2)], invalid=[5, None])
probe("X4", "`list[int]` (chính sách bất biến phải loại)", typing.List[int],
      valid=[], invalid=[[], [1], 5, None])
probe("X5", "`dict[str, int]` (chính sách bất biến phải loại)", typing.Dict[str, int],
      valid=[], invalid=[{}, {"a": 1}, 5, None])
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
probe("W14", "`Union[list, int]` — chính sách bất biến thắng nhánh khớp",
      Union[list, int], valid=[1], invalid=[[], [1]])


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
    for label in ("BYPASSED", "REJECTED", "BROKEN", "UNDECLARED", "UNSUPPORTED"):
        ids = [r[0] for r in RESULTS if r[1] == label]
        if ids:
            print(f"{label}: {', '.join(ids)}")
    print()
    print("BẤT BIẾN R1-A1: không ô nào được BYPASSED / REJECTED / BROKEN / UNDECLARED.")
    print("UNSUPPORTED là kết quả CHẤP NHẬN ĐƯỢC — nó là một tuyên bố, không phải lỗ hổng.")
