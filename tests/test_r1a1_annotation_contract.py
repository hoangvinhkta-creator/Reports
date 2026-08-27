"""R1-A1 — ANNOTATION CONTRACT. Suite chấp nhận của hợp đồng ĐÃ FREEZE.

Hợp đồng: `docs/tasks/TASK-110-R1-A1-FROZEN-CONTRACT.md` (Owner freeze).

## Vì sao file này được viết lại toàn bộ

Bản trước là một suite *falsification*: nó hỏi "framework có đóng được dạng
tấn công này chưa?" trên một không gian mở. Ba vòng repair cho thấy câu hỏi ấy
không kết thúc — mỗi vòng đóng thêm vài dạng, mỗi vòng review sau lại dựng
được một object Python mới. Không gian annotation/runtime của Python không
hữu hạn, nên một tiêu chí chấp nhận phát biểu trên nó cũng không hữu hạn.

File này hỏi một câu hỏi ĐÓNG: **hợp đồng đã freeze có đúng như đã freeze
không?** Corpus là bất biến trong một vòng repair; attack mới đi vào HARDENING
BACKLOG chứ không đi vào đây.

## Corpus chỉ có MỘT bản

`FROZEN_CORPUS` sống trong `tools/analysis/r1a1_annotation_probes.py` và file
này import lại. Hai bản sao song song sẽ là một nguồn drift thứ hai — đúng thứ
Review R1 đã chỉ ra ở inventory viết tay (oracle liệt kê 9 type trong khi 11
type mang `@canonical`).

## Ngữ pháp đóng mà file này canh giữ

    spec := any | none | class | optional

Bốn dạng. Mọi thứ khác nổ `CanonicalContractViolation` lúc decorate. Không có
ô thứ ba, và đặc biệt không có ô "framework không hiểu nên thôi bỏ qua".
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import sys
import typing
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

import pytest

import app.modules.domain.canonical as canonical_module
from app.modules.domain.canonical import (
    CanonicalContractViolation,
    CanonicalFieldError,
    FrozenCounter,
    FrozenMapping,
    canonical,
    canonical_types,
    frozen_class_allowlist,
)
from app.modules.mapping.employee_mapper import MappingResult, RecordRef

# Nạp nốt module còn lại để registry đầy đủ khi file này chạy độc lập.
import app.modules.validation.employee_mapping  # noqa: E402,F401

from tools.analysis.r1a1_annotation_probes import (  # noqa: E402
    FROZEN_CORPUS,
    MISSING,
    OUTSIDE_FRAMEWORK_BOUNDARY,
    SUPPORTED_INVALID_REJECT,
    SUPPORTED_VALID,
    OUTSIDE_BOUNDARY_CASE_IDS,
    PRE_FROZEN_OUTSIDE_BOUNDARY_IDS,
    UNSUPPORTED_AT_DECORATION,
    VERIFIED_IMPLEMENTATION,
    VERIFIED_PYTHON_VERSION,
    VERIFIED_VERSION_INFO,
    Z_INVARIANTS,
    _raw_dataclass,
    _satisfies,
    corpus_accounting,
    interpreter_matches_verified,
    observe_outside_boundary,
    probe_class,
)

# ── BA CASE NGOÀI BIÊN FRAMEWORK (HD-POST-A1-02, Owner đã duyệt).
#
# `K03`, `L03`, `M02` nhắm vào thuộc tính mà CPython tự đọc TRƯỚC khi
# `@canonical` bắt đầu chạy (`dataclasses._process_class` →
# `inspect.formatannotation` → `typing`). R1-A1 không có trách nhiệm normalize
# exception xảy ra trước biên của chính nó.
#
# Chúng KHÔNG dùng `xfail`: `xfail` chỉ chứng minh test fail, nó không chứng
# minh fail ĐÚNG VÌ biên. Thay vào đó mỗi case có một oracle PASS với bốn
# assertion tường minh (§9) — xem `test_outside_boundary_case_is_proven_...`.
#
# Biên R1-A1 bắt đầu tại thời điểm code của `@canonical` bắt đầu execution.
# Nếu CPython đổi và `canonical` xuất hiện trong đường xử lý trước exception,
# assertion A và D sai và oracle FAIL — đúng như thiết kế.

_FROZEN_OUTCOMES = frozenset({
    UNSUPPORTED_AT_DECORATION, SUPPORTED_VALID, SUPPORTED_INVALID_REJECT,
    OUTSIDE_FRAMEWORK_BOUNDARY,
})


def _case_id(case) -> str:
    return f"{case.id}-{case.group}"


# ── §10 PHÂN LOẠI ORACLE: HARDENING COVERAGE ≠ FROZEN ACCEPTANCE CORPUS.
#
# Ba enforcement dưới đây chỉ phân biệt được bằng những case mà corpus đã
# freeze KHÔNG chứa. Theo rule B chúng không được thêm vào corpus, nên chúng
# sống ở đây như coverage của implementation — và được liệt kê tường minh để
# Independent Reviewer không nhầm chúng với acceptance gate.
#
# Chúng KHÔNG làm 105 thành 106. Chúng KHÔNG đổi acceptance classification.
HARDENING_COVERAGE = {
    "test_the_mutable_guard_never_consults_a_hostile_class_attribute":
        ("M-8", "HB-A1-01", "field `Any` + giá trị có `__class__` thù địch"),
    "test_a_wide_union_is_stopped_by_the_node_budget_not_by_arity":
        ("M-10", "HB-A1-02", "`Union` rộng hơn 511 nhánh chạm ngân sách node"),
    "test_the_foreign_boundary_never_chains_the_original_exception":
        ("M-11", "HB-A1-03", "`__cause__ is None` ở biên lạ"),
}


# ═════════════════════════════════ FROZEN CORPUS


@pytest.mark.parametrize("case", FROZEN_CORPUS, ids=_case_id)
def test_frozen_corpus_case(case):
    """Mỗi case của corpus đã freeze phải cho ĐÚNG outcome đã freeze.

    Node ID của test mang chính Frozen Case ID (`...[K03-K]`), nên bảng ánh xạ
    Test ID → Case ID đọc thẳng được từ `pytest --collect-only`.
    """
    observed = case.run()
    assert _satisfies(case.expected, observed), (
        f"{case.id} ({case.group}, clause {case.clause}): chờ {case.expected}, "
        f"đo được {observed} — {case.description}"
    )


@pytest.mark.parametrize("cid,description,clause,fn", Z_INVARIANTS,
                         ids=[z[0] for z in Z_INVARIANTS])
def test_frozen_corpus_invariant(cid, description, clause, fn):
    """Z01–Z04 quét TOÀN BỘ corpus, không phải bốn case rời."""
    ok, detail = fn()
    assert ok, f"{cid} ({clause}): {description} — vi phạm: {detail}"


def test_the_corpus_is_frozen_not_a_growing_list():
    """Corpus KHÔNG được bổ sung trong cùng một vòng repair (§14 hợp đồng).

    Test này là cơ chế: thêm/bớt một case mà quên cập nhật freeze sẽ nổ ở đây
    chứ không lặng lẽ làm "X/X PASS" mang một nghĩa khác.
    """
    ids = [c.id for c in FROZEN_CORPUS]
    assert len(ids) == len(set(ids)), "ID case bị trùng"
    assert len(FROZEN_CORPUS) == 101
    assert len(Z_INVARIANTS) == 4
    # HD-POST-A1-01: corpus chính thức = 105 case. Con số "95" trong văn xuôi
    # PLAN là lỗi đếm; bảng ID §12 là nguồn quy phạm.
    assert len(FROZEN_CORPUS) + len(Z_INVARIANTS) == 105
    per_group = {}
    for c in FROZEN_CORPUS:
        per_group[c.group] = per_group.get(c.group, 0) + 1
    assert per_group == {
        "A": 8, "B": 4, "C": 7, "D": 6, "E": 3, "F": 1, "G": 3, "H": 3,
        "I": 2, "J": 3, "K": 3, "L": 3, "M": 2, "N": 2, "O": 2, "P": 3,
        "Q": 8, "R": 4, "S": 2, "T": 3, "U": 2, "V": 3, "W": 7, "X": 13,
        "Y": 4,
    }


def test_hardening_coverage_is_declared_and_is_not_part_of_the_corpus():
    """§10 — ba test hardening tồn tại, và KHÔNG cái nào là một frozen case."""
    module = sys.modules[__name__]
    corpus_ids = {c.id for c in FROZEN_CORPUS} | {z[0] for z in Z_INVARIANTS}
    for name, (mutation, backlog, what) in HARDENING_COVERAGE.items():
        assert hasattr(module, name), f"thiếu test hardening {name} ({mutation})"
        assert name not in corpus_ids
        assert backlog.startswith("HB-A1-")
    assert len(HARDENING_COVERAGE) == 3
    assert {m for m, _, _ in HARDENING_COVERAGE.values()} == {"M-8", "M-10", "M-11"}


# ── ĐỐI CHIẾU BẢNG QUY PHẠM ↔ CODE.
#
# Precedence rule (DEC-136): bảng §12 của Frozen Contract là nguồn quy phạm.
# Tại `aff0240` bảng ĐÃ lệch code — HD-POST-A1-02 được áp vào `FROZEN_CORPUS`
# và vào §21.2 nhưng KHÔNG áp vào chính bảng §12, nên bảng còn ghi
# `UNSUPPORTED_AT_DECORATION` cho `K03`/`L03`/`M02`. Không ai phát hiện cho tới
# khi three-way reconciliation chạy tay.
#
# Test này biến phép đối chiếu ấy thành cơ chế: lệch một ô là suite ĐỎ.

_CONTRACT_PATH = (pathlib.Path(__file__).resolve().parents[1]
                  / "docs" / "tasks" / "TASK-110-R1-A1-FROZEN-CONTRACT.md")
_OUTCOME_TOKENS = (
    "UNSUPPORTED_AT_DECORATION", "SUPPORTED_INVALID_REJECT", "SUPPORTED_VALID",
    "OUTSIDE_FRAMEWORK_BOUNDARY", "bất biến",
)


def _parse_normative_table() -> dict:
    """Đọc bảng ID §12 của Frozen Contract, bung mọi dải `X01–X0n`."""
    text = _CONTRACT_PATH.read_text(encoding="utf-8")
    segment = text[text.index("## 12. Frozen attack corpus"):
                   text.index("## 13. Witness matrix")]
    rows = {}
    for line in segment.splitlines():
        match = re.match(r"^\|\s*`?([A-Z]\d{2})`?(–`?([A-Z]\d{2})`?)?\s*\|(.*)$", line)
        if not match:
            continue
        # Tách theo pipe KHÔNG escape: ô mô tả chứa `int \| str` (PEP 604).
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", match.group(4))]
        outcome = next((t for t in _OUTCOME_TOKENS if t in cells[1]), cells[1])
        first, last = match.group(1), match.group(3)
        ids = ([first] if last is None else
               [f"{first[0]}{i:02d}" for i in range(int(first[1:]), int(last[1:]) + 1)])
        for case_id in ids:
            assert case_id not in rows, f"ID trùng trong bảng quy phạm: {case_id}"
            rows[case_id] = outcome
    return rows


def test_the_normative_table_and_the_code_corpus_agree_case_by_case():
    """Bảng §12 (quy phạm) phải khớp `FROZEN_CORPUS` (code) từng ô."""
    table = _parse_normative_table()
    code = {c.id: c.expected for c in FROZEN_CORPUS}
    code.update({z[0]: "bất biến" for z in Z_INVARIANTS})
    assert len(table) == 105, f"bảng quy phạm có {len(table)} ID, phải là 105"
    assert set(table) == set(code), (
        f"chỉ có trong bảng: {sorted(set(table) - set(code))}; "
        f"chỉ có trong code: {sorted(set(code) - set(table))}")
    mismatched = {k: (table[k], code[k]) for k in table if table[k] != code[k]}
    assert not mismatched, (
        "bảng quy phạm lệch code — theo precedence rule bảng THẮNG, nên phải "
        f"sửa code hoặc mở Owner Decision: {mismatched}")


def test_every_expected_outcome_is_one_of_the_frozen_set():
    """Không được lén thêm một outcome thứ năm để làm một case xanh."""
    for case in FROZEN_CORPUS:
        assert case.expected in _FROZEN_OUTCOMES, case.id


def test_frozen_corpus_accounting_is_exactly_105_equals_102_plus_3():
    """§8 — số học chính thức. Không báo "102/105 PASS" (đọc như 3 case hỏng),
    không báo "105/105 PASS" (đọc như 3 case ngoài biên cũng là in-scope)."""
    acc = corpus_accounting()
    assert acc["classified"] == 105
    assert acc["in_scope_total"] == 102 and acc["in_scope_pass"] == 102
    assert acc["outside_total"] == 3 and acc["outside_ok"] == 3
    assert tuple(acc["outside_ids"]) == OUTSIDE_BOUNDARY_CASE_IDS == ("K03", "L03", "M02")
    assert acc["unclassified"] == 0
    assert acc["blocking"] == []
    assert acc["in_scope_total"] + acc["outside_total"] == 105
    # T03 mang cùng outcome nhưng TỪ BẢN FREEZE GỐC, nên §8 đếm nó vào in-scope.
    assert PRE_FROZEN_OUTSIDE_BOUNDARY_IDS == ("T03",)


@pytest.mark.parametrize("case_id", OUTSIDE_BOUNDARY_CASE_IDS)
def test_outside_boundary_case_is_proven_not_merely_failing(case_id):
    """§9 — bốn chứng minh cho mỗi case ngoài biên.

    A. `@canonical` chưa hề bắt đầu xử lý class mục tiêu;
    B. registry canonical không đổi;
    C. class mục tiêu không nhận một mẩu state canonical nào;
    D. `canonical.py` KHÔNG có trong traceback, và frame chịu trách nhiệm nằm
       trong stdlib.

    Assertion dựa trên biên NGỮ NGHĨA, không phải `filename == dataclasses.py:946`
    — số dòng chỉ là evidence của interpreter hiện tại.
    """
    case = next(c for c in FROZEN_CORPUS if c.id == case_id)
    ev = observe_outside_boundary(case.annotation, f"Oracle{case_id}")
    assert ev["raised"], "phải có exception — nếu không thì không có gì để phân loại"
    assert ev["A_canonical_never_entered"], (
        f"{case_id}: `@canonical` ĐÃ bắt đầu chạy — đây là BLOCKING R1-A1 DEFECT, "
        "không phải outside-boundary")
    assert ev["B_registry_unchanged"], f"{case_id}: registry đổi {ev['B_registry']}"
    assert ev["C_no_partial_state"], f"{case_id}: class nhận state canonical nửa vời"
    assert ev["D_canonical_absent_from_traceback"], (
        f"{case_id}: `canonical.py` xuất hiện trong traceback -> exception KHÔNG "
        "xảy ra trước biên")
    assert ev["foreign_component"] in ("dataclasses.py", "inspect.py", "typing.py"), (
        f"{case_id}: foreign component không phải dataclasses/typing/interpreter: "
        f"{ev['foreign_call_site']}")


def test_outside_boundary_classification_is_pinned_to_a_verified_interpreter():
    """§6 — phân loại ngoài biên KHÔNG auto-carry sang minor version khác.

    Nếu chạy trên một Python minor version khác, test này FAIL và buộc
    re-verify K03/L03/M02 thay vì im lặng mang theo phân loại cũ.
    """
    assert VERIFIED_IMPLEMENTATION == "cpython"
    assert VERIFIED_VERSION_INFO[:2] == (3, 11)
    assert interpreter_matches_verified(), (
        "ENVIRONMENT_REVERIFY_REQUIRED — KHÔNG phải R1-A1 correctness FAIL.\n"
        f"interpreter đang chạy: {sys.implementation.name} {sys.version_info[:3]}\n"
        f"bản đã verify:         {VERIFIED_PYTHON_VERSION}\n"
        "Hãy chạy `test_outside_boundary_case_is_proven_not_merely_failing` trên "
        "interpreter này. Nếu bốn mệnh đề A/B/C/D vẫn đúng thì đây chỉ là "
        "NON-BLOCKING environment difference: cập nhật VERIFIED_* và ghi lại "
        "evidence. Chỉ khi một mệnh đề A/B/C/D SAI thì mới là BLOCKING.")


# ═════════════════════════════════ NGỮ PHÁP ĐÓNG — CẤU TRÚC


def test_the_grammar_has_exactly_four_productions():
    """`any | none | class | optional`. Một dạng nút thứ năm phải nổ ở đây."""
    specs = {
        canonical_module._AnySpec, canonical_module._NoneSpec,
        canonical_module._ClassSpec, canonical_module._OptionalSpec,
    }
    found = {
        obj for obj in vars(canonical_module).values()
        if isinstance(obj, type) and issubclass(obj, canonical_module._Spec)
        and obj is not canonical_module._Spec
    }
    assert found == specs


def test_the_class_allowlist_has_exactly_four_categories():
    assert canonical_module._FROZEN_SCALARS == (str, int, bool, date)
    assert canonical_module._FROZEN_CONTAINERS == (tuple, frozenset)
    assert tuple(canonical_module._FROZEN_FRAMEWORK) == (FrozenMapping, FrozenCounter)
    # Category thứ tư là registry — metadata do chính decorator ghi.
    assert all(c in canonical_module._REGISTRY for c in canonical_types())


def test_a_class_outside_the_allowlist_is_refused_however_ordinary_it_looks():
    """Đây là điểm khác biệt so với ba vòng repair trước: `metaclass is type`
    KHÔNG còn là điều kiện đủ. Mặc định là TỪ CHỐI."""
    class PerfectlyOrdinary:
        pass

    assert type(PerfectlyOrdinary) is type
    with pytest.raises(CanonicalContractViolation, match="NGOÀI ngữ pháp"):
        probe_class(PerfectlyOrdinary, "ProbeOrdinary")


def test_no_annotation_in_the_grammar_needs_more_than_three_nodes():
    """Ngữ pháp tự chặn độ sâu ở 2, nên ngân sách node không bao giờ chặn oan.

    Đây là lý do `_MAX_ANNOTATION_DEPTH` bị GỠ: không còn trục độ sâu để chặn.
    """
    assert not hasattr(canonical_module, "_MAX_ANNOTATION_DEPTH")
    assert canonical_module._MAX_ANNOTATION_NODES == 512
    for annotation in (Any, None, str, int, bool, date, tuple, frozenset,
                       FrozenMapping, FrozenCounter, RecordRef,
                       Optional[str], Optional[RecordRef], str | None):
        spec = canonical_module._build_spec(annotation, "`t`")
        depth, node = 1, spec
        while node.children():
            node = node.children()[0]
            depth += 1
        assert depth <= 2, annotation


def test_a_wide_union_is_stopped_by_the_node_budget_not_by_arity():
    """C12 còn sống: một `Union` 600 nhánh chạm ngân sách TRƯỚC phép kiểm
    arity, nên hàng rào bề rộng là thật chứ không phải một hằng số trang trí."""
    wide = typing.Union[tuple(typing.Literal[i] for i in range(600))]
    with pytest.raises(CanonicalContractViolation, match="nút"):
        probe_class(wide, "ProbeWide")


def test_the_parser_is_not_recursive():
    """Ngữ pháp sâu 2 tầng nên parser là mã thẳng: `RecursionError` của CPython
    không còn cửa nào làm chính sách."""
    import inspect
    source = inspect.getsource(canonical_module._build_spec)
    assert "_build_spec(" not in source.split('"""')[-1]


# ═════════════════════════════════ AN TOÀN PHÂN LOẠI


def test_classification_never_calls_isinstance_on_an_unknown_target():
    """`isinstance` bị XOÁ khỏi đường validate: nó tra `value.__class__`, nên
    một property `__class__` nổ làm lỗi thô thoát ra và một `__class__` nói
    dối đưa object giả qua được field khai class thật."""
    import inspect
    source = inspect.getsource(canonical_module._ClassSpec)
    assert "isinstance(" not in source
    assert "type(value) is self._target" in source


def test_the_runtime_check_is_immune_to_a_lying_class_attribute():
    class Liar:
        @property
        def __class__(self):
            return tuple

    cls = probe_class(tuple, "ProbeLiar")
    assert isinstance(Liar(), tuple)          # `isinstance` BỊ LỪA
    with pytest.raises(CanonicalFieldError):  # hợp đồng thì không
        cls(value=Liar())


def test_the_mutable_guard_catches_a_subclass_of_list():
    """`issubclass(type(v), MUTABLES)` — primitive bổ sung được Owner duyệt.
    Phép so định danh bỏ sót lớp con; `isinstance` thì tra `__class__`."""
    class Sneaky(list):
        pass

    cls = probe_class(Any, "ProbeMutable")
    with pytest.raises(CanonicalFieldError, match="mutable"):
        cls(value=Sneaky())


def test_an_error_message_never_carries_text_from_a_foreign_object():
    """C11. `_safe_name()` cũ gọi `repr()` trong `try/except`: nó không để lọt
    exception, nhưng nó VẪN chạy code của người khác. Không nổ ≠ không chạy.

    Phạm vi khẳng định là GIAI ĐOẠN `@canonical`. `@dataclass` của CPython tự
    nó gọi `repr(annotation)` khi dựng chữ ký `__init__`
    (`inspect.formatannotation`) — đó là biên ngoài framework, cùng loại với
    `T03`, và test này tách hai giai đoạn ra thay vì gộp chúng lại.
    """
    assert not hasattr(canonical_module, "_safe_name")
    ran = []

    class LoudRepr:
        def __repr__(self):
            ran.append("repr")
            return "SENTINEL_LEAK"

    raw = _raw_dataclass(LoudRepr(), "ProbeLoud")   # giai đoạn CPython
    ran.clear()
    with pytest.raises(CanonicalContractViolation) as exc:
        canonical()(raw)                             # giai đoạn framework
    assert "SENTINEL_LEAK" not in str(exc.value)
    assert ran == []


def test_a_foreign_exception_is_never_rendered():
    """M01/M02 ở dạng khẳng định trực tiếp: `str(exc)` của một exception lạ
    chính là chạy code lạ, nên biên dùng `from None` và một hằng lý do."""
    ran = []

    class HostileStr(Exception):
        def __str__(self):
            ran.append("str")
            raise RuntimeError("nổ")

    class BadOrigin:
        @property
        def __origin__(self):
            raise HostileStr("x")

    with pytest.raises(CanonicalContractViolation) as exc:
        probe_class(BadOrigin(), "ProbeForeignExc")
    assert exc.value.__cause__ is None
    assert exc.value.__context__ is None or ran == []
    assert ran == []


def test_the_foreign_boundary_never_chains_the_original_exception():
    """C11, phần `from None`.

    Giữ exception gốc trong chain nghĩa là bất kỳ ai in traceback về sau đều
    chạy `__str__` của nó — đúng lỗ hổng đang đóng, chỉ bị dời sang chỗ khác.
    Biên B1 (`get_type_hints`) là biên tới được từ một khai báo canonical thật,
    nên nó là chỗ khẳng định điều này.

    KHÔNG thuộc frozen corpus: đây là coverage của implementation, thêm vào sau
    khi mutation-by-revert M-11 cho thấy corpus không phân biệt được
    `from None` với `from exc`.
    """
    with pytest.raises(CanonicalContractViolation) as exc:
        probe_class("KhongTonTaiODau", "ProbeChain")
    assert exc.value.__cause__ is None
    assert exc.value.__suppress_context__ is True


def test_the_mutable_guard_never_consults_a_hostile_class_attribute():
    """C5 / HD-A1-10, phần phân biệt `issubclass(type(v),…)` với `isinstance`.

    Trên một field `Any`, `isinstance(v, MUTABLES)` tra `v.__class__` và để lỗi
    thô thoát ra; `issubclass(type(v), MUTABLES)` đọc slot `ob_type` nên không
    chạm hook nào.

    KHÔNG thuộc frozen corpus: coverage của implementation, thêm vào sau khi
    M-8 cho thấy corpus không phân biệt được hai primitive này.
    """
    ran = []

    class HostileClass:
        @property
        def __class__(self):
            ran.append("__class__")
            raise RuntimeError("__class__ nổ")

    cls = probe_class(Any, "ProbeGuardPrimitive")
    cls(value=HostileClass())          # không phải mutable -> được nhận
    assert ran == []
    with pytest.raises(RuntimeError):  # đối chứng: `isinstance` thì nổ
        isinstance(HostileClass(), (list, dict, set, bytearray))


def test_a_framework_bug_is_not_swallowed_into_a_contract_violation():
    """C10, chiều ngược lại: biên HẸP nên lỗi lập trình bên trong framework nổ
    nguyên hình thay vì được đóng gói thành một lỗi domain."""
    original = canonical_module._in_allowlist

    def exploding(_target):
        raise ZeroDivisionError("bug giả lập")

    canonical_module._in_allowlist = exploding
    try:
        with pytest.raises(ZeroDivisionError):
            probe_class(str, "ProbeFrameworkBug")
    finally:
        canonical_module._in_allowlist = original


# ═════════════════════════════════ NGUYÊN TỬ CỦA DECORATION


def test_a_custom_metaclass_is_refused_before_anything_is_written():
    """C9. Không có cổng này, một `__setattr__` nổ giữa chừng để lại class nửa
    vời — đo được tại `1b0da151`: `__canonical_contract__` đã ghi trong khi
    `__post_init__` chưa bọc."""
    class Meta(type):
        pass

    cls = Meta("Probe", (), {"__annotations__": {"value": int},
                             "__post_init__": lambda self: None,
                             "__module__": __name__})
    cls = dataclass(frozen=True)(cls)
    before = len(canonical_types())
    with pytest.raises(CanonicalContractViolation, match="metaclass"):
        canonical()(cls)
    assert len(canonical_types()) == before
    assert not hasattr(cls, "__canonical_contract__")
    assert not hasattr(cls, "__canonical__")


def test_all_eleven_production_types_pass_the_metaclass_gate():
    for cls in canonical_types():
        if cls.__module__.startswith("app."):
            assert type(cls) is type, cls.__name__


# ═════════════════════════════════ PRODUCTION


def test_every_production_canonical_type_still_builds_its_contract():
    prod = [c for c in canonical_types() if c.__module__.startswith("app.")]
    assert len(prod) == 11
    total = 0
    for cls in prod:
        contract = getattr(cls, "__canonical_contract__", None)
        assert contract, cls.__name__
        assert {n for n, _ in contract} == {f.name for f in dataclasses.fields(cls)}
        total += len(contract)
    assert total == 72


def test_every_production_annotation_is_inside_the_frozen_grammar():
    """Exit criterion #3. Nếu một field production rơi ra ngoài ngữ pháp thì
    hợp đồng sai, không phải field sai — và nó phải nổ ở đây."""
    forms = {"any": 0, "none": 0, "class": 0, "optional": 0}
    for cls in canonical_types():
        if not cls.__module__.startswith("app."):
            continue
        hints = typing.get_type_hints(cls)
        for fld in dataclasses.fields(cls):
            spec = canonical_module._build_spec(hints[fld.name], f"`{fld.name}`")
            if isinstance(spec, canonical_module._AnySpec):
                forms["any"] += 1
            elif isinstance(spec, canonical_module._NoneSpec):
                forms["none"] += 1
            elif isinstance(spec, canonical_module._OptionalSpec):
                forms["optional"] += 1
            else:
                forms["class"] += 1
    assert forms == {"any": 1, "none": 0, "class": 37, "optional": 34}


def test_production_error_messages_are_unchanged():
    """Thông báo là bằng chứng đã trích dẫn ở nhiều nơi; hợp đồng mới không
    được làm chúng đổi giọng — kể cả khi renderer đã thành an toàn."""
    with pytest.raises(CanonicalFieldError) as exc:
        RecordRef(snapshot_id=None, index=0, label="x")
    assert str(exc.value) == "`snapshot_id` không được là None (khai chuỗi thuần)."

    with pytest.raises(CanonicalFieldError) as exc:
        MappingResult(normalized=1, status="mapped", default_lead_source=None,
                      include_in_kpi=None, group="SALES")
    assert str(exc.value) == (
        "`normalized` phải là chuỗi thuần hoặc `None`, gặp int (1). Kiểm CHÍNH "
        "XÁC chứ không `isinstance`: một lớp con của `str` đổi giá trị giữa hai "
        "lần đọc, và `True` là một `int` hợp lệ."
    )

    with pytest.raises(CanonicalFieldError) as exc:
        MappingResult(normalized="Ly", status="mapped", default_lead_source=None,
                      include_in_kpi=None, group="SALES", record="not-a-RecordRef")
    assert str(exc.value) == (
        "`record` phải là `RecordRef` hoặc `None`, gặp str ('not-a-RecordRef')."
    )


def test_a_value_the_renderer_cannot_show_becomes_a_constant_not_a_repr_call():
    ran = []

    class LoudValue:
        def __repr__(self):
            ran.append("repr")
            return "LEAK"

    cls = probe_class(str, "ProbeRender")
    with pytest.raises(CanonicalFieldError) as exc:
        cls(value=LoudValue())
    assert "LEAK" not in str(exc.value)
    assert "<giá trị không hiển thị được>" in str(exc.value)
    assert ran == []


# ═════════════════════════════════ WITNESS MATRIX (C14)


def test_the_witness_matrix_covers_every_member_of_the_frozen_allowlist():
    """Thêm một class vào allowlist mà quên witness phải nổ ở đây.

    Chỉ tính phần ĐÃ FREEZE của allowlist: probe class do chính corpus đăng ký
    không thuộc hợp đồng.
    """
    frozen_members = [
        c for c in frozen_class_allowlist()
        if not getattr(c, "__module__", "").startswith("tools.")
        and not getattr(c, "__module__", "").startswith("tests.")
    ]
    witnessed = set()
    for case in FROZEN_CORPUS:
        if case.group == "X" and case.annotation is not MISSING:
            witnessed.add(case.annotation)
    missing = [getattr(c, "__name__", c) for c in frozen_members
               if not any(c is w for w in witnessed)]
    # 11 canonical type production: ba type đại diện đủ cho hình thái `class`
    # (không sealed, sealed, và một type do type khác tham chiếu). Các type còn
    # lại được phủ bởi `test_every_production_annotation_is_inside_...`.
    allowed_gap = {"AffectedRow", "AmbiguousRow", "Diagnostics", "ReviewItem",
                   "MappingStats", "MappingResult", "EmployeeRecord",
                   "EmployeeMaster"}
    assert set(missing) <= allowed_gap, missing


def test_every_witness_row_really_builds_an_object():
    """Một dòng tuyên bố SUPPORTED mà không dựng nổi giá trị nào là lỗi của
    chính oracle — đây là finding #6 của Review R1-A1 #3, giữ nguyên hiệu lực."""
    rows = [c for c in FROZEN_CORPUS if c.group == "X"]
    assert len(rows) == 13
    for case in rows:
        assert case.witness is not MISSING, case.id
        cls = probe_class(case.annotation, f"W{case.id}")
        cls(value=case.witness)


# ═════════════════════════════════ ORACLE CÓ THỂ FAIL


def test_oracle_proof_reverting_to_isinstance_reopens_the_class_hole(monkeypatch):
    """Nếu gỡ phép kiểm định danh, nhóm J phải QUAY LẠI hỏng. Một oracle không
    bao giờ fail được thì không chứng minh gì."""
    monkeypatch.setattr(
        canonical_module._ClassSpec, "matches",
        lambda self, value: isinstance(value, self._target))
    broken = [c.id for c in FROZEN_CORPUS
              if c.group == "J" and not _satisfies(c.expected, c.run())]
    assert broken == ["J01", "J02", "J03"]


def test_oracle_proof_widening_the_allowlist_reopens_the_class_hole(monkeypatch):
    monkeypatch.setattr(canonical_module, "_in_allowlist",
                        lambda target: isinstance(target, type))
    broken = [c.id for c in FROZEN_CORPUS
              if c.group == "W" and not _satisfies(c.expected, c.run())]
    assert "W05" in broken and "W06" in broken and "W07" in broken


def test_oracle_proof_the_atomicity_observer_detects_a_half_written_class(monkeypatch):
    """Observer của V01 không được vacuous: nếu decoration ghi lên class RỒI
    mới hỏng — đúng hành vi đo được tại `1b0da151` khi chưa có cổng C9 — nó
    phải báo `CLASS_LEFT_HALF_WRITTEN`, không phải PASS."""
    import tools.analysis.r1a1_annotation_probes as probes

    def half_writing(**kwargs):
        def decorate(cls):
            cls.__canonical_contract__ = ()      # ghi trước…
            raise CanonicalContractViolation("…rồi mới hỏng")
        return decorate

    monkeypatch.setattr(probes, "canonical", half_writing)
    case = next(c for c in FROZEN_CORPUS if c.id == "V01")
    observed = case.run()
    assert observed != UNSUPPORTED_AT_DECORATION
    assert not _satisfies(case.expected, observed)
