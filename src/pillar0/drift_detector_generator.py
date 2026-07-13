"""
Strategic Drift Detector – Wrapper for easy use.
"""

from datetime import datetime
from typing import Optional, List, Dict
from src.pillar0.drift_detector import DriftRule, DriftReport, generate_drift_report


def create_rule(
    rule_id: str,
    description: str,
    metric: str,
    threshold: float,
    time_window_days: int,
    andon_level: str,
    escalation_path: str = "Owner",
) -> DriftRule:
    return DriftRule(
        id=rule_id,
        description=description,
        metric=metric,
        threshold=threshold,
        time_window_days=time_window_days,
        andon_level=andon_level,
        escalation_path=escalation_path,
    )


def run_drift_check(
    rules: List[DriftRule],
    data_feeds: Dict[str, List[Dict]],
    report_date: Optional[str] = None,
) -> str:
    report = generate_drift_report(rules, data_feeds, report_date)
    return report.to_markdown()


def get_drift_report(
    rules: List[DriftRule],
    data_feeds: Dict[str, List[Dict]],
    report_date: Optional[str] = None,
) -> DriftReport:
    return generate_drift_report(rules, data_feeds, report_date)


def run_weekly_drift_review(data_feeds: Optional[Dict[str, List]] = None) -> str:
    """
    Run the standard weekly strategic drift review using the four default P0 rules.
    data_feeds: dict with keys 'content_log', 'proposal_log', 'delivery_log', 'finance_log'.
    Each value is a list of event dicts. Pass None or empty lists to get a no-breach report.
    Returns drift report as markdown.
    """
    rules = [
        create_rule("R1", "Content voice/ICP violations", "content_violations", 3, 30, "CRITICAL"),
        create_rule("R2", "Proposals below price floor", "proposal_below_floor", 1, 30, "CRITICAL"),
        create_rule("R3", "Deliveries outside ICP", "delivery_outside_icp", 2, 30, "WARNING"),
        create_rule("R4", "Revenue decline >20% MoM", "revenue_decline", 20.0, 30, "WARNING"),
    ]
    if data_feeds is None:
        data_feeds = {
            "content_log": [],
            "proposal_log": [],
            "delivery_log": [],
            "finance_log": [],
        }
    report_date = datetime.now().strftime("%Y-%m-%d")
    return run_drift_check(rules, data_feeds, report_date)
