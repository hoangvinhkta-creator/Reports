"""R1 FALSIFICATION PROBES — chạy được trên BẤT KỲ commit nào của repo.

    PYTHONPATH=<repo-root> python tools/analysis/r1_falsification_probes.py

Đây là artefact bằng chứng của repair unit R1 (Canonical Object Safety). Nó
KHÔNG phải test suite: nó cố tình dựng canonical object INVALID qua public API
và báo cáo đường nào còn đi được. Nó chạy được cả trên commit TRƯỚC repair
(nơi phần lớn probe đi lọt) lẫn commit SAU repair, nên hai lần chạy so được
với nhau — đó là điều mà một file pytest nằm trong repo sau repair không làm
được, vì nó import module chỉ tồn tại sau repair.

Bản pytest tương ứng (dùng cho CI/regression) là
`tests/test_r1_canonical_object_safety.py`.

Mỗi probe in một dòng:  PROBE <id> | <kết quả> | <mô tả>
    BYPASSED  dựng được trạng thái invalid / đi vòng được  -> finding CÒN MỞ
    BLOCKED   kiến trúc chặn                                -> đóng cho đường đó
    RESIDUAL  đi vòng được NHƯNG phải thò tay vào tên `_`-private của module
              khác hoặc vào chính ngôn ngữ (`object.__setattr__`) — ngoài
              phạm vi "public/reasonable API" mà bất biến R1 phát biểu
    OUT       cố ý ngoài scope R1 (thuộc repair unit khác)

Nhóm A–F là bộ probe ban đầu, viết TRƯỚC khi sửa, từ finding của Review #8.
Nhóm G là wave hai: các đường CÙNG LỚP mà implementation KHÔNG nhắm trực tiếp.

Bằng chứng BEFORE/AFTER đầy đủ: `docs/tasks/TASK-110_REPAIR_PROGRESS.md` → R1.
"""

from __future__ import annotations

import copy
import copyreg
import dataclasses
import pickle
from dataclasses import dataclass, replace
from datetime import date

from app.modules.mapping.employee_mapper import (
    DateWindow, EmployeeMapper, EmployeeMaster, EmployeeRecord,
    build_employee_master,
)
import app.modules.mapping.employee_mapper as em
import app.modules.validation.models as vm
from app.modules.validation.models import (
    AffectedRow, AmbiguousRow, Diagnostics, ReviewItem, ReviewQueue, RowProvenance,
    CATEGORY_MISSING, SEVERITY_ERROR, SCOPE_ROW,
)
from app.modules.validation.employee_mapping import (
    MappingInput, MappingStats, collect_mapping_stats,
)
from tests.support.rows import affected

RESULTS = []


def probe(pid, desc):
    def deco(fn):
        try:
            outcome, detail = fn()
        except Exception as exc:  # noqa: BLE001
            outcome, detail = "BLOCKED", f"{type(exc).__name__}: {str(exc)[:100]}"
        RESULTS.append((pid, outcome, desc, detail))
        print(f"PROBE {pid:<4} | {outcome:<8} | {desc}\n{'':>7}   -> {detail}")
        return fn
    return deco


GOOD_EMPLOYEES = [
    {"raw_prefix": "Vũ Hạnh Ly", "normalized": "Ly", "group": "SALES", "active": True},
    {"raw_prefix": "Đức Kiên", "normalized": "Kiên", "group": "SALES", "active": True},
]
GOOD_GROUPS = [{"code": "SALES"}]


def good_master():
    return build_employee_master(GOOD_EMPLOYEES, GOOD_GROUPS)


def good_record():
    return good_master().records[0]


def good_stats():
    items = [MappingInput("raw.xlsx", 2, "Vũ Hạnh Ly 0868", date(2026, 1, 15), "Ly", "SALES")]
    return collect_mapping_stats(items, EmployeeMapper(good_master()))


# ══════════════════════════════════════════════════ A — dataclasses.replace()

@probe("A1", "replace(EmployeeMaster, records=<rác>)")
def _a1():
    bad = replace(good_master(), records=("KHÔNG PHẢI RECORD", 123))
    return "BYPASSED", f"records={bad.records!r}"


@probe("A2", "replace(EmployeeRecord, raw_prefix='') — prefix rỗng khớp mọi chuỗi (HD-110-06)")
def _a2():
    bad = replace(good_record(), raw_prefix="")
    return "BYPASSED", f"raw_prefix={bad.raw_prefix!r} normalized={bad.normalized!r}"


@probe("A3", "replace(EmployeeRecord, group=<group ma>) — HD-110-09")
def _a3():
    bad = replace(good_record(), group="GROUP_KHONG_TON_TAI")
    return "BYPASSED", f"group={bad.group!r}"


@probe("A4", "replace(EmployeeRecord, window=<start > end>) — cửa sổ bất khả")
def _a4():
    bad = replace(good_record(), window=DateWindow(date(2027, 1, 1), date(2020, 1, 1)))
    return "BYPASSED", f"window={bad.window.start}..{bad.window.end}"


@probe("A5", "replace(AffectedRow, source_file='BIA.xlsx', source_row=99999) — RC-1")
def _a5():
    bad = replace(affected(7), source_file="KHONG_TON_TAI.xlsx", source_row=99999)
    return "BYPASSED", f"{bad.source_file}:{bad.source_row}"


@probe("A6", "replace(RowProvenance, batch_scoped=<non-bool truthy>)")
def _a6():
    bad = replace(RowProvenance.of((affected(3),)), batch_scoped="chuỗi truthy")
    return "BYPASSED", f"batch_scoped={bad.batch_scoped!r} ({type(bad.batch_scoped).__name__})"


@probe("A7", "replace(MappingStats, total_rows=-1, mapper=None)")
def _a7():
    bad = replace(good_stats(), total_rows=-1, mapper=None)
    return "BYPASSED", f"total_rows={bad.total_rows} mapper={bad.mapper!r}"


@probe("A8", "replace(EmployeeMaster, records=<hai record trùng prefix, cửa sổ chồng>) — HD-110-15")
def _a8():
    m = build_employee_master(
        [{"raw_prefix": "Ly", "normalized": "Ly", "group": "SALES", "active": True}],
        GOOD_GROUPS)
    bad = replace(m, records=(m.records[0], m.records[0]))
    return "BYPASSED", f"{len(bad.records)} record cùng prefix {bad.records[0].raw_prefix!r}"


# ═══════════════════════════════════════════════════════════ B — subclassing

def _subclass_bypass(base, kwargs, describe):
    @dataclass(frozen=True)
    class Fake(base):
        def __post_init__(self):
            pass
    bad = Fake(**kwargs)
    return "BYPASSED", describe(bad)


@probe("B1", "subclass EmployeeMaster ghi đè __post_init__")
def _b1():
    return _subclass_bypass(
        EmployeeMaster, {"records": ("rác",), "group_codes": frozenset()},
        lambda b: f"isinstance={isinstance(b, EmployeeMaster)} records={b.records!r}")


@probe("B2", "subclass EmployeeRecord ghi đè __post_init__")
def _b2():
    return _subclass_bypass(
        EmployeeRecord,
        {"raw_prefix": "", "normalized": "", "group": "MA", "active": "yes",
         "window": None, "default_lead_source": None, "include_in_kpi": None},
        lambda b: f"isinstance={isinstance(b, EmployeeRecord)} active={b.active!r}")


@probe("B3", "subclass AffectedRow ghi đè __post_init__ — provenance bịa")
def _b3():
    return _subclass_bypass(
        AffectedRow, {"source_file": "BIA.xlsx", "source_row": 99999, "raw_original": "Bịa"},
        lambda b: f"isinstance={isinstance(b, AffectedRow)} {b.source_file}:{b.source_row}")


@probe("B4", "subclass RowProvenance ghi đè __post_init__")
def _b4():
    return _subclass_bypass(
        RowProvenance, {"rows": ("không phải AffectedRow",)},
        lambda b: f"rows={b.rows!r} affected_count={b.affected_count}")


@probe("B5", "subclass ReviewItem ghi đè __post_init__ — item không truy vết được")
def _b5():
    return _subclass_bypass(
        ReviewItem, {"category": "KHÔNG_TỒN_TẠI", "severity": "BỊA", "scope": "bịa"},
        lambda b: f"category={b.category!r} source_file={b.source_file!r}")


@probe("B6", "subclass Diagnostics ghi đè __post_init__ — str động qua được coercion")
def _b6():
    class Shifty(str):
        n = 0
        def __str__(self):
            Shifty.n += 1
            return f"lần đọc {Shifty.n}"

    @dataclass(frozen=True)
    class Fake(Diagnostics):
        def __post_init__(self):
            pass
    bad = Fake(employee=Shifty("x"))
    return "BYPASSED", f"hai lần đọc khác nhau: {str(bad.employee)!r} vs {str(bad.employee)!r}"


@probe("B7", "subclass MappingStats ghi đè __post_init__")
def _b7():
    return _subclass_bypass(
        MappingStats,
        {"mapper": None, "mapped": None, "groups": None, "unmapped": None,
         "ambiguities": None, "dataset_start": None, "dataset_end": None,
         "source_file": None, "total_rows": -5, "_unmapped_rows": None,
         "_rows_by_record": None, "_ambiguous_rows": None},
        lambda b: f"isinstance={isinstance(b, MappingStats)} total_rows={b.total_rows}")


# ══════════════════════════════════════════════════ C — seal đọc lại / rò rỉ

@probe("C1", "đọc `._seal` từ object hợp lệ rồi dựng object bịa")
def _c1():
    stolen = affected(3)._seal
    bad = AffectedRow(source_file="BIA.xlsx", source_row=1, raw_original="Bịa", _seal=stolen)
    return "BYPASSED", f"{bad.source_file}:{bad.source_row}"


@probe("C2", "đọc `_SEAL` module-level rồi dựng EmployeeMaster rác")
def _c2():
    bad = EmployeeMaster(records=("rác",), group_codes=frozenset(), _seal=em._SEAL)
    return "BYPASSED", f"records={bad.records!r}"


@probe("C3", "`_seal` còn là field của canonical type không?")
def _c3():
    leaky = [c.__name__ for c in (EmployeeRecord, EmployeeMaster, AffectedRow,
                                  AmbiguousRow, RowProvenance, MappingStats)
             if "_seal" in {f.name for f in dataclasses.fields(c)}]
    if leaky:
        return "BYPASSED", f"còn field `_seal`: {leaky}"
    return "BLOCKED", "không canonical type nào còn field `_seal`"


# ══════════════════════════════════════════════ D — copy / deepcopy / pickle

@probe("D1", "copy.deepcopy tạo bản sao RIÊNG không đi qua constructor?")
def _d1():
    original = good_master()
    clone = copy.deepcopy(original)
    if clone is original:
        return "BLOCKED", "deepcopy trả về chính object (value object bất biến)"
    return "BYPASSED", f"deepcopy tạo object riêng {id(clone)} != {id(original)}, không re-validate"


@probe("D2", "pickle round-trip AffectedRow — tái tạo không qua factory")
def _d2():
    bad = pickle.loads(pickle.dumps(affected(5)))
    return "BYPASSED", f"tái tạo {bad.source_file}:{bad.source_row} không cần factory"


@probe("D3", "copy.copy tạo bản sao RIÊNG?")
def _d3():
    original = affected(9)
    clone = copy.copy(original)
    if clone is original:
        return "BLOCKED", "copy trả về chính object"
    return "BYPASSED", "copy tạo object riêng, không re-validate"


# ═════════════════════════════════════ E — mutable alias trong sealed object

@probe("E1", "EmployeeMaster.records / group_codes có bất biến không?")
def _e1():
    m = good_master()
    kinds = sorted({type(m.records).__name__, type(m.group_codes).__name__})
    return "BLOCKED", f"{kinds} — bất biến"


@probe("E2", "MappingStats giữ Counter/dict mutable — sửa từ ngoài")
def _e2():
    s = good_stats()
    before = dict(s.mapped)
    s.mapped["BỊA"] = 999
    return "BYPASSED", f"mapped trước={before} sau={dict(s.mapped)}"


@probe("E3", "ReviewQueue.items list mutable, add() không kiểm kiểu")
def _e3():
    q = ReviewQueue()
    q.add("không phải ReviewItem")
    return "OUT", f"len={len(q)} items={q.items!r} — thuộc R5 (ReviewQueue Integrity), CỐ Ý không sửa ở R1"


@probe("E4", "AmbiguousRow.records: truyền list rồi sửa list đó từ ngoài")
def _e4():
    from tests.support.rows import line_for
    shared = ["A"]
    row = AmbiguousRow.from_line(line_for(4), raw_value="x", records=shared)
    shared.append("B ĐƯỢC THÊM SAU")
    if len(row.records) == 1:
        return "BLOCKED", f"records={row.records!r} — đã sao chép ở biên"
    return "BYPASSED", f"records={row.records!r}"


# ═══════════════════════════════════════════ F — hậu quả nghiệp vụ thực tế

@probe("F1", "EmployeeMapper resolve theo master giả mạo (prefix rỗng khớp mọi chuỗi)")
def _f1():
    m = good_master()
    bad = replace(m, records=(replace(m.records[0], raw_prefix="", group="MA"),))
    got = EmployeeMapper(bad).resolve("Người Hoàn Toàn Khác", date(2026, 1, 15))
    return "BYPASSED", f"normalized={got.normalized!r} group={got.group!r}"


@probe("F2", "ReviewItem sở hữu dòng bịa qua provenance giả mạo")
def _f2():
    bad_row = replace(affected(6), source_row=7777, source_file="BIA.xlsx")
    item = ReviewItem(category=CATEGORY_MISSING, severity=SEVERITY_ERROR,
                      scope=SCOPE_ROW, provenance=RowProvenance.of((bad_row,)))
    return "BYPASSED", f"item sở hữu dòng {item.source_row} tại {item.source_file!r}"


# ══════════════════════════════ G — WAVE 2: cùng lớp, KHÔNG nhắm trực tiếp

@probe("G1", "tạo subclass động bằng `type()` thay vì câu lệnh `class`")
def _g1():
    Fake = type("Fake", (AffectedRow,), {"__post_init__": lambda self: None})
    bad = Fake(source_file="BIA.xlsx", source_row=99999)
    return "BYPASSED", f"{bad.source_file}:{bad.source_row}"


@probe("G2", "metaclass tuỳ biến để né `__init_subclass__`")
def _g2():
    class Meta(type):
        def __new__(mcls, name, bases, ns, **kw):
            return super().__new__(mcls, name, bases, ns, **kw)
    Fake = Meta("Fake", (RowProvenance,), {"__post_init__": lambda self: None})
    bad = Fake(rows=("rác",))
    return "BYPASSED", f"rows={bad.rows!r}"


@probe("G3", "đăng ký một factory MỚI cho AffectedRow từ module khác")
def _g3():
    from app.modules.domain.canonical import factory_for as ff

    @ff(AffectedRow)
    def evil(**kw):
        return AffectedRow(**kw)
    bad = evil(source_file="BIA.xlsx", source_row=99999)
    return "BYPASSED", f"{bad.source_file}:{bad.source_row}"


@probe("G4", "gọi thẳng materialiser private của module (`_materialise_affected_row`)")
def _g4():
    fn = getattr(vm, "_materialise_affected_row", None)
    if fn is None:
        return "BLOCKED", "không có materialiser để gọi (bản trước repair)"
    bad = fn(source_file="BIA.xlsx", source_row=99999, raw_original="Bịa", when=None)
    return "RESIDUAL", (f"{bad.source_file}:{bad.source_row} — đòi hỏi thò tay vào tên "
                        "`_`-private của module khác; ngoài 'public/reasonable'")


@probe("G5", "`cls.__new__(cls)` rồi để dataclass __init__ chạy")
def _g5():
    obj = AffectedRow.__new__(AffectedRow)
    return "BYPASSED", f"dựng được instance rỗng {obj!r}"


@probe("G6", "`line` giả mạo lợi dụng cửa sổ permit của `AffectedRow.from_line`")
def _g6():
    built = []

    class EvilRaw:
        source_file = "that.xlsx"
        @property
        def source_row(self):
            try:
                built.append(AffectedRow(source_file="BIA.xlsx", source_row=99999))
            except Exception as exc:  # noqa: BLE001
                built.append(type(exc).__name__)
            return 5

    class EvilLine:
        raw = EvilRaw()
        employee_raw = "x"
        date = None

    AffectedRow.from_line(EvilLine())
    made = [b for b in built if isinstance(b, AffectedRow)]
    if made:
        return "BYPASSED", f"dựng được {made[0].source_file}:{made[0].source_row} trong cửa sổ permit"
    return "BLOCKED", f"trong cửa sổ permit vẫn bị chặn ({built})"


@probe("G7", "`__reduce_ex__(2)` (copyreg) thay vì `__reduce__`")
def _g7():
    blob = pickle.dumps(affected(5), protocol=2)
    bad = pickle.loads(blob)
    return "BYPASSED", f"protocol 2 tái tạo được {bad.source_file}:{bad.source_row}"


@probe("G8", "`copyreg._reconstructor` dựng instance rỗng rồi nạp __dict__")
def _g8():
    obj = copyreg._reconstructor(AffectedRow, object, None)
    obj.__dict__.update({"source_file": "BIA.xlsx", "source_row": 99999,
                         "raw_original": "Bịa", "when": None})
    return "BYPASSED", f"{obj.source_file}:{obj.source_row} không qua __init__"


@probe("G9", "replace() trên canonical KHÔNG sealed (Diagnostics) với giá trị rác")
def _g9():
    class Shifty(str):
        n = 0
        def __str__(self):
            Shifty.n += 1
            return f"lần đọc {Shifty.n}"
    bad = replace(Diagnostics(employee="ổn"), employee=Shifty("x"))
    a, b = bad.employee, bad.employee
    if type(bad.employee) is str and str(a) == str(b):
        return "BLOCKED", f"đã ép về str thuần: {bad.employee!r}"
    return "BYPASSED", f"hai lần đọc khác nhau: {str(a)!r} vs {str(b)!r}"


@probe("G10", "replace() trên ReviewItem với category/severity không tồn tại")
def _g10():
    ok = ReviewItem(category=CATEGORY_MISSING, severity=SEVERITY_ERROR,
                    scope=SCOPE_ROW, provenance=RowProvenance.of((affected(6),)))
    bad = replace(ok, category="KHÔNG_TỒN_TẠI")
    return "BYPASSED", f"category={bad.category!r}"


@probe("G11", "sửa nội dung `FrozenMapping._data` (thò tay vào private)")
def _g11():
    s = good_stats()
    if not hasattr(s.mapped, "_data"):
        return "BLOCKED", f"mapped là {type(s.mapped).__name__}, không có `_data`"
    try:
        s.mapped._data["BỊA"] = 999
        return "BYPASSED", f"sửa được qua `_data`: {dict(s.mapped)}"
    except TypeError as exc:
        return "BLOCKED", f"`_data` là MappingProxyType — {exc}"


@probe("G12", "MappingStats nhận `mapper` giả mạo (duck-typing)")
def _g12():
    class FakeMapper:
        records = ()
        def resolve_record(self, *a): return None
        def candidate_records(self, *a): return ()
        def record(self, ref): return None
        def ref_for_index(self, i): return None
    collect_mapping_stats([], FakeMapper())
    return "RESIDUAL", ("collector nhận mapper duck-typed; ownership thật của mapper/master "
                        "là R3 (WorkingData Ownership) — R1 chỉ đóng đường dựng stats giả")


@probe("G13", "`object.__setattr__` trên instance frozen hợp lệ")
def _g13():
    row = affected(6)
    object.__setattr__(row, "source_row", 99999)
    return "RESIDUAL", (f"source_row={row.source_row} — thò tay qua ngôn ngữ, "
                        "ngoài 'public/reasonable'; Python không đóng được đường này")


@probe("G14", "EmployeeMapper nhận master giả mạo không phải EmployeeMaster")
def _g14():
    class FakeMaster:
        records = ()
        snapshot_id = "bịa"
    EmployeeMapper(FakeMaster())
    return "BYPASSED", "EmployeeMapper chấp nhận master duck-typed"


@probe("G15", "dựng EmployeeMaster hợp lệ rồi replace group_codes bỏ trống")
def _g15():
    bad = replace(good_master(), group_codes=frozenset())
    return "BYPASSED", f"group_codes rỗng nhưng records vẫn khai group {bad.records[0].group!r}"


@probe("G16", "`_materialise_*` có bị đăng ký nhầm ngoài module chủ không?")
def _g16():
    from app.modules.domain.canonical import factory_for as ff
    try:
        ff(AffectedRow)(lambda **kw: None)
    except Exception as exc:  # noqa: BLE001
        return "BLOCKED", f"{type(exc).__name__}: {str(exc)[:80]}"
    return "BYPASSED", "đăng ký được factory từ module khác"


if __name__ == "__main__":
    print("=" * 78)
    tally = {}
    for _, outcome, _, _ in RESULTS:
        tally[outcome] = tally.get(outcome, 0) + 1
    print(f"TỔNG: {len(RESULTS)} probe | " +
          " | ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    for label in ("BYPASSED", "RESIDUAL", "OUT"):
        ids = [r[0] for r in RESULTS if r[1] == label]
        if ids:
            print(f"{label}: {', '.join(ids)}")
