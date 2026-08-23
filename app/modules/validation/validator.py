"""Build the Review Queue for one import — mục §18 đặc tả, TASK-110.

The hard constraint of §18, restated because it is the easiest thing to lose:
**không bao giờ chặn toàn bộ import**. Nothing in this module raises on bad
data. A dataset where every single row is defective still produces a full
`ImportResult` plus a queue describing what is wrong (CHECK-110-02). The only
exceptions that escape here are configuration errors — a severity spelled
wrong in `validation.yaml` is a broken tool, not bad data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from app.modules.config.loader import load_yaml
from app.modules.domain.models import Order, WorkingLine
from app.modules.validation.employee_mapping import (
    BUCKET_HARD,
    BUCKET_INFO,
    BUCKET_WARNING,
    MappingFinding,
    MappingStats,
    collect_mapping_stats,
    evaluate_inactive_records,
    evaluate_raw_mapping,
)
from app.modules.validation.models import (
    CATEGORY_EMPLOYEE_MAPPING,
    DETAIL_BATCH_ROWS,
    DETAIL_CRITERION,
    DETAIL_DATASET_RANGE,
    DETAIL_DECLARED_GROUP,
    DETAIL_EMPLOYEE,
    DETAIL_RAW_PREFIX,
    DETAIL_RAW_VALUE,
    DETAIL_RAW_VARIANTS,
    DETAIL_SOURCE_ROWS,
    ReviewItem,
    ReviewQueue,
    SCOPE_BATCH,
    SCOPE_ROW,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
)
from app.modules.validation.text import compile_keyword_patterns
from app.modules.validation.rules import (
    detect_duplicates,
    detect_missing,
    detect_missing_purchase_price,
    detect_order_inconsistency,
    detect_source_classification,
    detect_suspicious,
    detect_suspicious_erp,
)


class Validator:
    """Runs the seven detectors against one import's working data.

    Construction reads config; `build_queue` reads data. Keeping those apart
    means a config mistake surfaces once at load time rather than once per
    row.
    """

    def __init__(
        self,
        config: dict[str, Any],
        employee_rows: Optional[list[dict]] = None,
        employee_groups: Optional[set[str]] = None,
    ):
        self._config = config or {}
        self._categories = self._config.get("categories", {}) or {}
        non_product = self._config.get("non_product_lines", {}) or {}
        self._downgrade_to = non_product.get("downgrade_to", SEVERITY_INFO)
        # Compiled once per import, not once per line: the patterns carry the
        # normalization and word-boundary semantics HD-110-02 requires.
        self._patterns = compile_keyword_patterns(
            non_product.get("keywords", []) or []
        )
        self._employee_rows = employee_rows or []
        self._employee_groups = employee_groups or set()

    @classmethod
    def from_config_dir(cls, config_dir: Path) -> "Validator":
        """Load `validation.yaml`, plus the employee master data F1–F5 need.

        `employees.yaml` is read here rather than handed down from the
        pipeline so the validator stays self-contained; it is a read, and
        nothing in TASK-110 writes to employee master data.
        """
        config = load_yaml(config_dir / "validation.yaml")
        employees = load_yaml(config_dir / "employees.yaml")
        return cls(
            config=config,
            employee_rows=employees.get("employees", []),
            employee_groups={
                group.get("code")
                for group in employees.get("employee_groups", []) or []
            },
        )

    def _category(self, name: str) -> Optional[dict]:
        entry = self._categories.get(name)
        if not entry or not entry.get("enabled", True):
            return None
        return entry

    def build_queue(
        self, lines: list[WorkingLine], orders: list[Order]
    ) -> ReviewQueue:
        queue = ReviewQueue()

        entry = self._category("missing")
        if entry:
            queue.extend(detect_missing(lines, entry.get("fields", {}) or {}))

        entry = self._category("missing_purchase_price")
        if entry:
            queue.extend(
                detect_missing_purchase_price(
                    lines,
                    severity=entry.get("severity", SEVERITY_INFO),
                    aggregate=entry.get("aggregate", True),
                )
            )

        entry = self._category("suspicious")
        if entry:
            queue.extend(
                detect_suspicious(
                    lines,
                    rules=entry.get("rules", {}) or {},
                    downgrade_to=self._downgrade_to,
                    patterns=self._patterns,
                )
            )

        entry = self._category("suspicious_erp")
        if entry:
            queue.extend(
                detect_suspicious_erp(
                    lines,
                    severity=entry.get("severity", SEVERITY_INFO),
                    downgrade_to=self._downgrade_to,
                    patterns=self._patterns,
                )
            )

        entry = self._category("order_inconsistency")
        if entry:
            queue.extend(
                detect_order_inconsistency(
                    orders,
                    employee_severity=entry.get("employee_mismatch", SEVERITY_WARNING),
                    date_severity=entry.get("date_mismatch", SEVERITY_WARNING),
                )
            )

        entry = self._category("source_classification")
        if entry:
            queue.extend(
                detect_source_classification(
                    orders, severity=entry.get("severity", SEVERITY_WARNING)
                )
            )

        entry = self._category("duplicate")
        if entry:
            queue.extend(
                detect_duplicates(
                    lines, severity=entry.get("severity", SEVERITY_WARNING)
                )
            )

        entry = self._category("employee_mapping")
        if entry:
            queue.extend(self._employee_mapping_items(lines, entry))

        return queue

    def _employee_mapping_items(
        self, lines: list[WorkingLine], entry: dict
    ) -> list[ReviewItem]:
        """TD-001 — F1–F6 reach the Review Queue of the production import.

        Until now these criteria only ran inside a hand-run analysis script,
        which meant a real salesperson could be missing from master data and
        nothing on the import path would say so. A swallowed F4 means every
        row that person sold resolves to `Unresolved` (DEC-127 §8) and lands
        in nobody's KPI — that is payroll, not presentation.

        F1/F3/F5 are invariants that cannot hold for correct master data and
        are surfaced at `hard_failure_severity` (HD-110-01 — approved and
        canonical, see DEC-129). F6 reports contradictory master data —
        `active: false` with rows in the batch (HD-110-03). Surfacing only:
        none of them changes a result or blocks an import.

        With no lines there is nothing to diagnose — every criterion here
        describes this batch's data, and F5 ("nothing mapped at all") on an
        empty file would be noise, not a finding.
        """
        if not lines:
            return []

        stats = collect_mapping_stats(lines, self._employee_rows)
        verdict = evaluate_raw_mapping(
            mapped=stats.mapped,
            groups=stats.groups,
            unmapped=stats.unmapped,
            ambiguities=stats.ambiguities,
            employees=self._employee_rows,
            declared_groups=self._employee_groups,
            dataset_start=stats.dataset_start,
            dataset_end=stats.dataset_end,
            row_index=stats,
        )

        severities = {
            BUCKET_HARD: entry.get("hard_failure_severity", SEVERITY_ERROR),
            BUCKET_WARNING: entry.get("warning_severity", SEVERITY_WARNING),
            BUCKET_INFO: entry.get("info_severity", SEVERITY_INFO),
        }
        # F6 is evaluated separately because it needs each row's own date and
        # the production mapper's record-selection semantics — see
        # `evaluate_inactive_records` (Review #2, Finding 2).
        findings = [
            *verdict.findings,
            *evaluate_inactive_records(self._employee_rows, stats),
        ]
        return [
            self._mapping_item(finding, severities[finding.bucket], stats)
            for finding in findings
        ]

    @staticmethod
    def _mapping_item(
        finding: MappingFinding, severity: str, stats: MappingStats
    ) -> ReviewItem:
        """Turn one F1–F6 verdict into a traceable queue item.

        **Every provenance field comes from `finding.affected_rows` — the rows
        that actually produced the finding — and from nothing else.**
        Independent Review #1 (Finding 1) asked for provenance; Review #3
        (Finding 1) and Review #4 (Findings 1 and 2) then found it being built
        from a wider set: "every row sharing this canonical identity". So a
        finding about one ambiguous row named a second, unambiguous one; an F4
        about an unmapped row named a mapped row beside it.

        There is no identity-keyed lookup left here to regress to. A finding
        that knows no rows is batch-scoped and says which batch, over what date
        range, out of how many rows — it never borrows rows to look complete.
        """
        details: dict[str, str] = {DETAIL_CRITERION: finding.criterion}
        details.update(finding.details)
        if finding.employee:
            details[DETAIL_EMPLOYEE] = finding.employee
        if finding.raw_value:
            details[DETAIL_RAW_VALUE] = finding.raw_value
        if finding.raw_prefix:
            details[DETAIL_RAW_PREFIX] = str(finding.raw_prefix)
        if finding.declared_group:
            details[DETAIL_DECLARED_GROUP] = finding.declared_group

        rows = () if finding.batch_scoped else finding.source_rows
        if rows:
            details[DETAIL_SOURCE_ROWS] = ", ".join(str(row) for row in rows)
            variants = finding.render_variants()
            if variants:
                details[DETAIL_RAW_VARIANTS] = variants
            return ReviewItem(
                category=CATEGORY_EMPLOYEE_MAPPING,
                severity=severity,
                message=finding.message,
                scope=SCOPE_ROW,
                source_file=finding.source_file or stats.source_file,
                source_row=rows[0],
                affected_count=finding.affected_count,
                details=details,
            )

        # Nothing to point at — F2 ("configured employee matched nothing"), an
        # F1 for a record absent from this batch — or a finding that is about
        # the batch itself (F5). `affected_count` stays exact either way, and
        # for F2 it is honestly 0: inventing a 1 would claim a row.
        details[DETAIL_DATASET_RANGE] = stats.dataset_range()
        details[DETAIL_BATCH_ROWS] = str(stats.total_rows)
        return ReviewItem(
            category=CATEGORY_EMPLOYEE_MAPPING,
            severity=severity,
            message=finding.message,
            scope=SCOPE_BATCH,
            source_file=stats.source_file,
            affected_count=finding.affected_count,
            details=details,
        )
