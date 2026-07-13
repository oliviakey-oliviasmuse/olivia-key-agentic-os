"""
FMEA / RPN shared helpers — single source of truth for the RPN thresholds
used across pillars 3 (proposal_builder) and 4 (control_plan).

Before this module existed, RPN_ACTION_THRESHOLD and RPN_ANDON_THRESHOLD
were duplicated as module-level constants in two places, with a real risk
of drift.

Usage:
    from src.common.fmea import (
        calculate_rpn, classify_rpn, RPN_ACTION_THRESHOLD, RPN_ANDON_THRESHOLD,
    )
"""
from __future__ import annotations

from typing import Literal

# ── Thresholds (single source of truth) ─────────────────────────────────────
# Aligned between Pillar 3 (proposal_builder) and Pillar 4 (control_plan).
# RPN_ANDON: must be reviewed before handover
# RPN_ACTION: requires explicit control plan
RPN_ACTION_THRESHOLD: int = 150
RPN_ANDON_THRESHOLD: int = 300

AndonLevel = Literal["ANDON", "ACTION", "ACCEPT"]


def calculate_rpn(severity: int, occurrence: int, detection: int) -> int:
    """Standard FMEA RPN: severity * occurrence * detection. Each is 1-10."""
    if not (1 <= severity <= 10):
        raise ValueError(f"severity must be 1-10, got {severity}")
    if not (1 <= occurrence <= 10):
        raise ValueError(f"occurrence must be 1-10, got {occurrence}")
    if not (1 <= detection <= 10):
        raise ValueError(f"detection must be 1-10, got {detection}")
    return severity * occurrence * detection


def classify_rpn(rpn: int) -> AndonLevel:
    """
    Classify an RPN score.

    Returns:
        "ANDON"  — rpn >= RPN_ANDON_THRESHOLD (300) — must be reviewed before handover
        "ACTION" — rpn >= RPN_ACTION_THRESHOLD (150) — requires explicit control plan
        "ACCEPT" — rpn < RPN_ACTION_THRESHOLD — monitor only
    """
    if rpn >= RPN_ANDON_THRESHOLD:
        return "ANDON"
    if rpn >= RPN_ACTION_THRESHOLD:
        return "ACTION"
    return "ACCEPT"
