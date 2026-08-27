"""Chứng minh ORACLE CÓ THỂ FAIL (Architecture Closure §9).

Một oracle chưa bị mutation-test thì không có giá trị: nó có thể đang PASS vì
nó mù, chứ không phải vì hệ thống đúng. Mỗi test dưới đây **tiêm một sai lệch
đáng ra phải bị bắt** và khẳng định oracle **FAIL**.

Nếu bất kỳ test nào ở đây bắt đầu PASS-khi-đáng-ra-FAIL, oracle đã trở thành
INVALID và mọi kết quả non-regression khác mất ý nghĩa.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from tests.fixtures.baseline_snapshot import (
    L1_PATH,
    L2_PATH,
    build_l1,
    build_l2,
)


def _l2(path):
    return json.loads(json.dumps(build_l2(path), ensure_ascii=False))


# ─────────────────────────────────────────────── 1. scalar business mutation

def test_oracle_detects_a_scalar_business_mutation(synthetic_raw_path, monkeypatch):
    """`total_sales` + `price_source` — hai trường mà oracle whitelist cũ mù."""
    import app.pipeline as pipeline
    import app.modules.profit.profit_engine as profit_engine

    original = profit_engine.apply_accounting_profit

    def sabotage(lines):
        result = original(lines)
        for line in lines:
            if line.total_sales is not None:
                line.total_sales += Decimal("999999")
            line.price_source = "SABOTAGED"
        return result

    monkeypatch.setattr(pipeline, "apply_accounting_profit", sabotage)
    baseline = json.loads(L2_PATH.read_text(encoding="utf-8"))
    assert _l2(synthetic_raw_path) != baseline


# ─────────────────────────────────────────── 2. Order → Line graph mutation

def test_oracle_detects_an_order_to_line_graph_mutation(synthetic_raw_path, monkeypatch):
    """Dời một line từ Order A sang Order B, GIỮ NGUYÊN mọi scalar.

    Bản oracle làm phẳng lines rồi sort là **mù hoàn toàn** với thay đổi này:
    tập line không đổi, `line.order_id` không đổi, chỉ quyền sở hữu đổi. Mà
    `Order.total_sales` và `line_count` đọc từ đúng quyền sở hữu đó.
    """
    import app.pipeline as pipeline

    original = pipeline.build_working_data

    def sabotage(*args, **kwargs):
        working = original(*args, **kwargs)
        donors = [o for o in working.orders if len(o.lines) > 1]
        receivers = [o for o in working.orders if o is not donors[0]]
        receivers[0].lines.append(donors[0].lines.pop())
        return working

    monkeypatch.setattr(pipeline, "build_working_data", sabotage)
    baseline = json.loads(L2_PATH.read_text(encoding="utf-8"))
    mutated = _l2(synthetic_raw_path)
    assert mutated != baseline
    assert mutated["order_graph"] != baseline["order_graph"], (
        "graph phải là thứ bắt được — nếu chỉ scalar đổi thì oracle vẫn mù"
    )


# ────────────────────────────────────────────── 3. MappingResult field mutation

def test_oracle_detects_a_mapping_result_field_mutation(monkeypatch):
    """Đổi một trường của `MappingResult` mà whitelist L1 cũ không chụp."""
    from app.modules.mapping.employee_mapper import EmployeeMapper

    baseline = json.loads(L1_PATH.read_text(encoding="utf-8"))
    original = EmployeeMapper.resolve

    def sabotage(self, employee_raw, as_of):
        result = original(self, employee_raw, as_of)
        if result.record is None:
            return result
        return type(result)(
            normalized=result.normalized, status=result.status,
            default_lead_source=result.default_lead_source,
            include_in_kpi=result.include_in_kpi, group=result.group,
            record=None,          # <- trường `record`, bản cũ không chụp
        )

    monkeypatch.setattr(EmployeeMapper, "resolve", sabotage)
    assert json.loads(json.dumps(build_l1(), ensure_ascii=False)) != baseline


# ────────────────────────────────────────────────────── 4. foreign row / message

def test_oracle_detects_a_foreign_row_in_provenance():
    """Nới tập row của một item -> `affected_count` và `source_rows` cùng đổi."""
    from app.modules.validation.models import (
        CATEGORY_EMPLOYEE_MAPPING, Diagnostics, ReviewItem, RowProvenance, SEVERITY_INFO)
    from tests.support.rows import affected

    honest = ReviewItem(
        category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
        provenance=RowProvenance.of((affected(6),)),
        diagnostics=Diagnostics(criterion="F4", raw_value="Lạ",
                                smallest_employee="Ly", smallest_count=1))
    widened = ReviewItem(
        category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
        provenance=RowProvenance.of((affected(6), affected(7777))),
        diagnostics=honest.diagnostics)

    assert honest.affected_count != widened.affected_count
    assert honest.details["source_rows"] != widened.details["source_rows"]
    # Và message ĐỔI THEO, vì nó dẫn xuất — không phải một chuỗi cố định.
    assert honest.message != widened.message


def test_oracle_detects_a_message_that_drifts_from_provenance():
    """Không còn đường tiêm message lạ — nên phép kiểm là: message KHÔNG THỂ
    khác nhau khi provenance giống nhau, và PHẢI khác khi provenance khác."""
    from app.modules.validation.models import (
        CATEGORY_EMPLOYEE_MAPPING, Diagnostics, ReviewItem, RowProvenance, SEVERITY_INFO)
    from tests.support.rows import affected

    diag = Diagnostics(criterion="F4", raw_value="Lạ",
                       smallest_employee="Ly", smallest_count=1)
    a = ReviewItem(category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
                   provenance=RowProvenance.of((affected(6),)), diagnostics=diag)
    b = ReviewItem(category=CATEGORY_EMPLOYEE_MAPPING, severity=SEVERITY_INFO,
                   provenance=RowProvenance.of((affected(6),)), diagnostics=diag)
    assert a.message == b.message


# ───────────────────────────────────────────────────────── 5. mutable alias

def test_oracle_detects_a_mutable_alias_attempt():
    """Alias mutation phải KHÔNG đổi được object -> đây là chứng minh ngược:
    nếu một ngày nó đổi được, test này FAIL."""
    from app.modules.validation.models import RowProvenance
    from tests.support.rows import affected

    rows = [affected(6)]
    prov = RowProvenance.of(rows)
    rows.append(affected(7777))
    assert prov.affected_count == 1, "alias mutation đã xuyên qua được biên"


# ──────────────────────────────────────────────────── 6. foreign master / ref

def test_oracle_detects_a_foreign_master_reference():
    from app.modules.mapping.employee_mapper import (
        ForeignRecordRef, build_employee_master)

    groups = [{"code": "G"}]
    a = build_employee_master([{"raw_prefix": "A", "normalized": "A", "group": "G",
                                "active": True, "effective_from": "2026-01-01",
                                "effective_to": None}], groups)
    b = build_employee_master([{"raw_prefix": "B", "normalized": "B", "group": "G",
                                "active": True, "effective_from": "2026-01-01",
                                "effective_to": None}], groups)
    with pytest.raises(ForeignRecordRef):
        b.record(a.refs[0])


# ─────────────────────────────────────── 7. oracle tự phủ field mới (structural)

def test_oracle_would_fail_loudly_if_a_dataclass_stopped_being_one():
    """Oracle dựa `dataclasses.fields()`; nếu kiểu thoái hoá, nó phải nổ to chứ
    không im lặng thu hẹp phạm vi."""
    from tests.fixtures.baseline_snapshot import _snapshot_dataclass

    with pytest.raises(TypeError, match="dataclass"):
        _snapshot_dataclass(object())
