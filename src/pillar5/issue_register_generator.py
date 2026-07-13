"""
Issue Register Manager – Wrapper for easy use.
"""

from typing import Optional
from src.pillar5.issue_register import Issue, VALID_CATEGORIES, VALID_TOLERANCES, format_issue_markdown


def create_issue(
    issue_description: str,
    category: str,
    tolerance_dimension: str,
    severity: int,
    proposed_resolution: Optional[str] = None,
    raised_by: str = "Olivia",
) -> Issue:
    return Issue(
        issue_description=issue_description,
        category=category,
        tolerance_dimension=tolerance_dimension,
        severity=severity,
        proposed_resolution=proposed_resolution or "",
        raised_by=raised_by,
    )


def log_issue(issue: Issue, register_path: Optional[str] = None) -> str:
    md = format_issue_markdown(issue)
    if register_path:
        try:
            with open(register_path, 'a') as f:
                f.write(f"\n\n---\n\n{md}\n")
        except Exception as e:
            md += f"\n\n*Failed to write to Issue Register: {str(e)}*"
    return md
