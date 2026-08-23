"""Behavioral parity with the reference rule in
`tools/analysis/verify_ads_rule.py` (31/31 PASS, DEC-119). Same 18 LeadSource
cases (spec section 29 + section 13 edges + DEC-109 employee-default cases),
ported here as the production module's own test suite.
"""

from __future__ import annotations

import pytest

from app.modules.domain.models import ADS, Order, PERSONAL
from app.modules.lead_source.classifier import LeadSourceClassifier
from app.modules.mapping.employee_mapper import EmployeeMapper


@pytest.fixture
def classifier() -> LeadSourceClassifier:
    return LeadSourceClassifier(ads_keywords=("ADS",), default_lead_source=PERSONAL)


# (label, notes, manual_override, expected) — employee=None for cases 1-12.
CASES = [
    ("1  Một order 1 dòng, ghi chú 'ADS'", ["ADS"], None, ADS),
    ("2  Ghi chú 'ads facebook'", ["ads facebook"], None, ADS),
    ("3  Ghi chú 'Đơn Ads web'", ["Đơn Ads web"], None, ADS),
    ("4  Order 4 dòng, dòng 3 có 'ADS', còn lại trống", ["", "", "ADS", ""], None, ADS),
    ("5  Không dòng nào có ADS", ["Giao lắp sáng mai", "Chi phí vận chuyển"], None, PERSONAL),
    ("6  Rule auto = ADS nhưng user override PERSONAL", ["KH ADS"], PERSONAL, PERSONAL),
    ("7  User reset override", ["KH ADS"], None, ADS),
    ("8a Nhân viên có đơn ADS trong tháng", ["  ADS  "], None, ADS),
    ("8b Cùng nhân viên, đơn không ADS", ["Bán hàng Vanoka"], None, PERSONAL),
    ("9  Chữ thường hoàn toàn", ["đơn ads"], None, ADS),
    ("10 Khoảng trắng thừa", ["ĐƠN    ADS    WEB"], None, ADS),
    ("11 Ghi chú None", [None, None], None, PERSONAL),
    ("12 Override sang ADS khi auto = PERSONAL", ["Bán hàng"], ADS, ADS),
]


@pytest.mark.parametrize("label,notes,manual_override,expected", CASES)
def test_lead_source_cases(classifier, label, notes, manual_override, expected):
    auto = classifier.classify_auto(notes, None, None)
    final = classifier.resolve_final(auto, manual_override)
    assert final.lead_source == expected, label


# (label, notes, manual_override, employee_default, employee_name, expected)
EMPLOYEE_CASES = [
    ("13 Tín Phát, ghi chú mặc định ERP, không có ADS",
     ["Bán hàng Vanoka"], None, ADS, "Tín Phát", ADS),
    ("14 Tín Phát, ghi chú có ADS",
     ["Đơn ADS web"], None, ADS, "Tín Phát", ADS),
    ("15 Tín Phát, quản lý override về PERSONAL",
     ["Bán hàng Vanoka"], PERSONAL, ADS, "Tín Phát", PERSONAL),
    ("16 Ly, ghi chú mặc định ERP — không ăn theo Tín Phát",
     ["Bán hàng Vanoka"], None, None, "Ly", PERSONAL),
    ("17 Ly, ghi chú có ADS",
     ["KH ADS"], None, None, "Ly", ADS),
]


@pytest.mark.parametrize(
    "label,notes,manual_override,employee_default,employee_name,expected",
    EMPLOYEE_CASES,
)
def test_employee_default_cases(
    classifier, label, notes, manual_override, employee_default, employee_name, expected
):
    auto = classifier.classify_auto(notes, employee_default, employee_name)
    final = classifier.resolve_final(auto, manual_override)
    assert final.lead_source == expected, label


def test_apply_propagates_to_every_line(config_dir):
    from app.modules.importing.normalizer import normalize_line
    from tests.factories import make_raw_row

    classifier = LeadSourceClassifier.from_yaml(config_dir / "lead_source.yaml")
    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")

    line1 = normalize_line(
        make_raw_row(order_id="BH9101", source_row=6, note_raw="Bán hàng thường",
                     employee_raw="Lê Mạnh Hoàng 0865111533")
    )
    line2 = normalize_line(
        make_raw_row(order_id="BH9101", source_row=7, note_raw="Đơn có ADS",
                     employee_raw="Lê Mạnh Hoàng 0865111533")
    )
    order = Order(
        order_id="BH9101",
        date=line1.date,
        employee_raw=line1.employee_raw,
        employee_normalized=None,
        employee_mapping_status="unmapped",
        lines=[line1, line2],
    )
    mapper.apply(order.lines)
    order.employee_normalized = line1.employee_normalized

    classifier.apply([order], mapper)

    assert order.lead_source_final == ADS
    assert line1.lead_source_final == ADS
    assert line2.lead_source_final == ADS
