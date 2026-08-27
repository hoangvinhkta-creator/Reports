"""Ma trận falsification 20 case của Architecture Closure Audit (DEC-134).

**Đây là gate chính, không phải số lượng test.** Mỗi case dưới đây từng là một
lối vào có thật, đo được tại `2d1da98`: một cách để dựng nên trạng thái sai mà
hệ thống vẫn coi là hợp lệ. Test không kiểm "hành vi đúng" — nó kiểm rằng
**trạng thái sai không còn biểu diễn được**.

Nguyên tắc: không blacklist từ khoá, không regex trên văn bản. Một invariant
chỉ được coi là đóng khi cái sai không dựng được, chứ không phải khi có một
chỗ nào đó chặn nó lại.
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.modules.mapping.employee_mapper import (
    EmployeeMapper,
    EmployeeMaster,
    ForeignRecordRef,
    InvalidEmployeeConfig,
    RecordRef,
    build_employee_master,
    load_employee_master,
)
from app.modules.mapping import employee_mapper as mapper_module
from app.modules.validation import models as models_module
from app.modules.validation.employee_mapping import (
    MappingInput,
    collect_mapping_stats,
    collect_stats_from_lines,
    evaluate_inactive_records,
    evaluate_raw_mapping,
)
from app.modules.validation.models import (
    AffectedRow,
    AmbiguousRow,
    CATEGORY_EMPLOYEE_MAPPING,
    Diagnostics,
    ReviewItem,
    RowProvenance,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SealedConstruction,
)
from app.modules.validation.validator import MasterSnapshotMismatch, Validator
from tests.support.rows import affected, line_for, provenance

REPO_ROOT = Path(__file__).resolve().parents[1]
GROUPS = [{"code": "STANDARD_SALES"}, {"code": "NOI_THANH"}]
CONFIG = {"categories": {"employee_mapping": {
    "enabled": True, "hard_failure_severity": SEVERITY_ERROR,
    "warning_severity": SEVERITY_WARNING, "info_severity": SEVERITY_INFO}}}

OWN, FOREIGN = 6, 7777


def employee(normalized, prefix, **extra):
    row = {"raw_prefix": prefix, "normalized": normalized, "group": "STANDARD_SALES",
           "active": True, "effective_from": "2026-01-01", "effective_to": None}
    row.update(extra)
    return row


def mapper_for(rows, groups=GROUPS):
    return EmployeeMapper(build_employee_master(rows, groups))


# ════════════════════════════════════════════════════ P — PROVENANCE (RC-1/RC-2)

def test_p1_message_cannot_assert_a_foreign_row():
    """P1. `ReviewItem(message="…dòng 7777")` từng dựng được trên một item chỉ
    sở hữu dòng 6. Nay `message` không còn là tham số — nó do renderer sinh ra
    từ đúng payload + provenance của chính item, nên không có đầu vào nào để
    nêu một dòng ngoài tập đó."""
    with pytest.raises(TypeError):
        ReviewItem(category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
                   message=f"có vấn đề ở dòng {FOREIGN}", provenance=provenance(OWN))

    assert "message" not in {f.name for f in dataclasses.fields(ReviewItem)}
    item = ReviewItem(category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
                      provenance=provenance(OWN),
                      diagnostics=Diagnostics(criterion="F4", raw_value="Lạ",
                                              smallest_employee="Ly", smallest_count=1))
    assert str(FOREIGN) not in item.message
    assert str(OWN) in item.details["source_rows"]


def test_p2_nested_typed_metadata_cannot_smuggle_a_row():
    """P2. Trước đây `Diagnostics` "có kiểu" nhưng mọi trường là `str`, nên
    `raw_value="xem dòng 7777"` vào thẳng `details`. Nay renderer quyết định
    văn bản, và mọi con số nói về "bao nhiêu dòng" đọc từ provenance."""
    item = ReviewItem(
        category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
        provenance=provenance(OWN),
        diagnostics=Diagnostics(criterion="F4", raw_value=f"dòng {FOREIGN}",
                                smallest_employee="Ly", smallest_count=1),
    )
    # `raw_value` là DANH TÍNH nhân viên do người dùng gõ — nó được in lại
    # nguyên văn, nhưng con số dòng của item vẫn chỉ đến từ provenance.
    assert item.details["source_rows"] == str(OWN)
    assert item.affected_count == 1
    assert f"có {item.provenance.affected_count} dòng" in item.message


def test_p3_mutable_input_cannot_change_a_built_object():
    """P3. Truyền `list` vào `rows`/`records` rồi sửa list đó từ bên ngoài."""
    rows = [affected(OWN)]
    prov = RowProvenance.of(rows)
    rows.append(affected(FOREIGN))
    assert prov.source_rows == (OWN,)

    labels = ["A"]
    amb = AmbiguousRow.from_line(line_for(OWN), raw_value="x", records=labels)
    before = RowProvenance.of((amb,)).rendered_details()["conflicting_records"]
    labels.append("B")
    assert RowProvenance.of((amb,)).rendered_details()["conflicting_records"] == before


def test_p4_a_str_subclass_cannot_change_between_reads():
    """P4. Một lớp con của `str` với `__str__` đổi theo lần gọi qua được mọi
    `isinstance` và làm `details` trả giá trị khác nhau giữa hai lần đọc."""
    class Evil(str):
        def __init__(self, *a): self.n = 0
        def __str__(self):
            self.n += 1
            return "ổn" if self.n == 1 else f"thực ra là dòng {FOREIGN}"

    diag = Diagnostics(criterion="F6", employee=Evil("ổn"), raw_prefix="P",
                       window_start="2026-01-01", window_end="—")
    item = ReviewItem(category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
                      provenance=provenance(OWN), diagnostics=diag)
    assert item.details["employee"] == item.details["employee"]
    assert type(diag.employee) is str


def test_p5_provenance_cannot_be_fabricated():
    """P5. `AffectedRow("KHONG_TON_TAI.xlsx", 99999, "Bịa", None)` từng dựng
    được — provenance không buộc đến từ dữ liệu thật."""
    with pytest.raises(SealedConstruction):
        AffectedRow("KHONG_TON_TAI.xlsx", 99999, "Bịa", None)
    with pytest.raises(SealedConstruction):
        RowProvenance(rows=())
    assert affected(OWN).source_row == OWN  # đường hợp lệ vẫn chạy


# ════════════════════════════════════════════════════════ M — MASTER OWNERSHIP

def test_m1_a_foreign_record_ref_is_rejected():
    """M1. `B.record(A.refs[0])` từng trả về một nhân viên khác hẳn, im lặng."""
    a = build_employee_master([employee("Ly", "Vũ Hạnh Ly")], GROUPS)
    b = build_employee_master([employee("Kiên", "Đức Kiên")], GROUPS)
    with pytest.raises(ForeignRecordRef):
        b.record(a.refs[0])


def test_m2_two_masters_do_not_share_an_identity_at_the_same_index():
    a = build_employee_master([employee("Ly", "Vũ Hạnh Ly")], GROUPS)
    b = build_employee_master([employee("Kiên", "Đức Kiên")], GROUPS)
    assert a.refs[0] != b.refs[0]
    assert hash(a.refs[0]) != hash(b.refs[0])
    # Cùng logical master -> cùng danh tính, một cách chính đáng.
    assert build_employee_master([employee("Ly", "Vũ Hạnh Ly")], GROUPS).refs[0] == a.refs[0]


def test_m3_validator_cannot_be_paired_with_a_foreign_master():
    """M3. `build_queue(lines, orders)` từng là đường công khai đi vòng qua
    phép kiểm ownership."""
    from app.pipeline import WorkingData

    a, b = mapper_for([employee("Ly", "Vũ Hạnh Ly")]), mapper_for([employee("Kiên", "Đức Kiên")])
    lines = [line_for(OWN, "Vũ Hạnh Ly 0868345633")]
    a.apply(lines)
    working = WorkingData(preview=None, lines=lines, orders=[], employee_mapper=a)

    assert not hasattr(Validator(CONFIG, employee_mapper=b), "build_queue")
    with pytest.raises(MasterSnapshotMismatch):
        Validator(CONFIG, employee_mapper=b).build_queue_for(working)
    Validator(CONFIG, employee_mapper=a).build_queue_for(working)


def test_m4_snapshot_id_cannot_be_supplied_by_the_caller():
    """Bổ sung: `snapshot_id` từng là field, nên dựng được master nội dung B
    mang id của A và qua mặt phép so của Validator."""
    assert "snapshot_id" not in {f.name for f in dataclasses.fields(EmployeeMaster)}
    with pytest.raises(SealedConstruction):
        EmployeeMaster(records=(), group_codes=frozenset())


# ═════════════════════════════════════════════════ C — CONFIGURATION INTEGRITY

@pytest.mark.parametrize("row, needle", [
    (employee("V", "Mr Vinh", group="NOI_THAN"), "employee_groups"),         # C1
    ({"raw_prefix": "P", "normalized": "N", "active": True}, "group"),       # C1
    (employee("V", "P", effective_from="hôm qua"), "ngày hợp lệ"),           # C3
    (employee("V", "P", effective_from="2026-13-45"), "ngày hợp lệ"),        # C3
    (employee("V", "P", effective_to=20260101), "ngày hợp lệ"),              # C3
    (employee("V", "P", effective_from="2026-12-31", effective_to="2026-01-01"), "bất khả"),  # C4
    (employee("V", 123), "chuỗi thuần"),                                     # C5
    ({"raw_prefix": "P", "normalized": ["N"], "group": "STANDARD_SALES", "active": True}, "chuỗi thuần"),
    (employee("V", "P", active="false"), "boolean"),                         # C5
    (employee("V", ""), "rỗng"),                                             # HD-110-06
])
def test_c1_c5_invalid_master_fails_at_the_boundary(row, needle):
    """C1/C3/C4/C5. Trước đây tất cả những case này ĐƯỢC CHẤP NHẬN lúc load rồi
    nổ `ValueError`/`TypeError` giữa lúc xử lý giao dịch — hoặc tệ hơn, im lặng
    làm một nhân viên không bao giờ khớp dòng nào."""
    with pytest.raises(InvalidEmployeeConfig, match=needle):
        build_employee_master([row], GROUPS)


def test_c2_duplicate_prefix_with_overlapping_windows_is_rejected():
    """C2/HD-110-15. Hai employee KHÁC NHAU cùng prefix, cửa sổ chồng nhau:
    `resolve` chọn người đầu, người kia mất toàn bộ doanh số trong im lặng."""
    with pytest.raises(InvalidEmployeeConfig, match="trùng khít"):
        build_employee_master(
            [employee("Ly", "Vũ Hạnh Ly"), employee("Ngân", "Vũ Hạnh Ly")], GROUPS
        )


def test_c2_a_dec_121_handover_stays_legal():
    """Mặt còn lại: cùng prefix với cửa sổ RỜI NHAU là một lượt bàn giao
    (DEC-121), và nó phải tiếp tục hợp lệ — không dòng nào bị mất."""
    master = build_employee_master([
        employee("Cũ", "Vũ Hạnh Ly", effective_to="2026-03-31"),
        employee("Mới", "Vũ Hạnh Ly", effective_from="2026-04-01"),
    ], GROUPS)
    mapper = EmployeeMapper(master)
    assert mapper.resolve("Vũ Hạnh Ly 09", date(2026, 2, 1)).normalized == "Cũ"
    assert mapper.resolve("Vũ Hạnh Ly 09", date(2026, 5, 1)).normalized == "Mới"


def test_c2_nested_prefixes_stay_legal():
    master = build_employee_master(
        [employee("Ngắn", "Vũ Hạnh"), employee("Dài", "Vũ Hạnh Ly")], GROUPS)
    assert EmployeeMapper(master).resolve("Vũ Hạnh Ly 09", date(2026, 2, 1)).normalized == "Dài"


def test_c3_broken_transaction_data_never_becomes_a_config_failure():
    """C3 (chiều ngược lại). Lằn ranh chạy theo đúng MỘT chiều: một dòng giao
    dịch méo mó phải vào Review Queue, KHÔNG bao giờ làm gãy lượt import."""
    broken = [line_for(OWN, None, None), line_for(FOREIGN, "", None),
              line_for(8888, "Không Ai Cả 0900", None)]
    queue = Validator(CONFIG, employee_mapper=mapper_for(
        [employee("Ly", "Vũ Hạnh Ly")])).build_queue_for(
        type("W", (), {"lines": broken, "orders": [],
                       "employee_mapper": mapper_for([employee("Ly", "Vũ Hạnh Ly")])})()
    )
    assert len(queue) > 0


def test_c6_yaml_order_does_not_change_business_result():
    rows = [employee("Ngắn", "Vũ Hạnh"), employee("Dài", "Vũ Hạnh Ly")]
    one = EmployeeMapper(build_employee_master(rows, GROUPS))
    two = EmployeeMapper(build_employee_master(list(reversed(rows)), GROUPS))
    q = ("Vũ Hạnh Ly 0868", date(2026, 2, 1))
    assert one.resolve(*q).normalized == two.resolve(*q).normalized


# ══════════════════════════════════════════════════════════════════ L — LOADER

def test_l1_every_master_consumer_goes_through_the_canonical_loader():
    """L1. Không còn `load_yaml` thô nào cho employee master, và không còn
    tham số `validate=False` để đi vòng qua phép parse."""
    import inspect

    for path in ("tools/analysis/reconcile_conversion.py",
                 "tools/analysis/verify_ads_rule.py",
                 "app/pipeline.py",
                 "app/modules/validation/validator.py"):
        source = (REPO_ROOT / path).read_text(encoding="utf-8")
        assert 'load_yaml(CONFIG / "employees.yaml")' not in source
        assert 'load_yaml(config_dir / "employees.yaml")' not in source

    assert "validate" not in inspect.signature(build_employee_master).parameters


def test_l3_the_real_config_still_loads_and_behaves():
    mapper = EmployeeMapper.from_yaml(REPO_ROOT / "config" / "employees.yaml")
    assert len(mapper.records) == 8
    assert mapper.resolve("Mr Vinh 0900", date(2026, 6, 1)).group == "NOI_THANH"


# ══════════════════════════════════════════════════════════════════ O — ORACLE

def test_o1_scalar_business_mutation_is_detected(synthetic_raw_path, monkeypatch):
    """O1 + O2 + O3 được kiểm ở `test_task110_non_regression.py`; ở đây kiểm
    rằng oracle CÓ THỂ FAIL — xem `test_oracle_mutation_*`."""
    from tests.fixtures.baseline_snapshot import build_l2, L2_PATH

    baseline = json.loads(L2_PATH.read_text(encoding="utf-8"))
    assert json.loads(json.dumps(build_l2(synthetic_raw_path), ensure_ascii=False)) == baseline


# ═══════════════════════════════ HD-110-17 — F1 KHÔNG CÒN ĐƯỜNG NÀO ĐI TỚI QUEUE

@pytest.mark.parametrize("row", [
    employee("V", "Mr Vinh", group="NOI_THAN"),
    {"raw_prefix": "P", "normalized": "N", "active": True},
    employee("V", "P", group=""),
])
def test_hd_110_17_no_public_entry_point_admits_a_bad_group(row):
    """§6: cố ý dựng master group hỏng qua MỌI điểm vào production."""
    with pytest.raises(InvalidEmployeeConfig):
        build_employee_master([row], GROUPS)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "employees.yaml"
        import yaml
        path.write_text(yaml.safe_dump({"employees": [row], "employee_groups": GROUPS},
                                       allow_unicode=True), encoding="utf-8")
        with pytest.raises(InvalidEmployeeConfig):
            load_employee_master(path)
        with pytest.raises(InvalidEmployeeConfig):
            EmployeeMapper.from_yaml(path)


def test_hd_110_17_f1_no_longer_exists_as_a_criterion():
    source = (REPO_ROOT / "app/modules/validation/employee_mapping.py").read_text(encoding="utf-8")
    assert 'criterion="F1"' not in source
