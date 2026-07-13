"""
Case Study Writer – Pillar 4, Agent 2
PRINCE2-style case study from engagement data.

LLM-facing wrapper. For the deterministic, gate-enforced layer see case_study.py.
copq_baseline/outcome here use a dict API rather than float + CoPQBreakdown objects.
"""

# --- Constants ---

DEFAULT_TONE = "professional"
DEFECT_CODES = {
    "E1": "Case study published without client approval",
    "E2": "Outcome overstated vs actual client-validated number",
    "E3": "Lessons section empty – missed learning opportunity",
}


def generate_case_study(
    client_name,
    engagement_name,
    industry,
    copq_baseline,
    copq_outcome,
    intervention,
    metrics,
    client_quote=None,
    lessons=None,
    include_quote=True,
    include_lessons=True,
    anonymise=False,
    tone=DEFAULT_TONE,
    date=None,
):
    """
    Generate a PRINCE2-style case study.

    copq_baseline: dict with 'total' and optionally 'internal', 'external', 'appraisal', 'prevention'
    copq_outcome: dict with 'total' (new CoPQ after engagement)
    intervention: str – description of what was delivered
    metrics: dict with 'ftar', 'nps', 'repeat', 'roi' (optional)
    client_quote: str or None
    lessons: list of str or None
    anonymise: bool – if True, redact client name and industry
    tone: "professional" or "conversational"
    """
    if not copq_baseline or not copq_outcome:
        raise ValueError("G1: CoPQ baseline and outcome required")
    if not intervention:
        raise ValueError("G2: No intervention description provided")

    if anonymise:
        display_name = "Client (anonymised)"
        display_industry = "the client's industry"
    else:
        display_name = client_name
        display_industry = industry

    baseline_total = copq_baseline.get('total', 0)
    outcome_total = copq_outcome.get('total', 0)
    reduction = baseline_total - outcome_total
    reduction_pct = (reduction / baseline_total * 100) if baseline_total > 0 else 0

    md = f"# Case Study – {display_name}\n"
    md += f"**Date:** {date or 'YYYY-MM-DD'}\n\n"

    md += "## Client Context\n"
    md += f"{display_name} is a {display_industry} company. "
    md += f"The engagement focused on reducing hidden factory costs over {engagement_name}.\n\n"

    md += "## Problem Quantified\n"
    md += f"- CoPQ baseline: £{baseline_total:,.0f}/year\n"
    if copq_baseline.get('internal'):
        md += f"  - Internal failure: £{copq_baseline['internal']:,.0f}\n"
        md += f"  - External failure: £{copq_baseline['external']:,.0f}\n"
        md += f"  - Appraisal: £{copq_baseline['appraisal']:,.0f}\n"
        md += f"  - Prevention: £{copq_baseline['prevention']:,.0f}\n"

    md += "\n## Intervention Applied\n"
    md += f"{intervention}\n\n"

    md += "## Measurable Outcome\n"
    md += f"- CoPQ reduction: £{reduction:,.0f} ({reduction_pct:.0f}%)\n"
    md += f"- First-Time Acceptance Rate: {metrics.get('ftar', 'N/A')}%\n"
    md += f"- NPS: {metrics.get('nps', 'N/A')}\n"
    if metrics.get('repeat'):
        md += f"- Repeat engagement: {metrics.get('repeat')}\n"
    if metrics.get('roi'):
        md += f"- ROI: {metrics.get('roi')}%\n"

    if include_quote and client_quote:
        md += "\n## Client Quote\n"
        md += f"\"{client_quote}\"\n\n"

    if include_lessons and lessons:
        md += "\n## Lessons Learned\n"
        for i, lesson in enumerate(lessons, 1):
            md += f"- Lesson {i}: {lesson}\n"
        md += "\n"

    md += "## Next Steps\n"
    md += f"[Call to action – e.g., book a review call with {display_name}]\n"

    if not metrics.get('ftar') and not metrics.get('nps'):
        md += "\n**Warning:** No FTAR or NPS metrics provided – consider adding for completeness.\n"

    return md


def demo():
    copq_baseline = {
        'total': 14_000_000, 'internal': 10_200_000,
        'external': 3_000_000, 'appraisal': 600_000, 'prevention': 200_000,
    }
    copq_outcome = {'total': 10_500_000}
    metrics = {'ftar': 95, 'nps': 60, 'repeat': 'Yes – follow-on engagement signed'}
    print(generate_case_study(
        client_name='Acme Aerospace',
        engagement_name='Hidden Factory Reduction',
        industry='aerospace manufacturing',
        copq_baseline=copq_baseline,
        copq_outcome=copq_outcome,
        intervention='Implemented real-time defect logging, daily defect huddles, and a Control Plan for assembly line.',
        client_quote='"Olivia\'s approach turned our data into actionable insight. We saw results in weeks, not months." – Sarah Chen, VP Ops',
        lessons=[
            'Daily defect huddles reduced rework by 40% in the first month.',
            'Real-time logging caught issues before they reached the end of the line.',
            'SOP update: standardised work instructions for all assembly lines.',
        ],
        metrics=metrics,
        date='2026-06-17',
    ))


if __name__ == "__main__":
    demo()
