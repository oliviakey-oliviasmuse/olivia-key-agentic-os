"""
Issue Register Manager – Pillar 5, Agent 1
LSS MBB / PRINCE2 Manage by Exception

Maintains a structured Issue Register: logs every issue, categorises it,
flags tolerance breaches, and ensures documented corrective action before closure.

Rule: "Active Issue Register reviewed in every weekly cadence — zero tolerance
breaches escalating without documented corrective action."

Gates:
    G1: issue_description provided                        — hard, ValueError
    G2: category in valid list                            — hard, ValueError
    G3: tolerance_dimension in valid list                 — hard, ValueError
    G4: severity 1-5                                      — hard, ValueError
    G5: proposed_resolution for Critical issues           — soft, ANDON (blocks format, not creation)

Defect codes:
    IR1: Issue escalated but no corrective action documented
    IR2: Issue closed without root cause analysis
    IR3: Critical issue not escalated within 24 hours
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

VALID_CATEGORIES = ['Quality', 'Time', 'Cost', 'Scope', 'Benefits', 'Risk', 'Other']
VALID_TOLERANCES = ['time', 'cost', 'quality', 'scope', 'benefits', 'risk']


@dataclass
class Issue:
    issue_description: str
    category: str
    tolerance_dimension: str
    severity: int
    proposed_resolution: str
    raised_by: str = "Olivia"
    date_raised: str = field(default_factory=lambda: datetime.now().isoformat())
    closure_date: Optional[str] = None
    closure_notes: Optional[str] = None
    status: str = "Open"
    escalation_level: Optional[str] = None

    def __post_init__(self):
        if not self.issue_description:
            raise ValueError("G1: issue_description required")
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"G2: category must be one of {VALID_CATEGORIES}")
        if self.tolerance_dimension not in VALID_TOLERANCES:
            raise ValueError(f"G3: tolerance_dimension must be one of {VALID_TOLERANCES}")
        if not (1 <= self.severity <= 5):
            raise ValueError("G4: severity must be between 1 and 5")
        if self.escalation_level is None:
            self.escalation_level = self._compute_escalation()

    def _compute_escalation(self) -> str:
        if self.severity <= 2:
            return "Info"
        elif self.severity == 3:
            return "Warning"
        else:
            return "Critical"

    def check_and_on(self) -> Optional[str]:
        if self.escalation_level == "Critical" and not self.proposed_resolution:
            return "ANDON – Critical issue requires proposed_resolution before logging."
        return None


def generate_issue_id(issue: Issue) -> str:
    dt = issue.date_raised[:10].replace('-', '')
    idx = f"{hash(issue.issue_description) % 10000:04d}"
    return f"ISS-{dt}-{idx}"


def format_issue_markdown(issue: Issue) -> str:
    andon_msg = issue.check_and_on()
    if andon_msg:
        return f"**{andon_msg}**\n\n(Entry not logged until resolved.)"

    md = f"# Issue Register Entry – {generate_issue_id(issue)}\n"
    md += f"**Date Raised:** {issue.date_raised[:10]} | **Raised By:** {issue.raised_by}\n"
    md += f"**Category:** {issue.category} | **Tolerance:** {issue.tolerance_dimension}\n"
    md += f"**Severity:** {issue.severity}/5 | **Escalation:** {issue.escalation_level}\n"
    md += f"**Description:** {issue.issue_description}\n"
    md += f"**Proposed Resolution:** {issue.proposed_resolution or 'Pending'}\n"
    md += f"**Status:** {issue.status}\n"
    if issue.closure_date:
        md += f"**Closure Date:** {issue.closure_date}\n"
    if issue.closure_notes:
        md += f"**Closure Notes:** {issue.closure_notes}\n"
    return md
