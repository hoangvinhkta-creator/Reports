"""Batch 50 accounting semantics KHÔNG hỏng vì Reader V1 — `S059` non-regression.

`tools/analysis/batch_50_real_orders.py` là bộ đếm canonical của Order
Accounting: mỗi OrderID đầu vào phải rơi vào đúng một kết cục, và tổng
`AUTO_SUCCESS + REVIEW_QUEUE` phải bằng cỡ cohort (`ORDER_ACCOUNTING_RATE =
100%`, `SILENTLY_DROPPED = 0`). Đó là bất biến mà `S059` đã đóng.

Phiên này chạm vào `apply_prices()` (thêm nhãn nguồn do provider tự khai) và
thêm một `PriceProvider` mới. Cả hai đều nằm trên đúng đường mà bộ đếm ấy đo,
nên bất biến phải được chạy lại chứ không được suy luận là còn đúng.

Workbook thật (`DEC-108`) không nằm trong repo, nên test chạy chính hàm
`analyze()` đó trên workbook tổng hợp: cái được canh ở đây là **ngữ nghĩa
phân loại**, không phải con số của một file cụ thể.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BATCH_50 = REPO_ROOT / "tools" / "analysis" / "batch_50_real_orders.py"


def _load_batch_50():
    spec = importlib.util.spec_from_file_location("batch_50_real_orders", BATCH_50)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def batch_50():
    return _load_batch_50()


@pytest.fixture
def report(batch_50, synthetic_raw_path):
    return batch_50.analyze(synthetic_raw_path, 50)


def test_order_accounting_rate_is_still_one_hundred_percent(report):
    counts = report["outcome_counts"]
    accounted = counts.get("AUTO_SUCCESS", 0) + counts.get("REVIEW_QUEUE", 0)
    assert accounted == report["cohort_size"]


def test_nothing_is_silently_dropped(report):
    assert report["outcome_counts"].get("SILENTLY_DROPPED", 0) == 0


def test_no_order_is_pending_without_a_queue_item(report):
    """`PENDING_NOT_QUEUED` là đúng cái khe mà "no silent error" phải đóng."""
    assert report["outcome_counts"].get("PENDING_NOT_QUEUED", 0) == 0


def test_no_order_errors_out(report):
    assert report["outcome_counts"].get("ERROR", 0) == 0
    assert "pipeline_error" not in report


def test_every_cohort_order_appears_exactly_once(report):
    counts = report["outcome_counts"]
    assert sum(counts.values()) == report["cohort_size"]
