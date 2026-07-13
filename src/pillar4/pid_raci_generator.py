"""
PID & RACI Generator – Pillar 4, Agent 0
PRINCE2 PID + RACI matrix from proposal, CTQ, PPDs, Control Plan.

LLM-facing wrapper. For the deterministic, gate-enforced layer see pid_raci.py.
Uses flat string fields on Deliverable (vs list-of-str in the deterministic layer)
and a flat PID dataclass (vs the build_pid() function's explicit kwargs).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


# --- Dataclasses ---

@dataclass
class Deliverable:
    name: str
    responsible: str = ""
    accountable: str = ""
    consulted: str = ""
    informed: str = ""


@dataclass
class PID:
    client: str
    engagement: str
    scope: str
    deliverables: List[Deliverable]
    quality_standards: List[str]
    assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    risks: List[Dict[str, str]] = field(default_factory=list)
    communication_plan: Dict[str, Any] = field(default_factory=dict)
    timeline: Dict[str, str] = field(default_factory=dict)
    approval: bool = False


# --- Core functions ---

def generate_pid(
    client: str,
    engagement: str,
    scope: str,
    deliverables: List[Deliverable],
    quality_standards: List[str],
    assumptions: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    risks: Optional[List[Dict[str, str]]] = None,
    communication_plan: Optional[Dict[str, Any]] = None,
    timeline: Optional[Dict[str, str]] = None,
) -> PID:
    """Generate a PID data structure from inputs."""
    return PID(
        client=client,
        engagement=engagement,
        scope=scope,
        deliverables=deliverables,
        quality_standards=quality_standards,
        assumptions=assumptions or [],
        constraints=constraints or [],
        risks=risks or [],
        communication_plan=communication_plan or {},
        timeline=timeline or {},
        approval=False,
    )


def validate_pid(pid: PID) -> List[str]:
    """Validate a PID and return a list of warnings/errors."""
    errors = []
    if not pid.client or not pid.engagement:
        errors.append("Client or engagement name missing")
    if not pid.scope:
        errors.append("Scope missing")
    if not pid.deliverables:
        errors.append("No deliverables provided")
    else:
        for d in pid.deliverables:
            if not d.responsible and not d.accountable:
                errors.append(f"Deliverable '{d.name}' has no Responsible or Accountable")
    if not pid.quality_standards:
        errors.append("Quality standards missing")
    return errors


def raci_matrix_markdown(deliverables: List[Deliverable]) -> str:
    """Build a RACI matrix markdown table."""
    if not deliverables:
        return "No deliverables provided."
    md = "| Deliverable | Responsible | Accountable | Consulted | Informed |\n"
    md += "|-------------|-------------|-------------|-----------|----------|\n"
    for d in deliverables:
        md += f"| {d.name} | {d.responsible} | {d.accountable} | {d.consulted} | {d.informed} |\n"
    return md


def pid_markdown(pid: PID) -> str:
    """Generate a complete PID markdown document."""
    md = f"# Project Initiation Document – {pid.client}\n"
    md += f"**Date:** {pid.timeline.get('date', 'YYYY-MM-DD')}\n\n"
    md += "## Project Overview\n"
    md += f"- **Client:** {pid.client}\n"
    md += f"- **Engagement:** {pid.engagement}\n"
    md += f"- **Scope:** {pid.scope}\n"
    md += f"- **Deliverables:** {', '.join([d.name for d in pid.deliverables])}\n"
    if pid.timeline:
        md += f"- **Start:** {pid.timeline.get('start', 'N/A')}\n"
        md += f"- **End:** {pid.timeline.get('end', 'N/A')}\n"
    md += "\n## Quality Standards\n"
    for qs in pid.quality_standards:
        md += f"- {qs}\n"
    if pid.assumptions:
        md += "\n## Assumptions\n"
        for a in pid.assumptions:
            md += f"- {a}\n"
    if pid.constraints:
        md += "\n## Constraints\n"
        for c in pid.constraints:
            md += f"- {c}\n"
    if pid.risks:
        md += "\n## Risks\n"
        md += "| Risk | Mitigation |\n"
        md += "|------|------------|\n"
        for r in pid.risks:
            md += f"| {r.get('description', '')} | {r.get('mitigation', '')} |\n"
    if pid.communication_plan:
        md += "\n## Communication Plan\n"
        md += f"- **Frequency:** {pid.communication_plan.get('frequency', 'Weekly')}\n"
        md += f"- **Format:** {pid.communication_plan.get('format', 'Email / Meeting')}\n"
        md += f"- **Attendees:** {pid.communication_plan.get('attendees', 'Client, Consultant')}\n"
    md += "\n## RACI Matrix\n"
    md += raci_matrix_markdown(pid.deliverables)
    md += "\n## Sign-off\n"
    md += "- [ ] Scope reviewed\n"
    md += "- [ ] Quality standards accepted\n"
    md += f"- [ ] Approved by {pid.client}\n"
    return md


def generate_pid_from_inputs(
    client: str,
    engagement: str,
    scope: str,
    deliverables: list,
    quality_standards: list,
    assumptions: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    risks: Optional[List[Dict[str, str]]] = None,
    communication_plan: Optional[Dict[str, Any]] = None,
    timeline: Optional[Dict[str, str]] = None,
) -> str:
    """
    Convenience wrapper: accepts dict-based deliverables, returns markdown string directly.
    Appends a Warnings section for any deliverable missing Responsible or Accountable.

    deliverables: list of dicts with keys: name, responsible, accountable, consulted, informed
    """
    deliverable_objects = [
        Deliverable(
            name=d.get('name', ''),
            responsible=d.get('responsible', ''),
            accountable=d.get('accountable', ''),
            consulted=d.get('consulted', ''),
            informed=d.get('informed', ''),
        )
        for d in deliverables
    ]

    pid = generate_pid(
        client=client,
        engagement=engagement,
        scope=scope,
        deliverables=deliverable_objects,
        quality_standards=quality_standards,
        assumptions=assumptions,
        constraints=constraints,
        risks=risks,
        communication_plan=communication_plan,
        timeline=timeline,
    )

    md = pid_markdown(pid)

    raci_warnings = [
        e for e in validate_pid(pid)
        if "Responsible or Accountable" in e
    ]
    if raci_warnings:
        md += "\n## Warnings\n"
        for w in raci_warnings:
            md += f"- Warning: No Responsible or Accountable — {w}\n"

    return md
