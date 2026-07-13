"""
Product Pipeline Manager – Pillar 7, Agent 2
LSS MBB / Product Development.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

VALID_STATUSES = ['Concept', 'In Development', 'Launched', 'Dropped']

DEFAULT_EV_THRESHOLD = 15000.0


@dataclass
class ProductConcept:
    name: str
    launch_probability: float
    projected_revenue_year1: float
    description: Optional[str] = None
    status: str = "Concept"
    ev_threshold: float = DEFAULT_EV_THRESHOLD
    launch_date: Optional[str] = None
    created_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))

    def __post_init__(self):
        if not self.name:
            raise ValueError("G1: name required")
        if not (0.0 <= self.launch_probability <= 1.0):
            raise ValueError("G2: launch_probability must be between 0 and 1")
        if self.projected_revenue_year1 < 0:
            raise ValueError("G3: projected_revenue_year1 must be >= 0")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"G4: status must be one of {VALID_STATUSES}")

    @property
    def ev(self) -> float:
        return self.launch_probability * self.projected_revenue_year1

    @property
    def meets_threshold(self) -> bool:
        return self.ev >= self.ev_threshold


def compute_pipeline_summary(products: List[ProductConcept]) -> Dict[str, Any]:
    total = len(products)
    total_ev = sum(p.ev for p in products)
    meeting_threshold = sum(1 for p in products if p.meets_threshold)
    return {
        'total': total,
        'total_ev': total_ev,
        'meeting_threshold': meeting_threshold,
    }


def generate_pipeline_report(products: List[ProductConcept]) -> str:
    if not products:
        return "# Product Pipeline\nNo products in pipeline."

    summary = compute_pipeline_summary(products)
    md = "# Product Pipeline\n\n"
    md += "## Summary\n"
    md += f"- **Total products: {summary['total']}**\n"
    md += f"- **Total EV: £{summary['total_ev']:,.2f}**\n"
    md += f"- **Products meeting threshold: {summary['meeting_threshold']}**\n\n"
    md += "## Products\n"
    md += "| Name | Status | P(launch) | Revenue | EV | Meets Threshold |\n"
    md += "|------|--------|-----------|---------|----|-----------------|\n"
    for p in products:
        meets = "PASS" if p.meets_threshold else "BELOW THRESHOLD"
        md += (
            f"| {p.name} | {p.status} | {p.launch_probability:.2f} "
            f"| £{p.projected_revenue_year1:,.2f} | £{p.ev:,.2f} | {meets} |\n"
        )
    return md
