"""Feedback Owner local — S069: schema, fail-safe category, append-safe."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app import beta_feedback

FORBIDDEN_FIELDS = {
    "customer_name", "phone", "address", "raw_row", "product_description",
    "purchase_price", "sale_amount", "tracking_payload", "api_key", "secret",
}


def test_build_feedback_record_has_exactly_the_allowed_schema():
    record = beta_feedback.build_feedback_record(
        category="Kết quả có vẻ không đúng", comment="test note", run_id="run-1",
        now=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    fields = set(vars(record))
    assert fields == {"feedback_id", "timestamp", "run_id", "category", "comment"}
    assert fields.isdisjoint(FORBIDDEN_FIELDS)


def test_comment_is_stripped_and_optional():
    record = beta_feedback.build_feedback_record(
        category="Khác", comment="  \n  ", run_id=None,
    )
    assert record.comment == ""
    assert record.run_id is None


def test_invalid_category_is_rejected_fail_safe():
    with pytest.raises(beta_feedback.InvalidFeedbackError):
        beta_feedback.build_feedback_record(category="Không có trong danh sách")


def test_each_feedback_record_gets_a_unique_id():
    a = beta_feedback.build_feedback_record(category="Khác")
    b = beta_feedback.build_feedback_record(category="Khác")
    assert a.feedback_id != b.feedback_id


def test_save_feedback_appends_without_touching_prior_lines(tmp_path):
    log_path = tmp_path / "feedback.jsonl"
    log_path.write_text('{"malformed": true\n', encoding="utf-8")
    record = beta_feedback.build_feedback_record(category="Khác", comment="ok")

    beta_feedback.save_feedback(record, log_path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == '{"malformed": true'
    assert json.loads(lines[1])["feedback_id"] == record.feedback_id


def test_save_feedback_multiple_calls_preserve_every_record(tmp_path):
    log_path = tmp_path / "feedback.jsonl"
    first = beta_feedback.build_feedback_record(category="Khác")
    second = beta_feedback.build_feedback_record(category="Thao tác bất tiện")

    beta_feedback.save_feedback(first, log_path=log_path)
    beta_feedback.save_feedback(second, log_path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    ids = {json.loads(line)["feedback_id"] for line in lines}
    assert ids == {first.feedback_id, second.feedback_id}


def test_default_log_path_is_under_beta_feedback_directory():
    assert beta_feedback.FEEDBACK_LOG_PATH.parent.name == "beta_feedback"
