"""
NPS Tracker – Pillar 4, Agent 4
LSS MBB NPS collection and debrief trigger.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class NPSRecord:
    engagement_name: str
    client_name: str
    score: int  # 0–10
    comment: Optional[str] = None
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    debrief_conducted: bool = False

    def __post_init__(self):
        if not self.engagement_name or not self.client_name:
            raise ValueError("G1/G2: engagement and client names required")
        if not (0 <= self.score <= 10):
            raise ValueError("G3: score must be between 0 and 10")


def classify_nps(score: int) -> str:
    if score >= 9:
        return 'Promoter'
    elif score >= 7:
        return 'Passive'
    else:
        return 'Detractor'


def is_debrief_required(record: NPSRecord) -> bool:
    """Return True if the record's NPS <50 (i.e., score <=8)."""
    return record.score <= 8  # 9-10 are Promoters, everything else is NPS <50


def get_open_debriefs(records: List[NPSRecord]) -> List[NPSRecord]:
    """Return records where NPS <50 and debrief not conducted."""
    return [r for r in records if not r.debrief_conducted and is_debrief_required(r)]


def compute_nps_summary(records: List[NPSRecord]) -> dict:
    if not records:
        return {
            'total': 0,
            'average': 0.0,
            'promoters': 0,
            'passives': 0,
            'detractors': 0,
            'nps': None,
            'threshold_status': 'NO_DATA',
            'debrief_needed': False,
        }

    total = len(records)
    scores = [r.score for r in records]
    avg = sum(scores) / total
    promoters = sum(1 for r in records if classify_nps(r.score) == 'Promoter')
    passives = sum(1 for r in records if classify_nps(r.score) == 'Passive')
    detractors = total - promoters - passives
    nps = (promoters - detractors) / total * 100 if total > 0 else None

    threshold_status = 'PASS' if nps is not None and nps >= 50 else 'ANDON'
    debrief_needed = threshold_status == 'ANDON'

    return {
        'total': total,
        'average': avg,
        'promoters': promoters,
        'passives': passives,
        'detractors': detractors,
        'nps': nps,
        'threshold_status': threshold_status,
        'debrief_needed': debrief_needed,
    }


def generate_nps_debrief(record: NPSRecord) -> str:
    return f"""
# Debrief Request – {record.engagement_name}
**Client:** {record.client_name}
**NPS Score:** {record.score}/10 ({classify_nps(record.score)})

## Questions
1. What made you score us {record.score}/10?
2. What could we have done better during the engagement?
3. Would you consider working with us again?
4. Would you recommend us to a peer? Why or why not?

Please respond within 5 working days.
"""
