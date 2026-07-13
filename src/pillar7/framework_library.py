"""
Framework Library Manager – Pillar 7, Agent 1
LSS MBB / IP Management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

VALID_LICENSING = ['Proprietary', 'Licensed', 'Open']


@dataclass
class FrameworkEntry:
    name: str
    problem_solved: str
    inputs: List[str]
    process_steps: List[str]
    outputs: List[str]
    quality_criteria: List[str]
    licensing_status: str
    version: str = "1.0"
    date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("G1: name required")
        if not self.problem_solved:
            raise ValueError("G2: problem_solved required")
        if not self.inputs:
            raise ValueError("G3: inputs must have at least 1 item")
        if not self.process_steps:
            raise ValueError("G4: process_steps must have at least 1 item")
        if not self.outputs:
            raise ValueError("G5: outputs must have at least 1 item")
        if not self.quality_criteria:
            raise ValueError("G6: quality_criteria must have at least 1 item")
        if self.licensing_status not in VALID_LICENSING:
            raise ValueError(f"G7: licensing_status must be one of {VALID_LICENSING}")

    def to_markdown(self) -> str:
        lines = [
            f"# Framework – {self.name}",
            f"**Version: {self.version}** | **Date: {self.date[:10]}**",
            f"**Licensing: {self.licensing_status}**",
            "",
            f"## Problem Solved",
            self.problem_solved,
            "",
            "## Inputs",
        ]
        for item in self.inputs:
            lines.append(f"- {item}")
        lines += ["", "## Process Steps"]
        for i, step in enumerate(self.process_steps, 1):
            lines.append(f"{i}. {step}")
        lines += ["", "## Outputs"]
        for item in self.outputs:
            lines.append(f"- {item}")
        lines += ["", "## Quality Criteria"]
        for item in self.quality_criteria:
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"


def increment_version(current_version: str) -> str:
    parts = current_version.split('.')
    if len(parts) == 2:
        major, minor = parts
        return f"{major}.{int(minor) + 1}"
    return "1.0"


def list_entries(entries: List[FrameworkEntry]) -> str:
    if not entries:
        return "No entries found."
    lines = [
        "## Framework Library",
        "",
        "| Name | Version | Licensing | Date |",
        "|------|---------|-----------|------|",
    ]
    for e in entries:
        lines.append(f"| {e.name} | {e.version} | {e.licensing_status} | {e.date[:10]} |")
    return "\n".join(lines) + "\n"


def search_entries(entries: List[FrameworkEntry], query: str) -> List[FrameworkEntry]:
    q = query.lower()
    return [
        e for e in entries
        if (
            q in e.name.lower()
            or q in e.problem_solved.lower()
            or any(q in inp.lower() for inp in e.inputs)
            or any(q in step.lower() for step in e.process_steps)
        )
    ]
