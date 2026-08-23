"""TD-001 — F2/F4 must reach the production Review Queue.

CHECK-110-12 and CHECK-110-13.

Why this matters more than it looks: a swallowed F4 means a real salesperson
is missing from master data, every row they sold resolves to `Unresolved`
(DEC-127 §8), and none of their revenue lands in anybody's KPI. That is a
payroll defect that leaves no trace in the numbers — it just looks like the
person sold nothing.

Until TASK-110 these criteria only ran inside `tools/analysis/
reconcile_conversion.py`, a script somebody runs by hand. These tests pin that
they now run on the import path itself.
"""

from __future__ import annotations

import unicodedata
from datetime import date
from decimal import Decimal

from app.modules.domain.models import MAPPING_STATUS_MAPPED
from app.modules.mapping.employee_mapper import EmployeeMapper
from app.modules.importing.normalizer import normalize_line
from app.modules.validation.employee_mapping import (
    collect_mapping_stats,
    evaluate_inactive_records,
    evaluate_raw_mapping,
    select_effective_record,
)
from app.modules.validation.models import (
    CATEGORY_EMPLOYEE_MAPPING,
    CATEGORY_MISSING,
    DETAIL_AMBIGUOUS_ROWS,
    DETAIL_BATCH_ROWS,
    DETAIL_CONFLICTING_RECORDS,
    DETAIL_CRITERION,
    DETAIL_DATASET_RANGE,
    DETAIL_EMPLOYEE,
    DETAIL_RAW_VALUE,
    DETAIL_RAW_VARIANTS,
    DETAIL_SOURCE_ROWS,
    SCOPE_BATCH,
    SCOPE_ROW,
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


def mapped_line(normalized, employee_raw, *, source_row=6, when=date(2026, 1, 15)):
    working = normalize_line(
        make_raw_row(source_row=source_row, employee_raw=employee_raw, date_=when)
    )
    working.employee_normalized = normalized
    working.employee_mapping_status = MAPPING_STATUS_MAPPED
    working.employee_group = "STANDARD_SALES"
    return working


def unmapped_line(employee_raw, *, source_row=6, when=date(2026, 1, 15)):
    return normalize_line(
        make_raw_row(source_row=source_row, employee_raw=employee_raw, date_=when)
    )


def queue_for(lines, employee_rows, groups=GROUPS):
    validator = Validator(CONFIG, employee_rows=employee_rows, employee_groups=groups)
    return validator.build_queue(lines, [])


def items_of(queue, criterion=None, severity=None):
    items = queue.by_category(CATEGORY_EMPLOYEE_MAPPING)
    if criterion:
        items = [i for i in items if i.details.get(DETAIL_CRITERION) == criterion]
    if severity:
        items = [i for i in items if i.severity == severity]
    return items


def messages(queue, severity=None):
    return [item.message for item in items_of(queue, severity=severity)]


# --------------------------------------------------------- CHECK-110-12 (F2)

def test_f2_reaches_the_production_review_queue():
    """A configured, active, in-period employee that matched no row."""
    employees = [employee("Ly", "Vũ Hạnh Ly"), employee("Kiên", "Đức Kiên")]
    lines = [mapped_line("Ly", "Vũ Hạnh Ly 0868345633")]

    warnings = messages(queue_for(lines, employees), SEVERITY_WARNING)

    assert any("F2" in message and "Kiên" in message for message in warnings)


def test_f2_stays_silent_for_an_employee_legitimately_absent():
    """`active: false` is an expected absence, reported as INFO rather than
    as a warning — otherwise readers learn to ignore F2."""
    employees = [
        employee("Ly", "Vũ Hạnh Ly"),
        employee("Nghỉ", "Người Đã Nghỉ", active=False),
    ]
    queue = queue_for([mapped_line("Ly", "Vũ Hạnh Ly 0868345633")], employees)

    assert not any("Nghỉ" in m for m in messages(queue, SEVERITY_WARNING))
    assert any("Nghỉ" in m for m in messages(queue, SEVERITY_INFO))


# --------------------------------------------------------- CHECK-110-13 (F4)

def test_f4_reaches_the_production_review_queue():
    """An unmapped name carrying at least as many rows as the smallest mapped
    employee — the signal that master data is missing a real person."""
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line("Thảo Linh 0900000001", source_row=7),
        unmapped_line("Thảo Linh 0900000001", source_row=8),
    ]

    warnings = messages(queue_for(lines, employees), SEVERITY_WARNING)

    assert any("F4" in m and "Thảo Linh" in m for m in warnings)


def test_f2_and_f4_never_raise_and_never_empty_the_queue_of_other_findings():
    """TD-001 warnings are diagnostics. They must not be able to stop an
    import — that is the whole reason they are warnings and not failures."""
    employees = [employee("Ly", "Vũ Hạnh Ly"), employee("Kiên", "Đức Kiên")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line("Thảo Linh 0900000001", source_row=7),
    ]

    queue = queue_for(lines, employees)  # must not raise

    assert len(queue.by_category(CATEGORY_EMPLOYEE_MAPPING)) > 0


# ------------------------------------------------ Invariants F1 / F3 / F5

def test_hard_failures_are_surfaced_rather_than_dropped():
    """F1: a group nobody declared. An already-violated invariant reaching the
    queue is surfacing only — it changes no result and blocks no import."""
    employees = [employee("Ly", "Vũ Hạnh Ly", group="GHOST_GROUP")]
    lines = [mapped_line("Ly", "Vũ Hạnh Ly 0868345633")]

    errors = messages(queue_for(lines, employees), SEVERITY_ERROR)

    assert any("F1" in message for message in errors)


def test_f5_fires_when_nothing_maps_at_all():
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [unmapped_line("Người Lạ 0900000009")]

    errors = messages(queue_for(lines, employees), SEVERITY_ERROR)

    assert any("F5" in message for message in errors)


def test_f3_fires_only_when_effective_windows_actually_overlap():
    """Two prefixes that existed in disjoint periods are a handover, not an
    ambiguity (DEC-121)."""
    handover = [
        employee("Cũ", "Đức", effective_from="2026-01-01", effective_to="2026-01-31"),
        employee("Mới", "Đức", effective_from="2026-02-01"),
    ]
    lines = [mapped_line("Cũ", "Đức Kiên", when=date(2026, 1, 15))]
    assert not any(
        "F3" in m for m in messages(queue_for(lines, handover), SEVERITY_ERROR)
    )

    overlapping = [
        employee("A", "Đức", effective_from="2026-01-01"),
        employee("B", "Đức", effective_from="2026-01-01"),
    ]
    assert any(
        "F3" in m for m in messages(queue_for(lines, overlapping), SEVERITY_ERROR)
    )


# ---------------------------------------------------------- collect_mapping_stats

def test_stats_are_collected_from_lines_the_production_mapper_resolved():
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6, when=date(2026, 1, 5)),
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=7, when=date(2026, 3, 9)),
        unmapped_line("Người Lạ 0900000009", source_row=8, when=date(2026, 2, 1)),
    ]

    stats = collect_mapping_stats(lines, employees)

    assert stats.mapped["Ly"] == 2
    assert stats.unmapped["Người Lạ 0900000009"] == 1
    assert stats.groups["Ly"] == "STANDARD_SALES"
    assert stats.dataset_start == date(2026, 1, 5)
    assert stats.dataset_end == date(2026, 3, 9)


def test_stats_tolerate_lines_with_no_date():
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    line_without_date = mapped_line("Ly", "Vũ Hạnh Ly 0868345633", when=None)

    stats = collect_mapping_stats([line_without_date], employees)

    assert stats.dataset_start is None
    assert stats.mapped["Ly"] == 1


def test_disabled_category_produces_no_items():
    config = {"categories": {"employee_mapping": {"enabled": False}}}
    validator = Validator(config, employee_rows=[employee("Ly", "Vũ Hạnh Ly")])
    queue = validator.build_queue([unmapped_line("Ai Đó 0900000000")], [])
    assert queue.by_category(CATEGORY_EMPLOYEE_MAPPING) == []


def test_quantity_is_untouched_by_the_mapping_diagnostics():
    """A guard against the diagnostics quietly editing the data they read."""
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    working = mapped_line("Ly", "Vũ Hạnh Ly 0868345633")
    before = working.quantity

    queue_for([working], employees)

    assert working.quantity == before == Decimal("1")
    assert working.employee_normalized == "Ly"


# ------------------- Review #1, Finding 1: every criterion must be traceable

def test_f4_names_the_rows_it_is_about():
    """A criterion that says "this name has 2 rows" but cannot say WHICH rows
    leaves a reader with nothing to open. That was Finding 1."""
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line("Thảo Linh 0900000001", source_row=11),
        unmapped_line("Thảo Linh 0900000001", source_row=14),
    ]

    item = items_of(queue_for(lines, employees), criterion="F4")[0]

    assert item.scope == SCOPE_ROW
    assert item.source_file == "synthetic_raw_sample.xlsx"
    assert item.source_row == 11, "points at the first row of the unmapped name"
    assert item.details[DETAIL_SOURCE_ROWS] == "11, 14"
    assert item.details[DETAIL_RAW_VALUE] == "Thảo Linh 0900000001"
    assert item.affected_count == 2, "the real count, not a placeholder 1"


def test_f2_carries_batch_provenance_and_an_honest_zero_count():
    """F2 is precisely "this employee matched NO row", so there are no rows to
    point at. It gets batch provenance instead — which import, over what date
    range, out of how many rows — and `affected_count == 0`, because claiming
    1 would invent a row that does not exist."""
    employees = [employee("Ly", "Vũ Hạnh Ly"), employee("Kiên", "Đức Kiên")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6, when=date(2026, 1, 5)),
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=7, when=date(2026, 3, 9)),
    ]

    item = [
        i for i in items_of(queue_for(lines, employees), criterion="F2")
        if i.severity == SEVERITY_WARNING
    ][0]

    assert item.scope == SCOPE_BATCH
    assert item.source_file == "synthetic_raw_sample.xlsx"
    assert item.source_row is None
    assert item.details[DETAIL_EMPLOYEE] == "Kiên"
    assert item.details[DETAIL_DATASET_RANGE] == "2026-01-05..2026-03-09"
    assert item.details[DETAIL_BATCH_ROWS] == "2"
    assert item.affected_count == 0


def test_f1_points_at_the_rows_of_the_employee_whose_group_is_undeclared():
    employees = [employee("Ly", "Vũ Hạnh Ly", group="GHOST_GROUP")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=9),
    ]

    item = items_of(queue_for(lines, employees), criterion="F1")[0]

    assert item.scope == SCOPE_ROW
    assert item.details[DETAIL_SOURCE_ROWS] == "6, 9"
    assert item.affected_count == 2


def test_f5_is_batch_scoped_and_counts_every_orphaned_row():
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        unmapped_line("Người Lạ 0900000009", source_row=6),
        unmapped_line("Người Lạ 0900000009", source_row=7),
    ]

    item = items_of(queue_for(lines, employees), criterion="F5")[0]

    assert item.scope == SCOPE_BATCH
    assert item.source_file == "synthetic_raw_sample.xlsx"
    assert item.affected_count == 2


def test_every_employee_mapping_item_satisfies_the_reference_invariant():
    employees = [
        employee("Ly", "Vũ Hạnh Ly"),
        employee("Kiên", "Đức Kiên"),
        employee("Nghỉ", "Người Đã Nghỉ", active=False),
    ]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line("Thảo Linh 0900000001", source_row=7),
    ]

    produced = items_of(queue_for(lines, employees))
    assert produced

    for item in produced:
        assert item.source_file, item
        assert item.details.get(DETAIL_CRITERION), item
        if item.scope == SCOPE_ROW:
            assert item.source_row is not None, item
            assert item.details.get(DETAIL_SOURCE_ROWS), item
        else:
            assert item.scope == SCOPE_BATCH, item
            assert item.details.get(DETAIL_DATASET_RANGE), item


# --------------------------------- HD-110-03: F6, inactive employee with rows

def test_f6_reports_an_inactive_employee_that_still_has_rows():
    """Contradictory master data: flagged as having left, yet selling.

    Before HD-110-03 this was reported as `Missing.employee` — wrong, the
    seller is known (Review #1, Finding 3). Dropping it instead would have
    left a real defect with no signal at all while the revenue kept counting
    toward that person's KPI.
    """
    employees = [employee("Ly", "Vũ Hạnh Ly", active=False)]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=8),
    ]

    found = items_of(queue_for(lines, employees), criterion="F6")

    assert len(found) == 1
    item = found[0]
    assert item.severity == SEVERITY_WARNING
    assert item.scope == SCOPE_ROW
    assert item.details[DETAIL_SOURCE_ROWS] == "6, 8"
    assert item.details[DETAIL_EMPLOYEE] == "Ly"
    assert item.affected_count == 2
    assert "active: false" in item.message


def test_f6_stays_silent_for_an_active_employee():
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6)]
    assert items_of(queue_for(lines, employees), criterion="F6") == []


def test_f6_and_f2_never_describe_the_same_employee_at_once():
    """F2's INFO branch is "inactive AND no rows"; F6 is "inactive AND rows".
    They are complements — an employee must land in exactly one."""
    employees = [
        employee("Ly", "Vũ Hạnh Ly", active=False),
        employee("Nghỉ", "Người Đã Nghỉ", active=False),
    ]
    lines = [mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6)]

    queue = queue_for(lines, employees)
    f6 = {i.details[DETAIL_EMPLOYEE] for i in items_of(queue, criterion="F6")}
    f2 = {
        i.details[DETAIL_EMPLOYEE]
        for i in items_of(queue, criterion="F2")
        if DETAIL_EMPLOYEE in i.details
    }

    assert f6 == {"Ly"}
    assert f2 == {"Nghỉ"}
    assert not (f6 & f2)


def test_f6_does_not_change_what_the_analysis_script_reports_for_healthy_data():
    """CHECK-110-14: adding F6 must not shift `reconcile_conversion.py`'s
    output. It cannot fire unless master data contradicts itself."""
    from app.modules.validation.employee_mapping import evaluate_raw_mapping
    from collections import Counter

    verdict = evaluate_raw_mapping(
        Counter({"Ly": 10}),
        {"Ly": "STANDARD_SALES"},
        Counter(),
        {},
        [employee("Ly", "Vũ Hạnh Ly")],
        {"STANDARD_SALES"},
        date(2026, 1, 1),
        date(2026, 6, 30),
    )
    assert verdict.hard_failures == []
    assert verdict.warnings == []


def test_empty_batch_produces_no_mapping_noise():
    """F5 ("nothing mapped at all") on a file with no rows is noise, not a
    finding — and there would be no source_file to point at either."""
    assert queue_for([], [employee("Ly", "Vũ Hạnh Ly")]).items == []


# ------------------- Review #2, Finding 1: blank identity never reaches F4

def test_blank_employee_produces_only_missing_and_never_an_f4():
    """A row with no `NVBH` has no IDENTITY for master data to be missing.

    Before this fix it fell into the unmapped counter under the key `""`, and
    once that key crossed the F4 threshold it produced a finding with no raw
    identity, no source rows and batch scope — a queue line nobody could act
    on. It is already reported as `Missing.employee`; F4 is for a real name
    that master data does not know.
    """
    config = {
        "categories": {
            "employee_mapping": CONFIG["categories"]["employee_mapping"],
            "missing": {"enabled": True, "fields": {"employee": SEVERITY_ERROR}},
        }
    }
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line(None, source_row=7),
        unmapped_line("", source_row=8),
        unmapped_line("   ", source_row=9),
    ]

    queue = Validator(
        config, employee_rows=employees, employee_groups=GROUPS
    ).build_queue(lines, [])

    assert items_of(queue, criterion="F4") == []
    assert sorted(i.source_row for i in queue.by_category(CATEGORY_MISSING)) == [7, 8, 9]


def test_a_real_unmapped_identity_still_raises_a_fully_traceable_f4():
    """The other half of Finding 1: excluding blanks must not weaken F4 for a
    genuine raw identity."""
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line(None, source_row=7),
        unmapped_line("Thảo Linh 0900000001", source_row=11),
        unmapped_line("Thảo Linh 0900000001", source_row=14),
    ]

    found = items_of(queue_for(lines, employees), criterion="F4")

    assert len(found) == 1, "one identity, one finding — no blank-keyed duplicate"
    item = found[0]
    assert item.source_file == "synthetic_raw_sample.xlsx"
    assert item.details[DETAIL_SOURCE_ROWS] == "11, 14"
    assert item.affected_count == 2
    assert item.details[DETAIL_RAW_VALUE] == "Thảo Linh 0900000001"


def test_blank_rows_do_not_inflate_the_f4_threshold_either():
    """`smallest` comes from mapped employees, and blanks must not sneak into
    the unmapped side and create a second, identity-less finding."""
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6)] + [
        unmapped_line("", source_row=10 + i) for i in range(20)
    ]

    assert items_of(queue_for(lines, employees), criterion="F4") == []


# ----------------- Review #2, Finding 2: F6 respects effective dating

OLD_RECORD = {
    "raw_prefix": "Vũ Hạnh Ly",
    "normalized": "Ly",
    "group": "STANDARD_SALES",
    "active": False,
    "effective_from": "2026-01-01",
    "effective_to": "2026-03-31",
}
NEW_RECORD = {
    "raw_prefix": "Vũ Hạnh Ly",
    "normalized": "Ly",
    "group": "STANDARD_SALES",
    "active": True,
    "effective_from": "2026-04-01",
    "effective_to": None,
}
HANDOVER = [OLD_RECORD, NEW_RECORD]
RAW_LY = "Vũ Hạnh Ly 0868345633"


def resolved_lines(employee_rows, dated_rows):
    """Lines mapped by the REAL production mapper, exactly as the pipeline
    would leave them."""
    mapper = EmployeeMapper(employee_rows)
    lines = []
    for source_row, when in dated_rows:
        working = unmapped_line(RAW_LY, source_row=source_row, when=when)
        result = mapper.resolve(working.employee_raw, working.date)
        working.employee_normalized = result.normalized
        working.employee_mapping_status = result.status
        working.employee_group = result.group
        lines.append(working)
    return lines


def resolved_lines_for(employee_rows, raw_value, dated_rows):
    """`resolved_lines` for an arbitrary raw identity."""
    mapper = EmployeeMapper(employee_rows)
    lines = []
    for source_row, when in dated_rows:
        working = unmapped_line(raw_value, source_row=source_row, when=when)
        result = mapper.resolve(working.employee_raw, working.date)
        working.employee_normalized = result.normalized
        working.employee_mapping_status = result.status
        working.employee_group = result.group
        lines.append(working)
    return lines


def test_a_closed_record_never_borrows_the_active_record_s_transactions():
    """The defect Review #2 found: F6 aggregated by normalized name and then
    applied one boolean `active` to every record sharing it. A handover
    (DEC-121) deliberately reuses the name, so the closed historical record
    raised a false F6 on the current record's sales."""
    lines = resolved_lines(HANDOVER, [(6, date(2026, 5, 10)), (7, date(2026, 5, 11))])

    assert {line.employee_mapping_status for line in lines} == {MAPPING_STATUS_MAPPED}
    assert items_of(queue_for(lines, HANDOVER), criterion="F6") == []


def test_rows_inside_the_inactive_record_s_own_window_do_raise_f6():
    """The rule still has to work: a row that genuinely resolves to the closed
    record, inside its own effective window, is contradictory master data."""
    lines = resolved_lines(HANDOVER, [(6, date(2026, 2, 10)), (8, date(2026, 2, 11))])

    assert {line.employee_mapping_status for line in lines} == {"inactive"}
    found = items_of(queue_for(lines, HANDOVER), criterion="F6")

    assert len(found) == 1
    item = found[0]
    assert item.scope == SCOPE_ROW
    assert item.details[DETAIL_SOURCE_ROWS] == "6, 8"
    assert item.affected_count == 2
    assert "2026-01-01..2026-03-31" in item.message, "names WHICH record"


def test_a_batch_spanning_both_windows_attributes_each_row_to_its_own_record():
    """The strongest form of the rule: the same raw name, the same batch, two
    dates, two records — only the rows inside the closed window count."""
    lines = resolved_lines(
        HANDOVER,
        [(6, date(2026, 2, 10)), (7, date(2026, 5, 10)), (8, date(2026, 3, 31))],
    )

    found = items_of(queue_for(lines, HANDOVER), criterion="F6")

    assert len(found) == 1
    assert found[0].details[DETAIL_SOURCE_ROWS] == "6, 8"
    assert found[0].affected_count == 2, "row 7 belongs to the active record"


def test_two_inactive_records_sharing_a_name_are_reported_separately():
    """Keying by record, not by name, means two closed periods do not merge
    into one finding with a doubled count."""
    first = dict(OLD_RECORD, effective_from="2026-01-01", effective_to="2026-01-31")
    second = dict(OLD_RECORD, effective_from="2026-02-01", effective_to="2026-02-28")
    rows = [first, second]

    lines = resolved_lines(rows, [(6, date(2026, 1, 10)), (7, date(2026, 2, 10))])
    found = items_of(queue_for(lines, rows), criterion="F6")

    assert len(found) == 2
    assert sorted(i.details[DETAIL_SOURCE_ROWS] for i in found) == ["6", "7"]
    assert all(i.affected_count == 1 for i in found)


def test_f6_record_selection_agrees_with_the_production_employee_mapper():
    """`select_effective_record` is a second reading of a production rule, so
    something has to prove the two agree rather than assume it."""
    rows = HANDOVER + [employee("Kiên", "Đức Kiên")]
    mapper = EmployeeMapper(rows)

    cases = [
        (RAW_LY, date(2026, 2, 10)),
        (RAW_LY, date(2026, 3, 31)),
        (RAW_LY, date(2026, 4, 1)),
        (RAW_LY, date(2026, 5, 10)),
        ("Đức Kiên - Tân Á 0867666533", date(2026, 5, 10)),
        ("Người Lạ 0900000009", date(2026, 5, 10)),
        ("", date(2026, 5, 10)),
        (None, date(2026, 5, 10)),
    ]

    for raw_value, when in cases:
        record = select_effective_record(rows, raw_value, when)
        result = mapper.resolve(raw_value, when)

        if record is None:
            assert result.normalized is None, (raw_value, when)
            continue
        assert record["normalized"] == result.normalized, (raw_value, when)
        expected_inactive = not record.get("active", True)
        assert expected_inactive is (result.status == "inactive"), (raw_value, when)


def test_f6_never_changes_mapping_status_or_group():
    """Diagnostic only — no KPI or conversion behaviour moves because of it."""
    lines = resolved_lines(HANDOVER, [(6, date(2026, 2, 10))])
    before = [
        (line.employee_normalized, line.employee_mapping_status, line.employee_group)
        for line in lines
    ]

    queue_for(lines, HANDOVER)

    after = [
        (line.employee_normalized, line.employee_mapping_status, line.employee_group)
        for line in lines
    ]
    assert after == before


# --------------- Review #3, Finding 1: F3 provenance is per raw ROW

AMBIGUOUS_A = {
    "raw_prefix": "Đức", "normalized": "A", "group": "STANDARD_SALES",
    "active": True, "effective_from": "2026-01-01", "effective_to": None,
}
AMBIGUOUS_B = {
    "raw_prefix": "Đức", "normalized": "B", "group": "STANDARD_SALES",
    "active": True, "effective_from": "2026-01-01", "effective_to": "2026-02-28",
}
OVERLAP_ROWS = [AMBIGUOUS_A, AMBIGUOUS_B]
RAW_DUC = "Đức Kiên"


def mapped_as(normalized, raw, source_row, when):
    working = unmapped_line(raw, source_row=source_row, when=when)
    working.employee_normalized = normalized
    working.employee_mapping_status = MAPPING_STATUS_MAPPED
    working.employee_group = "STANDARD_SALES"
    return working


def test_f3_names_only_the_rows_that_are_really_ambiguous():
    """The same raw identity, one row inside the overlap and one outside.

    F3 is judged against **each row's own date** (DEC-121): two prefixes that
    only ever existed in disjoint periods are a handover, not a clash. Keying
    ambiguity by raw *value* tarred every row carrying that value — row 7 has
    exactly one record in force and is not ambiguous at all.
    """
    lines = [
        mapped_as("A", RAW_DUC, 6, date(2026, 2, 10)),   # both records in force
        mapped_as("A", RAW_DUC, 7, date(2026, 5, 10)),   # only A in force
    ]

    item = items_of(queue_for(lines, OVERLAP_ROWS), criterion="F3")[0]

    assert item.details[DETAIL_SOURCE_ROWS] == "6"
    assert item.affected_count == 1
    assert item.source_row == 6
    assert item.scope == SCOPE_ROW


def test_f3_provenance_carries_identity_row_date_and_conflicting_records():
    """Everything a reviewer needs to re-check the verdict without the file."""
    lines = [
        mapped_as("A", RAW_DUC, 6, date(2026, 2, 10)),
        mapped_as("A", RAW_DUC, 7, date(2026, 5, 10)),
    ]

    item = items_of(queue_for(lines, OVERLAP_ROWS), criterion="F3")[0]
    detail = item.details[DETAIL_AMBIGUOUS_ROWS]

    assert item.source_file == "synthetic_raw_sample.xlsx"
    assert item.details[DETAIL_RAW_VALUE] == RAW_DUC
    assert "dòng 6" in detail
    assert "2026-02-10" in detail, "transaction date of the ambiguous row"
    assert "2026-05-10" not in detail, "the non-ambiguous row must not appear"
    # The colliding master RECORDS, not just their names — two records can
    # deliberately share a name (DEC-121).
    conflicting = item.details[DETAIL_CONFLICTING_RECORDS]
    assert "A[Đức|2026-01-01..9999-12-31]" in conflicting
    assert "B[Đức|2026-01-01..2026-02-28]" in conflicting


def test_f3_counts_every_ambiguous_row_when_several_collide():
    lines = [
        mapped_as("A", RAW_DUC, 6, date(2026, 1, 10)),
        mapped_as("A", RAW_DUC, 7, date(2026, 2, 20)),
        mapped_as("A", RAW_DUC, 9, date(2026, 6, 1)),   # outside the overlap
    ]

    item = items_of(queue_for(lines, OVERLAP_ROWS), criterion="F3")[0]

    assert item.details[DETAIL_SOURCE_ROWS] == "6, 7"
    assert item.affected_count == 2


def test_no_overlap_at_all_means_no_f3():
    """A clean handover: the two records never coexist, so nothing collides."""
    old = dict(AMBIGUOUS_B, effective_from="2026-01-01", effective_to="2026-02-28")
    new = dict(AMBIGUOUS_A, effective_from="2026-03-01", effective_to=None)
    lines = [
        mapped_as("B", RAW_DUC, 6, date(2026, 2, 10)),
        mapped_as("A", RAW_DUC, 7, date(2026, 5, 10)),
    ]

    assert items_of(queue_for(lines, [old, new]), criterion="F3") == []


# ------------------------ HD-110-04: F6 needs a transaction date

def test_missing_date_produces_missing_date_and_never_f6():
    """HD-110-04. With no date there is no evidence for which master record
    was in force. Picking the first match would manufacture a verdict out of
    an unknown."""
    config = {
        "categories": {
            "employee_mapping": CONFIG["categories"]["employee_mapping"],
            "missing": {"enabled": True, "fields": {"date": SEVERITY_ERROR}},
        }
    }
    lines = resolved_lines(HANDOVER, [(6, None)])

    queue = Validator(
        config, employee_rows=HANDOVER, employee_groups=GROUPS
    ).build_queue(lines, [])

    assert items_of(queue, criterion="F6") == []
    assert [i.source_row for i in queue.by_category(CATEGORY_MISSING)] == [6]


def test_a_date_inside_the_inactive_window_still_raises_f6():
    lines = resolved_lines(HANDOVER, [(6, date(2026, 2, 10))])
    assert len(items_of(queue_for(lines, HANDOVER), criterion="F6")) == 1


def test_a_date_inside_the_active_window_raises_no_f6():
    lines = resolved_lines(HANDOVER, [(6, date(2026, 5, 10))])
    assert items_of(queue_for(lines, HANDOVER), criterion="F6") == []


def test_dateless_rows_are_dropped_without_hiding_the_dated_ones():
    """A batch mixing both: the dateless row is silent for F6, the dated one
    inside the closed window still speaks."""
    lines = resolved_lines(HANDOVER, [(6, None), (7, date(2026, 2, 10))])

    found = items_of(queue_for(lines, HANDOVER), criterion="F6")

    assert len(found) == 1
    assert found[0].details[DETAIL_SOURCE_ROWS] == "7"
    assert found[0].affected_count == 1


def test_hd_110_04_does_not_change_mapping_status_for_a_dateless_row():
    """Diagnostic only: `EmployeeMapper` still resolves however it resolves —
    TASK-110 does not touch its behaviour."""
    lines = resolved_lines(HANDOVER, [(6, None)])
    before = [line.employee_mapping_status for line in lines]

    queue_for(lines, HANDOVER)

    assert [line.employee_mapping_status for line in lines] == before


# -------------- Review #3, Finding 3: F4 keeps every raw variant

def test_f4_keeps_every_original_raw_spelling_with_its_own_rows():
    """Canonical form is right for GROUPING; the originals are the evidence.

    Whitespace and Unicode variants normalize to one identity — that is what
    makes the grouping correct — but an audit trail that only kept the
    canonical form has destroyed the difference somebody actually typed.
    """
    plain = "Thảo Linh 0900000001"
    spaced = "Thảo  Linh 0900000001"
    decomposed = unicodedata.normalize("NFD", plain)
    assert decomposed != plain, "fixture must really differ, else this proves nothing"

    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line(plain, source_row=11),
        unmapped_line(spaced, source_row=12),
        unmapped_line(decomposed, source_row=13),
    ]

    item = items_of(queue_for(lines, employees), criterion="F4")[0]
    variants = item.details[DETAIL_RAW_VARIANTS]

    # One canonical identity, one finding, all three rows.
    assert item.details[DETAIL_RAW_VALUE] == plain
    assert item.affected_count == 3
    assert item.details[DETAIL_SOURCE_ROWS] == "11, 12, 13"

    # …and every original spelling preserved, each with its own row.
    assert repr(plain) in variants
    assert repr(spaced) in variants, "the doubled space must survive"
    assert repr(decomposed) in variants, "the NFD spelling must survive"
    assert "→ 12" in variants and "→ 13" in variants


def test_raw_variants_use_repr_so_invisible_differences_stay_visible():
    """A doubled space printed plainly is indistinguishable from one space."""
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line("Thảo  Linh", source_row=11),
        unmapped_line("Thảo  Linh", source_row=12),
    ]

    item = items_of(queue_for(lines, employees), criterion="F4")[0]

    assert "'Thảo  Linh'" in item.details[DETAIL_RAW_VARIANTS]


def test_a_single_spelling_still_records_itself():
    employees = [employee("Ly", "Vũ Hạnh Ly")]
    lines = [
        mapped_line("Ly", "Vũ Hạnh Ly 0868345633", source_row=6),
        unmapped_line("Thảo Linh", source_row=11),
    ]

    item = items_of(queue_for(lines, employees), criterion="F4")[0]

    assert item.details[DETAIL_RAW_VARIANTS] == "'Thảo Linh' → 11"


# ------------------------------------------------- F3 × F6 interaction

def test_f3_and_f6_describe_the_same_batch_without_contradicting_each_other():
    """One raw identity, two records that overlap, one of them inactive.

    F3 must name only the rows where both records were in force; F6 must name
    only the rows that resolved to the inactive record. They answer different
    questions about the same data and must not borrow each other's rows.
    """
    active = {
        "raw_prefix": "Đức", "normalized": "A", "group": "STANDARD_SALES",
        "active": True, "effective_from": "2026-01-01", "effective_to": None,
    }
    closed_inactive = {
        "raw_prefix": "Đức Kiên", "normalized": "B", "group": "STANDARD_SALES",
        "active": False, "effective_from": "2026-01-01", "effective_to": "2026-02-28",
    }
    rows = [active, closed_inactive]

    lines = resolved_lines_for(rows, RAW_DUC, [(6, date(2026, 2, 10)),
                                               (7, date(2026, 5, 10))])

    queue = queue_for(lines, rows)
    f3 = items_of(queue, criterion="F3")
    f6 = items_of(queue, criterion="F6")

    # Row 6: both records effective -> ambiguous. Row 7: only `active`.
    assert f3[0].details[DETAIL_SOURCE_ROWS] == "6"
    # Row 6 resolves to the longer prefix, which is the inactive record.
    assert f6[0].details[DETAIL_SOURCE_ROWS] == "6"
    assert f6[0].affected_count == 1
    # Neither claims row 7.
    assert "7" not in f3[0].details[DETAIL_SOURCE_ROWS]
    assert "7" not in f6[0].details[DETAIL_SOURCE_ROWS]


def test_f3_fires_but_f6_stays_silent_when_the_dates_are_unknown():
    """HD-110-04 applies to F6 only. F3's own semantics are unchanged by this
    round, so a dateless row keeps whatever verdict it had — but it must not
    leak into F6."""
    closed_inactive = {
        "raw_prefix": "Đức Kiên", "normalized": "B", "group": "STANDARD_SALES",
        "active": False, "effective_from": "2026-01-01", "effective_to": "2026-02-28",
    }
    rows = [AMBIGUOUS_A, closed_inactive]

    lines = resolved_lines_for(rows, RAW_DUC, [(6, None)])

    queue = queue_for(lines, rows)

    assert items_of(queue, criterion="F6") == []


# ============ Review #4: provenance comes from the finding's own rows ========

DISJOINT_A = {
    "raw_prefix": "Đức", "normalized": "A", "group": "STANDARD_SALES",
    "active": True, "effective_from": "2026-01-01", "effective_to": "2026-02-28",
}
DISJOINT_B = {
    "raw_prefix": "Đức", "normalized": "B", "group": "STANDARD_SALES",
    "active": True, "effective_from": "2026-03-01", "effective_to": None,
}
DISJOINT = [DISJOINT_A, DISJOINT_B]

MISSING_DATE_CONFIG = {
    "categories": {
        "employee_mapping": CONFIG["categories"]["employee_mapping"],
        "missing": {"enabled": True, "fields": {"date": SEVERITY_ERROR}},
    }
}


def queue_with_missing(lines, employee_rows):
    return Validator(
        MISSING_DATE_CONFIG, employee_rows=employee_rows, employee_groups=GROUPS
    ).build_queue(lines, [])


def provenance_blob(item):
    """Everything the item exposes as provenance, as one searchable string."""
    return " | ".join(
        [str(item.source_row), *(f"{k}={v}" for k, v in item.details.items())]
    )


# ------------------------------ Finding 1: F3 provenance scoping

def test_f3_provenance_never_mentions_a_row_outside_the_ambiguous_set():
    """Review #4, Finding 1. `source_rows` was already right, but
    `raw_variants` still pulled every row sharing the canonical identity — so
    a finding about row 6 named row 7, which was never ambiguous at all.
    """
    lines = resolved_lines_for(
        OVERLAP_ROWS, RAW_DUC, [(6, date(2026, 2, 10)), (7, date(2026, 5, 10))]
    )

    item = items_of(queue_for(lines, OVERLAP_ROWS), criterion="F3")[0]

    assert item.details[DETAIL_SOURCE_ROWS] == "6"
    assert item.affected_count == 1
    assert item.source_row == 6
    assert item.details[DETAIL_RAW_VARIANTS] == "'Đức Kiên' → 6"
    assert "7" not in provenance_blob(item), (
        "row 7 is not ambiguous and must not appear in ANY provenance field"
    )


def test_f3_raw_variants_keep_only_the_spellings_of_ambiguous_rows():
    """Two spellings of one identity, only one of them on an ambiguous row."""
    mapper = EmployeeMapper(OVERLAP_ROWS)
    lines = []
    for source_row, raw, when in [
        (6, "Đức Kiên", date(2026, 2, 10)),      # ambiguous
        (7, "Đức  Kiên", date(2026, 5, 10)),     # different spelling, not ambiguous
    ]:
        working = unmapped_line(raw, source_row=source_row, when=when)
        result = mapper.resolve(working.employee_raw, working.date)
        working.employee_normalized = result.normalized
        working.employee_mapping_status = result.status
        lines.append(working)

    item = items_of(queue_for(lines, OVERLAP_ROWS), criterion="F3")[0]

    assert "'Đức Kiên' → 6" == item.details[DETAIL_RAW_VARIANTS]
    assert "Đức  Kiên" not in item.details[DETAIL_RAW_VARIANTS]


# ------------------------------ Finding 2: F4 provenance scoping

def _mapped_and_unmapped_sharing_one_identity():
    """`Thảo Linh` is only effective in January, so the same raw string maps in
    January and fails to map in May — one canonical identity, one mapped row
    and one unmapped row."""
    employees = [
        {"raw_prefix": "Thảo Linh", "normalized": "TL", "group": "STANDARD_SALES",
         "active": True, "effective_from": "2026-01-01", "effective_to": "2026-01-31"},
        employee("Ly", "Vũ Hạnh Ly"),
    ]
    lines = resolved_lines_for(
        employees, "Vũ Hạnh Ly 0868345633", [(5, date(2026, 1, 5))]
    ) + resolved_lines_for(
        employees, "Thảo Linh", [(6, date(2026, 1, 10)), (7, date(2026, 5, 10))]
    )
    return employees, lines


def test_f4_provenance_never_mentions_a_mapped_row_of_the_same_identity():
    """Review #4, Finding 2. F4 counted only unmapped rows but its provenance
    still listed every row of the canonical identity — including the one that
    mapped perfectly well."""
    employees, lines = _mapped_and_unmapped_sharing_one_identity()
    assert [line.employee_mapping_status for line in lines] == [
        MAPPING_STATUS_MAPPED, MAPPING_STATUS_MAPPED, "unmapped"
    ], "fixture must really mix mapped and unmapped under one identity"

    item = items_of(queue_for(lines, employees), criterion="F4")[0]

    assert item.details[DETAIL_SOURCE_ROWS] == "7"
    assert item.affected_count == 1
    assert item.source_row == 7
    assert item.details[DETAIL_RAW_VARIANTS] == "'Thảo Linh' → 7"
    assert "6" not in provenance_blob(item), "row 6 mapped; it is not F4 evidence"


def test_f4_keeps_several_unmapped_variants_but_no_mapped_one():
    """Double-space and NFC/NFD variants, plus a mapped row of the same
    canonical identity — only the unmapped spellings may appear."""
    plain = "Thảo Linh"
    spaced = "Thảo  Linh"
    decomposed = unicodedata.normalize("NFD", plain)
    assert decomposed != plain

    employees = [
        {"raw_prefix": "Thảo Linh", "normalized": "TL", "group": "STANDARD_SALES",
         "active": True, "effective_from": "2026-01-01", "effective_to": "2026-01-31"},
        employee("Ly", "Vũ Hạnh Ly"),
    ]
    lines = resolved_lines_for(
        employees, "Vũ Hạnh Ly 0868345633", [(5, date(2026, 1, 5))]
    )
    lines += resolved_lines_for(employees, plain, [(6, date(2026, 1, 10))])  # mapped
    lines += resolved_lines_for(employees, plain, [(11, date(2026, 5, 1))])
    lines += resolved_lines_for(employees, spaced, [(12, date(2026, 5, 2))])
    lines += resolved_lines_for(employees, decomposed, [(13, date(2026, 5, 3))])

    item = items_of(queue_for(lines, employees), criterion="F4")[0]
    variants = item.details[DETAIL_RAW_VARIANTS]

    assert item.details[DETAIL_SOURCE_ROWS] == "11, 12, 13"
    assert item.affected_count == 3
    assert repr(plain) in variants
    assert repr(spaced) in variants
    assert repr(decomposed) in variants
    assert "→ 6" not in variants, "the mapped row must not appear"


# ------------------------------ HD-110-05: F3 needs a transaction date

def test_missing_date_with_disjoint_windows_gives_missing_date_and_no_f3():
    """HD-110-05, case 1. Disjoint windows are a handover, never a clash —
    and without a date there is no moment at which to judge that anyway."""
    lines = resolved_lines_for(DISJOINT, RAW_DUC, [(6, None)])

    queue = queue_with_missing(lines, DISJOINT)

    assert items_of(queue, criterion="F3") == []
    assert [i.source_row for i in queue.by_category(CATEGORY_MISSING)] == [6]


def test_missing_date_with_overlapping_windows_still_gives_no_f3():
    """HD-110-05, case 2. Even when the records DO overlap somewhere, an
    undated row gives no evidence that this transaction fell inside it."""
    lines = resolved_lines_for(OVERLAP_ROWS, RAW_DUC, [(6, None)])

    queue = queue_with_missing(lines, OVERLAP_ROWS)

    assert items_of(queue, criterion="F3") == []
    assert [i.source_row for i in queue.by_category(CATEGORY_MISSING)] == [6]


def test_a_date_inside_the_overlap_raises_f3():
    """HD-110-05, case 3."""
    lines = resolved_lines_for(OVERLAP_ROWS, RAW_DUC, [(6, date(2026, 2, 10))])
    assert len(items_of(queue_for(lines, OVERLAP_ROWS), criterion="F3")) == 1


def test_a_date_outside_the_overlap_raises_no_f3():
    """HD-110-05, case 4."""
    lines = resolved_lines_for(OVERLAP_ROWS, RAW_DUC, [(6, date(2026, 5, 10))])
    assert items_of(queue_for(lines, OVERLAP_ROWS), criterion="F3") == []


def test_an_undated_row_never_hides_a_dated_ambiguous_one():
    lines = resolved_lines_for(
        OVERLAP_ROWS, RAW_DUC, [(6, None), (7, date(2026, 2, 10))]
    )

    item = items_of(queue_with_missing(lines, OVERLAP_ROWS), criterion="F3")[0]

    assert item.details[DETAIL_SOURCE_ROWS] == "7"
    assert item.affected_count == 1


def test_hd_110_05_does_not_change_employee_mapper_behaviour():
    """TASK-110 diagnoses; it never changes how a row is mapped."""
    lines = resolved_lines_for(OVERLAP_ROWS, RAW_DUC, [(6, None)])
    before = [(l.employee_normalized, l.employee_mapping_status) for l in lines]

    queue_with_missing(lines, OVERLAP_ROWS)

    assert [(l.employee_normalized, l.employee_mapping_status) for l in lines] == before


# ------------------------------ The invariant itself

def _all_mapping_items(queue):
    return queue.by_category(CATEGORY_EMPLOYEE_MAPPING)


def test_no_finding_can_carry_provenance_from_a_row_outside_its_own_set():
    """The invariant Review #4 asked for, asserted on the objects rather than
    on one scenario: for every finding, `affected_count` equals the number of
    its affected rows, and every rendered row number and raw variant traces
    back to one of them.

    This holds structurally — `MappingFinding.affected_count`,
    `.source_rows` and `.raw_variants()` are all DERIVED from
    `affected_rows`, so there is no second source to disagree with.
    """
    employees, lines = _mapped_and_unmapped_sharing_one_identity()
    employees = employees + [employee("Vắng", "Không Ai")]
    lines = lines + resolved_lines_for(OVERLAP_ROWS, RAW_DUC,
                                       [(20, date(2026, 2, 10))])

    stats = collect_mapping_stats(lines, employees)
    verdict = evaluate_raw_mapping(
        stats.mapped, stats.groups, stats.unmapped, stats.ambiguities,
        employees, GROUPS, stats.dataset_start, stats.dataset_end,
        row_index=stats,
    )
    findings = list(verdict.findings) + list(
        evaluate_inactive_records(employees, stats)
    )
    assert findings, "fixture must produce findings"

    for finding in findings:
        own_rows = {row.source_row for row in finding.affected_rows}

        assert finding.affected_count == len(finding.affected_rows)
        assert set(finding.source_rows) <= own_rows

        for original, rows in finding.raw_variants().items():
            assert rows, f"{finding.criterion}: variant {original!r} has no row"
            assert set(rows) <= own_rows, (
                f"{finding.criterion}: variant {original!r} names rows outside "
                "the finding"
            )
            assert any(
                row.raw_original == original for row in finding.affected_rows
            ), f"{finding.criterion}: variant {original!r} is not from its rows"


def test_the_invariant_test_would_actually_catch_a_widened_provenance():
    """Falsification: hand-build a finding whose rendered variants come from a
    row it does not own, and prove the checks above reject it."""
    from app.modules.validation.employee_mapping import AffectedRow, MappingFinding

    honest = MappingFinding(
        criterion="F4", bucket="WARNING", message="x",
        affected_rows=(AffectedRow("s.xlsx", 7, "Thảo Linh", None),),
    )
    widened = MappingFinding(
        criterion="F4", bucket="WARNING", message="x",
        affected_rows=(
            AffectedRow("s.xlsx", 7, "Thảo Linh", None),
            AffectedRow("s.xlsx", 6, "Thảo Linh", None),   # a row it should not own
        ),
    )

    assert honest.source_rows == (7,)
    assert honest.raw_variants() == {"Thảo Linh": [7]}
    # The widened one is detectably different — the invariant is a real
    # discriminator, not a tautology.
    assert widened.source_rows == (6, 7)
    assert widened.affected_count == 2
    assert widened.raw_variants() == {"Thảo Linh": [6, 7]}


def test_every_mapping_item_in_a_real_import_obeys_the_invariant(synthetic_raw_path):
    """The same invariant, end to end through `run_import()`."""
    from app.pipeline import run_import

    queue = run_import(synthetic_raw_path).review_queue
    items = _all_mapping_items(queue)
    assert items

    for item in items:
        listed = item.details.get(DETAIL_SOURCE_ROWS)
        if listed is None:
            assert item.scope == SCOPE_BATCH
            continue
        rows = {int(part) for part in listed.split(", ")}
        assert item.source_row in rows
        assert len(rows) == item.affected_count
        for chunk in item.details.get(DETAIL_RAW_VARIANTS, "").split(" ; "):
            if not chunk:
                continue
            named = {int(p) for p in chunk.split("→")[1].split(",")}
            assert named <= rows
