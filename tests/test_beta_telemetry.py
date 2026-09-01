"""Telemetry aggregate Owner local — S069: chỉ đọc ReportSummary, append-safe."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app import beta_telemetry
from app.modules.exporting.excel_exporter import ReportSummary

FORBIDDEN_FIELDS = {
    "customer_identity", "phone", "address", "raw_descriptions",
    "product_codes", "purchase_prices", "sale_prices", "revenue_detail",
    "raw_workbook", "tracking_payload", "secret", "api_key",
}


def _summary(**overrides) -> ReportSummary:
    base = dict(
        input_orders=58, accounted_orders=58, total_lines=83, auto_orders=22,
        review_orders=36, review_lines=47, error_count=3,
        review_reason_counts={"IDENTITY_UNRESOLVED": 31, "Suspicious": 3},
    )
    base.update(overrides)
    return ReportSummary(**base)


def test_build_run_record_has_exactly_the_allowed_schema():
    record = beta_telemetry.build_run_record(
        run_id="report-20260901T080000Z", summary=_summary(),
        processing_duration_ms=1234, now=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    fields = set(vars(record))
    assert fields == {
        "run_id", "timestamp", "app_version", "order_count", "line_count",
        "auto_orders", "review_orders", "error_count", "accounting_rate",
        "review_reason_counts", "processing_duration_ms",
    }
    assert fields.isdisjoint(FORBIDDEN_FIELDS)


def test_build_run_record_uses_only_authoritative_summary_fields():
    summary = _summary()
    record = beta_telemetry.build_run_record(run_id="r1", summary=summary)

    assert record.order_count == summary.input_orders
    assert record.line_count == summary.total_lines
    assert record.auto_orders == summary.auto_orders
    assert record.review_orders == summary.review_orders
    assert record.error_count == summary.error_count
    assert record.accounting_rate == summary.order_accounting_rate
    assert record.review_reason_counts == summary.review_reason_counts


def test_git_sha_is_best_effort_none_outside_a_repo(tmp_path):
    assert beta_telemetry._git_sha(tmp_path) is None


def test_git_sha_resolves_inside_the_real_repo():
    sha = beta_telemetry._git_sha(beta_telemetry.REPO_ROOT)
    assert sha is None or (isinstance(sha, str) and len(sha) >= 7)


def test_record_run_appends_without_touching_prior_lines(tmp_path):
    log_path = tmp_path / "runs.jsonl"
    log_path.write_text('{"malformed": true\n', encoding="utf-8")
    record = beta_telemetry.build_run_record(run_id="r1", summary=_summary())

    beta_telemetry.record_run(record, log_path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == '{"malformed": true'
    assert json.loads(lines[1])["run_id"] == "r1"


def test_record_run_multiple_calls_preserve_every_record(tmp_path):
    log_path = tmp_path / "runs.jsonl"
    beta_telemetry.record_run(
        beta_telemetry.build_run_record(run_id="r1", summary=_summary()), log_path=log_path
    )
    beta_telemetry.record_run(
        beta_telemetry.build_run_record(run_id="r2", summary=_summary()), log_path=log_path
    )

    lines = log_path.read_text(encoding="utf-8").splitlines()
    run_ids = {json.loads(line)["run_id"] for line in lines}
    assert run_ids == {"r1", "r2"}


def test_default_log_path_is_under_beta_feedback_directory():
    assert beta_telemetry.TELEMETRY_LOG_PATH.parent.name == "beta_feedback"
