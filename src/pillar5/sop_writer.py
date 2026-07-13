"""
SOP Writer – Pillar 5, Agent 0
LSS MBB Standard Operating Procedure generator with version control and storage.

Gates:
    G1: process_name provided                          — hard, ValueError
    G2: process_description provided                   — hard, ValueError
    G3: steps list has at least 1 item                 — hard, ValueError
    G4: owner provided                                 — hard, ValueError
    G5: quality_gates list has at least 1 gate         — hard, ValueError

Defect codes:
    S1: SOP written but not followed → false assurance
    S2: SOP version not incremented correctly → confusion
    S3: Owner not updated → stale ownership
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List
import re


@dataclass
class QualityGate:
    name: str
    criterion: str
    action_on_fail: str


@dataclass
class DefectCode:
    code: str
    description: str


@dataclass
class SOP:
    process_name: str
    description: str
    steps: List[str]
    owner: str
    quality_gates: List[QualityGate]
    purpose: str = ""
    scope: str = "All applicable instances of this process"
    inputs: List[str] = field(default_factory=lambda: ["User provides necessary data"])
    outputs: List[str] = field(default_factory=lambda: ["Completed process"])
    defect_codes: List[DefectCode] = field(default_factory=list)
    version: str = "1.0"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    review_date: str = field(
        default_factory=lambda: (datetime.now() + timedelta(days=180)).isoformat()
    )
    trigger_count: int = 0

    def __post_init__(self):
        if not self.process_name:
            raise ValueError("G1: process_name is required")
        if not self.description:
            raise ValueError("G2: description is required")
        if not self.steps:
            raise ValueError("G3: steps list must have at least 1 item")
        if not self.owner:
            raise ValueError("G4: owner is required")
        if not self.quality_gates:
            raise ValueError("G5: at least 1 quality_gate is required")
        if not self.purpose:
            self.purpose = self.description


def generate_sop_filename(process_name: str) -> str:
    safe = re.sub(r'[^a-zA-Z0-9\-_]', '_', process_name.lower())
    return f"sop_{safe}.md"


def increment_version(current_version: str) -> str:
    parts = current_version.split('.')
    if len(parts) == 2:
        major, minor = parts
        return f"{major}.{int(minor) + 1}"
    return "1.0"


def format_sop_markdown(sop: SOP) -> str:
    md = f"# SOP – {sop.process_name}\n"
    md += f"**Version:** {sop.version} | Owner: {sop.owner} | **Review Date:** {sop.review_date[:10]}\n\n"
    md += f"## Purpose\n{sop.purpose}\n\n"
    md += f"## Scope\n{sop.scope}\n\n"
    md += "## Inputs\n"
    for inp in sop.inputs:
        md += f"- {inp}\n"
    md += "\n## Outputs\n"
    for out in sop.outputs:
        md += f"- {out}\n"
    md += "\n## Steps\n"
    for i, step in enumerate(sop.steps, 1):
        md += f"{i}. {step}\n"
    md += "\n## Quality Gates\n"
    md += "| Gate | Criterion | Action on Fail |\n"
    md += "|------|-----------|----------------|\n"
    for g in sop.quality_gates:
        md += f"| {g.name} | {g.criterion} | {g.action_on_fail} |\n"
    if sop.defect_codes:
        md += "\n## Defect Codes\n"
        md += "| Code | Description |\n"
        md += "|------|-------------|\n"
        for d in sop.defect_codes:
            md += f"| {d.code} | {d.description} |\n"
    md += "\n## Change Log\n"
    md += "| Date | Version | Change |\n"
    md += "|------|---------|--------|\n"
    md += f"| {sop.created_date[:10]} | {sop.version} | Initial creation |\n"
    md += "\n## Sign-off\n"
    md += f"- [ ] Reviewed by {sop.owner}\n"
    md += "- [ ] Approved by [Manager]\n"
    return md


def trigger_check(sop: SOP) -> Optional[str]:
    if sop.trigger_count >= 3:
        return f"ANDON – SOP must be written before next execution (trigger_count={sop.trigger_count})."
    return None
