"""
Budget Variance Analyser – Pillar 6, Agent 1
LSS MBB / Budget Control.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class BudgetLine:
    name: str
    budgeted_amount: float
    actual_amount: float

    def variance(self) -> float:
        if self.budgeted_amount == 0:
            return 0.0
        return ((self.actual_amount - self.budgeted_amount) / self.budgeted_amount) * 100

    def status(self, warning_threshold: float = 5.0, escalate_threshold: float = 10.0) -> str:
        var = abs(self.variance())
        if var <= warning_threshold:
            return 'OK'
        elif var <= escalate_threshold:
            return 'WARNING'
        else:
            return 'ESCALATE'


def validate_inputs(period: str, budget_lines: List[BudgetLine]) -> None:
    if not period:
        raise ValueError("G1: period required")
    if not budget_lines:
        raise ValueError("G2: budget_lines must be non-empty")


def compute_summary(lines: List[BudgetLine]) -> Dict[str, Any]:
    total_budget = sum(l.budgeted_amount for l in lines)
    total_actual = sum(l.actual_amount for l in lines)
    overall_variance = (
        (total_actual - total_budget) / total_budget * 100
        if total_budget > 0
        else 0.0
    )
    return {
        'total_budget': total_budget,
        'total_actual': total_actual,
        'overall_variance': overall_variance,
        'ok_count': sum(1 for l in lines if l.status() == 'OK'),
        'warning_count': sum(1 for l in lines if l.status() == 'WARNING'),
        'escalate_count': sum(1 for l in lines if l.status() == 'ESCALATE'),
    }


def generate_variance_report(
    lines: List[BudgetLine],
    period: str,
    warning_threshold: float = 5.0,
    escalate_threshold: float = 10.0,
) -> str:
    validate_inputs(period, lines)

    # G3: skip zero/negative budget lines; G4: flag negative actual amounts
    g3_skipped: List[str] = []
    g4_flagged: List[str] = []
    valid_lines: List[BudgetLine] = []
    for line in lines:
        if line.budgeted_amount <= 0:
            g3_skipped.append(line.name)
            continue
        if line.actual_amount < 0:
            g4_flagged.append(line.name)
        valid_lines.append(line)

    summary = compute_summary(valid_lines) if valid_lines else {
        'total_budget': 0.0, 'total_actual': 0.0, 'overall_variance': 0.0,
        'ok_count': 0, 'warning_count': 0, 'escalate_count': 0,
    }

    md = f"# Budget Variance Report – {period}\n\n"

    if g3_skipped:
        md += f"**G3 WARNING:** Lines skipped (zero/negative budget): {', '.join(g3_skipped)}\n\n"
    if g4_flagged:
        md += f"**G4 WARNING:** Negative actual amount on: {', '.join(g4_flagged)}\n\n"

    md += "| Line Item | Budget (£) | Actual (£) | Variance % | Status |\n"
    md += "|-----------|------------|------------|------------|--------|\n"
    for line in valid_lines:
        var_str = f"{line.variance():+.1f}%"
        md += (
            f"| {line.name} | {line.budgeted_amount:,.2f} | "
            f"{line.actual_amount:,.2f} | {var_str} | "
            f"{line.status(warning_threshold, escalate_threshold)} |\n"
        )

    md += "\n## Summary\n"
    md += f"Total budget: £{summary['total_budget']:,.2f}\n"
    md += f"Total actual: £{summary['total_actual']:,.2f}\n"
    md += f"Overall variance: {summary['overall_variance']:+.1f}%\n"
    md += f"OK lines: {summary['ok_count']}\n"
    md += f"WARNING lines: {summary['warning_count']}\n"
    md += f"ESCALATE lines: {summary['escalate_count']}\n"

    escalations = [
        l for l in valid_lines
        if l.status(warning_threshold, escalate_threshold) == 'ESCALATE'
    ]
    if escalations:
        md += "\n## Escalations (Issue Register)\n"
        for l in escalations:
            md += f"- {l.name}: variance {l.variance():+.1f}% – log to Issue Register\n"

    return md
