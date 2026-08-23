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
from app.modules.importing.normalizer import normalize_line
from app.modules.validation.employee_mapping import collect_mapping_stats
from app.modules.validation.models import (
    CATEGORY_EMPLOYEE_MAPPING,
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


def messages(queue, severity=None):
    items = queue.by_category(CATEGORY_EMPLOYEE_MAPPING)
    if severity:
        items = [item for item in items if item.severity == severity]
    return [item.message for item in items]


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
