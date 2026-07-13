"""
Defect Rate Monitor – Pillar 5, Agent 3
LSS MBB / Internal Quality

Tracks internal defect rate (deliverables requiring rework / total deliverables).
Triggers 5 Whys root cause analysis when defect rate breaches the 5% threshold.
Feeds into the Issue Register and SOP update loop.

Rule: "Internal Defect Rate <5% by Month 3. Any breach triggers 5 Whys."

Gates:
    G1: deliverable_name provided       — hard, ValueError
    G2: defect is bool                  — hard, ValueError
    G3: date valid YYYY-MM-DD           — hard, ValueError

Defect codes:
    D1: Defect rate >5% not investigated → missed root cause
    D2: 5 Whys not documented → repeat defect likely
    D3: Corrective action not linked to SOP update → process improvement missed
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List

DEFECT_THRESHOLD = 5.0


@dataclass
class DefectRecord:
    deliverable_name: str
    defect: bool
    date: str
    defect_description: str = ""
    process_type: str = "general"
    root_cause: str = ""
    corrective_action: str = ""

    def __post_init__(self):
        if not self.deliverable_name:
            raise ValueError("G1: deliverable_name is required")
        if not isinstance(self.defect, bool):
            raise ValueError("G2: defect must be a bool (True or False)")
        if self.date:
            try:
                datetime.strptime(self.date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("G3: date must be YYYY-MM-DD")


def compute_defect_rate(records: List[DefectRecord]) -> Optional[float]:
    if not records:
        return None
    defects = sum(1 for r in records if r.defect)
    return (defects / len(records)) * 100


def filter_window(
    records: List[DefectRecord], window_days: Optional[int] = None
) -> List[DefectRecord]:
    if window_days is None:
        return records
    cutoff = (datetime.now() - timedelta(days=window_days)).strftime('%Y-%m-%d')
    return [r for r in records if r.date >= cutoff]


def check_threshold(rate: Optional[float], threshold: float = DEFECT_THRESHOLD) -> str:
    if rate is None:
        return "NO_DATA"
    if rate >= threshold:
        return f"WARNING – defect rate {rate:.1f}% ≥ {threshold:.0f}% target: 5 Whys triggered"
    return f"OK – defect rate {rate:.1f}% < {threshold:.0f}% target"


def generate_five_whys_prompt(defect_description: str = "") -> str:
    desc = defect_description or "a defect requiring rework"
    md = f"**Defect:** {desc}\n\n"
    md += "1. Why did the defect occur?\n   - [answer]\n"
    md += "2. Why did that happen?\n   - [answer]\n"
    md += "3. Why did that happen?\n   - [answer]\n"
    md += "4. Why did that happen?\n   - [answer]\n"
    md += "5. Why did that happen?\n   - [root cause]\n"
    return md


def generate_defect_report(
    records: List[DefectRecord],
    process_type: str = "general",
    threshold: float = DEFECT_THRESHOLD,
    window_days: Optional[int] = None,
) -> str:
    period_label = f"last {window_days} days" if window_days else "all time"
    windowed = filter_window(records, window_days)
    total = len(windowed)
    defects = sum(1 for r in windowed if r.defect)
    rate = compute_defect_rate(windowed)
    status = check_threshold(rate, threshold)
    five_whys_triggered = rate is not None and rate >= threshold

    md = f"# Defect Rate Report – {process_type}\n"
    md += f"**Period:** {period_label}\n"
    md += f"Total deliverables: {total}\n"
    md += f"Defects (rework): {defects}\n"
    md += f"**Defect rate:** {rate:.1f}%\n" if rate is not None else "**Defect rate:** N/A\n"
    md += f"\n**Status:** {status}\n"

    if five_whys_triggered:
        most_recent_desc = next(
            (r.defect_description for r in reversed(windowed) if r.defect and r.defect_description),
            "",
        )
        md += "\n## 5 Whys\n"
        md += generate_five_whys_prompt(most_recent_desc)
        md += "\n## Root Cause\n[Root cause identified after investigation]\n"
        md += "\n## Corrective Action\n[Action taken]\n"
        md += "\n## SOP Update\n[Yes/No – if yes, link to SOP Writer]\n"

    return md
