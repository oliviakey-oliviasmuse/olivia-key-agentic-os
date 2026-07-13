"""
NPS Tracker – Pillar 4, Agent 4 (LLM wrapper)
"""

from typing import Optional, List
from src.pillar4.nps_tracker import (
    NPSRecord,
    compute_nps_summary,
    generate_nps_debrief,
    get_open_debriefs,
    classify_nps,
)


def add_nps(
    engagement_name: str,
    client_name: str,
    score: int,
    comment: Optional[str] = None,
) -> NPSRecord:
    return NPSRecord(
        engagement_name=engagement_name,
        client_name=client_name,
        score=score,
        comment=comment,
    )


def generate_nps_report(records: List[NPSRecord]) -> str:
    summary = compute_nps_summary(records)

    md = "# NPS Report\n"
    md += f"- Total responses: {summary['total']}\n"
    if summary['total'] > 0:
        md += f"- Average score: {summary['average']:.1f}\n"
        md += f"- Promoters: {summary['promoters']} ({summary['promoters']/summary['total']*100:.1f}%)\n"
        md += f"- Passives: {summary['passives']} ({summary['passives']/summary['total']*100:.1f}%)\n"
        md += f"- Detractors: {summary['detractors']} ({summary['detractors']/summary['total']*100:.1f}%)\n"
        md += f"- NPS: {summary['nps']:.1f}\n"
    md += f"- Status: {summary['threshold_status']}\n"

    # Open debriefs
    open_debriefs = get_open_debriefs(records)
    if open_debriefs:
        md += "\n## Open Debriefs\n"
        md += "The following engagements have NPS <50 and no debrief recorded:\n"
        for r in open_debriefs:
            md += f"- {r.engagement_name} (Client: {r.client_name}) – Score: {r.score}/10 ({classify_nps(r.score)})\n"
        md += "\n*Note: Passives (7–8) are included because they are not Promoters. Debriefing helps understand why they were not more positive.*\n"

    # Include a debrief request if the portfolio overall is ANDON
    if summary['debrief_needed']:
        md += "\n**ANDON:** NPS <50 – debrief required.\n"
        if records:
            latest = records[-1]
            md += "\n## Debrief Request\n"
            md += generate_nps_debrief(latest)

    return md
