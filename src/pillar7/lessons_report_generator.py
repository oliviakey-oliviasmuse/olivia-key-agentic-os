"""
Lessons Report Generator – Wrapper for easy use.
"""

from datetime import datetime
from typing import List, Optional
from src.pillar7.lessons_report import LessonsReport, generate_lessons_report


def create_report(
    engagement_name: str,
    client_name: str,
    close_date: str,
    what_worked: List[str],
    what_didnt: List[str],
    root_cause: str,
    corrective_action: str,
    sop_update_required: bool,
    sop_update_description: Optional[str] = None,
    report_date: Optional[str] = None,
    lessons_learned: Optional[List[str]] = None,
) -> LessonsReport:
    return LessonsReport(
        engagement_name=engagement_name,
        client_name=client_name,
        close_date=close_date,
        what_worked=what_worked,
        what_didnt=what_didnt,
        root_cause=root_cause,
        corrective_action=corrective_action,
        sop_update_required=sop_update_required,
        sop_update_description=sop_update_description,
        report_date=report_date or datetime.now().strftime('%Y-%m-%d'),
        lessons_learned=lessons_learned,
    )


def get_lessons_report(report: LessonsReport) -> str:
    return generate_lessons_report(report)


def log_to_lessons_log(report: LessonsReport, log_path: str) -> str:
    """Append report to the Lessons Log file with timestamp. Returns the appended entry."""
    ts = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    entry = (
        f"\n---\n"
        f"## {report.engagement_name} – logged {ts}\n"
        f"**Client:** {report.client_name} | **Close:** {report.close_date}\n"
        f"**Root cause:** {report.root_cause}\n"
        f"**Corrective action:** {report.corrective_action}\n"
        f"SOP update: {'Yes – ' + report.sop_update_description if report.sop_update_required else 'No'}\n"
    )
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(entry)
    return entry
