"""
ICP Qualification Rubric — Pillar 0, Agent 1
LSS MBB / CIM STP / PRINCE2 Business Case.

Scores a prospect against 5 ICP criteria (1–5 each, max 25).
  PROCEED  ≥ 18/25
  DEFER    12–17/25
  REJECT   < 12/25

PRINCE2 Business Case secondary filter: viable / desirable / achievable.
Source of truth for the ICP rubric applied in P4 Sales (pillar-3 in code).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

CRITERIA = ['company_size', 'sector_fit', 'role_title', 'pain_indicators', 'budget_authority']

THRESHOLD_PROCEED = 18
THRESHOLD_DEFER = 12

CRITERIA_GUIDE = {
    'company_size':      '1=<£1M | 2=£1–10M | 3=£10–25M | 4=£25–50M | 5=£50M+',
    'sector_fit':        '1=no operational exposure | 3=mixed | 5=capital-intensive mfg/ops',
    'role_title':        '1=no authority | 3=mid-mgmt | 5=CEO/COO/VP Ops/MD with P&L',
    'pain_indicators':   '1=no awareness | 3=aware but passive | 5=active crisis / CoPQ identified',
    'budget_authority':  '1=no budget/authority | 3=indirect influence | 5=confirmed authority + budget',
}

DEFECT_CODES = {
    'R1': 'Prospect scored below PROCEED threshold but discovery call booked anyway',
    'R2': 'Rubric not calibrated against ≥20 contacts at ≥80% confidence',
    'R3': 'Criteria descriptions not updated after ICP language captured from discovery',
}


@dataclass
class ICPScore:
    prospect_name: str
    company_size: int
    sector_fit: int
    role_title: int
    pain_indicators: int
    budget_authority: int
    date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.prospect_name:
            raise ValueError("G1: prospect_name required")
        for criterion in CRITERIA:
            val = getattr(self, criterion)
            if not isinstance(val, int) or not (1 <= val <= 5):
                raise ValueError(f"G2: {criterion} must be an integer between 1 and 5")
        try:
            datetime.strptime(self.date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("G3: date must be YYYY-MM-DD")

    @property
    def total(self) -> int:
        return (self.company_size + self.sector_fit + self.role_title
                + self.pain_indicators + self.budget_authority)

    @property
    def verdict(self) -> str:
        if self.total >= THRESHOLD_PROCEED:
            return 'PROCEED'
        elif self.total >= THRESHOLD_DEFER:
            return 'DEFER'
        return 'REJECT'


@dataclass
class BusinessCaseFilter:
    prospect_name: str
    viable: bool
    desirable: bool
    achievable: bool

    def __post_init__(self):
        if not self.prospect_name:
            raise ValueError("G1: prospect_name required")

    @property
    def passes(self) -> bool:
        return self.viable and self.desirable and self.achievable

    @property
    def verdict(self) -> str:
        return 'PASS' if self.passes else 'FAIL'

    def failed_dimensions(self) -> List[str]:
        dims = []
        if not self.viable:
            dims.append('viable')
        if not self.desirable:
            dims.append('desirable')
        if not self.achievable:
            dims.append('achievable')
        return dims


def compute_rubric_summary(scores: List[ICPScore]) -> dict:
    total = len(scores)
    proceed = sum(1 for s in scores if s.verdict == 'PROCEED')
    defer = sum(1 for s in scores if s.verdict == 'DEFER')
    reject = sum(1 for s in scores if s.verdict == 'REJECT')
    return {
        'total': total,
        'proceed': proceed,
        'defer': defer,
        'reject': reject,
        'proceed_rate_pct': round(proceed / total * 100, 1) if total > 0 else 0.0,
    }


def generate_icp_report(score: ICPScore, bc_filter: Optional[BusinessCaseFilter] = None) -> str:
    md = "# ICP Qualification Report\n\n"
    md += f"**Prospect: {score.prospect_name}**\n"
    md += f"**Date: {score.date}**\n\n"

    md += "## Rubric Scores\n"
    md += "| Criterion | Score | /5 |\n"
    md += "|-----------|-------|----|\n"
    for c in CRITERIA:
        label = c.replace('_', ' ').title()
        md += f"| {label} | {getattr(score, c)} | 5 |\n"
    md += f"\n**Total: {score.total}/25**\n"
    md += f"**Verdict: {score.verdict}**\n\n"

    if bc_filter:
        md += "## PRINCE2 Business Case Filter\n"
        md += f"**Viable: {'Yes' if bc_filter.viable else 'No'}**\n"
        md += f"**Desirable: {'Yes' if bc_filter.desirable else 'No'}**\n"
        md += f"**Achievable: {'Yes' if bc_filter.achievable else 'No'}**\n"
        md += f"**Business Case: {bc_filter.verdict}**\n"
        if not bc_filter.passes:
            md += f"**Failed dimensions: {', '.join(bc_filter.failed_dimensions())}**\n"
        md += "\n"

    if score.notes:
        md += f"## Notes\n{score.notes}\n"

    return md
