from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_LOG = Path(__file__).resolve().parent.parent.parent / 'outreach_log.md'

_HEADER = (
    '# Pillar 3 — Outreach Log\n'
    'One entry per prospect. Append only — do not edit previous entries.\n\n'
)


def append_log_entry(
    prospect_name: str,
    company: str,
    scorecard_type: str,
    total_score: int,
    max_score: int,
    recommendation: str,
    notes: str = '',
    warm_lead_signals: list[str] | None = None,
    log_file: Path = _DEFAULT_LOG,
) -> None:
    from src.pillar3.scorecard import THRESHOLD_PASS, THRESHOLD_PASS_WARM
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lead_type = f'Warm ({", ".join(sorted(warm_lead_signals))})' if warm_lead_signals else 'Cold'
    threshold_used = THRESHOLD_PASS_WARM if warm_lead_signals else THRESHOLD_PASS
    lines = [
        f'## {prospect_name} — {company}',
        f'**Date:** {ts} | **Scorecard:** {scorecard_type}',
        f'**Score:** {total_score}/{max_score} | **Recommendation:** {recommendation}',
        f'**Lead type:** {lead_type} | **Threshold applied:** ≥{threshold_used}',
    ]
    if notes:
        lines.append(f'**Notes:** {notes}')
    lines.append('')

    if not log_file.exists():
        log_file.write_text(_HEADER, encoding='utf-8')

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
