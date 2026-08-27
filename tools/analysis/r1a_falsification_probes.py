"""R1-A FALSIFICATION PROBES — canonical type coverage.

    PYTHONPATH=<repo-root> python tools/analysis/r1a_falsification_probes.py

Artefact bằng chứng của sub-repair **R1-A** (Canonical Type Coverage), mở sau
Independent Review R1 FAIL tại `2be5bfe`. Chạy được trên cả commit TRƯỚC lẫn
SAU R1-A nên hai lần chạy so trực tiếp được với nhau.

Câu hỏi mà bộ probe này trả lời — KHÔNG phải "type X có validate không", mà:

    framework `@canonical` có BẢO ĐẢM mọi type nó nhận đều được validate
    không, hay nó chỉ ĐÁNH DẤU rồi tin developer nhớ tự viết?

Nên A7 là probe quan trọng nhất: nó khai báo một canonical type mới hoàn toàn
rỗng và hỏi framework có phát hiện được không.

Bản pytest tương ứng: `tests/test_r1a_canonical_type_coverage.py`.
Bộ probe của R1 gốc: `tools/analysis/r1_falsification_probes.py` (vẫn chạy).

Kết quả mỗi probe:
    BYPASSED  dựng được trạng thái invalid / framework không phát hiện
    BLOCKED   kiến trúc chặn
    RESIDUAL  đi vòng được nhưng phải thò tay ngoài "public/reasonable API"
    OUT       cố ý ngoài scope R1-A (thuộc R1-B..R1-E hoặc R2→R8)
"""

from __future__ import annotations

import ast
import copy
import pathlib
import pickle
from dataclasses import dataclass, replace
from datetime import date

from app.modules.domain.canonical import canonical
from app.modules.domain.models import (
    MAPPING_STATUS_INACTIVE,
    MAPPING_STATUS_MAPPED,
    MAPPING_STATUS_UNMAPPED,
)
from app.modules.mapping.employee_mapper import (
    EmployeeMapper,
    MappingResult,
    RecordRef,
    build_employee_master,
)

# Nạp MỌI module có canonical type để registry đầy đủ khi probe chạy.
# `employee_mapping` kéo theo `validation.models`.
import app.modules.validation.employee_mapping  # noqa: E402,F401

RESULTS = []


def _decorated_class_names():
    """Quét AST `app/` tìm mọi class mang `@canonical` — nguồn độc lập với
    registry, để so chéo."""
    repo = pathlib.Path(__file__).resolve().parents[2]
    names = []
    for path in sorted((repo / "app").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                ast.unparse(d).startswith("canonical") for d in node.decorator_list
            ):
                names.append(node.name)
    return names


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


GROUPS = [{"code": "SALES"}]
EMPLOYEES = [
    {"raw_prefix": "Vũ Hạnh Ly", "normalized": "Ly", "group": "SALES", "active": True},
    {"raw_prefix": "Đức Kiên", "normalized": "Kiên", "group": "SALES", "active": True},
]


def master():
    return build_employee_master(EMPLOYEES, GROUPS)


def valid_ref():
    return master().refs[0]


# ═════════════════════════════════════════════════════════ A — RecordRef

@probe("A1", "RecordRef(index=-1) — Python negative index chọn thầm employee cuối")
def _a1():
    m = master()
    forged = RecordRef(m.snapshot_id, -1, "forged")
    picked = m.record(forged)
    return "BYPASSED", (f"dựng được, và master.record() trả {picked.normalized!r} "
                        f"(employee CUỐI, không phải employee 0)")


@probe("A2", "RecordRef index vượt range — boundary có chặn không")
def _a2():
    m = master()
    forged = RecordRef(m.snapshot_id, 99, "forged")
    try:
        m.record(forged)
    except IndexError as exc:
        return "BYPASSED", (f"RecordRef dựng được; master.record() nổ IndexError thô "
                            f"({exc}) thay vì lỗi domain — ref vẫn tồn tại được")
    return "BYPASSED", "dựng được và resolve được"


@probe("A3", "replace(valid RecordRef, index=-1) — tái dựng không được validate lại")
def _a3():
    bad = replace(valid_ref(), index=-1)
    return "BYPASSED", f"index={bad.index} snapshot_id={bad.snapshot_id!r}"


@probe("A3b", "RecordRef field sai kiểu hoàn toàn (snapshot_id=None, index=bool, label=list)")
def _a3b():
    bad = RecordRef(snapshot_id=None, index=True, label=["không phải chuỗi"])
    return "BYPASSED", (f"snapshot_id={bad.snapshot_id!r} index={bad.index!r} "
                        f"({type(bad.index).__name__}) label={bad.label!r}")


# ═════════════════════════════════════════════════════ A — MappingResult

@probe("A4", "MappingResult(status='NOT_A_MAPPING_STATUS')")
def _a4():
    bad = MappingResult(normalized="Ly", status="NOT_A_MAPPING_STATUS",
                        default_lead_source=None, include_in_kpi=None,
                        group="SALES", record=valid_ref())
    return "BYPASSED", f"status={bad.status!r} ngoài {(MAPPING_STATUS_MAPPED, MAPPING_STATUS_UNMAPPED, MAPPING_STATUS_INACTIVE)}"


@probe("A5", "MappingResult(record='not-a-RecordRef')")
def _a5():
    bad = MappingResult(normalized="Ly", status=MAPPING_STATUS_MAPPED,
                        default_lead_source=None, include_in_kpi=None,
                        group="SALES", record="not-a-RecordRef")
    return "BYPASSED", f"record={bad.record!r} ({type(bad.record).__name__})"


@probe("A6", "MappingResult mutable alias — normalized=[] rồi sửa list từ ngoài")
def _a6():
    shared = []
    bad = MappingResult(normalized=shared, status=MAPPING_STATUS_MAPPED,
                        default_lead_source=None, include_in_kpi=None,
                        group="SALES", record=valid_ref())
    shared.append("SỬA SAU KHI DỰNG")
    return "BYPASSED", f"normalized={bad.normalized!r} — alias vẫn sống"


@probe("A6b", "MappingResult mâu thuẫn: status=unmapped nhưng record vẫn có")
def _a6b():
    bad = MappingResult(normalized=None, status=MAPPING_STATUS_UNMAPPED,
                        default_lead_source=None, include_in_kpi=None,
                        record=valid_ref())
    return "BYPASSED", (f"status={bad.status!r} nhưng record={bad.record.label!r} "
                        "— hai câu trả lời mâu thuẫn cho cùng một câu hỏi")


@probe("A6c", "MappingResult(include_in_kpi=<str>) — không phải bool")
def _a6c():
    bad = MappingResult(normalized="Ly", status=MAPPING_STATUS_MAPPED,
                        default_lead_source=None, include_in_kpi="false",
                        group="SALES", record=valid_ref())
    return "BYPASSED", (f"include_in_kpi={bad.include_in_kpi!r} — chuỗi 'false' là "
                        "truthy trong Python")


# ══════════════════════════════════ A7 — framework có tự bảo đảm không?

@probe("A7", "khai báo một @canonical type MỚI hoàn toàn rỗng — framework phát hiện?")
def _a7():
    @canonical()
    @dataclass(frozen=True, slots=True)
    class DummyCanonical:
        anything: str
        whatever: int

    bad = DummyCanonical(anything=["không phải chuỗi"], whatever="không phải int")
    return "BYPASSED", (f"framework nhận type không có validate nào; dựng được "
                        f"anything={bad.anything!r} whatever={bad.whatever!r}")


@probe("A7b", "@canonical type mới có bị bắt buộc khai báo validator không?")
def _a7b():
    @canonical()
    @dataclass(frozen=True, slots=True)
    class NoValidator:
        x: str

    has = "__post_init__" in NoValidator.__dict__ or hasattr(NoValidator, "__post_init__")
    return "BYPASSED", (f"decorate xong không lỗi gì; có __post_init__ = {has} "
                        "— 'canonical' chỉ là một nhãn, không phải hợp đồng")


@probe("A7c", "oracle của R1 có phủ MỌI type @canonical không?")
def _a7c():
    """Đo cái đáng đo: tập type mà oracle THỰC SỰ chạy trên, lúc chạy — không
    phải việc tên type có xuất hiện trong source hay không. Sau R1-A oracle
    dẫn xuất từ registry nên tên không cần xuất hiện ở đâu cả."""
    import importlib

    module = importlib.import_module("tests.test_r1_canonical_object_safety")
    covered = {c.__name__ for c in getattr(module, "CANONICAL_TYPES", ())}
    scanned = set(_decorated_class_names())
    missing = sorted(scanned - covered)
    if missing:
        return "BYPASSED", (f"{len(scanned)} type mang @canonical nhưng oracle "
                            f"BỎ SÓT: {missing}")
    return "BLOCKED", f"oracle phủ đủ {len(scanned)} type"


@probe("A7d", "registry tự động có tồn tại VÀ khớp với AST scan không?")
def _a7d():
    import app.modules.domain.canonical as canon
    if not hasattr(canon, "canonical_types"):
        return "BYPASSED", ("không có registry — inventory phải maintain thủ công, "
                            "nên quên là chuyện không tránh khỏi")
    registered = {c.__name__ for c in canon.canonical_types()}
    scanned = set(_decorated_class_names())
    if registered != scanned:
        return "BYPASSED", (f"registry {sorted(registered)} != AST scan "
                            f"{sorted(scanned)}")
    return "BLOCKED", f"registry khớp AST scan, {len(registered)} type"


# ════════════════════════════ WAVE 2 — adversarial, không nhắm trực tiếp

@probe("W1", "bool thay int: RecordRef(index=True) rồi dùng làm khoá")
def _w1():
    m = master()
    a = RecordRef(m.snapshot_id, True, "x")
    b = RecordRef(m.snapshot_id, 1, "x")
    return "BYPASSED", f"True == 1 nên hai ref BẰNG NHAU và cùng hash: {a == b}, {hash(a) == hash(b)}"


@probe("W2", "str subclass đổi giá trị giữa hai lần đọc trong RecordRef.snapshot_id")
def _w2():
    class Shifty(str):
        n = 0
        def __str__(self):
            Shifty.n += 1
            return f"đọc lần {Shifty.n}"
    ref = RecordRef(Shifty("x"), 0, "label")
    return "BYPASSED", f"snapshot_id đọc hai lần: {str(ref.snapshot_id)!r} vs {str(ref.snapshot_id)!r}"


@probe("W3", "dict mutable trong MappingResult.group")
def _w3():
    shared = {"a": 1}
    bad = MappingResult(normalized="Ly", status=MAPPING_STATUS_MAPPED,
                        default_lead_source=None, include_in_kpi=None,
                        group=shared, record=valid_ref())
    shared["b"] = 2
    return "BYPASSED", f"group={bad.group!r} — dict alias sống sau khi dựng"


@probe("W4", "replace() nhiều field cùng lúc trên MappingResult")
def _w4():
    ok = EmployeeMapper(master()).resolve("Vũ Hạnh Ly 0868", date(2026, 1, 15))
    bad = replace(ok, status="BỊA", record=None, normalized=[], group={})
    return "BYPASSED", (f"status={bad.status!r} record={bad.record!r} "
                        f"normalized={bad.normalized!r} group={bad.group!r}")


@probe("W5", "pickle round-trip RecordRef rác")
def _w5():
    bad = pickle.loads(pickle.dumps(RecordRef("x", -5, "y")))
    return "BYPASSED", f"tái tạo được index={bad.index}"


@probe("W6", "deepcopy MappingResult rác")
def _w6():
    bad = copy.deepcopy(MappingResult(normalized="Ly", status="BỊA",
                                      default_lead_source=None, include_in_kpi=None,
                                      group="SALES", record=valid_ref()))
    return "BYPASSED", f"deepcopy giữ nguyên status={bad.status!r}"


@probe("W7", "MappingResult(status=mapped) nhưng normalized=None — mapped mà không có tên")
def _w7():
    bad = MappingResult(normalized=None, status=MAPPING_STATUS_MAPPED,
                        default_lead_source=None, include_in_kpi=None,
                        record=valid_ref())
    return "BYPASSED", f"status={bad.status!r} normalized={bad.normalized!r} group={bad.group!r}"


@probe("W8", "RecordRef(snapshot_id='') — snapshot rỗng khớp master nào?")
def _w8():
    bad = RecordRef("", 0, "x")
    return "BYPASSED", f"snapshot_id={bad.snapshot_id!r}"


@probe("W9", "resolve() trên dữ liệu hợp lệ có còn chạy đúng không? (non-regression)")
def _w9():
    got = EmployeeMapper(master()).resolve("Vũ Hạnh Ly 0868", date(2026, 1, 15))
    ok = (got.normalized == "Ly" and got.status == MAPPING_STATUS_MAPPED
          and got.group == "SALES" and type(got.record) is RecordRef)
    return ("BLOCKED" if ok else "BYPASSED"), f"resolve hợp lệ: {ok} ({got.normalized!r}/{got.status!r})"


@probe("W10", "master.record(ref hợp lệ) vẫn trả đúng employee? (non-regression)")
def _w10():
    m = master()
    ok = m.record(m.refs[1]).normalized == "Kiên"
    return ("BLOCKED" if ok else "BYPASSED"), f"record(refs[1]) == 'Kiên': {ok}"


# ═══════════════════════════════════ ngoài scope R1-A, ghi nhận có chủ đích

@probe("O1", "R1-C — AffectedRow.from_line nhận `line` duck-typed")
def _o1():
    from app.modules.validation.models import AffectedRow

    class FakeRaw:
        source_file = "BIA.xlsx"
        source_row = 99999

    class FakeLine:
        raw = FakeRaw()
        employee_raw = "Bịa"
        date = None

    row = AffectedRow.from_line(FakeLine())
    return "OUT", f"{row.source_file}:{row.source_row} — thuộc R1-C, KHÔNG sửa ở lượt này"


@probe("O2", "R1-D — FrozenMapping giữ value lồng nhau mutable")
def _o2():
    from app.modules.domain.canonical import FrozenMapping
    inner = ["a"]
    fm = FrozenMapping({"k": inner})
    inner.append("b")
    return "OUT", f"fm['k']={fm['k']!r} — thuộc R1-D, KHÔNG sửa ở lượt này"


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
