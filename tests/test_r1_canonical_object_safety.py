"""R1 — CANONICAL OBJECT SAFETY. Falsification suite của repair unit R1.

Nguồn: `docs/tasks/TASK-110-REPAIR-MODE.md` §3 R1, Independent Review #8.
Bằng chứng BEFORE/AFTER: `docs/tasks/TASK-110_REPAIR_PROGRESS.md` → R1.

Mỗi test dưới đây là một **probe falsification**: nó CỐ dựng một canonical
object invalid qua public/reasonable API. Trước repair (`0f3a6a4`) 29/43 probe
dựng được; sau repair không probe nào còn dựng được.

Đây KHÔNG phải test "tính năng chạy đúng". Chúng chỉ trả lời đúng một câu:

    có còn đường công khai nào dựng được canonical object invalid không?

Ba đường vẫn còn mở được ghi nhận tường minh ở cuối file dưới dạng test —
chúng đòi hỏi thò tay vào tên `_`-private của module khác hoặc vào chính ngôn
ngữ (`object.__setattr__`), tức là ngoài phạm vi "public/reasonable API" mà
bất biến R1 phát biểu. Ghi chúng thành test để một lần siết chặt hay nới lỏng
nào về sau cũng phải đi qua code review, thay vì lặng lẽ trôi.
"""

from __future__ import annotations

import copy
import copyreg
import dataclasses
import pickle
from dataclasses import dataclass, replace
from datetime import date

import pytest

import app.modules.mapping.employee_mapper as employee_mapper_module
import app.modules.validation.models as models_module
from app.modules.domain.canonical import (
    CanonicalSubclassRejected,
    FrozenCounter,
    FrozenMapping,
    SealedConstruction,
    factory_for,
)
from app.modules.mapping.employee_mapper import (
    DateWindow,
    EmployeeMapper,
    EmployeeMaster,
    EmployeeRecord,
    InvalidEmployeeConfig,
    build_employee_master,
)
from app.modules.validation.employee_mapping import (
    MappingInput,
    MappingStats,
    collect_mapping_stats,
)
from app.modules.validation.models import (
    CATEGORY_MISSING,
    SCOPE_ROW,
    SEVERITY_ERROR,
    AffectedRow,
    AmbiguousRow,
    Diagnostics,
    ReviewItem,
    RowProvenance,
)
from tests.support.rows import affected, line_for

GROUPS = [{"code": "SALES"}]
EMPLOYEES = [
    {"raw_prefix": "Vũ Hạnh Ly", "normalized": "Ly", "group": "SALES", "active": True},
    {"raw_prefix": "Đức Kiên", "normalized": "Kiên", "group": "SALES", "active": True},
]

SEALED_TYPES = (
    EmployeeRecord,
    EmployeeMaster,
    AffectedRow,
    AmbiguousRow,
    RowProvenance,
    MappingStats,
)
CANONICAL_TYPES = SEALED_TYPES + (DateWindow, Diagnostics, ReviewItem)


def master():
    return build_employee_master(EMPLOYEES, GROUPS)


def record():
    return master().records[0]


def stats():
    item = MappingInput("raw.xlsx", 2, "Vũ Hạnh Ly 0868", date(2026, 1, 15), "Ly", "SALES")
    return collect_mapping_stats([item], EmployeeMapper(master()))


# ══════════════════════════════════ ROOT CAUSE — seal không còn là dữ liệu

def test_r1_root_cause_no_canonical_type_carries_a_seal_field():
    """Root cause của R1: seal là một FIELD, nên nó đọc lại, sao chép và
    truyền vào được. Một capability token mà object tự trao lại cho caller thì
    không phải capability token."""
    leaky = {
        cls.__name__: sorted(f.name for f in dataclasses.fields(cls) if "seal" in f.name)
        for cls in CANONICAL_TYPES
        if any("seal" in f.name for f in dataclasses.fields(cls))
    }
    assert not leaky, f"canonical type còn field seal: {leaky}"


def test_r1_the_old_module_level_sentinels_are_gone():
    """`_SEAL` / `_STATS_SEAL` là biến module-level, đọc được từ bất kỳ đâu."""
    import app.modules.validation.employee_mapping as em_mod

    assert not hasattr(employee_mapper_module, "_SEAL")
    assert not hasattr(models_module, "_SEAL")
    assert not hasattr(em_mod, "_STATS_SEAL")


# ═══════════════════════════════════════ A — dataclasses.replace() (Review #8)

@pytest.mark.parametrize("build, changes", [
    (master, {"records": ("KHÔNG PHẢI RECORD", 123)}),
    (master, {"group_codes": frozenset()}),
    (record, {"raw_prefix": ""}),
    (record, {"group": "GROUP_KHONG_TON_TAI"}),
    (record, {"active": "yes"}),
    (lambda: affected(7), {"source_file": "KHONG_TON_TAI.xlsx", "source_row": 99999}),
    (lambda: RowProvenance.of((affected(3),)), {"batch_scoped": "chuỗi truthy"}),
    (lambda: RowProvenance.of((affected(3),)), {"rows": ("không phải AffectedRow",)}),
    (stats, {"total_rows": -1, "mapper": None}),
])
def test_a_replace_cannot_copy_a_valid_seal_onto_invalid_data(build, changes):
    """Finding chính của Review #8. `replace()` mang `_seal` hợp lệ sang một
    object mới rồi thay dữ liệu thành invalid — đo được ở `0f3a6a4` trên cả
    sáu sealed type."""
    with pytest.raises(SealedConstruction):
        replace(build(), **changes)


def test_a_replace_on_a_master_cannot_smuggle_in_duplicate_prefixes():
    """HD-110-15 là bất biến CỦA TẬP HỢP, nên nó phải sống trong kiểu của tập
    hợp. Khi nó nằm ở `parse_employee_master_rows()`, `replace()` đi vòng qua
    được — và `resolve` chọn bản ghi đầu, người kia mất sạch doanh số."""
    one = build_employee_master(
        [{"raw_prefix": "Ly", "normalized": "Ly", "group": "SALES", "active": True}],
        GROUPS)
    with pytest.raises(SealedConstruction):
        replace(one, records=(one.records[0], one.records[0]))


def test_a_the_window_invariant_now_lives_in_the_window_type():
    """`DateWindow` không sealed (không có yêu cầu nguồn gốc) nhưng nó tự kiểm
    `start <= end`, nên `replace(record, window=<bất khả>)` không mượn được
    một cửa sổ hợp lệ nữa."""
    with pytest.raises(InvalidEmployeeConfig, match="bất khả"):
        DateWindow(date(2027, 1, 1), date(2020, 1, 1))


# ═══════════════════════════════════════════ B — subclass bypass __post_init__

@pytest.mark.parametrize("base", CANONICAL_TYPES, ids=lambda c: c.__name__)
def test_b_a_canonical_type_cannot_be_subclassed_from_outside_its_module(base):
    """Bypass thứ hai của Review #8: một subclass ghi đè `__post_init__` xoá
    sạch phép validate trong khi `isinstance()` vẫn trả True."""
    with pytest.raises(CanonicalSubclassRejected):
        @dataclass(frozen=True)
        class Fake(base):  # noqa: D401
            def __post_init__(self):
                pass


@pytest.mark.parametrize("base", CANONICAL_TYPES, ids=lambda c: c.__name__)
def test_b_dynamic_subclass_creation_is_rejected_too(base):
    """`type()` và metaclass tuỳ biến đều phải đi qua `type.__new__`, nên
    `__init_subclass__` vẫn chạy. Đây là bảo đảm cấp ngôn ngữ, không phải một
    danh sách chặn."""
    with pytest.raises(CanonicalSubclassRejected):
        type("Fake", (base,), {"__post_init__": lambda self: None})

    class Meta(type):
        pass

    with pytest.raises(CanonicalSubclassRejected):
        Meta("Fake", (base,), {"__post_init__": lambda self: None})


def test_b_the_in_module_subclass_that_must_keep_working():
    """`AmbiguousRow` kế thừa `AffectedRow` trong CÙNG module — đường hợp lệ
    duy nhất, và nó vẫn phải chạy."""
    row = AmbiguousRow.from_line(line_for(4), raw_value="x", records=("A",))
    assert isinstance(row, AffectedRow)
    assert row.source_row == 4


# ══════════════════════════════════════════════ C — seal không còn rò rỉ

def test_c_a_valid_instance_hands_out_nothing_that_builds_another():
    with pytest.raises(AttributeError):
        affected(3)._seal  # noqa: B018


@pytest.mark.parametrize("cls, kwargs", [
    (AffectedRow, {"source_file": "BIA.xlsx", "source_row": 99999}),
    (RowProvenance, {"rows": ()}),
    (EmployeeMaster, {"records": (), "group_codes": frozenset()}),
])
def test_c_the_public_constructor_always_refuses(cls, kwargs):
    """Không tham số nào bật được đường này — không còn tham số nào cả."""
    with pytest.raises(SealedConstruction):
        cls(**kwargs)


def test_c_cls_new_directly_is_refused():
    with pytest.raises(SealedConstruction):
        AffectedRow.__new__(AffectedRow)


def test_c_a_factory_cannot_be_registered_from_another_module():
    """Nếu đăng ký được factory từ ngoài, permit trở thành một sentinel công
    khai — đúng cái đã bị falsify."""
    with pytest.raises(SealedConstruction, match="module định nghĩa nó"):
        factory_for(AffectedRow)(lambda **kw: None)


def test_c_a_forged_line_cannot_exploit_the_permit_window():
    """Permit chỉ mở quanh lời gọi constructor trong materialiser. Mọi thuộc
    tính của `line` đã được đọc xong trước đó, nên một `line` giả mạo có
    property tự dựng object không có cửa sổ nào để chen vào."""
    attempts = []

    class EvilRaw:
        source_file = "that.xlsx"

        @property
        def source_row(self):
            try:
                attempts.append(AffectedRow(source_file="BIA.xlsx", source_row=99999))
            except SealedConstruction:
                attempts.append("BLOCKED")
            return 5

    class EvilLine:
        raw = EvilRaw()
        employee_raw = "x"
        date = None

    AffectedRow.from_line(EvilLine())
    assert attempts == ["BLOCKED"]


# ═════════════════════════════════════════ D — copy / deepcopy / pickle

@pytest.mark.parametrize("build", [master, record, lambda: affected(3),
                                   lambda: RowProvenance.of((affected(3),)), stats],
                         ids=["master", "record", "affected", "provenance", "stats"])
def test_d_copy_and_deepcopy_return_the_same_object(build):
    """Value object bất biến: bản sao của nó chính là nó. Điều này cũng đóng
    đường "deepcopy rồi sửa bản sao"."""
    obj = build()
    assert copy.copy(obj) is obj
    assert copy.deepcopy(obj) is obj


@pytest.mark.parametrize("protocol", [0, 1, 2, 3, 4, 5])
def test_d_a_sealed_object_cannot_be_resurrected_from_bytes(protocol):
    """Tính hợp lệ của `AffectedRow` bao gồm NGUỒN GỐC, mà nguồn gốc thì không
    hồi sinh được từ byte. Kiểm mọi protocol vì `__reduce_ex__` chọn đường
    khác nhau theo protocol."""
    with pytest.raises(SealedConstruction):
        pickle.dumps(affected(5), protocol=protocol)


def test_d_copyreg_reconstructor_cannot_fill_an_empty_husk():
    """`copyreg._reconstructor` gọi thẳng `object.__new__`, đi vòng qua
    `__new__` của canonical type. `slots=True` khiến cái vỏ nó tạo ra không có
    `__dict__` để nạp trạng thái vào."""
    husk = copyreg._reconstructor(AffectedRow, object, None)
    with pytest.raises(AttributeError):
        husk.__dict__.update({"source_file": "BIA.xlsx", "source_row": 99999})


def test_d_every_canonical_type_uses_slots():
    missing = [c.__name__ for c in CANONICAL_TYPES if not hasattr(c, "__slots__")]
    assert not missing, f"thiếu __slots__: {missing}"


# ═══════════════════════════════ E — bất biến sâu (mutable alias, Review #8)

def test_e_a_sealed_object_holds_no_mutable_alias():
    """Review #8: *sealed dataclass có thể giữ mutable alias*. `frozen=True`
    chỉ cấm gán lại thuộc tính; nó không cấm sửa `Counter` mà thuộc tính đó
    trỏ tới."""
    s = stats()
    assert isinstance(s.mapped, FrozenCounter)
    assert isinstance(s.unmapped, FrozenCounter)
    for name in ("groups", "ambiguities", "_unmapped_rows", "_rows_by_record",
                 "_ambiguous_rows"):
        assert isinstance(getattr(s, name), FrozenMapping), name

    with pytest.raises(TypeError):
        s.mapped["BỊA"] = 999
    with pytest.raises(TypeError):
        s.mapped._data["BỊA"] = 999  # kể cả khi thò tay vào tên private
    assert "BỊA" not in s.mapped


def test_e_frozen_counter_keeps_counter_read_semantics():
    """`reconcile_conversion.py` in ra từ `most_common()` và output đó là bằng
    chứng đã ký của CHECK-108A1-15 (CHECK-110-14), nên thứ tự phải khớp."""
    from collections import Counter

    raw = Counter({"a": 3, "b": 1, "c": 3})
    frozen = FrozenCounter(raw)
    assert frozen.most_common() == raw.most_common()
    assert frozen.most_common(2) == raw.most_common(2)
    assert frozen["khong-co"] == 0 == raw["khong-co"]
    assert sum(frozen.values()) == sum(raw.values())
    assert dict(frozen) == dict(raw)


def test_e_containers_are_copied_at_the_boundary_not_just_checked():
    """Truyền một list vào rồi sửa list đó từ bên ngoài."""
    shared = ["A"]
    row = AmbiguousRow.from_line(line_for(4), raw_value="x", records=shared)
    shared.append("B THÊM SAU")
    assert row.records == ("A",)

    rows = [affected(6)]
    prov = RowProvenance.of(rows)
    rows.append(affected(7))
    assert prov.affected_count == 1


# ═════════════════════════════ F — hậu quả nghiệp vụ mà bypass từng gây ra

def test_f_a_forged_master_can_no_longer_reach_the_mapper():
    """Prefix rỗng khớp MỌI chuỗi, nên một master giả mạo nhận doanh số của
    người khác — và vì `employee_group` là chiều tra tỉ lệ quy đổi, đó là
    tiền."""
    m = master()
    with pytest.raises(SealedConstruction):
        EmployeeMapper(replace(m, records=(replace(m.records[0], raw_prefix=""),)))


def test_f_a_review_item_can_no_longer_own_a_fabricated_row():
    """Review Queue là sản phẩm cho người duyệt; một item "truy vết" về một
    dòng chưa từng tồn tại còn tệ hơn im lặng."""
    with pytest.raises(SealedConstruction):
        ReviewItem(
            category=CATEGORY_MISSING, severity=SEVERITY_ERROR, scope=SCOPE_ROW,
            provenance=RowProvenance.of(
                (replace(affected(6), source_row=7777, source_file="BIA.xlsx"),)
            ),
        )


def test_f_the_valid_paths_all_still_work():
    """Mặt còn lại: đóng chặt mà chặn luôn đường hợp lệ thì không phải sửa."""
    m = master()
    assert len(m.records) == 2
    assert m.snapshot_id == build_employee_master(EMPLOYEES, GROUPS).snapshot_id
    assert EmployeeMapper(m).resolve("Vũ Hạnh Ly 0868", date(2026, 1, 15)).normalized == "Ly"

    row = affected(6)
    prov = RowProvenance.of((row,))
    item = ReviewItem(category=CATEGORY_MISSING, severity=SEVERITY_ERROR,
                      scope=SCOPE_ROW, provenance=prov,
                      diagnostics=Diagnostics(criterion="F4"))
    assert item.source_row == 6 and item.affected_count == 1
    assert RowProvenance.batch((row,)).batch_scoped is True
    assert stats().total_rows == 1


# ══════════════════════════ G — canonical KHÔNG sealed: validate vẫn không bỏ qua được

def test_g_replace_on_an_unsealed_canonical_revalidates():
    """`Diagnostics`/`ReviewItem` dựng công khai được (validator dựng chúng),
    nên `replace()` chạy được — nhưng nó chạy qua `__post_init__`, nên nó chỉ
    sinh ra được object HỢP LỆ."""
    class Shifty(str):
        n = 0

        def __str__(self):
            Shifty.n += 1
            return f"lần đọc {Shifty.n}"

    diag = replace(Diagnostics(employee="ổn"), employee=Shifty("x"))
    assert type(diag.employee) is str
    assert diag.employee == diag.employee

    item = ReviewItem(category=CATEGORY_MISSING, severity=SEVERITY_ERROR,
                      scope=SCOPE_ROW, provenance=RowProvenance.of((affected(6),)))
    with pytest.raises(ValueError, match="Unknown review category"):
        replace(item, category="KHÔNG_TỒN_TẠI")


def test_g_an_unsealed_canonical_survives_a_pickle_round_trip_validated():
    diag = pickle.loads(pickle.dumps(Diagnostics(criterion="F4", employee="Ly")))
    assert diag == Diagnostics(criterion="F4", employee="Ly")


# ═══════════════════════════════════════════════════ RESIDUAL RISK, ghi rõ

def test_residual_object_setattr_still_reaches_past_frozen():
    """Python không có kiểu thật sự đóng. `object.__setattr__` đi thẳng qua
    `frozen=True`. Bất biến R1 phát biểu với **public/reasonable API**, và
    đường này nằm ngoài — nhưng nó tồn tại, nên nó được ghi lại ở đây."""
    row = affected(6)
    object.__setattr__(row, "source_row", 99999)
    assert row.source_row == 99999


def test_residual_the_private_materialiser_is_reachable_by_name():
    """Gọi thẳng `models._materialise_affected_row(...)` dựng được provenance
    bịa. Nó đòi hỏi thò tay vào một tên `_`-private của module khác — cùng lớp
    với `object.__setattr__` — nên nằm ngoài bất biến. Không có đường public
    nào tới nó: `factory_for` từ chối đăng ký ngoài module chủ."""
    forged = models_module._materialise_affected_row(
        source_file="BIA.xlsx", source_row=99999, raw_original="Bịa", when=None
    )
    assert forged.source_row == 99999


def test_residual_mapping_stats_accepts_a_duck_typed_mapper():
    """`collect_mapping_stats` nhận bất kỳ object nào có đủ phương thức mapper.
    Chứng minh mapper/master thật sự sở hữu lines là **R3 — WorkingData
    Ownership**, không phải R1. R1 chỉ đóng đường dựng `MappingStats` giả."""
    class FakeMapper:
        records = ()

        def resolve_record(self, *a):
            return None

        def candidate_records(self, *a):
            return ()

        def record(self, ref):
            return None

        def ref_for_index(self, i):
            return None

    assert collect_mapping_stats([], FakeMapper()).total_rows == 0


def test_out_of_scope_review_queue_stays_mutable_for_r5():
    """`ReviewQueue.items` là list mutable và `add()` không kiểm kiểu. Đó là
    **R5 — ReviewQueue Integrity**, một repair unit riêng, và R1 CỐ Ý không
    chạm vào. Test này đóng đinh ranh giới: nếu ai đó sửa nó, họ đang làm R5."""
    from app.modules.validation.models import ReviewQueue

    queue = ReviewQueue()
    queue.add("không phải ReviewItem")
    assert queue.items == ["không phải ReviewItem"]
