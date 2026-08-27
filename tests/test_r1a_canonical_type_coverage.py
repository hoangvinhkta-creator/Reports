"""R1-A — CANONICAL TYPE COVERAGE. Falsification suite của sub-repair R1-A.

Nguồn: Independent Review R1 FAIL tại `2be5bfe`.
Bằng chứng BEFORE/AFTER: `docs/tasks/TASK-110_REPAIR_PROGRESS.md` → R1-A.

Câu hỏi mà file này trả lời KHÔNG phải "type X có validate không" — đó là câu
hỏi của một danh sách, và một danh sách thì quên được. Câu hỏi là:

    framework `@canonical` có BẢO ĐẢM mọi type nó nhận đều được validate
    không, hay nó chỉ ĐÁNH DẤU rồi tin developer nhớ tự viết?

Tại `2be5bfe` câu trả lời là "chỉ đánh dấu": `RecordRef` và `MappingResult`
mang decorator mà không có một phép kiểm nào, và inventory của chính oracle
(`CANONICAL_TYPES`) là một tuple viết tay đã bỏ sót đúng hai type đó.

Nên phần lớn test dưới đây **parametrize trên registry**, không trên một danh
sách. Thêm một canonical type mới là tự động thêm nó vào mọi test ở đây.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import pathlib
import pickle
import typing
from dataclasses import dataclass, replace
from datetime import date

import pytest

from app.modules.domain.canonical import (
    CanonicalContractViolation,
    CanonicalFieldError,
    canonical,
    canonical_types,
)
from app.modules.domain.models import (
    MAPPING_STATUS_INACTIVE,
    MAPPING_STATUS_MAPPED,
    MAPPING_STATUS_UNMAPPED,
    MAPPING_STATUSES,
)
from app.modules.mapping.employee_mapper import (
    EmployeeMapper,
    ForeignRecordRef,
    MappingResult,
    RecordRef,
    build_employee_master,
)

# Nạp mọi module có canonical type để registry đầy đủ khi test chạy độc lập.
# `employee_mapping` kéo theo `validation.models`; `employee_mapper` đã import
# ở trên.
import app.modules.validation.employee_mapping  # noqa: F401

REPO = pathlib.Path(__file__).resolve().parents[1]

GROUPS = [{"code": "SALES"}]
EMPLOYEES = [
    {"raw_prefix": "Vũ Hạnh Ly", "normalized": "Ly", "group": "SALES", "active": True},
    {"raw_prefix": "Đức Kiên", "normalized": "Kiên", "group": "SALES", "active": True},
]


def master():
    return build_employee_master(EMPLOYEES, GROUPS)


def valid_ref():
    return master().refs[0]


def mapped_result(**overrides):
    """`MappingResult` hợp lệ, để mỗi probe chỉ hỏng đúng một thứ."""
    base = dict(normalized="Ly", status=MAPPING_STATUS_MAPPED,
                default_lead_source=None, include_in_kpi=None,
                group="SALES", record=valid_ref())
    base.update(overrides)
    return MappingResult(**base)


# ═══════════════════════════ ROOT CAUSE — framework là HỢP ĐỒNG, không phải NHÃN

def test_r1a_root_cause_a_canonical_type_must_declare_a_validator():
    """A7/A7b. Tại `2be5bfe` khai một `@canonical` type rỗng hoàn toàn không
    gây lỗi gì — nên `RecordRef` và `MappingResult` sống được nhiều vòng review
    trong trạng thái "được framework coi là canonical nhưng không validate gì"."""
    with pytest.raises(CanonicalContractViolation, match="__post_init__"):
        @canonical()
        @dataclass(frozen=True, slots=True)
        class NoValidator:
            x: str


def test_r1a_root_cause_the_inventory_is_derived_not_hand_written():
    """A7c/A7d. Nguồn drift thứ hai: oracle liệt kê 9 type trong khi 11 type
    mang `@canonical`. Registry do chính decorator ghi, nên không còn danh sách
    nào để quên.

    Lọc registry theo module `app.` để so ĐÚNG hai tập giống nhau: vế phải chỉ
    quét `app/`, còn registry ghi MỌI canonical type — kể cả những type động mà
    `test_r1a1_annotation_contract.py` khai để dò ngữ pháp annotation. Bản đầu
    của test này so "toàn bộ registry" với "khai báo trong app/" và chỉ đúng
    một cách tình cờ, vì khi đó chưa file test nào khai canonical type. Phép
    bảo đảm thật — registry phủ hết mọi `@canonical` trong `app/` — giữ nguyên.
    """
    registered = {c.__name__ for c in canonical_types()
                  if c.__module__.startswith("app.")}
    scanned = set()
    for path in sorted((REPO / "app").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                ast.unparse(d).startswith("canonical") for d in node.decorator_list
            ):
                scanned.add(node.name)
    assert registered == scanned, (
        f"registry và mã nguồn bất đồng. Chỉ trong registry: "
        f"{sorted(registered - scanned)}; chỉ trong mã nguồn: "
        f"{sorted(scanned - registered)}"
    )
    assert len(registered) >= 11


def test_r1a_the_r1_oracle_now_reads_from_the_registry():
    """File oracle của R1 không được quay lại tuple viết tay."""
    source = (REPO / "tests" / "test_r1_canonical_object_safety.py").read_text(encoding="utf-8")
    assert "CANONICAL_TYPES = canonical_types()" in source
    assert "SEALED_TYPES = sealed_canonical_types()" in source


# ═════════════════ HỢP ĐỒNG FIELD — áp cho MỌI type trong registry, tự động

@pytest.mark.parametrize("cls", canonical_types(), ids=lambda c: c.__name__)
def test_every_canonical_type_carries_a_field_contract(cls):
    """Hợp đồng phải phủ ĐÚNG từng field, không phải "có là được"."""
    contract = getattr(cls, "__canonical_contract__", None)
    assert contract is not None, f"{cls.__name__} không có hợp đồng field"
    assert {name for name, _ in contract} == {f.name for f in dataclasses.fields(cls)}


@pytest.mark.parametrize("cls", canonical_types(), ids=lambda c: c.__name__)
def test_every_canonical_type_declares_a_validator(cls):
    assert hasattr(cls, "__post_init__"), f"{cls.__name__} thiếu `__post_init__`"


@pytest.mark.parametrize("cls", canonical_types(), ids=lambda c: c.__name__)
def test_every_canonical_type_rejects_a_mutable_container_in_any_field(cls):
    """Bất kể annotation nói gì: một canonical object không được giữ alias mà
    người gọi còn sửa được. Test này chạy trên MỌI type, kể cả type thêm sau
    này — đó là điểm khác biệt so với một danh sách viết tay.

    Thông báo có thể là "phải là <kiểu>" (khi annotation loại nó trước) hoặc
    "container mutable" (khi annotation là `Any`); điều được khẳng định ở đây
    là **bị từ chối**, không phải câu chữ."""
    for name, check in cls.__canonical_contract__:
        for mutable in ([], {}, set(), bytearray()):
            with pytest.raises((TypeError, ValueError)):
                check(mutable, cls.__name__)


@pytest.mark.parametrize("cls", canonical_types(), ids=lambda c: c.__name__)
def test_every_canonical_type_rejects_a_str_subclass_where_str_is_declared(cls):
    """Một lớp con của `str` với `__str__` đổi theo lần gọi qua được mọi
    `isinstance` và làm cùng một field trả hai giá trị khác nhau (Audit P4)."""
    class Shifty(str):
        n = 0

        def __str__(self):
            Shifty.n += 1
            return f"đọc lần {Shifty.n}"

    hints = typing.get_type_hints(cls)
    str_fields = [
        f.name for f in dataclasses.fields(cls)
        if hints[f.name] is str or hints[f.name] == typing.Optional[str]
    ]
    if not str_fields:
        pytest.skip(f"{cls.__name__} không có field khai `str`")
    checks = dict(cls.__canonical_contract__)
    for name in str_fields:
        with pytest.raises((TypeError, ValueError), match="chuỗi thuần"):
            checks[name](Shifty("x"), cls.__name__)


@pytest.mark.parametrize("cls", canonical_types(), ids=lambda c: c.__name__)
def test_every_canonical_type_rejects_bool_where_int_is_declared(cls):
    """`True` là một `int` hợp lệ với `isinstance`, và `True == 1` nên nó còn
    va chạm khoá dict với index 1."""
    hints = typing.get_type_hints(cls)
    int_fields = [
        f.name for f in dataclasses.fields(cls)
        if hints[f.name] is int or hints[f.name] == typing.Optional[int]
    ]
    if not int_fields:
        pytest.skip(f"{cls.__name__} không có field khai `int`")
    checks = dict(cls.__canonical_contract__)
    for name in int_fields:
        with pytest.raises((TypeError, ValueError), match="số nguyên thuần"):
            checks[name](True, cls.__name__)


# ═══════════════════════════════════════════════════ A1–A3 — RecordRef

def test_a1_a_negative_index_cannot_be_expressed():
    """A1. `RecordRef(snapshot_id, -1, "forged")` từng dựng được, và
    `master.record()` IM LẶNG trả về employee CUỐI."""
    m = master()
    with pytest.raises(ValueError, match="không được âm"):
        RecordRef(m.snapshot_id, -1, "forged")


def test_a2_an_out_of_range_index_is_a_domain_error_not_an_indexerror():
    """A2. Cận trên cần biết master nên nó thuộc về `EmployeeMaster`."""
    m = master()
    with pytest.raises(ForeignRecordRef, match="vượt quá số record"):
        m.record(RecordRef(m.snapshot_id, 99, "forged"))
    with pytest.raises(ForeignRecordRef):
        m.ref_for_index(99)
    with pytest.raises(ForeignRecordRef):
        m.ref_for_index(-1)


def test_a2b_record_refuses_anything_that_is_not_a_recordref():
    with pytest.raises(ForeignRecordRef):
        master().record("không phải RecordRef")


def test_a3_replace_on_a_recordref_is_revalidated():
    """A3. Tái dựng qua `replace()` phải đi qua đúng phép kiểm như lần đầu."""
    with pytest.raises(ValueError, match="không được âm"):
        replace(valid_ref(), index=-1)


@pytest.mark.parametrize("kwargs, match", [
    ({"snapshot_id": None}, "không được là None"),
    ({"snapshot_id": ""}, "rỗng"),
    ({"index": True}, "số nguyên thuần"),
    ({"index": "0"}, "số nguyên thuần"),
    ({"label": ["không phải chuỗi"]}, "chuỗi thuần"),
    ({"label": ""}, "rỗng"),
])
def test_a3b_recordref_rejects_every_malformed_field(kwargs, match):
    base = dict(snapshot_id=master().snapshot_id, index=0, label="Ly[...]")
    base.update(kwargs)
    with pytest.raises((ValueError, TypeError), match=match):
        RecordRef(**base)


# ════════════════════════════════════════════════ A4–A6 — MappingResult

def test_a4_an_unknown_status_cannot_be_expressed():
    """A4. `status` đi thẳng vào `WorkingLine.employee_mapping_status`, nên một
    status bịa là dữ liệu nghiệp vụ sai, không chỉ một chuỗi xấu."""
    with pytest.raises(ValueError, match="không thuộc"):
        mapped_result(status="NOT_A_MAPPING_STATUS")


def test_a5_record_must_be_an_actual_recordref():
    with pytest.raises(CanonicalFieldError, match="RecordRef"):
        mapped_result(record="not-a-RecordRef")


def test_a6_a_mutable_alias_cannot_enter_a_mapping_result():
    shared = []
    with pytest.raises(CanonicalFieldError, match="chuỗi thuần"):
        mapped_result(normalized=shared)
    with pytest.raises(CanonicalFieldError, match="chuỗi thuần"):
        mapped_result(group={"a": 1})


def test_a6_an_any_typed_field_reports_the_mutable_alias_itself():
    """Khi annotation không loại được (`Any`), phép cấm container mutable là
    thứ duy nhất còn đứng — và nó phải đứng."""
    from app.modules.validation.employee_mapping import MappingStats

    check = dict(MappingStats.__canonical_contract__)["mapper"]
    with pytest.raises(CanonicalFieldError, match="mutable"):
        check([], "MappingStats")


def test_a6b_a_selected_record_contradicts_status_unmapped():
    with pytest.raises(ValueError, match="mâu thuẫn"):
        MappingResult(normalized=None, status=MAPPING_STATUS_UNMAPPED,
                      default_lead_source=None, include_in_kpi=None,
                      record=valid_ref())


def test_a6c_include_in_kpi_must_be_a_real_bool():
    """Một chuỗi `"false"` là truthy trong Python."""
    with pytest.raises(CanonicalFieldError, match="boolean"):
        mapped_result(include_in_kpi="false")


@pytest.mark.parametrize("status", [MAPPING_STATUS_MAPPED, MAPPING_STATUS_INACTIVE])
def test_a6d_a_mapped_result_must_carry_a_name_and_a_group(status):
    """`group` là chiều tra tỉ lệ quy đổi — thiếu nó là thiếu tiền."""
    with pytest.raises(ValueError, match="rỗng"):
        mapped_result(status=status, normalized=None)
    with pytest.raises(ValueError, match="rỗng"):
        mapped_result(status=status, group=None)


def test_a6e_an_unmapped_result_must_not_carry_a_name_or_group():
    with pytest.raises(ValueError, match="có\\s+giá trị"):
        MappingResult(normalized="Ly", status=MAPPING_STATUS_UNMAPPED,
                      default_lead_source=None, include_in_kpi=None)


# ══════════════════════ WAVE 2 — adversarial, không nhắm trực tiếp bởi bản sửa

def test_w1_two_recordrefs_can_no_longer_collide_via_bool_index():
    """`True == 1` nên `RecordRef(sid, True, l)` và `RecordRef(sid, 1, l)` từng
    BẰNG NHAU và cùng hash — hai danh tính trộn vào nhau trong `_rows_by_record`."""
    m = master()
    with pytest.raises(CanonicalFieldError):
        RecordRef(m.snapshot_id, True, "x")


def test_w4_replace_with_several_broken_fields_at_once():
    ok = EmployeeMapper(master()).resolve("Vũ Hạnh Ly 0868", date(2026, 1, 15))
    with pytest.raises((ValueError, TypeError)):
        replace(ok, status="BỊA", record=None, normalized=[], group={})


@pytest.mark.parametrize("protocol", [0, 2, 5])
def test_w5_pickle_reconstruction_goes_through_the_contract(protocol):
    """Canonical không sealed pickle được — nhưng phải qua constructor, nên
    một payload rác không hồi sinh thành object hợp lệ."""
    with pytest.raises(ValueError, match="không được âm"):
        pickle.loads(pickle.dumps(replace_free_recordref(-5), protocol=protocol))


def replace_free_recordref(index: int):
    """Dựng một payload pickle mang index xấu mà KHÔNG cần dựng object xấu:
    lấy object hợp lệ, pickle nó, rồi vá index trong tuple `__reduce__`."""
    good = valid_ref()
    rebuild, args = good.__reduce__()
    cls, values = args
    values = dict(values)
    values["index"] = index

    class _Payload:
        def __reduce__(self):
            return (rebuild, (cls, values))

    return _Payload()


def test_w6_deepcopy_of_a_valid_result_is_the_same_object():
    ok = mapped_result()
    assert copy.deepcopy(ok) is ok
    assert copy.copy(ok) is ok


def test_w11_an_any_typed_field_still_rejects_a_mutable_container():
    """`MappingStats.mapper: Any` — hợp đồng bỏ qua KIỂU nhưng không bỏ qua
    tính mutable."""
    from app.modules.validation.employee_mapping import MappingStats

    checks = dict(MappingStats.__canonical_contract__)
    with pytest.raises(CanonicalFieldError, match="mutable"):
        checks["mapper"]([], "MappingStats")


def test_w12_a_canonical_type_with_an_unresolvable_annotation_is_refused():
    """Nếu framework không đọc nổi kiểu thì nó không bảo đảm được gì, nên nó
    phải từ chối ngay lúc decorate chứ không im lặng bỏ qua field đó."""
    with pytest.raises(CanonicalContractViolation, match="annotation"):
        @canonical()
        @dataclass(frozen=True, slots=True)
        class Unresolvable:
            x: "KhongTonTaiODau"  # noqa: F821

            def __post_init__(self) -> None:
                pass


def test_w13_the_contract_runs_after_post_init_coercion():
    """Thứ tự quan trọng: `__post_init__` ÉP kiểu (`as_exact_str`), hợp đồng
    khẳng định TRẠNG THÁI CUỐI. Chạy hợp đồng trước sẽ loại nhầm đầu vào hợp lệ."""
    from tests.support.rows import affected

    row = affected(6)
    assert type(row.raw_original) is str
    assert type(row.source_row) is int


def test_w14_a_plain_frozen_dataclass_is_untouched():
    """Hợp đồng chỉ áp cho type mang `@canonical`; nó không phải một luật toàn
    cục âm thầm đổi hành vi của mọi dataclass trong repo."""
    @dataclass(frozen=True)
    class Plain:
        x: str

    assert Plain(x=["vẫn dựng được"]).x == ["vẫn dựng được"]
    assert not hasattr(Plain, "__canonical_contract__")


# ════════════════════════════════════════ NON-REGRESSION trên dữ liệu hợp lệ

def test_valid_construction_is_untouched():
    m = master()
    mapper = EmployeeMapper(m)
    got = mapper.resolve("Vũ Hạnh Ly 0868345633", date(2026, 1, 15))
    assert (got.normalized, got.status, got.group) == ("Ly", MAPPING_STATUS_MAPPED, "SALES")
    assert type(got.record) is RecordRef
    assert m.record(got.record).normalized == "Ly"
    assert m.record(m.refs[1]).normalized == "Kiên"
    assert mapper.resolve("Người Lạ", date(2026, 1, 15)).status == MAPPING_STATUS_UNMAPPED


def test_the_real_production_config_still_resolves():
    mapper = EmployeeMapper.from_yaml(REPO / "config" / "employees.yaml")
    assert len(mapper.records) == 8
    assert mapper.resolve("Mr Vinh 0900", date(2026, 6, 1)).group == "NOI_THANH"
    for index, ref in enumerate(mapper.refs):
        assert ref.index == index
        assert mapper.record(ref) is mapper.records[index]


def test_mapping_statuses_enum_has_a_single_home():
    """Enum có hai chỗ ở là đúng cái smell repair này đang đóng."""
    assert MAPPING_STATUSES == (
        MAPPING_STATUS_MAPPED, MAPPING_STATUS_UNMAPPED, MAPPING_STATUS_INACTIVE
    )
    source = (REPO / "app" / "modules" / "mapping" / "employee_mapper.py").read_text(encoding="utf-8")
    assert 'MAPPING_STATUSES = (' not in source, "enum phải chỉ khai ở domain/models.py"


# ══════════════════════════════════════ NGOÀI SCOPE R1-A — đóng đinh ranh giới

def test_out_of_scope_r1c_from_line_still_accepts_a_duck_typed_line():
    """**R1-C**, một sub-repair riêng. R1-A CỐ Ý không chạm."""
    from app.modules.validation.models import AffectedRow

    class FakeRaw:
        source_file = "BIA.xlsx"
        source_row = 99999

    class FakeLine:
        raw = FakeRaw()
        employee_raw = "Bịa"
        date = None

    assert AffectedRow.from_line(FakeLine()).source_row == 99999


def test_out_of_scope_r1d_frozen_mapping_values_stay_shallow():
    """**R1-D**, một sub-repair riêng. Hợp đồng field của R1-A cũng cố tình
    NÔNG: nó cấm chính field là container mutable, không đi vào bên trong
    tuple/mapping."""
    from app.modules.domain.canonical import FrozenMapping

    inner = ["a"]
    frozen = FrozenMapping({"k": inner})
    inner.append("b")
    assert frozen["k"] == ["a", "b"]
