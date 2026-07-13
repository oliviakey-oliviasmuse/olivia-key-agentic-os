"""
Lessons Report Generator – Pillar 7, Agent 0
PRINCE2 Learn from Experience.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class LessonsReport:
    engagement_name: str
    client_name: str
    close_date: str
    what_worked: List[str]
    what_didnt: List[str]
    root_cause: str
    corrective_action: str
    sop_update_required: bool
    sop_update_description: Optional[str] = None
    report_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    lessons_learned: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if not self.engagement_name:
            raise ValueError("G1: engagement_name required")
        if not self.client_name:
            raise ValueError("G2: client_name required")
        try:
            datetime.strptime(self.close_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("G3: close_date must be YYYY-MM-DD")
        if not self.what_worked:
            raise ValueError("G4: what_worked must have at least 1 item")
        if not self.what_didnt:
            raise ValueError("G5: what_didnt must have at least 1 item")
        if not self.root_cause:
            raise ValueError("G6: root_cause required")
        if not self.corrective_action:
            raise ValueError("G7: corrective_action required")
        if self.sop_update_required and not self.sop_update_description:
            raise ValueError("sop_update_description required when sop_update_required is True")
        if self.lessons_learned is None:
            self.lessons_learned = self._derive_lessons()

    def _derive_lessons(self) -> List[str]:
        lessons = []
        if self.what_worked:
            lessons.append(f"Continue: {self.what_worked[0]}")
        if self.what_didnt:
            lessons.append(f"Improve: {self.what_didnt[0]}")
        if self.root_cause:
            lessons.append(f"Root cause: {self.root_cause}")
        if self.corrective_action:
            lessons.append(f"Action: {self.corrective_action}")
        return lessons

    def days_since_close(self, as_of: Optional[str] = None) -> int:
        """Days elapsed between close_date and as_of (default: today). Used to check L1 defect."""
        end = (
            datetime.strptime(as_of, '%Y-%m-%d').date()
            if as_of
            else datetime.now().date()
        )
        start = datetime.strptime(self.close_date, '%Y-%m-%d').date()
        return (end - start).days

    def is_overdue(self, days_limit: int = 5, as_of: Optional[str] = None) -> bool:
        """True if report_date is more than days_limit days after close_date (L1 defect)."""
        report_d = datetime.strptime(self.report_date[:10], '%Y-%m-%d').date()
        close_d = datetime.strptime(self.close_date, '%Y-%m-%d').date()
        return (report_d - close_d).days > days_limit


def generate_lessons_report(report: LessonsReport) -> str:
    lines = [
        f"# Lessons Report – {report.engagement_name}",
        f"**Client:** {report.client_name}",
        f"**Close Date:** {report.close_date}",
        f"**Report Date:** {report.report_date[:10]}",
        "**Prepared by:** Olivia Key",
        "",
        "## What Worked",
    ]
    for item in report.what_worked:
        lines.append(f"- {item}")

    lines += ["", "## What Didn't Work"]
    for item in report.what_didnt:
        lines.append(f"- {item}")

    lines += [
        "",
        "## Root Cause (5 Whys)",
        report.root_cause,
        "",
        "## Corrective Action",
        report.corrective_action,
        "",
        "## SOP Update Required?",
        f"**{'Yes' if report.sop_update_required else 'No'}**",
    ]
    if report.sop_update_required and report.sop_update_description:
        lines.append(report.sop_update_description)

    if report.lessons_learned:
        lines += ["", "## Lessons Learned"]
        for lesson in report.lessons_learned:
            lines.append(f"- {lesson}")

    if report.is_overdue():
        lines += ["", "**L1 WARNING: Report generated more than 5 days after close – learning at risk.**"]

    return "\n".join(lines) + "\n"
