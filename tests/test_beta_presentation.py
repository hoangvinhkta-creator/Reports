"""Nhãn hiển thị Review reason — S069: chỉ đổi tên gọi, không đổi/gộp reason."""

from __future__ import annotations

from app.beta_presentation import REASON_DISPLAY_LABELS, format_review_reasons


def test_empty_counts_produce_empty_text():
    assert format_review_reasons({}) == ""


def test_known_reason_uses_its_display_label():
    text = format_review_reasons({"IDENTITY_UNRESOLVED": 5})
    assert REASON_DISPLAY_LABELS["IDENTITY_UNRESOLVED"] in text
    assert "5" in text


def test_unknown_reason_falls_back_to_the_raw_authoritative_string():
    text = format_review_reasons({"SOME_NEW_REASON_NOT_YET_MAPPED": 2})
    assert "SOME_NEW_REASON_NOT_YET_MAPPED" in text


def test_reasons_do_not_get_merged_even_with_equal_counts():
    text = format_review_reasons({"Suspicious": 1, "TRACKING_HISTORY_PENDING": 1})
    for label in (
        REASON_DISPLAY_LABELS["Suspicious"], REASON_DISPLAY_LABELS["TRACKING_HISTORY_PENDING"],
    ):
        assert label in text


def test_sorted_by_count_descending():
    text = format_review_reasons({"Suspicious": 1, "IDENTITY_UNRESOLVED": 9})
    assert text.index(REASON_DISPLAY_LABELS["IDENTITY_UNRESOLVED"]) < text.index(
        REASON_DISPLAY_LABELS["Suspicious"]
    )
