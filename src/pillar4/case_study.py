"""
Case Study Writer — Pillar 4, Agent 2

Generates a PRINCE2-style case study within 15 working days of engagement close.
Output becomes Hero content (P3) and proposal proof (P4).

Gates:
    G1: Both CoPQ baseline and outcome required    — hard, ValueError
    G2: Intervention description required           — hard, ValueError
    G3: At least one metric (FTAR, NPS, repeat)   — soft, warning only

Defect codes:
    E1: Published without client approval
    E2: Outcome overstated vs client-validated number
    E3: Lessons section empty
"""

from dataclasses import dataclass, field

DEFECT_CODES = {
    "E1": "Case study published without client approval — reputational risk",
    "E2": "Outcome overstated vs actual client-validated number — credibility loss",
    "E3": "Lessons section empty — missed learning opportunity",
}

ANONYMISED_NAME = "[Confidential Client]"


@dataclass
class CoPQBreakdown:
    internal: float | None = None
    external: float | None = None
    appraisal: float | None = None
    prevention: float | None = None


@dataclass
class CaseStudyMetrics:
    ftar: float | None = None         # First-Time Acceptance Rate %
    nps: int | None = None
    repeat_engagement: bool | None = None
    roi_pct: float | None = None      # provided directly; if None, calculated from engagement_cost


@dataclass
class CaseStudyResult:
    markdown: str
    warnings: list[str] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)
    gate: str = "PASS"
    client_approved: bool = False     # E1 must be cleared before publishing


def calculate_copq_reduction(baseline: float, outcome: float) -> dict:
    """Returns reduction amount, percentage, and reversed flag."""
    reduction = baseline - outcome
    pct = (reduction / baseline * 100) if baseline > 0 else 0.0
    return {
        "reduction": reduction,
        "pct": pct,
        "reversed": outcome > baseline,
    }


def calculate_roi(copq_reduction: float, engagement_cost: float) -> float | None:
    """ROI = (reduction - cost) / cost × 100. None if cost ≤ 0."""
    if engagement_cost <= 0:
        return None
    return (copq_reduction - engagement_cost) / engagement_cost * 100


def build_case_study(
    client_name: str,
    copq_baseline: float | None,
    copq_outcome: float | None,
    intervention: str | None,
    copq_breakdown: CoPQBreakdown | None = None,
    metrics: CaseStudyMetrics | None = None,
    client_quote: str | None = None,
    quote_attribution: str | None = None,
    lessons: list[str] | None = None,
    engagement_cost: float | None = None,
    industry: str | None = None,
    engagement_duration: str | None = None,
    date: str = "",
    include_quote: bool = True,
    include_lessons: bool = True,
    anonymise: bool = False,
    tone: str = "professional",
    client_approved: bool = False,
) -> CaseStudyResult:
    """
    Build the case study from engagement data.

    tone: "professional" | "conversational" — deterministic layer does not differentiate;
          tone shaping is the LLM layer's responsibility (see agent_case_study.md).
    """
    warnings: list[str] = []
    defects: list[str] = []

    # G1: both CoPQ figures required
    if copq_baseline is None or copq_outcome is None:
        raise ValueError("G1: Both CoPQ baseline and outcome required")

    # G2: intervention required
    if not intervention or not intervention.strip():
        raise ValueError("G2: Intervention description is required")

    # G3: at least one metric — soft warning only
    metrics = metrics or CaseStudyMetrics()
    has_metric = any([
        metrics.ftar is not None,
        metrics.nps is not None,
        metrics.repeat_engagement is not None,
        metrics.roi_pct is not None,
    ])
    if not has_metric and engagement_cost is None:
        warnings.append("G3: No metrics provided — consider adding FTAR, NPS, or repeat engagement")

    # E1: client approval gate
    if not client_approved:
        defects.append(f"E1: {DEFECT_CODES['E1']}")

    # E3: lessons required when include_lessons=True
    if include_lessons and not lessons:
        defects.append(f"E3: {DEFECT_CODES['E3']}")

    # CoPQ reduction
    reduction_data = calculate_copq_reduction(copq_baseline, copq_outcome)
    if reduction_data["reversed"]:
        warnings.append("CoPQ outcome exceeds baseline — verify figures before publishing")

    # ROI: use provided metric, else calculate from engagement_cost
    roi = metrics.roi_pct
    if roi is None and engagement_cost is not None:
        roi = calculate_roi(reduction_data["reduction"], engagement_cost)

    # Anonymisation
    if anonymise and industry:
        display_name = f"[{industry} Client]"
    elif anonymise:
        display_name = ANONYMISED_NAME
    else:
        display_name = client_name

    md = _render_markdown(
        display_name=display_name,
        date=date,
        industry=industry,
        engagement_duration=engagement_duration,
        copq_baseline=copq_baseline,
        copq_outcome=copq_outcome,
        reduction_data=reduction_data,
        copq_breakdown=copq_breakdown,
        intervention=intervention,
        metrics=metrics,
        roi=roi,
        client_quote=client_quote,
        quote_attribution=quote_attribution,
        lessons=lessons,
        include_quote=include_quote,
        include_lessons=include_lessons,
        client_approved=client_approved,
    )

    return CaseStudyResult(
        markdown=md,
        warnings=warnings,
        defects=defects,
        gate="PASS",
        client_approved=client_approved,
    )


def _render_markdown(
    display_name, date, industry, engagement_duration,
    copq_baseline, copq_outcome, reduction_data, copq_breakdown,
    intervention, metrics, roi,
    client_quote, quote_attribution, lessons,
    include_quote, include_lessons, client_approved,
) -> str:
    md = f"# Case Study – {display_name}\n"
    if date:
        md += f"**Date:** {date}\n"
    if not client_approved:
        md += "\n> DRAFT — not approved for publication. Obtain client sign-off before use.\n"
    md += "\n"

    # Client Context
    md += "## Client Context\n"
    context_parts = []
    if industry:
        context_parts.append(industry)
    if engagement_duration:
        context_parts.append(f"engagement duration: {engagement_duration}")
    md += (", ".join(context_parts) + "\n") if context_parts else "[Add client context]\n"
    md += "\n"

    # Problem Quantified
    md += "## Problem Quantified\n"
    md += f"- CoPQ baseline: £{copq_baseline:,.0f}/year\n"
    if copq_breakdown:
        if copq_breakdown.internal is not None:
            md += f"  - Internal failure: £{copq_breakdown.internal:,.0f}\n"
        if copq_breakdown.external is not None:
            md += f"  - External failure: £{copq_breakdown.external:,.0f}\n"
        if copq_breakdown.appraisal is not None:
            md += f"  - Appraisal: £{copq_breakdown.appraisal:,.0f}\n"
        if copq_breakdown.prevention is not None:
            md += f"  - Prevention: £{copq_breakdown.prevention:,.0f}\n"
    md += "\n"

    # Intervention Applied
    md += "## Intervention Applied\n"
    md += f"{intervention}\n\n"

    # Measurable Outcome
    md += "## Measurable Outcome\n"
    md += f"- CoPQ reduction: £{reduction_data['reduction']:,.0f}/year ({reduction_data['pct']:.1f}%)\n"
    md += f"- CoPQ post-engagement: £{copq_outcome:,.0f}/year\n"
    if metrics.ftar is not None:
        md += f"- First-Time Acceptance Rate: {metrics.ftar:.0f}%\n"
    if metrics.nps is not None:
        md += f"- NPS: {metrics.nps}\n"
    if metrics.repeat_engagement is not None:
        md += f"- Repeat engagement: {'Yes' if metrics.repeat_engagement else 'No'}\n"
    if roi is not None:
        md += f"- ROI: {roi:.1f}%\n"
    md += "\n"

    # Client Quote
    if include_quote:
        md += "## Client Quote\n"
        if client_quote:
            attribution = f" – {quote_attribution}" if quote_attribution else ""
            md += f'"{client_quote}"{attribution}\n'
        else:
            md += "[No quote provided — request from client before publishing]\n"
        md += "\n"

    # Lessons Learned
    if include_lessons:
        md += "## Lessons Learned\n"
        if lessons:
            for lesson in lessons:
                md += f"- {lesson}\n"
        else:
            md += "[No lessons recorded — complete before filing]\n"
        md += "\n"

    # Next Steps
    md += "## Next Steps\n"
    md += "Book a review call to discuss further opportunities.\n"

    return md
