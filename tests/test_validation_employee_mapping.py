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

from datetime import date
from decimal import Decimal

from app.modules.domain.models import MAPPING_STATUS_MAPPED
from app.modules.mapping.employee_mapper import EmployeeMapper
from app.modules.importing.normalizer import normalize_line
from app.modules.validation.employee_mapping import (
    collect_mapping_stats,
    select_effective_record,
)
from app.modules.validation.models import (
    CATEGORY_EMPLOYEE_MAPPING,
    CATEGORY_MISSING,
    DETAIL_BATCH_ROWS,
    DETAIL_CRITERION,
    DETAIL_DATASET_RANGE,
    DETAIL_EMPLOYEE,
    DETAIL_RAW_VALUE,
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
