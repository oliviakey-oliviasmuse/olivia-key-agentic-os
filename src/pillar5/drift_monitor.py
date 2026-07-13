"""
Strategic Drift Monitor — Pillar 5 extension.
Wraps Pillar 0 Strategic Drift Detector for weekly review.
"""

from typing import Optional, Dict, List

try:
    from src.pillar0.drift_detector_generator import (
        run_drift_check,
        create_rule,
        run_weekly_drift_review as _p0_weekly_review,
    )
    _P0_AVAILABLE = True
except ImportError:
    run_drift_check = None
    create_rule = None
    _p0_weekly_review = None
    _P0_AVAILABLE = False


def run_weekly_drift_review(data_feeds: Optional[Dict[str, List]] = None) -> str:
    """
    Generate a strategic drift report for the week using Pillar 0 drift rules.

    data_feeds: dict with keys 'content_log', 'proposal_log', 'delivery_log',
                'finance_log'. Each value is a list of event dicts.
                Pass None or empty dict for a no-breach baseline report.

    Returns drift report as markdown string.
    """
    if not _P0_AVAILABLE:
        return "Pillar 0 not available — drift check skipped."

    if data_feeds is None:
        data_feeds = {}

    return _p0_weekly_review(data_feeds=data_feeds or None)
