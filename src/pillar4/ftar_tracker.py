"""
FTAR Tracker – Pillar 4, Agent 3
Tracks First-Time Acceptance Rate (FTAR) per deliverable.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

THRESHOLD_TRIGGER = 0.85
THRESHOLD_WARNING = 0.90

# --- Dataclasses ---

@dataclass
class FTARRecord:
    """A single deliverable submission record."""
    deliverable_name: str          # required (G1)
    status: str                    # 'PASS' or 'FAIL' (G2)
    submission_date: Optional[str] = field(default=None)
    failure_reason: Optional[str] = field(default=None)
    client_name: Optional[str] = field(default=None)
    engagement_name: Optional[str] = field(default=None)
    reviewer: Optional[str] = field(default=None)
    notes: Optional[str] = field(default=None)

    def __post_init__(self):
        if not self.deliverable_name:
            raise ValueError("G1: deliverable_name is required")
        if self.status not in ('PASS', 'FAIL'):
            raise ValueError("G2: status must be 'PASS' or 'FAIL'")
        if self.submission_date is None:
            self.submission_date = datetime.now().isoformat()

@dataclass
class FTARSummary:
    total: int
    pass_count: int
    fail_count: int
    ftar: float
    threshold_status: str
    first_submission: Optional[str] = None
    last_submission: Optional[str] = None
    failure_reasons: List[str] = field(default_factory=list)

# --- Core functions ---

def threshold_status(ftar: float, total: int) -> str:
    if total == 0:
        return 'NO_DATA'
    if ftar < THRESHOLD_TRIGGER:
        return 'ANDON'
    elif ftar < THRESHOLD_WARNING:
        return 'WARNING'
    else:
        return 'PASS'

def compute_ftar_summary(records: List[FTARRecord]) -> FTARSummary:
    """Compute FTAR statistics from a list of records."""
    if not records:
        return FTARSummary(
            total=0,
            pass_count=0,
            fail_count=0,
            ftar=0.0,
            threshold_status='NO_DATA',
            failure_reasons=[],
        )

    total = len(records)
    pass_count = sum(1 for r in records if r.status == 'PASS')
    fail_count = total - pass_count
    ftar = pass_count / total

    failure_reasons = [r.failure_reason for r in records if r.status == 'FAIL' and r.failure_reason]

    dates = [r.submission_date for r in records if r.submission_date]
    first_submission = min(dates) if dates else None
    last_submission = max(dates) if dates else None

    # Local variable renamed to 'status' to avoid shadowing the module-level function
    status = threshold_status(ftar, total)

    return FTARSummary(
        total=total,
        pass_count=pass_count,
        fail_count=fail_count,
        ftar=ftar,
        threshold_status=status,
        first_submission=first_submission,
        last_submission=last_submission,
        failure_reasons=failure_reasons,
    )
