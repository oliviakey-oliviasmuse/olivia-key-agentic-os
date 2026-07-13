"""
Budget Variance Analyser – Wrapper for easy use.
"""

from typing import List, Optional
from src.pillar6.budget_variance import (
    BudgetLine,
    compute_summary,
    generate_variance_report,
)


def create_budget_line(name: str, budgeted_amount: float, actual_amount: float) -> BudgetLine:
    return BudgetLine(name=name, budgeted_amount=budgeted_amount, actual_amount=actual_amount)


def get_variance_report(lines: List[BudgetLine], period: str) -> str:
    return generate_variance_report(lines, period)


def log_escalations_to_issue_register(
    lines: List[BudgetLine],
    issue_register_path: Optional[str] = None,
) -> str:
    escalations = [l for l in lines if l.status() == 'ESCALATE']
    if not escalations:
        return "No escalations to log."

    log_entry = ""
    for l in escalations:
        log_entry += f"- {l.name}: variance {l.variance():+.1f}% – budget breach >10%\n"

    if issue_register_path:
        with open(issue_register_path, 'a', encoding='utf-8') as f:
            f.write(f"\n---\n## Budget Variance Escalations\n{log_entry}\n")

    return log_entry
