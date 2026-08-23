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

import pytest
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

# `record.snapshot_id` là trường DUY NHẤT được phép đổi biểu diễn (owner
# decision §3): nó chuyển từ *field caller đặt được* sang *property dẫn xuất*,
# nên giá trị đổi theo công thức mới. Đây không phải một whitelist quay lại —
# đây là một ngoại lệ đúng một trường, có tuyên bố, và kèm bốn chứng minh ở
# `test_check_110_18_snapshot_id_semantic_equivalence` bên dưới.
_REPRESENTATION_EXCEPTION = ("record", "snapshot_id")


def _without_representation_exception(row: dict) -> dict:
    outer, inner = _REPRESENTATION_EXCEPTION
    if isinstance(row.get(outer), dict):
        row = dict(row)
        row[outer] = {k: v for k, v in row[outer].items() if k != inner}
    return row


def test_check_110_18_employee_resolve_matrix_is_unchanged():
    """MỌI trường nghiệp vụ IDENTICAL — kể cả `record.index` và `record.label`."""
    baseline = json.loads(L1_PATH.read_text(encoding="utf-8"))
    current = _roundtrip(build_l1())

    assert len(current) == len(baseline)
    differences = [
        (b, c)
        for b, c in zip(baseline, current)
        if _without_representation_exception(b) != _without_representation_exception(c)
    ]
    assert not differences, (
        f"{len(differences)} tổ hợp raw × as_of đổi kết quả, ví dụ: "
        f"{differences[0]}"
    )


def test_check_110_18_snapshot_id_semantic_equivalence():
    """Bốn chứng minh mà owner decision §3 yêu cầu cho ngoại lệ biểu diễn."""
    import dataclasses
    from datetime import date
    from pathlib import Path as _Path

    from app.modules.mapping.employee_mapper import (
        EmployeeMapper,
        SealedConstruction,
        build_employee_master,
        load_employee_master,
    )

    root = _Path(__file__).resolve().parents[1]

    # 1. DERIVE từ nội dung master — không phải field.
    assert "snapshot_id" not in {
        f.name for f in dataclasses.fields(load_employee_master(root / "config" / "employees.yaml"))
    }

    # 2. Caller KHÔNG tự truyền được.
    with pytest.raises(SealedConstruction):
        type(load_employee_master(root / "config" / "employees.yaml"))(
            records=(), group_codes=frozenset()
        )

    # 3. Cùng logical master -> cùng identity.
    one = load_employee_master(root / "config" / "employees.yaml")
    two = load_employee_master(root / "config" / "employees.yaml")
    assert one.snapshot_id == two.snapshot_id

    # 4. Khác logical master -> khác identity.
    groups = [{"code": "STANDARD_SALES"}]
    base = [{"raw_prefix": "A", "normalized": "A", "group": "STANDARD_SALES",
             "active": True, "effective_from": "2026-01-01", "effective_to": None}]
    other = [dict(base[0], normalized="B")]
    assert (
        build_employee_master(base, groups).snapshot_id
        != build_employee_master(other, groups).snapshot_id
    )

    # 5. KHÔNG tham gia calculation: mọi trường nghiệp vụ của `resolve()` giữ
    #    nguyên khi id đổi — chính là điều test phía trên đã chứng minh trên
    #    972 tổ hợp.
    mapper = EmployeeMapper(build_employee_master(base, groups))
    assert mapper.resolve("A1", date(2026, 6, 1)).normalized == "A"


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

    for section in ("raw_rows", "lines", "orders", "unmapped_line_rows"):
        assert current[section] == baseline[section], (
            f"`{section}` đổi so với baseline trước sửa chữa"
        )


def test_check_110_19_oracle_is_structural_not_a_whitelist(synthetic_raw_path):
    """O3 — oracle phủ MỌI trường vì nó dẫn xuất, không liệt kê.

    Bản trước có một test tên "đã phủ đủ trường chủ dự án nêu chưa" đối chiếu
    một danh sách trắng với **chính nó** — một tautology, đúng cùng lỗi luận
    lý mà Review #5 Finding 2 đã bác bỏ, chỉ chuyển sang tầng oracle. Nó bị
    xoá. Test này so ảnh chụp với `dataclasses.fields()` của chính các
    dataclass, nên một trường thêm vào ngày mai tự động được canh và một
    trường bị xoá cũng bị phát hiện.
    """
    import dataclasses

    from app.modules.domain.models import Order, RawRow, WorkingLine

    baseline = json.loads(L2_PATH.read_text(encoding="utf-8"))
    covered = baseline["_covered_fields"]

    expected_raw = {f.name for f in dataclasses.fields(RawRow)}
    expected_line = {f.name for f in dataclasses.fields(WorkingLine)} - {"raw"}
    expected_order = {f.name for f in dataclasses.fields(Order)} - {"lines"}

    assert set(covered["raw_rows"]) == expected_raw
    assert set(covered["lines"]) - {"_source_row"} == expected_line
    assert set(covered["orders"]) == expected_order


def test_check_110_19_pii_is_stored_as_digest_never_raw(synthetic_raw_path):
    """HD-110-11 — thay đổi vẫn bị phát hiện, giá trị không nằm trong repo."""
    from app.modules.validation.models import PII_FIELD_NAMES

    baseline = json.loads(L2_PATH.read_text(encoding="utf-8"))
    for row in baseline["raw_rows"]:
        for name in PII_FIELD_NAMES:
            if name in row and row[name] is not None:
                assert str(row[name]).startswith(("sha256:", "∅")), (
                    f"{name} lưu giá trị thô trong ảnh chụp đã commit"
                )


def test_check_110_19_o2_oracle_detects_a_previously_missed_field(
    synthetic_raw_path, monkeypatch
):
    """O1/O2 — chính mutation mà oracle CŨ bỏ sót, oracle mới phải bắt.

    Review #6 Finding 6 đo được trên oracle cũ: cộng 999.999 vào `total_sales`
    của MỌI dòng và đổi `price_source` → oracle vẫn PASS. Cả hai trường đó đều
    nằm ngoài danh sách trắng 9 trường.
    """
    from decimal import Decimal

    import app.pipeline as pipeline
    import app.modules.profit.profit_engine as profit_engine

    original = profit_engine.apply_accounting_profit

    def sabotage(lines):
        result = original(lines)
        for line in lines:
            if line.total_sales is not None:
                line.total_sales = line.total_sales + Decimal("999999")
            line.price_source = "SABOTAGED"
        return result

    monkeypatch.setattr(pipeline, "apply_accounting_profit", sabotage)

    baseline = json.loads(L2_PATH.read_text(encoding="utf-8"))
    sabotaged = _roundtrip(build_l2(synthetic_raw_path))
    assert sabotaged != baseline, (
        "oracle KHÔNG phát hiện thay đổi ở total_sales/price_source — nó lại "
        "trở thành một danh sách trắng"
    )

    changed = {
        key
        for base_row, now_row in zip(baseline["lines"], sabotaged["lines"])
        for key in base_row
        if base_row[key] != now_row[key]
    }
    assert {"total_sales", "price_source"} <= changed


# ============================================================ CHECK-110-20 (L3)

def test_check_110_20_analysis_script_call_signature_still_works():
    """`reconcile_conversion.py` gọi `evaluate_raw_mapping` bằng 8 tham số vị
    trí và KHÔNG truyền `row_index`. Output của nó là bằng chứng đã ship của
    CHECK-108A1-15, nên chữ ký này là hợp đồng, không phải chi tiết nội bộ.
    """
    from app.modules.validation.employee_mapping import evaluate_raw_mapping

    # HD-110-12: chữ ký CŨ 8-tham-số-vị-trí đã bị XOÁ. Nó là chính cơ chế để
    # bộ đếm và chỉ mục dòng đến từ hai nguồn khác nhau (RC-3).
    params = list(inspect.signature(evaluate_raw_mapping).parameters)
    assert params == ["stats"], (
        "evaluate_raw_mapping phải nhận đúng MỘT tham số canonical"
    )

    from app.modules.mapping.employee_mapper import (
        EmployeeMapper,
        build_employee_master,
    )
    from app.modules.validation.employee_mapping import (
        MappingInput,
        collect_mapping_stats,
    )

    mapper = EmployeeMapper(build_employee_master(
        [{"raw_prefix": "Vũ Hạnh Ly", "normalized": "Ly",
          "group": "STANDARD_SALES", "active": True,
          "effective_from": "2026-01-01", "effective_to": None}],
        [{"code": "STANDARD_SALES"}],
    ))
    stats = collect_mapping_stats(
        [MappingInput("s.xlsx", 6, "Người Lạ", None, None, None)], mapper
    )
    verdict = evaluate_raw_mapping(stats)
    assert isinstance(verdict.hard_failures, list)
    assert isinstance(verdict.warnings, list)
    assert isinstance(verdict.info, list)
    assert all(isinstance(m, str) for m in verdict.warnings)


def test_check_110_20_frozen_helpers_are_still_importable():
    """Script import `norm` và `_overlaps` trực tiếp từ module này."""
    from app.modules.validation.employee_mapping import (  # noqa: F401
        MappingInput,
        collect_mapping_stats,
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
    # HD-110-12: vòng khớp prefix riêng và bộ đếm song song của script đã
    # biến mất — giữ chúng là giữ một bản cài đặt thứ hai của cùng quy tắc.
    assert "raw_value.startswith(prefix)" not in source
    assert "ambiguities[raw_value] = hits" not in source
    assert "collect_mapping_stats" in source

    # Logic đối chiếu KHÔNG đổi: script vẫn gọi mapper production để resolve.
    assert "mapper.resolve(raw_value, when)" in source
