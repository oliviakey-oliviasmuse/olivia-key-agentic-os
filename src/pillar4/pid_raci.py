"""
PID & RACI Generator — Pillar 4, Agent 0

Generates a PRINCE2 Project Initiation Document (PID) and RACI matrix.
Stage gate between sales and delivery: the countersigned PID, not the
signed contract, is the green light for delivery to start.

Gates:
    G1: client_name, scope, and ≥1 deliverable required   — hard, ValueError
    G2: At least 3 quality standards (CTQ/PPD pairs)       — hard, ValueError
    G3: Each RACI row must have ≥1 Responsible and ≥1 Accountable — soft, warning only

Defect codes:
    D1: Scope changed after PID sign-off without document update
    D2: RACI missing a key role — confusion during delivery
    D3: Quality standard not linked to a PPD — acceptance disputes
"""

from dataclasses import dataclass, field

DEFECT_CODES = {
    "D1": "Scope changed after PID sign-off without document update — scope creep risk",
    "D2": "RACI missing a key role — confusion during delivery",
    "D3": "Quality standard not linked to a PPD — acceptance disputes at handover",
}

DEFAULT_COMM_FREQUENCY = "Weekly"
DEFAULT_COMM_FORMAT = "Email summary + video call"
DEFAULT_COMM_OWNER = "Olivia Key"


@dataclass
class QualityStandard:
    ctq: str
    ppd_ref: str | None = None
    lsl: float | bool | None = None
    usl: float | bool | None = None
    unit: str = ""


@dataclass
class RACIRow:
    deliverable: str
    responsible: list[str] = field(default_factory=list)
    accountable: list[str] = field(default_factory=list)
    consulted: list[str] = field(default_factory=list)
    informed: list[str] = field(default_factory=list)


@dataclass
class RiskRow:
    mode: str
    rpn: int | None = None
    mitigation: str = ""


@dataclass
class CommunicationEntry:
    frequency: str = DEFAULT_COMM_FREQUENCY
    format: str = DEFAULT_COMM_FORMAT
    owner: str = DEFAULT_COMM_OWNER
    attendees: list[str] = field(default_factory=list)


@dataclass
class PIDResult:
    markdown: str
    warnings: list[str] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)
    gate: str = "PASS"
    signed_off: bool = False


def validate_raci(raci_rows: list[RACIRow]) -> list[str]:
    """
    Returns warning strings for rows missing Responsible or Accountable.
    G3: soft gate — warnings only, never blocks generation.
    """
    warnings = []
    for row in raci_rows:
        if not row.responsible:
            warnings.append(f"D2: RACI row '{row.deliverable}' has no Responsible assigned")
        if not row.accountable:
            warnings.append(f"D2: RACI row '{row.deliverable}' has no Accountable assigned")
    return warnings


def build_pid(
    client_name: str,
    engagement_name: str,
    scope: str,
    deliverables: list[str],
    quality_standards: list[QualityStandard],
    raci_rows: list[RACIRow] | None = None,
    risks: list[RiskRow] | None = None,
    assumptions: list[str] | None = None,
    constraints: list[str] | None = None,
    communication: CommunicationEntry | None = None,
    timeline_start: str = "",
    timeline_end: str = "",
    date: str = "",
    include_raci: bool = True,
    include_communication_plan: bool = True,
    include_risks: bool = True,
    include_approval: bool = True,
    signed_off: bool = False,
) -> PIDResult:
    """
    Build the PID and RACI from engagement data.

    signed_off=False → PENDING SIGN-OFF notice in output.
    Delivery cannot start until signed_off=True.
    """
    warnings: list[str] = []
    defects: list[str] = []

    # G1: proposal data required
    if not client_name or not client_name.strip():
        raise ValueError("G1: Missing proposal data — client name required")
    if not scope or not scope.strip():
        raise ValueError("G1: Missing proposal data — scope required")
    if not deliverables:
        raise ValueError("G1: Missing proposal data — at least one deliverable required")

    # G2: quality standards minimum
    if len(quality_standards) < 3:
        raise ValueError(
            f"G2: Insufficient quality standards — {len(quality_standards)} provided, minimum 3 required"
        )

    # D3: standards without PPD refs
    for qs in quality_standards:
        if qs.ppd_ref is None:
            defects.append(f"D3: Quality standard '{qs.ctq}' not linked to a PPD")

    # G3: RACI validation (soft)
    raci_rows = raci_rows or []
    if include_raci and raci_rows:
        warnings.extend(validate_raci(raci_rows))

    md = _render_markdown(
        client_name=client_name,
        engagement_name=engagement_name,
        scope=scope,
        deliverables=deliverables,
        quality_standards=quality_standards,
        raci_rows=raci_rows,
        risks=risks or [],
        assumptions=assumptions or [],
        constraints=constraints or [],
        communication=communication or CommunicationEntry(),
        timeline_start=timeline_start,
        timeline_end=timeline_end,
        date=date,
        include_raci=include_raci,
        include_communication_plan=include_communication_plan,
        include_risks=include_risks,
        include_approval=include_approval,
        signed_off=signed_off,
    )

    return PIDResult(
        markdown=md,
        warnings=warnings,
        defects=defects,
        gate="PASS",
        signed_off=signed_off,
    )


def _render_markdown(
    client_name, engagement_name, scope, deliverables, quality_standards,
    raci_rows, risks, assumptions, constraints, communication,
    timeline_start, timeline_end, date,
    include_raci, include_communication_plan, include_risks, include_approval,
    signed_off,
) -> str:
    md = f"# Project Initiation Document – {client_name}\n"
    if date:
        md += f"**Date:** {date}\n"
    if not signed_off:
        md += "\n> PENDING SIGN-OFF — delivery cannot start until this PID is countersigned.\n"
    md += "\n"

    # Project Overview
    md += "## Project Overview\n"
    md += f"- **Client:** {client_name}\n"
    md += f"- **Engagement:** {engagement_name}\n"
    md += f"- **Scope:** {scope}\n"
    md += "- **Deliverables:**\n"
    for d in deliverables:
        md += f"  - {d}\n"
    if timeline_start or timeline_end:
        parts = [p for p in [timeline_start, timeline_end] if p]
        md += f"- **Timeline:** {' – '.join(parts)}\n"
    md += "\n"

    # Quality Standards
    md += "## Quality Standards\n"
    for qs in quality_standards:
        spec_parts = []
        if qs.lsl is not None:
            spec_parts.append(f"LSL: {qs.lsl}")
        if qs.usl is not None:
            spec_parts.append(f"USL: {qs.usl}")
        spec = " / ".join(spec_parts) if spec_parts else "TBC"
        ppd = f" — PPD: {qs.ppd_ref}" if qs.ppd_ref else " — PPD: not linked"
        unit = f" ({qs.unit})" if qs.unit else ""
        md += f"- {qs.ctq}{unit}: {spec}{ppd}\n"
    md += "\n"

    # Assumptions & Constraints
    if assumptions or constraints:
        md += "## Assumptions & Constraints\n"
        for a in assumptions:
            md += f"- Assumption: {a}\n"
        for c in constraints:
            md += f"- Constraint: {c}\n"
        md += "\n"

    # Risks
    if include_risks:
        md += "## Risks\n"
        if risks:
            md += "| Risk | RPN | Mitigation |\n"
            md += "|------|-----|------------|\n"
            for r in risks:
                rpn = str(r.rpn) if r.rpn is not None else "—"
                md += f"| {r.mode} | {rpn} | {r.mitigation} |\n"
        else:
            md += "[No risks provided — add from FMEA before sign-off]\n"
        md += "\n"

    # Communication Plan
    if include_communication_plan:
        md += "## Communication Plan\n"
        md += f"- **Frequency:** {communication.frequency}\n"
        md += f"- **Format:** {communication.format}\n"
        md += f"- **Owner:** {communication.owner}\n"
        if communication.attendees:
            md += f"- **Attendees:** {', '.join(communication.attendees)}\n"
        md += "\n"

    # RACI Matrix
    if include_raci:
        md += "## RACI Matrix\n"
        if raci_rows:
            md += "| Deliverable | Responsible | Accountable | Consulted | Informed |\n"
            md += "|---|---|---|---|---|\n"
            for row in raci_rows:
                md += (
                    f"| {row.deliverable} "
                    f"| {', '.join(row.responsible) or '—'} "
                    f"| {', '.join(row.accountable) or '—'} "
                    f"| {', '.join(row.consulted) or '—'} "
                    f"| {', '.join(row.informed) or '—'} |\n"
                )
        else:
            md += "[No RACI rows provided — add before sign-off]\n"
        md += "\n"

    # Sign-off
    if include_approval:
        md += "## Sign-off\n"
        md += "- [ ] Scope reviewed\n"
        md += "- [ ] Quality standards accepted\n"
        md += f"- [ ] Approved by {client_name}\n"

    return md


# Re-export generator API so both layers are importable from a single module.
# Allows: from src.pillar4.pid_raci import Deliverable, generate_pid, ...
from src.pillar4.pid_raci_generator import (  # noqa: E402
    Deliverable,
    PID,
    generate_pid,
    validate_pid,
    raci_matrix_markdown,
    pid_markdown,
    generate_pid_from_inputs,
)
