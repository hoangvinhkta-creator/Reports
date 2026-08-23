from __future__ import annotations

from app.modules.adjustment.ac_classifier import AirConditionerClassifier


def _classifier():
    return AirConditionerClassifier(keywords=("điều hòa", "dieu hoa"))


def test_matches_diacritic_keyword_before_model_code():
    classifier = _classifier()
    assert classifier.is_air_conditioner("Điều hòa Daikin FTKC35XVMV") is True


def test_matches_case_insensitively():
    classifier = _classifier()
    assert classifier.is_air_conditioner("ĐIỀU HÒA Panasonic CU/CS-XU9XKH-8") is True


def test_matches_ascii_no_diacritic_variant():
    classifier = _classifier()
    assert classifier.is_air_conditioner("Dieu hoa Casper SC-12TL32") is True


def test_non_air_conditioner_product_returns_false():
    classifier = _classifier()
    assert classifier.is_air_conditioner("Máy giặt Electrolux EWF9024D3WB") is False


def test_none_product_raw_returns_false_not_error():
    classifier = _classifier()
    assert classifier.is_air_conditioner(None) is False


def test_empty_string_returns_false():
    classifier = _classifier()
    assert classifier.is_air_conditioner("") is False
