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
    collect_mapping_stats,
    evaluate_raw_mapping,
)
from app.modules.validation.models import (
    CATEGORY_EMPLOYEE_MAPPING,
    ReviewItem,
    ReviewQueue,
    SEVERITY_INFO,
    SEVERITY_WARNING,
)
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
        self._keywords = [
            str(keyword).lower() for keyword in non_product.get("keywords", []) or []
        ]
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
                    keywords=self._keywords,
                )
            )

        entry = self._category("suspicious_erp")
        if entry:
            queue.extend(
                detect_suspicious_erp(
                    lines,
                    severity=entry.get("severity", SEVERITY_INFO),
                    downgrade_to=self._downgrade_to,
                    keywords=self._keywords,
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
        """TD-001 — F2/F4 reach the Review Queue of the production import.

        Until now these criteria only ran inside a hand-run analysis script,
        which meant a real salesperson could be missing from master data and
        nothing on the import path would say so. A swallowed F4 means every
        row that person sold resolves to `Unresolved` (DEC-127 §8) and lands
        in nobody's KPI — that is payroll, not presentation.

        F1/F3/F5 come back from the same evaluator. They are invariants that
        cannot hold for correct master data, so they are surfaced too, at
        `hard_failure_severity`. Dropping an already-violated invariant on the
        floor is exactly the silence this task exists to end — but note it is
        surfacing only: like every rule here, it changes no result and blocks
        no import.
        """
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
        )

        buckets = (
            (verdict.hard_failures, entry.get("hard_failure_severity", "ERROR")),
            (verdict.warnings, entry.get("warning_severity", SEVERITY_WARNING)),
            (verdict.info, entry.get("info_severity", SEVERITY_INFO)),
        )
        return [
            ReviewItem(
                category=CATEGORY_EMPLOYEE_MAPPING,
                severity=severity,
                message=message,
            )
            for messages, severity in buckets
            for message in messages
        ]
