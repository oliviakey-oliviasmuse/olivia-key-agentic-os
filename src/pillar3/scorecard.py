from __future__ import annotations
from datetime import date
from typing import Optional, Dict, Any

try:
    from src.pillar0.icp_positioning_generator import validate_prospect
    _P0_AVAILABLE = True
except ImportError:
    validate_prospect = None  # type: ignore[assignment]
    _P0_AVAILABLE = False

SCORE_MIN               = 0
SCORE_MAX_PER_QUESTION  = 3
QUESTIONS_MIN           = 5
QUESTIONS_MAX           = 10
QUESTIONS_DEFAULT       = 8
THRESHOLD_PASS          = 18
THRESHOLD_DEFER_LOW     = 12

# Warm lead: prospect demonstrated intent before the scorecard.
# Reduces both thresholds by WARM_THRESHOLD_REDUCTION (18→14, 12→8).
WARM_LEAD_SIGNALS = frozenset({
    'inbound_dm',
    'gated_content_download',
    'requested_call',
    'provided_copq_estimate',
})
WARM_THRESHOLD_REDUCTION = 4
THRESHOLD_PASS_WARM      = THRESHOLD_PASS - WARM_THRESHOLD_REDUCTION       # 14
THRESHOLD_DEFER_LOW_WARM = THRESHOLD_DEFER_LOW - WARM_THRESHOLD_REDUCTION  # 8

RECOMMENDATION_PROCEED = 'PROCEED'
RECOMMENDATION_DEFER   = 'DEFER'
RECOMMENDATION_REJECT  = 'REJECT'

SCORECARD_TYPES = ('CoPQ_Health', 'Hidden_Factory', 'Ops_Maturity')

DEFECT_CODES = {
    'S1': 'Prospect did not return completed scorecard within 7 days — may need shorter version',
    'S2': 'Scorecard passed (≥18) but discovery call produced no commercial result — false positive; adjust rubric',
    'S3': 'Scorecard failed (<12) but prospect later converted via another channel — false negative; adjust rubric',
}

QUESTION_BANKS: dict[str, list[str]] = {
    'CoPQ_Health': [
        'Do you track internal failure costs (rework, scrap, downtime)?',
        'Do you track external failure costs (warranty, returns, customer penalties)?',
        'Do you have a measurement system for your hidden factory?',
        'Is there a documented Control Plan for any core process?',
        'Do you have real-time or daily defect logging in place?',
        'Is there a formal root-cause process (e.g., 5 Whys, Fishbone, 8D)?',
        'Have you quantified your total CoPQ in the last 12 months?',
        'Is reducing process variation a formal operational goal this year?',
        'Do senior leaders review quality cost data at least monthly?',
        'Is there budget allocated specifically for prevention activities?',
    ],
    'Hidden_Factory': [
        'Do you know what percentage of production time is spent on rework?',
        'Can you quantify the cost of your hidden factory in the last financial year?',
        'Do you have defect visibility at each production stage (not just end-of-line)?',
        'Are labour hours lost to non-value-added activity formally tracked?',
        'Do you have a documented value stream map for your highest-volume product?',
        'Is excess inventory or WIP tracked as a cost category?',
        'Do you have real-time machine downtime data?',
        'Is waste (TIMWOOD) formally measured or estimated across production?',
        'Are inspection and test costs included in your monthly reporting?',
        'Do you hold post-incident reviews when a hidden factory event is discovered?',
    ],
    'Ops_Maturity': [
        'Do you have documented SOPs for all core processes?',
        'Are process performance metrics reviewed at least weekly by operations leadership?',
        'Do you have a formal continuous improvement programme (Kaizen, Six Sigma, or equivalent)?',
        'Is your measurement system validated (MSA / Gauge R&R)?',
        'Are critical-to-quality parameters defined for your key products or services?',
        'Do you have a process for translating customer requirements into internal specifications?',
        'Is there a formal supplier quality management process in place?',
        'Do you conduct periodic management reviews of quality system effectiveness?',
        'Is statistical process control (SPC) used on any critical process?',
        'Do you have a formal change management process for process modifications?',
    ],
}


class ScorecardError(Exception):
    pass


def generate_questions(
    scorecard_type: str = 'CoPQ_Health',
    questions_count: int = QUESTIONS_DEFAULT,
) -> list[str]:
    if scorecard_type not in SCORECARD_TYPES:
        raise ScorecardError(
            f"Unknown scorecard type '{scorecard_type}'. Must be one of: {SCORECARD_TYPES}"
        )
    if not (QUESTIONS_MIN <= questions_count <= QUESTIONS_MAX):
        raise ScorecardError(
            f"questions_count must be {QUESTIONS_MIN}–{QUESTIONS_MAX}. Got {questions_count}."
        )
    return QUESTION_BANKS[scorecard_type][:questions_count]


def max_score(questions_count: int) -> int:
    return questions_count * SCORE_MAX_PER_QUESTION


def calculate_score(responses: list[int]) -> int:
    for i, r in enumerate(responses):
        if not (SCORE_MIN <= r <= SCORE_MAX_PER_QUESTION):
            raise ScorecardError(
                f"Response {i + 1} out of range: {r}. Must be {SCORE_MIN}–{SCORE_MAX_PER_QUESTION}."
            )
    return sum(responses)


def validate_scorecard(questions: list[str], responses: list[int]) -> bool:
    n = len(questions)
    if not (QUESTIONS_MIN <= n <= QUESTIONS_MAX):
        raise ScorecardError(
            f"Question count {n} out of range. Must be {QUESTIONS_MIN}–{QUESTIONS_MAX}."
        )
    if len(responses) != n:
        raise ScorecardError(
            f"Response count ({len(responses)}) must match question count ({n})."
        )
    calculate_score(responses)  # validates individual score ranges
    return True


def recommend(
    total: int,
    warm_lead_signals: list[str] | None = None,
    threshold_pass: int = THRESHOLD_PASS,
    threshold_defer_low: int = THRESHOLD_DEFER_LOW,
    *,
    industry: str | None = None,
    company_size: int | None = None,
    arr: float | None = None,
    role: str | None = None,
    geography: str | None = None,
) -> tuple[str, str]:
    """Returns (recommendation_code, explanation).

    When warm_lead_signals is provided and non-empty, warm thresholds apply
    (PROCEED ≥14, DEFER 8–13, REJECT <8) instead of cold (18/12).

    When industry and company_size are provided and P0 is available, an ICP hard gate
    fires first — REJECT regardless of score if prospect is outside P0 ICP.
    """
    # P0 ICP hard gate — fires before score thresholds when prospect data is supplied
    if _P0_AVAILABLE and industry is not None and company_size is not None:
        prospect_data = {k: v for k, v in {
            "industry": industry,
            "company_size": company_size,
            "arr": arr,
            "role": role,
            "geography": geography,
        }.items() if v is not None}
        icp_check = validate_prospect(prospect_data)
        if not icp_check["pass"]:
            return (
                RECOMMENDATION_REJECT,
                f"P0 ICP gate: {icp_check.get('reason', 'outside ICP')} — rejected regardless of score.",
            )

    if warm_lead_signals:
        invalid = set(warm_lead_signals) - WARM_LEAD_SIGNALS
        if invalid:
            raise ScorecardError(f"Unknown warm lead signal(s): {invalid!r}")
        threshold_pass = THRESHOLD_PASS_WARM
        threshold_defer_low = THRESHOLD_DEFER_LOW_WARM

    warm_note = (
        f' (warm lead — {", ".join(sorted(warm_lead_signals))})'
        if warm_lead_signals else ''
    )

    if total >= threshold_pass:
        return (
            RECOMMENDATION_PROCEED,
            f'Score {total} ≥ {threshold_pass}{warm_note}. Strong pain signal and measurement '
            f'awareness. Proceed to Discovery Call.',
        )
    if total >= threshold_defer_low:
        return (
            RECOMMENDATION_DEFER,
            f'Score {total} is in the defer range ({threshold_defer_low}–{threshold_pass - 1})'
            f'{warm_note}. Pain exists but measurement infrastructure is underdeveloped. '
            f'Gather more data before scheduling a call.',
        )
    return (
        RECOMMENDATION_REJECT,
        f'Score {total} < {threshold_defer_low}{warm_note}. Low pain signal or absent '
        f'measurement system. Not a suitable fit at this time.',
    )


def build_scorecard_markdown(
    prospect_name: str,
    company: str,
    questions: list[str],
    responses: Optional[list[int]] = None,
    scorecard_type: str = 'CoPQ_Health',
    warm_lead_signals: Optional[list[str]] = None,
) -> str:
    today = date.today().isoformat()
    title = scorecard_type.replace('_', ' ')

    lead_type = 'Warm' if warm_lead_signals else 'Cold'
    t_pass = THRESHOLD_PASS_WARM if warm_lead_signals else THRESHOLD_PASS
    t_defer = THRESHOLD_DEFER_LOW_WARM if warm_lead_signals else THRESHOLD_DEFER_LOW

    lines = [
        f'# {title} — Scorecard',
        f'**Prospect:** {prospect_name} | **Company:** {company} | **Date:** {today}',
        f'**Lead type:** {lead_type} | **Thresholds:** PROCEED ≥{t_pass} / DEFER ≥{t_defer} / REJECT <{t_defer}',
    ]
    if warm_lead_signals:
        lines.append(f'**Warm signals:** {", ".join(sorted(warm_lead_signals))}')

    lines += [
        '',
        '| # | Question | Score (0–3) | Notes |',
        '|---|----------|-------------|-------|',
    ]
    for i, q in enumerate(questions, 1):
        score_cell = str(responses[i - 1]) if responses else ''
        lines.append(f'| {i} | {q} | {score_cell} | |')

    mx = max_score(len(questions))

    if responses:
        total = calculate_score(responses)
        rec_code, rec_text = recommend(total, warm_lead_signals=warm_lead_signals)
        lines.append(f'| **Total** | | **{total}/{mx}** | |')
        lines.append('')
        lines.append(f'**Recommendation:** {rec_code} — {rec_text}')
    else:
        lines.append(f'| **Total** | | **/{mx}** | |')
        lines.append('')
        lines.append(
            '*Copy this table, fill in your scores (0–3 per question), and reply '
            'with the completed scorecard.*'
        )

    return '\n'.join(lines)


def scorecard_analyser(scores, warm_lead=False, threshold_cold=18, threshold_warm=14):
    """
    Wrapper for simulation and pipeline use.
    Converts a list of scores to a verdict dict using recommend().
    """
    total = sum(scores)
    warm_signals = ['inbound_dm'] if warm_lead else []
    verdict, _ = recommend(total, warm_signals, threshold_cold, threshold_warm)
    return {
        'verdict': verdict,
        'score': total,
        'threshold_used': threshold_warm if warm_lead else threshold_cold,
    }
