"""CHECK-110-18 → CHECK-110-20 — TASK-110 không làm dịch chuyển nghiệp vụ.

Bản sửa kiến trúc của Independent Review #5 viết lại `EmployeeMapper.resolve()`
trên một primitive mới. Một test viết tay khẳng định "kết quả vẫn đúng" chỉ
khẳng định lại kỳ vọng của người viết test. Ba check dưới đây so với hành vi
THẬT trước khi sửa, chụp tại commit `8386d345b04b754c061ce03b79116e75f0dfae4e`
và commit vào repo (`tests/fixtures/baseline/`).

    CHECK-110-18 (L1)  `resolve()` trên ma trận raw × as_of.
    CHECK-110-19 (L2)  Đầu ra nghiệp vụ đầu-cuối của `run_import()`.
    CHECK-110-20 (L3)  Bằng chứng đã đóng băng của TASK-108A-1 còn nguyên.

Review Queue KHÔNG nằm trong L2: chính nó đang được sửa. L2 tồn tại để trả lời
đúng một câu — tiền có dịch chuyển không?
"""

from __future__ import annotations

import inspect
import json
from collections import Counter

from tests.fixtures.baseline_snapshot import (
    L1_PATH,
    L2_PATH,
    build_l1,
    build_l2,
)


def _roundtrip(payload):
    """So sánh trên JSON đã roundtrip: tránh mọi khác biệt chỉ do kiểu dữ liệu
    trong bộ nhớ, để một FAIL luôn là khác biệt hành vi thật."""
    return json.loads(json.dumps(payload, ensure_ascii=False))


# ============================================================ CHECK-110-18 (L1)

def test_check_110_18_employee_resolve_matrix_is_unchanged():
    baseline = json.loads(L1_PATH.read_text(encoding="utf-8"))
    current = _roundtrip(build_l1())

    assert len(current) == len(baseline)
    differences = [
        (b, c) for b, c in zip(baseline, current) if b != c
    ]
    assert not differences, (
        f"{len(differences)} tổ hợp raw × as_of đổi kết quả, ví dụ: "
        f"{differences[0]}"
    )


def test_check_110_18_the_matrix_is_a_real_discriminator():
    """Ảnh chụp phải thật sự phân biệt được — một ma trận toàn `None` sẽ PASS
    kể cả khi mapping hỏng hoàn toàn."""
    baseline = json.loads(L1_PATH.read_text(encoding="utf-8"))
    statuses = Counter(row["status"] for row in baseline)

    assert statuses["mapped"] > 0, "không có case nào map được: ảnh chụp vô nghĩa"
    assert statuses["unmapped"] > 0, "không có case nào trượt: ảnh chụp vô nghĩa"
    assert len({row["normalized"] for row in baseline}) > 2


# ============================================================ CHECK-110-19 (L2)

def test_check_110_19_business_output_is_unchanged(synthetic_raw_path):
    baseline = json.loads(L2_PATH.read_text(encoding="utf-8"))
    current = _roundtrip(build_l2(synthetic_raw_path))

    for section in ("lines", "orders", "unmapped_line_rows"):
        assert current[section] == baseline[section], (
            f"`{section}` đổi so với baseline trước sửa chữa"
        )


def test_check_110_19_covers_every_field_the_owner_named(synthetic_raw_path):
    """Bảo vệ chính phép bảo vệ: nếu một trường bị lặng lẽ bỏ khỏi ảnh chụp thì
    L2 vẫn PASS trong khi không còn canh gì cả."""
    required = {
        "employee_normalized",
        "employee_mapping_status",
        "employee_group",
        "conversion_scheme_final",
        "conversion_rate_final",
        "product_group_final",
        "accounting_purchase_price",
        "accounting_profit",
        "lead_source_final",
    }
    baseline = json.loads(L2_PATH.read_text(encoding="utf-8"))
    assert baseline["lines"], "ảnh chụp rỗng thì không canh được gì"
    assert required <= set(baseline["lines"][0])

    order_fields = {
        "employee_raw",
        "employee_normalized",
        "employee_mapping_status",
        "employee_group",
    }
    assert order_fields <= set(baseline["orders"][0])


# ============================================================ CHECK-110-20 (L3)

def test_check_110_20_analysis_script_call_signature_still_works():
    """`reconcile_conversion.py` gọi `evaluate_raw_mapping` bằng 8 tham số vị
    trí và KHÔNG truyền `row_index`. Output của nó là bằng chứng đã ship của
    CHECK-108A1-15, nên chữ ký này là hợp đồng, không phải chi tiết nội bộ.
    """
    from app.modules.validation.employee_mapping import evaluate_raw_mapping

    params = list(inspect.signature(evaluate_raw_mapping).parameters)
    assert params[:8] == [
        "mapped",
        "groups",
        "unmapped",
        "ambiguities",
        "employees",
        "declared_groups",
        "dataset_start",
        "dataset_end",
    ]
    assert params[8] == "row_index"

    verdict = evaluate_raw_mapping(
        Counter({"ly": 3}),
        {"ly": "STANDARD_SALES"},
        Counter({"người lạ": 5}),
        {},
        [
            {
                "raw_prefix": "Vũ Hạnh Ly",
                "normalized": "Ly",
                "group": "STANDARD_SALES",
                "active": True,
            }
        ],
        {"STANDARD_SALES"},
        None,
        None,
    )
    assert isinstance(verdict.hard_failures, list)
    assert isinstance(verdict.warnings, list)
    assert isinstance(verdict.info, list)
    assert all(isinstance(m, str) for m in verdict.warnings)


def test_check_110_20_frozen_helpers_are_still_importable():
    """Script import `norm` và `_overlaps` trực tiếp từ module này."""
    from app.modules.validation.employee_mapping import (  # noqa: F401
        _overlaps,
        evaluate_raw_mapping,
        norm,
    )

    assert norm("  Đức   Kiên ") == "Đức Kiên"


def test_check_110_20_analysis_script_is_untouched():
    """Bằng chứng đã ký duyệt không được viết lại (CHECK-110-14)."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "tools" / "analysis" / "reconcile_conversion.py"
    source = script.read_text(encoding="utf-8")

    # Script dùng `EmployeeMapper.resolve()` để đếm mapped/unmapped, nhưng
    # giữ NGUYÊN vòng khớp prefix của riêng nó để dựng `ambiguities`, rồi
    # truyền tập đó vào `evaluate_raw_mapping`. Đó là ngoại lệ CÓ CHỦ ĐÍCH với
    # luật "một nguồn sự thật" của DEC-132: output này là bằng chứng đã ký
    # duyệt ở CHECK-108A1-15, nên đóng băng nó thắng việc thống nhất. Chính vì
    # thế thay đổi ngữ nghĩa F3 ở phía production (D3) KHÔNG chạm tới script.
    assert "raw_value.startswith(prefix)" in source
    assert "ambiguities[raw_value] = hits" in source
    assert "collect_mapping_stats" not in source

    # Và nó vẫn gọi mapper production để đếm — nên `resolve()` phải giữ đúng
    # hành vi cũ, điều CHECK-110-18 đã chứng minh.
    assert "mapper.resolve(raw_value, when)" in source
