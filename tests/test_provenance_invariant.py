"""F1–F9 — ma trận falsification của Independent Review #5 (DEC-132).

**Vì sao cần một file riêng.** Bốn vòng review trước đều đóng đúng cái
representation mà reviewer chỉ ra, rồi vòng sau tìm ra cái kế tiếp:
`source_row` → `source_rows` → `raw_variants` → `ambiguous_rows` → `details`.
Các test ở đây không kiểm một representation nào cả. Chúng kiểm rằng trạng
thái sai **không dựng được**, và — quan trọng không kém — rằng chính cái
oracle đang kiểm điều đó THỰC SỰ FAIL khi bị tiêm provenance lạ (F6).

Review #5, Finding 2 bác bỏ test falsification cũ vì nó gọi một dòng là
"không sở hữu" rồi lại đưa chính dòng đó vào `affected_rows`. Đó là tautology.
Ở đây, F5/F6 quét **mọi chuỗi** của một `ReviewItem` đã serialize và bắt bất
kỳ số dòng nào thuộc về lô nhưng KHÔNG thuộc về item — không dựa vào một danh
sách trường nào cả.
"""

from __future__ import annotations

import dataclasses
import re
from datetime import date

import pytest

from app.modules.domain.models import MAPPING_STATUS_MAPPED
from app.modules.importing.normalizer import normalize_line
from app.modules.mapping.employee_mapper import (
    EmployeeMapper,
    InvalidEmployeeConfig,
    RecordRef,
)
from app.modules.validation.employee_mapping import (
    MappingFinding,
    collect_mapping_stats,
    evaluate_inactive_records,
    evaluate_raw_mapping,
)
from app.modules.validation.models import (
    AffectedRow,
    CATEGORY_EMPLOYEE_MAPPING,
    ROW_BEARING_DETAIL_KEYS,
    ReviewItem,
    RowProvenance,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
)
from app.modules.validation.validator import Validator
from tests.factories import make_raw_row

GROUPS = {"STANDARD_SALES"}

CONFIG = {
    "categories": {
        "employee_mapping": {
            "enabled": True,
            "hard_failure_severity": SEVERITY_ERROR,
            "warning_severity": SEVERITY_WARNING,
            "info_severity": SEVERITY_INFO,
        }
    }
}

# Số dòng cố ý đặt xa mọi con số khác trong dữ liệu (ngày, tiền, số lượng),
# để phép quét số nguyên ở F5 không thể dương tính giả.
ROW_MAPPED = 6101
ROW_UNMAPPED = 7202
ROW_THIRD = 8303


def employee(normalized, prefix, **extra):
    row = {
        "raw_prefix": prefix,
        "normalized": normalized,
        "group": "STANDARD_SALES",
        "active": True,
        "effective_from": "2026-01-01",
        "effective_to": None,
    }
    row.update(extra)
    return row


def _line(employee_raw, source_row, when=date(2026, 1, 15), normalized=None):
    working = normalize_line(
        make_raw_row(source_row=source_row, employee_raw=employee_raw, date_=when)
    )
    if normalized:
        working.employee_normalized = normalized
        working.employee_mapping_status = MAPPING_STATUS_MAPPED
        working.employee_group = "STANDARD_SALES"
    return working


# ===================================================================== F1–F4
# Trạng thái sai không BIỂU DIỄN được.


def test_f1_mapping_finding_has_no_arbitrary_details_channel():
    """`MappingFinding(details=...)` phải không dựng được."""
    names = {f.name for f in dataclasses.fields(MappingFinding)}
    assert "details" not in names
    assert not any(
        f.type is dict or "dict" in str(f.type) for f in dataclasses.fields(MappingFinding)
    ), "một trường dict tùy ý sẽ mở lại đúng đường thoát provenance"

    with pytest.raises(TypeError):
        MappingFinding(criterion="F4", bucket="WARNING", message="x",
                       details={"ambiguous_rows": "dòng 7"})


def test_f2_review_item_affected_count_cannot_be_assigned():
    """`ReviewItem(affected_count=...)` phải không dựng được."""
    names = {f.name for f in dataclasses.fields(ReviewItem)}
    assert "affected_count" not in names
    assert "source_row" not in names

    with pytest.raises(TypeError):
        ReviewItem(category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
                   message="x", affected_count=3)

    item = ReviewItem(
        category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO, message="x",
        provenance=RowProvenance((AffectedRow("s.xlsx", ROW_MAPPED),)),
    )
    assert item.affected_count == 1 and item.source_row == ROW_MAPPED


@pytest.mark.parametrize("key", sorted(ROW_BEARING_DETAIL_KEYS))
def test_f3_row_bearing_details_are_rejected(key):
    """Không caller nào ghi được khóa mang thông tin dòng."""
    with pytest.raises(ValueError, match=key):
        ReviewItem(
            category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO, message="x",
            provenance=RowProvenance((AffectedRow("s.xlsx", ROW_MAPPED),)),
            diagnostics={key: str(ROW_UNMAPPED)},
        )


def test_f4_select_effective_record_is_gone():
    """Không còn bản cài đặt thứ hai để mà drift."""
    with pytest.raises(ImportError):
        from app.modules.validation.employee_mapping import (  # noqa: F401
            select_effective_record,
        )


# ======================================================================== F5
# Quét provenance đã serialize: KHÔNG dựa vào danh sách trường.


def _mixed_batch():
    """Một dòng map được và một dòng KHÔNG, cùng canonical identity.

    Đây đúng là hình dạng mà Review #4 và #5 dùng: nếu provenance nới rộng
    theo identity, F4 về dòng unmapped sẽ nhắc tới dòng đã map bên cạnh.
    """
    employees = [employee("Ly", "Vũ Hạnh Ly"), employee("Vắng", "Không Ai")]
    raw = "Vũ Hạnh Ly 0868345633"
    lines = [
        _line(raw, ROW_MAPPED, normalized="Ly"),   # map được
        _line(raw, ROW_UNMAPPED),                  # KHÔNG map, cùng identity
        _line(raw, ROW_THIRD),                     # KHÔNG map, cùng identity
    ]
    return employees, lines


def _all_row_numbers(lines):
    return {line.raw.source_row for line in lines}


_INT = re.compile(r"\d+")


def _foreign_rows_in(
    item: ReviewItem, batch_rows: set[int], owned: set[int] | None = None
) -> set[int]:
    """Mọi số dòng THUỘC LÔ nhưng KHÔNG thuộc item, xuất hiện ở bất kỳ chuỗi nào.

    Quét cả `message`, cả từng khóa và từng giá trị của `details`. Không có
    whitelist trường: một representation mới thêm vào ngày mai cũng bị quét.

    `owned` mặc định là provenance của chính item — đó là câu hỏi "item có nói
    về dòng nào ngoài tập nó sở hữu không?". Truyền `owned` tường minh để hỏi
    câu chặt hơn: "item có nói về dòng nào ngoài tập mà TIÊU CHÍ thật sự sở
    hữu không?" — phân biệt này quan trọng, vì nới chính tuple provenance là
    một lớp lỗi khác với việc rò rỉ qua một representation.
    """
    owned = set(item.provenance.source_rows) if owned is None else owned
    forbidden = batch_rows - owned
    haystack = [item.message, str(item.source_row), str(item.affected_count)]
    for key, value in item.details.items():
        haystack.extend([key, str(value)])
    found = set()
    for text in haystack:
        for token in _INT.findall(text):
            if int(token) in forbidden:
                found.add(int(token))
    return found


def _items_for(employees, lines):
    validator = Validator(
        CONFIG,
        employee_mapper=EmployeeMapper(employees, validate=False),
        employee_groups=GROUPS,
    )
    queue = validator.build_queue(lines, [])
    return queue.by_category(CATEGORY_EMPLOYEE_MAPPING)


def test_f5_no_serialized_item_names_a_foreign_source_row():
    employees, lines = _mixed_batch()
    batch_rows = _all_row_numbers(lines)
    items = _items_for(employees, lines)
    assert items, "fixture phải sinh ra finding"

    for item in items:
        foreign = _foreign_rows_in(item, batch_rows)
        assert not foreign, (
            f"{item.details.get('criterion')}: nhắc tới dòng {sorted(foreign)} "
            f"ngoài provenance {item.provenance.source_rows}"
        )


def test_f5_holds_for_ambiguity_and_inactive_findings_too():
    """Cùng phép quét trên F3 và F6 — hai tiêu chí mang provenance giàu nhất."""
    # `Vũ Hạnh Ly ...` khớp CẢ HAI prefix và cả hai cùng hiệu lực → F3.
    # `Vũ Hạnh 0900` chỉ khớp record đã đóng → F6.
    handover = [
        employee("Ly", "Vũ Hạnh Ly"),
        employee("Hanh", "Vũ Hạnh", active=False),
    ]
    lines = [
        _line("Vũ Hạnh Ly 0868345633", ROW_MAPPED, normalized="Ly"),
        _line("Vũ Hạnh 0900000001", ROW_UNMAPPED, when=date(2026, 2, 20),
              normalized="Hanh"),
        _line("Người Lạ 0900000009", ROW_THIRD),
    ]
    batch_rows = _all_row_numbers(lines)
    items = _items_for(handover, lines)
    criteria = {item.details.get("criterion") for item in items}
    assert {"F3", "F6"} & criteria, f"fixture phải phát F3/F6, chỉ có {criteria}"

    for item in items:
        assert not _foreign_rows_in(item, batch_rows)


# ======================================================================== F6
# Mutation: chứng minh oracle F5 THỰC SỰ fail khi bị tiêm provenance lạ.


def test_f6_the_sweep_actually_fails_on_injected_foreign_provenance():
    """Falsification thật, không phải tautology.

    Test cũ đưa dòng lạ VÀO `affected_rows` rồi khẳng định nó xuất hiện — tức
    là chỉ chứng minh phép cộng hoạt động. Ở đây dòng lạ được tiêm vào ĐÚNG
    kênh mà Review #5 chỉ ra (một representation nói về dòng ngoài tập sở
    hữu), còn provenance giữ nguyên. Nếu `_foreign_rows_in` không bắt được,
    thì mọi kết quả PASS ở F5 đều vô nghĩa.
    """
    employees, lines = _mixed_batch()
    batch_rows = _all_row_numbers(lines)
    honest = _items_for(employees, lines)
    assert all(not _foreign_rows_in(i, batch_rows) for i in honest)

    victim = next(i for i in honest if i.provenance.rows)
    foreign_row = next(iter(batch_rows - set(victim.provenance.source_rows)))

    # Tiêm qua `message` — một representation mà không guard nào chặn.
    widened = dataclasses.replace(
        victim, message=f"{victim.message} (xem thêm dòng {foreign_row})"
    )
    detected = _foreign_rows_in(widened, batch_rows)
    assert detected == {foreign_row}, (
        "oracle F5 KHÔNG bắt được provenance lạ — mọi PASS ở F5 là vô nghĩa"
    )


def test_f6_the_sweep_also_catches_a_widened_provenance_tuple():
    """Biến thể thứ hai: nới chính tuple provenance.

    `affected_count` và `source_rows` cùng dẫn xuất nên chúng không bao giờ
    bất đồng — nhưng item khi đó nói về một dòng mà tiêu chí không sở hữu.
    Phép quét phải thấy điều đó khi so với tập dòng ĐÚNG của tiêu chí.
    """
    employees, lines = _mixed_batch()
    items = _items_for(employees, lines)
    victim = next(i for i in items if i.provenance.rows)
    true_rows = set(victim.provenance.source_rows)
    # F4 sở hữu đúng các dòng KHÔNG map được; dòng đã map là dòng lạ với nó —
    # đúng kịch bản Review #4 Finding 2.
    foreign_row = ROW_MAPPED
    assert foreign_row not in true_rows

    widened = dataclasses.replace(
        victim,
        provenance=RowProvenance(
            victim.provenance.rows + (AffectedRow("s.xlsx", foreign_row, "Lạ"),)
        ),
    )
    assert widened.affected_count == len(victim.provenance.rows) + 1
    # Đo với tập dòng THẬT của tiêu chí (`owned=true_rows`), không với tập mà
    # item tự khai — nếu không, một item nới provenance sẽ tự hợp thức hóa
    # chính mình.
    assert _foreign_rows_in(
        widened, true_rows | {foreign_row}, owned=true_rows
    ) == {foreign_row}
    # Và bằng chứng rằng phân biệt trên là thật: đo theo tập tự khai thì
    # KHÔNG bắt được — đó chính là lý do F7/F8 phải tồn tại riêng, để canh
    # việc tiêu chí quy dòng cho đúng record ngay từ đầu.
    assert _foreign_rows_in(widened, true_rows | {foreign_row}) == set()


# ======================================================================== F7
# Record identity không va chạm.


def _twins():
    """Hai record trùng khít name + prefix + cửa sổ hiệu lực, khác active/group.

    Trước Review #5, `_record_key` gộp hai record này làm một, nên F6 của
    record `active: false` nhặt đúng các dòng mà production đã gán cho record
    `active: true` — và tố cáo một nhân viên đang làm việc.
    """
    active = employee("Vinh", "Mr Vinh", group="STANDARD_SALES", active=True)
    closed = employee("Vinh", "Mr Vinh", group="NOI_THANH", active=False)
    return [active, closed]


def test_f7_duplicate_records_do_not_collide_on_identity():
    rows = _twins()
    mapper = EmployeeMapper(rows, validate=False)

    refs = {mapper.resolve_record("Mr Vinh 0900", date(2026, 2, 1))}
    assert len(mapper.refs) == 2
    assert len(set(mapper.refs)) == 2, "hai record phải có hai danh tính"
    assert refs.pop() == mapper.ref_for_index(0), "production chọn record đầu"


def test_f7_f6_fires_only_on_the_record_production_actually_selected():
    rows = _twins()
    mapper = EmployeeMapper(rows, validate=False)
    lines = [_line("Mr Vinh 0900", ROW_MAPPED, normalized="Vinh")]
    stats = collect_mapping_stats(lines, mapper)

    selected = mapper.resolve_record("Mr Vinh 0900", date(2026, 1, 15))
    assert selected == mapper.ref_for_index(0)

    # Record production ĐÃ chọn (index 0) sở hữu dòng; record kia không.
    assert stats.rows_for_record(rows[0]) != ()
    assert stats.rows_for_record(rows[1]) == (), (
        "record không được production chọn vẫn nhặt được dòng — collision đã tái phát"
    )

    # F6 chấm trên record `active: false` (index 1) phải im lặng.
    findings = evaluate_inactive_records(list(mapper.records), stats)
    assert findings == [], f"F6 phát sai trên record production không chọn: {findings}"


def test_f7_a_genuinely_inactive_selected_record_still_raises_f6():
    """Mặt còn lại: F7 không được làm F6 câm hẳn."""
    rows = [employee("Vinh", "Mr Vinh", active=False)]
    mapper = EmployeeMapper(rows, validate=False)
    lines = [_line("Mr Vinh 0900", ROW_MAPPED, normalized="Vinh")]
    stats = collect_mapping_stats(lines, mapper)

    findings = evaluate_inactive_records(list(mapper.records), stats)
    assert len(findings) == 1 and findings[0].criterion == "F6"
    assert findings[0].source_rows == (ROW_MAPPED,)


# ======================================================================== F8
# Không tồn tại bản cài đặt khớp thứ hai — ma trận raw × date.


_MATRIX_RAW = [
    None, "", "   ",
    "Vũ Hạnh Ly 0868345633",
    "Vũ  Hạnh Ly 0868345633",     # khoảng trắng đôi
    " Vũ Hạnh Ly 0868345633",     # khoảng trắng đầu
    "VŨ HẠNH LY 0868345633",      # hoa
    "vũ hạnh ly 0868345633",      # thường
    "Vũ Hạnh",                    # prefix cụt
    "Người Lạ 0900000009",
]
_MATRIX_DATES = [None, date(2025, 12, 31), date(2026, 1, 1),
                 date(2026, 3, 31), date(2026, 4, 1), date(2026, 6, 15)]


def test_f8_row_attribution_matches_production_on_the_whole_matrix():
    """Mọi dòng được quy về record NÀO — phải luôn là record production chọn.

    Đây là chỗ DRIFT C từng sống: collector cũ khớp prefix trên chuỗi đã
    normalize trong khi production khớp trên chuỗi thô, nên một dòng
    production để `unmapped` vẫn bị quy về một record.
    """
    rows = [
        employee("Ly", "Vũ Hạnh Ly", effective_to="2026-03-31"),
        employee("Ly2", "Vũ Hạnh Ly", effective_from="2026-04-01"),
        employee("Hanh", "Vũ Hạnh"),
    ]
    mapper = EmployeeMapper(rows, validate=False)

    for index, raw_value in enumerate(_MATRIX_RAW):
        for when in _MATRIX_DATES:
            expected = mapper.resolve_record(raw_value, when)
            result = mapper.resolve(raw_value, when)
            # `resolve()` được viết TRÊN `resolve_record()`: không có nhánh thứ hai.
            assert result.record == expected, (raw_value, when)
            if expected is None:
                assert result.normalized is None, (raw_value, when)
            else:
                assert result.normalized == mapper.record(expected)["normalized"]

            if raw_value and when:
                line = _line(raw_value, ROW_MAPPED + index, when=when,
                             normalized=result.normalized)
                stats = collect_mapping_stats([line], mapper)
                owned = [
                    record
                    for record in mapper.records
                    if stats.rows_for_record(record)
                ]
                if expected is None:
                    assert owned == [], (raw_value, when, "quy dòng cho record ma")
                else:
                    assert owned == [mapper.record(expected)], (raw_value, when)


def test_f8_ambiguity_uses_production_string_semantics():
    """F3 không được normalize theo cách riêng rồi kết luận ambiguity (D3).

    Một chuỗi mà production coi là `unmapped` thì không thể là bằng chứng hai
    master record cùng hiệu lực.
    """
    rows = [employee("A", "Vũ Hạnh Ly"), employee("B", "Vũ Hạnh")]
    mapper = EmployeeMapper(rows, validate=False)
    raw_value = "Vũ  Hạnh Ly 0868345633"  # khoảng trắng đôi: production KHÔNG khớp

    assert mapper.resolve_record(raw_value, date(2026, 2, 1)) is None
    stats = collect_mapping_stats(
        [_line(raw_value, ROW_UNMAPPED, when=date(2026, 2, 1))], mapper
    )
    assert stats.ambiguities == {}, (
        "F3 kết luận ambiguity trên chuỗi mà production để unmapped — drift đã tái phát"
    )


# ======================================================================== F9
# Master data hỏng fail-fast tại biên config (HD-110-06).


@pytest.mark.parametrize(
    "record, needle",
    [
        ({"normalized": "Ly", "group": "G", "active": True}, "raw_prefix"),
        ({"raw_prefix": "", "normalized": "Ly", "group": "G", "active": True}, "rỗng"),
        ({"raw_prefix": "   ", "normalized": "Ly", "group": "G", "active": True}, "rỗng"),
        ({"raw_prefix": "Ly", "group": "G", "active": True}, "normalized"),
        ({"raw_prefix": "Ly", "normalized": "  ", "group": "G", "active": True}, "rỗng"),
        ({"raw_prefix": "Ly", "normalized": "Ly", "active": True}, "group"),
        ({"raw_prefix": "Ly", "normalized": "Ly", "group": "G"}, "active"),
        ({"raw_prefix": "Ly", "normalized": "Ly", "group": "G", "active": "false"},
         "boolean"),
    ],
)
def test_f9_invalid_employee_config_fails_fast(record, needle):
    with pytest.raises(InvalidEmployeeConfig, match=needle):
        EmployeeMapper([record])


def test_f9_empty_prefix_never_becomes_a_catch_all():
    """Lý do luật tồn tại: prefix rỗng khớp MỌI chuỗi.

    Nếu nó lọt qua, mọi dòng lẽ ra `unmapped` sẽ được gán cho một người —
    tức là dời quyền sở hữu KPI vì một lỗi gõ.
    """
    bad = employee("Rỗng", "")
    with pytest.raises(InvalidEmployeeConfig):
        EmployeeMapper([bad])

    # Và nếu ai đó cố tình bỏ qua validate, hành vi catch-all vẫn là thật —
    # đó chính là điều luật này ngăn không cho vào production.
    unchecked = EmployeeMapper([bad], validate=False)
    assert unchecked.resolve("Bất Kỳ Ai 0900", date(2026, 2, 1)).normalized == "Rỗng"


def test_f9_the_real_config_passes_validation():
    """Master data thật phải hợp lệ — luật mới không được chặn chính dự án."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    mapper = EmployeeMapper.from_yaml(repo_root / "config" / "employees.yaml")
    assert len(mapper.records) > 0
