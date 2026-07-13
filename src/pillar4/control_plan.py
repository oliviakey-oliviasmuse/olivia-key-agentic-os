"""
Delivery Control Plan Generator — Pillar 4, Agent 1

Bridges P1 CTQ nodes and P3 FMEA engagement risks into a delivery control plan
that operationalises the "hold the gain" principle during client engagements.

Inputs:
    ctq_nodes    : list of CTQNode-compatible objects (.ctq, .unit, .lsl, .usl)
    fmea_results : list of dicts from P3 build_fmea() (mode, rpn, classification, action)
    ctq_mapping  : {fmea_mode: ctq_name}. If None → placeholder rows generated per CTQ (G3 fallback).

Gates:
    G1: CTQ node list must not be empty                          — hard, ValueError
    G2: Each CTQ should have LSL and USL                         — soft, warning only
    G3: In strict mode, every ACTION/ANDON mode must be mapped   — hard, ValueError
    G4: Every ctq_mapping value must match a known CTQ name      — hard, ValueError
"""

from dataclasses import dataclass, field

# --- Constants (RPN thresholds aligned with P3 proposal_builder.py) ---

RPN_ACTION_THRESHOLD = 150
RPN_ANDON_THRESHOLD = 300

DEFAULT_SAMPLE_SIZE = "100% of units"
DEFAULT_FREQUENCY_ANDON = "Daily"
DEFAULT_FREQUENCY_ACTION = "Weekly"
DEFAULT_FREQUENCY_PLACEHOLDER = "Per batch"
DEFAULT_OWNER = "Operations Manager"
DEFAULT_REACTION_PLAN = "Escalate to Operations Director; investigate within 5 days"
DEFAULT_CONTROL_METHOD = "Run chart vs specification"
DEFAULT_MEASUREMENT_METHOD = "Manual inspection / SPC"

DEFECT_CODES = {
    "D1": "Control Plan missing a CTQ that later causes a defect (post-handover)",
    "D2": "Control limit (LSL/USL) wrong — false alarms or missed signals",
    "D3": "Reaction plan missing — client doesn't act on breach",
}


@dataclass
class ControlPlanItem:
    process_step: str
    ctq_name: str
    unit: str
    lsl: float | bool | None
    usl: float | bool | None
    specification: str
    measurement_method: str
    sample_size: str
    frequency: str
    control_method: str
    owner: str
    reaction_plan: str
    rpn: int | None = None
    classification: str | None = None
    is_placeholder: bool = False
    is_andon: bool = False


@dataclass
class ControlPlanResult:
    control_plan: list[ControlPlanItem] = field(default_factory=list)
    orphan_ctqs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    andon_flags: list[str] = field(default_factory=list)
    gate: str = "PASS"
    defects: list[str] = field(default_factory=list)


def _format_specification(lsl, usl, unit: str) -> str:
    parts = []
    if lsl is not None:
        parts.append(f"LSL: {lsl}")
    if usl is not None:
        parts.append(f"USL: {usl}")
    spec = " / ".join(parts) if parts else "Not specified"
    if unit:
        spec += f" {unit}"
    return spec


def _derive_measurement_method(unit: str) -> str:
    u = unit.lower() if unit else ""
    if "%" in u or "rate" in u or "percent" in u:
        return "Weekly % calculation"
    if "day" in u or "hour" in u or "minute" in u:
        return "Time tracking log"
    return DEFAULT_MEASUREMENT_METHOD


def _derive_control_method(classification: str | None) -> str:
    if classification == "ANDON":
        return "ANDON – must be reviewed before handover"
    if classification == "ACTION":
        return "SPC chart with control limits"
    return DEFAULT_CONTROL_METHOD


def validate_ctq_coverage(ctq_nodes: list, control_plan_items: list) -> list[str]:
    """
    Returns list of CTQ names not referenced in any non-placeholder control plan item.
    Call only in strict mode (when ctq_mapping was provided).
    """
    referenced = {item.ctq_name for item in control_plan_items if not item.is_placeholder}
    return [node.ctq for node in ctq_nodes if node.ctq not in referenced]


def build_delivery_control_plan(
    ctq_nodes: list,
    fmea_results: list[dict],
    ctq_mapping: dict[str, str] | None = None,
    owner_overrides: dict[str, str] | None = None,
    measurement_overrides: dict[str, str] | None = None,
    sample_size_overrides: dict[str, str] | None = None,
    include_reaction_plan: bool = True,
    include_owner: bool = True,
    include_sample_size: bool = True,
) -> ControlPlanResult:
    """
    Build the delivery control plan from CTQ nodes and FMEA results.

    ctq_mapping=None  → placeholder mode: one row per CTQ with default values (G3 fallback)
    ctq_mapping={...} → strict mode: every ACTION/ANDON must be explicitly mapped
    """
    owner_overrides = owner_overrides or {}
    measurement_overrides = measurement_overrides or {}
    sample_size_overrides = sample_size_overrides or {}

    warnings: list[str] = []
    andon_flags: list[str] = []

    # G1: Hard gate — no CTQs → no plan
    if not ctq_nodes:
        raise ValueError("G1: CTQ node list is empty — cannot build control plan without CTQs")

    # G2: Soft gate — missing LSL/USL
    for node in ctq_nodes:
        if node.lsl is None:
            warnings.append(f"G2: CTQ '{node.ctq}' missing LSL — specify before handover")
        if node.usl is None:
            warnings.append(f"G2: CTQ '{node.ctq}' missing USL — specify before handover")

    ctq_lookup = {node.ctq: node for node in ctq_nodes}
    plan_items: list[ControlPlanItem] = []

    if ctq_mapping is not None:
        # --- Strict mode ---

        # G4: mapping values must reference known CTQ names
        unknown = [v for v in ctq_mapping.values() if v not in ctq_lookup]
        if unknown:
            raise ValueError(f"G4: ctq_mapping references unknown CTQ names: {unknown}")

        # G3: every ACTION/ANDON must have a mapping entry
        action_modes = [
            r["mode"] for r in fmea_results
            if r["classification"] in ("ACTION", "ANDON")
        ]
        unmapped = [m for m in action_modes if m not in ctq_mapping]
        if unmapped:
            raise ValueError(
                f"G3: ACTION/ANDON FMEA items have no CTQ mapping: {unmapped}"
            )

        for fm in fmea_results:
            if fm["classification"] not in ("ACTION", "ANDON"):
                continue

            ctq_name = ctq_mapping[fm["mode"]]
            node = ctq_lookup[ctq_name]
            freq = DEFAULT_FREQUENCY_ANDON if fm["classification"] == "ANDON" else DEFAULT_FREQUENCY_ACTION
            is_andon = fm["rpn"] >= RPN_ANDON_THRESHOLD

            if is_andon:
                andon_flags.append(
                    f"ANDON – '{fm['mode']}' (RPN {fm['rpn']}) — must be reviewed before handover"
                )

            plan_items.append(ControlPlanItem(
                process_step=fm["mode"],
                ctq_name=ctq_name,
                unit=node.unit,
                lsl=node.lsl,
                usl=node.usl,
                specification=_format_specification(node.lsl, node.usl, node.unit),
                measurement_method=measurement_overrides.get(fm["mode"]) or _derive_measurement_method(node.unit),
                sample_size=sample_size_overrides.get(fm["mode"], DEFAULT_SAMPLE_SIZE) if include_sample_size else "",
                frequency=freq,
                control_method=_derive_control_method(fm["classification"]),
                owner=owner_overrides.get(fm["mode"], DEFAULT_OWNER) if include_owner else "",
                reaction_plan=fm["action"] if include_reaction_plan else "",
                rpn=fm["rpn"],
                classification=fm["classification"],
                is_placeholder=False,
                is_andon=is_andon,
            ))

        # Orphan check — only meaningful in strict mode
        orphans = validate_ctq_coverage(ctq_nodes, plan_items)
        if orphans:
            warnings.append(f"Orphan CTQs (not referenced in any control point): {orphans}")

    else:
        # --- Placeholder mode (G3 fallback) ---
        action_fmea = [r for r in fmea_results if r["classification"] in ("ACTION", "ANDON")]

        for i, node in enumerate(ctq_nodes):
            fm = action_fmea[i] if i < len(action_fmea) else None
            freq = DEFAULT_FREQUENCY_PLACEHOLDER
            classification = None
            rpn = None
            reaction = DEFAULT_REACTION_PLAN if include_reaction_plan else ""
            ctrl_method = DEFAULT_CONTROL_METHOD
            is_andon = False

            if fm:
                freq = DEFAULT_FREQUENCY_ANDON if fm["classification"] == "ANDON" else DEFAULT_FREQUENCY_ACTION
                classification = fm["classification"]
                rpn = fm["rpn"]
                reaction = fm["action"] if include_reaction_plan else ""
                ctrl_method = _derive_control_method(fm["classification"])
                is_andon = fm["rpn"] >= RPN_ANDON_THRESHOLD
                if is_andon:
                    andon_flags.append(
                        f"ANDON – '{fm['mode']}' (RPN {fm['rpn']}) — must be reviewed before handover"
                    )

            plan_items.append(ControlPlanItem(
                process_step="N/A",
                ctq_name=node.ctq,
                unit=node.unit,
                lsl=node.lsl,
                usl=node.usl,
                specification=_format_specification(node.lsl, node.usl, node.unit),
                measurement_method=measurement_overrides.get(node.ctq) or _derive_measurement_method(node.unit),
                sample_size=sample_size_overrides.get(node.ctq, DEFAULT_SAMPLE_SIZE) if include_sample_size else "",
                frequency=freq,
                control_method=ctrl_method,
                owner=owner_overrides.get(node.ctq, DEFAULT_OWNER) if include_owner else "",
                reaction_plan=reaction,
                rpn=rpn,
                classification=classification,
                is_placeholder=True,
                is_andon=is_andon,
            ))

        warnings.append("G3: No CTQ mapping provided — placeholder rows generated for all CTQs")
        orphans = []

    return ControlPlanResult(
        control_plan=plan_items,
        orphan_ctqs=orphans,
        warnings=warnings,
        andon_flags=andon_flags,
        gate="PASS",
        defects=[],
    )


def render_control_plan_md(
    result: ControlPlanResult,
    engagement_name: str = "Engagement",
    client_name: str = "",
    date: str = "",
) -> str:
    title = client_name or engagement_name
    md = f"# Control Plan – {title}\n"
    if date:
        md += f"**Date:** {date}\n"
    md += "\n## Table\n\n"
    md += (
        "| Process Step | CTQ Characteristic | Specification | "
        "Measurement Method | Sample Size | Frequency | Control Method | Owner | Reaction Plan |\n"
    )
    md += "|---|---|---|---|---|---|---|---|---|\n"
    for item in result.control_plan:
        md += (
            f"| {item.process_step} "
            f"| {item.ctq_name} "
            f"| {item.specification} "
            f"| {item.measurement_method} "
            f"| {item.sample_size} "
            f"| {item.frequency} "
            f"| {item.control_method} "
            f"| {item.owner} "
            f"| {item.reaction_plan} |\n"
        )

    if result.andon_flags or result.warnings:
        md += "\n## ANDON / Warnings\n"
        for flag in result.andon_flags:
            md += f"- {flag}\n"
        for w in result.warnings:
            md += f"- {w}\n"

    md += "\n## Sign-off\n"
    md += "- [ ] CTQ tree reviewed\n"
    md += "- [ ] FMEA reviewed\n"
    md += f"- [ ] Control Plan approved by {client_name or '[client name]'}\n"

    return md
