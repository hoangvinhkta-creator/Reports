from __future__ import annotations

from decimal import Decimal

from app.modules.adjustment.adjustment_resolver import AdjustmentResolver


def _resolver():
    return AdjustmentResolver(
        delivery_method_tiers={
            "Qua kho": {
                "xe_may_nhe": -50000,
                "xe_may_cong_kenh": -100000,
                "o_to": -200000,
            },
            "NCC giao": {
                "xe_may_nhe": -50000,
                "xe_may_cong_kenh": -100000,
                "o_to": -200000,
            },
        },
        air_conditioner_only_defaults={
            "KHBH": -50000,
            "Thợ lắp": -200000,
        },
    )


def test_qua_kho_motorbike_light_tier():
    result = _resolver().resolve_suggested_amount(
        "Qua kho", delivery_method="xe_may_nhe"
    )
    assert result.amount == Decimal("-50000")
    assert result.source_of_value == "Auto:DeliveryMethod(xe_may_nhe)"


def test_qua_kho_motorbike_bulky_tier():
    result = _resolver().resolve_suggested_amount(
        "Qua kho", delivery_method="xe_may_cong_kenh"
    )
    assert result.amount == Decimal("-100000")


def test_ncc_giao_car_tier():
    result = _resolver().resolve_suggested_amount("NCC giao", delivery_method="o_to")
    assert result.amount == Decimal("-200000")


def test_qua_kho_without_delivery_method_has_no_default():
    result = _resolver().resolve_suggested_amount("Qua kho")
    assert result.amount is None
    assert result.source_of_value == "Manual:NoDeliveryMethodMatch"


def test_qua_kho_unknown_delivery_method_has_no_default():
    result = _resolver().resolve_suggested_amount(
        "Qua kho", delivery_method="xe_dap"
    )
    assert result.amount is None


def test_khbh_air_conditioner_has_default():
    result = _resolver().resolve_suggested_amount("KHBH", is_air_conditioner=True)
    assert result.amount == Decimal("-50000")
    assert result.source_of_value == "Auto:AirConditionerDefault"


def test_tho_lap_air_conditioner_has_default():
    result = _resolver().resolve_suggested_amount(
        "Thợ lắp", is_air_conditioner=True
    )
    assert result.amount == Decimal("-200000")


def test_khbh_non_air_conditioner_has_no_default():
    result = _resolver().resolve_suggested_amount("KHBH", is_air_conditioner=False)
    assert result.amount is None
    assert result.source_of_value == "Manual:NotAirConditionerOrUnknown"


def test_khbh_unknown_air_conditioner_status_has_no_default():
    # is_air_conditioner not provided at all — must not guess.
    result = _resolver().resolve_suggested_amount("KHBH")
    assert result.amount is None


def test_unknown_adjustment_type_has_no_default():
    result = _resolver().resolve_suggested_amount("Ship hỏa tốc")
    assert result.amount is None
    assert result.source_of_value == "Manual:UnknownAdjustmentType"


def test_from_yaml_loads_real_config(config_dir):
    resolver = AdjustmentResolver.from_yaml(config_dir / "adjustments.yaml")
    result = resolver.resolve_suggested_amount("Qua kho", delivery_method="o_to")
    assert result.amount == Decimal("-200000")
