"""R6 — công cụ đối soát sổ kế toán, ĐO TRÊN CHÍNH nó.

`DEC-108`: sổ thật không có mặt trong repo và không được commit. Vì thế bài
kiểm ở đây chạy `scripts/r6_book_reconciliation.py` trên HAI sổ có thật trong
môi trường:

1. `tests/fixtures/r6_reconciliation_workbook.py` — sổ tổng hợp dựng theo
   ĐÚNG tám đặc trưng của vector Owner. Nó chứng minh công cụ đo đúng tám con
   số ấy, và chứng minh aggregate của R6 tái tạo được chúng qua ĐÚNG đường
   import production.
2. `tests/fixtures/golden/period_2026_01.xlsx` — sổ golden đã nghiệm thu. Nó
   chứng minh công cụ khớp với một con số đã được freeze từ trước R6
   (`3.562.310.000`), tức nó không "khớp" chỉ vì hai vế cùng do R6 sinh ra.

Điều KHÔNG bài nào ở đây chứng minh, và phải nói ra: sổ THẬT của Owner chưa
được chạy. `CHECK-R6-30` giữ `NOT_TESTED` cho tới khi lần chạy ấy xảy ra.
"""

from __future__ import annotations

import ast
import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest

from tests.fixtures.r6_reconciliation_workbook import (
    EXPECTED, build_reconciliation_workbook,
)

# `scripts/` cố ý KHÔNG phải một package: biến nó thành package chỉ để test
# import được sẽ đổi hình dạng repo vì một lý do của test. Nạp bằng đường dẫn
# giữ ranh giới đó nguyên vẹn.
_HARNESS_PATH = (Path(__file__).resolve().parents[1]
                 / "scripts" / "r6_book_reconciliation.py")
_spec = importlib.util.spec_from_file_location(
    "r6_book_reconciliation", _HARNESS_PATH)
harness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(harness)

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN = REPO_ROOT / "tests/fixtures/golden/period_2026_01.xlsx"
GOLDEN_EXPECTED = REPO_ROOT / "tests/fixtures/golden/expected/period_2026_01.json"


@pytest.fixture(scope="module")
def workbook(tmp_path_factory) -> Path:
    return build_reconciliation_workbook(
        tmp_path_factory.mktemp("r6-doi-soat") / "so_tong_hop.xlsx")


@pytest.fixture(scope="module")
def figures(workbook, tmp_path_factory) -> tuple[dict, dict]:
    workdir = tmp_path_factory.mktemp("r6-pipeline")
    return (harness.source_figures(workbook),
            harness.aggregate_figures(workbook, workdir))


# --- Vector Owner, đo hai lần bằng hai đường độc lập -------------------------

@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_the_source_reader_measures_the_owner_vector(figures, key):
    source, _aggregate = figures
    assert Decimal(str(source[key])) == Decimal(str(EXPECTED[key]))


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_the_r6_aggregate_reproduces_the_owner_vector_through_the_real_pipeline(
    figures, key,
):
    """Đây là mệnh đề quan trọng nhất của file: tám con số ấy sống sót qua
    `raw_reader` → `run_demo` → `write_run_history` → `PeriodData` →
    `dashboard_metrics.totals` mà không đổi một đồng."""
    _source, aggregate = figures
    assert Decimal(str(aggregate[key])) == Decimal(str(EXPECTED[key]))


def test_the_two_layers_agree_on_every_metric(figures):
    source, aggregate = figures
    rows, ok = harness.compare(source, aggregate, EXPECTED)
    assert ok, [row for row in rows if not (row["source_vs_aggregate"]
                                            and row["aggregate_vs_expected"])]


def test_the_frozen_owner_vector_in_the_script_matches_the_fixture():
    """Hai bản của cùng tám con số — trong script và trong fixture — phải
    khớp. Nếu chúng trôi khỏi nhau, một lần chạy trên sổ thật sẽ đối soát với
    một vector khác cái mà test này đã chứng minh là đo được."""
    for key, value in EXPECTED.items():
        assert Decimal(str(harness.OWNER_BOOK_EXPECTED[key])) == Decimal(str(value))


# --- Công cụ phải BẮT được một ô lệch ---------------------------------------

def test_the_harness_reports_the_exact_metric_that_drifted(figures):
    """Một công cụ đối soát luôn nói "khớp" thì không đối soát gì cả."""
    source, aggregate = figures
    wrong = {**EXPECTED, "sales_revenue": Decimal("1")}
    rows, ok = harness.compare(source, aggregate, wrong)
    assert not ok
    drifted = [row["key"] for row in rows if not row["aggregate_vs_expected"]]
    assert drifted == ["sales_revenue"]


def test_a_missing_workbook_is_reported_as_a_missing_file_not_a_failure():
    """Sổ thật vắng mặt KHÔNG được đọc thành "R6 sai" — nó là một sự thật về
    môi trường, và công cụ phải nói ra bằng đúng chữ đó."""
    assert harness.main(["--so", "/khong/co/that.xlsx"]) == 2


# --- Đối chiếu chéo với một con số đã freeze TRƯỚC R6 ------------------------

def test_the_harness_matches_the_golden_baseline_frozen_before_r6(tmp_path):
    """`3.562.310.000` là con số golden đã nghiệm thu từ `TASK-PRA-002`, không
    phải do R6 sinh ra. Công cụ khớp với nó là bằng chứng nó đo doanh thu
    THẬT, chứ không chỉ đo lại chính đầu ra của mình."""
    frozen = Decimal(json.loads(GOLDEN_EXPECTED.read_text(
        encoding="utf-8"))["money"]["sales_normalized"][0])
    source = harness.source_figures(GOLDEN)
    aggregate = harness.aggregate_figures(GOLDEN, tmp_path / "golden")
    assert source["sales_revenue"] == frozen == Decimal("3562310000")
    assert aggregate["sales_revenue"] == frozen


def test_the_harness_never_reads_the_excel_profit_column():
    """Brief R6: cột `Lợi nhuận` của Excel KHÔNG được dùng làm nguồn.

    Canh bằng cây cú pháp, không bằng phép tìm chuỗi: văn xuôi giải thích ĐƯỢC
    PHÉP nhắc tên trường (và docstring của script cố ý nhắc, để người đọc biết
    trường ấy tồn tại mà không được dùng). Cái không được phép là một phép ĐỌC
    thật sự trên nó.
    """
    tree = ast.parse(_HARNESS_PATH.read_text(encoding="utf-8"))
    read = {node.attr for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)}
    assert "source_profit" not in read
    assert "profit" not in read
