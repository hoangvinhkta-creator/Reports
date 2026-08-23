from __future__ import annotations

from datetime import date

from app.modules.domain.models import (
    MAPPING_STATUS_MAPPED,
    MAPPING_STATUS_UNMAPPED,
)
from app.modules.mapping.employee_mapper import EmployeeMapper


def test_maps_ly_by_prefix(config_dir):
    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    result = mapper.resolve("Vũ Hạnh Ly 0868345633", date(2026, 1, 15))
    assert result.normalized == "Ly"
    assert result.status == MAPPING_STATUS_MAPPED
    assert result.default_lead_source is None


def test_tin_phat_has_ads_default(config_dir):
    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    result = mapper.resolve("Tín Phát 0869931931", date(2026, 3, 1))
    assert result.normalized == "Tín Phát"
    assert result.default_lead_source == "ADS"


def test_channel_employees_keep_identity_and_share_a_group(config_dir):
    # DEC-127 §1: the three channel sellers are three real people. They used to
    # be collapsed into one fake employee "Nội thành"; what they share is a
    # group, not a name.
    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    expected = {"Đức Hiệp": "Hiệp", "Mr Quý": "Quý", "Mr Vinh": "Vinh"}
    for raw, normalized in expected.items():
        result = mapper.resolve(raw, date(2026, 2, 1))
        assert result.normalized == normalized, raw
        assert result.group == "NOI_THANH", raw
        assert result.default_lead_source is None, raw

    resolved = {mapper.resolve(raw, date(2026, 2, 1)).normalized for raw in expected}
    assert len(resolved) == 3, "ba nhân viên phải giữ ba danh tính riêng"


def test_unmapped_employee_is_flagged_not_dropped(config_dir):
    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    result = mapper.resolve("Người Lạ Test 0900000009", date(2026, 1, 19))
    assert result.normalized is None
    assert result.status == MAPPING_STATUS_UNMAPPED


def test_blank_employee_is_unmapped(config_dir):
    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    result = mapper.resolve(None, date(2026, 1, 1))
    assert result.status == MAPPING_STATUS_UNMAPPED


def test_date_before_effective_from_is_unmapped(config_dir):
    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    result = mapper.resolve("Vũ Hạnh Ly 0868345633", date(2025, 12, 31))
    assert result.status == MAPPING_STATUS_UNMAPPED


def test_apply_sets_fields_on_working_lines(config_dir):
    from app.modules.importing.normalizer import normalize_line
    from tests.factories import make_raw_row

    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    line = normalize_line(make_raw_row(employee_raw="Lê Mạnh Hoàng 0865111533"))
    mapper.apply([line])
    assert line.employee_normalized == "Hoàng"
    assert line.employee_mapping_status == MAPPING_STATUS_MAPPED
