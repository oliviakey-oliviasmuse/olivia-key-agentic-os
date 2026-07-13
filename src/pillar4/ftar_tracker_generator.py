"""
FTAR Tracker – Pillar 4, Agent 3 (LLM wrapper)
"""

from typing import List, Optional
from src.pillar4.ftar_tracker import FTARRecord, compute_ftar_summary


def add_record(
    deliverable_name: str,
    status: str,
    failure_reason: Optional[str] = None,
    client_name: Optional[str] = None,
    engagement_name: Optional[str] = None,
    reviewer: Optional[str] = None,
    notes: Optional[str] = None,
) -> FTARRecord:
    """Create a new FTAR record. Enforces G1 (deliverable_name required)."""
    if not deliverable_name:
        raise ValueError("G1: deliverable_name is required")
    return FTARRecord(
        deliverable_name=deliverable_name,
        status=status,
        failure_reason=failure_reason,
        client_name=client_name,
        engagement_name=engagement_name,
        reviewer=reviewer,
        notes=notes,
    )


def generate_ftar_report(records: List[FTARRecord]) -> str:
    """Generate a markdown summary report from FTAR records."""
    summary = compute_ftar_summary(records)

    md = "# FTAR Report\n"
    md += f"- Total deliverables: {summary.total}\n"
    md += f"- Accepted (PASS): {summary.pass_count}\n"
    md += f"- Rework (FAIL): {summary.fail_count}\n"
    md += f"- First-Time Acceptance Rate: {summary.ftar:.1%}\n"
    md += f"- Status: {summary.threshold_status}\n"
    if summary.first_submission:
        md += f"- First submission: {summary.first_submission}\n"
    if summary.last_submission:
        md += f"- Last submission: {summary.last_submission}\n"
    if summary.failure_reasons:
        md += "\n## Failure Reasons\n"
        for reason in summary.failure_reasons:
            md += f"- {reason}\n"
    if summary.threshold_status == 'ANDON':
        md += "\n**ANDON:** FTAR <85% – trigger Lessons Report immediately.\n"
    elif summary.threshold_status == 'WARNING':
        md += "\n**WARNING:** FTAR between 85% and 90% – review root causes.\n"
    elif summary.threshold_status == 'NO_DATA':
        md += "\n**NO_DATA:** No deliverables logged yet.\n"
    else:
        md += "\n**PASS:** FTAR ≥90% – target met.\n"
    return md
