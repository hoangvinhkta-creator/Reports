from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.modules.conversion.scheme_resolver import (
    AmbiguousSchemeConfigError,
    ConversionSchemeResolver,
)
from app.modules.domain.models import (
    ADS,
    CONVERSION_UNRESOLVED,
    DIEN_MAY,
    GIA_DUNG,
    PERSONAL,
)

JAN = date(2026, 1, 15)


def _resolver(config_dir):
    return ConversionSchemeResolver.from_yaml(config_dir / "conversion_rates.yaml")


def _resolve(config_dir, employee, group, lead_source, product_group, as_of=JAN):
    return _resolver(config_dir).resolve_auto(
        employee=employee,
        employee_group=group,
        lead_source=lead_source,
        product_group=product_group,
        as_of=as_of,
    )


# --------------------------------------------------------------------------
# Cases A-G (DEC-119), re-expressed in the DEC-127 model. The expected scheme
# and rate are unchanged from before the EmployeeGroup/ProductGroup split —
# that equality IS the regression proof.
# --------------------------------------------------------------------------

AG_CASES = [
    ("A", "Tín Phát", "STANDARD_SALES", ADS, DIEN_MAY, "ADS_7_5", "0.075"),
    ("B", "Kiên", "STANDARD_SALES", PERSONAL, DIEN_MAY, "PERSONAL_5_5", "0.055"),
    ("C", "Kiên", "STANDARD_SALES", ADS, DIEN_MAY, "ADS_7_5", "0.075"),
    ("D", "Hoàng", "STANDARD_SALES", ADS, DIEN_MAY, "ADS_7_5", "0.075"),
    ("E", "Vinh", "NOI_THANH", PERSONAL, DIEN_MAY, "NOI_THANH_2", "0.020"),
    ("F", "Quý", "NOI_THANH", PERSONAL, DIEN_MAY, "NOI_THANH_2", "0.020"),
    ("G1", "Kiên", "STANDARD_SALES", PERSONAL, DIEN_MAY, "PERSONAL_5_5", "0.055"),
    ("G2", "Kiên", "STANDARD_SALES", ADS, DIEN_MAY, "ADS_7_5", "0.075"),
]


@pytest.mark.parametrize(
    "label,employee,group,lead_source,product_group,scheme,rate", AG_CASES
)
def test_case_a_to_g_unchanged_after_model_change(
    config_dir, label, employee, group, lead_source, product_group, scheme, rate
):
    got = _resolve(config_dir, employee, group, lead_source, product_group)
    assert got.scheme == scheme, label
    assert got.rate == Decimal(rate), label


def test_case_f_covers_all_three_channel_employees(config_dir):
    # All three keep separate identities and still land on the same scheme.
    for employee in ("Vinh", "Quý", "Hiệp"):
        got = _resolve(config_dir, employee, "NOI_THANH", PERSONAL, DIEN_MAY)
        assert got.scheme == "NOI_THANH_2", employee
        assert got.rate == Decimal("0.020"), employee


# --------------------------------------------------------------------------
# ProductGroup — the new dimension.
# --------------------------------------------------------------------------


def test_same_employee_different_product_group_gives_different_rate(config_dir):
    dien_may = _resolve(config_dir, "Vinh", "NOI_THANH", PERSONAL, DIEN_MAY)
    gia_dung = _resolve(config_dir, "Vinh", "NOI_THANH", PERSONAL, GIA_DUNG)
    assert dien_may.rate == Decimal("0.020")
    assert gia_dung.rate == Decimal("0.080")
    assert dien_may.scheme != gia_dung.scheme


def test_standard_sales_selling_gia_dung_keeps_its_own_scheme(config_dir):
    # DEC-127 §3: GIA_DUNG_8 is keyed on NOI_THANH, not on "*". 34% of real
    # Gia dụng lines are sold by STANDARD_SALES people; they must NOT jump to
    # 8% — that would diverge from how the historical workbook computes them.
    got = _resolve(config_dir, "Ly", "STANDARD_SALES", PERSONAL, GIA_DUNG)
    assert got.scheme == "PERSONAL_5_5"
    assert got.rate == Decimal("0.055")


def test_group_row_beats_wildcard_row(config_dir):
    got = _resolve(config_dir, "Vinh", "NOI_THANH", PERSONAL, DIEN_MAY)
    assert got.scheme == "NOI_THANH_2"  # not PERSONAL_5_5 from the "*" row


def test_same_lead_source_different_group_gives_different_rate(config_dir):
    ly = _resolve(config_dir, "Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY)
    vinh = _resolve(config_dir, "Vinh", "NOI_THANH", PERSONAL, DIEN_MAY)
    assert ly.rate == Decimal("0.055")
    assert vinh.rate == Decimal("0.020")


# --------------------------------------------------------------------------
# Effective dating (DEC-121).
# --------------------------------------------------------------------------


def test_lookup_uses_the_order_date_not_today(config_dir):
    got = _resolve(
        config_dir, "Kiên", "STANDARD_SALES", ADS, DIEN_MAY, as_of=date(2026, 3, 15)
    )
    assert got.rate == Decimal("0.075")


def test_date_before_effective_from_is_unresolved_not_guessed(config_dir):
    got = _resolve(
        config_dir, "Kiên", "STANDARD_SALES", ADS, DIEN_MAY, as_of=date(2025, 12, 31)
    )
    assert got.scheme == CONVERSION_UNRESOLVED
    assert got.rate is None


def test_a_future_policy_row_does_not_change_a_past_period(config_dir):
    # The correct way to change a policy (DEC-121): close the old row and open
    # a new one. Leaving the old row open would make both effective and
    # equally specific from 2027 — which this engine treats as an ambiguous
    # config error rather than silently picking one (see the test below).
    rows = [
        {
            "employee": "*",
            "employee_group": "*",
            "lead_source": PERSONAL,
            "product_group": "*",
            "scheme": "PERSONAL_5_5",
            "rate": "0.055",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
        },
        {
            "employee": "*",
            "employee_group": "*",
            "lead_source": PERSONAL,
            "product_group": "*",
            "scheme": "PERSONAL_6_0",
            "rate": "0.060",
            "effective_from": "2027-01-01",
            "effective_to": None,
        },
    ]
    resolver = ConversionSchemeResolver(rows, DIEN_MAY)

    past = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)
    assert past.rate == Decimal("0.055")  # re-running 2026 still gives 2026

    later = resolver.resolve_auto(
        "Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, date(2027, 6, 1)
    )
    assert later.rate == Decimal("0.060")


def test_an_unclosed_old_row_is_reported_not_silently_resolved(config_dir):
    # The mistake the test above avoids: adding a future row WITHOUT closing
    # the old one. Both become effective and equally specific. The engine must
    # refuse rather than pick — a coin flip here lands in payroll.
    base = ConversionSchemeResolver.from_yaml(
        config_dir / "conversion_rates.yaml"
    )._rows
    careless = list(base) + [
        {
            "employee": "*",
            "employee_group": "*",
            "lead_source": PERSONAL,
            "product_group": "*",
            "scheme": "PERSONAL_6_0",
            "rate": "0.060",
            "effective_from": "2027-01-01",
            "effective_to": None,
        }
    ]
    resolver = ConversionSchemeResolver(careless, DIEN_MAY)

    # 2026 is still unambiguous — the new row is not yet effective.
    assert resolver.resolve_auto(
        "Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN
    ).rate == Decimal("0.055")

    with pytest.raises(AmbiguousSchemeConfigError):
        resolver.resolve_auto(
            "Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, date(2027, 6, 1)
        )


# --------------------------------------------------------------------------
# Unresolved and ambiguity — the two safety behaviours.
# --------------------------------------------------------------------------


def test_unmapped_employee_is_unresolved_not_borrowed(config_dir):
    # DEC-127 §8: an unidentified seller must NOT fall through to the
    # universal "*" row. "*" means "any KNOWN employee", not "anyone at all".
    got = _resolve(config_dir, None, None, PERSONAL, DIEN_MAY)
    assert got.scheme == CONVERSION_UNRESOLVED
    assert got.rate is None
    assert got.source_of_value == "Unresolved:UnmappedEmployee"


def test_employee_without_a_group_is_also_unresolved(config_dir):
    # A configured name but no group is still not enough to price a line.
    got = _resolve(config_dir, "Ai Đó", None, PERSONAL, DIEN_MAY)
    assert got.scheme == CONVERSION_UNRESOLVED
    assert got.rate is None


def test_unmapped_check_runs_before_the_universal_rule(config_dir):
    # The guard must precede scheme lookup for EVERY lead source, so no
    # combination sneaks a rate out of the "*" rows.
    for lead_source in (PERSONAL, ADS):
        got = _resolve(config_dir, None, None, lead_source, DIEN_MAY)
        assert got.rate is None, lead_source


def test_missing_lead_source_is_unresolved(config_dir):
    got = _resolve(config_dir, "Ly", "STANDARD_SALES", None, DIEN_MAY)
    assert got.scheme == CONVERSION_UNRESOLVED
    assert got.rate is None


def test_no_matching_row_is_unresolved(config_dir):
    resolver = ConversionSchemeResolver(
        [
            {
                "employee": "*",
                "employee_group": "NOI_THANH",
                "lead_source": PERSONAL,
                "product_group": "*",
                "scheme": "ONLY_ROW",
                "rate": "0.020",
                "effective_from": "2026-01-01",
                "effective_to": None,
            }
        ],
        DIEN_MAY,
    )
    got = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)
    assert got.scheme == CONVERSION_UNRESOLVED
    assert got.rate is None


def test_equally_specific_rows_raise_instead_of_picking_one(config_dir):
    ambiguous = [
        {
            "employee": "*",
            "employee_group": "NOI_THANH",
            "lead_source": PERSONAL,
            "product_group": "*",
            "scheme": "ROW_A",
            "rate": "0.020",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "employee": "*",
            "employee_group": "NOI_THANH",
            "lead_source": PERSONAL,
            "product_group": "*",
            "scheme": "ROW_B",
            "rate": "0.080",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
    ]
    resolver = ConversionSchemeResolver(ambiguous, DIEN_MAY)
    with pytest.raises(AmbiguousSchemeConfigError) as excinfo:
        resolver.resolve_auto("Vinh", "NOI_THANH", PERSONAL, DIEN_MAY, JAN)
    assert "ROW_A" in str(excinfo.value) and "ROW_B" in str(excinfo.value)


# --------------------------------------------------------------------------
# Manual override.
# --------------------------------------------------------------------------


def test_manual_override_outranks_auto_but_rate_still_comes_from_config(config_dir):
    resolver = _resolver(config_dir)
    auto = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)
    final = resolver.resolve_final(auto, "GIA_DUNG_8", as_of=JAN)
    assert final.scheme == "GIA_DUNG_8"
    assert final.rate == Decimal("0.080")  # from config, not typed by a person
    assert final.source_of_value == "Manual"


def test_manual_override_of_unknown_scheme_gives_no_rate(config_dir):
    resolver = _resolver(config_dir)
    auto = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)
    final = resolver.resolve_final(auto, "SCHEME_KHONG_TON_TAI", as_of=JAN)
    assert final.rate is None
    assert final.source_of_value == "Manual:UnknownScheme"


def test_no_override_keeps_the_auto_verdict(config_dir):
    resolver = _resolver(config_dir)
    auto = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)
    assert resolver.resolve_final(auto, None, as_of=JAN) == auto


# --- Manual override must obey effective dating, same as resolve_auto -------

_TWO_PERIOD_ROWS = [
    {
        "employee": "*",
        "employee_group": "*",
        "lead_source": PERSONAL,
        "product_group": "*",
        "scheme": "PERSONAL_5_5",
        "rate": "0.055",
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
    },
    {
        "employee": "*",
        "employee_group": "*",
        "lead_source": PERSONAL,
        "product_group": "*",
        "scheme": "PERSONAL_5_5",  # same scheme name, later period, new rate
        "rate": "0.065",
        "effective_from": "2027-01-01",
        "effective_to": None,
    },
]


def test_manual_override_uses_the_period_matching_the_order_date():
    resolver = ConversionSchemeResolver(_TWO_PERIOD_ROWS, DIEN_MAY)
    auto = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)

    in_2026 = resolver.resolve_final(auto, "PERSONAL_5_5", as_of=JAN)
    assert in_2026.rate == Decimal("0.055")

    in_2027 = resolver.resolve_final(
        auto, "PERSONAL_5_5", as_of=date(2027, 6, 1)
    )
    assert in_2027.rate == Decimal("0.065")

    # The bug this guards: taking "the first row naming this scheme" would
    # return 0.055 for both periods.
    assert in_2026.rate != in_2027.rate


def test_manual_override_before_any_period_has_no_rate():
    resolver = ConversionSchemeResolver(_TWO_PERIOD_ROWS, DIEN_MAY)
    auto = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)
    got = resolver.resolve_final(auto, "PERSONAL_5_5", as_of=date(2025, 6, 1))
    assert got.rate is None
    assert got.source_of_value == "Manual:UnknownScheme"


def test_manual_override_without_a_date_refuses_to_guess():
    resolver = ConversionSchemeResolver(_TWO_PERIOD_ROWS, DIEN_MAY)
    auto = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)
    got = resolver.resolve_final(auto, "PERSONAL_5_5", as_of=None)
    assert got.rate is None
    assert got.source_of_value == "Manual:NoEffectiveDate"


def test_manual_override_with_two_rates_in_one_period_is_ambiguous():
    overlapping = [
        dict(_TWO_PERIOD_ROWS[0], effective_to=None),  # left open by mistake
        _TWO_PERIOD_ROWS[1],
    ]
    resolver = ConversionSchemeResolver(overlapping, DIEN_MAY)
    auto = resolver.resolve_auto("Ly", "STANDARD_SALES", PERSONAL, DIEN_MAY, JAN)
    with pytest.raises(AmbiguousSchemeConfigError):
        resolver.resolve_final(auto, "PERSONAL_5_5", as_of=date(2027, 6, 1))


# --------------------------------------------------------------------------
# Master data: adding an employee must be config-only.
# --------------------------------------------------------------------------


def test_new_employee_resolves_without_touching_any_python(config_dir):
    # A person who exists in no config row at all still resolves through the
    # "*" row for their group — adding them is an employees.yaml edit only.
    got = _resolve(config_dir, "Nhân Viên Mới", "STANDARD_SALES", PERSONAL, DIEN_MAY)
    assert got.scheme == "PERSONAL_5_5"
    assert got.rate == Decimal("0.055")
