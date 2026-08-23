"""Falsification tests for normalization and keyword boundaries — TASK-110.

Independent Review #1, Findings 4 and 5. Both defects were invisible to the
old tests because those tests only ever fed the matcher strings typed the same
way the config was typed. These tests deliberately feed it the other spellings.

The rule under test (HD-110-02): a keyword matches only as a whole word or
whole phrase, after both sides are NFC-normalized, whitespace-collapsed and
case-folded.
"""

from __future__ import annotations

import unicodedata

import pytest

from app.modules.validation.text import (
    compile_keyword_patterns,
    fold,
    matches_any,
    normalize_text,
)

# The production keyword list. Kept here as the semantics under test, not as a
# number to hit: HD-110-02 forbids tuning it to reproduce a historical count.
KEYWORDS = ["phí", "công lắp đặt", "chênh vat", "chiết khấu", "voucher"]
PATTERNS = compile_keyword_patterns(KEYWORDS)


# ------------------------------------------------- Finding 4: normalization

def test_nfd_and_nfc_spellings_are_the_same_word():
    """`phí` typed as one character and as `i` + combining acute.

    Excel and YAML need not agree on which form they store. Before this fix,
    which one a file happened to use decided whether a shipping line was
    flagged as suspicious.
    """
    nfc = unicodedata.normalize("NFC", "Chi phí vận chuyển")
    nfd = unicodedata.normalize("NFD", "Chi phí vận chuyển")

    assert nfc != nfd, "fixture must actually differ, else the test proves nothing"
    assert matches_any(nfc, PATTERNS)
    assert matches_any(nfd, PATTERNS)


def test_a_keyword_written_in_nfd_still_compiles_to_the_same_matcher():
    """Normalization has to apply to the config side too, not just the data."""
    decomposed = compile_keyword_patterns([unicodedata.normalize("NFD", "phí")])
    assert matches_any("Chi phí vận chuyển", decomposed)


@pytest.mark.parametrize(
    "spelling",
    [
        "Chi  phí   vận chuyển",      # doubled spaces
        "Chi\tphí\tvận chuyển",       # tabs
        "  Chi phí vận chuyển  ",     # leading/trailing
        "Chi phí\nvận chuyển",        # newline inside the cell
    ],
)
def test_whitespace_variants_collapse_to_the_same_phrase(spelling):
    assert matches_any(spelling, PATTERNS)


@pytest.mark.parametrize(
    "spelling",
    ["CHI PHÍ VẬN CHUYỂN", "chi phí vận chuyển", "Chi Phí Vận Chuyển"],
)
def test_matching_is_case_insensitive(spelling):
    assert matches_any(spelling, PATTERNS)


def test_normalize_and_fold_handle_none_and_empty():
    assert normalize_text(None) == ""
    assert fold(None) == ""
    assert matches_any(None, PATTERNS) is False
    assert matches_any("", PATTERNS) is False


def test_no_patterns_never_matches():
    assert matches_any("Chi phí vận chuyển", []) is False


# ----------------------------------------------- Finding 5: word boundaries

def test_phi_does_not_match_ban_phim():
    """The case that made `"phí "` necessary in the first place.

    `bàn phím` is a keyboard — a real product. A plain substring `phí` matches
    inside `phím`, which would silently downgrade a genuine product line to
    INFO. The old config dodged this with a trailing space; boundaries say it
    properly.
    """
    assert "phí" in fold("Bàn phím cơ Logitech"), (
        "sanity: the substring really is present, so only the boundary saves us"
    )
    assert matches_any("Bàn phím cơ Logitech", PATTERNS) is False


@pytest.mark.parametrize(
    "product",
    [
        "Bàn phím cơ Logitech",
        "Điều hòa Casper 12000BTU",
        "Máy giặt LG Inverter 9kg",
        "Tủ lạnh Samsung 236L",
    ],
)
def test_real_products_are_never_treated_as_auxiliary_lines(product):
    assert matches_any(product, PATTERNS) is False


@pytest.mark.parametrize(
    "product",
    [
        "Chi phí vận chuyển",
        "Chi phí lắp đặt",
        "Chi phí giao hộ 65C6K x1",
        "Chi phí vận chuyển - chỉ giao",
        "Phí đổi trả",
        "Chênh VAT",
        "Chênh VAT 25%",
        "Chênh VAT (25%)",
        "Công lắp đặt + dây cấp ( Chưa bao gồm phụ kiện ngoài phát sinh nếu có ạ)",
        "Voucher giảm giá",
        "Chiết khấu cuối kỳ",
    ],
)
def test_real_auxiliary_lines_are_all_matched(product):
    """Shapes observed in the raw file. Listed to pin the semantics, not to
    reach a count — HD-110-02 forbids tuning to 1.261."""
    assert matches_any(product, PATTERNS) is True


def test_a_keyword_at_the_very_end_of_the_value_still_matches():
    """The false negative the trailing-space trick actually had: nothing
    follows the word, so `"phí "` could never match."""
    assert matches_any("Thu chi phí", PATTERNS) is True


def test_boundary_holds_on_the_left_side_too():
    assert matches_any("xxphí", PATTERNS) is False
    assert matches_any("xx phí", PATTERNS) is True


def test_multiword_keyword_needs_the_whole_phrase():
    assert matches_any("Công lắp đặt", PATTERNS) is True
    assert matches_any("Công lắp", PATTERNS) is False
    assert matches_any("lắp đặt", PATTERNS) is False


def test_blank_keywords_are_dropped_rather_than_matching_everything():
    """An empty or whitespace-only entry in YAML must not compile into a
    pattern that matches every line."""
    patterns = compile_keyword_patterns(["", "   ", None, "voucher"])
    assert len(patterns) == 1
    assert matches_any("Điều hòa Casper", patterns) is False
    assert matches_any("Voucher giảm giá", patterns) is True
