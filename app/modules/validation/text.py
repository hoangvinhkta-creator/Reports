"""Text normalization and keyword matching for validation — TASK-110.

Independent Review #1, Findings 4 and 5. Two defects lived here:

**Normalization.** `product_raw` came out of Excel; the keyword list comes out
of YAML. The same Vietnamese word can be byte-different in the two ("phí" as
one precomposed character, or as `i` plus a combining acute), and Excel cells
carry stray double spaces and tabs. Comparing them raw makes matching depend
on how somebody typed the file. Both sides are now NFC-normalized,
whitespace-collapsed and case-folded before they ever meet.

**Boundary semantics.** Matching used a plain substring, and the config
compensated with a literal `"phí "` — a trailing space standing in for "word
ends here". That is a trick, not a meaning: it silently fails on a value
ending in the word, and it invites the next person to drop the space, at which
point `"phí"` starts matching `"bàn phím"` (a keyboard) and a real product gets
downgraded to INFO. HD-110-02 requires real boundary semantics, so a keyword
now matches only as a whole word or whole phrase.

HD-110-02 also makes the standing rule explicit: this keyword heuristic is
**temporary**, allowed only because Product/Transaction Classification (§17
đặc tả, TASK-103) does not exist yet, and it must not be tuned to reproduce
any historical count.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Pattern

_WHITESPACE = re.compile(r"\s+")


def normalize_text(value) -> str:
    """NFC-normalize, collapse all whitespace runs to one space, strip.

    Spec section 13. `None` becomes `""` so callers never branch on it.
    """
    if value is None:
        return ""
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFC", str(value))).strip()


def fold(value) -> str:
    """`normalize_text` plus case folding, for case-insensitive comparison.

    Case folding can itself denormalize (a handful of characters change form
    when lowercased), so the result is re-normalized. Skipping that second
    pass is the kind of bug that shows up only for one word in one locale.
    """
    return unicodedata.normalize("NFC", normalize_text(value).casefold())


def compile_keyword_patterns(keywords: Iterable[str]) -> list[Pattern[str]]:
    """Compile keywords into whole-word/whole-phrase matchers.

    `(?<!\\w)` / `(?!\\w)` rather than `\\b`: they behave identically for
    keywords that start and end with word characters, and they stay correct
    for one that does not (a keyword ending in `%` or `)`), where `\\b` would
    invert its meaning.
    """
    patterns: list[Pattern[str]] = []
    for keyword in keywords:
        folded = fold(keyword)
        if not folded:
            continue
        patterns.append(re.compile(rf"(?<!\w){re.escape(folded)}(?!\w)"))
    return patterns


def matches_any(value, patterns: list[Pattern[str]]) -> bool:
    """Does `value` contain any keyword as a whole word or phrase?"""
    if not patterns:
        return False
    haystack = fold(value)
    if not haystack:
        return False
    return any(pattern.search(haystack) for pattern in patterns)
