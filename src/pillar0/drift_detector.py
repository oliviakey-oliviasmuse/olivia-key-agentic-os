"""
Strategic Drift Detector – Pillar 0, Agent 5
LSS MBB / Strategy Alignment.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

VALID_ANDON_LEVELS = ["CRITICAL", "WARNING", "INFO"]


@dataclass
class DriftRule:
    id: str
    description: str
    metric: str  # content_violations, proposal_below_floor, delivery_outside_icp, revenue_decline
    threshold: float
    time_window_days: int
    andon_level: str  # CRITICAL, WARNING, INFO
    # Default is generic "Owner" — override per-rule in YAML or at construction
    # time with the actual person/team who should be notified on breach.
    escalation_path: str = "Owner"

    def __post_init__(self):
        if not self.id:
            raise ValueError("G2: rule id required")
        if not self.description:
            raise ValueError("G2: rule description required")
        if not self.metric:
            raise ValueError("G2: rule metric required")
        if self.threshold < 0:
            raise ValueError("G2: threshold must be >= 0")
        if self.time_window_days <= 0:
            raise ValueError("G2: time_window_days must be > 0")
        if self.andon_level not in VALID_ANDON_LEVELS:
            raise ValueError(f"G2: andon_level must be one of {VALID_ANDON_LEVELS}")


@dataclass
class DriftBreach:
    rule_id: str
    andon_level: str
    actual_value: float
    threshold: float
    details: str
    escalation_path: str


class DriftReport:
    def __init__(self, date: str, rules_checked: int, breaches: List[DriftBreach]):
        self.date = date
        self.rules_checked = rules_checked
        self.breaches = breaches

    def to_markdown(self) -> str:
        md = f"# Strategic Drift Report – {self.date[:10]}\n\n"
        md += "## Summary\n"
        md += f"**Rules checked: {self.rules_checked}**\n"
        md += f"**Breaches: {len(self.breaches)}**\n"
        md += f"**ANDONs: {sum(1 for b in self.breaches if b.andon_level == 'CRITICAL')}**\n\n"
        if self.breaches:
            md += "## Breaches\n"
            md += "| Rule | ANDON Level | Actual | Threshold | Details | Action Required |\n"
            md += "|------|-------------|--------|-----------|---------|-----------------|\n"
            for b in self.breaches:
                md += (
                    f"| {b.rule_id} | {b.andon_level} | {b.actual_value:.1f} | "
                    f"{b.threshold:.1f} | {b.details} | Escalate to {b.escalation_path} |\n"
                )
        else:
            md += "## No Breaches\nAll rules within tolerance. Strategy remains aligned.\n"
        return md


def check_content_violations(events: List[Dict], rule: DriftRule) -> float:
    return float(sum(1 for e in events if e.get("type") == "content" and e.get("violation", False)))


def check_proposal_below_floor(events: List[Dict], rule: DriftRule) -> float:
    return float(sum(1 for e in events if e.get("type") == "proposal" and e.get("below_floor", False)))


def check_delivery_outside_icp(events: List[Dict], rule: DriftRule) -> float:
    return float(sum(1 for e in events if e.get("type") == "delivery" and e.get("outside_icp", False)))


def check_revenue_decline(events: List[Dict], rule: DriftRule) -> float:
    """MoM revenue decline percentage. Requires full event history — not time-window-filtered."""
    revenues = sorted(
        [e for e in events if e.get("type") == "revenue"],
        key=lambda x: x.get("date", ""),
    )
    if len(revenues) < 2:
        return 0.0
    prev = revenues[-2].get("amount", 0)
    current = revenues[-1].get("amount", 0)
    if prev == 0:
        return 0.0
    return ((prev - current) / prev) * 100


METRIC_FUNCTIONS = {
    "content_violations": check_content_violations,
    "proposal_below_floor": check_proposal_below_floor,
    "delivery_outside_icp": check_delivery_outside_icp,
    "revenue_decline": check_revenue_decline,
}

# Metrics that need full event history (not limited to the time window)
_FULL_HISTORY_METRICS = {"revenue_decline"}


def check_rule(rule: DriftRule, data_feeds: Dict[str, List[Dict]]) -> Optional[DriftBreach]:
    if rule.metric not in METRIC_FUNCTIONS:
        return None
    all_events: List[Dict] = []
    for events in data_feeds.values():
        all_events.extend(events)

    # Revenue decline compares two consecutive periods; must not filter to current window only
    if rule.metric in _FULL_HISTORY_METRICS:
        filtered_events = all_events
    else:
        cutoff_str = (datetime.now() - timedelta(days=rule.time_window_days)).isoformat()
        filtered_events = [e for e in all_events if e.get("date", "") >= cutoff_str]

    actual_value = METRIC_FUNCTIONS[rule.metric](filtered_events, rule)
    if actual_value >= rule.threshold:
        return DriftBreach(
            rule_id=rule.id,
            andon_level=rule.andon_level,
            actual_value=actual_value,
            threshold=rule.threshold,
            details=f"{rule.description} (value: {actual_value:.1f}, threshold: {rule.threshold:.1f})",
            escalation_path=rule.escalation_path,
        )
    return None


def generate_drift_report(
    rules: List[DriftRule],
    data_feeds: Dict[str, List[Dict]],
    date: Optional[str] = None,
) -> DriftReport:
    if not rules:
        raise ValueError("G1: at least one rule required")
    if date is None:
        date = datetime.now().isoformat()
    breaches = [b for rule in rules for b in [check_rule(rule, data_feeds)] if b is not None]
    return DriftReport(date=date, rules_checked=len(rules), breaches=breaches)
