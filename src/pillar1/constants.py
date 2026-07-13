"""
Shared constants for Pillar 1 — extracted to avoid duplication across modules.

Why a regex blocklist:
- Plain substring matching ('good' in text) falsely flags 'goodwill', 'goodness',
  'high-quality' (hyphen variant), 'fast-moving', etc.
- Word-boundary regex matching (\\bfast\\b) only matches complete words, preventing
  false positives on substrings.
"""
from __future__ import annotations

import re
from typing import Final

# ── Subjective language blocklist ────────────────────────────────────────────
# Used by ctq.py and ppd.py. Updated in ONE place only.

SUBJECTIVE_BLOCKLIST: Final[list[str]] = [
    # Core vague adjectives
    "good",
    "clear",
    "professional",
    "appropriate",
    "reasonable",
    "sufficient",
    "adequate",
    "timely",
    "well-structured",
    "effective",
    "suitable",
    "satisfactory",
    "robust",
    "solid",
    "fast",
    "efficient",
    # Phrases (order matters — longer phrases before shorter substrings)
    "high quality",
    "high-quality",
]

# Compiled regex: matches each term as a whole word only.
# Sorted longest-first to avoid partial overlaps.
_BLOCKLIST_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    for term in sorted(SUBJECTIVE_BLOCKLIST, key=len, reverse=True)
]


def has_subjective_language(text: str) -> tuple[bool, list[str]]:
    """
    Scan text for any blocklisted terms using word-boundary regex.

    Returns:
        (has_subjectives: bool, flagged_terms: list[str])
    """
    flagged: list[str] = []
    lower = text.lower()
    for pattern in _BLOCKLIST_PATTERNS:
        if pattern.search(lower):
            term = pattern.pattern.removeprefix(r"\b").removesuffix(r"\b")
            if term not in flagged:
                flagged.append(term)
    return len(flagged) > 0, flagged


# ── SIPOC columns ─────────────────────────────────────────────────────────────
SIPOC_COLUMNS: Final[list[str]] = [
    "suppliers",
    "inputs",
    "process",
    "outputs",
    "customers",
]

# ── PPD required fields ───────────────────────────────────────────────────────
REQUIRED_PPD_FIELDS: Final[list[str]] = [
    "purpose",
    "composition",
    "derivation",
    "format",
    "quality_criteria",
    "acceptance_method",
]
